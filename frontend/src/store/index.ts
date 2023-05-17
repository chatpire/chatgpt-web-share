import { createPinia } from 'pinia';

import useAppStore from './modules/app';
import useConversationStore from './modules/conversation';
import useUserStore from './modules/user';

const pinia = createPinia();

export { useAppStore, useConversationStore, useUserStore };

export default pinia;
