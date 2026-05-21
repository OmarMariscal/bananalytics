import os
import requests
import hashlib

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
        # 1. Nos aseguramos de que la carpeta exista, pero ya NO la borramos
        os.makedirs(cls.CACHE_DIR, exist_ok=True)

        # 2. Creamos un 'set' para guardar los nombres de las imágenes que SÍ ocupamos
        imagenes_necesarias = set()

        for item in alerts_list:
            url = getattr(item, 'image_url', None)
            if not url: continue

            try:
                filename = cls._get_file_name(url)
                filepath = os.path.join(cls.CACHE_DIR, filename)
                
                # Agregamos este archivo a la lista de "archivos útiles"
                imagenes_necesarias.add(filename)

                # 3. MAGIA: Si el archivo ya existe en la carpeta, pasamos al siguiente producto
                if os.path.exists(filepath):
                    # print(f"✅ Ya en caché: {filename}") # Descomenta para debuggear
                    continue

                # Si no existe, entonces sí lo descargamos
                # print(f"⬇️ Descargando nueva: {url}")
                response = requests.get(
                    url, 
                    headers=cls.HEADERS, 
                    timeout=20,
                    stream=True
                )
                
                if response.status_code == 200:
                    with open(filepath, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                else:
                    print(f"Error {response.status_code} en {url}")

            except requests.exceptions.Timeout:
                print(f"Timeout: {url}")
            except Exception as e:
                print(f"Error descargando: {url} - Error: {e}")

        # 4. LIMPIEZA PROFUNDA: Borrar lo que ya no sirve
        cls._limpiar_cache_viejo(imagenes_necesarias)

    @classmethod
    def _limpiar_cache_viejo(cls, imagenes_necesarias):
        """Revisa la carpeta y borra los archivos que no están en la lista de necesarios"""
        if not os.path.exists(cls.CACHE_DIR): return

        for archivo in os.listdir(cls.CACHE_DIR):
            # Si el archivo en la carpeta NO está en nuestra lista de imágenes de esta sincronización...
            if archivo not in imagenes_necesarias:
                ruta_archivo = os.path.join(cls.CACHE_DIR, archivo)
                try:
                    os.remove(ruta_archivo)
                except Exception as e:
                    print(f"No se pudo eliminar {archivo} - Error: {e}")

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