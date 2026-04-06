<template>
  <div v-if="team">
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 20px">
      <el-button @click="$router.back()" link><el-icon><ArrowLeft /></el-icon></el-button>
      <h2>{{ team.name }}</h2>
      <el-tag size="small">{{ team.member_count }} 名成员</el-tag>
    </div>

    <el-row :gutter="20">
      <el-col :span="10">
        <el-card>
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center">
              <span>团队成员</span>
              <el-button v-if="auth.isAdmin" type="primary" size="small" @click="showAddMember = true">添加成员</el-button>
            </div>
          </template>
          <el-table :data="team.members" size="small">
            <el-table-column prop="username" label="用户名" />
            <el-table-column prop="role" label="角色" width="80">
              <template #default="{ row }">
                <el-tag :type="ROLES[row.role]?.type" size="small">{{ ROLES[row.role]?.label }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column v-if="auth.isAdmin" label="操作" width="80">
              <template #default="{ row }">
                <el-popconfirm title="确认移除？" @confirm="handleRemove(row.user_id)">
                  <template #reference>
                    <el-button link type="danger" size="small">移除</el-button>
                  </template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="14">
        <el-card>
          <template #header><span>团队密码</span></template>
          <el-table :data="passwords" size="small">
            <el-table-column prop="title" label="标题" />
            <el-table-column prop="username" label="用户名" />
            <el-table-column prop="creator_name" label="创建人" width="100" />
          </el-table>
          <el-empty v-if="passwords.length === 0" description="暂无密码" :image-size="60" />
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="showAddMember" title="添加成员" width="400px">
      <el-select v-model="selectedUser" filterable placeholder="选择用户" style="width: 100%">
        <el-option v-for="u in availableUsers" :key="u.id" :label="`${u.username} (${u.email})`" :value="u.id" />
      </el-select>
      <template #footer>
        <el-button @click="showAddMember = false">取消</el-button>
        <el-button type="primary" @click="handleAdd">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { getTeam, addMember, removeMember } from '../api/teams'
import { getPasswords } from '../api/passwords'
import { getAllUsers } from '../api/users'
import { ROLES } from '../utils/constants'
import { ElMessage } from 'element-plus'

const route = useRoute()
const auth = useAuthStore()
const team = ref(null)
const passwords = ref([])
const allUsers = ref([])
const showAddMember = ref(false)
const selectedUser = ref(null)

const availableUsers = computed(() => {
  if (!team.value) return []
  const memberIds = new Set(team.value.members.map(m => m.user_id))
  return allUsers.value.filter(u => !memberIds.has(u.id))
})

async function loadData() {
  const id = route.params.id
  const [teamRes, pwRes] = await Promise.all([getTeam(id), getPasswords({ team_id: id })])
  team.value = teamRes.data
  passwords.value = pwRes.data
}

async function handleAdd() {
  if (!selectedUser.value) return
  await addMember(route.params.id, selectedUser.value)
  ElMessage.success('已添加')
  showAddMember.value = false
  selectedUser.value = null
  loadData()
}

async function handleRemove(userId) {
  await removeMember(route.params.id, userId)
  ElMessage.success('已移除')
  loadData()
}

onMounted(async () => {
  await loadData()
  const { data } = await getAllUsers()
  allUsers.value = data
})
</script>
