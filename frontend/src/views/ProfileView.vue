<template>
  <div style="max-width: 500px">
    <h2 style="margin-bottom: 20px">个人设置</h2>

    <el-card>
      <template #header><span>账号信息</span></template>
      <el-descriptions :column="1" border>
        <el-descriptions-item label="用户名">{{ auth.username }}</el-descriptions-item>
        <el-descriptions-item label="角色">
          <el-tag :type="ROLES[auth.role]?.type" size="small">{{ ROLES[auth.role]?.label }}</el-tag>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card style="margin-top: 20px">
      <template #header><span>修改密码</span></template>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="当前密码" prop="old_password">
          <el-input v-model="form.old_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input v-model="form.new_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm">
          <el-input v-model="form.confirm" type="password" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSubmit">保存</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
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

const rules = {
  old_password: [{ required: true, message: '请输入当前密码', trigger: 'blur' }],
  new_password: [{ required: true, message: '请输入新密码', trigger: 'blur' }, { min: 6, message: '至少6位', trigger: 'blur' }],
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
