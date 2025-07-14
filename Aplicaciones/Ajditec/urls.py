from django.urls import path
from . import views

urlpatterns = [

    path('perfil/', views.perfil_usuario, name='perfil_usuario'),
    path('cambiar_contraseña/', views.cambiar_contraseña, name='cambiar_contraseña'),
    path('', views.inicio, name='inicio'),
   # path('pago/', views.pago_view, name='pago'),
    path('plantilla_admin/', views.plantilla_admin, name='plantilla_admin'),
    path('datosPedido/', views.pago, name='datosPedido'),
    

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

    #INVENTARIO
    path('nuevoInventario/', views.nuevoInventario, name='nuevoInventario'),
    path('guardarInventario/', views.guardarInventario, name='guardarInventario'),
    path('listadoInventario/', views.listadoInventario, name='listadoInventario'),

    #DETALLE_CARRITO
    
    path('add-to-cart/<int:id_prod>/', views.add_to_cart, name='add_to_cart'),
    path('carrito/', views.carrito, name='carrito'),
    path('eliminar-del-carrito/<int:id_prod>/', views.eliminar_del_carrito, name='eliminar_del_carrito'),
    path('actualizar-cantidad/<int:id_prod>/', views.actualizar_cantidad_carrito, name='actualizar_cantidad_carrito'),
    


    
    #LOGIN
    path('login/', views.login_usuario, name='login'),
    path('reporteVentas/', views.reporte_ventas_productos, name='reporte_ventas_productos'),
    path('registro/', views.registrar_cliente, name='registro'),
    path('logout/', views.logout_usuario, name='logout'),
    path('plantilla/', views.admin_dashboard, name='admin_dashboard'),
    path('catalogo/', views.catalogo, name='catalogo'),
    #LISTAR ORDENES
    path('listar_ordenes/', views.listar_ordenes, name='listar_ordenes'),
    #DETALLE DE ORDEN
    path('detalle_orden/<int:id_ord>/', views.detalle_orden, name='detalle_orden'),
    #VISTA RAPIDA
    path('producto/<int:id_prod>/vista-rapida/', views.producto_vista_rapida, name='producto_vista_rapida'),
    #CONFIRMACION DE LA ORDEN
    path('admin_listar_pagos/', views.admin_listar_pagos, name='admin_listar_pagos'),
    path('admin_detalle_pago/<int:id_regpag>/', views.admin_detalle_pago, name='admin_detalle_pago'),
    path('admin_confirmar_pago/<int:id_regpag>/', views.admin_confirmar_pago, name='admin_confirmar_pago'),
    path('admin_rechazar_pago/<int:id_regpag>/', views.admin_rechazar_pago, name='admin_rechazar_pago'),

    #FINAL PEDIDOA
    path('finalPedido/', views.finalPedido, name='finalPedido'),
    path('orden_confirmada/<int:id_ord>/', views.orden_confirmada, name='orden_confirmada'),
    path('procesar_pedido/', views.procesar_pedido, name='procesar_pedido'),
    path('conf_pago/<int:id_ord>/', views.conf_pago, name='conf_pago'),
    #NOTIFICACIONES
    path('verNotificaciones/', views.verNotificaciones, name='verNotificaciones'),
    #BANCO
    path('nuevoBanco/', views.nuevoBanco, name='nuevoBanco'),
    path('guardarBanco/', views.guardarBanco, name='guardarBanco'),
    path('editarBanco/<int:id_banco>/', views.editarBanco, name='editarBanco'),
    path('procesarEdicionBanco/', views.procesarEdicionBanco, name='procesarEdicionBanco'),
    path('eliminarBanco/<int:id_banco>/', views.eliminarBanco, name='eliminarBanco'),
    #MOVIIENTO DE INVENTARIO
    path('nuevoIngreso', views.nuevoIngresoInventario, name='nuevoIngreso'),
    path('listadoMovimiento', views.listadoMovimiento, name='listadoMovimiento'),
    #REPORTES
    path('reporteVentas/', views.reporte_ventas_productos, name='reporteVentas'),
    #IMPUESTO
    path('nuevoImpuesto/', views.nuevoImpuesto, name='nuevoImpuesto'),
    path('guardarImpuesto/', views.guardarImpuesto, name='guardarImpuesto'),
    path('editarImpuesto/<int:id_impuesto>/', views.editarImpuesto, name='editarImpuesto'),
    path('procesarEdicionImpuesto/', views.procesarEdicionImpuesto, name='procesarEdicionImpuesto'),
    path('eliminarImpuesto/<int:id_impuesto>/', views.eliminarImpuesto, name='eliminarImpuesto'),






    
    
    

  


     


]

