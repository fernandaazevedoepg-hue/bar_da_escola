from .models import Utilizador

def utilizador_context(request):
    if 'utilizador_id' in request.session:
        try:
            utilizador = Utilizador.objects.get(id=request.session['utilizador_id'])
            return {'utilizador': utilizador}
        except Utilizador.DoesNotExist:
            pass
    return {'utilizador': None}
