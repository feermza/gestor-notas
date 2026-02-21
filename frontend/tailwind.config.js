/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js}'],
  theme: {
    extend: {
      colors: {
        primario: 'var(--color-primario)',
        secundario: 'var(--color-secundario)',
        acento: 'var(--color-acento)',
        alerta: 'var(--color-alerta)',
        ok: 'var(--color-ok)',
      },
    },
  },
  plugins: [],
}
