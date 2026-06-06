from django.db import models
from django.contrib.auth.models import AbstractUser

# 1. A Empresa (Quem contrata o SaaS)
class Empresa(models.Model):
    nome = models.CharField(max_length=255)
    cnpj = models.CharField(max_length=20, unique=True)
    ativo = models.BooleanField(default=True)
    logo = models.ImageField(upload_to='empresas/logos/', null=True, blank=True)
    banner = models.ImageField(upload_to='empresas/banners/', null=True, blank=True, help_text="Imagem de fundo da tela inicial")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.nome

# 2. O Usuário do Sistema (Vinculado a uma empresa)
class Usuario(AbstractUser):
    # O usuário 'admin' do Django (superuser) pode não ter empresa (null=True)
    # Mas usuários normais sempre terão.
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, null=True, blank=True)
    
    # Campos extras se quiser (ex: cargo)
    cargo = models.CharField(max_length=100, blank=True)

# 3. Classe Abstrata para Models SaaS
# TODAS as tabelas do sistema herdarão disso.
# Isso garante que nada seja criado sem dono.
class ModeloSaaS(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, verbose_name="Empresa")
    
    class Meta:
        abstract = True  # Isso diz ao Django: "Não crie uma tabela 'ModeloSaaS', use isso como modelo para outras"

# ... (Mantenha as classes Empresa, Usuario e ModeloSaaS anteriores)

class ParametroSistema(ModeloSaaS):
    """
    Armazena configurações globais da empresa.
    Ex: ID do Caixa Padrão, Taxa de Juros, etc.
    """
    CHAVES_CHOICES = [
        ('CAIXA_PADRAO_ID', 'Financeiro - ID do Caixa Padrão'),
        ('TAXA_JUROS_MENSAL', 'Financeiro - Taxa de Juros Mensal (%)'),
        ('PLANO_CONTAS_MENSALIDADE_ID', 'Financeiro - ID Plano Contas (Mensalidade)'),
        ('PLANO_CONTAS_JUROS_ID', 'Financeiro - ID Plano Contas (Juros/Multa)'),
        ('PLANO_CONTAS_SERVICOS_ID', 'Serviços - ID Plano Contas (Receita de Serviços)'),
    ]

    chave = models.CharField(max_length=100, choices=CHAVES_CHOICES)
    valor = models.CharField(max_length=255, help_text="Digite o ID ou o Valor correspondente")
    descricao = models.TextField(blank=True, verbose_name="Descrição / Notas")

    def __str__(self):
        return f"{self.get_chave_display()}: {self.valor}"

    class Meta:
        verbose_name = "Parâmetro do Sistema"
        verbose_name_plural = "Parâmetros do Sistema"
        # Garante que uma empresa não tenha duas configurações para a mesma chave
        unique_together = ['empresa', 'chave']

        