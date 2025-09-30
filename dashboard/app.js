// Segment Chart
const segmentCtx = document.getElementById('segmentChart').getContext('2d');
new Chart(segmentCtx, {
    type: 'doughnut',
    data: {
        labels: ['Low Value Inactive', 'Low Value Active', 'High Value Inactive', 'High Value Active'],
        datasets: [{
            data: [399, 45, 20, 1],
            backgroundColor: ['#E53935', '#FFA726', '#FDD835', '#43A047']
        }]
    }
});

// Risk Chart
const riskCtx = document.getElementById('riskChart').getContext('2d');
new Chart(riskCtx, {
    type: 'bar',
    data: {
        labels: ['Medium Risk', 'High Risk', 'Low Risk'],
        datasets: [{
            label: 'Customer Count',
            data: [261, 170, 34],
            backgroundColor: ['#FFA726', '#E53935', '#43A047']
        }]
    },
    options: {
        scales: {
            y: {
                beginAtZero: true
            }
        }
    }
});

console.log('Dashboard loaded with data from Customer Analytics Platform');
