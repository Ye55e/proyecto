from django.shortcuts import render

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