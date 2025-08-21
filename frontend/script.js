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
            showError('No competitive groups found. Please create competitive groups using the API first.');
        }
    } catch (error) {
        console.error('Initialization failed:', error);
        showError('Initialization failed: ' + error.message);
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