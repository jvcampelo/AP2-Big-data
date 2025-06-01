from app import create_app
from app.database import db
import logging

# Configuração do logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = create_app()

def init_db():
    try:
        with app.app_context():
            logger.info("Criando tabelas do banco de dados...")
            db.create_all()
            logger.info("Tabelas criadas com sucesso!")
    except Exception as e:
        logger.error(f"Erro ao criar tabelas: {str(e)}")
        raise

if __name__ == "__main__":
    init_db()
    logger.info("Iniciando servidor na porta 8000...")
    app.run(host="0.0.0.0", port=8000)
