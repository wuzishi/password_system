<template>
  <div style="height: 100vh; display: flex; flex-direction: column; background: #1e1e1e">
    <!-- 顶栏 -->
    <div class="term-topbar">
      <div style="display: flex; align-items: center; gap: 10px">
        <el-button size="small" text style="color: #ccc" @click="goBack">
          <el-icon><ArrowLeft /></el-icon> 返回
        </el-button>
        <span style="color: #aaa">{{ serverInfo }}</span>
        <el-tag :type="connected ? 'success' : 'danger'" size="small" effect="dark">
          {{ connected ? '已连接' : '未连接' }}
        </el-tag>
      </div>
      <div style="display: flex; align-items: center; gap: 10px">
        <el-button size="small" :type="showFiles ? 'primary' : 'default'" text style="color: #ccc" @click="showFiles = !showFiles">
          <el-icon><Folder /></el-icon> {{ showFiles ? '隐藏文件' : '文件管理' }}
        </el-button>
        <span style="color: #555">SSH 终端</span>
      </div>
    </div>

    <!-- 主体 -->
    <div style="flex: 1; min-height: 0">
      <SplitPane v-if="showFiles" :initial-left-percent="35" :min-left-px="220" :min-right-px="400">
        <template #left>
          <FileManager
            ref="fileManagerRef"
            :password-id="passwordId"
            @cd="handleFileCd"
          />
        </template>
        <template #right>
          <WebTerminal
            ref="termRef"
            v-if="wsUrl"
            :ws-url="wsUrl"
            @connected="connected = true"
            @disconnected="connected = false"
            @error="connected = false"
            @command="handleTerminalCommand"
          />
        </template>
      </SplitPane>
      <template v-else>
        <WebTerminal
          ref="termRef"
          v-if="wsUrl"
          :ws-url="wsUrl"
          @connected="connected = true"
          @disconnected="connected = false"
          @error="connected = false"
          @command="handleTerminalCommand"
          style="height: 100%"
        />
      </template>
      <div v-if="!wsUrl" style="color: #999; padding: 40px; text-align: center">
        正在准备连接...
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import WebTerminal from '../components/WebTerminal.vue'
import SplitPane from '../components/SplitPane.vue'
import FileManager from '../components/FileManager.vue'
import { getPasswords } from '../api/passwords'

const route = useRoute()
const router = useRouter()
const connected = ref(false)
const server = ref(null)
const showFiles = ref(true)
const termRef = ref(null)
const fileManagerRef = ref(null)

const passwordId = computed(() => route.params.id)

const wsUrl = computed(() => {
  if (!passwordId.value) return ''
  const token = localStorage.getItem('token')
  return `${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/api/ws/terminal/${passwordId.value}?token=${token}`
})

const serverInfo = computed(() => {
  if (!server.value) return '加载中...'
  return `${server.value.title} (${server.value.host}:${server.value.port || 22}) @${server.value.username}`
})

function goBack() {
  router.push('/servers')
}

function handleFileCd(path) {
  termRef.value?.sendCommand(`cd ${path}`)
  // sendCommand 会触发回车 → handleTerminalCommand → 刷新文件列表
}

let cdTimer = null
function handleTerminalCommand(cmd) {
  // 检测 cd 命令，延迟刷新文件列表
  const trimmed = cmd.trim()
  const isCd = trimmed === 'cd' || trimmed.startsWith('cd ') || trimmed.startsWith('cd\t')
  // pushd/popd 也会改变目录
  const isNav = isCd || trimmed.startsWith('pushd') || trimmed.startsWith('popd')

  if (isNav && fileManagerRef.value) {
    if (cdTimer) clearTimeout(cdTimer)
    cdTimer = setTimeout(() => {
      // 解析 cd 目标路径
      if (isCd) {
        const parts = trimmed.split(/\s+/)
        const target = parts[1] || '~'
        // 如果是绝对路径直接用，否则让 FileManager 基于当前目录拼接
        if (target.startsWith('/')) {
          fileManagerRef.value.navigateTo(target)
        } else if (target === '~' || target === '') {
          fileManagerRef.value.navigateTo('~')
        } else if (target === '..') {
          fileManagerRef.value.goUp()
        } else if (target === '-') {
          fileManagerRef.value.refresh()
        } else {
          // 相对路径：基于当前目录拼接
          fileManagerRef.value.navigateRelative(target)
        }
      } else {
        // pushd/popd —— 直接刷新当前目录
        fileManagerRef.value.refresh()
      }
    }, 500)  // 等命令执行完
  }
}

onMounted(async () => {
  try {
    const { data } = await getPasswords({ category: 'server' })
    server.value = data.find(p => p.id === parseInt(passwordId.value))
  } catch {}
})
</script>

<style scoped>
.term-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 16px;
  background: #2d2d2d;
  color: #ccc;
  font-size: 13px;
  flex-shrink: 0;
  border-bottom: 1px solid #333;
}
</style>
