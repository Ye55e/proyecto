# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Usuario 

# Formulario de REGISTRO para clientes
class FormRegistroCliente(UserCreationForm):
    email = forms.EmailField(required=True, label="Correo Electrónico")
    cel_user = forms.CharField(label="Celular", max_length=10)

    class Meta:
        model = Usuario
        fields = ['username', 'email', 'cel_user', 'password1', 'password2']
        labels = {
            'username': 'Nombre de usuario',
            'password1': 'Contraseña',
            'password2': 'Confirmar contraseña',
        }

# Formulario de LOGIN para todos los usuarios
class FormLogin(AuthenticationForm):
    username = forms.CharField(label="Nombre de usuario")
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput)
