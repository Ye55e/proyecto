from  Aplicaciones.Ajditec.models import Categoria

def categorias_disponibles(request):
    return {
        'categoria': Categoria.objects.all()
    }


from django.utils import timezone
from datetime import timedelta
from .models import Carrito

def carrito_total_items(request):
    if request.user.is_authenticated:
        tiempo_limite = timezone.now() - timedelta(hours=48)
        carrito = Carrito.objects.filter(
            usuarios=request.user,
            fechacreac_carr__gte=tiempo_limite
        ).first()
        total = sum(detalle.cantidad for detalle in carrito.detalles.all()) if carrito else 0
    else:
        carrito_sesion = request.session.get('carrito', {})
        total = sum(carrito_sesion.values())
    return {'carrito_total_items': total}
