# Generated manually for baixa parcial (haver)

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('financeiro', '0004_alter_planodecontas_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='conta',
            name='valor_pago',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Valor Pago'),
        ),
        migrations.AlterField(
            model_name='conta',
            name='status',
            field=models.CharField(choices=[
                ('PENDENTE', 'Pendente'),
                ('PARCIAL', 'Parcialmente Paga'),
                ('PAGA', 'Paga / Recebida'),
                ('CANCELADA', 'Cancelada'),
            ], default='PENDENTE', max_length=10),
        ),
        migrations.AlterField(
            model_name='lancamento',
            name='conta_origem',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='lancamentos_vinculados',
                to='financeiro.conta',
            ),
        ),
    ]
