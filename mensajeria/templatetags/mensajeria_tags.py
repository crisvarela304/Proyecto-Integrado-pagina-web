from django import template

register = template.Library()

@register.filter
def mensajeria_no_leidos(conversacion, usuario):
    """
    Retorna el número de mensajes no leídos para el usuario en la conversación.
    Uso: {{ conversacion|mensajeria_no_leidos:usuario_actual }}
    """
    return conversacion.get_contador_no_leidos(usuario)

@register.filter
def mensajeria_otro_participante(conversacion, usuario):
    """
    Retorna el otro participante de la conversación.
    Uso: {{ conversacion|mensajeria_otro_participante:usuario_actual }}
    """
    return conversacion.get_otro_participante(usuario)
