from flask import request
from flask_restx import Resource, Namespace, fields
from app.database import db
from app.models.usuario import Usuario

# Criando namespace para o Swagger
ns = Namespace('usuarios', description='Operações relacionadas a usuários')

# Modelos para documentação do Swagger
usuario_model = ns.model('Usuario', {
    'id': fields.Integer(readonly=True),
    'nome': fields.String(required=True, description='Nome do usuário'),
    'email': fields.String(required=True, description='Email do usuário'),
    'dt_nascimento': fields.String(description='Data de nascimento'),
    'cpf': fields.String(description='CPF do usuário'),
    'telefone': fields.String(description='Telefone do usuário')
})

@ns.route('')
class UsuarioList(Resource):
    @ns.doc('list_usuarios')
    @ns.marshal_list_with(usuario_model)
    def get(self):
        """Lista todos os usuários"""
        usuarios = Usuario.query.all()
        return usuarios

    @ns.doc('create_usuario')
    @ns.expect(usuario_model)
    @ns.marshal_with(usuario_model, code=201)
    def post(self):
        """Cria um novo usuário"""
        dados = request.json

        if not dados.get("nome") or not dados.get("email"):
            ns.abort(400, "Nome e email são obrigatórios")

        novo_usuario = Usuario(
            nome=dados["nome"],
            email=dados["email"],
            dt_nascimento=dados.get("dt_nascimento"),
            cpf=dados.get("cpf"),
            telefone=dados.get("telefone")
        )

        try:
            db.session.add(novo_usuario)
            db.session.commit()
            return novo_usuario, 201
        except Exception as e:
            db.session.rollback()
            ns.abort(500, "Erro ao salvar usuário no banco de dados")

@ns.route('/<int:id>')
@ns.param('id', 'Identificador do usuário')
@ns.response(404, 'Usuário não encontrado')
class UsuarioResource(Resource):
    @ns.doc('get_usuario')
    @ns.marshal_with(usuario_model)
    def get(self, id):
        """Busca um usuário específico"""
        usuario = Usuario.query.get(id)
        if not usuario:
            ns.abort(404, "Usuário não encontrado")
        return usuario

    @ns.doc('update_usuario')
    @ns.expect(usuario_model)
    @ns.marshal_with(usuario_model)
    def put(self, id):
        """Atualiza um usuário"""
        usuario = Usuario.query.get(id)
        if not usuario:
            ns.abort(404, "Usuário não encontrado")

        dados = request.json
        if not dados:
            ns.abort(400, "O corpo da requisição não pode estar vazio")

        usuario.nome = dados.get("nome", usuario.nome)
        usuario.email = dados.get("email", usuario.email)
        usuario.dt_nascimento = dados.get("dt_nascimento", usuario.dt_nascimento)
        usuario.cpf = dados.get("cpf", usuario.cpf)
        usuario.telefone = dados.get("telefone", usuario.telefone)

        db.session.commit()
        return usuario

    @ns.doc('delete_usuario')
    @ns.response(204, 'Usuário deletado')
    def delete(self, id):
        """Deleta um usuário"""
        usuario = Usuario.query.get(id)
        if not usuario:
            ns.abort(404, "Usuário não encontrado")

        db.session.delete(usuario)
        db.session.commit()
        return '', 204
