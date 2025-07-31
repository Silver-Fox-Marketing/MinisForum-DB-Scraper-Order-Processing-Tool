"""
Database connection manager with connection pooling and error handling
"""
import psycopg2
from psycopg2 import pool, sql
from psycopg2.extras import RealDictCursor, execute_batch
import logging
from contextlib import contextmanager
from typing import Optional, List, Dict, Any
import time
from database_config import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseConnectionError(Exception):
    """Custom exception for database connection errors"""
    pass

class DatabaseManager:
    """Manages database connections with pooling and utilities"""
    
    def __init__(self, db_config=None):
        self.config = db_config or config
        self._connection_pool = None
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize the connection pool"""
        try:
            self._connection_pool = psycopg2.pool.ThreadedConnectionPool(
                self.config.min_connections,
                self.config.max_connections,
                **self.config.connection_dict
            )
            logger.info("Database connection pool initialized successfully")
        except psycopg2.Error as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            raise DatabaseConnectionError(f"Could not create connection pool: {e}")
    
    @contextmanager
    def get_connection(self, cursor_factory=None):
        """Get a connection from the pool"""
        if self._connection_pool is None:
            raise DatabaseConnectionError("Database connection pool not initialized")
            
        connection = None
        try:
            connection = self._connection_pool.getconn()
            if cursor_factory:
                connection.cursor_factory = cursor_factory
            yield connection
            connection.commit()
        except psycopg2.Error as e:
            if connection:
                connection.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if connection:
                self._connection_pool.putconn(connection)
    
    @contextmanager
    def get_cursor(self, cursor_factory=RealDictCursor):
        """Get a cursor with automatic connection management"""
        with self.get_connection(cursor_factory) as conn:
            cursor = conn.cursor()
            try:
                yield cursor
            finally:
                cursor.close()
    
    def execute_query(self, query: str, params: tuple = None, fetch: str = 'all') -> List[Dict]:
        """Execute a query and return results"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            
            # Check if this is a query that returns results
            if cursor.description is None:
                # This was an INSERT/UPDATE/DELETE or similar, return empty list
                return []
            
            if fetch == 'all':
                return cursor.fetchall()
            elif fetch == 'one':
                return cursor.fetchone()
            elif fetch == 'many':
                return cursor.fetchmany()
            else:
                return []
    
    def execute_non_query(self, query: str, params: tuple = None) -> int:
        """Execute a non-returning query (INSERT/UPDATE/DELETE) and return row count"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.rowcount
    
    def execute_batch_insert(self, table: str, columns: List[str], data: List[tuple], 
                           page_size: int = 1000, max_retries: int = 3) -> int:
        """Execute batch insert with optimal performance and retry logic"""
        if not data:
            return 0
        
        # Build the INSERT query
        cols = sql.SQL(', ').join(map(sql.Identifier, columns))
        placeholders = sql.SQL(', ').join(sql.Placeholder() * len(columns))
        query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
            sql.Identifier(table),
            cols,
            placeholders
        )
        
        rows_inserted = 0
        last_error = None
        
        for attempt in range(max_retries):
            try:
                with self.get_cursor() as cursor:
                    execute_batch(cursor, query, data, page_size=page_size)
                    rows_inserted = cursor.rowcount
                    logger.info(f"Inserted {rows_inserted} rows into {table}")
                    return rows_inserted
                    
            except psycopg2.OperationalError as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"Batch insert attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                    # Reinitialize connection pool if needed
                    if "connection" in str(e).lower():
                        self._initialize_pool()
                else:
                    logger.error(f"Batch insert failed after {max_retries} attempts: {e}")
                    raise
                    
            except psycopg2.Error as e:
                # Don't retry for data errors (constraint violations, etc.)
                logger.error(f"Batch insert failed with data error: {e}")
                raise
        
        return rows_inserted
    
    def upsert_data(self, table: str, columns: List[str], data: List[tuple],
                    conflict_columns: List[str], update_columns: List[str] = None) -> int:
        """Perform UPSERT operation (INSERT ... ON CONFLICT)"""
        if not data:
            return 0
        
        update_columns = update_columns or columns
        
        # Build the query
        cols = sql.SQL(', ').join(map(sql.Identifier, columns))
        placeholders = sql.SQL(', ').join(sql.Placeholder() * len(columns))
        conflict_cols = sql.SQL(', ').join(map(sql.Identifier, conflict_columns))
        
        # Build UPDATE SET clause
        update_set = sql.SQL(', ').join([
            sql.SQL("{} = EXCLUDED.{}").format(sql.Identifier(col), sql.Identifier(col))
            for col in update_columns
        ])
        
        query = sql.SQL("""
            INSERT INTO {} ({}) VALUES ({})
            ON CONFLICT ({}) DO UPDATE SET {}
        """).format(
            sql.Identifier(table),
            cols,
            placeholders,
            conflict_cols,
            update_set
        )
        
        rows_affected = 0
        with self.get_cursor() as cursor:
            try:
                execute_batch(cursor, query, data)
                rows_affected = cursor.rowcount
                logger.info(f"Upserted {rows_affected} rows in {table}")
            except psycopg2.Error as e:
                logger.error(f"Upsert failed: {e}")
                raise
        
        return rows_affected
    
    def test_connection(self) -> bool:
        """Test if database connection is working"""
        try:
            result = self.execute_query("SELECT 1", fetch='one')
            return result is not None
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def get_table_stats(self) -> List[Dict]:
        """Get statistics for all tables"""
        query = """
            SELECT 
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                n_live_tup as row_count
            FROM pg_stat_user_tables
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
        """
        return self.execute_query(query)
    
    def vacuum_analyze(self, table: str = None):
        """Run VACUUM ANALYZE on table or entire database"""
        with self.get_connection() as conn:
            # Need to set autocommit for VACUUM
            old_isolation_level = conn.isolation_level
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            
            try:
                with conn.cursor() as cursor:
                    if table:
                        cursor.execute(f"VACUUM ANALYZE {table}")
                        logger.info(f"VACUUM ANALYZE completed for {table}")
                    else:
                        cursor.execute("VACUUM ANALYZE")
                        logger.info("VACUUM ANALYZE completed for entire database")
            finally:
                conn.set_isolation_level(old_isolation_level)
    
    def close(self):
        """Close all connections in the pool"""
        if self._connection_pool:
            self._connection_pool.closeall()
            logger.info("Database connection pool closed")

# Create a singleton instance
db_manager = DatabaseManager()

# Utility functions for common operations
def test_database_connection():
    """Test the database connection"""
    if db_manager.test_connection():
        print("✓ Database connection successful")
        
        # Get table stats
        stats = db_manager.get_table_stats()
        if stats:
            print("\nDatabase tables:")
            for stat in stats:
                print(f"  - {stat['tablename']}: {stat['size']} ({stat['row_count']} rows)")
        else:
            print("\nNo tables found. Run the SQL scripts to create tables.")
    else:
        print("✗ Database connection failed")
        print("Please check your PostgreSQL installation and credentials")

if __name__ == "__main__":
    test_database_connection()