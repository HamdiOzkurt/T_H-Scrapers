# config.py

# --- Dosya ve Klasör Ayarları ---
OUTPUT_DIR = "output"
COMMENTS_FILE_TEMPLATE = "{product_id}_reviews.csv"
SENTIMENT_FILE_TEMPLATE = "{product_id}_reviews_sentiment.csv"
CATEGORIZATION_FILE_TEMPLATE = "{product_id}_categorization.csv"
REPORT_FILE_TEMPLATE = "{product_id}_analiz_raporu.docx"

# --- Yapay Zeka Modeli Ayarları ---
# Local Ollama modelini kullan (gemma3:4b)
DEFAULT_OLLAMA_MODEL = "gemma3:4b"
DEFAULT_BATCH_SIZE = 3  # Aynı anda Ollama'ya gönderilecek yorum sayısı (daha küçük model için)

# BERT Duygu Analizi için kullanılacak model
BERT_SENTIMENT_MODEL = "savasy/bert-base-turkish-sentiment-cased"

# --- Web Scraper Ayarları (EN ÖNEMLİ KISIM) ---
# Trendyol'un web sitesi yapısı değişirse bu seçicilerin güncellenmesi gerekir.
# Güncellenmiş selectors (2024)
TRENDYOL_SELECTORS = {
    "review_button": "button.reviews-summary-reviews-detail, div.pr-in-review-summary-container, div[class*='review-summary']",  # Değerlendirme butonları
    "review_card": "div.rnr-com-w, div.comment-container, div[class*='review-card'], div.pr-review-item",  # Yorum kartları
    "review_text": ".comment, .comment-text, .review-text, .rnr-com-tx, div[class*='content']",  # Yorum metni
    "rating": ".full, .rating-line-full, span[class*='rating'], div[class*='star']",  # Yıldız değerlendirmesi
    "author_name": "span.user-name, .rnr-com-usr, span[class*='user']",  # Kullanıcı adı
    "review_date": "span.comment-date, .rnr-com-dt, span[class*='date']",  # Yorum tarihi
    "product_title": "h1.pr-new-br, h1.detail-name, h1[class*='title']", # Ürün başlığı
    "review_container": "div.reviews, div.pr-in-w, div.comments-container",  # Yorumların bulunduğu ana konteyner
    "load_more_button": "button.load-more, button.pr-see-more, button[class*='more']",  # Daha fazla yorum yükle butonu
    "review_section": ".pr-in-review-cont, .reviews-detail, div[id='reviews']"  # Yorum bölümü
}

# --- Arayüz (GUI) Stil Dosyası ---
# Buraya daha önce size verdiğim uzun QSS_STYLE içeriğini yapıştırabilirsiniz.
# Şimdilik daha sade bir stil ekliyorum.
QSS_STYLE = """
    QWidget {
        background-color: #f0f0f0;
        font-family: Arial;
    }
    QPushButton {
        background-color: #007bff;
        color: white;
        border-radius: 5px;
        padding: 8px;
        font-size: 14px;
    }
    QPushButton:hover {
        background-color: #0056b3;
    }
    QPushButton:disabled {
        background-color: #cccccc;
    }
    QLineEdit, QSpinBox {
        padding: 5px;
        border: 1px solid #cccccc;
        border-radius: 5px;
        background-color: white;
    }
    QLabel {
        font-size: 14px;
    }
    QGroupBox {
        font-weight: bold;
        border: 1px solid #cccccc;
        border-radius: 5px;
        margin-top: 10px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 3px;
    }
    QProgressBar {
        text-align: center;
    }
"""