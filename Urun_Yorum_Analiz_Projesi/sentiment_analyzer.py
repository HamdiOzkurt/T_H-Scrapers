import pandas as pd
import torch
import numpy as np
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from PyQt6.QtCore import QObject, pyqtSignal
import os
from datetime import datetime
import re # Gerekli import eklendi

class SentimentAnalyzerWorker(QObject):
    analysis_finished = pyqtSignal(str)  # CSV dosya yolu
    analysis_error = pyqtSignal(str)
    status_update = pyqtSignal(str)
    progress_update = pyqtSignal(int,int)

    def __init__(self, reviews_csv_path):
        super().__init__()
        self.reviews_csv_path = reviews_csv_path
        self._is_running = False
        self.tokenizer = None
        self.model = None

    def stop(self):
        self._is_running = False

    def _load_bert_model(self):
        """BERT Türkçe sentiment model yükle"""
        try:
            self.status_update.emit("🤖 BERT modeli yükleniyor...")
            print("BERT modeli yükleniyor...")
            
            model_name = "savasy/bert-base-turkish-sentiment-cased"
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
            
            self.model.eval()
            
            self.status_update.emit("✅ BERT modeli yüklendi!")
            print("✅ BERT modeli yüklendi!")
            return True
            
        except Exception as e:
            self.status_update.emit(f"❌ BERT model yükleme hatası: {e}")
            return False

    def _predict_sentiment(self, text):
        """Tek bir metin için sentiment tahmini"""
        try:
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                padding=True,
                max_length=512
            )
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
                predicted_class = torch.argmax(predictions, dim=-1).item()
                confidence = torch.max(predictions).item()
            
            sentiment_labels = ["negative", "positive"]
            sentiment = sentiment_labels[predicted_class]
            
            return sentiment, confidence
            
        except Exception as e:
            print(f"Sentiment tahmin hatası: {e}")
            return "neutral", 0.5

    def _convert_turkish_date(self, date_str):
        """
        '16Şubat2025' gibi çeşitli Türkçe tarih formatlarını datetime objesine çevirir.
        Başarısız olursa None (NaT) döndürür.
        """
        if pd.isna(date_str) or not isinstance(date_str, str):
            return None

        month_map = {
            'Ocak': 'January', 'Şubat': 'February', 'Mart': 'March', 'Nisan': 'April',
            'Mayıs': 'May', 'Haziran': 'June', 'Temmuz': 'July', 'Ağustos': 'August',
            'Eylül': 'September', 'Ekim': 'October', 'Kasım': 'November', 'Aralık': 'December'
        }
        
        # Tarih formatını ayırmak için düzenli ifade (regex)
        # Örn: "16Şubat2025" -> ("16", "Şubat", "2025")
        match = re.match(r"(\d+)\s*([a-zA-ZğüşıöçĞÜŞİÖÇ]+)\s*(\d{4})", date_str)
        
        if not match:
            # Eğer yukarıdaki formata uymuyorsa, pandas'ın standart çevirmesini dene
            try:
                return pd.to_datetime(date_str)
            except (ValueError, TypeError):
                return None # Yine başarısız olursa None döndür

        day, month_tr, year = match.groups()
        month_en = month_map.get(month_tr.capitalize())
        
        if not month_en:
            return None # Geçersiz ay adı

        # Standart bir tarih string'i oluştur: "16 February 2025"
        standard_date_str = f"{day} {month_en} {year}"
        
        try:
            return pd.to_datetime(standard_date_str, format='%d %B %Y')
        except (ValueError, TypeError):
            return None

    def run(self):
        """Ana sentiment analizi işlemi"""
        self._is_running = True
        
        try:
            if not self._load_bert_model():
                self.analysis_error.emit("BERT modeli yüklenemedi")
                return
            
            self.status_update.emit("📄 Yorumlar okunuyor...")
            df = pd.read_csv(self.reviews_csv_path)
            
            if 'text' not in df.columns:
                self.analysis_error.emit("CSV dosyasında 'text' sütunu bulunamadı")
                return
            
            total_reviews = len(df)
            self.status_update.emit(f"📊 {total_reviews} yorum için sentiment analizi başlıyor...")
            
            sentiments = []
            confidences = []
            
            for i, text in enumerate(df['text']):
                if not self._is_running:
                    break
                
                progress = int((i + 1) / total_reviews * 100)
                self.progress_update.emit(i + 1, total_reviews)
                self.status_update.emit(f"🔍 Sentiment analizi: {i+1}/{total_reviews}")
                
                sentiment, confidence = self._predict_sentiment(str(text))
                sentiments.append(sentiment)
                confidences.append(confidence)
            
            if not self._is_running:
                return
            
            # Sonuçları DataFrame'e ekle
            df['duygu_tahmini'] = sentiments
            df['duygu_skoru'] = confidences

            # Tarihleri işle
            if 'date' in df.columns:
                self.status_update.emit("📅 Tarihler işleniyor...")
                # Yeni ve sağlam _convert_turkish_date fonksiyonumuzu kullanıyoruz
                df['hesaplanan_tarih'] = df['date'].apply(self._convert_turkish_date)
            else:
                # 'date' sütunu hiç yoksa, bu sütunu boş bırakıyoruz (NaT)
                df['hesaplanan_tarih'] = pd.NaT
            
            # Çıktı dosya adını oluştur
            base_name = os.path.splitext(os.path.basename(self.reviews_csv_path))[0]
            output_path = os.path.join(
                os.path.dirname(self.reviews_csv_path), 
                f"{base_name}_sentiment.csv"
            )
            
            # CSV'ye kaydet
            df.to_csv(output_path, index=False, encoding='utf-8')
            
            self.status_update.emit(f"✅ Sentiment analizi tamamlandı! {len(sentiments)} yorum analiz edildi")
            self.analysis_finished.emit(output_path)
            
        except Exception as e:
            if self._is_running:
                # Hata detayını daha iyi görmek için traceback ekleyelim
                import traceback
                print(f"Sentiment analizi hatası: {e}\n{traceback.format_exc()}")
                self.analysis_error.emit(f"Sentiment analizi hatası: {e}")

# Bu alt kısımdaki fonksiyonu silebiliriz, çünkü ana class içinde her şey yapılıyor.
# İsterseniz kalabilir, programın çalışmasına engel olmaz.
def analyze_sentiment_batch(reviews_df):
    """Batch sentiment analizi için yardımcı fonksiyon (Artık kullanılmıyor)"""
    print("🤖 BERT modeli yükleniyor...")
    model_name = "savasy/bert-base-turkish-sentiment-cased"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name)
    model.eval()
    print("✅ BERT modeli yüklendi!")
    
    sentiments = []
    confidences = []
    
    for i, text in enumerate(reviews_df['text']):
        try:
            inputs = tokenizer(
                str(text),
                return_tensors="pt",
                truncation=True,
                padding=True,
                max_length=512
            )
            
            with torch.no_grad():
                outputs = model(**inputs)
                predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
                predicted_class = torch.argmax(predictions, dim=--1).item()
                confidence = torch.max(predictions).item()
            
            sentiment_labels = ["negative", "positive"]
            sentiment = sentiment_labels[predicted_class]
            
            sentiments.append(sentiment)
            confidences.append(confidence)
            
            if (i + 1) % 10 == 0:
                print(f"✅ {i+1}/{len(reviews_df)} yorum analiz edildi")
                
        except Exception as e:
            print(f"Hata: {e}")
            sentiments.append("neutral")
            confidences.append(0.5)
    
    reviews_df['duygu_tahmini'] = sentiments
    reviews_df['duygu_skoru'] = confidences
    
    return reviews_df