// Color scheme from Flight Data Project
const colors = {
    primary: '#304CB2',        // Bold Blue
    primaryLight: '#3453C4',   // Cerulean Blue
    secondary: '#E51D23',      // Bright Red
    accent: '#F9B612',         // Sunshine Yellow
    gray: '#CCCCCC',           // Neutral Gray
    success: '#43A047'         // Green
};

// Segment Chart - Doughnut
const segmentCtx = document.getElementById('segmentChart').getContext('2d');
new Chart(segmentCtx, {
    type: 'doughnut',
    data: {
        labels: ['Low Value Inactive', 'Low Value Active', 'High Value Inactive', 'High Value Active'],
        datasets: [{
            data: [399, 45, 20, 1],
            backgroundColor: [
                colors.secondary,      // Low Value Inactive - Red
                colors.accent,         // Low Value Active - Yellow
                colors.primaryLight,   // High Value Inactive - Light Blue
                colors.success         // High Value Active - Green
            ],
            borderColor: '#FFFFFF',
            borderWidth: 2
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
            legend: {
                position: 'bottom',
                labels: {
                    padding: 15,
                    font: {
                        size: 12,
                        family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto'
                    },
                    color: '#111111'
                }
            },
            tooltip: {
                backgroundColor: colors.primary,
                titleFont: {
                    size: 14,
                    weight: '600'
                },
                bodyFont: {
                    size: 13
                },
                padding: 12,
                cornerRadius: 8,
                callbacks: {
                    label: function(context) {
                        const total = context.dataset.data.reduce((a, b) => a + b, 0);
                        const value = context.parsed;
                        const percentage = ((value / total) * 100).toFixed(1);
                        return ` ${context.label}: ${value} (${percentage}%)`;
                    }
                }
            }
        }
    }
});

// Risk Chart - Horizontal Bar
const riskCtx = document.getElementById('riskChart').getContext('2d');
new Chart(riskCtx, {
    type: 'bar',
    data: {
        labels: ['Low Risk', 'Medium Risk', 'High Risk'],
        datasets: [{
            label: 'Customer Count',
            data: [34, 261, 170],
            backgroundColor: [
                colors.success,        // Low Risk - Green
                colors.accent,         // Medium Risk - Yellow
                colors.secondary       // High Risk - Red
            ],
            borderColor: [
                colors.success,
                colors.accent,
                colors.secondary
            ],
            borderWidth: 2,
            borderRadius: 8
        }]
    },
    options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
            legend: {
                display: false
            },
            tooltip: {
                backgroundColor: colors.primary,
                titleFont: {
                    size: 14,
                    weight: '600'
                },
                bodyFont: {
                    size: 13
                },
                padding: 12,
                cornerRadius: 8,
                callbacks: {
                    label: function(context) {
                        const total = context.dataset.data.reduce((a, b) => a + b, 0);
                        const value = context.parsed.x;
                        const percentage = ((value / total) * 100).toFixed(1);
                        return ` ${value} customers (${percentage}%)`;
                    }
                }
            }
        },
        scales: {
            x: {
                beginAtZero: true,
                grid: {
                    color: 'rgba(204, 204, 204, 0.2)'
                },
                ticks: {
                    font: {
                        size: 11
                    },
                    color: '#111111'
                }
            },
            y: {
                grid: {
                    display: false
                },
                ticks: {
                    font: {
                        size: 12,
                        weight: '600'
                    },
                    color: colors.primary
                }
            }
        }
    }
});

console.log('Customer Analytics Dashboard loaded successfully');
console.log('Using Flight Data Project color scheme');
console.log('Data pipeline: S3 → Alteryx ETL → Lambda → Visualization');
