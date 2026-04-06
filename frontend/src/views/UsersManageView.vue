<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px">
      <h2>用户管理</h2>
      <el-button type="primary" @click="openCreate"><el-icon><Plus /></el-icon> 新建用户</el-button>
    </div>

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

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑用户' : '新建用户'" width="460px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" :disabled="!!editingId" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" />
        </el-form-item>
        <el-form-item label="密码" :prop="editingId ? '' : 'password'">
          <el-input v-model="form.password" type="password" show-password :placeholder="editingId ? '留空不修改' : ''" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="form.role">
            <el-option v-for="r in ROLE_OPTIONS" :key="r.value" :label="r.label" :value="r.value" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getUsers, createUser, updateUser, deleteUser } from '../api/users'
import { ROLES, ROLE_OPTIONS } from '../utils/constants'
import { ElMessage } from 'element-plus'

const users = ref([])
const dialogVisible = ref(false)
const editingId = ref(null)
const formRef = ref()
const form = reactive({ username: '', email: '', password: '', role: 'developer' })
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  email: [{ required: true, message: '请输入邮箱', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
}

async function loadUsers() {
  const { data } = await getUsers()
  users.value = data
}

function openCreate() {
  editingId.value = null
  Object.assign(form, { username: '', email: '', password: '', role: 'developer' })
  dialogVisible.value = true
}

function openEdit(row) {
  editingId.value = row.id
  Object.assign(form, { username: row.username, email: row.email, password: '', role: row.role })
  dialogVisible.value = true
}

async function handleSave() {
  await formRef.value.validate()
  if (editingId.value) {
    const payload = { email: form.email, role: form.role }
    if (form.password) payload.password = form.password
    await updateUser(editingId.value, payload)
  } else {
    await createUser(form)
  }
  ElMessage.success('保存成功')
  dialogVisible.value = false
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

onMounted(loadUsers)
</script>
