from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from models import *
from database import *
from dotenv import load_dotenv
import google.generativeai as genai
import os
import base64
from io import BytesIO
from PIL import Image

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# สมัครสมาชิก
@app.post("/signup/")
def signup(user_data: User_signup, db: Session = Depends(get_db)):
    hashed_password = pwd_context.hash(user_data.password)
    user = User(name=user_data.name,user_name=user_data.username, user_password=hashed_password)
    db.add(user)
    db.commit()
    return {"message": "User created successfully"}

# เข้าสู่ระบบ
@app.post("/login/")
def login(request: User_login, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_name == request.username).first()
    if not user or not pwd_context.verify(request.password, user.user_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = jwt.encode({"sub": request.username}, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}

@app.post("/post_reciept/")
async def create_reciept(user_id: int = Form(...), 
                         recipe_name: str = Form(...),
                         detail: str = Form(...), 
                         image: UploadFile = File(...), 
                         db: Session = Depends(get_db)):
    image_data = await image.read()
    reciept = Reciept(user_id=user_id, recipe_name=recipe_name, image=image_data, detail=detail)
    db.add(reciept)
    db.commit()
    return {"message": "Reciept created successfully"}

@app.get("/reciept_table/")
def table(user_id: int, db: Session = Depends(get_db)):
    table_data = db.query(Reciept.recipe_id, Reciept.recipe_name, Reciept.date).filter(Reciept.user_id == user_id).all()
    # image_base64 = base64.b64encode(table_data.image).decode("utf-8")
    return [
        {
            "Id": data.recipe_id,
            "Name": data.recipe_name,
            "Date": data.date
        }
        for data in table_data
    ]
    
@app.get("/reciept_detail/")
def responseDetail(user_id: int, reciept_id: int, db: Session = Depends(get_db)):
    table_data = db.query(Reciept.recipe_name, Reciept.image, Reciept.detail).filter(Reciept.user_id == user_id, Reciept.recipe_id == reciept_id).all()
    
    return [
        {
            "Name": data.recipe_name,
            "Image": base64.b64encode(data.image).decode("utf-8"),
            "Date": data.detail
        }
        for data in table_data
    ]
    
@app.delete("/delete_reciept/")
def delete_reciept(reciept_id: int, db: Session = Depends(get_db)):
    reciept = db.query(Reciept).filter(Reciept.recipe_id == reciept_id).first()

    if not reciept:
        raise HTTPException(status_code=404, detail="Reciept not found")

    db.delete(reciept)
    db.commit()
    return {"message": "Reciept deleted successfully"}

# Configure Gemini API
def configure_genai():
    genai.configure(api_key=os.getenv('GOOGLE_API_KEY')) 
    
# Initialize the model
def initialize_model():
    return genai.GenerativeModel('gemini-1.5-pro')

# Process the image and get response
async def process_image(model, image):
    prompt = """นี่คืออาหารไทยเมนูอะไร บอกส่วนผสม วัตถุดิบ วัตถุดิบที่ใช้ทดทนกันได้ และขั้นตอนการประกอบอาหารชนิดนี้อย่างละเอียด โดยอธิบายเป็นภาษาไทย"""
    
    response = model.generate_content([prompt, image])
    return response.text

@app.post("/process-image/")
async def process_receipt(file: UploadFile = File(...)):
    try:
        # Read and validate the image
        contents = await file.read()
        image = Image.open(BytesIO(contents))
        
        # Configure and initialize Gemini
        configure_genai()
        model = initialize_model()
        
        # Process the image and get raw text response
        response_text = await process_image(model, image)
        
        return {
            "status": "success",
            "result": response_text
        }
            
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
        
if __name__ =='__main__':
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)