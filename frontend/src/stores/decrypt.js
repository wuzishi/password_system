import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const DURATION_MS = 5 * 60 * 1000

export const useDecryptStore = defineStore('decrypt', () => {
  const decryptToken = ref(null)
  const expiresAt = ref(null)
  const now = ref(Date.now())
  let _timerId = null
  let _tickId = null

  const isValid = computed(() => {
    return !!decryptToken.value && now.value < (expiresAt.value || 0)
  })

  const remainingSeconds = computed(() => {
    if (!expiresAt.value) return 0
    return Math.max(0, Math.ceil((expiresAt.value - now.value) / 1000))
  })

  function _startTick() {
    _stopTick()
    _tickId = setInterval(() => {
      now.value = Date.now()
      if (now.value >= (expiresAt.value || 0) && decryptToken.value) {
        clearToken()
      }
    }, 1000)
  }

  function _stopTick() {
    if (_tickId) {
      clearInterval(_tickId)
      _tickId = null
    }
  }

  function setToken(token) {
    decryptToken.value = token
    expiresAt.value = Date.now() + DURATION_MS
    now.value = Date.now()
    if (_timerId) clearTimeout(_timerId)
    _timerId = setTimeout(() => clearToken(), DURATION_MS)
    _startTick()
  }

  function clearToken() {
    decryptToken.value = null
    expiresAt.value = null
    _stopTick()
    if (_timerId) {
      clearTimeout(_timerId)
      _timerId = null
    }
  }

  return { decryptToken, expiresAt, isValid, remainingSeconds, setToken, clearToken }
})
