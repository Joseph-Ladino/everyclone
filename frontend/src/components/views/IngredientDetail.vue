<script setup>
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { getOptimalImage } from '../../utils/imageOptimizer';
import { sixteenthsToFraction } from "../../utils/decimalToFraction";

const route = useRoute();
const ingredient = ref(null);
const loading = ref(true);

onMounted(async () => {
    try {
        const res = await fetch(`${import.meta.env.VITE_API_URL}/ingredients/${route.params.id}`);
        if (!res.ok) throw new Error("Failed to fetch ingredient");
        ingredient.value = await res.json();
    } catch (error) {
        console.error(error);
    } finally {
        loading.value = false;
    }
});
</script>

<template>
    <div v-if="loading" class="loading">Loading database...</div>

    <div v-else-if="ingredient" class="ing-layout">

        <div class="header-card">
            <img v-if="ingredient.image_url" :src="getOptimalImage(ingredient.image_url, 150, 150)" class="ing-img"
                alt="Ingredient Image" />
            <h1>{{ ingredient.name }}</h1>
            <p class="category">
                Category: {{ ingredient.category !== 'none' ? ingredient.category : 'Misc / Other' }}
            </p>

            <div class="stats">
                <p v-if="ingredient.unit_conversion" class="unit-data">
                    <strong>Standard EP Unit:</strong> 
                    {{ sixteenthsToFraction(ingredient.unit_conversion.amount) }} {{ ingredient.unit_conversion.unit }}
                </p>
                <p>Used in <strong>{{ ingredient.used_in_recipes_count }}</strong> unique recipes.</p>
            </div>
            <p class="id-hash">ID: {{ ingredient.id }}</p>
        </div>

        <div v-if="ingredient.is_blend && ingredient.blend_recipe" class="prep-card">
            <div class="prep-header">
                <h2>Blend Recipe</h2>
                <span class="yield-badge">Yields: {{ sixteenthsToFraction(ingredient.blend_recipe.yield_tbsp) }} tbsp</span>
            </div>

            <ul class="staples-list">
                <li v-for="(data, name) in ingredient.blend_recipe.ingredients" :key="name">
                    <span class="staple-name">{{ name }}</span>
                    <span class="staple-amount">{{ sixteenthsToFraction(data.amount) }} {{ data.unit }}</span>
                </li>
            </ul>
        </div>

    </div>
</template>

<style scoped>
.ing-layout {
    max-width: 600px;
    margin: 2rem auto;
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
}

/* Header Card */
.header-card {
    background: var(--bg-surface);
    padding: 2rem;
    border-radius: 12px;
    border: 1px solid var(--border-color);
    text-align: center;
    box-shadow: 0 1px 3px var(--shadow);
}

.ing-img {
    width: 120px;
    height: 120px;
    object-fit: contain;
    background: var(--bg-page);
    border-radius: 50%;
    padding: 0.5rem;
    margin-bottom: 1rem;
    border: 1px solid var(--border-color);
}

h1 {
    font-size: 1.8rem;
    color: var(--text-deep);
    margin-bottom: 0.25rem;
}

.category {
    color: var(--accent);
    text-transform: uppercase;
    letter-spacing: 1px;
    font-size: 0.85rem;
    font-weight: bold;
}

.stats {
    margin-top: 2rem;
    padding-top: 1.5rem;
    border-top: 1px solid var(--border-light);
    color: var(--text-muted);
    font-size: 0.95rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.unit-data {
    color: var(--text-main);
    font-size: 1.15rem;
}

.id-hash {
    font-family: monospace;
    color: var(--text-faint);
    font-size: 0.8rem;
    margin-top: 1.5rem;
}

/* Prep / Blend Card (Matching the Staples style) */
.prep-card {
    background: var(--bg-surface);
    border-radius: 12px;
    padding: 1.5rem;
    border: 1px solid var(--border-color);
    box-shadow: 0 1px 3px var(--shadow);
}

.prep-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
}

.prep-card h2 {
    font-size: 1.25rem;
    color: var(--text-deep);
    margin: 0;
}

.yield-badge {
    background: var(--bg-page);
    color: var(--accent);
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 1.1rem;
    font-weight: bold;
    border: 1px solid var(--border-color);
}

.staples-list {
    list-style: circle inside;
    padding: 0;
    margin: 0;
}

.staples-list li {
    padding: 0.75rem 0;
    border-bottom: 1px solid var(--border-light);
    justify-content: space-between;
    display: flex;
}

.staples-list li:last-child {
    border-bottom: none;
    padding-bottom: 0;
}

.staple-name {
    font-weight: bold;
    color: var(--text-main);
    font-size: 1.15rem;
}

.staple-amount {
    color: var(--text-muted);
    font-size: 1.1rem;
}
</style>