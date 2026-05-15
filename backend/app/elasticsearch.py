from elasticsearch import AsyncElasticsearch

from app.config import settings

es_client: AsyncElasticsearch | None = None


async def init_elasticsearch():
    global es_client
    if not settings.elasticsearch_enabled:
        return
    es_client = AsyncElasticsearch(settings.elasticsearch_hosts)
    if await es_client.ping():
        await _ensure_indexes()


async def close_elasticsearch():
    global es_client
    if es_client:
        await es_client.close()
        es_client = None


async def _ensure_indexes():
    assert es_client is not None
    index_name = "listings"
    if not await es_client.indices.exists(index=index_name):
        await es_client.indices.create(
            index=index_name,
            body={
                "settings": {"number_of_shards": 1, "number_of_replicas": 0},
                "mappings": {
                    "properties": {
                        "id": {"type": "keyword"},
                        "title": {"type": "text", "analyzer": "standard"},
                        "description": {"type": "text", "analyzer": "standard"},
                        "city": {"type": "keyword"},
                        "price": {"type": "float"},
                        "location": {"type": "geo_point"},
                        "host_id": {"type": "keyword"},
                        "status": {"type": "keyword"},
                        "created_at": {"type": "date"},
                    }
                },
            },
        )


def get_es() -> AsyncElasticsearch | None:
    return es_client
