import React from 'react';
import './App.css';
import VoicePdfInput from './components/VoicePdfInput';
import { motion } from 'framer-motion';
import Aurora from './components/Aurora';

function App() {
  return (
    <motion.div
      className="App"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
    >
     <div className="absolute inset-0 -z-10">
        <Aurora />
      </div>
      <header className="App-header">
        <h1>ClauseWise</h1>
      </header>

      <main>
        <VoicePdfInput />
      </main>
    </motion.div>
  );
}

export default App;