<template>
  <div class="mt-6">
    <n-form :label-placement="'left'" :label-align="'left'" label-width="100px">
      <n-form-item :label="t('labels.title')">
        <n-input v-model:value="newConversationInfo.title" />
      </n-form-item>
      <!-- Source selection removed -->
      <n-form-item :label="t('labels.model')">
        <n-select v-model:value="newConversationInfo.model" :options="availableModels" />
      </n-form-item>
      <n-form-item
        v-if="newConversationInfo.source === 'openai_web' && newConversationInfo.model === 'GPT-4 Plugins'"
        :label="t('labels.plugins')"
      >
        <n-select
          v-model:value="newConversationInfo.openaiWebPlugins"
          :options="pluginOptions"
          clearable
          multiple
          :placeholder="selectPluginPlaceholder"
          :loading="loadingPlugins"
          :disabled="loadingPlugins"
          :render-label="renderPluginSelectionLabel"
          :render-tag="renderPluginSelectionTag"
        />
      </n-form-item>
    </n-form>
  </div>
</template>

<script setup lang="ts">
// ... (the rest of the imports remain the same)

const availableModels = computed<SelectOption[]>(() => {
  if (!userStore.user) {
    return [];
  }
  return [
    ...userStore.user.setting.openai_web.available_models,
    ...userStore.user.setting.openai_api.available_models
  ].map((model) => ({
    label: t(`models.${model}`),
    value: model,
  }));
});

const newConversationInfo = ref<NewConversationInfo>({
  title: null,
  source: 'openai_api',  // default, will be overridden by watcher
  model: null,
  openaiWebPlugins: null,
});

watch(
  () => newConversationInfo.value.model,
  (newModel) => {
    if (newModel === 'GPT-3.5' || newModel === 'GPT-4') {
      newConversationInfo.value.source = 'openai_api';
    } else if (newModel === 'GPT-4 Browsing' || newModel === 'GPT-4 Plugins') {
      newConversationInfo.value.source = 'openai_web';
    }
  }
);

// ... (the rest of the code remains the same)

</script>
