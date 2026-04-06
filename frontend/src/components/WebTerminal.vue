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

// cwd 检测
let cwdNonce = null
let markerRe = null
let outputBuffer = ''
let flushTimer = null

function flushBuffer() {
  if (outputBuffer && term) {
    term.write(outputBuffer)
    outputBuffer = ''
  }
}

function scheduleFlush() {
  if (flushTimer) clearTimeout(flushTimer)
  flushTimer = setTimeout(flushBuffer, 150)
}

function processOutput(raw) {
  if (!cwdNonce || !markerRe) {
    // 尚未收到 nonce，直接写入
    term.write(raw)
    return
  }

  outputBuffer += raw

  // 检查完整标记
  const match = outputBuffer.match(markerRe)
  if (match) {
    const cwd = match[1].trim()
    if (cwd) emit('cwd-changed', cwd)
    // 剥离标记行（含 echo 命令本身和输出）
    outputBuffer = outputBuffer.replace(new RegExp(`[^\\r\\n]*~~CWD${cwdNonce}~~[^\\r\\n]*~~CWDEND~~[^\\r\\n]*`, 'g'), '')
    // 也剥离 echo 命令本身（前导空格 + echo）
    outputBuffer = outputBuffer.replace(new RegExp(`[^\\r\\n]* echo "~~CWD${cwdNonce}~~[^"]*~~CWDEND~~"[^\\r\\n]*`, 'g'), '')
  }

  // 如果缓冲区末尾可能是标记的一部分，保留
  const markerPrefix = `~~CWD`
  const tailKeep = 60  // 标记最大长度
  if (outputBuffer.length > tailKeep) {
    const tail = outputBuffer.slice(-tailKeep)
    if (tail.includes(markerPrefix)) {
      // 可能有不完整标记，只输出安全部分
      const safeLen = outputBuffer.length - tailKeep
      if (safeLen > 0) {
        term.write(outputBuffer.substring(0, safeLen))
        outputBuffer = outputBuffer.substring(safeLen)
      }
      scheduleFlush()
      return
    }
  }

  // 无标记嫌疑，全部输出
  flushBuffer()
}

// 暴露 sendCommand 给父组件
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

  // Connect WebSocket
  try {
    ws = new WebSocket(props.wsUrl)
    ws.binaryType = 'arraybuffer'
  } catch (e) {
    term.writeln(`\r\n连接创建失败: ${e.message}\r\n`)
    emit('error')
    return
  }

  let initReceived = false

  ws.onopen = () => {
    emit('connected')
    term.clear()
    try {
      const dims = { cols: term.cols, rows: term.rows }
      ws.send(JSON.stringify({ resize: dims }))
    } catch {}
  }

  ws.onmessage = (e) => {
    // 第一条消息是 init JSON
    if (!initReceived && typeof e.data === 'string') {
      try {
        const msg = JSON.parse(e.data)
        if (msg.init && msg.init.cwd_nonce) {
          cwdNonce = msg.init.cwd_nonce
          markerRe = new RegExp(`~~CWD${cwdNonce}~~(.+?)~~CWDEND~~`)
          initReceived = true
          return
        }
      } catch {}
      initReceived = true
    }

    // 正常终端数据
    if (e.data instanceof ArrayBuffer) {
      const text = new TextDecoder().decode(e.data)
      processOutput(text)
    } else {
      processOutput(e.data)
    }
  }

  ws.onclose = () => {
    flushBuffer()
    term.writeln('\r\n\r\n--- 连接已断开 ---')
    emit('disconnected')
  }

  ws.onerror = () => {
    flushBuffer()
    term.writeln('\r\n--- 连接错误 ---')
    emit('error')
  }

  // Send keystrokes to server
  term.onData((data) => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(data)
    }
  })

  // Handle resize
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
  if (flushTimer) clearTimeout(flushTimer)
  if (resizeObserver) resizeObserver.disconnect()
  if (ws) ws.close()
  if (term) term.dispose()
})
</script>
