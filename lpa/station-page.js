// SPDX-License-Identifier: AGPL-3.0-or-later
// Standalone observation pages do not need upstream interactive controls.
async function llegeixDades(name) {
  const url = new URL(name, location.href);
  url.searchParams.set('t', Date.now());
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000);
  try {
    const response = await fetch(url, {cache:'no-store', signal:controller.signal});
    if (!response.ok) throw new Error('Weather data unavailable');
    return await response.json();
  } finally { clearTimeout(timeout); }
}
function dadesVelles(data) {
  const age = Date.now() - new Date(data.generat).getTime();
  return !Number.isFinite(age) || age > 2 * 60 * 60 * 1000 || age < -300000;
}
