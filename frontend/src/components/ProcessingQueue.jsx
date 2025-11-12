import React, { useEffect, useState } from 'react';
import axios from 'axios';
import ProgressBar from './ProgressBar';

const API_BASE_URL = 'http://127.0.0.1:8000';

const ProcessingQueue = ({ files, onRemoveFile, updateFileStatus, useOllamaCleanup }) => {
  const [processing, setProcessing] = useState(false);

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const uploadFile = async (fileObj) => {
    try {
      updateFileStatus(fileObj.id, { status: 'uploading' });

      const formData = new FormData();
      formData.append('file', fileObj.file);

      const response = await axios.post(`${API_BASE_URL}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.data.success) {
        return response.data.file_id;
      } else {
        throw new Error(response.data.error || 'Upload failed');
      }
    } catch (error) {
      updateFileStatus(fileObj.id, {
        status: 'error',
        error: error.message
      });
      throw error;
    }
  };

  const processFile = async (fileObj, fileId) => {
    try {
      updateFileStatus(fileObj.id, { status: 'processing', progress: 0 });

      // Start processing
      await axios.post(`${API_BASE_URL}/process/${fileId}`, null, {
        params: {
          use_ollama_cleanup: useOllamaCleanup
        }
      });

      // Connect to WebSocket for progress updates
      const ws = new WebSocket(`ws://127.0.0.1:8000/ws/${fileId}`);

      ws.onopen = () => {
        console.log('WebSocket connected for', fileObj.name);
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Progress update:', data);

        updateFileStatus(fileObj.id, {
          progress: data.progress,
          status: data.stage === 'complete' ? 'complete' : 'processing'
        });

        if (data.stage === 'complete') {
          updateFileStatus(fileObj.id, {
            status: 'complete',
            progress: 100,
            outputFile: data.output_file,
            metadata: data.metadata
          });
          ws.close();
        } else if (data.stage === 'error') {
          updateFileStatus(fileObj.id, {
            status: 'error',
            error: data.message
          });
          ws.close();
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        updateFileStatus(fileObj.id, {
          status: 'error',
          error: 'Connection error'
        });
      };

      ws.onclose = () => {
        console.log('WebSocket closed for', fileObj.name);
      };

    } catch (error) {
      updateFileStatus(fileObj.id, {
        status: 'error',
        error: error.message
      });
    }
  };

  const startProcessing = async () => {
    setProcessing(true);

    const pendingFiles = files.filter(f => f.status === 'pending');

    for (const file of pendingFiles) {
      try {
        const fileId = await uploadFile(file);
        await processFile(file, fileId);
      } catch (error) {
        console.error('Error processing file:', error);
      }
    }

    setProcessing(false);
  };

  const downloadFile = async (fileObj) => {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/download/${fileObj.outputFile.replace('.md', '')}`,
        { responseType: 'blob' }
      );

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', fileObj.outputFile);
      document.body.appendChild(link);
      link.click();
      link.remove();

      // If Electron API available, save to downloads folder
      if (window.electronAPI) {
        const text = await response.data.text();
        await window.electronAPI.saveFile(text, fileObj.outputFile);
      }
    } catch (error) {
      console.error('Error downloading file:', error);
      alert('Failed to download file: ' + error.message);
    }
  };

  const pendingCount = files.filter(f => f.status === 'pending').length;
  const processingCount = files.filter(f => ['uploading', 'processing'].includes(f.status)).length;
  const completeCount = files.filter(f => f.status === 'complete').length;

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold text-apple-gray-900">
            Processing Queue
          </h2>
          <p className="text-sm text-apple-gray-500 mt-1">
            {pendingCount} pending • {processingCount} processing • {completeCount} complete
          </p>
        </div>

        {pendingCount > 0 && (
          <button
            onClick={startProcessing}
            disabled={processing}
            className="btn-primary"
          >
            {processing ? 'Processing...' : `Process ${pendingCount} File${pendingCount > 1 ? 's' : ''}`}
          </button>
        )}
      </div>

      {/* File List */}
      <div className="space-y-3">
        {files.map(file => (
          <div
            key={file.id}
            className="border border-apple-gray-200 rounded-lg p-4 hover:bg-apple-gray-50 transition-colors"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1 min-w-0 mr-4">
                {/* File Info */}
                <div className="flex items-center gap-2 mb-2">
                  <h4 className="font-medium text-apple-gray-900 truncate">
                    {file.name}
                  </h4>
                  <span className="text-xs text-apple-gray-500">
                    {formatFileSize(file.size)}
                  </span>
                </div>

                {/* Status */}
                <div className="flex items-center gap-2 mb-2">
                  <StatusBadge status={file.status} />
                  {file.error && (
                    <span className="text-xs text-red-600">{file.error}</span>
                  )}
                </div>

                {/* Progress Bar */}
                {['uploading', 'processing'].includes(file.status) && (
                  <ProgressBar progress={file.progress} />
                )}

                {/* Metadata */}
                {file.metadata && (
                  <p className="text-xs text-apple-gray-500 mt-2">
                    {file.metadata.total_pages} pages • {file.metadata.file_type}
                  </p>
                )}
              </div>

              {/* Actions */}
              <div className="flex gap-2">
                {file.status === 'complete' && (
                  <button
                    onClick={() => downloadFile(file)}
                    className="px-3 py-1.5 bg-apple-blue text-white text-sm rounded-lg hover:bg-blue-600 transition-colors"
                  >
                    Download
                  </button>
                )}
                {file.status === 'pending' && (
                  <button
                    onClick={() => onRemoveFile(file.id)}
                    className="px-3 py-1.5 bg-apple-gray-200 text-apple-gray-700 text-sm rounded-lg hover:bg-apple-gray-300 transition-colors"
                  >
                    Remove
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const StatusBadge = ({ status }) => {
  const config = {
    pending: { label: 'Pending', color: 'bg-apple-gray-200 text-apple-gray-700' },
    uploading: { label: 'Uploading', color: 'bg-blue-100 text-blue-700' },
    processing: { label: 'Processing', color: 'bg-blue-100 text-blue-700' },
    complete: { label: 'Complete', color: 'bg-green-100 text-green-700' },
    error: { label: 'Error', color: 'bg-red-100 text-red-700' },
  };

  const { label, color } = config[status] || config.pending;

  return (
    <span className={`px-2 py-1 text-xs font-medium rounded ${color}`}>
      {label}
    </span>
  );
};

export default ProcessingQueue;
