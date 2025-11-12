import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000';

const Settings = () => {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [serverStatus, setServerStatus] = useState('checking');

  useEffect(() => {
    fetchConfig();
    checkServerStatus();
  }, []);

  const fetchConfig = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/config`);
      setConfig(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching config:', error);
      setLoading(false);
    }
  };

  const checkServerStatus = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/`);
      if (response.data.status === 'running') {
        setServerStatus('online');
      } else {
        setServerStatus('offline');
      }
    } catch (error) {
      setServerStatus('offline');
    }
  };

  if (loading) {
    return (
      <div className="card">
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-apple-blue mx-auto"></div>
          <p className="mt-4 text-apple-gray-500">Loading settings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Server Status */}
      <div className="card">
        <h2 className="text-xl font-semibold text-apple-gray-900 mb-4">
          Server Status
        </h2>
        <div className="flex items-center gap-3">
          <div className={`w-3 h-3 rounded-full ${
            serverStatus === 'online' ? 'bg-green-500' :
            serverStatus === 'offline' ? 'bg-red-500' :
            'bg-yellow-500'
          }`} />
          <span className="font-medium text-apple-gray-900">
            {serverStatus === 'online' ? 'Backend Online' :
             serverStatus === 'offline' ? 'Backend Offline' :
             'Checking...'}
          </span>
          <button
            onClick={checkServerStatus}
            className="ml-auto btn-secondary text-sm py-1.5"
          >
            Refresh
          </button>
        </div>
        <p className="text-sm text-apple-gray-500 mt-2">
          {API_BASE_URL}
        </p>
      </div>

      {/* Configuration */}
      {config && (
        <>
          {/* OCR Settings */}
          <div className="card">
            <h2 className="text-xl font-semibold text-apple-gray-900 mb-4">
              OCR Configuration
            </h2>
            <div className="space-y-3">
              <div>
                <label className="text-sm font-medium text-apple-gray-700">
                  Supported Languages
                </label>
                <div className="mt-2 flex flex-wrap gap-2">
                  {config.ocr_languages?.map(lang => (
                    <span
                      key={lang}
                      className="px-3 py-1 bg-apple-gray-100 text-apple-gray-700 text-sm rounded-full"
                    >
                      {lang}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Ollama Settings */}
          <div className="card">
            <h2 className="text-xl font-semibold text-apple-gray-900 mb-4">
              Ollama Configuration
            </h2>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-apple-gray-700">
                  Status
                </span>
                <span className={`px-3 py-1 text-sm rounded-full ${
                  config.ollama_enabled
                    ? 'bg-green-100 text-green-700'
                    : 'bg-red-100 text-red-700'
                }`}>
                  {config.ollama_enabled ? 'Enabled' : 'Disabled'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-apple-gray-700">
                  Default Model
                </span>
                <span className="text-sm text-apple-gray-600 font-mono">
                  {config.ollama_model || 'Not configured'}
                </span>
              </div>
            </div>

            {!config.ollama_enabled && (
              <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                <p className="text-sm text-yellow-800">
                  Ollama is disabled. To enable, make sure Ollama is installed and running on your system.
                </p>
              </div>
            )}
          </div>

          {/* Supported Formats */}
          <div className="card">
            <h2 className="text-xl font-semibold text-apple-gray-900 mb-4">
              Supported File Formats
            </h2>
            <div className="flex flex-wrap gap-2">
              {config.supported_formats?.map(format => (
                <span
                  key={format}
                  className="px-3 py-1 bg-apple-gray-100 text-apple-gray-700 text-sm rounded-full uppercase"
                >
                  .{format}
                </span>
              ))}
            </div>
          </div>

          {/* System Info */}
          <div className="card">
            <h2 className="text-xl font-semibold text-apple-gray-900 mb-4">
              System Information
            </h2>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-apple-gray-600">Backend API</span>
                <span className="text-apple-gray-900 font-mono">{API_BASE_URL}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-apple-gray-600">Platform</span>
                <span className="text-apple-gray-900">{navigator.platform}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-apple-gray-600">User Agent</span>
                <span className="text-apple-gray-900 truncate max-w-xs">
                  {navigator.userAgent.split(' ')[0]}
                </span>
              </div>
            </div>
          </div>
        </>
      )}

      {/* Help */}
      <div className="card bg-blue-50 border border-blue-200">
        <h3 className="font-semibold text-blue-900 mb-2">
          Need Help?
        </h3>
        <p className="text-sm text-blue-800">
          Make sure the backend server is running before processing files.
          Start it with: <code className="bg-blue-100 px-2 py-0.5 rounded">python backend/main.py</code>
        </p>
      </div>
    </div>
  );
};

export default Settings;
