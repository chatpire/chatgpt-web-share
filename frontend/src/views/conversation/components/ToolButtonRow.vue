<template>
  <div class="flex flex-row space-x-2 p-2 justify-center">
    <!-- 居中排列：清空、导出markdown、使用prompt、发送 -->
    <n-button secondary size="small">
      <template #icon>
        <n-icon>
          <InformationCircle />
        </n-icon>
      </template>
    </n-button>
    <n-button secondary type="primary" size="small">
      <template #icon>
        <n-icon>
          <LogoMarkdown />
        </n-icon>
      </template>
    </n-button>
    <n-button secondary type="info" size="small">
      <template #icon>
        <n-icon>
          <Build />
        </n-icon>
      </template>
    </n-button>
  </div>
</template>

<script setup lang="ts">
import { InformationCircle, LogoMarkdown, Build } from '@vicons/ionicons5';
</script>