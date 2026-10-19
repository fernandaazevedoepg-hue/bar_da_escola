from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from .models import Utilizador, Produto, Encomenda, ItemEncomenda
import secrets
from django.contrib.auth.hashers import make_password, check_password
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.views.decorators.http import require_POST
from django.utils.timezone import localtime
from django.db.models import Prefetch
from django.db.models import Case, When, Value, IntegerField
from datetime import timedelta
from .models import ConfiguracaoHorario

def home(request):
    user_info = None

    if 'utilizador_id' in request.session:
        try:
            user_info = Utilizador.objects.get(id=request.session['utilizador_id'])
        except Utilizador.DoesNotExist:
        
            user_info = None

    return render(request, 'app_encomenda/home.html', {'user_info': user_info})


MB_ENTITY = "12345"  

def finalizar_encomenda(request):
    if 'utilizador_id' not in request.session:
        return redirect('login')

    utilizador = get_object_or_404(Utilizador, id=request.session['utilizador_id'])
    carrinho = request.session.get('carrinho', {})
    if not carrinho:
        messages.error(request, "Carrinho vazio.")
        return redirect('ver_carrinho')

    metodo = request.POST.get('metodo', 'cartao')
    when_str = request.POST.get('levantamento_em')

    if when_str:
        try:
            levantamento_em = timezone.make_aware(timezone.datetime.fromisoformat(when_str))
        except Exception:
            messages.error(request, "Data e hora de levantamento inválidas.")
            return redirect('ver_carrinho')
    else:
        messages.error(request, "Por favor, escolhe uma data e hora para levantamento.")
        return redirect('ver_carrinho')

    # --- Verificação com base nas configurações do admin ---
    config = ConfiguracaoHorario.objects.first()
    if not config:
        messages.error(request, "Configuração de horário não encontrada. Define-a no painel de administração.")
        return redirect('ver_carrinho')

    weekday = levantamento_em.weekday()
    hora = levantamento_em.time()

    # Verifica se o dia está permitido
    if weekday not in config.dias_funcionamento:
        messages.error(request, "O levantamento não pode ser agendado neste dia. Escolhe um dia de funcionamento.")
        return redirect('ver_carrinho')

    # Verifica se a hora está dentro do intervalo permitido
    if hora < config.hora_inicio or hora > config.hora_fim:
        messages.error(
            request,
            f"O levantamento só pode ser agendado entre "
            f"{config.hora_inicio.strftime('%H:%M')} e {config.hora_fim.strftime('%H:%M')}."
        )
        return redirect('ver_carrinho')

    # --- Continua com o processamento normal ---
    total = Decimal('0.00')
    linhas = []
    for produto_id, quantidade in carrinho.items():
        produto = get_object_or_404(Produto, id=int(produto_id))
        if not produto.tem_stock(quantidade) and metodo == 'cartao':
            messages.error(request, f"Sem stock suficiente de {produto.nome}.")
            return redirect('ver_carrinho')
        subtotal = produto.preco * quantidade
        total += subtotal
        linhas.append((produto, quantidade, subtotal))

    if metodo == 'cartao':
        if not utilizador.efetuar_pagamento(total):
            messages.error(request, "Saldo insuficiente.")
            return redirect('ver_carrinho')

        encomenda = Encomenda.objects.create(
            utilizador=utilizador, levantamento_em=levantamento_em,
            estado='paga', total=total
        )

        for produto, quantidade, subtotal in linhas:
            ItemEncomenda.objects.create(
                encomenda=encomenda, produto=produto, quantidade=quantidade, subtotal=subtotal
            )
            produto.quantidade -= quantidade
            produto.save(update_fields=['quantidade'])

        request.session['carrinho'] = {}
        request.session.modified = True

        return render(request, 'app_encomenda/encomenda_confirmada.html', {'encomenda': encomenda})

    elif metodo == 'multibanco':
        referencia = generate_mb_reference()
        encomenda = Encomenda.objects.create(
            utilizador=utilizador, levantamento_em=levantamento_em,
            estado='pendente', total=total,
            mb_entidade=MB_ENTITY, mb_referencia=referencia
        )

        for produto, quantidade, subtotal in linhas:
            ItemEncomenda.objects.create(
                encomenda=encomenda, produto=produto, quantidade=quantidade, subtotal=subtotal
            )

        request.session['carrinho'] = {}
        request.session.modified = True

        return render(request, 'app_encomenda/mb_instructions.html', {
            'encomenda': encomenda,
            'mb_entidade': MB_ENTITY,
            'mb_referencia': referencia,
            'mb_valor': total
        })

    else:
        messages.error(request, "Método de pagamento inválido.")
        return redirect('ver_carrinho')



def generate_mb_reference():

    return ''.join(secrets.choice('0123456789') for _ in range(9))


@require_http_methods(["GET", "POST"])
def confirmar_mb_pagamento(request, encomenda_id):
    encomenda = get_object_or_404(Encomenda, id=encomenda_id)


    if encomenda.estado == 'paga':
        messages.info(request, "Esta encomenda já foi paga.")
        return redirect('encomendas')

    if request.method == "POST":
  
        for item in encomenda.itens.select_related('produto').all():
            if item.produto.quantidade < item.quantidade:
                messages.error(
                    request,
                    f"Stock insuficiente para {item.produto.nome}. Pagamento não pode ser confirmado."
                )
                return redirect('encomendas')

        for item in encomenda.itens.select_related('produto').all():
            produto = item.produto
            produto.quantidade -= item.quantidade
            produto.save(update_fields=['quantidade'])

        encomenda.estado = 'paga'
        encomenda.save(update_fields=['estado'])

        messages.success(request, f"Pagamento confirmado! Stock atualizado para encomenda #{encomenda.id}.")
        return redirect('encomendas')


    return render(request, 'app_encomenda/mb_instructions.html', {
        'encomenda': encomenda,
        'mb_entidade': encomenda.mb_entidade,
        'mb_referencia': encomenda.mb_referencia,
        'mb_valor': encomenda.total
    })

def encomenda_detalhe(request, encomenda_id):
    encomenda = get_object_or_404(Encomenda, id=encomenda_id)
    return render(request, 'app_encomenda/encomenda_detalhe.html', {'encomenda': encomenda})


def encomendas(request):
    if 'utilizador_id' not in request.session:
        return redirect('login')

    utilizador = get_object_or_404(Utilizador, id=request.session['utilizador_id'])
    minhas = Encomenda.objects.filter(utilizador=utilizador).prefetch_related('itens__produto').order_by('-data_hora')

    return render(request, 'app_encomenda/encomendas.html', {
        'utilizador': utilizador,
        'minhas': minhas
    })


def generate_mb_reference():
    return ''.join(secrets.choice('0123456789') for _ in range(9))

def carregar_saldo(request):
    if 'utilizador_id' not in request.session:
        return redirect('login')

    utilizador = get_object_or_404(Utilizador, id=request.session['utilizador_id'])

    if request.method == 'POST':
        valor_str = request.POST.get('valor', '0').replace(',', '.')
        try:
            valor = Decimal(valor_str)
        except Exception:
            valor = Decimal('0')

        if valor <= 0:
            messages.error(request, 'Introduza um valor válido.')
            return redirect('carregar_saldo')

        referencia = generate_mb_reference()
        request.session['mb_topup'] = {
            'utilizador_id': utilizador.id,
            'valor': str(valor),
            'mb_entidade': MB_ENTITY,
            'mb_referencia': referencia
        }
        request.session.modified = True

        return render(request, 'app_encomenda/mb_instructions_saldo.html', {
            'mb_entidade': MB_ENTITY,
            'mb_referencia': referencia,
            'mb_valor': valor
        })

    return render(request, 'app_encomenda/carregar_saldo.html', {'utilizador': utilizador})

@require_POST
def confirmar_mb_topup(request):
    data = request.session.get('mb_topup')
    if not data:
        messages.error(request, "Não existe carregamento MBWay em curso.")
        return redirect('carregar_saldo')

    utilizador = get_object_or_404(Utilizador, id=data['utilizador_id'])
    valor = Decimal(data['valor'])

    try:
        with transaction.atomic():
            utilizador.saldo += valor
            utilizador.save(update_fields=['saldo'])
    except Exception:
        messages.error(request, "Erro ao confirmar pagamento.")
        return redirect('carregar_saldo')

    request.session.pop('mb_topup', None)

    messages.success(request, f"Pagamento MBWay confirmado! {valor:.2f} € adicionados. Novo saldo: {utilizador.saldo:.2f} €")
    return redirect('carregar_saldo')

def adicionar_carrinho(request, produto_id):
    get_object_or_404(Produto, id=produto_id)
    carrinho=request.session.get('carrinho',{}); pid=str(produto_id)
    carrinho[pid]=carrinho.get(pid,0)+1
    request.session['carrinho']=carrinho; request.session.modified=True
    return redirect('ver_carrinho')


def remover_item(request, produto_id):
    carrinho=request.session.get('carrinho',{}); pid=str(produto_id)
    if pid in carrinho: del carrinho[pid]
    request.session['carrinho']=carrinho; request.session.modified=True
    return redirect('ver_carrinho')

def alterar_qtd(request, produto_id, operacao):
    carrinho=request.session.get('carrinho',{}); pid=str(produto_id)
    if pid in carrinho:
        if operacao=='mais': carrinho[pid]+=1
        elif operacao=='menos': 
            carrinho[pid]-=1
            if carrinho[pid]<=0: del carrinho[pid]
        request.session['carrinho']=carrinho; request.session.modified=True
    return redirect('ver_carrinho')


def ver_carrinho(request):
    carrinho = request.session.get('carrinho', {})
    itens = []
    total = Decimal('0.00')
    utilizador = None

    if 'utilizador_id' in request.session:
        utilizador = get_object_or_404(Utilizador, id=request.session['utilizador_id'])

    for produto_id, quantidade in carrinho.items():
        produto = get_object_or_404(Produto, id=int(produto_id))
        subtotal = produto.preco * quantidade
        itens.append({'produto': produto, 'quantidade': quantidade, 'subtotal': subtotal})
        total += subtotal

    agora = timezone.localtime(timezone.now()) 
    
    
    config = ConfiguracaoHorario.objects.first()
    dias_semana = ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo']
    dias_funcionamento = []
    if config:
        dias_funcionamento = [dias_semana[d] for d in config.dias_funcionamento]

    return render(request, 'app_encomenda/carrinho.html', {
        'itens': itens,
        'total': total,
        'utilizador': utilizador,
        'agora': timezone.localtime(),
        'config': config,
        'dias_funcionamento': dias_funcionamento,
})

def registar(request):
    if request.method == 'POST':
        nome = request.POST.get('nome').strip()
        email = request.POST.get('email').strip().lower()
        tipo = request.POST.get('tipo')
        password = request.POST.get('password')

        if Utilizador.objects.filter(email=email).exists():
            messages.error(request, 'Já existe um utilizador com esse email.')
        else:
            Utilizador.objects.create(
                nome=nome,
                email=email,
                tipo=tipo,
                saldo=0,
                password=make_password(password)
            )
            messages.success(request, 'Conta criada com sucesso! Faça login.')
            return redirect('login')

    return render(request, 'app_encomenda/registar.html')



def login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            u = Utilizador.objects.get(email=email)
            if check_password(password, u.password):
                request.session['utilizador_id'] = u.id

                if u.tipo == 'funcionario':
                    return redirect('painel_funcionario')
                else:
                    return redirect('home')

            else:
                messages.error(request, 'Palavra-passe incorreta.')
        except Utilizador.DoesNotExist:
            messages.error(request, 'Utilizador não encontrado.')

    return render(request, 'app_encomenda/login.html')


def logout(request):
    if 'utilizador_id' in request.session: del request.session['utilizador_id']
    return redirect('login')


def painel_funcionario(request):
    if 'utilizador_id' not in request.session:
        return redirect('login')

    utilizador = get_object_or_404(Utilizador, id=request.session['utilizador_id'])
    if utilizador.tipo != 'funcionario':
        messages.error(request, "Acesso restrito a funcionários.")
        return redirect('home')

    encomendas = (
        Encomenda.objects
        .select_related('utilizador')
        .prefetch_related('itens__produto')
        .filter(estado__in=['pendente', 'paga'])
        .annotate(
            prioridade=Case(
                When(utilizador__tipo__in=['professor', 'funcionario'], then=Value(0)),
                default=Value(1),
                output_field=IntegerField()
            )
        )
        .order_by('levantamento_em', 'prioridade')
    )

    agora = timezone.now()
    for e in encomendas:
        if e.levantamento_em:
            diferenca = e.levantamento_em - agora
            e.alerta = timedelta(minutes=0) <= diferenca <= timedelta(minutes=5)
        else:
            e.alerta = False

    return render(request, 'app_encomenda/painel_funcionario.html', {
        'utilizador': utilizador,
        'encomendas': encomendas
    })

def historico_encomendas(request):
    if 'utilizador_id' not in request.session:
        return redirect('login')

    utilizador = get_object_or_404(Utilizador, id=request.session['utilizador_id'])
    if utilizador.tipo != 'funcionario':
        messages.error(request, "Acesso restrito a funcionários.")
        return redirect('home')

    historico = (
        Encomenda.objects
        .select_related('utilizador')
        .prefetch_related('itens__produto')
        .filter(estado__in=['concluida', 'cancelada'])
        .order_by('-levantamento_em')
    )

    return render(request, 'app_encomenda/historico_encomendas.html', {
        'utilizador': utilizador,
        'historico': historico
    })



@require_POST
def marcar_concluida(request, encomenda_id):
    if 'utilizador_id' not in request.session:
        return redirect('login')

    utilizador = get_object_or_404(Utilizador, id=request.session['utilizador_id'])
    if utilizador.tipo != 'funcionario':
        messages.error(request, "Apenas funcionários podem concluir encomendas.")
        return redirect('home')

    encomenda = get_object_or_404(Encomenda, id=encomenda_id)
    if encomenda.estado != 'concluida':
        encomenda.estado = 'concluida'
        encomenda.save(update_fields=['estado'])
        messages.success(request, f"Encomenda #{encomenda.id} marcada como concluída.")
    else:
        messages.info(request, f"Encomenda #{encomenda.id} já estava concluída.")

    return redirect('painel_funcionario')

@require_POST
def cancelar_encomenda(request, encomenda_id):
    if 'utilizador_id' not in request.session:
        return redirect('login')

    utilizador = get_object_or_404(Utilizador, id=request.session['utilizador_id'])
    if utilizador.tipo != 'funcionario':
        messages.error(request, "Apenas funcionários podem cancelar encomendas.")
        return redirect('home')

    encomenda = get_object_or_404(Encomenda, id=encomenda_id)
    if encomenda.estado not in ['concluida', 'cancelada']:
        encomenda.estado = 'cancelada'
        encomenda.save(update_fields=['estado'])
        messages.warning(request, f"Encomenda #{encomenda.id} foi cancelada.")
    else:
        messages.info(request, f"A encomenda #{encomenda.id} já estava finalizada ou cancelada.")

    return redirect('painel_funcionario')
