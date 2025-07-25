import os
import zipfile
import requests

url = "https://app.roboflow.com/ds/jVyLy60T4K?key=Yj8OFr6q4l"
zip_path = "roboflow.zip"

def download_and_extract(url, zip_path, extract_to="."):
    print("İndiriliyor...")
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(zip_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    print("İndirme tamamlandı.")

    print("Zip açılıyor...")
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_to)
    print("Zip açıldı.")

    os.remove(zip_path)
    print("Zip dosyası silindi.")

if __name__ == "__main__":
    download_and_extract(url, zip_path) 