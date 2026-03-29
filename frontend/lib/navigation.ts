import { Capacitor } from '@capacitor/core'

/**
 * Open an external URL (e.g., Stripe checkout).
 * On native: uses @capacitor/browser (in-app browser) so the user stays in the app.
 * On web: uses window.location.href (standard redirect).
 */
export async function openExternalUrl(url: string): Promise<void> {
  if (Capacitor.isNativePlatform()) {
    const { Browser } = await import('@capacitor/browser')
    await Browser.open({ url, presentationStyle: 'popover' })
  } else {
    window.location.href = url
  }
}

/**
 * Listen for the app being opened via a URL (deep link or browser return).
 * On native: listens for appUrlOpen events.
 * Returns a cleanup function.
 */
export function onAppUrl(callback: (url: string) => void): () => void {
  if (Capacitor.isNativePlatform()) {
    import('@capacitor/app').then(({ App }) => {
      App.addListener('appUrlOpen', (event) => {
        callback(event.url)
      })
    })
    return () => {
      import('@capacitor/app').then(({ App }) => {
        App.removeAllListeners()
      })
    }
  }
  return () => {}
}
