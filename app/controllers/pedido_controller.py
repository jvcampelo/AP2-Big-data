from flask import request
from flask_restx import Resource, Namespace, fields
from app.database import db
from app.models.pedido import Pedido
from datetime import datetime
from app.models.usuario import Usuario

# Criando namespace para o Swagger
ns = Namespace('pedidos', description='Operações relacionadas a pedidos')

# Modelos para documentação do Swagger
pedido_model = ns.model('Pedido', {
    'id_pedido': fields.Integer(readonly=True, description='ID do pedido'),
    'nome_cliente': fields.String(required=True, description='Nome do cliente'),
    'nome_produto': fields.String(required=True, description='Nome do produto'),
    'data_pedido': fields.Date(required=True, description='Data do pedido'),
    'valor_total': fields.Float(required=True, description='Valor total do pedido'),
    'status': fields.String(required=True, description='Status do pedido'),
    'id_usuario': fields.Integer(required=True, description='ID do usuário')
})

@ns.route('')
class PedidoList(Resource):
    @ns.doc('list_pedidos')
    @ns.marshal_list_with(pedido_model)
    def get(self):
        """Lista todos os pedidos"""
        pedidos = Pedido.query.all()
        return pedidos

    @ns.doc('create_pedido')
    @ns.expect(pedido_model)
    @ns.marshal_with(pedido_model, code=201)
    @ns.response(404, 'Usuário não encontrado')
    def post(self):
        """Cria um novo pedido"""
        dados = request.json
        if not dados.get("nome_cliente") or not dados.get("nome_produto") or not dados.get("valor_total"):
            ns.abort(400, "Nome do cliente, nome dos produtos, preço e data da compra são obrigatórios")

        usuario = Usuario.query.filter(Usuario.nome.ilike(dados["nome_cliente"])).first()
        if not usuario:
            ns.abort(404, "Usuário não encontrado para o nome fornecido")

        novo_pedido = Pedido(
            nome_cliente=dados["nome_cliente"],
            data_pedido=datetime.strptime(dados["data_pedido"], "%Y-%m-%d"),
            nome_produto=dados["nome_produto"],
            valor_total=dados["valor_total"],
            status=dados["status"],
            id_usuario=usuario.id
        )

        db.session.add(novo_pedido)
        db.session.commit()
        return novo_pedido, 201

@ns.route('/<int:id>')
@ns.param('id', 'ID do pedido')
@ns.response(404, 'Pedido não encontrado')
class PedidoResource(Resource):
    @ns.doc('get_pedido')
    @ns.marshal_with(pedido_model)
    def get(self, id):
        """Busca um pedido específico"""
        pedido = Pedido.query.get_or_404(id)
        return pedido

    @ns.doc('update_pedido')
    @ns.expect(pedido_model)
    @ns.marshal_with(pedido_model)
    def put(self, id):
        """Atualiza um pedido"""
        pedido = Pedido.query.get_or_404(id)
        data = request.json

        pedido.nome_cliente = data.get("nome_cliente", pedido.nome_cliente)
        pedido.data_pedido = datetime.strptime(data["data_pedido"], "%Y-%m-%d")
        pedido.nome_produto = data.get("nome_produto", pedido.nome_produto)
        pedido.valor_total = data.get("valor_total", pedido.valor_total)
        pedido.status = data.get("status", pedido.status)

        db.session.commit()
        return pedido

    @ns.doc('delete_pedido')
    @ns.response(204, 'Pedido deletado')
    def delete(self, id):
        """Deleta um pedido"""
        pedido = Pedido.query.get_or_404(id)
        db.session.delete(pedido)
        db.session.commit()
        return '', 204

@ns.route('/nome/<string:nome>')
@ns.param('nome', 'Nome do cliente')
class PedidoNomeResource(Resource):
    @ns.doc('list_pedidos_por_nome')
    @ns.marshal_list_with(pedido_model)
    def get(self, nome):
        """Lista pedidos por nome do cliente"""
        pedidos = Pedido.query.filter(
            Pedido.nome_cliente.ilike(f"%{nome}%")
        ).all()
        return pedidos
