const chatService = require('../services/chatService');

class ChatController {
  // Create a new chat session
  async createChatSession(req, res) {
    try {
      const { documentId, language, sessionName } = req.body;

      if (!documentId) {
        return res.status(400).json({
          error: 'Missing required field',
          message: 'documentId is required'
        });
      }

      if (!language) {
        return res.status(400).json({
          error: 'Missing required field',
          message: 'language is required'
        });
      }

      const chatSession = await chatService.createChatSession(documentId, language, sessionName);

      res.status(201).json({
        success: true,
        message: 'Chat session created successfully',
        chatSession: chatSession
      });

    } catch (error) {
      console.error('Error creating chat session:', error);
      res.status(500).json({
        error: 'Failed to create chat session',
        message: error.message
      });
    }
  }

  // Add a message to chat
  async addMessage(req, res) {
    try {
      const { chatId } = req.params;
      const { message, sender, messageType } = req.body;

      if (!message) {
        return res.status(400).json({
          error: 'Missing required field',
          message: 'message is required'
        });
      }

      const newMessage = await chatService.addMessage(
        chatId, 
        message, 
        sender || 'user',
        messageType || 'text'
      );

      res.status(201).json({
        success: true,
        message: 'Message added successfully',
        messageData: newMessage
      });

    } catch (error) {
      console.error('Error adding message:', error);
      res.status(500).json({
        error: 'Failed to add message',
        message: error.message
      });
    }
  }

  // Get chat messages
  async getChatMessages(req, res) {
    try {
      const { chatId } = req.params;
      const { limit } = req.query;

      const messages = await chatService.getChatMessages(chatId, limit ? parseInt(limit) : 50);

      res.json({
        success: true,
        messages: messages,
        count: messages.length
      });

    } catch (error) {
      console.error('Error getting messages:', error);
      res.status(500).json({
        error: 'Failed to get messages',
        message: error.message
      });
    }
  }

  // Get chat session details
  async getChatSession(req, res) {
    try {
      const { chatId } = req.params;

      const chatSession = await chatService.getChatSession(chatId);

      if (!chatSession) {
        return res.status(404).json({
          error: 'Chat not found',
          message: `No chat session found with ID: ${chatId}`
        });
      }

      res.json({
        success: true,
        chatSession: chatSession
      });

    } catch (error) {
      console.error('Error getting chat session:', error);
      res.status(500).json({
        error: 'Failed to get chat session',
        message: error.message
      });
    }
  }

  // Get all chats for a document
  async getDocumentChats(req, res) {
    try {
      const { documentId } = req.params;

      const chats = await chatService.getDocumentChats(documentId);

      res.json({
        success: true,
        chats: chats,
        count: chats.length
      });

    } catch (error) {
      console.error('Error getting document chats:', error);
      res.status(500).json({
        error: 'Failed to get document chats',
        message: error.message
      });
    }
  }

  // Get chats by language
  async getChatsByLanguage(req, res) {
    try {
      const { language } = req.params;

      const chats = await chatService.getChatsByLanguage(language);

      res.json({
        success: true,
        chats: chats,
        count: chats.length,
        language: language
      });

    } catch (error) {
      console.error('Error getting chats by language:', error);
      res.status(500).json({
        error: 'Failed to get chats by language',
        message: error.message
      });
    }
  }

  // Update chat session
  async updateChatSession(req, res) {
    try {
      const { chatId } = req.params;
      const updateData = req.body;

      const result = await chatService.updateChatSession(chatId, updateData);

      res.json({
        success: true,
        ...result
      });

    } catch (error) {
      console.error('Error updating chat session:', error);
      res.status(500).json({
        error: 'Failed to update chat session',
        message: error.message
      });
    }
  }

  // Delete chat session
  async deleteChatSession(req, res) {
    try {
      const { chatId } = req.params;

      const result = await chatService.deleteChatSession(chatId);

      res.json({
        success: true,
        ...result
      });

    } catch (error) {
      console.error('Error deleting chat session:', error);
      res.status(500).json({
        error: 'Failed to delete chat session',
        message: error.message
      });
    }
  }
}

module.exports = new ChatController();