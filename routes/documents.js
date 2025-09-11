const express = require('express');
const documentController = require('../controllers/documentController');
const upload = require('../middleware/upload');

const router = express.Router();

// Health check
router.get('/health', documentController.healthCheck);

// Upload document
router.post('/upload', upload.single('document'), documentController.uploadDocument);

// Update document content (called by frontend after PDF extraction)
router.put('/documents/:docId/content', documentController.updateDocumentContent);

// Update AI analysis results (called by AI service)
router.put('/documents/:docId/analysis', documentController.updateAIAnalysis);

// Get all documents
router.get('/documents', documentController.getAllDocuments);

// Get documents ready for AI analysis
router.get('/documents/ai-ready', documentController.getDocumentsForAI);

// Get specific document by ID
router.get('/documents/:id', documentController.getDocumentById);

module.exports = router;