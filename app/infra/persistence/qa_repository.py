from app.shared.clients.mongo_business_utils import get_business_db


class QARepository:
    @property
    def db(self):
        return get_business_db()


qa_repository = QARepository()
