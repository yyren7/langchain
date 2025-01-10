const http = require('http');
const fs = require('fs');
const yaml = require('js-yaml');
const path = require('path');
const { spawn } = require('child_process');
// const WebSocket = require('ws');

const hostname = '127.0.0.1';
const httpPort = 3000;
// const wsPort = 8080;
const static_path = '../static/';
const templates_path = '../templates/';
const app_path = '/app/';

var server = http.createServer();
server.on('request', (req, res) => {
  let url = req.url;
  switch (url) {
    case '/':
      serveFile('./index.html', 'text/html', res);
      break;
    case '/teaching':
      serveFile(`${templates_path}/teaching.html`, 'text/html', res);
      break;
    case '/blockly':
      serveFile(`${templates_path}/blockly.html`, 'text/html', res);
      break;
    case '/js/fetchData.js':
    case '/js/myblocks.js':
    case '/js/toolbox.js':
    case '/js/code.js':
    case '/js/tabSwitch.js':
    case '/blockly/blockly_compressed.js':
    case '/blockly/blocks_compressed.js':
    case '/blockly/python_compressed.js':
    case '/blockly/msg/en.js':
      serveFile(`${static_path}${url}`, 'text/plain', res);
      break;

    case '/css/code.css':
    case '/css/style.css':
      serveFile(`${static_path}${url}`, 'text/css', res);
      break;
    case '/jsonData':
      serveJsonData(res);
      break;
    case '/savePython':
      savePython(req, res);
      break;
  }
});

server.listen(httpPort, hostname, () => {
  console.log(`Server running at http://${hostname}:${httpPort}/`);
});

// ファイルを提供する関数
function serveFile(filePath, contentType, res) {
  fs.readFile(filePath, 'utf8', (error, data) => {
    if (error) {
      serveError(res);
      return;
    }
    res.writeHead(200, { 'Content-Type': contentType + '; charset=UTF-8' });
    res.write(data);
    res.end();
  });
}

// JSONデータを提供する関数
function serveJsonData(res) {
  try {
    const jsonData = yaml.load(fs.readFileSync(`${static_path}config/teaching.yaml`, 'utf8'));
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.write(JSON.stringify(jsonData));
    res.end();
  } catch (error) {
    serveError(res);
  }
}

// エラーを処理する関数
function serveError(res, error) {
  res.writeHead(500, { 'Content-Type': 'text/plain' });
  res.write('Internal Server Error');
  res.end();
  console.error('Internal Server Error:', error);
}

function savePython(req, res) {
  let body = '';
  req.on('data', (chunk) => {
    body += chunk;
  });
  req.on('end', () => {
    try {
      // クライアントから受け取ったデータを解析してファイルに書き出す
      const parent_file_path = path.resolve(__dirname, '..');
      const filePath_dummy = path.join(__dirname, 'block_robot_dummy.py');
      const filePath = path.join(parent_file_path+app_path, 'robot_sub.py');
      fs.writeFile(filePath_dummy, body, (err) => {
        if (err) {
          console.error('Error writing Python script to file:', err);
          res.writeHead(500, { 'Content-Type': 'text/plain' });
          res.end('Error writing Python script to file');
          return;
        }

        console.log('Python script saved to file:', filePath);

        // Pythonスクリプトを実行
        const pythonProcess = spawn('python', [filePath]);

        // Pythonプログラムの起動を確認し、クライアントにレスポンスを送信
        pythonProcess.on('spawn', () => {
          res.writeHead(200, { 'Content-Type': 'text/plain' });
          res.end('Python script execution started.');
        });
      });
    } catch (error) {
      console.error('Error executing Python script:', error);
      res.writeHead(500, { 'Content-Type': 'text/plain' });
      res.end('Error executing Python script');
    }
  });
}