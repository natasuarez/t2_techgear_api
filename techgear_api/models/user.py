from pydantic import BaseModel, Field, EmailStr
from typing import Optional

class UserSchema(BaseModel):
    nombre: str = Field(..., min_length=2, description="Nombre completo del usuario")
    correo: EmailStr = Field(..., description="Correo electrónico único")
    password: str = Field(..., min_length=6, description="Contraseña de acceso")
    rol: str = Field(default="cliente", description="Rol en el sistema (cliente, admin)")

class UserResponse(UserSchema):
    id: str = Field(..., alias="_id", description="ID único generado por MongoDB")

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True