import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';

// https://vite.dev/config/
export default defineConfig({
    plugins: [vue()],
    resolve: {
        alias: {
            vue: 'vue/dist/vue.esm-bundler.js',
        },
    },
    server: {
        host: true,       // Exposes the server to the Docker network
        port: 5173,
        watch: {
            usePolling: true, // <--- THE MAGIC LINE
            interval: 100     // Checks every 100ms
        }
    }
})
