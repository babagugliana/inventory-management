// Date parsing helpers.
//
// JavaScript parses a date-only ISO string ("2025-12-15") as midnight UTC, but a
// date-time string without an offset ("2025-12-15T00:00:00") as local time. In time
// zones behind UTC the date-only form therefore displays as the previous day.
// Our data mixes both forms (task due dates, join dates and transaction dates are
// date-only; order dates carry a time), so always parse through parseDate().

const DATE_ONLY = /^(\d{4})-(\d{2})-(\d{2})$/

/**
 * Parse an API/mock date value into a local Date.
 * Returns null for missing or invalid input so callers can show a fallback.
 */
export function parseDate(value) {
  if (value === null || value === undefined || value === '') return null
  if (value instanceof Date) return isNaN(value.getTime()) ? null : new Date(value.getTime())

  const match = typeof value === 'string' ? DATE_ONLY.exec(value) : null
  if (match) {
    const [year, month, day] = [Number(match[1]), Number(match[2]), Number(match[3])]
    const date = new Date(year, month - 1, day)
    // new Date(2025, 12, 45) silently rolls over; reject dates that don't round-trip
    if (date.getFullYear() !== year || date.getMonth() !== month - 1 || date.getDate() !== day) return null
    return date
  }

  const date = new Date(value)
  return isNaN(date.getTime()) ? null : date
}

/**
 * Local "YYYY-MM" key for grouping by month. Use this instead of
 * toISOString().slice(0, 7), which converts to UTC and can move a late-evening
 * or early-morning date into the neighbouring month.
 */
export function monthKey(value) {
  const date = parseDate(value)
  if (!date) return null
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
}
