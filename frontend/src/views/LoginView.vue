<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-header">
        <div class="logo-icon">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2L3 7v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-9-5z"/>
            <path d="M12 8v4m0 4h.01"/>
          </svg>
        </div>
        <h2>团队密码平台</h2>
        <p>安全管理你的团队凭据</p>
      </div>
      <el-form ref="formRef" :model="form" :rules="rules" @submit.prevent="handleLogin">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="用户名" size="large" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" placeholder="密码" type="password" show-password size="large" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" native-type="submit" :loading="loading" size="large" style="width: 100%; height: 44px; font-size: 15px">
            登 录
          </el-button>
        </el-form-item>
      </el-form>
      <div class="login-footer">
        <span>安全登录</span>
      </div>
    </div>
    <!-- Theme toggle on login page -->
    <div class="login-theme" @click="themeStore.toggle()">
      <el-icon v-if="themeStore.mode === 'dark'"><Sunny /></el-icon>
      <el-icon v-else><Moon /></el-icon>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useThemeStore } from '../stores/theme'
import { ElMessage } from 'element-plus'

const auth = useAuthStore()
const themeStore = useThemeStore()
const router = useRouter()
const formRef = ref()
const loading = ref(false)

const form = reactive({ username: '', password: '' })
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function handleLogin() {
  await formRef.value.validate()
  loading.value = true
  try {
    await auth.login(form)
    ElMessage.success('登录成功')
    router.push('/dashboard')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-primary);
  position: relative;
}
.login-card {
  width: 400px;
  padding: 48px 40px 36px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-subtle);
  border-radius: 20px;
  box-shadow: var(--shadow-dialog);
}
.login-header {
  text-align: center;
  margin-bottom: 40px;
}
.logo-icon {
  color: var(--text-primary);
  margin-bottom: 20px;
}
.login-header h2 {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.5px;
  margin-bottom: 8px;
}
.login-header p {
  color: var(--text-tertiary);
  font-size: 14px;
}
.login-footer {
  text-align: center;
  margin-top: 12px;
}
.login-footer span {
  color: var(--text-tertiary);
  font-size: 12px;
}
.login-theme {
  position: absolute;
  top: 24px;
  right: 24px;
  cursor: pointer;
  color: var(--text-tertiary);
  font-size: 20px;
  padding: 8px;
  border-radius: 8px;
  transition: all 0.15s;
}
.login-theme:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}
</style>
