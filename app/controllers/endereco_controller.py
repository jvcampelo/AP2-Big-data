from flask import request
from flask_restx import Resource, Namespace, fields
from app.database import db
from app.models.endereco import Endereco
from app.models.usuario import Usuario

# Criando namespace para o Swagger
ns = Namespace('enderecos', description='Operações relacionadas a endereços')

# Modelos para documentação do Swagger
endereco_model = ns.model('Endereco', {
    'id': fields.Integer(readonly=True),
    'usuario_id': fields.Integer(required=True, description='ID do usuário'),
    'logradouro': fields.String(required=True, description='Logradouro'),
    'complemento': fields.String(description='Complemento'),
    'bairro': fields.String(required=True, description='Bairro'),
    'cidade': fields.String(required=True, description='Cidade'),
    'uf': fields.String(required=True, description='UF'),
    'cep': fields.String(required=True, description='CEP'),
    'pais': fields.String(description='País'),
    'tipo': fields.String(description='Tipo do endereço')
})

@ns.route('/usuario/<int:usuario_id>')
@ns.param('usuario_id', 'ID do usuário')
class EnderecoUsuarioList(Resource):
    @ns.doc('list_enderecos_usuario')
    @ns.marshal_list_with(endereco_model)
    @ns.response(404, 'Usuário não encontrado')
    def get(self, usuario_id):
        """Lista todos os endereços de um usuário"""
        if not Usuario.query.get(usuario_id):
            ns.abort(404, "Usuário não encontrado")
            
        enderecos = Endereco.query.filter_by(usuario_id=usuario_id).all()
        if not enderecos:
            ns.abort(404, "Nenhum endereço encontrado para este usuário")
            
        return enderecos

    @ns.doc('create_endereco')
    @ns.expect(endereco_model)
    @ns.marshal_with(endereco_model, code=201)
    @ns.response(404, 'Usuário não encontrado')
    def post(self, usuario_id):
        """Cria um novo endereço para um usuário"""
        if not Usuario.query.get(usuario_id):
            ns.abort(404, "Usuário não encontrado")
        
        dados = request.json
        
        # Validar campos obrigatórios
        campos_obrigatorios = ["logradouro", "bairro", "cidade", "uf", "cep"]
        for campo in campos_obrigatorios:
            if not dados.get(campo):
                ns.abort(400, f"O campo '{campo}' é obrigatório")
        
        endereco = Endereco(
            usuario_id=usuario_id,
            logradouro=dados["logradouro"],
            complemento=dados.get("complemento"),
            bairro=dados["bairro"],
            cidade=dados["cidade"],
            uf=dados["uf"],
            cep=dados["cep"],
            pais=dados.get("pais", "Brasil"),
            tipo=dados.get("tipo")
        )
        
        try:
            db.session.add(endereco)
            db.session.commit()
            return endereco, 201
        except Exception as e:
            db.session.rollback()
            ns.abort(500, "Erro ao criar endereço")

@ns.route('/<int:id>')
@ns.param('id', 'ID do endereço')
@ns.response(404, 'Endereço não encontrado')
class EnderecoResource(Resource):
    @ns.doc('update_endereco')
    @ns.expect(endereco_model)
    @ns.marshal_with(endereco_model)
    def put(self, id):
        """Atualiza um endereço"""
        endereco = Endereco.query.get(id)
        if not endereco:
            ns.abort(404, "Endereço não encontrado")
        
        dados = request.json
        if not dados:
            ns.abort(400, "O corpo da requisição não pode estar vazio")
        
        endereco.logradouro = dados.get("logradouro", endereco.logradouro)
        endereco.complemento = dados.get("complemento", endereco.complemento)
        endereco.bairro = dados.get("bairro", endereco.bairro)
        endereco.cidade = dados.get("cidade", endereco.cidade)
        endereco.uf = dados.get("uf", endereco.uf)
        endereco.cep = dados.get("cep", endereco.cep)
        endereco.pais = dados.get("pais", endereco.pais)
        endereco.tipo = dados.get("tipo", endereco.tipo)
        
        try:
            db.session.commit()
            return endereco
        except Exception as e:
            db.session.rollback()
            ns.abort(500, "Erro ao atualizar endereço")

    @ns.doc('delete_endereco')
    @ns.response(204, 'Endereço deletado')
    def delete(self, id):
        """Deleta um endereço"""
        endereco = Endereco.query.get(id)
        if not endereco:
            ns.abort(404, "Endereço não encontrado")
        
        db.session.delete(endereco)
        db.session.commit()
        return '', 204