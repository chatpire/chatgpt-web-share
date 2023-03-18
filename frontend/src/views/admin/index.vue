
<template>
  <n-card class="h-full mb-6">
    <n-tabs type="line" justify-content="center" animated>
      <n-tab-pane name="user" :tab="$t('commons.userManagement')">
        <UserManager />
      </n-tab-pane>
      <n-tab-pane name="conv" :tab="$t('commons.conversationManagement')">
        <ConvManager />
      </n-tab-pane>
      <n-tab-pane name="log" :tab="$t('commons.logViewer')">
        <LogViewer />
      </n-tab-pane>
    </n-tabs>
  </n-card>
</template>

<script setup lang="ts">
import UserManager from './components/UserManager.vue';
import ConvManager from './components/ConvManager.vue';
import LogViewer from './components/LogViewer.vue';
</script>