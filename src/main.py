from fastapi import FastAPI
from src.views.products import router as product_router  # O la ruta donde lo hayas guardado

app = FastAPI(
    title="E-commerce API Core",
    version="1.0.0",
    description="API desarrollada con FastAPI y MongoDB Atlas"
)

# Incluir las rutas de productos
app.include_router(product_router)

@app.get("/")
async def root():
    return {"message": "¡Bienvenido al Backend de FastAPI y MongoDB!"}