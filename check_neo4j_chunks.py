import asyncio
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Load environment variables
load_dotenv()

async def check_chunks():
    # Neo4j Aura connection
    uri = os.getenv("NEO4J_URI")
    username = os.getenv("NEO4J_USERNAME") 
    password = os.getenv("NEO4J_PASSWORD")
    
    print(f"Connecting to Neo4j Aura: {uri}")
    
    driver = GraphDatabase.driver(uri, auth=(username, password))
    
    try:
        with driver.session(database='neo4j') as session:
            # Check what nodes exist
            result = session.run('MATCH (n) RETURN labels(n) as labels, count(n) as count ORDER BY count DESC')
            print('Node types in database:')
            for record in result:
                print(f'  {record["labels"]}: {record["count"]} nodes')
            
            # Check DocumentChunk nodes specifically for session 2
            result = session.run('''
                MATCH (n:DocumentChunk) 
                WHERE n.session_id = "2"
                RETURN keys(n) as properties, n.session_id, n.chunk_index, 
                       size(n.content) as content_length,
                       n.content[0..100] as content_preview
                ORDER BY n.chunk_index
            ''')
            
            print('\nDocumentChunk nodes for session 2:')
            chunks = list(result)
            if chunks:
                for record in chunks:
                    print(f'  Properties: {record["properties"]}')
                    print(f'  Session: {record.get("n.session_id", "N/A")}, Chunk: {record.get("n.chunk_index", "N/A")}')
                    print(f'  Content length: {record.get("content_length", "N/A")} chars')
                    print(f'  Preview: {record.get("content_preview", "N/A")}...')
                print(f'Total chunks found: {len(chunks)}')
            else:
                print('  No DocumentChunk nodes found for session 2')
            
            # Check all DocumentChunk nodes
            result = session.run('''
                MATCH (n:DocumentChunk) 
                RETURN n.session_id, count(n) as chunk_count
                ORDER BY n.session_id
            ''')
            
            print('\nAll DocumentChunk nodes by session:')
            for record in result:
                print(f'  Session {record["session_id"]}: {record["chunk_count"]} chunks')
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    asyncio.run(check_chunks())
