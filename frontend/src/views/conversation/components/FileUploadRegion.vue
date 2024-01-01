<template>
  <div v-if="props.mode === 'legacy_code_interpreter'" class="flex flex-row lt-sm:flex-col sm:space-x-4 w-full">
    <n-upload
      ref="uploadLegacyRef"
      v-model:file-list="fileStore.naiveUiUploadFileInfos"
      class="lt-sm:mb-4"
      multiple
      :disabled="props.disabled"
      :show-file-list="false"
      :trigger-style="{ width: '100%' }"
      :custom-request="customRequest"
      :max="10"
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

    <n-upload
      v-model:file-list="fileStore.naiveUiUploadFileInfos"
      abstract
      multiple
      :disabled="props.disabled"
      :custom-request="customRequest"
      :show-cancel-button="true"
      :show-remove-button="true"
      :show-retry-button="true"
      :on-remove="removeFile"
      :max="10"
    >
      <n-card :content-style="{ padding: '1em' }">
        <n-empty
          v-if="fileStore.naiveUiUploadFileInfos.length == 0"
          :description="$t('commons.emptyFileList')"
          class="h-full flex items-center justify-center"
        />
        <n-scrollbar v-else>
          <n-upload-file-list />
        </n-scrollbar>
      </n-card>
    </n-upload>
  </div>

  <div v-else-if="props.mode === 'all'" class="flex flex-row lt-sm:flex-col sm:space-x-4 w-full">
    <n-upload
      v-model:file-list="fileStore.naiveUiUploadFileInfos"
      class="lt-sm:hidden"
      multiple
      :show-file-list="false"
      :trigger-style="{ width: '100%' }"
      :disabled="props.disabled"
      :custom-request="customRequest"
      :accept="acceptedMimeTypes.join(',')"
      :on-before-upload="checkFileBeforeUpload"
      :max="10"
    >
      <n-upload-dragger class="lt-sm:hidden h-44">
        <div class="mb-2">
          <n-icon size="48" :depth="3">
            <UploadFileRound />
          </n-icon>
        </div>
        <n-text style="font-size: 16px">
          {{ $t('tips.dragFileOrImageHere') }}
        </n-text>
        <n-p depth="3" style="margin: 8px 0 0 0">
          {{ $t('tips.gpt4UploadingRequirements') }}
        </n-p>
      </n-upload-dragger>
    </n-upload>

    <n-upload
      ref="uploadAllRef"
      v-model:file-list="fileStore.naiveUiUploadFileInfos"
      abstract
      multiple
      :disabled="props.disabled"
      :custom-request="customRequest"
      :show-cancel-button="true"
      :show-remove-button="true"
      :show-retry-button="true"
      :on-remove="removeFile"
      list-type="image"
      :accept="acceptedMimeTypes.join(',')"
      :on-before-upload="checkFileBeforeUpload"
      :max="10"
    >
      <n-upload-trigger>
        <n-button style="width: 100%;" class="sm:hidden mb-3">
          {{ $t('commons.selectFile') }}
        </n-button>
      </n-upload-trigger>

      <n-card :content-style="{ padding: '0.75rem' }">
        <n-empty
          v-if="fileStore.naiveUiUploadFileInfos.length == 0"
          :description="$t('commons.emptyFileList')"
          class="h-full flex items-center justify-center"
        />
        <n-scrollbar v-else class="sm:max-h-37 max-h-44">
          <n-upload-file-list />
        </n-scrollbar>
      </n-card>
    </n-upload>
  </div>
</template>

<script setup lang="ts">
import { UploadFileRound } from '@vicons/material';
import { UploadCustomRequestOptions, UploadFileInfo } from 'naive-ui';
import { v4 as uuidv4 } from 'uuid';
import { computed, nextTick, ref } from 'vue';
import { useI18n } from 'vue-i18n';

import {
  completeUploadFileToOpenaiWeb,
  requestUploadFileFromLocalToOpenaiWeb,
  startUploadFileToOpenaiWeb,
  uploadFileToAzureBlob,
  uploadFileToLocalApi,
} from '@/api/files';
import { useFileStore } from '@/store';
import { StartUploadRequestSchema, UploadedFileInfoSchema } from '@/types/schema';
import { Message } from '@/utils/tips';

import { acceptedMimeTypes, getImageDimensions, isImage, isSupportedImage } from '../utils/files';
const { t } = useI18n();

const fileStore = useFileStore();

const props = defineProps<{
  mode: 'all' | 'legacy_code_interpreter';
  disabled: boolean;
}>();

const uploadLegacyRef = ref();
const uploadAllRef = ref();

const checkFileBeforeUpload = (options: { file: UploadFileInfo; fileList: UploadFileInfo[] }) => {
  const rawFile = options.file.file as File;
  if (isImage(rawFile) && !isSupportedImage(rawFile)) {
    Message.warning(t('tips.unsupportedImageFormat', [options.file.name]));
    return false;
  }
  if (rawFile.size > 512 * 1024 * 1024) {
    Message.warning(t('tips.fileSizeTooLarge', [options.file.name]));
    return false;
  }
  return true;
};

const customRequest = async ({ file, onFinish, onError, onProgress }: UploadCustomRequestOptions) => {
  console.log('customRequest', file);
  try {
    if (!file.file) {
      throw new Error('Failed to get the file.');
    }

    const rawFile = file.file as File;
    if (isImage(rawFile) && !isSupportedImage(rawFile)) {
      Message.warning(t('tips.unsupportedImageFormat', [file.name]));
      onError();
      return;
    }
    const isImageType = isSupportedImage(rawFile);

    let useCase;
    if (isImageType) useCase = 'multimodal';
    else useCase = 'my_files';

    // 1. 先调用 startUploadFileToOpenaiWeb
    const uploadInfo = {
      file_name: file.name,
      file_size: file.file?.size,
      use_case: useCase,
      mime_type: file.file?.type,
    } as StartUploadRequestSchema;

    if (isImageType) {
      const { width, height } = await getImageDimensions(rawFile);
      uploadInfo.width = width;
      uploadInfo.height = height;
    }

    onProgress({ percent: 0 });

    const startUploadResponse = await startUploadFileToOpenaiWeb(uploadInfo);

    // 检查返回的状态，如果有错误或者没有返回 upload_file_info，抛出错误
    if (!startUploadResponse.data) {
      throw new Error('Failed to start the upload process.');
    }

    // 2. 若响应中 upload_file_info 不为空，进入 browser 上传流程
    let uploadedFileInfo;
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

      uploadedFileInfo = completeUploadResponse.data;
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

      uploadedFileInfo = fileFromLocalToOpenaiWebResponse.data;
      console.log('uploadedFileInfo', uploadedFileInfo);
    }

    fileStore.uploadedFileInfos = [...fileStore.uploadedFileInfos, uploadedFileInfo];
    fileStore.naiveUiFileIdToServerFileIdMap[file.id] = uploadedFileInfo.id;

    // 文件上传成功完成
    Message.success(t('tips.fileUploadSuccess', [file.name]));
    onFinish();
  } catch (error) {
    Message.error(t('tips.fileUploadFailed', [file.name]) + `: ${JSON.stringify(error)}`, { duration: 5 * 1000 });
    console.error(error);
    onError();
  }
};

const removeFile = async (options: { file: UploadFileInfo; fileList: Array<UploadFileInfo> }) => {
  const { file } = options;
  const fileId = fileStore.naiveUiFileIdToServerFileIdMap[file.id];
  if (fileId != undefined) {
    fileStore.uploadedFileInfos = fileStore.uploadedFileInfos.filter((uploadedFileInfo: UploadedFileInfoSchema) => {
      return uploadedFileInfo.id != fileId;
    });
    delete fileStore.naiveUiFileIdToServerFileIdMap[file.id];
    console.log(`Removed file ${file.name} with id ${fileId}`);
  }
  return true;
};

function addFile(file: File) {
  const fileId = uuidv4();
  const newFileInfo = {
    id: fileId,
    name: file.name,
    status: 'pending',
    file,
    type: file.type,
  } as UploadFileInfo;
  fileStore.naiveUiUploadFileInfos = [...fileStore.naiveUiUploadFileInfos, newFileInfo];
  console.log('addFile', fileStore.naiveUiUploadFileInfos);
  // console.log(uploadAllRef.value);
  nextTick(() => {
    if (props.mode === 'legacy_code_interpreter') {
      uploadLegacyRef.value?.submit();
    } else {
      uploadAllRef.value?.submit();
    }
    // console.log('ok');
  });
}

const isUploading = computed(() => {
  return fileStore.naiveUiUploadFileInfos.some((file) => file.status === 'uploading');
});

defineExpose({ isUploading, addFile });
</script>
