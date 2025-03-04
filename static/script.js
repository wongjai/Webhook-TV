// static/script.js
async function loadTradeHistory() {
    const symbol = document.getElementById('history_symbol').value;
    const response = await fetch(`/trade_history/${symbol}`);
    const trades = await response.json();

    const tableBody = document.getElementById('trade_history_table').getElementsByTagName('tbody')[0];
    tableBody.innerHTML = ''; // Clear existing rows

    for (const trade of trades) {
        const row = tableBody.insertRow();
        row.insertCell(0).textContent = trade.id;
        row.insertCell(1).textContent = trade.symbol;
        row.insertCell(2).textContent = trade.side;
        row.insertCell(3).textContent = trade.entry_price;
        row.insertCell(4).textContent = trade.exit_price || 'N/A';
        row.insertCell(5).textContent = trade.pnl || 'N/A';
        row.insertCell(6).textContent = trade.open_time;
        row.insertCell(7).textContent = trade.close_time || 'N/A';
    }
}

async function activateKillSwitch() {
    if (confirm("Are you sure you want to activate the Kill Switch?")) {
        const response = await fetch('/kill_switch', { method: 'POST' });
        const data = await response.json();
        document.getElementById('kill_switch_message').textContent = data.message;
    }
}
