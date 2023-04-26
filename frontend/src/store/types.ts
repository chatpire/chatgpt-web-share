import { RemovableRef } from '@vueuse/core';

import { Preference } from '@/types/custom';
import { UserRead } from '@/types/schema';

interface UserState {
  user: UserRead | null;
  savedUsername: string | null;
  savedPassword: string | null;
}

interface AppState {
  theme: any;
  language: any;
  preference: RemovableRef<Preference>;
}

export type { AppState, UserState };
