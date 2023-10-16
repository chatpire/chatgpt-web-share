<template>
  <n-tooltip trigger="hover">
    <template #trigger>
      <n-icon class="my-auto">
        <HelpRound />
      </n-icon>
    </template>
    <slot />
  </n-tooltip>
</template>

<script setup lang="ts">
import { HelpRound } from '@vicons/material';
</script>
