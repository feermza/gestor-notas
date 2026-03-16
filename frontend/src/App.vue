<script setup>
// Toast global para notificaciones (PrimeVue)
</script>

<template>
  <Toast position="top-right" />
  <router-view />
</template>

<style>
/* ── DataTable ── */
.p-datatable {
  background-color: white !important;
}
.p-datatable-table {
  background-color: white !important;
}
.p-datatable-thead > tr > th {
  background-color: #f8fafc !important;
  color: #1e293b !important;
  border-bottom: 2px solid #e2e8f0 !important;
}
.p-datatable-tbody > tr {
  background-color: white !important;
  color: #1e293b !important;
}
.p-datatable-tbody > tr:hover {
  background-color: #f1f5f9 !important;
}
.p-datatable-tbody > tr.fila-atrasada {
  background-color: #fff5f5 !important;
}
.p-datatable .p-datatable-tbody > tr > td {
  word-break: break-word;
}
.p-paginator {
  background-color: white !important;
  color: #1e293b !important;
  border-top: 1px solid #e2e8f0 !important;
}

/* ── Dialog ── */
.p-dialog {
  --p-dialog-background: #ffffff !important;
  --p-dialog-color: #1e293b !important;
  --p-dialog-border-color: #e2e8f0 !important;
  background-color: white !important;
}
.p-dialog-header {
  background-color: white !important;
  color: #1e3a5f !important;
}
.p-dialog-header .p-dialog-title {
  color: #1e3a5f !important;
}
.p-dialog-header .p-button-icon {
  color: #1e293b !important;
}
.p-dialog-content {
  background-color: white !important;
  color: #1e293b !important;
}
.p-dialog-footer {
  background-color: white !important;
  border-top: 1px solid #e2e8f0 !important;
}

/* ── InputText / InputNumber ── */
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
/* Inputs dentro de dialogs (algunas vistas usan fondo blanco) */
.p-dialog .p-inputtext,
.p-dialog .p-inputnumber-input,
.p-dialog .p-textarea,
.p-dialog input,
.p-dialog textarea {
  background-color: white !important;
  color: #1e293b !important;
  border: 1px solid #e2e8f0 !important;
}

/* ── Select / Dropdown ── */
.p-select,
.p-select-overlay,
.p-select-list,
.p-select-panel {
  background-color: white !important;
  color: #1e293b !important;
  border: 1px solid #e2e8f0 !important;
}
.p-select-option {
  color: #1e293b !important;
  background-color: white !important;
}
.p-select-option:hover,
.p-select-option.p-focus {
  background-color: #f1f5f9 !important;
  color: #1e293b !important;
}
.p-select-label {
  color: #1e293b !important;
}
.p-placeholder {
  color: #94a3b8 !important;
}

/* ── Textarea ── */
textarea,
.p-textarea {
  background-color: #f8fafc !important;
  color: #1e293b !important;
  border: 1px solid #e2e8f0 !important;
}
textarea::placeholder {
  color: #94a3b8 !important;
}

/* ── TabView ── */
/* (sin overrides específicos en las vistas revisadas) */

/* ── Card ── */
.p-card {
  background-color: white !important;
  color: #1e293b !important;
}
.p-card-title {
  color: #1e3a5f !important;
  font-size: 1rem !important;
  font-weight: 600 !important;
}

/* ── Button ── */
/* Botón con label blanco cuando va con estilo primario (ej. NotasView "Nueva Nota") */
.p-button-label {
  color: inherit;
}

/* ── Toast ── */
/* (Toast de PrimeVue usa posicionamiento; toasts custom están en vistas con slide-down) */

/* ── Transition slide-down ── */
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.3s ease;
}
.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-1rem);
}

/* Tag prioridad URGENTE: animación de pulso */
@keyframes pulso {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}
.tag-urgente {
  animation: pulso 1.5s ease-in-out infinite;
}
</style>
