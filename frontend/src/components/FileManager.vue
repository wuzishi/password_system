<template>
  <div class="fm" @contextmenu.prevent="onBgContext" @dragover.prevent="dragHover = true" @dragleave="dragHover = false" @drop.prevent="onDrop">
    <!-- 面包屑 + 工具栏 -->
    <div class="fm-toolbar">
      <div class="fm-breadcrumb">
        <span class="bc-item" @click="navigate('/')">/</span>
        <template v-for="(seg, i) in pathSegments" :key="i">
          <span class="bc-sep">/</span>
          <span class="bc-item" @click="navigate(seg.fullPath)">{{ seg.name }}</span>
        </template>
      </div>
      <div class="fm-actions">
        <el-button size="small" text style="color:#aaa" @click="onMkdir" title="新建目录">
          <el-icon><FolderAdd /></el-icon>
        </el-button>
        <el-button size="small" text style="color:#aaa" @click="triggerUpload" title="上传">
          <el-icon><Upload /></el-icon>
        </el-button>
        <el-button size="small" text style="color:#aaa" @click="loadDirectory(currentPath)" title="刷新">
          <el-icon><Refresh /></el-icon>
        </el-button>
      </div>
    </div>

    <!-- 文件列表 -->
    <div class="fm-list" v-loading="loading">
      <!-- 上级目录 -->
      <div v-if="currentPath !== '/'" class="fm-row fm-row-dir" @dblclick="goUp">
        <div class="fm-col-icon"><el-icon><Back /></el-icon></div>
        <div class="fm-col-name">..</div>
        <div class="fm-col-size"></div>
        <div class="fm-col-time"></div>
      </div>

      <div
        v-for="f in files" :key="f.name"
        class="fm-row"
        :class="{ 'fm-row-dir': f.is_dir, 'fm-row-selected': selected === f.name }"
        @click="selected = f.name"
        @dblclick="onDblClick(f)"
        @contextmenu.prevent.stop="onFileContext($event, f)"
      >
        <div class="fm-col-icon">
          <el-icon v-if="f.is_dir" style="color:#e6a23c"><Folder /></el-icon>
          <el-icon v-else :style="{ color: fileColor(f.name) }"><Document /></el-icon>
        </div>
        <div class="fm-col-name" :title="f.name">{{ f.name }}</div>
        <div class="fm-col-size">{{ f.is_dir ? '' : formatSize(f.size) }}</div>
        <div class="fm-col-time">{{ f.mtime }}</div>
        <div class="fm-col-perm">{{ f.permissions }}</div>
      </div>

      <div v-if="!loading && files.length === 0" class="fm-empty">空目录</div>
    </div>

    <!-- 拖拽上传遮罩 -->
    <div v-if="dragHover" class="fm-drop-overlay" @dragleave="dragHover = false">
      <el-icon :size="40"><Upload /></el-icon>
      <div>拖放文件到此处上传</div>
    </div>

    <!-- 上传进度 -->
    <div v-if="uploading" class="fm-upload-bar">
      <el-progress :percentage="uploadProgress" :stroke-width="3" :show-text="false" />
      <span>上传中 {{ uploadProgress }}%</span>
    </div>

    <!-- 隐藏 file input -->
    <input ref="fileInput" type="file" multiple style="display:none" @change="onFileSelected" />

    <!-- 右键菜单 -->
    <FileContextMenu
      :visible="ctx.visible"
      :x="ctx.x"
      :y="ctx.y"
      :target="ctx.target"
      @close="ctx.visible = false"
      @download="handleDownload(ctx.target); ctx.visible = false"
      @open="handleOpen(ctx.target); ctx.visible = false"
      @rename="handleRename(ctx.target); ctx.visible = false"
      @delete="handleDelete(ctx.target); ctx.visible = false"
      @mkdir="onMkdir(); ctx.visible = false"
      @upload="triggerUpload(); ctx.visible = false"
      @refresh="loadDirectory(currentPath); ctx.visible = false"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { listFiles, mkdir, renameFile, deleteFile, uploadFile, downloadFile } from '../api/sftp'
import FileContextMenu from './FileContextMenu.vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const props = defineProps({
  passwordId: { type: [Number, String], required: true },
  cwd: { type: String, default: '' },
})

const emit = defineEmits(['cd'])

const currentPath = ref('/')
const files = ref([])
const loading = ref(false)
const selected = ref('')
const dragHover = ref(false)
const uploading = ref(false)
const uploadProgress = ref(0)
const fileInput = ref(null)

const ctx = reactive({ visible: false, x: 0, y: 0, target: null })

const pathSegments = computed(() => {
  const parts = currentPath.value.split('/').filter(Boolean)
  return parts.map((name, i) => ({
    name,
    fullPath: '/' + parts.slice(0, i + 1).join('/'),
  }))
})

// 当终端 cwd 变化时同步
watch(() => props.cwd, (val) => {
  if (val && val !== currentPath.value) {
    loadDirectory(val)
  }
})

function navigate(path) {
  loadDirectory(path)
  emit('cd', path)
}

function goUp() {
  const parts = currentPath.value.split('/').filter(Boolean)
  parts.pop()
  const parent = '/' + parts.join('/')
  navigate(parent || '/')
}

async function loadDirectory(path) {
  loading.value = true
  selected.value = ''
  try {
    const { data } = await listFiles(props.passwordId, path)
    currentPath.value = data.path
    files.value = data.files
  } catch {
    // interceptor handles
  } finally {
    loading.value = false
  }
}

function onDblClick(f) {
  if (f.is_dir) {
    const newPath = currentPath.value === '/' ? `/${f.name}` : `${currentPath.value}/${f.name}`
    navigate(newPath)
  } else {
    handleDownload(f)
  }
}

function handleOpen(f) {
  if (f && f.is_dir) {
    const newPath = currentPath.value === '/' ? `/${f.name}` : `${currentPath.value}/${f.name}`
    navigate(newPath)
  }
}

async function handleDownload(f) {
  if (!f || f.is_dir) return
  const filePath = currentPath.value === '/' ? `/${f.name}` : `${currentPath.value}/${f.name}`
  try {
    const res = await downloadFile(props.passwordId, filePath)
    const url = URL.createObjectURL(res.data)
    const a = document.createElement('a')
    a.href = url
    a.download = f.name
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success(`已下载 ${f.name}`)
  } catch {}
}

async function handleRename(f) {
  if (!f) return
  try {
    const { value: newName } = await ElMessageBox.prompt('新名称', '重命名', {
      inputValue: f.name,
      confirmButtonText: '确定',
      cancelButtonText: '取消',
    })
    if (!newName || newName === f.name) return
    const oldPath = currentPath.value === '/' ? `/${f.name}` : `${currentPath.value}/${f.name}`
    const newPath = currentPath.value === '/' ? `/${newName}` : `${currentPath.value}/${newName}`
    await renameFile(props.passwordId, oldPath, newPath)
    ElMessage.success('已重命名')
    loadDirectory(currentPath.value)
  } catch {}
}

async function handleDelete(f) {
  if (!f) return
  try {
    await ElMessageBox.confirm(`确认删除 ${f.name}${f.is_dir ? '（含子文件）' : ''}？`, '删除', {
      type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消',
    })
    const filePath = currentPath.value === '/' ? `/${f.name}` : `${currentPath.value}/${f.name}`
    await deleteFile(props.passwordId, filePath)
    ElMessage.success('已删除')
    loadDirectory(currentPath.value)
  } catch {}
}

async function onMkdir() {
  try {
    const { value: name } = await ElMessageBox.prompt('目录名称', '新建目录', {
      confirmButtonText: '创建', cancelButtonText: '取消',
    })
    if (!name) return
    const newPath = currentPath.value === '/' ? `/${name}` : `${currentPath.value}/${name}`
    await mkdir(props.passwordId, newPath)
    ElMessage.success('已创建')
    loadDirectory(currentPath.value)
  } catch {}
}

function triggerUpload() {
  fileInput.value?.click()
}

function onFileSelected(e) {
  const fileList = e.target.files
  if (fileList.length) doUpload(Array.from(fileList))
  e.target.value = ''
}

function onDrop(e) {
  dragHover.value = false
  const fileList = e.dataTransfer?.files
  if (fileList?.length) doUpload(Array.from(fileList))
}

async function doUpload(fileList) {
  uploading.value = true
  uploadProgress.value = 0
  let done = 0
  for (const f of fileList) {
    try {
      await uploadFile(props.passwordId, currentPath.value, f, (e) => {
        if (e.total) {
          uploadProgress.value = Math.round(((done / fileList.length) + (e.loaded / e.total / fileList.length)) * 100)
        }
      })
      done++
    } catch {
      ElMessage.error(`上传失败: ${f.name}`)
    }
  }
  uploading.value = false
  uploadProgress.value = 0
  if (done > 0) {
    ElMessage.success(`已上传 ${done} 个文件`)
    loadDirectory(currentPath.value)
  }
}

function onBgContext(e) {
  ctx.target = null
  ctx.x = e.clientX
  ctx.y = e.clientY
  ctx.visible = true
}

function onFileContext(e, f) {
  ctx.target = f
  ctx.x = e.clientX
  ctx.y = e.clientY
  ctx.visible = true
}

function fileColor(name) {
  const ext = name.split('.').pop()?.toLowerCase()
  const colors = { js: '#f0db4f', ts: '#3178c6', py: '#3572a5', vue: '#42b883', json: '#999', md: '#083fa1', sh: '#89e051', yml: '#cb171e', yaml: '#cb171e', sql: '#e38c00', html: '#e34c26', css: '#563d7c', go: '#00add8', rs: '#dea584', java: '#b07219', log: '#666' }
  return colors[ext] || '#888'
}

function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' K'
  if (bytes < 1024 * 1024 * 1024) return (bytes / 1024 / 1024).toFixed(1) + ' M'
  return (bytes / 1024 / 1024 / 1024).toFixed(1) + ' G'
}

onMounted(() => {
  loadDirectory(props.cwd || '/')
})
</script>

<style scoped>
.fm {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #1e1e1e;
  color: #ccc;
  font-size: 13px;
  position: relative;
  overflow: hidden;
}

.fm-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 10px;
  background: #252525;
  border-bottom: 1px solid #333;
  flex-shrink: 0;
}

.fm-breadcrumb {
  display: flex;
  align-items: center;
  gap: 2px;
  overflow: hidden;
  white-space: nowrap;
}
.bc-item {
  cursor: pointer;
  padding: 2px 4px;
  border-radius: 3px;
  color: #8ab4f8;
  font-weight: 500;
}
.bc-item:hover { background: #333; }
.bc-sep { color: #555; }

.fm-actions {
  display: flex;
  gap: 2px;
  flex-shrink: 0;
}

.fm-list {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
}

.fm-row {
  display: flex;
  align-items: center;
  padding: 4px 10px;
  cursor: pointer;
  border-bottom: 1px solid #2a2a2a;
  transition: background 0.1s;
  gap: 6px;
}
.fm-row:hover { background: #2a2a2a; }
.fm-row-selected { background: #2c3e50 !important; }
.fm-row-dir { font-weight: 500; }

.fm-col-icon { width: 20px; flex-shrink: 0; display: flex; align-items: center; }
.fm-col-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.fm-col-size { width: 60px; flex-shrink: 0; text-align: right; color: #777; font-size: 11px; }
.fm-col-time { width: 130px; flex-shrink: 0; text-align: right; color: #666; font-size: 11px; }
.fm-col-perm { width: 80px; flex-shrink: 0; text-align: right; color: #555; font-size: 11px; font-family: monospace; }

.fm-empty {
  padding: 40px;
  text-align: center;
  color: #555;
}

.fm-drop-overlay {
  position: absolute;
  inset: 0;
  background: rgba(30, 30, 30, 0.9);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #8ab4f8;
  font-size: 16px;
  z-index: 10;
  border: 2px dashed #8ab4f8;
  border-radius: 8px;
  margin: 8px;
}

.fm-upload-bar {
  padding: 6px 12px;
  background: #252525;
  border-top: 1px solid #333;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
  color: #aaa;
  flex-shrink: 0;
}
.fm-upload-bar .el-progress { flex: 1; }
</style>
