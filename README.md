#BilisimVadisi2025

#turkiyeacikkaynakplatformu

https://github.com/tracikkaynak

# 📞 AI Çağrı Merkezi

Modern, sesli sohbet destekli yapay zeka tabanlı çağrı merkezi uygulaması. Türkçe dil desteği ile müşteri hizmetlerini otomatikleştiren gelişmiş platform.

## 🚀 Özellikler

### 🤖 AI Destekli Çağrı Yönetimi
- **Akıllı yönlendirme sistemi** (dispatcher(router) layer)
- **Özel uzman katmanları** (fatura ve ödemeler uzmanı, paket bilgileri uzmanı, kullanıcı bilgileri uzmanı, genel-teknik uzman)
- **Çok katmanlı AI asistan** mimarisi
- **Gerçek zamanlı mesaj işleme**

### 🎤 Sesli Sohbet Teknolojisi
- **Türkçe Ses Tanıma** (Speech-to-Text)
- **Türkçe Ses Sentezi** (Text-to-Speech)
- **Web tabanlı mikrofon entegrasyonu**
- **Otomatik ses çalma** desteği

### 🏢 Müşteri Yönetimi
- **Kapsamlı müşteri profilleri**
- **Paket ve abonelik yönetimi**
- **Fatura takibi ve ödeme sistemi**
- **Kullanım istatistikleri**

### 📊 Analytics & Raporlama
- **Günlük performance metrikleri**
- **Araç kullanım istatistikleri**
- **Müşteri memnuniyet takibi**
- **Sistem sağlık kontrolleri**

### 🎨 Modern UI/UX
- **Mobil uyumlu tasarım**
- **WhatsApp benzeri chat arayüzü**
- **iOS tarzı butonlar ve animasyonlar**
- **Responsive layout**

## 🛠️ Teknoloji Stack

- **Frontend:** Streamlit + Modern CSS
- **Backend:** FastAPI + Uvicorn
- **Database:** SQLite3
- **AI/LLM:** Configurable (Gemma)
- **Speech:** gTTS + Web Speech API
- **Charts:** Plotly
- **Data:** Pandas + NumPy

## 📦 Kurulum

### 1. Repository'yi Klonlayın
```bash
git clone https://github.com/[your-username]/YZT-MEVZUU-Senaryo-Kategorisi.git

```

### 2. Sanal Ortam Oluşturun
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Bağımlılıkları Yükleyin
```bash
pip install -r requirements.txt
```

### 4. (Opsiyonel) Sesli Sohbet için Ek Paket
```bash
pip install streamlit-mic-recorder
```

## 🚀 Çalıştırma

### 1. Backend API'yi Başlatın
```bash
python app_with_database.py
```
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### 2. Streamlit Uygulamasını Başlatın
```bash
streamlit run streamlitApp.py
```
- Web UI: http://localhost:8501

## 💡 Kullanım

### İlk Başlatma
1. **Agent'ı Başlat** butonuna tıklayın
2. **Müşteri ID** girin (Test: 1001, 1002, 1003,1004,1005)
3. **Yeni Konuşma Başlat** butonuna tıklayın

### Metin Sohbeti
- Alt kısımdaki metin kutusuna yazdığınız mesajları gönderin
- AI asistan müşteri talebinizi analiz edip uygun uzmana yönlendirir

### Sesli Sohbet
1. **Sesli Mod** toggle'ını açın
2. **"🎤 Konuşmaya Başla"** butonuna tıklayın
3. Türkçe konuşun, sistem otomatik olarak tanıyacak
4. AI yanıtı hem metin hem ses olarak gelir

### Hızlı Komutlar
- "Müşteri bilgilerimi göster"
- "Faturamı ödemek istiyorum" 
- "Yeni paketleri göster"
- "Kullanım istatistiklerimi göster"
- "Ana menü" (geri dönmek için)

## 📁 Proje Yapısı

```

├── streamlitApp.py          # Ana Streamlit uygulaması
├── app_with_database.py     # FastAPI backend
├── database.py              # SQLite veritabanı yönetimi
├── services.py              # Business logic katmanları
├── agentG2_local_lm_stduio.py  # AI agent (local)
├── call_center.db           # SQLite veritabanı
├── temp_audio/              # Geçici ses dosyaları
├── requirements.txt         # Python bağımlılıkları
├── README.md               # Bu dosya
└── SPEECH_INTEGRATION_README.md  # Sesli sohbet dokümantasyonu
```

## 🗄️ Veritabanı Şeması

### Ana Tablolar
- **customers** - Müşteri bilgileri
- **packages** - Paket tanımları  
- **customer_subscriptions** - Müşteri abonelikleri
- **bills** - Fatura kayıtları
- **call_sessions** - Görüşme oturumları
- **call_messages** - Sohbet mesajları

### Analytics Tabloları
- **tool_usage_logs** - Araç kullanım logları
- **error_logs** - Hata kayıtları
- **usage_stats** - Kullanım istatistikleri

## 🔧 Konfigürasyon

### AI Model Ayarları
`agentG2_local_lm_stduio.py` dosyasında:
- Model seçimi (Gemma)
- API anahtarları
- Temperature ve diğer parametreler

### Veritabanı Ayarları
`database.py` dosyasında:
- SQLite dosya yolu
- İlk veriler (test müşterileri)
- Tablo şemaları

### UI Ayarları
`streamlitApp.py` dosyasında:
- Tema renkleri (CSS variables)
- Sayfa layoutu
- Mobil responsive ayarları

  ------
  LM Studio Kurulumu ve Yapılandırması
Bu bölümde, LM Studio'nun yerel bir sunucuda çalışacak şekilde nasıl kurulacağı ve gemma-3-12b-it modelinin nasıl indirilip yapılandırılacağı açıklanmaktadır.
Adım 1: LM Studio'yu İndirin ve Kurun

LM Studio'yu İndirin: Resmi LM Studio web sitesinden (https://lmstudio.ai/) işletim sisteminize uygun sürümü indirin.
Kurulumu Gerçekleştirin: İndirilen dosyayı çalıştırarak kurulum sihirbazını takip edin ve LM Studio'yu bilgisayarınıza kurun.

Adım 2: Modeli İndirin

LM Studio uygulamasını başlatın.
Model kütüphanesinde gemma-3-12b-it modelini arayın.
Modeli seçin ve indirin. İndirme işlemi tamamlandıktan sonra model otomatik olarak LM Studio tarafından kullanılabilir hale gelecektir.

Adım 3: Yerel Sunucuyu Başlatın

LM Studio arayüzünde, indirilen gemma-3-12b-it modelini seçin.
Yerel sunucuyu başlatmak için "Start Server" seçeneğini tıklayın.
Sunucu varsayılan olarak http://127.0.0.1:1234 adresinde çalışacaktır.

Adım 4: API Yapılandırması
Aşağıdaki ayarları kullanarak uygulamanızı LM Studio API ile entegre edin:
LM_STUDIO_API_URL = "http://127.0.0.1:1234/v1/chat/completions"
MODEL_NAME = "gemma-3-12b-it"


LM_STUDIO_API_URL: Yerel sunucunun API uç noktası. Varsayılan olarak http://127.0.0.1:1234/v1/chat/completions kullanılır.
MODEL_NAME: Kullanılacak modelin adı, bu durumda gemma-3-12b-it.

Adım 5: Test Etme

LM Studio sunucusunun çalıştığından emin olun.
API istemcinizi kullanarak LM_STUDIO_API_URL adresine bir test isteği gönderin.
Yanıtın doğru şekilde döndüğünü kontrol edin.

Notlar

Modelin çalışması için yeterli donanım kaynaklarına (RAM, GPU, vb.) sahip olduğunuzdan emin olun.
Yerel sunucunun port numarası (1234) farklı bir uygulamayla çakışırsa, LM Studio ayarlarından portu değiştirebilirsiniz.
Daha fazla bilgi için LM Studio'nun resmi dokümantasyonuna göz atın: https://lmstudio.ai/docs.


## 🎯 Test Verileri

### Test Müşterileri
- **1001** - Ali Veli (Premium paket, 243.45₺ bakiye)
- **1002** - Ayşe Demir (Standart paket, 0₺ bakiye)  
- **1003** - Mehmet Can (Gold paket, 1240₺ bakiye)
- **1004** - Elif Yılmaz (Silver paket, 5455.75₺ bakiye)
- **1005** - Berke Kara (Bronze paket, 5415.20₺ bakiye)

### Paket Seçenekleri
- **Bronze** (25₺) - 50 DK + 10 GB
- **Silver** (50₺) - 200 DK + 50 GB  
- **Gold** (100₺) - Limitsiz + 100 GB
- **Standart** (75₺) - 100 DK + 50 GB
- **Premium** (150₺) - Limitsiz + Limitsiz

## 📱 Tarayıcı Uyumluluğu

### Önerilen Tarayıcılar
- **Chrome/Chromium** (en iyi performans)
- **Firefox** (iyi destek)
- **Safari** (sınırlı sesli özellik)

### Sesli Sohbet Gereksinimleri
- Modern tarayıcı
- Mikrofon izni
- İnternet bağlantısı (gTTS için)
- HTTPS (production için)

## 🚨 Sorun Giderme

### Backend Bağlantı Sorunu
```bash
# API'nin çalıştığını kontrol edin
curl http://localhost:8000/health
```

### Sesli Sohbet Çalışmıyor
1. Tarayıcı mikrofon izni kontrol edin
2. Chrome kullanmayı deneyin
3. Sistem ses ayarlarını kontrol edin

### Veritabanı Hataları
```bash
# Veritabanını yeniden oluşturun
rm call_center.db
python database.py
```

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit yapın (`git commit -m 'Add amazing feature'`)
4. Push yapın (`git push origin feature/amazing-feature`)
5. Pull Request oluşturun

## 📄 Lisans

Bu proje [MIT Lisansı](LICENSE) altında lisanslanmıştır.

## 📞 İletişim

- **Geliştirici:** [Your Name]
- **Email:** [your.email@example.com]
- **GitHub:** [https://github.com/your-username](https://github.com/your-username)

## 🙏 Teşekkürler

- **Streamlit** - Modern web UI framework
- **FastAPI** - High-performance web framework  
- **Google TTS** - Türkçe ses sentezi
- **Web Speech API** - Tarayıcı ses tanıma

---
