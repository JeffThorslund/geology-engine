/**
 * Health check script — pings the geology-engine /health endpoint.
 *
 * Usage:
 *   BASE_URL=https://your-app.railway.app npm run health
 *
 * Defaults to http://localhost:8000 when BASE_URL is not set.
 */

const BASE_URL = process.env.BASE_URL ?? "http://localhost:8000";

async function main() {
  const url = `${BASE_URL}/health`;
  console.log(`Checking health at ${url} ...`);

  try {
    const res = await fetch(url);
    if (!res.ok) {
      console.error(`Health check failed: HTTP ${res.status}`);
      process.exit(1);
    }

    const body = await res.json();
    console.log("Response:", JSON.stringify(body, null, 2));

    if (body.status === "ok") {
      console.log("Service is healthy.");
      process.exit(0);
    } else {
      console.error("Unexpected status:", body.status);
      process.exit(1);
    }
  } catch (err) {
    console.error("Health check failed:", err);
    process.exit(1);
  }
}

main();
