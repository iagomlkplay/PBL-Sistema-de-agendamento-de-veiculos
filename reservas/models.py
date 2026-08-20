from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta

class Colaborador(models.Model):
    nome = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    telefone = models.CharField(max_length=20, blank=True)
    cpf = models.CharField(max_length=14, unique=True)  # formato: 000.000.000-00
    departamento = models.CharField(max_length=100)
    ativo = models.BooleanField(default=True)  # se está ativo na empresa

    def __str__(self):
        return self.nome

class Motorista(models.Model):
    nome = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    telefone = models.CharField(max_length=20, blank=True)
    cpf = models.CharField(max_length=14, unique=True)  # formato: 000.000.000-00
    cnh = models.CharField(max_length=20, unique=True)  # número da CNH
    ativo = models.BooleanField(default=True)  # se está disponível para trabalhar

    def __str__(self):
        return self.nome

class Veiculo(models.Model):
    TIPO_CHOICES = (
        ('carro', 'Carro'),
        ('van', 'Van'),
    )
    placa = models.CharField(max_length=10, unique=True)
    modelo = models.CharField(max_length=50)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    capacidade = models.PositiveIntegerField(help_text="Número total de ocupantes (incluindo motorista)")
    ativo = models.BooleanField(default=True)  # se está disponível para reserva

    def __str__(self):
        return f"{self.modelo} - {self.placa}"

class Reserva(models.Model):
    colaborador = models.ForeignKey(Colaborador, on_delete=models.PROTECT)
    motorista = models.ForeignKey(Motorista, on_delete=models.PROTECT)
    veiculo = models.ForeignKey(Veiculo, on_delete=models.PROTECT)
    data_inicio = models.DateTimeField()
    data_fim = models.DateTimeField()
    origem = models.CharField(max_length=200)
    destino = models.CharField(max_length=200)
    num_passageiros = models.PositiveIntegerField()
    motivo = models.TextField()
    protocolo = models.CharField(max_length=20, unique=True, blank=True)
    STATUS_CHOICES = (
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
        ('finalizada', 'Finalizada'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='confirmada')
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reserva {self.protocolo} - {self.colaborador.nome}"

    def clean(self):
        # 1. Verificar horário comercial (8h-17h)
        if self.data_inicio.hour < 8 or self.data_inicio.hour >= 17:
            raise ValidationError("O horário de início deve ser entre 8:00 e 17:00.")
        if self.data_fim.hour < 8 or self.data_fim.hour > 17:
            raise ValidationError("O horário de fim deve ser entre 8:00 e 17:00.")
        if self.data_inicio >= self.data_fim:
            raise ValidationError("A data/hora de início deve ser anterior à data/hora de fim.")

        # 2. Limite de 10 reservas por semana (últimos 7 dias)
        uma_semana_atras = timezone.now() - timedelta(days=7)
        reservas_semana = Reserva.objects.filter(
            colaborador=self.colaborador,
            data_criacao__gte=uma_semana_atras
        ).exclude(pk=self.pk)
        if reservas_semana.count() >= 10:
            raise ValidationError("Este colaborador já atingiu o limite de 10 reservas na semana.")

        # 3. Verificar disponibilidade do veículo com buffer de 1h
        conflitos_veiculo = Reserva.objects.filter(
            veiculo=self.veiculo,
            status='confirmada'
        ).exclude(pk=self.pk).filter(
            models.Q(data_fim__gt=self.data_inicio - timedelta(hours=1)) &
            models.Q(data_inicio__lt=self.data_fim)
        )
        if conflitos_veiculo.exists():
            raise ValidationError("Veículo não disponível no período solicitado (inclui buffer de 1h).")

        # 4. Verificar disponibilidade do motorista com buffer de 1h
        conflitos_motorista = Reserva.objects.filter(
            motorista=self.motorista,
            status='confirmada'
        ).exclude(pk=self.pk).filter(
            models.Q(data_fim__gt=self.data_inicio - timedelta(hours=1)) &
            models.Q(data_inicio__lt=self.data_fim)
        )
        if conflitos_motorista.exists():
            raise ValidationError("Motorista não disponível no período solicitado (inclui buffer de 1h).")

    def save(self, *args, **kwargs):
        if not self.protocolo:
            self.protocolo = self.gerar_protocolo()
        # Chama a validação completa
        self.full_clean()
        super().save(*args, **kwargs)

    def gerar_protocolo(self):
        ano = timezone.now().year
        # Conta quantas reservas já existem no ano
        reservas_ano = Reserva.objects.filter(protocolo__endswith=f"/{ano}")
        ultimo_numero = 0
        for r in reservas_ano:
            # extrai o número antes da barra
            num_str = r.protocolo.split('/')[0]
            try:
                num = int(num_str)
                if num > ultimo_numero:
                    ultimo_numero = num
            except:
                pass
        novo_numero = ultimo_numero + 1
        # Formata com 5 dígitos
        numero_formatado = f"{novo_numero:05d}"
        return f"{numero_formatado}/{ano}"