import os
from google.cloud.sql.connector import Connector
import sqlalchemy

INSTANCE_CONNECTION_NAME = os.environ["INSTANCE_CONNECTION_NAME"]
DB_USER = os.environ["DB_USER"]
DB_PASS = os.environ["DB_PASS"]
DB_NAME = os.environ["DB_NAME"]

class DBHandler:
    def __init__(self):
        self.is_connected = False
        self.connector = Connector()
        self.engine = None

    
    def _getconn(self):
        conn = self.connector.connect(
            INSTANCE_CONNECTION_NAME,
            "pg8000",
            user=DB_USER,
            password=DB_PASS,
            db=DB_NAME,
        )
        return conn

    def setupEngine(self):
        if self.is_connected:
            return
        
        engine = sqlalchemy.create_engine(
            "postgresql+pg8000://",
            creator=self._getconn,
            pool_size=5,
            max_overflow=2,
            pool_timeout=30,
            pool_recycle=1800,
        )
        self.engine = engine
        self.is_connected = True
    
    def query(self, query, method = "findone"):
        if self.is_connected != True:
            self.setupEngine()

        if method == "findone":
            with self.engine.connect() as connection:
                result = connection.execute(sqlalchemy.text(query))
                return result.fetchone()
        elif method == "findall":
            with self.engine.connect() as connection:
                result = connection.execute(sqlalchemy.text(query))
                return result.fetchall()
    
    def close(self):
        if hasattr(self, "connector"):
            self.connector.close()