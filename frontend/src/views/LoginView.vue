<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-header">
        <div class="logo-icon">
          <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2L3 7v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-9-5z"/>
            <path d="M12 8v4m0 4h.01"/>
          </svg>
        </div>
        <h2>Password Vault</h2>
        <p>Secure team credential management</p>
      </div>
      <el-form ref="formRef" :model="form" :rules="rules" @submit.prevent="handleLogin">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="Username" size="large" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" placeholder="Password" type="password" show-password size="large" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" native-type="submit" :loading="loading" size="large" style="width: 100%">
            Sign In
          </el-button>
        </el-form-item>
      </el-form>
      <div class="login-footer">
        <span>Default: admin / admin123</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { ElMessage } from 'element-plus'

const auth = useAuthStore()
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
}
.login-card {
  width: 380px;
  padding: 48px 40px 36px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-subtle);
  border-radius: 16px;
}
.login-header {
  text-align: center;
  margin-bottom: 36px;
}
.logo-icon {
  color: var(--text-primary);
  margin-bottom: 16px;
}
.login-header h2 {
  font-size: 22px;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: -0.5px;
  margin-bottom: 6px;
}
.login-header p {
  color: var(--text-tertiary);
  font-size: 13px;
}
.login-footer {
  text-align: center;
  margin-top: 8px;
}
.login-footer span {
  color: var(--text-tertiary);
  font-size: 12px;
}
</style>
