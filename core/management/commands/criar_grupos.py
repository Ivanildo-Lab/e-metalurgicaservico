from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission


class Command(BaseCommand):
    help = 'Cria grupos padrão de permissões'

    def handle(self, *args, **options):
        grupos_config = {
            'Administrador': [
                ('web', 'acesso_modulo'),
                ('cadastros', 'acesso_modulo'),
                ('financeiro', 'acesso_modulo'),
                ('servicos', 'acesso_modulo'),
                ('core', 'acesso_modulo'),
            ],
            'Painel': [
                ('web', 'acesso_modulo'),
            ],
            'Financeiro': [
                ('financeiro', 'acesso_modulo'),
            ],
            'Cadastros': [
                ('cadastros', 'acesso_modulo'),
            ],
            'Servicos': [
                ('servicos', 'acesso_modulo'),
            ],
        }

        for nome_grupo, permissoes in grupos_config.items():
            grupo, _ = Group.objects.get_or_create(name=nome_grupo)
            grupo.permissions.clear()
            for app_label, perm_codename in permissoes:
                try:
                    perm = Permission.objects.get(
                        codename=perm_codename,
                        content_type__app_label=app_label
                    )
                    grupo.permissions.add(perm)
                except Permission.DoesNotExist:
                    self.stdout.write(self.style.WARNING(
                        f'Permissão {app_label}.{perm_codename} não encontrada.'
                    ))
            self.stdout.write(self.style.SUCCESS(f'Grupo "{nome_grupo}" configurado.'))

        self.stdout.write(self.style.SUCCESS('Grupos padrão criados com sucesso!'))
