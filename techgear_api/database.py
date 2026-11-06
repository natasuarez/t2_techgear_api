
import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise ValueError("No se encontró MONGO_URI en el archivo .env")

cliente = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=20000
)

db = cliente["techgear"]

# Colecciones de MongoDB
users_collection = db["users"]
products_collection = db["products"]
orders_collection = db["orders"]


def verificar_conexion():
    try:
        cliente.admin.command("ping")
        print("Conexion exitosa con MongoDB Atlas")
        return True

    except Exception as e:
        print("Error de conexion:", e)
        return False
