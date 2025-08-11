<template>
  <div class="container mt-4">
    <h1 class="mb-4">Data Sources</h1>
     <!-- Loading State -->
    <div v-if="loading" class="text-center">
      <div class="spinner-border text-primary"></div>
    </div>
    <!-- Error State -->
    <div v-else-if="error" class="alert alert-danger">
      {{ error }}
    </div>
    <!-- Success State -->
    <div v-else>
      <div class="list-group">
        <router-link
          v-for="source in sources"
          :key="source.id"
          :to="`/sources/${source.id}/readings`"
          class="list-group-item list-group-item-action d-flex justify-content-between align-items-center"
        >
          <div>
            <h5 class="mb-1">{{ source.name }}</h5>
            <small class="text-muted">{{ source.type }}</small>
          </div>
          <span class="badge bg-primary rounded-pill">
            {{ source.reading_count }} readings
          </span>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '@/api'

interface Source {
  id: string
  name: string
  type: string
  reading_count: number
}

const sources = ref<Source[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

const fetchSources = async () => {
  console.log("token:", localStorage.getItem('token'))  // to verify token exists
  try {
    const response = await api.get('/sources')
    sources.value = response.data
  } catch (err) {
    error.value = 'Failed to load data sources'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  console.log("SourcesView mounted")
  fetchSources()
})
</script>

<style scoped>
/* Optional: Add custom spacing as needed */
.list-group-item {
  margin-bottom: 0.5rem;
}
</style>