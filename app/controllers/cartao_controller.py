from flask import request
from flask_restx import Resource, Namespace, fields
from app.database import db
from app.models.usuario import Usuario
from app.models.cartao import Cartao
from app.request.transacao_request import TransacaoRequest
from app.response.transacao_response import TransacaoResponse
from datetime import datetime
import uuid
from decimal import Decimal
from dateutil.relativedelta import relativedelta

# Criando namespace para o Swagger
ns = Namespace('cartoes', description='Operações relacionadas a cartões')

# Modelos para documentação do Swagger
cartao_model = ns.model('Cartao', {
    'id': fields.Integer(readonly=True),
    'usuario_id': fields.Integer(required=True, description='ID do usuário'),
    'numero': fields.String(required=True, description='Número do cartão'),
    'nome_impresso': fields.String(required=True, description='Nome impresso no cartão'),
    'validade': fields.String(required=True, description='Data de validade (MM/AAAA)'),
    'cvv': fields.String(required=True, description='Código de segurança'),
    'bandeira': fields.String(required=True, description='Bandeira do cartão'),
    'tipo': fields.String(description='Tipo do cartão'),
    'saldo': fields.Float(description='Saldo disponível')
})

transacao_model = ns.model('Transacao', {
    'numero': fields.String(required=True, description='Número do cartão'),
    'cvv': fields.String(required=True, description='Código de segurança'),
    'dt_expiracao': fields.String(required=True, description='Data de expiração (MM/AAAA)'),
    'valor': fields.Float(required=True, description='Valor da transação')
})

transacao_response_model = ns.model('TransacaoResponse', {
    'status': fields.String(description='Status da transação'),
    'codigo_autorizacao': fields.String(description='Código de autorização'),
    'dt_transacao': fields.DateTime(description='Data da transação'),
    'message': fields.String(description='Mensagem de retorno')
})

@ns.route('/usuario/<int:id_user>')
@ns.param('id_user', 'ID do usuário')
class CartaoUsuarioList(Resource):
    @ns.doc('list_cartoes_usuario')
    @ns.marshal_list_with(cartao_model)
    @ns.response(404, 'Usuário não encontrado')
    def get(self, id_user):
        """Lista todos os cartões de um usuário"""
        usuario = Usuario.query.get(id_user)
        if not usuario:
            ns.abort(404, "Usuário não encontrado")
            
        cartoes = Cartao.query.filter_by(usuario_id=id_user).all()
        if not cartoes:
            ns.abort(404, "Nenhum cartão encontrado para este usuário")
            
        return cartoes

    @ns.doc('create_cartao')
    @ns.expect(cartao_model)
    @ns.marshal_with(cartao_model, code=201)
    @ns.response(404, 'Usuário não encontrado')
    def post(self, id_user):
        """Cria um novo cartão para um usuário"""
        try:
            data = request.get_json()
            
            if not data:
                ns.abort(400, "O corpo da requisição não pode estar vazio")

            usuario = Usuario.query.get(id_user)
            if not usuario:
                ns.abort(404, "Usuário não encontrado")
            
            # Validar campos obrigatórios
            campos_obrigatorios = ["numero", "nome_impresso", "validade", "cvv", "bandeira"]
            for campo in campos_obrigatorios:
                if not data.get(campo):
                    ns.abort(400, f"O campo '{campo}' é obrigatório")
            
            # Verificar se já existe um cartão com o mesmo número para este usuário
            cartao_existente = Cartao.query.filter_by(
                usuario_id=id_user,
                numero=data["numero"]
            ).first()
            
            if cartao_existente:
                ns.abort(400, "Já existe um cartão cadastrado com este número para este usuário")
            
            mes, ano = map(int, data["validade"].split("/"))
            validade = datetime(ano, mes, 1) + relativedelta(day=31)

            novo_cartao = Cartao(
                usuario_id=id_user,
                numero=data["numero"],
                nome_impresso=data["nome_impresso"],
                validade=validade,
                cvv=data["cvv"],
                bandeira=data["bandeira"],
                tipo=data.get("tipo", ""),
                saldo=data.get("saldo", 0.00),
            )

            db.session.add(novo_cartao)
            db.session.commit()

            return novo_cartao, 201
            
        except ValueError:
            ns.abort(400, "Formato de data inválido. Use o formato MM/AAAA")
        except Exception as e:
            db.session.rollback()
            ns.abort(500, "Erro ao criar cartão")

@ns.route('/authorize/usuario/<int:id_user>')
@ns.param('id_user', 'ID do usuário')
class CartaoAutorizacao(Resource):
    @ns.doc('authorize_transaction')
    @ns.expect(transacao_model)
    @ns.marshal_with(transacao_response_model)
    @ns.response(404, 'Usuário ou cartão não encontrado')
    def post(self, id_user):
        """Autoriza uma transação com cartão"""
        try:
            data = request.get_json()
            transacao = TransacaoRequest(**data)

            usuario = Usuario.query.get(id_user)
            if not usuario:
                return TransacaoResponse(
                    status="NOT_AUTHORIZED",
                    codigo_autorizacao=None,
                    dt_transacao=datetime.utcnow(),
                    message="Usuário não encontrado"
                ), 404

            cartao = Cartao.query.filter_by(usuario_id=id_user, numero=transacao.numero, cvv=transacao.cvv).first()
            if not cartao:
                return TransacaoResponse(
                    status="NOT_AUTHORIZED",
                    codigo_autorizacao=None,
                    dt_transacao=datetime.utcnow(),
                    message="Cartão não encontrado"
                ), 404
            
            mes, ano = map(int, transacao.dt_expiracao.split("/"))
            validade_requisicao = datetime(ano, mes, 1) + relativedelta(day=31)

            if cartao.validade < datetime.utcnow():
                return TransacaoResponse(
                    status="NOT_AUTHORIZED",
                    codigo_autorizacao=None,
                    dt_transacao=datetime.utcnow(),
                    message="Cartão expirado"
                ), 400
            
            if cartao.validade != validade_requisicao:
                return TransacaoResponse(
                    status="NOT_AUTHORIZED",
                    codigo_autorizacao=None,
                    dt_transacao=datetime.utcnow(),
                    message="Validade incorreta"
                ), 400

            if cartao.saldo < Decimal(str(transacao.valor)):
                return TransacaoResponse(
                    status="NOT_AUTHORIZED",
                    codigo_autorizacao=None,
                    dt_transacao=datetime.utcnow(),
                    message="Saldo insuficiente"
                ), 400

            cartao.saldo -= Decimal(str(transacao.valor))
            db.session.commit()

            return TransacaoResponse(
                status="AUTHORIZED",
                codigo_autorizacao=uuid.uuid4(),
                dt_transacao=datetime.utcnow(),
                message="Compra autorizada"
            ), 200

        except Exception as e:
            ns.abort(500, str(e))

@ns.route('/saldo/<int:id>')
@ns.param('id', 'ID do cartão')
class CartaoSaldo(Resource):
    @ns.doc('update_saldo')
    @ns.expect(ns.model('SaldoUpdate', {
        'saldo': fields.Float(required=True, description='Valor a ser adicionado ao saldo')
    }))
    @ns.response(404, 'Cartão não encontrado')
    def put(self, id):
        """Atualiza o saldo de um cartão"""
        try:
            data = request.get_json()
            
            if 'saldo' not in data:
                ns.abort(400, "O campo 'saldo' é obrigatório")
                
            cartao = Cartao.query.get(id)
            if not cartao:
                ns.abort(404, "Cartão não encontrado")
            
            cartao.saldo += Decimal(str(data['saldo']))
            db.session.commit()
            
            return {
                "message": "Saldo atualizado com sucesso",
                "cartao_id": cartao.id,
                "saldo": float(cartao.saldo)
            }, 200
            
        except Exception as e:
            ns.abort(500, str(e))

@ns.route('/<int:id>')
@ns.param('id', 'ID do cartão')
class CartaoResource(Resource):
    @ns.doc('delete_cartao')
    @ns.response(204, 'Cartão deletado')
    def delete(self, id):
        """Deleta um cartão"""
        try:
            cartao = Cartao.query.get(id)
            if not cartao:
                ns.abort(404, "Cartão não encontrado")
                
            db.session.delete(cartao)
            db.session.commit()
            
            return '', 204
            
        except Exception as e:
            ns.abort(500, str(e))

