# utils.py
import re
from urllib.parse import urlparse, parse_qs

def sanitize_filename(text):
    """Verilen metni dosya adı için güvenli hale getirir."""
    if not text:
        return "default_product"
    sanitized = re.sub(r'[^\w\s-]', '', text).strip()
    sanitized = re.sub(r'[-\s]+', '_', sanitized)
    return sanitized[:100] # Çok uzun olmasını engelle

def get_product_id_from_url(url):
    """Trendyol URL'sinden ürün adını ve ID'sini çıkarmaya çalışır."""
    try:
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.strip('/').split('/')
        
        # URL yapısı: /brand/product-name-p-12345
        if '-p-' in path_parts[-1]:
            name_part, id_part = path_parts[-1].rsplit('-p-', 1)
            product_id = id_part.split('?')[0] # Query parametrelerini temizle
            product_name = name_part
            return f"{sanitize_filename(product_name)}_{product_id}"
    except Exception:
        return None
    return "unknown_product" # Eğer ID bulunamazsa