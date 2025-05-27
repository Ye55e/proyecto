from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Producto, Categoria, Usuario

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


#Usuarios
def nuevoUsuario(request):
    usuario = Usuario.objects.all()
    return render (request, 'nuevoUsuario.html',{
        'usuario':usuario
    })

def listadoUsuario(request):
    usuarioBdd = Usuario.objects.all()
    return render(request, 'listadoUsuario.html', 
                  {'usuario':usuarioBdd})

def guardarUsuario(request):
    username = request.POST['nomb_usu'],
    first_name = request.POST['primer_nom'],
    last_name= request.POST['primer_apell'],
    email= request.POST['email_usu'],
    cel_user= request.POST['telf_usu'],
    password= request.POST['contra_usu'],

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

def eliminarUsuario(request, id_user):
    usuarioELiminar = get_object_or_404(Usuario, id_user=id)
    usuarioELiminar.delete()
    messages.success(request,"Usuario Eliminado con exito")
    return redirect('listadoUsuario')

def editarUsuario(request, id_user):
    usuarioEditar = Usuario.objects.get(id = id_user)
    return render(request,'editarUsuario.html', {'usuario':usuarioEditar })

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
    return redirect('/listadoUsuario')

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

