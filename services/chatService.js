const { admin, db } = require('../config/firebase');

class ChatService {
  // Create a new chat session for a document
  async createChatSession(documentId, language = 'en', sessionName = null) {
    try {
      // Verify document exists
      const docRef = await db.collection('documents').doc(documentId).get();
      if (!docRef.exists) {
        throw new Error('Document not found');
      }

      const chatData = {
        documentId: documentId,
        language: language, // Mandatory field
        sessionName: sessionName || `Chat Session - ${new Date().toLocaleString()}`,
        createdAt: admin.firestore.FieldValue.serverTimestamp(),
        lastMessageAt: admin.firestore.FieldValue.serverTimestamp(),
        messageCount: 0,
        isActive: true,
        // Optional: Add user info when auth is implemented
        userId: null, // Will be populated when auth is added
        userName: 'Anonymous' // Temporary for now
      };

      const chatRef = await db.collection('chats').add(chatData);

      return {
        chatId: chatRef.id,
        ...chatData,
        createdAt: new Date(),
        lastMessageAt: new Date()
      };
    } catch (error) {
      throw new Error(`Failed to create chat session: ${error.message}`);
    }
  }

  // Add a message to a chat session
  async addMessage(chatId, message, sender = 'user', messageType = 'text') {
    try {
      // Verify chat exists
      const chatRef = await db.collection('chats').doc(chatId).get();
      if (!chatRef.exists) {
        throw new Error('Chat session not found');
      }

      const chatData = chatRef.data();

      // Create message data
      const messageData = {
        chatId: chatId,
        message: message,
        sender: sender, // 'user' or 'ai'
        messageType: messageType, // 'text', 'analysis', 'summary', etc.
        language: chatData.language, // Inherit from chat session
        timestamp: admin.firestore.FieldValue.serverTimestamp(),
        // Optional metadata
        metadata: {
          wordCount: message.split(' ').length,
          characterCount: message.length
        }
      };

      // Add message to messages subcollection
      const messageRef = await db.collection('chats').doc(chatId)
        .collection('messages').add(messageData);

      // Update chat session stats
      await db.collection('chats').doc(chatId).update({
        lastMessageAt: admin.firestore.FieldValue.serverTimestamp(),
        messageCount: admin.firestore.FieldValue.increment(1)
      });

      return {
        messageId: messageRef.id,
        ...messageData,
        timestamp: new Date()
      };
    } catch (error) {
      throw new Error(`Failed to add message: ${error.message}`);
    }
  }

  // Get all messages for a chat session
  async getChatMessages(chatId, limit = 50) {
    try {
      const messagesRef = await db.collection('chats').doc(chatId)
        .collection('messages')
        .orderBy('timestamp', 'asc')
        .limit(limit)
        .get();

      const messages = [];
      messagesRef.forEach((doc) => {
        const data = doc.data();
        messages.push({
          messageId: doc.id,
          ...data,
          timestamp: data.timestamp ? data.timestamp.toDate() : null
        });
      });

      return messages;
    } catch (error) {
      throw new Error(`Failed to get messages: ${error.message}`);
    }
  }

  // Get chat session details
  async getChatSession(chatId) {
    try {
      const chatRef = await db.collection('chats').doc(chatId).get();
      
      if (!chatRef.exists) {
        return null;
      }

      const data = chatRef.data();
      return {
        chatId: chatRef.id,
        ...data,
        createdAt: data.createdAt ? data.createdAt.toDate() : null,
        lastMessageAt: data.lastMessageAt ? data.lastMessageAt.toDate() : null
      };
    } catch (error) {
      throw new Error(`Failed to get chat session: ${error.message}`);
    }
  }

  // Get all chat sessions for a document
  async getDocumentChats(documentId) {
    try {
      const chatsRef = await db.collection('chats')
        .where('documentId', '==', documentId)
        .orderBy('lastMessageAt', 'desc')
        .get();

      const chats = [];
      chatsRef.forEach((doc) => {
        const data = doc.data();
        chats.push({
          chatId: doc.id,
          ...data,
          createdAt: data.createdAt ? data.createdAt.toDate() : null,
          lastMessageAt: data.lastMessageAt ? data.lastMessageAt.toDate() : null
        });
      });

      return chats;
    } catch (error) {
      throw new Error(`Failed to get document chats: ${error.message}`);
    }
  }

  // Get chat sessions by language
  async getChatsByLanguage(language) {
    try {
      const chatsRef = await db.collection('chats')
        .where('language', '==', language)
        .orderBy('lastMessageAt', 'desc')
        .get();

      const chats = [];
      chatsRef.forEach((doc) => {
        const data = doc.data();
        chats.push({
          chatId: doc.id,
          ...data,
          createdAt: data.createdAt ? data.createdAt.toDate() : null,
          lastMessageAt: data.lastMessageAt ? data.lastMessageAt.toDate() : null
        });
      });

      return chats;
    } catch (error) {
      throw new Error(`Failed to get chats by language: ${error.message}`);
    }
  }

  // Update chat session (e.g., change name, language, etc.)
  async updateChatSession(chatId, updateData) {
    try {
      const allowedFields = ['sessionName', 'language', 'isActive'];
      const filteredData = {};
      
      Object.keys(updateData).forEach(key => {
        if (allowedFields.includes(key)) {
          filteredData[key] = updateData[key];
        }
      });

      filteredData.updatedAt = admin.firestore.FieldValue.serverTimestamp();

      await db.collection('chats').doc(chatId).update(filteredData);

      return {
        success: true,
        message: 'Chat session updated successfully'
      };
    } catch (error) {
      throw new Error(`Failed to update chat session: ${error.message}`);
    }
  }

  // Delete a chat session (and all its messages)
  async deleteChatSession(chatId) {
    try {
      // Delete all messages first
      const messagesRef = await db.collection('chats').doc(chatId)
        .collection('messages').get();

      const batch = db.batch();
      messagesRef.docs.forEach((doc) => {
        batch.delete(doc.ref);
      });

      // Delete the chat document
      batch.delete(db.collection('chats').doc(chatId));

      await batch.commit();

      return {
        success: true,
        message: 'Chat session deleted successfully'
      };
    } catch (error) {
      throw new Error(`Failed to delete chat session: ${error.message}`);
    }
  }
}

module.exports = new ChatService();