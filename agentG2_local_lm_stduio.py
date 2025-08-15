# agentG2_local_lm_studio.py
import os
import json
import requests
import logging
import threading
import time
import queue
import sys
from typing import Dict, List, Optional, Any
from datetime import datetime
import traceback
import requests
from services import ServiceFactory

# Voice processing imports
from gtts import gTTS

# Database import
from database import CallCenterDatabase, CallSessionManager

# Pydantic for validation
from pydantic import BaseModel, Field

# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("voice-call-center-agent")

# API Configuration
MOCK_API_BASE = "http://localhost:8000"
API_CLIENT_TIMEOUT = 300

# --- YENİ: LM Studio API Yapılandırması ---
LM_STUDIO_API_URL = "http://127.0.0.1:1234/v1/chat/completions"
# LM Studio Model Adı 
MODEL_NAME = "gemma-3-12b-it"


# Voice Configuration
AUDIO_TEMP_DIR = "temp_audio"
os.makedirs(AUDIO_TEMP_DIR, exist_ok=True)

# Database Configuration
DATABASE_PATH = "call_center.db"

# -------------------------------------------------------------------
# Voice Processing Functions (DEĞİŞİKLİK YOK)
# -------------------------------------------------------------------
class VoiceProcessor:
    def __init__(self):
        logger.info("Voice processor initialized for web interface")
    
    def text_to_speech(self, text, lang='tr'):
        """Metni sese çevirir - web arayüzünde ses dosyası oluşturur."""
        try:
            filename = f"{AUDIO_TEMP_DIR}/output_{int(time.time())}.mp3"
            tts = gTTS(text=text, lang=lang, slow=False)
            tts.save(filename)
            
            logger.info(f"🗣️  Asistan: {text}")
            return filename
            
        except Exception as e:
            logger.error(f"TTS hatası: {e}")
            return None

# -------------------------------------------------------------------
# Tool Definitions (DEĞİŞİKLİK YOK)
# -------------------------------------------------------------------
AVAILABLE_TOOLS = {
    # UZMAN ARAÇLARI
    "get_user_info": {
        "description": "Müşteri temel bilgilerini (isim, paket, bakiye) getirir. Genellikle ilk adımdır.",
        "parameters": {
            "customer_id": "string - Müşteri ID'si"
        }
    },
    "get_available_packages": {
        "description": "Mevcut tüm internet/telefon paketi seçeneklerini listeler.",
        "parameters": {}
    },
    "change_package": {
        "description": "Müşterinin mevcut paketini yenisiyle değiştirir.",
        "parameters": {
            "customer_id": "string - Müşteri ID'si",
            "new_package": "string - Yeni paket adı (Bronze, Silver, Gold, Standart, Premium)"
        }
    },
    "get_billing_info": {
        "description": "Müşterinin geçmiş ve güncel fatura bilgilerini getirir.",
        "parameters": {
            "customer_id": "string - Müşteri ID'si"
        }
    },
    "get_usage_stats": {
        "description": "Müşterinin arama, internet ve SMS kullanım istatistiklerini getirir.",
        "parameters": {
            "customer_id": "string - Müşteri ID'si"
        }
    },
    "pay_bill": {
        "description": "Belirli bir aya ait faturanın ödemesini yapar.",
        "parameters": {
            "customer_id": "string - Müşteri ID'si",
            "month": "string - Fatura ayı (YYYY-MM formatında)",
            "amount": "float - Ödeme tutarı"
        }
    },
    # DAĞITICI ARACI
    "route_to_specialist": {
        "description": "Müşterinin isteğini anladıktan sonra onu ilgili uzmana yönlendirir.",
        "parameters": {
            "specialist": "string - Yönlendirilecek uzman alanı. Seçenekler: 'billing', 'package_management', 'user_info', 'general_inquiry'"
        }
    }
}

SPECIALIST_DEFINITIONS = {
    "billing": {
        "name": "Fatura Uzmanı",
        "description": """-Müşterinin fatura bilgilerini yönetir ve ödemeleri yapar.
                          - Fatura sorgulama ve detayları görüntüleme işlemlerini yapar.
                          - Farklı konularda bilgi vermemelisin. Sana sadece faturayla ilgili işlemler yaptırılabilir. Senden istenen bilgi veya araştırma konularına bakmadan direkt olarak faturayla ilgisizse "Üzgünüm sadece fatura konularıyla ilgili yardımcı olabiliyorum desin"
                          - Ödeme işlemleri yapabilir.
                          - Bakiye kontrolleri yapabilir.
                          - Ödeme geçmişini görüntüleyebilir.
                          - Fatura açıklamaları ve detayları hakkında bilgi verebilir.""",
        "tools": ["get_billing_info", "pay_bill", "get_user_info", "route_to_specialist"]
    },
    "package_management": {
        "name": "Paket Yönetimi Uzmanı",
        "description": """Mevcut paketleri listeleme, paketleri karşılaştırma ve müşterinin paketini değiştirme işlemlerini yapar.
            - Mevcut paket analizi yapabilir.
            - Paket karşılaştırması yapabilir.
            - Paket değişikliği yapabilir.
            - Farklı konularda bilgi vermemelisin. Sana sadece paket yönetimi ile ilgili işlemler yaptırılabilir. Senden istenen bilgi veya araştırma konularına bakmadan direkt olarak paket yönetimi ile ilgisizse "Üzgünüm sadece paket ile ilgili konularla yardımcı olabiliyorum" de
            - Yükseltme önerileri sunabilir.
            - Fiyat bilgilendirmesi yapabilir.""",
        "tools": ["get_available_packages", "change_package", "get_user_info", "route_to_specialist"]
    },
    "user_info": {
        "name": "Kullanıcı Bilgileri Uzmanı",
        "description": """Müşteri bilgileri, kullanım istatistikleri ve genel hesap durumu hakkında bilgi verir.
                        - Limit kontrolleri yapabilir.
                        - Kullanım önerileri sunabilir.
                        - Farklı konularda bilgi vermemelisin. Sana sadece kullanıcı bilgileri ile ilgili işlemler yaptırılabilir. Senden istenen bilgi veya araştırma konularına bakmadan direkt olarak kullanıcı bilgileri ile ilgisizse "Üzgünüm sadece kullanıcıya yönelik konularda yardımcı olabiliyorum" de.
                        - Trafik analizi yapabilir.
                        - Aşım durumları hakkında bilgi verebilir.""",
        "tools": ["get_user_info", "get_usage_stats", "route_to_specialist"]
    },
    "general_inquiry": {
        "name": "Genel Bilgi Asistanı",
        "description": """Herhangi bir araca ihtiyaç duymayan genel soruları yanıtlar.
        - Sohbet edebilir.
        - Genel bilgilendirme yapabilir.
        - Müşteri hizmetleri sorularını yanıtlayabilir.
        - Şikayet alımı yapabilir.
        - Temel sorular yanıtlayabilir.
        - Yönlendirme desteği verebilir.""",
        "tools": ["route_to_specialist"]
    }
}


# -------------------------------------------------------------------
# APIToolExecutor 
# ------------------------------------------------------------------
class APIToolExecutor:
    def __init__(self, api_base_url: str, session_service, timeout: int = 300):
        self.api_base = api_base_url
        self.session_service = session_service
        self.timeout = timeout

    def execute_tool(self, tool_name: str, parameters: Dict) -> tuple[str, bool]:
        """Araçları API üzerinden çalıştırır."""
        start_time = time.time()
        success = True
        error_message = None
        
        try:
            if tool_name == "get_user_info":
                customer_id = parameters.get("customer_id")
                response = requests.get(f"{self.api_base}/getUserInfo/{customer_id}", timeout=self.timeout)
                
                if response.status_code == 200:
                    data = response.json()["data"]
                    result = f"Müşteri: {data['name']}, Paket: {data['package']}, Bakiye: {data['balance']} TL"
                else:
                    result = "Müşteri bulunamadı"
                    success = False
            
            elif tool_name == "get_available_packages":
                customer_id = parameters.get("customer_id", "1001") 
                response = requests.get(f"{self.api_base}/getAvailablePackages/{customer_id}", timeout=self.timeout)
                
                if response.status_code == 200:
                    packages = response.json()["data"]
                    package_list = []
                    for name, info in packages.items():
                        features = ", ".join(info['features'])
                        package_list.append(f"{name}: {info['price']} TL - {features}")
                    result = "Mevcut paketler:\n" + "\n".join(package_list)
                else:
                    result = "Paket listesi alınamadı"
                    success = False
            
            elif tool_name == "change_package":
                
                customer_id = parameters.get("customer_id")
                new_package = parameters.get("new_package")
                
                if not customer_id:
                    result = "Müşteri ID'si belirtilmedi"
                    success = False
                elif not new_package:
                    result = "Yeni paket adı belirtilmedi"
                    success = False
                else:
                    payload = {
                        "customer_id": str(customer_id),
                        "new_package": str(new_package)
                    }
                    
                    response = requests.post(
                        f"{self.api_base}/initiatePackageChange", 
                        json=payload, 
                        timeout=self.timeout,
                        headers={'Content-Type': 'application/json'}
                    )
                    
                    if response.status_code == 200:
                        response_data = response.json()
                        result = response_data.get("message", "Paket değişikliği tamamlandı")
                    elif response.status_code == 422:
                        try:
                            error_detail = response.json()
                            logger.error(f"🚨 Validation error: {error_detail}")
                            result = f"Parametre hatası: {error_detail}"
                        except:
                            result = "Parametre formatı hatalı"
                        success = False
                    elif response.status_code == 404:
                        result = "Müşteri bulunamadı"
                        success = False
                    elif response.status_code == 400:
                        result = "Geçersiz paket adı"
                        success = False
                    else:
                        result = f"API hatası: {response.status_code}"
                        success = False
            
            elif tool_name == "get_billing_info":
                customer_id = parameters.get("customer_id")
                response = requests.get(f"{self.api_base}/getBillingInfo/{customer_id}", timeout=self.timeout)
                
                if response.status_code == 200:
                    bills = response.json()["data"]["bills"]
                    bill_info = []
                    for bill in bills:
                        status = "Ödendi" if bill["paid"] else "Ödenmedi"
                        bill_info.append(f"{bill['month']}: {bill['amount']} TL - {status}")
                    result = "Fatura bilgileri:\n" + "\n".join(bill_info)
                else:
                    result = "Fatura bilgisi alınamadı"
                    success = False
            
            elif tool_name == "get_usage_stats":
                customer_id = parameters.get("customer_id")
                response = requests.get(f"{self.api_base}/getUsageStats/{customer_id}", timeout=self.timeout)
                
                if response.status_code == 200:
                    stats = response.json()["data"]
                    data_gb = stats["data_mb"] / 1024
                    result = f"Kullanım: {stats['calls']} dakika arama, {data_gb:.1f} GB internet, {stats['sms']} SMS"
                else:
                    result = "Kullanım bilgisi alınamadı"
                    success = False
            
            elif tool_name == "pay_bill":
                payload = {
                    "customer_id": parameters.get("customer_id"),
                    "month": parameters.get("month"),
                    "amount": parameters.get("amount")
                }
                response = requests.post(f"{self.api_base}/payBill", json=payload, timeout=self.timeout)
                
                if response.status_code == 200:
                    result = "Fatura başarıyla ödendi"
                else:
                    result = "Ödeme başarısız"
                    success = False
            
            else:
                result = f"Bilinmeyen araç: {tool_name}"
                success = False
                error_message = "Unknown tool"
        
        except requests.exceptions.Timeout:
            result = "API zaman aşımı"
            success = False
            error_message = "Timeout"
        except requests.exceptions.ConnectionError:
            result = "API bağlantı hatası"
            success = False
            error_message = "Connection error"
        except Exception as e:
            result = f"Sistem hatası: {str(e)}"
            success = False
            error_message = str(e)
            logger.error(f"Tool execution error: {e}")
        
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        try:
            self.session_service.log_tool_usage(
                tool_name, parameters, result, execution_time_ms, success
            )
        except Exception as e:
            logger.error(f"Failed to log tool usage: {e}")
        
        return result, success

# -------------------------------------------------------------------
# --- YENİ: Yerel LLM (LM Studio) Entegrasyonu ---
# -------------------------------------------------------------------
def call_llm_api(messages: List[Dict], max_tokens: int = 512) -> str:
    """LM Studio API'sini (OpenAI uyumlu) çağırır."""

    headers = {
        'Content-Type': 'application/json',
    }
    
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": max_tokens,
        "stream": False # Stream'i kapalı tutarak tam yanıtı alıyoruz
    }

    try:
        logger.debug(f"🔗 LLM API çağrısı yapılıyor... Model: {MODEL_NAME}")
        response = requests.post(LM_STUDIO_API_URL, headers=headers, json=payload, timeout=300)
        
        if response.status_code == 200:
            result = response.json()
            # OpenAI uyumlu yanıttan mesaj içeriğini al
            content = result['choices'][0]['message'].get('content', '')
            if content:
                logger.debug(f"✅ LLM yanıtı alındı ({len(content)} karakter)")
                return content
            else:
                logger.error("LLM yanıtı boş")
                return 'Yanıt alınamadı'
        else:
            logger.error(f"LLM API hatası: {response.status_code}")
            logger.error(f"Yanıt: {response.text}")
            return f"API Hatası: {response.status_code} - {response.text}"

    except requests.exceptions.Timeout:
        logger.error("LLM API zaman aşımı")
        return "Sistem yanıt vermiyor, lütfen tekrar deneyin"
    except requests.exceptions.ConnectionError:
        logger.error("LLM bağlantı hatası")
        return "Model sunucusuna bağlanılamıyor."
    except Exception as e:
        logger.error(f"LLM API istisnası: {e}")
        return "Bağlantı hatası oluştu"

def test_llm_connection() -> bool:
    """LM Studio API bağlantısını test eder."""
    try:
        test_payload = {
            "model": MODEL_NAME,
            "messages": [{"role": "user", "content": "Test"}],
            "max_tokens": 10
        }
        headers = {'Content-Type': 'application/json'}
        
        response = requests.post(LM_STUDIO_API_URL, headers=headers, json=test_payload, timeout=20)
        
        if response.status_code == 200:
            logger.info("✅ LM Studio API bağlantısı başarılı")
            return True
        else:
            logger.error(f"❌ LM Studio API bağlantı hatası: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ LM Studio API bağlantı testi başarısız: {e}")
        return False

# --- Kalan Yardımcı Fonksiyonlarda Değişiklik Yok ---

def parse_tool_call(response: str) -> Optional[Dict]:
    """
    LLM yanıtından araç çağrısını daha esnek bir şekilde parse eder.
    Hem 'TOOL_CALL:' formatını hem de markdown içindeki JSON'u arar.
    """
    try:
        if "TOOL_CALL:" in response:
            tool_part_str = response.split("TOOL_CALL:")[1].split("END_TOOL")[0].strip()
            return json.loads(tool_part_str)
    except json.JSONDecodeError as e:
        logger.error(f"Tool call JSON parse hatası: {e} - Yanıt: {response}")
        return None
    except Exception as e:
        logger.error(f"Genel tool call parse hatası: {e}")
        return None

def format_conversation_history(history: List[Dict]) -> str:
    """Konuşma geçmişini formatlar."""
    formatted = []
    for msg in history[-8:]: # Son 8 mesajı göster
        role = "Müşteri" if msg["role"] == "user" else "Asistan"
        formatted.append(f"{role}: {msg['content']}")
    return "\n".join(formatted)

# -------------------------------------------------------------------
# Enhanced CallCenterAgent Class (Gerekli Değişiklikler Yapıldı)
# -------------------------------------------------------------------
class EnhancedCallCenterAgent:
    def __init__(self, voice_mode=True, database_path=DATABASE_PATH, api_base_url=MOCK_API_BASE):
        self.voice_mode = voice_mode
        self.api_base_url = api_base_url
        self.voice_processor = VoiceProcessor() if voice_mode else None
        self.conversation_history = []
        
        self.current_layer = 'dispatcher'
        self.active_specialist = None
        
        try:
            self.db = CallCenterDatabase(database_path)
            self.services = ServiceFactory(self.db)
            self.session_manager = CallSessionManager(self.db)
            self.tool_executor = APIToolExecutor(api_base_url, self.session_manager)
            logger.info("✅ Database and API tool executor initialized")
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            raise
        
        self.prompts = {}
        self.specialist_tools = {}
        self._initialize_prompts()
        
        self.current_customer_id = None
        
        self._test_api_connection()
        # --- DEĞİŞİKLİK:LM Studio bağlantısı test ediliyor ---
        if not test_llm_connection():
            logger.warning("⚠️ LM Studio API bağlantısı başarısız!")

    def _initialize_prompts(self):
        """Tüm katmanlar için sistem prompt'larını ve araç listelerini oluşturur."""
        
        # 1. Dağıtıcı (Dispatcher) Katmanı Prompt'u
        route_tool = AVAILABLE_TOOLS['route_to_specialist']
        params = ", ".join([f"{k}: {v}" for k, v in route_tool["parameters"].items()])
        
        specialist_descriptions = "\n".join([f"- **{s_def['name']} ({s_key})**: {s_def['description']}" for s_key, s_def in SPECIALIST_DEFINITIONS.items()])
        
        self.prompts['dispatcher'] = f"""Sen bir çağrı merkezi yönlendirme ajanısın.
Görevin müşterinin isteğini analiz edip doğru uzmana yönlendirmek için `route_to_specialist` aracını çağırmaktır.

YÖNLENDİREBİLECEĞİN UZMANLAR:
{specialist_descriptions}

KATI KURALLAR:
1. Müşterinin talebini anında analiz et.
2. Yanıtın SADECE `TOOL_CALL: {{"tool": "route_to_specialist", "parameters": {{"specialist": "UZMAN_ADI"}}}} END_TOOL` formatında olmalıdır.
3. YANITINA ASLA MARKDOWN (```json) EKLEME.
4. Yanıtına kendi notlarını ekleme.
5. Konudan alakasız herhangi bir şey sorduğunda "Üzgünüm size yalnızca belli konularda hizmet verebiliyorum desin".


ÖRNEK TALEPLER VE YANITLAR:
- Müşteri: "faturamı ödemek istiyorum" -> YANIT: TOOL_CALL: {{"tool": "route_to_specialist", "parameters": {{"specialist": "billing"}}}} END_TOOL
- Müşteri: "yeni paketleri göster" -> YANIT: TOOL_CALL: {{"tool": "route_to_specialist", "parameters": {{"specialist": "package_management"}}}} END_TOOL
"""
        
        # 2. Uzman (Specialist) Katmanları için Prompt'lar
        self.prompts['specialists'] = {}
        for spec_key, spec_def in SPECIALIST_DEFINITIONS.items():
            tools_info = []
            self.specialist_tools[spec_key] = spec_def['tools']
            for tool_name in spec_def['tools']:
                tool_info = AVAILABLE_TOOLS[tool_name]
                params = ", ".join([f"{k}: {v}" for k, v in tool_info["parameters"].items()])
                tools_info.append(f"- {tool_name}: {tool_info['description']} | Parametreler: {params}")
            
            tools_section = "\n".join(tools_info)
            self.prompts['specialists'][spec_key] = f"""Sen profesyonel bir çağrı merkezi uzmanısın.
Senin uzmanlık alanın: **{spec_def['name']}**.
            Uzmanlık alan bilgilerin: **{spec_def['description']}**

GÖREVİN:
Müşterinin bu alandaki sorunlarını çözmek için aşağıdaki araçları kullan.
MEVCUT ARAÇLARIN:
{tools_section}

BİR ARAÇ KULLANMA FORMATI:
TOOL_CALL: {{"tool": "araç_adı", "parameters": {{"param1": "değer1"}}}}
END_TOOL

KATI KURALLAR:
1. Müşteri ID'sini bilmiyorsan onu sor, konuşma bitene kadar müşteri ID'sini aklında tut.
2. Eğer müşterinin talebi senin uzmanlık alanın dışındaysa, kesinlikle başka bir aracı kullanmaya veya tahmin etmeye çalışma.
3. Bu durumda, müşteriyi doğru uzmana yönlendirmek için `route_to_specialist` aracını kullanmalısın.
4. Konudan alakasız herhangi bir şey sorduğunda "Üzgünüm size yalnızca belli konularda hizmet verebiliyorum desin".

YÖNLENDİREBİLECEĞİN UZMANLAR:{specialist_descriptions}
"""

    def _get_current_prompt(self) -> str:
        """Mevcut katmana göre doğru sistem prompt'unu döndürür."""
        if self.current_layer == 'dispatcher':
            return self.prompts['dispatcher']
        elif self.current_layer == 'specialist' and self.active_specialist:
            return self.prompts['specialists'].get(self.active_specialist, "")
        return "Bir hata oluştu."

    def _activate_specialist(self, specialist_name: str) -> str:
        """
        Belirtilen uzman katmanına geçiş yapar ve son kullanıcı mesajını yeni uzmana iletir.
        """
        if specialist_name not in SPECIALIST_DEFINITIONS:
            return f"Hata: '{specialist_name}' adında bir uzman bulunamadı."
        
        last_user_message = ""
        for message in reversed(self.conversation_history):
            if message['role'] == 'user':
                last_user_message = message['content']
                break
        
        self.current_layer = 'specialist'
        self.active_specialist = specialist_name
        specialist_info = SPECIALIST_DEFINITIONS[specialist_name]
        
        
        self.session_manager.log_message("system", f"Katman değiştirildi: Uzman -> {specialist_name}")
        
        welcome_message = f"Merhaba, ben {specialist_info['name']}. Talebiniz üzerine bu alana yönlendirildiniz."
        self.conversation_history.append({"role": "assistant", "content": welcome_message})

        if last_user_message:
            return self.process_message(last_user_message)
        
        return welcome_message

    def _return_to_dispatcher(self) -> str:
        """Dağıtıcı katmanına geri döner."""
        if self.current_layer == 'dispatcher':
            return "Zaten ana menüdesiniz. Nasıl yardımcı olabilirim?"

        logger.info(f"LAYER SWITCH: Specialist({self.active_specialist}) -> Dispatcher")
        self.session_manager.log_message("system", f"Katman değiştirildi: Ana Menü (Dağıtıcı)")
        
        self.current_layer = 'dispatcher'
        self.active_specialist = None
        self.reset_conversation() # Ana menüye dönüldüğünde geçmişi temizle
        
        response = "Ana menüye döndünüz. Başka bir konuda yardımcı olabilir miyim?"
        self.conversation_history.append({"role": "assistant", "content": response})
        return response

    def _test_api_connection(self) -> bool:
        """Arka uç API bağlantısını test eder."""
        try:
            response = requests.get(f"{self.api_base_url}/health", timeout=10)
            if response.status_code == 200:
                logger.info("✅ Arka uç API bağlantısı başarılı")
                return True
            else:
                logger.warning(f"⚠️ Arka uç API bağlantı uyarısı: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Arka uç API bağlantı testi başarısız: {e}")
            return False

    def start_new_session(self, customer_id: str = None) -> str:
        """Yeni bir görüşme oturumu başlat."""
        session_id = self.services.session.create_call_session(customer_id, 'ai')
        self.session_manager.current_session_id = session_id
        self.current_customer_id = customer_id
        
        self.current_layer = 'dispatcher'
        self.active_specialist = None
        self.conversation_history = []
        
        self.services.session.add_call_message(session_id, "system", f"Görüşme başladı - Müşteri: {customer_id or 'Bilinmiyor'}")
        
        logger.info(f"🎬 Yeni görüşme oturumu başladı: {session_id} (Layer: {self.current_layer})")
        return session_id
    
    def end_current_session(self, resolution_status: str = 'resolved', customer_satisfaction: int = None, notes: str = None):
        """Mevcut görüşme oturumunu sonlandır."""
        if self.session_manager.get_session_id():
            self.session_manager.end_session(resolution_status, customer_satisfaction, notes)
            logger.info("🏁 Görüşme oturumu sonlandırıldı")
        self.current_customer_id = None

    def process_message(self, user_message: str, voice_response: bool = False) -> str:
        """Kullanıcı mesajını işler ve mevcut katmana göre yanıt döner."""
        start_time = time.time()
        
        try:
            if not self.session_manager.get_session_id():
                self.start_new_session()

            if any(cmd in user_message.lower() for cmd in ["ana menü", "geri dön", "başka işlem"]):
                return self._return_to_dispatcher()

            self.conversation_history.append({"role": "user", "content": user_message})
            self.session_manager.log_message("user", user_message)
            
            system_prompt = self._get_current_prompt()
            
            if self.current_customer_id:
                customer_id_note = f"Sistem notu: Mevcut müşterinin ID'si {self.current_customer_id} olarak belirlenmiştir. Araç çağrılarında bu ID'yi kullan."
                system_prompt = f"mevcut müşteri ID: {customer_id_note}\n\n{system_prompt}"
            
            max_tokens_for_call = 256 if self.current_layer == 'dispatcher' else 800
            
            # LM Studio'nun OpenAI formatına uygun mesaj listesi oluşturuluyor
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(self.conversation_history[-8:]) # Son 8 mesajı geçmiş olarak ekle
            
            # --- DEĞİŞİKLİK: Yerel LLM API çağrısı yapılıyor ---
            response = call_llm_api(messages, max_tokens=max_tokens_for_call)
            
            tool_call = parse_tool_call(response)
            
            if tool_call:
                tool_name = tool_call.get("tool")
                parameters = tool_call.get("parameters", {})
                
                if 'customer_id' in AVAILABLE_TOOLS.get(tool_name, {}).get('parameters', {}) and 'customer_id' not in parameters:
                    if self.current_customer_id:
                        logger.info(f"💡 Otomatik olarak müşteri ID'si ({self.current_customer_id}) eklendi.")
                        parameters['customer_id'] = self.current_customer_id
                
                
                
                if tool_name == "route_to_specialist":
                    specialist = parameters.get("specialist")
                    final_response = self._activate_specialist(specialist)
                else:
                    tool_result, tool_success = self.tool_executor.execute_tool(tool_name, parameters)
                    
                    if tool_name == "get_user_info" and tool_success:
                        if parameters.get("customer_id"):
                            self.current_customer_id = parameters.get("customer_id")
                            
                    
                    follow_up_system_prompt = self._get_current_prompt()
                    
                    
                    follow_up_messages = [
                        {"role": "system", "content": follow_up_system_prompt},
                        {"role": "user", "content": f"Araç '{tool_name}' sonucu: {tool_result}\n\nBu sonucu kullanarak müşteriye kısa ve net bir yanıt ver."}
                    ]
                    
                    final_response = call_llm_api(follow_up_messages)
                    
                    self.session_manager.log_message("assistant", final_response, tool_name, tool_result, int((time.time() - start_time) * 1000))
            else:
                final_response = response
                self.session_manager.log_message("assistant", final_response, processing_time_ms=int((time.time() - start_time) * 1000))
            
            final_response = final_response.split("TOOL_CALL:")[0].strip()
            final_response = final_response.split("END_TOOL")[0].strip()
            if final_response.startswith("Asistan:"):
                final_response = final_response[9:].strip()

            self.conversation_history.append({"role": "assistant", "content": final_response})
            return final_response
            
        except Exception as e:
            error_message = f"İşlem sırasında hata oluştu: {str(e)}"
            logger.error(f"Process message error: {e}\n{traceback.format_exc()}")
            if self.session_manager.get_session_id():
                self.session_manager.db.log_error(self.session_manager.get_session_id(), "process_message_error", error_message, traceback.format_exc(), "high")
            return "Üzgünüm, şu anda bir teknik sorun yaşıyorum. Lütfen tekrar deneyin."

    def reset_conversation(self):
        """Konuşma geçmişini sıfırlar ama session'ı sonlandırmaz."""
        self.conversation_history = []
        logger.info(f"Konuşma geçmişi sıfırlandı (Layer: {self.current_layer})")

    def get_session_info(self) -> Optional[Dict]:
        session_id = self.session_manager.get_session_id()
        if session_id:
            return self.db.get_call_session_history(session_id)
        return None

    def get_customer_history(self, customer_id: str, limit: int = 5) -> List[Dict]:
        return self.db.get_customer_call_history(customer_id, limit)

    def generate_session_report(self) -> Dict:
        session_info = self.get_session_info()
        if not session_info:
            return {}
        
        session = session_info['session']
        messages = session_info['messages']
        tools = session_info['tool_usage']
        
        total_messages = len(messages)
        user_messages = len([m for m in messages if m['role'] == 'user'])
        assistant_messages = len([m for m in messages if m['role'] == 'assistant'])
        tool_calls = len(tools)
        
        successful_tools = len([t for t in tools if t['success']])
        tool_success_rate = (successful_tools / tool_calls * 100) if tool_calls > 0 else 0
        
        processing_times = [m.get('processing_time_ms', 0) for m in messages if m.get('processing_time_ms')]
        avg_response_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        return {
            'session_id': session['session_id'],
            'customer_id': session.get('customer_id'),
            'customer_name': session.get('customer_name'),
            'start_time': session['start_time'],
            'end_time': session.get('end_time'),
            'duration_seconds': session.get('duration_seconds'),
            'status': session['status'],
            'resolution_status': session.get('resolution_status'),
            'customer_satisfaction': session.get('customer_satisfaction'),
            'total_messages': total_messages,
            'user_messages': user_messages,
            'assistant_messages': assistant_messages,
            'tool_calls': tool_calls,
            'tool_success_rate': round(tool_success_rate, 2),
            'avg_response_time_ms': round(avg_response_time, 2)
        }

# -------------------------------------------------------------------
# Web API Integration Class (DEĞİŞİKLİK YOK)
# -------------------------------------------------------------------
class WebAgentAPI:
    def __init__(self):
        self.agent = None
        self.current_session_id = None

    def initialize_agent(self) -> Dict:
        try:
            self.agent = EnhancedCallCenterAgent(voice_mode=False)
            return {"success": True, "message": "Agent başarıyla başlatıldı"}
        except Exception as e:
            logger.error(f"Agent initialization failed: {e}")
            return {"success": False, "message": f"Agent başlatılamadı: {str(e)}"}

    def start_conversation(self, customer_id: str = None) -> Dict:
        if not self.agent:
            return {"success": False, "message": "Agent başlatılmamış"}
        
        try:
            session_id = self.agent.start_new_session(customer_id)
            self.current_session_id = session_id
            return {
                "success": True,
                "session_id": session_id,
                "message": "Görüşme başladı. Nasıl yardımcı olabilirim?"
            }
        except Exception as e:
            logger.error(f"Start conversation failed: {e}")
            return {"success": False, "message": f"Görüşme başlatılamadı: {str(e)}"}

    def send_message(self, message: str) -> Dict:
        if not self.agent:
            return {"success": False, "message": "Agent başlatılmamış"}
        
        try:
            response = self.agent.process_message(message)
            return {
                "success": True,
                "response": response,
                "session_id": self.current_session_id,
                "layer": self.agent.current_layer,
                "specialist": self.agent.active_specialist
            }
        except Exception as e:
            logger.error(f"Send message failed: {e}")
            return {"success": False, "message": f"Mesaj işlenemedi: {str(e)}"}

    def end_conversation(self, satisfaction: int = None, notes: str = None) -> Dict:
        if not self.agent:
            return {"success": False, "message": "Agent başlatılmamış"}
        
        try:
            self.agent.end_current_session("resolved", satisfaction, notes)
            report = self.agent.generate_session_report()
            
            self.current_session_id = None
            return {
                "success": True,
                "message": "Görüşme sonlandırıldı",
                "report": report
            }
        except Exception as e:
            logger.error(f"End conversation failed: {e}")
            return {"success": False, "message": f"Görüşme sonlandırılamadı: {str(e)}"}

    def get_customer_info(self, customer_id: str) -> Dict:
        if not self.agent: return {"success": False, "message": "Agent başlatılmamış"}
        try:
            customer_info = self.agent.db.get_customer_info(customer_id)
            if customer_info:
                return {"success": True, "customer": customer_info}
            else:
                return {"success": False, "message": "Müşteri bulunamadı"}
        except Exception as e:
            logger.error(f"Get customer info failed: {e}")
            return {"success": False, "message": f"Müşteri bilgisi alınamadı: {str(e)}"}

    def get_analytics(self, days: int = 30) -> Dict:
        if not self.agent: return {"success": False, "message": "Agent başlatılmamış"}
        try:
            daily_metrics = self.agent.db.get_daily_metrics()
            tool_stats = self.agent.db.get_tool_usage_stats(days)
            db_stats = self.agent.db.get_database_stats()
            
            return {
                "success": True,
                "daily_metrics": daily_metrics,
                "tool_usage": tool_stats,
                "database_stats": db_stats
            }
        except Exception as e:
            logger.error(f"Get analytics failed: {e}")
            return {"success": False, "message": f"Analitik veriler alınamadı: {str(e)}"}


# -------------------------------------------------------------------
# Main Application (Test için güncellendi)
# -------------------------------------------------------------------
def main():
    """Ana uygulama - Test amaçlı."""
    print("🎙️  Katmanlı Çağrı Merkezi Asistanı (Dispatcher + Specialists)")
    # --- DEĞİŞİKLİK: Model sunucu bilgisi güncellendi ---
    print(f"🔗 Model API: LM Studio @ {LM_STUDIO_API_URL}")
    print(f"🤖 Model: {MODEL_NAME}")
    print(f"🗄️  Database: {DATABASE_PATH}")
    print("-" * 80)
    
    print("🔍 Sistem bileşenleri kontrol ediliyor...")
    
    # --- DEĞİŞİKLİK: LM Studio bağlantısı test ediliyor ---
    if not test_llm_connection():
        print(f"❌ LM Studio API'sine ({LM_STUDIO_API_URL}) bağlanılamıyor! Sunucunun çalıştığından ve modelin yüklü olduğundan emin olun.")
        return
    
    try:
        db = CallCenterDatabase(DATABASE_PATH)
        print("✅ Veritabanı bağlantısı başarılı")
    except Exception as e:
        print(f"❌ Veritabanı hatası: {e}")
        return
    
    try:
        agent = EnhancedCallCenterAgent(voice_mode=False)
        print("✅ Agent başarıyla başlatıldı")
        
        print("\n⌨️  Test modu aktif")
        print("Komutlar: 'quit' (çıkış), 'reset' (konuşmayı sıfırla), 'end' (session sonlandır), 'ana menü' (dağıtıcıya dön)")
        
        initial_greeting = "Merhaba, size nasıl yardımcı olabilirim?"
        print(f"\nAsistan [Dispatcher]: {initial_greeting}")
        agent.start_new_session()
        agent.conversation_history.append({"role": "assistant", "content": initial_greeting})


        while True:
            current_layer_info = f"{agent.current_layer.capitalize()}"
            if agent.active_specialist:
                current_layer_info += f" ({agent.active_specialist})"

            user_input = input(f"\nKullanıcı [{current_layer_info}]: ")
            
            if user_input.lower() == 'quit':
                break
            if user_input.lower() == 'end':
                agent.end_current_session()
                print("--- GÖRÜŞME SONLANDIRILDI ---")
                continue
            if user_input.lower() == 'reset':
                agent.reset_conversation()
                print("--- KONUŞMA SIFIRLANDI ---")
                continue

            response = agent.process_message(user_input)
            print(f"\nAsistan [{current_layer_info}]: {response}")

    except Exception as e:
        print(f"\n❌ Ana uygulamada kritik bir hata oluştu: {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    main()