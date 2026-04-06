<template>
  <div style="max-width: 500px">
    <h2 style="margin-bottom: 20px">个人设置</h2>

    <el-card>
      <template #header><span>账号信息</span></template>
      <el-descriptions :column="1" border>
        <el-descriptions-item label="用户名">{{ auth.username }}</el-descriptions-item>
        <el-descriptions-item label="角���">
          <el-tag :type="ROLES[auth.role]?.type" size="small">{{ ROLES[auth.role]?.label }}</el-tag>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card style="margin-top: 20px">
      <template #header><span>修改密码</span></template>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="当前密码" prop="old_password">
          <el-input v-model="form.old_password" type="password" show-password autocomplete="current-password" />
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input v-model="form.new_password" type="password" show-password autocomplete="new-password" />
          <div v-if="form.new_password" style="margin-top: 4px; font-size: 12px; color: var(--text-tertiary)">
            密码强度:
            <span :style="{ color: pwdStrength.color, fontWeight: 600 }">{{ pwdStrength.label }}</span>
            <div style="margin-top: 2px; font-size: 11px; color: var(--text-tertiary)">
              要求: 至少8位，包含大小写字母、数字、特殊字符
            </div>
          </div>
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm">
          <el-input v-model="form.confirm" type="password" show-password autocomplete="new-password" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSubmit">保存</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useAuthStore } from '../stores/auth'
import { changePassword } from '../api/users'
import { ROLES } from '../utils/constants'
import { ElMessage } from 'element-plus'

const auth = useAuthStore()
const formRef = ref()
const form = reactive({ old_password: '', new_password: '', confirm: '' })

const validateConfirm = (rule, value, callback) => {
  if (value !== form.new_password) callback(new Error('两次密码不一致'))
  else callback()
}

const validateStrong = (rule, value, callback) => {
  if (!value) return callback()
  if (value.length < 8) return callback(new Error('至少8位'))
  if (!/[a-z]/.test(value)) return callback(new Error('需包含小写字母'))
  if (!/[A-Z]/.test(value)) return callback(new Error('需包含大写字母'))
  if (!/\d/.test(value)) return callback(new Error('需包含数字'))
  if (!/[!@#$%^&*()_+\-=\[\]{};:'",.<>?/\\|`~]/.test(value)) return callback(new Error('需包含特殊字符'))
  callback()
}

const pwdStrength = computed(() => {
  const v = form.new_password
  if (!v) return { label: '', color: '' }
  let score = 0
  if (v.length >= 8) score++
  if (v.length >= 12) score++
  if (/[a-z]/.test(v) && /[A-Z]/.test(v)) score++
  if (/\d/.test(v)) score++
  if (/[^a-zA-Z0-9]/.test(v)) score++
  if (score <= 2) return { label: '弱', color: 'var(--red, #f56c6c)' }
  if (score <= 3) return { label: '中', color: 'var(--yellow, #e6a23c)' }
  return { label: '强', color: 'var(--green, #67c23a)' }
})

const rules = {
  old_password: [{ required: true, message: '请输入当前��码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { validator: validateStrong, trigger: 'blur' },
  ],
  confirm: [{ required: true, message: '请确认密码', trigger: 'blur' }, { validator: validateConfirm, trigger: 'blur' }],
}

async function handleSubmit() {
  await formRef.value.validate()
  await changePassword({ old_password: form.old_password, new_password: form.new_password })
  ElMessage.success('密码已修改')
  form.old_password = ''
  form.new_password = ''
  form.confirm = ''
}
</script>
