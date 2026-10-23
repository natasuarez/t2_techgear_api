from fastapi import APIRouter, HTTPException, status
from src.database import product_collection
from src.models.product import ProductSchema, ProductResponse
from bson import ObjectId

router = APIRouter(prefix="/products", tags=["Productos"])

@router.post("/", response_description="Crear un nuevo producto", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductSchema):
    # Convertir el modelo de Pydantic a diccionario para MongoDB
    product_dict = product.dict()
    
    # Insertar en MongoDB Atlas
    new_product = await product_collection.insert_one(product_dict)
    
    # Buscar el producto insertado para retornarlo con su ID
    created_product = await product_collection.find_one({"_id": new_product.inserted_id})
    
    # Convertir el ObjectId de MongoDB a string para que Pydantic lo acepte
    created_product["_id"] = str(created_product["_id"])
    return created_product

@router.get("/", response_description="Listar todos los productos", response_model=list[ProductResponse])
async def get_products():
    products = []
    # Recorrer los documentos de la colección de manera asíncrona
    async for product in product_collection.find():
        product["_id"] = str(product["_id"])
        products.append(product)
    return products