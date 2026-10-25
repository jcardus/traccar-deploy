import qs from 'querystring';

// Parse explicitly so encoded dates and duplicate keys also work on older njs.
function archive(r) {
    const values = qs.parse(r.variables.args || '', '&', '=', { maxKeys: 0 }).from;
    const from = Array.isArray(values) ? values[0] : values;
    const oldest = new Date();
    const weeks = parseInt(r.variables.database_retention_weeks || '2');
    oldest.setUTCDate(oldest.getUTCDate() - weeks * 7);
    return from && new Date(from).getTime() < oldest.getTime() ? '1' : '0';
}

export default { archive };
