#!/usr/bin/env python3
"""
Script to clear all data from Neo4j Aura database
"""
import asyncio
import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.db.neo4j import neo4j_manager
from app.core.config import settings

async def clear_all_data():
    """Clear all data from Neo4j database"""
    try:
        print("Initializing Neo4j connection...")
        await neo4j_manager.initialize()
        print(f"Connected to Neo4j: {settings.neo4j_uri}")
        
        # Clear all nodes and relationships
        print("Clearing all data from Neo4j database...")
        
        # Delete all relationships first
        delete_relationships_query = """
        MATCH ()-[r]->()
        DELETE r
        """
        
        # Delete all nodes
        delete_nodes_query = """
        MATCH (n)
        DELETE n
        """
        
        # Execute queries
        async with neo4j_manager.driver.session(database=settings.neo4j_database) as session:
            # Delete relationships
            result = await session.run(delete_relationships_query)
            summary = await result.consume()
            relationships_deleted = summary.counters.relationships_deleted
            print(f"Deleted {relationships_deleted} relationships")
            
            # Delete nodes
            result = await session.run(delete_nodes_query)
            summary = await result.consume()
            nodes_deleted = summary.counters.nodes_deleted
            print(f"Deleted {nodes_deleted} nodes")
        
        print("✅ Successfully cleared all data from Neo4j Aura database")
        
    except Exception as e:
        print(f"❌ Error clearing Neo4j database: {e}")
        raise
    finally:
        await neo4j_manager.close()
        print("Neo4j connection closed")

if __name__ == "__main__":
    asyncio.run(clear_all_data())
