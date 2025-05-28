from django.urls import path
from . import views

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('pago/', views.pago_view, name='pago'),
    path('carrito/', views.carrito_view, name='carrito'),

    #Usuarios
    path('nuevoUsuario/', views.nuevoUsuario, name='nuevoUsuario'),
    path('listadoUsuario/',views.listadoUsuario, name='listadoUsuario'),
    path('guardarUsuario/',views.guardarUsuario, name='guardarUsuario'),
    path('eliminarUsuario/<id>', views.eliminarUsuario, name='eliminarUsuario'),
    path('editarUsuario/<id>',views.editarUsuario, name='editarUsuario'),
    path('procesarEdicionUsuario/',views.procesarEdicionUsuario, name='procesarEdicionUsuario'),
    #Productos
    path('nuevoProducto/', views.nuevoProducto, name='nuevoProducto'),
    path('listadoProducto/',views.listadoProducto, name='listadoProducto'),
    path('guardarProducto/',views.guardarProducto, name='guardarProducto'),
    path('eliminarProducto/<id_prod>', views.eliminarProducto, name='eliminarProducto'),
    path('editarProducto/<id_prod>',views.editarProducto, name='editarProducto'),
    path('procesarEdicionProducto/',views.procesarEdicionProducto, name='procesarEdicionProducto'),
    
    #Categorias
    path('nuevoCategoria/', views.nuevoCategoria, name='nuevoCategoria'),
    path('listadoCategoria/',views.listadoCategoria, name='listadoCategoria'),
    path('guardarCategoria/',views.guardarCategoria, name='guardarCategoria'),
    path('eliminarCategoria/<id_categoria>', views.eliminarCategoria, name='eliminarCategoria'),
    path('editarCategoria/<id_categoria>',views.editarCategoria, name='editarCategoria'),
    path('procesarEdicionCategoria/',views.procesarEdicionCategoria, name='procesarEdicionCategoria'),
   


]

