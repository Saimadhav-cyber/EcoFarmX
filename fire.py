import os
import firebase_admin
from firebase_admin import credentials, firestore

# Load service account from environment variable
cred_path = os.environ.get("FIREBASE_CRED_PATH")
cred = credentials.Certificate(cred_path)

# Initialize Firebase
firebase_admin.initialize_app(cred)
print("Firebase initialized successfully!")

# Example: connect to Firestore
db = firestore.client()

# Example: add a document
doc_ref = db.collection('test').document('example')
doc_ref.set({'message': 'Hello Firebase from Python!'})

print("Document added to Firestore!")
