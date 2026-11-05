import type { Metadata } from "next";
import "./tokens.css";
import "./globals.css";
export const metadata: Metadata = {
  title: "More Than Meets the AI",
  icons: { icon: "/design/assets/more-than-meets-the-ai-icon.png" },
  description: "Make your player, grab your people, and start drawing.",
};
export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
