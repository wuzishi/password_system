<template>
  <div style="height: 100vh; display: flex; flex-direction: column; background: #1e1e1e">
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

    <div style="flex: 1; min-height: 0">
      <SplitPane v-if="showFiles" :initial-left-percent="35" :min-left-px="220" :min-right-px="400">
        <template #left>
          <FileManager
            :password-id="passwordId"
            :cwd="currentCwd"
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
            @cwd-changed="currentCwd = $event"
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
          @cwd-changed="currentCwd = $event"
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
const currentCwd = ref('')
const termRef = ref(null)

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
