from fastapi import APIRouter, HTTPException, Query
import logging

from app.schemas.graph import GraphResponse
from app.services.neo4j_service import neo4j_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/neo4j", tags=["neo4j"])


@router.get("/test")
def test_neo4j_connection():
    try:
        result = neo4j_service.verify_connectivity()
        if not result:
            raise Exception("connectivity check failed")

        # Đảm bảo nút Test đơn giản tồn tại và trả về nút đó
        try:
            repo = neo4j_service._repository
            # đảm bảo trình điều khiển (driver) tồn tại
            repo._ensure_driver()
            # sử dụng phiên làm việc (session) trực tiếp để thực hiện ghi/đọc
            with repo._driver.session() as session:
                session.run("MERGE (t:Test {name: $name})", name="hello")
                result = session.run(
                    "MATCH (t:Test {name: $name}) RETURN t.name AS name", name="hello"
                )
                rows = [r.data() for r in result]
                node = rows[0] if rows else None
        except Exception:
            node = None

        return {"status": "connected", "result": result, "node": node}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Neo4j connection failed: {str(e)}")


@router.get("/stats")
def get_neo4j_stats():
    """Lấy thông tin thống kê về dữ liệu Neo4j."""
    stats = neo4j_service.get_graph_stats()
    return stats


@router.get("/graph", response_model=GraphResponse)
def get_graph_data(limit: int = Query(100, ge=1, le=1000)):
    """Lấy tất cả các nút và mối quan hệ phục vụ cho trực quan hóa đồ thị."""
    return neo4j_service.get_graph_data(limit=limit)
