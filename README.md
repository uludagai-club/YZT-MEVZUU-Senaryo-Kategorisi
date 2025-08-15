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
...

[#LM Studio Kurulumu ve Yapılandırması
Bu bölüm, gemma-3-12b-it modelini kullanarak LM Studio'yu yerel bir sunucuda kurma ve yapılandırma adımlarını açıklamaktadır.
Gereksinimler

#İşletim sisteminizle uyumlu LM Studio yazılımı
gemma-3-12b-it modeli
Yeterli donanım (önerilen: en az 16 GB RAM ve GPU desteği)
İnternet bağlantısı (model indirme için)

Kurulum Adımları
1. LM Studio Kurulumu

İndirme: LM Studio resmi web sitesinden işletim sisteminize uygun sürümü indirin.
Kurulum: İndirilen dosyayı çalıştırın ve kurulum sihirbazındaki talimatları izleyerek kurulumu tamamlayın.

2. Model İndirme

LM Studio uygulamasını başlatın.
Model kütüphanesinde arama çubuğuna gemma-3-12b-it yazın.
Modeli seçin ve İndir butonuna tıklayın. İndirme tamamlandıktan sonra model otomatik olarak kullanıma hazır olacaktır.

3. Yerel Sunucuyu Başlatma

LM Studio arayüzünden gemma-3-12b-it modelini seçin.
Start Server butonuna tıklayarak yerel sunucuyu başlatın.
Sunucu varsayılan olarak http://127.0.0.1:1234 adresinde çalışır.

4. API Yapılandırması
Uygulamanızı LM Studio API ile entegre etmek için aşağıdaki yapılandırma ayarlarını kullanın:
LM_STUDIO_API_URL = "http://127.0.0.1:1234/v1/chat/completions"
MODEL_NAME = "gemma-3-12b-it"
](https://github.com/uludagai-club/YZT-MEVZUU-Senaryo-Kategorisi-BilisimVadisi2025-)

LM_STUDIO_API_URL: Yerel sunucunun API uç noktası (http://127.0.0.1:1234/v1/chat/completions).
MODEL_NAME: Kullanılacak modelin adı (gemma-3-12b-it).

5. Test Etme

LM Studio sunucusunun çalıştığından emin olun.
Bir API istemcisi (ör. Postman veya cURL) kullanarak LM_STUDIO_API_URL adresine test isteği gönderin.
Yanıtın doğru şekilde döndüğünü doğrulayın.

Önemli Notlar

Modelin düzgün çalışması için yeterli donanım kaynaklarına sahip olduğunuzdan emin olun.
Varsayılan port (1234) başka bir uygulama ile çakışırsa, LM Studio ayarlarından portu değiştirin.
Daha fazla bilgi ve destek için LM Studio dokümantasyonuna göz atın.

Hata Ayıklama

Sunucu çalışmıyor: LM Studio'nun açık olduğundan ve doğru modelin seçildiğinden emin olun.
Bağlantı hatası: LM_STUDIO_API_URL adresini ve port numarasını kontrol edin.
Model yüklenmiyor: Modelin tamamen indirildiğini ve dosya bütünlüğünü doğrulayın.





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
