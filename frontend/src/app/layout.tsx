import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "readeb — AI PDF Study Assistant",
  description:
    "Turn university textbook PDFs into summaries, flashcards, quizzes, mind maps, audio lessons and study notes.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-slate-50 text-slate-900">
        <header className="border-b border-slate-200 bg-white">
          <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-4">
            <Link href="/" className="flex items-center gap-2 font-semibold">
              <span className="grid h-8 w-8 place-items-center rounded-lg bg-indigo-600 text-sm font-bold text-white">
                rb
              </span>
              <span className="text-lg">readeb</span>
              <span className="hidden text-sm font-normal text-slate-500 sm:inline">
                AI PDF Study Assistant
              </span>
            </Link>
            <a
              href="https://github.com/karimimh/readeb"
              target="_blank"
              rel="noreferrer"
              className="text-sm text-slate-500 hover:text-slate-900"
            >
              GitHub
            </a>
          </div>
        </header>
        <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-8">{children}</main>
        <footer className="border-t border-slate-200 bg-white">
          <div className="mx-auto max-w-5xl px-4 py-6 text-sm text-slate-500">
            readeb — convert textbooks into study materials.
          </div>
        </footer>
      </body>
    </html>
  );
}
