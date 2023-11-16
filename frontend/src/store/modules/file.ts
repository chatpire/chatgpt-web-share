import { defineStore } from 'pinia';

import { FileState } from '../types';

const useFileStore = defineStore('file', {
  state: (): FileState => ({
    uploadedFileInfos: [],
    naiveUiUploadFileInfos: [],
    naiveUiFileIdToServerFileIdMap: {},
    imageMetadataMap: {},
  }),
  actions: {
    clear() {
      this.uploadedFileInfos = [];
      this.naiveUiUploadFileInfos = [];
      this.naiveUiFileIdToServerFileIdMap = {};
      this.imageMetadataMap = {};
    },
  },
});

export default useFileStore;
