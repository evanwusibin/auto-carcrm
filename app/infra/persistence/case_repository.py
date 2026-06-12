from app.shared.clients.mongo_business_utils import get_business_db


class CaseRepository:
    @property
    def db(self):
        return get_business_db()


case_repository = CaseRepository()
