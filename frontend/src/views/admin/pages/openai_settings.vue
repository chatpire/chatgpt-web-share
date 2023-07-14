<template>
  <n-card class="mb-4 h-full">
    <n-tabs
      class="-mt-2"
      default-value="pluginSettings"
      size="large"
      animated
      pane-wrapper-style="margin: 0 -4px"
      pane-style="padding-left: 4px; padding-right: 4px; box-sizing: border-box;"
    >
      <n-tab-pane name="pluginSettings" :tab="$t('commons.pluginSettings')">
        <OpenaiWebPluginSetting />
      </n-tab-pane>
    </n-tabs>
  </n-card>
</template>

<script setup lang="ts">
import OpenaiWebPluginSetting from '@/views/admin/components/OpenaiWebPluginSetting.vue';
</script>
