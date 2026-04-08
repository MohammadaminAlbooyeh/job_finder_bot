

<script setup>
import { ref } from 'vue'

const searchTitle = ref('')
const searchLocation = ref('')
const jobs = ref([])
const loading = ref(false)
const error = ref('')

function searchJobs() {
  loading.value = true
  error.value = ''
  jobs.value = []
  fetch(`http://127.0.0.1:8000/run?query=${encodeURIComponent(searchTitle.value)}&location=${encodeURIComponent(searchLocation.value)}`)
    .then(async (res) => {
      if (!res.ok) throw new Error('Failed to fetch jobs')
      return await res.json()
    })
    .then(data => {
      jobs.value = Array.isArray(data) ? data : []
    })
    .catch(e => {
      error.value = e.message || 'Error fetching jobs'
    })
    .finally(() => {
      loading.value = false
    })
}

function saveJob(job) {
  // Placeholder for save functionality
  alert('Job saved!')
}
</script>

<template>
  <div id="app">
    <!-- Header -->
    <header class="header">
      <img src="/logo.svg" alt="Logo" class="logo" />
      <div class="header-actions">
        <button class="login-btn">Login / Register</button>
        <button class="post-job-btn">Post Job</button>
      </div>
    </header>

    <!-- Main Content -->
    <div class="main-layout">
      <!-- Sidebar Filters -->
      <aside class="sidebar">
        <h3>Filters</h3>
        <div class="filter-group">
          <label>Job Type</label>
          <select>
            <option>All</option>
            <option>Full-time</option>
            <option>Part-time</option>
            <option>Remote</option>
            <option>Internship</option>
          </select>
        </div>
        <div class="filter-group">
          <label>Experience Level</label>
          <select>
            <option>All</option>
            <option>Junior</option>
            <option>Mid</option>
            <option>Senior</option>
          </select>
        </div>
        <div class="filter-group">
          <label>Salary Range</label>
          <input type="text" placeholder="e.g. 1000-2000" />
        </div>
        <div class="filter-group">
          <label>Date Posted</label>
          <select>
            <option>Anytime</option>
            <option>Last 24 hours</option>
            <option>Last 7 days</option>
            <option>Last 30 days</option>
          </select>
        </div>
      </aside>

      <!-- Main Section -->
      <main class="content">
        <!-- Search Box -->

        <section class="search-box">
          <input
            v-model="searchTitle"
            type="text"
            placeholder="Job title or keyword"
            @keyup.enter="searchJobs"
          />
          <input
            v-model="searchLocation"
            type="text"
            placeholder="Location"
            @keyup.enter="searchJobs"
          />
          <button @click="searchJobs" :disabled="loading">Search</button>
        </section>

        <!-- Job List -->

        <section class="job-list">
          <h2>Job Results</h2>
          <div v-if="loading">Loading...</div>
          <div v-if="error" class="error">{{ error }}</div>
          <div v-if="jobs.length === 0 && !loading && !error" class="no-results">No jobs found.</div>
          <div v-for="job in jobs" :key="job.url || job.id || job.title + job.company" class="job-card">
            <div class="job-card-header">
              <span class="job-title">{{ job.title }}</span>
              <span class="company">{{ job.company }}</span>
            </div>
            <div class="job-card-meta">
              <span class="location">{{ job.location }}</span>
              <span v-if="job.salary" class="salary">{{ job.salary }}</span>
            </div>
            <div class="job-card-actions">
              <a v-if="job.url" :href="job.url" target="_blank"><button>Apply</button></a>
              <button @click="saveJob(job)">Save</button>
            </div>
          </div>
        </section>

        <section class="job-details">
          <h2>Job Details</h2>
          <!-- Job details will appear here -->
        </section>

        <!-- User Dashboard Placeholder -->
        <section class="dashboard">
          <h2>User Dashboard</h2>
          <ul>
            <li>Saved jobs</li>
            <li>Applied jobs</li>
            <li>Profile</li>
          </ul>
        </section>
      </main>
    </div>
  </div>
</template>
<style scoped>
#app {
  font-family: 'Segoe UI', Arial, sans-serif;
  background: #f8f9fa;
  min-height: 100vh;
}
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 2rem;
  background: #fff;
  border-bottom: 1px solid #eee;
}
.logo {
  width: 48px;
  height: 48px;
}
.header-actions button {
  margin-left: 1rem;
  padding: 0.5rem 1.2rem;
  border: none;
  border-radius: 4px;
  background: #42b883;
  color: #fff;
  font-weight: 600;
  cursor: pointer;
}
.main-layout {
  display: flex;
  max-width: 1200px;
  margin: 2rem auto;
  gap: 2rem;
}
.sidebar {
  width: 220px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.03);
  padding: 1.5rem 1rem;
  height: fit-content;
}
.filter-group {
  margin-bottom: 1.2rem;
}
.filter-group label {
  display: block;
  margin-bottom: 0.3rem;
  font-weight: 500;
}
.filter-group select, .filter-group input {
  width: 100%;
  padding: 0.4rem;
  border-radius: 4px;
  border: 1px solid #ddd;
}
.content {
  flex: 1;
}
.search-box {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
}
.search-box input {
  flex: 1;
  padding: 0.6rem;
  border-radius: 4px;
  border: 1px solid #ddd;
}
.search-box button {
  padding: 0.6rem 1.5rem;
  border-radius: 4px;
  border: none;
  background: #35495e;
  color: #fff;
  font-weight: 600;
  cursor: pointer;
}
.job-list {
  margin-bottom: 2rem;
}
.job-card {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  padding: 1.2rem;
  margin-bottom: 1.2rem;
}
.job-card-header {
  display: flex;
  justify-content: space-between;
  font-size: 1.1rem;
  font-weight: 600;
}
.job-card-meta {
  display: flex;
  gap: 2rem;
  margin: 0.5rem 0 1rem 0;
  color: #666;
}
.job-card-actions button {
  margin-right: 0.7rem;
  padding: 0.4rem 1.1rem;
  border: none;
  border-radius: 4px;
  background: #42b883;
  color: #fff;
  font-weight: 500;
  cursor: pointer;
}
.job-details, .dashboard {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  padding: 1.2rem;
  margin-bottom: 1.2rem;
}
.dashboard ul {
  list-style: disc;
  margin-left: 1.5rem;
}
</style>
