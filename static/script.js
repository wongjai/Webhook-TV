// static/script.js

// 圖表初始化
let pnlChart;

async function initializePnlChart() {
    const ctx = document.getElementById('pnlChart').getContext('2d');
    pnlChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Cumulative PnL',
                data: [],
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// 載入交易歷史
async function loadTradeHistory() {
    const symbol = document.getElementById('history_symbol').value;
    try {
        const response = await fetch(`/trade_history/${symbol}`);
        const trades = await response.json();

        // 更新表格
        updateTradeHistoryTable(trades);
        
        // 更新圖表
        updatePnlChart(trades);
        
    } catch (error) {
        console.error('Error loading trade history:', error);
        alert('Failed to load trade history');
    }
}

function updateTradeHistoryTable(trades) {
    const tableBody = document.getElementById('trade_history_table');
    tableBody.innerHTML = '';

    trades.forEach(trade => {
        const row = document.createElement('tr');
        row.className = 'hover:bg-gray-50';
        
        const cells = [
            { value: trade.id, class: '' },
            { value: trade.symbol, class: 'font-medium' },
            { 
                value: trade.side, 
                class: trade.side.toLowerCase() === 'buy' ? 'text-green-600' : 'text-red-600'
            },
            { value: formatPrice(trade.entry_price), class: '' },
            { value: formatPrice(trade.exit_price), class: '' },
            { 
                value: formatPnL(trade.pnl), 
                class: trade.pnl > 0 ? 'text-green-600' : 'text-red-600'
            },
            { value: formatDate(trade.open_time), class: 'text-gray-500' },
            { value: formatDate(trade.close_time), class: 'text-gray-500' }
        ];

        cells.forEach(cell => {
            const td = document.createElement('td');
            td.className = `px-6 py-4 whitespace-nowrap text-sm ${cell.class}`;
            td.textContent = cell.value || 'N/A';
            row.appendChild(td);
        });

        tableBody.appendChild(row);
    });
}

function updatePnlChart(trades) {
    // 計算累計 PnL
    let cumulativePnl = 0;
    const chartData = trades
        .filter(trade => trade.pnl != null)
        .map(trade => {
            cumulativePnl += trade.pnl;
            return {
                time: new Date(trade.close_time),
                pnl: cumulativePnl
            };
        })
        .sort((a, b) => a.time - b.time);

    pnlChart.data.labels = chartData.map(d => formatDate(d.time));
    pnlChart.data.datasets[0].data = chartData.map(d => d.pnl);
    pnlChart.update();
}

// Kill Switch 功能
async function activateKillSwitch() {
    if (!confirm('Are you sure you want to activate the Kill Switch? This will immediately stop all trading activities.')) {
        return;
    }

    try {
        const response = await fetch('/kill_switch', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const result = await response.json();
        const messageElement = document.getElementById('kill_switch_message');
        
        if (response.ok) {
            messageElement.textContent = '✅ Kill Switch activated successfully. Trading has been stopped.';
            messageElement.className = 'mt-4 text-sm text-green-600';
            
            // 更新交易模式指示器
            document.querySelector('.trade-mode-indicator span').className = 
                'px-4 py-2 rounded-full bg-yellow-500 text-white';
            document.querySelector('.trade-mode-indicator span').textContent = 'Demo Mode';
            
        } else {
            messageElement.textContent = '❌ Failed to activate Kill Switch: ' + result.message;
            messageElement.className = 'mt-4 text-sm text-red-600';
        }
    } catch (error) {
        console.error('Error activating kill switch:', error);
        alert('Failed to activate Kill Switch');
    }
}

// 工具函數
function formatPrice(price) {
    return price ? parseFloat(price).toFixed(2) : 'N/A';
}

function formatPnL(pnl) {
    if (pnl == null) return 'N/A';
    return (pnl > 0 ? '+' : '') + parseFloat(pnl).toFixed(2);
}

function formatDate(dateStr) {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleString();
}

// 頁面載入時初始化
document.addEventListener('DOMContentLoaded', () => {
    initializePnlChart();
    loadTradeHistory();
});

// 自動更新功能
setInterval(loadTradeHistory, 30000); // 每30秒更新一次
