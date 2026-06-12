from app.shared.clients.mongo_business_utils import get_business_db


class DiagnosisRepository:
    @property
    def db(self):
        return get_business_db()


diagnosis_repository = DiagnosisRepository()
