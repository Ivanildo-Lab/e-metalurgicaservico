from django import template

register = template.Library()

@register.filter
def moeda_br(valor):
    """Formata valor para o padrão brasileiro: R$ 20.999,99"""
    if valor is None:
        return 'R$ 0,00'
    try:
        valor = float(valor)
    except (ValueError, TypeError):
        return 'R$ 0,00'

    # Formata com 2 casas decimais
    parte_inteira = int(valor)
    parte_decimal = round((valor - parte_inteira) * 100)

    # Ajusta se decimal arredondou para 100
    if parte_decimal >= 100:
        parte_inteira += 1
        parte_decimal = 0

    # Formata parte inteira com pontos como separador de milhar
    s_inteira = f'{parte_inteira:,}'.replace(',', '.')

    return f'R$ {s_inteira},{parte_decimal:02d}'


@register.filter
def moeda_br_valor(valor):
    """Formata valor SEM o R$: 20.999,99"""
    if valor is None:
        return '0,00'
    try:
        valor = float(valor)
    except (ValueError, TypeError):
        return '0,00'

    parte_inteira = int(valor)
    parte_decimal = round((valor - parte_inteira) * 100)

    if parte_decimal >= 100:
        parte_inteira += 1
        parte_decimal = 0

    s_inteira = f'{parte_inteira:,}'.replace(',', '.')

    return f'{s_inteira},{parte_decimal:02d}'
