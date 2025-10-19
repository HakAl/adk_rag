/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_VERSION: string
  // add more env variables here as needed
  readonly VITE_API_URL: string
  readonly VITE_APP_TITLE: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}