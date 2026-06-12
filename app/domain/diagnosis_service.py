class DiagnosisService:
    def run(self, payload: dict, *, user_id: str) -> dict:
        return {
            'user_id': user_id,
            'risk_level': 'medium',
            'possible_causes': [],
            'suggestion': '诊断服务骨架已建立，后续接入 RAG 检索和规则判断。',
            'raw_payload': payload,
        }


diagnosis_service = DiagnosisService()
