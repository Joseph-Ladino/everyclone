<script setup>
import { ref, onMounted } from 'vue';

const theme = ref('light');

// Run this the second the app boots
onMounted(() => {
    // 1. Check if they saved a preference previously
    const savedTheme = localStorage.getItem('theme');

    // 2. If not, check if their operating system prefers dark mode
    if (savedTheme) {
        theme.value = savedTheme;
    } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        theme.value = 'dark';
    }

    // 3. Apply it to the HTML tag
    document.documentElement.setAttribute('data-theme', theme.value);
});

const toggleTheme = () => {
    theme.value = theme.value === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', theme.value);
    localStorage.setItem('theme', theme.value); // Save it for next time
};
</script>

<template>
    <nav class="navbar" v-if="!$route.meta.hideNavbar">
        <RouterLink to="/" class="logo">EP Pro</RouterLink>
        <button @click="toggleTheme" class="theme-toggle">
            {{ theme === 'dark' ? '☀️ Light Mode' : '🌙 Dark Mode' }}
        </button>
    </nav>

    <main class="content-window">
        <RouterView />
    </main>
</template>

<style scoped>
.navbar {
    padding: 1rem 2rem;
    background: var(--bg-surface);
    border-bottom: 1px solid var(--border-color);
    display: flex;
    justify-content: space-between;
    /* Pushes the button to the right */
    align-items: center;
}

.logo {
    font-size: 1.5rem;
    font-weight: bold;
    color: var(--accent);
    text-decoration: none;
    transition: color 0.2s ease;
}

.logo:hover {
    color: var(--accent-hover);
}

.content-window {
    padding: 2rem;
}

.theme-toggle {
    background-color: var(--bg-page);
    border: 1px solid var(--border-color);
    color: var(--text-main);
    padding: 0.5rem 1rem;
    border-radius: 8px;
    cursor: pointer;
    font-weight: 600;
    transition: all 0.2s ease;
}

.theme-toggle:hover {
    filter: brightness(0.9);
    color: var(--accent-hover);
    box-shadow: 0px 4px 6px -3px var(--accent-hover);
}
</style>