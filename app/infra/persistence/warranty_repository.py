from app.shared.clients.mongo_business_utils import get_business_db


class WarrantyRepository:
    @property
    def db(self):
        return get_business_db()


warranty_repository = WarrantyRepository()
