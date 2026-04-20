"""
Database connection pool
✅ FIXED: Proper connection pooling with reuse, max size enforcement, and cleanup
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

    ✅ FIXED:
    - Reuses available connections instead of always creating new ones
    - Enforces max_size limit to prevent unbounded pool growth
    - Connections are properly released back to the pool after use
    - close_all() is called on shutdown to free all resources
    """
    
    def __init__(self, max_size=10):
        self.max_size = max_size
        self.connections = []   # All connections (active + available)
        self.available = []     # ✅ FIX: Available connections are now actually reused
        self.lock = Lock()
        self.connection_counter = 0
    
    def get_connection(self):
        """
        Get a database connection.

        ✅ FIX: Reuses available connections from the pool. Only creates a new
        connection when none are available and the pool has not reached max_size.
        Raises RuntimeError if the pool is exhausted.
        """
        with self.lock:
            # ✅ FIX: Reuse an available connection if one exists
            if self.available:
                conn = self.available.pop()
                print(f"🔌 Reusing connection {conn.id} (Available: {len(self.available)})")
                return conn

            # ✅ FIX: Enforce max pool size
            if len(self.connections) >= self.max_size:
                raise RuntimeError(
                    f"Connection pool exhausted (max_size={self.max_size}). "
                    "All connections are in use."
                )

            # Create a new connection only when necessary
            self.connection_counter += 1
            conn = DatabaseConnection(self.connection_counter)
            self.connections.append(conn)
            print(f"🔌 Created connection {conn.id} (Total: {len(self.connections)})")
            return conn
    
    def release_connection(self, conn):
        """
        Release a connection back to the pool.

        ✅ FIX: This method is now called by callers (e.g. BackgroundProcessor)
        after every use so connections are properly recycled.
        """
        with self.lock:
            if conn and not conn.is_closed:
                self.available.append(conn)
                print(f"🔌 Released connection {conn.id} (Available: {len(self.available)})")
    
    def close_all(self):
        """
        Close all connections and free their resources.

        ✅ FIX: Called during BackgroundProcessor.stop() to ensure all
        connections are properly cleaned up on shutdown.
        """
        with self.lock:
            for conn in self.connections:
                if not conn.is_closed:
                    conn.close()
            self.connections.clear()
            self.available.clear()
            print("🔌 Closed all connections")
    
    def get_stats(self):
        """Get connection pool statistics"""
        with self.lock:
            return {
                'total_connections': len(self.connections),
                'available_connections': len(self.available),
                'active_connections': len(self.connections) - len(self.available),
                'connections_created': self.connection_counter
            }
