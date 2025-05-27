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

def nuevoCategoria(request):
    return render(request, 'nuevoCategoria.html')

#Categoria 
def nuevoCategoria(request):
    categoria = Categoria.objects.all()
    return render (request, 'nuevoCategoria.html',{
        'categoria':categoria
    })

def listadoCategoria(request):
    categoriaBdd = Categoria.objects.all()
    return render(request, 'listadoCategoria.html', 
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
    return render(request,'editarCategoria.html', {'categoria':categoriaEditar })

def procesarEdicionCategoria(request):
    categoria=Categoria.objects.get(id_cat = request.POST['id_cat'])
    categoria.tipo_cat=request.POST['tipo_cat']

    categoria.save()
    messages.success(request,"Categoria actualizada con exito")
    return redirect('/listadoCategoria')

from django.http import HttpResponse
from django.db import connection

def mostrar_base_datos(request):
    return HttpResponse(f"Base de datos en uso: {connection.settings_dict['NAME']}")

