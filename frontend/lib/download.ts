import { Capacitor } from '@capacitor/core'

/**
 * Download a file. On native (Capacitor), saves to device Downloads folder.
 * On web, uses the standard blob download approach.
 */
export async function downloadFile(
  blob: Blob,
  filename: string
): Promise<void> {
  if (Capacitor.isNativePlatform()) {
    // Dynamic import to avoid bundling Filesystem on web
    const { Filesystem, Directory } = await import('@capacitor/filesystem')

    const base64 = await blobToBase64(blob)

    await Filesystem.writeFile({
      path: filename,
      data: base64,
      directory: Directory.Documents,
    })

    // Try to open share dialog so user can see/open the file
    try {
      const { Share } = await import('@capacitor/share')
      const result = await Filesystem.getUri({
        path: filename,
        directory: Directory.Documents,
      })
      await Share.share({
        title: filename,
        url: result.uri,
      })
    } catch {
      // Share not available, just notify
    }
  } else {
    // Web: standard download
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  }
}

/**
 * Download a data URL (e.g. from canvas.toDataURL).
 * On native, saves to device. On web, triggers download.
 */
export async function downloadDataUrl(
  dataUrl: string,
  filename: string
): Promise<void> {
  if (Capacitor.isNativePlatform()) {
    const { Filesystem, Directory } = await import('@capacitor/filesystem')

    // Extract base64 from data URL
    const base64 = dataUrl.split(',')[1]

    await Filesystem.writeFile({
      path: filename,
      data: base64,
      directory: Directory.Documents,
    })

    try {
      const { Share } = await import('@capacitor/share')
      const result = await Filesystem.getUri({
        path: filename,
        directory: Directory.Documents,
      })
      await Share.share({
        title: filename,
        url: result.uri,
      })
    } catch {
      // Share not available
    }
  } else {
    const a = document.createElement('a')
    a.href = dataUrl
    a.download = filename
    a.click()
  }
}

function blobToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const result = reader.result as string
      // Remove the data:...;base64, prefix
      resolve(result.split(',')[1])
    }
    reader.onerror = reject
    reader.readAsDataURL(blob)
  })
}
