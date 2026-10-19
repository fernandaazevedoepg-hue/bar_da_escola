from django.urls import path
from . import views


urlpatterns=[
    path('painel_funcionario/', views.painel_funcionario, name='painel_funcionario'),
    path('encomendas/historico/', views.historico_encomendas, name='historico_encomendas'),
    path('carrinho/', views.ver_carrinho, name='ver_carrinho'),
    path('carrinho/adicionar/<int:produto_id>/', views.adicionar_carrinho, name='adicionar_carrinho'),
    path('carrinho/remover/<int:produto_id>/', views.remover_item, name='remover_item'),
    path('carrinho/qtd/<int:produto_id>/<str:operacao>/', views.alterar_qtd, name='alterar_qtd'),
    path('finalizar/', views.finalizar_encomenda, name='finalizar_encomenda'),
    path('encomendas/', views.encomendas, name='encomendas'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('registar/', views.registar, name='registar'),
    path('carregar_saldo/', views.carregar_saldo, name='carregar_saldo'),
    path('confirmar_mb_topup/', views.confirmar_mb_topup, name='confirmar_mb_topup'),
    path('mb/<int:encomenda_id>/confirmar/', views.confirmar_mb_pagamento, name='confirmar_mb_pagamento'),
    path('encomenda/<int:encomenda_id>/', views.encomenda_detalhe, name='encomenda_detalhe'),
    path('marcar_concluida/<int:encomenda_id>/', views.marcar_concluida, name='marcar_concluida'),
    path('cancelar_encomenda/<int:encomenda_id>/', views.cancelar_encomenda, name='cancelar_encomenda'),

]