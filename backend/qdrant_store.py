
from qdrant_client import QdrantClient
from .constants import COLLECTION_NAME

def get_collection_size(client: QdrantClient) -> int:
    info = client.get_collection(collection_name=COLLECTION_NAME)
    # qdrant-client >= 1.10 exposes `points_count` on CollectionInfo
    return getattr(info, "points_count", 0) or 0
