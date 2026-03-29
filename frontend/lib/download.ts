import { Capacitor } from '@capacitor/core'

/**
 * Download a file. On native (Capacitor), saves to device Documents folder.
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

    try {
      await Filesystem.writeFile({
        path: filename,
        data: base64,
        directory: Directory.Documents,
      })

      // Notify user the file was saved
      try {
        const { Toast } = await import('@capacitor/toast')
        await Toast.show({ text: `Arquivo salvo em Documentos: ${filename}`, duration: 'long' })
      } catch {
        // Toast plugin not available, use alert as fallback
        alert(`Arquivo salvo em Documentos: ${filename}`)
      }

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
        // Share not available, already notified via toast
      }
    } catch (writeError) {
      console.error('Filesystem.writeFile failed:', writeError)

      // Fallback: use Share plugin to let user choose where to save
      try {
        const { Share } = await import('@capacitor/share')
        const dataUrl = `data:${blob.type};base64,${base64}`
        await Share.share({
          title: filename,
          url: dataUrl,
        })
      } catch (shareError) {
        console.error('Share fallback also failed:', shareError)
        throw new Error('Nao foi possivel salvar o arquivo. Verifique as permissoes do aplicativo.')
      }
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

    try {
      await Filesystem.writeFile({
        path: filename,
        data: base64,
        directory: Directory.Documents,
      })

      // Notify user the file was saved
      try {
        const { Toast } = await import('@capacitor/toast')
        await Toast.show({ text: `Arquivo salvo em Documentos: ${filename}`, duration: 'long' })
      } catch {
        alert(`Arquivo salvo em Documentos: ${filename}`)
      }

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
        // Share not available, already notified via toast
      }
    } catch (writeError) {
      console.error('Filesystem.writeFile failed:', writeError)

      // Fallback: use Share plugin to let user choose where to save
      try {
        const { Share } = await import('@capacitor/share')
        await Share.share({
          title: filename,
          url: dataUrl,
        })
      } catch (shareError) {
        console.error('Share fallback also failed:', shareError)
        throw new Error('Nao foi possivel salvar o arquivo. Verifique as permissoes do aplicativo.')
      }
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
