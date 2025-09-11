const express = require('express');
const chatController = require('../controllers/chatController');

const router = express.Router();

// Create a new chat session
router.post('/', chatController.createChatSession);

// Add a message to a chat
router.post('/:chatId/messages', chatController.addMessage);

// Get all messages in a chat
router.get('/:chatId/messages', chatController.getChatMessages);

// Get chat session details
router.get('/:chatId', chatController.getChatSession);

// Update chat session
router.put('/:chatId', chatController.updateChatSession);

// Delete chat session
router.delete('/:chatId', chatController.deleteChatSession);

// Get all chats for a specific document
router.get('/documents/:documentId/chats', chatController.getDocumentChats);

// Get chats by language
router.get('/language/:language', chatController.getChatsByLanguage);

module.exports = router;