

<script setup>
import { ref } from 'vue'


const searchTitle = ref('')
const searchLocation = ref('')
const selectedLocations = ref([])
const jobs = ref([])
const loading = ref(false)
const error = ref('')

// Demo city and job title lists, can be replaced with API
const cityList = [
  'Milan', 'Turin', 'Rome', 'Naples', 'Florence', 'Venice', 'Bologna', 'Genoa', 'Palermo', 'Bari', 'Catania', 'Verona', 'Padua', 'Trieste', 'Brescia', 'Parma', 'Prato', 'Modena', 'Reggio Calabria', 'Reggio Emilia', 'Perugia', 'Livorno', 'Ravenna', 'Cagliari', 'Foggia', 'Rimini', 'Salerno', 'Ferrara', 'Sassari', 'Latina', 'Giugliano in Campania', 'Monza', 'Siracusa', 'Pescara', 'Bergamo', 'Forlì', 'Trento', 'Vicenza', 'Terni', 'Bolzano', 'Novara', 'Piacenza', 'Ancona', 'Andria', 'Udine', 'Arezzo', 'Cesena', 'Lecce', 'Barletta', 'Alessandria', 'La Spezia'
]
const jobTitleList = [
  'Frontend Developer', 'Backend Developer', 'Full Stack Developer', 'Data Scientist', 'Machine Learning Engineer', 'DevOps Engineer', 'QA Engineer', 'Product Manager', 'UI/UX Designer', 'Mobile Developer', 'Project Manager', 'Business Analyst', 'System Administrator', 'Cloud Engineer', 'Security Engineer', 'Database Administrator', 'Network Engineer', 'Scrum Master', 'Software Architect', 'Web Developer', 'React Developer', 'Vue Developer', 'Angular Developer', 'Python Developer', 'Java Developer', 'C# Developer', 'PHP Developer', 'Ruby Developer', 'Go Developer', 'iOS Developer', 'Android Developer', 'Flutter Developer', 'Node.js Developer', 'TypeScript Developer', 'Scala Developer', 'Rust Developer', 'Game Developer', 'Embedded Engineer', 'Support Engineer', 'Technical Writer', 'IT Consultant', 'AI Engineer', 'Research Scientist', 'Solutions Architect', 'Test Automation Engineer', 'Release Manager', 'Site Reliability Engineer', 'Hardware Engineer', 'SAP Consultant', 'ERP Specialist', 'Help Desk Specialist'
]
const citySuggestions = ref([])
const showCitySuggestions = ref(false)
const jobTitleSuggestions = ref([])
const showJobTitleSuggestions = ref(false)

function updateCitySuggestions() {
  const val = searchLocation.value.trim().toLowerCase()
  if (!val) {
    citySuggestions.value = []
    showCitySuggestions.value = false
    return
  }
  // Exclude already selected locations
  citySuggestions.value = cityList.filter(city => city.toLowerCase().startsWith(val) && !selectedLocations.value.includes(city)).slice(0, 6)
  showCitySuggestions.value = citySuggestions.value.length > 0
}

function selectCitySuggestion(city) {
  if (!selectedLocations.value.includes(city)) {
    selectedLocations.value.push(city)
  }
  searchLocation.value = ''
  showCitySuggestions.value = false
}

function removeLocation(city) {
  selectedLocations.value = selectedLocations.value.filter(l => l !== city)
}

function updateJobTitleSuggestions() {
  const val = searchTitle.value.trim().toLowerCase()
  if (!val) {
    jobTitleSuggestions.value = []
    showJobTitleSuggestions.value = false
    return
  }
  jobTitleSuggestions.value = jobTitleList.filter(title => title.toLowerCase().startsWith(val)).slice(0, 6)
  showJobTitleSuggestions.value = jobTitleSuggestions.value.length > 0
}

function selectJobTitleSuggestion(title) {
  searchTitle.value = title
  showJobTitleSuggestions.value = false
}

function searchJobs() {
  loading.value = true
  error.value = ''
  jobs.value = []
  
  // Get API URL from environment or use default for development
  const apiUrl = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'
  
  fetch(`${apiUrl}/run?query=${encodeURIComponent(searchTitle.value)}&location=${encodeURIComponent(searchLocation.value)}`)
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
      <div class="app-title">Find Your Dream Job</div>
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
          <label>Work Arrangement</label>
          <select>
            <option>All</option>
            <option>Remote</option>
            <option>In-person</option>
            <option>Hybrid</option>
          </select>
        </div>
        <div class="filter-group">
          <label>Job Type</label>
          <select>
            <option>All</option>
            <option>Full-time</option>
            <option>Part-time</option>
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
          <div class="search-row">
            <div style="position:relative; flex:1;">
              <input
                v-model="searchTitle"
                type="text"
                placeholder="Job title or keyword"
                @keyup.enter="searchJobs"
                @input="updateJobTitleSuggestions"
                @focus="updateJobTitleSuggestions"
                @blur="setTimeout(() => showJobTitleSuggestions = false, 120)"
                autocomplete="off"
                style="width:100%"
              />
              <ul v-if="showJobTitleSuggestions" class="city-suggestions">
                <li v-for="title in jobTitleSuggestions" :key="title" @mousedown.prevent="selectJobTitleSuggestion(title)">
                  {{ title }}
                </li>
              </ul>
            </div>
            <div style="position:relative; flex:1; margin-left:1rem;">
              <input
                v-model="searchLocation"
                type="text"
                placeholder="Add location"
                @keyup.enter="() => { if (citySuggestions.length > 0) selectCitySuggestion(citySuggestions[0]) }"
                @input="updateCitySuggestions"
                @focus="updateCitySuggestions"
                @blur="setTimeout(() => showCitySuggestions = false, 120)"
                autocomplete="off"
                style="width:100%"
              />
              <ul v-if="showCitySuggestions" class="city-suggestions">
                <li v-for="city in citySuggestions" :key="city" @mousedown.prevent="selectCitySuggestion(city)">
                  {{ city }}
                </li>
              </ul>
            </div>
            <button @click="searchJobs" :disabled="loading" style="margin-left:1rem;">Search</button>
          </div>
          <div class="selected-locations-row">
            <div class="selected-locations">
              <span v-for="city in selectedLocations" :key="city" class="location-tag">
                {{ city }}
                <button class="remove-tag" @click.prevent="removeLocation(city)">&times;</button>
              </span>
            </div>
          </div>
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
            <div class="job-card-desc">
              {{ job.description ? job.description.slice(0, 120) + (job.description.length > 120 ? '...' : '') : '' }}
            </div>
            <div class="job-card-actions">
              <a v-if="job.url" :href="job.url" target="_blank" rel="noopener">
                <button>Apply</button>
              </a>
              <button @click="saveJob(job)">Save</button>
            </div>
          </div>
        .job-card-desc {
          margin: 0.7rem 0 0.5rem 0;
          color: #444;
          font-size: 0.98em;
          min-height: 1.2em;
        }
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
# ...existing styles...
<style scoped>
.selected-locations {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin-bottom: 0.2rem;
}
.location-tag {
  background: #e6f4f1;
  color: #222;
  border-radius: 12px;
  padding: 0.2rem 0.7rem 0.2rem 0.7rem;
  font-size: 0.97em;
  display: flex;
  align-items: center;
}
.remove-tag {
  background: none;
  border: none;
  color: #888;
  font-size: 1.1em;
  margin-left: 0.3em;
  cursor: pointer;
  padding: 0;
}
.remove-tag:hover {
  color: #d00;
}
/* ...existing styles... */
#app {
  /* City autocomplete styles */
  .city-suggestions {
    position: absolute;
    left: 0;
    right: 0;
    top: 100%;
    z-index: 10;
    background: #fff;
    box-shadow: 0 4px 16px rgba(0,0,0,0.13);
    border-radius: 0 0 8px 8px;
    margin: 0;
    padding: 0.2rem 0;
    list-style: none;
    max-height: 180px;
    overflow-y: auto;
  }
  .city-suggestions li {
    padding: 0.5rem 1rem;
    cursor: pointer;
    transition: background 0.15s;
  }
  .city-suggestions li:hover {
    background: #f2f2f2;
  }
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
.app-title {
  font-size: 1.7rem;
  font-weight: 700;
  color: #35495e;
  letter-spacing: 0.5px;
  padding: 0.2rem 0.5rem;
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
  margin-bottom: 2rem;
}
.search-row {
  display: flex;
  gap: 1rem;
}
.search-row input {
  padding: 0.6rem;
  border-radius: 4px;
  border: 1px solid #ddd;
}
.search-row button {
  padding: 0.6rem 1.5rem;
  border-radius: 4px;
  border: none;
  background: #35495e;
  color: #fff;
  font-weight: 600;
  cursor: pointer;
  height: 42px;
  align-self: center;
}
.selected-locations-row {
  margin-top: 0.3rem;
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
