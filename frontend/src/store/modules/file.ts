import { defineStore } from 'pinia';

import { FileState } from '../types';

const useFileStore = defineStore('file', {
  state: (): FileState => ({
    uploadedFileInfos: [],
    naiveUiUploadFileInfos: [],
    naiveUiFileIdToServerFileIdMap: {},
  }),
  actions: {
    clear() {
      this.uploadedFileInfos = [];
      this.naiveUiUploadFileInfos = [];
      this.naiveUiFileIdToServerFileIdMap = {};
    },
  },
});

export default useFileStore;
