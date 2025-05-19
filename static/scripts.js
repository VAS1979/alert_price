// scripts.js

/**
 * Рассчитывает процент расхождения между текущей ценой и границами
 * @param {number} buyPrice - Цена покупки
 * @param {number} sellPrice - Цена продажи
 * @param {number} currentPrice - Текущая цена
 * @returns {string} Процент расхождения с 2 знаками после запятой или 'N/A'
 */
function calculateDifference(buyPrice, sellPrice, currentPrice) {
    if (currentPrice === undefined || currentPrice === null) 
        return {value: '', type: ''};
    
    // Если цена выше цены продажи - зеленый
    if (currentPrice > sellPrice) {
        const percent = (((currentPrice - sellPrice) / sellPrice) * 100).toFixed(2);
        return {value: percent, type: 'high'};
    }
    // Если цена ниже цены покупки - красный
    else if (currentPrice < buyPrice) {
        const percent = (((buyPrice - currentPrice) / buyPrice) * 100).toFixed(2);
        return {value: percent, type: 'low'};
    }
    // Если цена в пределах - пусто
    return {value: '', type: ''};
}

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
                    cell.textContent = price ?? 'N/A';
                
                    const row = cell.closest('tr');
                    updateRowStyle(row, ticker);
                
                    // Обновляем процент расхождения
                    const buyPrice = parseFloat(row.children[1].textContent);
                    const sellPrice = parseFloat(row.children[2].textContent);
                    const currentPrice = price ? parseFloat(price) : null;
                    const diffCell = row.querySelector('.difference-cell');
                    const diff = calculateDifference(buyPrice, sellPrice, currentPrice);
                
                    // Обновляем классы и значение
                    diffCell.className = `difference-cell ${diff.type}-difference`;
                    diffCell.textContent = diff.value ? `${diff.value}%` : '';
                });
            } catch (error) {
                console.error('Ошибка обновления цен:', error);
            }
        }, 9000);
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

    // Функция для форматирования чисел
    const formatNumber = (num) => {
        if (num === undefined || num === null) return 'N/A';
        const str = num.toString();
        return str.includes('.') ? str.replace(/\.?0+$/, '') : str;
    };

    // Рендеринг таблицы
    function renderStockTable(stocks) {
        tableBody.innerHTML = stocks.map(stock => {
            const currentPrice = currentPrices[stock.ticker];
            const diff = calculateDifference(
                parseFloat(stock.buy_price),
                parseFloat(stock.sell_price),
                currentPrice ? parseFloat(currentPrice) : null
            );

            return `
            <tr>
                <td>${stock.ticker}</td>
                <td>${stock.buy_price}</td>
                <td>${stock.sell_price}</td>
                <td class="price-cell" data-ticker="${stock.ticker}">
                    ${currentPrice ?? 'N/A'}
                </td>
                <!-- Новая колонка с процентом расхождения -->
                <td class="difference-cell ${diff.type}-difference" data-ticker="${stock.ticker}">
                    ${diff.value ? `${diff.value}%` : ''}
                </td>
                <td class="status-cell">
                    ${getStatus(stock, currentPrices)}
                </td>
            </tr>
            `;
        }).join('');

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

    // Функция для точного сравнения цен
    function comparePrices(price1, price2) {
        const num1 = typeof price1 === 'string' ? parseFloat(price1) : price1;
        const num2 = typeof price2 === 'string' ? parseFloat(price2) : price2;
        return { num1, num2 };
    }

    // Обновление стилей строки
    function updateRowStyle(row, ticker) {
        const priceCell = row.querySelector('.price-cell');
        const statusCell = row.querySelector('.status-cell');
        const diffCell = row.querySelector('.difference-cell'); // Новая ячейка
        const price = currentPrices[ticker];
    
        // Сброс стилей
        priceCell.className = 'price-cell';
        statusCell.className = 'status-cell';
        diffCell.className = 'difference-cell';
    
        if (!price) return;
    
        const buyPrice = parseFloat(row.children[1].textContent);
        const sellPrice = parseFloat(row.children[2].textContent);
        const currentPrice = parseFloat(price);
    
        if (currentPrice <= buyPrice) {
            priceCell.classList.add('price-low');
            statusCell.classList.add('status-buy');
            statusCell.textContent = 'Покупка';
            diffCell.classList.add('difference-low'); // Стиль для снижения цены
        } else if (currentPrice >= sellPrice) {
            priceCell.classList.add('price-high');
            statusCell.classList.add('status-sell');
            statusCell.textContent = 'Продажа';
            diffCell.classList.add('difference-high'); // Стиль для превышения цены
        }
}
});