from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.
#Usuario
class Usuario(AbstractUser):
    id_user= models.AutoField(primary_key=True)
    cel_user = models.CharField(max_length=10)
    
#Categoria
class Categoria(models.Model):
    id_cat = models.AutoField(primary_key=True)
    tipo_cat = models.CharField(max_length=100)
    
#Producto
class Producto(models.Model):
    ESTADOS=[
        ('Agotado', 'Agotado'),
        ('Disponible', 'Disponible'),
    ]
    id_prod = models.AutoField(primary_key=True)
    nomb_prod = models.CharField(max_length=200)
    descrip_prod = models.TextField()
    img_prod = models.FileField(upload_to='productos' )
    esta_prod = models.CharField(max_length=20, choices=ESTADOS, default='Agotado')
    borrado_prod = models.BooleanField(default=False)
    fechcreac_prod = models.DateField(auto_now_add=True)
    fechactu_prod = models.DateField(auto_now=True)
    categorias = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='productos' )

#Inventario
class Inventario(models.Model):
    id_inve = models.AutoField(primary_key=True)
    precunit_prod = models.DecimalField(max_digits=10, decimal_places=2)
    stock_actual = models.IntegerField(default=0)
    fechacrea_inve= models.DateField(auto_now_add=True)
    fechactu_inve = models.DateField(auto_now=True)
    productos = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='invetario',)
    
#Orden 
class Orden(models.Model):
    id_ord = models.AutoField(primary_key=True)
    direc_entre = models.TextField()
    metodo_pago = models.CharField(max_length=100)
    total_pagar = models.DecimalField(max_digits=10, decimal_places=2)
    estado_ord = models.BooleanField()
    fechacrea_ord = models.DateField(auto_now_add=True)
    fechactua_ord = models.DateField(auto_now=True)
    usuarios = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='ordenes')

#Carrito
class Carrito(models.Model):
    id_carr = models.AutoField(primary_key=True)
    prec_carr = models.DecimalField(max_digits=10, decimal_places=2)
    cantidad_carr = models.IntegerField(default=1)
    fechacreac_carr = models.DateTimeField(auto_now_add=True)
    usuarios = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='carritos')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)

    
#DetalleOrden
class DetalleOrden (models.Model):
    id_detord = models.AutoField(primary_key=True)
    cantidad = models.IntegerField(default=0)
    preciounitar = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    orden = models.ForeignKey(Orden, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    
#RegistroPago
class RegistroPago (models.Model):
    ESTADO=[
        ('Confirmado', 'Confirmado'),
        ('Pendiente', 'Pendiente'),
        ('Rechazado', 'Rechazado'),
    ]
    id_regpag = models.AutoField(primary_key=True)
    total_pago = models.DecimalField(max_digits=10, decimal_places=2)
    orden = models.ForeignKey(Orden, on_delete=models.CASCADE, related_name='pagos')
    fech_crea = models.DateField(auto_now_add=True)
    estado_reg = models.CharField(max_length=20, choices=ESTADO, default='Confirmado')
    
#DetalleTransferencia
class DetalleTrans(models.Model):
    BANCOS=[
        ('Banco Produbanco', 'Banco Produbanco'),
        ('Banco Pichincha', 'Banco Pichincha'),
    ]
    id_detaltrans = models.AutoField(primary_key=True)
    monto_trans = models.DecimalField()
    banco_transfe = models.CharField(max_length=20, choices=BANCOS, default='Banco Pichincha')
    codigo_compro = models.CharField(max_length=25)
    comentario = models.TextField()
    fecha_trans = models.DateField()
    registro_pago = models.ForeignKey(RegistroPago, on_delete=models.CASCADE, related_name='regispagos')