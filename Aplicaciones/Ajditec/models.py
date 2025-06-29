from django.db import models
from django.contrib.auth.models import AbstractUser

# Usuario
class Usuario(AbstractUser):
    TIPO_USUARIO = [
        ('admin', 'Administrador'),
        ('cliente', 'Cliente'),
    ]
    tipo_usuario = models.CharField(max_length=10, choices=TIPO_USUARIO, default='cliente')
    cel_user = models.CharField(max_length=10, verbose_name="Celular")

    class Meta:
        db_table = 'usuario'


# Categoria
class Categoria(models.Model):
    id_cat = models.AutoField(primary_key=True)
    tipo_cat = models.CharField(max_length=100)

    class Meta:
        db_table = 'categoria'


# Producto
class Producto(models.Model):
    id_prod = models.AutoField(primary_key=True)
    nomb_prod = models.CharField(max_length=200)
    descrip_prod = models.TextField()
    img_prod = models.ImageField(upload_to='productos/')
    borrado_prod = models.BooleanField(default=False)
    fechcreac_prod = models.DateField(auto_now_add=True)
    fechactu_prod = models.DateField(auto_now=True)
    id_cat = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='productos', db_column='id_cat')

    class Meta:
        db_table = 'producto'


# Inventario
class Inventario(models.Model):
    id_inve = models.AutoField(primary_key=True)
    producto = models.OneToOneField(
        Producto,
        on_delete=models.CASCADE,
        related_name='inventario',
        db_column='id_prod',
        verbose_name="Producto"
    )
    precunit_prod = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Precio Unitario"
    )
    stock_actual = models.IntegerField(
        default=0,
        verbose_name="Stock Actual"
    )
    fechacrea_inve = models.DateField(
        auto_now_add=True,
        verbose_name="Fecha Creación"
    )
    fechactu_inve = models.DateField(
        auto_now=True,
        verbose_name="Fecha Actualización"
    )

    class Meta:
        db_table = 'inventario'
        verbose_name = 'Inventario'
        verbose_name_plural = 'Inventarios'

    def actualizar_estado_producto(self):
        if self.stock_actual < 2:
            self.producto.esta_prod = 'Agotado'
        else:
            self.producto.esta_prod = 'Disponible'
        self.producto.save()

    def actualizar_stock(self, cantidad, tipo):
        if tipo == 'Entrada':
            self.stock_actual += cantidad
        elif tipo == 'Salida' and self.stock_actual >= cantidad:
            self.stock_actual -= cantidad
        else:
            raise ValueError("Stock insuficiente para realizar la operación.")
        self.save()
        self.actualizar_estado_producto()



# Carrito
class Carrito(models.Model):
    id_carr = models.AutoField(primary_key=True)
    fechacreac_carr = models.DateTimeField(auto_now_add=True)
    usuarios = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='carritos', db_column='id_user')
    session_key = models.CharField(max_length=40, null=True, blank=True)
    estado_carr = models.CharField(
    max_length=10,
    choices=[('activo', 'Activo'), ('pagado', 'Pagado')],
    default='activo'
)


    class Meta:
        db_table = 'carrito'

    def total_carrito(self):
        total = sum([detalle.subtotal for detalle in self.detalles.all()])
        return total


# DetalleCarrito (tabla intermedia)
class DetalleCarrito(models.Model):
    id_detcarr = models.AutoField(primary_key=True)
    carrito = models.ForeignKey(Carrito, on_delete=models.CASCADE, related_name='detalles', db_column='id_carr')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, db_column='id_prod')
    cantidad = models.PositiveIntegerField(default=1)

    @property
    def subtotal(self):
        if hasattr(self.producto, 'inventario'):
            return self.producto.inventario.precunit_prod * self.cantidad
        else:
            return 0

    class Meta:
        db_table = 'detalle_carrito'


# models.py

class Orden(models.Model):
    ESTADO_CHOICES = [
        ('Pendiente', 'Pendiente'),
        ('Entregado', 'Entregado'),
        ('Rechazado', 'Rechazado'),
    ]

    id_ord = models.AutoField(primary_key=True)
    nombre_cliente = models.CharField(max_length=150)
    cedula_ruc = models.CharField(max_length=13)
    correo_cliente = models.EmailField()
    direccion_cliente = models.CharField(max_length=255)
    ciudad_cliente = models.CharField(max_length=100)
    telefono_cliente = models.CharField(max_length=10)

    direc_entre = models.TextField()
    metodo_pago = models.CharField(max_length=100)
    num_trans = models.CharField(max_length=20, null=True, blank=True)
    fecha_trans= models.DateField(null=True, blank=True)
    estado_ord = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='Pendiente')
    fechacrea_ord = models.DateField(auto_now_add=True)
    fechactua_ord = models.DateField(auto_now=True)

    usuarios = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column='id_user')
    carrito = models.ForeignKey(Carrito, on_delete=models.SET_NULL, null=True, blank=True, db_column='id_carr')

    class Meta:
        db_table = 'orden'



# DetalleOrden
class DetalleOrden(models.Model):
    id_detord = models.AutoField(primary_key=True)
    cantidad = models.IntegerField(default=0)
    orden = models.ForeignKey(Orden, on_delete=models.CASCADE, related_name='detalles', db_column='id_ord')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, db_column='id_prod')

    @property
    def subtotal(self):
        if hasattr(self.producto, 'inventario'):
            return self.producto.inventario.precunit_prod * self.cantidad
        return 0

    class Meta:
        db_table = 'detalle_orden'


# RegistroPago
class RegistroPago(models.Model):
    ESTADO = [
        ('Confirmado', 'Confirmado'),
        ('Pendiente', 'Pendiente'),
        ('Rechazado', 'Rechazado'),
    ]
    id_regpag = models.AutoField(primary_key=True)
    total_pago = models.DecimalField(max_digits=10, decimal_places=2)
    orden = models.ForeignKey(Orden, on_delete=models.CASCADE, related_name='pagos', db_column='id_ord')
    fech_crea = models.DateField(auto_now_add=True)
    estado_reg = models.CharField(max_length=20, choices=ESTADO, default='Confirmado')

    class Meta:
        db_table = 'registro_pago'


# DetalleTransferencia
class DetalleTrans(models.Model):
    BANCOS = [
        ('Banco Produbanco', 'Banco Produbanco'),
        ('Banco Pichincha', 'Banco Pichincha'),
    ]
    id_detaltrans = models.AutoField(primary_key=True)
    monto_trans = models.DecimalField(max_digits=10, decimal_places=2)
    banco_transfe = models.CharField(max_length=50, choices=BANCOS, default='Banco Pichincha')
    codigo_compro = models.CharField(max_length=25, unique=True)
    fecha_trans = models.DateField()
    registro_pago = models.ForeignKey(RegistroPago, on_delete=models.CASCADE, related_name='regispagos', db_column='id_regpag')

    class Meta:
        db_table = 'detalle_trans'


# MovimientoInventario
class MovimientoInventario(models.Model):
    TIPO_MOVIMIENTO = [
        ('Entrada', 'Entrada'),
        ('Salida', 'Salida'),
    ]
    id_mov = models.AutoField(primary_key=True)
    tipo = models.CharField(max_length=10, choices=TIPO_MOVIMIENTO)
    cantidad = models.IntegerField()
    fecha = models.DateTimeField(auto_now_add=True)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='movimientos', db_column='id_prod')
    observacion = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'movimiento_inventario'
