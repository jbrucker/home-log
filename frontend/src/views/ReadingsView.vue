<template>
  <div class="container mt-4">
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h1>Readings for {{ sourceName }}</h1>
      <router-link to="/sources" class="btn btn-outline-secondary">
        &larr; Back to Sources
      </router-link>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="text-center">
      <div class="spinner-border text-primary"></div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="alert alert-danger">
      {{ error }}
    </div>

    <!-- Data Table -->
    <div v-else class="table-responsive">
      <table class="table table-striped">
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>Value</th>
            <th>Unit</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="reading in readings" :key="reading.timestamp">
            <td>{{ formatDate(reading.timestamp) }}</td>
            <td>{{ reading.value }}</td>
            <td>{{ reading.unit }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/api'

interface Reading {
  timestamp: string
  value: number
  unit: string
}

const route = useRoute()
const sourceName = ref('')
const readings = ref<Reading[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

const formatDate = (timestamp: string) => {
  return new Date(timestamp).toLocaleString()
}

const fetchData = async () => {
  try {
    // Fetch source details
    const sourceResponse = await api.get(`/sources/${route.params.id}`)
    sourceName.value = sourceResponse.data.name

    // Fetch readings
    const readingsResponse = await api.get(`/sources/${route.params.id}/readings`)
    readings.value = readingsResponse.data
  } catch (err) {
    error.value = 'Failed to load readings'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
/* Optional: Consistent spacing with SourcesView */
.table {
  margin-top: 1rem;
}
</style>