// API Configuration - Auto-detect environment
const API_BASE_URL = (() => {
    // Check if running on GitHub Pages
    if (window.location.hostname.includes('github.io')) {
        // Production API URL - you'll need to replace this with your actual API domain
        return 'https://your-api-domain.herokuapp.com/api/v1';
    }
    // Local development
    return 'http://localhost:8001/api/v1';
})();

// Global variables
let currentAnalysisData = null;
let priceChart = null;
let ratingChart = null;

// DOM Elements
const elements = {
    loadingState: document.getElementById('loadingState'),
    errorState: document.getElementById('errorState'),
    mainContent: document.getElementById('mainContent'),
    groupSelect: document.getElementById('groupSelect'),
    refreshBtn: document.getElementById('refreshBtn'),
    retryBtn: document.getElementById('retryBtn'),
    errorMessage: document.getElementById('errorMessage'),
    lastUpdate: document.getElementById('lastUpdate')
};

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing Amazon Insights Dashboard...');
    
    // Check if this is a demo environment (GitHub Pages)
    const isDemoMode = window.location.hostname.includes('github.io');
    
    if (isDemoMode) {
        // Show demo mode interface
        showDemoModeInterface();
        return;
    }
    
    // Check if Chart.js is loaded
    const initWithDelay = () => {
        if (typeof Chart === 'undefined' && !window.chartReady) {
            console.warn('Chart.js not yet loaded, waiting...');
            setTimeout(initWithDelay, 200);
            return;
        }
        
        console.log('Chart.js is available, initializing app...');
        initializeApp();
    };
    
    // Start initialization with a small delay to let Chart.js load
    setTimeout(initWithDelay, 500);
    
    // Event listeners
    elements.refreshBtn.addEventListener('click', () => {
        const selectedGroupId = elements.groupSelect.value;
        if (selectedGroupId) {
            loadAnalysisData(selectedGroupId);
        } else {
            showError('Please select a competitive group first');
        }
    });
    
    elements.retryBtn.addEventListener('click', initializeApp);
    
    elements.groupSelect.addEventListener('change', function() {
        if (this.value) {
            loadAnalysisData(this.value);
        }
    });
});

// Initialize application
async function initializeApp() {
    showLoading();
    try {
        await loadCompetitiveGroups();
        
        // Auto-load first group if available
        if (elements.groupSelect.options.length > 1) {
            elements.groupSelect.selectedIndex = 1; // Select first actual group (not placeholder)
            await loadAnalysisData(elements.groupSelect.value);
        } else {
            // If no groups, show demo mode anyway for GitHub Pages
            if (window.location.hostname.includes('github.io')) {
                showDemoModeInterface();
            } else {
                showError('No competitive groups found. Please create competitive groups using the API first.');
            }
        }
    } catch (error) {
        console.error('Initialization failed:', error);
        // Always show demo mode on GitHub Pages, even if API fails
        if (window.location.hostname.includes('github.io')) {
            showDemoModeInterface();
        } else {
            showError('Initialization failed: ' + error.message);
        }
    }
}

// Load competitive groups
async function loadCompetitiveGroups() {
    try {
        const response = await fetch(`${API_BASE_URL}/competitive/groups`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const groups = await response.json();
        
        // Clear existing options except placeholder
        elements.groupSelect.innerHTML = '<option value="">Select Competitive Group...</option>';
        
        groups.forEach(group => {
            const option = document.createElement('option');
            option.value = group.id;
            option.textContent = `${group.name} (${group.competitors.length} competitors)`;
            elements.groupSelect.appendChild(option);
        });
        
        console.log(`Loaded ${groups.length} competitive groups`);
    } catch (error) {
        console.error('Failed to load groups:', error);
        
        // If on GitHub Pages, don't throw error - we'll show demo mode
        if (window.location.hostname.includes('github.io')) {
            console.log('GitHub Pages detected - will show demo mode');
            return; // Don't throw error
        }
        
        throw new Error('Failed to load competitive groups list');
    }
}

// Load analysis data
async function loadAnalysisData(groupId) {
    showLoading();
    
    try {
        console.log(`Loading analysis for group ${groupId}...`);
        const response = await fetch(`${API_BASE_URL}/competitive/groups/${groupId}/analyze?include_llm_report=true`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error(`API returned ${response.status}: ${response.statusText}`);
        }
        
        const analysisData = await response.json();
        console.log('Analysis data loaded:', analysisData);
        
        currentAnalysisData = analysisData;
        displayAnalysisResults(analysisData);
        showMainContent();
        
        elements.lastUpdate.textContent = new Date().toLocaleString('zh-TW');
        
    } catch (error) {
        console.error('Failed to load analysis:', error);
        showError(`Failed to load analysis data: ${error.message}`);
    }
}

// Display analysis results
function displayAnalysisResults(data) {
    console.log('Displaying analysis results...');
    
    // Update overview cards
    updateOverviewCards(data);
    
    // Display basic analysis
    displayPriceComparison(data);
    displayRatingAnalysis(data);
    
    // Display advanced analysis
    displayBSRAnalysis(data);
    
    // Display LLM report
    if (data.positioning_report) {
        displayLLMReport(data.positioning_report);
    } else {
        console.warn('No positioning report found in data');
    }
}

// Update overview cards
function updateOverviewCards(data) {
    const summary = data.competitive_summary || {};
    const scores = summary.competitive_scores || {};
    const positions = summary.position_summary || {};
    
    // Price competitiveness
    document.getElementById('priceScore').textContent = formatScore(scores.price_competitiveness);
    document.getElementById('pricePosition').textContent = formatPosition(positions.price_position);
    
    // Quality competitiveness
    document.getElementById('qualityScore').textContent = formatScore(scores.quality_competitiveness);
    document.getElementById('qualityPosition').textContent = formatPosition(positions.quality_position);
    
    // Popularity competitiveness
    document.getElementById('popularityScore').textContent = formatScore(scores.popularity_competitiveness);
    document.getElementById('popularityPosition').textContent = formatPosition(positions.popularity_position);
    
    // Overall competitiveness
    document.getElementById('overallScore').textContent = formatScore(scores.overall_competitiveness);
    document.getElementById('overallPosition').textContent = formatPosition(positions.overall_position);
}

// Display price comparison
function displayPriceComparison(data) {
    const mainProduct = data.main_product || {};
    const competitors = data.competitors || [];
    const priceAnalysis = data.price_analysis || {};
    
    // Update main product info
    document.getElementById('mainProductTitle').textContent = 
        mainProduct.title ? mainProduct.title.substring(0, 50) + '...' : 'Main Product';
    document.getElementById('mainPrice').textContent = 
        mainProduct.price ? `$${mainProduct.price}` : '$--';
    
    // Update competitors prices
    const competitorsPricesDiv = document.getElementById('competitorsPrices');
    competitorsPricesDiv.innerHTML = '';
    
    competitors.forEach((competitor, index) => {
        const competitorDiv = document.createElement('div');
        competitorDiv.className = 'competitor-item';
        competitorDiv.innerHTML = `
            <div>
                <strong>${competitor.competitor_name || `Competitor ${index + 1}`}</strong>
                <div style="font-size: 0.9em; color: #666;">
                    ${competitor.title ? competitor.title.substring(0, 40) + '...' : ''}
                </div>
            </div>
            <div class="competitor-price">$${competitor.price || '--'}</div>
        `;
        competitorsPricesDiv.appendChild(competitorDiv);
    });
    
    // Create price chart
    createPriceChart(data);
}

// Create price chart
function createPriceChart(data) {
    // Check if Chart.js is available
    if (typeof Chart === 'undefined') {
        console.error('Chart.js is not available, skipping price chart creation');
        const chartContainer = document.getElementById('priceChart').parentElement;
        chartContainer.innerHTML = '<p style="text-align: center; color: #999; padding: 40px;">Chart functionality temporarily unavailable. Please refresh the page.</p>';
        return;
    }
    
    const ctx = document.getElementById('priceChart');
    if (!ctx) {
        console.error('Price chart canvas not found');
        return;
    }
    
    try {
        if (priceChart) {
            priceChart.destroy();
        }
        
        const mainProduct = data.main_product || {};
        const competitors = data.competitors || [];
        
        const labels = ['Main Product', ...competitors.map((c, i) => c.competitor_name || `Competitor ${i + 1}`)];
        const prices = [mainProduct.price || 0, ...competitors.map(c => c.price || 0)];
        const colors = ['#2ecc71', ...competitors.map(() => '#3498db')];
        
        priceChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Price ($)',
                data: prices,
                backgroundColor: colors,
                borderColor: colors,
                borderWidth: 2,
                borderRadius: 8,
                borderSkipped: false,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0,0,0,0.1)'
                    },
                    ticks: {
                        callback: function(value) {
                            return '$' + value;
                        }
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
        
    } catch (error) {
        console.error('Error creating price chart:', error);
        const chartContainer = document.getElementById('priceChart').parentElement;
        chartContainer.innerHTML = '<p style="text-align: center; color: #e74c3c; padding: 40px;">Failed to load price chart</p>';
    }
}

// Display rating analysis
function displayRatingAnalysis(data) {
    const mainProduct = data.main_product || {};
    const competitors = data.competitors || [];
    const ratingAnalysis = data.rating_analysis || {};
    
    // Check if Chart.js is available and create rating chart
    if (typeof Chart !== 'undefined') {
        try {
            const ctx = document.getElementById('ratingChart');
            
            if (ratingChart) {
                ratingChart.destroy();
            }
            
            const labels = ['Main Product', ...competitors.map((c, i) => c.competitor_name || `Competitor ${i + 1}`)];
            const ratings = [mainProduct.rating || 0, ...competitors.map(c => c.rating || 0)];
            const reviews = [mainProduct.review_count || 0, ...competitors.map(c => c.review_count || 0)];
            
            ratingChart = new Chart(ctx, {
        type: 'bubble',
        data: {
            datasets: [{
                label: 'Rating Performance',
                data: ratings.map((rating, index) => ({
                    x: rating,
                    y: Math.log10(reviews[index] + 1), // Log scale for reviews
                    r: Math.min(Math.sqrt(reviews[index] / 100), 30) // Bubble size
                })),
                backgroundColor: ['rgba(46, 204, 113, 0.6)', ...competitors.map(() => 'rgba(52, 152, 219, 0.6)')],
                borderColor: ['#2ecc71', ...competitors.map(() => '#3498db')],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const index = context.dataIndex;
                            return `${labels[index]}: ${ratings[index]}⭐ (${reviews[index].toLocaleString()} reviews)`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Rating'
                    },
                    min: 0,
                    max: 5
                },
                y: {
                    title: {
                        display: true,
                        text: 'Review Count (Log Scale)'
                    },
                    ticks: {
                        callback: function(value) {
                            return Math.round(Math.pow(10, value)).toLocaleString();
                        }
                    }
                }
            }
        }
    });
        
        } catch (error) {
            console.error('Error creating rating chart:', error);
            const chartContainer = document.getElementById('ratingChart').parentElement;
            chartContainer.innerHTML = '<p style="text-align: center; color: #e74c3c; padding: 40px;">Failed to load rating chart</p>';
        }
    } else {
        console.error('Chart.js not available for rating chart');
        const chartContainer = document.getElementById('ratingChart').parentElement;
        chartContainer.innerHTML = '<p style="text-align: center; color: #999; padding: 40px;">Chart functionality temporarily unavailable</p>';
    }
    
    // Display rating statistics
    const ratingStats = document.getElementById('ratingStats');
    const stats = ratingAnalysis.rating_statistics || {};
    
    ratingStats.innerHTML = `
        <div class="rating-stat">
            <h4>Market Average Rating</h4>
            <div class="rating-value">${stats.average || '--'}⭐</div>
        </div>
        <div class="rating-stat">
            <h4>Rating Range</h4>
            <div class="rating-value">${stats.min || '--'} - ${stats.max || '--'}</div>
        </div>
        <div class="rating-stat">
            <h4>Main Product Position</h4>
            <div class="rating-value">${formatPosition(stats.main_product_position)}</div>
        </div>
    `;
}


// Display BSR analysis
function displayBSRAnalysis(data) {
    const bsrAnalysis = data.bsr_analysis || {};
    const bsrDiv = document.getElementById('bsrAnalysis');
    
    if (Object.keys(bsrAnalysis).length === 0 || bsrAnalysis.error) {
        bsrDiv.innerHTML = '<p>No Amazon ranking data available</p>';
        return;
    }
    
    bsrDiv.innerHTML = '';
    
    Object.entries(bsrAnalysis).forEach(([category, data]) => {
        const categoryDiv = document.createElement('div');
        categoryDiv.className = 'bsr-category';
        
        const position = data.position || 'unknown';
        const positionClass = `position-${position}`;
        const stats = data.rank_statistics || {};
        
        categoryDiv.innerHTML = `
            <h4>${category.replace(/[\[\]]/g, '')}</h4>
            <div class="bsr-info">
                <div class="bsr-metric">
                    <div class="label">Main Product Rank</div>
                    <div class="value ${positionClass}">#${data.main_product_rank || '--'}</div>
                </div>
                <div class="bsr-metric">
                    <div class="label">Market Position</div>
                    <div class="value ${positionClass}">${formatPosition(position)}</div>
                </div>
                <div class="bsr-metric">
                    <div class="label">Best Rank</div>
                    <div class="value">#${stats.best_rank || '--'}</div>
                </div>
                <div class="bsr-metric">
                    <div class="label">Average Rank</div>
                    <div class="value">#${stats.average_rank || '--'}</div>
                </div>
            </div>
        `;
        
        bsrDiv.appendChild(categoryDiv);
    });
}

// Display LLM report
function displayLLMReport(report) {
    console.log('Displaying LLM report:', report);
    
    // Executive summary
    const executiveSummary = document.getElementById('executiveSummary');
    executiveSummary.textContent = report.executive_summary || 'No executive summary available';
    
    // SWOT Analysis
    displaySWOTAnalysis(report.strengths_weaknesses || {});
    
    // Strategic actions
    displayStrategicActions(report.strategic_recommendations || []);
    
    // Market insights
    displayMarketInsights(report.market_insights || {});
}

// Display SWOT analysis
function displaySWOTAnalysis(swot) {
    const sections = {
        swotStrengths: swot.strengths || [],
        swotWeaknesses: swot.weaknesses || [],
        swotOpportunities: swot.opportunities || [],
        swotThreats: swot.threats || []
    };
    
    Object.entries(sections).forEach(([elementId, items]) => {
        const element = document.getElementById(elementId);
        element.innerHTML = '';
        
        if (items.length === 0) {
            const li = document.createElement('li');
            li.textContent = 'No items available';
            li.style.color = '#999';
            element.appendChild(li);
        } else {
            items.forEach(item => {
                const li = document.createElement('li');
                // Remove **bold** formatting from the text
                let cleanText = item.replace(/\*\*(.*?)\*\*/g, '$1');
                li.textContent = cleanText;
                element.appendChild(li);
            });
        }
    });
}

// Display strategic actions
function displayStrategicActions(recommendations) {
    const actionsDiv = document.getElementById('strategicActions');
    actionsDiv.innerHTML = '';
    
    if (recommendations.length === 0) {
        actionsDiv.innerHTML = '<p>No strategic recommendations available</p>';
        return;
    }
    
    recommendations.forEach(recommendation => {
        const priority = recommendation.priority || 'medium';
        const actionDiv = document.createElement('div');
        actionDiv.className = `action-item action-${priority}`;
        
        // Clean up action title by removing **bold** formatting
        const cleanAction = (recommendation.action || 'No action specified').replace(/\*\*(.*?)\*\*/g, '$1');
        const cleanRationale = (recommendation.rationale || 'No detailed description').replace(/\*\*(.*?)\*\*/g, '$1');
        const cleanImpact = (recommendation.expected_impact || 'To be evaluated').replace(/\*\*(.*?)\*\*/g, '$1');
        
        actionDiv.innerHTML = `
            <div class="action-header">
                <div class="action-title">${cleanAction}</div>
                <div class="action-priority priority-${priority}">${formatPriority(priority)}</div>
            </div>
            <div class="action-description">${cleanRationale}</div>
            <div class="action-impact"><strong>Expected Impact:</strong> ${cleanImpact}</div>
        `;
        
        actionsDiv.appendChild(actionDiv);
    });
}

// Display market insights
function displayMarketInsights(insights) {
    const insightsDiv = document.getElementById('marketInsights');
    insightsDiv.innerHTML = '<div class="insight-grid"></div>';
    const gridDiv = insightsDiv.querySelector('.insight-grid');
    
    const insightItems = [
        {
            title: 'Market Dynamics',
            content: insights.market_dynamics || {}
        },
        {
            title: 'Competitive Landscape',
            content: insights.competitive_landscape || {}
        },
        {
            title: 'Trend Analysis',
            content: insights.trends || []
        }
    ];
    
    insightItems.forEach(item => {
        const itemDiv = document.createElement('div');
        itemDiv.className = 'insight-item';
        
        let contentHtml = '';
        if (Array.isArray(item.content)) {
            contentHtml = item.content.length > 0 
                ? `<ul>${item.content.map(trend => `<li>${trend}</li>`).join('')}</ul>`
                : '<p>No data available</p>';
        } else if (typeof item.content === 'object') {
            contentHtml = Object.keys(item.content).length > 0
                ? Object.entries(item.content).map(([key, value]) => 
                    `<p><strong>${formatKey(key)}:</strong> ${value}</p>`).join('')
                : '<p>No data available</p>';
        } else {
            contentHtml = `<p>${item.content}</p>`;
        }
        
        itemDiv.innerHTML = `
            <h4>${item.title}</h4>
            <div class="insight-content">${contentHtml}</div>
        `;
        
        gridDiv.appendChild(itemDiv);
    });
}

// Utility functions
function formatScore(score) {
    return score ? Math.round(score) + '/100' : '--';
}

function formatPosition(position) {
    const translations = {
        'lowest': 'Lowest Price',
        'highest': 'Highest Price', 
        'middle': 'Middle',
        'competitive': 'Competitive',
        'expensive': 'Expensive',
        'superior': 'Superior',
        'average': 'Average',
        'leading': 'Leading',
        'following': 'Following',
        'strong': 'Strong',
        'weak': 'Weak',
        'best': 'Best',
        'worst': 'Worst',
        'unknown': 'Unknown'
    };
    
    return translations[position] || position || '--';
}

function formatPriority(priority) {
    const translations = {
        'high': 'High',
        'medium': 'Medium',
        'low': 'Low'
    };
    
    return translations[priority] || priority;
}

function formatKey(key) {
    const translations = {
        'price_volatility': 'Price Volatility',
        'market_maturity': 'Market Maturity',
        'price_competition_intensity': 'Price Competition Intensity',
        'market_leadership': 'Market Leadership',
        'quality_differentiation': 'Quality Differentiation',
        'price_leadership': 'Price Leadership',
        'overall_market_position': 'Overall Market Position'
    };
    
    return translations[key] || key;
}

// State management functions
function showLoading() {
    elements.loadingState.style.display = 'block';
    elements.errorState.style.display = 'none';
    elements.mainContent.style.display = 'none';
}

function showError(message) {
    elements.loadingState.style.display = 'none';
    elements.errorState.style.display = 'block';
    elements.mainContent.style.display = 'none';
    elements.errorMessage.textContent = message;
}

function showMainContent() {
    elements.loadingState.style.display = 'none';
    elements.errorState.style.display = 'none';
    elements.mainContent.style.display = 'block';
    
    // Add fade-in animation
    elements.mainContent.classList.add('fade-in');
    setTimeout(() => {
        elements.mainContent.classList.remove('fade-in');
    }, 500);
}

// Demo mode interface for GitHub Pages
function showDemoModeInterface() {
    elements.loadingState.style.display = 'none';
    elements.errorState.style.display = 'none';
    elements.mainContent.style.display = 'block';
    
    // Update header for demo mode
    const headerContent = document.querySelector('.header-content');
    headerContent.innerHTML = `
        <h1><i class="fas fa-chart-line"></i> Amazon Insights</h1>
        <p class="subtitle">🌐 Live Demo - Competitive Analysis Dashboard</p>
        <div class="demo-notice">
            <i class="fas fa-info-circle"></i> 
            <strong>Demo Mode:</strong> Interface preview without live data. 
            <a href="https://github.com/jiasyuanchu/amazon-insights#installation-and-setup" target="_blank">
                Setup locally for full functionality
            </a>
        </div>
    `;
    
    // Hide group selector and refresh button in demo mode
    elements.groupSelect.style.display = 'none';
    elements.refreshBtn.style.display = 'none';
    
    // Show demo content
    displayDemoContent();
}

// Display demo content explaining each component
function displayDemoContent() {
    // Update overview cards with explanations
    updateDemoOverviewCards();
    
    // Show demo charts with explanations
    displayDemoCharts();
    
    // Show demo analysis sections
    displayDemoAnalysis();
    
    // Update timestamp
    elements.lastUpdate.textContent = new Date().toLocaleString('en-US');
}

// Demo overview cards
function updateDemoOverviewCards() {
    const demoData = [
        {
            id: 'priceScore',
            label: 'pricePosition',
            title: 'Price Competitiveness',
            description: 'Analyzes your product pricing relative to competitors (0-100 scale)',
            icon: 'fas fa-dollar-sign',
            example: 'Shows if your price is competitive, expensive, or budget-friendly'
        },
        {
            id: 'qualityScore', 
            label: 'qualityPosition',
            title: 'Quality Competitiveness',
            description: 'Based on Amazon ratings and review analysis (0-100 scale)',
            icon: 'fas fa-star',
            example: 'Compares customer satisfaction vs competitors'
        },
        {
            id: 'popularityScore',
            label: 'popularityPosition', 
            title: 'Market Popularity',
            description: 'BSR ranking performance and market position (0-100 scale)',
            icon: 'fas fa-fire',
            example: 'Shows sales ranking performance vs competition'
        },
        {
            id: 'overallScore',
            label: 'overallPosition',
            title: 'Overall Competitiveness', 
            description: 'Combined score across all competitive dimensions',
            icon: 'fas fa-trophy',
            example: 'Comprehensive competitive strength assessment'
        }
    ];
    
    demoData.forEach(item => {
        document.getElementById(item.id).innerHTML = `
            <div class="demo-explanation">
                <h4>${item.title}</h4>
                <p>${item.description}</p>
                <small><strong>Example:</strong> ${item.example}</small>
            </div>
        `;
        document.getElementById(item.label).textContent = 'Demo Mode';
    });
}

// Demo charts with explanations
function displayDemoCharts() {
    // Price chart explanation
    const priceChartContainer = document.getElementById('priceChart').parentElement;
    priceChartContainer.innerHTML = `
        <div class="demo-chart-explanation">
            <h4><i class="fas fa-chart-bar"></i> Price Comparison Chart</h4>
            <p>Visual comparison of your product price vs competitors:</p>
            <ul>
                <li><strong>Green Bar:</strong> Your main product price</li>
                <li><strong>Blue Bars:</strong> Competitor prices</li>
                <li><strong>Analysis:</strong> Instantly see if you're priced competitively</li>
            </ul>
            <div class="chart-preview">
                📊 <em>Interactive bar chart displays here with real data</em>
            </div>
        </div>
    `;
    
    // Rating chart explanation  
    const ratingChartContainer = document.getElementById('ratingChart').parentElement;
    ratingChartContainer.innerHTML = `
        <div class="demo-chart-explanation">
            <h4><i class="fas fa-star-half-alt"></i> Rating vs Reviews Bubble Chart</h4>
            <p>Bubble chart showing rating performance vs review volume:</p>
            <ul>
                <li><strong>X-axis:</strong> Product rating (1-5 stars)</li>
                <li><strong>Y-axis:</strong> Review count (logarithmic scale)</li>
                <li><strong>Bubble size:</strong> Relative review volume</li>
                <li><strong>Colors:</strong> Your product (green) vs competitors (blue)</li>
            </ul>
            <div class="chart-preview">
                🫧 <em>Interactive bubble chart displays here with real data</em>
            </div>
        </div>
    `;
}

// Demo analysis sections
function displayDemoAnalysis() {
    // BSR Analysis demo
    const bsrDiv = document.getElementById('bsrAnalysis');
    bsrDiv.innerHTML = `
        <div class="demo-analysis-explanation">
            <h4>Amazon Best Seller Rank Analysis</h4>
            <p>Comprehensive BSR (Best Seller Rank) competitive positioning:</p>
            
            <div class="demo-metrics-grid">
                <div class="demo-metric">
                    <strong>Main Product Rank:</strong> Your product's ranking in each category
                </div>
                <div class="demo-metric">
                    <strong>Market Position:</strong> Leading, Following, or Middle position
                </div>
                <div class="demo-metric">
                    <strong>Best Rank:</strong> Highest ranking achieved in period
                </div>
                <div class="demo-metric">
                    <strong>Average Rank:</strong> Average performance over time period
                </div>
            </div>
            
            <p><small><em>Real data shows ranking across multiple Amazon categories</em></small></p>
        </div>
    `;
    
    // Executive Summary demo
    const executiveSummary = document.getElementById('executiveSummary');
    executiveSummary.innerHTML = `
        <div class="demo-analysis-explanation">
            <h4>AI-Powered Executive Summary</h4>
            <p>OpenAI GPT-4 generated competitive positioning overview including:</p>
            <ul>
                <li>Overall market position assessment</li>
                <li>Competitive strength analysis</li>
                <li>Key performance indicators</li>
                <li>Strategic positioning insights</li>
            </ul>
            <p><small><em>Generated automatically from your competitive analysis data</em></small></p>
        </div>
    `;
    
    // SWOT Analysis demo
    displayDemoSWOT();
    
    // Strategic Actions demo
    displayDemoStrategicActions();
    
    // Market Insights demo
    displayDemoMarketInsights();
}

function displayDemoSWOT() {
    const swotSections = {
        swotStrengths: {
            title: 'Strengths',
            description: 'Competitive advantages identified from data analysis',
            examples: ['Superior customer ratings', 'Competitive pricing position', 'Unique product features']
        },
        swotWeaknesses: {
            title: 'Weaknesses', 
            description: 'Areas requiring improvement based on competitor comparison',
            examples: ['Limited feature differentiation', 'Higher price point', 'Lower review volume']
        },
        swotOpportunities: {
            title: 'Opportunities',
            description: 'Market opportunities identified through competitive analysis', 
            examples: ['Premium market expansion', 'Feature gap exploitation', 'Underserved segments']
        },
        swotThreats: {
            title: 'Threats',
            description: 'Competitive threats and market risks',
            examples: ['New competitor entry', 'Price competition intensification', 'Market saturation']
        }
    };
    
    Object.entries(swotSections).forEach(([elementId, data]) => {
        const element = document.getElementById(elementId);
        element.innerHTML = `
            <div class="demo-swot-explanation">
                <h5>${data.title}</h5>
                <p>${data.description}</p>
                <div class="demo-examples">
                    <strong>Examples:</strong>
                    ${data.examples.map(example => `<span class="demo-tag">${example}</span>`).join('')}
                </div>
            </div>
        `;
    });
}

function displayDemoStrategicActions() {
    const actionsDiv = document.getElementById('strategicActions');
    actionsDiv.innerHTML = `
        <div class="demo-analysis-explanation">
            <h4>AI-Generated Strategic Recommendations</h4>
            <p>Actionable business insights with priority scoring:</p>
            
            <div class="demo-action-examples">
                <div class="demo-action-item">
                    <div class="demo-action-header">
                        <span class="demo-action-title">Example: Price Optimization Strategy</span>
                        <span class="demo-priority priority-high">High Priority</span>
                    </div>
                    <p class="demo-action-desc">Analyze competitor pricing and adjust strategy for better market position</p>
                    <p class="demo-action-impact"><strong>Expected Impact:</strong> 10-15% improvement in competitive ranking</p>
                </div>
                
                <div class="demo-action-item">
                    <div class="demo-action-header">
                        <span class="demo-action-title">Example: Feature Enhancement Plan</span>
                        <span class="demo-priority priority-medium">Medium Priority</span>
                    </div>
                    <p class="demo-action-desc">Address feature gaps identified through competitor analysis</p>
                    <p class="demo-action-impact"><strong>Expected Impact:</strong> Enhanced product differentiation</p>
                </div>
            </div>
            
            <p><small><em>Real recommendations generated from actual competitive data analysis</em></small></p>
        </div>
    `;
}

function displayDemoMarketInsights() {
    const insightsDiv = document.getElementById('marketInsights');
    insightsDiv.innerHTML = `
        <div class="demo-analysis-explanation">
            <h4>Market Intelligence Insights</h4>
            <p>Comprehensive market analysis including:</p>
            
            <div class="demo-insights-grid">
                <div class="demo-insight-item">
                    <h5><i class="fas fa-chart-line"></i> Market Dynamics</h5>
                    <p>Price volatility, market maturity, competition intensity analysis</p>
                </div>
                
                <div class="demo-insight-item">
                    <h5><i class="fas fa-users"></i> Competitive Landscape</h5>
                    <p>Market leadership analysis, quality differentiation assessment</p>
                </div>
                
                <div class="demo-insight-item">
                    <h5><i class="fas fa-trending-up"></i> Trend Analysis</h5>
                    <p>Market trends, emerging opportunities, competitive shifts</p>
                </div>
            </div>
            
            <p><small><em>Insights derived from real-time Amazon data analysis</em></small></p>
        </div>
    `;
}