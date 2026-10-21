from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Rotas dos Apps
    path('cadastros/', include('cadastros.urls')),
    path('financeiro/', include('financeiro.urls')),
    path('servicos/', include('servicos.urls')),
    
    # O App WEB assume a raiz do site
    path('', include('web.urls')),

    path('configuracoes/', views.configuracoes_sistema, name='configuracoes'),
    path('configuracoes/editar/<int:id>/', views.editar_parametro, name='editar_parametro'),

]

# Media (uploads: logo/banner) servido INDEPENDENTE do DEBUG (producao roda com DEBUG=False).
# Sem esta rota, /media/* = 404 (mesma correcao aplicada no e-cobrancas).
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]

# Configuracao para servir arquivos estaticos em modo DEBUG (dev local)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
