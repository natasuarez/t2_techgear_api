from pydantic import BaseModel, Field

class ProductSchema(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100, description="Nombre del producto")
    precio: float = Field(..., gt=0, description="El precio debe ser mayor a 0")
    stock: int = Field(..., ge=0, description="Cantidad disponible en inventario")
    categoria: str = Field(..., description="Categoría a la que pertenece")

class ProductResponse(ProductSchema):
    id: str = Field(..., alias="_id", description="ID único generado por MongoDB")

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True