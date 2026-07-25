# Generated manually - adds forma_pagamento FK to Lancamento

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('financeiro', '0005_conta_valor_pago_lancamento_conta_origem_fk'),
        ('servicos', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='lancamento',
            name='forma_pagamento',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='servicos.formapagamento',
                verbose_name='Forma de Pagamento',
            ),
        ),
    ]
