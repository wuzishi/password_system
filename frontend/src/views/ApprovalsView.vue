<template>
  <div>
    <h2 style="margin-bottom: 20px">审批管理</h2>

    <el-tabs v-model="activeTab" @tab-change="loadData">
      <el-tab-pane label="待审批" name="pending" v-if="auth.isAdmin">
        <el-table :data="pendingList" stripe v-loading="loading">
          <el-table-column prop="requester_name" label="申请人" width="100" />
          <el-table-column prop="password_title" label="密码标题" min-width="150" />
          <el-table-column label="类型" width="100">
            <template #default="{ row }">
              <el-tag :type="row.request_type === 'view' ? 'primary' : 'warning'" size="small">
                {{ row.request_type === 'view' ? '查看' : '分享' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="分享给" width="100">
            <template #default="{ row }">
              {{ row.share_target_username || '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="reason" label="申请理由" min-width="150" show-overflow-tooltip />
          <el-table-column prop="created_at" label="申请时间" width="170">
            <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="160" fixed="right">
            <template #default="{ row }">
              <el-button type="success" size="small" @click="handleApprove(row)">通过</el-button>
              <el-button type="danger" size="small" @click="openReject(row)">拒绝</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-if="!loading && pendingList.length === 0" description="暂无待审批请求" />
      </el-tab-pane>

      <el-tab-pane label="我的申请" name="mine">
        <el-table :data="myList" stripe v-loading="loading">
          <el-table-column prop="password_title" label="密码标题" min-width="150" />
          <el-table-column label="类型" width="100">
            <template #default="{ row }">
              <el-tag :type="row.request_type === 'view' ? 'primary' : 'warning'" size="small">
                {{ row.request_type === 'view' ? '查看' : '分享' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="reason" label="理由" min-width="120" show-overflow-tooltip />
          <el-table-column label="状态" width="120">
            <template #default="{ row }">
              <el-tag v-if="row.status === 'pending'" type="info" size="small">审批中</el-tag>
              <el-tag v-else-if="row.status === 'approved'" type="success" size="small">已通过</el-tag>
              <el-tag v-else type="danger" size="small">已拒绝</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="有效期" width="140">
            <template #default="{ row }">
              <template v-if="row.status === 'approved' && row.expires_at">
                <span v-if="isExpired(row.expires_at)" style="color: #999">已过期</span>
                <el-tag v-else type="success" size="small">{{ remainingMin(row.expires_at) }}</el-tag>
              </template>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="reject_reason" label="拒绝理由" min-width="120" show-overflow-tooltip />
          <el-table-column prop="created_at" label="时间" width="170">
            <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="全部记录" name="all" v-if="auth.isAdmin">
        <el-table :data="allList" stripe v-loading="loading">
          <el-table-column prop="requester_name" label="申请人" width="100" />
          <el-table-column prop="password_title" label="密码" min-width="130" />
          <el-table-column label="类型" width="80">
            <template #default="{ row }">
              <el-tag size="small">{{ row.request_type === 'view' ? '查看' : '分享' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="90">
            <template #default="{ row }">
              <el-tag :type="row.status === 'approved' ? 'success' : row.status === 'rejected' ? 'danger' : 'info'" size="small">
                {{ row.status === 'pending' ? '待审批' : row.status === 'approved' ? '已通过' : '已拒绝' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="approver_name" label="审批人" width="100" />
          <el-table-column prop="created_at" label="时间" width="170">
            <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <!-- Reject dialog -->
    <el-dialog v-model="rejectVisible" title="拒绝理由" width="400px">
      <el-input v-model="rejectReason" type="textarea" :rows="3" placeholder="请输入拒绝理由（可选）" />
      <template #footer>
        <el-button @click="rejectVisible = false">取消</el-button>
        <el-button type="danger" @click="handleReject">确认拒绝</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { getApprovals, approveRequest, rejectRequest } from '../api/approvals'
import { ElMessage } from 'element-plus'

const auth = useAuthStore()
const activeTab = ref(auth.isAdmin ? 'pending' : 'mine')
const loading = ref(false)
const pendingList = ref([])
const myList = ref([])
const allList = ref([])

const rejectVisible = ref(false)
const rejectReason = ref('')
const rejectingId = ref(null)

function formatTime(t) {
  if (!t) return ''
  return new Date(t).toLocaleString('zh-CN')
}

function isExpired(t) {
  return new Date(t) < new Date()
}

function remainingMin(t) {
  const diff = Math.max(0, Math.ceil((new Date(t) - new Date()) / 60000))
  return `${diff}分钟`
}

async function loadData() {
  loading.value = true
  try {
    if (activeTab.value === 'pending') {
      const { data } = await getApprovals({ status: 'pending' })
      pendingList.value = data
    } else if (activeTab.value === 'mine') {
      const { data } = await getApprovals()
      myList.value = data
    } else {
      const { data } = await getApprovals()
      allList.value = data
    }
  } finally {
    loading.value = false
  }
}

async function handleApprove(row) {
  await approveRequest(row.id)
  ElMessage.success('已批准')
  loadData()
}

function openReject(row) {
  rejectingId.value = row.id
  rejectReason.value = ''
  rejectVisible.value = true
}

async function handleReject() {
  await rejectRequest(rejectingId.value, { reject_reason: rejectReason.value })
  ElMessage.success('已拒绝')
  rejectVisible.value = false
  loadData()
}

onMounted(loadData)
</script>
