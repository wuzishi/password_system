<template>
  <el-container style="height: 100vh">
    <el-aside :width="isCollapse ? '64px' : '220px'" style="transition: width 0.3s; background: #1d1e2c">
      <div class="logo" :class="{ collapsed: isCollapse }">
        <el-icon size="24" color="#409eff"><Lock /></el-icon>
        <span v-if="!isCollapse" class="logo-text">密码平台</span>
      </div>
      <el-menu
        :default-active="$route.path"
        router
        :collapse="isCollapse"
        background-color="#1d1e2c"
        text-color="#a3a6b4"
        active-text-color="#409eff"
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
          <template #title>服务器管理</template>
        </el-menu-item>
        <el-menu-item index="/teams">
          <el-icon><UserFilled /></el-icon>
          <template #title>团队管理</template>
        </el-menu-item>
        <el-menu-item v-if="auth.isAdmin" index="/users">
          <el-icon><User /></el-icon>
          <template #title>用户管理</template>
        </el-menu-item>
        <el-menu-item v-if="auth.isAdmin" index="/audit">
          <el-icon><Document /></el-icon>
          <template #title>审计日志</template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header style="display: flex; align-items: center; justify-content: space-between; background: #fff; border-bottom: 1px solid #e8e8e8; padding: 0 20px">
        <el-icon style="cursor: pointer; font-size: 20px" @click="isCollapse = !isCollapse">
          <Fold v-if="!isCollapse" /><Expand v-else />
        </el-icon>
        <div style="display: flex; align-items: center; gap: 16px">
          <el-tag :type="roleTag.type" size="small">{{ roleTag.label }}</el-tag>
          <el-dropdown @command="handleCommand">
            <span style="cursor: pointer; display: flex; align-items: center; gap: 6px">
              <el-avatar :size="32" style="background: #409eff">{{ auth.username[0]?.toUpperCase() }}</el-avatar>
              {{ auth.username }}
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

      <el-main style="background: #f0f2f5; padding: 20px; overflow-y: auto">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { ROLES } from '../../utils/constants'

const auth = useAuthStore()
const router = useRouter()
const isCollapse = ref(false)

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
.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  border-bottom: 1px solid rgba(255,255,255,0.05);
}
.logo-text {
  color: #fff;
  font-size: 18px;
  font-weight: 600;
  white-space: nowrap;
}
.logo.collapsed .logo-text {
  display: none;
}
.el-menu {
  border-right: none;
}
</style>
