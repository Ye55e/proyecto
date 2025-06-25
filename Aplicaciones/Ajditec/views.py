from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from .models import Producto, Categoria, Inventario,Usuario,DetalleCarrito

def carrito(request):
    return render(request, 'carrito.html')
def finalPedido(request):
    return render(request, 'finalPedido.html')
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
    cart_items_qs = carrito.detalles.select_related('producto', 'producto__inventario').all()
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

    context = {
        'cart_items': cart_items,
        'cart_total': cart_total,
        'carrito': carrito  # Pasar el objeto carrito completo
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
    return render(request, 'categoria/listadoCategoria.html', 
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
    return render(request,'categoria/editarCategoria.html', {'categoria':categoriaEditar })

def procesarEdicionCategoria(request):
    categoria=Categoria.objects.get(id_cat = request.POST['id_cat'])
    categoria.tipo_cat=request.POST['tipo_cat']

    categoria.save()
    messages.success(request,"Categoria actualizada con exito")
    return redirect('/nuevoCategoria')
#PRODUCTOS
def nuevoProducto(request):
    categorias = Categoria.objects.all()
    return render(request, 'producto/nuevoProducto.html', {
        'categoria': categorias
    })

def listadoProducto(request):
    productos = Producto.objects.filter(borrado_prod=False)
    return render(request, 'producto/listadoProducto.html', {
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
    return render(request, 'producto/editarProducto.html', {
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
    return render(request, 'inventario/nuevoInventario.html', {
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
    return render(request, 'inventario/listadoInventario.html', {
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
        else:
            cart_items = []

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
    })

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
    return render(request, 'pago.html')

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
