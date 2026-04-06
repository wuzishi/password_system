<template>
  <div>
    <h2 style="margin-bottom: 20px">审计日志</h2>

    <el-card style="margin-bottom: 16px">
      <el-form inline>
        <el-form-item label="操作类型">
          <el-input v-model="filterAction" placeholder="如 password.decrypt" clearable @clear="loadLogs" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadLogs">查询</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-table :data="logs" stripe v-loading="loading">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="username" label="用户" width="100" />
      <el-table-column prop="action" label="操作" width="160">
        <template #default="{ row }">
          <el-tag size="small" :type="actionTagType(row.action)">{{ row.action }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="resource_type" label="资源类型" width="100" />
      <el-table-column prop="resource_id" label="资源ID" width="80" />
      <el-table-column prop="details" label="详情" show-overflow-tooltip />
      <el-table-column prop="ip_address" label="IP" width="130" />
      <el-table-column prop="timestamp" label="时间" width="180">
        <template #default="{ row }">{{ formatTime(row.timestamp) }}</template>
      </el-table-column>
    </el-table>

    <div style="margin-top: 16px; text-align: right">
      <el-pagination
        v-model:current-page="page"
        :page-size="50"
        layout="prev, pager, next"
        :total="500"
        @current-change="loadLogs"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getAuditLogs } from '../api/audit'

const logs = ref([])
const loading = ref(false)
const page = ref(1)
const filterAction = ref('')

function formatTime(t) {
  if (!t) return ''
  return new Date(t).toLocaleString('zh-CN')
}

function actionTagType(action) {
  if (action.includes('delete')) return 'danger'
  if (action.includes('create')) return 'success'
  if (action.includes('decrypt')) return 'warning'
  return 'info'
}

async function loadLogs() {
  loading.value = true
  try {
    const params = { page: page.value, size: 50 }
    if (filterAction.value) params.action = filterAction.value
    const { data } = await getAuditLogs(params)
    logs.value = data
  } finally {
    loading.value = false
  }
}

onMounted(loadLogs)
</script>
