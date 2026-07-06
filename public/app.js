/**
 * GovTechJobs — Frontend Application (Enhanced)
 * Features: Bookmarks, Sort, Detail Modal, Age Calculator,
 *           Exam Calendar, Share, Dark/Light Mode, Back-to-Top
 */

(function () {
  'use strict';

  const API_BASE = '/api';
  const DEBOUNCE_MS = 350;

  // ============================================================
  // State
  // ============================================================
  const state = {
    itJobs: [], itTotal: 0, itPage: 1, itTotalPages: 1,
    itFilters: { domain: 'software_it', status: 'active', organization: '', qualification: '', experience: '', search: '' },
    allJobs: [], allTotal: 0, allPage: 1, allTotalPages: 1,
    allFilters: { domain: '', search: '' },
    cutoffs: [], portals: [], stats: {},
    allJobsCache: [], // For calendar and age calc
    savedJobs: JSON.parse(localStorage.getItem('govtechjobs_saved') || '[]'),
    activeTab: 'it-jobs',
    sortBy: 'deadline',
    calendarMonth: new Date().getMonth(),
    calendarYear: new Date().getFullYear(),
    theme: localStorage.getItem('govtechjobs_theme') || 'dark'
  };

  // ============================================================
  // Utilities
  // ============================================================
  function formatDate(dateStr) {
    if (!dateStr) return 'N/A';
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return 'N/A';
    return `${d.getDate()} ${months[d.getMonth()]} ${d.getFullYear()}`;
  }

  function daysRemaining(dateStr) {
    if (!dateStr) return null;
    return Math.ceil((new Date(dateStr) - new Date()) / (1000 * 60 * 60 * 24));
  }

  function formatNumber(num) {
    if (num == null) return '—';
    return num >= 1000 ? (num / 1000).toFixed(1).replace(/\.0$/, '') + 'K' : num.toString();
  }

  function debounce(fn, ms) {
    let timer;
    return (...args) => { clearTimeout(timer); timer = setTimeout(() => fn(...args), ms); };
  }

  function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  function showToast(message) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.classList.add('visible');
    setTimeout(() => toast.classList.remove('visible'), 2500);
  }

  const domainLabels = {
    software_it: '🖥️ Software/IT', telecom: '📡 Telecom', cybersecurity: '🔒 Cybersecurity',
    data_analytics: '📊 Data/Analytics', non_it: '🏛️ Non-IT Govt', banking: '🏦 Banking',
    psu: '⚡ PSU', teaching: '🎓 Teaching'
  };

  const statusLabels = {
    active: '🟢 Apply Now', upcoming: '🟡 Coming Soon', exam_scheduled: '🔵 Exam Scheduled',
    result: '🟠 Result Out', closed: '🔴 Closed'
  };

  const categoryLabelMap = {
    it_focused: '🖥️ IT/Software Focused Portals', central_govt: '🏛️ Central Government',
    defence: '🎖️ Defence', banking: '🏦 Banking & Finance', psu: '⚡ PSU / Public Sector',
    education: '🎓 Education & Research', state: '🗺️ State Government'
  };

  // ============================================================
  // API
  // ============================================================
  async function fetchJSON(url) {
    try {
      const r = await fetch(url);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      return await r.json();
    } catch (err) { console.error('API Error:', url, err); return null; }
  }

  async function fetchStats() {
    const data = await fetchJSON(`${API_BASE}/stats`);
    if (data) { state.stats = data; renderHeaderStats(data); }
  }

  async function fetchITJobs() {
    const f = state.itFilters;
    const params = new URLSearchParams();
    if (f.domain) params.set('domain', f.domain);
    if (f.status) params.set('status', f.status);
    if (f.organization) params.set('org', f.organization);
    if (f.qualification) params.set('qualification', f.qualification);
    if (f.experience) params.set('experience', f.experience);
    if (f.search) params.set('q', f.search);
    params.set('page', state.itPage);
    params.set('limit', 20);

    showLoading('it-loading');
    const data = await fetchJSON(`${API_BASE}/jobs?${params}`);
    hideLoading('it-loading');

    if (data) {
      state.itJobs = sortJobs(data.jobs);
      state.itTotal = data.total;
      state.itTotalPages = data.totalPages;
      renderJobCards('it-jobs-grid', state.itJobs);
      renderPagination('it-pagination', state.itPage, state.itTotalPages, p => { state.itPage = p; fetchITJobs(); });
      renderResultsCount('results-count', state.itTotal, data.total);
      renderActiveFilters();
    }
  }

  async function fetchAllJobs() {
    const f = state.allFilters;
    const params = new URLSearchParams();
    if (f.domain) params.set('domain', f.domain);
    if (f.search) params.set('q', f.search);
    params.set('page', state.allPage);
    params.set('limit', 20);

    showLoading('all-loading');
    const data = await fetchJSON(`${API_BASE}/jobs?${params}`);
    hideLoading('all-loading');

    if (data) {
      state.allJobs = data.jobs;
      state.allTotal = data.total;
      state.allTotalPages = data.totalPages;
      renderJobCards('all-jobs-grid', state.allJobs);
      renderPagination('all-pagination', state.allPage, state.allTotalPages, p => { state.allPage = p; fetchAllJobs(); });
      renderResultsCount('all-results-count', state.allTotal, data.total);
    }
  }

  async function fetchAllJobsForCalendar() {
    const data = await fetchJSON(`${API_BASE}/jobs?limit=100`);
    if (data) { state.allJobsCache = data.jobs; }
  }

  async function fetchCutoffs() {
    const y = document.getElementById('cutoff-year-filter').value;
    const c = document.getElementById('cutoff-category-filter').value;
    const params = new URLSearchParams();
    if (y) params.set('year', y);
    if (c) params.set('category', c);
    const data = await fetchJSON(`${API_BASE}/cutoffs?${params}`);
    if (data) { state.cutoffs = data.cutoffs; renderCutoffs(data.cutoffs); }
  }

  async function fetchPortals() {
    showLoading('portals-loading');
    const data = await fetchJSON(`${API_BASE}/portals`);
    hideLoading('portals-loading');
    if (data) { state.portals = data.portals; renderPortals(data.portals); }
  }

  // ============================================================
  // Sort
  // ============================================================
  function sortJobs(jobs) {
    const sorted = [...jobs];
    switch (state.sortBy) {
      case 'deadline':
        sorted.sort((a, b) => {
          const da = a.application_last_date ? new Date(a.application_last_date) : new Date('2099-01-01');
          const db = b.application_last_date ? new Date(b.application_last_date) : new Date('2099-01-01');
          return da - db;
        });
        break;
      case 'newest':
        sorted.sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0));
        break;
      case 'vacancies':
        sorted.sort((a, b) => (b.vacancies || 0) - (a.vacancies || 0));
        break;
      case 'org':
        sorted.sort((a, b) => (a.organization || '').localeCompare(b.organization || ''));
        break;
    }
    return sorted;
  }

  // ============================================================
  // Bookmarks / Save
  // ============================================================
  function isJobSaved(jobId) {
    return state.savedJobs.some(j => j.id === jobId);
  }

  function toggleSaveJob(job) {
    if (isJobSaved(job.id)) {
      state.savedJobs = state.savedJobs.filter(j => j.id !== job.id);
      showToast('Job removed from saved list');
    } else {
      state.savedJobs.push(job);
      showToast('⭐ Job saved! View in "Saved Jobs" tab');
    }
    localStorage.setItem('govtechjobs_saved', JSON.stringify(state.savedJobs));
    updateSavedBadge();
    // Re-render current cards to update bookmark buttons
    if (state.activeTab === 'it-jobs') renderJobCards('it-jobs-grid', state.itJobs);
    if (state.activeTab === 'all-jobs') renderJobCards('all-jobs-grid', state.allJobs);
    if (state.activeTab === 'saved-jobs') renderSavedJobs();
  }

  function updateSavedBadge() {
    const badge = document.getElementById('saved-badge');
    badge.textContent = state.savedJobs.length > 0 ? state.savedJobs.length : '';
  }

  function renderSavedJobs() {
    const container = document.getElementById('saved-jobs-grid');
    container.innerHTML = '';
    if (state.savedJobs.length === 0) {
      container.innerHTML = `
        <div class="saved-empty">
          <div class="saved-empty-icon">⭐</div>
          <div class="saved-empty-title">No Saved Jobs Yet</div>
          <div class="saved-empty-text">Click the bookmark icon (🔖) on any job card to save it here for quick access. Your saved jobs persist across sessions.</div>
        </div>`;
      return;
    }
    renderJobCards('saved-jobs-grid', state.savedJobs);
  }

  // ============================================================
  // Render Helpers
  // ============================================================
  function showLoading(id) { const el = document.getElementById(id); if (el) el.style.display = 'flex'; }
  function hideLoading(id) { const el = document.getElementById(id); if (el) el.style.display = 'none'; }

  function renderHeaderStats(s) {
    document.getElementById('stat-total-jobs').textContent = s.totalJobs || '—';
    document.getElementById('stat-active-jobs').textContent = s.activeJobs || '—';
    document.getElementById('stat-it-jobs').textContent = s.itJobs || '—';
    document.getElementById('stat-vacancies').textContent = formatNumber(s.totalVacancies);
    document.getElementById('last-updated').textContent = `Updated ${formatDate(s.lastUpdated)}`;
    document.getElementById('stat-sw-count').textContent = s.itJobs || '—';
    document.getElementById('stat-portals-count').textContent = s.totalPortals || '—';
    document.getElementById('stat-total-vacancies').textContent = formatNumber(s.totalVacancies);
    document.getElementById('stat-apply-now').textContent = s.activeJobs || '—';
  }

  function renderJobCards(containerId, jobs) {
    const container = document.getElementById(containerId);
    if (!container) return;
    const existing = container.querySelectorAll('.job-card, .empty-state, .saved-empty');
    existing.forEach(el => el.remove());

    if (jobs.length === 0) {
      container.insertAdjacentHTML('beforeend', `
        <div class="empty-state">
          <div class="empty-state-icon">🔍</div>
          <div class="empty-state-title">No jobs found</div>
          <div class="empty-state-text">Try adjusting your filters or search terms</div>
        </div>`);
      return;
    }

    jobs.forEach((job, index) => {
      const days = daysRemaining(job.application_last_date);
      const isUrgent = days !== null && days <= 7 && days > 0;
      let deadlineText = '';
      if (days !== null) {
        if (days <= 0) deadlineText = 'Deadline passed';
        else if (days === 1) deadlineText = '1 day left!';
        else deadlineText = `${days} days left`;
      }

      const saved = isJobSaved(job.id);
      const card = document.createElement('div');
      card.className = 'job-card';
      card.style.animationDelay = `${index * 50}ms`;

      card.innerHTML = `
        <div class="job-card-header">
          <div class="job-card-title-section" style="cursor:pointer;" data-job-id="${job.id}">
            <div class="job-org-badge ${job.job_domain || ''}">${job.organization} ${domainLabels[job.job_domain] ? '· ' + domainLabels[job.job_domain] : ''}</div>
            <div class="job-exam-name">${escapeHtml(job.exam_name)}</div>
            <div class="job-post-name">${escapeHtml(job.post_name || '')}</div>
          </div>
          <div class="job-status-badge ${job.status}">${statusLabels[job.status] || job.status}</div>
        </div>
        ${job.application_last_date ? `
        <div class="job-deadline">
          <span class="job-deadline-icon">📅</span>
          <span class="job-deadline-text">Apply by: <strong>${formatDate(job.application_last_date)}</strong></span>
          ${deadlineText ? `<span class="job-deadline-countdown ${isUrgent ? 'urgent' : 'normal'}">${deadlineText}</span>` : ''}
        </div>` : ''}
        <div class="job-meta">
          ${job.qualification ? `<div class="job-meta-item"><span class="job-meta-icon">🎓</span><span class="job-meta-value">${escapeHtml(job.qualification)}</span></div>` : ''}
          ${job.experience_required ? `<div class="job-meta-item"><span class="job-meta-icon">💼</span><span class="job-meta-value">${escapeHtml(job.experience_required)}</span></div>` : ''}
          ${job.pay_scale ? `<div class="job-meta-item"><span class="job-meta-icon">💰</span><span class="job-meta-value">${escapeHtml(job.pay_scale)}</span></div>` : ''}
          ${job.location ? `<div class="job-meta-item"><span class="job-meta-icon">📍</span><span class="job-meta-value">${escapeHtml(job.location)}</span></div>` : ''}
          ${job.vacancies ? `<div class="job-meta-item"><span class="job-meta-icon">👥</span><span class="job-meta-value">${job.vacancies} vacancies</span></div>` : ''}
          ${job.application_fee ? `<div class="job-meta-item"><span class="job-meta-icon">🏷️</span><span class="job-meta-value">${escapeHtml(job.application_fee)}</span></div>` : ''}
        </div>
        <div class="job-actions">
          ${job.apply_link ? `<a href="${escapeHtml(job.apply_link)}" target="_blank" rel="noopener" class="btn btn-apply"><span class="btn-icon">✅</span> Apply Now →</a>` : `<a href="${escapeHtml(job.portal_url || '#')}" target="_blank" rel="noopener" class="btn btn-portal"><span class="btn-icon">🌐</span> Visit Portal →</a>`}
          <button class="btn btn-cutoff" data-cutoff-job="${job.id}"><span class="btn-icon">📊</span> View Cutoffs</button>
          ${job.notification_pdf_url ? `<a href="${escapeHtml(job.notification_pdf_url)}" target="_blank" rel="noopener" class="btn btn-pdf"><span class="btn-icon">📄</span> PDF</a>` : ''}
          <button class="btn btn-bookmark ${saved ? 'saved' : ''}" data-bookmark-job='${JSON.stringify({ id: job.id, exam_name: job.exam_name, organization: job.organization, post_name: job.post_name, job_domain: job.job_domain, status: job.status, application_last_date: job.application_last_date, qualification: job.qualification, experience_required: job.experience_required, pay_scale: job.pay_scale, location: job.location, vacancies: job.vacancies, application_fee: job.application_fee, apply_link: job.apply_link, portal_url: job.portal_url, notification_pdf_url: job.notification_pdf_url, portal_instructions: job.portal_instructions, notification_date: job.notification_date, application_start_date: job.application_start_date, exam_date: job.exam_date, age_limit: job.age_limit, organization_full: job.organization_full, total_marks: job.total_marks, source_url: job.source_url })}'><span class="bookmark-icon">${saved ? '⭐' : '🔖'}</span></button>
          <div class="btn btn-share" data-share-job="${job.id}" style="position:relative;"><span class="btn-icon">📤</span>
            <div class="share-popup" id="share-popup-${job.id}">
              <div class="share-option" data-share-action="whatsapp" data-share-text="${escapeHtml(job.exam_name)} — ${escapeHtml(job.organization)}\n${job.apply_link || job.portal_url || ''}"><span class="share-option-icon">💬</span> WhatsApp</div>
              <div class="share-option" data-share-action="telegram" data-share-text="${escapeHtml(job.exam_name)} — ${escapeHtml(job.organization)}\n${job.apply_link || job.portal_url || ''}"><span class="share-option-icon">✈️</span> Telegram</div>
              <div class="share-option" data-share-action="copy" data-share-text="${escapeHtml(job.exam_name)} — ${escapeHtml(job.organization)}\nApply: ${job.apply_link || job.portal_url || ''}\nDeadline: ${formatDate(job.application_last_date)}"><span class="share-option-icon">📋</span> Copy Text</div>
            </div>
          </div>
        </div>
        <div class="job-cutoffs" id="cutoffs-${job.id}"></div>
      `;

      // Click title to open modal
      card.querySelector('[data-job-id]').addEventListener('click', () => openJobModal(job));

      container.appendChild(card);
    });

    // Attach event handlers
    container.querySelectorAll('[data-cutoff-job]').forEach(btn => {
      btn.addEventListener('click', () => toggleCutoffsInline(parseInt(btn.dataset.cutoffJob)));
    });
    container.querySelectorAll('[data-bookmark-job]').forEach(btn => {
      btn.addEventListener('click', () => toggleSaveJob(JSON.parse(btn.dataset.bookmarkJob)));
    });
    container.querySelectorAll('[data-share-job]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const popup = document.getElementById(`share-popup-${btn.dataset.shareJob}`);
        document.querySelectorAll('.share-popup.visible').forEach(p => { if (p !== popup) p.classList.remove('visible'); });
        popup.classList.toggle('visible');
      });
    });
    container.querySelectorAll('[data-share-action]').forEach(opt => {
      opt.addEventListener('click', (e) => {
        e.stopPropagation();
        const text = opt.dataset.shareText;
        if (opt.dataset.shareAction === 'whatsapp') {
          window.open(`https://wa.me/?text=${encodeURIComponent(text)}`, '_blank');
        } else if (opt.dataset.shareAction === 'telegram') {
          window.open(`https://t.me/share/url?url=${encodeURIComponent(text)}`, '_blank');
        } else if (opt.dataset.shareAction === 'copy') {
          navigator.clipboard.writeText(text).then(() => showToast('📋 Copied to clipboard!'));
        }
        opt.closest('.share-popup').classList.remove('visible');
      });
    });
  }

  async function toggleCutoffsInline(jobId) {
    const container = document.getElementById(`cutoffs-${jobId}`);
    if (!container) return;
    if (container.classList.contains('visible')) { container.classList.remove('visible'); return; }
    container.innerHTML = '<div class="loading-container" style="padding:16px;"><div class="loading-spinner" style="width:24px;height:24px;"></div></div>';
    container.classList.add('visible');
    const data = await fetchJSON(`${API_BASE}/jobs/${jobId}`);
    const cutoffs = data?.cutoffs || [];
    if (cutoffs.length === 0) {
      container.innerHTML = '<div style="text-align:center;padding:16px;color:var(--text-muted);font-size:0.85rem;">📊 No previous cutoff data available for this exam yet.</div>';
    } else {
      let html = '<table class="cutoff-table"><thead><tr><th>Tier</th><th>Year</th><th>Category</th><th>Qualifying</th><th>Merit</th><th>Total</th></tr></thead><tbody>';
      cutoffs.forEach(c => {
        html += `<tr><td>${escapeHtml(c.tier||'N/A')}</td><td>${c.year||'N/A'}</td><td><span class="cutoff-cat-badge ${c.category}">${c.category}</span></td><td style="color:var(--accent-secondary);font-weight:600;">${c.qualifying_marks||'N/A'}</td><td style="color:var(--accent-primary);font-weight:600;">${c.merit_marks||'N/A'}</td><td>${c.total_marks||'N/A'}</td></tr>`;
      });
      html += '</tbody></table>';
      container.innerHTML = html;
    }
  }

  // ============================================================
  // Job Detail Modal
  // ============================================================
  function openJobModal(job) {
    const headerContent = document.getElementById('modal-header-content');
    const body = document.getElementById('modal-body');
    const actions = document.getElementById('modal-actions');

    headerContent.innerHTML = `
      <div class="job-org-badge ${job.job_domain || ''}" style="margin-bottom:8px;">${job.organization} ${domainLabels[job.job_domain] ? '· ' + domainLabels[job.job_domain] : ''}</div>
      <h2 style="font-family:var(--font-heading);font-size:1.3rem;margin-bottom:4px;">${escapeHtml(job.exam_name)}</h2>
      <div style="font-size:0.9rem;color:var(--text-secondary);">${escapeHtml(job.post_name || '')}</div>
      ${job.organization_full ? `<div style="font-size:0.8rem;color:var(--text-muted);margin-top:4px;">${escapeHtml(job.organization_full)}</div>` : ''}
    `;

    // Build info grid
    const infoItems = [
      { label: 'Qualification', value: job.qualification },
      { label: 'Experience', value: job.experience_required },
      { label: 'Pay Scale', value: job.pay_scale },
      { label: 'Location', value: job.location },
      { label: 'Vacancies', value: job.vacancies },
      { label: 'Age Limit', value: job.age_limit },
      { label: 'Application Fee', value: job.application_fee },
      { label: 'Total Marks', value: job.total_marks },
    ].filter(i => i.value);

    // Build timeline
    const now = new Date();
    const dates = [
      { label: 'Notification Date', date: job.notification_date },
      { label: 'Application Start', date: job.application_start_date },
      { label: 'Application Deadline', date: job.application_last_date },
      { label: 'Exam Date', date: job.exam_date },
    ].filter(d => d.date);

    // Build apply steps
    let stepsHTML = '';
    if (job.portal_instructions) {
      const steps = job.portal_instructions.split('→').map(s => s.trim()).filter(Boolean);
      stepsHTML = `
        <div class="modal-section">
          <div class="modal-section-title">📝 How to Apply</div>
          <div class="apply-steps">${steps.map((s, i) =>
            `<div class="apply-step"><div class="apply-step-number">${i + 1}</div><div class="apply-step-text">${escapeHtml(s)}</div></div>`
          ).join('')}</div>
        </div>`;
    }

    body.innerHTML = `
      <div class="modal-section">
        <div class="modal-section-title">📋 Job Details</div>
        <div class="modal-info-grid">
          ${infoItems.map(i => `<div class="modal-info-item"><div class="modal-info-label">${i.label}</div><div class="modal-info-value">${escapeHtml(String(i.value))}</div></div>`).join('')}
        </div>
      </div>
      ${dates.length > 0 ? `
      <div class="modal-section">
        <div class="modal-section-title">📅 Important Dates</div>
        <div class="timeline">
          ${dates.map(d => {
            const dd = new Date(d.date);
            const cls = dd < now ? 'past' : (daysRemaining(d.date) <= 7 ? 'current' : '');
            return `<div class="timeline-item ${cls}"><div class="timeline-date">${formatDate(d.date)}</div><div class="timeline-label">${d.label}</div></div>`;
          }).join('')}
        </div>
      </div>` : ''}
      ${stepsHTML}
    `;

    const saved = isJobSaved(job.id);
    actions.innerHTML = `
      ${job.apply_link ? `<a href="${escapeHtml(job.apply_link)}" target="_blank" rel="noopener" class="btn btn-apply"><span class="btn-icon">✅</span> Apply Now →</a>` : `<a href="${escapeHtml(job.portal_url || '#')}" target="_blank" rel="noopener" class="btn btn-portal"><span class="btn-icon">🌐</span> Visit Portal →</a>`}
      ${job.notification_pdf_url ? `<a href="${escapeHtml(job.notification_pdf_url)}" target="_blank" rel="noopener" class="btn btn-pdf"><span class="btn-icon">📄</span> Notification PDF</a>` : ''}
      <button class="btn btn-bookmark ${saved ? 'saved' : ''}" id="modal-bookmark"><span class="bookmark-icon">${saved ? '⭐' : '🔖'}</span> ${saved ? 'Saved' : 'Save Job'}</button>
    `;

    document.getElementById('modal-bookmark').addEventListener('click', () => {
      toggleSaveJob(job);
      const btn = document.getElementById('modal-bookmark');
      const nowSaved = isJobSaved(job.id);
      btn.className = `btn btn-bookmark ${nowSaved ? 'saved' : ''}`;
      btn.innerHTML = `<span class="bookmark-icon">${nowSaved ? '⭐' : '🔖'}</span> ${nowSaved ? 'Saved' : 'Save Job'}`;
    });

    document.getElementById('job-modal-overlay').classList.add('visible');
  }

  function closeJobModal() {
    document.getElementById('job-modal-overlay').classList.remove('visible');
  }

  // ============================================================
  // Age Eligibility Calculator
  // ============================================================
  function checkAgeEligibility() {
    const dobInput = document.getElementById('dob-input');
    const resultDiv = document.getElementById('age-result');
    if (!dobInput.value) { showToast('Please enter your date of birth'); return; }

    const dob = new Date(dobInput.value);
    const now = new Date();
    let age = now.getFullYear() - dob.getFullYear();
    const m = now.getMonth() - dob.getMonth();
    if (m < 0 || (m === 0 && now.getDate() < dob.getDate())) age--;

    // Check all cached jobs
    const jobs = state.allJobsCache.length > 0 ? state.allJobsCache : state.itJobs;
    let eligibleCount = 0;
    let notEligibleCount = 0;
    let resultHTML = `<div class="age-result-current">🎂 Your Age: <strong>${age} years</strong> (Born: ${formatDate(dobInput.value)})</div>`;
    resultHTML += '<div style="margin-top:12px;">';

    jobs.forEach(job => {
      if (!job.age_limit) return;
      const match = job.age_limit.match(/(\d+)\s*years/);
      if (!match) return;
      const maxAge = parseInt(match[1]);
      const isEligible = age <= maxAge;
      if (isEligible) eligibleCount++; else notEligibleCount++;
      resultHTML += `<div style="display:flex;align-items:center;gap:8px;padding:6px 0;border-bottom:1px solid var(--border-color);">
        <span class="${isEligible ? 'eligible' : 'not-eligible'}">${isEligible ? '✅' : '❌'}</span>
        <span style="flex:1;font-size:0.83rem;">${escapeHtml(job.exam_name)} <span style="color:var(--text-muted);">— Max: ${maxAge} yrs</span></span>
        <span class="${isEligible ? 'eligible' : 'not-eligible'}" style="font-size:0.78rem;">${isEligible ? 'Eligible' : 'Over age'}</span>
      </div>`;
    });

    resultHTML += '</div>';
    resultHTML += `<div style="margin-top:12px;font-size:0.85rem;">Summary: <span class="eligible">${eligibleCount} eligible</span> · <span class="not-eligible">${notEligibleCount} not eligible</span></div>`;

    resultDiv.innerHTML = resultHTML;
    resultDiv.style.display = 'block';
  }

  // ============================================================
  // Exam Calendar
  // ============================================================
  function renderCalendar() {
    const grid = document.getElementById('calendar-grid');
    const label = document.getElementById('cal-month-label');
    const months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
    label.textContent = `${months[state.calendarMonth]} ${state.calendarYear}`;

    grid.innerHTML = '';

    // Day headers
    ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].forEach(d => {
      grid.insertAdjacentHTML('beforeend', `<div class="calendar-day-header">${d}</div>`);
    });

    const firstDay = new Date(state.calendarYear, state.calendarMonth, 1);
    const lastDay = new Date(state.calendarYear, state.calendarMonth + 1, 0);
    const startPad = firstDay.getDay();
    const totalDays = lastDay.getDate();
    const today = new Date();

    // Collect events from jobs
    const events = [];
    const jobs = state.allJobsCache.length > 0 ? state.allJobsCache : state.itJobs;
    jobs.forEach(job => {
      if (job.application_last_date) events.push({ date: job.application_last_date, label: `📛 ${job.organization}`, type: 'deadline', job });
      if (job.exam_date) events.push({ date: job.exam_date, label: `📝 ${job.organization}`, type: 'exam', job });
      if (job.application_start_date) events.push({ date: job.application_start_date, label: `🟢 ${job.organization}`, type: 'start', job });
    });

    // Previous month padding
    const prevMonth = new Date(state.calendarYear, state.calendarMonth, 0);
    for (let i = startPad - 1; i >= 0; i--) {
      const dayNum = prevMonth.getDate() - i;
      grid.insertAdjacentHTML('beforeend', `<div class="calendar-day other-month"><div class="calendar-day-number">${dayNum}</div></div>`);
    }

    // Days
    for (let d = 1; d <= totalDays; d++) {
      const dateStr = `${state.calendarYear}-${String(state.calendarMonth + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
      const isToday = today.getFullYear() === state.calendarYear && today.getMonth() === state.calendarMonth && today.getDate() === d;
      const dayEvents = events.filter(e => e.date && e.date.startsWith(dateStr));

      let eventsHTML = '';
      dayEvents.slice(0, 3).forEach(e => {
        eventsHTML += `<div class="calendar-event ${e.type}" title="${escapeHtml(e.job.exam_name)}">${escapeHtml(e.label)}</div>`;
      });
      if (dayEvents.length > 3) {
        eventsHTML += `<div style="font-size:0.55rem;color:var(--text-muted);">+${dayEvents.length - 3} more</div>`;
      }

      grid.insertAdjacentHTML('beforeend', `<div class="calendar-day ${isToday ? 'today' : ''}"><div class="calendar-day-number">${d}</div>${eventsHTML}</div>`);
    }

    // Next month padding
    const totalCells = startPad + totalDays;
    const remaining = (7 - (totalCells % 7)) % 7;
    for (let i = 1; i <= remaining; i++) {
      grid.insertAdjacentHTML('beforeend', `<div class="calendar-day other-month"><div class="calendar-day-number">${i}</div></div>`);
    }
  }

  // ============================================================
  // Theme Toggle
  // ============================================================
  function applyTheme(theme) {
    state.theme = theme;
    document.body.classList.toggle('light-mode', theme === 'light');
    document.getElementById('theme-toggle').textContent = theme === 'light' ? '☀️' : '🌙';
    localStorage.setItem('govtechjobs_theme', theme);
  }

  // ============================================================
  // Back to Top
  // ============================================================
  function initBackToTop() {
    const btn = document.getElementById('back-to-top');
    window.addEventListener('scroll', () => {
      btn.classList.toggle('visible', window.scrollY > 400);
    });
    btn.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
  }

  // ============================================================
  // Render: Pagination, Results, Filters, Cutoffs, Portals
  // ============================================================
  function renderPagination(containerId, currentPage, totalPages, onPageChange) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = '';
    if (totalPages <= 1) return;

    const prevBtn = document.createElement('button');
    prevBtn.className = 'page-btn'; prevBtn.textContent = '← Prev'; prevBtn.disabled = currentPage <= 1;
    prevBtn.addEventListener('click', () => onPageChange(currentPage - 1));
    container.appendChild(prevBtn);

    const maxVisible = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxVisible / 2));
    let endPage = Math.min(totalPages, startPage + maxVisible - 1);
    if (endPage - startPage < maxVisible - 1) startPage = Math.max(1, endPage - maxVisible + 1);

    if (startPage > 1) {
      container.appendChild(createPageBtn(1, currentPage, onPageChange));
      if (startPage > 2) { const dots = document.createElement('span'); dots.textContent = '...'; dots.style.cssText = 'color:var(--text-muted);padding:0 4px;'; container.appendChild(dots); }
    }
    for (let i = startPage; i <= endPage; i++) container.appendChild(createPageBtn(i, currentPage, onPageChange));
    if (endPage < totalPages) {
      if (endPage < totalPages - 1) { const dots = document.createElement('span'); dots.textContent = '...'; dots.style.cssText = 'color:var(--text-muted);padding:0 4px;'; container.appendChild(dots); }
      container.appendChild(createPageBtn(totalPages, currentPage, onPageChange));
    }

    const nextBtn = document.createElement('button');
    nextBtn.className = 'page-btn'; nextBtn.textContent = 'Next →'; nextBtn.disabled = currentPage >= totalPages;
    nextBtn.addEventListener('click', () => onPageChange(currentPage + 1));
    container.appendChild(nextBtn);
  }

  function createPageBtn(pageNum, currentPage, onPageChange) {
    const btn = document.createElement('button');
    btn.className = `page-btn ${pageNum === currentPage ? 'active' : ''}`;
    btn.textContent = pageNum;
    btn.addEventListener('click', () => onPageChange(pageNum));
    return btn;
  }

  function renderResultsCount(elementId, filtered, total) {
    const el = document.getElementById(elementId);
    if (el) el.innerHTML = `Showing <strong>${filtered}</strong> of <strong>${total}</strong> jobs`;
  }

  function renderActiveFilters() {
    const container = document.getElementById('active-filters');
    if (!container) return;
    container.innerHTML = '';
    const f = state.itFilters;

    if (f.domain) addFilterChip(container, domainLabels[f.domain] || f.domain, () => { state.itFilters.domain = ''; updateDomainPills(); state.itPage = 1; fetchITJobs(); });
    if (f.status) addFilterChip(container, statusLabels[f.status] || f.status, () => { state.itFilters.status = ''; updateStatusPills(); state.itPage = 1; fetchITJobs(); });
    if (f.organization) addFilterChip(container, `Org: ${f.organization}`, () => { state.itFilters.organization = ''; document.getElementById('filter-org').value = ''; state.itPage = 1; fetchITJobs(); });
    if (f.qualification) addFilterChip(container, `Qual: ${f.qualification}`, () => { state.itFilters.qualification = ''; document.getElementById('filter-qualification').value = ''; state.itPage = 1; fetchITJobs(); });
    if (f.experience) addFilterChip(container, `Exp: ${f.experience}`, () => { state.itFilters.experience = ''; document.getElementById('filter-experience').value = ''; state.itPage = 1; fetchITJobs(); });
    if (f.search) addFilterChip(container, `"${f.search}"`, () => { state.itFilters.search = ''; document.getElementById('search-input').value = ''; state.itPage = 1; fetchITJobs(); });

    const count = [f.domain, f.status, f.organization, f.qualification, f.experience, f.search].filter(Boolean).length;
    if (count > 1) {
      const clearBtn = document.createElement('button');
      clearBtn.className = 'clear-all-btn'; clearBtn.textContent = '✕ Clear All';
      clearBtn.addEventListener('click', () => {
        state.itFilters = { domain: '', status: '', organization: '', qualification: '', experience: '', search: '' };
        document.getElementById('search-input').value = '';
        document.getElementById('filter-org').value = '';
        document.getElementById('filter-qualification').value = '';
        document.getElementById('filter-experience').value = '';
        updateDomainPills(); updateStatusPills(); state.itPage = 1; fetchITJobs();
      });
      container.appendChild(clearBtn);
    }
  }

  function addFilterChip(container, label, onRemove) {
    const chip = document.createElement('div');
    chip.className = 'filter-chip';
    chip.innerHTML = `${escapeHtml(label)} <button class="filter-chip-remove" aria-label="Remove">✕</button>`;
    chip.querySelector('.filter-chip-remove').addEventListener('click', onRemove);
    container.appendChild(chip);
  }

  function renderCutoffs(cutoffs) {
    const tbody = document.getElementById('cutoffs-tbody');
    if (!tbody) return;
    tbody.innerHTML = '';
    if (cutoffs.length === 0) {
      tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;padding:32px;color:var(--text-muted);">No cutoff data available.</td></tr>';
      return;
    }
    cutoffs.forEach(c => {
      tbody.insertAdjacentHTML('beforeend', `<tr>
        <td style="color:var(--text-primary);font-weight:500;">${escapeHtml(c.exam_name || 'N/A')}</td>
        <td>${escapeHtml(c.organization || 'N/A')}</td>
        <td>${escapeHtml(c.tier || 'N/A')}</td><td>${c.year || 'N/A'}</td>
        <td><span class="cutoff-cat-badge ${c.category}">${c.category}</span></td>
        <td style="font-weight:600;color:var(--accent-secondary);">${c.qualifying_marks || 'N/A'}</td>
        <td style="font-weight:600;color:var(--accent-primary);">${c.merit_marks || 'N/A'}</td>
        <td>${c.total_marks || 'N/A'}</td></tr>`);
    });
  }

  function renderPortals(portals) {
    const container = document.getElementById('portals-container');
    if (!container) return;
    const loadingEl = document.getElementById('portals-loading');
    if (loadingEl) loadingEl.remove();
    container.querySelectorAll('.portal-category-header, .portal-grid').forEach(el => el.remove());

    const grouped = {};
    portals.forEach(p => { if (!grouped[p.category]) grouped[p.category] = []; grouped[p.category].push(p); });
    ['it_focused', 'central_govt', 'defence', 'banking', 'psu', 'education', 'state'].forEach(cat => {
      if (!grouped[cat] || grouped[cat].length === 0) return;
      container.insertAdjacentHTML('beforeend', `<h2 class="portal-category-header">${categoryLabelMap[cat] || cat}</h2>`);
      const grid = document.createElement('div'); grid.className = 'portal-grid';
      grouped[cat].forEach(p => {
        grid.insertAdjacentHTML('beforeend', `
          <div class="portal-card">
            <div class="portal-card-header"><span class="portal-short-name">${escapeHtml(p.short_name)}</span><span class="portal-cat-badge">${(categoryLabelMap[p.category] || '').split(' ')[0]}</span></div>
            <div class="portal-full-name">${escapeHtml(p.name)}</div>
            <div class="portal-description">${escapeHtml(p.description || '')}</div>
            ${p.it_roles_available ? `<div class="portal-it-roles"><strong>IT Roles:</strong> ${escapeHtml(p.it_roles_available)}</div>` : ''}
            <a href="${escapeHtml(p.url)}" target="_blank" rel="noopener" class="portal-link">Visit Portal <span>→</span></a>
          </div>`);
      });
      container.appendChild(grid);
    });
  }

  // ============================================================
  // Filter Interaction
  // ============================================================
  function updateDomainPills() {
    document.querySelectorAll('#domain-filter-row .filter-pill').forEach(p => p.classList.toggle('active', p.dataset.domain === state.itFilters.domain));
  }
  function updateStatusPills() {
    document.querySelectorAll('#status-filter-row .filter-pill').forEach(p => p.classList.toggle('active', p.dataset.status === state.itFilters.status));
  }

  function initFilters() {
    document.querySelectorAll('#domain-filter-row .filter-pill').forEach(pill => {
      pill.addEventListener('click', () => { state.itFilters.domain = state.itFilters.domain === pill.dataset.domain ? '' : pill.dataset.domain; updateDomainPills(); state.itPage = 1; fetchITJobs(); });
    });
    document.querySelectorAll('#status-filter-row .filter-pill').forEach(pill => {
      pill.addEventListener('click', () => { state.itFilters.status = state.itFilters.status === pill.dataset.status ? '' : pill.dataset.status; updateStatusPills(); state.itPage = 1; fetchITJobs(); });
    });
    document.getElementById('filter-org').addEventListener('change', e => { state.itFilters.organization = e.target.value; state.itPage = 1; fetchITJobs(); });
    document.getElementById('filter-qualification').addEventListener('change', e => { state.itFilters.qualification = e.target.value; state.itPage = 1; fetchITJobs(); });
    document.getElementById('filter-experience').addEventListener('change', e => { state.itFilters.experience = e.target.value; state.itPage = 1; fetchITJobs(); });

    const searchInput = document.getElementById('search-input');
    searchInput.addEventListener('input', debounce(() => { state.itFilters.search = searchInput.value.trim(); state.itPage = 1; fetchITJobs(); }, DEBOUNCE_MS));

    // Sort
    document.getElementById('sort-select').addEventListener('change', e => { state.sortBy = e.target.value; fetchITJobs(); });

    // All Jobs tab
    document.querySelectorAll('.all-domain-pill').forEach(pill => {
      pill.addEventListener('click', () => { document.querySelectorAll('.all-domain-pill').forEach(p => p.classList.remove('active')); pill.classList.add('active'); state.allFilters.domain = pill.dataset.domain; state.allPage = 1; fetchAllJobs(); });
    });
    const allSearch = document.getElementById('all-search-input');
    allSearch.addEventListener('input', debounce(() => { state.allFilters.search = allSearch.value.trim(); state.allPage = 1; fetchAllJobs(); }, DEBOUNCE_MS));

    // Cutoff filters
    document.getElementById('cutoff-year-filter').addEventListener('change', fetchCutoffs);
    document.getElementById('cutoff-category-filter').addEventListener('change', fetchCutoffs);

    populateOrgDropdown();
  }

  function populateOrgDropdown() {
    const orgs = ['DRDO','ISRO','NIC','CDAC','BEL','ECIL','NIELIT','SSC','UPSC','IBPS','RRB','NTA','SBI','RBI','HAL','BSNL','NTPC','SEBI','KVS','PowerGrid','RailTel','STPI','UIDAI','Navy','LIC'].sort();
    const select = document.getElementById('filter-org');
    orgs.forEach(org => { const o = document.createElement('option'); o.value = org; o.textContent = org; select.appendChild(o); });
  }

  // ============================================================
  // Tab Navigation
  // ============================================================
  function initTabs() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
      btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });
  }

  function switchTab(tab) {
    state.activeTab = tab;
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('active', b.dataset.tab === tab));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    const panel = document.getElementById(`panel-${tab}`);
    if (panel) panel.classList.add('active');

    if (tab === 'all-jobs' && state.allJobs.length === 0) fetchAllJobs();
    else if (tab === 'cutoffs' && state.cutoffs.length === 0) fetchCutoffs();
    else if (tab === 'portals' && state.portals.length === 0) fetchPortals();
    else if (tab === 'saved-jobs') renderSavedJobs();
    else if (tab === 'calendar') {
      if (state.allJobsCache.length === 0) fetchAllJobsForCalendar().then(() => renderCalendar());
      else renderCalendar();
    }
  }

  // ============================================================
  // Global Event Listeners
  // ============================================================
  function initGlobalListeners() {
    // Modal close
    document.getElementById('modal-close').addEventListener('click', closeJobModal);
    document.getElementById('job-modal-overlay').addEventListener('click', e => { if (e.target === e.currentTarget) closeJobModal(); });
    document.addEventListener('keydown', e => { if (e.key === 'Escape') closeJobModal(); });

    // Theme toggle
    document.getElementById('theme-toggle').addEventListener('click', () => applyTheme(state.theme === 'dark' ? 'light' : 'dark'));

    // Age calculator
    document.getElementById('age-calc-btn').addEventListener('click', checkAgeEligibility);

    // Calendar navigation
    document.getElementById('cal-prev').addEventListener('click', () => {
      state.calendarMonth--;
      if (state.calendarMonth < 0) { state.calendarMonth = 11; state.calendarYear--; }
      renderCalendar();
    });
    document.getElementById('cal-next').addEventListener('click', () => {
      state.calendarMonth++;
      if (state.calendarMonth > 11) { state.calendarMonth = 0; state.calendarYear++; }
      renderCalendar();
    });

    // Close share popups on outside click
    document.addEventListener('click', () => document.querySelectorAll('.share-popup.visible').forEach(p => p.classList.remove('visible')));
  }

  // ============================================================
  // Initialize
  // ============================================================
  async function init() {
    applyTheme(state.theme);
    updateSavedBadge();
    initTabs();
    initFilters();
    initBackToTop();
    initGlobalListeners();
    await Promise.all([fetchStats(), fetchITJobs(), fetchAllJobsForCalendar()]);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
