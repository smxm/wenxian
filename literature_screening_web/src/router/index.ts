import { createRouter, createWebHistory } from 'vue-router'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: () => import('@/views/DashboardView.vue')
    },
    {
      path: '/strategy/new',
      name: 'strategy-new',
      component: () => import('@/views/StrategyRunView.vue')
    },
    {
      path: '/screening/new',
      name: 'screening-new',
      component: () => import('@/views/ScreeningRunView.vue')
    },
    {
      path: '/tasks',
      name: 'tasks',
      component: () => import('@/views/TasksView.vue')
    },
    {
      path: '/projects/:projectId',
      redirect: to => ({ path: `/threads/${String(to.params.projectId)}` })
    },
    {
      path: '/threads/:projectId',
      name: 'thread-detail',
      component: () => import('@/views/ProjectDetailView.vue'),
      props: true
    },
    {
      path: '/tasks/:taskId',
      name: 'task-detail',
      component: () => import('@/views/TaskDetailView.vue'),
      props: true
    }
  ],
  scrollBehavior() {
    return { top: 0 }
  }
})
