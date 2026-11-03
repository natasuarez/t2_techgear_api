from django.shortcuts import render

# Create your views here.
import requests
from django.shortcuts import render, redirect
from django.contrib import messages

# URL base de tu FastAPI (ajústala si usas la de Render o http://127.0.0.1:8000)
API_URL = "http://127.0.0.1:8000"

def login_view(request):
    if request.method == "POST":
        correo = request.POST.get("correo")
        password = request.POST.get("password")
        
        # Petición al endpoint /login de FastAPI
        try:
            response = requests.post(f"{API_URL}/login", json={"correo": correo, "password": password})
            if response.status_code == 200:
                token_data = response.json()
                # Guardar el JWT en la sesión de Django
                request.session["access_token"] = token_data["access_token"]
                messages.success(request, "¡Inicio de sesión exitoso!")
                return redirect("products_list")
            else:
                messages.error(request, "Correo o contraseña incorrectos.")
        except requests.exceptions.ConnectionError:
            messages.error(request, "No se pudo conectar con el servidor backend (FastAPI).")
            
    return render(request, "store/login.html")

def register_view(request):
    if request.method == "POST":
        nombre = request.POST.get("nombre")
        correo = request.POST.get("correo")
        password = request.POST.get("password")
        
        # Estructura requerida por tu UserSchema en FastAPI
        user_data = {
            "nombre": nombre,
            "correo": correo,
            "password": password,
            "rol": "cliente"
        }
        
        try:
            response = requests.post(f"{API_URL}/users/", json=user_data)
            if response.status_code == 201:
                messages.success(request, "¡Registro exitoso! Por favor inicia sesión.")
                return redirect("login")
            else:
                error_detail = response.json().get("detail", "Error al registrarse.")
                messages.error(request, f"Error: {error_detail}")
        except requests.exceptions.ConnectionError:
            messages.error(request, "Error de conexión con la API.")
            
    return render(request, "store/register.html")

def products_list_view(request):
    token = request.session.get("access_token")
    if not token:
        return redirect("login")
    
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(f"{API_URL}/products/", headers=headers)
        products = response.json() if response.status_code == 200 else []
    except requests.exceptions.ConnectionError:
        products = []
        messages.error(request, "No se pudo obtener el catálogo de productos.")
        
    return render(request, "store/products.html", {"products": products})

def logout_view(request):
    request.session.flush()
    return redirect("login")