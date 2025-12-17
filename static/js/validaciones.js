/**
 * LiceoOS - Validaciones de Formularios
 * Este archivo contiene funciones de validación reutilizables para todo el proyecto
 */

// =====================================================
// VALIDACIÓN DE RUT CHILENO
// =====================================================

/**
 * Formatear RUT mientras escribe (XX.XXX.XXX-X)
 */
function formatearRUT(valor) {
    // Limpiar todo excepto números y K
    let rut = valor.replace(/[^0-9kK]/g, '').toUpperCase();
    if (rut.length === 0) return '';

    // Separar cuerpo y dígito verificador
    let dv = rut.slice(-1);
    let cuerpo = rut.slice(0, -1);

    // Agregar puntos al cuerpo
    cuerpo = cuerpo.replace(/\B(?=(\d{3})+(?!\d))/g, '.');

    return cuerpo.length > 0 ? cuerpo + '-' + dv : dv;
}

/**
 * Calcular dígito verificador usando algoritmo módulo 11
 */
function calcularDV(rut) {
    let suma = 0;
    let multiplo = 2;

    for (let i = rut.length - 1; i >= 0; i--) {
        suma += parseInt(rut[i]) * multiplo;
        multiplo = multiplo === 7 ? 2 : multiplo + 1;
    }

    let residuo = suma % 11;
    let dv = 11 - residuo;

    if (dv === 11) return '0';
    if (dv === 10) return 'K';
    return dv.toString();
}

/**
 * Validar RUT completo (formato y dígito verificador)
 */
function validarRUT(rutCompleto) {
    if (!rutCompleto || rutCompleto.length < 3) return false;

    // Limpiar
    let rut = rutCompleto.replace(/[^0-9kK]/g, '').toUpperCase();
    if (rut.length < 2) return false;

    let dv = rut.slice(-1);
    let cuerpo = rut.slice(0, -1);

    // Validar que el cuerpo sean solo números
    if (!/^\d+$/.test(cuerpo)) return false;

    // Calcular y comparar DV
    return calcularDV(cuerpo) === dv;
}

// =====================================================
// VALIDACIÓN DE NOTAS (1.0 - 7.0)
// =====================================================

/**
 * Validar si un valor es una nota válida
 */
function esNotaValida(valor) {
    if (!valor || valor.trim() === '' || valor === '-') return true;
    const num = parseFloat(valor.replace(',', '.'));
    return !isNaN(num) && num >= 1.0 && num <= 7.0;
}

/**
 * Formatear nota a formato correcto (X.X)
 */
function formatearNota(valor) {
    if (!valor || valor.trim() === '') return '';
    let num = parseFloat(valor.replace(',', '.'));
    if (isNaN(num)) return '';
    num = Math.round(num * 10) / 10;
    if (num < 1.0) num = 1.0;
    if (num > 7.0) num = 7.0;
    return num.toFixed(1);
}

// =====================================================
// INICIALIZACIÓN AUTOMÁTICA
// =====================================================

document.addEventListener('DOMContentLoaded', function () {

    // ===== Inicializar inputs de RUT =====
    const rutInputs = document.querySelectorAll('.rut-input');
    rutInputs.forEach(input => {
        input.addEventListener('input', function () {
            let valor = this.value;
            let cursorPos = this.selectionStart;
            let antiguaLongitud = valor.length;

            this.value = formatearRUT(valor);

            let nuevaLongitud = this.value.length;
            let diff = nuevaLongitud - antiguaLongitud;
            this.setSelectionRange(cursorPos + diff, cursorPos + diff);

            this.classList.remove('is-valid', 'is-invalid');
        });

        input.addEventListener('blur', function () {
            let valor = this.value.trim();
            if (valor.length > 0) {
                if (validarRUT(valor)) {
                    this.classList.remove('is-invalid');
                    this.classList.add('is-valid');
                } else {
                    this.classList.remove('is-valid');
                    this.classList.add('is-invalid');
                }
            } else {
                this.classList.remove('is-valid', 'is-invalid');
            }
        });

        input.addEventListener('keypress', function (e) {
            const char = String.fromCharCode(e.which).toUpperCase();
            if (!/[0-9kK.-]/.test(char)) {
                e.preventDefault();
            }
        });
    });

    // ===== Inicializar inputs de Notas =====
    const notaInputs = document.querySelectorAll('.nota-input');
    notaInputs.forEach(input => {
        input.addEventListener('keypress', function (e) {
            const char = String.fromCharCode(e.which);
            const currentValue = this.value;

            if (!/[0-9.,]/.test(char)) {
                e.preventDefault();
                return;
            }

            if ((char === '.' || char === ',') && (currentValue.includes('.') || currentValue.includes(','))) {
                e.preventDefault();
                return;
            }

            if (currentValue === '' && !/[1-7]/.test(char)) {
                e.preventDefault();
                return;
            }
        });

        input.addEventListener('blur', function () {
            let valor = this.value.trim();

            if (valor && valor !== '-') {
                const formateado = formatearNota(valor);
                this.value = formateado;

                if (!esNotaValida(formateado)) {
                    this.classList.add('is-invalid');
                    this.classList.remove('is-valid');
                } else {
                    this.classList.remove('is-invalid');
                    this.classList.add('is-valid');
                }
            } else {
                this.classList.remove('is-invalid', 'is-valid');
            }
        });

        input.addEventListener('input', function () {
            const valor = this.value.trim();
            this.classList.remove('is-invalid', 'is-valid');

            if (valor.length === 1 && /[089]/.test(valor)) {
                this.value = '';
                this.classList.add('is-invalid');
            }

            const num = parseFloat(valor.replace(',', '.'));
            if (!isNaN(num) && num > 7.0) {
                this.classList.add('is-invalid');
            }
        });
    });
});

// =====================================================
// EXPORTAR FUNCIONES PARA USO EN OTRAS PARTES
// =====================================================
window.LiceoOS = window.LiceoOS || {};
window.LiceoOS.validarRUT = validarRUT;
window.LiceoOS.formatearRUT = formatearRUT;
window.LiceoOS.esNotaValida = esNotaValida;
window.LiceoOS.formatearNota = formatearNota;
