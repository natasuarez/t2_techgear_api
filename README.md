# ⚡ TechGear - Sistema de Gestión de Pedidos y Catálogo

TechGear es una aplicación web full-stack orientada al comercio electrónico de calzado deportivo y tecnología. El sistema está desacoplado en una arquitectura moderna que separa la lógica de servicios mediante una API REST de alto rendimiento y una interfaz de cliente interactiva basada en sesiones.

---

## 🚀 Arquitectura y Tecnologías

El proyecto se divide en dos componentes principales:

*   **Backend (API REST):** Desarrollado con **FastAPI**, utilizando **MongoDB** como base de datos NoSQL, validación de esquemas con **Pydantic** y autenticación segura mediante **JWT (JSON Web Tokens)**.
*   **Frontend (Cliente Web):** Desarrollado en **Django**, gestionando el estado mediante cookies de sesión, plantillas HTML semánticas y diseño responsivo optimizado con **Bootstrap 5/6**.

---

## ✨ Características Principales

1.  **Autenticación y Registro Seguros:**
    *   Registro de nuevos usuarios con validación de datos.
    *   Inicio de sesión con emisión de tokens JWT almacenados de forma segura en la sesión de Django.
2.  **Control de Acceso Basado en Roles (RBAC):**
    *   **Administrador:** Acceso exclusivo al Dashboard de gestión (`/dashboard/`) para crear, editar y eliminar productos del catálogo.
    *   **Cliente:** Acceso restringido al catálogo de visualización y al manejo del pedido.
3.  **Gestión de Pedidos y Validación de Stock en Tiempo Real:**
    *   Control dinámico de cantidades (botones de incremento/decremento).
    *   Validación estricta contra el inventario disponible en la base de datos para evitar pedidos que superen el stock.
    *   Selector interactivo de tallas de calzado por producto.
4.  **Optimización y Rendimiento (Lighthouse 100):**
    *   Estructura HTML semántica, atributos ARIA de accesibilidad, metadatos SEO completos y carga diferida de scripts (`defer`).

---

## 🛠️ Estructura del Proyecto

```text
t2_techgear_api/
│
├── techgear_api/              # Backend (FastAPI)
│   ├── main.py                # Endpoints principales y conexión a MongoDB
│   ├── models.py              # Esquemas Pydantic
│   └── requirements.txt       # Dependencias de FastAPI
│
└── techgear_web/              # Frontend (Django)
    ├── store/                 # App de Django (views.py, urls.py)
    ├── templates/store/       # Plantillas HTML (cart.html, dashboard.html, login.html, register.html)
    ├── manage.py              # Administrador de Django
    └── requirements.txt       # Dependencias de Django

link
render: https://t2-techgear-api.onrender.com
vercel: t2-techgear-k3yse9b3f-natasuarezxx-5873s-projects.vercel.app
