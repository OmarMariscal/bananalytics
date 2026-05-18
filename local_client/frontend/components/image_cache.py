import os
import shutil
import requests
import hashlib
import flet as ft

class ImageCacheManager:
    CACHE_DIR = "assets/image_cache"
    
    # "Disfraz" de navegador para que el servidor no nos bloquee
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    @staticmethod
    def _get_file_name(url):
        if not url: return "placeholder.png"
        ext = url.split('.')[-1].split('?')[0]
        if len(ext) > 4: ext = "png"
        hash_name = hashlib.md5(url.encode()).hexdigest()
        return f"{hash_name}.{ext}"

    @classmethod
    def sync_all_images(cls, alerts_list):
        if os.path.exists(cls.CACHE_DIR):
            shutil.rmtree(cls.CACHE_DIR)
        os.makedirs(cls.CACHE_DIR)

        for item in alerts_list:
            url = getattr(item, 'image_url', None)
            if not url: continue

            try:
                filename = cls._get_file_name(url)
                filepath = os.path.join(cls.CACHE_DIR, filename)
                
                # Agregamos los headers y aumentamos el timeout a 20 segundos
                response = requests.get(
                    url, 
                    headers=cls.HEADERS, 
                    timeout=20,
                    stream=True # Útil para archivos grandes
                )
                
                if response.status_code == 200:
                    with open(filepath, "wb") as f:
                        # Guardar el contenido por pedazos para evitar saturar memoria
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                else:
                    print(f"Error {response.status_code} en {url}")

            except requests.exceptions.Timeout:
                print(f"⌛ Tiempo agotado descargando: {url} (El servidor tardó demasiado)")
            except Exception as e:
                print(f"❌ Error descargando {url}: {e}")

    @classmethod
    def get_local_image_path(cls, url):
        if not url:
            return "/icon_products.png"
        filename = cls._get_file_name(url)
        relative_path = f"/image_cache/{filename}"
        full_path = os.path.join(cls.CACHE_DIR, filename)

        if os.path.exists(full_path):
            return relative_path
        return "/icon_products.png"