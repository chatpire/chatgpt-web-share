<script setup lang="ts">
import PageHeader from './components/PageHeader.vue';
</script>

<template>
  <!-- page header: logo, site title, login button -->
  <div class="w-full lg:w-screen-lg mx-auto h-screen flex flex-col">
    <div class="my-4">
      <PageHeader />
    </div>
    <router-view></router-view>
  </div>
</template>
