class WarrantyService:
    def precheck(self, payload: dict, *, user_id: str) -> dict:
        return {
            'user_id': user_id,
            'result': 'insufficient_info',
            'issues': [],
            'details': {},
            'disclaimer': '本结果仅为初步预判，最终质保结论以授权服务站检测结果为准。',
            'raw_payload': payload,
        }


warranty_service = WarrantyService()
