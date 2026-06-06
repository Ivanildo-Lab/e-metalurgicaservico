from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
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

# Configuração para servir Arquivos em modo DEBUG
if settings.DEBUG:
    # 1. Imagens de Upload (Media) - Banners das empresas
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # 2. Arquivos Estáticos (Static) - CSS, JS e sua imagem de fundo local
    # Aqui estava o erro: usamos a primeira pasta da lista de diretórios estáticos
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])