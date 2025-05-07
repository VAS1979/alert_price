// scripts.js

document.addEventListener('DOMContentLoaded', () => {
    // Элементы DOM
    const addForm = document.getElementById('entering-data-form');
    const deleteForm = document.getElementById('delete-stock-form');
    const tableBody = document.getElementById('stock-table-body');
    let currentPrices = {};

    // Загрузка данных при старте
    loadData();

    // Обработчики форм
    addForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        await handleAddStock();
    });

    deleteForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        await handleDeleteStock();
    });

    // Функция загрузки данных
    async function loadData() {
        try {
            const [stocks, prices] = await Promise.all([
                fetch('/api/tracked-stocks').then(res => res.json()),
                fetch('/api/prices').then(res => res.json())
            ]);
            
            currentPrices = prices.prices || {};
            renderStockTable(stocks);
            startPriceUpdates();
        } catch (error) {
            console.error('Ошибка загрузки:', error);
        }
    }

    // Функция обновления цен
    function startPriceUpdates() {
        setInterval(async () => {
            try {
                const response = await fetch('/api/prices');
                const { prices } = await response.json();
                currentPrices = prices || {};
                
                document.querySelectorAll('.price-cell').forEach(cell => {
                    const ticker = cell.dataset.ticker;
                    const price = currentPrices[ticker];
                    cell.textContent = price ? price.toFixed(2) : 'N/A';
                    updateRowStyle(cell.closest('tr'), ticker);
                });
            } catch (error) {
                console.error('Ошибка обновления цен:', error);
            }
        }, 30000);
    }

    // Обработка добавления акции
    async function handleAddStock() {
        const formData = new FormData(addForm);
        
        try {
            const response = await fetch('/api/stock-alerts', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            alert(data.success ? "Акция добавлена" : data.error || "Ошибка");
            if (data.success) {
                addForm.reset();
                loadData();
            }
        } catch (error) {
            console.error('Ошибка:', error);
            alert("Ошибка при добавлении акции");
        }
    }

    // Обработка удаления акции
    async function handleDeleteStock() {
        const ticker = document.getElementById('ticker-to-delete').value.toUpperCase();
        
        if (!ticker) {
            alert("Введите тикер акции");
            return;
        }

        try {
            const response = await fetch(`/api/stock-alerts/${ticker}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            alert(data.success ? data.message : "Ошибка при удалении");
            if (data.success) {
                deleteForm.reset();
                loadData();
            }
        } catch (error) {
            console.error('Ошибка:', error);
            alert("Ошибка при удалении акции");
        }
    }

    // Рендеринг таблицы
    function renderStockTable(stocks) {
        tableBody.innerHTML = stocks.map(stock => `
            <tr>
                <td>${stock.ticker}</td>
                <td>${parseFloat(stock.buy_price).toFixed(2)}</td>
                <td>${parseFloat(stock.sell_price).toFixed(2)}</td>
                <td class="price-cell" data-ticker="${stock.ticker}">
                    ${currentPrices[stock.ticker]?.toFixed(2) || 'N/A'}
                </td>
                <td class="status-cell">
                    ${getStatus(stock, currentPrices)}
                </td>
            </tr>
        `).join('');

        // Обновление стилей
        document.querySelectorAll('#stock-table-body tr').forEach(row => {
            const ticker = row.querySelector('.price-cell').dataset.ticker;
            updateRowStyle(row, ticker);
        });
    }

    // Определение статуса
    function getStatus(stock, prices) {
        const price = prices[stock.ticker];
        if (!price) return '';
        
        const buyPrice = parseFloat(stock.buy_price);
        const sellPrice = parseFloat(stock.sell_price);
        
        if (price <= buyPrice) return 'Покупка';
        if (price >= sellPrice) return 'Продажа';
        return '';
    }

    // Обновление стилей строки
    function updateRowStyle(row, ticker) {
        const priceCell = row.querySelector('.price-cell');
        const statusCell = row.querySelector('.status-cell');
        const price = currentPrices[ticker];
        
        // Сброс стилей
        priceCell.className = 'price-cell';
        statusCell.className = 'status-cell';
        
        if (!price) return;
        
        const buyPrice = parseFloat(row.children[1].textContent);
        const sellPrice = parseFloat(row.children[2].textContent);
        
        if (price <= buyPrice) {
            priceCell.classList.add('price-low');
            statusCell.classList.add('status-buy');
            statusCell.textContent = 'Покупка';
        } else if (price >= sellPrice) {
            priceCell.classList.add('price-high');
            statusCell.classList.add('status-sell');
            statusCell.textContent = 'Продажа';
        }
    }
});