from  Aplicaciones.Ajditec.models import Categoria

def categorias_disponibles(request):
    return {
        'categoria': Categoria.objects.all()
    }


def carrito_total_items(request):
    carrito = request.session.get('carrito', {})  # Esperado: {'3': 2, '5': 1}
    total_items = sum(carrito.values())  # Solo sumamos las cantidades
    return {'carrito_total_items': total_items}
