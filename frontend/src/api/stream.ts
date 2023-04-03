
export async function processNDJSON<T>(
  response: Response,
  onDataReceived: (data: T) => void,
  onError: (response: Response, error: Error) => Promise<void>
): Promise<void> {
  const reader = response.body?.getReader();
  const decoder = new TextDecoder('utf-8');

  if (!reader) {
    await onError(response, new Error('No response body reader found'));
    return;
  }

  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      const lines = decoder.decode(value, { stream: true }).split('\n');
      for (const line of lines) {
        if (line) {
          const data = JSON.parse(line);
          onDataReceived(data);
        }
      }
    }
  } catch (error: any) {
    if (error.name === 'AbortError') {
      console.log('Stream aborted.');
    } else {
      await onError(response, error);
    }
  }
}