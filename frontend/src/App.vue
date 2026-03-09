<script setup>
// Toast global para notificaciones (PrimeVue)
</script>

<template>
  <Toast position="top-right" />
  <router-view />
</template>

<style>
.p-dialog {
  --p-dialog-background: #ffffff !important;
  --p-dialog-color: #1e293b !important;
  --p-dialog-border-color: #e2e8f0 !important;
}
.p-dialog-header {
  background-color: #1e3a5f !important;
  color: #ffffff !important;
}

.p-dialog-header .p-dialog-title {
  color: #ffffff !important;
}

.p-dialog-header .p-button-icon {
  color: #ffffff !important;
}

.p-dialog-content {
  background-color: #cbd5e1 !important;
  color: #1e293b !important;
}

.p-inputtext,
.p-inputnumber-input,
.p-select,
.p-select-label {
  background-color: #f8fafc !important;
  color: #1e293b !important;
  border: 1px solid #e2e8f0 !important;
}

.p-inputtext::placeholder,
.p-inputnumber-input::placeholder {
  color: #94a3b8 !important;
}

.p-select-label.p-placeholder {
  color: #94a3b8 !important;
}

.p-dialog-footer {
  background-color: #cbd5e1 !important;
  border-top: 2px solid #94a3b8 !important;
}

textarea,
.p-textarea {
  background-color: #f8fafc !important;
  color: #1e293b !important;
  border: 1px solid #e2e8f0 !important;
}

textarea::placeholder {
  color: #94a3b8 !important;
}
</style>
