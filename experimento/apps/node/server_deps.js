const http = require('http'), crypto = require('crypto'), axios = require('axios');

const d = JSON.parse('{"a":1,"b":[1,2,3]}');

crypto.createHash('sha256').update(JSON.stringify(d)).digest('hex');
axios.create({ timeout: 1000 });
http.createServer((req, res) => res.end('OK')).listen(8080, '0.0.0.0');