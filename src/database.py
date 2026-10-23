import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Carga las variables del archivo .env
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

# Inicializa el cliente asíncrono de MongoDB
client = AsyncIOMotorClient(MONGO_URI)

# Selecciona la base de datos (puedes cambiar "tienda_db" por el nombre que prefieras)
database = client.get_database("tienda_db")

# Define las colecciones principales para productos y pedidos
product_collection = database.get_collection("products")
order_collection = database.get_collection("orders")