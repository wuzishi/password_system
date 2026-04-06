<template>
  <div style="height: 100vh; display: flex; flex-direction: column; background: #1e1e1e">
    <div style="display: flex; align-items: center; justify-content: space-between; padding: 8px 16px; background: #2d2d2d; color: #ccc; font-size: 13px">
      <div style="display: flex; align-items: center; gap: 10px">
        <el-button size="small" text style="color: #ccc" @click="goBack">
          <el-icon><ArrowLeft /></el-icon> 返回
        </el-button>
        <span>{{ serverInfo }}</span>
        <el-tag :type="connected ? 'success' : 'danger'" size="small" effect="dark">
          {{ connected ? '已连接' : '未连接' }}
        </el-tag>
      </div>
      <span style="color: #666">SSH 终端</span>
    </div>
    <div style="flex: 1; padding: 4px; min-height: 0">
      <WebTerminal
        v-if="wsUrl"
        :ws-url="wsUrl"
        @connected="connected = true"
        @disconnected="connected = false"
        @error="connected = false"
      />
      <div v-else style="color: #999; padding: 40px; text-align: center">
        正在准备连接...
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import WebTerminal from '../components/WebTerminal.vue'
import { getPasswords } from '../api/passwords'

const route = useRoute()
const router = useRouter()
const connected = ref(false)
const server = ref(null)

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

onMounted(async () => {
  try {
    const { data } = await getPasswords({ category: 'server' })
    server.value = data.find(p => p.id === parseInt(passwordId.value))
  } catch {}
})
</script>
