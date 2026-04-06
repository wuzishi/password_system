<template>
  <div>
    <h2 style="margin-bottom: 24px">Dashboard</h2>

    <!-- Alerts -->
    <div v-if="invalidPasswords.length > 0" class="alert alert-danger">
      <span class="alert-icon">!</span>
      <div>
        <strong>{{ invalidPasswords.length }} server password(s) failed verification</strong>
        <div v-for="p in invalidPasswords" :key="p.id" class="alert-item">
          {{ p.title }} <span class="dim">{{ p.host }}:{{ p.port || 22 }}</span>
        </div>
      </div>
    </div>

    <div v-if="expiringPasswords.length > 0" class="alert alert-warning">
      <span class="alert-icon">&#9888;</span>
      <div>
        <strong>{{ expiringPasswords.length }} server password(s) expiring soon</strong>
        <div v-for="p in expiringPasswords" :key="p.id" class="alert-item">
          <span :class="p.expire_status === 'expired' ? 'text-red' : 'text-yellow'">
            {{ p.expire_status === 'expired' ? 'expired' : `${p.expire_remaining_days}d left` }}
          </span>
          {{ p.title }} <span class="dim">{{ p.host }}:{{ p.port || 22 }}</span>
        </div>
      </div>
    </div>

    <!-- Stats -->
    <div class="stat-grid">
      <div class="stat-card">
        <div class="stat-label">Websites</div>
        <div class="stat-value">{{ stats.websiteCount }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Servers</div>
        <div class="stat-value">{{ stats.serverCount }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Teams</div>
        <div class="stat-value">{{ stats.teams }}</div>
      </div>
      <div class="stat-card" :class="{ 'stat-alert': stats.expiredCount > 0 }">
        <div class="stat-label">Expiring</div>
        <div class="stat-value" :style="{ color: stats.expiredCount > 0 ? 'var(--red)' : '' }">{{ stats.expiredCount }}</div>
      </div>
    </div>

    <!-- Recent -->
    <div class="section-header">Recent Passwords</div>
    <el-table :data="recentPasswords" style="width: 100%">
      <el-table-column label="Type" width="80">
        <template #default="{ row }">
          <span class="type-dot" :class="row.category === 'server' ? 'dot-red' : 'dot-blue'"></span>
          {{ row.category === 'server' ? 'SVR' : 'WEB' }}
        </template>
      </el-table-column>
      <el-table-column prop="title" label="Title" />
      <el-table-column prop="username" label="Account" />
      <el-table-column label="Address" show-overflow-tooltip>
        <template #default="{ row }">
          <span class="dim">{{ row.category === 'server' ? `${row.host}:${row.port || 22}` : row.url }}</span>
        </template>
      </el-table-column>
      <el-table-column label="Status" width="100">
        <template #default="{ row }">
          <template v-if="row.expire_days > 0">
            <span v-if="row.expire_status === 'expired'" class="text-red">expired</span>
            <span v-else-if="row.expire_status === 'warning'" class="text-yellow">{{ row.expire_remaining_days }}d</span>
            <span v-else class="text-green">ok</span>
          </template>
          <span v-else class="dim">-</span>
        </template>
      </el-table-column>
      <el-table-column prop="updated_at" label="Updated" width="170">
        <template #default="{ row }">
          <span class="dim">{{ formatTime(row.updated_at) }}</span>
        </template>
      </el-table-column>
    </el-table>
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
  gap: 16px;
  margin-bottom: 32px;
}

.stat-card {
  background: var(--bg-elevated);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius);
  padding: 20px 24px;
  transition: border-color 0.15s;
}

.stat-card:hover {
  border-color: var(--border-default);
}

.stat-card.stat-alert {
  border-color: rgba(239, 68, 68, 0.3);
}

.stat-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -1px;
}

.section-header {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 12px;
}

.alert {
  display: flex;
  gap: 12px;
  padding: 14px 18px;
  border-radius: var(--radius);
  margin-bottom: 16px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-subtle);
  font-size: 13px;
  line-height: 1.6;
}

.alert-danger {
  border-color: rgba(239, 68, 68, 0.25);
}

.alert-warning {
  border-color: rgba(245, 166, 35, 0.25);
}

.alert-icon {
  font-size: 16px;
  flex-shrink: 0;
  margin-top: 1px;
}

.alert-danger .alert-icon { color: var(--red); }
.alert-warning .alert-icon { color: var(--yellow); }

.alert-item {
  color: var(--text-secondary);
  margin-top: 2px;
}

.dim { color: var(--text-tertiary); }
.text-red { color: var(--red); font-weight: 500; }
.text-yellow { color: var(--yellow); font-weight: 500; }
.text-green { color: var(--green); font-weight: 500; }

.type-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  margin-right: 4px;
}
.dot-red { background: var(--red); }
.dot-blue { background: #60a5fa; }
</style>
