<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';

import { getOptimalImage } from '../../utils/imageOptimizer';
import { getDisplayString } from '../../utils/ingredientFormatter';
import NutritionLabel from '../NutritionLabel.vue';

const route = useRoute();
const recipe = ref(null);
const loading = ref(true);
const portionScale = ref(1);

// onMounted runs the second this page is loaded onto the screen
onMounted(async () => {
    try {
        const res = await fetch(`${import.meta.env.VITE_API_URL}/recipes/${route.params.id}`);
        if (!res.ok) throw new Error("Failed to fetch");
        recipe.value = await res.json();
    } catch (error) {
        console.error(error);
    } finally {
        loading.value = false;
    }
});

const boxIngredients = computed(() => {
    if (!recipe.value) return [];
    return recipe.value.ingredients.filter(ing => ing.image_url);
});

const stapleIngredients = computed(() => {
    if (!recipe.value) return [];
    return recipe.value.ingredients.filter(ing => !ing.image_url);
});

</script>

<template>
    <div v-if="loading" class="loading">Loading recipe data...</div>

    <div v-else-if="recipe" class="recipe-layout">

        <div class="main-content">
            <div class="header">
                <h1>{{ recipe.name }}</h1>
                <p class="headline">{{ recipe.headline }}</p>
            </div>

            <img :src="getOptimalImage(recipe.image_url, 1000)" :alt="recipe.name" class="hero-image" />

            <div class="meta-bar">
                <span>⏱️ {{ recipe.prep_time_minutes }} Min.</span>
                <span v-if="recipe.rating">⭐ {{ recipe.rating.toFixed(1) }}</span>
                <a :href="recipe.web_link" target="_blank" class="ep-link">Original Recipe</a>
            </div>

            <div class="description-box" v-if="recipe.description">
                <p>{{ recipe.description }}</p>
            </div>

            <div class="ingredients-section">
                <div class="ing-header">
                    <h2>Core Ingredients</h2>
                    <div class="scale-controls">
                        <button @click="portionScale = Math.max(0.5, portionScale - 0.5)" class="btn-scale">−</button>
                        <span class="scale-readout">{{ 2 * portionScale }} serv.</span>
                        <button @click="portionScale += 0.5" class="btn-scale">+</button>
                    </div>
                </div>

                <ul class="ingredient-grid">
                    <li v-for="ing in boxIngredients" :key="ing.id" class="ingredient-item">
                        <RouterLink :to="`/ingredient/${ing.id}`" class="ing-link">
                            <img :src="getOptimalImage(ing.image_url, 80, 80)" :alt="ing.name" class="ing-thumb" />
                            <div class="ing-info">
                                <span class="name"> {{ ing.name }} </span>
                                <span class="amount">
                                    {{ getDisplayString(ing.amount, ing.unit, ing.unit_conversion, portionScale) }}
                                </span>
                            </div>
                            <span v-if="ing.is_blend" class="prep-badge">Prep</span>
                        </RouterLink>
                    </li>
                </ul>
            </div>
        </div>

        <div class="sidebar">
            <NutritionLabel :nutrition="recipe.nutrition" :allergens="recipe.allergens" />

            <div v-if="stapleIngredients.length" class="staples-card">
                <h2>Staple Ingredients</h2>
                <ul class="staples-list">
                    <li v-for="ing in stapleIngredients" :key="ing.id">
                        <span class="staple-name">{{ ing.name }}</span>
                        <span class="staple-amount">
                            {{ getDisplayString(ing.amount, ing.unit, ing.unit_conversion, portionScale) }}
                        </span>
                        <span v-if="ing.is_blend" class="prep-badge">Prep</span>
                    </li>
                </ul>
            </div>
        </div>

    </div>
</template>

<style scoped>
/* Responsive Grid: 1 column on mobile, 2 columns on desktop */
.recipe-layout {
    display: grid;
    grid-template-columns: 1fr;
    gap: 2rem;
    max-width: 1200px;
    margin: 0 auto;
}

@media (min-width: 900px) {
    .recipe-layout {
        grid-template-columns: 1fr 350px;
    }
}

/* Typography & Headers */
h1 {
    font-size: 2rem;
    margin-bottom: 0.25rem;
    color: var(--text-deep);
}

.headline {
    color: var(--text-muted);
    font-size: 1.2rem;
    font-weight: 500;
    margin-bottom: 1rem;
}

/* Images & Meta */
.hero-image {
    width: 100%;
    height: 400px;
    object-fit: cover;
    border: 1px solid var(--border-light);
    border-radius: 8px;
}

.meta-bar {
    display: flex;
    gap: 1.5rem;
    margin: 1rem 0;
    font-weight: bold;
    color: var(--text-muted);
    align-items: center;
    justify-content: center;
}

.ep-link {
    padding: 0.4rem 1rem;
    background: var(--bg-surface);
    color: var(--text-main);
    border-radius: 20px;
    text-decoration: none;
    font-size: 0.9rem;
    box-shadow: 0px 4px 6px -3px var(--shadow);
    transition: color 0.2s ease, box-shadow 0.2s ease, border 0.5s ease, background 0.5s ease;
}

.ep-link:hover {
    filter: brightness(0.9);
    color: var(--accent-hover);
    box-shadow: 0px 4px 6px -3px var(--accent-hover);
}

/* Description */
.description-box {
    background: var(--bg-surface);
    padding: 1.5rem;
    border-radius: 8px;
    border: 1px solid var(--border-color);
    margin-bottom: 2rem;
    color: var(--text-main);
    line-height: 1.6;
}

/* Ingredients Grid */
h2 {
    font-size: 1.5rem;
    margin: 0.1rem 0.25rem;
    color: var(--text-deep);
}

.ingredient-grid {
    list-style: none;
    padding: 0;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 1rem;
}

.ingredient-item {
    background: var(--bg-surface);
    padding: 0.75rem;
    border-radius: 8px;
    border: 1px solid var(--border-color);
    box-shadow: 0 4px 6px -3px var(--shadow);
    transition: box-shadow 0.2s ease, border 0.5s ease, background 0.5s ease;
}

.ingredient-item .name {
    color: var(--text-main);
    transition: color 0.2s ease, border 0.5s ease, background 0.5s ease;
}

.ingredient-item:hover {
    box-shadow: 0px 4px 6px -3px var(--accent-hover);
    filter: brightness(0.9);
    cursor: pointer;
}

.ingredient-item:hover .name {
    color: var(--accent-hover);
}

.ing-link {
    text-decoration: none;
    display: flex;
    align-items: center;
    gap: 1rem;
    position: relative;
}

.ing-thumb {
    width: 60px;
    height: 60px;
    object-fit: contain;
    background: var(--bg-page);
    border-radius: 50%;
    /* circle crop */
    padding: 4px;
    flex-shrink: 0;
    border: 1px solid var(--border-color);
}

.ing-info {
    display: flex;
    flex-direction: column;
}

.ing-info .name {
    font-weight: 600;
    /* color: var(--text-main); */
    font-size: 0.95rem;
}

.ing-info .amount {
    color: var(--text-faint);
    font-size: 0.85rem;
}

/* Sidebar Staples */
.staples-card {
    background: var(--bg-surface);
    border-radius: 12px;
    padding: 1.5rem;
    border: 1px solid var(--border-color);
    margin-top: 1.5rem;
    box-shadow: 0 1px 3px var(--shadow);
}

.staples-card h2 {
    font-size: 1.25rem;
}

.staples-list {
    list-style: circle inside;
    padding: 0;
}

.staples-list li {
    padding: 0.5rem 0;
    border-bottom: 1px solid var(--border-light);
    color: var(--text-muted);
    justify-content: space-between;
    display: flex;
}

.staples-list li:last-child {
    border-bottom: none;
}

.staple-name {
    font-weight: bold;
    color: var(--text-main);
}

.staple-amount {
    color: var(--text-faint);
    font-size: 0.85rem;
}

.prep-badge {
    display: inline-block;
    background: var(--accent);
    color: white;
    font-size: 0.65rem;
    font-weight: bold;
    text-transform: uppercase;
    padding: 0.15rem 0.4rem;
    border-radius: 12px;
    vertical-align: middle;
    width: fit-content;
    position: absolute;
    right: 0;
    bottom: 0;
}

.ing-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
}

.scale-controls {
    display: flex;
    align-items: center;
    background: var(--bg-page);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    overflow: hidden;
}

.btn-scale {
    background: none;
    border: none;
    color: var(--text-main);
    font-size: 1.2rem;
    padding: 0.2rem 0.8rem;
    cursor: pointer;
    transition: background 0.2s;
}

.btn-scale:hover {
    background: var(--border-light);
    color: var(--accent-hover);
    filter: brightness(0.9)
}

.scale-readout {
    font-weight: bold;
    font-size: 0.95rem;
    padding: 0 0.5rem;
    min-width: 40px;
    text-align: center;
    color: var(--text-main);
}

</style>