from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os
from dotenv import load_dotenv
from passlib.context import CryptContext
from jose import jwt
from pydantic import BaseModel, EmailStr
from fastapi import FastAPI

# Importa tus esquemas Pydantic
from techgear_api.models.product import ProductSchema, ProductResponse
from techgear_api.models.order import OrderSchema, OrderResponse
from techgear_api.models.user import UserSchema, UserResponse

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Bienvenido a TechGear API"}

app = FastAPI(title="TechGear API", version="1.0")

client = AsyncIOMotorClient(MONGO_URI)
db = client.techgear_db  # Nombre de tu base de datos en Atlas

# --- CONFIGURACIÓN DE SEGURIDAD Y JWT ---
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Esquema adicional exclusivo para recibir las credenciales en el Login
class UserLoginSchema(BaseModel):
    correo: EmailStr
    password: str

class TokenSchema(BaseModel):
    access_token: str
    token_type: str

def get_password_hash(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


@app.get("/")
async def root():
    return {"message": "Bienvenido a TechGear API - FastAPI & MongoDB"}

# --- CRUD DE PRODUCTOS ---
@app.post("/products/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductSchema):
    product_dict = product.model_dump()
    result = await db.products.insert_one(product_dict)
    created_product = await db.products.find_one({"_id": result.inserted_id})
    created_product["_id"] = str(created_product["_id"])
    return created_product

@app.get("/products/", response_model=list[ProductResponse])
async def get_products():
    products = []
    async for product in db.products.find():
        product["_id"] = str(product["_id"])
        products.append(product)
    return products

@app.get("/products/{id}", response_model=ProductResponse)
async def get_product(id: str):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="ID de producto inválido")
    product = await db.products.find_one({"_id": ObjectId(id)})
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    product["_id"] = str(product["_id"])
    return product

@app.put("/products/{id}", response_model=ProductResponse)
async def update_product(id: str, product: ProductSchema):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="ID inválido")
    update_data = product.model_dump()
    result = await db.products.update_one({"_id": ObjectId(id)}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    updated_product = await db.products.find_one({"_id": ObjectId(id)})
    updated_product["_id"] = str(updated_product["_id"])
    return updated_product

@app.delete("/products/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(id: str):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="ID inválido")
    result = await db.products.delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return None

# --- REGISTRO DE PEDIDOS ---
@app.post("/orders/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(order: OrderSchema):
    order_dict = order.model_dump()
    result = await db.orders.insert_one(order_dict)
    created_order = await db.orders.find_one({"_id": result.inserted_id})
    created_order["_id"] = str(created_order["_id"])
    return created_order

# --- REGISTRO DE USUARIOS Y AUTENTICACIÓN (JWT) ---
@app.post("/users/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserSchema):
    # Verificar si el usuario ya existe
    existing_user = await db.users.find_one({"correo": user.correo})
    if existing_user:
        raise HTTPException(status_code=400, detail="El correo ya está registrado")
    
    user_dict = user.model_dump()
    # Encriptar la contraseña antes de guardarla en MongoDB
    user_dict["password"] = get_password_hash(user_dict["password"])
    
    result = await db.users.insert_one(user_dict)
    created_user = await db.users.find_one({"_id": result.inserted_id})
    created_user["_id"] = str(created_user["_id"])
    return created_user

@app.post("/login", response_model=TokenSchema)
async def login(form_data: UserLoginSchema):
    user = await db.users.find_one({"correo": form_data.correo})
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas o correo no registrado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generar el Token JWT con expiración
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": user["correo"], "exp": expire}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return {"access_token": encoded_jwt, "token_type": "bearer"}