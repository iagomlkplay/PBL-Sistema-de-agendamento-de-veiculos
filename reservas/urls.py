from django.urls import path
from . import views

urlpatterns = [
    path('api/reservas/', views.listar_reservas, name='listar_reservas'),
    path('api/reservas/criar/', views.criar_reserva, name='criar_reserva'),
]