const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const qs = require('node:querystring');

const now = Date.parse('2026-10-25T12:00:00.000Z');
class FixedDate extends Date {
    constructor(...args) { super(...(args.length ? args : [now])); }
    static now() { return now; }
}
const source = fs.readFileSync(__dirname + '/reports.js', 'utf8')
    .replace("import qs from 'querystring';", '')
    .replace('export default { archive, upstreamUri };', 'globalThis.archive = archive; globalThis.upstreamUri = upstreamUri;');
const context = vm.createContext({ Date: FixedDate, qs });
vm.runInContext(source, context);
const cases = [
    ['missing from', '', '0'],
    ['empty from', 'from=', '0'],
    ['invalid from', 'from=invalid', '0'],
    ['recent', 'from=2026-10-24T12%3A00%3A00Z', '0'],
    ['exact cutoff', 'from=2026-10-11T12:00:00.000Z', '0'],
    ['one millisecond older', 'from=2026-10-11T11:59:59.999Z', '1'],
    ['timezone offset', 'from=2026-10-11T13%3A00%3A00%2B01%3A00', '0'],
    ['first duplicate wins', 'from=2026-10-01&from=2026-10-25', '1'],
    ['empty first duplicate wins', 'from=&from=2026-10-01', '0'],
    ['encoded key', '%66rom=2026-10-01&deviceId=1&deviceId=2', '1'],
    ['case sensitive key', 'From=2026-10-01', '0'],
    ['malformed encoding', 'from=%ZZ', '0'],
];
for (const [name, args, expected] of cases) {
    test(name, () => assert.equal(context.archive({ variables: { args } }), expected));
}

test('configurable retention of one week', () => {
    assert.equal(context.archive({variables: {args: 'from=2026-10-15', database_retention_weeks: '1'}}), '1');
});
test('default two weeks keeps ten-day-old requests local', () => {
    assert.equal(context.archive({variables: {args: 'from=2026-10-15'}}), '0');
});
test('configured three weeks keeps twenty-day-old requests local', () => {
    assert.equal(context.archive({variables: {args: 'from=2026-10-05', database_retention_weeks: '3'}}), '0');
});
test('prefix removal preserves encoded query and repeated arguments', () => {
    assert.equal(context.upstreamUri({variables: {request_uri: '/traccar/api/positions?from=a%2Bb&id=1&id=2'}}),
        '/api/positions?from=a%2Bb&id=1&id=2');
});
test('unprefixed path and query remain unchanged', () => {
    assert.equal(context.upstreamUri({variables: {request_uri: '/api/reports/route?value=/traccar/'}}),
        '/api/reports/route?value=/traccar/');
});
