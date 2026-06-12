from app.shared.clients.mongo_business_utils import get_business_db


class RepairRepository:
    @property
    def db(self):
        return get_business_db()


repair_repository = RepairRepository()
