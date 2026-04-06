<template>
  <div>
    <!-- Alerts -->
    <div v-if="invalidPasswords.length > 0" class="alert alert-danger">
      <span class="alert-dot dot-red"></span>
      <div>
        <strong>{{ invalidPasswords.length }} 个服务器密码验证失败</strong>
        <div v-for="p in invalidPasswords" :key="p.id" class="alert-item">
          {{ p.title }} <span class="dim">{{ p.host }}:{{ p.port || 22 }}</span>
        </div>
      </div>
    </div>

    <div v-if="expiringPasswords.length > 0" class="alert alert-warning">
      <span class="alert-dot dot-yellow"></span>
      <div>
        <strong>{{ expiringPasswords.length }} 个服务器密码即将过期</strong>
        <div v-for="p in expiringPasswords" :key="p.id" class="alert-item">
          <span :class="p.expire_status === 'expired' ? 'text-red' : 'text-yellow'">
            {{ p.expire_status === 'expired' ? '已过期' : `剩余${p.expire_remaining_days}天` }}
          </span>
          {{ p.title }}
        </div>
      </div>
    </div>

    <!-- Stats -->
    <div class="stat-grid">
      <div class="stat-card">
        <div class="stat-label">网站密码</div>
        <div class="stat-value">{{ stats.websiteCount }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">服务器密码</div>
        <div class="stat-value">{{ stats.serverCount }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">我的团队</div>
        <div class="stat-value">{{ stats.teams }}</div>
      </div>
      <div class="stat-card" :class="{ 'stat-alert': stats.expiredCount > 0 }">
        <div class="stat-label">需关注</div>
        <div class="stat-value" :style="{ color: stats.expiredCount > 0 ? 'var(--red)' : '' }">{{ stats.expiredCount }}</div>
      </div>
    </div>

    <!-- Recent -->
    <div class="section">
      <div class="section-label">最近更新</div>
      <div class="table-wrapper">
        <el-table :data="recentPasswords" style="width: 100%">
          <el-table-column label="类型" width="90">
            <template #default="{ row }">
              <span class="type-badge" :class="row.category === 'server' ? 'type-server' : 'type-web'">
                {{ row.category === 'server' ? '服务器' : '网站' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="title" label="标题" min-width="160" />
          <el-table-column prop="username" label="账号" min-width="120" />
          <el-table-column label="地址" min-width="180" show-overflow-tooltip>
            <template #default="{ row }">
              <span class="dim">{{ row.category === 'server' ? `${row.host}:${row.port || 22}` : row.url }}</span>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <template v-if="row.expire_days > 0">
                <span v-if="row.expire_status === 'expired'" class="text-red">已过期</span>
                <span v-else-if="row.expire_status === 'warning'" class="text-yellow">{{ row.expire_remaining_days }}天</span>
                <span v-else class="text-green">正常</span>
              </template>
              <span v-else class="dim">—</span>
            </template>
          </el-table-column>
          <el-table-column prop="updated_at" label="更新时间" width="170">
            <template #default="{ row }">
              <span class="dim">{{ formatTime(row.updated_at) }}</span>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
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
.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 40px;
}

.stat-card {
  background: var(--bg-elevated);
  border: 1px solid var(--border-subtle);
  border-radius: 14px;
  padding: 28px 28px 24px;
  transition: border-color 0.2s;
}
.stat-card:hover { border-color: var(--border-default); }
.stat-card.stat-alert { border-color: rgba(248,113,113,0.25); }

.stat-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-tertiary);
  margin-bottom: 12px;
}

.stat-value {
  font-size: 40px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -2px;
  line-height: 1;
}

.section { margin-bottom: 32px; }

.section-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 16px;
}

.table-wrapper {
  background: var(--bg-elevated);
  border: 1px solid var(--border-subtle);
  border-radius: 14px;
  overflow: hidden;
}

.alert {
  display: flex;
  gap: 14px;
  padding: 18px 22px;
  border-radius: 14px;
  margin-bottom: 20px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-subtle);
  font-size: 13px;
  line-height: 1.7;
}
.alert-danger { border-color: rgba(248,113,113,0.2); }
.alert-warning { border-color: rgba(251,191,36,0.2); }

.alert-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 6px;
}
.dot-red { background: var(--red); }
.dot-yellow { background: var(--yellow); }

.alert-item { color: var(--text-secondary); margin-top: 2px; }

.dim { color: var(--text-tertiary); }
.text-red { color: var(--red); font-weight: 600; }
.text-yellow { color: var(--yellow); font-weight: 600; }
.text-green { color: var(--green); font-weight: 600; }

.type-badge {
  font-size: 12px;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: 5px;
}
.type-server {
  background: rgba(248,113,113,0.12);
  color: var(--red);
}
.type-web {
  background: rgba(96,165,250,0.12);
  color: var(--blue);
}
</style>
