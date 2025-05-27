from django.urls import path
from . import views

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('pago/', views.pago_view, name='pago'),
    path('carrito/', views.carrito_view, name='carrito'),
    
    #Productos
    path('nuevoProducto/', views.nuevoProducto, name='nuevoProducto'),
    
    #Categorias
    path('nuevoCategoria/', views.nuevoCategoria, name='nuevoCategoria'),
    path('listadoCategoria/',views.listadoCategoria, name='listadoCategoria'),
    path('guardarCategoria/',views.guardarCategoria, name='guardarCategoria'),
    path('eliminarCategoria/<id_categoria>', views.eliminarCategoria, name='eliminarCategoria'),
    path('editarCategoria/<id_categoria>',views.editarCategoria, name='editarCategoria'),
    path('procesarEdicionCategoria/',views.procesarEdicionCategoria, name='procesarEdicionCategoria'),
    path('ver-bd/', views.mostrar_base_datos),

]

