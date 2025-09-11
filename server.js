const express = require('express');
const cors = require('cors');
require('dotenv').config();

// Import routes and middleware
const documentRoutes = require('./routes/documents');
const chatRoutes = require("./routes/chats")
const { errorHandler, notFoundHandler } = require('./middleware/errorHandler');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Routes
app.use('/documents', documentRoutes);  
app.use('/chats', chatRoutes); 

// Error handling middleware
app.use(errorHandler);

// 404 handler (must be last)
app.use(notFoundHandler);

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);

});

module.exports = app;