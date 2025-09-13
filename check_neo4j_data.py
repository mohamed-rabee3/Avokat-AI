import asyncio
from neo4j import AsyncGraphDatabase
from dotenv import load_dotenv
import os

load_dotenv()

async def check_neo4j_data():
    driver = AsyncGraphDatabase.driver(
        os.getenv('NEO4J_URI'),
        auth=(os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD'))
    )
    
    try:
        async with driver.session(database='neo4j') as session:
            # Check what node types exist
            result = await session.run('MATCH (n) RETURN labels(n) as labels, count(n) as count ORDER BY count DESC')
            print('Node types in database:')
            async for record in result:
                print(f'  {record["labels"]}: {record["count"]} nodes')
            
            # Check DocumentChunk nodes specifically
            result = await session.run('MATCH (n:DocumentChunk) RETURN n LIMIT 5')
            print('\nDocumentChunk nodes:')
            async for record in result:
                node = record["n"]
                print(f'  Node: {dict(node)}')
                print(f'    Properties: {list(node.keys())}')
            
            # Check if any nodes have embeddings
            result = await session.run('MATCH (n) WHERE n.embedding IS NOT NULL RETURN labels(n) as labels, count(n) as count')
            print('\nNodes with embeddings:')
            async for record in result:
                print(f'  {record["labels"]}: {record["count"]} nodes with embeddings')
                
    finally:
        await driver.close()

if __name__ == "__main__":
    asyncio.run(check_neo4j_data())
