from pydantic import BaseModel, Field
from typing import List

class ItemPedido(BaseModel):
    producto_id: str = Field(..., description="ID del producto en la base de datos")
    cantidad: int = Field(..., gt=0, description="Cantidad solicitada (debe ser mayor a 0)")

class OrderSchema(BaseModel):
    cliente: str = Field(..., min_length=1, description="Nombre o identificación del cliente")
    items: List[ItemPedido] = Field(..., description="Lista de productos que componen el pedido")
    total: float = Field(..., gt=0, description="Costo total del pedido")
    estado: str = Field(default="pendiente", description="Estado actual del pedido")

class OrderResponse(OrderSchema):
    id: str = Field(..., alias="_id", description="ID único generado por MongoDB")

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True