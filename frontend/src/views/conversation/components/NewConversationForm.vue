<template>
  <div class="mt-6">
    <n-form :label-placement="'left'" :label-align="'left'" label-width="100px">
      <n-form-item :label="t('labels.title')">
        <n-input v-model:value="newConversationInfo.title" />
      </n-form-item>
      <!-- Remove the source selection -->
      <n-form-item :label="t('labels.model')">
        <n-select v-model:value="newConversationInfo.model" :options="availableModels" />
      </n-form-item>
      <n-form-item
        v-if="shouldRenderPluginsSection"
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
// ... (import statements and setup code)

// Update availableModels computed property
const availableModels = computed<SelectOption[]>(() => {
  if (!userStore.user) {
    return [];
  }
  return userStore.user.setting.openai_web.available_models.map((model) => ({
    label: t(`models.${model}`),
    value: model,
  }));
});

// Modify the watch for newConversationInfo changes
watch(
  () => {
    return [newConversationInfo.value.model];
  },
  async ([model]) => {
    if (model === 'gpt_4_plugins') {
      newConversationInfo.value.openaiWebPlugins = [];
      loadingPlugins.value = true;
      try {
        const res = await getInstalledOpenaiChatPluginsApi();
        availablePlugins.value = res.data;
      } catch (err) {
        Message.error(t('tips.NewConversationForm.failedToGetPlugins'));
      }
      loadingPlugins.value = false;
    }
    
    // Update the source based on the selected model
    if (model === 'gpt_3_5' || model === 'gpt_4') {
      newConversationInfo.value.source = 'openai_api';
    } else if (model === 'gpt_4_plugins') {
      newConversationInfo.value.source = 'openai_web';
    }
  },
  { immediate: true }
);

// Add a computed property to determine whether to render the plugins section
const shouldRenderPluginsSection = computed(() => {
  return newConversationInfo.value.model === 'gpt_4_plugins';
});
</script>
