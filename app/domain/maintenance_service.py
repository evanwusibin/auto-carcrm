class MaintenanceService:
    def check(self, payload: dict, *, user_id: str) -> dict:
        return {
            'user_id': user_id,
            'result': 'pending',
            'payload': payload,
        }


maintenance_service = MaintenanceService()
