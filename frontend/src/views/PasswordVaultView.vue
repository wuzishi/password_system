<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px">
      <h2>密码库</h2>
      <div style="display: flex; align-items: center; gap: 12px">
        <el-tag v-if="decryptStore.isValid" type="warning" effect="dark" style="font-size: 13px">
          <el-icon style="vertical-align: -2px"><Timer /></el-icon>
          解密会话剩余 {{ formattedTime }}
        </el-tag>
        <el-button v-if="canCreate" type="primary" @click="openCreate"><el-icon><Plus /></el-icon> 新建密码</el-button>
      </div>
    </div>

    <el-card style="margin-bottom: 16px">
      <el-form inline>
        <el-form-item label="搜索">
          <el-input v-model="keyword" placeholder="标题/用户名/网址/主机" clearable @clear="loadList" @keyup.enter="loadList" />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="filterCategory" clearable placeholder="全部" @change="loadList">
            <el-option label="网站" value="website" />
            <el-option label="服务器" value="server" />
            <el-option label="数据库" value="database" />
            <el-option label="API密钥" value="api_key" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="filterType" clearable placeholder="全部" @change="loadList">
            <el-option label="团队密码" value="team" />
            <el-option label="个人密码" value="personal" />
          </el-select>
        </el-form-item>
        <el-form-item label="团队">
          <el-select v-model="filterTeam" clearable placeholder="全部" @change="loadList">
            <el-option v-for="t in teams" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filterExpire" clearable placeholder="全部" @change="loadList">
            <el-option label="已过期" value="expired" />
            <el-option label="即将过期" value="warning" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadList">查询</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-table :data="passwords" stripe v-loading="loading">
      <el-table-column label="分类" width="90">
        <template #default="{ row }">
          <el-tag :type="CATEGORY_TAGS[row.category]?.type || 'info'" size="small" effect="plain">
            {{ CATEGORY_TAGS[row.category]?.label || row.category }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="title" label="标题" min-width="130" />
      <el-table-column label="安全等级" width="95">
        <template #default="{ row }">
          <el-tag v-if="row.security_level === 'personal'" type="info" size="small" effect="dark" style="background: #9b59b6; border-color: #9b59b6">个人</el-tag>
          <el-tag v-else-if="row.security_level === 'high'" type="danger" size="small" effect="dark">高</el-tag>
          <el-tag v-else-if="row.security_level === 'medium'" type="warning" size="small" effect="dark">中</el-tag>
          <el-tag v-else type="success" size="small">低</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="username" label="用户名" min-width="110" />
      <el-table-column label="密码" width="200">
        <template #default="{ row }">
          <div style="display: flex; align-items: center; gap: 6px">
            <span>{{ revealedMap[row.id] || '••••••••' }}</span>
            <el-button link type="primary" size="small" @click="toggleReveal(row)">
              {{ revealedMap[row.id] ? '隐藏' : '查看' }}
            </el-button>
            <el-button link size="small" @click="copyPassword(row)">
              <el-icon><CopyDocument /></el-icon>
            </el-button>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="地址" min-width="150" show-overflow-tooltip>
        <template #default="{ row }">
          <span v-if="row.category === 'server' || row.category === 'database'">{{ row.host }}{{ row.port ? ':' + row.port : '' }}<span v-if="row.db_name" style="color: var(--text-tertiary)"> / {{ row.db_name }}</span></span>
          <span v-else-if="row.category === 'api_key'">{{ row.api_provider }}{{ row.api_endpoint ? ' - ' + row.api_endpoint : '' }}</span>
          <span v-else>{{ row.url }}</span>
        </template>
      </el-table-column>
      <el-table-column label="归属" width="100">
        <template #default="{ row }">
          <el-tag v-if="row.team_name" size="small">{{ row.team_name }}</el-tag>
          <el-tag v-else-if="row.is_personal" type="info" size="small">个人</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="有效期" width="110">
        <template #default="{ row }">
          <template v-if="row.expire_days > 0">
            <el-tag v-if="row.expire_status === 'expired'" type="danger" size="small" effect="dark">已过期</el-tag>
            <el-tag v-else-if="row.expire_status === 'warning'" type="warning" size="small" effect="dark">
              {{ row.expire_remaining_days }}天
            </el-tag>
            <el-tag v-else type="success" size="small">{{ row.expire_remaining_days }}天</el-tag>
          </template>
          <span v-else style="color: #999; font-size: 12px">-</span>
        </template>
      </el-table-column>
      <el-table-column label="连接验证" width="130">
        <template #default="{ row }">
          <template v-if="row.category === 'server'">
            <div style="display: flex; flex-direction: column; gap: 2px">
              <el-tag v-if="row.verify_status === 'valid'" type="success" size="small">已验证</el-tag>
              <el-tag v-else-if="row.verify_status === 'invalid'" type="danger" size="small" effect="dark">密码失效</el-tag>
              <el-tag v-else-if="row.verify_status === 'error'" type="info" size="small">连接异常</el-tag>
              <el-tag v-else type="info" size="small" effect="plain">未验证</el-tag>
              <span v-if="row.last_verified_at" style="color: #999; font-size: 11px">{{ formatShortTime(row.last_verified_at) }}</span>
            </div>
          </template>
          <span v-else style="color: #999; font-size: 12px">-</span>
        </template>
      </el-table-column>
      <el-table-column prop="creator_name" label="创建人" width="90" />
      <el-table-column label="操作" width="310" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="openEdit(row)">编辑</el-button>
          <el-button v-if="row.category === 'server'" link size="small" style="color: #e6a23c" @click="openChangePwd(row)">改密</el-button>
          <el-button v-if="row.category === 'server'" link type="success" size="small" :loading="verifyingMap[row.id]" @click="handleVerify(row)">验证</el-button>
          <el-button link type="warning" size="small" @click="openShare(row)" v-if="canShare">分享</el-button>
          <el-popconfirm title="确认删除？" @confirm="handleDelete(row.id)">
            <template #reference>
              <el-button link type="danger" size="small">删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <!-- Create/Edit Dialog -->
    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑密码' : '新建密码'" width="560px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="90px">
        <el-form-item label="分类" prop="category">
          <el-select v-model="form.category" :disabled="!!editingId" style="width: 100%">
            <el-option value="website" label="网站密码" />
            <el-option value="server" label="服务器密码" />
            <el-option value="database" label="数据库密码" />
            <el-option value="api_key" label="API 密钥" />
            <el-option value="other" label="其他" />
          </el-select>
        </el-form-item>
        <el-form-item label="安全等级" prop="security_level">
          <el-radio-group v-model="form.security_level" :disabled="!!editingId">
            <el-radio-button value="personal">
              <el-icon style="vertical-align: -2px"><Lock /></el-icon> 个人
            </el-radio-button>
            <el-radio-button value="high">高安全</el-radio-button>
            <el-radio-button value="medium">中安全</el-radio-button>
            <el-radio-button value="low">低安全</el-radio-button>
          </el-radio-group>
          <div style="font-size: 12px; color: #999; margin-top: 4px">
            <span v-if="form.security_level === 'personal'">仅本人可见，包括管理员也无法查看</span>
            <span v-else-if="form.security_level === 'high'">查看需Admin审批，只读5分钟时效</span>
            <span v-else-if="form.security_level === 'medium'">Admin赋权后可读写，分享需审批</span>
            <span v-else>团队内自由共享</span>
          </div>
        </el-form-item>
        <el-form-item label="标题" prop="title">
          <el-input v-model="form.title" :placeholder="categoryPlaceholders[form.category]?.title || ''" />
        </el-form-item>
        <el-form-item :label="form.category === 'api_key' ? 'Key名称' : '用户名'" prop="username">
          <el-input v-model="form.username" :placeholder="categoryPlaceholders[form.category]?.username || ''" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <div style="display: flex; gap: 8px; width: 100%">
            <el-input v-model="form.password" show-password style="flex: 1" />
            <el-popover placement="bottom" :width="320" :visible="genPopoverVisible">
              <template #reference>
                <el-button type="primary" plain @click="genPopoverVisible = !genPopoverVisible">生成密码</el-button>
              </template>
              <div style="padding: 4px 0">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px">
                  <span style="font-weight: 600">密码生成器</span>
                  <el-button link @click="genPopoverVisible = false"><el-icon><Close /></el-icon></el-button>
                </div>
                <div style="margin-bottom: 10px">
                  <span style="font-size: 13px; color: #666">长度: {{ genOptions.length }}</span>
                  <el-slider v-model="genOptions.length" :min="8" :max="64" :step="1" style="padding: 0 6px" />
                </div>
                <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px">
                  <el-checkbox v-model="genOptions.uppercase">大写字母</el-checkbox>
                  <el-checkbox v-model="genOptions.lowercase">小写字母</el-checkbox>
                  <el-checkbox v-model="genOptions.numbers">数字</el-checkbox>
                  <el-checkbox v-model="genOptions.symbols">特殊符号</el-checkbox>
                </div>
                <div style="background: #f5f7fa; padding: 10px; border-radius: 6px; font-family: monospace; font-size: 14px; word-break: break-all; margin-bottom: 10px; min-height: 40px">
                  {{ previewPassword }}
                </div>
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 10px">
                  <span style="font-size: 13px; color: #666">强度:</span>
                  <el-progress :percentage="strengthPercent" :color="strengthColor" :stroke-width="10" style="flex: 1" :show-text="false" />
                  <span :style="{ color: strengthColor, fontSize: '13px', fontWeight: 600 }">{{ strengthLabel }}</span>
                </div>
                <div style="display: flex; gap: 8px">
                  <el-button size="small" @click="refreshPreview">换一个</el-button>
                  <el-button size="small" type="primary" @click="applyGenerated">使用此密码</el-button>
                </div>
              </div>
            </el-popover>
          </div>
        </el-form-item>
        <!-- 网站 -->
        <el-form-item v-if="form.category === 'website' || form.category === 'other'" label="网址">
          <el-input v-model="form.url" placeholder="https://" />
        </el-form-item>
        <!-- 服务器 -->
        <template v-if="form.category === 'server'">
          <el-form-item label="主机地址">
            <el-input v-model="form.host" placeholder="IP 或域名" />
          </el-form-item>
          <el-form-item label="端口">
            <el-input-number v-model="form.port" :min="1" :max="65535" />
          </el-form-item>
          <el-form-item label="过期天数">
            <el-input-number v-model="form.expire_days" :min="0" :step="30" />
            <span style="margin-left: 8px; color: var(--text-tertiary); font-size: 12px">0=不过期，默认90天</span>
          </el-form-item>
        </template>
        <!-- 数据库 -->
        <template v-if="form.category === 'database'">
          <el-form-item label="数据库类型">
            <el-select v-model="form.db_type" placeholder="选择类型" style="width: 100%">
              <el-option value="mysql" label="MySQL" />
              <el-option value="postgresql" label="PostgreSQL" />
              <el-option value="mongodb" label="MongoDB" />
              <el-option value="redis" label="Redis" />
              <el-option value="sqlserver" label="SQL Server" />
              <el-option value="oracle" label="Oracle" />
              <el-option value="sqlite" label="SQLite" />
              <el-option value="other" label="其他" />
            </el-select>
          </el-form-item>
          <el-form-item label="主机地址">
            <el-input v-model="form.host" placeholder="IP 或域名" />
          </el-form-item>
          <el-form-item label="端口">
            <el-input-number v-model="form.port" :min="1" :max="65535" />
          </el-form-item>
          <el-form-item label="数据库名">
            <el-input v-model="form.db_name" placeholder="数据库名称" />
          </el-form-item>
        </template>
        <!-- API Key -->
        <template v-if="form.category === 'api_key'">
          <el-form-item label="服务商">
            <el-select v-model="form.api_provider" placeholder="选择或输入" filterable allow-create style="width: 100%">
              <el-option value="openai" label="OpenAI" />
              <el-option value="anthropic" label="Anthropic" />
              <el-option value="google" label="Google AI" />
              <el-option value="azure" label="Azure OpenAI" />
              <el-option value="deepseek" label="DeepSeek" />
              <el-option value="zhipu" label="智谱 AI" />
              <el-option value="baidu" label="百度千帆" />
              <el-option value="aliyun" label="阿里云" />
              <el-option value="other" label="其他" />
            </el-select>
          </el-form-item>
          <el-form-item label="接口地址">
            <el-input v-model="form.api_endpoint" placeholder="https://api.openai.com/v1" />
          </el-form-item>
        </template>
        <el-form-item label="备注">
          <el-input v-model="form.notes" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="归属">
          <el-radio-group v-model="form.is_personal" :disabled="!!editingId">
            <el-radio :value="false">团队密码</el-radio>
            <el-radio :value="true">个人密码</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="!form.is_personal" label="团队">
          <el-select v-model="form.team_id" placeholder="选择团队" :disabled="!!editingId">
            <el-option v-for="t in teams" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- Share / Grant Dialog -->
    <el-dialog v-model="shareVisible" :title="auth.isAdmin ? '授权管理' : '分享密码'" width="540px" destroy-on-close>
      <el-form inline style="margin-bottom: 12px">
        <el-form-item label="用户">
          <el-select v-model="shareUserId" filterable placeholder="选择用户" style="width: 160px">
            <el-option v-for="u in allUsers" :key="u.id" :label="u.username" :value="u.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="权限">
          <el-select v-model="sharePermission" style="width: 100px">
            <el-option value="view" label="只读" />
            <el-option value="edit" label="读写" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleShare">{{ auth.isAdmin ? '授权' : '分享' }}</el-button>
        </el-form-item>
      </el-form>
      <el-table :data="shares" size="small">
        <el-table-column prop="shared_with_username" label="用户" min-width="100" />
        <el-table-column label="权限" width="80">
          <template #default="{ row }">
            <el-tag :type="row.permission === 'edit' ? 'warning' : 'info'" size="small">
              {{ row.permission === 'edit' ? '读写' : '只读' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="shared_by_name" label="授权人" width="90" />
        <el-table-column label="操作" width="80">
          <template #default="{ row }">
            <el-button link type="danger" size="small" @click="handleRevokeShare(row)">撤销</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="shares.length === 0" description="暂无授权记录" :image-size="48" />
    </el-dialog>

    <!-- Security Confirm Dialog -->
    <el-dialog v-model="confirmDialogVisible" title="安全验证" width="400px" :close-on-click-modal="false">
      <div style="margin-bottom: 16px; color: #666">
        <el-icon style="color: #e6a23c; margin-right: 6px"><Lock /></el-icon>
        请输入您的登录密码以查看敏感信息
      </div>
      <el-input
        v-model="confirmPassword"
        type="password"
        show-password
        placeholder="请输入登录密码"
        size="large"
        @keyup.enter="handleConfirm"
      />
      <div v-if="confirmError" style="color: #f56c6c; font-size: 13px; margin-top: 8px">{{ confirmError }}</div>
      <template #footer>
        <el-button @click="cancelConfirm">取消</el-button>
        <el-button type="primary" :loading="confirmLoading" @click="handleConfirm">验证</el-button>
      </template>
    </el-dialog>

    <!-- Change Server Password Dialog -->
    <el-dialog v-model="changePwdVisible" title="远程修改服务器密码" width="620px" :close-on-click-modal="false" destroy-on-close>
      <div style="margin-bottom: 12px">
        <span style="color: #666">服务器: </span>
        <el-tag size="small">{{ changePwdRow?.title }}</el-tag>
        <span style="margin-left: 8px; color: #999">{{ changePwdRow?.host }}:{{ changePwdRow?.port || 22 }}</span>
      </div>
      <div style="margin-bottom: 12px; display: flex; align-items: center; gap: 8px">
        <span style="color: #666; white-space: nowrap">新密码:</span>
        <el-input v-model="changePwdNew" size="small" :placeholder="'留空则自动生成强密码'" style="flex: 1" :disabled="changePwdRunning" />
      </div>
      <div
        ref="changePwdTermRef"
        style="background: #1e1e1e; color: #d4d4d4; font-family: 'Cascadia Code', 'Consolas', monospace; font-size: 13px; padding: 12px; border-radius: 6px; height: 320px; overflow-y: auto; white-space: pre-wrap; line-height: 1.6"
      >{{ changePwdOutput || '点击「执行」开始修改密码...' }}</div>
      <div v-if="changePwdNewResult" style="margin-top: 12px; padding: 10px; background: #f0f9eb; border-radius: 6px; display: flex; align-items: center; gap: 8px">
        <el-tag type="success" effect="dark" size="small">新密码</el-tag>
        <code style="font-size: 14px; font-weight: 600">{{ changePwdNewResult }}</code>
        <el-button size="small" @click="copyText(changePwdNewResult)">复制</el-button>
      </div>
      <template #footer>
        <el-button @click="changePwdVisible = false" :disabled="changePwdRunning">关闭</el-button>
        <el-button type="primary" @click="execChangePwd" :loading="changePwdRunning" :disabled="changePwdDone">
          {{ changePwdRunning ? '执行中...' : '执行' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch, nextTick } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useDecryptStore } from '../stores/decrypt'
import { getPasswords, createPassword, updatePassword, deletePassword, decryptPassword, sharePassword, getShares, revokeShare, verifyServerPassword, grantAccess } from '../api/passwords'
import { createApproval, checkAccess } from '../api/approvals'
import { getTeams } from '../api/teams'
import { getAllUsers } from '../api/users'
import { ElMessage } from 'element-plus'

const auth = useAuthStore()
const decryptStore = useDecryptStore()

const CATEGORY_TAGS = {
  website: { label: '网站', type: '' },
  server: { label: '服务器', type: 'danger' },
  database: { label: '数据库', type: 'warning' },
  api_key: { label: 'API', type: 'primary' },
  other: { label: '其他', type: 'info' },
}

const categoryPlaceholders = {
  website: { title: '如: GitHub', username: '登录用户名' },
  server: { title: '如: 生产服务器-web01', username: 'root' },
  database: { title: '如: 生产数据库-主库', username: '数据库用户名' },
  api_key: { title: '如: OpenAI GPT-4', username: 'API Key 名称' },
  other: { title: '标题', username: '账号' },
}

const passwords = ref([])
const teams = ref([])
const allUsers = ref([])
const loading = ref(false)
const keyword = ref('')
const filterType = ref('')
const filterTeam = ref(null)
const filterCategory = ref('')
const filterExpire = ref('')
const revealedMap = ref({})

const canCreate = computed(() => auth.role === 'admin' || auth.role === 'product' || auth.role === 'developer')
const canShare = computed(() => auth.role === 'admin' || auth.role === 'product')

// Form
const dialogVisible = ref(false)
const editingId = ref(null)
const saving = ref(false)
const formRef = ref()
const form = reactive({
  title: '', category: 'website', username: '', password: '',
  url: '', host: '', port: 22, notes: '',
  db_type: '', db_name: '', api_provider: '', api_endpoint: '',
  is_personal: false, team_id: null, expire_days: 0, security_level: 'low',
})
const formRules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

// Share
const shareVisible = ref(false)
const sharePasswordId = ref(null)
const shareUserId = ref(null)
const sharePermission = ref('view')
const shares = ref([])

// Security confirm
const confirmDialogVisible = ref(false)
const confirmPassword = ref('')
const confirmLoading = ref(false)
const confirmError = ref('')
const pendingAction = ref(null)

// Countdown
const formattedTime = computed(() => {
  const s = decryptStore.remainingSeconds
  const min = Math.floor(s / 60)
  const sec = s % 60
  return `${min}:${sec.toString().padStart(2, '0')}`
})

const _expiryCheck = computed(() => decryptStore.isValid)
watch(_expiryCheck, (val) => {
  if (!val) revealedMap.value = {}
})

// --- Decrypt with auth ---

function getDecryptPayload() {
  if (decryptStore.isValid) return { decrypt_token: decryptStore.decryptToken }
  return null
}

function requestConfirm(type, row) {
  pendingAction.value = { type, row }
  confirmPassword.value = ''
  confirmError.value = ''
  confirmDialogVisible.value = true
}

function cancelConfirm() {
  confirmDialogVisible.value = false
  pendingAction.value = null
}

async function handleConfirm() {
  if (!confirmPassword.value) { confirmError.value = '请输入密码'; return }
  confirmLoading.value = true
  confirmError.value = ''
  try {
    const { data } = await decryptPassword(pendingAction.value.row.id, { password_confirm: confirmPassword.value })
    if (data.decrypt_token) decryptStore.setToken(data.decrypt_token)
    confirmDialogVisible.value = false
    executePendingAction(data)
  } catch (err) {
    if (err.response?.status === 403) confirmError.value = '密码错误，请重试'
  } finally {
    confirmLoading.value = false
  }
}

function executePendingAction(data) {
  if (!pendingAction.value) return
  const { type, row } = pendingAction.value
  if (type === 'reveal') {
    revealedMap.value = { ...revealedMap.value, [row.id]: data.password }
  } else if (type === 'copy') {
    navigator.clipboard.writeText(data.password)
    ElMessage.success('已复制到剪贴板')
  } else if (type === 'edit') {
    editingId.value = row.id
    Object.assign(form, {
      title: data.title, category: row.category || 'website',
      username: data.username, password: data.password,
      url: data.url, host: data.host || '', port: data.port || 22,
      db_type: data.db_type || '', db_name: data.db_name || '',
      api_provider: data.api_provider || '', api_endpoint: data.api_endpoint || '',
      notes: data.notes, is_personal: row.is_personal, team_id: row.team_id,
      expire_days: row.expire_days || 0, security_level: row.security_level || 'low',
    })
    dialogVisible.value = true
  }
  pendingAction.value = null
}

async function callDecryptWithToken(row) {
  const payload = getDecryptPayload()
  if (!payload) return null
  try {
    const { data } = await decryptPassword(row.id, payload)
    return data
  } catch (err) {
    if (err.response?.status === 401) { decryptStore.clearToken(); revealedMap.value = {} }
    return null
  }
}

// --- Main actions ---

async function loadList() {
  loading.value = true
  try {
    const params = {}
    if (keyword.value) params.keyword = keyword.value
    if (filterType.value === 'personal') params.is_personal = true
    if (filterType.value === 'team') params.is_personal = false
    if (filterTeam.value) params.team_id = filterTeam.value
    if (filterCategory.value) params.category = filterCategory.value
    if (filterExpire.value) params.expire_status = filterExpire.value
    const { data } = await getPasswords(params)
    passwords.value = data
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingId.value = null
  Object.assign(form, {
    title: '', category: 'website', username: '', password: '',
    url: '', host: '', port: 22, notes: '',
    is_personal: false, team_id: null, expire_days: 0,
  })
  dialogVisible.value = true
}

async function openEdit(row) {
  if (decryptStore.isValid) {
    const data = await callDecryptWithToken(row)
    if (data) {
      editingId.value = row.id
      Object.assign(form, {
        title: data.title, category: row.category || 'website',
        username: data.username, password: data.password,
        url: data.url, host: data.host || '', port: data.port || 22,
        notes: data.notes, is_personal: row.is_personal, team_id: row.team_id,
        expire_days: row.expire_days || 0, security_level: row.security_level || 'low',
      })
      dialogVisible.value = true
      return
    }
  }
  requestConfirm('edit', row)
}

async function handleSave() {
  await formRef.value.validate()
  saving.value = true
  try {
    const payload = {
      title: form.title, category: form.category,
      username: form.username, password: form.password,
      url: form.url, host: form.host, port: form.port,
      db_type: form.db_type, db_name: form.db_name,
      api_provider: form.api_provider, api_endpoint: form.api_endpoint,
      notes: form.notes, expire_days: form.expire_days,
    }
    if (editingId.value) {
      await updatePassword(editingId.value, payload)
    } else {
      await createPassword({ ...payload, is_personal: form.is_personal, team_id: form.team_id })
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    loadList()
  } finally {
    saving.value = false
  }
}

async function handleDelete(id) {
  await deletePassword(id)
  ElMessage.success('已删除')
  loadList()
}

async function requireApproval(row, type) {
  if (row.security_level === 'high' && type === 'view') {
    const { data } = await checkAccess(row.id)
    if (data.has_access) return true
    if (data.pending) { ElMessage.warning('审批申请已提交，等待Admin审批'); return false }
    try {
      await createApproval({ password_entry_id: row.id, request_type: 'view', reason: '申请查看高安全密码' })
      ElMessage.success('审批申请已提交，请等待Admin审批')
    } catch {}
    return false
  }
  if (row.security_level === 'medium' && type === 'share') {
    ElMessage.warning('中安全密码分享需要Admin审批，请到审批管理发起申请')
    return false
  }
  return true
}

async function toggleReveal(row) {
  if (revealedMap.value[row.id]) {
    delete revealedMap.value[row.id]
    revealedMap.value = { ...revealedMap.value }
    return
  }
  if (row.security_level === 'high') {
    const allowed = await requireApproval(row, 'view')
    if (!allowed) return
  }
  if (decryptStore.isValid) {
    const data = await callDecryptWithToken(row)
    if (data) { revealedMap.value = { ...revealedMap.value, [row.id]: data.password }; return }
  }
  requestConfirm('reveal', row)
}

async function copyPassword(row) {
  if (row.security_level === 'high') {
    const allowed = await requireApproval(row, 'view')
    if (!allowed) return
  }
  if (decryptStore.isValid) {
    const data = await callDecryptWithToken(row)
    if (data) { await navigator.clipboard.writeText(data.password); ElMessage.success('已复制到剪贴板'); return }
  }
  requestConfirm('copy', row)
}

// --- Server verify ---
const verifyingMap = ref({})

// --- Change server password ---
const changePwdVisible = ref(false)
const changePwdRow = ref(null)
const changePwdNew = ref('')
const changePwdOutput = ref('')
const changePwdRunning = ref(false)
const changePwdDone = ref(false)
const changePwdNewResult = ref('')
const changePwdTermRef = ref(null)

function openChangePwd(row) {
  changePwdRow.value = row
  changePwdNew.value = ''
  changePwdOutput.value = ''
  changePwdRunning.value = false
  changePwdDone.value = false
  changePwdNewResult.value = ''
  changePwdVisible.value = true
}

function execChangePwd() {
  changePwdRunning.value = true
  changePwdOutput.value = ''
  changePwdNewResult.value = ''

  const token = localStorage.getItem('token')
  const wsUrl = `${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/api/ws/change-password/${changePwdRow.value.id}?token=${token}`
  const ws = new WebSocket(wsUrl)

  ws.onopen = () => {
    ws.send(JSON.stringify({ action: 'start', new_password: changePwdNew.value || '' }))
  }

  ws.onmessage = (e) => {
    const msg = JSON.parse(e.data)
    if (msg.type === 'output') {
      changePwdOutput.value += msg.data
      // Auto scroll
      nextTick(() => {
        if (changePwdTermRef.value) changePwdTermRef.value.scrollTop = changePwdTermRef.value.scrollHeight
      })
    } else if (msg.type === 'new_password') {
      changePwdNewResult.value = msg.data
    } else if (msg.type === 'status') {
      changePwdRunning.value = false
      changePwdDone.value = true
      if (msg.data === 'success') {
        ElMessage.success('服务器密码修改成功')
        loadList()
      } else {
        ElMessage.error('密码修改失败，请查看输出日志')
      }
    } else if (msg.type === 'error') {
      changePwdOutput.value += `\r\n[错误] ${msg.data}\r\n`
      changePwdRunning.value = false
    }
  }

  ws.onerror = () => {
    changePwdOutput.value += '\r\n[错误] WebSocket 连接失败\r\n'
    changePwdRunning.value = false
  }

  ws.onclose = () => {
    changePwdRunning.value = false
  }
}

function copyText(text) {
  navigator.clipboard.writeText(text)
  ElMessage.success('已复制')
}

function formatShortTime(t) {
  if (!t) return ''
  return new Date(t).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

async function handleVerify(row) {
  verifyingMap.value = { ...verifyingMap.value, [row.id]: true }
  try {
    const { data } = await verifyServerPassword(row.id)
    if (data.status === 'valid') {
      ElMessage.success(`${row.title}: ${data.message}`)
    } else if (data.status === 'invalid') {
      ElMessage.error(`${row.title}: ${data.message}`)
    } else {
      ElMessage.warning(`${row.title}: ${data.message}`)
    }
    loadList()
  } catch {
    // error handled by interceptor
  } finally {
    verifyingMap.value = { ...verifyingMap.value, [row.id]: false }
  }
}

// --- Password generator ---
const genPopoverVisible = ref(false)
const genOptions = reactive({ length: 20, uppercase: true, lowercase: true, numbers: true, symbols: true })
const previewPassword = ref('')

function buildCharset() {
  let chars = ''
  if (genOptions.uppercase) chars += 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
  if (genOptions.lowercase) chars += 'abcdefghijklmnopqrstuvwxyz'
  if (genOptions.numbers) chars += '0123456789'
  if (genOptions.symbols) chars += '!@#$%^&*()_+-=[]{}|;:,.<>?'
  return chars || 'abcdefghijklmnopqrstuvwxyz0123456789'
}

function doGenerate() {
  const chars = buildCharset()
  const arr = new Uint32Array(genOptions.length)
  crypto.getRandomValues(arr)
  let pwd = ''
  for (let i = 0; i < genOptions.length; i++) pwd += chars[arr[i] % chars.length]
  // Ensure at least one char from each selected category
  const required = []
  if (genOptions.uppercase) required.push('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
  if (genOptions.lowercase) required.push('abcdefghijklmnopqrstuvwxyz')
  if (genOptions.numbers) required.push('0123456789')
  if (genOptions.symbols) required.push('!@#$%^&*()_+-=[]{}|;:,.<>?')
  const pwdArr = pwd.split('')
  const posArr = new Uint32Array(required.length)
  crypto.getRandomValues(posArr)
  for (let i = 0; i < required.length; i++) {
    const pos = posArr[i] % pwdArr.length
    const catArr = new Uint32Array(1)
    crypto.getRandomValues(catArr)
    pwdArr[pos] = required[i][catArr[0] % required[i].length]
  }
  return pwdArr.join('')
}

function refreshPreview() {
  previewPassword.value = doGenerate()
}

function applyGenerated() {
  if (!previewPassword.value) refreshPreview()
  form.password = previewPassword.value
  genPopoverVisible.value = false
}

const strengthPercent = computed(() => {
  const pwd = previewPassword.value
  if (!pwd) return 0
  let score = 0
  if (pwd.length >= 12) score += 25
  if (pwd.length >= 20) score += 15
  if (/[A-Z]/.test(pwd)) score += 15
  if (/[a-z]/.test(pwd)) score += 15
  if (/[0-9]/.test(pwd)) score += 15
  if (/[^A-Za-z0-9]/.test(pwd)) score += 15
  return Math.min(100, score)
})

const strengthColor = computed(() => {
  const p = strengthPercent.value
  if (p >= 80) return '#67c23a'
  if (p >= 50) return '#e6a23c'
  return '#f56c6c'
})

const strengthLabel = computed(() => {
  const p = strengthPercent.value
  if (p >= 80) return '强'
  if (p >= 50) return '中'
  return '弱'
})

// Auto-generate preview when popover options change
watch(() => [genOptions.length, genOptions.uppercase, genOptions.lowercase, genOptions.numbers, genOptions.symbols], () => {
  refreshPreview()
}, { immediate: true })

async function openShare(row) {
  sharePasswordId.value = row.id
  shareUserId.value = null
  shareVisible.value = true
  const { data } = await getShares(row.id)
  shares.value = data
}

async function handleShare() {
  if (!shareUserId.value) return
  const payload = { shared_with_user_id: shareUserId.value, permission: sharePermission.value }
  if (auth.isAdmin) {
    await grantAccess(sharePasswordId.value, payload)
  } else {
    await sharePassword(sharePasswordId.value, payload)
  }
  ElMessage.success('授权成功')
  const { data } = await getShares(sharePasswordId.value)
  shares.value = data
  shareUserId.value = null
  sharePermission.value = 'view'
}

async function handleRevokeShare(row) {
  await revokeShare(sharePasswordId.value, row.id)
  ElMessage.success('已撤销')
  const { data } = await getShares(sharePasswordId.value)
  shares.value = data
}

onMounted(async () => {
  await Promise.all([loadList(), getTeams().then(r => teams.value = r.data), getAllUsers().then(r => allUsers.value = r.data)])
})
</script>
