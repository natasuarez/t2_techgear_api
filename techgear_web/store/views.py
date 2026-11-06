
import os
import requests

from django.shortcuts import render, redirect
from django.contrib import messages


# ==========================================
# CONFIGURACION
# ==========================================

API_URL = os.getenv(
    "API_URL",
    "https://t2-techgear-api.onrender.com"
).rstrip("/")


# ==========================================
# FUNCIONES AUXILIARES
# ==========================================

def obtener_headers(request):
    token = request.session.get("access_token")

    return {
        "Authorization": f"Bearer {token}"
    } if token else {}


def es_admin(request):
    return (
        request.session.get("access_token")
        and request.session.get("rol") == "admin"
    )


def verificar_admin(request):
    if not request.session.get("access_token"):
        messages.error(request, "Debes iniciar sesión.")
        return False

    if not es_admin(request):
        messages.error(request, "No tienes permisos de administrador.")
        return False

    return True


# ==========================================
# LOGIN
# ==========================================

def login_view(request):

    if request.session.get("access_token"):
        if es_admin(request):
            return redirect("admin_dashboard")

        return redirect("view_cart")

    if request.method == "POST":

        correo = request.POST.get("correo")
        password = request.POST.get("password")

        try:
            response = requests.post(
                f"{API_URL}/login",
                json={
                    "correo": correo,
                    "password": password
                },
                timeout=30
            )

            if response.status_code == 200:

                token_data = response.json()
                request.session["access_token"] = token_data["access_token"]
                request.session["rol"] = token_data.get("rol", "cliente")
                request.session["nombre"] = token_data.get("nombre", "")

                if es_admin(request):
                    messages.success(request, "¡Bienvenido al panel de administración!")
                    return redirect("admin_dashboard")

                messages.success(request, "¡Bienvenido a TechGear!")
                return redirect("view_cart")

            messages.error(request, "Correo o contraseña incorrectos.")

        except requests.exceptions.RequestException:
            messages.error(request, "No se pudo conectar con FastAPI.")

    return render(request, "store/login.html")


# ==========================================
# REGISTRO
# ==========================================

def register_view(request):

    if request.session.get("access_token"):
        return redirect("view_cart")

    if request.method == "POST":

        user_data = {
            "nombre": request.POST.get("nombre"),
            "correo": request.POST.get("correo"),
            "password": request.POST.get("password"),
            "rol": "cliente"
        }

        try:
            response = requests.post(
                f"{API_URL}/users/",
                json=user_data,
                timeout=30
            )

            if response.status_code in [200, 201]:

                messages.success(
                    request,
                    "¡Registro exitoso! Ahora puedes iniciar sesión."
                )

                return redirect("login")

            messages.error(
                request,
                f"Error al registrar: {response.text}"
            )

        except requests.exceptions.RequestException:
            messages.error(request, "No se pudo conectar con FastAPI.")

    return render(request, "store/register.html")


# ==========================================
# PANEL ADMINISTRADOR
# ==========================================

def admin_dashboard_view(request):

    if not verificar_admin(request):
        return redirect("login")

    headers = obtener_headers(request)

    try:
        response = requests.get(
            f"{API_URL}/products/",
            headers=headers,
            timeout=30
        )

        if response.status_code == 200:

            products = response.json()

            for prod in products:
                if "_id" in prod:
                    prod["id"] = str(prod["_id"])

        else:
            products = []
            messages.error(request, "No se pudieron cargar los productos.")

    except requests.exceptions.RequestException:
        products = []
        messages.error(request, "Error de conexión con FastAPI.")

    return render(
        request,
        "store/dashboard.html",
        {"products": products}
    )


# ==========================================
# CREAR PRODUCTO
# ==========================================

def create_product_view(request):

    if not verificar_admin(request):
        return redirect("login")

    if request.method == "POST":

        try:
            product_data = {
                "nombre": request.POST.get("nombre"),
                "descripcion": request.POST.get("descripcion"),
                "precio": float(request.POST.get("precio")),
                "stock": int(request.POST.get("stock", 0))
            }

            response = requests.post(
                f"{API_URL}/products/",
                json=product_data,
                headers=obtener_headers(request),
                timeout=30
            )

            if response.status_code == 201:
                messages.success(request, "¡Producto creado exitosamente!")
            else:
                messages.error(request, f"Error: {response.text}")

        except (ValueError, requests.exceptions.RequestException):
            messages.error(request, "No se pudo crear el producto. Verifica los datos.")

        return redirect("admin_dashboard")

    return render(request, "store/product_form.html")


# ==========================================
# ACTUALIZAR PRODUCTO
# ==========================================

def update_product_view(request, product_id):

    if not verificar_admin(request):
        return redirect("login")

    headers = obtener_headers(request)

    if request.method == "POST":

        try:
            product_data = {
                "nombre": request.POST.get("nombre"),
                "descripcion": request.POST.get("descripcion"),
                "precio": float(request.POST.get("precio")),
                "stock": int(request.POST.get("stock", 0))
            }

            response = requests.put(
                f"{API_URL}/products/{product_id}",
                json=product_data,
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                messages.success(request, "Producto actualizado correctamente.")
            else:
                messages.error(request, f"Error: {response.text}")

        except (ValueError, requests.exceptions.RequestException):
            messages.error(request, "No se pudo actualizar el producto.")

        return redirect("admin_dashboard")

    try:
        response = requests.get(
            f"{API_URL}/products/{product_id}",
            headers=headers,
            timeout=30
        )

        product = response.json() if response.status_code == 200 else {}

    except requests.exceptions.RequestException:
        product = {}
        messages.error(request, "Error al consultar el producto.")

    return render(
        request,
        "store/product_form.html",
        {
            "product": product,
            "edit_mode": True
        }
    )


# ==========================================
# ELIMINAR PRODUCTO
# ==========================================

def delete_product_view(request, product_id):

    if not verificar_admin(request):
        return redirect("login")

    if request.method != "POST":
        return redirect("admin_dashboard")

    try:
        response = requests.delete(
            f"{API_URL}/products/{product_id}",
            headers=obtener_headers(request),
            timeout=30
        )

        if response.status_code == 204:
            messages.success(request, "Producto eliminado correctamente.")
        else:
            messages.error(request, f"No se pudo eliminar: {response.text}")

    except requests.exceptions.RequestException:
        messages.error(request, "Error de conexión con FastAPI.")

    return redirect("admin_dashboard")


# ==========================================
# CERRAR SESION
# ==========================================

def logout_view(request):

    request.session.flush()

    messages.success(request, "Has cerrado sesión correctamente.")

    return redirect("login")


# ==========================================
# AGREGAR AL CARRITO
# ==========================================

def add_to_cart(request, product_id):

    if request.method != "POST":
        return redirect("view_cart")

    if not request.session.get("access_token"):
        messages.error(request, "Inicia sesión para realizar pedidos.")
        return redirect("login")

    if es_admin(request):
        messages.error(request, "El administrador no puede realizar pedidos desde esta cuenta.")
        return redirect("admin_dashboard")

    try:
        response = requests.get(
            f"{API_URL}/products/{product_id}",
            headers=obtener_headers(request),
            timeout=30
        )

        if response.status_code != 200:
            messages.error(request, "No se pudo obtener el producto.")
            return redirect("view_cart")

        product = response.json()

        stock_disponible = int(product.get("stock", 0))

        cart = request.session.get("cart", {})
        product_id_str = str(product_id)

        cantidad_actual = cart.get(
            product_id_str, {}
        ).get("cantidad", 0)

        if cantidad_actual >= stock_disponible:
            messages.error(request, "No hay suficiente stock disponible.")
            return redirect("view_cart")

        if product_id_str in cart:

            cart[product_id_str]["cantidad"] += 1

        else:

            cart[product_id_str] = {
                "nombre": product.get("nombre"),
                "precio": product.get("precio", 0),
                "cantidad": 1,
                "talla": "39",
                "stock": stock_disponible,
                "imagen": product.get("imagen", "")
            }

        request.session["cart"] = cart
        request.session.modified = True

        messages.success(request, "¡Producto agregado al pedido!")

    except requests.exceptions.RequestException:
        messages.error(request, "Error de conexión con FastAPI.")

    return redirect("view_cart")


# ==========================================
# VER CARRITO
# ==========================================

def view_cart(request):

    cart = request.session.get("cart", {})

    total = sum(
        float(item.get("precio", 0)) * int(item.get("cantidad", 0))
        for item in cart.values()
    )

    productos = []

    try:
        respuesta = requests.get(
            f"{API_URL}/products/",
            timeout=15
        )

        if respuesta.status_code == 200:
            productos = respuesta.json()

    except requests.RequestException:
        messages.error(request, "No se pudieron cargar los productos.")

    return render(
        request,
        "store/cart.html",
        {
            "cart": cart,
            "total": total,
            "productos": productos
        }
    )


# ==========================================
# AUMENTAR CANTIDAD
# ==========================================

def increase_cart_quantity(request, product_id):

    cart = request.session.get("cart", {})
    product_id_str = str(product_id)

    if product_id_str in cart:

        item = cart[product_id_str]

        cantidad_actual = int(item.get("cantidad", 1))
        stock_maximo = int(item.get("stock", 10))

        if cantidad_actual < stock_maximo:

            cart[product_id_str]["cantidad"] += 1

            request.session["cart"] = cart
            request.session.modified = True

            messages.success(request, "Cantidad aumentada.")

        else:
            messages.error(request, "No hay más unidades disponibles.")

    return redirect("view_cart")


# ==========================================
# DISMINUIR CANTIDAD
# ==========================================

def decrease_cart_quantity(request, product_id):

    cart = request.session.get("cart", {})
    product_id_str = str(product_id)

    if product_id_str in cart:

        actual = int(cart[product_id_str]["cantidad"])

        if actual > 1:
            cart[product_id_str]["cantidad"] = actual - 1
        else:
            del cart[product_id_str]

        request.session["cart"] = cart
        request.session.modified = True

    return redirect("view_cart")


# ==========================================
# ACTUALIZAR TALLA
# ==========================================

def update_cart_size(request, product_id):

    if request.method == "POST":

        nueva_talla = request.POST.get("talla")

        cart = request.session.get("cart", {})
        product_id_str = str(product_id)

        if product_id_str in cart and nueva_talla:

            cart[product_id_str]["talla"] = nueva_talla

            request.session["cart"] = cart
            request.session.modified = True

            messages.success(request, "Talla actualizada.")

    return redirect("view_cart")


# ==========================================
# ELIMINAR DEL CARRITO
# ==========================================

def remove_from_cart(request, product_id):

    cart = request.session.get("cart", {})
    product_id_str = str(product_id)

    if product_id_str in cart:

        del cart[product_id_str]

        request.session["cart"] = cart
        request.session.modified = True

        messages.success(request, "Producto eliminado del pedido.")

    return redirect("view_cart")


# ==========================================
# PEDIDOS DEL CLIENTE
# ==========================================

def client_orders_view(request):

    if not request.session.get("access_token"):
        return redirect("login")

    if es_admin(request):
        return redirect("admin_orders")

    try:
        response = requests.get(
            f"{API_URL}/orders/",
            headers=obtener_headers(request),
            timeout=30
        )

        if response.status_code == 200:
            orders = response.json()
        else:
            orders = []
            messages.error(request, "No se pudieron consultar tus pedidos.")

    except requests.exceptions.RequestException:
        orders = []
        messages.error(request, "Error de conexión con FastAPI.")

    return render(
        request,
        "store/orders_client.html",
        {"orders": orders}
    )


# ==========================================
# PEDIDOS DEL ADMINISTRADOR
# ==========================================

def admin_orders_view(request):

    if not verificar_admin(request):
        return redirect("login")

    try:
        response = requests.get(
            f"{API_URL}/orders/",
            headers=obtener_headers(request),
            timeout=30
        )

        if response.status_code == 200:
            orders = response.json()
        else:
            orders = []
            messages.error(request, "No se pudieron consultar los pedidos.")

    except requests.exceptions.RequestException:
        orders = []
        messages.error(request, "Error de conexión con FastAPI.")

    return render(
        request,
        "store/orders_admin.html",
        {"orders": orders}
    )


# ==========================================
# APROBAR PEDIDO
# ==========================================

def approve_order_view(request, order_id):

    if request.method != "POST":
        return redirect("admin_orders")

    if not verificar_admin(request):
        return redirect("login")

    try:
        response = requests.put(
            f"{API_URL}/orders/{order_id}/approve",
            headers=obtener_headers(request),
            timeout=30
        )

        if response.status_code == 200:
            messages.success(request, "Pedido aprobado correctamente.")
        else:
            messages.error(request, f"Error: {response.text}")

    except requests.exceptions.RequestException:
        messages.error(request, "Error de conexión con FastAPI.")

    return redirect("admin_orders")


# ==========================================
# RECHAZAR PEDIDO
# ==========================================

def reject_order_view(request, order_id):

    if request.method != "POST":
        return redirect("admin_orders")

    if not verificar_admin(request):
        return redirect("login")

    try:
        response = requests.put(
            f"{API_URL}/orders/{order_id}/reject",
            headers=obtener_headers(request),
            timeout=30
        )

        if response.status_code == 200:
            messages.success(request, "Pedido rechazado correctamente.")
        else:
            messages.error(request, f"Error: {response.text}")

    except requests.exceptions.RequestException:
        messages.error(request, "Error de conexión con FastAPI.")

    return redirect("admin_orders")
