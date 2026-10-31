/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  safelist: [
    'bg-orange-500/20',
    'bg-blue-500/20',
    'bg-purple-500/20',
    'bg-green-500/20',
    'bg-slate-500/20',
    'border-orange-500',
    'border-blue-500',
    'border-purple-500',
    'border-green-500',
    'border-slate-500',
    'text-orange-400',
    'text-blue-400',
    'text-purple-400',
    'text-green-400',
    'text-slate-400',
  ],
  theme: {
    extend: {},
  },
  plugins: [],
};
