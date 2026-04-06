<template>
  <div ref="termContainer" style="width: 100%; height: 100%"></div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { Terminal } from '@xterm/xterm'
import { FitAddon } from '@xterm/addon-fit'
import '@xterm/xterm/css/xterm.css'

const props = defineProps({
  wsUrl: { type: String, required: true },
})

const emit = defineEmits(['connected', 'disconnected', 'error', 'cwd-changed'])

const termContainer = ref(null)
let term = null
let fitAddon = null
let ws = null
let resizeObserver = null

function sendCommand(cmd) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(cmd + '\r')
  }
}

defineExpose({ sendCommand })

onMounted(() => {
  if (!termContainer.value) return

  term = new Terminal({
    cursorBlink: true,
    fontSize: 14,
    fontFamily: "'Cascadia Code', 'Consolas', 'Courier New', monospace",
    theme: {
      background: '#1e1e1e',
      foreground: '#d4d4d4',
      cursor: '#d4d4d4',
    },
    scrollback: 5000,
  })

  fitAddon = new FitAddon()
  term.loadAddon(fitAddon)
  term.open(termContainer.value)

  setTimeout(() => {
    try { fitAddon.fit() } catch {}
  }, 100)

  term.writeln('正在连接服务器...\r\n')

  try {
    ws = new WebSocket(props.wsUrl)
    ws.binaryType = 'arraybuffer'
  } catch (e) {
    term.writeln(`\r\n连接创建失败: ${e.message}\r\n`)
    emit('error')
    return
  }

  ws.onopen = () => {
    emit('connected')
    term.clear()
    try {
      ws.send(JSON.stringify({ resize: { cols: term.cols, rows: term.rows } }))
    } catch {}
  }

  ws.onmessage = (e) => {
    if (typeof e.data === 'string') {
      try {
        const msg = JSON.parse(e.data)
        if (msg.init) return
        if (msg.cwd) {
          emit('cwd-changed', msg.cwd)
          return
        }
      } catch {}
      term.write(e.data)
      return
    }
    if (e.data instanceof ArrayBuffer) {
      term.write(new Uint8Array(e.data))
    }
  }

  ws.onclose = () => {
    term.writeln('\r\n\r\n--- 连接已断开 ---')
    emit('disconnected')
  }

  ws.onerror = () => {
    term.writeln('\r\n--- 连接错误 ---')
    emit('error')
  }

  term.onData((data) => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(data)
    }
  })

  resizeObserver = new ResizeObserver(() => {
    try {
      fitAddon.fit()
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ resize: { cols: term.cols, rows: term.rows } }))
      }
    } catch {}
  })
  resizeObserver.observe(termContainer.value)
})

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect()
  if (ws) ws.close()
  if (term) term.dispose()
})
</script>
