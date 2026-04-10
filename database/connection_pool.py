"""
Database connection pool
⚠️ THIS FILE CONTAINS INTENTIONAL MEMORY LEAKS
"""

import time
from threading import Lock

class DatabaseConnection:
    """
    Mock database connection
    Simulates a real DB connection that holds resources
    """
    
    def __init__(self, connection_id):
        self.id = connection_id
        self.created_at = time.time()
        self.queries_executed = 0
        # Simulate connection holding memory (~5MB)
        self.buffer = bytearray(5 * 1024 * 1024)  # 5MB buffer
        self.is_closed = False
    
    def execute_query(self, query):
        """Execute a database query"""
        if self.is_closed:
            raise Exception("Connection is closed")
        self.queries_executed += 1
        # Simulate query execution
        time.sleep(0.01)
        return f"Query executed: {query}"
    
    def close(self):
        """Close the connection and free resources"""
        self.is_closed = True
        self.buffer = None  # Free the buffer
        print(f"🔌 Connection {self.id} closed")


class ConnectionPool:
    """
    Database connection pool
    
    ⚠️ MEMORY LEAK: Connections are created but never properly closed!
    The pool keeps growing and connections are never returned or cleaned up.
    """
    
    def __init__(self, max_size=10):
        self.max_size = max_size
        
        # 🐛 MEMORY LEAK: This list grows forever!
        # Connections are added but never removed
        self.connections = []
        
        # 🐛 MEMORY LEAK: "Available" connections are never actually reused
        self.available = []
        
        self.lock = Lock()
        self.connection_counter = 0
    
    def get_connection(self):
        """
        Get a database connection
        
        🐛 BUG: Always creates new connection instead of reusing!
        Should check self.available first, but doesn't.
        """
        with self.lock:
            # BUG: Should check if available connections exist
            # if self.available:
            #     return self.available.pop()
            
            # Instead, always create new connection (LEAK!)
            self.connection_counter += 1
            conn = DatabaseConnection(self.connection_counter)
            self.connections.append(conn)  # Never removed!
            
            print(f"🔌 Created connection {conn.id} (Total: {len(self.connections)})")
            
            # Simulate the leak getting worse over time
            if len(self.connections) % 10 == 0:
                print(f"⚠️  WARNING: {len(self.connections)} connections in pool!")
            
            return conn
    
    def release_connection(self, conn):
        """
        Release a connection back to the pool
        
        🐛 BUG: This method exists but is NEVER called!
        Connections are never returned to the pool.
        """
        with self.lock:
            if conn and not conn.is_closed:
                self.available.append(conn)
                print(f"🔌 Released connection {conn.id}")
    
    def close_all(self):
        """
        Close all connections
        
        🐛 BUG: This is never called during normal operation
        """
        with self.lock:
            for conn in self.connections:
                if not conn.is_closed:
                    conn.close()
            self.connections.clear()
            self.available.clear()
            print(f"🔌 Closed all connections")
    
    def get_stats(self):
        """Get connection pool statistics"""
        with self.lock:
            return {
                'total_connections': len(self.connections),
                'available_connections': len(self.available),
                'active_connections': len(self.connections) - len(self.available),
                'connections_created': self.connection_counter
            }
