from django.db import models
from decimal import Decimal
from app_produtos.models import Produto


class Grupo(models.Model):
    nome = models.CharField(max_length=100)
    def __str__(self):
        return self.nome
    
class Utilizador(models.Model):
    TIPOS=[('aluno','Aluno'),('professor','Professor'),('funcionario','Funcionário')]

    nome=models.CharField(max_length=100, unique=True)
    email=models.EmailField(unique=True)
    tipo=models.CharField(max_length=20, choices=TIPOS)
    saldo=models.DecimalField(max_digits=8, decimal_places=2, default=0)
    password=models.CharField(max_length=128)

    def __str__(self): return f"{self.nome} ({self.tipo})"

    def adicionar_saldo(self, valor):
        self.saldo=(self.saldo or Decimal('0'))+(valor or Decimal('0')); self.save(update_fields=['saldo'])

    def efetuar_pagamento(self, valor: Decimal):
        if self.saldo>=valor:
            self.saldo-=valor; self.save(update_fields=['saldo']); return True
        return False
    
    @property
    def prioridade(self): return 0 if self.tipo in ('professor','funcionario') else 1


class Encomenda(models.Model):
    ESTADOS = [('pendente','Pendente'), ('paga','Paga'), ('concluida','Concluída')]
    utilizador = models.ForeignKey('Utilizador', on_delete=models.CASCADE)
    data_hora = models.DateTimeField(auto_now_add=True)
    levantamento_em = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendente')
    total = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    mb_entidade = models.CharField(max_length=20, null=True, blank=True)
    mb_referencia = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"Encomenda #{self.id} - {self.utilizador.nome} - {self.estado}"

class ItemEncomenda(models.Model):

    encomenda=models.ForeignKey(Encomenda, on_delete=models.CASCADE, related_name='itens')
    produto=models.ForeignKey(Produto, on_delete=models.PROTECT)
    quantidade=models.PositiveIntegerField(default=1)
    subtotal=models.DecimalField(max_digits=8, decimal_places=2, default=0)

    def __str__(self): return f"{self.quantidade} x {self.produto.nome}"


class ConfiguracaoHorario(models.Model):
    DIAS_SEMANA = [
        (0, 'Segunda-feira'),
        (1, 'Terça-feira'),
        (2, 'Quarta-feira'),
        (3, 'Quinta-feira'),
        (4, 'Sexta-feira'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]

    dias_funcionamento = models.JSONField(default=list, blank=True)
    hora_inicio = models.TimeField(default='08:00')
    hora_fim = models.TimeField(default='17:00')

    def __str__(self):
        return "Configuração de Horário do Bar Escolar"

    class Meta:
        verbose_name = "Configuração de Horário"
        verbose_name_plural = "Configurações de Horário"