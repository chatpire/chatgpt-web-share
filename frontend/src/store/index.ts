import { createPinia } from 'pinia';

import useAppStore from './modules/app';
import useConversationStore from './modules/conversation';
import useFileStore from './modules/file';
import useUserStore from './modules/user';

const pinia = createPinia();

export { useAppStore, useConversationStore, useFileStore, useUserStore };

export default pinia;
