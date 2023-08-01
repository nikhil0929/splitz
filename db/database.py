from sqlalchemy import create_engine
import logging
from .base_model import Base
from .models import *


# SQLALCHEMY_DATABASE_URL = "postgres://YourUserName:YourPassword@YourHostname:5432/YourDatabaseName"


class Database:
    def __init__(
        self, db_user: str, db_password: str, db_host: str, db_port: str, db_name: str
    ):
        self.database_url = (
            f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        )
        self.engine = create_engine(self.database_url)

    def get_engine(self):
        return self.engine
        
    # def get_db(self):
    #     db = self.session_local()
    #     try:
    #         yield db
    #     finally:
    #         db.close()

    def run_migrations(self):
        Base.metadata.create_all(self.engine)
        print("Migrations complete")
        logging.info("Migrations complete")
