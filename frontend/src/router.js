import { createRouter, createWebHistory } from 'vue-router';
import RecipeDetail from './components/views/RecipeDetail.vue';
import IngredientDetail from './components/views/IngredientDetail.vue';
import MenuGenerator from './components/views/MenuGenerator.vue';
import PrintList from './components/views/PrintList.vue'

const routes = [
    { path: '/', component: MenuGenerator },
    { path: '/recipe/:id', component: RecipeDetail },
    { path: '/ingredient/:id', component: IngredientDetail },
    {
        path: '/print',
        component: PrintList,
        meta: { hideNavbar: true }
    }
];

export const router = createRouter({
    history: createWebHistory(),
    routes
});