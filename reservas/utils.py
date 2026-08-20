from django.db import models
from django.core.exceptions import ValidationError
from datetime import timedelta
from .models import Veiculo, Motorista, Reserva

def escolher_veiculo_motorista(num_passageiros, data_inicio, data_fim, reserva_excluir=None):
    """
    Retorna um veículo e um motorista disponíveis para o período.
    Levanta ValidationError se não encontrar.
    """
    # 1. Determinar tipo de veículo necessário
    if num_passageiros <= 4:
        tipo_veiculo = 'carro'
        capacidade_minima = 5  # carro tem 5 lugares
    else:
        tipo_veiculo = 'van'
        capacidade_minima = num_passageiros + 1  # motorista incluso

    # 2. Buscar veículos ativos do tipo adequado
    veiculos = Veiculo.objects.filter(tipo=tipo_veiculo, ativo=True)
    if tipo_veiculo == 'carro':
        # para carro, capacidade deve ser exatamente 5
        veiculos = veiculos.filter(capacidade=5)
    else:
        # Ordena da menor capacidade para a maior
        veiculos = veiculos.filter(capacidade__gte=capacidade_minima).order_by('capacidade')

    # 3. Verificar disponibilidade de cada veículo com buffer de 1h
    veiculo_disponivel = None
    for veiculo in veiculos:
        conflitos = Reserva.objects.filter(
            veiculo=veiculo,
            status='confirmada'
        )
        if reserva_excluir:
            conflitos = conflitos.exclude(pk=reserva_excluir.pk)
        # conflito se existente termina após (início_nova - 1h) E começa antes de fim_nova
        conflitos = conflitos.filter(
            models.Q(data_fim__gt=data_inicio - timedelta(hours=1)) &
            models.Q(data_inicio__lt=data_fim)
        )
        if not conflitos.exists():
            veiculo_disponivel = veiculo
            break

    if not veiculo_disponivel:
        raise ValidationError("Nenhum veículo disponível para o período solicitado.")

    # 4. Escolher motorista disponível (mesma lógica)
    motoristas = Motorista.objects.filter(ativo=True)
    motorista_disponivel = None
    for motorista in motoristas:
        conflitos = Reserva.objects.filter(
            motorista=motorista,
            status='confirmada'
        )
        if reserva_excluir:
            conflitos = conflitos.exclude(pk=reserva_excluir.pk)
        conflitos = conflitos.filter(
            models.Q(data_fim__gt=data_inicio - timedelta(hours=1)) &
            models.Q(data_inicio__lt=data_fim)
        )
        if not conflitos.exists():
            motorista_disponivel = motorista
            break

    if not motorista_disponivel:
        raise ValidationError("Nenhum motorista disponível para o período solicitado.")

    return veiculo_disponivel, motorista_disponivel