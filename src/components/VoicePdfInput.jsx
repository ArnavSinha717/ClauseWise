import React, { useEffect, useRef, useState } from "react";
// Import the standard, up-to-date version of the library.
import * as pdfjsLib from "pdfjs-dist";
import { motion, AnimatePresence } from "framer-motion";
import "./VoicePdfInput.css";

// Point to the local worker file in your public folder. This is the most reliable method.
pdfjsLib.GlobalWorkerOptions.workerSrc = "/pdf.worker.min.js";

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition || null;

const SendIcon = () => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M4.5 11.5L21 3L12.5 21L10.5 13.5L4.5 11.5Z" stroke="white" strokeWidth="2" strokeLinejoin="round"/>
    </svg>
);

export default function VoicePdfInput({ onResult = (data) => console.log("result", data) }) {
  const [lang, setLang] = useState("en");
  // eslint-disable-next-line no-unused-vars
  const [pdfFile, setPdfFile] = useState(null);
  const [pdfText, setPdfText] = useState("");
  const [micActive, setMicActive] = useState(false);
  const [transcript, setTranscript] = useState("");
  const recognitionRef = useRef(null);

  useEffect(() => {
    if (!SpeechRecognition) {
      console.error("Speech Recognition is not supported in this browser.");
      return;
    }
    const recog = new SpeechRecognition();
    recog.lang = lang === 'en' ? 'en-IN' : 'hi-IN';
    recog.interimResults = true;
    recog.continuous = true;

    recog.onresult = (e) => {
      let finalTranscript = "";
      for (let i = e.resultIndex; i < e.results.length; ++i) {
        if (e.results[i].isFinal) {
          finalTranscript += e.results[i][0].transcript;
        }
      }
      if (finalTranscript) {
        setTranscript(prev => (prev ? prev + ' ' + finalTranscript : finalTranscript).trim());
      }
    };

    recog.onstart = () => setMicActive(true);
    recog.onerror = (event) => {
        console.error("Speech recognition error:", event.error);
        setMicActive(false);
    };
    recog.onend = () => setMicActive(false);
    
    recognitionRef.current = recog;
    
    return () => recog.stop();
  }, [lang]);

  function toggleMic() {
    if (!recognitionRef.current) return;
    if (micActive) {
      recognitionRef.current.stop();
    } else {
      setTranscript("");
      recognitionRef.current.start();
    }
  }

  async function extractPdfText(file) {
    try {
      const arrayBuffer = await file.arrayBuffer();
      const loadingTask = pdfjsLib.getDocument({ data: arrayBuffer });
      const pdf = await loadingTask.promise;
      
      const textPromises = [];
      for (let i = 1; i <= pdf.numPages; i++) {
        textPromises.push(
          pdf.getPage(i).then(page => {
            return page.getTextContent().then(content => {
              return content.items.map(item => item.str).join(" ");
            });
          })
        );
      }
      
      const pageTexts = await Promise.all(textPromises);
      const fullText = pageTexts.join("\n\n");
      
      setPdfText(fullText);
      setTranscript("");
    } catch (error) {
      console.error("Error extracting PDF text:", error);
      alert("Failed to extract text from the PDF. The file might be corrupted, protected, or an image-based PDF.");
    }
  }

  async function onFileChange(e) {
    const file = e.target.files[0];
    if (file && file.type === "application/pdf") {
      setPdfFile(file);
      await extractPdfText(file);
    }
  }
  
  function handleSubmit() {
    const dataToSubmit = {
      text: transcript || pdfText,
      language: lang,
    };
    onResult(dataToSubmit);
    alert("Data submitted! Check the console.");
  }
  
  const handleLangToggle = () => {
    setLang(currentLang => currentLang === 'en' ? 'hi' : 'en');
  };

  return (
    <div className="imessage-container">
      <div className="messages-area">
        <AnimatePresence>
          {pdfText && (
            <motion.div
              className="message-bubble incoming"
              initial={{ opacity: 0, y: 20, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
            >
              <div className="pdf-preview">
                <h4>Extracted PDF Text</h4>
                <pre>{pdfText.slice(0, 500)}...</pre>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <motion.div
        className="input-area"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.3, ease: "easeOut" }}
      >
        <div className="input-bubble">
          <button className="lang-toggle-button" onClick={handleLangToggle}>
            {lang === 'en' ? 'EN' : 'HI'}
          </button>
          
          <textarea
            value={transcript}
            onChange={(e) => setTranscript(e.target.value)}
            placeholder="Type or speak..."
            rows={1}
          />
          
          <button className={`mic-button ${micActive ? 'active' : ''}`} onClick={toggleMic}>
            🎤
          </button>
          <label htmlFor="pdf-upload" className="file-upload-button">
            📎
          </label>
          <input id="pdf-upload" type="file" accept="application/pdf" onChange={onFileChange} />
        </div>
        <button
          className="submit-button"
          onClick={handleSubmit}
          disabled={!transcript && !pdfText}
        >
          <SendIcon />
        </button>
      </motion.div>
    </div>
  );
}