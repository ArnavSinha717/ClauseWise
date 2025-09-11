const path = require('path');

// Helper function to generate unique filename
const generateFileName = (originalName) => {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substring(2, 15);
  const extension = path.extname(originalName);
  const baseName = path.basename(originalName, extension);
  return `${baseName}_${timestamp}_${random}${extension}`;
};

module.exports = {
  generateFileName
};