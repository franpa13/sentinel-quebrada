import { Suspense } from "react";
import { Shell } from "@/components/Shell";

type Query = Promise<Record<string, string | string[] | undefined>>;

async function ShellFromQuery({ searchParams }: { searchParams: Query }) {
  const { vista } = await searchParams;
  return <Shell initial={vista === "cuenca" ? "cuenca" : "viaje"} />;
}

export default function Home({ searchParams }: { searchParams: Query }) {
  return <Suspense fallback={<div className="atlas" />}>
    <ShellFromQuery searchParams={searchParams} />
  </Suspense>;
}
