from fastapi import APIRouter, HTTPException, Query
from .models import Agency, Review
from .store import IndexUnavailable, Store


def router(store: Store):
    api = APIRouter()

    @api.get("/v2/sources")
    def sources(agency: Agency | None = None, review_status: Review | None = None,
                limit: int = Query(20, ge=1, le=50), offset: int = Query(0, ge=0)):
        items = [store.detail(key) for key in sorted(store.catalog)]
        items = [item for item in items if (not agency or item["source"]["agency"] == agency)
                 and (not review_status or item["review_status"] == review_status)]
        return {"status": "ok" if items else "empty", "total": len(items),
                "limit": limit, "offset": offset, "results": items[offset:offset + limit]}

    @api.get("/v2/sources/{source_id}")
    def source(source_id: str):
        if source_id not in store.catalog:
            raise HTTPException(404, "unknown_source")
        return store.detail(source_id)

    @api.get("/v2/references/search")
    def search(q: str = Query(min_length=1, max_length=500), agency: Agency | None = None,
               source_id: str | None = None, limit: int = Query(20, ge=1, le=50),
               offset: int = Query(0, ge=0)):
        if source_id and source_id not in store.catalog:
            raise HTTPException(404, "unknown_source")
        try:
            return store.search(q, agency, source_id, limit, offset)
        except ValueError:
            raise HTTPException(422, "query_requires_search_terms") from None
        except IndexUnavailable as error:
            raise HTTPException(503, str(error)) from None

    return api
