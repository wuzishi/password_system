<template>
  <div>
    <h2 style="margin-bottom: 20px">服务器管理</h2>

    <el-table :data="servers" stripe v-loading="loading">
      <el-table-column prop="title" label="名称" min-width="150" />
      <el-table-column label="主机" min-width="180">
        <template #default="{ row }">
          {{ row.host }}:{{ row.port || 22 }}
        </template>
      </el-table-column>
      <el-table-column prop="username" label="用户名" width="120" />
      <el-table-column label="归属" width="100">
        <template #default="{ row }">
          <el-tag v-if="row.team_name" size="small">{{ row.team_name }}</el-tag>
          <el-tag v-else-if="row.is_personal" type="info" size="small">个人</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="密码有效期" width="110">
        <template #default="{ row }">
          <el-tag v-if="row.expire_status === 'expired'" type="danger" size="small" effect="dark">已过期</el-tag>
          <el-tag v-else-if="row.expire_status === 'warning'" type="warning" size="small">{{ row.expire_remaining_days }}天</el-tag>
          <el-tag v-else-if="row.expire_remaining_days" type="success" size="small">{{ row.expire_remaining_days }}天</el-tag>
          <span v-else style="color: #999; font-size: 12px">-</span>
        </template>
      </el-table-column>
      <el-table-column label="连接状态" width="110">
        <template #default="{ row }">
          <el-tag v-if="row.verify_status === 'valid'" type="success" size="small">正常</el-tag>
          <el-tag v-else-if="row.verify_status === 'invalid'" type="danger" size="small" effect="dark">失效</el-tag>
          <el-tag v-else-if="row.verify_status === 'error'" type="info" size="small">异常</el-tag>
          <el-tag v-else type="info" size="small" effect="plain">未检测</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <template v-if="row.has_permission">
            <el-button type="primary" size="small" @click="openTerminal(row)">
              <el-icon style="margin-right: 4px"><Monitor /></el-icon>终端
            </el-button>
          </template>
          <template v-else>
            <el-button size="small" @click="requestServerAccess(row)">
              <el-icon style="margin-right: 4px"><Lock /></el-icon>申请权限
            </el-button>
          </template>
        </template>
      </el-table-column>
    </el-table>

    <el-empty v-if="!loading && servers.length === 0" description="暂无服务器密码" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getPasswords } from '../api/passwords'
import { createApproval } from '../api/approvals'
import { ElMessage } from 'element-plus'

const router = useRouter()
const servers = ref([])
const loading = ref(false)

function openTerminal(row) {
  router.push(`/terminal/${row.id}`)
}

async function requestServerAccess(row) {
  try {
    await createApproval({ password_entry_id: row.id, request_type: 'view', reason: '申请服务器访问权限' })
    ElMessage.success('权限申请已提交，等待管理员审批')
  } catch {}
}

onMounted(async () => {
  loading.value = true
  try {
    const { data } = await getPasswords({ category: 'server' })
    servers.value = data
  } finally {
    loading.value = false
  }
})
</script>
