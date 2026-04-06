<template>
  <Teleport to="body">
    <div v-if="visible" class="ctx-menu" :style="{ left: x + 'px', top: y + 'px' }" @click.stop>
      <template v-if="target">
        <div class="ctx-item" @click="$emit('download')" v-if="!target.is_dir">
          <el-icon><Download /></el-icon> 下载
        </div>
        <div class="ctx-item" @click="$emit('open')" v-if="target.is_dir">
          <el-icon><FolderOpened /></el-icon> 打开
        </div>
        <div class="ctx-item" @click="$emit('rename')">
          <el-icon><Edit /></el-icon> 重命名
        </div>
        <div class="ctx-divider" />
        <div class="ctx-item ctx-danger" @click="$emit('delete')">
          <el-icon><Delete /></el-icon> 删除
        </div>
      </template>
      <template v-else>
        <div class="ctx-item" @click="$emit('mkdir')">
          <el-icon><FolderAdd /></el-icon> 新建目录
        </div>
        <div class="ctx-item" @click="$emit('upload')">
          <el-icon><Upload /></el-icon> 上传文件
        </div>
        <div class="ctx-item" @click="$emit('refresh')">
          <el-icon><Refresh /></el-icon> 刷新
        </div>
      </template>
    </div>
  </Teleport>
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue'

const props = defineProps({
  visible: Boolean,
  x: { type: Number, default: 0 },
  y: { type: Number, default: 0 },
  target: { type: Object, default: null },
})

const emit = defineEmits(['close', 'download', 'open', 'rename', 'delete', 'mkdir', 'upload', 'refresh'])

function onClickOutside() {
  if (props.visible) emit('close')
}

onMounted(() => document.addEventListener('click', onClickOutside))
onUnmounted(() => document.removeEventListener('click', onClickOutside))
</script>

<style scoped>
.ctx-menu {
  position: fixed;
  z-index: 9999;
  background: #2d2d2d;
  border: 1px solid #444;
  border-radius: 6px;
  padding: 4px 0;
  min-width: 140px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.4);
}
.ctx-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  font-size: 13px;
  color: #ccc;
  cursor: pointer;
  transition: background 0.1s;
}
.ctx-item:hover {
  background: #3a3a3a;
  color: #fff;
}
.ctx-danger:hover {
  color: #f56c6c;
}
.ctx-divider {
  height: 1px;
  background: #444;
  margin: 4px 0;
}
</style>
