from django.shortcuts import render

import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from .models import Colaborador, Reserva
from .utils import escolher_veiculo_motorista
from datetime import datetime

@csrf_exempt  # apenas para teste
def criar_reserva(request):
    if request.method != 'POST':
        return JsonResponse({'erro': 'Método não permitido'}, status=405)
    
    try:
        dados = json.loads(request.body)
    except:
        return JsonResponse({'erro': 'JSON inválido'}, status=400)

    # Extrair dados
    colaborador_id = dados.get('colaborador_id')
    origem = dados.get('origem')
    destino = dados.get('destino')
    num_passageiros = dados.get('num_passageiros')
    motivo = dados.get('motivo')
    data_inicio_str = dados.get('data_inicio')  # espera formato ISO "2026-08-18T10:00:00"
    data_fim_str = dados.get('data_fim')

    # Validações básicas de campos obrigatórios
    if not all([colaborador_id, origem, destino, num_passageiros, motivo, data_inicio_str, data_fim_str]):
        return JsonResponse({'erro': 'Todos os campos são obrigatórios'}, status=400)

    try:
        colaborador = Colaborador.objects.get(id=colaborador_id)
    except Colaborador.DoesNotExist:
        return JsonResponse({'erro': 'Colaborador não encontrado'}, status=404)

    try:
        data_inicio = datetime.fromisoformat(data_inicio_str)
        data_fim = datetime.fromisoformat(data_fim_str)
    except:
        return JsonResponse({'erro': 'Formato de data/hora inválido. Use ISO (YYYY-MM-DDTHH:MM:SS)'}, status=400)

    # Verificar horário comercial (8-17) (Pré-validação)
    if data_inicio.hour < 8 or data_inicio.hour >= 17 or data_fim.hour < 8 or data_fim.hour > 17:
        return JsonResponse({'erro': 'Horário deve ser entre 8:00 e 17:00'}, status=400)
    if data_inicio >= data_fim:
        return JsonResponse({'erro': 'Início deve ser antes do fim'}, status=400)

    # Escolher veículo e motorista automaticamente
    try:
        veiculo, motorista = escolher_veiculo_motorista(
            num_passageiros, data_inicio, data_fim
        )
    except ValidationError as e:
        return JsonResponse({'erro': str(e)}, status=400)

    # Criar a reserva
    reserva = Reserva(
        colaborador=colaborador,
        motorista=motorista,
        veiculo=veiculo,
        data_inicio=data_inicio,
        data_fim=data_fim,
        origem=origem,
        destino=destino,
        num_passageiros=num_passageiros,
        motivo=motivo
    )
    try:
        reserva.save()  # dispara clean() e gera protocolo
    except ValidationError as e:
        # Pega as mensagens de erro do clean
        return JsonResponse({'erro': e.messages}, status=400)

    # Retornar os dados da reserva criada + protocolo
    return JsonResponse({
        'protocolo': reserva.protocolo,
        'veiculo': veiculo.placa,
        'motorista': motorista.nome,
        'data_inicio': reserva.data_inicio.isoformat(),
        'data_fim': reserva.data_fim.isoformat(),
        'status': reserva.status,
        'mensagem': 'Reserva criada com sucesso!'
    }, status=201)

def listar_reservas(request):
    reservas = Reserva.objects.filter(status='confirmada').order_by('data_inicio')
    data = []
    for r in reservas:
        data.append({
            'protocolo': r.protocolo,
            'colaborador': r.colaborador.nome,
            'motorista': r.motorista.nome,
            'veiculo': r.veiculo.placa,
            'data_inicio': r.data_inicio.isoformat(),
            'data_fim': r.data_fim.isoformat(),
            'origem': r.origem,
            'destino': r.destino,
            'num_passageiros': r.num_passageiros,
            'motivo': r.motivo,
            'status': r.status,
        })
    return JsonResponse(data, safe=False)