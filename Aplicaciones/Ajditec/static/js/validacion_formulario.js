// Validación de Cédula
function validarCedula(cedula) {
    if (cedula.length !== 13) {
        return false;
    }
    
    // Validar formato
    const regex = /^[0-9]{13}$/;
    if (!regex.test(cedula)) {
        return false;
    }
    
    // Validar dígito verificador
    let total = 0;
    let digito;
    let pares = 0;
    let impares = 0;
    
    for (let i = 0; i < 9; i++) {
        digito = parseInt(cedula.charAt(i));
        if (i % 2 === 0) {
            pares += digito;
        } else {
            let mult = digito * 2;
            if (mult > 9) {
                mult = parseInt(mult / 10) + (mult % 10);
            }
            impares += mult;
        }
    }
    
    total = pares + impares;
    let digitoVerificador = 10 - (total % 10);
    if (digitoVerificador === 10) {
        digitoVerificador = 0;
    }
    
    return digitoVerificador === parseInt(cedula.charAt(9));
}

// Validación de Teléfono con prefijo +593
function validarTelefono(telefono) {
    // Remover el prefijo si existe
    const numero = telefono.replace('+593', '');
    
    // Validar que tenga 10 dígitos
    if (numero.length !== 10) {
        return false;
    }
    
    // Validar que sea un número válido
    const regex = /^[0-9]{10}$/;
    return regex.test(numero);
}

// Formatear número de teléfono
function formatearTelefono(telefono) {
    return '+593 ' + telefono;
}

// Eventos del formulario
document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form');
    const cedulaInput = document.querySelector('input[name="cedula"]');
    const telefonoInput = document.querySelector('input[name="telefono"]');
    
    // Validación de cédula
    cedulaInput.addEventListener('input', function() {
        this.value = this.value.replace(/[^0-9]/g, ''); // Solo números
        if (this.value.length > 13) {
            this.value = this.value.slice(0, 13);
        }
    });
    
    // Validación de teléfono
    telefonoInput.addEventListener('input', function() {
        this.value = this.value.replace(/[^0-9]/g, ''); // Solo números
        if (this.value.length > 10) {
            this.value = this.value.slice(0, 10);
        }
    });
    
    // Formatear teléfono al enviar
    form.addEventListener('submit', function(e) {
        const telefono = telefonoInput.value;
        if (!validarTelefono(telefono)) {
            e.preventDefault();
            alert('El número de teléfono debe tener 10 dígitos y ser válido para Ecuador');
            return;
        }
        
        // Formatear el teléfono
        telefonoInput.value = formatearTelefono(telefono);
    });
});
