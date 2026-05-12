<script setup>
import { ref, onMounted } from 'vue';
import { sixteenthsToFraction } from '../../utils/decimalToFraction';

const printData = ref(null);

const categoryHasItems = (category) => {
    return printData.value?.groceries[category]?.length > 0;
};

onMounted(() => {
    document.documentElement.setAttribute('data-theme', 'light');
    const data = localStorage.getItem('ep_print_data');
    if (data) {
        printData.value = JSON.parse(data);
        setTimeout(() => window.print(), 500);
    }
});
</script>

<template>
    <div class="print-container" v-if="printData">
        <h1>Grocery List</h1>

        <template v-for="category in printData.order" :key="category">
            <div v-if="categoryHasItems(category)">
                <h2>{{ category }}</h2>
                <ul class="print-list">
                    <li v-for="item in (printData.groceries[category] || [])" :key="item.name" class="print-item"
                        :class="{ 'crossed-off': printData.crossedOff.includes(item.name) }">
                        <span class="box"></span>
                        <span class="name">{{ item.name }}</span>
                        <span class="amount">{{ sixteenthsToFraction(item.amount) }} {{ item.unit }}</span>
                    </li>
                </ul>
            </div>
        </template>
    </div>
</template>

<style scoped>
.print-container {
    max-width: 800px;
    margin: 0 auto;
    padding: 2rem;
    font-family: sans-serif;
    color: black;
}

h1 {
    text-align: center;
    border-bottom: 2px solid black;
    padding-bottom: 1rem;
    margin-bottom: 2rem;
}

h2 {
    font-size: 1.2rem;
    text-transform: uppercase;
    color: #4a5568;
    border-bottom: 1px solid #e2e8f0;
    margin-top: 1.5rem;
    padding-bottom: 0.25rem;
}

.print-list {
    list-style: none;
    padding: 0;
}

.print-item {
    display: flex;
    align-items: center;
    padding: 0.5rem 0;
    font-size: 1.1rem;
}

.box {
    width: 16px;
    height: 16px;
    border: 1px solid black;
    border-radius: 3px;
    margin-right: 1rem;
}

.name {
    flex: 1;
}

.amount {
    font-weight: bold;
}

.staple .name {
    font-style: italic;
    color: #4a5568;
}

.crossed-off {
    text-decoration: line-through;
    opacity: 0.5;
}

/* Hide navigation/app shells when printing */
@media print {
    @page {
        margin: 0.5in;
    }

    body {
        background: white;
    }

    .print-container {
        padding: 0;
    }
}
</style>