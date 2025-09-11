const admin = require('firebase-admin');

// Initialize Firebase Admin SDK with service account
const serviceAccount = require('../serviceAccountKey.json');

// Use the correct bucket name format for your project
const storageBucket = process.env.FIREBASE_STORAGE_BUCKET;

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
  storageBucket: storageBucket
});

const bucket = admin.storage().bucket();
const db = admin.firestore();

// Log the bucket name for debugging
console.log(`Using bucket: ${storageBucket}`);

module.exports = {
  admin,
  bucket,
  db
};