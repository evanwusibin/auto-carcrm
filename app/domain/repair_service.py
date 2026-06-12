class RepairService:
    def create(self, payload: dict, *, user_id: str) -> dict:
        return {
            'order_id': 'RO-SKELETON-001',
            'state': 'submitted',
            'user_id': user_id,
            'payload': payload,
        }

    def get(self, order_id: str, *, user_id: str) -> dict:
        return {
            'order_id': order_id,
            'state': 'submitted',
            'user_id': user_id,
            'message': '报修单骨架已建立，后续接入 Mongo 持久化。',
        }


repair_service = RepairService()
