export const textMimeTypes = [
  'text/x-csharp',
  'text/x-java',
  'text/x-sh',
  'text/x-typescript',
  'application/pdf',
  'text/plain',
  'application/json',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/msword',
  'text/javascript',
  'text/x-c',
  'text/x-ruby',
  'text/x-c++',
  'text/x-tex',
  'text/x-php',
  'application/x-latext',
  'application/vnd.openxmlformats-officedocument.presentationml.presentation',
  'text/html',
  'text/x-script.python',
  'text/markdown',
];

export const imageMimeTypes = ['image/png', 'image/webp', 'image/jpeg', 'image/gif'];

export const acceptedMimeTypes = [...textMimeTypes, ...imageMimeTypes];

export function mimeTypeToHumanReadable(mimeType: string): string {
  const mimeTypesMap: { [key: string]: string } = {
    'text/x-csharp': 'Code',
    'text/x-java': 'Code',
    'text/x-sh': 'Code',
    'text/x-typescript': 'Code',
    'application/pdf': 'PDF Document',
    'text/plain': 'Plain Text',
    'application/json': 'Code',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'Office Document',
    'application/msword': 'Office Document',
    'text/javascript': 'Code',
    'text/x-c': 'Code',
    'text/x-ruby': 'Code',
    'text/x-c++': 'Code',
    'text/x-tex': 'Code',
    'text/x-php': 'Code',
    'application/x-latext': 'Code',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'Office Document',
    'text/html': 'Code',
    'text/x-script.python': 'Code',
    'text/markdown': 'Markdown',
  };

  return mimeTypesMap[mimeType] || 'Others';
}

export async function getImageDimensions(file: File) {
  const resolvePromise = new Promise<{ width: number; height: number }>((resolve, reject) => {
    const img = new Image();
    img.onload = () => {
      resolve({ width: img.width, height: img.height });
    };
    img.onerror = (error) => {
      reject(new Error(`Failed to load image: ${error}`));
    };
    img.src = URL.createObjectURL(file);
  });
  try {
    const dimensions = await resolvePromise;
    const width = dimensions.width;
    const height = dimensions.height;
    return { width, height };
  } catch (error) {
    console.error(error);
    return { width: undefined, height: undefined };
  }
}

export function isImage(file: File) {
  return file.type.startsWith('image/');
}

export function isSupportedImage(file: File) {
  return imageMimeTypes.includes(file.type);
}
