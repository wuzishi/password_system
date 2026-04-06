<template>
  <div>
    <h2 style="margin-bottom: 20px">工作台</h2>

    <!-- SSH verification failed alert -->
    <el-alert
      v-if="invalidPasswords.length > 0"
      :title="`${invalidPasswords.length} 个服务器密码验证失败`"
      type="error"
      show-icon
      :closable="false"
      style="margin-bottom: 12px"
    >
      <div style="margin-top: 8px">
        <div v-for="p in invalidPasswords" :key="p.id" style="margin-bottom: 4px; display: flex; align-items: center; gap: 8px">
          <el-tag type="danger" size="small" effect="dark">密码失效</el-tag>
          <span>{{ p.title }}</span>
          <span style="color: #999">({{ p.host }}{{ p.port ? ':' + p.port : '' }})</span>
          <span v-if="p.last_verified_at" style="color: #999; font-size: 12px">验证于 {{ formatTime(p.last_verified_at) }}</span>
        </div>
      </div>
    </el-alert>

    <!-- Expiring passwords alert -->
    <el-alert
      v-if="expiringPasswords.length > 0"
      :title="`${expiringPasswords.length} 个服务器密码即将过期`"
      type="warning"
      show-icon
      :closable="false"
      style="margin-bottom: 12px"
    >
      <div style="margin-top: 8px">
        <div v-for="p in expiringPasswords" :key="p.id" style="margin-bottom: 4px; display: flex; align-items: center; gap: 8px">
          <el-tag :type="p.expire_status === 'expired' ? 'danger' : 'warning'" size="small" effect="dark">
            {{ p.expire_status === 'expired' ? '已过期' : `${p.expire_remaining_days}天后过期` }}
          </el-tag>
          <span>{{ p.title }}</span>
          <span style="color: #999">({{ p.host }}{{ p.port ? ':' + p.port : '' }})</span>
        </div>
      </div>
    </el-alert>

    <el-row :gutter="20">
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header><span>网站密码</span></template>
          <div class="stat-num">{{ stats.websiteCount }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header><span>服务器密码</span></template>
          <div class="stat-num">{{ stats.serverCount }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header><span>我的团队</span></template>
          <div class="stat-num">{{ stats.teams }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" :class="{ 'expire-card': stats.expiredCount > 0 }">
          <template #header><span>密码过期/即将过期</span></template>
          <div class="stat-num" :style="{ color: stats.expiredCount > 0 ? '#f56c6c' : '#409eff' }">
            {{ stats.expiredCount }}
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card style="margin-top: 20px">
      <template #header><span>最近密码</span></template>
      <el-table :data="recentPasswords" stripe>
        <el-table-column label="分类" width="90">
          <template #default="{ row }">
            <el-tag :type="row.category === 'server' ? 'danger' : ''" size="small" effect="plain">
              {{ row.category === 'server' ? '服务器' : '网站' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" />
        <el-table-column prop="username" label="用户名" />
        <el-table-column label="地址" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.category === 'server'">{{ row.host }}{{ row.port ? ':' + row.port : '' }}</span>
            <span v-else>{{ row.url }}</span>
          </template>
        </el-table-column>
        <el-table-column label="密码状态" width="120">
          <template #default="{ row }">
            <template v-if="row.expire_days > 0">
              <el-tag v-if="row.expire_status === 'expired'" type="danger" size="small" effect="dark">已过期</el-tag>
              <el-tag v-else-if="row.expire_status === 'warning'" type="warning" size="small">{{ row.expire_remaining_days }}天</el-tag>
              <el-tag v-else type="success" size="small">正常</el-tag>
            </template>
            <span v-else style="color:#999; font-size:12px">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新时间" width="180">
          <template #default="{ row }">{{ formatTime(row.updated_at) }}</template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getPasswords, getExpiringPasswords } from '../api/passwords'
import { getTeams } from '../api/teams'

const stats = ref({ websiteCount: 0, serverCount: 0, teams: 0, expiredCount: 0 })
const recentPasswords = ref([])
const expiringPasswords = ref([])
const invalidPasswords = ref([])

function formatTime(t) {
  if (!t) return ''
  return new Date(t).toLocaleString('zh-CN')
}

onMounted(async () => {
  const [pwRes, teamRes, expRes] = await Promise.all([
    getPasswords(), getTeams(), getExpiringPasswords(),
  ])
  const passwords = pwRes.data
  recentPasswords.value = passwords.slice(0, 10)
  stats.value.websiteCount = passwords.filter(p => (p.category || 'website') === 'website').length
  stats.value.serverCount = passwords.filter(p => p.category === 'server').length
  stats.value.teams = teamRes.data.length
  expiringPasswords.value = expRes.data
  stats.value.expiredCount = expRes.data.length
  invalidPasswords.value = passwords.filter(p => p.category === 'server' && p.verify_status === 'invalid')
})
</script>

<style scoped>
.stat-num {
  font-size: 36px;
  font-weight: 700;
  color: #409eff;
  text-align: center;
}
.expire-card {
  border-color: #f56c6c;
}
</style>
