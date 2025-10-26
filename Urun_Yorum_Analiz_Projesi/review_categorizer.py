import os
import pandas as pd
import re
import traceback
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from config import DEFAULT_OLLAMA_MODEL

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

class ReviewCategorizerWorker(QObject):
    progress_updated = pyqtSignal(int, int)
    categorization_finished = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    status_message = pyqtSignal(str)

    def __init__(self, input_csv_path, output_csv_path, categories_data, ollama_model=DEFAULT_OLLAMA_MODEL):
        super().__init__()
        self.input_csv_path = input_csv_path
        self.output_csv_path = output_csv_path
        self.categories = categories_data
        self.ollama_model = ollama_model
        self._is_running = True # Başlangıçta çalışıyor olarak ayarla
        self.client = None

    def stop(self):
        self._is_running = False

    def _initialize_ollama_client(self):
        if not OLLAMA_AVAILABLE:
            raise Exception("Ollama kütüphanesi yüklü değil. 'pip install ollama' ile yükleyin.")
        try:
            # ollama.Client() kullanmak yerine doğrudan ollama.chat daha stabil olabilir
            # Test amaçlı `ollama list` komutu ile bağlantıyı doğrulayalım
            ollama.list()
            print("[DEBUG] Ollama bağlantısı başarılı.")
        except Exception as e:
            raise Exception(f"Ollama'ya bağlanılamadı. Lütfen Ollama'nın çalıştığından emin olun. Hata: {e}")

    def _build_chat_messages(self, comment_text):
        """
        Ollama.chat için daha etkili bir mesaj listesi oluşturur.
        Sistem mesajı, modelin rolünü ve görevini tanımlar.
        Kullanıcı mesajı, asıl veriyi içerir.
        """
        category_desc_str = "\n".join([f"- {cat['display_name']}: {cat['aciklama']}" for cat in self.categories])
        category_names_str = ", ".join([cat['csv_col'] for cat in self.categories])

        system_prompt = f"""Sen, kullanıcı yorumlarını analiz eden bir uzmansın. Görevin, sana verilen bir yorumun, belirtilen kategorilerden hangileriyle ilgili olduğunu belirlemektir.

Cevabını SADECE virgülle ayrılmış 0'lar ve 1'ler olarak, başka HİÇBİR AÇIKLAMA EKLEMEDEN vermelisin.
Cevabındaki sayıların sırası şu şekilde olmalı: {category_names_str}.

- Bir yorum o kategoriyle ilgiliyse '1' kullan.
- İlgili değilse '0' kullan.

Örneğin, cevap formatın '0,1,1,0' gibi olmalıdır."""

        user_prompt = f"""Aşağıdaki yorumu analiz et ve kategorilere ayır.

--- KATEGORİLER ---
{category_desc_str}

--- YORUM ---
"{comment_text}"

--- CEVABIN (Sadece 0 ve 1'ler, virgülle ayrılmış) ---"""

        return [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt},
        ]

    def _get_ollama_response(self, messages):
        """Ollama'dan yanıtı alır. Artık ollama.chat kullanılıyor."""
        try:
            # ollama.generate yerine ollama.chat kullanıyoruz
            response = ollama.chat(
                model=self.ollama_model,
                messages=messages,
                options={'temperature': 0.0} # Kategorizasyon için sıcaklığı 0 yapmak en tutarlı sonuçları verir
            )
            return response['message']['content'].strip()
        except Exception as e:
            # Hata mesajına model ismini de ekleyerek daha bilgilendirici hale getirelim
            raise Exception(f"Ollama '{self.ollama_model}' modelinden yanıt alınırken hata oluştu: {e}")

    # _parse_response fonksiyonu genellikle aynı kalabilir, çünkü hala çok iyi çalışıyor.
    def _parse_response(self, raw_response):
        """Ollama'dan gelen yanıtı daha sağlam bir şekilde işler."""
        digits = re.findall(r'\d', raw_response)
        scores = [int(d) for d in digits if d in ('0', '1')]
        
        if len(scores) != len(self.categories):
            print(f"[UYARI] Beklenmedik yanıt formatı. Yanıt: '{raw_response}'. Kategori sayısı ({len(self.categories)}) ile bulunan skor sayısı ({len(scores)}) eşleşmiyor. Sonuç [0,0,...] olarak ayarlandı.")
            return {cat['csv_col']: 0 for cat in self.categories}
            
        return {self.categories[i]['csv_col']: scores[i] for i in range(len(scores))}

    @pyqtSlot()
    def run(self):
        try:
            self.status_message.emit("Ollama bağlantısı kontrol ediliyor...")
            self._initialize_ollama_client()

            self.status_message.emit("Kategorizasyon: Yorumlar okunuyor...")
            df = pd.read_csv(self.input_csv_path, encoding='utf-8')
            
            for cat_info in self.categories:
                df[cat_info['csv_col']] = 0

            total_reviews = len(df)
            self.status_message.emit(f"Kategorizasyon: Toplam {total_reviews} yorum işlenecek. Model: {self.ollama_model}")

            print("\n" + "="*50)
            print("REVIEW CATEGORIZER DEBUG MODU AKTİF (CHAT VERSİYONU)")
            print(f"Kullanılacak Kategoriler: {[cat['csv_col'] for cat in self.categories]}")
            print(f"Kullanılacak Model: {self.ollama_model}")
            print("="*50 + "\n")

            for index, row in df.iterrows():
                if not self._is_running:
                    self.status_message.emit("Kategorizasyon kullanıcı tarafından durduruldu.")
                    break

                comment_text = str(row.get('text', ''))
                if not comment_text.strip():
                    continue

                # Eski _build_prompt yerine yeni _build_chat_messages kullanılıyor
                messages = self._build_chat_messages(comment_text)

                print(f"\n--- Yorum {index+1}/{total_reviews} İşleniyor ---")
                # Detaylı loglama için prompt'u yazdırabiliriz
                # print(f"Ollama'ya Gönderilen Mesajlar:\n---\nSystem: {messages[0]['content']}\nUser: {messages[1]['content']}\n---")
                
                raw_response = self._get_ollama_response(messages)
                
                print(f"Ollama'dan Alınan Ham Yanıt: >>>{raw_response}<<<")

                parsed_categories = self._parse_response(raw_response)
                
                print(f"Parse Edilen Sonuç: {parsed_categories}")

                for cat_name, value in parsed_categories.items():
                    if cat_name in df.columns:
                        df.at[index, cat_name] = value
                
                self.progress_updated.emit(index + 1, total_reviews)
                self.status_message.emit(f"Kategorizasyon: {index + 1}/{total_reviews} yorum işlendi.")

            self.status_message.emit("Kategorizasyon tamamlandı, sonuçlar kaydediliyor...")
            df.to_csv(self.output_csv_path, index=False, encoding='utf-8-sig')
            
            self.categorization_finished.emit(self.output_csv_path)

        except Exception as e:
            error_msg = f"Kategorizasyon hatası: {e}\n{traceback.format_exc()}"
            self.error_occurred.emit(error_msg)
        finally:
            self._is_running = False