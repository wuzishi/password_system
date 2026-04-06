<template>
  <router-view />
</template>

<script setup>
import { useThemeStore } from './stores/theme'
useThemeStore() // Initialize theme on app start
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

* { margin: 0; padding: 0; box-sizing: border-box; }
html, body, #app { height: 100%; }

/* ========== Dark Theme (default) ========== */
:root,
[data-theme="dark"] {
  --bg-primary: #09090b;
  --bg-elevated: #131316;
  --bg-surface: #1a1a1e;
  --bg-hover: #1f1f24;
  --bg-active: #27272c;
  --text-primary: #f0f0f0;
  --text-secondary: #a0a0a8;
  --text-tertiary: #55555e;
  --border-subtle: rgba(255,255,255,0.06);
  --border-default: rgba(255,255,255,0.1);
  --border-strong: rgba(255,255,255,0.18);
  --accent: #f0f0f0;
  --accent-hover: #d4d4d4;
  --accent-bg: rgba(255,255,255,0.08);
  --green: #34d399;
  --yellow: #fbbf24;
  --red: #f87171;
  --purple: #a78bfa;
  --blue: #60a5fa;
  --shadow-card: 0 1px 3px rgba(0,0,0,0.3);
  --shadow-dialog: 0 16px 64px rgba(0,0,0,0.5);
}

/* ========== Light Theme ========== */
[data-theme="light"] {
  --bg-primary: #f8f9fa;
  --bg-elevated: #ffffff;
  --bg-surface: #f1f3f5;
  --bg-hover: #e9ecef;
  --bg-active: #dee2e6;
  --text-primary: #111111;
  --text-secondary: #555555;
  --text-tertiary: #999999;
  --border-subtle: rgba(0,0,0,0.06);
  --border-default: rgba(0,0,0,0.1);
  --border-strong: rgba(0,0,0,0.18);
  --accent: #111111;
  --accent-hover: #333333;
  --accent-bg: rgba(0,0,0,0.05);
  --green: #16a34a;
  --yellow: #d97706;
  --red: #dc2626;
  --purple: #7c3aed;
  --blue: #2563eb;
  --shadow-card: 0 1px 3px rgba(0,0,0,0.08);
  --shadow-dialog: 0 16px 64px rgba(0,0,0,0.12);
}

/* ========== Element Plus Variable Bridge ========== */
:root, [data-theme="dark"], [data-theme="light"] {
  --el-bg-color: var(--bg-primary);
  --el-bg-color-overlay: var(--bg-elevated);
  --el-bg-color-page: var(--bg-primary);
  --el-text-color-primary: var(--text-primary);
  --el-text-color-regular: var(--text-secondary);
  --el-text-color-secondary: var(--text-tertiary);
  --el-text-color-placeholder: var(--text-tertiary);
  --el-border-color: var(--border-default);
  --el-border-color-light: var(--border-subtle);
  --el-border-color-lighter: var(--border-subtle);
  --el-border-color-extra-light: var(--border-subtle);
  --el-fill-color: var(--bg-hover);
  --el-fill-color-light: var(--bg-elevated);
  --el-fill-color-lighter: var(--bg-elevated);
  --el-fill-color-blank: var(--bg-elevated);
  --el-color-primary: var(--accent);
  --el-color-primary-light-3: var(--accent-bg);
  --el-color-primary-light-5: var(--accent-bg);
  --el-color-primary-light-7: var(--accent-bg);
  --el-color-primary-light-8: var(--accent-bg);
  --el-color-primary-light-9: var(--accent-bg);
  --el-color-primary-dark-2: var(--accent-hover);
  --el-color-success: var(--green);
  --el-color-warning: var(--yellow);
  --el-color-danger: var(--red);
  --el-color-info: #6b7280;
  --el-mask-color: rgba(0,0,0,0.5);
  --el-box-shadow: var(--shadow-dialog);
  --el-box-shadow-light: var(--shadow-card);
  --el-dialog-bg-color: var(--bg-elevated);
  --el-dialog-box-shadow: var(--shadow-dialog);
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: var(--bg-surface);
  --el-table-row-hover-bg-color: var(--bg-hover);
  --el-table-border-color: var(--border-subtle);
  --el-table-header-text-color: var(--text-tertiary);
  --el-table-text-color: var(--text-primary);
  --el-card-bg-color: var(--bg-elevated);
  --el-card-border-color: var(--border-subtle);
  --el-input-bg-color: var(--bg-primary);
  --el-input-border-color: var(--border-default);
  --el-input-text-color: var(--text-primary);
  --el-input-placeholder-color: var(--text-tertiary);
  --el-input-hover-border-color: var(--border-strong);
  --el-input-focus-border-color: var(--border-strong);
  --el-menu-bg-color: transparent;
  --el-menu-text-color: var(--text-secondary);
  --el-menu-active-color: var(--text-primary);
  --el-menu-hover-bg-color: var(--bg-hover);
  --el-menu-item-height: 44px;
  --el-popover-bg-color: var(--bg-elevated);
  --el-popover-border-color: var(--border-default);
  --el-tag-bg-color: var(--accent-bg);
  --el-tag-border-color: transparent;
  --el-tag-text-color: var(--text-secondary);
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 14px;
  -webkit-font-smoothing: antialiased;
  transition: background 0.3s, color 0.3s;
}

/* ========== Component Overrides ========== */

.el-card {
  --el-card-padding: 24px;
  border-radius: 12px !important;
  box-shadow: var(--shadow-card) !important;
}
.el-card__header {
  padding: 18px 24px !important;
  border-bottom: 1px solid var(--border-subtle) !important;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.el-table { --el-table-border: none; font-size: 13px; }
.el-table th.el-table__cell {
  font-weight: 500 !important;
  font-size: 12px !important;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  color: var(--text-tertiary) !important;
}
.el-table--striped .el-table__body tr.el-table__row--striped td.el-table__cell {
  background: transparent !important;
}
.el-button--primary {
  --el-button-bg-color: var(--accent);
  --el-button-border-color: var(--accent);
  --el-button-text-color: var(--bg-primary);
  --el-button-hover-bg-color: var(--accent-hover);
  --el-button-hover-border-color: var(--accent-hover);
  --el-button-hover-text-color: var(--bg-primary);
  font-weight: 500;
  border-radius: 8px !important;
}
.el-button--default {
  --el-button-bg-color: transparent;
  --el-button-border-color: var(--border-default);
  --el-button-text-color: var(--text-secondary);
  --el-button-hover-bg-color: var(--bg-hover);
  --el-button-hover-border-color: var(--border-default);
  --el-button-hover-text-color: var(--text-primary);
  border-radius: 8px !important;
}
.el-dialog {
  border-radius: 16px !important;
  border: 1px solid var(--border-subtle);
}
.el-dialog__header {
  border-bottom: 1px solid var(--border-subtle);
  padding: 20px 24px !important;
  margin-right: 0 !important;
}
.el-dialog__title { font-size: 16px; font-weight: 600; }
.el-dialog__footer {
  border-top: 1px solid var(--border-subtle);
  padding: 14px 24px !important;
}
.el-form-item__label {
  color: var(--text-secondary) !important;
  font-size: 13px !important;
}
.el-input__wrapper {
  background-color: var(--bg-primary) !important;
  box-shadow: 0 0 0 1px var(--border-default) inset !important;
  border-radius: 8px !important;
  transition: box-shadow 0.15s ease;
}
.el-input__wrapper:hover {
  box-shadow: 0 0 0 1px var(--border-strong) inset !important;
}
.el-input__wrapper.is-focus {
  box-shadow: 0 0 0 1.5px var(--border-strong) inset !important;
}
.el-select__wrapper {
  background-color: var(--bg-primary) !important;
  box-shadow: 0 0 0 1px var(--border-default) inset !important;
  border-radius: 8px !important;
}
.el-alert {
  border-radius: 12px !important;
  border: 1px solid var(--border-subtle) !important;
  background: var(--bg-elevated) !important;
}
.el-alert .el-alert__title { color: var(--text-primary) !important; }
.el-alert--error { border-color: rgba(248,113,113,0.2) !important; }
.el-alert--warning { border-color: rgba(251,191,36,0.2) !important; }
.el-tabs__item { color: var(--text-tertiary) !important; font-size: 14px; }
.el-tabs__item.is-active { color: var(--text-primary) !important; }
.el-tabs__active-bar { background-color: var(--text-primary) !important; }
.el-tag { border-radius: 6px !important; font-size: 12px; font-weight: 500; }
.el-tag--dark { border: none !important; }
.el-dropdown-menu {
  background-color: var(--bg-elevated) !important;
  border: 1px solid var(--border-default) !important;
  border-radius: 10px !important;
}
.el-dropdown-menu__item { color: var(--text-secondary) !important; }
.el-dropdown-menu__item:hover {
  background-color: var(--bg-hover) !important;
  color: var(--text-primary) !important;
}
.el-pagination button, .el-pagination .el-pager li {
  background: transparent !important;
  color: var(--text-tertiary) !important;
}
.el-pagination .el-pager li.is-active { color: var(--text-primary) !important; }
.el-radio-button__inner {
  background: var(--bg-primary) !important;
  border-color: var(--border-default) !important;
  color: var(--text-secondary) !important;
}
.el-radio-button__original-radio:checked + .el-radio-button__inner {
  background: var(--accent) !important;
  color: var(--bg-primary) !important;
  border-color: var(--accent) !important;
}
.el-checkbox__label { color: var(--text-secondary) !important; }
.el-empty__description p { color: var(--text-tertiary) !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border-default); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--border-strong); }

::selection { background: rgba(99,102,241,0.25); }

h2 { font-size: 22px; font-weight: 700; letter-spacing: -0.5px; }
</style>
