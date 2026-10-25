import qs from 'querystring';

// Parse explicitly so encoded dates and duplicate keys also work on older njs.
function archive(r) {
    const values = qs.parse(r.variables.args || '', '&', '=', { maxKeys: 0 }).from;
    const from = Array.isArray(values) ? values[0] : values;
    const oldest = new Date();
    oldest.setUTCDate(oldest.getUTCDate() - 7);
    return from && new Date(from).getTime() < oldest.getTime() ? '1' : '0';
}

export default { archive };
