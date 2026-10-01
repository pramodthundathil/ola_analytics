/**
 * Arrendadora Ola Cars AI Superuser - Frontend Interactions & Dynamic Engine
 * Handles Initial Startup Splash Screen, Theme Toggle, Bilingual Language Switcher,
 * Interactive Charts (Chart.js), and Live AI Chat Assistant.
 */

// Global State
const OlaApp = {
  theme: localStorage.getItem("ola_theme") || "dark",
  lang: document.documentElement.lang || "en",
  
  init() {
    this.applyTheme(this.theme);
    this.initSplashLoading();
    this.initThemeToggle();
    this.initSidebarToggle();
    this.initDemoButtons();
    this.initTimeFilters();
    this.initSpeechRecognition();
  },

  initSidebarToggle() {
    const toggleBtn = document.getElementById("sidebar-toggle");
    const sidebar = document.getElementById("app-sidebar");
    if (toggleBtn && sidebar) {
      toggleBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        sidebar.classList.toggle("sidebar-open");
      });
      document.addEventListener("click", (e) => {
        if (sidebar.classList.contains("sidebar-open") && !sidebar.contains(e.target) && !toggleBtn.contains(e.target)) {
          sidebar.classList.remove("sidebar-open");
        }
      });
    }
  },

  /* --------------------------------------------------------------------------
     Theme Management (Dark Mode #05080A / Light Mode #F7F9FA)
     -------------------------------------------------------------------------- */
  applyTheme(theme) {
    this.theme = theme;
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("ola_theme", theme);
    document.cookie = `ola_theme=${theme}; path=/; max-age=31536000`;
    
    // Update toggle icons if present
    const toggleBtn = document.getElementById("theme-toggle-btn");
    if (toggleBtn) {
      toggleBtn.innerHTML = theme === "dark" ? "☀️" : "🌙";
    }

    // Refresh charts if open to update axis colors
    if (window.revenueLineChart) window.revenueLineChart.update();
    if (window.vehicleDonutChart) window.vehicleDonutChart.update();
  },

  initThemeToggle() {
    const toggleBtn = document.getElementById("theme-toggle-btn");
    if (toggleBtn) {
      toggleBtn.addEventListener("click", () => {
        const nextTheme = this.theme === "dark" ? "light" : "dark";
        this.applyTheme(nextTheme);
      });
    }
  },

  /* --------------------------------------------------------------------------
     Initial Server Startup Loading Animation (Splash on Server Login Screen)
     -------------------------------------------------------------------------- */
  initSplashLoading() {
    const splash = document.getElementById("server-startup-splash");
    if (!splash) return;

    const progressBar = splash.querySelector(".splash-progress-bar");
    const statusText = splash.querySelector(".splash-status-text");

    const steps = [
      { pct: 25, delay: 300, en: "Initializing Ola Cars AI Engine...", es: "Iniciando motor de IA de Ola Cars..." },
      { pct: 60, delay: 800, en: "Verifying Read-Only ERP Database Connection...", es: "Verificando conexión segura de sólo lectura con ERP..." },
      { pct: 90, delay: 1300, en: "Loading Bilingual NLP Models (EN / ES)...", es: "Cargando modelos bilingües de PNL (EN / ES)..." },
      { pct: 100, delay: 1700, en: "System Online • Read-Only Security Active", es: "Sistema en Línea • Seguridad de Sólo Lectura Activa" }
    ];

    const currentLang = this.lang;

    steps.forEach((step) => {
      setTimeout(() => {
        if (progressBar) progressBar.style.width = step.pct + "%";
        if (statusText) statusText.textContent = currentLang === "es" ? step.es : step.en;
      }, step.delay);
    });

    // Dismiss splash smoothly after completion
    setTimeout(() => {
      splash.classList.add("splash-dismissed");
    }, 2200);
  },

  /* --------------------------------------------------------------------------
     Demo Login Quick Fill
     -------------------------------------------------------------------------- */
  initDemoButtons() {
    document.querySelectorAll(".demo-btn-fill").forEach((btn) => {
      btn.addEventListener("click", () => {
        const username = btn.getAttribute("data-user");
        const pass = btn.getAttribute("data-pass");
        const userInput = document.getElementById("username");
        const passInput = document.getElementById("password");
        if (userInput && passInput) {
          userInput.value = username;
          passInput.value = pass;
          userInput.focus();
        }
      });
    });
  },

  /* --------------------------------------------------------------------------
     Analytics Filter Tabs (7D, 30D, 3M, 6M, 1Y)
     -------------------------------------------------------------------------- */
  initTimeFilters() {
    const filterTabs = document.querySelectorAll(".filter-tab");
    filterTabs.forEach((tab) => {
      tab.addEventListener("click", () => {
        filterTabs.forEach((t) => t.classList.remove("active"));
        tab.classList.add("active");
        
        const period = tab.getAttribute("data-period");
        if (window.updateAnalyticsPeriod) {
          window.updateAnalyticsPeriod(period);
        }
      });
    });
  },

  /* --------------------------------------------------------------------------
     Speech Recognition (Microphone input)
     -------------------------------------------------------------------------- */
  initSpeechRecognition() {
    const micBtn = document.getElementById("mic-btn");
    const chatInput = document.getElementById("chat-input");
    if (!micBtn || !chatInput) return;

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = this.lang === "es" ? "es-ES" : "en-US";

      micBtn.addEventListener("click", () => {
        micBtn.style.color = "#ccff00";
        try {
          recognition.start();
        } catch (e) {
          recognition.stop();
        }
      });

      recognition.onresult = (event) => {
        const text = event.results[0][0].transcript;
        chatInput.value = text;
        micBtn.style.color = "";
        chatInput.focus();
      };

      recognition.onend = () => {
        micBtn.style.color = "";
      };
    } else {
      micBtn.addEventListener("click", () => {
        alert(this.lang === "es" ? "Reconocimiento de voz no soportado en este navegador." : "Voice recognition not supported in this browser.");
      });
    }
  }
};

// Initialize when DOM is ready
document.addEventListener("DOMContentLoaded", () => {
  OlaApp.init();
});
