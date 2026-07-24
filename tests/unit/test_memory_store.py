import os
from src.context.memory.memory_store import EpisodicMemoryStore

def test_episodic_memory_store_basic():
    db_path = ".agent/test_memory_store.db"
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except OSError:
            pass

    store = EpisodicMemoryStore(db_path=db_path)

    # Store entries
    success1 = store.store("session_1", "orchestrator", "Recherche sur le protocole MCP et son architecture")
    success2 = store.store("session_2", "researcher", "Configuration de la clé API Gemini dans .env")
    assert success1 is True
    assert success2 is True

    # Recall
    results = store.recall("protocole MCP")
    assert len(results) >= 1
    assert "MCP" in results[0].content

    # Clean up
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except OSError:
            pass
