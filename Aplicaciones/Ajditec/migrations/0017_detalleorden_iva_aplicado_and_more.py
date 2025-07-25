# Generated by Django 5.1.3 on 2025-07-14 22:21

from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Ajditec', '0016_remove_orden_cedula_ruc_orden_numero_documento_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='detalleorden',
            name='iva_aplicado',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=5),
        ),
        migrations.AddField(
            model_name='detalleorden',
            name='precio_aplicado',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10),
        ),
    ]
