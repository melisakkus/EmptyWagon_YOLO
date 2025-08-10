# features/database/firestore_crud.py
# --- Genel CRUD Fonksiyonları ---
from features.database.initialize_firebase import initialize_firebase
from firebase_admin import firestore # SERVER_TIMESTAMP için gerekli

# collection = "trainwagon" # Bu satırı kaldırın, koleksiyon adını fonksiyonlara parametre olarak geçireceğiz.

def create_document(db, collection_name, data, document_id=None):
    """
    Belirtilen koleksiyona yeni bir doküman ekler.
    Eğer document_id verilirse, o ID ile doküman oluşturur. Verilmezse, otomatik ID atanır.
    """
    try:
        if db is None:
            print("❌ Hata: Firebase istemcisi başlatılmamış.")
            return None

        if document_id:
            doc_ref = db.collection(collection_name).document(document_id)
            doc_ref.set(data)
            # print(f"📄 '{collection_name}' koleksiyonuna '{document_id}' ID'li doküman eklendi/güncellendi.")
            return document_id
        else:
            _, doc_ref = db.collection(collection_name).add(data)
            # print(f"📄 '{collection_name}' koleksiyonuna yeni doküman eklendi. ID: {doc_ref.id}")
            return doc_ref.id

    except Exception as e:
        print(f"❌ Hata: Doküman oluşturulamadı. Detay: {e}")
        return None

def get_document(db, collection_name, document_id):
    """
    Belirli bir ID'ye sahip tek bir dokümanı getirir.
    """
    try:
        if db is None:
            print("❌ Hata: Firebase istemcisi başlatılmamış.")
            return None

        doc_ref = db.collection(collection_name).document(document_id)
        doc = doc_ref.get()
        if doc.exists:
            # print(f"🔎 '{document_id}' ID'li doküman bulundu.")
            return doc.to_dict()
        else:
            # print(f"⚠️ '{document_id}' ID'li doküman bulunamadı.")
            return None
    except Exception as e:
        print(f"❌ Hata: Doküman okunamadı. Detay: {e}")
        return None

def get_all_documents(db, collection_name):
    """
    Bir koleksiyondaki tüm dokümanları getirir.
    """
    try:
        if db is None:
            print("❌ Hata: Firebase istemcisi başlatılmamış.")
            return []

        docs = db.collection(collection_name).stream()
        return {doc.id: doc.to_dict() for doc in docs}
    except Exception as e:
        print(f"❌ Hata: Tüm dokümanlar okunamadı. Detay: {e}")
        return {}


def update_document(db, collection_name, document_id, data):
    """
    Mevcut bir dokümanın belirli alanlarını günceller.
    """
    try:
        if db is None:
            print("❌ Hata: Firebase istemcisi başlatılmamış.")
            return False

        db.collection(collection_name).document(document_id).update(data)
        # print(f"🔄 '{document_id}' ID'li doküman güncellendi.")
        return True
    except Exception as e:
        print(f"❌ Hata: Doküman güncellenemedi. Detay: {e}")
        return False


def delete_document(db, collection_name, document_id):
    """
    Belirtilen ID'ye sahip dokümanı koleksiyondan siler.
    """
    try:
        if db is None:
            print("❌ Hata: Firebase istemcisi başlatılmamış.")
            return False

        db.collection(collection_name).document(document_id).delete()
        # print(f"🗑️ '{document_id}' ID'li doküman silindi.")
        return True
    except Exception as e:
        print(f"❌ Hata: Doküman silinemedi. Detay: {e}")
        return False

# Ekleme işlemi denemesi - Bu kısım test amaçlıdır, canlı kodda kaldırılabilir
# client = initialize_firebase()
# if client:
#     data = {
#         "url": "denemeLink",
#         "is_active": False
#     }
#     create_document(client, "trainwagon_test", data)
# else:
#     print("Firebase istemcisi başlatılamadığı için doküman oluşturulamadı.")