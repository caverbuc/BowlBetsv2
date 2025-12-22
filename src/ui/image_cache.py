import os
import requests
from PyQt6.QtGui import QPixmap

class ImageCache:
    def __init__(self, cache_dir="resources/logos"):
        self.cache_dir = cache_dir
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def get_pixmap(self, url: str) -> QPixmap:
        if not url:
            return None

        # Generate a filename from the URL
        filename = url.split("/")[-1]
        local_path = os.path.join(self.cache_dir, filename)

        if os.path.exists(local_path):
            return QPixmap(local_path)
        else:
            try:
                response = requests.get(url, timeout=5)
                response.raise_for_status()
                with open(local_path, "wb") as f:
                    f.write(response.content)
                return QPixmap(local_path)
            except requests.exceptions.RequestException as e:
                print(f"Error downloading image {url}: {e}")
                return None
