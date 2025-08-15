# database.py
import sqlite3
import json
import uuid
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Any
from contextlib import contextmanager
import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("database")

# ================================
# Data Models

@dataclass
class Customer:
    customer_id: str
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    status: str = 'active'

@dataclass
class Package:
    package_id: Optional[int]
    package_name: str
    price: float
    description: Optional[str] = None
    is_active: bool = True

@dataclass
class PackageFeature:
    package_id: int
    feature_name: str
    feature_value: str

@dataclass
class CallSession:
    session_id: str
    customer_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: str = 'active'
    agent_mode: str = 'ai'
    resolution_status: Optional[str] = None
    notes: Optional[str] = None

@dataclass
class CallMessage:
    session_id: str
    role: str  # user, assistant, system
    content: str
    message_type: str = 'text'
    tool_call: Optional[str] = None
    tool_result: Optional[str] = None
    processing_time_ms: Optional[int] = None

# ================================
# Database Manager Class
# ================================

class CallCenterDatabase:
    def __init__(self, db_path: str = "call_center.db"):
        self.db_path = db_path
        self.init_database()
        logger.info(f"Database initialized: {db_path}")

    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()

    def init_database(self):
        """Initialize database with schema."""
        with self.get_connection() as conn:
            # Read and execute schema
            schema_sql = self._get_schema_sql()
            conn.executescript(schema_sql)
            
            # Insert initial data
            self._insert_initial_data(conn)
            logger.info("Database schema created successfully")

    def _get_schema_sql(self) -> str:
        """Returns the database schema SQL."""
        return '''
        -- Customers table
        CREATE TABLE IF NOT EXISTS customers (
            customer_id VARCHAR(10) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            phone VARCHAR(15),
            email VARCHAR(100),
            address TEXT,
            registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(20) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Packages table
        CREATE TABLE IF NOT EXISTS packages (
            package_id INTEGER PRIMARY KEY AUTOINCREMENT,
            package_name VARCHAR(50) UNIQUE NOT NULL,
            price DECIMAL(10,2) NOT NULL,
            description TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Package features
        CREATE TABLE IF NOT EXISTS package_features (
            feature_id INTEGER PRIMARY KEY AUTOINCREMENT,
            package_id INTEGER NOT NULL,
            feature_name VARCHAR(100) NOT NULL,
            feature_value VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (package_id) REFERENCES packages(package_id) ON DELETE CASCADE
        );

        -- Customer subscriptions
        CREATE TABLE IF NOT EXISTS customer_subscriptions (
            subscription_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id VARCHAR(10) NOT NULL,
            package_id INTEGER NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE,
            status VARCHAR(20) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE,
            FOREIGN KEY (package_id) REFERENCES packages(package_id)
        );

        -- Customer balances
        CREATE TABLE IF NOT EXISTS customer_balances (
            balance_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id VARCHAR(10) UNIQUE NOT NULL,
            current_balance DECIMAL(10,2) DEFAULT 0.00,
            credit_limit DECIMAL(10,2) DEFAULT 0.00,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
        );

        -- Bills
        CREATE TABLE IF NOT EXISTS bills (
            bill_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id VARCHAR(10) NOT NULL,
            bill_month VARCHAR(7) NOT NULL,
            amount DECIMAL(10,2) NOT NULL,
            due_date DATE NOT NULL,
            is_paid BOOLEAN DEFAULT FALSE,
            paid_date TIMESTAMP NULL,
            payment_method VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE,
            UNIQUE(customer_id, bill_month)
        );

        -- Usage statistics
        CREATE TABLE IF NOT EXISTS usage_stats (
            usage_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id VARCHAR(10) NOT NULL,
            usage_month VARCHAR(7) NOT NULL,
            calls_minutes INTEGER DEFAULT 0,
            data_mb INTEGER DEFAULT 0,
            sms_count INTEGER DEFAULT 0,
            extra_charges DECIMAL(10,2) DEFAULT 0.00,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE,
            UNIQUE(customer_id, usage_month)
        );

        -- Call sessions
        CREATE TABLE IF NOT EXISTS call_sessions (
            session_id VARCHAR(50) PRIMARY KEY,
            customer_id VARCHAR(10),
            start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            end_time TIMESTAMP,
            duration_seconds INTEGER,
            call_type VARCHAR(20) DEFAULT 'inbound',
            status VARCHAR(20) DEFAULT 'active',
            agent_mode VARCHAR(20) DEFAULT 'ai',
            customer_satisfaction INTEGER,
            resolution_status VARCHAR(30),
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        );

        -- Call messages
        CREATE TABLE IF NOT EXISTS call_messages (
            message_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id VARCHAR(50) NOT NULL,
            role VARCHAR(20) NOT NULL,
            content TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            message_type VARCHAR(20) DEFAULT 'text',
            tool_call VARCHAR(50),
            tool_result TEXT,
            processing_time_ms INTEGER,
            FOREIGN KEY (session_id) REFERENCES call_sessions(session_id) ON DELETE CASCADE
        );

        -- Tool usage logs
        CREATE TABLE IF NOT EXISTS tool_usage_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id VARCHAR(50) NOT NULL,
            tool_name VARCHAR(50) NOT NULL,
            parameters TEXT,
            result TEXT,
            execution_time_ms INTEGER,
            success BOOLEAN DEFAULT TRUE,
            error_message TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES call_sessions(session_id) ON DELETE CASCADE
        );

        -- Error logs
        CREATE TABLE IF NOT EXISTS error_logs (
            error_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id VARCHAR(50),
            error_type VARCHAR(50) NOT NULL,
            error_message TEXT NOT NULL,
            stack_trace TEXT,
            severity VARCHAR(20) DEFAULT 'medium',
            resolved BOOLEAN DEFAULT FALSE,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES call_sessions(session_id)
        );

        -- Indexes
        CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone);
        CREATE INDEX IF NOT EXISTS idx_customers_status ON customers(status);
        CREATE INDEX IF NOT EXISTS idx_bills_customer ON bills(customer_id);
        CREATE INDEX IF NOT EXISTS idx_bills_month ON bills(bill_month);
        CREATE INDEX IF NOT EXISTS idx_call_sessions_customer ON call_sessions(customer_id);
        CREATE INDEX IF NOT EXISTS idx_call_messages_session ON call_messages(session_id);
        CREATE INDEX IF NOT EXISTS idx_tool_usage_session ON tool_usage_logs(session_id);
        '''

    def _insert_initial_data(self, conn):
        """Insert initial test data."""
        
        # Insert customers
        customers_data = [
            ("1001", "Ali Veli", "5551234567", "ali.veli@email.com", "İstanbul"),
            ("1002", "Ayşe Demir", "5552345678", "ayse.demir@email.com", "Ankara"),
            ("1003", "Mehmet Can", "5553456789", "mehmet.can@email.com", "İzmir"),
            ("1004", "Elif Yılmaz", "5554567890", "elif.yilmaz@email.com", "Bursa"),
            ("1005", "Berke Kara", "5555678901", "berke.kara@email.com", "Antalya"),
        ]
        
        conn.executemany('''
            INSERT OR REPLACE INTO customers (customer_id, name, phone, email, address)
            VALUES (?, ?, ?, ?, ?)
        ''', customers_data)

        # Insert packages
        packages_data = [
            ("Bronze", 25.00, "Başlangıç paketi"),
            ("Silver", 50.00, "Orta seviye paket"),
            ("Gold", 100.00, "Gelişmiş paket"),
            ("Standart", 75.00, "Standart paket"),
            ("Premium", 150.00, "Premium paket"),
        ]
        
        conn.executemany('''
            INSERT OR REPLACE INTO packages (package_name, price, description)
            VALUES (?, ?, ?)
        ''', packages_data)

        # Get package IDs and insert features
        package_features = {
            "Bronze": ["50 DK Arama", "10 GB İnternet"],
            "Silver": ["200 DK Arama", "50 GB İnternet"],
            "Gold": ["Limitsiz Arama", "100 GB İnternet"],
            "Standart": ["100 DK Arama", "50 GB İnternet"],
            "Premium": ["Limitsiz Arama", "Limitsiz İnternet"],
        }

        for package_name, features in package_features.items():
            package_id = conn.execute(
                'SELECT package_id FROM packages WHERE package_name = ?', 
                (package_name,)
            ).fetchone()[0]
            
            for feature in features:
                conn.execute('''
                    INSERT OR REPLACE INTO package_features (package_id, feature_name, feature_value)
                    VALUES (?, ?, ?)
                ''', (package_id, feature.split()[1], feature.split()[0]))

        # Insert customer subscriptions
        subscription_data = [
            ("1001", "Premium", "2024-01-01"),
            ("1002", "Standart", "2024-02-01"),
            ("1003", "Gold", "2024-01-15"),
            ("1004", "Silver", "2024-03-01"),
            ("1005", "Bronze", "2024-02-15"),
        ]

        for customer_id, package_name, start_date in subscription_data:
            package_id = conn.execute(
                'SELECT package_id FROM packages WHERE package_name = ?', 
                (package_name,)
            ).fetchone()[0]
            
            conn.execute('''
                INSERT OR REPLACE INTO customer_subscriptions 
                (customer_id, package_id, start_date)
                VALUES (?, ?, ?)
            ''', (customer_id, package_id, start_date))

        # Insert customer balances
        balance_data = [
            ("1001", 243.45, 100.00),
            ("1002", 0.00, 50.00),
            ("1003", 1240.00, 200.00),
            ("1004", 5455.75, 75.00),
            ("1005", 5415.20, 25.00),
        ]
        
        conn.executemany('''
            INSERT OR REPLACE INTO customer_balances 
            (customer_id, current_balance, credit_limit)
            VALUES (?, ?, ?)
        ''', balance_data)

        # Insert bills
        bill_data = [
            ("1001", "2025-06", 145.00, "2025-07-01", False),
            ("1001", "2025-07", 150.00, "2025-08-01", False),
            ("1002", "2025-07", 75.00, "2025-08-01", True),
            ("1003", "2025-07", 100.00, "2025-08-01", False),
        ]
        
        conn.executemany('''
            INSERT OR REPLACE INTO bills 
            (customer_id, bill_month, amount, due_date, is_paid)
            VALUES (?, ?, ?, ?, ?)
        ''', bill_data)

        # Insert usage stats
        usage_data = [
            ("1001", "2025-07", 120, 20480, 30, 0.00),
            ("1002", "2025-07", 80, 15360, 25, 0.00),
            ("1003", "2025-07", 200, 30720, 50, 0.00),
        ]
        
        conn.executemany('''
            INSERT OR REPLACE INTO usage_stats 
            (customer_id, usage_month, calls_minutes, data_mb, sms_count, extra_charges)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', usage_data)

    # ================================
    # Customer Operations
    # ================================
    
    def get_customer_info(self, customer_id: str) -> Optional[Dict]:
        """Get customer information with current package and balance."""
        with self.get_connection() as conn:
            query = '''
                SELECT 
                    c.customer_id, c.name, c.phone, c.email,
                    p.package_name, cb.current_balance, cb.credit_limit,
                    julianday('now') - julianday(c.registration_date) as days_as_customer,
                    SUM(CASE WHEN b.is_paid = TRUE THEN b.amount ELSE 0 END) as total_paid
                FROM customers c
                LEFT JOIN customer_subscriptions cs ON c.customer_id = cs.customer_id 
                    AND cs.status = 'active'
                LEFT JOIN packages p ON cs.package_id = p.package_id
                LEFT JOIN customer_balances cb ON c.customer_id = cb.customer_id
                LEFT JOIN bills b ON c.customer_id = b.customer_id
                WHERE c.customer_id = ? AND c.status = 'active'
                GROUP BY c.customer_id
            '''
            
            result = conn.execute(query, (customer_id,)).fetchone()
            
            if result:
                data = dict(result)
                # Calculate monthly value
                months_as_customer = max(1, data['days_as_customer'] / 30)
                data['monthly_value'] = data['total_paid'] / months_as_customer if data['total_paid'] else 0
                return data
            
            return {}

    def get_system_health(self) -> Dict:
        """Get system health metrics."""
        with self.get_connection() as conn:
            # Recent activity metrics
            recent_calls = conn.execute('''
                SELECT COUNT(*) FROM call_sessions 
                WHERE start_time >= datetime('now', '-24 hours')
            ''').fetchone()[0]
            
            recent_errors = conn.execute('''
                SELECT COUNT(*) FROM error_logs 
                WHERE timestamp >= datetime('now', '-24 hours')
                AND severity IN ('high', 'critical')
            ''').fetchone()[0]
            
            active_sessions = conn.execute('''
                SELECT COUNT(*) FROM call_sessions 
                WHERE status = 'active'
            ''').fetchone()[0]
            
            avg_response_time = conn.execute('''
                SELECT AVG(processing_time_ms) FROM call_messages
                WHERE timestamp >= datetime('now', '-1 hour')
                AND processing_time_ms IS NOT NULL
            ''').fetchone()[0]
            
            # Tool success rate
            tool_success_rate = conn.execute('''
                SELECT 
                    (COUNT(CASE WHEN success = 1 THEN 1 END) * 100.0 / COUNT(*)) as success_rate
                FROM tool_usage_logs
                WHERE timestamp >= datetime('now', '-24 hours')
            ''').fetchone()[0]
            
            return {
                'recent_calls_24h': recent_calls,
                'recent_errors_24h': recent_errors,
                'active_sessions': active_sessions,
                'avg_response_time_ms': avg_response_time or 0,
                'tool_success_rate': tool_success_rate or 0,
                'status': 'healthy' if recent_errors < 10 else 'warning'
            }

    # ================================
    # Call Session Management
    # ================================
    
    def create_call_session(self, customer_id: str = None, agent_mode: str = 'ai') -> str:
        """Create a new call session."""
        session_id = str(uuid.uuid4())
        
        with self.get_connection() as conn:
            conn.execute('''
                INSERT INTO call_sessions 
                (session_id, customer_id, agent_mode, start_time)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (session_id, customer_id, agent_mode))
        
        logger.info(f"New call session created: {session_id}")
        return session_id

    def end_call_session(self, session_id: str, resolution_status: str = None, 
                        customer_satisfaction: int = None, notes: str = None) -> bool:
        """End a call session."""
        with self.get_connection() as conn:
            # Calculate duration
            session = conn.execute('''
                SELECT start_time FROM call_sessions WHERE session_id = ?
            ''', (session_id,)).fetchone()
            
            if not session:
                return False
            
            conn.execute('''
                UPDATE call_sessions 
                SET end_time = CURRENT_TIMESTAMP,
                    duration_seconds = (julianday(CURRENT_TIMESTAMP) - julianday(start_time)) * 86400,
                    status = 'completed',
                    resolution_status = ?,
                    customer_satisfaction = ?,
                    notes = ?
                WHERE session_id = ?
            ''', (resolution_status, customer_satisfaction, notes, session_id))
        
        logger.info(f"Call session ended: {session_id}")
        return True

    def add_call_message(self, session_id: str, role: str, content: str, 
                        message_type: str = 'text', tool_call: str = None, 
                        tool_result: str = None, processing_time_ms: int = None) -> int:
        """Add a message to call session."""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO call_messages 
                (session_id, role, content, message_type, tool_call, tool_result, processing_time_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (session_id, role, content, message_type, tool_call, tool_result, processing_time_ms))
            
            return cursor.lastrowid

    def log_tool_usage(self, session_id: str, tool_name: str, parameters: Dict, 
                      result: str, execution_time_ms: int, success: bool = True, 
                      error_message: str = None) -> int:
        """Log tool usage."""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO tool_usage_logs 
                (session_id, tool_name, parameters, result, execution_time_ms, success, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (session_id, tool_name, json.dumps(parameters), result, 
                  execution_time_ms, success, error_message))
            
            return cursor.lastrowid

    def log_error(self, session_id: str, error_type: str, error_message: str, 
                 stack_trace: str = None, severity: str = 'medium') -> int:
        """Log system errors."""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO error_logs 
                (session_id, error_type, error_message, stack_trace, severity)
                VALUES (?, ?, ?, ?, ?)
            ''', (session_id, error_type, error_message, stack_trace, severity))
            
            return cursor.lastrowid

    def get_call_session_history(self, session_id: str) -> Dict:
        """Get complete call session with messages."""
        with self.get_connection() as conn:
            # Get session info
            session_query = '''
                SELECT cs.*, c.name as customer_name
                FROM call_sessions cs
                LEFT JOIN customers c ON cs.customer_id = c.customer_id
                WHERE cs.session_id = ?
            '''
            session = conn.execute(session_query, (session_id,)).fetchone()
            
            if not session:
                return None
            
            # Get messages
            messages_query = '''
                SELECT role, content, timestamp, message_type, tool_call, tool_result
                FROM call_messages
                WHERE session_id = ?
                ORDER BY timestamp
            '''
            messages = conn.execute(messages_query, (session_id,)).fetchall()
            
            # Get tool usage
            tools_query = '''
                SELECT tool_name, parameters, result, execution_time_ms, success
                FROM tool_usage_logs
                WHERE session_id = ?
                ORDER BY timestamp
            '''
            tools = conn.execute(tools_query, (session_id,)).fetchall()
            
            return {
                'session': dict(session),
                'messages': [dict(msg) for msg in messages],
                'tool_usage': [dict(tool) for tool in tools]
            }

    # ================================
    # Analytics and Reporting
    # ================================
    
    def get_daily_metrics(self, date_str: str = None) -> Dict:
        """Get daily performance metrics."""
        if not date_str:
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        with self.get_connection() as conn:
            query = '''
                SELECT 
                    COUNT(*) as total_calls,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_calls,
                    COUNT(CASE WHEN resolution_status = 'resolved' THEN 1 END) as resolved_calls,
                    AVG(duration_seconds) as avg_duration,
                    AVG(customer_satisfaction) as avg_satisfaction
                FROM call_sessions
                WHERE DATE(start_time) = ?
            '''
            
            result = conn.execute(query, (date_str,)).fetchone()
            return dict(result) if result else {}

    def get_tool_usage_stats(self, days: int = 30) -> List[Dict]:
        """Get tool usage statistics."""
        with self.get_connection() as conn:
            query = '''
                SELECT 
                    tool_name,
                    COUNT(*) as usage_count,
                    AVG(execution_time_ms) as avg_execution_time,
                    (COUNT(CASE WHEN success = 1 THEN 1 END) * 100.0 / COUNT(*)) as success_rate
                FROM tool_usage_logs 
                WHERE timestamp >= datetime('now', '-{} days')
                GROUP BY tool_name
                ORDER BY usage_count DESC
            '''.format(days)
            
            result = conn.execute(query).fetchall()
            return [dict(row) for row in result]

    def get_customer_call_history(self, customer_id: str, limit: int = 10) -> List[Dict]:
        """Get customer's recent call history."""
        with self.get_connection() as conn:
            query = '''
                SELECT 
                    session_id, start_time, end_time, duration_seconds,
                    status, resolution_status, customer_satisfaction
                FROM call_sessions
                WHERE customer_id = ?
                ORDER BY start_time DESC
                LIMIT ?
            '''
            
            result = conn.execute(query, (customer_id, limit)).fetchall()
            return [dict(row) for row in result]

    # ================================
    # Maintenance and Utilities
    # ================================
    
    def cleanup_old_logs(self, days_to_keep: int = 90) -> int:
        """Clean up old call logs and messages."""
        with self.get_connection() as conn:
            # Get sessions to delete
            old_sessions = conn.execute('''
                SELECT session_id FROM call_sessions
                WHERE start_time < datetime('now', '-{} days')
            '''.format(days_to_keep)).fetchall()
            
            deleted_count = 0
            for session in old_sessions:
                session_id = session[0]
                
                # Delete related records
                conn.execute('DELETE FROM call_messages WHERE session_id = ?', (session_id,))
                conn.execute('DELETE FROM tool_usage_logs WHERE session_id = ?', (session_id,))
                conn.execute('DELETE FROM error_logs WHERE session_id = ?', (session_id,))
                conn.execute('DELETE FROM call_sessions WHERE session_id = ?', (session_id,))
                
                deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} old call sessions")
            return deleted_count

    def backup_database(self, backup_path: str = None) -> str:
        """Create database backup."""
        if not backup_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = f"call_center_backup_{timestamp}.db"
        
        with self.get_connection() as conn:
            backup_conn = sqlite3.connect(backup_path)
            conn.backup(backup_conn)
            backup_conn.close()
        
        logger.info(f"Database backed up to: {backup_path}")
        return backup_path

    def get_database_stats(self) -> Dict:
        """Get database statistics."""
        with self.get_connection() as conn:
            stats = {}
            
            # Table row counts
            tables = ['customers', 'packages', 'call_sessions', 'call_messages', 
                     'tool_usage_logs', 'bills', 'usage_stats', 'error_logs']
            
            for table in tables:
                count = conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
                stats[f'{table}_count'] = count
            
            # Database file size
            stats['db_size_mb'] = Path(self.db_path).stat().st_size / (1024 * 1024)
            
            # Recent activity
            recent_calls = conn.execute('''
                SELECT COUNT(*) FROM call_sessions 
                WHERE start_time >= datetime('now', '-24 hours')
            ''').fetchone()[0]
            stats['calls_last_24h'] = recent_calls
            
            return stats


    def get_available_packages(self) -> List[Dict]:
        """Get all available packages with features."""
        with self.get_connection() as conn:
            packages_query = '''
                SELECT package_id, package_name, price, description
                FROM packages
                WHERE is_active = TRUE
                ORDER BY price
            '''
            
            packages = conn.execute(packages_query).fetchall()
            result = []
            
            for package in packages:
                features_query = '''
                    SELECT feature_name, feature_value
                    FROM package_features
                    WHERE package_id = ?
                '''
                features = conn.execute(features_query, (package['package_id'],)).fetchall()
                
                package_dict = dict(package)
                package_dict['features'] = [f"{f['feature_value']} {f['feature_name']}" for f in features]
                result.append(package_dict)
            
            return result

    def change_customer_package(self, customer_id: str, new_package_name: str) -> bool:
        """Change customer's package."""
        with self.get_connection() as conn:
            # Get new package ID
            package_result = conn.execute(
                'SELECT package_id FROM packages WHERE package_name = ? AND is_active = TRUE',
                (new_package_name,)
            ).fetchone()
            
            if not package_result:
                return False
            
            package_id = package_result[0]
            
            # End current subscription
            conn.execute('''
                UPDATE customer_subscriptions 
                SET status = 'cancelled', end_date = DATE('now')
                WHERE customer_id = ? AND status = 'active'
            ''', (customer_id,))
            
            # Create new subscription
            conn.execute('''
                INSERT INTO customer_subscriptions 
                (customer_id, package_id, start_date)
                VALUES (?, ?, DATE('now'))
            ''', (customer_id, package_id))
            
            return True

    def get_customer_bills(self, customer_id: str) -> List[Dict]:
        """Get customer billing information."""
        with self.get_connection() as conn:
            query = '''
                SELECT bill_month, amount, due_date, is_paid, paid_date, payment_method
                FROM bills
                WHERE customer_id = ?
                ORDER BY bill_month DESC
            '''
            
            result = conn.execute(query, (customer_id,)).fetchall()
            return [dict(bill) for bill in result]

    def pay_bill(self, customer_id: str, bill_month: str, amount: float, payment_method: str = 'online') -> bool:
        """Process bill payment."""
        with self.get_connection() as conn:
            # Check if bill exists and unpaid
            bill = conn.execute('''
                SELECT bill_id, amount FROM bills
                WHERE customer_id = ? AND bill_month = ? AND is_paid = FALSE
            ''', (customer_id, bill_month)).fetchone()
            
            if not bill:
                return False
            
            if abs(bill['amount'] - amount) > 0.01:
                return False
            
            # Update bill as paid
            conn.execute('''
                UPDATE bills
                SET is_paid = TRUE, paid_date = CURRENT_TIMESTAMP, payment_method = ?
                WHERE customer_id = ? AND bill_month = ?
            ''', (payment_method, customer_id, bill_month))
            
            # Update customer balance
            conn.execute('''
                UPDATE customer_balances
                SET current_balance = current_balance - ?, last_updated = CURRENT_TIMESTAMP
                WHERE customer_id = ?
            ''', (amount, customer_id))
            
            return True

    def get_customer_usage_stats(self, customer_id: str, month: str = None) -> Optional[Dict]:
        """Get customer usage statistics."""
        with self.get_connection() as conn:
            if month:
                query = '''
                    SELECT calls_minutes, data_mb, sms_count, extra_charges
                    FROM usage_stats
                    WHERE customer_id = ? AND usage_month = ?
                '''
                result = conn.execute(query, (customer_id, month)).fetchone()
            else:
                query = '''
                    SELECT calls_minutes, data_mb, sms_count, extra_charges
                    FROM usage_stats
                    WHERE customer_id = ?
                    ORDER BY usage_month DESC
                    LIMIT 1
                '''
                result = conn.execute(query, (customer_id,)).fetchone()
            
            return dict(result) if result else None

    def create_customer(self, customer_id: str, name: str, phone: str = None, 
                       email: str = None, address: str = None) -> bool:
        """Create a new customer."""
        with self.get_connection() as conn:
            try:
                conn.execute('''
                    INSERT INTO customers (customer_id, name, phone, email, address)
                    VALUES (?, ?, ?, ?, ?)
                ''', (customer_id, name, phone, email, address))
                
                # Create balance record
                conn.execute('''
                    INSERT INTO customer_balances (customer_id, current_balance, credit_limit)
                    VALUES (?, 0.00, 0.00)
                ''', (customer_id,))
                
                logger.info(f"New customer created: {customer_id}")
                return True
            except Exception as e:
                logger.error(f"Error creating customer {customer_id}: {e}")
                return False

    def update_customer_info(self, customer_id: str, **kwargs) -> bool:
        """Update customer information."""
        with self.get_connection() as conn:
            # Build dynamic update query
            valid_fields = ['name', 'phone', 'email', 'address', 'status']
            updates = []
            values = []
            
            for field, value in kwargs.items():
                if field in valid_fields and value is not None:
                    updates.append(f"{field} = ?")
                    values.append(value)
            
            if not updates:
                return False
            
            # Add updated_at timestamp
            updates.append("updated_at = CURRENT_TIMESTAMP")
            values.append(customer_id)
            
            query = f"UPDATE customers SET {', '.join(updates)} WHERE customer_id = ?"
            
            try:
                result = conn.execute(query, values)
                return result.rowcount > 0
            except Exception as e:
                logger.error(f"Error updating customer {customer_id}: {e}")
                return False

    def update_customer_balance(self, customer_id: str, amount: float, operation: str = 'add') -> bool:
        """Update customer balance (add or subtract)."""
        with self.get_connection() as conn:
            try:
                if operation == 'add':
                    conn.execute('''
                        UPDATE customer_balances
                        SET current_balance = current_balance + ?, last_updated = CURRENT_TIMESTAMP
                        WHERE customer_id = ?
                    ''', (amount, customer_id))
                elif operation == 'subtract':
                    conn.execute('''
                        UPDATE customer_balances
                        SET current_balance = current_balance - ?, last_updated = CURRENT_TIMESTAMP
                        WHERE customer_id = ?
                    ''', (amount, customer_id))
                elif operation == 'set':
                    conn.execute('''
                        UPDATE customer_balances
                        SET current_balance = ?, last_updated = CURRENT_TIMESTAMP
                        WHERE customer_id = ?
                    ''', (amount, customer_id))
                else:
                    return False
                
                logger.info(f"Balance updated for {customer_id}: {operation} {amount}")
                return True
            except Exception as e:
                logger.error(f"Error updating balance for {customer_id}: {e}")
                return False

    def create_bill(self, customer_id: str, bill_month: str, amount: float, due_date: str) -> bool:
        """Create a new bill for customer."""
        with self.get_connection() as conn:
            try:
                conn.execute('''
                    INSERT INTO bills (customer_id, bill_month, amount, due_date)
                    VALUES (?, ?, ?, ?)
                ''', (customer_id, bill_month, amount, due_date))
                
                logger.info(f"New bill created for {customer_id}: {bill_month} - {amount}")
                return True
            except Exception as e:
                logger.error(f"Error creating bill for {customer_id}: {e}")
                return False

    def update_usage_stats(self, customer_id: str, usage_month: str, 
                          calls_minutes: int = None, data_mb: int = None, 
                          sms_count: int = None, extra_charges: float = None) -> bool:
        """Update or create usage statistics for a customer."""
        with self.get_connection() as conn:
            try:
                # Check if record exists
                existing = conn.execute('''
                    SELECT usage_id FROM usage_stats
                    WHERE customer_id = ? AND usage_month = ?
                ''', (customer_id, usage_month)).fetchone()
                
                if existing:
                    # Update existing record
                    updates = []
                    values = []
                    
                    if calls_minutes is not None:
                        updates.append("calls_minutes = ?")
                        values.append(calls_minutes)
                    if data_mb is not None:
                        updates.append("data_mb = ?")
                        values.append(data_mb)
                    if sms_count is not None:
                        updates.append("sms_count = ?")
                        values.append(sms_count)
                    if extra_charges is not None:
                        updates.append("extra_charges = ?")
                        values.append(extra_charges)
                    
                    if updates:
                        updates.append("updated_at = CURRENT_TIMESTAMP")
                        values.extend([customer_id, usage_month])
                        
                        query = f"UPDATE usage_stats SET {', '.join(updates)} WHERE customer_id = ? AND usage_month = ?"
                        conn.execute(query, values)
                else:
                    # Create new record
                    conn.execute('''
                        INSERT INTO usage_stats 
                        (customer_id, usage_month, calls_minutes, data_mb, sms_count, extra_charges)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (customer_id, usage_month, 
                         calls_minutes or 0, data_mb or 0, sms_count or 0, extra_charges or 0.0))
                
                logger.info(f"Usage stats updated for {customer_id}: {usage_month}")
                return True
            except Exception as e:
                logger.error(f"Error updating usage stats for {customer_id}: {e}")
                return False

    def search_customers(self, query: str, limit: int = 10) -> List[Dict]:
        """Search customers by name, phone, or email."""
        with self.get_connection() as conn:
            search_query = '''
                SELECT customer_id, name, phone, email, status
                FROM customers
                WHERE (name LIKE ? OR phone LIKE ? OR email LIKE ?)
                AND status = 'active'
                ORDER BY name
                LIMIT ?
            '''
            
            search_pattern = f"%{query}%"
            results = conn.execute(search_query, 
                                 (search_pattern, search_pattern, search_pattern, limit)).fetchall()
            
            return [dict(customer) for customer in results]

    def get_unpaid_bills(self, customer_id: str = None) -> List[Dict]:
        """Get unpaid bills for a customer or all customers."""
        with self.get_connection() as conn:
            if customer_id:
                query = '''
                    SELECT b.*, c.name as customer_name
                    FROM bills b
                    JOIN customers c ON b.customer_id = c.customer_id
                    WHERE b.customer_id = ? AND b.is_paid = FALSE
                    ORDER BY b.due_date
                '''
                results = conn.execute(query, (customer_id,)).fetchall()
            else:
                query = '''
                    SELECT b.*, c.name as customer_name
                    FROM bills b
                    JOIN customers c ON b.customer_id = c.customer_id
                    WHERE b.is_paid = FALSE
                    ORDER BY b.due_date
                '''
                results = conn.execute(query).fetchall()
            
            return [dict(bill) for bill in results]

    def get_overdue_bills(self, days_overdue: int = 0) -> List[Dict]:
        """Get overdue bills."""
        with self.get_connection() as conn:
            query = '''
                SELECT b.*, c.name as customer_name,
                       julianday('now') - julianday(b.due_date) as days_overdue
                FROM bills b
                JOIN customers c ON b.customer_id = c.customer_id
                WHERE b.is_paid = FALSE 
                AND julianday('now') - julianday(b.due_date) > ?
                ORDER BY days_overdue DESC
            '''
            
            results = conn.execute(query, (days_overdue,)).fetchall()
            return [dict(bill) for bill in results]

    def get_monthly_revenue(self, year_month: str = None) -> Dict:
        """Get monthly revenue statistics."""
        with self.get_connection() as conn:
            if not year_month:
                year_month = datetime.now().strftime('%Y-%m')
            
            query = '''
                SELECT 
                    COUNT(*) as total_bills,
                    SUM(amount) as total_amount,
                    COUNT(CASE WHEN is_paid = TRUE THEN 1 END) as paid_bills,
                    SUM(CASE WHEN is_paid = TRUE THEN amount ELSE 0 END) as collected_amount,
                    COUNT(CASE WHEN is_paid = FALSE THEN 1 END) as unpaid_bills,
                    SUM(CASE WHEN is_paid = FALSE THEN amount ELSE 0 END) as outstanding_amount
                FROM bills
                WHERE bill_month = ?
            '''
            
            result = conn.execute(query, (year_month,)).fetchone()
            return dict(result) if result else {}

    def get_package_statistics(self) -> List[Dict]:
        """Get package subscription statistics."""
        with self.get_connection() as conn:
            query = '''
                SELECT 
                    p.package_name,
                    p.price,
                    COUNT(cs.subscription_id) as active_subscriptions,
                    SUM(p.price) as monthly_revenue
                FROM packages p
                LEFT JOIN customer_subscriptions cs ON p.package_id = cs.package_id 
                    AND cs.status = 'active'
                WHERE p.is_active = TRUE
                GROUP BY p.package_id, p.package_name, p.price
                ORDER BY monthly_revenue DESC
            '''
            
            results = conn.execute(query).fetchall()
            return [dict(stat) for stat in results]

    def get_customer_lifetime_value(self, customer_id: str) -> Dict:
        """Calculate customer lifetime value."""
        with self.get_connection() as conn:
            query = '''
                SELECT 
                    c.registration_date,
                    COUNT(b.bill_id) as total_bills,
                    SUM(CASE WHEN b.is_paid = TRUE THEN b.amount ELSE 0 END) as total_paid,
                    AVG(CASE WHEN b.is_paid = TRUE THEN b.amount ELSE NULL END) as avg_bill_amount,
                    julianday('now') - julianday(c.registration_date) as days_as_customer
                FROM customers c
                LEFT JOIN bills b ON c.customer_id = b.customer_id
                WHERE c.customer_id = ?
                GROUP BY c.customer_id
            '''
            
            result = conn.execute(query, (customer_id,)).fetchone()
            
            if result:
                data = dict(result)
                # Calculate monthly value
                months_as_customer = max(1, data['days_as_customer'] / 30)
                data['monthly_value'] = data['total_paid'] / months_as_customer if data['total_paid'] else 0
                return data
            
            return {}
    def get_system_health(self) -> Dict:
        """Get system health metrics."""
        with self.get_connection() as conn:
            # Recent activity metrics
            recent_calls = conn.execute('''
                SELECT COUNT(*) FROM call_sessions 
                WHERE start_time >= datetime('now', '-24 hours')
            ''').fetchone()[0]
            
            recent_errors = conn.execute('''
                SELECT COUNT(*) FROM error_logs 
                WHERE timestamp >= datetime('now', '-24 hours')
                AND severity IN ('high', 'critical')
            ''').fetchone()[0]
            
            active_sessions = conn.execute('''
                SELECT COUNT(*) FROM call_sessions 
                WHERE status = 'active'
            ''').fetchone()[0]
            
            avg_response_time = conn.execute('''
                SELECT AVG(processing_time_ms) FROM call_messages
                WHERE timestamp >= datetime('now', '-1 hour')
                AND processing_time_ms IS NOT NULL
            ''').fetchone()[0]
            
            # Tool success rate
            tool_success_rate = conn.execute('''
                SELECT 
                    (COUNT(CASE WHEN success = 1 THEN 1 END) * 100.0 / COUNT(*)) as success_rate
                FROM tool_usage_logs
                WHERE timestamp >= datetime('now', '-24 hours')
            ''').fetchone()[0]
            
            return {
                'recent_calls_24h': recent_calls,
                'recent_errors_24h': recent_errors,
                'active_sessions': active_sessions,
                'avg_response_time_ms': avg_response_time or 0,
                'tool_success_rate': tool_success_rate or 0,
                'status': 'healthy' if recent_errors < 10 else 'warning'
            }
    
# ================================
# Session Manager for Agent Integration
# ================================

class CallSessionManager:
    """High-level session manager for agent integration."""
    
    def __init__(self, database: CallCenterDatabase):
        self.db = database
        self.current_session_id = None
        self.start_time = None

    def start_session(self, customer_id: str = None) -> str:
        """Start a new call session."""
        self.current_session_id = self.db.create_call_session(customer_id, 'ai')
        self.start_time = datetime.now()
        return self.current_session_id

    def log_message(self, role: str, content: str, tool_call: str = None, 
                   tool_result: str = None, processing_time_ms: int = None):
        """Log a message in current session."""
        if self.current_session_id:
            self.db.add_call_message(
                self.current_session_id, role, content, 'text',
                tool_call, tool_result, processing_time_ms
            )

    def log_tool_usage(self, tool_name: str, parameters: Dict, result: str, 
                      execution_time_ms: int, success: bool = True):
        """Log tool usage in current session."""
        if self.current_session_id:
            self.db.log_tool_usage(
                self.current_session_id, tool_name, parameters, result,
                execution_time_ms, success
            )

    def end_session(self, resolution_status: str = 'resolved', 
                   customer_satisfaction: int = None, notes: str = None):
        """End current session."""
        if self.current_session_id:
            self.db.end_call_session(
                self.current_session_id, resolution_status, 
                customer_satisfaction, notes
            )
            
            session_duration = (datetime.now() - self.start_time).total_seconds()
            logger.info(f"Session ended: {self.current_session_id}, Duration: {session_duration:.2f}s")
            
            self.current_session_id = None
            self.start_time = None

    def get_session_id(self) -> Optional[str]:
        """Get current session ID."""
        return self.current_session_id


if __name__ == "__main__":
    # Test the database functionality
    db = CallCenterDatabase("call_center.db")