from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.
#Usuario
class Usuario(AbstractUser):
    TIPO_USUARIO = [
        ('admin', 'Administrador'),
        ('cliente', 'Cliente'),
    ]
    tipo_usuario = models.CharField(max_length=10, choices=TIPO_USUARIO, default='cliente')
    cel_user = models.CharField(max_length=10, verbose_name="Celular")
    
    class Meta:
        db_table = 'Usuario'
    
#Categoria
class Categoria(models.Model):
    id_cat = models.AutoField(primary_key=True)
    tipo_cat = models.CharField(max_length=100)
    
    class Meta:
        db_table = 'Categoria'
    
#Producto 
class Producto(models.Model):
    ESTADOS=[
        ('Agotado', 'Agotado'),
        ('Disponible', 'Disponible'),
    ]
    id_prod = models.AutoField(primary_key=True)
    nomb_prod = models.CharField(max_length=200)
    descrip_prod = models.TextField()
    img_prod = models.ImageField(upload_to='productos/' )
    esta_prod = models.CharField(max_length=20, choices=ESTADOS, default='Agotado')
    borrado_prod = models.BooleanField(default=False)
    fechcreac_prod = models.DateField(auto_now_add=True)
    fechactu_prod = models.DateField(auto_now=True)
    categorias = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='productos' )
    
    class Meta:
        db_table = 'Producto'

#Inventario
class Inventario(models.Model):
    id_inve = models.AutoField(primary_key=True)
    precunit_prod = models.DecimalField(max_digits=10, decimal_places=2)
    stock_actual = models.IntegerField(default=0)
    fechacrea_inve= models.DateField(auto_now_add=True)
    fechactu_inve = models.DateField(auto_now=True)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='inventario',)
    
    class Meta:
        db_table = 'Inventario'
    
    def actualizar_stock(self, cantidad, tipo):
        if tipo == 'Entrada':
            self.stock_actual += cantidad
        elif tipo == 'Salida' and self.stock_actual >= cantidad:
            self.stock_actual -= cantidad
        else:
            raise ValueError("Stock insuficiente para realizar la operación.")
        self.save()
    

#Carrito
class Carrito(models.Model):
    id_carr = models.AutoField(primary_key=True)
    fechacreac_carr = models.DateTimeField(auto_now_add=True)
    usuarios = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='carritos')
    productos = models.ManyToManyField(Producto)
    
    class Meta:
        db_table = 'Carrito'
    
    def total_carrito(self):
        total = sum([detalle.subtotal for detalle in self.detallecarrito_set.all()])
        return total
    
# DetalleCarrito (Tabla intermedia)
class DetalleCarrito(models.Model):
    id_detcarr = models.AutoField(primary_key=True)
    carrito = models.ForeignKey(Carrito, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    

    @property
    def subtotal(self):
        if hasattr(self.producto, 'inventario'):
            return self.producto.inventario.precunit_prod * self.cantidad
        else:
            return 0  # Si no existe inventario, el subtotal es 0d
        
    class Meta:
        db_table = 'DetalleCarrito'


#Orden 
class Orden(models.Model):
    ORDENES=[
        ('Pendiente','Pendiente'),
        ('Entregado','Entregado'),
        ('Rechazado','Rechazado')
    ]
    id_ord = models.AutoField(primary_key=True)
    direc_entre = models.TextField()
    metodo_pago = models.CharField(max_length=100)
    estado_ord = models.CharField(max_length=20, choices=ORDENES, default='Pendiente')
    fechacrea_ord = models.DateField(auto_now_add=True)
    fechactua_ord = models.DateField(auto_now=True)
    usuarios = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='ordenes')
    carrito = models.ForeignKey(Carrito, on_delete=models.SET_NULL, null=True, blank=True, related_name='ordenes')
    
    @property
    def total_pagar(self):
        return sum([detalle.subtotal for detalle in self.detalles.all()])
    
    class Meta:
        db_table = 'Orden'
    
#DetalleOrden
class DetalleOrden (models.Model):
    id_detord = models.AutoField(primary_key=True)
    cantidad = models.IntegerField(default=0)
    
    
    orden = models.ForeignKey(Orden, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    
    @property
    def subtotal(self):
        if hasattr(self.producto, 'inventario'):
            return self.producto.inventario.precunit_prod * self.cantidad
        return 0
    
    class Meta:
        db_table = 'DetalleOrden'



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
    
    class Meta:
        db_table = 'RegistroPago'
    
#DetalleTransferencia
class DetalleTrans(models.Model):
    BANCOS=[
        ('Banco Produbanco', 'Banco Produbanco'),
        ('Banco Pichincha', 'Banco Pichincha'),
    ]
    id_detaltrans = models.AutoField(primary_key=True)
    monto_trans = models.DecimalField(max_digits=10, decimal_places=2)
    banco_transfe = models.CharField(max_length=50, choices=BANCOS, default='Banco Pichincha')
    codigo_compro = models.CharField(max_length=25,unique=True)
    comentario = models.TextField()
    fecha_trans = models.DateField()
    registro_pago = models.ForeignKey(RegistroPago, on_delete=models.CASCADE, related_name='regispagos')
    
    class Meta:
        db_table = 'DetalleTrans'
    
# Movimiento de Inventario
class MovimientoInventario(models.Model):
    TIPO_MOVIMIENTO = [
        ('Entrada', 'Entrada'),
        ('Salida', 'Salida'),
    ]
    
    id_mov = models.AutoField(primary_key=True)
    tipo = models.CharField(max_length=10, choices=TIPO_MOVIMIENTO)
    cantidad = models.IntegerField()
    fecha = models.DateTimeField(auto_now_add=True)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='movimientos')
    observacion = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'MovimientoInventario'
    
