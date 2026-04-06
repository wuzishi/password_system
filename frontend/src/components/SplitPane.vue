<template>
  <div ref="container" class="split-pane" @mousemove="onMouseMove" @mouseup="onMouseUp" @mouseleave="onMouseUp">
    <div class="split-left" :style="{ width: leftWidth + 'px' }">
      <slot name="left" />
    </div>
    <div class="split-divider" @mousedown.prevent="onMouseDown" :class="{ dragging }">
      <div class="divider-dot" />
    </div>
    <div class="split-right" :style="{ flex: 1 }">
      <slot name="right" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const props = defineProps({
  initialLeftPercent: { type: Number, default: 35 },
  minLeftPx: { type: Number, default: 200 },
  minRightPx: { type: Number, default: 300 },
})

const container = ref(null)
const leftWidth = ref(300)
const dragging = ref(false)

onMounted(() => {
  if (container.value) {
    leftWidth.value = Math.round(container.value.offsetWidth * props.initialLeftPercent / 100)
  }
})

function onMouseDown() {
  dragging.value = true
}

function onMouseMove(e) {
  if (!dragging.value || !container.value) return
  const rect = container.value.getBoundingClientRect()
  let newLeft = e.clientX - rect.left
  const maxLeft = rect.width - props.minRightPx - 6
  newLeft = Math.max(props.minLeftPx, Math.min(newLeft, maxLeft))
  leftWidth.value = newLeft
}

function onMouseUp() {
  dragging.value = false
}
</script>

<style scoped>
.split-pane {
  display: flex;
  height: 100%;
  overflow: hidden;
}
.split-left {
  overflow: hidden;
  flex-shrink: 0;
}
.split-right {
  overflow: hidden;
  min-width: 0;
}
.split-divider {
  width: 6px;
  background: #2d2d2d;
  cursor: col-resize;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: background 0.15s;
}
.split-divider:hover,
.split-divider.dragging {
  background: #404040;
}
.divider-dot {
  width: 2px;
  height: 30px;
  border-radius: 1px;
  background: #555;
}
.split-pane.dragging * {
  user-select: none !important;
}
</style>
