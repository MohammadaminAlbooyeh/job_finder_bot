

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'

const searchTitle = ref('')
const searchLocation = ref('')
const selectedLocations = ref([])
const jobTypeOptions = [
  { value: 'remote', label: 'Remote' },
  { value: 'onsite', label: 'On-site' },
  { value: 'hybrid', label: 'Hybrid' },
]
const selectedJobTypes = ref([])
const experienceLevelOptions = [
  { value: 'entry', label: 'Entry' },
  { value: 'associate', label: 'Associate' },
  { value: 'mid-senior', label: 'Mid-Senior' },
  { value: 'director', label: 'Director' },
]
const selectedExperienceLevels = ref([])
const applyTypeOptions = [
  { value: 'easy', label: 'Easy Apply' },
  { value: 'regular', label: 'Regular Apply' },
]
const selectedApplyTypes = ref([])
const datePosted = ref('')
const includeKeywords = ref('')
const excludeKeywords = ref('')
const sortBy = ref('relevance')
const numPages = ref(1)
const selectedTitles = ref([])
const recentSearches = ref([])

const jobs = ref([])
const loading = ref(false)
const loadingMore = ref(false)
const error = ref('')
const notice = ref('')

const cvFile = ref(null)
const cvUploading = ref(false)
const cvAnalysis = ref(null)
const cvError = ref('')

const activeTab = ref('results') // results | saved | history
const savedJobs = ref([])
const toasts = ref([])
let toastId = 0

const theme = ref('light')

const scanStatus = ref(null)
const runningNow = ref(false)
const historyList = ref([])
const historyLoading = ref(false)

const selectedJob = ref(null)

// Demo country/city and job title lists, can be replaced with API
const countryList = [
  'Italy', 'Remote', 'United States', 'United Kingdom', 'Germany', 'France', 'Spain', 'Netherlands', 'Switzerland', 'Portugal', 'Ireland', 'Sweden', 'Canada', 'United Arab Emirates', 'India', 'Poland', 'Austria', 'Belgium', 'Turkey', 'Greece'
]
const cityList = [
  'Milan', 'Turin', 'Rome', 'Naples', 'Florence', 'Venice', 'Bologna', 'Genoa', 'Palermo', 'Bari', 'Catania', 'Verona', 'Padua', 'Trieste', 'Brescia', 'Parma', 'Prato', 'Modena', 'Reggio Calabria', 'Reggio Emilia', 'Perugia', 'Livorno', 'Ravenna', 'Cagliari', 'Foggia', 'Rimini', 'Salerno', 'Ferrara', 'Sassari', 'Latina', 'Giugliano in Campania', 'Monza', 'Siracusa', 'Pescara', 'Bergamo', 'Forlì', 'Trento', 'Vicenza', 'Terni', 'Bolzano', 'Novara', 'Piacenza', 'Ancona', 'Andria', 'Udine', 'Arezzo', 'Cesena', 'Lecce', 'Barletta', 'Alessandria', 'La Spezia'
]
const locationList = [...countryList, ...cityList]
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
  citySuggestions.value = locationList.filter(loc => loc.toLowerCase().startsWith(val) && !selectedLocations.value.includes(loc)).slice(0, 6)
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
  if (!selectedTitles.value.includes(title)) {
    selectedTitles.value.push(title)
  }
  searchTitle.value = ''
  showJobTitleSuggestions.value = false
}

function removeTitle(title) {
  selectedTitles.value = selectedTitles.value.filter(t => t !== title)
}

function onTitleEnter() {
  if (jobTitleSuggestions.value.length > 0) {
    selectJobTitleSuggestion(jobTitleSuggestions.value[0])
  } else {
    searchJobs()
  }
}

function toggleExperienceLevel(value) {
  if (selectedExperienceLevels.value.includes(value)) {
    selectedExperienceLevels.value = selectedExperienceLevels.value.filter(v => v !== value)
  } else {
    selectedExperienceLevels.value = [...selectedExperienceLevels.value, value]
  }
}

function toggleApplyType(value) {
  if (selectedApplyTypes.value.includes(value)) {
    selectedApplyTypes.value = selectedApplyTypes.value.filter(v => v !== value)
  } else {
    selectedApplyTypes.value = [...selectedApplyTypes.value, value]
  }
}

function getApiBaseUrl() {
  const raw = (import.meta.env.VITE_API_URL || '').trim()
  const productionFallback = 'https://job-finder-bot-xhst.onrender.com'

  if (raw) {
    return raw.replace(/\/$/, '')
  }

  if (import.meta.env.DEV) {
    return 'http://127.0.0.1:8000'
  }

  return productionFallback
}

function jobKey(job) {
  return (job?.url || `${job?.title || ''}|${job?.company || ''}|${job?.location || ''}`).trim()
}

function toggleJobType(value) {
  if (selectedJobTypes.value.includes(value)) {
    selectedJobTypes.value = selectedJobTypes.value.filter(v => v !== value)
  } else {
    selectedJobTypes.value = [...selectedJobTypes.value, value]
  }
}

function buildQueryParams(pages, jobTypeValue, experienceValue) {
  const parts = []
  if (jobTypeValue) parts.push(`job_type=${encodeURIComponent(jobTypeValue)}`)
  if (experienceValue) parts.push(`experience_level=${encodeURIComponent(experienceValue)}`)
  if (datePosted.value) parts.push(`date_posted=${encodeURIComponent(datePosted.value)}`)
  if (includeKeywords.value.trim()) parts.push(`include_keywords=${encodeURIComponent(includeKeywords.value.trim())}`)
  if (excludeKeywords.value.trim()) parts.push(`exclude_keywords=${encodeURIComponent(excludeKeywords.value.trim())}`)
  if (pages && pages > 1) parts.push(`num_pages=${pages}`)
  return parts.length ? `&${parts.join('&')}` : ''
}

function currentQueries() {
  return selectedTitles.value.length > 0
    ? [...selectedTitles.value]
    : [searchTitle.value.trim() || 'python developer']
}

function currentLocations() {
  return selectedLocations.value.length > 0
    ? [...selectedLocations.value]
    : [searchLocation.value.trim() || 'remote']
}

async function fetchJobsForLocations(apiUrl, queries, locations, pages) {
  // Fan out over every query x location x job-type x experience-level combination (OR'd together).
  const jobTypesToQuery = selectedJobTypes.value.length > 0 ? selectedJobTypes.value : ['']
  const experienceToQuery = selectedExperienceLevels.value.length > 0 ? selectedExperienceLevels.value : ['']
  const combos = []
  for (const q of queries) {
    for (const loc of locations) {
      for (const jt of jobTypesToQuery) {
        for (const exp of experienceToQuery) {
          combos.push({ q, loc, jt, exp })
        }
      }
    }
  }

  const responses = await Promise.all(
    combos.map(async ({ q, loc, jt, exp }) => {
      const extraParams = buildQueryParams(pages, jt, exp)
      const res = await fetch(
        `${apiUrl}/run?query=${encodeURIComponent(q)}&location=${encodeURIComponent(loc)}${extraParams}`
      )
      if (!res.ok) {
        throw new Error(`API error for ${loc}: ${res.status} ${res.statusText}`)
      }
      const data = await res.json()
      return Array.isArray(data) ? data : (Array.isArray(data.jobs) ? data.jobs : [])
    })
  )
  return responses.flat()
}

function dedupeJobs(list) {
  const deduped = []
  const seen = new Set()
  for (const job of list) {
    const key = jobKey(job)
    if (!key || seen.has(key)) continue
    seen.add(key)
    deduped.push(job)
  }
  return deduped
}

function recordRecentSearch(query, location) {
  const label = `${query} · ${location}`
  recentSearches.value = [label, ...recentSearches.value.filter(s => s !== label)].slice(0, 6)
  try {
    localStorage.setItem('jobfinder_recent_searches', JSON.stringify(recentSearches.value))
  } catch {
    // storage unavailable — ignore
  }
}

function applyRecentSearch(label) {
  const [query, location] = label.split(' · ')
  selectedTitles.value = []
  searchTitle.value = query || ''
  selectedLocations.value = []
  searchLocation.value = location || ''
  searchJobs()
}

function maybeNotifyNewJobs(newCount, query) {
  if (!newCount || typeof Notification === 'undefined') return
  if (Notification.permission === 'granted') {
    new Notification('Job Finder', { body: `${newCount} new "${query}" job(s) found` })
  } else if (Notification.permission !== 'denied') {
    Notification.requestPermission().then(perm => {
      if (perm === 'granted') {
        new Notification('Job Finder', { body: `${newCount} new "${query}" job(s) found` })
      }
    })
  }
}

async function exportResultsToBackend(list) {
  try {
    await fetch(`${getApiBaseUrl()}/export`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(list),
    })
  } catch {
    // download files just won't reflect this merge — non-fatal
  }
}

async function searchJobs() {
  loading.value = true
  error.value = ''
  notice.value = ''
  jobs.value = []
  numPages.value = 1
  activeTab.value = 'results'

  try {
    const apiUrl = getApiBaseUrl()
    const queries = currentQueries()
    const locations = currentLocations()

    let merged = await fetchJobsForLocations(apiUrl, queries, locations, numPages.value)
    let deduped = dedupeJobs(merged)

    if (deduped.length === 0 && !locations.some((loc) => loc.toLowerCase() === 'remote')) {
      const fallbackJobs = await fetchJobsForLocations(apiUrl, queries, ['remote'], numPages.value)
      deduped = dedupeJobs(fallbackJobs)
      if (deduped.length > 0) {
        notice.value = 'No exact matches for selected locations. Showing remote results.'
      }
    }

    jobs.value = deduped
    recordRecentSearch(queries[0], locations[0])
    const newCount = deduped.filter(j => j.is_new).length
    maybeNotifyNewJobs(newCount, queries[0])
    fetchStatus()
    exportResultsToBackend(sortedJobs.value)
  } catch (e) {
    const rawMessage = e?.message || 'Error fetching jobs'
    const normalizedMessage = rawMessage.toLowerCase()
    if (normalizedMessage.includes('failed to fetch')) {
      error.value = 'Cannot reach backend API. Check VITE_API_URL in Vercel and ensure Render backend is HTTPS and healthy.'
    } else {
      error.value = rawMessage
    }
  } finally {
    loading.value = false
  }
}

async function loadMore() {
  loadingMore.value = true
  try {
    const apiUrl = getApiBaseUrl()
    const queries = currentQueries()
    const locations = currentLocations()

    numPages.value += 1
    const merged = await fetchJobsForLocations(apiUrl, queries, locations, numPages.value)
    const combined = dedupeJobs([...jobs.value, ...merged])
    jobs.value = combined
    exportResultsToBackend(sortedJobs.value)
    showToast(`Loaded page ${numPages.value}`, 'success')
  } catch (e) {
    showToast(e?.message || 'Could not load more jobs', 'error')
  } finally {
    loadingMore.value = false
  }
}

function clearFilters() {
  selectedJobTypes.value = []
  selectedExperienceLevels.value = []
  selectedApplyTypes.value = []
  datePosted.value = ''
  includeKeywords.value = ''
  excludeKeywords.value = ''
  selectedLocations.value = []
  searchLocation.value = ''
  selectedTitles.value = []
  showToast('Filters cleared', 'success')
}

const sortedJobs = computed(() => {
  let list = [...jobs.value]

  if (selectedApplyTypes.value.length > 0) {
    const wantEasy = selectedApplyTypes.value.includes('easy')
    const wantRegular = selectedApplyTypes.value.includes('regular')
    list = list.filter(j => (j.easy_apply ? wantEasy : wantRegular))
  }

  if (sortBy.value === 'title') {
    return list.sort((a, b) => (a.title || '').localeCompare(b.title || ''))
  }
  if (sortBy.value === 'newest') {
    return list.sort((a, b) => (b.is_new === a.is_new) ? 0 : (b.is_new ? 1 : -1))
  }
  return list
})

// Keep the downloadable CSV/HTML in sync whenever the apply-type filter changes results.
watch(selectedApplyTypes, () => {
  if (jobs.value.length > 0) exportResultsToBackend(sortedJobs.value)
})

function onCvFileSelected(event) {
  cvFile.value = event.target.files?.[0] || null
  cvAnalysis.value = null
  cvError.value = ''
}

async function uploadCv() {
  if (!cvFile.value) {
    cvError.value = 'Please choose a CV file first (.pdf, .docx or .txt).'
    return
  }
  cvUploading.value = true
  cvError.value = ''
  cvAnalysis.value = null

  try {
    const apiUrl = getApiBaseUrl()
    const formData = new FormData()
    formData.append('file', cvFile.value)

    const res = await fetch(`${apiUrl}/parse-cv`, { method: 'POST', body: formData })
    const data = await res.json()

    if (!res.ok) {
      throw new Error(data?.error || `API error: ${res.status}`)
    }

    cvAnalysis.value = data
    searchTitle.value = data.suggested_query
    notice.value = `CV analyzed — detected role "${data.suggested_query}". Now choose a location and job type on the left, then click Search.`
  } catch (e) {
    cvError.value = e?.message || 'Could not analyze the CV.'
  } finally {
    cvUploading.value = false
  }
}

// --- Toasts ---
function showToast(message, kind = 'success') {
  const id = ++toastId
  toasts.value.push({ id, message, kind })
  setTimeout(() => {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }, 3000)
}

// --- Saved jobs (localStorage) ---
function loadSavedJobs() {
  try {
    const raw = localStorage.getItem('jobfinder_saved_jobs')
    savedJobs.value = raw ? JSON.parse(raw) : []
  } catch {
    savedJobs.value = []
  }
}

function persistSavedJobs() {
  try {
    localStorage.setItem('jobfinder_saved_jobs', JSON.stringify(savedJobs.value))
  } catch {
    // storage unavailable (private mode, etc.) — ignore
  }
}

function isSaved(job) {
  const key = jobKey(job)
  return savedJobs.value.some(j => jobKey(j) === key)
}

function saveJob(job) {
  const key = jobKey(job)
  if (isSaved(job)) {
    savedJobs.value = savedJobs.value.filter(j => jobKey(j) !== key)
    showToast('Removed from saved jobs', 'success')
  } else {
    savedJobs.value = [...savedJobs.value, job]
    showToast('Job saved', 'success')
  }
  persistSavedJobs()
}

function copyLink(job) {
  if (!job.url) return
  navigator.clipboard?.writeText(job.url)
    .then(() => showToast('Link copied to clipboard', 'success'))
    .catch(() => showToast('Could not copy link', 'error'))
}

function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}

function highlightSummary(text) {
  if (!text) return ''
  const escaped = escapeHtml(text)
  const keywords = includeKeywords.value.split(',').map(k => k.trim()).filter(Boolean)
  if (keywords.length === 0) return escaped
  const pattern = new RegExp(`(${keywords.map(k => k.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})`, 'ig')
  return escaped.replace(pattern, '<mark>$1</mark>')
}

function openJobDetails(job) {
  selectedJob.value = job
}

function closeJobDetails() {
  selectedJob.value = null
}

function exportSavedCsv() {
  if (savedJobs.value.length === 0) {
    showToast('No saved jobs to export', 'error')
    return
  }
  const columns = ['title', 'company', 'location', 'job_type', 'posted_date', 'url']
  const rows = [columns.join(',')]
  for (const job of savedJobs.value) {
    rows.push(columns.map(col => `"${String(job[col] || '').replace(/"/g, '""')}"`).join(','))
  }
  const blob = new Blob([rows.join('\n')], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'saved_jobs.csv'
  link.click()
  URL.revokeObjectURL(url)
}

// --- Theme ---
function applyTheme() {
  document.documentElement.setAttribute('data-theme', theme.value)
}

function toggleTheme() {
  theme.value = theme.value === 'dark' ? 'light' : 'dark'
  localStorage.setItem('jobfinder_theme', theme.value)
  applyTheme()
}

// --- Auto-scan status & history ---
async function fetchStatus() {
  try {
    const res = await fetch(`${getApiBaseUrl()}/status`)
    if (res.ok) scanStatus.value = await res.json()
  } catch {
    // backend unreachable — leave previous status as-is
  }
}

async function fetchHistory() {
  historyLoading.value = true
  try {
    const res = await fetch(`${getApiBaseUrl()}/history`)
    if (res.ok) historyList.value = await res.json()
  } catch {
    showToast('Could not load scan history', 'error')
  } finally {
    historyLoading.value = false
  }
}

async function runNow() {
  runningNow.value = true
  try {
    const res = await fetch(`${getApiBaseUrl()}/run-now`, { method: 'POST' })
    if (!res.ok) throw new Error(`API error: ${res.status}`)
    const data = await res.json()
    jobs.value = dedupeJobs(Array.isArray(data) ? data : [])
    activeTab.value = 'results'
    showToast('Scan triggered — results updated', 'success')
    fetchStatus()
  } catch (e) {
    showToast(e?.message || 'Could not trigger scan', 'error')
  } finally {
    runningNow.value = false
  }
}

function selectTab(tab) {
  activeTab.value = tab
  if (tab === 'history') fetchHistory()
}

function formatTime(iso) {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
}

let statusTimer = null

onMounted(() => {
  loadSavedJobs()
  const storedTheme = localStorage.getItem('jobfinder_theme')
  if (storedTheme) theme.value = storedTheme
  applyTheme()
  try {
    const raw = localStorage.getItem('jobfinder_recent_searches')
    recentSearches.value = raw ? JSON.parse(raw) : []
  } catch {
    recentSearches.value = []
  }
  fetchStatus()
  statusTimer = setInterval(fetchStatus, 60000)
})

onUnmounted(() => {
  if (statusTimer) clearInterval(statusTimer)
})
</script>

<template>
  <div id="app">
    <!-- Toasts -->
    <div class="toast-stack">
      <div v-for="toast in toasts" :key="toast.id" class="toast" :class="`toast-${toast.kind}`">
        {{ toast.message }}
      </div>
    </div>

    <!-- Header -->
    <header class="header">
      <div class="header-inner">
        <div class="brand">
          <span class="brand-mark">JF</span>
          <div class="brand-text">
            <span class="app-title">Job Finder</span>
            <span class="app-subtitle">LinkedIn search, automated</span>
          </div>
        </div>
        <div class="header-actions">
          <div class="scan-badge" :title="scanStatus?.next_run_at ? `Next scan: ${formatTime(scanStatus.next_run_at)}` : ''">
            <span class="dot"></span>
            <span>{{ scanStatus?.interval_hours ? `Auto-scan every ${scanStatus.interval_hours}h` : 'Auto-scan' }}</span>
          </div>
          <button class="btn-secondary btn-sm" @click="runNow" :disabled="runningNow">
            <span v-if="runningNow" class="spinner spinner-dark"></span>
            {{ runningNow ? 'Running…' : 'Run Now' }}
          </button>
          <button class="icon-btn" @click="toggleTheme" :title="theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'">
            {{ theme === 'dark' ? '☀️' : '🌙' }}
          </button>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <div class="main-layout">
      <!-- Sidebar Filters -->
      <aside class="sidebar">
        <h3>Filters</h3>
        <div class="filter-group">
          <label>Job Type</label>
          <div class="checkbox-group">
            <label v-for="opt in jobTypeOptions" :key="opt.value" class="checkbox-option">
              <input
                type="checkbox"
                :checked="selectedJobTypes.includes(opt.value)"
                @change="toggleJobType(opt.value)"
              />
              {{ opt.label }}
            </label>
          </div>
        </div>
        <div class="filter-group">
          <label>Experience Level</label>
          <div class="checkbox-group">
            <label v-for="opt in experienceLevelOptions" :key="opt.value" class="checkbox-option">
              <input
                type="checkbox"
                :checked="selectedExperienceLevels.includes(opt.value)"
                @change="toggleExperienceLevel(opt.value)"
              />
              {{ opt.label }}
            </label>
          </div>
        </div>
        <div class="filter-group">
          <label>Apply Type</label>
          <div class="checkbox-group">
            <label v-for="opt in applyTypeOptions" :key="opt.value" class="checkbox-option">
              <input
                type="checkbox"
                :checked="selectedApplyTypes.includes(opt.value)"
                @change="toggleApplyType(opt.value)"
              />
              {{ opt.label }}
            </label>
          </div>
        </div>
        <div class="filter-group">
          <label>Date Posted</label>
          <select v-model="datePosted">
            <option value="">Anytime</option>
            <option value="24h">Last 24 hours</option>
            <option value="3d">Last 3 days</option>
            <option value="week">Last 7 days</option>
          </select>
        </div>
        <div class="filter-group">
          <label>Include keywords</label>
          <input v-model="includeKeywords" type="text" placeholder="e.g. django, api" />
        </div>
        <div class="filter-group">
          <label>Exclude keywords</label>
          <input v-model="excludeKeywords" type="text" placeholder="e.g. senior, lead" />
        </div>
        <button class="btn-secondary" style="width:100%; margin-bottom: 0.8rem;" @click="clearFilters">
          Clear filters
        </button>
        <a class="download-link" :href="`${getApiBaseUrl()}/download/csv`" target="_blank" rel="noopener">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3v12m0 0l-4-4m4 4l4-4M4 19h16"/></svg>
          Download CSV
        </a>
        <a class="download-link" style="margin-top: 0.6rem;" :href="`${getApiBaseUrl()}/download/html`" target="_blank" rel="noopener">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3v12m0 0l-4-4m4 4l4-4M4 19h16"/></svg>
          Download HTML (clickable links)
        </a>
      </aside>

      <!-- Main Section -->
      <main class="content">
        <!-- CV Upload -->
        <section class="cv-box">
          <div class="cv-box-header">
            <h3>Find jobs from your CV</h3>
            <p class="cv-box-subtitle">Upload a CV and we'll suggest a role, skills and a matching search.</p>
          </div>
          <div class="cv-row">
            <label class="file-input">
              <input type="file" accept=".pdf,.docx,.txt" @change="onCvFileSelected" />
              <span>{{ cvFile ? cvFile.name : 'Choose file (.pdf, .docx, .txt)' }}</span>
            </label>
            <button class="btn-primary" @click="uploadCv" :disabled="cvUploading">
              <span v-if="cvUploading" class="spinner"></span>
              {{ cvUploading ? 'Analyzing…' : 'Analyze CV' }}
            </button>
          </div>
          <div v-if="cvError" class="alert alert-error">{{ cvError }}</div>
          <div v-if="cvAnalysis" class="cv-result">
            <div class="cv-result-row">Detected role <strong>{{ cvAnalysis.suggested_query }}</strong></div>
            <div v-if="cvAnalysis.matched_skills?.length" class="skill-tags">
              <span v-for="skill in cvAnalysis.matched_skills" :key="skill" class="skill-tag">{{ skill }}</span>
            </div>
            <div class="cv-hint">Pick a location and job type below, then click Search.</div>
          </div>
        </section>

        <!-- Search Box -->
        <section class="search-box">
          <div class="search-row">
            <div class="search-field">
              <input
                v-model="searchTitle"
                type="text"
                placeholder="Job title or keyword (Enter adds another)"
                @keyup.enter="onTitleEnter"
                @input="updateJobTitleSuggestions"
                @focus="updateJobTitleSuggestions"
                @blur="setTimeout(() => showJobTitleSuggestions = false, 120)"
                autocomplete="off"
              />
              <ul v-if="showJobTitleSuggestions" class="suggestions">
                <li v-for="title in jobTitleSuggestions" :key="title" @mousedown.prevent="selectJobTitleSuggestion(title)">
                  {{ title }}
                </li>
              </ul>
            </div>
            <div class="search-field">
              <input
                v-model="searchLocation"
                type="text"
                placeholder="Add location"
                @keyup.enter="() => { if (citySuggestions.length > 0) selectCitySuggestion(citySuggestions[0]) }"
                @input="updateCitySuggestions"
                @focus="updateCitySuggestions"
                @blur="setTimeout(() => showCitySuggestions = false, 120)"
                autocomplete="off"
              />
              <ul v-if="showCitySuggestions" class="suggestions">
                <li v-for="city in citySuggestions" :key="city" @mousedown.prevent="selectCitySuggestion(city)">
                  {{ city }}
                </li>
              </ul>
            </div>
            <button class="btn-primary btn-search" @click="searchJobs" :disabled="loading">
              <span v-if="loading" class="spinner"></span>
              {{ loading ? 'Searching…' : 'Search' }}
            </button>
          </div>
          <div v-if="selectedTitles.length || selectedLocations.length" class="selected-locations">
            <span v-for="title in selectedTitles" :key="title" class="location-tag">
              {{ title }}
              <button class="remove-tag" @click.prevent="removeTitle(title)">&times;</button>
            </span>
            <span v-for="city in selectedLocations" :key="city" class="location-tag">
              {{ city }}
              <button class="remove-tag" @click.prevent="removeLocation(city)">&times;</button>
            </span>
          </div>
          <div v-if="recentSearches.length" class="recent-searches">
            <span class="recent-label">Recent:</span>
            <button v-for="s in recentSearches" :key="s" class="recent-chip" @click="applyRecentSearch(s)">{{ s }}</button>
          </div>
        </section>

        <!-- Tabs -->
        <div class="tabs">
          <button class="tab" :class="{ active: activeTab === 'results' }" @click="selectTab('results')">
            Results <span v-if="jobs.length" class="tab-count">{{ jobs.length }}</span>
          </button>
          <button class="tab" :class="{ active: activeTab === 'saved' }" @click="selectTab('saved')">
            Saved <span v-if="savedJobs.length" class="tab-count">{{ savedJobs.length }}</span>
          </button>
          <button class="tab" :class="{ active: activeTab === 'history' }" @click="selectTab('history')">
            Scan history
          </button>
          <select v-if="activeTab === 'results'" v-model="sortBy" class="sort-select">
            <option value="relevance">Sort: Relevance</option>
            <option value="newest">Sort: New first</option>
            <option value="title">Sort: Title A-Z</option>
          </select>
        </div>

        <!-- Results tab -->
        <section v-if="activeTab === 'results'" class="job-list">
          <div v-if="error" class="alert alert-error">{{ error }}</div>
          <div v-if="notice" class="alert alert-notice">{{ notice }}</div>

          <div v-if="loading" class="skeleton-list">
            <div class="job-card skeleton" v-for="n in 3" :key="n">
              <div class="skeleton-line w-60"></div>
              <div class="skeleton-line w-30"></div>
              <div class="skeleton-line w-90"></div>
            </div>
          </div>

          <div v-else-if="jobs.length === 0 && !error" class="empty-state">
            <div class="empty-icon">🔍</div>
            <p>No jobs yet — try a search above or upload your CV.</p>
          </div>

          <template v-else>
            <div class="job-grid">
              <div v-for="job in sortedJobs" :key="jobKey(job)" class="job-card" @click="openJobDetails(job)">
                <span v-if="job.is_new" class="new-badge">New</span>
                <div class="job-card-header">
                  <span class="job-title">{{ job.title }}</span>
                  <span class="company">{{ job.company }}</span>
                </div>
                <div class="job-card-meta">
                  <span v-if="job.location" class="meta-tag">📍 {{ job.location }}</span>
                  <span v-if="job.job_type" class="meta-tag meta-tag-accent">{{ job.job_type }}</span>
                  <span v-if="job.experience_level" class="meta-tag">{{ job.experience_level }}</span>
                  <span v-if="job.posted_date" class="meta-tag">{{ job.posted_date }}</span>
                  <span class="meta-tag" :class="job.easy_apply ? 'meta-tag-easy' : ''">{{ job.easy_apply ? '⚡ Easy Apply' : 'Regular Apply' }}</span>
                  <span v-if="job.salary" class="meta-tag meta-tag-salary">💰 {{ job.salary }}</span>
                </div>
                <div v-if="job.summary" class="job-card-desc" v-html="highlightSummary(job.summary.slice(0, 140) + (job.summary.length > 140 ? '…' : ''))"></div>
                <div class="job-card-actions" @click.stop>
                  <a v-if="job.url" :href="job.url" target="_blank" rel="noopener" class="btn-primary btn-sm">Apply on LinkedIn</a>
                  <button class="btn-secondary btn-sm" @click="copyLink(job)" title="Copy link">🔗</button>
                  <button class="btn-secondary btn-sm" :class="{ 'btn-saved': isSaved(job) }" @click="saveJob(job)">
                    {{ isSaved(job) ? '★ Saved' : '☆ Save' }}
                  </button>
                </div>
              </div>
            </div>
            <div class="load-more-row">
              <button class="btn-secondary" @click="loadMore" :disabled="loadingMore">
                <span v-if="loadingMore" class="spinner spinner-dark"></span>
                {{ loadingMore ? 'Loading…' : 'Load more' }}
              </button>
            </div>
          </template>
        </section>

        <!-- Saved tab -->
        <section v-else-if="activeTab === 'saved'" class="job-list">
          <div v-if="savedJobs.length === 0" class="empty-state">
            <div class="empty-icon">⭐</div>
            <p>No saved jobs yet. Click "Save" on any job to keep it here.</p>
          </div>
          <template v-else>
            <div class="saved-toolbar">
              <button class="btn-secondary btn-sm" @click="exportSavedCsv">Export to CSV</button>
            </div>
            <div class="job-grid">
              <div v-for="job in savedJobs" :key="jobKey(job)" class="job-card" @click="openJobDetails(job)">
                <div class="job-card-header">
                  <span class="job-title">{{ job.title }}</span>
                  <span class="company">{{ job.company }}</span>
                </div>
                <div class="job-card-meta">
                  <span v-if="job.location" class="meta-tag">📍 {{ job.location }}</span>
                  <span v-if="job.job_type" class="meta-tag meta-tag-accent">{{ job.job_type }}</span>
                </div>
                <div class="job-card-actions" @click.stop>
                  <a v-if="job.url" :href="job.url" target="_blank" rel="noopener" class="btn-primary btn-sm">Apply on LinkedIn</a>
                  <button class="btn-secondary btn-sm" @click="copyLink(job)" title="Copy link">🔗</button>
                  <button class="btn-secondary btn-sm btn-saved" @click="saveJob(job)">Remove</button>
                </div>
              </div>
            </div>
          </template>
        </section>

        <!-- History tab -->
        <section v-else class="job-list">
          <div v-if="historyLoading" class="empty-state"><p>Loading history…</p></div>
          <div v-else-if="historyList.length === 0" class="empty-state">
            <div class="empty-icon">🕓</div>
            <p>No scans recorded yet — run a search or wait for the next auto-scan.</p>
          </div>
          <table v-else class="history-table">
            <thead>
              <tr>
                <th>When</th>
                <th>Query</th>
                <th>Location</th>
                <th>Type</th>
                <th>Total</th>
                <th>New</th>
                <th>Trigger</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(entry, idx) in historyList" :key="idx">
                <td>{{ formatTime(entry.timestamp) }}</td>
                <td>{{ entry.query }}</td>
                <td>{{ entry.location }}</td>
                <td>{{ entry.job_type || '—' }}</td>
                <td>{{ entry.total }}</td>
                <td><span v-if="entry.new_count" class="meta-tag meta-tag-accent">{{ entry.new_count }} new</span><span v-else>0</span></td>
                <td>{{ entry.triggered_by }}</td>
              </tr>
            </tbody>
          </table>
        </section>
      </main>
    </div>

    <!-- Job details modal -->
    <div v-if="selectedJob" class="modal-overlay" @click.self="closeJobDetails">
      <div class="modal">
        <button class="modal-close" @click="closeJobDetails">&times;</button>
        <h2 class="modal-title">{{ selectedJob.title }}</h2>
        <div class="modal-company">{{ selectedJob.company }}</div>
        <div class="job-card-meta">
          <span v-if="selectedJob.location" class="meta-tag">📍 {{ selectedJob.location }}</span>
          <span v-if="selectedJob.job_type" class="meta-tag meta-tag-accent">{{ selectedJob.job_type }}</span>
          <span v-if="selectedJob.experience_level" class="meta-tag">{{ selectedJob.experience_level }}</span>
          <span v-if="selectedJob.posted_date" class="meta-tag">{{ selectedJob.posted_date }}</span>
          <span class="meta-tag" :class="selectedJob.easy_apply ? 'meta-tag-easy' : ''">{{ selectedJob.easy_apply ? '⚡ Easy Apply' : 'Regular Apply' }}</span>
          <span v-if="selectedJob.salary" class="meta-tag meta-tag-salary">💰 {{ selectedJob.salary }}</span>
        </div>
        <div v-if="selectedJob.summary" class="modal-desc" v-html="highlightSummary(selectedJob.summary)"></div>
        <div class="job-card-actions">
          <a v-if="selectedJob.url" :href="selectedJob.url" target="_blank" rel="noopener" class="btn-primary btn-sm">Apply on LinkedIn</a>
          <button class="btn-secondary btn-sm" @click="copyLink(selectedJob)">🔗 Copy link</button>
          <button class="btn-secondary btn-sm" :class="{ 'btn-saved': isSaved(selectedJob) }" @click="saveJob(selectedJob)">
            {{ isSaved(selectedJob) ? '★ Saved' : '☆ Save' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
  --ink: #16202a;
  --ink-soft: #5b6b7a;
  --line: #e4e9ee;
  --surface: #ffffff;
  --canvas: #f4f6f9;
  --brand: #2f6fed;
  --brand-dark: #1f4fc4;
  --accent: #12a894;
  --accent-soft: #e4f7f4;
  --danger: #d64545;
  --danger-soft: #fdecec;
  --radius: 12px;
  --shadow: 0 1px 2px rgba(16, 24, 40, 0.04), 0 4px 16px rgba(16, 24, 40, 0.06);
}

:root[data-theme="dark"] {
  --ink: #e8edf3;
  --ink-soft: #97a3b0;
  --line: #2a323d;
  --surface: #1a2028;
  --canvas: #12161c;
  --brand: #5b8cff;
  --brand-dark: #7fa2ff;
  --accent: #2bcdb4;
  --accent-soft: rgba(43, 205, 180, 0.12);
  --danger: #ff6b6b;
  --danger-soft: rgba(255, 107, 107, 0.12);
  --shadow: 0 1px 2px rgba(0, 0, 0, 0.3), 0 4px 16px rgba(0, 0, 0, 0.35);
}

* { box-sizing: border-box; }
body { background: var(--canvas); }
</style>

<style scoped>
#app {
  font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
  background: var(--canvas);
  min-height: 100vh;
  color: var(--ink);
}

/* Toasts */
.toast-stack {
  position: fixed;
  top: 1.2rem;
  right: 1.2rem;
  z-index: 100;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.toast {
  padding: 0.7rem 1rem;
  border-radius: 8px;
  font-size: 0.87rem;
  font-weight: 600;
  color: #fff;
  box-shadow: var(--shadow);
  animation: toast-in 0.2s ease-out;
}
.toast-success { background: var(--accent); }
.toast-error { background: var(--danger); }
@keyframes toast-in {
  from { opacity: 0; transform: translateY(-8px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Header */
.header {
  background: var(--surface);
  border-bottom: 1px solid var(--line);
}
.header-inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 1rem 2rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}
.brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
.brand-mark {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--brand), var(--accent));
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.9rem;
  letter-spacing: 0.5px;
}
.brand-text {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}
.app-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--ink);
}
.app-subtitle {
  font-size: 0.8rem;
  color: var(--ink-soft);
}
.header-actions {
  display: flex;
  align-items: center;
  gap: 0.7rem;
}
.scan-badge {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4rem 0.9rem;
  border-radius: 999px;
  background: var(--accent-soft);
  color: var(--accent);
  font-size: 0.82rem;
  font-weight: 600;
}
.scan-badge .dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--accent);
  box-shadow: 0 0 0 3px rgba(18, 168, 148, 0.18);
}
.icon-btn {
  border: 1px solid var(--line);
  background: var(--surface);
  border-radius: 8px;
  width: 38px;
  height: 38px;
  cursor: pointer;
  font-size: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
}
.icon-btn:hover { border-color: var(--brand); }

/* Layout */
.main-layout {
  display: flex;
  max-width: 1200px;
  margin: 2rem auto;
  gap: 2rem;
  padding: 0 2rem;
  align-items: flex-start;
}
.sidebar {
  width: 240px;
  flex-shrink: 0;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 1.5rem;
  position: sticky;
  top: 1.5rem;
}
.sidebar h3 {
  margin: 0 0 1.1rem;
  font-size: 0.95rem;
  font-weight: 700;
}
.filter-group {
  margin-bottom: 1.2rem;
}
.filter-group label {
  display: block;
  margin-bottom: 0.4rem;
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--ink-soft);
}
.filter-group select,
.filter-group input:not([type="checkbox"]) {
  width: 100%;
  min-height: 46px;
  padding: 0.7rem 0.9rem;
  border-radius: 8px;
  border: 1px solid var(--line);
  background: var(--surface);
  font-family: inherit;
  font-size: 0.92rem;
  color: var(--ink);
}
.filter-group select:focus,
.filter-group input:not([type="checkbox"]):focus {
  outline: none;
  border-color: var(--brand);
  box-shadow: 0 0 0 3px rgba(47, 111, 237, 0.12);
}
.checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
  min-height: 46px;
  justify-content: center;
  padding: 0.5rem 0.9rem;
  border-radius: 8px;
  border: 1px solid var(--line);
  background: var(--surface);
}
.checkbox-option {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  color: var(--ink);
  cursor: pointer;
}
.checkbox-option input {
  width: 16px;
  height: 16px;
  accent-color: var(--brand);
  cursor: pointer;
}
.download-link {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  width: 100%;
  min-height: 46px;
  padding: 0.7rem 1rem;
  border-radius: 8px;
  border: 1px solid var(--line);
  color: var(--ink);
  text-decoration: none;
  font-weight: 600;
  font-size: 0.9rem;
  transition: background 0.15s, border-color 0.15s;
}
.download-link:hover {
  background: var(--canvas);
  border-color: var(--brand);
  color: var(--brand);
}
.content {
  flex: 1;
  min-width: 0;
}

/* Shared surfaces */
.cv-box, .search-box {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 1.4rem 1.5rem;
  margin-bottom: 1.5rem;
}
.cv-box-header h3 {
  margin: 0 0 0.25rem;
  font-size: 1.05rem;
  font-weight: 700;
}
.cv-box-subtitle {
  margin: 0 0 1rem;
  color: var(--ink-soft);
  font-size: 0.88rem;
}

/* Buttons */
.btn-primary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.65rem 1.3rem;
  border-radius: 8px;
  border: none;
  background: var(--brand);
  color: #fff;
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
  text-decoration: none;
  transition: background 0.15s, transform 0.05s;
  white-space: nowrap;
}
.btn-primary:hover:not(:disabled) { background: var(--brand-dark); }
.btn-primary:active:not(:disabled) { transform: translateY(1px); }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-secondary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.65rem 1.3rem;
  border-radius: 8px;
  border: 1px solid var(--line);
  background: var(--surface);
  color: var(--ink);
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s;
}
.btn-secondary:hover { border-color: var(--brand); color: var(--brand); }
.btn-secondary:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-saved { color: var(--accent); border-color: var(--accent); }
.btn-sm { padding: 0.5rem 1rem; font-size: 0.85rem; }

.spinner {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 2px solid rgba(255,255,255,0.4);
  border-top-color: #fff;
  animation: spin 0.7s linear infinite;
}
.spinner-dark {
  border: 2px solid rgba(22, 32, 42, 0.2);
  border-top-color: var(--ink);
}
@keyframes spin { to { transform: rotate(360deg); } }

/* CV upload */
.cv-row {
  display: flex;
  gap: 0.8rem;
  align-items: center;
  flex-wrap: wrap;
}
.file-input {
  flex: 1;
  min-width: 220px;
  display: flex;
  align-items: center;
  padding: 0.6rem 0.9rem;
  border: 1px dashed var(--line);
  border-radius: 8px;
  color: var(--ink-soft);
  font-size: 0.87rem;
  cursor: pointer;
  background: var(--canvas);
}
.file-input:hover { border-color: var(--brand); }
.file-input input { display: none; }
.cv-result {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--line);
}
.cv-result-row {
  font-size: 0.92rem;
  margin-bottom: 0.6rem;
}
.skill-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin-bottom: 0.6rem;
}
.skill-tag {
  background: var(--accent-soft);
  color: var(--accent);
  border-radius: 999px;
  padding: 0.2rem 0.7rem;
  font-size: 0.78rem;
  font-weight: 600;
}
.cv-hint {
  color: var(--accent);
  font-size: 0.85rem;
  font-weight: 500;
}

/* Search box */
.search-row {
  display: flex;
  gap: 0.8rem;
}
.search-field {
  position: relative;
  flex: 1;
}
.search-field input {
  width: 100%;
  padding: 0.65rem 0.9rem;
  border-radius: 8px;
  border: 1px solid var(--line);
  font-family: inherit;
  font-size: 0.92rem;
  background: var(--surface);
  color: var(--ink);
}
.search-field input:focus {
  outline: none;
  border-color: var(--brand);
  box-shadow: 0 0 0 3px rgba(47, 111, 237, 0.12);
}
.btn-search { flex-shrink: 0; }
.suggestions {
  position: absolute;
  left: 0;
  right: 0;
  top: calc(100% + 4px);
  z-index: 10;
  background: var(--surface);
  border: 1px solid var(--line);
  box-shadow: var(--shadow);
  border-radius: 8px;
  margin: 0;
  padding: 0.3rem 0;
  list-style: none;
  max-height: 200px;
  overflow-y: auto;
}
.suggestions li {
  padding: 0.55rem 0.9rem;
  cursor: pointer;
  font-size: 0.88rem;
  transition: background 0.1s;
}
.suggestions li:hover { background: var(--canvas); }
.selected-locations {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin-top: 0.8rem;
}
.location-tag {
  background: var(--accent-soft);
  color: var(--accent);
  border-radius: 999px;
  padding: 0.25rem 0.4rem 0.25rem 0.8rem;
  font-size: 0.83rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.3rem;
}
.remove-tag {
  background: none;
  border: none;
  color: inherit;
  opacity: 0.6;
  font-size: 1.1em;
  line-height: 1;
  cursor: pointer;
  padding: 0 0.2rem;
}
.remove-tag:hover { opacity: 1; }

/* Tabs */
.tabs {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin-bottom: 1rem;
  border-bottom: 1px solid var(--line);
  flex-wrap: wrap;
}
.tab {
  border: none;
  background: none;
  padding: 0.7rem 0.9rem;
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--ink-soft);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}
.tab.active {
  color: var(--brand);
  border-bottom-color: var(--brand);
}
.tab-count {
  background: var(--canvas);
  border-radius: 999px;
  padding: 0.05rem 0.5rem;
  font-size: 0.75rem;
}
.sort-select {
  margin-left: auto;
  padding: 0.4rem 0.7rem;
  border-radius: 8px;
  border: 1px solid var(--line);
  background: var(--surface);
  color: var(--ink);
  font-size: 0.85rem;
}

/* Alerts */
.alert {
  margin: 0 0 1rem;
  padding: 0.7rem 0.9rem;
  border-radius: 8px;
  font-size: 0.88rem;
}
.alert-error { background: var(--danger-soft); color: var(--danger); border: 1px solid var(--danger); border-opacity: 0.3; }
.alert-notice { background: var(--accent-soft); color: var(--accent); border: 1px solid var(--accent); }

/* Job list */
.job-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1rem;
}
.job-card {
  position: relative;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 1.2rem;
  display: flex;
  flex-direction: column;
  transition: box-shadow 0.15s, transform 0.15s;
  cursor: pointer;
}
.job-card:hover {
  box-shadow: 0 4px 20px rgba(16, 24, 40, 0.1);
  transform: translateY(-1px);
}
.new-badge {
  position: absolute;
  top: 0.9rem;
  right: 0.9rem;
  background: var(--brand);
  color: #fff;
  font-size: 0.7rem;
  font-weight: 700;
  padding: 0.15rem 0.55rem;
  border-radius: 999px;
}
.job-card-header {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  margin-bottom: 0.6rem;
  padding-right: 2.5rem;
}
.job-title {
  font-size: 1.02rem;
  font-weight: 700;
  color: var(--ink);
}
.company {
  color: var(--ink-soft);
  font-size: 0.88rem;
  font-weight: 500;
}
.job-card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin-bottom: 0.7rem;
}
.meta-tag {
  background: var(--canvas);
  color: var(--ink-soft);
  border-radius: 999px;
  padding: 0.2rem 0.65rem;
  font-size: 0.76rem;
  font-weight: 600;
}
.meta-tag-accent {
  background: rgba(47, 111, 237, 0.1);
  color: var(--brand);
  text-transform: capitalize;
}
.meta-tag-easy {
  background: var(--accent-soft);
  color: var(--accent);
}
.meta-tag-salary {
  background: rgba(18, 168, 148, 0.12);
  color: var(--accent);
  font-weight: 700;
}
.job-card-desc {
  color: var(--ink-soft);
  font-size: 0.87rem;
  line-height: 1.45;
  margin-bottom: 1rem;
  flex: 1;
}
.job-card-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}
.load-more-row {
  display: flex;
  justify-content: center;
  margin-top: 1.5rem;
}

/* Skeleton loading */
.skeleton-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1rem;
}
.skeleton { gap: 0.6rem; }
.skeleton-line {
  height: 12px;
  border-radius: 6px;
  background: linear-gradient(90deg, var(--canvas) 25%, var(--line) 50%, var(--canvas) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite;
}
.w-60 { width: 60%; }
.w-30 { width: 30%; }
.w-90 { width: 90%; }
@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* Empty state */
.empty-state {
  text-align: center;
  padding: 3rem 1rem;
  color: var(--ink-soft);
  background: var(--surface);
  border: 1px dashed var(--line);
  border-radius: var(--radius);
}
.empty-icon { font-size: 2rem; margin-bottom: 0.6rem; }

/* History table */
.history-table {
  width: 100%;
  border-collapse: collapse;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  overflow: hidden;
  font-size: 0.85rem;
}
.history-table th, .history-table td {
  text-align: left;
  padding: 0.6rem 0.9rem;
  border-bottom: 1px solid var(--line);
}
.history-table th {
  color: var(--ink-soft);
  font-weight: 600;
  background: var(--canvas);
}
.history-table tr:last-child td { border-bottom: none; }

/* Recent searches */
.recent-searches {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.4rem;
  margin-top: 0.8rem;
}
.recent-label {
  font-size: 0.8rem;
  color: var(--ink-soft);
  font-weight: 600;
}
.recent-chip {
  border: 1px solid var(--line);
  background: var(--canvas);
  color: var(--ink-soft);
  border-radius: 999px;
  padding: 0.25rem 0.8rem;
  font-size: 0.8rem;
  cursor: pointer;
}
.recent-chip:hover { border-color: var(--brand); color: var(--brand); }

.saved-toolbar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 1rem;
}

/* Highlighted keywords */
:deep(mark) {
  background: rgba(255, 214, 51, 0.5);
  color: inherit;
  border-radius: 3px;
  padding: 0 0.15em;
}

/* Job details modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(10, 14, 20, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.5rem;
  z-index: 200;
}
.modal {
  position: relative;
  background: var(--surface);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 1.8rem;
  max-width: 560px;
  width: 100%;
  max-height: 85vh;
  overflow-y: auto;
}
.modal-close {
  position: absolute;
  top: 1rem;
  right: 1rem;
  border: none;
  background: none;
  font-size: 1.4rem;
  line-height: 1;
  color: var(--ink-soft);
  cursor: pointer;
}
.modal-title {
  font-size: 1.2rem;
  font-weight: 700;
  margin: 0 0 0.2rem;
  padding-right: 2rem;
}
.modal-company {
  color: var(--ink-soft);
  font-weight: 500;
  margin-bottom: 0.8rem;
}
.modal-desc {
  color: var(--ink);
  font-size: 0.92rem;
  line-height: 1.6;
  margin: 1rem 0 1.4rem;
  white-space: pre-line;
}

@media (max-width: 800px) {
  .main-layout { flex-direction: column; padding: 0 1rem; }
  .sidebar { width: 100%; position: static; }
  .search-row { flex-direction: column; }
  .history-table { display: block; overflow-x: auto; }
}
</style>
