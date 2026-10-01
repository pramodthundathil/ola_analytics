/**
 * Arrendadora Ola Cars AI Superuser - Enterprise Table Manager
 * Implements interactive column sorting, real-time search filtering,
 * status dropdown filtering, and pagination with "Show All" option.
 */

class EnterpriseTableManager {
  constructor(tableElement, options = {}) {
    this.table = tableElement;
    this.options = Object.assign({
      defaultPageSize: 5,
      pageSizeOptions: [5, 10, 25, "all"],
      searchPlaceholder: "🔍 Search table records...",
      statusFilter: true,
      initialSortCol: 0,
      initialSortDir: "asc"
    }, options);

    this.tbody = this.table.querySelector("tbody");
    if (!this.tbody) return;

    this.allRows = Array.from(this.tbody.querySelectorAll("tr"));
    this.filteredRows = [...this.allRows];
    this.currentPage = 1;
    this.pageSize = this.options.defaultPageSize;
    this.currentSortCol = -1;
    this.currentSortDir = "asc";
    this.searchTerm = "";
    this.statusFilterVal = "ALL";

    this.init();
  }

  init() {
    this.createControlsToolbar();
    this.setupSorting();
    this.render();
  }

  createControlsToolbar() {
    // Wrapper around table if not already present
    let wrapper = this.table.closest(".enterprise-table-container");
    if (!wrapper) {
      wrapper = document.createElement("div");
      wrapper.className = "enterprise-table-container";
      this.table.parentNode.insertBefore(wrapper, this.table);
      wrapper.appendChild(this.table);
    }
    this.wrapper = wrapper;

    // Top Controls Toolbar
    const toolbar = document.createElement("div");
    toolbar.className = "table-controls-toolbar";

    // 1. Search Box
    const searchBox = document.createElement("div");
    searchBox.className = "table-search-box";
    searchBox.innerHTML = `
      <input type="text" class="table-search-input" placeholder="${this.options.searchPlaceholder}" autocomplete="off">
      <button type="button" class="table-search-clear" style="display:none;" title="Clear search">✕</button>
    `;

    const searchInput = searchBox.querySelector(".table-search-input");
    const clearBtn = searchBox.querySelector(".table-search-clear");

    searchInput.addEventListener("input", (e) => {
      this.searchTerm = e.target.value.trim().toLowerCase();
      clearBtn.style.display = this.searchTerm ? "block" : "none";
      this.currentPage = 1;
      this.applyFilters();
    });

    clearBtn.addEventListener("click", () => {
      searchInput.value = "";
      this.searchTerm = "";
      clearBtn.style.display = "none";
      this.currentPage = 1;
      this.applyFilters();
      searchInput.focus();
    });

    toolbar.appendChild(searchBox);

    // Right Controls Group: Status Filter + Page Size Selector
    const rightGroup = document.createElement("div");
    rightGroup.className = "table-controls-right";

    // Optional Status Dropdown Filter
    const statuses = this.extractStatuses();
    if (this.options.statusFilter && statuses.length > 1) {
      const statusSelect = document.createElement("select");
      statusSelect.className = "table-filter-select";
      let statusOptions = '<option value="ALL">All Statuses</option>';
      statuses.forEach((s) => {
        statusOptions += `<option value="${s}">${s}</option>`;
      });
      statusSelect.innerHTML = statusOptions;
      statusSelect.addEventListener("change", (e) => {
        this.statusFilterVal = e.target.value;
        this.currentPage = 1;
        this.applyFilters();
      });
      rightGroup.appendChild(statusSelect);
    }

    // Page Size Selector
    const pageSizeWrap = document.createElement("div");
    pageSizeWrap.className = "table-pagesize-wrap";
    pageSizeWrap.innerHTML = `
      <span style="font-size: 11.5px; color: var(--text-secondary); font-weight: 600;">Show:</span>
      <select class="table-pagesize-select">
        <option value="5" ${this.pageSize === 5 ? "selected" : ""}>5</option>
        <option value="10" ${this.pageSize === 10 ? "selected" : ""}>10</option>
        <option value="25" ${this.pageSize === 25 ? "selected" : ""}>25</option>
        <option value="all" ${this.pageSize === "all" ? "selected" : ""}>All</option>
      </select>
    `;

    const pageSizeSelect = pageSizeWrap.querySelector(".table-pagesize-select");
    pageSizeSelect.addEventListener("change", (e) => {
      const val = e.target.value;
      this.pageSize = val === "all" ? "all" : parseInt(val, 10);
      this.currentPage = 1;
      this.render();
    });

    rightGroup.appendChild(pageSizeWrap);
    toolbar.appendChild(rightGroup);

    // Insert toolbar before table
    wrapper.insertBefore(toolbar, this.table);

    // Bottom Pagination Footer
    const footer = document.createElement("div");
    footer.className = "table-pagination-footer";
    wrapper.appendChild(footer);
    this.footer = footer;
  }

  extractStatuses() {
    const statuses = new Set();
    this.allRows.forEach((row) => {
      // Look for badges or status columns
      const badges = row.querySelectorAll("span, td");
      badges.forEach((el) => {
        const text = el.textContent.trim();
        if (["Active", "Draft", "Inactive", "Positive", "Credit Line", "Zero Balance", "OPEN", "PARTIALLY_PAID", "PAID"].includes(text)) {
          statuses.add(text);
        }
      });
    });
    return Array.from(statuses);
  }

  setupSorting() {
    const headers = this.table.querySelectorAll("thead th");
    headers.forEach((th, idx) => {
      th.classList.add("sortable-th");
      th.setAttribute("title", "Click to sort");
      
      const sortIcon = document.createElement("span");
      sortIcon.className = "sort-indicator";
      sortIcon.textContent = "↕";
      th.appendChild(sortIcon);

      th.addEventListener("click", () => {
        if (this.currentSortCol === idx) {
          this.currentSortDir = this.currentSortDir === "asc" ? "desc" : "asc";
        } else {
          this.currentSortCol = idx;
          this.currentSortDir = "asc";
        }

        // Update indicators
        headers.forEach((h, hIdx) => {
          const icon = h.querySelector(".sort-indicator");
          if (icon) {
            if (hIdx === idx) {
              icon.textContent = this.currentSortDir === "asc" ? "▲" : "▼";
              h.classList.add("sorted");
            } else {
              icon.textContent = "↕";
              h.classList.remove("sorted");
            }
          }
        });

        this.sortRows(idx, this.currentSortDir);
        this.render();
      });
    });
  }

  parseCellValue(cell) {
    if (!cell) return "";
    let text = cell.textContent.trim();
    // Currency or numeric check: e.g. "$21,448.60" or "97.4%" or "2,160"
    const cleaned = text.replace(/[$,%]/g, "").replace(/\s+/g, "");
    if (!isNaN(cleaned) && cleaned !== "") {
      return parseFloat(cleaned);
    }
    return text.toLowerCase();
  }

  sortRows(colIdx, dir) {
    this.filteredRows.sort((a, b) => {
      const cellA = a.children[colIdx];
      const cellB = b.children[colIdx];
      const valA = this.parseCellValue(cellA);
      const valB = this.parseCellValue(cellB);

      let comparison = 0;
      if (typeof valA === "number" && typeof valB === "number") {
        comparison = valA - valB;
      } else {
        comparison = String(valA).localeCompare(String(valB));
      }

      return dir === "asc" ? comparison : -comparison;
    });
  }

  applyFilters() {
    this.filteredRows = this.allRows.filter((row) => {
      const text = row.textContent.toLowerCase();
      const matchesSearch = !this.searchTerm || text.includes(this.searchTerm);

      let matchesStatus = true;
      if (this.statusFilterVal !== "ALL") {
        matchesStatus = text.includes(this.statusFilterVal.toLowerCase());
      }

      return matchesSearch && matchesStatus;
    });

    if (this.currentSortCol !== -1) {
      this.sortRows(this.currentSortCol, this.currentSortDir);
    }

    this.render();
  }

  render() {
    const totalEntries = this.filteredRows.length;
    let totalPages = 1;
    let startIdx = 0;
    let endIdx = totalEntries;

    if (this.pageSize !== "all") {
      totalPages = Math.ceil(totalEntries / this.pageSize) || 1;
      if (this.currentPage > totalPages) this.currentPage = totalPages;
      if (this.currentPage < 1) this.currentPage = 1;

      startIdx = (this.currentPage - 1) * this.pageSize;
      endIdx = Math.min(startIdx + this.pageSize, totalEntries);
    }

    // Hide all rows then show only the current page rows
    this.allRows.forEach((r) => (r.style.display = "none"));

    if (totalEntries === 0) {
      let emptyRow = this.tbody.querySelector(".table-empty-row");
      if (!emptyRow) {
        emptyRow = document.createElement("tr");
        emptyRow.className = "table-empty-row";
        emptyRow.innerHTML = `<td colspan="100%" style="text-align: center; padding: 28px; color: var(--text-muted);">
          🔍 No matching records found for "${this.searchTerm}".
        </td>`;
        this.tbody.appendChild(emptyRow);
      }
      emptyRow.style.display = "";
    } else {
      const emptyRow = this.tbody.querySelector(".table-empty-row");
      if (emptyRow) emptyRow.style.display = "none";

      for (let i = startIdx; i < endIdx; i++) {
        if (this.filteredRows[i]) {
          this.filteredRows[i].style.display = "";
        }
      }
    }

    this.renderFooter(totalEntries, startIdx, endIdx, totalPages);
  }

  renderFooter(totalEntries, startIdx, endIdx, totalPages) {
    if (!this.footer) return;

    let infoText = "";
    if (totalEntries === 0) {
      infoText = "Showing 0 entries";
    } else if (this.pageSize === "all") {
      infoText = `Showing all <strong>${totalEntries}</strong> entries`;
    } else {
      infoText = `Showing <strong>${startIdx + 1}</strong> to <strong>${endIdx}</strong> of <strong>${totalEntries}</strong> entries`;
      if (totalEntries < this.allRows.length) {
        infoText += ` (filtered from ${this.allRows.length} total)`;
      }
    }

    let paginationBtns = "";
    if (this.pageSize !== "all" && totalPages > 1) {
      paginationBtns += `<button type="button" class="page-nav-btn ${this.currentPage === 1 ? "disabled" : ""}" data-page="${this.currentPage - 1}">« Prev</button>`;
      
      for (let p = 1; p <= totalPages; p++) {
        // Show all if <= 7 pages, or condensed
        if (totalPages <= 7 || p === 1 || p === totalPages || (p >= this.currentPage - 1 && p <= this.currentPage + 1)) {
          paginationBtns += `<button type="button" class="page-num-btn ${p === this.currentPage ? "active" : ""}" data-page="${p}">${p}</button>`;
        } else if (p === this.currentPage - 2 || p === this.currentPage + 2) {
          paginationBtns += `<span class="page-ellipsis">...</span>`;
        }
      }

      paginationBtns += `<button type="button" class="page-nav-btn ${this.currentPage === totalPages ? "disabled" : ""}" data-page="${this.currentPage + 1}">Next »</button>`;
    }

    this.footer.innerHTML = `
      <div class="table-info-counter">${infoText}</div>
      <div class="table-pagination-nav">${paginationBtns}</div>
    `;

    // Bind page click events
    this.footer.querySelectorAll("button[data-page]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const p = parseInt(btn.getAttribute("data-page"), 10);
        if (p >= 1 && p <= totalPages && p !== this.currentPage) {
          this.currentPage = p;
          this.render();
        }
      });
    });
  }
}

// Auto-initialize on all tables with class `.enterprise-table`
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".enterprise-table").forEach((tbl) => {
    // Avoid double init
    if (!tbl.dataset.tableManaged) {
      tbl.dataset.tableManaged = "true";
      new EnterpriseTableManager(tbl);
    }
  });
});
