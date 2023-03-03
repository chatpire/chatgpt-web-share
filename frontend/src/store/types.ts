import { UserRead, ConversationSchema } from "@/types/schema";

interface UserState {
  user: UserRead | null;
  savedUsername: string | null;
  savedPassword: string | null;
}

export type { UserState };
