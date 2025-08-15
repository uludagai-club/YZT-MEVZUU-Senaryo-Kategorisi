import streamlit as st
import json
import time
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Optional
from gtts import gTTS
from io import BytesIO
import base64
import html

# Modern ses tanıma için güvenilir bileşen
try:
    from streamlit_mic_recorder import speech_to_text
    MODERN_SPEECH_AVAILABLE = True
except ImportError:
    MODERN_SPEECH_AVAILABLE = False

# Agent kodunu import et (agentG2.py ile aynı dizinde olmalı)
try:
    from agentG2_local_lm_stduio import WebAgentAPI, EnhancedCallCenterAgent, CallCenterDatabase
except ImportError:
    st.error("❌ agentG2_local_lm_stduio.py dosyası bulunamadı! Lütfen aynı dizinde olduğundan emin olun.")
    st.stop()

# Modern Mobile-First Page Configuration
st.set_page_config(
    page_title="📞 AI Çağrı Merkezi",
    page_icon="📞",
    layout="centered",  # Mobil için daha uygun
    initial_sidebar_state="auto",  # Mobilde otomatik gizle
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "📞 AI Çağrı Merkezi - Modern mobil uyumlu tasarım"
    }
)

# Modern Mobil Uyumlu CSS
st.markdown("""
<style>
    /* Global Variables - Beyaz ve Mavi Tema */
    :root {
        --primary-color: #2563eb;
        --primary-light: #60a5fa;
        --primary-dark: #1d4ed8;
        --primary-gradient: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        --secondary-gradient: linear-gradient(135deg, #60a5fa 0%, #2563eb 100%);
        --light-gradient: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        --accent-gradient: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
        --surface-color: #ffffff;
        --surface-light: #f8fafc;
        --background-color: #ffffff;
        --text-primary: #1e293b;
        --text-secondary: #64748b;
        --text-muted: #94a3b8;
        --border-color: #e2e8f0;
        --border-light: #f1f5f9;
        --shadow-sm: 0 1px 2px 0 rgb(59 130 246 / 0.05);
        --shadow-md: 0 4px 6px -1px rgb(59 130 246 / 0.1);
        --shadow-lg: 0 10px 15px -3px rgb(59 130 246 / 0.1);
        --border-radius: 16px;
        --border-radius-sm: 8px;
    }

    /* Main Layout - Mobile First */
    .main .block-container {
        padding: 1rem 0.5rem;
        max-width: 100%;
    }

    .main {
        background: linear-gradient(to bottom, #ffffff 0%, #f8fafc 100%);
        font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }

    /* Mobile Header */
    .mobile-header {
        background: var(--primary-gradient);
        color: white;
        padding: 1.5rem 1rem;
        border-radius: 0 0 24px 24px;
        margin: -1rem -1rem 2rem -1rem;
        text-align: center;
        box-shadow: var(--shadow-lg);
    }

    .mobile-header h1 {
        margin: 0;
        font-size: 1.5rem;
        font-weight: 700;
    }

    .mobile-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
        font-size: 0.9rem;
    }

    /* Chat Container - iPhone Style */
    .chat-container {
        background: var(--surface-color);
        border-radius: var(--border-radius);
        padding: 1rem;
        margin: 1rem 0;
        box-shadow: var(--shadow-md);
        min-height: 400px;
        max-height: 60vh;
        overflow-y: auto;
    }

    /* Chat Messages - WhatsApp Style */
    .chat-message {
        margin: 0.75rem 0;
        padding: 0;
        display: flex;
        flex-direction: column;
        animation: slideIn 0.3s ease-out;
    }

    .user-message {
        align-self: flex-end;
        background: var(--primary-gradient);
        color: white;
        padding: 0.75rem 1rem;
        border-radius: 20px 20px 6px 20px;
        max-width: 85%;
        margin-left: auto;
        word-wrap: break-word;
        box-shadow: var(--shadow-md);
    }

    .assistant-message {
        align-self: flex-start;
        background: var(--surface-color);
        color: var(--text-primary);
        padding: 0.75rem 1rem;
        border-radius: 20px 20px 20px 6px;
        max-width: 85%;
        margin-right: auto;
        border: 2px solid var(--border-light);
        word-wrap: break-word;
        box-shadow: var(--shadow-sm);
    }

    .system-message {
        align-self: center;
        background: var(--accent-gradient);
        color: var(--primary-dark);
        padding: 0.5rem 1rem;
        border-radius: 16px;
        max-width: 90%;
        text-align: center;
        font-size: 0.85rem;
        font-style: italic;
        margin: 1rem auto;
        border: 1px solid var(--border-color);
    }

    .message-meta {
        font-size: 0.7rem;
        color: var(--text-muted);
        margin-top: 0.25rem;
        text-align: right;
    }

    /* Input Area - Modern Mobile */
    .input-container {
        background: var(--surface-color);
        border-radius: var(--border-radius);
        padding: 1rem;
        margin: 1rem 0;
        box-shadow: var(--shadow-md);
        position: sticky;
        bottom: 1rem;
        border: 1px solid var(--border-light);
    }

    .stTextInput > div > div > input {
        border-radius: 24px !important;
        border: 2px solid var(--border-color) !important;
        padding: 0.75rem 1rem !important;
        font-size: 1rem !important;
        background: var(--surface-light) !important;
        transition: all 0.2s ease !important;
    }

    .stTextInput > div > div > input:focus {
        border-color: var(--primary-color) !important;
        box-shadow: 0 0 0 3px rgb(37 99 235 / 0.1) !important;
        background: var(--surface-color) !important;
    }

    /* Buttons - iOS Style */
    .stButton > button {
        background: var(--primary-gradient) !important;
        color: white !important;
        border: none !important;
        border-radius: 24px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        transition: all 0.2s ease !important;
        box-shadow: var(--shadow-sm) !important;
        width: 100% !important;
    }

    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: var(--shadow-md) !important;
    }

    .stButton > button:active {
        transform: translateY(0) !important;
    }

    /* Voice Controls - Floating Action Button Style */
    .voice-controls {
        background: var(--surface-color);
        border-radius: var(--border-radius);
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: var(--shadow-md);
        text-align: center;
        border: 1px solid var(--border-light);
    }

    .voice-button {
        background: var(--secondary-gradient) !important;
        color: white !important;
        border: none !important;
        border-radius: 50% !important;
        width: 80px !important;
        height: 80px !important;
        font-size: 2rem !important;
        margin: 0.5rem !important;
        transition: all 0.3s ease !important;
        box-shadow: var(--shadow-lg) !important;
    }

    .voice-button:hover {
        transform: scale(1.05) !important;
        box-shadow: 0 20px 25px -5px rgb(37 99 235 / 0.2) !important;
        background: var(--primary-gradient) !important;
    }

    /* Status Cards - Material Design */
    .status-card {
        background: var(--surface-color);
        border-radius: var(--border-radius);
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: var(--shadow-sm);
        border-left: 4px solid var(--primary-color);
        border: 1px solid var(--border-light);
    }

    .status-active {
        color: var(--primary-color);
        font-weight: 600;
    }

    .status-inactive {
        color: var(--text-muted);
        font-weight: 600;
    }

    /* Sidebar - Mobile Drawer Style */
    .sidebar .sidebar-content {
        background: var(--surface-color) !important;
        border-radius: 0 var(--border-radius) var(--border-radius) 0 !important;
    }

    /* Metrics - Cards */
    .metric-card {
        background: var(--surface-color);
        border-radius: var(--border-radius);
        padding: 1.5rem;
        margin: 0.5rem 0;
        box-shadow: var(--shadow-sm);
        border: 1px solid var(--border-color);
        text-align: center;
        transition: all 0.2s ease;
    }

    .metric-card:hover {
        box-shadow: var(--shadow-md);
        transform: translateY(-1px);
    }

    /* Animations */
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @keyframes pulse {
        0%, 100% {
            transform: scale(1);
        }
        50% {
            transform: scale(1.05);
        }
    }

    .recording {
        animation: pulse 1.5s infinite;
        background: var(--primary-gradient) !important;
        border-color: var(--primary-light) !important;
    }

    /* Responsive Design */
    @media (max-width: 768px) {
        .main .block-container {
            padding: 0.5rem;
        }
        
        .chat-container {
            margin: 0.5rem 0;
            border-radius: var(--border-radius-sm);
        }
        
        .user-message, .assistant-message {
            max-width: 90%;
        }
        
        .mobile-header {
            margin: -0.5rem -0.5rem 1rem -0.5rem;
        }
    }

    /* Dark mode support - Mavi tonları korunur */
    @media (prefers-color-scheme: dark) {
        :root {
            --surface-color: #1e293b;
            --surface-light: #334155;
            --background-color: #0f172a;
            --text-primary: #f1f5f9;
            --text-secondary: #cbd5e1;
            --text-muted: #94a3b8;
            --border-color: #475569;
            --border-light: #334155;
            --light-gradient: linear-gradient(135deg, #334155 0%, #475569 100%);
            --accent-gradient: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
        }
        
        .main {
            background: linear-gradient(to bottom, #0f172a 0%, #1e293b 100%);
        }
    }

    /* Loading States */
    .loading {
        background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
        background-size: 200% 100%;
        animation: loading 1.5s infinite;
    }

    @keyframes loading {
        0% { background-position: 200% 0; }
        100% { background-position: -200% 0; }
    }

    /* Hide Streamlit default elements for cleaner mobile look */
    .stDeployButton {display: none;}
    header[data-testid="stHeader"] {display: none;}
    div[data-testid="stToolbar"] {display: none;}
    .stActionButton {display: none;}
    
    /* Custom scrollbar */
    .chat-container::-webkit-scrollbar {
        width: 4px;
    }
    
    .chat-container::-webkit-scrollbar-track {
        background: var(--background-color);
    }
    
    .chat-container::-webkit-scrollbar-thumb {
        background: var(--border-color);
        border-radius: 2px;
    }
</style>
""", unsafe_allow_html=True)

# Session state initialization
if 'web_api' not in st.session_state:
    st.session_state.web_api = None
    st.session_state.agent_initialized = False
    st.session_state.conversation_active = False
    st.session_state.chat_history = []
    st.session_state.current_session_id = None
    st.session_state.customer_id = None
    st.session_state.current_layer = "dispatcher"
    st.session_state.current_specialist = None
    st.session_state.voice_mode = False
    st.session_state.is_recording = False
    st.session_state.auto_play_response = True
    st.session_state.pending_audio = None

def initialize_agent():
    """Agent'ı başlatır"""
    if not st.session_state.agent_initialized:
        with st.spinner("🤖 AI Agent başlatılıyor..."):
            st.session_state.web_api = WebAgentAPI()
            result = st.session_state.web_api.initialize_agent()
            
            if result['success']:
                st.session_state.agent_initialized = True
                st.success("✅ AI Agent başarıyla başlatıldı!")
                return True
            else:
                st.error(f"❌ Agent başlatılamadı: {result['message']}")
                return False
    return True

def start_conversation(customer_id=None):
    """Yeni bir konuşma başlatır"""
    if st.session_state.web_api:
        result = st.session_state.web_api.start_conversation(customer_id)
        if result['success']:
            st.session_state.conversation_active = True
            st.session_state.current_session_id = result['session_id']
            st.session_state.customer_id = customer_id
            st.session_state.chat_history = []
            st.session_state.current_layer = "dispatcher"
            st.session_state.current_specialist = None
            
            # İlk karşılama mesajını ekle - system mesajı olarak
            add_message("system", result['message'], "system")
            return True
        else:
            st.error(f"❌ Konuşma başlatılamadı: {result['message']}")
            return False
    return False

def send_message(message):
    """Mesaj gönderir ve yanıtı alır"""
    if st.session_state.web_api and st.session_state.conversation_active:
        # Kullanıcı mesajını ekle
        add_message("user", message)
        
        # AI yanıtını al
        with st.spinner("🤔 AI düşünüyor..."):
            result = st.session_state.web_api.send_message(message)
            
        if result['success']:
            # Layer bilgilerini güncelle
            st.session_state.current_layer = result.get('layer', 'dispatcher')
            st.session_state.current_specialist = result.get('specialist')
            
            # AI yanıtını ekle
            add_message("assistant", result['response'])
            
            # Eğer sesli mod aktifse ve otomatik çalma açıksa, yanıtı sesli olarak çal
            if st.session_state.voice_mode and st.session_state.auto_play_response:
                with st.spinner("🔊 Yanıt seslendirilıyor..."):
                    audio_base64 = text_to_speech(result['response'])
                    if audio_base64:
                        # Session state'e ses dosyasını kaydet ki sayfa yenilendiğinde çalabilsin
                        st.session_state.pending_audio = audio_base64
            
            return True
        else:
            st.error(f"❌ Mesaj gönderilemedi: {result['message']}")
            return False
    return False

def add_message(role, content, msg_type="normal"):
    """Chat geçmişine mesaj ekler"""
    timestamp = datetime.now().strftime("%H:%M")
    
    st.session_state.chat_history.append({
        'role': role,
        'content': content,
        'timestamp': timestamp,
        'type': msg_type
    })

def text_to_speech(text):
    """Metni sesli konuşmaya dönüştürür"""
    try:
        # Metni temizle (HTML etiketlerini kaldır)
        clean_text = html.unescape(text).strip()
        if not clean_text:
            st.warning("⚠️ Boş metin, ses oluşturulamadı")
            return None
            
        # gTTS ile ses oluştur
        tts = gTTS(text=clean_text, lang='tr', slow=False)
        
        # Bellek içi dosya oluştur
        audio_buffer = BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        
        # Base64 encode
        audio_base64 = base64.b64encode(audio_buffer.read()).decode()
        return audio_base64
    except Exception as e:
        st.error(f"Ses oluşturma hatası: {str(e)}")
        return None

def play_audio(audio_base64):
    """Streamlit native audio player kullanarak ses çalar"""
    if audio_base64:
        # Base64'ü bytes'a çevir
        audio_bytes = base64.b64decode(audio_base64)
        
        # Autoplay sorunları için manuel kontrol de ekle
        col1, col2 = st.columns([3, 1])
        with col1:
            # Streamlit'in native audio widget'ını kullan
            st.audio(audio_bytes, format='audio/mp3', autoplay=True)
        with col2:
            if st.button("▶️ Oynat", key=f"play_{hash(audio_base64)}", help="Ses otomatik başlamazsa bu butona tıklayın"):
                st.audio(audio_bytes, format='audio/mp3', autoplay=True)

def create_modern_speech_component():
    """Modern ve güvenilir ses tanıma bileşeni"""
    if not MODERN_SPEECH_AVAILABLE:
        st.error("❌ st-mic-recorder yüklü değil!")
        return None
    
    voice_text = speech_to_text(
        language='tr-TR',
        start_prompt="🎤 Konuşmaya Başla",
        stop_prompt="⏹️ Durdur", 
        just_once=True,
        use_container_width=False,
        key="voice_input"
    )
    
    return voice_text

def create_speech_recognition_component():
    """Tarayıcı tabanlı ses tanıma bileşeni oluşturur (fallback)"""
    speech_js = """
    <div style="text-align: center; margin: 10px 0;">
        <button id="startRecord" onclick="startRecording()" 
                style="background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%); 
                       color: white; border: none; padding: 12px 24px; 
                       border-radius: 25px; font-weight: 500; cursor: pointer; 
                       margin: 5px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
            🎤 Konuşmaya Başla
        </button>
        <button id="stopRecord" onclick="stopRecording()" disabled
                style="background: linear-gradient(135deg, #95e1d3 0%, #fce38a 100%); 
                       color: #333; border: none; padding: 12px 24px; 
                       border-radius: 25px; font-weight: 500; cursor: pointer; 
                       margin: 5px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
            ⏹️ Durdur
        </button>
    </div>
    <div id="recordingStatus" style="text-align: center; margin: 10px 0; font-weight: 500;"></div>
    
    <script>
    let recognition;
    let isRecording = false;
    
    function startRecording() {
        console.log('startRecording çağrıldı');
        
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
            recognition.lang = 'tr-TR';
            recognition.continuous = false;
            recognition.interimResults = false;
            
            console.log('Speech recognition oluşturuldu, dil: tr-TR');
            
            recognition.onstart = function() {
                console.log('Kayıt başladı');
                isRecording = true;
                document.getElementById('startRecord').disabled = true;
                document.getElementById('stopRecord').disabled = false;
                document.getElementById('recordingStatus').innerHTML = 
                    '<span style="color: #ff6b6b;">🔴 Kaydediliyor... Lütfen konuşun</span>';
            };
            
            recognition.onresult = function(event) {
                const transcript = event.results[0][0].transcript;
                document.getElementById('recordingStatus').innerHTML = 
                    '<span style="color: #28a745;">✅ Kaydedildi: "' + transcript + '"</span>';
                
                // Streamlit'e sonucu gönder - form içindeki input için güncellenmiş selector'lar
                let textInput = parent.document.querySelector('form input[placeholder*="yazın"]') ||
                               parent.document.querySelector('form input[type="text"]') ||
                               parent.document.querySelector('input[placeholder*="yazın"]') ||
                               parent.document.querySelector('input[type="text"]');
                
                if (textInput) {
                    textInput.value = transcript;
                    textInput.dispatchEvent(new Event('input', { bubbles: true }));
                    textInput.dispatchEvent(new Event('change', { bubbles: true }));
                    
                                         // Form submit button'a tıkla - güvenilir selector
                     setTimeout(() => {
                         const sendButton = parent.document.querySelector('form button[type="submit"]') ||
                                          parent.document.querySelector('button[type="submit"]');
                         if (sendButton) {
                             sendButton.click();
                         } else {
                             console.log('Send button bulunamadı - form yapısı değişmiş olabilir');
                         }
                     }, 200);
                } else {
                    console.log('Form text input bulunamadı');
                }
                stopRecording();
            };
            
            recognition.onerror = function(event) {
                console.log('Speech recognition hatası:', event.error);
                let errorMessage = '';
                switch(event.error) {
                    case 'not-allowed':
                        errorMessage = 'Mikrofon izni verilmedi';
                        break;
                    case 'no-speech':
                        errorMessage = 'Ses algılanamadı';
                        break;
                    case 'network':
                        errorMessage = 'Ağ bağlantısı hatası';
                        break;
                    case 'service-not-allowed':
                        errorMessage = 'Servis izni yok';
                        break;
                    default:
                        errorMessage = event.error;
                }
                document.getElementById('recordingStatus').innerHTML = 
                    '<span style="color: #dc3545;">❌ Hata: ' + errorMessage + '</span>';
                stopRecording();
            };
            
            recognition.onend = function() {
                stopRecording();
            };
            
            try {
                recognition.start();
                console.log('Recognition başlatıldı');
            } catch (error) {
                console.log('Recognition başlatma hatası:', error);
                document.getElementById('recordingStatus').innerHTML = 
                    '<span style="color: #dc3545;">❌ Başlatma hatası: ' + error.message + '</span>';
            }
        } else {
            console.log('Speech recognition desteklenmiyor');
            alert('Tarayıcınız ses tanımayı desteklemiyor! Chrome tarayıcısı kullanın.');
        }
    }
    
    function stopRecording() {
        if (recognition && isRecording) {
            recognition.stop();
        }
        isRecording = false;
        document.getElementById('startRecord').disabled = false;
        document.getElementById('stopRecord').disabled = true;
        
        if (document.getElementById('recordingStatus').innerHTML.indexOf('✅') === -1) {
            document.getElementById('recordingStatus').innerHTML = 
                '<span style="color: #6c757d;">⏹️ Kayıt durduruldu</span>';
        }
    }
    </script>
    """
    
    return speech_js

def end_conversation():
    """Konuşmayı sonlandırır"""
    if st.session_state.web_api and st.session_state.conversation_active:
        satisfaction = st.session_state.get('satisfaction_rating', None)
        notes = st.session_state.get('session_notes', None)
        
        result = st.session_state.web_api.end_conversation(satisfaction, notes)
        
        if result['success']:
            st.session_state.conversation_active = False
            st.session_state.current_session_id = None
            st.session_state.customer_id = None
            add_message("system", "Görüşme sonlandırıldı", "system")
            return result.get('report', {})
        else:
            st.error(f"❌ Konuşma sonlandırılamadı: {result['message']}")
    return None

def display_chat():
    """Modern mobil uyumlu chat arayüzü"""
    # Chat container with modern styling
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    # Chat messages
    for msg in st.session_state.chat_history:
        timestamp = msg['timestamp']
        content = msg['content']
        role = msg['role']
        msg_type = msg.get('type', 'normal')
        
        if role == "user":
            st.markdown(f"""
            <div class="chat-message">
                <div class="user-message">
                    {content}
                    <div class="message-meta">{timestamp}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        elif role == "assistant":
            # Specialist info for better UX
            specialist_emoji = ""
            if st.session_state.current_layer == "specialist" and st.session_state.current_specialist:
                specialist_emojis = {
                    "billing": "💰",
                    "package_management": "📦", 
                    "user_info": "👤",
                    "general_inquiry": "💬"
                }
                specialist_emoji = specialist_emojis.get(st.session_state.current_specialist, "🤖")
            else:
                specialist_emoji = "🤖"
            
            st.markdown(f"""
            <div class="chat-message">
                <div class="assistant-message">
                    <div style="display: flex; align-items: center; margin-bottom: 0.25rem;">
                        <span style="margin-right: 0.5rem;">{specialist_emoji}</span>
                        <small style="color: var(--text-secondary); font-weight: 500;">AI Asistan</small>
                    </div>
                    {content}
                    <div class="message-meta">{timestamp}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        elif role == "system":
            st.markdown(f"""
            <div class="chat-message">
                <div class="system-message">
                    ℹ️ {content}
                    <div class="message-meta" style="text-align: center; color: rgba(255,255,255,0.8);">{timestamp}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def main():
    # Modern Mobile Header
    st.markdown("""
    <div class="mobile-header">
        <h1>📞 AI Çağrı Merkezi</h1>
        <p>Sesli sohbet destekli yapay zeka asistanı</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Modern Sidebar
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0;">
            <h2 style="color: var(--primary-color); margin: 0;">🎛️ Kontrol</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Kullanılan Model Bilgisi
        st.markdown("""
        <div class="status-card" style="background: var(--accent-gradient); color: var(--primary-dark); margin-bottom: 1rem;">
            <div style="text-align: center;">
                <strong>🤖 Kullanılan Model</strong><br/>
                <code style="background: rgba(255,255,255,0.8); padding: 0.25rem 0.5rem; border-radius: 6px; font-size: 0.85rem;">gemma-3-12b-it</code>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Agent durumu
        if st.session_state.agent_initialized:
            st.markdown('<p class="status-active">🟢 Agent Aktif</p>', unsafe_allow_html=True)
        else:
            st.markdown('<p class="status-inactive">🔴 Agent Pasif</p>', unsafe_allow_html=True)
        
        st.divider()
        
        # Agent başlatma
        if not st.session_state.agent_initialized:
            if st.button("🚀 Agent'ı Başlat", type="primary"):
                initialize_agent()
        
        # Konuşma kontrolları
        if st.session_state.agent_initialized:
            st.subheader("💬 Konuşma Yönetimi")
            
            # Müşteri ID girişi
            customer_id = st.text_input("👤 Müşteri ID", placeholder="Örn: 1001, 1002, 1003")
            
            if not st.session_state.conversation_active:
                if st.button("🆕 Yeni Konuşma Başlat", type="primary"):
                    start_conversation(customer_id if customer_id else None)
            else:
                st.success(f"📱 Aktif Konuşma: {st.session_state.current_session_id}")
                if st.session_state.customer_id:
                    st.info(f"👤 Müşteri: {st.session_state.customer_id}")
                
                # Layer bilgisi
                layer_display = st.session_state.current_layer.title()
                if st.session_state.current_specialist:
                    specialist_names = {
                        "billing": "Fatura Uzmanı",
                        "package_management": "Paket Uzmanı",
                        "user_info": "Bilgi Uzmanı",
                        "general_inquiry": "Genel Asistan"
                    }
                    layer_display = specialist_names.get(st.session_state.current_specialist, "Uzman")
                
                st.markdown(f'<div class="layer-indicator">🎯 {layer_display}</div>', unsafe_allow_html=True)
                
                if st.button("🏁 Konuşmayı Sonlandır", type="secondary"):
                    report = end_conversation()
                    if report:
                        st.success("✅ Konuşma başarıyla sonlandırıldı")
        
        st.divider()
        
        # Sesli sohbet kontrolleri
        if st.session_state.conversation_active:
            st.subheader("🎤 Sesli Sohbet")
            
            # Sesli mod toggle
            voice_mode = st.toggle(
                "Sesli Mod", 
                value=st.session_state.voice_mode,
                help="Sesli konuşma modunu açar/kapatır"
            )
            st.session_state.voice_mode = voice_mode
            
            if voice_mode:
                # Otomatik çalma ayarı
                auto_play = st.checkbox(
                    "Yanıtları otomatik seslendir", 
                    value=st.session_state.auto_play_response,
                    help="AI yanıtlarını otomatik olarak sesli çalar"
                )
                st.session_state.auto_play_response = auto_play
                
                # Durum göstergesi
                if st.session_state.voice_mode:
                    st.success("🟢 Sesli mod aktif")
                    st.info("💡 Mikrofon butonuna tıklayarak konuşabilirsiniz")
            else:
                st.info("🔇 Sadece metin modu aktif")
        
        st.divider()
        
        # Hızlı eylemler
        if st.session_state.conversation_active:
            st.subheader("⚡ Hızlı Eylemler")
            
            quick_actions = [
                "Müşteri bilgilerimi göster",
                "Mevcut paketleri listele", 
                "Fatura bilgilerimi göster",
                "Kullanım istatistiklerimi göster",
                "Ana menüye dön"
            ]
            
            for action in quick_actions:
                if st.button(action, key=f"quick_{action}"):
                    send_message(action)
        
        st.divider()
        
        # Sistem durumu
        st.subheader("🔍 Sistem Durumu")
        try:
            import requests
            # API sağlık kontrolü
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                st.success("🟢 Backend API Aktif")
            else:
                st.warning("🟡 Backend API Uyarı")
        except:
            st.error("🔴 Backend API Pasif")
        
        # Database kontrolü
        try:
            db = CallCenterDatabase("call_center.db")
            st.success("🟢 Veritabanı Aktif")
        except:
            st.error("🔴 Veritabanı Hatası")

    # Ana içerik alanı
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Chat alanı
        st.subheader("💬 Konuşma")
        
        if st.session_state.conversation_active:
            # Chat geçmişi
            chat_container = st.container()
            with chat_container:
                display_chat()
            
            # Modern Voice Input Section
            if st.session_state.voice_mode:
                st.markdown("""
                <div class="voice-controls">
                    <h3 style="text-align: center; color: var(--text-primary); margin-bottom: 1rem;">🎤 Sesli Girdi</h3>
                </div>
                """, unsafe_allow_html=True)
                
                # Modern speech component kullan (güvenilir)
                if MODERN_SPEECH_AVAILABLE:
                    voice_text = create_modern_speech_component()
                    if voice_text:
                        st.markdown(f"""
                        <div class="status-card" style="background: var(--secondary-gradient); color: white;">
                            <strong>✅ Ses Algılandı:</strong><br/>"{voice_text}"
                        </div>
                        """, unsafe_allow_html=True)
                        send_message(voice_text)
                        st.rerun()
                else:
                    # Fallback: JavaScript tabanlı (kırılgan)
                    st.markdown("""
                    <div class="status-card" style="background: var(--accent-gradient); color: var(--primary-dark);">
                        ⚠️ Modern ses tanıma yok, JavaScript fallback kullanılıyor
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown(create_speech_recognition_component(), unsafe_allow_html=True)
            
            # Modern Message Input
            st.markdown("""
            <div class="input-container">
            """, unsafe_allow_html=True)
            
            # Form kullanarak input temizleme sorununu çöz
            with st.form(key="message_form", clear_on_submit=True):
                user_message = st.text_input(
                    "Mesajınızı yazın...", 
                    placeholder="💬 Merhaba, size nasıl yardımcı olabilirim?",
                    label_visibility="collapsed"
                )
                
                send_clicked = st.form_submit_button("📤 Gönder", type="primary", use_container_width=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Mesaj gönderme
            if user_message and send_clicked:
                send_message(user_message)
                st.rerun()
        
        else:
            st.markdown("""
            <div class="alert-info">
                <h4>👋 Hoş geldiniz!</h4>
                <p>AI Çağrı Merkezi Asistanı'na hoş geldiniz. Başlamak için:</p>
                <ol>
                    <li>Soldaki panelden <strong>"Agent'ı Başlat"</strong> butonuna tıklayın</li>
                    <li>Müşteri ID'si girin (isteğe bağlı)</li>
                    <li><strong>"Yeni Konuşma Başlat"</strong> butonuna tıklayın</li>
                </ol>
                <p><strong>Test Müşteri ID'leri:</strong> 1001, 1002, 1003</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        # Bilgi paneli
        st.subheader("📊 Bilgi Paneli")
        
        if st.session_state.conversation_active:
            # Konuşma istatistikleri
            total_messages = len(st.session_state.chat_history)
            user_messages = len([m for m in st.session_state.chat_history if m['role'] == 'user'])
            assistant_messages = len([m for m in st.session_state.chat_history if m['role'] == 'assistant'])
            
            st.metric("💬 Toplam Mesaj", total_messages)
            st.metric("👤 Müşteri Mesajları", user_messages)
            st.metric("🤖 AI Yanıtları", assistant_messages)
            
            # Sesli mod durumu
            if st.session_state.voice_mode:
                st.metric("🎤 Sesli Mod", "Aktif")
            else:
                st.metric("🔇 Sesli Mod", "Pasif")
            
            st.divider()
            
            # Mevcut katman bilgisi
            st.subheader("🎯 Aktif Katman")
            if st.session_state.current_layer == "dispatcher":
                st.info("🔀 **Yönlendirme Katmanı**\nMüşteri talebi analiz ediliyor ve uygun uzmana yönlendiriliyor.")
            elif st.session_state.current_layer == "specialist":
                specialist_info = {
                    "billing": ("💰", "Fatura Uzmanı", "Fatura sorguları ve ödemeleri"),
                    "package_management": ("📦", "Paket Uzmanı", "Paket değişiklikleri ve karşılaştırma"),
                    "user_info": ("👤", "Bilgi Uzmanı", "Kullanıcı bilgileri ve istatistikler"),
                    "general_inquiry": ("💬", "Genel Asistan", "Genel sorular ve yönlendirme")
                }
                
                if st.session_state.current_specialist in specialist_info:
                    icon, name, desc = specialist_info[st.session_state.current_specialist]
                    st.success(f"{icon} **{name}**\n{desc}")
            
            st.divider()
            
            # Yardım
            st.subheader("❓ Yardım")
            st.markdown("""
            **📝 Metin Komutları:**
            - "Müşteri bilgilerimi göster"
            - "Faturamı ödemek istiyorum"
            - "Yeni paketleri göster"
            - "Kullanım istatistiklerimi göster"
            - "Ana menü" (geri dönmek için)
            
            **🎤 Sesli Sohbet:**
            1. Sesli Mod'u açın
            2. "Konuşmaya Başla" butonuna tıklayın
            3. Türkçe konuşun
            4. AI yanıtını hem metin hem ses olarak alın
            
            **💡 İpuçları:**
            - Mikrofon izni vermeyi unutmayın
            - Sessiz bir ortamda konuşun
            - Net ve anlaşılır konuşun
            """)
        
        else:
            st.info("🔄 Konuşma başlatıldığında burada detaylar görünecek.")
    
    # Bekleyen ses dosyası varsa çal (sayfa yenilendikten sonra)
    if st.session_state.get('pending_audio'):
        # Ses oynatıcısını sidebar'da göster - daha temiz görünüm
        with st.sidebar:
            st.markdown("---")
            current_time = datetime.now().strftime("%H:%M:%S")
            st.markdown(f"**🔊 AI Yanıtı ({current_time})**")
            play_audio(st.session_state.pending_audio)
        st.session_state.pending_audio = None

if __name__ == "__main__":
    main()