from django.contrib import admin
from django.urls import path
from store import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.login_view, name='login'),           # <-- Añade esta línea para la raíz
    path('register/', views.register_view, name='register'),
    path('dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('dashboard/product/add/', views.create_product_view, name='create_product'),
    path('dashboard/product/edit/<str:product_id>/', views.update_product_view, name='update_product'),
    path('dashboard/product/delete/<str:product_id>/', views.delete_product_view, name='delete_product'),
    path('logout/', views.logout_view, name='logout'),
]