<script setup>
import { ref, computed, watch, onMounted } from 'vue';
import RecipePreview from '../RecipePreview.vue';
import { sixteenthsToFraction } from '../../utils/decimalToFraction';
import { getOptimalImage } from '../../utils/imageOptimizer';
import { getDisplayString, getRawMath } from '../../utils/ingredientFormatter';

// --- State: Filters & Parameters ---
const targetMeals = ref(5);
const minRating = ref(3.5);
const selectedAnchors = ref([]);
const availableAnchors = ['Chicken', 'Beef', 'Pork', 'Sausage', 'Shrimp'];

// --- State: Data & UI ---
const proposedMenu = ref([]);
const groceryList = ref({});
const isGenerating = ref(false);
const isDrawerOpen = ref(false);
const drawerTab = ref('groceries');
const prepToggles = ref({});

// --- NEW STATE: Export & Sorting ---
const crossedOffItems = ref([]);
const defaultCategories = ['Produce', 'Meat & Poultry', 'Seafood', 'Dairy & Eggs', 'Bakery', 'Pantry & Dry Goods', 'Spices & Seasonings', 'Sauces & Condiments', 'Misc / Other'];
const categoryOrder = ref([...defaultCategories]);

// --- SWAP MODAL STATE ---
const isSwapModalOpen = ref(false);
const recipeToSwap = ref(null);
const swapCandidates = ref([]);
const isFetchingSwaps = ref(false);

const openSwapModal = async (recipe) => {
    recipeToSwap.value = recipe;
    isSwapModalOpen.value = true;
    isFetchingSwaps.value = true;
    swapCandidates.value = [];

    try {
        const res = await fetch(`${import.meta.env.VITE_API_URL}/propose-menu`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                target_meals: 3, // We want exactly 3 alternatives
                history_ids: proposedMenu.value.map(r => r.id), // Exclude the active menu!
                target_anchors: [], // No anchors, let them have completely random variety
                min_rating: minRating.value
            })
        });
        if (!res.ok) throw new Error("Failed to fetch swap candidates");
        swapCandidates.value = await res.json();
    } catch (error) {
        console.error(error);
    } finally {
        isFetchingSwaps.value = false;
    }
};

// Inside executeSwap():
const executeSwap = (newRecipe) => {
    newRecipe.scale = 1; // Inject here too
    const index = proposedMenu.value.findIndex(r => r.id === recipeToSwap.value.id);
    if (index !== -1) proposedMenu.value.splice(index, 1, newRecipe);
    closeSwapModal();
};

const closeSwapModal = () => {
    isSwapModalOpen.value = false;
    recipeToSwap.value = null;
    swapCandidates.value = [];
};

// --- Lifecycle: LocalStorage Hydration ---
onMounted(() => {
    const savedMenu = localStorage.getItem('ep_menu');
    if (savedMenu) {
        proposedMenu.value = JSON.parse(savedMenu);
        targetMeals.value = proposedMenu.value.length;
    }

    const savedPrep = localStorage.getItem('ep_prep');
    if (savedPrep) prepToggles.value = JSON.parse(savedPrep);

    const savedCrossed = localStorage.getItem('ep_crossed');
    if (savedCrossed) crossedOffItems.value = JSON.parse(savedCrossed);

    const savedOrder = localStorage.getItem('ep_order');
    if (savedOrder) {
        let parsedOrder = JSON.parse(savedOrder);
        // 2. The Patch: Inject any new backend categories into the user's saved layout
        defaultCategories.forEach(cat => {
            if (!parsedOrder.includes(cat)) parsedOrder.push(cat);
        });
        categoryOrder.value = parsedOrder;
    }
});

// 3. Helper function to check for empty categories
const categoryHasItems = (category) => {
    return displayGroceries.value[category]?.length > 0;
};

// --- Lifecycle: LocalStorage Autosave ---
watch(proposedMenu, (val) => localStorage.setItem('ep_menu', JSON.stringify(val)), { deep: true });
watch(prepToggles, (val) => localStorage.setItem('ep_prep', JSON.stringify(val)), { deep: true });
watch(crossedOffItems, (val) => localStorage.setItem('ep_crossed', JSON.stringify(val)), { deep: true });
watch(categoryOrder, (val) => localStorage.setItem('ep_order', JSON.stringify(val)), { deep: true });

// --- The Engine ---
const generateMenu = async () => {
    isGenerating.value = true;
    try {
        const res = await fetch(`${import.meta.env.VITE_API_URL}/propose-menu`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                target_meals: targetMeals.value,
                history_ids: [],
                target_anchors: selectedAnchors.value,
                min_rating: minRating.value
            })
        });

        if (!res.ok) throw new Error("Failed to generate menu");

        const rawMenu = await res.json();
        // Inject the reactive scale property
        proposedMenu.value = rawMenu.map(r => ({ ...r, scale: 1 }));

        // Reset crossed-off items for a new week
        crossedOffItems.value = [];
        isDrawerOpen.value = true;
    } catch (error) {
        console.error(error);
    } finally {
        isGenerating.value = false;
    }
};

watch(proposedMenu, async (newMenu) => {
    if (newMenu.length === 0) {
        groceryList.value = { core: {}, staples: {} };
        return;
    }

    // Build the dictionary: { "recipe_id": 1.5 }
    const scales = {};
    newMenu.forEach(recipe => {
        scales[recipe.id] = recipe.scale || 1;
    });

    try {
        const res = await fetch(`${import.meta.env.VITE_API_URL}/grocery-list`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ recipe_scales: scales }) // Use the new key
        });
        if (!res.ok) throw new Error("Failed to compile groceries");
        groceryList.value = await res.json();
    } catch (error) {
        console.error(error);
    }
}, { deep: true });

// --- Prep Sheet Compiler ---
const prepSheet = computed(() => {
    const blends = {};
    proposedMenu.value.forEach(recipe => {
        recipe.ingredients.forEach(ing => {
            if (ing.is_blend && ing.blend_recipe) {
                if (!blends[ing.name]) {
                    blends[ing.name] = { neededAmount: 0, yield_tbsp: ing.blend_recipe.yield_tbsp, rawIngredients: ing.blend_recipe.ingredients };
                }
                // Multiply the blend requirement by the recipe's scale!
                blends[ing.name].neededAmount += (ing.amount * (recipe.scale || 1));
            }
        });
    });

    Object.values(blends).forEach(blend => {
        blend.scaledRecipe = {};
        const scale = blend.neededAmount / blend.yield_tbsp;
        Object.entries(blend.rawIngredients).forEach(([rawName, data]) => {
            let tspAmount = data.unit === 'tbsp' ? data.amount * 3 : data.amount;
            let finalTsp = tspAmount * scale;
            if (finalTsp >= 3) blend.scaledRecipe[rawName] = { amount: finalTsp / 3, unit: 'tbsp' };
            else blend.scaledRecipe[rawName] = { amount: finalTsp, unit: 'tsp' };
        });
    });
    return blends;
});

// --- Grocery List Router ---
const displayGroceries = computed(() => {
    const list = JSON.parse(JSON.stringify(groceryList.value));

    // Ensure the spices category exists before we try to inject into it
    if (!list['Spices & Seasonings']) list['Spices & Seasonings'] = [];

    const spicesToInject = {};

    Object.entries(prepSheet.value).forEach(([blendName, blendData]) => {
        const isInjecting = prepToggles.value[blendName] !== false;

        if (isInjecting) {
            // 1. Remove the pre-mixed blend from wherever it landed
            Object.keys(list).forEach(category => {
                list[category] = list[category].filter(
                    item => item.name.toLowerCase() !== blendName.toLowerCase()
                );
            });

            // 2. Aggregate the raw spices to inject
            Object.entries(blendData.scaledRecipe).forEach(([rawName, rawData]) => {
                if (!spicesToInject[rawName]) spicesToInject[rawName] = { amount: 0, unit: rawData.unit };
                let currentTsp = spicesToInject[rawName].unit === 'tbsp' ? spicesToInject[rawName].amount * 3 : spicesToInject[rawName].amount;
                let addedTsp = rawData.unit === 'tbsp' ? rawData.amount * 3 : rawData.amount;
                let totalTsp = currentTsp + addedTsp;
                spicesToInject[rawName] = totalTsp >= 3 ? { amount: totalTsp / 3, unit: 'tbsp' } : { amount: totalTsp, unit: 'tsp' };
            });
        }
    });

    // 3. Inject them directly into the Spices category
    Object.entries(spicesToInject).forEach(([name, data]) => {
        const existing = list['Spices & Seasonings'].find(i => i.name === name);
        if (existing) {
            let eTsp = existing.unit === 'tbsp' ? existing.amount * 3 : (existing.amount || 0);
            let dTsp = data.unit === 'tbsp' ? data.amount * 3 : data.amount;
            let total = eTsp + dTsp;
            existing.unit = total >= 3 ? 'tbsp' : 'tsp';
            existing.amount = total >= 3 ? total / 3 : total;
        } else {
            list['Spices & Seasonings'].push({ name, amount: data.amount, unit: data.unit });
        }
    });

    list['Spices & Seasonings'].sort((a, b) => a.name.localeCompare(b.name));
    return list;
});

const toggleAnchor = (anchor) => {
    if (selectedAnchors.value.includes(anchor)) selectedAnchors.value = selectedAnchors.value.filter(a => a !== anchor);
    else selectedAnchors.value.push(anchor);
};

// --- Drag & Drop Category Sorting ---
const draggedCategory = ref(null);
const onDragStart = (cat) => { draggedCategory.value = cat; };
const onDrop = (targetCat) => {
    if (!draggedCategory.value || draggedCategory.value === targetCat) return;
    const fromIdx = categoryOrder.value.indexOf(draggedCategory.value);
    const toIdx = categoryOrder.value.indexOf(targetCat);
    categoryOrder.value.splice(fromIdx, 1);
    categoryOrder.value.splice(toIdx, 0, draggedCategory.value);
    draggedCategory.value = null;
};
const onDragEnd = () => {
    draggedCategory.value = null;
};

// --- Checkbox Logic ---
const toggleCrossOff = (itemName) => {
    if (crossedOffItems.value.includes(itemName)) {
        crossedOffItems.value = crossedOffItems.value.filter(i => i !== itemName);
    } else {
        crossedOffItems.value.push(itemName);
    }
};

// --- Export Pipelines ---
const copyToClipboard = async () => {
    let text = "EveryPlate Grocery List\n\n";
    categoryOrder.value.forEach(aisle => {
        if (displayGroceries.value[aisle] && displayGroceries.value[aisle].length > 0) {
            let aisleText = `${aisle.toUpperCase()}\n`;
            let hasItems = false;

            displayGroceries.value[aisle].forEach(item => {
                if (!crossedOffItems.value.includes(item.name)) {
                    hasItems = true;
                    // Inject the new formatter here (scale is 1 because backend already scaled it)
                    const display = getDisplayString(item.amount, item.unit, item.unit_conversion, 1);
                    aisleText += `- ${item.name} (${display})\n`;
                }
            });
            if (hasItems) text += aisleText + '\n';
        }
    });
    try { await navigator.clipboard.writeText(text); alert("List copied!"); } catch (err) { console.error(err); }
};

const exportJSON = () => {
    const payload = {};
    categoryOrder.value.forEach(aisle => {
        if (displayGroceries.value[aisle]) {
            displayGroceries.value[aisle].forEach(item => {
                if (!crossedOffItems.value.includes(item.name)) {
                    // Extract the raw floats for the automation JSON
                    const parsed = getRawMath(item.amount, item.unit, item.unit_conversion, 1);
                    payload[item.name] = { amount: parsed.amount, unit: parsed.unit, aisle: aisle };
                }
            });
        }
    });
    const blob = new Blob([JSON.stringify(payload, null, 4)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = 'grocery_export.json'; a.click();
    URL.revokeObjectURL(url);
};

const openPrintView = () => {
    localStorage.setItem('ep_print_data', JSON.stringify({
        groceries: displayGroceries.value,
        crossedOff: crossedOffItems.value,
        order: categoryOrder.value
    }));
    window.open('/print', '_blank');
};
</script>

<template>
    <div class="generator-container">

        <div class="workspace">
            <div class="controls-panel">
                <h2>Menu Generator</h2>
                <div class="filter-group">
                    <label>Meals: {{ targetMeals }}</label>
                    <input type="range" v-model.number="targetMeals" min="1" max="14" class="slider" />
                </div>
                <div class="filter-group">
                    <label>Min Rating: {{ minRating }}⭐</label>
                    <input type="range" v-model.number="minRating" min="1" max="4.5" step="0.1" class="slider" />
                </div>
                <div class="filter-group anchors">
                    <label>Bulk Anchors (Optional)</label>
                    <div class="tag-cloud">
                        <button v-for="anchor in availableAnchors" :key="anchor" @click="toggleAnchor(anchor)"
                            class="anchor-tag" :class="{ 'active': selectedAnchors.includes(anchor) }">
                            {{ anchor }}
                        </button>
                    </div>
                </div>
                <div class="actions">
                    <button @click="generateMenu" :disabled="isGenerating" class="btn-primary">
                        {{ isGenerating ? 'Computing...' : 'Generate Optimized Menu' }}
                    </button>
                    <button @click="isDrawerOpen = !isDrawerOpen" class="btn-secondary" v-if="proposedMenu.length">
                        {{ isDrawerOpen ? 'Hide Drawer' : 'Show Drawer' }}
                    </button>
                </div>
            </div>

            <div v-if="proposedMenu.length" class="menu-grid">
                <RecipePreview v-for="recipe in proposedMenu" :key="recipe.id" :recipe="recipe" @swap="openSwapModal"
                    @update-scale="(r, s) => r.scale = s" />
            </div>
            <div v-else class="empty-state">
                <p>No menu generated yet. Set your parameters and hit go.</p>
            </div>
        </div>

        <aside class="grocery-drawer" :class="{ 'open': isDrawerOpen }">
            <div class="drawer-tabs">
                <button :class="{ active: drawerTab === 'groceries' }" @click="drawerTab = 'groceries'">Grocery
                    List</button>
                <button :class="{ active: drawerTab === 'prep' }" @click="drawerTab = 'prep'">Prep Sheet</button>
                <button @click="isDrawerOpen = false" class="close-btn">✖</button>
            </div>

            <div class="drawer-content">

                <div v-show="drawerTab === 'groceries'" class="tab-scroll-area">
                    <div v-if="!displayGroceries" class="empty-state-drawer">
                        Nothing to buy yet.
                    </div>

                    <template v-for="category in categoryOrder" :key="category">
                        <div v-if="categoryHasItems(category)" draggable="true" @dragstart="onDragStart(category)"
                            @dragover.prevent @drop="onDrop(category)" @dragend="onDragEnd" class="g-category-group"
                            :class="{ 'is-dragging': draggedCategory === category }">
                            
                            <h5 class="g-category-title">☰ {{ category }}</h5>

                            <ul class="g-list">
                                <li v-for="item in (displayGroceries[category] || [])" :key="item.name" class="g-item"
                                    :class="{ 'crossed-off': crossedOffItems.includes(item.name) }">
                                    <label class="g-item-label">
                                        <input type="checkbox" :checked="crossedOffItems.includes(item.name)"
                                            @change="toggleCrossOff(item.name)" />
                                        <span class="g-name">{{ item.name }}</span>
                                    </label>
                                    <span class="g-amount">
                                        {{ getDisplayString(item.amount, item.unit, item.unit_conversion) }}
                                    </span>
                                </li>
                            </ul>
                        </div>
                    </template>
                </div>

                <div class="export-footer" v-show="drawerTab === 'groceries' && proposedMenu.length > 0">
                    <button @click="openPrintView" class="btn-secondary btn-sm">🖨️ Print</button>
                    <button @click="copyToClipboard" class="btn-secondary btn-sm">📋 Copy Text</button>
                    <button @click="exportJSON" class="btn-secondary btn-sm">📦 JSON</button>
                </div>

                <div v-show="drawerTab === 'prep'">
                    <div v-if="Object.keys(prepSheet).length === 0" class="empty-state-drawer">
                        No custom prep required this week.
                    </div>

                    <div v-for="(data, name) in prepSheet" :key="name" class="prep-blend-card">
                        <div class="prep-blend-header">
                            <label class="blend-title-group">
                                <input type="checkbox" :checked="prepToggles[name] !== false"
                                    @change="prepToggles[name] = $event.target.checked" class="blend-checkbox" />
                                <h4 class="blend-name">{{ name }}</h4>
                            </label>
                            <span class="blend-yield">Needed: {{ sixteenthsToFraction(data.neededAmount) }} tbsp</span>
                        </div>

                        <ul class="g-list" :class="{ 'disabled-list': prepToggles[name] === false }">
                            <li v-for="(raw, rawName) in data.scaledRecipe" :key="rawName" class="g-item">
                                <span class="g-name">{{ rawName }}</span>
                                <span class="g-amount">{{ sixteenthsToFraction(raw.amount) }} {{ raw.unit }}</span>
                            </li>
                        </ul>
                    </div>
                </div>

            </div>
        </aside>
        <div v-if="isSwapModalOpen" class="modal-overlay" @click.self="closeSwapModal">
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Swap out "{{ recipeToSwap?.name }}"</h3>
                    <button @click="closeSwapModal" class="close-btn">✖</button>
                </div>

                <div v-if="isFetchingSwaps" class="swap-loading">
                    <p>Cooking up alternatives...</p>
                </div>

                <div v-else class="swap-grid">
                    <div v-for="candidate in swapCandidates" :key="candidate.id" class="swap-card">
                        <img :src="getOptimalImage(candidate.image_url, 250, 180)" class="swap-thumb" />
                        <div class="swap-info">
                            <h4 class="swap-title">{{ candidate.name }}</h4>
                            <p class="swap-meta">⭐ {{ candidate.rating?.toFixed(1) }} • ⏱️ {{
                                candidate.prep_time_minutes }}m</p>
                            <button @click="executeSwap(candidate)" class="btn-primary btn-sm">Pick This</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped>
.generator-container {
    display: flex;
    height: calc(100vh - 80px);
    overflow: hidden;
    gap: 1.5rem;
}

.workspace {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow-y: auto;
    padding-right: 0.5rem;
}

/* Controls Panel */
.controls-panel {
    background: var(--bg-surface);
    padding: 1.5rem;
    border-radius: 12px;
    border: 1px solid var(--border-color);
    margin-bottom: 2rem;
    box-shadow: 0 1px 3px var(--shadow);
}

.controls-panel h2 {
    margin-bottom: 1.5rem;
    color: var(--text-main);
}

.filter-group {
    margin-bottom: 1.5rem;
}

.filter-group label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 600;
    color: var(--text-main);
}

.slider {
    width: 100%;
    max-width: 300px;
}

/* Tags & Buttons */
.tag-cloud {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
}

.anchor-tag {
    background: var(--bg-page);
    color: var(--text-muted);
    border: 1px solid var(--border-color);
    padding: 0.4rem 1rem;
    border-radius: 20px;
    cursor: pointer;
    font-size: 0.9rem;
    font-weight: bold;
    transition: all 0.2s ease, border 0.5s ease, background 0.5s ease;
}

.anchor-tag:hover {
    background: var(--border-light);
}

.anchor-tag.active {
    background: var(--accent);
    color: white;
    border-color: var(--accent);
}

.actions {
    display: flex;
    gap: 1rem;
    margin-top: 1rem;
}

.btn-primary,
.btn-secondary {
    padding: 0.6rem 1.2rem;
    border-radius: 8px;
    font-weight: bold;
    cursor: pointer;
    border: 1px solid transparent;
    transition: color 0.2s ease, box-shadow 0.2s ease, border 0.5s ease, background 0.5s ease;
}

.btn-primary {
    background: var(--accent);
    color: white;
}

.btn-primary:hover {
    background: var(--accent-hover);
    box-shadow: 0px 4px 6px -3px var(--accent-hover);
    filter: brightness(0.9);
}

.btn-secondary {
    background: var(--bg-surface);
    color: var(--text-main);
    border-color: var(--border-color);
    box-shadow: 0px 4px 6px -3px var(--shadow);
}

.btn-secondary:hover {
    color: var(--accent-hover);
    box-shadow: 0px 4px 6px -3px var(--accent-hover);
}

/* Menu Grid */
.menu-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 1.5rem;
    padding-bottom: 2rem;
}

.empty-state {
    text-align: center;
    padding: 3rem;
    color: var(--text-faint);
    background: var(--bg-surface);
    border-radius: 12px;
    border: 1px dashed var(--border-color);
}

/* Drawer */
.grocery-drawer {
    width: 400px;
    background: var(--bg-surface);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    display: flex;
    flex-direction: column;
    transition: transform 0.3s ease, opacity 0.3s ease, margin 0.3s ease, border 0.5s ease, background 0.5s ease;
    transform: translateX(120%);
    opacity: 0;
    margin-left: -400px;
}

.grocery-drawer.open {
    transform: translateX(0);
    opacity: 1;
    margin-left: 0;
}

/* Tabs */
.drawer-tabs {
    display: flex;
    align-items: center;
    border-bottom: 1px solid var(--border-color);
    background: var(--bg-page);
    border-radius: 12px 12px 0 0;
}

.drawer-tabs>button:first-child {
    margin-left: 0.3rem;
    border-top-left-radius: 8px;
}

.drawer-tabs button {
    flex: 1;
    padding: 1rem;
    background: none;
    border: none;
    font-weight: bold;
    color: var(--text-muted);
    cursor: pointer;
    transition: color 0.2s, border 0.5s ease, background 0.5s ease;
}

.drawer-tabs button.active {
    color: var(--accent);
    background: var(--bg-surface);
    box-shadow: 0 4px 0px -2px var(--accent);
}

.drawer-tabs button:hover:not(.active) {
    color: var(--text-main);
}

.close-btn {
    flex: 0 0 50px !important;
    color: var(--text-faint) !important;
    font-size: 1.2rem;
}

/* Content */
.drawer-content {
    flex: 1;
    overflow-y: auto;
    padding: 1.5rem;
    background: var(--bg-surface);
    transition: border 0.5s ease, background 0.5s ease;
}

.empty-state-drawer {
    text-align: center;
    color: var(--text-faint);
    padding: 2rem 0;
    font-style: italic;
}

/* Groceries */
.g-section {
    margin-bottom: 2rem;
}

.g-section-title {
    font-size: 1.1rem;
    color: var(--accent);
    border-bottom: 2px solid var(--border-color);
    padding-bottom: 0.5rem;
    margin-bottom: 1rem;
}

.g-category-group {
    margin-bottom: 1.5rem;
}

.g-category-title {
    font-size: 0.9rem;
    color: var(--text-faint);
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 0.5rem;
}

.g-list {
    list-style: none;
    padding: 0;
    margin: 0;
    transition: opacity 0.2s ease, border 0.5s ease, background 0.5s ease;
}

.g-item {
    display: flex;
    justify-content: space-between;
    padding: 0.6rem 0;
    border-bottom: 1px solid var(--border-light);
    color: var(--text-main);
    font-size: 0.95rem;
}

.g-item:last-child {
    border-bottom: none;
}

.g-amount {
    color: var(--text-faint);
    font-weight: 600;
    font-size: 0.9rem;
}

/* Prep Sheet Specifics */
.prep-controls {
    margin-bottom: 1.5rem;
    padding-bottom: 1.5rem;
    border-bottom: 1px dashed var(--border-color);
}

.checkbox-label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: 600;
    color: var(--text-main);
    cursor: pointer;
}

.checkbox-label input {
    accent-color: var(--accent);
    width: 16px;
    height: 16px;
    cursor: pointer;
}

.prep-blend-card {
    background: var(--bg-page);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1rem;
}

.prep-blend-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.75rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--border-color);
}

.blend-name {
    color: var(--text-main);
    font-size: 1.05rem;
    margin: 0;
}

.blend-yield {
    background: var(--bg-surface);
    color: var(--accent);
    padding: 0.2rem 0.6rem;
    border-radius: 12px;
    font-size: 0.8rem;
    font-weight: bold;
    border: 1px solid var(--border-color);
}

.blend-title-group {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    cursor: pointer;
}

.blend-checkbox {
    accent-color: var(--accent);
    width: 16px;
    height: 16px;
    cursor: pointer;
}

.disabled-list {
    opacity: 0.4;
    pointer-events: none;
}

/* Drag & Drop */
.g-category-group {
    margin-bottom: 1.5rem;
    padding: 0.5rem;
    border-radius: 8px;
    border: 1px solid transparent;
    transition: background 0.2s, border 0.2s;
}

.g-category-group[draggable="true"] {
    cursor: grab;
}

.g-category-group.is-dragging {
    opacity: 0.7;
    background: var(--bg-page);
    border-color: var(--border-color);
}

.g-category-title {
    cursor: grab;
}

.g-category-group.is-dragging .g-category-title {
    cursor: grabbing;
}

.g-category-title {
    font-size: 0.9rem;
    color: var(--text-faint);
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* Checkboxes & Cross-Offs */
.g-item-label {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    cursor: pointer;
    flex: 1;
}

.g-item-label input {
    accent-color: var(--accent);
    width: 16px;
    height: 16px;
    cursor: pointer;
}

.crossed-off {
    opacity: 0.4;
}

.crossed-off > .g-item-label {
    text-decoration: line-through;
}

.staple-item .g-name {
    color: var(--text-muted);
    font-style: italic;
}

/* Export Footer */
.drawer-content {
    display: flex;
    flex-direction: column;
    padding: 0;
    /* Removing padding to allow sticky footer */
}

.tab-scroll-area {
    flex: 1;
    overflow-y: auto;
    padding: 1.5rem;
}

.export-footer {
    padding: 1rem;
    background: var(--bg-surface);
    border-top: 1px solid var(--border-color);
    display: flex;
    gap: 0.5rem;
    justify-content: space-between;
}

.btn-sm {
    font-size: 0.85rem;
    padding: 0.4rem 0.8rem;
    flex: 1;
}


/* SWAP MODAL */
.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.6);
    backdrop-filter: blur(3px);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 999;
}

.modal-content {
    background: var(--bg-page);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    width: 90%;
    max-width: 800px;
    padding: 2rem;
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3);
}

.modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid var(--border-color);
}

.modal-header h3 {
    margin: 0;
    color: var(--text-main);
}

.swap-loading {
    text-align: center;
    padding: 3rem;
    color: var(--text-faint);
    font-size: 1.1rem;
    font-style: italic;
}

.swap-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1.5rem;
}

.swap-card {
    background: var(--bg-surface);
    border: 1px solid var(--border-light);
    border-radius: 8px;
    overflow: hidden;
    display: flex;
    flex-direction: column;
}

.swap-thumb {
    width: 100%;
    height: 140px;
    object-fit: cover;
}

.swap-info {
    padding: 1rem;
    display: flex;
    flex-direction: column;
    flex: 1;
}

.swap-title {
    margin: 0 0 0.5rem 0;
    font-size: 1rem;
    color: var(--text-main);
}

.swap-meta {
    color: var(--text-faint);
    font-size: 0.85rem;
    margin: 0 0 1rem 0;
    flex: 1;
}

.swap-info .btn-primary {
    width: 100%;
}
</style>