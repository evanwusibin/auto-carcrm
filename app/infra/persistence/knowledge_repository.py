from app.shared.clients.mongo_knowledge_utils import get_knowledge_db


class KnowledgeRepository:
    @property
    def db(self):
        return get_knowledge_db()


knowledge_repository = KnowledgeRepository()
