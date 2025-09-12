# 🚀 Neo4j Aura Cloud Setup Guide

This guide will help you set up Neo4j Aura (cloud version) for your Avokat AI application.

## 📋 Prerequisites

- A Neo4j Aura account (free tier available)
- Your Aura database connection details

## 🔧 Step 1: Create Neo4j Aura Account

1. **Go to Neo4j Aura Console**
   - Visit: https://console.neo4j.io/
   - Click "Sign Up" or "Log In"

2. **Create a New Database**
   - Click "New Instance"
   - Choose "AuraDB Free" (free tier)
   - Select a region close to you
   - Choose a database name (e.g., "avokat-ai")
   - Set a strong password (save this!)

3. **Get Connection Details**
   - After creation, you'll see connection details
   - Copy the **Connection URI** (looks like: `neo4j+s://xxxxxxxx.databases.neo4j.io`)
   - Note your **username** (usually "neo4j")
   - Note your **password** (the one you set)

## ⚙️ Step 2: Update Configuration

Update your `backend/app/core/config.py` with your Aura credentials:

```python
# Neo4j Aura Cloud Database settings
neo4j_uri: str = "neo4j+s://YOUR_ACTUAL_URI.databases.neo4j.io"  # Replace with your Aura URI
neo4j_username: str = "neo4j"  # Replace with your Aura username
neo4j_password: str = "YOUR_ACTUAL_PASSWORD"  # Replace with your Aura password
neo4j_database: str = "neo4j"
```

## 🔐 Step 3: Environment Variables (Recommended)

For security, use environment variables instead of hardcoding credentials:

1. **Create `.env` file** in your project root:
```bash
# Neo4j Aura Configuration
NEO4J_URI=neo4j+s://YOUR_ACTUAL_URI.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=YOUR_ACTUAL_PASSWORD
NEO4J_DATABASE=neo4j
```

2. **Update `config.py`** to use environment variables:
```python
# Neo4j Aura Cloud Database settings
neo4j_uri: str = "neo4j+s://xxxxxxxx.databases.neo4j.io"  # Default fallback
neo4j_username: str = "neo4j"  # Default fallback
neo4j_password: str = ""  # Default fallback
neo4j_database: str = "neo4j"
```

## 🧪 Step 4: Test Connection

Run the connection test:

```bash
# Activate virtual environment
backend\venv\Scripts\Activate.ps1

# Test Neo4j connection
python test_neo4j_connection.py
```

## 🌐 Step 5: Access Neo4j Browser

1. **Open Neo4j Browser**
   - Go to your Aura Console
   - Click "Open" next to your database
   - Or visit: `https://console.neo4j.io/`

2. **Run Test Queries**
   ```cypher
   // Test basic connectivity
   RETURN "Hello Neo4j Aura!" as message
   
   // Check if indexes were created
   SHOW INDEXES
   
   // View your data
   MATCH (n) RETURN n LIMIT 10
   ```

## 🔧 Step 6: Start Your Application

```bash
# Start the FastAPI server
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

## 📊 Step 7: Test API Endpoints

1. **Health Check**
   ```bash
   curl http://127.0.0.1:8000/neo4j/health
   ```

2. **Create Session**
   ```bash
   curl -X POST http://127.0.0.1:8000/sessions/ \
     -H "Content-Type: application/json" \
     -d '{"name": "Test Session"}'
   ```

3. **Create Entity**
   ```bash
   curl -X POST http://127.0.0.1:8000/neo4j/entities \
     -H "Content-Type: application/json" \
     -d '{
       "session_id": 1,
       "name": "Test Legal Entity",
       "entity_type": "PERSON",
       "description": "A test entity"
     }'
   ```

## 🚨 Troubleshooting

### Connection Issues
- **Check URI format**: Must start with `neo4j+s://`
- **Verify credentials**: Username/password are correct
- **Check network**: Ensure you can reach `*.databases.neo4j.io`

### SSL/TLS Issues
- **Aura requires SSL**: Always use `neo4j+s://` scheme
- **Firewall**: Ensure port 7687 is open for outbound connections

### Authentication Issues
- **Password**: Make sure password is correct and not expired
- **Username**: Usually "neo4j" but check your Aura console

## 📈 Aura Features

### Free Tier Limits
- **Database size**: Up to 50,000 nodes
- **Concurrent connections**: Up to 3
- **Backup retention**: 7 days

### Paid Tiers
- **Larger databases**: Up to 1M+ nodes
- **More connections**: Up to 100+
- **Longer backups**: Up to 30 days
- **Advanced features**: Graph Data Science, APOC plugins

## 🔒 Security Best Practices

1. **Use Environment Variables**: Never commit credentials to code
2. **Strong Passwords**: Use complex passwords for Aura
3. **IP Whitelisting**: Restrict access by IP if possible
4. **Regular Backups**: Aura handles this automatically
5. **Monitor Usage**: Check Aura console for usage patterns

## 📚 Additional Resources

- [Neo4j Aura Documentation](https://neo4j.com/docs/aura/)
- [Neo4j Python Driver](https://neo4j.com/docs/python-manual/current/)
- [Neo4j Cypher Manual](https://neo4j.com/docs/cypher-manual/current/)

## 🎉 Success!

Once you've completed these steps, your Avokat AI application will be connected to Neo4j Aura cloud, providing:

- ✅ **Scalable graph database** in the cloud
- ✅ **Automatic backups** and maintenance
- ✅ **High availability** and performance
- ✅ **Session isolation** for multi-tenant usage
- ✅ **Real-time graph analytics** capabilities

Your legal chatbot now has a powerful knowledge graph backend! 🚀
