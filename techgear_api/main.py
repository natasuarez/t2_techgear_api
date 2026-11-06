
import os
import hashlib
import secrets

from datetime import datetime, timedelta, timezone

from bson import ObjectId
from jose import jwt, JWTError

from fastapi import (
    FastAPI,
    HTTPException,
    Depends,
    status
)

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from pydantic import BaseModel, EmailStr, Field

from pymongo import ReturnDocument

from database import (
    cliente,
    db,
    users_collection,
    products_collection,
    orders_collection,
    verificar_conexion
)


# ==========================================
# CONFIGURACION
# ==========================================

SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    raise ValueError("Falta SECRET_KEY en las variables de entorno")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# ADMINISTRADOR QUEMADO
ADMIN_CORREO = "admin@techgear.com"
ADMIN_PASSWORD = "Admin123*"
ADMIN_NOMBRE = "Administrador"

security = HTTPBearer()

app = FastAPI(
    title="TechGear API",
    description="API de la tienda TechGear",
    version="2.0.0"
)


# ==========================================
# MODELOS
# ==========================================

class Usuario(BaseModel):
    nombre: str
    correo: EmailStr
    password: str = Field(min_length=6)
    rol: str = "cliente"


class Producto(BaseModel):
    nombre: str
    descripcion: str = ""
    precio: float = Field(gt=0)
    stock: int = Field(ge=0)
    imagen: str = ""


class ProductoPedido(BaseModel):
    producto_id: str
    cantidad: int = Field(gt=0)
    talla: str


class Pedido(BaseModel):
    productos: list[ProductoPedido]


# ==========================================
# FUNCIONES AUXILIARES
# ==========================================

def convertir_id(documento):
    if documento:
        documento["_id"] = str(documento["_id"])
    return documento


def obtener_password_hash(password):
    salt = secrets.token_hex(16)

    hash_password = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt.encode(),
        200000
    ).hex()

    return f"{salt}${hash_password}"


def verificar_password(password, password_guardado):
    try:
        salt, hash_original = password_guardado.split("$")

        hash_nuevo = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            salt.encode(),
            200000
        ).hex()

        return secrets.compare_digest(hash_nuevo, hash_original)

    except ValueError:
        return secrets.compare_digest(password, password_guardado)


def crear_token(usuario):
    datos = {
        "sub": usuario["correo"],
        "rol": usuario["rol"],
        "exp": datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    }

    return jwt.encode(datos, SECRET_KEY, algorithm=ALGORITHM)


def obtener_usuario(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

    try:
        datos = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        correo = datos.get("sub")

        if not correo:
            raise HTTPException(
                status_code=401,
                detail="Token inválido"
            )

        # Reconocer al administrador quemado
        if (
            correo == ADMIN_CORREO
            and datos.get("rol") == "admin"
        ):
            return {
                "_id": "admin-techgear",
                "correo": ADMIN_CORREO,
                "nombre": ADMIN_NOMBRE,
                "rol": "admin"
            }

        # Buscar clientes en MongoDB
        usuario = users_collection.find_one({
            "correo": correo
        })

        if not usuario:
            raise HTTPException(
                status_code=401,
                detail="Usuario no encontrado"
            )

        return usuario

    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Token inválido o vencido"
        )


def solo_admin(usuario=Depends(obtener_usuario)):
    if usuario.get("rol") != "admin":
        raise HTTPException(
            status_code=403,
            detail="No tienes permisos de administrador"
        )

    return usuario


def validar_producto_id(product_id):
    if not ObjectId.is_valid(product_id):
        raise HTTPException(
            status_code=400,
            detail="ID de producto inválido"
        )

    return ObjectId(product_id)


# ==========================================
# CONEXION
# ==========================================

@app.on_event("startup")
def iniciar():
    verificar_conexion()


@app.get("/")
def inicio():
    return {
        "mensaje": "API TechGear funcionando correctamente"
    }


@app.get("/test-mongo")
def test_mongo():
    try:
        cliente.admin.command("ping")

        return {
            "estado": "Conectado",
            "mensaje": "MongoDB Atlas funciona correctamente"
        }

    except Exception as e:
        return {
            "estado": "Error",
            "mensaje": str(e)
        }


# ==========================================
# REGISTRO DE USUARIOS
# ==========================================

@app.post("/users/", status_code=201)
def registrar_usuario(usuario: Usuario):

    if usuario.rol != "cliente":
        raise HTTPException(
            status_code=403,
            detail="No puedes registrarte como administrador"
        )

    if str(usuario.correo) == ADMIN_CORREO:
        raise HTTPException(
            status_code=400,
            detail="Este correo está reservado para el administrador"
        )

    if users_collection.find_one({"correo": usuario.correo}):
        raise HTTPException(
            status_code=400,
            detail="Este correo ya está registrado"
        )

    nuevo_usuario = {
        "nombre": usuario.nombre,
        "correo": usuario.correo,
        "password": obtener_password_hash(usuario.password),
        "rol": "cliente"
    }

    resultado = users_collection.insert_one(nuevo_usuario)

    return {
        "mensaje": "Usuario registrado correctamente",
        "id": str(resultado.inserted_id)
    }


# ==========================================
# LOGIN
# ==========================================

@app.post("/login")
def login(datos: dict):

    correo = datos.get("correo")
    password = datos.get("password")

    if not correo or not password:
        raise HTTPException(
            status_code=400,
            detail="Debes ingresar correo y contraseña"
        )

    # PRIMERO: comprobar administrador quemado
    if (
        correo == ADMIN_CORREO
        and secrets.compare_digest(password, ADMIN_PASSWORD)
    ):
        administrador = {
            "_id": "admin-techgear",
            "correo": ADMIN_CORREO,
            "nombre": ADMIN_NOMBRE,
            "rol": "admin"
        }

        token = crear_token(administrador)

        return {
            "access_token": token,
            "token_type": "bearer",
            "rol": "admin",
            "nombre": ADMIN_NOMBRE
        }

    # SEGUNDO: comprobar cliente en MongoDB
    usuario = users_collection.find_one({
        "correo": correo
    })

    if not usuario or not verificar_password(
        password,
        usuario["password"]
    ):
        raise HTTPException(
            status_code=401,
            detail="Correo o contraseña incorrectos"
        )

    token = crear_token(usuario)

    return {
        "access_token": token,
        "token_type": "bearer",
        "rol": usuario["rol"],
        "nombre": usuario["nombre"]
    }


# ==========================================
# PRODUCTOS
# ==========================================

@app.post("/products/", status_code=201)
def crear_producto(
    producto: Producto,
    usuario=Depends(solo_admin)
):

    nuevo_producto = producto.model_dump()

    resultado = products_collection.insert_one(nuevo_producto)

    return {
        "mensaje": "Producto creado correctamente",
        "id": str(resultado.inserted_id)
    }


@app.get("/products/")
def listar_productos():

    productos = list(products_collection.find())

    return [convertir_id(p) for p in productos]


@app.get("/products/{product_id}")
def obtener_producto(product_id: str):

    oid = validar_producto_id(product_id)

    producto = products_collection.find_one({"_id": oid})

    if not producto:
        raise HTTPException(
            status_code=404,
            detail="Producto no encontrado"
        )

    return convertir_id(producto)


@app.put("/products/{product_id}")
def actualizar_producto(
    product_id: str,
    producto: Producto,
    usuario=Depends(solo_admin)
):

    oid = validar_producto_id(product_id)

    resultado = products_collection.update_one(
        {"_id": oid},
        {"$set": producto.model_dump()}
    )

    if resultado.matched_count == 0:
        raise HTTPException(
            status_code=404,
            detail="Producto no encontrado"
        )

    return {
        "mensaje": "Producto actualizado correctamente"
    }


@app.delete("/products/{product_id}", status_code=204)
def eliminar_producto(
    product_id: str,
    usuario=Depends(solo_admin)
):

    oid = validar_producto_id(product_id)

    resultado = products_collection.delete_one({
        "_id": oid
    })

    if resultado.deleted_count == 0:
        raise HTTPException(
            status_code=404,
            detail="Producto no encontrado"
        )

    return None


# ==========================================
# CREAR PEDIDOS
# ==========================================

@app.post("/orders/", status_code=201)
def crear_pedido(
    pedido: Pedido,
    usuario=Depends(obtener_usuario)
):

    if not pedido.productos:
        raise HTTPException(
            status_code=400,
            detail="El pedido debe tener productos"
        )

    productos_pedido = []
    total = 0

    for item in pedido.productos:

        oid = validar_producto_id(item.producto_id)

        producto = products_collection.find_one({
            "_id": oid
        })

        if not producto:
            raise HTTPException(
                status_code=404,
                detail=f"Producto {item.producto_id} no encontrado"
            )

        stock = int(producto.get("stock", 0))

        if stock < item.cantidad:
            raise HTTPException(
                status_code=400,
                detail=f"Stock insuficiente para {producto['nombre']}. Disponible: {stock}"
            )

        precio = float(producto["precio"])
        subtotal = precio * item.cantidad

        productos_pedido.append({
            "producto_id": str(oid),
            "nombre": producto["nombre"],
            "precio": precio,
            "cantidad": item.cantidad,
            "talla": item.talla,
            "subtotal": subtotal
        })

        total += subtotal

    nuevo_pedido = {
        "cliente_id": str(usuario["_id"]),
        "cliente_nombre": usuario["nombre"],
        "cliente_correo": usuario["correo"],
        "productos": productos_pedido,
        "total": total,
        "estado": "Pendiente",
        "fecha": datetime.now(timezone.utc)
    }

    resultado = orders_collection.insert_one(nuevo_pedido)

    return {
        "mensaje": "Pedido enviado correctamente",
        "pedido_id": str(resultado.inserted_id),
        "estado": "Pendiente",
        "total": total
    }


# ==========================================
# CONSULTAR PEDIDOS
# ==========================================

@app.get("/orders/")
def listar_pedidos(usuario=Depends(obtener_usuario)):

    if usuario.get("rol") == "admin":
        pedidos = list(
            orders_collection.find().sort("fecha", -1)
        )
    else:
        pedidos = list(
            orders_collection.find({
                "cliente_id": str(usuario["_id"])
            }).sort("fecha", -1)
        )

    return [convertir_id(p) for p in pedidos]


@app.get("/orders/{order_id}")
def obtener_pedido(
    order_id: str,
    usuario=Depends(obtener_usuario)
):

    if not ObjectId.is_valid(order_id):
        raise HTTPException(
            status_code=400,
            detail="ID de pedido inválido"
        )

    pedido = orders_collection.find_one({
        "_id": ObjectId(order_id)
    })

    if not pedido:
        raise HTTPException(
            status_code=404,
            detail="Pedido no encontrado"
        )

    if (
        usuario.get("rol") != "admin"
        and pedido["cliente_id"] != str(usuario["_id"])
    ):
        raise HTTPException(
            status_code=403,
            detail="No puedes consultar este pedido"
        )

    return convertir_id(pedido)


# ==========================================
# APROBAR PEDIDOS
# ==========================================

@app.put("/orders/{order_id}/approve")
def aprobar_pedido(
    order_id: str,
    usuario=Depends(solo_admin)
):

    if not ObjectId.is_valid(order_id):
        raise HTTPException(
            status_code=400,
            detail="ID de pedido inválido"
        )

    pedido = orders_collection.find_one({
        "_id": ObjectId(order_id),
        "estado": "Pendiente"
    })

    if not pedido:
        raise HTTPException(
            status_code=404,
            detail="Pedido no encontrado o ya procesado"
        )

    descontados = []

    try:
        for item in pedido["productos"]:

            oid = validar_producto_id(item["producto_id"])
            cantidad = int(item["cantidad"])

            resultado = products_collection.update_one(
                {
                    "_id": oid,
                    "stock": {"$gte": cantidad}
                },
                {
                    "$inc": {"stock": -cantidad}
                }
            )

            if resultado.modified_count == 0:
                raise ValueError(
                    f"Stock insuficiente para {item['nombre']}"
                )

            descontados.append({
                "id": oid,
                "cantidad": cantidad
            })

        resultado = orders_collection.update_one(
            {
                "_id": pedido["_id"],
                "estado": "Pendiente"
            },
            {
                "$set": {
                    "estado": "Aprobado",
                    "fecha_aprobacion": datetime.now(timezone.utc),
                    "aprobado_por": usuario["correo"]
                }
            }
        )

        if resultado.modified_count == 0:
            raise ValueError("El pedido ya fue procesado")

    except Exception as e:

        for producto in descontados:
            products_collection.update_one(
                {"_id": producto["id"]},
                {
                    "$inc": {
                        "stock": producto["cantidad"]
                    }
                }
            )

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    return {
        "mensaje": "Pedido aprobado correctamente",
        "estado": "Aprobado",
        "inventario": "Stock actualizado"
    }


# ==========================================
# RECHAZAR PEDIDOS
# ==========================================

@app.put("/orders/{order_id}/reject")
def rechazar_pedido(
    order_id: str,
    usuario=Depends(solo_admin)
):

    if not ObjectId.is_valid(order_id):
        raise HTTPException(
            status_code=400,
            detail="ID de pedido inválido"
        )

    resultado = orders_collection.update_one(
        {
            "_id": ObjectId(order_id),
            "estado": "Pendiente"
        },
        {
            "$set": {
                "estado": "Rechazado",
                "fecha_rechazo": datetime.now(timezone.utc),
                "rechazado_por": usuario["correo"]
            }
        }
    )

    if resultado.modified_count == 0:
        raise HTTPException(
            status_code=404,
            detail="Pedido no encontrado o ya procesado"
        )

    return {
        "mensaje": "Pedido rechazado correctamente",
        "estado": "Rechazado",
        "inventario": "Sin cambios"
    }
