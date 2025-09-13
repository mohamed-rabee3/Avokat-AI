# Neo4j Aura GUI Queries

Use these queries in the Neo4j Aura Browser to explore your knowledge graph data.

## Basic Queries

### 1. View All Nodes and Relationships
```cypher
MATCH (n)-[r]->(m)
RETURN n, r, m
LIMIT 100
```

### 1.1. View All Nodes and Relationships by Language
```cypher
MATCH (n)-[r]->(m)
WHERE n.language = "arabic" AND m.language = "arabic"
RETURN n, r, m
LIMIT 100
```

### 2. Count All Nodes by Type
```cypher
MATCH (n)
RETURN labels(n)[0] as NodeType, count(n) as Count
ORDER BY Count DESC
```

### 2.1. Count All Nodes by Type and Language
```cypher
MATCH (n)
RETURN labels(n)[0] as NodeType, n.language as Language, count(n) as Count
ORDER BY Count DESC
```

### 3. Count All Relationships by Type
```cypher
MATCH ()-[r]->()
RETURN type(r) as RelationshipType, count(r) as Count
ORDER BY Count DESC
```

## Session-Specific Queries

### 4. View All Data for a Specific Session
```cypher
MATCH (n)-[r]->(m)
WHERE n.session_id = 1 AND m.session_id = 1
RETURN n, r, m
LIMIT 50
```

### 5. Count Nodes by Type for a Session
```cypher
MATCH (n)
WHERE n.session_id = 1
RETURN labels(n)[0] as NodeType, count(n) as Count
ORDER BY Count DESC
```

### 6. Count Relationships by Type for a Session
```cypher
MATCH ()-[r]->()
WHERE r.session_id = 1
RETURN type(r) as RelationshipType, count(r) as Count
ORDER BY Count DESC
```

## Entity Exploration

### 7. View All Entities
```cypher
MATCH (e:Entity)
WHERE e.session_id = 1
RETURN e.name, e.entity_type, e.description
ORDER BY e.name
```

### 8. View Entities by Type
```cypher
MATCH (e:Entity)
WHERE e.session_id = 1 AND e.entity_type = "PERSON"
RETURN e.name, e.description
ORDER BY e.name
```

### 9. View Entity Relationships
```cypher
MATCH (e1:Entity)-[r:RELATED_TO]->(e2:Entity)
WHERE e1.session_id = 1 AND e2.session_id = 1
RETURN e1.name, type(r), e2.name
LIMIT 20
```

## Fact Exploration

### 10. View All Facts
```cypher
MATCH (f:Fact)
WHERE f.session_id = 1
RETURN f.content, f.fact_type, f.confidence_score
ORDER BY f.confidence_score DESC
LIMIT 20
```

### 11. View Facts by Type
```cypher
MATCH (f:Fact)
WHERE f.session_id = 1 AND f.fact_type = "LEGAL_FACT"
RETURN f.content, f.confidence_score
ORDER BY f.confidence_score DESC
```

### 12. View Facts Related to Entities
```cypher
MATCH (e:Entity)<-[r:ABOUT]-(f:Fact)
WHERE e.session_id = 1 AND f.session_id = 1
RETURN e.name, f.content, f.fact_type
LIMIT 20
```

## Document Exploration

### 13. View All Documents
```cypher
MATCH (d:Document)
WHERE d.session_id = 1
RETURN d.title, d.document_type, d.file_size, d.upload_date
ORDER BY d.upload_date DESC
```

### 14. View Document Contents
```cypher
MATCH (d:Document)
WHERE d.session_id = 1
RETURN d.title, d.content
LIMIT 5
```

### 15. View Documents and Their Facts
```cypher
MATCH (d:Document)-[r:CONTAINS]->(f:Fact)
WHERE d.session_id = 1 AND f.session_id = 1
RETURN d.title, f.content, f.fact_type
LIMIT 20
```

## Legal Concept Exploration

### 16. View All Legal Concepts
```cypher
MATCH (lc:LegalConcept)
WHERE lc.session_id = 1
RETURN lc.term, lc.definition, lc.category, lc.jurisdiction
ORDER BY lc.term
```

### 17. View Legal Concepts by Category
```cypher
MATCH (lc:LegalConcept)
WHERE lc.session_id = 1 AND lc.category = "STATUTE"
RETURN lc.term, lc.definition
ORDER BY lc.term
```

### 18. View Related Legal Concepts
```cypher
MATCH (lc1:LegalConcept)-[r:RELATED_TO]->(lc2:LegalConcept)
WHERE lc1.session_id = 1 AND lc2.session_id = 1
RETURN lc1.term, lc2.term
LIMIT 20
```

## Case Exploration

### 19. View All Cases
```cypher
MATCH (c:Case)
WHERE c.session_id = 1
RETURN c.case_number, c.case_name, c.court, c.jurisdiction, c.status
ORDER BY c.case_date DESC
```

### 20. View Case Parties
```cypher
MATCH (c:Case)-[r:INVOLVES]->(e:Entity)
WHERE c.session_id = 1 AND e.session_id = 1
RETURN c.case_name, e.name, e.entity_type
LIMIT 20
```

## Advanced Queries

### 21. Find Most Connected Entities
```cypher
MATCH (e:Entity)
WHERE e.session_id = 1
OPTIONAL MATCH (e)-[r]-()
RETURN e.name, e.entity_type, count(r) as Connections
ORDER BY Connections DESC
LIMIT 10
```

### 22. Find Entities with Most Facts
```cypher
MATCH (e:Entity)<-[r:ABOUT]-(f:Fact)
WHERE e.session_id = 1 AND f.session_id = 1
RETURN e.name, e.entity_type, count(f) as FactCount
ORDER BY FactCount DESC
LIMIT 10
```

### 23. View Knowledge Graph Structure
```cypher
MATCH (n)
WHERE n.session_id = 1
OPTIONAL MATCH (n)-[r]->(m)
WHERE m.session_id = 1
RETURN DISTINCT labels(n)[0] as NodeType, 
       collect(DISTINCT type(r)) as RelationshipTypes
ORDER BY NodeType
```

### 24. Find Paths Between Entities
```cypher
MATCH path = (e1:Entity)-[*1..3]-(e2:Entity)
WHERE e1.session_id = 1 AND e2.session_id = 1
  AND e1.name CONTAINS "John" AND e2.name CONTAINS "Company"
RETURN path
LIMIT 5
```

### 25. Session Statistics Summary
```cypher
MATCH (n)
WHERE n.session_id = 1
WITH labels(n)[0] as NodeType, count(n) as NodeCount
OPTIONAL MATCH ()-[r]->()
WHERE r.session_id = 1
WITH NodeType, NodeCount, count(r) as RelCount
RETURN NodeType, NodeCount, RelCount
ORDER BY NodeCount DESC
```

## Multilingual Queries

### 26. View Arabic Content Only
```cypher
MATCH (n)-[r]->(m)
WHERE n.language = "arabic" AND m.language = "arabic"
RETURN n, r, m
LIMIT 50
```

### 27. View English Content Only
```cypher
MATCH (n)-[r]->(m)
WHERE n.language = "english" AND m.language = "english"
RETURN n, r, m
LIMIT 50
```

### 28. View Mixed Language Content
```cypher
MATCH (n)-[r]->(m)
WHERE n.language = "mixed" OR m.language = "mixed"
RETURN n, r, m
LIMIT 50
```

### 29. Count Entities by Language
```cypher
MATCH (n)
RETURN n.language as Language, labels(n)[0] as NodeType, count(n) as Count
ORDER BY Language, Count DESC
```

### 30. Find Arabic Legal Concepts
```cypher
MATCH (n)
WHERE n.language = "arabic" AND "LegalConcept" IN labels(n)
RETURN n.name, n.definition, n.category
ORDER BY n.name
```

### 31. Find Arabic Entities by Type
```cypher
MATCH (n)
WHERE n.language = "arabic" AND n.entity_type = "PERSON"
RETURN n.name, n.description
ORDER BY n.name
```

### 32. Cross-Language Relationships
```cypher
MATCH (n)-[r]->(m)
WHERE n.language <> m.language
RETURN n.name, n.language, type(r), m.name, m.language
LIMIT 20
```

## Database Management Queries

### 33. Clear All Data (Use with caution!)
```cypher
MATCH (n)
DETACH DELETE n
```

### 27. Clear Data for Specific Session
```cypher
MATCH (n)
WHERE n.session_id = 1
DETACH DELETE n
```

### 28. View Database Size
```cypher
MATCH (n)
RETURN count(n) as TotalNodes
UNION ALL
MATCH ()-[r]->()
RETURN count(r) as TotalRelationships
```

## Usage Instructions

1. **Open Neo4j Aura Browser**: Go to your Neo4j Aura console and open the browser
2. **Connect to Database**: Make sure you're connected to the correct database
3. **Run Queries**: Copy and paste any of the above queries into the query editor
4. **Modify Session ID**: Replace `session_id = 1` with your actual session ID
5. **Adjust Limits**: Modify `LIMIT` values based on your data size

## Tips

- Start with basic queries (#1-3) to get an overview
- Use session-specific queries (#4-6) to focus on specific data
- Explore different node types (#7-20) to understand your data structure
- Use advanced queries (#21-25) for deeper analysis
- Always be careful with deletion queries (#26-27)

## Common Modifications

- **Change Session ID**: Replace `1` with your session ID in WHERE clauses
- **Add More Filters**: Add additional WHERE conditions to narrow results
- **Sort Results**: Add `ORDER BY` clauses to sort by different properties
- **Limit Results**: Adjust `LIMIT` values to control result size
