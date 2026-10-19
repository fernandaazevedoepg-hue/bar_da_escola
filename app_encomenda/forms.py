from django import forms
from .models import ConfiguracaoHorario

class ConfiguracaoHorarioForm(forms.ModelForm):
    DIAS_SEMANA = [
        (0, 'Segunda'),
        (1, 'Terça'),
        (2, 'Quarta'),
        (3, 'Quinta'),
        (4, 'Sexta'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]

    dias_funcionamento = forms.MultipleChoiceField(
        choices=DIAS_SEMANA,
        widget=forms.CheckboxSelectMultiple,
        label="Dias de funcionamento"
    )

    class Meta:
        model = ConfiguracaoHorario
        fields = ['dias_funcionamento', 'hora_inicio', 'hora_fim']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.dias_funcionamento:

            self.initial['dias_funcionamento'] = [str(d) for d in self.instance.dias_funcionamento]

    def clean_dias_funcionamento(self):

        dias = self.cleaned_data.get('dias_funcionamento', [])
        return [int(d) for d in dias]
