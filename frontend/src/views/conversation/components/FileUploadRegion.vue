<template>
  <div class="flex flex-row lt-sm:flex-col sm:space-x-4 w-full">
    <n-upload
      v-model:file-list="fileList"
      class="lt-sm:mb-4"
      multiple
      action=""
      :show-file-list="false"
      :show-cancel-button="false"
      :show-remove-button="false"
      :show-retry-button="false"
      :trigger-style="{ width: '100%' }"
      :custom-request="customRequest"
    >
      <n-upload-dragger class="lt-sm:hidden">
        <div class="mb-2">
          <n-icon size="48" :depth="3">
            <UploadFileRound />
          </n-icon>
        </div>
        <n-text style="font-size: 16px">
          {{ $t('tips.dragFileHere') }}
        </n-text>
        <n-p depth="3" style="margin: 8px 0 0 0">
          {{ $t('tips.fileUploadRequirements') }}
        </n-p>
      </n-upload-dragger>

      <n-upload-trigger abstract>
        <n-button class="sm:hidden">
          {{ $t('commons.selectFile') }}
        </n-button>
      </n-upload-trigger>
    </n-upload>

    <n-upload v-model:file-list="fileList" abstract multiple>
      <n-card :content-style="{ padding: '1em' }">
        <n-empty
          v-if="fileList.length == 0"
          :description="$t('commons.emptyFileList')"
          class="h-full flex items-center justify-center"
        />
        <n-scrollbar v-else>
          <n-upload-file-list />
        </n-scrollbar>
      </n-card>
    </n-upload>
  </div>
</template>

<script setup lang="ts">
import { UploadFileRound } from '@vicons/material';
import { UploadCustomRequestOptions, UploadFileInfo } from 'naive-ui';
import { computed, ref } from 'vue';
import { useI18n } from 'vue-i18n';

import {
  completeUploadFileToOpenaiWeb,
  requestUploadFileFromLocalToOpenaiWeb,
  startUploadFileToOpenaiWeb,
  uploadFileToAzureBlob,
  uploadFileToLocalApi,
} from '@/api/files';
import { UploadedFileInfoSchema } from '@/types/schema';
import { Message } from '@/utils/tips';

const { t } = useI18n();
const fileList = ref<UploadFileInfo[]>([]);

const props = defineProps<{
  uploadedFileInfos: UploadedFileInfoSchema[];
}>();

const emits = defineEmits<{
  (e: 'update:uploaded-file-infos', value: UploadedFileInfoSchema[]): void;
}>();

const uploadedFileInfos = computed({
  get() {
    return props.uploadedFileInfos;
  },
  set(value) {
    emits('update:uploaded-file-infos', value);
  },
});

const isUploading = computed(() => {
  return fileList.value.some((file) => file.status === 'uploading');
});

const customRequest = async ({ file, onFinish, onError, onProgress }: UploadCustomRequestOptions) => {
  try {
    if (!file.file) {
      throw new Error('Failed to get the file.');
    }
    // 1. 先调用 startUploadFileToOpenaiWeb
    const uploadInfo = {
      file_name: file.name,
      file_size: file.file?.size,
      use_case: 'ace_upload', // 您需要根据实际情况来设定 use_case
    };

    onProgress({ percent: 0 });

    const startUploadResponse = await startUploadFileToOpenaiWeb(uploadInfo);

    // 检查返回的状态，如果有错误或者没有返回 upload_file_info，抛出错误
    if (!startUploadResponse.data || startUploadResponse.data.strategy === 'disable_upload') {
      throw new Error('Failed to start the upload process.');
    }

    // 2. 若响应中 upload_file_info 不为空，进入 browser 上传流程
    if (startUploadResponse.data.upload_file_info) {
      if (!startUploadResponse.data.upload_file_info.openai_web_info) {
        throw new Error('Failed to get the upload url.');
      }

      const signedUrl = startUploadResponse.data.upload_file_info.openai_web_info.upload_url;

      // 2.1 调用 uploadFileToAzureBlob 上传文件到 Azure Blob
      await uploadFileToAzureBlob(file.file as File, signedUrl!, onProgress);

      // 2.2 调用 completeUploadFileToOpenaiWeb 通知服务端完成上传
      const completeUploadResponse = await completeUploadFileToOpenaiWeb(startUploadResponse.data.upload_file_info.id);

      if (completeUploadResponse.status !== 200) {
        throw new Error('Failed to complete the upload process.');
      }

      const uploadedFileInfo = completeUploadResponse.data;
      uploadedFileInfos.value = [...uploadedFileInfos.value, uploadedFileInfo];
    }
    // 3. 若响应中 upload_file_info 为空，进入服务端中转上传流程
    else {
      // 3.1 调用 uploadFileToLocalApi 上传文件到服务端
      const localUploadResponse = await uploadFileToLocalApi(file.file as File);

      if (localUploadResponse.status !== 200) {
        throw new Error('Failed to upload the file to the local server.');
      }

      // 3.2 调用 requestUploadFileFromLocalToOpenaiWeb 通知服务端上传文件到 OpenAI Web
      const fileFromLocalToOpenaiWebResponse = await requestUploadFileFromLocalToOpenaiWeb(localUploadResponse.data.id);

      if (fileFromLocalToOpenaiWebResponse.status !== 200) {
        throw new Error('Failed to upload the file from local to OpenAI Web.');
      }

      const uploadedFileInfo = fileFromLocalToOpenaiWebResponse.data;
      uploadedFileInfos.value = [...uploadedFileInfos.value, uploadedFileInfo];
    }

    // 文件上传成功完成
    Message.success(t('tips.fileUploadSuccess', [file.name]));
    onFinish();
  } catch (error) {
    Message.error(t('tips.fileUploadFailed', [file.name]));
    console.error(error);
    onError();
  }
};

defineExpose({ isUploading, fileList });
</script>
