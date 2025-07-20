from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
from django.http import HttpResponseForbidden
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from .models import *

def principal(request):
    # Obtener los productos más recientes (8 productos)
    productos_destacados = Producto.objects.all().order_by('-fechcreac_prod')[:4]
    
    # Obtener todas las categorías para la barra de búsqueda
    categorias = Categoria.objects.all()
    
    context = {
        'productos_destacados': productos_destacados,
        'categorias': categorias,
    }
    return render(request, 'principal.html', context)

def is_admin(user):
    """Verifica si el usuario es administrador"""
    return user.is_authenticated and user.tipo_usuario == 'admin'

# Decorador personalizado para vistas que requieren ser admin
def admin_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not is_admin(request.user):
            messages.error(request, 'Solo los administradores pueden acceder a este panel.')
            return redirect('inicio')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@login_required(login_url='login')
@admin_required
def plantilla_admin(request):
    return render(request, 'plantilla_admin.html')
#CARRITO ACTIVO Y PROCESO DE DATOS PARA ORDEN 
@login_required(login_url='login')
def finalPedido(request):
    # Buscar carrito actual
    carrito_id = request.session.get('carrito_id')
    carrito = None

    if carrito_id:
        carrito = Carrito.objects.filter(
            id_carr=carrito_id,
            usuarios=request.user
        ).first()
    if not carrito:
        # Si no hay en sesión, buscar el más reciente de 48 horas
        tiempo_limite = timezone.now() - timedelta(hours=48)
        carrito = Carrito.objects.filter(
            usuarios=request.user,
            fechacreac_carr__gte=tiempo_limite
        ).first()

    if not carrito:
        messages.error(request, "No se encontró ningún carrito activo. Agregue productos primero.")
        return redirect('carrito')

    # Guardar en sesión por consistencia
    request.session['carrito_id'] = carrito.id_carr

    # Obtener items del carrito
    cart_items = [
        {
            'product': detalle.producto,
            'quantity': detalle.cantidad,
            'total_price': detalle.subtotal
        }
        for detalle in carrito.detalles.select_related('producto', 'producto__inventario').all()
    ]
    cart_total = sum(item['total_price'] for item in cart_items)

    # Calcular impuesto
    impuesto_activo = Impuesto.objects.filter(estado=True).first()
    iva_valor = Decimal(impuesto_activo.valor) if impuesto_activo else Decimal('0')
    impuesto = cart_total * (iva_valor / Decimal('100'))
    total_con_impuesto = cart_total + impuesto

    

    # Datos cliente
    datos_cliente = request.session.get('datos_cliente', {})
    bancos = Banco.objects.filter(activo=True)

    return render(request, 'finalPedido.html', {
        'cart_items': cart_items,
        'cart_total': cart_total,
        'impuesto': impuesto,
        'total_con_impuesto': total_con_impuesto,
        'datos_cliente': datos_cliente,
        'carrito': carrito,
        'bancos': bancos,
        'iva_valor': iva_valor
    })


#HISTORIAL DE ORDENES USUARIO 
from django.core.exceptions import ObjectDoesNotExist

@login_required
@user_passes_test(lambda u: u.tipo_usuario == 'cliente', login_url='login')
def listar_ordenes(request):
    ordenes = Orden.objects.filter(usuarios=request.user).order_by('-fechacrea_ord')

    # Intentamos obtener el registro_pago para cada orden, y manejamos la excepción si no existe
    for orden in ordenes:
        try:
            # Intentamos obtener el RegistroPago correspondiente
            orden.registro_pago = RegistroPago.objects.get(orden=orden)
        except ObjectDoesNotExist:
            # Si no existe el RegistroPago, lo seteamos como None
            orden.registro_pago = None

    return render(request, 'listar_ordenes.html', {
        'ordenes': ordenes
    })

from decimal import Decimal

@login_required
@user_passes_test(lambda u: u.tipo_usuario == 'cliente', login_url='login')
def detalle_orden(request, id_ord):
    orden = get_object_or_404(Orden, id_ord=id_ord, usuarios=request.user)
    detalles = orden.detalles.all()

    subtotal = Decimal('0.00')
    total_iva = Decimal('0.00')

    for det in detalles:
        precio = det.precio_aplicado if det.precio_aplicado else Decimal('0.00')
        iva = det.iva_aplicado if det.iva_aplicado else Decimal('0.00')
        cantidad = det.cantidad if det.cantidad else 0

        subtotal += precio * cantidad
        total_iva += (precio * (iva / Decimal('100'))) * cantidad

    total_con_impuesto = subtotal + total_iva

    try:
        registro_pago = RegistroPago.objects.get(orden=orden)
    except ObjectDoesNotExist:
        registro_pago = None

    return render(request, 'detalle_orden.html', {
        'orden': orden,
        'detalles': detalles,
        'subtotal': subtotal,
        'iva_valor': None,  # ya no es un solo iva general, cada detalle tiene su iva
        'impuesto_total': total_iva,
        'total_con_impuesto': total_con_impuesto,
        'registro_pago': registro_pago,
    })

#CREAR ORDEN DE MI FINALPEDIDO
from django.utils import timezone
from datetime import timedelta

@login_required(login_url='login')
def procesar_pedido(request):
    if request.method == 'POST':
        metodo_entrega = request.POST.get('metodo_entrega')
        metodo_pago = request.POST.get('metodo_pago')
        num_transferencia = request.POST.get('num_transferencia')
        fecha_transferencia = request.POST.get('fecha_transferencia')
        banco_id = request.POST.get('banco_id')

        if not metodo_entrega or not metodo_pago:
            messages.error(request, "Seleccione un método de entrega y pago.")
            return redirect('finalPedido')

        carrito_id = request.session.get('carrito_id')
        if not carrito_id:
            messages.error(request, "No hay carrito activo.")
            return redirect('carrito')

        carrito = get_object_or_404(Carrito, id_carr=carrito_id)
        datos_cliente = request.session.get('datos_cliente', {})
        if not datos_cliente:
            messages.error(request, "Complete primero sus datos.")
            return redirect('pago')

        cart_total = carrito.total_carrito()
        impuesto_activo = Impuesto.objects.filter(estado=True).first()
        iva_valor = Decimal(impuesto_activo.valor) if impuesto_activo else Decimal('0')
        impuesto = cart_total * (iva_valor / Decimal('100'))
        total_con_impuesto = cart_total + impuesto

        if metodo_pago == 'transferencia':
            if not num_transferencia:
                messages.error(request, "Ingrese el número de transferencia.")
                return redirect('finalPedido')

            if Orden.objects.filter(num_trans=num_transferencia).exists():
                context = {
                    'error_num_transferencia': "Este número de transferencia ya fue registrado.",
                    'num_transferencia': num_transferencia,
                    'fecha_transferencia': fecha_transferencia,
                    'banco_id': banco_id,
                    'bancos':Banco.objects.filter(activo=True),
                    'cart_total': cart_total,
                    'impuesto': impuesto,
                    'total_con_impuesto': total_con_impuesto,
                    'iva_valor': iva_valor,
                    'carrito': carrito,
                    'datos_cliente': datos_cliente,
                }
                return render(request, 'finalPedido.html', context)

        orden = Orden.objects.create(
            nombre_cliente=datos_cliente.get('nombre', ''),
            tipo_documento=datos_cliente.get('tipo_documento', 'cedula'),
            numero_documento=datos_cliente.get('numero_documento', ''),
            correo_cliente=datos_cliente.get('email', ''),
            direccion_cliente=datos_cliente.get('direccion', ''),
            ciudad_cliente=datos_cliente.get('ciudad', ''),
            telefono_cliente=datos_cliente.get('telefono', ''),
            direc_entre=datos_cliente.get('direccion', ''),
            metodo_entrega=metodo_entrega,
            metodo_pago=metodo_pago,
            num_trans=num_transferencia,
            fecha_trans=fecha_transferencia,
            banco=Banco.objects.get(id_banco=banco_id) if banco_id else None,
            estado_ord='Pendiente',
            usuarios=request.user,
            carrito=carrito,
            fecha_expira=timezone.now() + timedelta(hours=48)
        )

        for detalle in carrito.detalles.all():
            inventario = detalle.producto.inventario
            if inventario.stock_actual >= detalle.cantidad:
                DetalleOrden.objects.create(
                    orden=orden,
                    producto=detalle.producto,
                    cantidad=detalle.cantidad,
                    precio_aplicado=inventario.precunit_prod,
                    iva_aplicado=iva_valor
                )
                inventario.stock_actual -= detalle.cantidad
                inventario.save()
            else:
                messages.error(request, f"No hay stock suficiente para {detalle.producto.nomb_prod}.")
                return redirect('carrito')

        RegistroPago.objects.create(
            orden=orden,
            total_pago=total_con_impuesto,
            estado_reg='Pendiente'
        )

        carrito.estado_carr = 'pagado'
        carrito.save()
        carrito.detalles.all().delete()

        for admin in Usuario.objects.filter(tipo_usuario='admin'):
            Notificacion.objects.create(
                titulo=f"Nueva Orden #{orden.id_ord} de {orden.nombre_cliente}",
                mensaje=f"El cliente {orden.nombre_cliente} ha realizado la orden #{orden.id_ord}.",
                usuario_destino=admin
            )

        if 'carrito_id' in request.session:
            del request.session['carrito_id']

        messages.success(request, f"¡Orden #{orden.id_ord} creada exitosamente! Está pendiente de confirmación.")
        return redirect('orden_confirmada', id_ord=orden.id_ord)

    return redirect('finalPedido')

#DETALLE DE LA ORDEN
def conf_pago(request, id_ord):
    """Muestra la confirmación de pago"""
    print("Entrando a conf_pago con orden_id:", id_ord)
    orden = get_object_or_404(Orden, id_ord=id_ord)
    detalles = DetalleOrden.objects.filter(orden=orden)
    registro_pago = RegistroPago.objects.get(orden=orden)
    print("Orden encontrada:", orden)
    print("Detalles de la orden:", detalles)
    print("Registro de pago:", registro_pago)
    
    return render(request, 'conf_pago.html', {
        'orden': orden,
        'detalles': detalles,
        'registro_pago': registro_pago,
        'detalles_orden': detalles,
        'total': registro_pago.total_pago,
        'metodo_pago': orden.metodo_pago,
        'Banco': f"{orden.banco.nombre_banco} - {orden.banco.numero_cuenta}" if orden.banco else 'No especificado'

    })

from django.utils import timezone

def inicio(request):
    buscar = request.GET.get('buscar', '')
    categoria_id = request.GET.get('categoria', '')
    marca = request.GET.get('marca', '')  # Obtener filtro por marca

    productos = Producto.objects.filter(borrado_prod=False).select_related('id_cat', 'inventario')

    if categoria_id:
        productos = productos.filter(id_cat__id_cat=categoria_id)

    if marca:
        productos = productos.filter(marca__iexact=marca)  # Filtra productos con marca exacta, no case sensitive

    if buscar:
        productos = productos.filter(nomb_prod__icontains=buscar)

    categorias = Categoria.objects.all()

    # Obtener las marcas únicas de los productos
    marcas = Producto.objects.values_list('marca', flat=True).distinct()

    hoy = timezone.now()
    productos_recientes = Producto.objects.filter(
        borrado_prod=False,
        fechcreac_prod__year=hoy.year,
        fechcreac_prod__month=hoy.month
    ).order_by('-fechcreac_prod')

    return render(request, 'inicio.html', {
        'productos': productos,
        'productos_recientes': productos_recientes,
        'categorias': categorias,
        'marcas': marcas,          # Paso la lista de marcas
        'buscar': buscar,
        'categoria_id': categoria_id,
        'marca': marca,            # Paso la marca seleccionada
    })
#carriito

def vista_pago(request):
    if not request.user.is_authenticated:
        return redirect('login')

    # Obtener el carrito más reciente del usuario
    tiempo_limite = timezone.now() - timedelta(hours=48)
    carrito = Carrito.objects.filter(
        usuarios=request.user,
        fechacreac_carr__gte=tiempo_limite
    ).first()

    if not carrito:
        messages.error(request, "No se encontró ningún carrito activo. Por favor, agregue productos al carrito primero.")
        return redirect('carrito')

    # Guardar el ID del carrito en la sesión para mantener la consistencia
    request.session['carrito_id'] = carrito.id_carr
    print(f"Guardando carrito_id en sesión: {carrito.id_carr}")

    # Obtener los detalles del carrito
    cart_items_qs = carrito.detalles.all()
    cart_items = [
        {
            'product': detalle.producto,
            'quantity': detalle.cantidad,
            'total_price': detalle.subtotal
        }
        for detalle in cart_items_qs
    ]

    # Calcular el total del carrito
    cart_total = sum(detalle.subtotal for detalle in cart_items_qs)

    print("Productos en carrito (vista_pago):", cart_items)  # Verifica los productos

    # Verificar si hay datos del cliente en la sesión y prellenar el formulario
    datos_cliente = request.session.get('datos_cliente', {})

    context = {
        'cart_items': cart_items,
        'cart_total': cart_total,
        'carrito': carrito,
        'datos_cliente': datos_cliente
    }
    return render(request, 'pago.html', context)


#Usuarios
@login_required(login_url='login')
@admin_required
def nuevoUsuario(request):
    usuario = Usuario.objects.all()
    return render (request, 'admin/usuarios/nuevoUsuario.html',{
        'usuario':usuario
    })

@login_required(login_url='login')
@admin_required
def listadoUsuario(request):
    # Filtrar usuarios con rol de cliente
    usuarioBdd = Usuario.objects.filter(tipo_usuario='cliente')
    return render(request, 'admin/usuarios/listadoUsuario.html', 
                  {'usuario':usuarioBdd})

@login_required(login_url='login')
@admin_required
def guardarUsuario(request):
    username = request.POST['nomb_usu']
    first_name = request.POST['primer_nom']
    last_name= request.POST['primer_apell']
    email= request.POST['email_usu']
    cel_user= request.POST['telf_usu']
    password= request.POST['contra_usu']

    nuevoUsuario = Usuario.objects.create(
        username = username,
        first_name= first_name,
        last_name = last_name,
        email = email,
        cel_user = cel_user,
        password = password
    )

    messages.success(request,"Se ha guardado el usuario")
    return redirect ('/inicio')

@login_required(login_url='login')
@admin_required
def eliminarUsuario(request, id):
    usuarioELiminar = get_object_or_404(Usuario, id=id)
    usuarioELiminar.delete()
    messages.success(request,"Usuario Eliminado con exito")
    return redirect('/listadoUsuario')

@login_required(login_url='login')
@admin_required
def editarUsuario(request, id):
    usuarioEditar = Usuario.objects.get(id = id)
    return render(request,'admin/usuarios/editarUsuario.html', {'usuario':usuarioEditar })

@login_required(login_url='login')
@admin_required
def procesarEdicionUsuario(request):
    usuario=Usuario.objects.get(id = request.POST['id_usuario'])
    usuario.username=request.POST['nomb_usu']
    usuario.first_name=request.POST['primer_nom']
    usuario.last_name=request.POST['primer_apell']
    usuario.email=request.POST['email_usu']
    usuario.cel_user=request.POST['telf_usu']
    usuario.password=request.POST['contra_usu']

    usuario.save()
    messages.success(request,"Usuario actualizado con exito")
    return redirect('admin/usuarios/listadoUsuario')
#BANCO 
@login_required(login_url='login')
@admin_required
def nuevoBanco(request):
    bancos = Banco.objects.all()
    return render(request, 'admin/banco/nuevoBanco.html', {
        'bancos': bancos
    })

# Vista opcional si separas el listado
def listadoBanco(request):
    bancos = Banco.objects.all()
    return render(request, 'admin/banco/listadoBanco.html', {
        'bancos': bancos
    })

# Guardar nuevo banco
@login_required(login_url='login')
@admin_required
def guardarBanco(request):
    if request.method == 'POST':
        nombre_banco = request.POST.get('nombre_banco', '').strip().upper()
        numero_cuenta = request.POST.get('numero_cuenta', '').strip()
        tipo_cuenta = request.POST.get('tipo_cuenta')
        nombre_titular = request.POST.get('nombre_titular', '').strip()
        identificacion_titular = request.POST.get('identificacion_titular', '').strip()
        activo = True if request.POST.get('activo') == 'on' else False

        # Validar si ya existe un banco con mismo nombre y número de cuenta
        if Banco.objects.filter(nombre_banco__iexact=nombre_banco, numero_cuenta=numero_cuenta).exists():
            messages.error(request, f"Ya existe un banco con ese nombre y número de cuenta.")
            return redirect('/nuevoBanco')

        Banco.objects.create(
            nombre_banco=nombre_banco,
            numero_cuenta=numero_cuenta,
            tipo_cuenta=tipo_cuenta,
            nombre_titular=nombre_titular,
            identificacion_titular=identificacion_titular,
            activo=activo
        )
        messages.success(request, "Banco registrado correctamente.")
        return redirect('/nuevoBanco')

# Eliminar banco
@login_required(login_url='login')
@admin_required
def eliminarBanco(request, id_banco):
    bancoEliminar = get_object_or_404(Banco, id_banco=id_banco)
    bancoEliminar.delete()
    messages.success(request, "Banco eliminado correctamente.")
    return redirect('/nuevoBanco')

# Mostrar formulario de edición
@login_required(login_url='login')
@admin_required
def editarBanco(request, id_banco):
    bancoEditar = get_object_or_404(Banco, id_banco=id_banco)
    return render(request, 'admin/banco/editarBanco.html', {'banco': bancoEditar})

# Procesar edición
@login_required(login_url='login')
@admin_required
def procesarEdicionBanco(request):
    banco = get_object_or_404(Banco, id_banco=request.POST['id_banco'])

    banco.nombre_banco = request.POST['nombre_banco'].strip().upper()
    banco.numero_cuenta = request.POST['numero_cuenta'].strip()
    banco.tipo_cuenta = request.POST['tipo_cuenta']
    banco.nombre_titular = request.POST['nombre_titular'].strip()
    banco.identificacion_titular = request.POST['identificacion_titular'].strip()
    banco.activo = True if request.POST.get('activo') == 'on' else False

    banco.save()
    messages.success(request, "Banco actualizado correctamente.")
    return redirect('/nuevoBanco')
#Categoria 
@login_required(login_url='login')
@admin_required
def nuevoCategoria(request):
    categoria = Categoria.objects.all()
    return render (request, 'admin/categoria/nuevoCategoria.html',{
        'categoria':categoria
    })

@login_required(login_url='login')
@admin_required
def listadoCategoria(request):
    categoriaBdd = Categoria.objects.all()
    return render(request, 'admin/categoria/listadoCategoria.html', 
                  {'categoria':categoriaBdd})

@login_required(login_url='login')
@admin_required
def guardarCategoria(request):
    if request.method == 'POST':
        tipo_cat = request.POST.get('tipo_cat', '').strip().upper()  # quitar espacios y convertir a mayúsculas

        # Verificar si la categoría ya existe sin importar mayúsculas/minúsculas
        if Categoria.objects.filter(tipo_cat__iexact=tipo_cat).exists():
            messages.error(request, f"La categoría '{tipo_cat}' ya existe.")
            return redirect('/nuevoCategoria')

        # Si no existe, crearla
        Categoria.objects.create(tipo_cat=tipo_cat)
        messages.success(request, f"Categoría '{tipo_cat}' guardada exitosamente.")
        return redirect('/nuevoCategoria')

@login_required(login_url='login')
@admin_required
def eliminarCategoria(request, id_categoria):
    categoriaELiminar = get_object_or_404(Categoria, id_cat=id_categoria)
    categoriaELiminar.delete()
    messages.success(request,"Categoria Eliminada")
    return redirect('nuevoCategoria')

@login_required(login_url='login')
@admin_required
def editarCategoria(request, id_categoria):
    categoriaEditar = Categoria.objects.get(id_cat = id_categoria)
    return render(request,'admin/categoria/editarCategoria.html', {'categoria':categoriaEditar })

@login_required(login_url='login')
@admin_required
def procesarEdicionCategoria(request):
    categoria=Categoria.objects.get(id_cat = request.POST['id_cat'])
    categoria.tipo_cat=request.POST['tipo_cat']

    categoria.save()
    messages.success(request,"Categoria actualizada con exito")
    return redirect('/nuevoCategoria')
#PRODUCTOS
@login_required(login_url='login')
@admin_required
def nuevoProducto(request):
    categorias = Categoria.objects.all()
    return render(request, 'admin/producto/nuevoProducto.html', {
        'categoria': categorias
    })

@login_required(login_url='login')
@admin_required
def listadoProducto(request):
    productos = Producto.objects.filter(borrado_prod=False)
    return render(request, 'admin/producto/listadoProducto.html', {
        'producto': productos
    })

@login_required(login_url='login')
@admin_required
def guardarProducto(request):
    if request.method == 'POST':
        nomb = request.POST['nomb_prod']
        descr = request.POST['descrip_prod']
        marca = request.POST['marca_prod']
        img = request.FILES.get('foto_prod')
        id_categoria = request.POST['id_cat']

        id_cat= Categoria.objects.get(id_cat=id_categoria)

        Producto.objects.create(
            nomb_prod=nomb,
            descrip_prod=descr,
            marca=marca,
            img_prod=img,
            id_cat=id_cat
        )

        messages.success(request, "Producto guardado correctamente.")
        return redirect('/listadoProducto')

@login_required(login_url='login')
@admin_required
def eliminarProducto(request, id_prod):
    producto_eliminar = get_object_or_404(Producto, id_prod=id_prod)
    producto_eliminar.borrado_prod = True  # borrado lógico
    producto_eliminar.save()
    messages.success(request, "Producto eliminado")
    return redirect('/listadoProducto')

@login_required(login_url='login')
@admin_required
def editarProducto(request, id_prod):
    producto_editar = get_object_or_404(Producto, id_prod=id_prod)
    id_cat = Categoria.objects.all()
    return render(request, 'admin/producto/editarProducto.html', {
        'producto': producto_editar,
        'id_cat': id_cat
    })

@login_required(login_url='login')
@admin_required
def procesarEdicionProducto(request):
    if request.method == 'POST':
        producto = get_object_or_404(Producto, id_prod=request.POST['id_prod'])

        producto.nomb_prod = request.POST['nomb_prod']
        producto.descrip_prod = request.POST['descrip_prod']
        producto.marca = request.POST['marca_prod']
        id_cat = request.POST['id_cat']
        producto.id_cat = get_object_or_404(Categoria, id_cat=id_cat)

        # Si suben una nueva imagen, actualizarla
        if 'foto_prod' in request.FILES:
            producto.img_prod = request.FILES['foto_prod']

        producto.save()
        messages.success(request, "Producto actualizado con éxito")
        return redirect('/listadoProducto')
    else:
        messages.error(request, "Error en el envío del formulario")
        return redirect('/listadoProducto')
#FILTRADO POR CATEGORIA
def tienda(request):
    query = request.GET.get('query', '')
    categoria_id = request.GET.get('categoria')

    productos = Producto.objects.all()

    if query:
        productos = productos.filter(nombre_prod__icontains=query)

    if categoria_id:
        productos = productos.filter(id_cat=categoria_id)

    categorias = Categoria.objects.all()

    return render(request, 'tienda.html', {
        'productos': productos,
        'categorias': categorias,
        'query': query,
        'categoria_seleccionada': categoria_id
    })
#INVENTARIO
@login_required(login_url='login')
@admin_required
def nuevoInventario(request):
    productos = Producto.objects.filter(borrado_prod=False)  # solo productos activos
    return render(request, 'admin/inventario/nuevoInventario.html', {
        'productos': productos
    })

@login_required(login_url='login')
@admin_required
def guardarInventario(request):
    if request.method == 'POST':
        producto_id = request.POST.get('producto')
        precio_str = request.POST.get('precunit_prod')
        stock_str = request.POST.get('stock_actual')

        # Validar que todos los campos estén completos
        if not producto_id or not precio_str or not stock_str:
            messages.error(request, 'Todos los campos son obligatorios.')
            return redirect('nuevoInventario')

        producto = get_object_or_404(Producto, id_prod=producto_id)

        # Intentar convertir el precio y el stock a valores numéricos
        try:
            precunit = float(precio_str)
            stock_inicial = int(stock_str)
        except ValueError:
            messages.error(request, 'Precio unitario o stock inválido.')
            return redirect('nuevoInventario')

        # Verificar si ya existe un inventario para este producto
        if Inventario.objects.filter(producto=producto).exists():
            messages.error(request, f"El producto {producto.nomb_prod} ya tiene un inventario registrado.")
            return redirect('nuevoInventario')

        # Crear un nuevo inventario si no existe
        inventario = Inventario.objects.create(
            producto=producto,
            precunit_prod=precunit,
            stock_actual=stock_inicial
        )

        # Registrar el movimiento de entrada en inventario
        MovimientoInventario.objects.create(
            tipo='Entrada',  # Tipo de movimiento: Entrada
            cantidad=stock_inicial,
            precio_uni=precunit,
            producto=producto,
            observacion='Primer ingreso al inventario'
        )

        # Mensaje de éxito
        messages.success(request, f'Inventario para "{producto.nomb_prod}" creado correctamente con un stock inicial de {stock_inicial}.')
        return redirect('listadoInventario')

#LISTADO INVENTARIO 
@login_required(login_url='login')
@admin_required
@login_required(login_url='login')
@admin_required
def listadoInventario(request):
    # Obtener todos los productos e inventarios asociados
    inventarios = Inventario.objects.select_related('producto').all()

    # Filtrar productos con stock bajo
    productos_bajos_stock = [inventario for inventario in inventarios if inventario.stock_actual <= 3]

    # Pasar los inventarios y productos con stock bajo al template
    return render(request, 'admin/inventario/listadoInventario.html', {
        'inventarios': inventarios,
        'productos_bajos_stock': productos_bajos_stock,  # Para alertar sobre productos con stock bajo
    })

@login_required(login_url='login')
@admin_required
def eliminarInventario(request, id_inv):
    try:
        inventario = Inventario.objects.get(id_inve=id_inv)
        producto_nombre = inventario.producto.nomb_prod  # Para mostrar en mensaje
        inventario.delete()
        messages.success(request, f'Inventario del producto "{producto_nombre}" eliminado correctamente.')
    except Inventario.DoesNotExist:
        messages.error(request, 'Inventario no encontrado.')
    return redirect('listadoInventario')


# LOGIN
# views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import PerfilUsuarioForm
from .models import Usuario

@login_required
def perfil_usuario(request):
    user = request.user
    if request.method == 'POST':
        form = PerfilUsuarioForm(request.POST, instance=user)
        if form.is_valid():
            try:
                # Guardar los cambios en el usuario
                user = form.save()
                # Actualizar la sesión para reflejar los cambios
                request.session['user_first_name'] = user.first_name
                request.session['user_last_name'] = user.last_name
                request.session['user_email'] = user.email
                request.session['user_tipo_usuario'] = user.tipo_usuario
                messages.success(request, 'Perfil actualizado exitosamente')
                return redirect('perfil_usuario')
            except Exception as e:
                messages.error(request, f'Error al actualizar el perfil: {str(e)}')
                return redirect('perfil_usuario')
    else:
        form = PerfilUsuarioForm(instance=user)
    return render(request, 'admin/perfil_usuario.html', {
        'perfil_form': form,
        'user': user
    })

@login_required
def cambiar_contraseña(request):
    user = request.user
    perfil_form = PerfilUsuarioForm(instance=user)
    
    if request.method == 'POST':
        password_form = PasswordChangeForm(request.user, request.POST)
        if password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)  # Actualiza la sesión del usuario
            messages.success(request, 'Contraseña cambiada exitosamente')
            return redirect('perfil_usuario')
        else:
            # Mostrar mensajes de error específicos
            if 'old_password' in password_form.errors:
                messages.error(request, 'La contraseña actual es incorrecta.')
            if 'new_password1' in password_form.errors:
                messages.error(request, 'La nueva contraseña no cumple con los requisitos.')
            if 'new_password2' in password_form.errors:
                messages.error(request, 'Las contraseñas no coinciden.')
    else:
        password_form = PasswordChangeForm(request.user)
    
    return render(request, 'admin/perfil_usuario.html', {
        'perfil_form': perfil_form,
        'password_form': password_form,
        'cambiar_contraseña': True
    })

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .forms import FormRegistroCliente, FormLogin
from .models import Usuario

def registrar_cliente(request):
    if request.method == 'POST':
        form = FormRegistroCliente(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            if Usuario.objects.filter(email=email).exists():
                form.add_error('email', 'Ya existe un usuario con ese correo.')
            else:
                user = form.save(commit=False)
                user.tipo_usuario = 'cliente'
                user.set_password(form.cleaned_data['password1'])  # Asegúrate de usar set_password si tienes password
                user.save()
                messages.success(request, 'Registro exitoso. Ahora puede iniciar sesión.')
                return redirect('login')
    else:
        form = FormRegistroCliente()
    return render(request, 'registro.html', {'form': form})


def login_usuario(request):
    if request.method == 'POST':
        form = FormLogin(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            if user.tipo_usuario == 'admin':
                return redirect('dashboard')
            elif user.tipo_usuario == 'cliente':
                return redirect('inicio')
            else:
                messages.error(request, 'Tipo de usuario no válido.')
                return redirect('login_usuario')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    else:
        form = FormLogin()

    return render(request, 'login.html', {'form': form})
@login_required
def logout_usuario(request):
    logout(request)
    return redirect('login')

from django.contrib import messages

from .models import Notificacion

@login_required
def admin_dashboard(request):
    if request.user.tipo_usuario != 'admin':
        messages.error(request, "Acceso denegado: Solo para administradores.")
        return redirect('inicio')

    # Obtener notificaciones no leídas para este admin
    notificaciones = Notificacion.objects.filter(usuario_destino=request.user, leido=False).order_by('-fecha_noti')[:5]
    total_notif = notificaciones.count()

    return render(request, 'plantilla_admin.html', {
        'notificaciones': notificaciones,
        'total_notif': total_notif,
    })




@login_required
def catalogo(request):
    if request.user.tipo_usuario != 'cliente':
        messages.error(request, "Acceso denegado: Solo para clientes.")
        return redirect('admin_dashboard')
    return render(request, 'inicio.html')


from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta

from django.contrib import messages

def add_to_cart(request, id_prod):
    producto = get_object_or_404(Producto, pk=id_prod)

    cantidad = 1
    if request.method == 'POST':
        try:
            cantidad = int(request.POST.get('quantity', 1))
        except:
            cantidad = 1

    try:
        inventario = producto.inventario
        stock_actual = inventario.stock_actual
    except Inventario.DoesNotExist:
        stock_actual = 0

    # 👇 Reemplazamos is_ajax() correctamente
    es_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if cantidad < 1:
        if not es_ajax:
            messages.error(request, 'La cantidad debe ser al menos 1.')
            return redirect('producto_vista_rapida', id_prod=id_prod)
        else:
            return JsonResponse({'success': False, 'message': 'Cantidad inválida.'}, status=400)

    if cantidad > stock_actual:
        msg = f'No hay suficiente stock para "{producto.nomb_prod}". Disponible: {stock_actual}'
        if not es_ajax:
            messages.error(request, msg)
            return redirect('producto_vista_rapida', id_prod=id_prod)
        else:
            return JsonResponse({'success': False, 'message': msg}, status=400)

    if request.user.is_authenticated:
        tiempo_limite = timezone.now() - timedelta(hours=48)
        carrito = Carrito.objects.filter(
            usuarios=request.user,
            fechacreac_carr__gte=tiempo_limite
        ).first()
        if not carrito:
            carrito = Carrito.objects.create(usuarios=request.user)

        detalle, creado = DetalleCarrito.objects.get_or_create(
            carrito=carrito,
            producto=producto,
            defaults={'cantidad': cantidad}
        )
        if not creado:
            detalle.cantidad += cantidad
            detalle.save()

        cart_count = sum(d.cantidad for d in carrito.detalles.all())

        if es_ajax:
            return JsonResponse({'success': True, 'message': 'Añadido al carrito.', 'cart_count': cart_count})
        else:
            messages.success(request, f'Se agregó {cantidad} unidad(es) de "{producto.nomb_prod}" a tu carrito.')
            return redirect('producto_vista_rapida', id_prod=id_prod)

    else:
        carrito_sesion = request.session.get('carrito', {})
        prev = carrito_sesion.get(str(id_prod), 0)
        carrito_sesion[str(id_prod)] = prev + cantidad
        request.session['carrito'] = carrito_sesion

        if es_ajax:
            cart_count = sum(carrito_sesion.values())
            return JsonResponse({'success': True, 'message': 'Añadido al carrito.', 'cart_count': cart_count})
        else:
            messages.success(request, f'Se agregó {cantidad} unidad(es) de "{producto.nomb_prod}" al carrito temporal.')
            return redirect('producto_vista_rapida', id_prod=id_prod)

from decimal import Decimal

def carrito(request):
    cart_items = []  
    carrito = None

    if request.user.is_authenticated:
        tiempo_limite = timezone.now() - timedelta(hours=48)
        carrito = Carrito.objects.filter(
            usuarios=request.user,
            fechacreac_carr__gte=tiempo_limite
        ).first()

        if carrito:
            cart_items = [{
                'product': detalle.producto,
                'quantity': detalle.cantidad,
                'total_price': detalle.subtotal
            } for detalle in carrito.detalles.all()]
            request.session['carrito_id'] = carrito.id_carr
    else:
        carrito_sesion = request.session.get('carrito', {})
        for id_prod_str, quantity in carrito_sesion.items():
            try:
                producto = Producto.objects.get(pk=int(id_prod_str))
                total_price = producto.inventario.precunit_prod * quantity
                cart_items.append({
                    'product': producto,
                    'quantity': quantity,
                    'total_price': total_price,
                })
            except Producto.DoesNotExist:
                continue

    cart_total = sum(item['total_price'] for item in cart_items)

    impuesto_activo = Impuesto.objects.filter(estado=True).first()
    iva_valor = Decimal(impuesto_activo.valor) if impuesto_activo else Decimal('0')

    impuesto = cart_total * (iva_valor / Decimal('100'))
    total_con_impuesto = cart_total + impuesto

    return render(request, 'carrito.html', {
        'cart_items': cart_items,
        'cart_total': cart_total,
        'impuesto': impuesto,
        'iva_valor': iva_valor,
        'total_con_impuesto': total_con_impuesto,
        'carrito': carrito,
    })

#ORDEN CONFIRMADA 
@login_required(login_url='login')
def orden_confirmada(request, id_ord):
    """Muestra la página de confirmación de orden"""
    try:
        orden = get_object_or_404(Orden, id_ord=id_ord, usuarios=request.user)
        detalles_orden = orden.detalles.all()
        registro_pago = orden.pagos.first()

        # Calcular subtotal e impuesto
        impuesto_activo = Impuesto.objects.filter(estado=True).first()
        iva_valor = Decimal(impuesto_activo.valor) if impuesto_activo else Decimal('0')

        # Si existe IVA, calcularlo a partir del total
        if iva_valor > 0:
            impuesto = registro_pago.total_pago * iva_valor / (100 + iva_valor)
            subtotal = registro_pago.total_pago - impuesto
        else:
            impuesto = Decimal('0')
            subtotal = registro_pago.total_pago

        return render(request, 'orden_confirmada.html', {
            'orden': orden,
            'detalles_orden': detalles_orden,
            'registro_pago': registro_pago,
            'subtotal': subtotal,
            'impuesto': impuesto,
            'total': registro_pago.total_pago,
            'metodo_entrega': orden.metodo_entrega
        })
    except Orden.DoesNotExist:
        messages.error(request, "No se encontró la orden solicitada")
        return redirect('carrito')

def eliminar_del_carrito(request, id_prod):
    if request.method != 'POST':
        return redirect('carrito')

    if request.user.is_authenticated:
        carrito = Carrito.objects.filter(
            usuarios=request.user
        ).order_by('-fechacreac_carr').first()
        if carrito:
            detalle = carrito.detalles.filter(producto_id=id_prod).first()
            if detalle:
                detalle.delete()
    else:
        carrito_sesion = request.session.get('carrito', {})
        prod_key = str(id_prod)
        if prod_key in carrito_sesion:
            del carrito_sesion[prod_key]
            request.session['carrito'] = carrito_sesion

    return redirect('carrito')

def actualizar_cantidad_carrito(request, id_prod):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)

    cantidad_nueva = int(request.POST.get('quantity', 1))
    producto = get_object_or_404(Producto, pk=id_prod)
    inventario = get_object_or_404(Inventario, producto=producto)

    if cantidad_nueva < 1:
        return JsonResponse({'success': False, 'message': 'La cantidad debe ser al menos 1.'})

    if cantidad_nueva > inventario.stock_actual:
        return JsonResponse({'success': False,
                             'message': f'No hay suficiente stock para "{producto.nomb_prod}". Stock disponible: {inventario.stock_actual}'})

    if request.user.is_authenticated:
        carrito = Carrito.objects.filter(
            usuarios=request.user
        ).order_by('-fechacreac_carr').first()
        if carrito:
            detalle = carrito.detalles.filter(producto=producto).first()
            if detalle:
                detalle.cantidad = cantidad_nueva
                detalle.save()
            else:
                DetalleCarrito.objects.create(carrito=carrito, producto=producto, cantidad=cantidad_nueva)
        else:
            carrito = Carrito.objects.create(usuarios=request.user)
            DetalleCarrito.objects.create(carrito=carrito, producto=producto, cantidad=cantidad_nueva)

        return JsonResponse({'success': True, 'message': f'Cantidad actualizada para "{producto.nomb_prod}".'})
    else:
        carrito_sesion = request.session.get('carrito', {})
        carrito_sesion[str(id_prod)] = cantidad_nueva
        request.session['carrito'] = carrito_sesion

        return JsonResponse({'success': True, 'message': f'Cantidad actualizada para "{producto.nomb_prod}".'})

# PROCESO DE DATOS DEL CLIENTE 
from decimal import Decimal


@login_required(login_url='login')  
def pago(request):
    if request.method == 'POST':
        try:
            nombre = request.POST.get('nombre', '')
            tipo_documento = request.POST.get('tipo_documento', 'cedula')
            numero_documento = request.POST.get('numero_documento', '') 
            email = request.POST.get('email', '')
            direccion = request.POST.get('direccion', '')
            ciudad = request.POST.get('ciudad', '')
            telefono = request.POST.get('telefono', '')

            if not all([nombre, tipo_documento, numero_documento, email, direccion, ciudad, telefono]):
                messages.error(request, "Por favor, complete todos los campos del formulario")
                return redirect('datosPedido')

            carrito_id = request.session.get('carrito_id')
            if not carrito_id:
                messages.error(request, "No hay carrito activo")
                return redirect('carrito')

            datos_cliente = {
                'nombre': nombre,
                'tipo_documento': tipo_documento,
                'numero_documento': numero_documento,
                'email': email,
                'direccion': direccion,
                'ciudad': ciudad,
                'telefono': telefono
            }

            if 'datos_cliente' in request.session:
                request.session['datos_cliente'].update(datos_cliente)
            else:
                request.session['datos_cliente'] = datos_cliente

            messages.success(request, "Datos del cliente guardados exitosamente")
            return redirect('/finalPedido/')

        except Exception as e:
            print(f"Error en pago: {str(e)}")
            messages.error(request, f"Error al procesar los datos: {str(e)}")
            return redirect('datosPedido')

    # Si es GET
    carrito_id = request.session.get('carrito_id')
    if carrito_id:
        carrito = get_object_or_404(Carrito, id_carr=carrito_id)
        detalles = carrito.detalles.select_related('producto', 'producto__inventario').all()

        cart_items = [
            {
                'product': detalle.producto,
                'quantity': detalle.cantidad,
                'total_price': detalle.subtotal
            }
            for detalle in detalles
        ]

        cart_total = carrito.total_carrito()

        impuesto_activo = Impuesto.objects.filter(estado=True).first()
        iva_valor = Decimal(impuesto_activo.valor) if impuesto_activo else Decimal('0')
        impuesto = cart_total * (iva_valor / Decimal('100'))
        total_con_impuesto = cart_total + impuesto

        datos_cliente = request.session.get('datos_cliente', {})

        return render(request, 'datosPedido.html', {
            'cart_items': cart_items,
            'cart_total': cart_total,
            'impuesto': impuesto,
            'total_con_impuesto': total_con_impuesto,
            'datos_cliente': datos_cliente,
            'carrito': carrito,
            'iva_valor': iva_valor
        })
    else:
        messages.error(request, "No hay carrito activo. Por favor, agregue productos al carrito primero.")
        return redirect('carrito')

#VISTA RAPIDA
# views.py
from django.shortcuts import render, get_object_or_404
from .models import Producto, Inventario

def producto_vista_rapida(request, id_prod):
    producto = get_object_or_404(Producto, pk=id_prod)
    try:
        inventario = producto.inventario
        stock = inventario.stock_actual
        precio = inventario.precunit_prod
    except Inventario.DoesNotExist:
        stock = 0
        precio = None
    return render(request, 'producto_vista_rapida.html', {
        'producto': producto,
        'stock': stock,
        'precio': precio,
    })

### DASHBORAD ADMIN ACEPTAR O RECHAZAR ORDEN 



from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.core.mail import EmailMessage
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import RegistroPago
from django.conf import settings

@login_required(login_url='login')
@admin_required
def admin_confirmar_pago(request, id_regpag):
    registro_pago = get_object_or_404(RegistroPago, id_regpag=id_regpag)
    orden = registro_pago.orden

    if registro_pago.estado_reg == 'Pendiente':
        # Descontar stock
        # Registrar movimiento de salida sin modificar el stock actual
        for detalle in orden.detalles.all():
            try:
                inventario = detalle.producto.inventario
                
                # Registrar el movimiento de salida
                MovimientoInventario.objects.create(
                    tipo='Salida',
                    cantidad=detalle.cantidad,
                    precio_uni=inventario.precunit_prod,
                    precio_anterior=inventario.precunit_prod,
                    producto=detalle.producto,
                    observacion=f'Salida por confirmación de orden #{orden.id_ord} - Venta'
                )

            except ValueError as e:
                messages.error(request, f"No se pudo procesar la orden: {str(e)}")
                return redirect('admin_detalle_pago', id_regpag=registro_pago.id_regpag)

        # Actualizamos el estado de la orden y el pago
        registro_pago.estado_reg = 'Confirmado'
        registro_pago.save()
        orden.estado_ord = 'Entregado'
        orden.save()

        # ✅ GENERAR PDF EN MEMORIA
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        p.setTitle(f"Presupuesto #{orden.id_ord}")

        # Título "COMPROBANTE"
        p.setFont("Helvetica-Bold", 16)
        
        # Cabecera con márgenes ajustados
        p.setFont("Helvetica-Bold", 14)
        p.drawString(100, 735, "AJ DITEC DISTRIBUIDORA")
        p.drawString(100, 780, f"Comprobante de Compra - Orden #{orden.id_ord}")
        p.setFont("Helvetica", 10)
        p.drawString(100, 720, "RUC: 1791101030101")
        p.drawString(100, 705, "AV. 10 de Agosto, Quito 170129")
        p.drawString(400, 735, f"Cliente: {orden.nombre_cliente}")
        p.drawString(400, 720, f"Identificación: {orden.tipo_documento} - {orden.numero_documento}")
        p.drawString(400, 705, f"Dirección: {orden.direccion_cliente}")
        p.drawString(400, 690, f"Fecha: {registro_pago.fech_crea}")

        # Separación para la tabla
        p.setFont("Helvetica-Bold", 10)
        p.drawString(100, 680, "Descripción")
        p.drawString(300, 680, "Cantidad")
        p.drawString(400, 680, "Precio Unitario")

        # Detalle de productos con márgenes ajustados
        y = 660
        p.setFont("Helvetica", 9)  # Reducir tamaño de fuente para detalles
        for det in orden.detalles.all():
            p.drawString(100, y, det.producto.nomb_prod)
            p.drawString(300, y, f"x{det.cantidad}")
            p.drawString(400, y, f"${det.producto.inventario.precunit_prod:.2f}")
            y -= 15  # Reducir el espacio entre productos para evitar desbordamiento

        # Total
        p.setFont("Helvetica-Bold", 10)
        p.drawString(400, y-10, "Total")
        p.drawString(500, y-10, f"${registro_pago.total_pago:.2f}")

        # Mensaje de agradecimiento
        p.setFont("Helvetica", 10)
        p.drawString(100, y-40, "Gracias por tu compra. ¡Esperamos verte pronto!")

        p.showPage()
        p.save()
        buffer.seek(0)

        # ✅ ENVIAR EMAIL CON PDF ADJUNTO
        email = EmailMessage(
            subject=f"Presupuesto confirmado - Orden #{orden.id_ord}",
            body=f"Hola {orden.nombre_cliente},\n\nAdjuntamos el presupuesto de tu compra. Gracias por confiar en nosotros.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[orden.correo_cliente],
        )
        email.attach(f"Presupuesto_Orden_{orden.id_ord}.pdf", buffer.read(), "application/pdf")
        email.send()

        messages.success(request, f"Pago confirmado, stock descontado y presupuesto PDF enviado por email.")
    else:
        messages.info(request, "Este pago ya fue procesado.")

    return redirect('admin_listar_pagos')


from django.core.mail import send_mail


@login_required(login_url='login')
@admin_required
def admin_rechazar_pago(request, id_regpag):
    registro_pago = get_object_or_404(RegistroPago, id_regpag=id_regpag)
    orden = registro_pago.orden

    if registro_pago.estado_reg == 'Pendiente':
        # DEVOLVER EL STOCK
        for detalle in orden.detalles.all():
            inventario = detalle.producto.inventario

            # Sumar nuevamente la cantidad al stock actual
            inventario.stock_actual += detalle.cantidad
            inventario.save()

            # Registrar el movimiento como "Entrada por devolución"
            MovimientoInventario.objects.create(
                tipo='Entrada',
                cantidad=detalle.cantidad,
                precio_uni=inventario.precunit_prod,
                precio_anterior=inventario.precunit_prod,
                producto=detalle.producto,
                observacion=f"Devolución por rechazo de orden #{orden.id_ord}"
            )

        # Cambiar el estado
        registro_pago.estado_reg = 'Rechazado'
        registro_pago.save()
        orden.estado_ord = 'Rechazado'
        orden.save()

        # Notificación por correo
        whatsapp_link = "https://wa.me/593969025956?text=Hola,%20tengo%20una%20consulta%20sobre%20mi%20pedido."

        detalles_texto = "\n".join(
            f"- {det.producto.nomb_prod}, Cantidad: {det.cantidad}, Subtotal: ${det.subtotal:.2f}"
            for det in orden.detalles.all()
        )

        mensaje = f"""
Hola {orden.nombre_cliente},

Lamentablemente tu pedido con Orden #{orden.id_ord} ha sido RECHAZADO.

---------------------------------
{detalles_texto}
---------------------------------
Total: ${registro_pago.total_pago:.2f}

Para más información o solucionar este inconveniente, puedes contactarnos directamente por WhatsApp:
{whatsapp_link}

Gracias por tu comprensión.

AJ Ditec Distribuidora
"""

        send_mail(
            subject=f"Orden #{orden.id_ord} rechazada",
            message=mensaje,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[orden.correo_cliente],
            fail_silently=False,
        )

        messages.warning(request, f"Orden #{orden.id_ord} rechazada, stock devuelto y correo enviado al cliente.")
    else:
        messages.info(request, "Este pago ya fue procesado anteriormente.")

    return redirect('admin_listar_pagos')

from django.contrib.auth.decorators import login_required


@login_required(login_url='login')
@admin_required
def admin_listar_pagos(request):
    pagos = RegistroPago.objects.select_related('orden', 'orden__banco').order_by('-id_regpag')

    # Obtener filtros desde GET
    estado = request.GET.get('estado', '')
    banco_id = request.GET.get('banco', '')
    cliente = request.GET.get('cliente', '')

    # Aplicar filtros
    if estado:
        pagos = pagos.filter(estado_reg=estado)
    if banco_id:
        pagos = pagos.filter(orden__banco_id=banco_id)
    if cliente:
        pagos = pagos.filter(orden__nombre_cliente__icontains=cliente)

    bancos = Banco.objects.all()

    return render(request, 'admin_listar_pagos.html', {
        'pagos': pagos,
        'estado': estado,
        'banco_id': banco_id,
        'cliente': cliente,
        'bancos': bancos,
    })

from decimal import Decimal
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required

@login_required(login_url='login')
@admin_required
def admin_detalle_pago(request, id_regpag):
    registro_pago = get_object_or_404(RegistroPago, id_regpag=id_regpag)
    orden = registro_pago.orden
    detalles_orden = DetalleOrden.objects.filter(orden=orden)

    # Calcular subtotal: precio aplicado * cantidad para cada detalle
    subtotal = sum(det.precio_aplicado * det.cantidad for det in detalles_orden)

    # Obtener el IVA aplicado; asumimos que todos usan el mismo IVA, sino ajustar
    iva_valor = detalles_orden[0].iva_aplicado if detalles_orden.exists() else Decimal('0.00')
    iva_valor = Decimal(str(iva_valor))  # asegurar tipo Decimal

    # Calcular impuesto total
    impuesto_total = subtotal * (iva_valor / Decimal('100'))

    # Total con impuesto
    total_con_impuesto = subtotal + impuesto_total

    return render(request, 'admin_detalle_pago.html', {
        'registro_pago': registro_pago,
        'orden': orden,
        'detalles': detalles_orden,
        'subtotal': subtotal,
        'impuesto_total': impuesto_total,
        'iva_valor': iva_valor,
        'total_con_impuesto': total_con_impuesto,
    })


#NOTIFICACIONES
from django.contrib.auth.decorators import login_required
from .models import Notificacion

@login_required
@login_required(login_url='login')
@admin_required
def verNotificaciones(request):
    if request.user.tipo_usuario != 'admin':
        messages.error(request, "Acceso denegado: Solo para administradores.")
        return redirect('catalogo')

    # Traer todas las notificaciones de este admin
    notificaciones = Notificacion.objects.filter(usuario_destino=request.user).order_by('-fecha_noti')

    # Marcar todas como leídas
    Notificacion.objects.filter(usuario_destino=request.user, leido=False).update(leido=True)

    return render(request, 'admin/verNotificaciones.html', {
        'notificaciones': notificaciones
    })

#MOVIMIENTO
@login_required(login_url='login')
@admin_required
def nuevoIngresoInventario(request):
    if request.method == 'POST':
        producto_id = request.POST.get('producto')
        cantidad = request.POST.get('cantidad')
        nuevo_precio = request.POST.get('precio')

        producto = get_object_or_404(Producto, id_prod=producto_id)

        # Verificar inventario existente
        try:
            inventario = producto.inventario
        except Inventario.DoesNotExist:
            messages.error(request, "El producto no tiene inventario asociado.")
            return redirect('nuevoIngreso')

        # Validación
        try:
            cantidad = int(cantidad)
            nuevo_precio = float(nuevo_precio)
        except ValueError:
            messages.error(request, "Cantidad o precio inválido.")
            return redirect('nuevoIngreso')

        if cantidad <= 0 or nuevo_precio <= 0:
            messages.error(request, "Cantidad y precio deben ser mayores a cero.")
            return redirect('nuevoIngreso')

        # Precio anterior
        precio_anterior = inventario.precunit_prod

        # Determinar el nuevo precio de venta (mayor entre el anterior y el nuevo)
        precio_venta = max(precio_anterior, nuevo_precio)

        # Registrar movimiento
        MovimientoInventario.objects.create(
            tipo='Entrada',
            cantidad=cantidad,
            precio_uni=nuevo_precio,
            precio_anterior=precio_anterior,
            producto=producto,
            observacion='Ingreso por reposición manual'
        )

        # Actualizar inventario
        inventario.precunit_prod = precio_venta
        inventario.stock_actual += cantidad
        inventario.save()

        messages.success(request, f'Ingreso exitoso. {cantidad} unidades agregadas. Nuevo precio de venta: ${precio_venta}')
        return redirect('listadoInventario')

    # Mostrar formulario
    productos = Producto.objects.filter(borrado_prod=False).select_related('inventario')
    return render(request, 'admin/inventario/nuevoIngreso.html', {
        'productos': productos
    })

#LISTADO DE MOVIMIENTOS

from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Min, Max
from django.contrib import messages
from datetime import datetime
from django.shortcuts import render

@login_required
@user_passes_test(lambda u: u.tipo_usuario == 'admin', login_url='login')
def listadoMovimiento(request):
    # Obtener parámetros de filtrado
    producto_id = request.GET.get('producto')
    tipo_movimiento = request.GET.get('tipo')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    # Consulta base con select_related para optimización
    movimientos = MovimientoInventario.objects.all().select_related(
        'producto', 
        'producto__inventario'
    ).order_by('-fecha')

    # Filtrado por producto
    if producto_id and producto_id.isdigit():
        movimientos = movimientos.filter(producto_id=int(producto_id))

    # Filtrado por tipo de movimiento
    if tipo_movimiento in ['Entrada', 'Salida']:
        movimientos = movimientos.filter(tipo=tipo_movimiento)

    # Validación y filtrado por fechas
    date_errors = []
    if fecha_inicio or fecha_fin:
        try:
            fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d') if fecha_inicio else None
            fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d') if fecha_fin else None
            
            if fecha_inicio_dt and fecha_fin_dt and fecha_fin_dt < fecha_inicio_dt:
                date_errors.append('La fecha fin no puede ser anterior a la fecha inicio.')
            else:
                if fecha_inicio_dt:
                    movimientos = movimientos.filter(fecha__date__gte=fecha_inicio_dt)
                if fecha_fin_dt:
                    movimientos = movimientos.filter(fecha__date__lte=fecha_fin_dt)
        except ValueError:
            date_errors.append('Formato de fecha inválido. Use YYYY-MM-DD.')

    # Obtener productos activos
    productos = Producto.objects.filter(borrado_prod=False)

    # Obtener rango de fechas disponible
    rango_fechas = MovimientoInventario.objects.aggregate(
        Min('fecha'),
        Max('fecha')
    )
    fecha_min = rango_fechas['fecha__min'] or datetime.now().date()
    fecha_max = rango_fechas['fecha__max'] or datetime.now().date()

    # Mostrar errores
    for error in date_errors:
        messages.error(request, error)

    context = {
        'movimientos': movimientos,
        'productos': productos,
        'filtro_producto': int(producto_id) if producto_id and producto_id.isdigit() else '',
        'filtro_tipo': tipo_movimiento,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'fecha_min': fecha_min.strftime('%Y-%m-%d'),
        'fecha_max': fecha_max.strftime('%Y-%m-%d'),
    }

    return render(request, 'admin/inventario/listadoMovimiento.html', context)


#reportes de ventas 
from django.shortcuts import render
from django.db.models import Sum, Q
from .models import Producto
from datetime import datetime

@login_required(login_url='login')
@admin_required
def reporte_ventas_productos(request):
    productos_vendidos = []
    tipo = request.GET.get('tipo', 'mayor')  # 'mayor' o 'menor'
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    # Obtener la primera y última fecha de ordenes
    primer_orden = Orden.objects.order_by('fechacrea_ord').first()
    ultima_orden = Orden.objects.order_by('-fechacrea_ord').first()
    
    if primer_orden and ultima_orden:
        fecha_minima = primer_orden.fechacrea_ord
        fecha_maxima = ultima_orden.fechacrea_ord
    else:
        fecha_minima = None
        fecha_maxima = None

    try:
        if fecha_inicio and fecha_fin:
            # Convertir strings de fecha a objetos date
            fecha_inicio_dt = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
            fecha_fin_dt = datetime.strptime(fecha_fin, "%Y-%m-%d").date()

            # Validar fechas
            if fecha_inicio_dt > fecha_fin_dt:
                messages.error(request, "La fecha de inicio no puede ser posterior a la fecha de fin")
                return redirect('reporte_ventas_productos')
            
            if fecha_minima and fecha_inicio_dt < fecha_minima:
                messages.error(request, f"La fecha de inicio no puede ser anterior a {fecha_minima.strftime('%Y-%m-%d')}")
                return redirect('reporte_ventas_productos')
            
            if fecha_maxima and fecha_fin_dt > fecha_maxima:
                messages.error(request, f"La fecha de fin no puede ser posterior a {fecha_maxima.strftime('%Y-%m-%d')}")
                return redirect('reporte_ventas_productos')

            # Obtener productos con ventas en el rango de fechas
            productos = Producto.objects.annotate(
                total_vendido=Sum(
                    'detalleorden__cantidad',
                    filter=Q(detalleorden__orden__fechacrea_ord__range=(fecha_inicio_dt, fecha_fin_dt))
                )
            ).filter(total_vendido__gt=0)

            # Filtrar y ordenar según el tipo seleccionado
            productos = productos.filter(total_vendido__isnull=False)
            
            if tipo == 'menor':
                # Para menos vendidos: mostrar productos con menos de 10 ventas
                productos_vendidos = productos.filter(total_vendido__lt=10).order_by('total_vendido')
            else:
                # Para más vendidos: mostrar productos con más de 10 ventas
                productos_vendidos = productos.filter(total_vendido__gt=10).order_by('-total_vendido')

    except Exception as e:
        print("Error:", e)
        messages.error(request, "Error al procesar el reporte")
        return redirect('reporte_ventas_productos')

    return render(request, 'reporteVentas.html', {
        'productos_vendidos': productos_vendidos,
        'tipo': tipo,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'fecha_minima': fecha_minima,
        'fecha_maxima': fecha_maxima
    })


#IMPUESTO
# Mostrar formulario para nuevo impuesto
@login_required(login_url='login')
@admin_required
def nuevoImpuesto(request):
    impuestos = Impuesto.objects.all()
    return render(request, 'admin/impuesto/nuevoImpuesto.html', {
        'impuestos': impuestos
    })

# Listado de impuestos (opcional si usas vista separada)
def listadoImpuesto(request):
    impuestos = Impuesto.objects.all()
    return render(request, 'admin/impuesto/listadoImpuesto.html', {
        'impuestos': impuestos
    })

# Guardar nuevo impuesto
@login_required(login_url='login')
@admin_required
def guardarImpuesto(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip().upper()
        valor = request.POST.get('valor')
        estado = True if request.POST.get('estado') == 'on' else False

        # Validar si ya existe un impuesto con el mismo nombre y valor
        if Impuesto.objects.filter(nombre__iexact=nombre, valor=valor).exists():
            messages.error(request, "Ya existe un impuesto con ese nombre y valor.")
            return redirect('/nuevoImpuesto')

        Impuesto.objects.create(
            nombre=nombre,
            valor=valor,
            estado=estado
        )
        messages.success(request, "Impuesto registrado correctamente.")
        return redirect('/nuevoImpuesto')

# Eliminar impuesto
@login_required(login_url='login')
@admin_required
def eliminarImpuesto(request, id_impuesto):
    impuestoEliminar = get_object_or_404(Impuesto, id_impuesto=id_impuesto)
    impuestoEliminar.delete()
    messages.success(request, "Impuesto eliminado correctamente.")
    return redirect('/nuevoImpuesto')

# Mostrar formulario para editar impuesto
@login_required(login_url='login')
@admin_required
def editarImpuesto(request, id_impuesto):
    impuestoEditar = get_object_or_404(Impuesto, id_impuesto=id_impuesto)
    # Convertir a string con punto decimal
    impuestoEditar.valor_str = str(impuestoEditar.valor).replace(',', '.')
    return render(request, 'admin/impuesto/editarImpuesto.html', {
        'impuesto': impuestoEditar
    })


# Procesar edición del impuesto
@login_required(login_url='login')
@admin_required
def procesarEdicionImpuesto(request):
    impuesto = get_object_or_404(Impuesto, id_impuesto=request.POST['id_impuesto'])

    impuesto.nombre = request.POST.get('nombre', '').strip().upper()
    impuesto.valor = request.POST.get('valor')
    impuesto.estado = True if request.POST.get('estado') == 'on' else False

    impuesto.save()
    messages.success(request, "Impuesto actualizado correctamente.")
    return redirect('/nuevoImpuesto')

from django.shortcuts import render
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from .models import RegistroPago, Orden, Usuario, DetalleOrden, Inventario, Banco
@login_required(login_url='login')
@admin_required
def dashboard(request):
    # Ventas mensuales
    ventas_mensuales_qs = (RegistroPago.objects
        .filter(estado_reg='Confirmado')
        .annotate(mes=TruncMonth('fech_crea'))
        .values('mes')
        .annotate(total=Sum('total_pago'))
        .order_by('mes'))

    ventas_labels = [v['mes'].strftime('%b %Y') for v in ventas_mensuales_qs]
    ventas_data = [float(v['total']) for v in ventas_mensuales_qs]

    # Pedidos por estado
    pedidos_estado_qs = (Orden.objects
        .values('estado_ord')
        .annotate(total=Count('id_ord')))
    pedidos_labels = [p['estado_ord'] for p in pedidos_estado_qs]
    pedidos_data = [p['total'] for p in pedidos_estado_qs]

    # Totales para tarjetas
    total_usuarios = Usuario.objects.count()
    total_confirmadas = Orden.objects.filter(estado_ord='Entregado').count()
    total_pendientes = Orden.objects.filter(estado_ord='Pendiente').count()
    total_rechazadas = Orden.objects.filter(estado_ord='Rechazado').count()
    total_bancos = Banco.objects.filter(activo=True).count()

    # Top productos más vendidos
    top_productos_qs = (DetalleOrden.objects
        .values('producto__nomb_prod')
        .annotate(total=Sum('cantidad'))
        .order_by('-total')[:5])
    top_prod_labels = [t['producto__nomb_prod'] for t in top_productos_qs]
    top_prod_data = [t['total'] for t in top_productos_qs]

    # Productos con bajo stock
    bajo_stock_qs = Inventario.objects.filter(stock_actual__lt=10).select_related('producto')

    return render(request, 'mi_dashboard.html', {
        'ventas_labels': ventas_labels,
        'ventas_data': ventas_data,
        'pedidos_labels': pedidos_labels,
        'pedidos_data': pedidos_data,
        'total_usuarios': total_usuarios,
        'total_confirmadas': total_confirmadas,
        'total_pendientes': total_pendientes,
        'total_rechazadas': total_rechazadas,
        'total_bancos': total_bancos,
        'top_prod_labels': top_prod_labels,
        'top_prod_data': top_prod_data,
        'bajo_stock': bajo_stock_qs
    })

