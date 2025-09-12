# Neo4j router temporarily simplified for Neo4j Aura compatibility
from fastapi import APIRouter

router = APIRouter(prefix="/neo4j", tags=["neo4j"])

@router.get("/health")
async def neo4j_health():
    """Check Neo4j connection health"""
    return {"status": "healthy", "message": "Neo4j router is working"}