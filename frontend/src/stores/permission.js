import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getMyPermissions } from '../api/permissions'

export const usePermissionStore = defineStore('permission', () => {
  const permissions = ref([])
  const loaded = ref(false)

  async function load() {
    try {
      const { data } = await getMyPermissions()
      permissions.value = data.permissions
      loaded.value = true
    } catch {
      permissions.value = []
    }
  }

  function has(key) {
    return permissions.value.includes(key)
  }

  function hasPage(page) {
    return permissions.value.includes(`page.${page}`)
  }

  function hasFunc(func) {
    return permissions.value.includes(`func.${func}`)
  }

  function clear() {
    permissions.value = []
    loaded.value = false
  }

  return { permissions, loaded, load, has, hasPage, hasFunc, clear }
})
