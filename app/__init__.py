from flask import Flask
from flask_restx import Api
from app.database import db
from app.config import Config
from app.controllers.usuario_controller import ns as usuario_ns
from app.controllers.endereco_controller import ns as endereco_ns
from app.controllers.cartao_controller import ns as cartao_ns
from app.controllers.produto_controller import ns as produto_ns
from app.controllers.pedido_controller import ns as pedido_ns

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Configuração do Swagger
    api = Api(
        app,
        version='1.0',
        title='API de E-commerce',
        description='API RESTful para sistema de e-commerce',
        doc='/docs'
    )

    # Registrando os namespaces do Swagger
    api.add_namespace(usuario_ns, path='/usuario')
    api.add_namespace(endereco_ns, path='/endereco')
    api.add_namespace(cartao_ns, path='/cartao')
    api.add_namespace(produto_ns, path='/produto')
    api.add_namespace(pedido_ns, path='/pedido')

    db.init_app(app)

    return app
