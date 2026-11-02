// Run with: npm run test:unit (runs under several time zones; see package.json)
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { parseDate, monthKey } from './date.js'

test('date-only strings parse as local calendar dates, not UTC midnight', () => {
  const d = parseDate('2025-12-15')
  assert.equal(d.getFullYear(), 2025)
  assert.equal(d.getMonth(), 11)
  assert.equal(d.getDate(), 15)
  assert.equal(d.getHours(), 0)
})

test('date-time strings without an offset keep their local wall-clock time', () => {
  const d = parseDate('2025-01-31T22:30:00')
  assert.equal(d.getDate(), 31)
  assert.equal(d.getHours(), 22)
})

test('Date objects are copied, not mutated or shared', () => {
  const original = new Date(2025, 0, 2)
  const copy = parseDate(original)
  assert.notEqual(copy, original)
  assert.equal(copy.getTime(), original.getTime())
})

test('missing or invalid input returns null', () => {
  for (const value of [null, undefined, '', 'not a date', '2025-13-45']) {
    assert.equal(parseDate(value), null, `expected null for ${JSON.stringify(value)}`)
  }
})

test('monthKey uses the local month, not the UTC month', () => {
  // 22:00 on Jan 31 is already Feb 1 in UTC for zones behind UTC
  assert.equal(monthKey('2025-01-31T22:00:00'), '2025-01')
  // Early on the 1st is still the previous month in UTC for zones ahead of UTC
  assert.equal(monthKey('2025-02-01T01:00:00'), '2025-02')
  assert.equal(monthKey('2025-09-01'), '2025-09')
  assert.equal(monthKey('garbage'), null)
})
