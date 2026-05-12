<script setup>
import { getOptimalImage } from '../utils/imageOptimizer'

defineProps({
    recipe: {
        type: Object,
        required: true
    }
})

// We declare the custom event this component can emit
defineEmits(['swap', 'update-scale'])
</script>

<template>
    <div class="recipe-card">
        <RouterLink :to="`/recipe/${recipe.id}`" class="card-content">
            <img :src="getOptimalImage(recipe.image_url, 400, 250)" :alt="recipe.name" class="cover-image" />
            <div class="info-block">
                <h3 class="title">{{ recipe.name }}</h3>
                <p class="meta">{{ recipe.rating ? recipe.rating.toFixed(1) : 'N/A' }}⭐ —
                    {{ recipe.prep_time_minutes }} mins — {{ recipe.calories }}kcal</p>
            </div>
        </RouterLink>

        <div class="card-actions">
            <div class="scale-controls">
                <button @click.prevent="$emit('update-scale', recipe, Math.max(0.5, (recipe.scale || 1) - 0.5))"
                    class="btn-scale">−</button>
                <span class="scale-readout">{{ 2 * (recipe.scale || 1) }} serv.</span>
                <button @click.prevent="$emit('update-scale', recipe, (recipe.scale || 1) + 0.5)"
                    class="btn-scale">+</button>
            </div>
            <button @click.prevent="$emit('swap', recipe)" class="btn-swap">
                🔄 Swap
            </button>
        </div>
    </div>
</template>

<style scoped>
.recipe-card {
    display: flex;
    flex-direction: column;
    border: 1px solid var(--border-color);
    border-radius: 8px;
    overflow: hidden;
    background: var(--bg-surface);
    transition: transform 0.2s, box-shadow 0.2s;
}

.recipe-card:hover {
    /* transform: translateY(-4px); */
    /* box-shadow: 0 10px 15px -3px var(--shadow); */
    box-shadow: 0 4px 0px -2px var(--accent-hover)
}

.card-content {
    text-decoration: none;
    color: var(--text-main);
    flex: 1;
    /* Pushes the swap button to the bottom */
}

.cover-image {
    width: 100%;
    height: 180px;
    object-fit: cover;
}

.info-block {
    padding: 1rem;
}

.title {
    font-size: 1.1rem;
    margin: 0 0 0.5rem 0;
    font-weight: 600;
    text-align: center;
}

.meta {
    font-size: 0.9rem;
    color: var(--text-faint);
    margin: 0;
    text-align: center;
}

.card-actions {
    padding: 0 1rem 1rem 1rem;
    display: flex;
    gap: 0.5rem;
}

.scale-controls {
    display: flex;
    align-items: center;
    background: var(--bg-page);
    border: 1px solid var(--border-color);
    border-radius: 6px;
    overflow: hidden;
    flex: 0 0 auto;
}

.btn-scale {
    background: none;
    border: none;
    color: var(--text-main);
    font-size: 1.1rem;
    padding: 0.35rem 0.6rem;
    cursor: pointer;
}

.btn-scale:hover {
    background: var(--border-light);
    color: var(--accent-hover);
    filter: brightness(0.9)
}

.scale-readout {
    font-weight: bold;
    font-size: 0.9rem;
    padding: 0 0.25rem;
    min-width: 35px;
    text-align: center;
    color: var(--text-main);
}

.btn-swap {
    flex: 1;
    width: 100%;
    padding: 0.5rem;
    background: var(--bg-page);
    border: 1px solid var(--border-color);
    color: var(--text-main);
    border-radius: 6px;
    cursor: pointer;
    font-weight: bold;
    transition: all 0.2s;
}

.btn-swap:hover {
    background: var(--border-light);
    color: var(--accent-hover);
}
</style>