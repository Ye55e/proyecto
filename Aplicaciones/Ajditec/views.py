from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from .models import Producto, Categoria, Inventario,Usuario


# Create your views here.
# views.py
def carrito(request):
    return render(request, 'carrito.html')

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



def pago_view(request):
    return render(request, 'pago.html')




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

