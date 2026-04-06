<template>
  <el-container style="height: 100vh">
    <el-aside :width="isCollapse ? '64px' : '220px'" class="sidebar">
      <div class="logo" :class="{ collapsed: isCollapse }">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="color: var(--text-primary)">
          <path d="M12 2L3 7v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-9-5z"/>
        </svg>
        <span v-if="!isCollapse" class="logo-text">Vault</span>
      </div>
      <el-menu
        :default-active="$route.path"
        router
        :collapse="isCollapse"
        :collapse-transition="false"
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataBoard /></el-icon>
          <template #title>Dashboard</template>
        </el-menu-item>
        <el-menu-item index="/passwords">
          <el-icon><Key /></el-icon>
          <template #title>Passwords</template>
        </el-menu-item>
        <el-menu-item index="/servers">
          <el-icon><Monitor /></el-icon>
          <template #title>Servers</template>
        </el-menu-item>
        <el-menu-item index="/teams">
          <el-icon><UserFilled /></el-icon>
          <template #title>Teams</template>
        </el-menu-item>
        <el-menu-item index="/approvals">
          <el-icon><Stamp /></el-icon>
          <template #title>
            Approvals
            <span v-if="pendingCount > 0" class="badge">{{ pendingCount }}</span>
          </template>
        </el-menu-item>
        <el-menu-item v-if="auth.isAdmin" index="/users">
          <el-icon><User /></el-icon>
          <template #title>Users</template>
        </el-menu-item>
        <el-menu-item v-if="auth.isAdmin" index="/audit">
          <el-icon><Document /></el-icon>
          <template #title>Audit Log</template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="top-header">
        <el-icon style="cursor: pointer; font-size: 18px; color: var(--text-tertiary)" @click="isCollapse = !isCollapse">
          <Fold v-if="!isCollapse" /><Expand v-else />
        </el-icon>
        <div style="display: flex; align-items: center; gap: 14px">
          <span class="role-label">{{ roleTag.label }}</span>
          <el-dropdown @command="handleCommand">
            <span class="user-info">
              <span class="avatar">{{ auth.username[0]?.toUpperCase() }}</span>
              {{ auth.username }}
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">Settings</el-dropdown-item>
                <el-dropdown-item command="logout" divided>Sign Out</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { ROLES } from '../../utils/constants'
import { getPendingCount } from '../../api/approvals'

const auth = useAuthStore()
const router = useRouter()
const isCollapse = ref(false)
const pendingCount = ref(0)

async function loadPendingCount() {
  try {
    const { data } = await getPendingCount()
    pendingCount.value = data.count
  } catch {}
}

onMounted(() => {
  loadPendingCount()
  setInterval(loadPendingCount, 30000)
})

const roleTag = computed(() => ROLES[auth.role] || { label: auth.role, type: 'info' })

function handleCommand(cmd) {
  if (cmd === 'logout') {
    auth.logout()
    router.push('/login')
  } else if (cmd === 'profile') {
    router.push('/profile')
  }
}
</script>

<style scoped>
.sidebar {
  background: var(--bg-primary);
  border-right: 1px solid var(--border-subtle);
  transition: width 0.2s ease;
}

.logo {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  border-bottom: 1px solid var(--border-subtle);
}

.logo-text {
  color: var(--text-primary);
  font-size: 17px;
  font-weight: 600;
  letter-spacing: -0.5px;
  white-space: nowrap;
}

.logo.collapsed .logo-text {
  display: none;
}

:deep(.el-menu) {
  border-right: none !important;
  padding: 8px;
}

:deep(.el-menu-item) {
  height: 40px !important;
  line-height: 40px !important;
  border-radius: 6px;
  margin-bottom: 2px;
  font-size: 13px;
  color: var(--text-secondary);
  transition: all 0.15s ease;
}

:deep(.el-menu-item:hover) {
  background: var(--bg-hover) !important;
  color: var(--text-primary);
}

:deep(.el-menu-item.is-active) {
  background: var(--bg-hover) !important;
  color: var(--text-primary) !important;
}

.badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  margin-left: 6px;
  background: var(--red);
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  border-radius: 9px;
}

.top-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border-subtle);
  padding: 0 24px;
  height: 56px;
}

.role-label {
  font-size: 12px;
  color: var(--text-tertiary);
  padding: 3px 8px;
  border: 1px solid var(--border-default);
  border-radius: 4px;
}

.user-info {
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--text-secondary);
  transition: color 0.15s;
}

.user-info:hover {
  color: var(--text-primary);
}

.avatar {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background: var(--bg-hover);
  border: 1px solid var(--border-default);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
}

.main-content {
  background: var(--bg-primary);
  padding: 28px 32px;
  overflow-y: auto;
}
</style>
