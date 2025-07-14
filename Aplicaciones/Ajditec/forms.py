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

# Formulario para editar el perfil
from django.contrib.auth.forms import UserChangeForm

class PerfilUsuarioForm(UserChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer el campo tipo_usuario de solo lectura
        self.fields['tipo_usuario'].widget.attrs['readonly'] = True
        self.fields['tipo_usuario'].widget.attrs['disabled'] = True
        # Hacer los otros campos editables
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = Usuario
        fields = ['username', 'email', 'first_name', 'last_name', 'cel_user', 'tipo_usuario']
        labels = {
            'username': 'Nombre de usuario',
            'email': 'Correo electrónico',
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'cel_user': 'Celular',
            'tipo_usuario': 'Tipo de usuario'
        }
