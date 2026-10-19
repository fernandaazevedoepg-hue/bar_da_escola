from django.db import models
from decimal import Decimal

class Produto(models.Model):
    CATEGORIAS = [
        ('pastelaria', 'Pastelaria'),
        ('bolos', 'Bolos'),
        ('bebidas', 'Bebidas'),
        ('salgados', 'Salgados'),
        ('menus', 'Menus'),
    ]

    SUBCATEGORIAS = [
        ('cafes', 'Cafés'),
        ('aguas', 'Águas'),
        ('sumos', 'Sumos naturais'),
        ('refrigerantes', 'Refrigerantes'),
        ('nenhuma', 'Nenhuma'),
    ]

    nome = models.CharField(max_length=100)
    categoria = models.CharField(max_length=50, choices=CATEGORIAS)
    subcategoria = models.CharField(max_length=50, choices=SUBCATEGORIAS, default='nenhuma')
    preco = models.DecimalField(max_digits=6, decimal_places=2)
    quantidade = models.PositiveIntegerField(default=0)
    descricao = models.TextField(blank=True)
    imagem = models.ImageField(upload_to='produtos/', blank=True, null=True)

    def __str__(self):
        cat = self.get_categoria_display()
        sub = self.get_subcategoria_display()
        return f"{self.nome} ({cat}{' - ' + sub if sub != 'Nenhuma' else ''})"

    def tem_stock(self, qtd=1):
        return self.quantidade >= qtd
