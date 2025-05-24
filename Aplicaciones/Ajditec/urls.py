from django.urls import path
from . import views

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('pago/', views.pago_view, name='pago'),
    path('carrito/', views.carrito_view, name='carrito'),
    
    #Productos
    path('nuevoProducto/', views.nuevoProducto, name='nuevoProducto'),
    
    #Categorias
    path('nuevoCategoria/', views.nuevoCategoria, name='nuevoCategoria')
]

