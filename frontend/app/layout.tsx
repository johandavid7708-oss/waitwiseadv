import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'WaitWise - Know Before You Go',
  description: 'Predictive human-flow intelligence platform with AI learning',
  viewport: 'width=device-width, initial-scale=1',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
