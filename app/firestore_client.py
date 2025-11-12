import os
from google.cloud import firestore

def get_client():
    emulator = os.environ.get("FIRESTORE_EMULATOR_HOST")
    if emulator:
        os.environ["FIRESTORE_EMULATOR_HOST"] = emulator
    return firestore.Client(project=os.environ.get("GCLOUD_PROJECT", "demo-project"))

def create_user_doc(user_dict: dict):
    client = get_client()
    users = client.collection("users")
    doc_ref = users.document()
    doc_ref.set(user_dict)
    return doc_ref.id
