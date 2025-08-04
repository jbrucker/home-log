// Login View using bootstrap
<template>
  <div class="login-container">
    <div class="card">
      <h2 class="card-header">Login</h2>
      <div class="card-body">
        <form @submit.prevent="handleSubmit">
          <div class="mb-3">
            <label class="form-label">Username</label>
            <input 
              type="text" 
              class="form-control" 
              v-model="form.username" 
              required
            >
          </div>

          <div class="mb-3">
            <label class="form-label">Password</label>
            <input 
              type="password" 
              class="form-control" 
              v-model="form.password" 
              required
            >
          </div>

          <button 
            type="submit" 
            class="btn btn-primary w-100"
            :disabled="loading"
          >
            <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
            Sign In
          </button>

          <div v-if="error" class="alert alert-danger mt-3 mb-0">
            {{ error }}
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()

const form = ref({
  username: '',
  password: ''
})

const loading = ref(false)
const error = ref<string | null>(null)

const handleSubmit = async () => {
  loading.value = true
  error.value = null
  try {
    await authStore.login(form.value.username, form.value.password)
    router.push('/sources')
  } catch (err) {
    error.value = 'Login failed. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  max-width: 400px;
  margin: 2rem auto;
  padding: 0 1rem;
}
</style>