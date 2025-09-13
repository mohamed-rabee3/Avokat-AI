import asyncio
from app.db.neo4j import neo4j_manager
from app.core.config import settings

async def check_db():
    await neo4j_manager.initialize()
    driver = neo4j_manager.driver
    
    with driver.session(database='neo4j') as session:
        # Check what nodes exist
        result = session.run('MATCH (n) RETURN labels(n) as labels, count(n) as count ORDER BY count DESC')
        print('Node types in database:')
        for record in result:
            print(f'  {record["labels"]}: {record["count"]} nodes')
        
        # Check DocumentChunk nodes specifically
        result = session.run('MATCH (n:DocumentChunk) RETURN n.session_id, n.chunk_index, n.content[0..50] as content_preview, keys(n) as properties LIMIT 5')
        print('\nDocumentChunk nodes:')
        for record in result:
            print(f'  Session {record["session_id"]}, Chunk {record["chunk_index"]}: {record["content_preview"]}...')
            print(f'    Properties: {record["properties"]}')
    
    await neo4j_manager.close()

if __name__ == "__main__":
    asyncio.run(check_db())
