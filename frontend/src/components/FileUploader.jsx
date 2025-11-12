import React, { useState, useRef } from 'react';

const FileUploader = ({ onFilesAdded }) => {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);

  const handleDragEnter = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const droppedFiles = Array.from(e.dataTransfer.files);
    handleFiles(droppedFiles);
  };

  const handleFileSelect = (e) => {
    const selectedFiles = Array.from(e.target.files);
    handleFiles(selectedFiles);
    // Reset input so same file can be selected again
    e.target.value = '';
  };

  const handleFiles = (fileList) => {
    // Filter for supported file types
    const supportedExtensions = ['pdf', 'png', 'jpg', 'jpeg', 'pptx', 'ppt', 'tiff', 'bmp'];
    const validFiles = fileList.filter(file => {
      const ext = file.name.split('.').pop().toLowerCase();
      return supportedExtensions.includes(ext);
    });

    if (validFiles.length > 0) {
      onFilesAdded(validFiles);
    }

    if (validFiles.length < fileList.length) {
      alert('Some files were skipped. Only PDF, images, and PPTX files are supported.');
    }
  };

  const handleBrowseClick = () => {
    fileInputRef.current?.click();
  };

  const handleElectronSelect = async () => {
    if (window.electronAPI) {
      const result = await window.electronAPI.selectFiles();
      if (!result.canceled && result.filePaths.length > 0) {
        // Convert file paths to File objects
        // This is a simplified version; in production you'd read the files
        const files = result.filePaths.map(path => {
          const filename = path.split('/').pop();
          return new File([], filename, { type: 'application/octet-stream' });
        });
        handleFiles(files);
      }
    } else {
      handleBrowseClick();
    }
  };

  return (
    <div className="card">
      <div
        onDragEnter={handleDragEnter}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`
          border-2 border-dashed rounded-apple p-12
          transition-all duration-200 ease-out
          ${isDragging
            ? 'border-apple-blue bg-blue-50'
            : 'border-apple-gray-300 bg-apple-gray-50 hover:bg-apple-gray-100'
          }
        `}
      >
        <div className="text-center">
          {/* Icon */}
          <div className="mb-4">
            <svg
              className="mx-auto h-16 w-16 text-apple-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            </svg>
          </div>

          {/* Text */}
          <h3 className="text-lg font-semibold text-apple-gray-900 mb-2">
            Drop files here
          </h3>
          <p className="text-sm text-apple-gray-500 mb-6">
            or click to browse from your computer
          </p>

          {/* Buttons */}
          <div className="flex gap-3 justify-center">
            <button
              onClick={handleBrowseClick}
              className="btn-primary"
            >
              Browse Files
            </button>
            {window.electronAPI && (
              <button
                onClick={handleElectronSelect}
                className="btn-secondary"
              >
                Select Files
              </button>
            )}
          </div>

          {/* Supported formats */}
          <p className="text-xs text-apple-gray-400 mt-6">
            Supported: PDF, PNG, JPG, PPTX, TIFF, BMP
          </p>
        </div>
      </div>

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept=".pdf,.png,.jpg,.jpeg,.pptx,.ppt,.tiff,.bmp"
        onChange={handleFileSelect}
        className="hidden"
      />
    </div>
  );
};

export default FileUploader;
