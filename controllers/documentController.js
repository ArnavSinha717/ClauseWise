const documentService = require('../services/documentService');

class DocumentController {
  // Upload document
  async uploadDocument(req, res) {
    try {
      if (!req.file) {
        return res.status(400).json({ 
          error: 'No file uploaded',
          message: 'Please select a file to upload' 
        });
      }

      // Check if extracted content is provided (from frontend)
      const extractedContent = req.body.extractedContent || null;

      const result = await documentService.uploadDocument(req.file, extractedContent);

      res.status(200).json({
        success: true,
        message: 'File uploaded successfully',
        ...result
      });

    } catch (error) {
      console.error('Upload error:', error);
      res.status(500).json({ 
        error: 'Upload failed',
        message: error.message 
      });
    }
  }

  // Update document content (called by frontend after PDF extraction)
  async updateDocumentContent(req, res) {
    try {
      const { docId } = req.params;
      const { extractedContent } = req.body;

      if (!extractedContent) {
        return res.status(400).json({
          error: 'Missing content',
          message: 'extractedContent is required'
        });
      }

      const result = await documentService.updateDocumentContent(docId, extractedContent);

      res.json({
        success: true,
        ...result
      });

    } catch (error) {
      console.error('Error updating content:', error);
      res.status(500).json({
        error: 'Failed to update content',
        message: error.message
      });
    }
  }

  // Update AI analysis results
  async updateAIAnalysis(req, res) {
    try {
      const { docId } = req.params;
      const { analysisResult } = req.body;

      if (!analysisResult) {
        return res.status(400).json({
          error: 'Missing analysis',
          message: 'analysisResult is required'
        });
      }

      const result = await documentService.updateAIAnalysis(docId, analysisResult);

      res.json({
        success: true,
        ...result
      });

    } catch (error) {
      console.error('Error updating AI analysis:', error);
      res.status(500).json({
        error: 'Failed to update AI analysis',
        message: error.message
      });
    }
  }

  // Get documents ready for AI analysis
  async getDocumentsForAI(req, res) {
    try {
      const documents = await documentService.getDocumentsForAIAnalysis();

      res.json({
        success: true,
        documents: documents,
        count: documents.length
      });

    } catch (error) {
      console.error('Error fetching documents for AI:', error);
      res.status(500).json({
        error: 'Failed to fetch documents for AI',
        message: error.message
      });
    }
  }

  // Get all documents
  async getAllDocuments(req, res) {
    try {
      const documents = await documentService.getAllDocuments();

      res.json({
        success: true,
        documents: documents,
        count: documents.length
      });

    } catch (error) {
      console.error('Error fetching documents:', error);
      res.status(500).json({ 
        error: 'Failed to fetch documents',
        message: error.message 
      });
    }
  }

  // Get specific document by ID
  async getDocumentById(req, res) {
    try {
      const docId = req.params.id;
      const document = await documentService.getDocumentById(docId);

      if (!document) {
        return res.status(404).json({ 
          error: 'Document not found',
          message: `No document found with ID: ${docId}` 
        });
      }

      res.json({
        success: true,
        document: document
      });

    } catch (error) {
      console.error('Error fetching document:', error);
      res.status(500).json({ 
        error: 'Failed to fetch document',
        message: error.message 
      });
    }
  }

  // Health check
  healthCheck(req, res) {
    res.json({ status: 'OK', message: 'Backend is running' });
  }
}

module.exports = new DocumentController();