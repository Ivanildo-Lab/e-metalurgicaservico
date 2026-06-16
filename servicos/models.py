from django.db import models
from django.core.exceptions import ValidationError
from core.models import ModeloSaaS
from cadastros.models import Cadastro


class Funcionario(ModeloSaaS):
    """Funcionários da metalúrgica (tabela separada de Cadastro)"""
    nome = models.CharField(max_length=255, verbose_name="Nome Completo")
    telefone = models.CharField(max_length=20, blank=True, verbose_name="Telefone")
    email = models.EmailField(blank=True, null=True, verbose_name="E-mail")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    observacoes = models.TextField(blank=True, verbose_name="Observações")

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Funcionário"
        verbose_name_plural = "Funcionários"
        ordering = ['nome']
        unique_together = [['empresa', 'nome']]


class OrdemServico(ModeloSaaS):
    """Ordem de Serviço — registro de trabalho recebido"""
    STATUS_CHOICES = [
        ('ABERTA', 'Aberta'),
        ('CONCLUIDA', 'Concluída'),
        ('FECHADA', 'Fechada'),
        ('CANCELADA', 'Cancelada'),
    ]

    FORMA_PGTO_CHOICES = [
        ('A_VISTA', 'À Vista'),
        ('A_PRAZO', 'A Prazo'),
    ]

    numero = models.CharField(max_length=20, verbose_name="Nº OS", editable=False)
    cadastro = models.ForeignKey(
        Cadastro, on_delete=models.PROTECT, verbose_name="Cliente",
        help_text="Cliente que enviou a peça / encomenda"
    )
    descricao_geral = models.TextField(verbose_name="Descrição do Objeto / Peça",
                                       help_text="Descreva o objeto recebido e o trabalho a ser feito")
    data_entrada = models.DateField(verbose_name="Data de Entrada")
    data_prevista = models.DateField(verbose_name="Previsão de Conclusão", null=True, blank=True)
    data_conclusao = models.DateField(verbose_name="Data de Conclusão", null=True, blank=True, editable=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ABERTA')

    forma_pagamento = models.CharField(
        max_length=10, choices=FORMA_PGTO_CHOICES, null=True, blank=True,
        verbose_name="Forma de Pagamento"
    )
    qtd_parcelas = models.IntegerField(default=1, verbose_name="Quantidade de Parcelas")

    observacoes = models.TextField(blank=True, verbose_name="Observações")
    created_at = models.DateTimeField(auto_now_add=True)

    # ---- Propriedades ----
    @property
    def valor_total(self):
        return self.servicos.aggregate(total=models.Sum('valor'))['total'] or 0

    @property
    def remuneracao_total(self):
        return self.funcionarios.aggregate(total=models.Sum('valor_remuneracao'))['total'] or 0

    @property
    def status_cor(self):
        cores = {
            'ABERTA': 'blue',
            'CONCLUIDA': 'yellow',
            'FECHADA': 'green',
            'CANCELADA': 'red',
        }
        return cores.get(self.status, 'gray')

    def clean(self):
        super().clean()
        # Validação de fechamento: remuneração deve bater com valor total
        if self.status == 'FECHADA':
            if self.remuneracao_total != self.valor_total:
                raise ValidationError(
                    f"A remuneração dos funcionários (R$ {self.remuneracao_total:.2f}) "
                    f"não confere com o valor total dos serviços (R$ {self.valor_total:.2f}). "
                    f"Ajuste antes de fechar a OS."
                )

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = self._gerar_numero()
        super().save(*args, **kwargs)

    def _gerar_numero(self):
        """Gera número sequencial: OS-2026-0001"""
        from django.utils import timezone
        ano = timezone.now().year
        prefixo = f'OS-{ano}-'
        ultimo = OrdemServico.objects.filter(
            empresa=self.empresa, numero__startswith=prefixo
        ).order_by('-numero').first()

        if ultimo:
            seq = int(ultimo.numero.split('-')[-1]) + 1
        else:
            seq = 1

        # Garante que o número não existe
        while OrdemServico.objects.filter(
            empresa=self.empresa, numero=f'{prefixo}{seq:04d}'
        ).exists():
            seq += 1

        return f'{prefixo}{seq:04d}'

    def __str__(self):
        return f"{self.numero} — {self.cadastro.nome}"

    class Meta:
        verbose_name = "Ordem de Serviço"
        verbose_name_plural = "Ordens de Serviço"
        ordering = ['-data_entrada', '-numero']
        unique_together = [['empresa', 'numero']]


class ServicoOS(models.Model):
    """Itens de serviço dentro de uma OS (ex: Usinagem do Cardan — R$100)"""
    ordem_servico = models.ForeignKey(OrdemServico, on_delete=models.CASCADE,
                                      related_name='servicos', verbose_name="Ordem de Serviço")
    descricao = models.CharField(max_length=255, verbose_name="Descrição do Serviço")
    valor = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor (R$)")

    def __str__(self):
        return f"{self.descricao} — R$ {self.valor:.2f}"

    class Meta:
        verbose_name = "Serviço da OS"
        verbose_name_plural = "Serviços da OS"
        ordering = ['id']


class FuncionarioOS(models.Model):
    """Participação de um funcionário em uma OS com sua remuneração"""
    ordem_servico = models.ForeignKey(OrdemServico, on_delete=models.CASCADE,
                                      related_name='funcionarios', verbose_name="Ordem de Serviço")
    funcionario = models.ForeignKey(Funcionario, on_delete=models.PROTECT,
                                     verbose_name="Funcionário")
    valor_remuneracao = models.DecimalField(max_digits=12, decimal_places=2,
                                             verbose_name="Remuneração (R$)")

    def __str__(self):
        return f"{self.funcionario.nome} — R$ {self.valor_remuneracao:.2f}"

    class Meta:
        verbose_name = "Funcionário da OS"
        verbose_name_plural = "Funcionários da OS"
        ordering = ['funcionario__nome']
        # Um funcionário só pode ter um registro por OS
        unique_together = ['ordem_servico', 'funcionario']


class MetaFuncionario(ModeloSaaS):
    """Meta mensal de remuneração por funcionário"""
    MESES_CHOICES = [
        (1, 'Janeiro'), (2, 'Fevereiro'), (3, 'Março'), (4, 'Abril'),
        (5, 'Maio'), (6, 'Junho'), (7, 'Julho'), (8, 'Agosto'),
        (9, 'Setembro'), (10, 'Outubro',), (11, 'Novembro'), (12, 'Dezembro'),
    ]

    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE,
                                     verbose_name="Funcionário")
    mes = models.IntegerField(choices=MESES_CHOICES, verbose_name="Mês")
    ano = models.IntegerField(verbose_name="Ano")
    meta_valor = models.DecimalField(max_digits=12, decimal_places=2,
                                      verbose_name="Meta (R$)")

    # Limites de avaliação (em % do valor realizado / meta)
    avaliacao_ruim = models.DecimalField(max_digits=5, decimal_places=1, default=50.0,
                                          verbose_name="% Mínima para Ruim",
                                          help_text="Ex: 50.0 = Ruim se atingir menos de 50% da meta")
    avaliacao_bom = models.DecimalField(max_digits=5, decimal_places=1, default=80.0,
                                         verbose_name="% Mínima para Bom",
                                         help_text="Ex: 80.0 = Bom se atingir entre 50% e 80% da meta")
    avaliacao_otimo = models.DecimalField(max_digits=5, decimal_places=1, default=100.0,
                                           verbose_name="% Mínima para Ótimo",
                                           help_text="Ex: 100.0 = Ótimo se atingir 100% ou mais da meta")

    def calcular_avaliacao(self, realizado):
        """Retorna a classificação baseado no percentual atingido"""
        if self.meta_valor == 0:
            return 'SEM_META'
        percentual = (realizado / self.meta_valor) * 100
        if percentual >= self.avaliacao_otimo:
            return 'OTIMO'
        elif percentual >= self.avaliacao_bom:
            return 'BOM'
        elif percentual >= self.avaliacao_ruim:
            return 'RUIM'
        return 'MUITO_BAIXO'

    def __str__(self):
        return f"{self.funcionario.nome} — {self.get_mes_display()}/{self.ano} — R$ {self.meta_valor:.2f}"

    class Meta:
        verbose_name = "Meta do Funcionário"
        verbose_name_plural = "Metas dos Funcionários"
        ordering = ['-ano', '-mes', 'funcionario__nome']
        unique_together = ['empresa', 'funcionario', 'mes', 'ano']


class Orcamento(ModeloSaaS):
    """Orçamento — proposta de serviços para o cliente"""
    FORMA_PGTO_CHOICES = [
        ('A_VISTA', 'À Vista'),
        ('A_PRAZO', 'A Prazo'),
    ]

    numero = models.CharField(max_length=20, verbose_name="Nº Orçamento", editable=False)
    cadastro = models.ForeignKey(
        Cadastro, on_delete=models.PROTECT, verbose_name="Cliente",
        help_text="Cliente para quem o orçamento será enviado"
    )
    descricao = models.TextField(verbose_name="Descrição / Observação do Orçamento",
                                 help_text="Descreva o serviço proposto")
    data = models.DateField(verbose_name="Data do Orçamento")
    data_validade = models.DateField(verbose_name="Validade do Orçamento", null=True, blank=True)

    forma_pagamento = models.CharField(
        max_length=10, choices=FORMA_PGTO_CHOICES, null=True, blank=True,
        verbose_name="Forma de Pagamento"
    )

    observacoes = models.TextField(blank=True, verbose_name="Observações")
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def valor_total(self):
        return self.servicos.aggregate(total=models.Sum('valor'))['total'] or 0

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = self._gerar_numero()
        super().save(*args, **kwargs)

    def _gerar_numero(self):
        """Gera número sequencial: ORC-2026-0001"""
        from django.utils import timezone
        ano = timezone.now().year
        prefixo = f'ORC-{ano}-'
        ultimo = Orcamento.objects.filter(
            empresa=self.empresa, numero__startswith=prefixo
        ).order_by('-numero').first()

        if ultimo:
            seq = int(ultimo.numero.split('-')[-1]) + 1
        else:
            seq = 1

        # Garante que o número não existe
        while Orcamento.objects.filter(
            empresa=self.empresa, numero=f'{prefixo}{seq:04d}'
        ).exists():
            seq += 1

        return f'{prefixo}{seq:04d}'

    def __str__(self):
        return f"{self.numero} — {self.cadastro.nome}"

    class Meta:
        verbose_name = "Orçamento"
        verbose_name_plural = "Orçamentos"
        ordering = ['-data', '-numero']
        unique_together = [['empresa', 'numero']]


class ServicoOrcamento(models.Model):
    """Itens de serviço dentro de um Orçamento"""
    orcamento = models.ForeignKey(Orcamento, on_delete=models.CASCADE,
                                  related_name='servicos', verbose_name="Orçamento")
    descricao = models.CharField(max_length=255, verbose_name="Descrição do Serviço")
    valor = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor (R$)")

    def __str__(self):
        return f"{self.descricao} — R$ {self.valor:.2f}"

    class Meta:
        verbose_name = "Serviço do Orçamento"
        verbose_name_plural = "Serviços do Orçamento"
        ordering = ['id']


class FormaPagamento(ModeloSaaS):
    """Formas de pagamento cadastradas pela empresa"""
    nome = models.CharField(max_length=100, verbose_name="Nome")
    afeta_caixa = models.BooleanField(
        default=False,
        verbose_name="Afeta o Caixa?",
        help_text="Marque apenas para formas que movimentam o caixa físico (ex: Dinheiro)"
    )
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    ordem = models.IntegerField(default=0, verbose_name="Ordem de Exibição")

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Forma de Pagamento"
        verbose_name_plural = "Formas de Pagamento"
        ordering = ['ordem', 'nome']
        unique_together = [['empresa', 'nome']]
