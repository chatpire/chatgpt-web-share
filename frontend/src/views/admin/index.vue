
<template>
  <n-card class="h-full mb-6">
    <n-tabs type="line" justify-content="center" animated>
      <n-tab-pane name="sys" :tab="$t('commons.systemManagement')">
        <SystemManager />
      </n-tab-pane>
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
import SystemManager from './system_manager.vue';
import UserManager from './user_manager.vue';
import ConvManager from './conversation_manager.vue';
import LogViewer from './log_viewer.vue';
</script>