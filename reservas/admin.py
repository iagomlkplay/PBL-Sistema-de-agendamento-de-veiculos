from django.contrib import admin
from .models import Colaborador, Motorista, Veiculo, Reserva

admin.site.register(Colaborador)
admin.site.register(Motorista)
admin.site.register(Veiculo)
admin.site.register(Reserva)
