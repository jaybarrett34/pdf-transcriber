import React, { useState } from 'react';
import FileUploader from './components/FileUploader';
import ProcessingQueue from './components/ProcessingQueue';
import Settings from './components/Settings';

function App() {
  const [files, setFiles] = useState([]);
  const [useOllamaCleanup, setUseOllamaCleanup] = useState(false);
  const [activeTab, setActiveTab] = useState('upload'); // 'upload' or 'settings'

  const handleFilesAdded = (newFiles) => {
    const fileObjects = newFiles.map(file => ({
      id: `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      file: file,
      name: file.name,
      size: file.size,
      status: 'pending', // pending, uploading, processing, complete, error
      progress: 0,
      outputFile: null,
      error: null,
      metadata: null
    }));

    setFiles(prev => [...prev, ...fileObjects]);
  };

  const handleRemoveFile = (fileId) => {
    setFiles(prev => prev.filter(f => f.id !== fileId));
  };

  const updateFileStatus = (fileId, updates) => {
    setFiles(prev => prev.map(f =>
      f.id === fileId ? { ...f, ...updates } : f
    ));
  };

  return (
    <div className="min-h-screen bg-apple-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-apple-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-semibold text-apple-gray-900">
                PDF Transcriber
              </h1>
              <p className="text-sm text-apple-gray-500 mt-1">
                Self-hosted OCR and document transcription
              </p>
            </div>

            {/* Tab Navigation */}
            <div className="flex gap-2">
              <button
                onClick={() => setActiveTab('upload')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  activeTab === 'upload'
                    ? 'bg-apple-blue text-white'
                    : 'text-apple-gray-600 hover:bg-apple-gray-100'
                }`}
              >
                Upload
              </button>
              <button
                onClick={() => setActiveTab('settings')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  activeTab === 'settings'
                    ? 'bg-apple-blue text-white'
                    : 'text-apple-gray-600 hover:bg-apple-gray-100'
                }`}
              >
                Settings
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {activeTab === 'upload' ? (
          <div className="space-y-6">
            {/* Ollama Cleanup Toggle */}
            <div className="card flex items-center justify-between">
              <div>
                <h3 className="font-medium text-apple-gray-900">
                  Use Ollama for Markdown Cleanup
                </h3>
                <p className="text-sm text-apple-gray-500 mt-1">
                  Clean up and improve markdown formatting using AI
                </p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={useOllamaCleanup}
                  onChange={(e) => setUseOllamaCleanup(e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-apple-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-apple-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-apple-blue"></div>
              </label>
            </div>

            {/* File Uploader */}
            <FileUploader onFilesAdded={handleFilesAdded} />

            {/* Processing Queue */}
            {files.length > 0 && (
              <ProcessingQueue
                files={files}
                onRemoveFile={handleRemoveFile}
                updateFileStatus={updateFileStatus}
                useOllamaCleanup={useOllamaCleanup}
              />
            )}
          </div>
        ) : (
          <Settings />
        )}
      </main>

      {/* Footer */}
      <footer className="fixed bottom-0 left-0 right-0 bg-white border-t border-apple-gray-200 py-3">
        <div className="max-w-7xl mx-auto px-6">
          <p className="text-xs text-apple-gray-500 text-center">
            PDF Transcriber v1.0.0 • Self-hosted OCR Solution
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
