from django.db import models


class Pagina(models.Model):
    class Meta:
        verbose_name = "Página"
        verbose_name_plural = "Páginas"
        permissions = [('acesso_modulo', 'Acesso ao módulo Painel')]
        managed = False
