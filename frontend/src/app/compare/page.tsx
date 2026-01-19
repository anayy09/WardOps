"use client";

import { Suspense } from "react";
import { CompareContent } from "./compare-content";

function CompareSkeleton() {
  return (
    <div className="flex h-screen items-center justify-center">
      <div className="text-center">Loading comparison...</div>
    </div>
  );
}

export default function ComparePage() {
  return (
    <Suspense fallback={<CompareSkeleton />}>
      <CompareContent />
    </Suspense>
  );
}

