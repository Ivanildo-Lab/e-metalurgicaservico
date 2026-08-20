from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('servicos', '0010_alter_funcionario_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='orcamento',
            name='status',
            field=models.CharField(
                choices=[('PENDENTE', 'Pendente'), ('IMPORTADO', 'Importado')],
                default='PENDENTE',
                max_length=10,
                verbose_name='Status',
            ),
        ),
    ]
