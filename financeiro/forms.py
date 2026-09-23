from django import forms
from .models import Conta, Lancamento, Caixa, PlanoDeContas

# --- FORMULÁRIO DE CAIXA / BANCO ---
class CaixaForm(forms.ModelForm):
    class Meta:
        model = Caixa
        fields = ['nome', 'saldo_inicial']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        for field_name, field in self.fields.items():
            if field_name == 'saldo_inicial':
                # AQUI ESTÁ A CORREÇÃO: pl-10 (Espaço na esquerda para o R$)
                field.widget.attrs['class'] = 'w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            else:
                # Padrão para o campo Nome
                field.widget.attrs['class'] = 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
                
# --- FORMULÁRIO DE PLANO DE CONTAS ---
class PlanoContasForm(forms.ModelForm):
    class Meta:
        model = PlanoDeContas
        fields = ['codigo', 'nome', 'tipo']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-gray-300 rounded-md bg-white'}),
        }
    
    def __init__(self, *args, **kwargs):
        # Captura o usuário para saber a empresa
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        for field in self.fields.values():
            if 'class' not in field.widget.attrs:
                 field.widget.attrs['class'] = 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'

    # --- VALIDAÇÃO DE CÓDIGO ÚNICO ---
    def clean_codigo(self):
        codigo = self.cleaned_data.get('codigo')
        
        if self.user and codigo:
            # Verifica se existe outro plano com esse código NA MESMA EMPRESA
            existe = PlanoDeContas.objects.filter(
                empresa=self.user.empresa,
                codigo=codigo
            ).exclude(id=self.instance.id).exists() # exclude impede erro na edição do próprio item

            if existe:
                raise forms.ValidationError("Este Código já está em uso nesta empresa.")
        
        return codigo
    

class ContaForm(forms.ModelForm):
    # --- CAMPOS EXTRAS PARA PARCELAMENTO (Não salvos no banco) ---
    gerar_parcelas = forms.BooleanField(required=False, label="Parcelar este lançamento?", widget=forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'}))
    qtd_parcelas = forms.IntegerField(required=False, min_value=2, max_value=60, label="Qtd. Parcelas", initial=2)
    taxa_juros = forms.DecimalField(required=False, min_value=0, max_value=100, label="Juros Total (%)", initial=0, help_text="Acréscimo sobre o total")

    class Meta:
        model = Conta
        fields = ['descricao', 'plano_de_contas', 'cadastro', 'valor', 'data_vencimento', 'observacoes']
        widgets = {
            'data_vencimento': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'observacoes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        tipo_filtro = kwargs.pop('tipo_filtro', None)
        super().__init__(*args, **kwargs)
        
        # Estilização Padrão
        estilo_input = 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
        
        for field_name, field in self.fields.items():
            if field_name == 'valor':
                field.widget.attrs['class'] = 'w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            elif field_name == 'gerar_parcelas':
                pass # Checkbox já estilizado na definição
            else:
                field.widget.attrs['class'] = estilo_input
        
        # Filtros SaaS
        if user:
            qs = PlanoDeContas.objects.filter(empresa=user.empresa)
            if tipo_filtro:
                qs = qs.filter(tipo=tipo_filtro)
            self.fields['plano_de_contas'].queryset = qs
            
            from cadastros.models import Cadastro
            # Filtro inteligente de cadastro (Cliente ou Fornecedor)
            qs_cadastro = Cadastro.objects.filter(empresa=user.empresa)
            if tipo_filtro == 'R':
                qs_cadastro = qs_cadastro.filter(papel__in=['CLI', 'AMB'])
            elif tipo_filtro == 'D':
                qs_cadastro = qs_cadastro.filter(papel__in=['FOR', 'AMB'])
            self.fields['cadastro'].queryset = qs_cadastro

    def clean(self):
        cleaned_data = super().clean()
        gerar = cleaned_data.get('gerar_parcelas')
        qtd = cleaned_data.get('qtd_parcelas')
        
        if generating := gerar:
            if not qtd or qtd < 2:
                self.add_error('qtd_parcelas', "Informe a quantidade maior que 1.")
        return cleaned_data
                
# --- FORMULÁRIO DE LANÇAMENTO MANUAL ---
class LancamentoManualForm(forms.ModelForm):
    class Meta:
        model = Lancamento
        fields = ['caixa', 'data_lancamento', 'tipo', 'plano_de_contas', 'forma_pagamento', 'descricao', 'valor']
        widgets = {
            # CORREÇÃO AQUI: format='%Y-%m-%d'
            'data_lancamento': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'forma_pagamento': forms.Select(attrs={'class': 'form-select border rounded p-2 w-full'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # forma_pagamento opcional
        if 'forma_pagamento' in self.fields:
            self.fields['forma_pagamento'].required = False
            self.fields['forma_pagamento'].empty_label = "--- Selecione ---"
        
        for field_name, field in self.fields.items():
            if field_name == 'valor':
                field.widget.attrs['class'] = 'w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            elif field_name == 'forma_pagamento':
                if 'class' not in field.widget.attrs or 'form-select' not in field.widget.attrs['class']:
                    field.widget.attrs['class'] = 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            else:
                field.widget.attrs['class'] = 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
        
        if user and hasattr(user, 'empresa') and user.empresa:
            self.fields['caixa'].queryset = Caixa.objects.filter(empresa=user.empresa)
            self.fields['plano_de_contas'].queryset = PlanoDeContas.objects.filter(empresa=user.empresa)
            try:
                from servicos.models import FormaPagamento
                self.fields['forma_pagamento'].queryset = FormaPagamento.objects.filter(empresa=user.empresa, ativo=True).order_by('ordem', 'nome')
            except Exception:
                pass

