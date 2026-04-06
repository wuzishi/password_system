<template>
  <el-container style="height: 100vh">
    <el-aside :width="isCollapse ? '68px' : '240px'" class="sidebar">
      <div class="logo" :class="{ collapsed: isCollapse }">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="color: var(--text-primary); flex-shrink: 0">
          <path d="M12 2L3 7v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-9-5z"/>
        </svg>
        <span v-if="!isCollapse" class="logo-text">密码平台</span>
      </div>
      <el-menu
        :default-active="$route.path"
        router
        :collapse="isCollapse"
        :collapse-transition="false"
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataBoard /></el-icon>
          <template #title>工作台</template>
        </el-menu-item>
        <el-menu-item index="/passwords">
          <el-icon><Key /></el-icon>
          <template #title>密码库</template>
        </el-menu-item>
        <el-menu-item index="/servers">
          <el-icon><Monitor /></el-icon>
          <template #title>服务器</template>
        </el-menu-item>
        <el-menu-item index="/teams">
          <el-icon><UserFilled /></el-icon>
          <template #title>团队</template>
        </el-menu-item>
        <el-menu-item index="/approvals">
          <el-icon><Stamp /></el-icon>
          <template #title>
            审批
            <span v-if="pendingCount > 0" class="badge">{{ pendingCount }}</span>
          </template>
        </el-menu-item>
        <el-menu-item v-if="auth.isAdmin" index="/users">
          <el-icon><User /></el-icon>
          <template #title>用户</template>
        </el-menu-item>
        <el-menu-item v-if="auth.isAdmin" index="/audit">
          <el-icon><Document /></el-icon>
          <template #title>审计</template>
        </el-menu-item>
      </el-menu>

      <!-- Bottom: theme toggle -->
      <div class="sidebar-bottom" v-if="!isCollapse">
        <div class="theme-toggle" @click="themeStore.toggle()">
          <el-icon v-if="themeStore.mode === 'dark'"><Sunny /></el-icon>
          <el-icon v-else><Moon /></el-icon>
          <span>{{ themeStore.mode === 'dark' ? '浅色模式' : '深色模式' }}</span>
        </div>
      </div>
      <div v-else class="sidebar-bottom-mini" @click="themeStore.toggle()">
        <el-icon v-if="themeStore.mode === 'dark'"><Sunny /></el-icon>
        <el-icon v-else><Moon /></el-icon>
      </div>
    </el-aside>

    <el-container>
      <el-header class="top-header">
        <div style="display: flex; align-items: center; gap: 16px">
          <el-icon style="cursor: pointer; font-size: 18px; color: var(--text-tertiary)" @click="isCollapse = !isCollapse">
            <Fold v-if="!isCollapse" /><Expand v-else />
          </el-icon>
          <span class="page-title">{{ pageTitle }}</span>
        </div>
        <div style="display: flex; align-items: center; gap: 16px">
          <span class="role-label">{{ roleTag.label }}</span>
          <el-dropdown @command="handleCommand">
            <span class="user-info">
              <span class="avatar">{{ auth.username[0]?.toUpperCase() }}</span>
              <span class="username">{{ auth.username }}</span>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人设置</el-dropdown-item>
                <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="main-content">
        <div class="content-wrapper">
          <router-view />
        </div>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { useThemeStore } from '../../stores/theme'
import { ROLES } from '../../utils/constants'
import { getPendingCount } from '../../api/approvals'

const auth = useAuthStore()
const themeStore = useThemeStore()
const router = useRouter()
const route = useRoute()
const isCollapse = ref(false)
const pendingCount = ref(0)

const PAGE_TITLES = {
  '/dashboard': '工作台',
  '/passwords': '密码库',
  '/servers': '服务器管理',
  '/teams': '团队管理',
  '/approvals': '审批管理',
  '/users': '用户管理',
  '/audit': '审计日志',
  '/profile': '个人设置',
}

const pageTitle = computed(() => PAGE_TITLES[route.path] || '')

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
  if (cmd === 'logout') { auth.logout(); router.push('/login') }
  else if (cmd === 'profile') { router.push('/profile') }
}
</script>

<style scoped>
.sidebar {
  background: var(--bg-elevated);
  border-right: 1px solid var(--border-subtle);
  transition: width 0.2s ease;
  display: flex;
  flex-direction: column;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
}

.logo-text {
  color: var(--text-primary);
  font-size: 16px;
  font-weight: 700;
  letter-spacing: -0.3px;
  white-space: nowrap;
}

.logo.collapsed .logo-text { display: none; }

:deep(.el-menu) {
  border-right: none !important;
  padding: 12px 10px;
  flex: 1;
}

:deep(.el-menu-item) {
  height: 42px !important;
  line-height: 42px !important;
  border-radius: 8px;
  margin-bottom: 2px;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  transition: all 0.15s ease;
}

:deep(.el-menu-item:hover) {
  background: var(--bg-hover) !important;
  color: var(--text-primary);
}

:deep(.el-menu-item.is-active) {
  background: var(--accent-bg) !important;
  color: var(--text-primary) !important;
}

.badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  margin-left: 8px;
  background: var(--red);
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  border-radius: 9px;
}

.sidebar-bottom {
  padding: 12px 10px;
  border-top: 1px solid var(--border-subtle);
  flex-shrink: 0;
}

.theme-toggle {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  color: var(--text-tertiary);
  transition: all 0.15s;
}

.theme-toggle:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.sidebar-bottom-mini {
  padding: 16px;
  border-top: 1px solid var(--border-subtle);
  text-align: center;
  cursor: pointer;
  color: var(--text-tertiary);
  transition: color 0.15s;
  flex-shrink: 0;
}
.sidebar-bottom-mini:hover { color: var(--text-primary); }

.top-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--bg-elevated);
  border-bottom: 1px solid var(--border-subtle);
  padding: 0 32px;
  height: 60px;
}

.page-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.role-label {
  font-size: 12px;
  color: var(--text-tertiary);
  padding: 4px 10px;
  border: 1px solid var(--border-default);
  border-radius: 6px;
  font-weight: 500;
}

.user-info {
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 10px;
  transition: opacity 0.15s;
}
.user-info:hover { opacity: 0.8; }

.avatar {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: var(--accent-bg);
  border: 1px solid var(--border-default);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.username {
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 500;
}

.main-content {
  background: var(--bg-primary);
  padding: 0;
  overflow-y: auto;
}

.content-wrapper {
  max-width: 1400px;
  margin: 0 auto;
  padding: 36px 48px;
}

@media (max-width: 1200px) {
  .content-wrapper { padding: 24px 28px; }
}
</style>
