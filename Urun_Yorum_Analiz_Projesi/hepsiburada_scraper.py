# hepsiburada_scraper.py (Corrected with hepsi_son.py logic)

import time
import json
import random
import re
import os
from dotenv import load_dotenv
from datetime import datetime
from urllib.parse import quote
from bs4 import BeautifulSoup

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import google.generativeai as genai

load_dotenv()

class HepsiburadaScraperWorker(QObject):
    # Signals are kept the same to maintain compatibility with main.py
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
        self.search_term = f"{brand_term} {product_name} {category_term}".strip()
        
        self._is_running = True
        self._driver = None # The active Selenium driver
        
        self._selected_products_full_info = []
        self._sku_to_name_map = {}
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
            self.status_update.emit(f"🗑️ Ürün kaldırıldı: {removed_product['name'][:50]}...")
            self.product_list_updated.emit(self._selected_products_full_info)

    @pyqtSlot(str)
    def remove_product_by_id(self, product_id):
        """Verilen product_id'ye sahip ürünü listeden kaldırır."""
        initial_len = len(self._selected_products_full_info)
        self._selected_products_full_info = [p for p in self._selected_products_full_info if str(p.get('sku')) != str(product_id)]
        if len(self._selected_products_full_info) < initial_len:
            self.status_update.emit(f"🗑️ Ürün (ID: {product_id}) listeden kaldırıldı.")
            self.product_list_updated.emit(self._selected_products_full_info)

    @pyqtSlot(dict)
    def set_review_counts_and_start(self, review_counts):
        """Kullanıcı yorum sayılarını (ID'ye göre) belirlediğinde çağrılır ve scraping'i başlatır."""
        self._review_counts = review_counts # Artık {sku: count} formatında bir sözlük
        self._start_scraping_flag = True
        self.status_update.emit(f"✅ Hepsiburada için yorum sayıları ayarlandı, çekme başlıyor...")

    # ===================================================================
    # METHODS ADAPTED 1-to-1 FROM hepsi_son.py
    # ===================================================================

    def _get_session_details_hepsiburada(self, search_url):
        self.status_update.emit("🤖 Selenium (gizli mod) başlatılıyor ve Hepsiburada'ya gidiliyor...")
        try:
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36")
            options.add_experimental_option('excludeSwitches', ['enable-logging']) 
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("useAutomationExtension", False)
            
            driver = webdriver.Chrome(options=options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            driver.get(search_url)
            
            self.status_update.emit("⏳ Sayfanın tam olarak yüklenmesi için 10 saniye bekleniyor...")
            time.sleep(10) 

            self.status_update.emit("✅ Tarayıcı (Selenium) başlatıldı ve API istekleri için hazır.")
            return driver
        except Exception as e:
            self.scraping_error.emit(f"Selenium başlatılamadı: {e}")
            if 'driver' in locals() and driver:
                driver.quit()
            return None

    def _extract_state_from_html_fragment(self, html_fragment, component_name):
        try:
            if '<script' not in html_fragment:
                return None
            script_start = html_fragment.find('<script')
            script_end = html_fragment.find('</script>', script_start)
            if script_start == -1 or script_end == -1:
                return None
            script_content_start = html_fragment.find('>', script_start) + 1
            script_content = html_fragment[script_content_start:script_end]
            state_start = script_content.find("'STATE':")
            if state_start == -1:
                state_start = script_content.find('"STATE":')
            if state_start == -1:
                return None
            json_start = script_content.find('{', state_start)
            if json_start == -1:
                return None
            bracket_count = 0
            json_end = json_start
            in_double_quote = False
            in_single_quote = False
            escape_next = False
            for i in range(json_start, len(script_content)):
                char = script_content[i]
                if escape_next:
                    escape_next = False
                    continue
                if char == '\\':
                    escape_next = True
                    continue
                if char == '"' and not in_single_quote:
                    in_double_quote = not in_double_quote
                    continue
                if char == "'" and not in_double_quote:
                    in_single_quote = not in_single_quote
                    continue
                if not in_double_quote and not in_single_quote:
                    if char == '{':
                        bracket_count += 1
                    elif char == '}':
                        bracket_count -= 1
                        if bracket_count == 0:
                            json_end = i + 1
                            break
            if json_end > json_start:
                json_str = script_content[json_start:json_end]
                try:
                    state_data = json.loads(json_str)
                    return state_data
                except json.JSONDecodeError:
                    return None
            return None
        except Exception:
            return None

    def _extract_product_json_from_html(self, html_content):
        self.status_update.emit("HTML içeriği analiz ediliyor (reduxStore)...")
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            json_script_tag = soup.find('script', {'id': 'reduxStore'})
            if json_script_tag and json_script_tag.string:
                self.status_update.emit("✅ Gömülü 'reduxStore' JSON verisi bulundu.")
                return json.loads(json_script_tag.string)
            self.status_update.emit("❌ HTML içinde 'reduxStore' verisi bulunamadı.")
            return None
        except Exception as e:
            self.status_update.emit(f"❌ 'reduxStore' JSON ayrıştırılamadı: {e}")
            return None

    def _fetch_raw_products_from_api(self, driver):
        self.status_update.emit("Sayfa kaynağından ürünler ayıklanıyor...")
        html_content = driver.page_source
        if not html_content:
            self.scraping_error.emit("❌ Selenium'dan sayfa kaynağı alınamadı.")
            return [], {}

        initial_state_data = self._extract_product_json_from_html(html_content)
        if not initial_state_data:
            return [], {}

        products = []
        try:
            fragments = initial_state_data.get('voltranState', {}).get('fragmentsMap', {})
            fragment_key_found = None 
            for fragment_id, fragment_data in fragments.items():
                component_state_data = None
                if 'VerticalFilter' in fragment_data:
                    if 'STATE' in fragment_data['VerticalFilter']:
                        state_value = fragment_data['VerticalFilter']['STATE']
                        if isinstance(state_value, str): 
                            try: state_value = json.loads(state_value)
                            except: continue
                        component_state_data = state_value.get('data', {})
                        fragment_key_found = f"{fragment_id} (VerticalFilter)"
                    elif 'html' in fragment_data['VerticalFilter']:
                        html_content_fragment = fragment_data['VerticalFilter']['html']
                        state_value = self._extract_state_from_html_fragment(html_content_fragment, 'VerticalFilter')
                        if state_value: 
                            component_state_data = state_value.get('data', {})
                            fragment_key_found = f"{fragment_id} (VerticalFilter/html)"
                
                elif 'ProductList' in fragment_data:
                    if 'STATE' in fragment_data['ProductList']:
                        state_value = fragment_data['ProductList']['STATE']
                        if isinstance(state_value, str): 
                            try: state_value = json.loads(state_value)
                            except: continue
                        component_state_data = state_value.get('data', {})
                        fragment_key_found = f"{fragment_id} (ProductList)"
                    elif 'html' in fragment_data['ProductList']:
                        html_content_fragment = fragment_data['ProductList']['html']
                        state_value = self._extract_state_from_html_fragment(html_content_fragment, 'ProductList')
                        if state_value: 
                            component_state_data = state_value.get('data', {})
                            fragment_key_found = f"{fragment_id} (ProductList/html)"
                
                if component_state_data and 'products' in component_state_data:
                    found_products = component_state_data.get('products', [])
                    if found_products:
                        products = found_products
                        self.status_update.emit(f"✅ Ürün listesi '{fragment_key_found}' içinde bulundu.")
                        break
            
            if not products:
                self.status_update.emit("❌ JSON verisi içinde 'products' listesi bulunamadı.")
                return [], {}

        except Exception as e:
            self.scraping_error.emit(f"❌ Ürün JSON'u işlenirken hata: {e}")
            return [], {}

        simplified_products = []
        sku_to_name_map = {}
        for p in products:
            main_sku = p.get("sku")
            main_name = p.get("name")
            main_brand = p.get("brand")
            main_url = p.get("url") 
            variants = p.get("variantList", [])
            sku, name, brand, category, product_url = None, None, None, None, None
            if variants:
                 default_variant = next((v for v in variants if v.get("isDefault")), variants[0])
                 sku = default_variant.get("sku")
                 name = default_variant.get("name")
                 brand = main_brand if main_brand else p.get("brand") 
                 category = p.get("mainCategory", {}).get("name")
                 product_url = default_variant.get("url") 
                 if not product_url:
                     product_url = main_url 
            elif main_sku:
                 sku = main_sku
                 name = main_name
                 brand = main_brand
                 category = p.get("mainCategory", {}).get("name")
                 product_url = main_url
            else:
                 continue 
            if sku and name:
                full_url = "https://www.hepsiburada.com" + product_url if product_url else None
                simplified_products.append({
                    "id": sku, "name": name, "brand": brand, "categoryName": category, "url": full_url
                })
                sku_to_name_map[sku] = {"name": name, "url": full_url}
        
        self.status_update.emit(f"✅ Filtreleme için {len(simplified_products)} ürün hazırlandı.")
        return simplified_products, sku_to_name_map

    def _filter_products_with_llm(self, simplified_product_list, max_products=5):
        YOUR_API_KEY = "AIzaSyDE-Ww6uCr9IZoqsZMCThAEWdtTyNM-vqg"
        if not YOUR_API_KEY or "BURAYA" in YOUR_API_KEY:
            self.scraping_error.emit("❌ Gemini API anahtarı girilmemiş!")
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
ÜRÜN LİSTESİ (Hepsiburada'dan gelen):
{json.dumps(simplified_product_list, indent=2, ensure_ascii=False)}
GÖREV:
1. Kullanıcının sorgusundaki anahtar kelimeleri (marka, model, özellik vb.) ürün adı ('name'), marka ('brand') ve kategori ('categoryName') bilgileriyle dikkatlice karşılaştır.
2. Sorguyla en alakalı olan en fazla {max_products} adet ürünün ID'sini ('id' alanındaki SKU değerini) seç.
3. Yanıt olarak sadece ve sadece JSON formatında bir çıktı üret.
İSTENEN ÇIKTI FORMATI: {{ "secilen_idler": ["SKU123", "SKU456", ...] }}
'''
        self.status_update.emit("🧠 Gemini AI ile en uygun ürünler seçiliyor...")
        try:
            response = model.generate_content(prompt)
            llm_json = json.loads(response.text)
            product_skus = llm_json.get("secilen_idler", [])
            if not product_skus:
                self.status_update.emit("⚠️ Gemini AI, sorguyla eşleşen bir ürün bulamadı.")
            else:
                self.status_update.emit(f"✅ Gemini {len(product_skus)} ürün seçti.")
            return product_skus
        except Exception as e:
            error_details = getattr(e, 'message', str(e))
            if 'API_KEY_INVALID' in str(e) or 'API key not valid' in str(e):
                 self.scraping_error.emit(f"❌ Gemini API Hatası: API Anahtarınız geçersiz.")
            else:
                 self.scraping_error.emit(f"❌ Gemini API hatası: {error_details}")
            return []

    def _execute_fetch_in_browser(self, url, referer=None, max_retries=3):
        fetch_script = f"""
        var callback = arguments[arguments.length - 1]; 
        fetch('{url}', {{
            method: 'GET',
            headers: {{
                'Accept': 'application/json, text/plain, */*', 
                'Origin': 'https://www.hepsiburada.com',
                'Referer': '{referer}' 
            }}
        }})
        .then(response => {{
            if (!response.ok) {{
                throw new Error('HTTP Error ' + response.status);
            }}
            return response.json();
        }})
        .then(data => callback(data))
        .catch(err => callback({{ 'selenium_fetch_error': err.message }}));
        """
        
        for attempt in range(max_retries):
            try:
                self._driver.set_script_timeout(30)
                response_data = self._driver.execute_async_script(fetch_script)
                
                if isinstance(response_data, dict) and 'selenium_fetch_error' in response_data:
                    raise Exception(response_data['selenium_fetch_error'])
                
                return response_data
                
            except Exception as e:
                self.status_update.emit(f"JS Fetch hatası: {e}. Deneme {attempt + 1}/{max_retries}...")
                if attempt + 1 == max_retries:
                    return None 
                time.sleep(random.uniform(3, 6))
        return None

    def _get_review_count_for_product(self, product_sku, product_url):
        api_url = f"https://user-content-gw-hermes.hepsiburada.com/queryapi/v2/ApprovedUserContents?sku={product_sku}&from=0&size=1"
        referer = product_url + '-yorumlari' if product_url and not product_url.endswith('-yorumlari') else product_url
        if not referer:
            referer = f'https://www.hepsiburada.com/product-p-{product_sku}-yorumlari'
        
        data = self._execute_fetch_in_browser(api_url, referer=referer)
        if data and 'data' in data:
            approved_content = data['data'].get('approvedUserContent', {})
            return approved_content.get('listCount', 0)
        return 0

    def _get_all_reviews_for_product(self, product_sku, product_url, target_review_count):
        reviews_for_this_product = []
        if target_review_count == 0:
            return []
            
        page_size = 25
        current_from = 0
        review_counter = 0
        
        if product_url:
            referer_url = product_url + '-yorumlari' if not product_url.endswith('-yorumlari') else product_url
        else:
            referer_url = f'https://www.hepsiburada.com/product-p-{product_sku}-yorumlari'

        while self._is_running and review_counter < target_review_count:
            api_url = f"https://user-content-gw-hermes.hepsiburada.com/queryapi/v2/ApprovedUserContents?sku={product_sku}&showOnlyMediaAvailableReviews=false&includeSiblingVariantContents=true&from={current_from}&size={page_size}"
            page_data = self._execute_fetch_in_browser(api_url, referer=referer_url)

            if not page_data or 'data' not in page_data:
                self.status_update.emit("⚠️ API yanıtı hatalı/boş, bu ürün için yorum çekme durduruldu.")
                break
            
            approved_content = page_data['data'].get('approvedUserContent', {})
            reviews_on_page = approved_content.get('approvedUserContentList', [])
            
            if not reviews_on_page:
                self.status_update.emit("✅ Mevcut sayfada yorum yok, tüm yorumlar çekildi.")
                break

            for review_item in reviews_on_page:
                if not self._is_running or review_counter >= target_review_count:
                    break
                
                review_content = review_item.get('review', {})
                comment = review_content.get('content', '') if review_content else ''
                if not comment or comment is None:
                    continue

                timestamp_str = review_item.get('createdAt', '')
                review_date = "Tarih bilinmiyor"
                if timestamp_str:
                    try:
                        review_date = datetime.fromisoformat(timestamp_str.replace('+00:00', '')).strftime('%Y-%m-%d')
                    except:
                        pass
                
                reviews_for_this_product.append(review_item)
                review_counter += 1
                self.review_found.emit("Hepsiburada", str(product_sku), review_counter, target_review_count)

            current_from += len(reviews_on_page)
            if not self._is_running: break
            time.sleep(random.uniform(1.0, 2.5))
        
        return reviews_for_this_product

    @pyqtSlot()
    def run(self):
        self._is_running = True
        try:
            search_url = f"https://www.hepsiburada.com/ara?q={quote(self.search_term)}"
            self._driver = self._get_session_details_hepsiburada(search_url)
            if not self._driver or not self._is_running: return

            simplified_list, self._sku_to_name_map = self._fetch_raw_products_from_api(self._driver)
            if not simplified_list:
                self.scraping_error.emit("Arama sonuçlarında ürün bulunamadı.")
                return

            matched_skus = self._filter_products_with_llm(simplified_list, max_products=5)
            if not matched_skus:
                self.status_update.emit("⚠️ AI seçimi başarısız, bulunan ilk 3 ürün kullanılıyor.")
                matched_skus = [p['id'] for p in simplified_list[:3]]

            products_for_ui = []
            self.status_update.emit("📊 Yorum sayıları alınıyor...")
            for sku in matched_skus:
                if not self._is_running: return
                product_info = self._sku_to_name_map.get(sku)
                if not product_info: continue

                review_count = self._get_review_count_for_product(sku, product_info.get('url'))
                product_data = {
                    'sku': sku,
                    'name': product_info.get('name', 'İsim Bulunamadı'),
                    'url': product_info.get('url', None),
                    'review_count': review_count
                }
                products_for_ui.append(product_data)
                self.status_update.emit(f"'{product_data['name'][:40]}...' için {review_count} yorum bulundu.")

            self._selected_products_full_info = products_for_ui
            self.products_selected.emit(products_for_ui)

            self.status_update.emit("▶️ 'Ürünleri Onayla' butonuna basılması bekleniyor...")
            while self._is_running and not self._start_scraping_flag:
                time.sleep(0.2)

            if not self._is_running or self._review_counts is None:
                if self._is_running:
                    self.scraping_error.emit("İşlem iptal edildi.")
                return

            all_reviews_collected = []
            total_target = sum(self._review_counts.values())
            collected_so_far = 0

            # Onaylanan ürünler üzerinden ID ve sayı ile döngüye gir
            for i, (sku, target_count) in enumerate(self._review_counts.items()):
                if not self._is_running: break
                if target_count == 0: continue

                # SKU kullanarak ürünün tam bilgisini listeden bul
                product_data = next((p for p in self._selected_products_full_info if str(p.get('sku')) == str(sku)), None)

                if not product_data:
                    self.status_update.emit(f"⚠️ Uyarı: Ürün SKU'su {sku} listede bulunamadı, atlanıyor.")
                    continue

                name = product_data['name']
                url = product_data['url']
                
                # Kullanıcı arayüzü için doğru ürün sırasını ve toplamını bildir
                total_products_to_scrape = len([c for c in self._review_counts.values() if c > 0])
                self.product_switching.emit("Hepsiburada", str(sku), name, i + 1, total_products_to_scrape)
                
                reviews = self._get_all_reviews_for_product(sku, url, target_count)
                
                for r in reviews:
                    r['product'] = name
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
                self.status_update.emit("Tarayıcı kapatıldı.")