<template>
  <div class="invite-page">
    <div class="invite-card">
      <div class="invite-header">
        <el-icon size="40" color="#409eff"><Lock /></el-icon>
        <h2>加入团队密码平台</h2>
      </div>

      <!-- Loading -->
      <div v-if="loading" style="text-align: center; padding: 40px 0">
        <div class="el-icon is-loading" style="font-size: 32px; color: #409eff">
          <svg viewBox="0 0 1024 1024" width="1em" height="1em"><path d="M512 64a32 32 0 0 1 32 32v192a32 32 0 0 1-64 0V96a32 32 0 0 1 32-32" fill="currentColor"/></svg>
        </div>
        <p style="color: #999; margin-top: 12px">正在验证邀请链接...</p>
      </div>

      <!-- Error -->
      <div v-else-if="error" style="text-align: center; padding: 30px 0">
        <div style="font-size: 48px; color: #f56c6c">&#10060;</div>
        <p style="color: #f56c6c; margin-top: 12px; font-size: 16px">{{ error }}</p>
        <el-button type="primary" style="margin-top: 20px" @click="$router.push('/login')">返回登录</el-button>
      </div>

      <!-- Success - show form -->
      <div v-else-if="inviteInfo">
        <div style="background: #f0f9eb; border-radius: 8px; padding: 16px; margin-bottom: 24px; text-align: center">
          <p style="margin: 0; color: #67c23a">
            <strong>{{ inviteInfo.inviter_name }}</strong> 邀请你加入，角色为
            <el-tag :type="ROLES[inviteInfo.role]?.type" size="small">{{ ROLES[inviteInfo.role]?.label }}</el-tag>
          </p>
          <p style="margin: 8px 0 0; color: #999; font-size: 13px">邮箱: {{ inviteInfo.email }}</p>
        </div>

        <el-form ref="formRef" :model="form" :rules="rules" label-width="80px" @submit.prevent="handleSubmit">
          <el-form-item label="用户名" prop="username">
            <el-input v-model="form.username" size="large" placeholder="设置登录用户名" />
          </el-form-item>
          <el-form-item label="密码" prop="password">
            <el-input v-model="form.password" type="password" show-password size="large" placeholder="设置登录密码">
              <template #append>
                <el-button @click="generatePassword">生成</el-button>
              </template>
            </el-input>
          </el-form-item>
          <el-form-item label="确认密码" prop="confirm">
            <el-input v-model="form.confirm" type="password" show-password size="large" placeholder="再次输入密码" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" native-type="submit" size="large" :loading="submitting" style="width: 100%">
              创建账号并登录
            </el-button>
          </el-form-item>
        </el-form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { ROLES } from '../utils/constants'
import api from '../api/index'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const loading = ref(true)
const error = ref('')
const inviteInfo = ref(null)
const submitting = ref(false)
const formRef = ref()

const form = reactive({ username: '', password: '', confirm: '' })

function generatePassword() {
  const lower = 'abcdefghijklmnopqrstuvwxyz'
  const upper = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
  const digits = '0123456789'
  const symbols = '!@#$%^&*()_+-=[]{};:,.<>?/|~'
  const all = lower + upper + digits + symbols
  const rand = (set) => set[Math.floor(Math.random() * set.length)]
  // 保证四类各至少一位，总长 16
  const chars = [rand(lower), rand(upper), rand(digits), rand(symbols)]
  for (let i = 0; i < 12; i++) chars.push(rand(all))
  // Fisher–Yates 洗牌
  for (let i = chars.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[chars[i], chars[j]] = [chars[j], chars[i]]
  }
  const pwd = chars.join('')
  form.password = pwd
  form.confirm = pwd
  // 复制到剪贴板，提醒用户保存
  if (navigator.clipboard) {
    navigator.clipboard.writeText(pwd).then(
      () => ElMessage.success('已生成强密码并复制到剪贴板，请妥善保存'),
      () => ElMessage.success('已生成强密码，请妥善保存'),
    )
  } else {
    ElMessage.success('已生成强密码，请妥善保存')
  }
}

const validateConfirm = (rule, value, callback) => {
  if (value !== form.password) callback(new Error('两次密码不一致'))
  else callback()
}

const validateStrongPassword = (rule, value, callback) => {
  if (!value) return callback(new Error('请输入密码'))
  if (value.length < 8) return callback(new Error('密码长度不能少于 8 位'))
  if (!/[a-z]/.test(value)) return callback(new Error('密码必须包含小写字母'))
  if (!/[A-Z]/.test(value)) return callback(new Error('密码必须包含大写字母'))
  if (!/\d/.test(value)) return callback(new Error('密码必须包含数字'))
  if (!/[!@#$%^&*()_+\-=\[\]{};:'",.<>?/\\|`~]/.test(value)) return callback(new Error('密码必须包含特殊字符'))
  callback()
}

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 50, message: '用户名长度需在 2-50 字符之间', trigger: 'blur' },
  ],
  password: [
    { required: true, validator: validateStrongPassword, trigger: 'blur' },
  ],
  confirm: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirm, trigger: 'blur' },
  ],
}

onMounted(async () => {
  const token = route.query.token
  if (!token) {
    error.value = '缺少邀请令牌'
    loading.value = false
    return
  }
  try {
    const { data } = await api.get(`/auth/invite-info?token=${token}`)
    inviteInfo.value = data
  } catch (err) {
    error.value = err.response?.data?.detail || '邀请链接无效'
  } finally {
    loading.value = false
  }
})

async function handleSubmit() {
  await formRef.value.validate()
  submitting.value = true
  try {
    const { data } = await api.post('/auth/accept-invite', {
      token: route.query.token,
      username: form.username,
      password: form.password,
    })
    // Auto login
    auth.token = data.access_token
    auth.username = data.username
    auth.role = data.role
    auth.userId = data.user_id
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('username', data.username)
    localStorage.setItem('role', data.role)
    localStorage.setItem('userId', data.user_id)

    ElMessage.success('账号创建成功，欢迎加入！')
    router.push('/dashboard')
  } catch (err) {
    const detail = err.response?.data?.detail
    if (Array.isArray(detail)) {
      ElMessage.error(detail.map(d => d.msg).join('; '))
    } else if (typeof detail === 'string') {
      ElMessage.error(detail)
    }
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.invite-page {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1d1e2c 0%, #2b3a67 100%);
}
.invite-card {
  width: 460px;
  padding: 40px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.3);
}
.invite-header {
  text-align: center;
  margin-bottom: 24px;
}
.invite-header h2 {
  margin: 12px 0 0;
  color: #1d1e2c;
}
</style>
