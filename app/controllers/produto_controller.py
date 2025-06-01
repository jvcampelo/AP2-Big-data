from flask import request
from flask_restx import Resource, Namespace, fields
from app.cosmosdb import container
from app.models.produto import Produto

# Criando namespace para o Swagger
ns = Namespace('produtos', description='Operações relacionadas a produtos')

# Modelos para documentação do Swagger
produto_model = ns.model('Produto', {
    'id': fields.String(readonly=True, description='ID do produto'),
    'produtoCategoria': fields.String(required=True, description='Categoria do produto'),
    'nome': fields.String(required=True, description='Nome do produto'),
    'preco': fields.Float(required=True, description='Preço do produto'),
    'urlImagem': fields.String(description='URL da imagem do produto'),
    'descricao': fields.String(description='Descrição do produto')
})

@ns.route('')
class ProdutoList(Resource):
    @ns.doc('list_produtos')
    @ns.marshal_list_with(produto_model)
    def get(self):
        """Lista todos os produtos"""
        query = "SELECT * FROM produtos"
        produtos = list(container.query_items(query=query, enable_cross_partition_query=True))
        return produtos

    @ns.doc('create_produto')
    @ns.expect(produto_model)
    @ns.marshal_with(produto_model, code=201)
    def post(self):
        """Cria um novo produto"""
        dados = request.json
        
        if not dados.get("produtoCategoria") or not dados.get("nome") or not dados.get("preco"):
            ns.abort(400, "Categoria, nome e preço são obrigatórios")

        novo_produto = Produto(
            produtoCategoria=dados["produtoCategoria"],
            nome=dados["nome"],
            preco=dados["preco"],
            urlImagem=dados.get("urlImagem"),
            descricao=dados.get("descricao")
        )

        container.create_item(novo_produto.to_dict())
        return novo_produto.to_dict(), 201

@ns.route('/<string:id>')
@ns.param('id', 'ID do produto')
@ns.response(404, 'Produto não encontrado')
class ProdutoResource(Resource):
    @ns.doc('get_produto')
    @ns.marshal_with(produto_model)
    def get(self, id):
        """Busca um produto específico"""
        query = f"SELECT * FROM produtos p WHERE p.id = '{id}'"
        produtos = list(container.query_items(query=query, enable_cross_partition_query=True))

        if not produtos:
            ns.abort(404, "Produto não encontrado")

        return produtos[0]

    @ns.doc('update_produto')
    @ns.expect(produto_model)
    @ns.marshal_with(produto_model)
    def put(self, id):
        """Atualiza um produto"""
        query = f"SELECT * FROM produtos p WHERE p.id = '{id}'"
        produtos = list(container.query_items(query=query, enable_cross_partition_query=True))

        if not produtos:
            ns.abort(404, "Produto não encontrado")

        produto = produtos[0]
        dados = request.json
        produto.update({
            "produtoCategoria": dados.get("produtoCategoria", produto["produtoCategoria"]),
            "nome": dados.get("nome", produto["nome"]),
            "preco": dados.get("preco", produto["preco"]),
            "urlImagem": dados.get("urlImagem", produto["urlImagem"]),
            "descricao": dados.get("descricao", produto["descricao"]),
        })

        container.replace_item(item=produto["id"], body=produto)
        return produto

    @ns.doc('delete_produto')
    @ns.response(204, 'Produto deletado')
    def delete(self, id):
        """Deleta um produto"""
        query = f"SELECT * FROM produtos p WHERE p.id = '{id}'"
        produtos = list(container.query_items(query=query, enable_cross_partition_query=True))

        if not produtos:
            ns.abort(404, "Produto não encontrado")

        container.delete_item(item=produtos[0]["id"], partition_key=produtos[0]["produtoCategoria"])
        return '', 204

@ns.route('/nome/<string:nome>')
@ns.param('nome', 'Nome do produto')
@ns.response(404, 'Produto não encontrado')
class ProdutoNomeResource(Resource):
    @ns.doc('get_produto_por_nome')
    @ns.marshal_with(produto_model)
    def get(self, nome):
        """Busca um produto pelo nome"""
        query = f"SELECT * FROM produtos p WHERE p.nome = '{nome}'"
        produtos = list(container.query_items(query=query, enable_cross_partition_query=True))

        if not produtos:
            ns.abort(404, "Produto não encontrado")

        return produtos[0]
