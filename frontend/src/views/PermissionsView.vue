<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px">
      <h2>权限管理</h2>
      <el-button type="primary" :loading="saving" @click="handleSave">保存修改</el-button>
    </div>

    <div class="perm-card">
      <table class="perm-table" v-if="permData">
        <thead>
          <tr>
            <th class="perm-key-col">权限项</th>
            <th v-for="role in permData.roles" :key="role" class="perm-role-col">
              <el-tag :type="ROLES[role]?.type" size="small">{{ ROLES[role]?.label }}</el-tag>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in permData.permissions" :key="p.key" :class="{ 'section-row': p.key.startsWith('func.') && prevIsPage(p.key) }">
            <td class="perm-key-col">
              <span :class="p.key.startsWith('page.') ? 'perm-page' : 'perm-func'">
                {{ p.key.startsWith('page.') ? '页面' : '功能' }}
              </span>
              {{ p.label }}
            </td>
            <td v-for="role in permData.roles" :key="role" class="perm-role-col">
              <el-switch
                v-model="matrix[role][p.key]"
                :disabled="role === 'admin'"
                size="small"
              />
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div style="margin-top: 16px; color: var(--text-tertiary); font-size: 13px">
      管理员权限始终为全部开启，不可修改。修改后需要对应用户重新登录生效。
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import { getAllPermissions, updatePermissions } from '../api/permissions'
import { ROLES } from '../utils/constants'
import { ElMessage } from 'element-plus'

const permData = ref(null)
const matrix = reactive({})
const saving = ref(false)

let permKeys = []

function prevIsPage(key) {
  const idx = permKeys.indexOf(key)
  return idx > 0 && permKeys[idx - 1].startsWith('page.')
}

onMounted(async () => {
  const { data } = await getAllPermissions()
  permData.value = data
  permKeys = data.permissions.map(p => p.key)
  for (const role of data.roles) {
    matrix[role] = {}
    for (const p of data.permissions) {
      matrix[role][p.key] = data.matrix[role]?.[p.key] ?? false
    }
  }
})

async function handleSave() {
  saving.value = true
  try {
    const items = []
    for (const role of permData.value.roles) {
      if (role === 'admin') continue
      for (const p of permData.value.permissions) {
        items.push({ role, permission_key: p.key, enabled: !!matrix[role][p.key] })
      }
    }
    await updatePermissions({ items })
    ElMessage.success('权限已更新')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.perm-card {
  background: var(--bg-elevated);
  border: 1px solid var(--border-subtle);
  border-radius: 14px;
  overflow: hidden;
}

.perm-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.perm-table thead {
  background: var(--bg-surface);
}

.perm-table th {
  padding: 14px 20px;
  text-align: center;
  font-weight: 500;
  font-size: 13px;
  color: var(--text-tertiary);
  border-bottom: 1px solid var(--border-subtle);
}

.perm-table td {
  padding: 12px 20px;
  border-bottom: 1px solid var(--border-subtle);
}

.perm-table tbody tr:last-child td {
  border-bottom: none;
}

.perm-table tbody tr:hover {
  background: var(--bg-hover);
}

.perm-key-col {
  text-align: left;
  min-width: 200px;
}

.perm-role-col {
  text-align: center;
  width: 140px;
}

.section-row td {
  border-top: 2px solid var(--border-default);
}

.perm-page, .perm-func {
  display: inline-block;
  font-size: 11px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 3px;
  margin-right: 6px;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.perm-page {
  background: rgba(96,165,250,0.15);
  color: var(--blue);
}

.perm-func {
  background: rgba(167,139,250,0.15);
  color: var(--purple);
}
</style>
