import os

class Config:
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://aluno:Ibmec2025@ibmectradingbot20252.mysql.database.azure.com:3306/bigdata?ssl=true&ssl_verify_cert=false"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    AZURE_COSMOS_URI = "https://banco-ibmec.documents.azure.com:443/"
    AZURE_COSMOS_KEY = "GOp8Yah6hONJFQ7exeCt6UBkQNNfb06Zot8lSH9JquDS2ee6uCCL0Lx9UF16QzdX5G36ogbawjDmACDbwrfmQQ=="
    AZURE_COSMOS_DATABASE = "ibmec-mall"
