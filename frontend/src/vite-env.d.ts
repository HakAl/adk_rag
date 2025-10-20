/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_VERSION: string
  readonly VITE_API_URL: string
  readonly VITE_APP_TITLE: string
  readonly VITE_HCAPTCHA_SITEKEY: string
  readonly VITE_APP_MODE?: 'full' | 'lite'
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}