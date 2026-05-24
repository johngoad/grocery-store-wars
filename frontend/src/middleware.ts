import { NextRequest, NextResponse } from "next/server";

const AUTH_USER = "iga";
const AUTH_PASS = process.env.AUTH_PASSWORD || "iga-vashon-2026";

export function middleware(request: NextRequest) {
  // Skip auth for API routes and static files
  if (
    request.nextUrl.pathname.startsWith("/_next") ||
    request.nextUrl.pathname.startsWith("/api") ||
    request.nextUrl.pathname.startsWith("/favicon.ico")
  ) {
    return NextResponse.next();
  }

  const authHeader = request.headers.get("authorization");

  if (authHeader) {
    const [scheme, encoded] = authHeader.split(" ");
    if (scheme === "Basic") {
      const decoded = atob(encoded);
      const [user, pass] = decoded.split(":");
      if (user === AUTH_USER && pass === AUTH_PASS) {
        return NextResponse.next();
      }
    }
  }

  return new NextResponse("Access Denied", {
    status: 401,
    headers: {
      "WWW-Authenticate": 'Basic realm="GSW Dashboard", charset="UTF-8"',
    },
  });
}

export const config = {
  matcher: ["/((?!_next|api|favicon.ico).*)"],
};
