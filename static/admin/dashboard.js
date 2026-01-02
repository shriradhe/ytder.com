// Global variables
let token = '';
let quillEditor = null;
let trafficChart = null;
let monthlyChart = null;
let dailyChart = null;
let currentPage = null;
let currentSection = null;

// Check authentication on page load
document.addEventListener('DOMContentLoaded', () => {
    token = localStorage.getItem('admin_token');
    if (!token) {
        window.location.href = '/admin';
        return;
    }

    initializeApp();
});

// Initialize application
async function initializeApp() {
    setupSidebarNavigation();
    await loadDashboardStats();
    await loadDailyTraffic();
    initializeQuill();
}

// Setup sidebar navigation
function setupSidebarNavigation() {
    // AdminLTE handles navigation, but we'll update active states
    const menuItems = document.querySelectorAll('.nav-link[data-section]');
    menuItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const section = item.getAttribute('data-section');
            switchSection(section);
        });
    });
}

// Switch between sections
async function switchSection(section) {
    // Update active menu item (AdminLTE nav)
    document.querySelectorAll('.nav-link[data-section]').forEach(item => {
        item.classList.remove('active');
        const parent = item.closest('.nav-item');
        if (parent) parent.classList.remove('menu-open');
    });
    
    const activeLink = document.querySelector(`.nav-link[data-section="${section}"]`);
    if (activeLink) {
        activeLink.classList.add('active');
        const parent = activeLink.closest('.nav-item');
        if (parent) parent.classList.add('menu-open');
    }

    // Update page title and breadcrumb
    const titles = {
        'dashboard': 'Dashboard',
        'pages': 'Pages Management',
        'home-sections': 'Home Sections',
        'news': 'Latest News',
        'analytics': 'Analytics',
        'seo': 'SEO Settings',
        'settings': 'Settings'
    };
    const title = titles[section] || 'Dashboard';
    document.getElementById('pageTitle').textContent = title;
    document.getElementById('breadcrumbActive').textContent = title;

    // Show/hide sections
    document.querySelectorAll('.content-section').forEach(sec => {
        sec.style.display = 'none';
    });
    const targetSection = document.getElementById(`${section}-section`);
    if (targetSection) {
        targetSection.style.display = 'block';
    }

    // Load section data
    switch(section) {
        case 'dashboard':
            await loadDashboardStats();
            await loadDailyTraffic();
            break;
        case 'pages':
            await loadPages();
            break;
        case 'home-sections':
            await loadHomeSections();
            initializeEmojiPicker();
            break;
        case 'news':
            await loadNews();
            break;
        case 'analytics':
            await loadAnalytics();
            break;
        case 'seo':
            await loadSeoSettings();
            break;
        case 'settings':
            await loadBackups();
            break;
    }
}

// API helper
async function apiCall(url, method = 'GET', data = null) {
    const options = {
        method,
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        }
    };

    if (data) {
        options.body = JSON.stringify(data);
    }

    const response = await fetch(url, options);
    
    if (response.status === 401) {
        localStorage.removeItem('admin_token');
        window.location.href = '/admin';
        return null;
    }

    if (!response.ok && response.status !== 204) {
        let errorMessage = 'Request failed';
        try {
            const error = await response.json();
            // Handle different error response formats
            if (error.detail) {
                errorMessage = error.detail;
            } else if (error.error) {
                errorMessage = error.error;
            } else if (error.message) {
                errorMessage = error.message;
            } else if (Array.isArray(error)) {
                // Pydantic validation errors
                errorMessage = error.map(e => `${e.loc?.join('.')}: ${e.msg}`).join('; ');
            } else if (typeof error === 'string') {
                errorMessage = error;
            } else {
                errorMessage = JSON.stringify(error);
            }
        } catch (e) {
            errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        }
        throw new Error(errorMessage);
    }

    if (response.status === 204) {
        return null;
    }

    return await response.json();
}

// Dashboard Stats
async function loadDashboardStats() {
    try {
        const stats = await apiCall('/api/admin/stats/overall');
        
        const statsHTML = `
            <div class="col-lg-3 col-6">
                <div class="small-box bg-info">
                    <div class="inner">
                        <h3>${stats.total_downloads.toLocaleString()}</h3>
                        <p>Total Downloads</p>
                    </div>
                    <div class="icon">
                        <i class="fas fa-download"></i>
                    </div>
                    <a href="#" class="small-box-footer" onclick="switchSection('analytics'); return false;">
                        More info <i class="fas fa-arrow-circle-right"></i>
                    </a>
                </div>
            </div>
            <div class="col-lg-3 col-6">
                <div class="small-box bg-success">
                    <div class="inner">
                        <h3>${stats.total_page_views.toLocaleString()}</h3>
                        <p>Total Page Views</p>
                    </div>
                    <div class="icon">
                        <i class="fas fa-eye"></i>
                    </div>
                    <a href="#" class="small-box-footer" onclick="switchSection('analytics'); return false;">
                        More info <i class="fas fa-arrow-circle-right"></i>
                    </a>
                </div>
            </div>
            <div class="col-lg-3 col-6">
                <div class="small-box bg-warning">
                    <div class="inner">
                        <h3>${stats.today_downloads.toLocaleString()}</h3>
                        <p>Today's Downloads</p>
                    </div>
                    <div class="icon">
                        <i class="fas fa-arrow-down"></i>
                    </div>
                    <a href="#" class="small-box-footer" onclick="switchSection('analytics'); return false;">
                        More info <i class="fas fa-arrow-circle-right"></i>
                    </a>
                </div>
            </div>
            <div class="col-lg-3 col-6">
                <div class="small-box bg-danger">
                    <div class="inner">
                        <h3>${stats.this_month_downloads.toLocaleString()}</h3>
                        <p>This Month Downloads</p>
                    </div>
                    <div class="icon">
                        <i class="fas fa-calendar"></i>
                    </div>
                    <a href="#" class="small-box-footer" onclick="switchSection('analytics'); return false;">
                        More info <i class="fas fa-arrow-circle-right"></i>
                    </a>
                </div>
            </div>
        `;
        
        document.getElementById('statsGrid').innerHTML = statsHTML;
    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}

// Load Daily Traffic Chart
async function loadDailyTraffic() {
    try {
        const dailyStats = await apiCall('/api/admin/stats/daily?days=7');
        
        const ctx = document.getElementById('trafficChart');
        if (!ctx) return;

        if (trafficChart) {
            trafficChart.destroy();
        }

        trafficChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: dailyStats.map(d => d.date),
                datasets: [
                    {
                        label: 'Downloads',
                        data: dailyStats.map(d => d.downloads),
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102,126,234,0.1)',
                        tension: 0.4
                    },
                    {
                        label: 'Page Views',
                        data: dailyStats.map(d => d.page_views),
                        borderColor: '#4caf50',
                        backgroundColor: 'rgba(76,175,80,0.1)',
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                    }
                }
            }
        });
    } catch (error) {
        console.error('Failed to load traffic chart:', error);
    }
}

// Load Pages
async function loadPages() {
    try {
        const pages = await apiCall('/api/admin/pages');
        
        if (pages.length === 0) {
            document.getElementById('pagesTable').innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-file-alt"></i>
                    <h3>No Pages Yet</h3>
                    <p>Create your first page to get started</p>
                </div>
            `;
            return;
        }

        const tableHTML = `
            <table class="table">
                <thead>
                    <tr>
                        <th>Title</th>
                        <th>Slug</th>
                        <th>Status</th>
                        <th>Updated</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${pages.map(page => `
                        <tr>
                            <td><strong>${page.title}</strong></td>
                            <td>${page.slug}</td>
                            <td>
                                <span class="badge ${page.is_published ? 'badge-success' : 'badge-warning'}">
                                    ${page.is_published ? 'Published' : 'Draft'}
                                </span>
                            </td>
                            <td>${new Date(page.updated_at).toLocaleDateString()}</td>
                            <td>
                                <div class="action-btns">
                                    <button class="action-btn edit" onclick="editPage(${page.id})">
                                        <i class="fas fa-edit"></i> Edit
                                    </button>
                                    <button class="action-btn delete" onclick="deletePage(${page.id}, '${page.title}')">
                                        <i class="fas fa-trash"></i> Delete
                                    </button>
                                </div>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
        
        document.getElementById('pagesTable').innerHTML = tableHTML;
    } catch (error) {
        console.error('Failed to load pages:', error);
        alert('Failed to load pages: ' + error.message);
    }
}

// Initialize Quill Editor
function initializeQuill() {
    const editorElement = document.getElementById('pageEditor');
    if (editorElement && !quillEditor) {
        quillEditor = new Quill('#pageEditor', {
            theme: 'snow',
            modules: {
                toolbar: [
                    [{ 'header': [1, 2, 3, false] }],
                    ['bold', 'italic', 'underline', 'strike'],
                    ['link', 'image'],
                    [{ 'list': 'ordered'}, { 'list': 'bullet' }],
                    ['clean']
                ]
            }
        });
    }
}

// Open Page Modal
function openPageModal(pageId = null) {
    currentPage = pageId;
    const title = document.getElementById('pageModalTitle');
    const titleInput = document.getElementById('pageTitleInput');
    const slugInput = document.getElementById('pageSlug');
    
    if (pageId) {
        title.textContent = 'Edit Page';
        loadPageData(pageId);
    } else {
        title.textContent = 'Add New Page';
        document.getElementById('pageForm').reset();
        if (quillEditor) {
            quillEditor.setContents([]);
        }
        
        // Auto-generate slug from title
        titleInput.addEventListener('input', function() {
            if (!slugInput.value || slugInput.dataset.autoGenerated === 'true') {
                slugInput.value = sanitizeSlug(titleInput.value);
                slugInput.dataset.autoGenerated = 'true';
            }
        });
        
        // Clear auto-generated flag when user manually edits slug
        slugInput.addEventListener('input', function() {
            slugInput.dataset.autoGenerated = 'false';
        });
    }
    
    $('#pageModal').modal('show');
}

// Close Page Modal
function closePageModal() {
    $('#pageModal').modal('hide');
    currentPage = null;
    // Reset form
    document.getElementById('pageForm').reset();
    if (quillEditor) {
        quillEditor.setContents([]);
    }
}

// Load Page Data
async function loadPageData(pageId) {
    try {
        const page = await apiCall(`/api/admin/pages/${pageId}`);
        
        document.getElementById('pageId').value = page.id;
        document.getElementById('pageTitleInput').value = page.title;
        document.getElementById('pageSlug').value = page.slug;
        document.getElementById('pageSlug').dataset.autoGenerated = 'false';
        document.getElementById('pagePublished').checked = page.is_published;
        
        if (quillEditor) {
            quillEditor.root.innerHTML = page.content;
        }
    } catch (error) {
        console.error('Failed to load page:', error);
        const errorMessage = error instanceof Error ? error.message : String(error);
        alert('Failed to load page: ' + errorMessage);
    }
}

// Sanitize slug (make it URL-friendly)
function sanitizeSlug(text) {
    return text
        .toLowerCase()
        .trim()
        .replace(/[^a-z0-9\s-]/g, '')  // Remove special characters
        .replace(/\s+/g, '-')           // Replace spaces with hyphens
        .replace(/-+/g, '-')            // Replace multiple hyphens with single
        .replace(/^-|-$/g, '');         // Remove leading/trailing hyphens
}

// Save Page
async function savePage(event) {
    event.preventDefault();
    
    const pageId = document.getElementById('pageId').value;
    let title = document.getElementById('pageTitleInput').value.trim();
    let slug = document.getElementById('pageSlug').value.trim();
    const content = quillEditor ? quillEditor.root.innerHTML : '';
    const is_published = document.getElementById('pagePublished').checked;
    
    // Validation
    if (!title) {
        alert('Please enter a page title');
        return;
    }
    
    if (!slug) {
        // Auto-generate slug from title if not provided
        slug = sanitizeSlug(title);
        document.getElementById('pageSlug').value = slug;
    } else {
        // Sanitize the slug
        slug = sanitizeSlug(slug);
        document.getElementById('pageSlug').value = slug;
    }
    
    if (!content || content === '<p><br></p>' || content.trim() === '') {
        alert('Please enter page content');
        return;
    }
    
    // Validate slug length
    if (slug.length > 100) {
        alert('Slug is too long (max 100 characters). Please use a shorter slug.');
        return;
    }
    
    if (slug.length < 1) {
        alert('Please enter a valid page slug');
        return;
    }
    
    const pageData = {
        title,
        slug,
        content,
        is_published
    };
    
    try {
        if (pageId) {
            await apiCall(`/api/admin/pages/${pageId}`, 'PUT', pageData);
        } else {
            await apiCall('/api/admin/pages', 'POST', pageData);
        }
        
        closePageModal();
        await loadPages();
        alert('Page saved successfully!');
    } catch (error) {
        console.error('Failed to save page:', error);
        let errorMessage = 'Unknown error occurred';
        
        if (error instanceof Error) {
            errorMessage = error.message;
        } else if (typeof error === 'string') {
            errorMessage = error;
        } else if (error && error.toString) {
            errorMessage = error.toString();
        }
        
        alert('Failed to save page: ' + errorMessage);
    }
}

// Edit Page
async function editPage(pageId) {
    openPageModal(pageId);
}

// Delete Page
async function deletePage(pageId, title) {
    if (!confirm(`Are you sure you want to delete "${title}"?`)) {
        return;
    }
    
    try {
        await apiCall(`/api/admin/pages/${pageId}`, 'DELETE');
        await loadPages();
        alert('Page deleted successfully!');
    } catch (error) {
        console.error('Failed to delete page:', error);
        alert('Failed to delete page: ' + error.message);
    }
}

// Load Home Sections
async function loadHomeSections() {
    try {
        const sections = await apiCall('/api/admin/home-sections');
        
        if (sections.length === 0) {
            document.getElementById('sectionsTable').innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-th-large"></i>
                    <h3>No Sections Yet</h3>
                    <p>Create your first home section to get started</p>
                </div>
            `;
            return;
        }

        const tableHTML = `
            <div class="table-responsive">
                <table class="table table-bordered table-striped table-hover">
                    <thead>
                        <tr>
                            <th style="width: 80px;" class="text-center">Icon</th>
                            <th>Title</th>
                            <th style="width: 80px;" class="text-center">Order</th>
                            <th style="width: 100px;" class="text-center">Status</th>
                            <th style="width: 150px;" class="text-center">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${sections.map(section => `
                            <tr>
                                <td class="text-center" style="font-size: 24px;">${section.icon}</td>
                                <td>
                                    <strong>${section.title}</strong><br>
                                    <small class="text-muted">${section.description.substring(0, 60)}${section.description.length > 60 ? '...' : ''}</small>
                                </td>
                                <td class="text-center">${section.order}</td>
                                <td class="text-center">
                                    <span class="badge ${section.is_active ? 'badge-success' : 'badge-warning'}">
                                        ${section.is_active ? 'Active' : 'Inactive'}
                                    </span>
                                </td>
                                <td class="text-center">
                                    <button class="btn btn-sm btn-primary" onclick="editSection(${section.id})" title="Edit">
                                        <i class="fas fa-edit"></i>
                                    </button>
                                    <button class="btn btn-sm btn-danger" onclick="deleteSection(${section.id}, '${section.title}')" title="Delete">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
        
        document.getElementById('sectionsTable').innerHTML = tableHTML;
    } catch (error) {
        console.error('Failed to load sections:', error);
        alert('Failed to load sections: ' + error.message);
    }
}

// Initialize Emoji Picker
function initializeEmojiPicker() {
    const emojiGrid = document.getElementById('emojiPickerGrid');
    if (!emojiGrid) return;
    
    // Popular emojis for home sections
    const emojis = [
        '🎬', '⚡', '🎯', '🚀', '💎', '⭐', '🔥', '💪',
        '🎨', '🎵', '📱', '💻', '🌐', '🔒', '📊', '🎁',
        '🏆', '✨', '🌟', '💡', '🎪', '🎭', '🎮', '📸',
        '🎥', '🎤', '🎧', '📺', '📻', '🎙️', '🎚️', '🎛️',
        '🎞️', '📽️', '📹', '📷', '🔍', '📡', '📢', '📣',
        '🔔', '🔕', '📯', '📮', '📬', '📭', '📪', '📫',
        '💌', '📧', '📨', '📩', '📤', '📥', '📦', '📯'
    ];
    
    emojiGrid.innerHTML = emojis.map(emoji => 
        `<div class="emoji-item" onclick="selectEmoji('${emoji}')">${emoji}</div>`
    ).join('');
}

// Select Emoji
function selectEmoji(emoji) {
    const iconInput = document.getElementById('sectionIcon');
    if (iconInput) {
        iconInput.value = emoji;
    }
}

// Open Section Modal
function openSectionModal(sectionId = null) {
    currentSection = sectionId;
    const title = document.getElementById('sectionModalTitle');
    
    // Initialize emoji picker if not already done
    if (!document.getElementById('emojiPickerGrid').innerHTML) {
        initializeEmojiPicker();
    }
    
    if (sectionId) {
        title.textContent = 'Edit Section';
        loadSectionData(sectionId);
    } else {
        title.textContent = 'Add New Section';
        document.getElementById('sectionForm').reset();
        document.getElementById('sectionOrder').value = '0';
        document.getElementById('sectionActive').checked = true;
        document.getElementById('sectionLink').value = ''; // Clear link field
    }
    
    $('#sectionModal').modal('show');
}

// Close Section Modal
function closeSectionModal() {
    $('#sectionModal').modal('hide');
    currentSection = null;
    // Reset form
    document.getElementById('sectionForm').reset();
}

// Load Section Data
async function loadSectionData(sectionId) {
    try {
        const section = await apiCall(`/api/admin/home-sections/${sectionId}`);
        
        document.getElementById('sectionId').value = section.id;
        document.getElementById('sectionTitle').value = section.title;
        
        // Parse link from description if it exists (format: __LINK__url__LINK__)
        let description = section.description || '';
        let link = '';
        const linkMatch = description.match(/__LINK__(.+?)__LINK__/);
        if (linkMatch) {
            link = linkMatch[1];
            description = description.replace(/__LINK__.+?__LINK__/g, '').trim();
        }
        
        document.getElementById('sectionDescription').value = description;
        document.getElementById('sectionLink').value = link;
        document.getElementById('sectionIcon').value = section.icon;
        document.getElementById('sectionOrder').value = section.order;
        document.getElementById('sectionActive').checked = section.is_active;
    } catch (error) {
        console.error('Failed to load section:', error);
        alert('Failed to load section: ' + error.message);
    }
}

// Save Section
async function saveSection(event) {
    event.preventDefault();
    
    const sectionId = document.getElementById('sectionId').value;
    const title = document.getElementById('sectionTitle').value;
    let description = document.getElementById('sectionDescription').value;
    const link = document.getElementById('sectionLink').value.trim();
    const icon = document.getElementById('sectionIcon').value;
    const order = parseInt(document.getElementById('sectionOrder').value);
    const is_active = document.getElementById('sectionActive').checked;
    
    // Store link in description with special marker (frontend-only storage)
    // Remove old link marker if exists
    description = description.replace(/__LINK__.+\?__LINK__/g, '').trim();
    // Append link if provided
    if (link) {
        description += ` __LINK__${link}__LINK__`;
    }
    
    const sectionData = {
        title,
        description,
        icon,
        order,
        is_active
    };
    
    try {
        if (sectionId) {
            await apiCall(`/api/admin/home-sections/${sectionId}`, 'PUT', sectionData);
        } else {
            await apiCall('/api/admin/home-sections', 'POST', sectionData);
        }
        
        closeSectionModal();
        await loadHomeSections();
        alert('Section saved successfully!');
    } catch (error) {
        console.error('Failed to save section:', error);
        alert('Failed to save section: ' + error.message);
    }
}

// Edit Section
async function editSection(sectionId) {
    openSectionModal(sectionId);
}

// Delete Section
async function deleteSection(sectionId, title) {
    if (!confirm(`Are you sure you want to delete "${title}"?`)) {
        return;
    }
    
    try {
        await apiCall(`/api/admin/home-sections/${sectionId}`, 'DELETE');
        await loadHomeSections();
        alert('Section deleted successfully!');
    } catch (error) {
        console.error('Failed to delete section:', error);
        alert('Failed to delete section: ' + error.message);
    }
}

// Load Analytics
async function loadAnalytics() {
    try {
        // Load monthly stats
        const monthlyStats = await apiCall('/api/admin/stats/monthly?months=6');
        
        const ctx1 = document.getElementById('monthlyChart');
        if (ctx1) {
            if (monthlyChart) {
                monthlyChart.destroy();
            }

            // Color palette for doughnut chart
            const colorPalette = [
                '#667eea', // Purple
                '#764ba2', // Dark Purple
                '#f093fb', // Pink
                '#4facfe', // Blue
                '#00f2fe', // Cyan
                '#43e97b', // Green
                '#fa709a', // Rose
                '#fee140', // Yellow
                '#30cfd0', // Teal
                '#a8edea', // Light Teal
                '#ff9a9e', // Coral
                '#fecfef'  // Light Pink
            ];

            // Prepare data for doughnut chart - showing total activity per month
            const labels = monthlyStats.map(d => d.month);
            const totalData = monthlyStats.map(d => d.downloads + d.page_views);
            const downloadData = monthlyStats.map(d => d.downloads);
            const pageViewData = monthlyStats.map(d => d.page_views);

            monthlyChart = new Chart(ctx1, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'Total Activity (Downloads + Page Views)',
                            data: totalData,
                            backgroundColor: colorPalette.slice(0, labels.length),
                            borderColor: '#ffffff',
                            borderWidth: 2,
                            hoverOffset: 4
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'right',
                            labels: {
                                padding: 15,
                                usePointStyle: true,
                                font: {
                                    size: 12
                                }
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const index = context.dataIndex;
                                    const month = labels[index];
                                    const downloads = downloadData[index];
                                    const pageViews = pageViewData[index];
                                    const total = totalData[index];
                                    return [
                                        `${month}:`,
                                        `Total: ${total}`,
                                        `Downloads: ${downloads}`,
                                        `Page Views: ${pageViews}`
                                    ];
                                }
                            }
                        }
                    }
                }
            });
        }

        // Load daily stats
        const dailyStats = await apiCall('/api/admin/stats/daily?days=30');
        
        const ctx2 = document.getElementById('dailyChart');
        if (ctx2) {
            if (dailyChart) {
                dailyChart.destroy();
            }

            dailyChart = new Chart(ctx2, {
                type: 'line',
                data: {
                    labels: dailyStats.map(d => d.date),
                    datasets: [
                        {
                            label: 'Downloads',
                            data: dailyStats.map(d => d.downloads),
                            borderColor: '#667eea',
                            backgroundColor: 'rgba(102,126,234,0.1)',
                            tension: 0.4,
                            fill: true
                        },
                        {
                            label: 'Page Views',
                            data: dailyStats.map(d => d.page_views),
                            borderColor: '#4caf50',
                            backgroundColor: 'rgba(76,175,80,0.1)',
                            tension: 0.4,
                            fill: true
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top',
                        }
                    }
                }
            });
        }
    } catch (error) {
        console.error('Failed to load analytics:', error);
    }
}

// Change Password
async function changePassword(event) {
    event.preventDefault();
    
    const oldPassword = document.getElementById('oldPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    
    try {
        await apiCall('/api/admin/change-password', 'POST', {
            old_password: oldPassword,
            new_password: newPassword
        });
        
        document.getElementById('passwordForm').reset();
        alert('Password changed successfully!');
    } catch (error) {
        console.error('Failed to change password:', error);
        alert('Failed to change password: ' + error.message);
    }
}

// Create Backup
async function createBackup() {
    if (!confirm('Create a database backup?')) {
        return;
    }
    
    try {
        const result = await apiCall('/api/admin/database/backup', 'POST');
        alert(`Backup created successfully!\nFile: ${result.filename}\nSize: ${(result.size / 1024).toFixed(2)} KB`);
        await loadBackups();
    } catch (error) {
        console.error('Failed to create backup:', error);
        alert('Failed to create backup: ' + error.message);
    }
}

// Load Backups
async function loadBackups() {
    try {
        const result = await apiCall('/api/admin/database/backups');
        const backups = result.backups || [];
        
        if (backups.length === 0) {
            document.getElementById('backupsList').innerHTML = `
                <p style="color: #999; text-align: center;">No backups found</p>
            `;
            return;
        }

        const tableHTML = `
            <h4 style="margin-bottom: 15px;">Available Backups</h4>
            <table class="table">
                <thead>
                    <tr>
                        <th>Filename</th>
                        <th>Size</th>
                        <th>Created</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${backups.map(backup => `
                        <tr>
                            <td><i class="fas fa-database"></i> ${backup.filename}</td>
                            <td>${(backup.size / 1024).toFixed(2)} KB</td>
                            <td>${new Date(backup.created_at).toLocaleString()}</td>
                            <td>
                                <button class="btn btn-warning btn-sm" onclick="restoreBackup('${backup.filename}')" title="Restore this backup">
                                    <i class="fas fa-undo"></i> Restore
                                </button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
        
        document.getElementById('backupsList').innerHTML = tableHTML;
    } catch (error) {
        console.error('Failed to load backups:', error);
    }
}

// Restore Backup
async function restoreBackup(filename) {
    const confirmMessage = `⚠️ WARNING: This will replace your current database with the backup!\n\n` +
                          `Backup file: ${filename}\n\n` +
                          `A safety backup of your current database will be created automatically.\n\n` +
                          `Are you absolutely sure you want to restore this backup?\n\n` +
                          `You will need to restart the application after restoring.`;
    
    if (!confirm(confirmMessage)) {
        return;
    }
    
    // Double confirmation for safety
    if (!confirm('This is your last chance to cancel. Proceed with restore?')) {
        return;
    }
    
    try {
        const result = await apiCall('/api/admin/database/restore', 'POST', { backup_filename: filename });
        alert(`✅ Database restored successfully!\n\n` +
              `Backup: ${result.backup_filename}\n` +
              `Size: ${(result.size / 1024).toFixed(2)} KB\n\n` +
              `⚠️ IMPORTANT: Please restart the application for changes to take effect.`);
        
        // Reload backups list
        await loadBackups();
    } catch (error) {
        console.error('Failed to restore backup:', error);
        let errorMsg = 'Failed to restore backup: ' + error.message;
        if (error.message.includes('403') || error.message.includes('super admin')) {
            errorMsg = '❌ Only Super Admins can restore the database.';
        }
        alert(errorMsg);
    }
}

// SEO Management Functions
async function loadSeoSettings() {
    try {
        const seo = await apiCall('/api/admin/seo');
        
        if (!seo) {
            // If no SEO settings, use defaults
            document.getElementById('seoPageTitle').value = 'Video Downloader - Download HD Videos from Any Platform';
            document.getElementById('seoMetaDescription').value = 'Download high-quality videos from YouTube, Instagram, TikTok, Facebook, Twitter, and more.';
            document.getElementById('seoMetaKeywords').value = 'video downloader, youtube downloader, instagram downloader';
            document.getElementById('seoRobots').value = 'index, follow';
            document.getElementById('seoTwitterCard').value = 'summary_large_image';
            document.getElementById('seoIsActive').checked = true;
            return;
        }
        
        document.getElementById('seoPageTitle').value = seo.page_title || '';
        document.getElementById('seoMetaDescription').value = seo.meta_description || '';
        document.getElementById('seoMetaKeywords').value = seo.meta_keywords || '';
        document.getElementById('seoOgTitle').value = seo.og_title || '';
        document.getElementById('seoOgDescription').value = seo.og_description || '';
        document.getElementById('seoOgImage').value = seo.og_image || '';
        document.getElementById('seoOgUrl').value = seo.og_url || '';
        document.getElementById('seoTwitterCard').value = seo.twitter_card || 'summary_large_image';
        document.getElementById('seoTwitterTitle').value = seo.twitter_title || '';
        document.getElementById('seoTwitterDescription').value = seo.twitter_description || '';
        document.getElementById('seoTwitterImage').value = seo.twitter_image || '';
        document.getElementById('seoCanonicalUrl').value = seo.canonical_url || '';
        document.getElementById('seoRobots').value = seo.robots || 'index, follow';
        document.getElementById('seoIsActive').checked = seo.is_active !== false;
    } catch (error) {
        console.error('Failed to load SEO settings:', error);
        // Use default values on error
        document.getElementById('seoPageTitle').value = 'Video Downloader - Download HD Videos from Any Platform';
        document.getElementById('seoMetaDescription').value = 'Download high-quality videos from YouTube, Instagram, TikTok, Facebook, Twitter, and more.';
        document.getElementById('seoMetaKeywords').value = 'video downloader, youtube downloader, instagram downloader';
        document.getElementById('seoRobots').value = 'index, follow';
        document.getElementById('seoTwitterCard').value = 'summary_large_image';
        document.getElementById('seoIsActive').checked = true;
        
        // Show warning but don't block the user
        console.warn('Using default SEO values. You can still save new settings.');
    }
}

async function saveSeoSettings(event) {
    event.preventDefault();
    
    try {
        const seoData = {
            page_title: document.getElementById('seoPageTitle').value.trim(),
            meta_description: document.getElementById('seoMetaDescription').value.trim(),
            meta_keywords: document.getElementById('seoMetaKeywords').value.trim() || null,
            og_title: document.getElementById('seoOgTitle').value.trim() || null,
            og_description: document.getElementById('seoOgDescription').value.trim() || null,
            og_image: document.getElementById('seoOgImage').value.trim() || null,
            og_url: document.getElementById('seoOgUrl').value.trim() || null,
            twitter_card: document.getElementById('seoTwitterCard').value,
            twitter_title: document.getElementById('seoTwitterTitle').value.trim() || null,
            twitter_description: document.getElementById('seoTwitterDescription').value.trim() || null,
            twitter_image: document.getElementById('seoTwitterImage').value.trim() || null,
            canonical_url: document.getElementById('seoCanonicalUrl').value.trim() || null,
            robots: document.getElementById('seoRobots').value.trim() || 'index, follow',
            is_active: document.getElementById('seoIsActive').checked
        };
        
        if (!seoData.page_title || !seoData.meta_description) {
            alert('Page title and meta description are required!');
            return;
        }
        
        await apiCall('/api/admin/seo', 'POST', seoData);
        alert('✅ SEO settings saved successfully!');
        await loadSeoSettings();
    } catch (error) {
        console.error('Failed to save SEO settings:', error);
        alert('Failed to save SEO settings: ' + error.message);
    }
}

async function loadSeoHistory() {
    try {
        const history = await apiCall('/api/admin/seo/history');
        
        if (history.length === 0) {
            alert('No SEO history found.');
            return;
        }
        
        const historyHTML = history.map(item => `
            <tr>
                <td>${item.page_title}</td>
                <td><span class="badge ${item.is_active ? 'badge-success' : 'badge-secondary'}">${item.is_active ? 'Active' : 'Inactive'}</span></td>
                <td>${new Date(item.updated_at).toLocaleString()}</td>
            </tr>
        `).join('');
        
        const modalHTML = `
            <div class="modal fade" id="seoHistoryModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h4 class="modal-title">SEO Settings History</h4>
                            <button type="button" class="close" data-dismiss="modal">
                                <span>&times;</span>
                            </button>
                        </div>
                        <div class="modal-body">
                            <div class="table-responsive">
                                <table class="table table-bordered">
                                    <thead>
                                        <tr>
                                            <th>Page Title</th>
                                            <th>Status</th>
                                            <th>Updated At</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${historyHTML}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Remove existing modal if any
        const existing = document.getElementById('seoHistoryModal');
        if (existing) existing.remove();
        
        // Add modal to body
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        $('#seoHistoryModal').modal('show');
        
        // Clean up on close
        $('#seoHistoryModal').on('hidden.bs.modal', function() {
            $(this).remove();
        });
    } catch (error) {
        console.error('Failed to load SEO history:', error);
        alert('Failed to load SEO history: ' + error.message);
    }
}

// News Management Functions
let currentNews = null;

async function loadNews() {
    try {
        const newsItems = await apiCall('/api/admin/news');
        
        if (newsItems.length === 0) {
            document.getElementById('newsTable').innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-newspaper"></i>
                    <h3>No News Items Yet</h3>
                    <p>Create your first news item to get started</p>
                </div>
            `;
            return;
        }

        const tableHTML = `
            <div class="table-responsive">
                <table class="table table-bordered table-striped table-hover">
                    <thead>
                        <tr>
                            <th>Title</th>
                            <th style="width: 120px;">Date</th>
                            <th style="width: 80px;" class="text-center">Order</th>
                            <th style="width: 100px;" class="text-center">Status</th>
                            <th style="width: 150px;" class="text-center">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${newsItems.map(item => `
                            <tr>
                                <td>
                                    <strong>${item.title}</strong><br>
                                    <small class="text-muted">${item.content.substring(0, 60)}${item.content.length > 60 ? '...' : ''}</small>
                                </td>
                                <td>${new Date(item.news_date).toLocaleDateString()}</td>
                                <td class="text-center">${item.order}</td>
                                <td class="text-center">
                                    <span class="badge ${item.is_active ? 'badge-success' : 'badge-warning'}">
                                        ${item.is_active ? 'Active' : 'Inactive'}
                                    </span>
                                </td>
                                <td class="text-center">
                                    <button class="btn btn-sm btn-primary" onclick="editNews(${item.id})" title="Edit">
                                        <i class="fas fa-edit"></i>
                                    </button>
                                    <button class="btn btn-sm btn-danger" onclick="deleteNews(${item.id}, '${item.title.replace(/'/g, "\\'")}')" title="Delete">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
        
        document.getElementById('newsTable').innerHTML = tableHTML;
    } catch (error) {
        console.error('Failed to load news:', error);
        alert('Failed to load news: ' + error.message);
    }
}

function openNewsModal(newsId = null) {
    currentNews = newsId;
    const title = document.getElementById('newsModalTitle');
    
    if (newsId) {
        title.textContent = 'Edit News';
        loadNewsData(newsId);
    } else {
        title.textContent = 'Add New News';
        document.getElementById('newsForm').reset();
        document.getElementById('newsDate').value = new Date().toISOString().split('T')[0];
        document.getElementById('newsOrder').value = '0';
        document.getElementById('newsActive').checked = true;
    }
    
    $('#newsModal').modal('show');
}

function closeNewsModal() {
    $('#newsModal').modal('hide');
    currentNews = null;
    document.getElementById('newsForm').reset();
}

async function loadNewsData(newsId) {
    try {
        const news = await apiCall(`/api/admin/news/${newsId}`);
        
        document.getElementById('newsId').value = news.id;
        document.getElementById('newsTitle').value = news.title;
        document.getElementById('newsContent').value = news.content;
        document.getElementById('newsDate').value = news.news_date;
        document.getElementById('newsOrder').value = news.order;
        document.getElementById('newsActive').checked = news.is_active;
    } catch (error) {
        console.error('Failed to load news:', error);
        alert('Failed to load news: ' + error.message);
    }
}

async function saveNews(event) {
    event.preventDefault();
    
    const newsId = document.getElementById('newsId').value;
    const title = document.getElementById('newsTitle').value;
    const content = document.getElementById('newsContent').value;
    const news_date = document.getElementById('newsDate').value;
    const order = parseInt(document.getElementById('newsOrder').value);
    const is_active = document.getElementById('newsActive').checked;
    
    const newsData = {
        title,
        content,
        news_date,
        order,
        is_active
    };
    
    try {
        if (newsId) {
            await apiCall(`/api/admin/news/${newsId}`, 'PUT', newsData);
        } else {
            await apiCall('/api/admin/news', 'POST', newsData);
        }
        
        closeNewsModal();
        await loadNews();
        alert('News saved successfully!');
    } catch (error) {
        console.error('Failed to save news:', error);
        alert('Failed to save news: ' + error.message);
    }
}

async function editNews(newsId) {
    openNewsModal(newsId);
}

async function deleteNews(newsId, title) {
    if (!confirm(`Are you sure you want to delete "${title}"?`)) {
        return;
    }
    
    try {
        await apiCall(`/api/admin/news/${newsId}`, 'DELETE');
        await loadNews();
        alert('News deleted successfully!');
    } catch (error) {
        console.error('Failed to delete news:', error);
        alert('Failed to delete news: ' + error.message);
    }
}

// Logout
function logout() {
    if (confirm('Are you sure you want to logout?')) {
        localStorage.removeItem('admin_token');
        window.location.href = '/admin';
    }
}

