declare global {
  interface Window {
    arkoseEnforcement: any;
    setupEnforcement: any;
  }
}

export type ResponseError = {
  error: string; // Error code string
};

export type ArkoseResponse = {
  token?: string; // Optional because it might not be present in all responses
  error?: ResponseError; // Optional for similar reasons
  height?: string; // Challenge frame height, e.g., "290px"
  width?: string; // Challenge frame width, e.g., "302px"
  suppressed?: boolean; // Whether the challenge was suppressed
};

export type ArkoseEnforcementConfig = {
  // publicKey: string;
  mode?: string;
  selector?: string;
  nonce?: string;
  onReady?: () => void;
  onShown?: () => void;
  onShow?: () => void;
  onSuppress?: (response: ArkoseResponse) => void;
  onCompleted?: (response: ArkoseResponse) => void;
  onReset?: () => void;
  onHide?: () => void;
  onError?: (response: ArkoseResponse) => void;
  onFailed?: (response: ArkoseResponse) => void;
};

function removeScript(scriptId: string) {
  const currentScript = document.getElementById(scriptId);
  if (currentScript) {
    currentScript.remove();
  }
}

export function setupEnforcement(
  arkoseUrl: string,
  config: ArkoseEnforcementConfig,
  scriptId: string,
  onLoaded: () => void,
  onError: (error: any) => void
): void {
  removeScript(scriptId);

  const script = document.createElement('script');
  script.setAttribute('data-callback', 'setupEnforcement');
  script.id = scriptId;
  script.type = 'text/javascript';
  script.src = arkoseUrl;
  script.async = true;
  script.defer = true;
  if (config.nonce) {
    script.setAttribute('data-nonce', config.nonce);
  }

  const setupEnforcement = (arkoseEnforcement: any) => {
    window.arkoseEnforcement = arkoseEnforcement;
    window.arkoseEnforcement.setConfig({
      selector: config.selector,
      mode: config.mode,
      onReady: config.onReady,
      onShown: config.onShown,
      onShow: config.onShow,
      onSuppress: config.onSuppress,
      onCompleted: config.onCompleted,
      onReset: config.onReset,
      onHide: config.onHide,
      onError: config.onError,
      onFailed: config.onFailed,
    });
  };
  window.setupEnforcement = setupEnforcement;

  script.onload = () => {
    onLoaded();
  };
  script.onerror = onError;

  document.body.appendChild(script);
}

export function removeEnforcement(scriptId: string) {
  if (window.arkoseEnforcement) {
    delete window.arkoseEnforcement;
  }
  if (window.setupEnforcement) {
    delete window.setupEnforcement;
  }
  removeScript(scriptId);
}

export function runEnforcement() {
  console.log('Running enforcement', window.arkoseEnforcement);
  if (window.arkoseEnforcement) {
    window.arkoseEnforcement.run();
  } else {
    console.error('Arkose Enforcment not set up');
  }
}

export function getArkoseToken(arkoseUrl: string): Promise<string | null> {
  return new Promise((resolve, reject) => {
    const config = {
      onReady() {
        console.log('Arkose is ready');
        runEnforcement();
      },
      onShown() {
        console.log('Arkose is shown');
      },
      onReset() {
        console.log('Arkose is reset');
      },
      onSuppress() {
        console.log('Arkose is suppressed');
      },
      onCompleted(response) {
        console.log('Arkose is completed', response);
        resolve(response.token || null);
      },
      onError(response) {
        const error = response.error?.error || 'null';
        reject(new Error(`Arkose error: ${error}`));
      },
      onFailed() {
        reject(new Error('Arkose Failed'));
      },
    } as ArkoseEnforcementConfig;

    // 调用 setupEnforcement 并传入配置
    setupEnforcement(
      arkoseUrl,
      config,
      'arkose-token-fetcher',
      () => {
        console.log('Arkose API is loaded');
      },
      (ev) => {
        console.error('Arkose API loaded error:', ev);
        reject(new Error('Arkose API loaded error'));
      }
    );
  });
}
