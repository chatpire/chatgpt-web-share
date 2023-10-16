import { defineStore } from 'pinia';

import { FileState } from '../types';

const useFileStore = defineStore('file', {
  state: (): FileState => ({
    attachments: {
      uploadedFileInfos: [],
      naiveUiUploadFileInfos: [],
      naiveUiFileIdToServerFileIdMap: {},
    },
    images: {
      uploadedFileInfos: [],
      naiveUiUploadFileInfos: [],
      naiveUiFileIdToServerFileIdMap: {},
      imageMetadataMap: {},
    },
  }),
  actions: {
    clearAll() {
      this.clearAttachments();
      this.clearImages();
    },
    clearAttachments() {
      this.attachments.uploadedFileInfos = [];
      this.attachments.naiveUiUploadFileInfos = [];
      this.attachments.naiveUiFileIdToServerFileIdMap = {};
    },
    clearImages() {
      this.images.uploadedFileInfos = [];
      this.images.naiveUiUploadFileInfos = [];
      this.attachments.naiveUiFileIdToServerFileIdMap = {};
    },
  },
});

export default useFileStore;
