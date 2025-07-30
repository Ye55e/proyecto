from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

# Usuario
class Usuario(AbstractUser):
    TIPO_USUARIO = [
        ('admin', 'Administrador'),
        ('cliente', 'Cliente'),
    ]
    tipo_usuario = models.CharField(max_length=10, choices=TIPO_USUARIO, default='cliente')
    cel_user = models.CharField(max_length=10, verbose_name="Celular")
    es_dios = models.BooleanField(default=False)

    class Meta:
        db_table = 'usuario'


# Categoria
class Categoria(models.Model):
    id_cat = models.AutoField(primary_key=True)
    tipo_cat = models.CharField(max_length=100)

    class Meta:
        db_table = 'categoria'
#PROVEEDOR

class Proveedor(models.Model):
    id_prov = models.AutoField(primary_key=True)
    nombre_prov = models.CharField(max_length=200, verbose_name="Nombre del Proveedor")
    direccion_prov = models.CharField(max_length=255, verbose_name="Dirección del Proveedor")
    telefono_prov = models.CharField(max_length=20, verbose_name="Teléfono del Proveedor")
    correo_prov = models.EmailField(verbose_name="Correo Electrónico")
    contacto_prov = models.CharField(max_length=150, verbose_name="Nombre de Contacto")
    activo = models.BooleanField(default=True, verbose_name="¿Activo?")

    class Meta:
        db_table = 'proveedor'

    def __str__(self):
        return self.nombre_prov


# Producto
class Producto(models.Model):
    id_prod = models.AutoField(primary_key=True)
    nomb_prod = models.CharField(max_length=200)
    descrip_prod = models.TextField()
    img_prod = models.ImageField(upload_to='productos/')
    borrado_prod = models.BooleanField(default=False)
    fechcreac_prod = models.DateField(auto_now_add=True)
    fechactu_prod = models.DateField(auto_now=True)
    marca = models.CharField(max_length=100, null=True, blank=True)
    id_cat = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='productos', db_column='id_cat')
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, related_name='productos', db_column='id_prov', null=True)
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)



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

    def actualizar_stock(self, cantidad, tipo, nuevo_precio=None, observacion=None):
        if tipo == 'Entrada':
            self.stock_actual += cantidad

            if nuevo_precio is not None:
                # Establecer el mayor entre el actual y el nuevo precio
                self.precunit_prod = max(self.precunit_prod, nuevo_precio)

        elif tipo == 'Salida':
            if self.stock_actual >= cantidad:
                self.stock_actual -= cantidad
            else:
                raise ValueError("Stock insuficiente para realizar la operación.")
        else:
            raise ValueError("Tipo de movimiento no válido.")

        precio_anterior = self.precunit_prod  # Guardamos antes del save si lo prefieres más exacto

        self.save()
        self.actualizar_estado_producto()

        MovimientoInventario.objects.create(
            tipo=tipo,
            cantidad=cantidad,
            precio_uni=self.precunit_prod,
            precio_anterior=precio_anterior,
            producto=self.producto,
            observacion=observacion
        )




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

#BANCO 
class Banco(models.Model):
    TIPO_CUENTA = [
        ('Ahorros', 'Ahorros'),
        ('Corriente', 'Corriente'),
    ]

    id_banco = models.AutoField(primary_key=True)
    nombre_banco= models.CharField(max_length=100, verbose_name="Nombre del Banco")
    numero_cuenta = models.CharField(max_length=20, verbose_name="Número de Cuenta")
    tipo_cuenta = models.CharField(max_length=10, choices=TIPO_CUENTA, verbose_name="Tipo de Cuenta")
    nombre_titular = models.CharField(max_length=150, verbose_name="Nombre del Titular")
    identificacion_titular = models.CharField(max_length=13, verbose_name="Cédula o RUC del Titular")
    activo = models.BooleanField(default=True, verbose_name="¿Activo?")

    class Meta:
        db_table = 'banco'

    def __str__(self):
        return f"{self.nombre} - {self.numero_cuenta} ({self.nombre_titular})"

class Orden(models.Model):
    ESTADO_CHOICES = [
        ('Pendiente', 'Pendiente'),
        ('Entregado', 'Entregado'),
        ('Rechazado', 'Rechazado'),
    ]
    TIPO_DOCUMENTO_CHOICES = [
        ('cedula', 'Cédula'),
        ('ruc', 'RUC'),
        ('pasaporte', 'Pasaporte'),
    ]

    id_ord = models.AutoField(primary_key=True)
    nombre_cliente = models.CharField(max_length=150)
    tipo_documento = models.CharField(max_length=10, choices=TIPO_DOCUMENTO_CHOICES, default='cedula')
    numero_documento = models.CharField(max_length=20) 
    correo_cliente = models.EmailField()
    direccion_cliente = models.CharField(max_length=255)
    ciudad_cliente = models.CharField(max_length=100)
    telefono_cliente = models.CharField(max_length=10)

    direc_entre = models.TextField()
    metodo_pago = models.CharField(max_length=100)
    num_trans = models.CharField(max_length=20, null=True, blank=True)
    metodo_entrega = models.CharField(max_length=10, choices=[('local', 'Local'), ('envio', 'Envío')], default='local') 
    fecha_trans= models.DateField(null=True, blank=True)
    estado_ord = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='Pendiente')
    fechacrea_ord = models.DateField(auto_now_add=True)
    fecha_expira = models.DateTimeField(null=True, blank=True) 
    fechactua_ord = models.DateField(auto_now=True)
    banco = models.ForeignKey(
    Banco,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    
    db_column='id_banco'
)

    usuarios = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column='id_user')
    carrito = models.ForeignKey(Carrito, on_delete=models.SET_NULL, null=True, blank=True, db_column='id_carr')

    class Meta:
        db_table = 'orden'


from decimal import Decimal

# DetalleOrden
class DetalleOrden(models.Model):
    id_detord = models.AutoField(primary_key=True)
    cantidad = models.IntegerField(default=0)
    orden = models.ForeignKey(Orden, on_delete=models.CASCADE, related_name='detalles', db_column='id_ord')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, db_column='id_prod')
    precio_aplicado = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    iva_aplicado = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    
    @property
    def subtotal(self):
        return self.precio_aplicado * self.cantidad
    

    @property
    def total_con_iva(self):
        return self.subtotal * (1 + self.iva_aplicado / 100)

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


# MovimientoInventario
class MovimientoInventario(models.Model):
    TIPO_MOVIMIENTO = [
        ('Entrada', 'Entrada'),
        ('Salida', 'Salida'),
    ]
    id_mov = models.AutoField(primary_key=True)
    tipo = models.CharField(max_length=10, choices=TIPO_MOVIMIENTO)
    cantidad = models.IntegerField()
    precio_uni = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True) 
    precio_anterior = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True) 
    fecha = models.DateTimeField(auto_now_add=True)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='movimientos', db_column='id_prod')
    observacion = models.TextField(blank=True, null=True)

    @property
    def precio_venta(self):
        if self.precio_uni is not None and self.precio_anterior is not None:
            return max(self.precio_uni, self.precio_anterior)
        return self.precio_uni or self.precio_anterior or 0

    class Meta:
        db_table = 'movimiento_inventario'

#FILTRADO DE PRODUCTOS 
#NOTIFICACIONES

from django.contrib.auth import get_user_model

User = get_user_model()

class Notificacion(models.Model):
    id_noti=models.AutoField(primary_key=True)
    titulo = models.CharField(max_length=100)
    mensaje = models.TextField()
    fecha_noti = models.DateTimeField(auto_now_add=True)
    leido = models.BooleanField(default=False)
    usuario_destino = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        db_table = 'notificacion'

    def __str__(self):
        return f"{self.titulo} - {self.usuario_destino.username}"


#IMPUESTO
from django.utils import timezone

class Impuesto(models.Model):
    id_impuesto = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)  # Ej: 'IVA', 'ICE'
    valor = models.DecimalField(max_digits=5, decimal_places=2)  # Ej: 12.00 = 12%
    estado = models.BooleanField(default=True)  # Activo (True) o Inactivo (False)
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'impuesto'

    def __str__(self):
        return f"{self.nombre} ({self.valor}%)"

    def save(self, *args, **kwargs):
        if self.estado:
            # Desactivar otros impuestos activos (excluyendo este)
            Impuesto.objects.filter(estado=True).exclude(pk=self.pk).update(estado=False)
        super().save(*args, **kwargs)