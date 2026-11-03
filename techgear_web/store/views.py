import os
import requests
from django.shortcuts import render, redirect
from django.contrib import messages

API_URL = os.getenv("API_URL") or "http://localhost:8000"

def login_view(request):
    if request.method == "POST":
        correo = request.POST.get("correo")
        password = request.POST.get("password")
        
        try:
            response = requests.post(f"{API_URL}/login", json={"correo": correo, "password": password})
            if response.status_code == 200:
                token_data = response.json()
                request.session["access_token"] = token_data["access_token"]
                messages.success(request, "¡Inicio de sesión exitoso!")
                return redirect("admin_dashboard")
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

def admin_dashboard_view(request):
    token = request.session.get("access_token")
    if not token:
        return redirect("login")
    
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(f"{API_URL}/products/", headers=headers)
        products = response.json() if response.status_code == 200 else []
    except requests.exceptions.ConnectionError:
        products = []
        messages.error(request, "No se pudo conectar con la API de FastAPI.")
        
    return render(request, "store/dashboard.html", {"products": products})

def create_product_view(request):
    token = request.session.get("access_token")
    if not token:
        return redirect("login")
        
    if request.method == "POST":
        product_data = {
            "nombre": request.POST.get("nombre"),
            "descripcion": request.POST.get("descripcion"),
            "precio": float(request.POST.get("precio")),
            "stock": int(request.POST.get("stock", 0))
        }
        
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(f"{API_URL}/products/", json=product_data, headers=headers)
        
        if response.status_code == 201:
            messages.success(request, "¡Producto creado exitosamente!")
        else:
            messages.error(request, "Error al crear el producto.")
            
        return redirect("admin_dashboard")
        
    return render(request, "store/product_form.html")

def update_product_view(request, product_id):
    token = request.session.get("access_token")
    if not token:
        return redirect("login")
        
    headers = {"Authorization": f"Bearer {token}"}
    
    if request.method == "POST":
        product_data = {
            "nombre": request.POST.get("nombre"),
            "descripcion": request.POST.get("descripcion"),
            "precio": float(request.POST.get("precio")),
            "stock": int(request.POST.get("stock", 0))
        }
        
        response = requests.put(f"{API_URL}/products/{product_id}", json=product_data, headers=headers)
        if response.status_code == 200:
            messages.success(request, "¡Producto actualizado correctamente!")
        else:
            messages.error(request, "Error al actualizar el producto.")
        return redirect("admin_dashboard")
        
    response = requests.get(f"{API_URL}/products/{product_id}", headers=headers)
    product = response.json() if response.status_code == 200 else {}
    
    return render(request, "store/product_form.html", {"product": product, "edit_mode": True})

def delete_product_view(request, product_id):
    token = request.session.get("access_token")
    if not token:
        return redirect("login")
        
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.delete(f"{API_URL}/products/{product_id}", headers=headers)
    
    if response.status_code == 204:
        messages.success(request, "Producto eliminado con éxito.")
    else:
        messages.error(request, "No se pudo eliminar el producto.")
        
    return redirect("admin_dashboard")

def logout_view(request):
    request.session.flush()
    return redirect("login")