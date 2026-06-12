from app.shared.clients.mongo_business_utils import get_business_db


class VehicleRepository:
    @property
    def db(self):
        return get_business_db()


vehicle_repository = VehicleRepository()
