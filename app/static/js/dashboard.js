document.addEventListener("DOMContentLoaded", () => {
    // --- TAB SWITCHING LOGIC ---
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    function switchTab(targetId) {
        // Update URL
        const url = new URL(window.location);
        url.searchParams.set('tab', targetId);
        window.history.pushState({}, '', url);

        // Update buttons
        tabBtns.forEach(btn => {
            if (btn.dataset.target === targetId) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });

        // Update content
        tabContents.forEach(content => {
            if (content.id === targetId) {
                content.classList.add('active');
            } else {
                content.classList.remove('active');
            }
        });

        // Trigger tab-specific initialization
        if (targetId === 'api-docs' && !window.swaggerInitialized) {
            initSwagger();
        }
        if (targetId === 'dashboard' && !window.dashboardInitialized) {
            initDashboard();
        }
        if (targetId === 'overview' && !window.countersAnimated) {
            animateCounters();
        }
    }

    // Handle button clicks
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.target));
    });

    // Handle initial URL param
    const urlParams = new URLSearchParams(window.location.search);
    const initialTab = urlParams.get('tab');
    if (initialTab && document.getElementById(initialTab)) {
        switchTab(initialTab);
    } else {
        animateCounters(); // animate default tab (overview)
    }

    // --- OVERVIEW ANIMATIONS ---
    function animateCounters() {
        const counters = document.querySelectorAll('.counter');
        counters.forEach(counter => {
            const target = +counter.getAttribute('data-target');
            const duration = 1500; // ms
            const stepTime = Math.abs(Math.floor(duration / (target || 1)));
            let current = 0;

            if (target === 0) return;

            const timer = setInterval(() => {
                current += Math.ceil(target / 50);
                if (current >= target) {
                    counter.innerText = target;
                    clearInterval(timer);
                } else {
                    counter.innerText = current;
                }
            }, stepTime);
        });
        window.countersAnimated = true;
    }

    // --- API DOCS LOGIC ---
    const docToggles = document.querySelectorAll('.doc-toggle-btn');
    const swaggerContainer = document.getElementById('swagger-ui-container');
    const redocContainer = document.getElementById('redoc-container');

    docToggles.forEach(btn => {
        btn.addEventListener('click', () => {
            docToggles.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            if (btn.dataset.doc === 'swagger') {
                swaggerContainer.style.display = 'block';
                redocContainer.style.display = 'none';
            } else {
                swaggerContainer.style.display = 'none';
                redocContainer.style.display = 'block';
                if (!window.redocInitialized) {
                    initRedoc();
                }
            }
        });
    });

    function initSwagger() {
        if (window.SwaggerUIBundle) {
            const ui = SwaggerUIBundle({
                url: "/openapi.json",
                dom_id: '#swagger-ui-container',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIBundle.SwaggerUIStandalonePreset
                ],
                layout: "BaseLayout",
            });
            window.swaggerInitialized = true;
        }
    }

    function initRedoc() {
        if (window.Redoc) {
            Redoc.init('/openapi.json', {
                theme: {
                    colors: { primary: { main: '#6C63FF' } },
                    typography: { fontFamily: 'Inter, sans-serif' }
                }
            }, document.getElementById('redoc-container'));
            window.redocInitialized = true;
        }
    }

    // --- DASHBOARD LOGIC ---
    async function initDashboard() {
        window.dashboardInitialized = true;
        try {
            const response = await fetch('/api/reviews');
            const data = await response.json();
            
            // Populate summary
            document.getElementById('dash-total-reviews').innerText = data.length;
            
            let critical = 0;
            let suggestions = 0;
            const dates = {};
            
            const tbody = document.querySelector('#reviews-table tbody');
            tbody.innerHTML = '';
            
            data.forEach(review => {
                // Table row
                const tr = document.createElement('tr');
                const badgeClass = review.decision === 'APPROVED' || review.decision === 'COMMENT' ? 'approved' : 'request_changes';
                const decisionText = review.decision || 'COMMENT';
                
                tr.innerHTML = `
                    <td>#${review.pr_number}</td>
                    <td>${review.owner}/${review.repo}</td>
                    <td>${new Date(review.created_at).toLocaleDateString()}</td>
                    <td>${review.total_issues}</td>
                    <td><span class="status-badge ${badgeClass.toLowerCase()}">${decisionText}</span></td>
                `;
                tbody.appendChild(tr);
                
                // Stats processing
                if (review.decision === 'REQUEST_CHANGES') critical++;
                suggestions += review.total_issues;
                
                const d = new Date(review.created_at).toLocaleDateString();
                dates[d] = (dates[d] || 0) + 1;
            });
            
            document.getElementById('dash-critical-issues').innerText = critical;
            document.getElementById('dash-suggestions').innerText = suggestions;
            
            // Chart.js
            const ctx = document.getElementById('reviewsChart').getContext('2d');
            const labels = Object.keys(dates).reverse();
            const values = Object.values(dates).reverse();
            
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels.length ? labels : ['No Data'],
                    datasets: [{
                        label: 'Reviews per Day',
                        data: values.length ? values : [0],
                        backgroundColor: '#6C63FF',
                        borderRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: { beginAtZero: true, ticks: { color: '#8b949e' }, grid: { color: '#30363d' } },
                        x: { ticks: { color: '#8b949e' }, grid: { display: false } }
                    },
                    plugins: {
                        legend: { labels: { color: '#c9d1d9' } }
                    }
                }
            });
        } catch (e) {
            console.error("Failed to load dashboard data", e);
        }
    }

    // --- DEMO LOGIC ---
    const runDemoBtn = document.getElementById('run-demo-btn');
    const demoStatus = document.getElementById('demo-status');
    const demoResult = document.getElementById('demo-result');

    if (runDemoBtn) {
        runDemoBtn.addEventListener('click', () => {
            runDemoBtn.disabled = true;
            demoResult.classList.add('hidden');
            demoResult.innerHTML = '';
            
            demoStatus.innerText = 'Fetching diff...';
            demoStatus.style.color = 'var(--text-muted)';
            
            setTimeout(() => {
                demoStatus.innerText = 'Running flake8 static analysis...';
                
                setTimeout(() => {
                    demoStatus.innerText = 'Gemini AI is analyzing the code...';
                    
                    setTimeout(() => {
                        demoStatus.innerText = 'Review complete!';
                        demoStatus.style.color = 'var(--success)';
                        
                        demoResult.classList.remove('hidden');
                        demoResult.innerHTML = `
                            <div class="ai-comment">
                                <strong>Gemini Suggestion (Line 2-5):</strong>
                                <p>Great job refactoring the loop into a sum() comprehension! This is much more Pythonic and efficient.</p>
                            </div>
                            <div class="ai-comment" style="border-left-color: var(--warning)">
                                <strong>Warning (Line 5):</strong>
                                <p>Creating a list comprehension inside sum() builds the entire list in memory first. You can use a generator expression instead by removing the square brackets: <code>return sum(item.price for item in items)</code></p>
                            </div>
                        `;
                        runDemoBtn.disabled = false;
                        runDemoBtn.innerText = 'Run Again';
                    }, 2000);
                }, 1500);
            }, 1000);
        });
    }
});
