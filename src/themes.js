'use strict';

const THEMES = {
  midnight: {
    label: 'midnight',
    bgFrom: '#0d1117',
    bgTo: '#161b22',
    border: '#00FF9D',
    accent: '#00FF9D',
    accentSoft: '#00C97D',
    secondary: '#FF5B67',
    text: '#f0f6fc',
    muted: '#8b949e',
    divider: '#30363d',
  },
  matrix: {
    label: 'matrix',
    bgFrom: '#000000',
    bgTo: '#0a140a',
    border: '#00FF41',
    accent: '#00FF41',
    accentSoft: '#00B82E',
    secondary: '#39FF14',
    text: '#D9FFD9',
    muted: '#4D9C4D',
    divider: '#1a3a1a',
  },
  synthwave: {
    label: 'synthwave',
    bgFrom: '#1a0633',
    bgTo: '#3a0a5e',
    border: '#FF2A6D',
    accent: '#00F0FF',
    accentSoft: '#00B8D4',
    secondary: '#FF2A6D',
    text: '#F8E8FF',
    muted: '#A479C4',
    divider: '#5C2A8A',
  },
  inferno: {
    label: 'inferno',
    bgFrom: '#1a0908',
    bgTo: '#2a1310',
    border: '#FF6B35',
    accent: '#FFAA00',
    accentSoft: '#FF8C00',
    secondary: '#FF3B30',
    text: '#FFF0E0',
    muted: '#B87355',
    divider: '#3a1a1a',
  },
  frost: {
    label: 'frost',
    bgFrom: '#f8fafc',
    bgTo: '#e2e8f0',
    border: '#0EA5E9',
    accent: '#0284C7',
    accentSoft: '#0369A1',
    secondary: '#6366F1',
    text: '#0f172a',
    muted: '#475569',
    divider: '#cbd5e1',
  },
};

const THEME_NAMES = Object.keys(THEMES);

function utcDayOfYear(date = new Date()) {
  const start = Date.UTC(date.getUTCFullYear(), 0, 0);
  const today = Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate());
  return Math.floor((today - start) / 86_400_000);
}

function pickTheme(input) {
  const value = (input || '').trim().toLowerCase();
  if (value === 'random') {
    return THEME_NAMES[Math.floor(Math.random() * THEME_NAMES.length)];
  }
  if (value === 'rotate' || value === '') {
    return THEME_NAMES[utcDayOfYear() % THEME_NAMES.length];
  }
  if (THEMES[value]) return value;
  console.warn(`[thm-badge] Unknown theme "${input}", falling back to "midnight".`);
  return 'midnight';
}

module.exports = { THEMES, THEME_NAMES, pickTheme, utcDayOfYear };
