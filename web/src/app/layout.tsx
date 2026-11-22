import type { Metadata } from "next";
import "./globals.css";
import "./atlas.css";

export const metadata: Metadata = {
  title: "Sentinel Quebrada · Volcán",
  description:
    "Motor de alerta temprana aluvional para Volcán, Jujuy. Índice explicable, fast-trigger y margen de reacción.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
