import React from 'react';

const ProgressBar = ({ progress = 0 }) => {
  return (
    <div className="w-full bg-apple-gray-200 rounded-full h-2 overflow-hidden">
      <div
        className="h-full bg-apple-blue transition-all duration-300 ease-out"
        style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
      >
        <div className="h-full w-full bg-gradient-to-r from-transparent via-white/30 to-transparent animate-shimmer" />
      </div>
    </div>
  );
};

export default ProgressBar;
