from django.urls import path, include
from . import views

urlpatterns = [
    # Autenticação
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Páginas (HTML)
    path('', views.index, name='index'),
    path('nova-reserva/', views.nova_reserva_page, name='nova_reserva_page'),
    path('reservas/', views.lista_reservas_page, name='lista_reservas_page'),

    # API (JSON)
    path('api/reservas/', views.listar_reservas, name='listar_reservas'),
    path('api/reservas/criar/', views.criar_reserva, name='criar_reserva'),
]