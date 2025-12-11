import re

def limpiar_rut(rut):
    """
    Limpia y formatea un RUT chileno.
    Elimina puntos y guiones, y convierte a mayúsculas.
    """
    if not rut:
        return ""
    return rut.strip().replace('.', '').replace('-', '').upper()

def formatear_rut(rut):
    """
    Formatea un RUT para que tenga el formato XXXXXXXX-X.
    Elimina puntos y asegura que exista el guion.
    """
    rut_limpio = limpiar_rut(rut)
    if len(rut_limpio) < 2:
        return rut_limpio
    
    return f"{rut_limpio[:-1]}-{rut_limpio[-1]}"

def validar_rut(rut):
    """
    Valida un RUT chileno.
    Retorna True si el RUT es válido, False en caso contrario.
    """
    if not rut:
        return False
    
    # Limpiar RUT
    rut = limpiar_rut(rut)
    
    if len(rut) < 2:
        return False
    
    # Separar cuerpo y dígito verificador
    cuerpo = rut[:-1]
    dv = rut[-1]
    
    try:
        # Calcular dígito verificador
        suma = 0
        multiplicador = 2
        
        for digito in reversed(cuerpo):
            suma += int(digito) * multiplicador
            multiplicador += 1
            if multiplicador == 8:
                multiplicador = 2
        
        resto = suma % 11
        dv_calculado = 11 - resto
        
        if dv_calculado == 11:
            dv_calculado = '0'
        elif dv_calculado == 10:
            dv_calculado = 'K'
        else:
            dv_calculado = str(dv_calculado)
        
        return dv == dv_calculado
    except ValueError:
        return False
