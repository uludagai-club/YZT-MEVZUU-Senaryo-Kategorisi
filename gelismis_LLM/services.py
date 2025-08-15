# services.py
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from database import CallCenterDatabase

logger = logging.getLogger("services")

class CustomerService:
    def __init__(self, db: CallCenterDatabase):
        self.db = db
    
    def get_customer_info(self, customer_id: str) -> Optional[Dict]:
        """Müşteri bilgilerini getirir."""
        return self.db.get_customer_info(customer_id)
    
    def create_customer(self, customer_id: str, name: str, **kwargs) -> bool:
        """Yeni müşteri oluşturur."""
        return self.db.create_customer(customer_id, name, **kwargs)
    
    def update_customer_info(self, customer_id: str, **kwargs) -> bool:
        """Müşteri bilgilerini günceller."""
        return self.db.update_customer_info(customer_id, **kwargs)
    
    def get_customer_call_history(self, customer_id: str, limit: int = 10) -> List[Dict]:
        """Müşteri görüşme geçmişi."""
        return self.db.get_customer_call_history(customer_id, limit)

class PackageService:
    def __init__(self, db: CallCenterDatabase):
        self.db = db
    
    def get_available_packages(self) -> List[Dict]:
        """Mevcut paketleri getirir."""
        return self.db.get_available_packages()
    
    def change_customer_package(self, customer_id: str, new_package_name: str) -> bool:
        """Müşteri paketini değiştirir."""
        return self.db.change_customer_package(customer_id, new_package_name)

class BillingService:
    def __init__(self, db: CallCenterDatabase):
        self.db = db
    
    def get_customer_bills(self, customer_id: str) -> List[Dict]:
        """Müşteri faturalarını getirir."""
        return self.db.get_customer_bills(customer_id)
    
    def pay_bill(self, customer_id: str, bill_month: str, amount: float, payment_method: str = 'api') -> bool:
        """Fatura ödemesi yapar."""
        return self.db.pay_bill(customer_id, bill_month, amount, payment_method)
    
    def get_customer_usage_stats(self, customer_id: str, month: str = None) -> Optional[Dict]:
        """Kullanım istatistiklerini getirir."""
        return self.db.get_customer_usage_stats(customer_id, month)

class SessionService:
    def __init__(self, db: CallCenterDatabase):
        self.db = db
    
    def create_call_session(self, customer_id: str = None, agent_mode: str = 'ai') -> str:
        """Yeni görüşme oturumu başlatır."""
        return self.db.create_call_session(customer_id, agent_mode)
    
    def end_call_session(self, session_id: str, resolution_status: str = None, 
                        customer_satisfaction: int = None, notes: str = None) -> bool:
        """Görüşme oturumunu sonlandırır."""
        return self.db.end_call_session(session_id, resolution_status, customer_satisfaction, notes)
    
    def add_call_message(self, session_id: str, role: str, content: str, 
                        message_type: str = 'text', tool_call: str = None, 
                        tool_result: str = None, processing_time_ms: int = None) -> int:
        """Görüşme mesajı ekler."""
        return self.db.add_call_message(session_id, role, content, message_type, 
                                       tool_call, tool_result, processing_time_ms)
    
    def log_tool_usage(self, session_id: str, tool_name: str, parameters: Dict, 
                      result: str, execution_time_ms: int, success: bool = True) -> int:
        """Araç kullanımını loglar."""
        return self.db.log_tool_usage(session_id, tool_name, parameters, result, 
                                     execution_time_ms, success)
    
    def get_call_session_history(self, session_id: str) -> Dict:
        """Görüşme oturumu geçmişi."""
        return self.db.get_call_session_history(session_id)

class AnalyticsService:
    def __init__(self, db: CallCenterDatabase):
        self.db = db
    
    def get_daily_metrics(self, date_str: str = None) -> Dict:
        """Günlük metrikleri getirir."""
        return self.db.get_daily_metrics(date_str)
    
    def get_tool_usage_stats(self, days: int = 30) -> List[Dict]:
        """Araç kullanım istatistiklerini getirir."""
        return self.db.get_tool_usage_stats(days)
    
    def get_database_stats(self) -> Dict:
        """Veritabanı istatistiklerini getirir."""
        return self.db.get_database_stats()
    
    def get_system_health(self) -> Dict:
        """Sistem sağlığını kontrol eder."""
        return self.db.get_system_health()

# Service Factory
class ServiceFactory:
    def __init__(self, database: CallCenterDatabase):
        self.db = database
        self._customer_service = None
        self._package_service = None
        self._billing_service = None
        self._session_service = None
        self._analytics_service = None
    
    @property
    def customer(self) -> CustomerService:
        if not self._customer_service:
            self._customer_service = CustomerService(self.db)
        return self._customer_service
    
    @property
    def package(self) -> PackageService:
        if not self._package_service:
            self._package_service = PackageService(self.db)
        return self._package_service
    
    @property
    def billing(self) -> BillingService:
        if not self._billing_service:
            self._billing_service = BillingService(self.db)
        return self._billing_service
    
    @property
    def session(self) -> SessionService:
        if not self._session_service:
            self._session_service = SessionService(self.db)
        return self._session_service
    
    @property
    def analytics(self) -> AnalyticsService:
        if not self._analytics_service:
            self._analytics_service = AnalyticsService(self.db)
        return self._analytics_service