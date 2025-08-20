// Simple Chart.js fallback for basic functionality
window.Chart = window.Chart || {
    register: function() {},
    defaults: {
        plugins: {
            legend: { display: true }
        }
    },
    
    // Mock Chart constructor
    Chart: function(ctx, config) {
        console.warn('Using fallback Chart implementation');
        
        if (!ctx) {
            console.error('Chart canvas context not found');
            return { destroy: function() {} };
        }
        
        // Create a simple fallback visualization
        const canvas = ctx.canvas || ctx;
        const parent = canvas.parentElement;
        
        // Replace canvas with simple HTML representation
        const fallbackDiv = document.createElement('div');
        fallbackDiv.style.cssText = 'padding: 40px; text-align: center; background: #f8f9fa; border-radius: 10px; border: 2px dashed #dee2e6;';
        
        if (config.type === 'bar') {
            // Simple bar chart representation
            const data = config.data.datasets[0].data;
            const labels = config.data.labels;
            const max = Math.max(...data);
            
            let html = '<h4 style="color: #666; margin-bottom: 20px;">Price Comparison</h4>';
            html += '<div style="display: flex; align-items: end; justify-content: space-around; height: 150px;">';
            
            data.forEach((value, index) => {
                const height = (value / max) * 100;
                const color = index === 0 ? '#2ecc71' : '#3498db';
                html += `
                    <div style="text-align: center; margin: 0 5px;">
                        <div style="background: ${color}; height: ${height}px; width: 40px; border-radius: 4px 4px 0 0; margin-bottom: 10px; display: flex; align-items: end; justify-content: center; color: white; font-weight: bold; font-size: 12px; padding: 5px 0;">
                            $${value}
                        </div>
                        <div style="font-size: 11px; color: #666; max-width: 50px; word-break: break-word;">
                            ${labels[index] || `Item ${index + 1}`}
                        </div>
                    </div>
                `;
            });
            
            html += '</div>';
            fallbackDiv.innerHTML = html;
            
        } else if (config.type === 'bubble') {
            // Simple bubble chart representation
            fallbackDiv.innerHTML = `
                <h4 style="color: #666; margin-bottom: 20px;">Rating vs Review Count</h4>
                <p style="color: #999;">Loading chart...</p>
                <div style="margin: 20px 0;">
                    <small style="color: #666;">📊 For best experience, please ensure stable internet connection</small>
                </div>
            `;
        }
        
        // Replace the canvas
        parent.replaceChild(fallbackDiv, canvas);
        
        return {
            destroy: function() {
                if (fallbackDiv.parentNode) {
                    fallbackDiv.parentNode.removeChild(fallbackDiv);
                }
            },
            update: function() {},
            resize: function() {}
        };
    }
};

// Set Chart to the constructor
if (typeof window !== 'undefined') {
    window.Chart = window.Chart.Chart;
    
    // Add Chart.js common methods
    window.Chart.register = function() {};
    window.Chart.defaults = {
        plugins: { legend: { display: true } },
        responsive: true,
        maintainAspectRatio: false
    };
}

console.log('Chart.js fallback loaded');