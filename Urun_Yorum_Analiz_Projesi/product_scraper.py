# product_scraper.py (REVISED AND CORRECTED - v2)

import time
import json
import random
import re
import os
from dotenv import load_dotenv
from datetime import datetime
from curl_cffi import requests as curl_requests
from urllib.parse import quote
import requests as standard_requests

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from selenium import webdriver
import google.generativeai as genai

load_dotenv()

class ProductScraperWorker(QObject):
    # Signals are kept the same
    scraping_finished = pyqtSignal(list, str)
    scraping_error = pyqtSignal(str)
    status_update = pyqtSignal(str)
    review_found = pyqtSignal(str, str, int, int)
    product_switching = pyqtSignal(str, str, str, int, int)
    products_selected = pyqtSignal(list)
    product_list_updated = pyqtSignal(list)
    overall_progress = pyqtSignal(int, int)

    def __init__(self, brand_term, product_name, category_term, parent=None):
        super().__init__(parent)
        self.brand_term = brand_term
        self.product_name = product_name
        self.category_term = category_term
        self.search_term = f"{self.brand_term} {self.product_name} {self.category_term}".strip()
        
        self._is_running = True
        self._driver = None
        self._session_details = None
        
        self._selected_products_full_info = []
        self._review_counts = None
        self._start_scraping_flag = False

    def stop(self):
        self._is_running = False
        if self._driver:
            try:
                self._driver.quit()
            except:
                pass

    @pyqtSlot(int)
    def remove_product_at_index(self, index):
        if self._selected_products_full_info and 0 <= index < len(self._selected_products_full_info):
            removed_product = self._selected_products_full_info.pop(index)
            self.status_update.emit(f"🗑 Ürün kaldırıldı: {removed_product['name'][:50]}...")
            self.product_list_updated.emit(self._selected_products_full_info)

    @pyqtSlot(str)
    def remove_product_by_id(self, product_id):
        """Verilen product_id'ye sahip ürünü listeden kaldırır."""
        initial_len = len(self._selected_products_full_info)
        self._selected_products_full_info = [p for p in self._selected_products_full_info if str(p.get('id')) != str(product_id)]
        if len(self._selected_products_full_info) < initial_len:
            self.status_update.emit(f"🗑️ Ürün (ID: {product_id}) listeden kaldırıldı.")
            self.product_list_updated.emit(self._selected_products_full_info)

    @pyqtSlot(dict)
    def set_review_counts_and_start(self, review_counts):
        """Kullanıcı yorum sayılarını (ID'ye göre) belirlediğinde çağrılır ve scraping'i başlatır."""
        self._review_counts = review_counts # Artık {product_id: count} formatında bir sözlük
        self._start_scraping_flag = True
        self.status_update.emit(f"✅ Trendyol için yorum sayıları ayarlandı, çekme başlıyor...")

    # ===================================================================
    # ADAPTED METHODS
    # ===================================================================

    # CORRECTED: Switched to headless mode with anti-detection options.
    def _get_session_details(self):
        """Uses a headless Selenium browser to get Cloudflare cookies and user-agent."""
        self.status_update.emit("🤖 Selenium (gizli mod) başlatılıyor ve cookie'ler alınıyor...")
        try:
            options = webdriver.ChromeOptions()
            options.add_argument("--headless")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36")
            options.add_experimental_option('excludeSwitches', ['enable-logging'])
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("useAutomationExtension", False)
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")

            self._driver = webdriver.Chrome(options=options)
            self._driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            self._driver.get("https://www.trendyol.com/sr?q=laptop")
            self.status_update.emit("⏳ Sayfanın yüklenmesi ve Cloudflare kontrolü için 10sn bekleniyor...")
            time.sleep(10)

            browser_cookies = self._driver.get_cookies()
            user_agent = self._driver.execute_script("return navigator.userAgent;")

            if not browser_cookies:
                self.scraping_error.emit("❌ Cookie alınamadı. Muhtemelen bot algılamasına takıldı.")
                return False

            self.status_update.emit("✅ Cookie'ler ve User-Agent başarıyla alındı.")
            self._session_details = {
                "cookies": {cookie['name']: cookie['value'] for cookie in browser_cookies},
                "user_agent": user_agent
            }
        except Exception as e:
            self.scraping_error.emit(f"Selenium (cookie) hatası: {e}")
            return False
        finally:
            if self._driver:
                self._driver.quit()
                self._driver = None
        return True

    def _fetch_raw_products_from_api(self):
        encoded_query = quote(self.search_term)
        api_url = f"https://apigw.trendyol.com/discovery-web-searchgw-service/v2/api/infinite-scroll/sr?q={encoded_query}&page=1&storefrontId=1&culture=tr-TR"
        headers = {"accept": "application/json", "user-agent": "Mozilla/5.0"}
        self.status_update.emit(f"🔍 API'den ürün listesi çekiliyor...")
        try:
            response = standard_requests.get(api_url, headers=headers, timeout=20)
            response.raise_for_status()
            data = response.json()

            # Save the response to a file for debugging
            output_filename = "trendyol_search_response.json"
            try:
                with open(output_filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                self.status_update.emit(f"💾 API yanıtı '{output_filename}' olarak kaydedildi.")
            except Exception as file_e:
                self.status_update.emit(f"💾 API yanıtı dosyaya yazılamadı: {file_e}")

            products = data.get("result", {}).get("products", [])
            if not products:
                self.status_update.emit("⚠ API'den ürün bulunamadı.")
                return []
            self.status_update.emit(f"✅ API'den {len(products)} ham ürün bulundu.")
            return products # Return the full product list
        except Exception as e:
            self.scraping_error.emit(f"Arama API hatası: {e}")
            return []

    def _filter_products_with_llm(self, product_list, max_products=5):
        YOUR_API_KEY = os.getenv("GEMINI_API_KEY")
        
        simplified_list = []
        for p in product_list:
            if p.get("id") and p.get("name"):
                simplified_list.append({
                    "id": p.get("id"), "name": p.get("name"),
                    "brand": p.get("brand", {}).get("name"),
                    "categoryName": p.get("categoryName")
                })

        if not YOUR_API_KEY or "BURAYA" in YOUR_API_KEY:
            self.scraping_error.emit("❌ Gemini API anahtarı .env dosyasında bulunamadı!")
            return []

        try:
            genai.configure(api_key=YOUR_API_KEY)
            generation_config = {"response_mime_type": "application/json"}
            model = genai.GenerativeModel('models/gemini-2.5-flash', generation_config=generation_config)
        except Exception as e:
            self.scraping_error.emit(f"❌ Gemini modeli başlatılamadı: {e}")
            return []

        prompt = f'''
Sen bir e-ticaret ürün eşleştirme uzmanısın. Kullanıcının arama sorgusuna en uygun ürünleri bulmakla görevlisin.
KULLANICI SORGUSU: "{self.search_term}"
ÜRÜN LİSTESİ:
{json.dumps(simplified_list, indent=2, ensure_ascii=False)}
GÖREV:
1. Kullanıcının sorgusundaki anahtar kelimeleri (marka, model, özellik vb.) ürün adı, marka ve kategori bilgileriyle dikkatlice karşılaştır.
2. Sorguyla en alakalı olan en fazla {max_products} adet ürünün ID'sini seç.
3. Yanıt olarak sadece ve sadece JSON formatında bir çıktı üret. Kesinlikle başka bir açıklama veya metin ekleme.
İSTENEN ÇIKTI FORMATI: {{ "secilen_idler": [12345, 67890, ...] }}
'''
        self.status_update.emit("🧠 Gemini AI ile en uygun ürünler seçiliyor...")
        try:
            response = model.generate_content(prompt)
            llm_json = json.loads(response.text)
            product_ids = llm_json.get("secilen_idler", [])
            if not product_ids:
                self.status_update.emit("⚠ LLM, sorguyla eşleşen bir ürün ID'si bulamadı.")
            else:
                self.status_update.emit(f"✅ Gemini {len(product_ids)} ürün seçti: {product_ids}")
            return product_ids
        except Exception as e:
            self.scraping_error.emit(f"❌ Gemini API hatası: {e}")
            return []



    def _get_all_reviews_for_product(self, product_id, product_url, target_review_count):
        """Fetches all reviews for a single product ID using the API."""
        reviews_for_this_product = []
        page_size = 10 # Changed from 20 to 10
        headers = {
            'accept': 'application/json, text/plain, */*',
            'origin': 'https://www.trendyol.com',
            'referer': f'https://www.trendyol.com/brand/product-p-{product_id}', # REVERTED to generic referer
            'user-agent': self._session_details['user_agent'],
        }
        total_pages_to_fetch = (target_review_count + page_size - 1) // page_size
        review_counter = 0

        for page_num in range(total_pages_to_fetch):
            if not self._is_running or review_counter >= target_review_count:
                break

            api_url = f"https://apigw.trendyol.com/discovery-pdp-websfxreviewrating-santral/{product_id}/reviews?page={page_num}&pageSize={page_size}&culture=tr-TR&order=DESC&orderBy=Score"
            
            page_successful = False
            for attempt in range(3): # Max 3 retries for a single page
                try:
                    response = curl_requests.get(
                        api_url, headers=headers, cookies=self._session_details['cookies'],
                        impersonate="chrome120", timeout=30
                    )
                    response.raise_for_status()
                    page_data = response.json()
                    
                    if page_data and 'result' in page_data and 'reviews' in page_data['result']:
                        new_reviews = page_data['result']['reviews']
                        if not new_reviews:
                            page_successful = True # No more reviews, but not an error
                            break
                        for review in new_reviews:
                            if review_counter >= target_review_count: break
                            comment = review.get('comment', '')
                            timestamp_ms = review.get('createdAt', 0)
                            review_date = "Tarih bilinmiyor"
                            if timestamp_ms > 0:
                                review_date = datetime.fromtimestamp(timestamp_ms / 1000).strftime('%Y-%m-%d')
                            reviews_for_this_product.append({"date": review_date, "text": comment})
                            review_counter += 1
                            self.review_found.emit("Trendyol", str(product_id), review_counter, target_review_count)
                        page_successful = True
                        break # Break retry loop, page processed successfully
                    else:
                        page_successful = True # No reviews or result, but not an error
                        break # Break retry loop, page processed successfully

                except Exception as e:
                    import requests as standard_requests # Ensure requests is imported for HTTPError
                    is_500_error = False
                    if isinstance(e, standard_requests.exceptions.HTTPError) and e.response.status_code == 500:
                        is_500_error = True
                    elif "500" in str(e): # Fallback for other exception types that might contain 500
                        is_500_error = True

                    if attempt < 2: # If not the last attempt (0-indexed, so 2 means 3rd attempt)
                        wait_time = random.uniform(10, 30) if is_500_error else random.uniform(3, 10)
                        self.status_update.emit(f"Yorum çekerken hata (Sayfa {page_num}, Deneme {attempt+1}/3): {e}. {wait_time:.1f} saniye bekleniyor...")
                        time.sleep(wait_time)
                    else:
                        self.status_update.emit(f"Yorum çekerken hata (Sayfa {page_num}, Tüm denemeler başarısız): {e}. Bu sayfa atlanıyor.")
                        break # Break retry loop, proceed to next page_num

            if not page_successful:
                # If all retries failed, or a non-retryable error occurred, skip this page
                continue # Continue to the next page_num in the outer loop

            time.sleep(random.uniform(1.0, 2.5)) # Normal delay between successful page fetches
        return reviews_for_this_product

    @pyqtSlot()
    def run(self):
        self._is_running = True
        try:
            # === STAGE 1: Find products and let user choose ===
            if not self._get_session_details(): return

            # Add a small delay just in case there's a timing issue with cookie propagation
            self.status_update.emit("Oturum bilgileri alındı, 2sn bekleniyor...")
            time.sleep(2)

            full_product_list = self._fetch_raw_products_from_api()
            if not full_product_list:
                self.scraping_error.emit("Arama sonuçlarında ürün bulunamadı.")
                return

            matched_ids = self._filter_products_with_llm(full_product_list)
            if not matched_ids:
                self.status_update.emit("⚠ AI seçimi başarısız, ilk 3 ürün kullanılıyor.")
                matched_ids = [p['id'] for p in full_product_list[:3]]

            products_for_ui = []
            self.status_update.emit("📊 Yorum sayıları API yanıtından okunuyor...")
            for product_id in matched_ids:
                if not self._is_running: return
                product_info = next((p for p in full_product_list if p.get('id') == product_id), None)
                if not product_info: continue

                # --- KEY CHANGE HERE ---
                # Get review count from the new, more accurate endpoint
                try:
                    self.status_update.emit(f"Metinli yorum sayısı çekiliyor (ID: {product_id})...")
                    count_api_url = f"https://apigw.trendyol.com/discovery-storefront-trproductgw-service/api/review-read/product-reviews/detailed?contentId={product_id}&page=0&pageSize=1"
                    
                    headers = {
                        'accept': 'application/json',
                        'origin': 'https://www.trendyol.com',
                        'referer': product_info.get('url', f'https://www.trendyol.com/brand/product-p-{product_id}'),
                        'user-agent': self._session_details['user_agent']
                    }
                    
                    response = curl_requests.get(
                        count_api_url, 
                        headers=headers, 
                        cookies=self._session_details['cookies'],
                        impersonate="chrome120", 
                        timeout=20
                    )
                    response.raise_for_status()
                    data = response.json()
                    
                    review_count = data.get("result", {}).get("summary", {}).get("totalCommentCount", 0)
                    
                    self.status_update.emit(f"✅ {review_count} metinli yorum bulundu.")
                except Exception as e:
                    import traceback
                    with open("error_log.txt", "a", encoding="utf-8") as f:
                        f.write(f"\n--- FINAL ATTEMPT FAILED ---\n")
                        f.write(f"Error fetching comment count for ID {product_id}: {e}\n")
                        traceback.print_exc(file=f)
                    self.status_update.emit(f"⚠️ Yeni API ile yorum sayısı alınamadı. Detaylar error_log.txt dosyasına yazıldı.")
                    self.status_update.emit("Fallback: Eski yöntemle (toplam değerlendirme) devam ediliyor.")
                    review_count = product_info.get('ratingScore', {}).get("summary", {}).get('totalCount', 0)
                
                product_url_full = "https://www.trendyol.com" + product_info.get('url', '')
                
                product_data = {
                    'id': product_id,
                    'name': product_info.get('name', 'İsim Bulunamadı'),
                    'url': product_url_full,
                    "review_count": review_count,
                    

                }
                products_for_ui.append(product_data)
                self.status_update.emit(f"'{product_data['name'][:40]}...' için {review_count} yorum bulundu.")

            self._selected_products_full_info = products_for_ui
            self.products_selected.emit(products_for_ui)

            # === STAGE 2: Wait for user to confirm counts and start scraping ===
            self.status_update.emit("▶ 'Ürünleri Onayla' butonuna basılmasını bekliyor...")
            while self._is_running and not self._start_scraping_flag:
                time.sleep(0.2)
            if not self._is_running or self._review_counts is None:
                if self._is_running:
                    self.scraping_error.emit("İşlem iptal edildi.")
                return

            # === STAGE 3: Scrape reviews for selected products ===
            all_reviews_collected = []
            total_target = sum(self._review_counts.values())
            collected_so_far = 0

            # Onaylanan ürünler üzerinden ID ve sayı ile döngüye gir
            for i, (product_id, target_count) in enumerate(self._review_counts.items()):
                if not self._is_running: break
                if target_count == 0: continue

                # ID kullanarak ürünün tam bilgisini listeden bul
                product_data = next((p for p in self._selected_products_full_info if str(p.get('id')) == str(product_id)), None)

                if not product_data:
                    self.status_update.emit(f"⚠️ Uyarı: Ürün ID'si {product_id} listede bulunamadı, atlanıyor.")
                    continue

                product_name = product_data['name']
                product_url = product_data['url']
                
                # Kullanıcı arayüzü için doğru ürün sırasını ve toplamını bildir
                total_products_to_scrape = len([c for c in self._review_counts.values() if c > 0])
                self.product_switching.emit("Trendyol", str(product_id), product_name, i + 1, total_products_to_scrape)
                
                reviews = self._get_all_reviews_for_product(product_id, product_url, target_count)
                
                for r in reviews:
                    r['product'] = product_name
                all_reviews_collected.extend(reviews)
                
                collected_so_far += len(reviews)
                self.overall_progress.emit(collected_so_far, total_target)

            if not self._is_running:
                self.scraping_error.emit("İşlem durduruldu.")
                return

            combined_title = f"{len(all_reviews_collected)} yorum ({len(self._review_counts)} üründen)"
            self.scraping_finished.emit(all_reviews_collected, combined_title)

        except Exception as e:
            import traceback
            self.scraping_error.emit(f"Beklenmedik hata: {e}\n{traceback.format_exc()}")
        finally:
            self._is_running = False
            if self._driver:
                self._driver.quit()