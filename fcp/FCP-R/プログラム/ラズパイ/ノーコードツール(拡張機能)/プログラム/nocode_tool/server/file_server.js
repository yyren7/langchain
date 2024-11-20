const express = require('express');
const fs = require('fs');
const yaml = require('js-yaml');
const path = require('path');
const { spawn } = require('child_process');
const next = require('next');

const dev = process.env.NODE_ENV !== 'production';
const nextApp = next({ dev });
const handle = nextApp.getRequestHandler();

const httpPort = 3000;
const static_path = '../static/';
const templates_path = '../templates/';
const app_path = '/app/';

nextApp.prepare().then(() => {
  const app = express();

  // CORS設定
  app.use((req, res, next) => {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, PATCH, DELETE');
    res.setHeader('Access-Control-Allow-Headers', 'X-Requested-With,content-type');
    res.setHeader('Access-Control-Allow-Credentials', true);
    next();
  });

  app.get('/', (req, res) => {
    serveFile('./index.html', 'text/html', res);
  });

  app.get('/:action', (req, res) => {
    const action = req.params.action;
    let url = req.url;
    // URLパスに基づいて処理を分岐
    switch (action) {
      case 'teaching':
        serveFile(`${templates_path}/teaching.html`, 'text/html', res);
        break;
      case 'blockly':
        serveFile(`${templates_path}/blockly.html`, 'text/html', res);
        break;
      case 'side_menu':
        serveFile(`${templates_path}/side_menu.html`, 'text/html', res);
        break;
      case 'jsonData':
        serveJsonData(res);
        break;
      case 'savePython':
        savePython(req, res);
        break;
      default:
        res.status(404).send('Not Found');
    }
  });

  app.get('/js/:action', (req, res) => {
    const action = req.params.action;
    let url = req.url;
    // URLパスに基づいて処理を分岐
    switch (action) {
      case 'fetchData.js':
      case 'myblocks.js':
      case 'toolbox.js':
      case 'code.js':
      case 'tabSwitch.js':
        serveFile(`${static_path}${url}`, 'text/plain', res);
        break;
      default:
        res.status(404).send('Not Found');
    }
  });

  app.get('/blockly/:action', (req, res) => {
    const action = req.params.action;
    let url = req.url;
    // URLパスに基づいて処理を分岐
    switch (action) {
      case 'blockly_compressed.js':
      case 'blocks_compressed.js':
      case 'python_compressed.js':
      case 'en.js':
        serveFile(`${static_path}${url}`, 'text/plain', res);
        break;
      default:
        res.status(404).send('Not Found');
    }
  });

  app.get('/css/:action', (req, res) => {
    const action = req.params.action;
    let url = req.url;
    // URLパスに基づいて処理を分岐
    switch (action) {
      case 'code.css':
      case 'style.css':
        serveFile(`${static_path}${url}`, 'text/css', res);
        break;
      default:
        res.status(404).send('Not Found');
    }
  });

  app.get('/xml/:action', (req, res) => {
    // const action = req.params.action;
    let url = req.url;
    serveFile(`${static_path}${url}`, 'text/plain', res);
  });

  app.post('/:action', (req, res) => {
    const action = req.params.action;
    // URLパスに基づいて処理を分岐
    switch (action) {
      case 'writeTeaching':
        writeTeaching(req, res);
        break;
      case 'writeXML':
        const file_name = req.query.query1;
        writeXML(req, res, file_name);
        break;
      default:
        res.status(404).send('Not Found');
    }
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
        const filePath = path.join(parent_file_path + app_path, 'robot_sub.py');
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


  function writeTeaching(req, res) {
    let body = '';
    req.on('data', (chunk) => {
      body += chunk;
    });
    req.on('end', () => {
      try {
        // JSONデータをyaml形式に変換
        const bodyObject = JSON.parse(body);
        const yamlData = yaml.dump(bodyObject);

        // yamlファイルに書き込み
        fs.writeFileSync(`${static_path}config/teaching.yaml`, yamlData, 'utf8');

        res.writeHead(200, { 'Content-Type': 'text/plain' });
        res.end('Message published successfully');

      } catch (error) {
        serveError(res);
      }
    });
  };

  function writeXML(req, res, file_name) {
    let body = '';
    req.on('data', (chunk) => {
      body += chunk;
    });
    req.on('end', () => {
      try {
        console.log(body);

        // yamlファイルに書き込み
        fs.writeFileSync(`${static_path}xml/${file_name}.xml`, body, 'utf8');

        res.writeHead(200, { 'Content-Type': 'text/plain' });
        res.end('Message published successfully');

      } catch (error) {
        serveError(res);
      }
    });
  };

  // サーバーを起動
  app.listen(httpPort, () => {
    console.log(`Server is running on port ${httpPort}`);
  });
});

// const http = require('http');
// const fs = require('fs');
// const yaml = require('js-yaml');
// const path = require('path');
// const express = require('express');
// const app = express();
// const { spawn } = require('child_process');

// const httpPort = 3000;
// const static_path = '../static/';
// const templates_path = '../templates/';
// const app_path = '/app/';

// // CORS設定
// app.use((req, res, next) => {
//   res.setHeader('Access-Control-Allow-Origin', '*');
//   res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, PATCH, DELETE');
//   res.setHeader('Access-Control-Allow-Headers', 'X-Requested-With,content-type');
//   res.setHeader('Access-Control-Allow-Credentials', true);
//   next();
// });

// app.get('/', (req, res) => {
//   serveFile('./index.html', 'text/html', res);
// });

// app.get('/:action', (req, res) => {
//   const action = req.params.action;
//   let url = req.url;
//   // URLパスに基づいて処理を分岐
//   switch (action) {
//     case 'teaching':
//       serveFile(`${templates_path}/teaching.html`, 'text/html', res);
//       break;
//     case 'blockly':
//       serveFile(`${templates_path}/blockly.html`, 'text/html', res);
//       break;
//     case 'side_menu':
//       serveFile(`${templates_path}/side_menu.html`, 'text/html', res);
//       break;
//     case 'jsonData':
//       serveJsonData(res);
//       break;      
//     case 'savePython':
//       savePython(req, res);
//       break;
//     default:
//         res.status(404).send('Not Found');
//   }
// });

// app.get('/js/:action', (req, res) => {
//   const action = req.params.action;
//   let url = req.url;
//   // URLパスに基づいて処理を分岐
//   switch (action) {
//     case 'fetchData.js':
//     case 'myblocks.js':
//     case 'toolbox.js':
//     case 'code.js':
//     case 'tabSwitch.js':
//       serveFile(`${static_path}${url}`, 'text/plain', res);
//       break;
//     default:
//         res.status(404).send('Not Found');
//   }
// });

// app.get('/blockly/:action', (req, res) => {
//   const action = req.params.action;
//   let url = req.url;
//   // URLパスに基づいて処理を分岐
//   switch (action) {
//     case 'blockly_compressed.js':
//     case 'blocks_compressed.js':
//     case 'python_compressed.js':
//     case 'en.js':
//       serveFile(`${static_path}${url}`, 'text/plain', res);
//       break;
//     default:
//         res.status(404).send('Not Found');
//   }
// });

// app.get('/css/:action', (req, res) => {
//   const action = req.params.action;
//   let url = req.url;
//   // URLパスに基づいて処理を分岐
//   switch (action) {
//     case 'code.css':
//     case 'style.css':
//       serveFile(`${static_path}${url}`, 'text/css', res);
//       break;
//     default:
//         res.status(404).send('Not Found');
//   }
// });

// app.get('/xml/:action', (req, res) => {
//   // const action = req.params.action;
//   let url = req.url;
//   serveFile(`${static_path}${url}`, 'text/plain', res);
// });

// app.post('/:action', (req, res) => {
//   const action = req.params.action;
//   // URLパスに基づいて処理を分岐
//   switch (action) {
//       case 'writeTeaching':
//         writeTeaching(req, res);
//         break;
//       case 'writeXML':
//         const file_name = req.query.query1;
//         writeXML(req, res, file_name);
//         break;
//       default:
//         res.status(404).send('Not Found');
//   }
// });

// // ファイルを提供する関数
// function serveFile(filePath, contentType, res) {
//   fs.readFile(filePath, 'utf8', (error, data) => {
//     if (error) {
//       serveError(res);
//       return;
//     }
//     res.writeHead(200, { 'Content-Type': contentType + '; charset=UTF-8' });
//     res.write(data);
//     res.end();
//   });
// }

// // JSONデータを提供する関数
// function serveJsonData(res) {
//   try {
//     const jsonData = yaml.load(fs.readFileSync(`${static_path}config/teaching.yaml`, 'utf8'));
//     res.writeHead(200, { 'Content-Type': 'application/json' });
//     res.write(JSON.stringify(jsonData));
//     res.end();
//   } catch (error) {
//     serveError(res);
//   }
// }

// // エラーを処理する関数
// function serveError(res, error) {
//   res.writeHead(500, { 'Content-Type': 'text/plain' });
//   res.write('Internal Server Error');
//   res.end();
//   console.error('Internal Server Error:', error);
// }

// function savePython(req, res) {
//   let body = '';
//   req.on('data', (chunk) => {
//     body += chunk;
//   });
//   req.on('end', () => {
//     try {
//       // クライアントから受け取ったデータを解析してファイルに書き出す
//       const parent_file_path = path.resolve(__dirname, '..');
//       const filePath_dummy = path.join(__dirname, 'block_robot_dummy.py');
//       const filePath = path.join(parent_file_path+app_path, 'robot_sub.py');
//       fs.writeFile(filePath_dummy, body, (err) => {
//         if (err) {
//           console.error('Error writing Python script to file:', err);
//           res.writeHead(500, { 'Content-Type': 'text/plain' });
//           res.end('Error writing Python script to file');
//           return;
//         }

//         console.log('Python script saved to file:', filePath);

//         // Pythonスクリプトを実行
//         const pythonProcess = spawn('python', [filePath]);

//         // Pythonプログラムの起動を確認し、クライアントにレスポンスを送信
//         pythonProcess.on('spawn', () => {
//           res.writeHead(200, { 'Content-Type': 'text/plain' });
//           res.end('Python script execution started.');
//         });
//       });
//     } catch (error) {
//       console.error('Error executing Python script:', error);
//       res.writeHead(500, { 'Content-Type': 'text/plain' });
//       res.end('Error executing Python script');
//     }
//   });
// }


// function writeTeaching(req, res) {
//   let body = '';
//   req.on('data', (chunk) => {
//     body += chunk;
//   });
//   req.on('end', () => {
//       try {    
//         // JSONデータをyaml形式に変換
//         const bodyObject = JSON.parse(body);
//         const yamlData = yaml.dump(bodyObject);

//         // yamlファイルに書き込み
//         fs.writeFileSync(`${static_path}config/teaching.yaml`, yamlData, 'utf8');

//         res.writeHead(200, { 'Content-Type': 'text/plain' });
//         res.end('Message published successfully');

//       } 
//       catch (error) {
//         serveError(res);
//       }
//   });
// };
  
// function writeXML(req, res, file_name) {
//   let body = '';
//   req.on('data', (chunk) => {
//     body += chunk;
//   });
//   req.on('end', () => {
//       try {    
//         console.log(body);

//         // yamlファイルに書き込み
//         fs.writeFileSync(`${static_path}xml/${file_name}.xml`, body, 'utf8');

//         res.writeHead(200, { 'Content-Type': 'text/plain' });
//         res.end('Message published successfully');

//       } 
//       catch (error) {
//         serveError(res);
//       }
//   });
// };

// // app.post('/writeTeaching', (req, res) => {
// //   let body = '';
// //   req.on('data', (chunk) => {
// //     body += chunk;
// //   });
// //   req.on('end', () => {
// //       try {    
// //         // JSONデータをyaml形式に変換
// //         const bodyObject = JSON.parse(body);
// //         const yamlData = yaml.dump(bodyObject);

// //         // yamlファイルに書き込み
// //         fs.writeFileSync(`${static_path}config/teaching.yaml`, yamlData, 'utf8');

// //         res.writeHead(200, { 'Content-Type': 'text/plain' });
// //         res.end('Message published successfully');

// //       } 
// //       catch (error) {
// //         serveError(res);
// //       }
// //   });
// // });

// // app.post('/writeXML', (req, res) => {
// //   let body = '';
// //   req.on('data', (chunk) => {
// //     body += chunk;
// //   });
// //   req.on('end', () => {
// //       try {    
// //         console.log(body);

// //         // yamlファイルに書き込み
// //         fs.writeFileSync(`${static_path}config/blocks.xml`, body, 'utf8');

// //         res.writeHead(200, { 'Content-Type': 'text/plain' });
// //         res.end('Message published successfully');

// //       } 
// //       catch (error) {
// //         serveError(res);
// //       }
// //   });
// // });

// // サーバーを起動
// app.listen(httpPort, () => {
//   console.log(`Server is running on port ${httpPort}`);
// });
