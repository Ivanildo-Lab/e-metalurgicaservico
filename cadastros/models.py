from django.db import models
from core.models import ModeloSaaS

class CategoriaCliente(ModeloSaaS):
    """Ex: Sócio Ouro, Aluno Manhã, Cliente Varejo"""
    nome = models.CharField(max_length=100)
    
    def __str__(self):
        return self.nome
    
    class Meta:
        verbose_name = "Categoria de Cliente"
        verbose_name_plural = "Categorias de Clientes"
        permissions = [('acesso_modulo', 'Acesso ao módulo Cadastros')]

class Cadastro(ModeloSaaS):
    TIPO_PESSOA_CHOICES = [
        ('PF', 'Pessoa Física'),
        ('PJ', 'Pessoa Jurídica'),
    ]
    
    PAPEL_CHOICES = [
        ('CLI', 'Cliente / Sócio / Aluno'),
        ('FOR', 'Fornecedor'),
        ('AMB', 'Ambos'),
    ]

    STATUS_CHOICES = [
        ('ATIVO', 'Ativo'),
        ('INATIVO', 'Inativo'),
    ]

    # --- Classificação ---
    papel = models.CharField(max_length=3, choices=PAPEL_CHOICES, default='CLI', verbose_name="Tipo de Cadastro")
    categoria = models.ForeignKey(CategoriaCliente, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Categoria (Apenas Clientes)")
    
    # --- Identificação ---
    tipo_pessoa = models.CharField(max_length=2, choices=TIPO_PESSOA_CHOICES, default='PF', verbose_name="Tipo de Pessoa")
    
    # PF e PJ compartilham o campo 'nome' (PF = Nome Completo, PJ = Nome Fantasia)
    nome = models.CharField(max_length=255, verbose_name="Nome / Nome Fantasia")
    
    # Exclusivo PJ
    razao_social = models.CharField(max_length=255, blank=True, null=True, verbose_name="Razão Social")
    
    # Documentos
    cpf_cnpj = models.CharField(max_length=20, verbose_name="CPF ou CNPJ")
    
    # Separando os documentos
    rg = models.CharField(max_length=20, blank=True, null=True, verbose_name="RG (Apenas PF)")
    inscricao_estadual = models.CharField(max_length=20, blank=True, null=True, verbose_name="Inscrição Estadual (PJ ou Produtor Rural)")
    
    # Flag para Produtor Rural (Permite IE mesmo sendo PF)
    is_produtor_rural = models.BooleanField(default=False, verbose_name="Produtor Rural?")
    
    # --- Dados Legados (Mantidos para não quebrar o que já fizemos) ---
    num_registro = models.IntegerField(verbose_name="Nº Registro", null=True, blank=True)
    data_nascimento = models.DateField(verbose_name="Data de Nascimento / Fundação", null=True, blank=True)
    
    # --- Contato ---
    email = models.EmailField(max_length=254, null=True, blank=True)
    celular = models.CharField(max_length=20, blank=True)
    telefone_fixo = models.CharField(max_length=20, blank=True)
    
    # --- Endereço ---
    cep = models.CharField(max_length=9, blank=True)
    endereco = models.CharField(max_length=255, blank=True)
    bairro = models.CharField(max_length=100, blank=True)
    cidade = models.CharField(max_length=100, blank=True)
    uf = models.CharField(max_length=2, blank=True)

    situacao = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ATIVO')
    foto = models.ImageField(upload_to='fotos_cadastros/', null=True, blank=True)
    observacoes = models.TextField(blank=True)

    def __str__(self):
        return self.nome 

    class Meta:
        verbose_name = "Cadastro"
        verbose_name_plural = "Cadastros"
        ordering = ['nome']
        unique_together = [['empresa', 'cpf_cnpj']] # CPF/CNPJ único por empresa
