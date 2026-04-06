<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px">
      <h2>用户管理</h2>
      <el-button type="primary" @click="openInvite"><el-icon><Message /></el-icon> 邀请用户</el-button>
    </div>

    <el-tabs v-model="activeTab">
      <el-tab-pane label="用户列表" name="users">
        <el-table :data="users" stripe>
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column prop="username" label="用户名" />
          <el-table-column prop="email" label="邮箱" />
          <el-table-column prop="role" label="角色" width="100">
            <template #default="{ row }">
              <el-tag :type="ROLES[row.role]?.type" size="small">{{ ROLES[row.role]?.label }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="is_active" label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">{{ row.is_active ? '启用' : '禁用' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="openEdit(row)">编辑</el-button>
              <el-button link :type="row.is_active ? 'warning' : 'success'" size="small" @click="toggleActive(row)">
                {{ row.is_active ? '禁用' : '启用' }}
              </el-button>
              <el-popconfirm title="确认删除？" @confirm="handleDelete(row.id)">
                <template #reference>
                  <el-button link type="danger" size="small">删除</el-button>
                </template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane name="invitations">
        <template #label>
          邀请记录
          <el-badge v-if="pendingInvites > 0" :value="pendingInvites" style="margin-left: 4px" />
        </template>
        <el-table :data="invitations" stripe>
          <el-table-column prop="email" label="邮箱" min-width="180" />
          <el-table-column prop="role" label="角色" width="100">
            <template #default="{ row }">
              <el-tag :type="ROLES[row.role]?.type" size="small">{{ ROLES[row.role]?.label }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="invited_by_name" label="邀请人" width="100" />
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag v-if="row.status === 'pending'" type="info" size="small">待接受</el-tag>
              <el-tag v-else-if="row.status === 'accepted'" type="success" size="small">已加入</el-tag>
              <el-tag v-else type="danger" size="small">已过期</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="邀请时间" width="170">
            <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="140">
            <template #default="{ row }">
              <el-button v-if="row.status !== 'accepted'" link type="primary" size="small" @click="handleResend(row)">重发</el-button>
              <el-popconfirm title="确认删除？" @confirm="handleDeleteInvite(row.id)">
                <template #reference>
                  <el-button link type="danger" size="small">删除</el-button>
                </template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <!-- Invite Dialog -->
    <el-dialog v-model="inviteVisible" title="邀请新用户" width="440px">
      <el-form ref="inviteFormRef" :model="inviteForm" :rules="inviteRules" label-width="70px">
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="inviteForm.email" placeholder="输入对方邮箱地址" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="inviteForm.role" style="width: 100%">
            <el-option v-for="r in ROLE_OPTIONS" :key="r.value" :label="r.label" :value="r.value" />
          </el-select>
        </el-form-item>
      </el-form>
      <div v-if="inviteUrl" style="margin-top: 12px; padding: 12px; background: #f0f9eb; border-radius: 6px">
        <p style="margin: 0 0 8px; font-size: 13px; color: #67c23a">邀请链接已生成（SMTP未配置时显示）：</p>
        <el-input :model-value="inviteUrl" readonly size="small">
          <template #append>
            <el-button @click="copyUrl">复制</el-button>
          </template>
        </el-input>
      </div>
      <template #footer>
        <el-button @click="inviteVisible = false">关闭</el-button>
        <el-button type="primary" :loading="inviting" @click="handleInvite">发送邀请</el-button>
      </template>
    </el-dialog>

    <!-- Edit Dialog -->
    <el-dialog v-model="editVisible" title="编辑用户" width="440px">
      <el-form ref="editFormRef" :model="editForm" label-width="70px">
        <el-form-item label="用户名">
          <el-input :model-value="editForm.username" disabled />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="editForm.email" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="editForm.password" type="password" show-password placeholder="留空不修改" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="editForm.role" style="width: 100%">
            <el-option v-for="r in ROLE_OPTIONS" :key="r.value" :label="r.label" :value="r.value" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { getUsers, updateUser, deleteUser } from '../api/users'
import { ROLES, ROLE_OPTIONS } from '../utils/constants'
import { ElMessage } from 'element-plus'
import api from '../api/index'

const activeTab = ref('users')
const users = ref([])
const invitations = ref([])

const pendingInvites = computed(() => invitations.value.filter(i => i.status === 'pending').length)

function formatTime(t) {
  if (!t) return ''
  return new Date(t).toLocaleString('zh-CN')
}

// --- Invite ---
const inviteVisible = ref(false)
const inviting = ref(false)
const inviteUrl = ref('')
const inviteFormRef = ref()
const inviteForm = reactive({ email: '', role: 'developer' })
const inviteRules = {
  email: [{ required: true, message: '请输入邮箱', trigger: 'blur' }, { type: 'email', message: '邮箱格式不正确', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
}

function openInvite() {
  inviteForm.email = ''
  inviteForm.role = 'developer'
  inviteUrl.value = ''
  inviteVisible.value = true
}

async function handleInvite() {
  await inviteFormRef.value.validate()
  inviting.value = true
  try {
    const { data } = await api.post('/users/invite', inviteForm)
    ElMessage.success(data.message)
    if (data.invite_url) inviteUrl.value = data.invite_url
    loadInvitations()
  } finally {
    inviting.value = false
  }
}

function copyUrl() {
  navigator.clipboard.writeText(inviteUrl.value)
  ElMessage.success('已复制')
}

async function handleResend(row) {
  const { data } = await api.post(`/users/invitations/${row.id}/resend`)
  ElMessage.success(data.message)
  if (data.invite_url) {
    inviteUrl.value = data.invite_url
    inviteVisible.value = true
  }
  loadInvitations()
}

async function handleDeleteInvite(id) {
  await api.delete(`/users/invitations/${id}`)
  ElMessage.success('已删除')
  loadInvitations()
}

// --- Edit ---
const editVisible = ref(false)
const editingId = ref(null)
const editFormRef = ref()
const editForm = reactive({ username: '', email: '', password: '', role: 'developer' })

function openEdit(row) {
  editingId.value = row.id
  Object.assign(editForm, { username: row.username, email: row.email, password: '', role: row.role })
  editVisible.value = true
}

async function handleSaveEdit() {
  const payload = { email: editForm.email, role: editForm.role }
  if (editForm.password) payload.password = editForm.password
  await updateUser(editingId.value, payload)
  ElMessage.success('保存成功')
  editVisible.value = false
  loadUsers()
}

async function toggleActive(row) {
  await updateUser(row.id, { is_active: !row.is_active })
  ElMessage.success(row.is_active ? '已禁用' : '已启用')
  loadUsers()
}

async function handleDelete(id) {
  await deleteUser(id)
  ElMessage.success('已删除')
  loadUsers()
}

async function loadUsers() {
  const { data } = await getUsers()
  users.value = data
}

async function loadInvitations() {
  try {
    const { data } = await api.get('/users/invitations')
    invitations.value = data
  } catch {}
}

onMounted(() => {
  loadUsers()
  loadInvitations()
})
</script>
