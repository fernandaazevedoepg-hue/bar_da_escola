from django.contrib import admin
from .models import Utilizador, Grupo, Encomenda, ItemEncomenda, ConfiguracaoHorario
from .forms import ConfiguracaoHorarioForm

@admin.register(Utilizador)
class UtilizadorAdmin(admin.ModelAdmin):
    list_display=('nome','email','tipo','saldo')
    list_filter=('tipo',)
    search_fields=('nome','email')

class ItemInline(admin.TabularInline):
    model=ItemEncomenda
    extra=0

@admin.register(Encomenda)
class EncomendaAdmin(admin.ModelAdmin):
    list_display=('id','utilizador','estado','total','data_hora','levantamento_em')
    list_filter=('estado',)
    date_hierarchy='data_hora'
    inlines=[ItemInline]

@admin.register(Grupo)
class GrupoAdmin(admin.ModelAdmin):
    list_display=('id','nome')

@admin.register(ConfiguracaoHorario)
class ConfiguracaoHorarioAdmin(admin.ModelAdmin):
    form = ConfiguracaoHorarioForm
    list_display = ['hora_inicio', 'hora_fim', 'get_dias']

    def get_dias(self, obj):
        dias = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']
        return ', '.join([dias[d] for d in obj.dias_funcionamento])
    get_dias.short_description = 'Dias de funcionamento'