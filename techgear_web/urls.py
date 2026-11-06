from django.urls import path
from store import views

urlpatterns = [
    path('', views.view_cart, name='view_cart'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('logout/', views.logout_view, name='logout'),
    
    path('product/create/', views.create_product_view, name='create_product'),
    path('product/update/<str:product_id>/', views.update_product_view, name='update_product'),
    path('product/delete/<str:product_id>/', views.delete_product_view, name='delete_product'),
    
    path('cart/add/<str:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/increase/<str:product_id>/', views.increase_cart_quantity, name='increase_quantity'),
    path('cart/decrease/<str:product_id>/', views.decrease_cart_quantity, name='decrease_quantity'),
    path('cart/update-size/<str:product_id>/', views.update_cart_size, name='update_cart_size'),
    path('cart/remove/<str:product_id>/', views.remove_from_cart, name='remove_from_cart'),
]