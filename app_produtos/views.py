from django.shortcuts import render
from .models import Produto

def produtos(request):
    categoria = request.GET.get('categoria')
    subcategoria = request.GET.get('subcategoria')

    categorias = dict(Produto.CATEGORIAS)
    subcategorias = dict(getattr(Produto, 'SUBCATEGORIAS', {}))

    if not categoria:
        produtos_por_categoria = {}
        for cat_key, cat_nome in categorias.items():
            if cat_key == 'bebidas':
                produtos_por_categoria[cat_nome] = {
                    sub_nome: Produto.objects.filter(categoria=cat_key, subcategoria=sub_key)
                    for sub_key, sub_nome in subcategorias.items() if sub_key != 'nenhuma'
                }
            else:
                produtos_por_categoria[cat_nome] = {
                    '': Produto.objects.filter(categoria=cat_key)
                }

        return render(request, 'app_produtos/produtos.html', {
            'produtos_por_categoria': produtos_por_categoria,
            'categorias': categorias,
            'subcategorias': subcategorias,
            'categoria_selecionada': categoria,
            'subcategoria_selecionada': subcategoria,
        })

    produtos_filtrados = Produto.objects.filter(categoria=categoria)

    if categoria == 'bebidas' and subcategoria:
        produtos_filtrados = produtos_filtrados.filter(subcategoria=subcategoria)

    produtos_por_categoria = {
        categorias.get(categoria, 'Outros'): {
            subcategorias.get(subcategoria, ''): produtos_filtrados
        }
    }

    return render(request, 'app_produtos/produtos.html', {
        'produtos_por_categoria': produtos_por_categoria,
        'categorias': categorias,
        'subcategorias': subcategorias,
        'categoria_selecionada': categoria,
        'subcategoria_selecionada': subcategoria,
    })
