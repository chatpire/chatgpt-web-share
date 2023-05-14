<template>
  <n-form
    :label-placement="'left'"
    :label-align="'left'"
    label-width="240px"
  >
    <n-form-item :label="$t('labels.credits')">
      <n-input-number v-model:value="credits" />
    </n-form-item>
  </n-form>
  <UpdateChatSourceSettingForm :user="props.user" @save="handleSave" />
</template>

<script lang="ts" setup>
import { ref, watch } from 'vue';

import { UserReadAdmin, UserSettingSchema } from '@/types/schema';

import UpdateChatSourceSettingForm from './UpdateChatSourceSettingForm.vue';

const props = defineProps<{
  user: UserReadAdmin | null;
}>();

const emits = defineEmits<{
  (e: 'save', userSetting: UserSettingSchema): void;
}>();

const credits = ref(0);

watch(
  () => props.user,
  async (user) => {
    if (!user) {
      return;
    }
    credits.value = user.setting.credits;
  },
  { immediate: true }
);

const handleSave = (updateUserSetting: UserSettingSchema) => {
  emits('save', updateUserSetting);
};
</script>