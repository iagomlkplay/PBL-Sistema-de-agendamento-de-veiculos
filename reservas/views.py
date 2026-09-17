from django.shortcuts import render, redirect

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm

import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from .models import Colaborador, Reserva
from .utils import escolher_veiculo_motorista
from datetime import datetime
from django.utils import timezone

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('index')
    else:
        form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

@csrf_exempt
@login_required
def criar_reserva(request):
    if request.method != 'POST':
        return JsonResponse({'erro': 'Método não permitido'}, status=405)

    # Obtém o colaborador do usuário logado
    try:
        colaborador = request.user.colaborador
    except Colaborador.DoesNotExist:
        return JsonResponse(
            {'erro': 'Usuário não está vinculado a um colaborador.'},
            status=403
        )

    try:
        dados = json.loads(request.body)
    except:
        return JsonResponse({'erro': 'JSON inválido'}, status=400)

    # Extrair dados
    origem = dados.get('origem')
    destino = dados.get('destino')
    num_passageiros = dados.get('num_passageiros')
    motivo = dados.get('motivo')
    data_inicio_str = dados.get('data_inicio')
    data_fim_str = dados.get('data_fim')

    if not all([origem, destino, num_passageiros, motivo, data_inicio_str, data_fim_str]):
        return JsonResponse({'erro': 'Todos os campos são obrigatórios'}, status=400)

    try:
        data_inicio = datetime.fromisoformat(data_inicio_str)
        data_fim = datetime.fromisoformat(data_fim_str)
        if timezone.is_naive(data_inicio):
            data_inicio = timezone.make_aware(data_inicio, timezone.get_current_timezone())
        if timezone.is_naive(data_fim):
            data_fim = timezone.make_aware(data_fim, timezone.get_current_timezone())
    except:
        return JsonResponse({'erro': 'Formato de data/hora inválido.'}, status=400)

    # Pré-validações (antes de buscar veículo)
    if data_inicio < timezone.now():
        return JsonResponse({'erro': 'Não é possível agendar para uma data/hora no passado.'}, status=400)
    
    if data_inicio.date() != data_fim.date():
        return JsonResponse({'erro': 'A reserva deve começar e terminar no mesmo dia.'}, status=400)
    
    if data_inicio >= data_fim:
        return JsonResponse({'erro': 'Início deve ser antes do fim'}, status=400)
    
    if data_inicio.hour < 8 or data_inicio.hour >= 17 or data_fim.hour < 8 or data_fim.hour > 17:
        return JsonResponse({'erro': 'Horário deve ser entre 8:00 e 17:00'}, status=400)

    # Escolher veículo e motorista automaticamente
    try:
        veiculo, motorista = escolher_veiculo_motorista(num_passageiros, data_inicio, data_fim)
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

@login_required
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

@login_required
def index(request):
    """Página inicial."""
    return render(request, 'reservas/index.html')

@login_required
def nova_reserva_page(request):
    """Página com o formulário de nova reserva."""
    return render(request, 'reservas/nova_reserva.html')

def lista_reservas_page(request):
    """Página que lista as reservas (o JS carrega via API)."""
    return render(request, 'reservas/lista_reservas.html')