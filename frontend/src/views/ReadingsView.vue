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
            <th v-for="(unit, metric) in metrics" :key="metric">
              {{ metric }} <small class="text-muted">({{ unit }})</small>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="reading in readings" :key="reading.id">
            <td>{{ formatDate(reading.timestamp) }}</td>
            <td v-for="(unit, metric) in metrics" :key="metric">
              {{ reading.values[metric] ?? '-' }}
            </td>
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
  id: number
  values: Record<string, number>
  timestamp: string
}

interface SourceDetails {
  id: string
  name: string
  metrics: Record<string, string>  // { "metric1": "unit1", "metric2": "unit2" }
}

const route = useRoute()
const sourceName = ref('')
const metrics = ref<Record<string, string>>({})
const readings = ref<Reading[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

const formatDate = (timestamp: string) => {
  return new Date(timestamp).toLocaleString()
}

const fetchData = async () => {
  try {
    // Fetch source details to get metrics dictionary
    const sourceResponse = await api.get<SourceDetails>(`/api/sources/${route.params.id}`)
    sourceName.value = sourceResponse.data.name
    metrics.value = sourceResponse.data.metrics

    // Fetch readings
    const readingsResponse = await api.get<Reading[]>(`/api/sources/${route.params.id}/readings`)
    readings.value = readingsResponse.data
  } catch (err) {
    error.value = 'Failed to load readings'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  console.log("ReadingsView mounted")
  fetchData()
})
</script>

<style scoped>
.table th small {
  font-weight: normal;
}
</style>