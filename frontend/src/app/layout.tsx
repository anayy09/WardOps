import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/providers";
import { CommandPalette } from "@/components/command-palette";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "WardOps Digital Twin",
  description: "Hospital Operations Command Center",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <Providers>
          {children}
          <CommandPalette />
        </Providers>
      </body>
    </html>
  );
}
