from django import template
from django.contrib.humanize.templatetags.humanize import intcomma

register = template.Library()

@register.filter
def moeda_br(value):
    """Formata valor numérico como moeda brasileira: 1.234,56"""
    if value is None:
        return 'R$ 0,00'
    try:
        valor = float(value)
    except (ValueError, TypeError):
        return 'R$ 0,00'
    
    # Separar parte inteira e decimal
    negativo = valor < 0
    valor = abs(valor)
    parte_inteira = int(valor)
    parte_decimal = round((valor - parte_inteira) * 100)
    
    # Se decimal arredondou para 100, ajustar
    if parte_decimal >= 100:
        parte_inteira += 1
        parte_decimal = 0
    
    # Formatar parte inteira com separador de milhar (ponto)
    inteira_str = intcomma(parte_inteira).replace(',', '.')
    
    resultado = f"R$ {inteira_str},{parte_decimal:02d}"
    if negativo:
        resultado = f"- {resultado}"
    return resultado


@register.filter
def moeda_br_sembase(value):
    """Formata valor como moeda brasileira sem o R$"""
    if value is None:
        return '0,00'
    try:
        valor = float(value)
    except (ValueError, TypeError):
        return '0,00'
    
    negativo = valor < 0
    valor = abs(valor)
    parte_inteira = int(valor)
    parte_decimal = round((valor - parte_inteira) * 100)
    
    if parte_decimal >= 100:
        parte_inteira += 1
        parte_decimal = 0
    
    inteira_str = intcomma(parte_inteira).replace(',', '.')
    resultado = f"{inteira_str},{parte_decimal:02d}"
    if negativo:
        resultado = f"- {resultado}"
    return resultado
