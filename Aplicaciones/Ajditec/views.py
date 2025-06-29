from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test

from .models import Producto, Categoria, Inventario,Usuario,DetalleCarrito,Orden,DetalleOrden,RegistroPago

def carrito(request):
    return render(request, 'carrito.html')
def finalPedido(request):
    carrito_id = request.session.get('carrito_id')
    if carrito_id:
        carrito = get_object_or_404(Carrito, id_carr=carrito_id)
        datos_cliente = request.session.get('datos_cliente', {})
        return render(request, 'finalPedido.html', {
            'cart_items': carrito.detalles.all(),
            'cart_total': carrito.total_carrito(),
            'datos_cliente': datos_cliente,
            'carrito': carrito
        })
    else:
        messages.error(request, "No hay carrito activo. Por favor, agregue productos al carrito primero.")
        return redirect('carrito')

@login_required
@user_passes_test(lambda u: u.tipo_usuario == 'cliente', login_url='login')
def listar_ordenes(request):
    ordenes = Orden.objects.filter(usuarios=request.user).order_by('-fechacrea_ord')
    return render(request, 'listar_ordenes.html', {
        'ordenes': ordenes
    })

@login_required
@user_passes_test(lambda u: u.tipo_usuario == 'cliente', login_url='login')
def detalle_orden(request, id_ord):
    orden = get_object_or_404(Orden, id_ord=id_ord, usuarios=request.user)
    detalles = orden.detalles.all()
    return render(request, 'detalle_orden.html', {
        'orden': orden,
        'detalles': detalles
    })

@login_required(login_url='login')
def procesar_pedido(request):
    """Procesa el pedido y crea la orden, sin descontar stock todavía"""
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            metodo_entrega = request.POST.get('metodo_entrega')
            metodo_pago = request.POST.get('metodo_pago')
            num_transferencia = request.POST.get('num_transferencia')
            fecha_transferencia = request.POST.get('fecha_transferencia')
            
            # Validar campos requeridos
            if not metodo_entrega or not metodo_pago:
                messages.error(request, "Por favor, seleccione un método de entrega y pago.")
                return redirect('finalPedido')
            
            if metodo_pago == 'transferencia' and not num_transferencia:
                messages.error(request, "Por favor, ingrese el número de transferencia.")
                return redirect('finalPedido')

            # Obtener el carrito
            carrito_id = request.session.get('carrito_id')
            if not carrito_id:
                messages.error(request, "No hay carrito activo.")
                return redirect('carrito')
            
            carrito = get_object_or_404(Carrito, id_carr=carrito_id)
            
            # Obtener datos del cliente
            datos_cliente = request.session.get('datos_cliente', {})
            if not datos_cliente:
                messages.error(request, "No se encontraron datos del cliente. Complete el formulario primero.")
                return redirect('pago')

            # Crear la orden
            orden = Orden.objects.create(
                nombre_cliente=datos_cliente.get('nombre', ''),
                cedula_ruc=datos_cliente.get('cedula', ''),
                correo_cliente=datos_cliente.get('email', ''),
                direccion_cliente=datos_cliente.get('direccion', ''),
                ciudad_cliente=datos_cliente.get('ciudad', ''),
                telefono_cliente=datos_cliente.get('telefono', ''),
                direc_entre=metodo_entrega,
                metodo_pago=metodo_pago,
                num_trans=num_transferencia,
                fecha_trans=fecha_transferencia,
                estado_ord='Pendiente',   
                usuarios=request.user,
                carrito=carrito
            )
            
            # Crear detalles de la orden
            for detalle in carrito.detalles.all():
                DetalleOrden.objects.create(
                    orden=orden,
                    producto=detalle.producto,
                    cantidad=detalle.cantidad
                )

            # Crear registro de pago
            RegistroPago.objects.create(
                orden=orden,
                total_pago=carrito.total_carrito(),
                estado_reg='Pendiente'
            )

            # Marcar el carrito como pagado
            carrito.estado_carr = 'pagado'
            carrito.save()

            # Limpiar el carrito de la sesión
            if 'carrito_id' in request.session:
                del request.session['carrito_id']

            # Mensaje de éxito
            messages.success(request, f"¡Orden #{orden.id_ord} creada exitosamente! Está pendiente de confirmación.")
            return redirect('orden_confirmada', id_ord=orden.id_ord)

        except Exception as e:
            messages.error(request, f"Error al crear la orden: {str(e)}")
            return redirect('carrito')
    else:
        return redirect('finalPedido')


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
        'metodo_pago': orden.metodo_pago
    })

def admin_plantilla(request):
    return render(request, 'plantilla_admin.html')
#

def inicio(request):
    buscar = request.GET.get('buscar', '')
    filtro = request.GET.get('filtro', 'nombre')  # valor por defecto: 'nombre'

    productos = Producto.objects.filter(borrado_prod=False).select_related('id_cat', 'inventario')

    if buscar:
        if filtro == 'nombre':
            productos = productos.filter(nomb_prod__icontains=buscar)
        elif filtro == 'categoria':
            productos = productos.filter(id_cat__tipo_cat__icontains=buscar)

    categorias = Categoria.objects.all()
    return render(request, 'inicio.html', {
        'productos': productos,
        'categorias': categorias,
        'buscar': buscar,
        'filtro': filtro,
    })
#DETALLE CARRITO
# views.py

from .models import Carrito, DetalleCarrito, Producto
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages

#vista del resumen de pedido en el template del final del pedido
def final_pedido(request):
    if not request.user.is_authenticated:
        return redirect('login')

    # Obtener el carrito del usuario
    carrito_id = request.session.get('carrito_id')
    print(f"ID del carrito en sesión: {carrito_id}")
    
    if not carrito_id:
        messages.warning(request, "No hay carrito_id en sesión")
        # Si no hay carrito en sesión, obtener el más reciente
        tiempo_limite = timezone.now() - timedelta(hours=48)
        carrito = Carrito.objects.filter(
            usuarios=request.user,
            fechacreac_carr__gte=tiempo_limite
        ).first()
    else:
        carrito = Carrito.objects.filter(
            id_carr=carrito_id,
            usuarios=request.user
        ).first()

    if not carrito:
        messages.error(request, "No se encontró ningún carrito activo. Por favor, agregue productos al carrito primero.")
        return redirect('carrito')
    else:
        print(f"Carrito encontrado: {carrito.id_carr}")

    # Guardar el ID del carrito en la sesión
    request.session['carrito_id'] = carrito.id_carr

    # Obtener los detalles del carrito
    cart_items_qs = carrito.detalles.select_related('producto', 'producto__inventario').all()
    print(f"Cantidad de detalles en el carrito: {cart_items_qs.count()}")
    
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
    print(f"Total del carrito: {cart_total}")

    # Pasar los productos y el total al template
    context = {
        'cart_items': cart_items,
        'cart_total': cart_total,
        'carrito': carrito
    }

    return render(request, 'finalPedido.html', context)


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
def nuevoUsuario(request):
    usuario = Usuario.objects.all()
    return render (request, 'usuarios/nuevoUsuario.html',{
        'usuario':usuario
    })

def listadoUsuario(request):
    usuarioBdd = Usuario.objects.all()
    return render(request, 'usuarios/listadoUsuario.html', 
                  {'usuario':usuarioBdd})

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

def eliminarUsuario(request, id):
    usuarioELiminar = get_object_or_404(Usuario, id=id)
    usuarioELiminar.delete()
    messages.success(request,"Usuario Eliminado con exito")
    return redirect('/listadoUsuario')

def editarUsuario(request, id):
    usuarioEditar = Usuario.objects.get(id = id)
    return render(request,'usuarios/editarUsuario.html', {'usuario':usuarioEditar })

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
    return redirect('usuarios/listadoUsuario')

#Categoria 
def nuevoCategoria(request):
    categoria = Categoria.objects.all()
    return render (request, 'categoria/nuevoCategoria.html',{
        'categoria':categoria
    })

def listadoCategoria(request):
    categoriaBdd = Categoria.objects.all()
    return render(request, 'admin/categoria/listadoCategoria.html', 
                  {'categoria':categoriaBdd})

def guardarCategoria(request):
    tipo_cat = request.POST['tipo_cat']

    nuevoCategoria = Categoria.objects.create(
        tipo_cat = tipo_cat,
    )

    messages.success(request,"Se ha guardado la categoria")
    return redirect ('/nuevoCategoria')

def eliminarCategoria(request, id_categoria):
    categoriaELiminar = get_object_or_404(Categoria, id_cat=id_categoria)
    categoriaELiminar.delete()
    messages.success(request,"Categoria Eliminada")
    return redirect('nuevoCategoria')

def editarCategoria(request, id_categoria):
    categoriaEditar = Categoria.objects.get(id_cat = id_categoria)
    return render(request,'admin/categoria/editarCategoria.html', {'categoria':categoriaEditar })

def procesarEdicionCategoria(request):
    categoria=Categoria.objects.get(id_cat = request.POST['id_cat'])
    categoria.tipo_cat=request.POST['tipo_cat']

    categoria.save()
    messages.success(request,"Categoria actualizada con exito")
    return redirect('/nuevoCategoria')
#PRODUCTOS
def nuevoProducto(request):
    categorias = Categoria.objects.all()
    return render(request, 'admin/producto/nuevoProducto.html', {
        'categoria': categorias
    })

def listadoProducto(request):
    productos = Producto.objects.filter(borrado_prod=False)
    return render(request, 'admin/producto/listadoProducto.html', {
        'producto': productos
    })

def guardarProducto(request):
    if request.method == 'POST':
        nomb = request.POST['nomb_prod']
        descr = request.POST['descrip_prod']
        img = request.FILES.get('foto_prod')
        id_categoria = request.POST['id_cat']

        id_cat= Categoria.objects.get(id_cat=id_categoria)

        Producto.objects.create(
            nomb_prod=nomb,
            descrip_prod=descr,
            img_prod=img,
            id_cat=id_cat
        )

        messages.success(request, "Producto guardado correctamente.")
        return redirect('/listadoProducto')

def eliminarProducto(request, id_prod):
    producto_eliminar = get_object_or_404(Producto, id_prod=id_prod)
    producto_eliminar.borrado_prod = True  # borrado lógico
    producto_eliminar.save()
    messages.success(request, "Producto eliminado")
    return redirect('/listadoProducto')

def editarProducto(request, id_prod):
    producto_editar = get_object_or_404(Producto, id_prod=id_prod)
    id_cat = Categoria.objects.all()
    return render(request, 'admin/producto/editarProducto.html', {
        'producto': producto_editar,
        'id_cat': id_cat
    })

def procesarEdicionProducto(request):
    if request.method == 'POST':
        producto = get_object_or_404(Producto, id_prod=request.POST['id_prod'])

        producto.nomb_prod = request.POST['nomb_prod']
        producto.descrip_prod = request.POST['descrip_prod']
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
def nuevoInventario(request):
    productos = Producto.objects.filter(borrado_prod=False)  # solo productos activos
    return render(request, 'admin/inventario/nuevoInventario.html', {
        'productos': productos
    })
def guardarInventario(request):
    if request.method == 'POST':
        # 1. Recogemos y validamos los datos del POST
        producto_id = request.POST.get('producto')
        precio_str  = request.POST.get('precunit_prod')
        stock_str   = request.POST.get('stock_actual')

        if not producto_id or not precio_str or not stock_str:
            messages.error(request, 'Todos los campos son obligatorios.')
            return redirect('nuevoInventario')

        # 2. Buscamos el producto
        producto = get_object_or_404(Producto, id_prod=producto_id)

        # 3. Convertimos precio y stock a tipos adecuados
        try:
            precunit = float(precio_str)
            stock_inicial = int(stock_str)
        except ValueError:
            messages.error(request, 'Precio unitario o stock inválido.')
            return redirect('nuevoInventario')

        # 4. Obtenemos (o creamos) el único Inventario para ese producto
        inventario, created = Inventario.objects.get_or_create(
            producto=producto,
            defaults={
                'precunit_prod': precunit,
                'stock_actual': stock_inicial
            }
        )

        if not created:
            # Si ya existía, actualizamos sus campos
            inventario.precunit_prod = precunit
            inventario.stock_actual = stock_inicial
            inventario.save()
            messages.success(
                request,
                f'Stock de "{producto.nomb_prod}" actualizado correctamente.'
            )
        else:
            messages.success(
                request,
                f'Inventario para "{producto.nomb_prod}" creado correctamente.'
            )

        return redirect('listadoInventario')

    # Si no es POST, redirigimos al formulario
    return redirect('nuevoInventario')
def listadoInventario(request):
    inventarios = Inventario.objects.select_related('producto').all()
    return render(request, 'admin/inventario/listadoInventario.html', {
        'inventarios': inventarios
    })

# LOGIN
# views.py
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
                return redirect('admin_dashboard')
            elif user.tipo_usuario == 'cliente':
                return redirect('catalogo')
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

@login_required
def admin_dashboard(request):
    if request.user.tipo_usuario != 'admin':
        return redirect('catalogo')  # o mostrar un error
    return render(request, 'plantilla.html')

@login_required
def catalogo(request):
    if request.user.tipo_usuario != 'cliente':
        return redirect('admin_dashboard')  # o mostrar un error
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

def carrito(request):
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
            # Guardar el ID del carrito en la sesión
            request.session['carrito_id'] = carrito.id_carr
        else:
            cart_items = []
            # Si no hay carrito, limpiar el carrito_id de la sesión
            if 'carrito_id' in request.session:
                del request.session['carrito_id']

    else:
        carrito_sesion = request.session.get('carrito', {})
        cart_items = []
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

    return render(request, 'carrito.html', {
        'cart_items': cart_items,
        'cart_total': cart_total,
        'carrito': carrito if carrito else None,
    })

@login_required(login_url='login')
def orden_confirmada(request, id_ord):
    """Muestra la página de confirmación de orden"""
    try:
        orden = get_object_or_404(Orden, id_ord=id_ord, usuarios=request.user)
        detalles_orden = orden.detalles.all()
        registro_pago = orden.pagos.first()
        
        return render(request, 'orden_confirmada.html', {
            'orden': orden,
            'detalles_orden': detalles_orden,
            'registro_pago': registro_pago
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

#PAGO
@login_required(login_url='login')  
def pago(request):
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            nombre = request.POST.get('nombre', '')
            cedula = request.POST.get('cedula', '')
            email = request.POST.get('email', '')
            direccion = request.POST.get('direccion', '')
            ciudad = request.POST.get('ciudad', '')
            telefono = request.POST.get('telefono', '')
            
            # Debug: Mostrar datos recibidos
            print(f"Datos recibidos: {request.POST}")
            print(f"Nombre: {nombre}, Cédula: {cedula}, Email: {email}")
            
            # Validar campos requeridos
            if not all([nombre, cedula, email, direccion, ciudad, telefono]):
                messages.error(request, "Por favor, complete todos los campos del formulario")
                return redirect('pago')
            
            # Verificar que el carrito existe
            carrito_id = request.session.get('carrito_id')
            if not carrito_id:
                messages.error(request, "No hay carrito activo")
                return redirect('carrito')
            
            # Guardar datos del cliente en la sesión
            datos_cliente = {
                'nombre': nombre,
                'cedula': cedula,
                'email': email,
                'direccion': direccion,
                'ciudad': ciudad,
                'telefono': telefono
            }
            
            # Verificar si ya existen datos del cliente en la sesión
            if 'datos_cliente' in request.session:
                # Actualizar los datos existentes
                request.session['datos_cliente'].update(datos_cliente)
            else:
                # Crear nuevos datos del cliente
                request.session['datos_cliente'] = datos_cliente
            
            # Debug: Confirmar que los datos se guardaron correctamente
            print(f"Datos del cliente guardados en sesión: {request.session['datos_cliente']}")
            
            # Redirigir a la vista finalPedido con mensaje de éxito
            messages.success(request, "Datos del cliente guardados exitosamente")
            
            # Usar la URL completa para la redirección
            return redirect('/finalPedido/')
            
        except Exception as e:
            # Debug: Mostrar el error completo
            print(f"Error en pago: {str(e)}")
            messages.error(request, f"Error al procesar los datos: {str(e)}")
            return redirect('pago')
    
    # Si es GET, mostrar el formulario
    carrito_id = request.session.get('carrito_id')
    if carrito_id:
        carrito = get_object_or_404(Carrito, id_carr=carrito_id)
        
        # Obtener los detalles del carrito
        detalles = carrito.detalles.select_related('producto', 'producto__inventario').all()
        
        # Preparar los items para el template
        cart_items = [
            {
                'product': detalle.producto,
                'quantity': detalle.cantidad,
                'total_price': detalle.subtotal
            }
            for detalle in detalles
        ]
        
        # Verificar si hay datos del cliente en la sesión y prellenar el formulario
        datos_cliente = request.session.get('datos_cliente', {})
        
        return render(request, 'datosPedido.html', {
            'cart_items': cart_items,
            'cart_total': carrito.total_carrito(),
            'datos_cliente': datos_cliente,
            'carrito': carrito
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
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string

from django.core.mail import send_mail

@login_required
@user_passes_test(lambda u: u.tipo_usuario == 'admin', login_url='login')
def admin_confirmar_pago(request, id_regpag):
    registro_pago = get_object_or_404(RegistroPago, id_regpag=id_regpag)
    orden = registro_pago.orden

    if registro_pago.estado_reg == 'Pendiente':
        # Descontar stock
        for detalle in orden.detalles.all():
            detalle.producto.inventario.actualizar_stock(detalle.cantidad, 'Salida')

        registro_pago.estado_reg = 'Confirmado'
        registro_pago.save()
        orden.estado_ord = 'Entregado'
        orden.save()

        # Email TEXTO PLANO
        detalles_texto = "\n".join(
            f"- {det.producto.nomb_prod}, Cantidad: {det.cantidad}, Subtotal: ${det.subtotal:.2f}"
            for det in orden.detalles.all()
        )
        mensaje = f"""
Hola {orden.nombre_cliente},

¡Tu compra ha sido CONFIRMADA!

Orden #{orden.id_ord}
---------------------------------
{detalles_texto}
---------------------------------
Total pagado: ${registro_pago.total_pago:.2f}

Pronto nos pondremos en contacto para coordinar la entrega.

¡Gracias por tu compra!

AJ Ditec Distribuidora
        """

        send_mail(
            subject=f"Compra confirmada - Orden #{orden.id_ord}",
            message=mensaje,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[orden.correo_cliente],
            fail_silently=False,
        )

        messages.success(request, f"Pago confirmado, stock descontado y correo enviado al cliente para la orden #{orden.id_ord}")
    else:
        messages.info(request, "Este pago ya fue procesado.")

    return redirect('admin_listar_pagos')


@login_required
@user_passes_test(lambda u: u.tipo_usuario == 'admin', login_url='login')
def admin_rechazar_pago(request, id_regpag):
    registro_pago = get_object_or_404(RegistroPago, id_regpag=id_regpag)
    orden = registro_pago.orden

    if registro_pago.estado_reg == 'Pendiente':
        registro_pago.estado_reg = 'Rechazado'
        registro_pago.save()
        orden.estado_ord = 'Rechazado'
        orden.save()

        whatsapp_link = "https://wa.me/593999999999?text=Hola,%20tengo%20una%20consulta%20sobre%20mi%20pedido."

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

        messages.warning(request, f"Orden #{orden.id_ord} rechazada y correo enviado al cliente.")
    else:
        messages.info(request, "Este pago ya fue procesado.")

    return redirect('admin_listar_pagos')

@login_required
@user_passes_test(lambda u: u.tipo_usuario == 'admin', login_url='login')
def admin_listar_pagos(request):
    pagos = RegistroPago.objects.select_related('orden').order_by('-id_regpag')

    print("======= LISTADO COMPLETO ========")
    for p in pagos:
        print(f"ID: {p.id_regpag}, Estado: {p.estado_reg}, Orden ID: {p.orden_id}")

    return render(request, 'admin_listar_pagos.html', {
        'pagos': pagos
    })
@login_required
@user_passes_test(lambda u: u.tipo_usuario == 'admin', login_url='login')
def admin_detalle_pago(request, id_regpag):
    registro_pago = get_object_or_404(RegistroPago, id_regpag=id_regpag)
    detalles_orden = DetalleOrden.objects.filter(orden=registro_pago.orden)
    return render(request, 'admin_detalle_pago.html', {
        'registro_pago': registro_pago,
        'orden': registro_pago.orden,
        'detalles': detalles_orden
    })
