<template>
  <div ref="termContainer" style="width: 100%; height: 100%"></div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { Terminal } from '@xterm/xterm'
import { FitAddon } from '@xterm/addon-fit'
import '@xterm/xterm/css/xterm.css'

const props = defineProps({
  wsUrl: { type: String, required: true },
})

const emit = defineEmits(['connected', 'disconnected', 'error'])

const termContainer = ref(null)
let term = null
let fitAddon = null
let ws = null

onMounted(() => {
  term = new Terminal({
    cursorBlink: true,
    fontSize: 14,
    fontFamily: "'Cascadia Code', 'Consolas', 'Courier New', monospace",
    theme: {
      background: '#1e1e1e',
      foreground: '#d4d4d4',
      cursor: '#d4d4d4',
    },
  })

  fitAddon = new FitAddon()
  term.loadAddon(fitAddon)
  term.open(termContainer.value)
  fitAddon.fit()

  term.writeln('正在连接...\r\n')

  // Connect WebSocket
  ws = new WebSocket(props.wsUrl)
  ws.binaryType = 'arraybuffer'

  ws.onopen = () => {
    emit('connected')
    // Send initial size
    const dims = { cols: term.cols, rows: term.rows }
    ws.send(JSON.stringify({ resize: dims }))
  }

  ws.onmessage = (e) => {
    if (e.data instanceof ArrayBuffer) {
      term.write(new Uint8Array(e.data))
    } else {
      term.write(e.data)
    }
  }

  ws.onclose = () => {
    term.writeln('\r\n\r\n连接已断开')
    emit('disconnected')
  }

  ws.onerror = () => {
    term.writeln('\r\n连接错误')
    emit('error')
  }

  // Send keystrokes to server
  term.onData((data) => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(data)
    }
  })

  // Handle resize
  const resizeObserver = new ResizeObserver(() => {
    fitAddon.fit()
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ resize: { cols: term.cols, rows: term.rows } }))
    }
  })
  resizeObserver.observe(termContainer.value)
})

onUnmounted(() => {
  if (ws) ws.close()
  if (term) term.dispose()
})
</script>
