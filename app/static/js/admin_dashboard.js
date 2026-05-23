let searchQuery = '';
let currentPage = 1;
const itemsPerPage = 10;

const searchInput = document.getElementById('searchInput');
const tableBody = document.getElementById('tableBody');
const tableInfo = document.getElementById('tableInfo');
const paginationGroup = document.getElementById('paginationGroup');
const toastContainer = document.getElementById('toastContainer');

document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    renderTable();
});

function setupEventListeners() {
    let searchTimeout;
    searchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            searchQuery = e.target.value.toLowerCase().trim();
            currentPage = 1;
            renderTable();
        }, 150);
    });
}

function getSearchableRows() {
    const rows = document.querySelectorAll('.searchable-row');
    if (!searchQuery) return Array.from(rows);

    return Array.from(rows).filter(row => {
        const searchText = row.dataset.search.toLowerCase();
        return searchText.includes(searchQuery);
    });
}

function renderTable() {
     const filteredRows = getSearchableRows();
     const totalItems = filteredRows.length;
     const totalPages = Math.ceil(totalItems / itemsPerPage) || 1;

     if (currentPage > totalPages) currentPage = totalPages;

     const startIndex = (currentPage - 1) * itemsPerPage;
     const endIndex = Math.min(startIndex + itemsPerPage, totalItems);
     document.querySelectorAll('.searchable-row').forEach(row => {
         row.style.display = 'none';
     });
     filteredRows.forEach((row, index) => {
         const isVisible = index >= startIndex && index < endIndex;
         row.style.display = isVisible ? 'table-row' : 'none';

         if (isVisible) {
             row.addEventListener('mouseenter', () => {
                 row.style.transform = 'scale(1.006)';
                 row.style.boxShadow = '0 6px 12px rgba(0,0,0,0.06)';
                 row.style.zIndex = '10';
             });
             row.addEventListener('mouseleave', () => {
                 row.style.transform = 'scale(1)';
                 row.style.boxShadow = 'none';
                 row.style.zIndex = '1';
             });
         }
     });

     tableInfo.innerText = `Hiển thị ${totalItems > 0 ? startIndex + 1 : 0}-${endIndex} trong số ${totalItems} lớp học phần`;
     renderPagination(totalPages);
 }

function renderPagination(totalPages) {
    paginationGroup.innerHTML = '';

    const prevBtn = document.createElement('button');
    prevBtn.className = 'pagination-btn';
    prevBtn.innerHTML = `<span class="material-symbols-outlined">chevron_left</span>`;
    prevBtn.disabled = currentPage === 1;
    prevBtn.addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            renderTable();
        }
    });
    paginationGroup.appendChild(prevBtn);

    for (let i = 1; i <= totalPages; i++) {
        const pageBtn = document.createElement('button');
        pageBtn.className = `pagination-btn ${i === currentPage ? 'is-active' : ''}`;
        pageBtn.innerText = i;
        pageBtn.addEventListener('click', () => {
            currentPage = i;
            renderTable();
        });
        paginationGroup.appendChild(pageBtn);
    }

    const nextBtn = document.createElement('button');
    nextBtn.className = 'pagination-btn';
    nextBtn.innerHTML = `<span class="material-symbols-outlined">chevron_right</span>`;
    nextBtn.disabled = currentPage === totalPages;
    nextBtn.addEventListener('click', () => {
        if (currentPage < totalPages) {
            currentPage++;
            renderTable();
        }
    });
    paginationGroup.appendChild(nextBtn);
}

function showToast(message, isError = false) {
    const toast = document.createElement('div');
    toast.className = `toast ${isError ? 'toast-error' : ''}`;
    toast.innerHTML = `
        <span class="material-symbols-outlined">${isError ? 'error' : 'check_circle'}</span>
        <span>${message}</span>
    `;
    toastContainer.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('toast-fadeout');
        setTimeout(() => toast.remove(), 300);
    }, 3800);
}


