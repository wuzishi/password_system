import api from './index'

export const listFiles = (passwordId, path = '/') =>
  api.get(`/sftp/${passwordId}/list`, { params: { path } })

export const mkdir = (passwordId, path) =>
  api.post(`/sftp/${passwordId}/mkdir`, { path })

export const renameFile = (passwordId, oldPath, newPath) =>
  api.post(`/sftp/${passwordId}/rename`, { old_path: oldPath, new_path: newPath })

export const deleteFile = (passwordId, path) =>
  api.delete(`/sftp/${passwordId}/delete`, { params: { path } })

export const uploadFile = (passwordId, targetDir, file, onProgress) => {
  const form = new FormData()
  form.append('file', file)
  return api.post(`/sftp/${passwordId}/upload`, form, {
    params: { path: targetDir },
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 300000,
    onUploadProgress: onProgress,
  })
}

export const downloadFile = (passwordId, path) =>
  api.get(`/sftp/${passwordId}/download`, {
    params: { path },
    responseType: 'blob',
  })
