from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Producto, Categoria 

# Create your views here.
def inicio(request):
    return render(request, 'inicio.html')

def nuevoProducto(request):
    return render(request, 'nuevoProducto.html')

def pago_view(request):
    return render(request, 'pago.html')

def carrito_view(request):
    return render(request, 'carrito.html')



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
    return redirect ('/listadoCategoria')

def eliminarCategoria(request, id_categoria):
    categoriaELiminar = get_object_or_404(Categoria, id_cat=id_categoria)
    categoriaELiminar.delete()
    messages.success(request,"Categoria Eliminada")
    return redirect('listadoCategoria')

def editarCategoria(request, id_categoria):
    categoriaEditar = Categoria.objects.get(id_cat = id_categoria)
    return render(request,'categoria/editarCategoria.html', {'categoria':categoriaEditar })

def procesarEdicionCategoria(request):
    categoria=Categoria.objects.get(id_cat = request.POST['id_cat'])
    categoria.tipo_cat=request.POST['tipo_cat']

    categoria.save()
    messages.success(request,"Categoria actualizada con exito")
    return redirect('/listadoCategoria')
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
        estado = request.POST['estado']
        id_categoria = request.POST['id_cat']

        id_cat= Categoria.objects.get(id_cat=id_categoria)

        Producto.objects.create(
            nomb_prod=nomb,
            descrip_prod=descr,
            img_prod=img,
            esta_prod=estado,
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
        producto.esta_prod = request.POST['estado']
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

