const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  selectFiles: () => ipcRenderer.invoke('select-files'),
  saveFile: (content, filename) => ipcRenderer.invoke('save-file', { content, filename }),
  getDownloadsPath: () => ipcRenderer.invoke('get-downloads-path')
});
