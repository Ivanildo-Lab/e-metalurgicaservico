from django import forms
from .models import (
    Funcionario, OrdemServico, ServicoOS, FuncionarioOS,
    MetaFuncionario, Orcamento, ServicoOrcamento, FormaPagamento
)
from cadastros.models import Cadastro


class FuncionarioForm(forms.ModelForm):
    class Meta:
        model = Funcionario
        fields = ['nome', 'telefone', 'email', 'ativo', 'observacoes']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = (
                'w-full px-3 py-2 border border-gray-300 rounded-lg '
                'focus:ring-2 focus:ring-blue-500 focus:border-blue-500 '
                'text-sm transition duration-150'
            )
        self.fields['observacoes'].widget.attrs['rows'] = 3


class OrdemServicoForm(forms.ModelForm):
    class Meta:
        model = OrdemServico
        fields = ['cadastro', 'descricao_geral', 'data_entrada', 'data_prevista', 'observacoes']
        widgets = {
            'data_entrada': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'data_prevista': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'descricao_geral': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user and self.user.empresa:
            self.fields['cadastro'].queryset = Cadastro.objects.filter(
                empresa=self.user.empresa
            ).order_by('nome')
        for field in self.fields.values():
            field.widget.attrs['class'] = (
                'w-full px-3 py-2 border border-gray-300 rounded-lg '
                'focus:ring-2 focus:ring-blue-500 focus:border-blue-500 '
                'text-sm transition duration-150'
            )
        self.fields['observacoes'].widget.attrs['rows'] = 3


class ServicoOSForm(forms.ModelForm):
    class Meta:
        model = ServicoOS
        fields = ['descricao', 'valor']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = (
                'w-full px-3 py-2 border border-gray-300 rounded-lg '
                'focus:ring-2 focus:ring-blue-500 focus:border-blue-500 '
                'text-sm transition duration-150'
            )


class FuncionarioOSForm(forms.ModelForm):
    class Meta:
        model = FuncionarioOS
        fields = ['funcionario', 'valor_remuneracao']

    def __init__(self, *args, **kwargs):
        self.empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
        if self.empresa:
            self.fields['funcionario'].queryset = Funcionario.objects.filter(
                empresa=self.empresa, ativo=True
            ).order_by('nome')
        for field in self.fields.values():
            field.widget.attrs['class'] = (
                'w-full px-3 py-2 border border-gray-300 rounded-lg '
                'focus:ring-2 focus:ring-blue-500 focus:border-blue-500 '
                'text-sm transition duration-150'
            )


class FecharOSForm(forms.Form):
    """Formulário para fechar uma OS (gera financeiro)"""
    FORMA_PGTO_CHOICES = [
        ('A_VISTA', 'À Vista'),
        ('A_PRAZO', 'A Prazo'),
    ]

    forma_pagamento = forms.ChoiceField(
        choices=FORMA_PGTO_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'flex space-x-4'}),
        label="Forma de Pagamento"
    )
    qtd_parcelas = forms.IntegerField(
        min_value=1, max_value=60, initial=1,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm',
            'min': '1'
        }),
        label="Quantidade de Parcelas"
    )
    caixa = forms.IntegerField(
        widget=forms.HiddenInput(),
        required=False,
        label="Caixa/Banco"
    )


class MetaFuncionarioForm(forms.ModelForm):
    class Meta:
        model = MetaFuncionario
        fields = ['funcionario', 'mes', 'ano', 'meta_valor',
                  'avaliacao_ruim', 'avaliacao_bom', 'avaliacao_otimo']
        widgets = {
            'mes': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user and self.user.empresa:
            self.fields['funcionario'].queryset = Funcionario.objects.filter(
                empresa=self.user.empresa, ativo=True
            ).order_by('nome')
        for name, field in self.fields.items():
            if name != 'mes':
                field.widget.attrs['class'] = (
                    'w-full px-3 py-2 border border-gray-300 rounded-lg '
                    'focus:ring-2 focus:ring-blue-500 focus:border-blue-500 '
                    'text-sm transition duration-150'
                )


class OrcamentoForm(forms.ModelForm):
    class Meta:
        model = Orcamento
        fields = ['cadastro', 'descricao', 'data', 'data_validade', 'observacoes']
        widgets = {
            'data': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'data_validade': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'descricao': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user and self.user.empresa:
            self.fields['cadastro'].queryset = Cadastro.objects.filter(
                empresa=self.user.empresa
            ).order_by('nome')
        for field in self.fields.values():
            field.widget.attrs['class'] = (
                'w-full px-3 py-2 border border-gray-300 rounded-lg '
                'focus:ring-2 focus:ring-blue-500 focus:border-blue-500 '
                'text-sm transition duration-150'
            )
        self.fields['observacoes'].widget.attrs['rows'] = 3


class ServicoOrcamentoForm(forms.ModelForm):
    class Meta:
        model = ServicoOrcamento
        fields = ['descricao', 'valor']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = (
                'w-full px-3 py-2 border border-gray-300 rounded-lg '
                'focus:ring-2 focus:ring-blue-500 focus:border-blue-500 '
                'text-sm transition duration-150'
            )


class FormaPagamentoForm(forms.ModelForm):
    class Meta:
        model = FormaPagamento
        fields = ['nome', 'afeta_caixa', 'ativo', 'ordem']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = (
                'w-full px-3 py-2 border border-gray-300 rounded-lg '
                'focus:ring-2 focus:ring-blue-500 focus:border-blue-500 '
                'text-sm transition duration-150'
            )
