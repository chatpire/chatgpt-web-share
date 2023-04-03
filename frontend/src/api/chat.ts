import { AskParams, AskResponse, ConversationSchema } from "@/types/schema";
import axios from "axios";
import ApiUrl from "./url";
import { processNDJSON } from "./stream";

export function getAllConversationsApi(fetch_all: boolean = false) {
  return axios.get<Array<ConversationSchema>>(ApiUrl.Conversation, {
    params: { fetch_all },
  });
}

export function getConversationHistoryApi(conversation_id: string) {
  return axios.get<any>(ApiUrl.Conversation + "/" + conversation_id);
}

export function deleteConversationApi(conversation_id: string) {
  return axios.delete(ApiUrl.Conversation + "/" + conversation_id);
}

export function vanishConversationApi(conversation_id: string) {
  return axios.delete(ApiUrl.Conversation + "/" + conversation_id + "/vanish");
}

export function setConversationTitleApi(
  conversation_id: string,
  title: string
) {
  return axios.patch<ConversationSchema>(
    ApiUrl.Conversation + "/" + conversation_id,
    null,
    {
      params: { title },
    }
  );
}

export function generateConversationTitleApi(
  conversation_id: string,
  message_id: string
) {
  return axios.patch<ConversationSchema>(
    ApiUrl.Conversation + "/" + conversation_id + "/gen_title",
    null,
    {
      params: { message_id },
    }
  );
}

export function assignConversationToUserApi(
  conversation_id: string,
  username: string
) {
  return axios.patch(
    `${ApiUrl.Conversation}/${conversation_id}/assign/${username}`
  );
}

export async function askStreamApi(
  askParams: AskParams,
  onDataReceived: (data: any) => void,
  onError: (response: Response | null, error: Error) => Promise<void>,
  abortController: AbortController
) {
  const requestOptions: RequestInit = {
    method: "POST",
    body: JSON.stringify(askParams),
    signal: abortController.signal,
    headers: {
      "Content-Type": "application/json",
    },
  };

  try {
    const response = await fetch(import.meta.env.VITE_API_BASE_URL + ApiUrl.Conversation, requestOptions);

    if (response.ok) {
      if (response.headers.get("content-type") === "application/x-ndjson") {
        await processNDJSON<AskResponse>(
          response,
          onDataReceived,
          onError,
        );
      } else {
        await onError(response, new Error("Invalid content type"));
      }
    } else {
      // 这里不需要处理大部分错误情况。在后端中，若 openai 返回非 200 请求，会封装在 response 中返回给前端
      await onError(response, new Error(`Error ${response.status}: ${response.statusText}`));
    }
  } catch (error: any) {
    await onError(null, error);
  }
}
