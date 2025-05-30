from  Ajditec.models import Categoria

def categorias_disponibles(request):
    return {
        'categoria': Categoria.objects.all()
    }
