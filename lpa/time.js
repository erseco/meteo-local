// SPDX-License-Identifier: AGPL-3.0-or-later
// Explicit site-local dates without changing the browser's global Date object.
// The upstream UI uses local calendar getters/setters, not only formatters.
const LPA_ZONE = 'Atlantic/Canary';
const LPA_DATE_FORMAT = new Intl.DateTimeFormat('en-GB', {
  timeZone: LPA_ZONE, year: 'numeric', month: '2-digit', day: '2-digit',
  hour: '2-digit', minute: '2-digit', second: '2-digit', hourCycle: 'h23',
});
function lpaParts(date) {
  if (!Number.isFinite(date.getTime())) return [NaN, NaN, NaN, NaN, NaN, NaN, NaN];
  const p = Object.fromEntries(LPA_DATE_FORMAT.formatToParts(date).map(x => [x.type, x.value]));
  return [+p.year, +p.month - 1, +p.day, +p.hour, +p.minute, +p.second, date.getUTCMilliseconds()];
}
function lpaOffset(timestamp) {
  const date = new Date(timestamp);
  return Date.UTC(...lpaParts(date)) - timestamp;
}
function lpaInstant(parts, offset = null) {
  const wall = Date.UTC(...parts);
  let result = wall - (offset ?? lpaOffset(wall));
  for (let i = 0; i < 3; i++) {
    const next = wall - lpaOffset(result);
    if (next === result) return result;
    result = next;
  }
  return result;
}
class LpaDate extends Date {
  constructor(...args) {
    if (args.length > 1) {
      const [y, m, d = 1, h = 0, min = 0, s = 0, ms = 0] = args;
      super(lpaInstant([y, m, d, h, min, s, ms]));
    } else if (typeof args[0] === 'string' && /^\d{4}-\d\d-\d\dT\d\d:\d\d(?::\d\d(?:\.\d+)?)?$/.test(args[0])) {
      const parsed = new Date(args[0] + 'Z');
      super(lpaInstant([parsed.getUTCFullYear(), parsed.getUTCMonth(), parsed.getUTCDate(),
        parsed.getUTCHours(), parsed.getUTCMinutes(), parsed.getUTCSeconds(), parsed.getUTCMilliseconds()]));
    } else { super(...args); }
  }
  getFullYear() { return lpaParts(this)[0]; }
  getMonth() { return lpaParts(this)[1]; }
  getDate() { return lpaParts(this)[2]; }
  getDay() { return new Date(Date.UTC(...lpaParts(this).slice(0, 3))).getUTCDay(); }
  getHours() { return lpaParts(this)[3]; }
  getMinutes() { return lpaParts(this)[4]; }
  getSeconds() { return lpaParts(this)[5]; }
  getMilliseconds() { return this.getUTCMilliseconds(); }
  getTimezoneOffset() { return -lpaOffset(this.getTime()) / 60000 + 0; }
  _set(index, values) {
    const parts = lpaParts(this);
    parts.splice(index, values.length, ...values);
    return this.setTime(lpaInstant(parts, lpaOffset(this.getTime())));
  }
  setFullYear(...values) { return this._set(0, values); }
  setMonth(...values) { return this._set(1, values); }
  setDate(...values) { return this._set(2, values); }
  setHours(...values) { return this._set(3, values); }
  setMinutes(...values) { return this._set(4, values); }
  setSeconds(...values) { return this._set(5, values); }
  setMilliseconds(...values) { return this._set(6, values); }
  toDateString() { return this.toLocaleDateString('en-CA'); }
  toLocaleDateString(locale, options = {}) { return super.toLocaleDateString(locale, { ...options, timeZone: LPA_ZONE }); }
  toLocaleTimeString(locale, options = {}) { return super.toLocaleTimeString(locale, { ...options, timeZone: LPA_ZONE }); }
  toLocaleString(locale, options = {}) { return super.toLocaleString(locale, { ...options, timeZone: LPA_ZONE }); }
}
