import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import AstroPWA from '@vite-pwa/astro';

export default defineConfig({
  integrations: [
    tailwind(),
    AstroPWA({
      mode: 'development',
      base: '/pypi-query-mcp-server',
      scope: '/pypi-query-mcp-server',
      includeAssets: ['favicon.svg'],
      registerType: 'autoUpdate',
      manifest: {
        name: '🎤 mcpypi Guest Book - Retro Edition',
        short_name: 'mcpypi Guest Book',
        description: 'The most radical guest book for Python developers! Sign in and show off your PyPI packages!',
        theme_color: '#800080',
        background_color: '#000080',
        display: 'standalone',
        orientation: 'portrait',
        scope: '/pypi-query-mcp-server',
        start_url: '/pypi-query-mcp-server',
        icons: [
          {
            src: '/icon-192.png',
            sizes: '192x192',
            type: 'image/png',
          },
          {
            src: '/icon-512.png',
            sizes: '512x512',
            type: 'image/png',
          },
          {
            src: '/icon-512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'any maskable',
          },
        ],
      },
      workbox: {
        navigateFallback: '/pypi-query-mcp-server',
        globPatterns: ['**/*.{css,js,html,svg,png,ico,txt}'],
      },
      devOptions: {
        enabled: true,
        navigateFallbackAllowlist: [/^\/pypi-query-mcp-server/],
      },
    }),
  ],
  site: 'https://yourusername.github.io',
  base: '/pypi-query-mcp-server',
  outDir: './dist',
  experimental: {
    contentCollectionCache: true,
  },
});