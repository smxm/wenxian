<script setup lang="ts">
import { darkTheme, dateZhCN, NConfigProvider, NDialogProvider, NLoadingBarProvider, NMessageProvider, zhCN } from 'naive-ui'
import AppShell from '@/layouts/AppShell.vue'

const themeOverrides = {
  common: {
    primaryColor: '#2d6a4f',
    primaryColorHover: '#3f8a68',
    primaryColorPressed: '#244f3c',
    bodyColor: '#f5f1e8',
    cardColor: '#fffdf8',
    borderColor: '#d9d1c5',
    textColorBase: '#1f2520',
    textColor2: '#526055',
    successColor: '#2f855a',
    warningColor: '#c4891d',
    errorColor: '#c05621'
  }
}
</script>

<template>
  <NConfigProvider
    :locale="zhCN"
    :date-locale="dateZhCN"
    :theme="null"
    :theme-overrides="themeOverrides"
  >
    <NLoadingBarProvider>
      <NDialogProvider>
        <NMessageProvider>
          <AppShell />
        </NMessageProvider>
      </NDialogProvider>
    </NLoadingBarProvider>
  </NConfigProvider>
</template>
