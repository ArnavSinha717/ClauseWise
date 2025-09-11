const { admin, bucket, db } = require('../config/firebase');
const { generateFileName } = require('../utils/helpers');

class DocumentService {
  // Upload document to Firebase Storage
  async uploadDocument(file, extractedContent = null) {
    try {
      const fileName = generateFileName(file.originalname);
      const fileRef = bucket.file(`documents/${fileName}`);

      // Upload file to Firebase Storage
      await fileRef.save(file.buffer, {
        metadata: {
          contentType: file.mimetype,
          metadata: {
            originalName: file.originalname,
            uploadedBy: 'system'
          }
        }
      });

      // Make file publicly readable and get download URL
      await fileRef.makePublic();

      // Get the proper download URL for the new Firebase Storage domain
      const [downloadURL] = await fileRef.getSignedUrl({
        action: 'read',
        expires: '03-09-2491' // Far future date for permanent access
      });

      // Store document metadata in Firestore
      const docData = {
        originalName: file.originalname,
        fileName: fileName,
        fileSize: file.size,
        mimeType: file.mimetype,
        uploadedAt: admin.firestore.FieldValue.serverTimestamp(),
        downloadURL: downloadURL,
        status: 'uploaded',
        content: extractedContent || null, // Store extracted content
        contentExtracted: extractedContent ? true : false, // Flag for AI processing
        aiAnalysisStatus: 'pending', // Status for AI analysis
        aiAnalysisResult: null // Will store AI analysis results
      };

      const docRef = await db.collection('documents').add(docData);

      return {
        documentId: docRef.id,
        downloadURL: downloadURL,
        metadata: {
          originalName: file.originalname,
          fileSize: file.size,
          uploadedAt: new Date(),
          contentExtracted: docData.contentExtracted
        }
      };
    } catch (error) {
      throw new Error(`Upload failed: ${error.message}`);
    }
  }

  // Update document content (called by frontend after PDF extraction)
  async updateDocumentContent(docId, extractedContent) {
    try {
      const updateData = {
        content: extractedContent,
        contentExtracted: true,
        contentUpdatedAt: admin.firestore.FieldValue.serverTimestamp(),
        aiAnalysisStatus: 'ready_for_analysis' // Ready for AI to process
      };

      await db.collection('documents').doc(docId).update(updateData);

      return {
        success: true,
        message: 'Document content updated successfully'
      };
    } catch (error) {
      throw new Error(`Failed to update content: ${error.message}`);
    }
  }

  // Update AI analysis results
  async updateAIAnalysis(docId, analysisResult) {
    try {
      const updateData = {
        aiAnalysisResult: analysisResult,
        aiAnalysisStatus: 'completed',
        aiAnalyzedAt: admin.firestore.FieldValue.serverTimestamp()
      };

      await db.collection('documents').doc(docId).update(updateData);

      return {
        success: true,
        message: 'AI analysis updated successfully'
      };
    } catch (error) {
      throw new Error(`Failed to update AI analysis: ${error.message}`);
    }
  }

  // Get all documents
  async getAllDocuments() {
    try {
      const snapshot = await db.collection('documents').orderBy('uploadedAt', 'desc').get();
      const documents = [];
      
      snapshot.forEach((doc) => {
        const data = doc.data();
        documents.push({
          id: doc.id,
          ...data,
          uploadedAt: data.uploadedAt ? data.uploadedAt.toDate() : null,
          contentUpdatedAt: data.contentUpdatedAt ? data.contentUpdatedAt.toDate() : null,
          aiAnalyzedAt: data.aiAnalyzedAt ? data.aiAnalyzedAt.toDate() : null
        });
      });

      return documents;
    } catch (error) {
      throw new Error(`Failed to fetch documents: ${error.message}`);
    }
  }

  // Get document by ID
  async getDocumentById(docId) {
    try {
      const docRef = await db.collection('documents').doc(docId).get();

      if (!docRef.exists) {
        return null;
      }

      const data = docRef.data();
      return {
        id: docRef.id,
        ...data,
        uploadedAt: data.uploadedAt ? data.uploadedAt.toDate() : null,
        contentUpdatedAt: data.contentUpdatedAt ? data.contentUpdatedAt.toDate() : null,
        aiAnalyzedAt: data.aiAnalyzedAt ? data.aiAnalyzedAt.toDate() : null
      };
    } catch (error) {
      throw new Error(`Failed to fetch document: ${error.message}`);
    }
  }

  // Get documents ready for AI analysis
  async getDocumentsForAIAnalysis() {
    try {
      const snapshot = await db.collection('documents')
        .where('contentExtracted', '==', true)
        .where('aiAnalysisStatus', '==', 'ready_for_analysis')
        .get();
      
      const documents = [];
      snapshot.forEach((doc) => {
        const data = doc.data();
        documents.push({
          id: doc.id,
          content: data.content,
          originalName: data.originalName,
          mimeType: data.mimeType,
          fileSize: data.fileSize,
          uploadedAt: data.uploadedAt ? data.uploadedAt.toDate() : null
        });
      });

      return documents;
    } catch (error) {
      throw new Error(`Failed to fetch documents for AI analysis: ${error.message}`);
    }
  }
}

module.exports = new DocumentService();