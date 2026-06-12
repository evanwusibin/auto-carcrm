class CaseService:
    def submit(self, payload: dict, *, user_id: str) -> dict:
        return {
            'user_id': user_id,
            'state': 'draft',
            'payload': payload,
        }


case_service = CaseService()
