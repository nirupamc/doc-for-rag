import "./globals.css"
import { DisplayProvider } from "@/app/display-provider"

export const metadata = {
  title: "RagParser",
  description: "Inspect and normalize PDFs for reliable RAG ingestion.",
  icons: { icon: "/ragparser-mark.svg" },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" data-theme="crt" data-crt-effects="true">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Jersey+15&family=Pixelify+Sans:wght@400..700&family=VT323&display=swap" rel="stylesheet" />
      </head>
      <body><DisplayProvider>{children}</DisplayProvider></body>
    </html>
  )
}
