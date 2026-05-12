<script setup>
defineProps({
    nutrition: {
        type: Array,
        default: () => []
    },
    allergens: {
        type: Array,
        default: () => []
    }
})
</script>

<template>
    <div class="nutrition-card">
        <h2>Nutrition Values</h2>
        <p class="subtitle">Per serving</p>

        <div class="nutrition-list">
            <div v-for="(item, index) in nutrition" :key="index" class="nutrition-row">
                <span class="nutrient-name">{{ item.name }}</span>
                <span class="nutrient-amount">{{ item.amount }}{{ item.unit }}</span>
            </div>
        </div>

        <div v-if="allergens.length" class="allergens-section">
            <p><strong>Allergens:</strong> {{ allergens.join(', ') }}</p>
        </div>
    </div>
</template>

<style scoped>
.nutrition-card {
    background: var(--bg-surface);
    border-radius: 12px;
    padding: 1.5rem;
    border: 1px solid var(--border-color);
    box-shadow: 0 1px 3px var(--shadow);
}

h2 {
    font-size: 1.35rem;
    margin-bottom: 0.25rem;
    color: var(--text-deep)
}

.subtitle {
    text-align: right;
    font-size: 0.85rem;
    font-weight: bold;
    color: var(--text-muted);
    margin-bottom: 1rem;
    border-bottom: 2px solid var(--border-color);
    padding-bottom: 0.5rem;
}

.nutrition-row {
    display: flex;
    justify-content: space-between;
    padding: 0.75rem 0;
    border-bottom: 1px solid var(--border-light);
    font-size: 0.9rem;
}

.nutrient-name {
    font-weight: 600;
    color: var(--text-main);
}

.nutrient-amount {
    color: var(--text-muted);
}

.allergens-section {
    margin-top: 1.5rem;
    padding-top: 1rem;
    border-top: 1px solid var(--border-color);
    font-size: 0.85rem;
    color: var(--text-muted);
}
</style>