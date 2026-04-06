<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px">
      <h2>团队管理</h2>
      <el-button v-if="auth.isAdmin" type="primary" @click="openCreate"><el-icon><Plus /></el-icon> 新建团队</el-button>
    </div>

    <el-row :gutter="16">
      <el-col :span="8" v-for="team in teams" :key="team.id" style="margin-bottom: 16px">
        <el-card shadow="hover" style="cursor: pointer" @click="$router.push(`/teams/${team.id}`)">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center">
              <span style="font-weight: 600">{{ team.name }}</span>
              <div v-if="auth.isAdmin" @click.stop>
                <el-button link type="primary" size="small" @click="openEdit(team)">编辑</el-button>
                <el-popconfirm title="确认删除该团队？" @confirm="handleDelete(team.id)">
                  <template #reference>
                    <el-button link type="danger" size="small">删除</el-button>
                  </template>
                </el-popconfirm>
              </div>
            </div>
          </template>
          <p style="color: #999; font-size: 14px; min-height: 40px">{{ team.description || '暂无描述' }}</p>
          <div style="display: flex; align-items: center; gap: 6px; color: #666; font-size: 13px; margin-top: 10px">
            <el-icon><UserFilled /></el-icon>
            {{ team.member_count }} 名成员
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-empty v-if="teams.length === 0" description="暂无团队" />

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑团队' : '新建团队'" width="440px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="70px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" />
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
import { useAuthStore } from '../stores/auth'
import { getTeams, createTeam, updateTeam, deleteTeam } from '../api/teams'
import { ElMessage } from 'element-plus'

const auth = useAuthStore()
const teams = ref([])
const dialogVisible = ref(false)
const editingId = ref(null)
const formRef = ref()
const form = reactive({ name: '', description: '' })
const rules = { name: [{ required: true, message: '请输入团队名称', trigger: 'blur' }] }

async function loadTeams() {
  const { data } = await getTeams()
  teams.value = data
}

function openCreate() {
  editingId.value = null
  form.name = ''
  form.description = ''
  dialogVisible.value = true
}

function openEdit(team) {
  editingId.value = team.id
  form.name = team.name
  form.description = team.description
  dialogVisible.value = true
}

async function handleSave() {
  await formRef.value.validate()
  if (editingId.value) {
    await updateTeam(editingId.value, form)
  } else {
    await createTeam(form)
  }
  ElMessage.success('保存成功')
  dialogVisible.value = false
  loadTeams()
}

async function handleDelete(id) {
  await deleteTeam(id)
  ElMessage.success('已删除')
  loadTeams()
}

onMounted(loadTeams)
</script>
