# ReviewInsight: E-Ticaret Yorum Analiz Aracı

![Uygulama Ekran Görüntüsü](https://via.placeholder.com/800x450.png?text=Uygulama+Ekran+Görüntüsü)

*<p align="center">ReviewInsight, e-ticaret sitelerindeki ürün yorumlarını analiz ederek pazar araştırması ve rakip analizi için derinlemesine içgörüler sunan bir masaüstü uygulamasıdır.</p>*

Bu proje, Trendyol ve Hepsiburada gibi büyük e-ticaret platformlarından ürün yorumlarını toplayan, analiz eden ve raporlayan bir masaüstü uygulamasıdır. PyQt6 ile geliştirilen bu araç, müşteri geri bildirimlerinden anlamlı içgörüler elde etmek için duygu analizi, yorum sınıflandırma ve kapsamlı rapor oluşturma işlevleri sunar.

## Temel Özellikler

*   **Otomatik Yorum Toplama:** Belirtilen ürünler için Trendyol ve Hepsiburada'dan otomatik olarak yorumları çeker.
*   **Yapay Zeka Destekli Ürün Seçimi:** Kullanıcı sorgularına göre analiz için en uygun ürünleri önermek üzere Gemini yapay zekasını kullanır.
*   **Adım Adım Analiz Süreci:**
    1.  **Veri Toplama:** Belirtilen ürünler için yorumları toplar.
    2.  **Duygu Analizi:** Toplanan yorumlar üzerinde duygu analizi gerçekleştirir.
    3.  **Akıllı Sınıflandırma:** Yorumları kullanıcı tanımlı veya varsayılan kategorilere (örneğin Fiyat, Kalite, Kargo) ayırır.
    4.  **Rapor Oluşturma:** Analiz sonuçlarını içeren, grafiklerle zenginleştirilmiş detaylı Word (.docx) raporları hazırlar.
*   **Etkileşimli Arayüz:** Kullanıcıyı analiz adımları boyunca yönlendiren, PyQt6 ile oluşturulmuş kullanıcı dostu bir arayüze sahiptir.
*   **Veri Görselleştirme:** Analiz sonuçlarını görselleştirmek için pasta grafikleri ve zaman serisi analizleri gibi çeşitli grafikler oluşturur.
*   **Özelleştirilebilir Kategoriler:** Kullanıcıların daha hedefe yönelik bir analiz için kendi kategorilerini tanımlamasına olanak tanır.

## Kullanılan Teknolojiler

*   **Backend/Çekirdek Mantık:** Python
*   **Masaüstü Arayüzü (GUI):** PyQt6
*   **Veri İşleme:** Pandas
*   **Web Scraping:** Selenium, Requests, BeautifulSoup gibi kütüphanelerle özelleştirilmiş scraper modülleri.
*   **Yapay Zeka:** Google Gemini (Ürün seçimi için)
*   **Veri Görselleştirme:** Matplotlib
*   **Raporlama:** python-docx

## Proje Yapısı

Proje, `Urun_Yorum_Analiz_Projesi` klasörü altında çeşitli modüller halinde düzenlenmiştir:

*   `main.py`: PyQt6 uygulamasının ana giriş noktasıdır. Arayüzü ve iş akışını yönetir.
*   `config.py`: Uygulama ayarları için yapılandırma dosyasıdır.
*   `product_scraper.py` / `hepsiburada_scraper.py`: E-ticaret sitelerinden yorumları çekmekle sorumlu modüllerdir.
*   `sentiment_analyzer.py`: Duygu analizi işlemlerini yürüten modüldür.
*   `review_categorizer.py`: Yorumları sınıflandırmak için kullanılan modüldür.
*   `report_builder.py`: Nihai analiz raporunu oluşturan modüldür.
*   `utils.py`: Proje genelinde kullanılan yardımcı fonksiyonları içerir.

## Nasıl Çalıştırılır?

1.  Proje için gerekli bağımlılıkları `requirements.txt` dosyasını kullanarak kurun:
    ```bash
    pip install -r requirements.txt
    ```
2.  `Urun_Yorum_Analiz_Projesi` klasörüne gidin.
3.  Ana uygulama dosyasını çalıştırın:
    ```bash
    python main.py
    ```
