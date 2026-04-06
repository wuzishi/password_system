<template>
  <router-view />
</template>

<script setup>
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  height: 100%;
}

:root {
  --bg-primary: #0a0a0b;
  --bg-elevated: #141415;
  --bg-hover: #1a1a1c;
  --bg-active: #222224;
  --text-primary: #ececec;
  --text-secondary: #a1a1a6;
  --text-tertiary: #5a5a5e;
  --border-subtle: rgba(255, 255, 255, 0.06);
  --border-default: rgba(255, 255, 255, 0.1);
  --accent: #ececec;
  --accent-dim: rgba(255, 255, 255, 0.08);
  --green: #3ecf8e;
  --yellow: #f5a623;
  --red: #ef4444;
  --purple: #a78bfa;
  --radius: 8px;

  /* Element Plus overrides */
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
  --el-color-primary: #ececec;
  --el-color-primary-light-3: rgba(236, 236, 236, 0.3);
  --el-color-primary-light-5: rgba(236, 236, 236, 0.15);
  --el-color-primary-light-7: rgba(236, 236, 236, 0.08);
  --el-color-primary-light-8: rgba(236, 236, 236, 0.06);
  --el-color-primary-light-9: rgba(236, 236, 236, 0.04);
  --el-color-primary-dark-2: #d4d4d4;
  --el-color-success: #3ecf8e;
  --el-color-warning: #f5a623;
  --el-color-danger: #ef4444;
  --el-color-info: #6b7280;
  --el-mask-color: rgba(0, 0, 0, 0.7);
  --el-box-shadow: 0 4px 24px rgba(0, 0, 0, 0.4);
  --el-box-shadow-light: 0 2px 12px rgba(0, 0, 0, 0.3);

  /* Dialog */
  --el-dialog-bg-color: var(--bg-elevated);
  --el-dialog-box-shadow: 0 12px 48px rgba(0, 0, 0, 0.5);

  /* Table */
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: var(--bg-elevated);
  --el-table-row-hover-bg-color: var(--bg-hover);
  --el-table-border-color: var(--border-subtle);
  --el-table-header-text-color: var(--text-tertiary);
  --el-table-text-color: var(--text-primary);

  /* Card */
  --el-card-bg-color: var(--bg-elevated);
  --el-card-border-color: var(--border-subtle);

  /* Input */
  --el-input-bg-color: var(--bg-primary);
  --el-input-border-color: var(--border-default);
  --el-input-text-color: var(--text-primary);
  --el-input-placeholder-color: var(--text-tertiary);
  --el-input-hover-border-color: rgba(255, 255, 255, 0.2);
  --el-input-focus-border-color: rgba(255, 255, 255, 0.3);

  /* Menu */
  --el-menu-bg-color: transparent;
  --el-menu-text-color: var(--text-secondary);
  --el-menu-active-color: var(--text-primary);
  --el-menu-hover-bg-color: var(--bg-hover);
  --el-menu-item-height: 44px;

  /* Popover */
  --el-popover-bg-color: var(--bg-elevated);
  --el-popover-border-color: var(--border-default);

  /* Tag */
  --el-tag-bg-color: var(--accent-dim);
  --el-tag-border-color: transparent;
  --el-tag-text-color: var(--text-secondary);

  /* Tabs */
  --el-border-color-light: var(--border-subtle);
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 14px;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* Global Element Plus refinements */

.el-card {
  --el-card-padding: 20px;
  border-radius: var(--radius) !important;
  box-shadow: none !important;
}

.el-card__header {
  padding: 16px 20px !important;
  border-bottom: 1px solid var(--border-subtle) !important;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.el-table {
  --el-table-border: none;
  font-size: 13px;
}

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
  --el-button-bg-color: var(--text-primary);
  --el-button-border-color: var(--text-primary);
  --el-button-text-color: var(--bg-primary);
  --el-button-hover-bg-color: #d4d4d4;
  --el-button-hover-border-color: #d4d4d4;
  --el-button-hover-text-color: var(--bg-primary);
  font-weight: 500;
}

.el-button--default {
  --el-button-bg-color: transparent;
  --el-button-border-color: var(--border-default);
  --el-button-text-color: var(--text-secondary);
  --el-button-hover-bg-color: var(--bg-hover);
  --el-button-hover-border-color: var(--border-default);
  --el-button-hover-text-color: var(--text-primary);
}

.el-dialog {
  border-radius: 12px !important;
  border: 1px solid var(--border-subtle);
}

.el-dialog__header {
  border-bottom: 1px solid var(--border-subtle);
  padding: 16px 20px !important;
  margin-right: 0 !important;
}

.el-dialog__title {
  font-size: 15px;
  font-weight: 600;
}

.el-dialog__footer {
  border-top: 1px solid var(--border-subtle);
  padding: 12px 20px !important;
}

.el-form-item__label {
  color: var(--text-secondary) !important;
  font-size: 13px !important;
}

.el-input__wrapper {
  background-color: var(--bg-primary) !important;
  box-shadow: 0 0 0 1px var(--border-default) inset !important;
  border-radius: 6px !important;
  transition: box-shadow 0.15s ease;
}

.el-input__wrapper:hover {
  box-shadow: 0 0 0 1px rgba(255,255,255,0.2) inset !important;
}

.el-input__wrapper.is-focus {
  box-shadow: 0 0 0 1px rgba(255,255,255,0.3) inset !important;
}

.el-select__wrapper {
  background-color: var(--bg-primary) !important;
  box-shadow: 0 0 0 1px var(--border-default) inset !important;
  border-radius: 6px !important;
}

.el-alert {
  border-radius: var(--radius) !important;
  border: 1px solid var(--border-subtle) !important;
  background: var(--bg-elevated) !important;
}

.el-alert .el-alert__title {
  color: var(--text-primary) !important;
}

.el-alert--error {
  border-color: rgba(239, 68, 68, 0.2) !important;
}

.el-alert--warning {
  border-color: rgba(245, 166, 35, 0.2) !important;
}

.el-tabs__item {
  color: var(--text-tertiary) !important;
  font-size: 13px;
}

.el-tabs__item.is-active {
  color: var(--text-primary) !important;
}

.el-tabs__active-bar {
  background-color: var(--text-primary) !important;
}

.el-tag {
  border-radius: 4px !important;
  font-size: 12px;
  font-weight: 500;
}

.el-tag--dark {
  border: none !important;
}

.el-popconfirm {
  --el-popover-bg-color: var(--bg-elevated);
}

.el-dropdown-menu {
  background-color: var(--bg-elevated) !important;
  border: 1px solid var(--border-default) !important;
  border-radius: var(--radius) !important;
}

.el-dropdown-menu__item {
  color: var(--text-secondary) !important;
}

.el-dropdown-menu__item:hover {
  background-color: var(--bg-hover) !important;
  color: var(--text-primary) !important;
}

.el-pagination button, .el-pagination .el-pager li {
  background: transparent !important;
  color: var(--text-tertiary) !important;
}

.el-pagination .el-pager li.is-active {
  color: var(--text-primary) !important;
}

/* Scrollbar */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.2);
}

/* Selection */
::selection {
  background: rgba(236, 236, 236, 0.2);
}

h2 {
  font-size: 20px;
  font-weight: 600;
  letter-spacing: -0.3px;
}
</style>
