import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({
    data: { status: "ok" },
    meta: { checked_at: new Date().toISOString() },
  });
}
