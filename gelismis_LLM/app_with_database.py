
import time
import random
import logging
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
# Database import
from database import CallCenterDatabase
from services import ServiceFactory  

# -------------------------------------------------------------------
# Logging Configuration
# -------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("mock-api")

# -------------------------------------------------------------------
# Database ve Services Initialization
# -------------------------------------------------------------------
DATABASE_PATH = "call_center.db"

try:
    db = CallCenterDatabase(DATABASE_PATH)
    services = ServiceFactory(db)  # Services factory initialize
    logger.info(f"✅ Database initialized: {DATABASE_PATH}")
    logger.info(f"✅ Services initialized")
except Exception as e:
    logger.error(f"❌ Database/Services initialization failed: {e}")
    raise

# -------------------------------------------------------------------
# Pydantic Models 
# -------------------------------------------------------------------
class StandardResponse(BaseModel):
    status: str = Field(..., example="success")
    data: Optional[Dict] = None
    message: Optional[str] = None

class PackageChangeRequest(BaseModel):
    customer_id: str = Field(..., example="1001")
    new_package: str = Field(..., example="Gold")
    
    # DEBUG için validation ekleyelim
    @validator('customer_id')
    def validate_customer_id(cls, v):
        if not v or not str(v).strip():
            raise ValueError('Customer ID boş olamaz')
        return str(v).strip()
    
    @validator('new_package')
    def validate_new_package(cls, v):
        if not v or not str(v).strip():
            raise ValueError('New package boş olamaz')
        valid_packages = ['Bronze', 'Silver', 'Gold', 'Standart', 'Premium']
        if str(v).strip() not in valid_packages:
            raise ValueError(f'Geçersiz paket adı. Geçerli paketler: {valid_packages}')
        return str(v).strip()

class PaymentRequest(BaseModel):
    customer_id: str = Field(..., example="1001")
    month: str = Field(..., example="2025-07")
    amount: float = Field(..., example=150.00)

# -------------------------------------------------------------------
# Utility Functions 
# -------------------------------------------------------------------
def simulate_latency(min_ms: int = 50, max_ms: int = 300):
    """Random delay to mimic real API response times."""
    delay = random.uniform(min_ms / 1000, max_ms / 1000)
    time.sleep(delay)

def random_failure(chance: float = 0.05):
    """Randomly raise a 503 to simulate transient errors."""
    if random.random() < chance:
        logger.warning("Simulated downstream service failure")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="Geçici hizmet kesintisi, lütfen tekrar deneyin")

# -------------------------------------------------------------------
# FastAPI Initialization  
# -------------------------------------------------------------------
app = FastAPI(
    title="Çağrı Merkezi API (Database Edition)",
    version="2.0.0",
    description="Gelişmiş veritabanı destekli çağrı merkezi servisleri."
)

# -------------------------------------------------------------------
# API Endpoints - Services Pattern 
# -------------------------------------------------------------------

@app.get("/health", response_model=StandardResponse)
def health_check():
    """API ve veritabanı sağlık kontrolü."""
    try:
        
        stats = services.analytics.get_database_stats()
        return StandardResponse(
            status="success",
            data={
                "api_status": "healthy",
                "database_status": "connected",
                "total_customers": stats.get('customers_count', 0),
                "total_sessions": stats.get('call_sessions_count', 0)
            },
            message="Sistem sağlıklı çalışıyor"
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Veritabanı bağlantı sorunu")

@app.get("/getUserInfo/{customer_id}", response_model=StandardResponse)
def get_user_info(customer_id: str):
    """Kullanıcı bilgilerini döner."""
    
    try:
        
        customer_info = services.customer.get_customer_info(customer_id)
        
        if not customer_info:
            logger.error(f"getUserInfo: {customer_id} bulunamadı")
            raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
        
        
        response_data = {
            "name": customer_info["name"],
            "package": customer_info["package_name"] or "Tanımsız",
            "balance": float(customer_info["current_balance"] or 0)
        }
        
        logger.info(f"getUserInfo: {customer_id} başarıyla getirildi")
        return StandardResponse(status="success", data=response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"getUserInfo error: {e}")
        raise HTTPException(status_code=500, detail="İç sistem hatası")



@app.get("/getAvailablePackages/{customer_id}", response_model=StandardResponse)
def get_available_packages(customer_id: str):
    """Mevcut paket listesini döner."""
    
    
    try:
        
        customer_info = services.customer.get_customer_info(customer_id)
        if not customer_info:
            logger.error(f"getAvailablePackages: {customer_id} bulunamadı")
            raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
        
        
        packages = services.package.get_available_packages()
        
       
        packages_dict = {}
        for pkg in packages:
            packages_dict[pkg["package_name"]] = {
                "price": float(pkg["price"]),
                "features": pkg["features"]
            }
        
        logger.info(f"getAvailablePackages: paket listesi sağlandı")
        return StandardResponse(status="success", data=packages_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"getAvailablePackages error: {e}")
        raise HTTPException(status_code=500, detail="İç sistem hatası")



@app.post("/initiatePackageChange", response_model=StandardResponse)
def initiate_package_change(req: PackageChangeRequest):
    """Kullanıcının paketini değiştirir."""
    
    # DEBUG: Gelen request'i logla
    logger.info(f"🔍 initiatePackageChange DEBUG - Received request:")
    logger.info(f"    customer_id: {req.customer_id} (type: {type(req.customer_id)})")
    logger.info(f"    new_package: {req.new_package} (type: {type(req.new_package)})")
    
    
    
    try:
        
        customer_info = services.customer.get_customer_info(req.customer_id)
        logger.info(f"🔍 Customer info result: {customer_info}")
        
        if not customer_info:
            logger.error(f"initiatePackageChange: {req.customer_id} bulunamadı")
            raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
        
        
        logger.info(f"🔍 Attempting package change: {req.customer_id} -> {req.new_package}")
        success = services.package.change_customer_package(req.customer_id, req.new_package)
        logger.info(f"🔍 Package change result: {success}")
        
        if not success:
            logger.error(f"initiatePackageChange: {req.new_package} geçersiz")
            raise HTTPException(status_code=400, detail="Paket bulunamadı")
        
        old_package = customer_info["package_name"] or "Tanımsız"
        logger.info(f"{req.customer_id}: {old_package} → {req.new_package}")
        
        return StandardResponse(
            status="success",
            message=f"Paket başarıyla {req.new_package} olarak güncellendi"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"initiatePackageChange error: {e}")
        
        raise HTTPException(status_code=500, detail="İç sistem hatası")



@app.get("/getBillingInfo/{customer_id}", response_model=StandardResponse)
def get_billing_info(customer_id: str):
    """Müşterinin fatura geçmişini getirir."""
   
    
    try:
        
        customer_info = services.customer.get_customer_info(customer_id)
        if not customer_info:
            logger.error(f"getBillingInfo: {customer_id} bulunamadı")
            raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
        
        
        bills = services.billing.get_customer_bills(customer_id)
        
        # Format to match old format
        formatted_bills = []
        for bill in bills:
            formatted_bills.append({
                "month": bill["bill_month"],
                "amount": float(bill["amount"]),
                "paid": bool(bill["is_paid"])
            })
        
        logger.info(f"getBillingInfo: {customer_id} için {len(bills)} kayıt bulundu")
        return StandardResponse(status="success", data={"bills": formatted_bills})
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"getBillingInfo error: {e}")
        raise HTTPException(status_code=500, detail="İç sistem hatası")

@app.get("/getUsageStats/{customer_id}", response_model=StandardResponse)
def get_usage_stats(customer_id: str):
    """Müşteri kullanım istatistiklerini döner."""
    
    
    try:
        
        customer_info = services.customer.get_customer_info(customer_id)
        if not customer_info:
            logger.error(f"getUsageStats: {customer_id} bulunamadı")
            raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
        
        
        stats = services.billing.get_customer_usage_stats(customer_id)
        
        if not stats:
            
            stats = {"calls_minutes": 0, "data_mb": 0, "sms_count": 0}
        
       
        formatted_stats = {
            "calls": int(stats["calls_minutes"]),
            "data_mb": int(stats["data_mb"]),
            "sms": int(stats["sms_count"])
        }
        
        logger.info(f"getUsageStats: {customer_id} istatistik gönderildi")
        return StandardResponse(status="success", data=formatted_stats)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"getUsageStats error: {e}")
        raise HTTPException(status_code=500, detail="İç sistem hatası")

@app.post("/payBill", response_model=StandardResponse)
def pay_bill(req: PaymentRequest):
    """Fatura ödemesi gerçekleştirir."""
    
    
    try:
        
        customer_info = services.customer.get_customer_info(req.customer_id)
        if not customer_info:
            logger.error(f"payBill: {req.customer_id} bulunamadı")
            raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
        
        
        bills = services.billing.get_customer_bills(req.customer_id)
        bill_to_pay = None
        
        for bill in bills:
            if bill["bill_month"] == req.month:
                bill_to_pay = bill
                break
        
        if not bill_to_pay:
            raise HTTPException(status_code=404, detail="Fatura bulunamadı")
        
        if bill_to_pay["is_paid"]:
            raise HTTPException(status_code=409, detail="Fatura zaten ödenmiş")
        
        if abs(float(bill_to_pay["amount"]) - req.amount) > 0.01:
            raise HTTPException(status_code=400, detail="Tutar uyuşmuyor")
        
        
        success = services.billing.pay_bill(req.customer_id, req.month, req.amount)
        
        if not success:
            raise HTTPException(status_code=500, detail="Ödeme işlenemedi")
        
        logger.info(f"{req.customer_id}: {req.month} faturası ödendi")
        return StandardResponse(status="success", message="Fatura ödendi")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"payBill error: {e}")
        raise HTTPException(status_code=500, detail="İç sistem hatası")


# -------------------------------------------------------------------
# Additional Analytics Endpoints - Services Pattern
# -------------------------------------------------------------------

@app.get("/analytics/daily", response_model=StandardResponse)
def get_daily_analytics():
    """Günlük analitik verileri."""
    try:
        # DEĞIŞIM: db.get_daily_metrics() -> services.analytics.get_daily_metrics()
        metrics = services.analytics.get_daily_metrics()
        return StandardResponse(status="success", data=metrics)
    except Exception as e:
        logger.error(f"Daily analytics error: {e}")
        raise HTTPException(status_code=500, detail="Analitik veriler alınamadı")

@app.get("/analytics/tools", response_model=StandardResponse)
def get_tool_analytics(days: int = 30):
    """Araç kullanım istatistikleri."""
    try:
        # DEĞIŞIM: db.get_tool_usage_stats() -> services.analytics.get_tool_usage_stats()
        tool_stats = services.analytics.get_tool_usage_stats(days)
        return StandardResponse(status="success", data=tool_stats)
    except Exception as e:
        logger.error(f"Tool analytics error: {e}")
        raise HTTPException(status_code=500, detail="Araç istatistikleri alınamadı")

@app.get("/analytics/database", response_model=StandardResponse)
def get_database_analytics():
    """Veritabanı istatistikleri."""
    try:
        # DEĞIŞIM: db.get_database_stats() -> services.analytics.get_database_stats()
        db_stats = services.analytics.get_database_stats()
        return StandardResponse(status="success", data=db_stats)
    except Exception as e:
        logger.error(f"Database analytics error: {e}")
        raise HTTPException(status_code=500, detail="Veritabanı istatistikleri alınamadı")

@app.get("/customer/{customer_id}/history", response_model=StandardResponse)
def get_customer_call_history(customer_id: str, limit: int = 10):
    """Müşterinin görüşme geçmişi."""
    try:
        # DEĞIŞIM: db.get_customer_info() -> services.customer.get_customer_info()
        customer_info = services.customer.get_customer_info(customer_id)
        if not customer_info:
            raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
        
        # DEĞIŞIM: db.get_customer_call_history() -> services.customer.get_customer_call_history()
        history = services.customer.get_customer_call_history(customer_id, limit)
        return StandardResponse(status="success", data={"history": history})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Customer history error: {e}")
        raise HTTPException(status_code=500, detail="Görüşme geçmişi alınamadı")

@app.get("/session/{session_id}", response_model=StandardResponse)
def get_session_details(session_id: str):
    """Görüşme oturumu detayları."""
    try:
        # DEĞIŞIM: db.get_call_session_history() -> services.session.get_call_session_history()
        session_info = services.session.get_call_session_history(session_id)
        if not session_info:
            raise HTTPException(status_code=404, detail="Oturum bulunamadı")
        
        return StandardResponse(status="success", data=session_info)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session details error: {e}")
        raise HTTPException(status_code=500, detail="Oturum detayları alınamadı")

# -------------------------------------------------------------------
# Maintenance Endpoints - Services Pattern
# -------------------------------------------------------------------

@app.post("/admin/cleanup", response_model=StandardResponse)
def cleanup_old_data(days_to_keep: int = 90):
    """Eski verileri temizle."""
    try:
        # Bu fonksiyon direkt database üzerinde çalışır, services'e taşımaya gerek yok
        deleted_count = db.cleanup_old_logs(days_to_keep)
        return StandardResponse(
            status="success", 
            data={"deleted_sessions": deleted_count},
            message=f"{deleted_count} eski oturum temizlendi"
        )
    except Exception as e:
        logger.error(f"Cleanup error: {e}")
        raise HTTPException(status_code=500, detail="Temizlik işlemi başarısız")

@app.post("/admin/backup", response_model=StandardResponse)
def backup_database():
    """Veritabanı yedeği oluştur."""
    try:
        
        backup_path = db.backup_database()
        return StandardResponse(
            status="success",
            data={"backup_path": backup_path},
            message="Veritabanı yedeği oluşturuldu"
        )
    except Exception as e:
        logger.error(f"Backup error: {e}")
        raise HTTPException(status_code=500, detail="Yedekleme başarısız")

# -------------------------------------------------------------------
# Web Agent Integration Endpoints - Services Pattern
# -------------------------------------------------------------------

@app.post("/agent/start", response_model=StandardResponse)
def start_agent_session(customer_id: Optional[str] = None):
    """Yeni agent oturumu başlat."""
    try:
        
        session_id = services.session.create_call_session(customer_id, 'web_api')
        return StandardResponse(
            status="success",
            data={"session_id": session_id},
            message="Agent oturumu başlatıldı"
        )
    except Exception as e:
        logger.error(f"Start agent session error: {e}")
        raise HTTPException(status_code=500, detail="Agent oturumu başlatılamadı")

@app.post("/agent/end/{session_id}", response_model=StandardResponse)
def end_agent_session(session_id: str, satisfaction: Optional[int] = None, notes: Optional[str] = None):
    """Agent oturumunu sonlandır."""
    try:
        # DEĞIŞIM: db.end_call_session() -> services.session.end_call_session()
        success = services.session.end_call_session(session_id, "completed", satisfaction, notes)
        if not success:
            raise HTTPException(status_code=404, detail="Oturum bulunamadı")
        
        return StandardResponse(
            status="success",
            message="Agent oturumu sonlandırıldı"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"End agent session error: {e}")
        raise HTTPException(status_code=500, detail="Agent oturumu sonlandırılamadı")

@app.post("/agent/log/{session_id}", response_model=StandardResponse)
def log_agent_message(session_id: str, role: str, content: str, tool_call: Optional[str] = None):
    """Agent mesajını logla."""
    try:
        
        message_id = services.session.add_call_message(session_id, role, content, tool_call=tool_call)
        return StandardResponse(
            status="success",
            data={"message_id": message_id},
            message="Mesaj loglandı"
        )
    except Exception as e:
        logger.error(f"Log message error: {e}")
        raise HTTPException(status_code=500, detail="Mesaj loglanamadı")

# -------------------------------------------------------------------
# Test Data Endpoints (Development Only) -
# -------------------------------------------------------------------

@app.post("/dev/reset-test-data", response_model=StandardResponse)
def reset_test_data():
    """Test verilerini sıfırla ve yeniden oluştur."""
    try:
        return StandardResponse(
            status="success",
            message="Test verileri sıfırlandı (geliştirme modu)"
        )
    except Exception as e:
        logger.error(f"Reset test data error: {e}")
        raise HTTPException(status_code=500, detail="Test verileri sıfırlanamadı")

@app.get("/dev/sample-customers", response_model=StandardResponse)
def get_sample_customers():
    """Test müşteri listesi."""
    sample_customers = [
        {"id": "1001", "name": "Ali Veli", "package": "Premium"},
        {"id": "1002", "name": "Ayşe Demir", "package": "Standart"},
        {"id": "1003", "name": "Mehmet Can", "package": "Gold"},
        {"id": "1004", "name": "Elif Yılmaz", "package": "Silver"},
        {"id": "1005", "name": "Berke Kara", "package": "Bronze"},
    ]
    
    return StandardResponse(
        status="success",
        data={"customers": sample_customers},
        message="Test müşteri listesi"
    )

# -------------------------------------------------------------------
# Error Handlers (aynı kalıyor)
# -------------------------------------------------------------------

@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content=StandardResponse(
            status="error",
            message="İstenen kaynak bulunamadı"
        ).dict()
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal server error: {exc}")
    return StandardResponse(
        status="error", 
        message="İç sistem hatası"
    )

# -------------------------------------------------------------------
# Startup/Shutdown Events - Services Pattern
# -------------------------------------------------------------------

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Çağrı Merkezi API başlatıldı")
    logger.info(f"📊 Veritabanı: {DATABASE_PATH}")
    
    # Veritabanı istatistikleri
    try:
        
        stats = services.analytics.get_database_stats()
        logger.info(f"📈 Toplam müşteri: {stats.get('customers_count', 0)}")
        logger.info(f"📞 Toplam görüşme: {stats.get('call_sessions_count', 0)}")
        logger.info(f"💾 DB boyutu: {stats.get('db_size_mb', 0):.2f} MB")
    except Exception as e:
        logger.error(f"Startup stats error: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Çağrı Merkezi API kapatılıyor")
    
    # Son yedek alma (opsiyonel)
    try:
        backup_path = db.backup_database()  
        logger.info(f"💾 Kapatılırken yedek alındı: {backup_path}")
    except Exception as e:
        logger.warning(f"Shutdown backup failed: {e}")

# -------------------------------------------------------------------
# Uvicorn ile Çalıştırma 
# -------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    print("🎯 Gelişmiş Çağrı Merkezi API (Database Edition)")
    print(f"🗄️  Database: {DATABASE_PATH}")
    print("🔗 Endpoints:")
    print("   • http://localhost:8000/docs (API Documentation)")
    print("   • http://localhost:8000/health (Health Check)")
    print("   • http://localhost:8000/analytics/daily (Daily Metrics)")
    print("-" * 60)
    
    uvicorn.run("app_with_database:app", host="0.0.0.0", port=8000, reload=True)