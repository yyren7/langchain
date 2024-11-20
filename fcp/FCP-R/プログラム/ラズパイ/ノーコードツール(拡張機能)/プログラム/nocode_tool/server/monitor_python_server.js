const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const express = require('express');
const app = express();

const httpPort = 3001;
const app_path = '/app/';

// CORS設定
app.use((req, res, next) => {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, PATCH, DELETE');
    res.setHeader('Access-Control-Allow-Headers', 'X-Requested-With,content-type');
    res.setHeader('Access-Control-Allow-Credentials', true);
    next();
});

let pythonProcess;

app.post('/:action', (req, res) => {
    const action = req.params.action;

    // URLパスに基づいて処理を分岐
    switch (action) {
        case 'startPython':
            const prog_name = req.query.prog_name; // クエリ文字列からテキストを取得
            startPython(req, res, prog_name);
            break;
        default:
            res.status(404).send('Not Found');
    }
});

app.get('/:action', (req, res) => {
    const action = req.params.action;

    // URLパスに基づいて処理を分岐
    switch (action) {
        case 'stopPython':
            stopPython(req, res);
            break;
        default:
            res.status(404).send('Not Found');
    }
});

function startPython(req, res, prog_name) {
    if(prog_name === 'auto'){
        let body = '';
        req.on('data', (chunk) => {
          body += chunk;
        });
        req.on('end', () => {
            try {
                // クライアントから受け取ったデータを解析してファイルに書き出す
                const parent_file_path = path.resolve(__dirname, '..');
                const filePath = path.join(parent_file_path+app_path, 'auto.py');
                fs.writeFile(filePath, body, (err) => {
                    if (err) {
                        console.error('Error writing Python script to file:', err);
                        res.status(200).send('Error writing Python script to file');
                        return;
                    }
    
                    console.log('Python script saved to file:', filePath);
    
                    // 既存のPythonプロセスが実行中であれば終了する
                    if (pythonProcess) {
                        pythonProcess.kill();
                        console.log('Terminated existing Python process.');
                    }
    
                    // Pythonスクリプトを実行
                    pythonProcess = spawn('python', [filePath]);
                    console.log('start Python process.');
                    res.status(200).send('Message subscribed successfully');
    
                    // Pythonプログラムの起動を確認し、クライアントにレスポンスを送信
                    pythonProcess.stdout.on('data', (data) => {
                        console.log(`stdout: ${data}`);
                    });
    
                    pythonProcess.stderr.on('data', (data) => {
                        console.error(`stderr: ${data}`);
                    });
    
                });
            } catch (error) {
                console.error('Error executing Python script:', error);
                res.status(200).send('Error executing Python script');
            }
        });
    }
    else if(prog_name === 'manual'){
        try {
            // クライアントから受け取ったデータを解析してファイルに書き出す
            const parent_file_path = path.resolve(__dirname, '..');
            // const filePath_dummy = path.join(__dirname, 'auto.py');
            const filePath = path.join(parent_file_path+app_path, 'manual.py');

            // 既存のPythonプロセスが実行中であれば終了する
            if (pythonProcess) {
                pythonProcess.kill();
                console.log('Terminated existing Python process.');
            }

            // Pythonスクリプトを実行
            pythonProcess = spawn('python', [filePath]);
            console.log('start Python process.');
            res.status(200).send('Message subscribed successfully');

            // Pythonプログラムの起動を確認し、クライアントにレスポンスを送信
            pythonProcess.stdout.on('data', (data) => {
                console.log(`stdout: ${data}`);
            });

            pythonProcess.stderr.on('data', (data) => {
                console.error(`stderr: ${data}`);
            });

        } catch (error) {
            console.error('Error executing Python script:', error);
            res.status(200).send('Error executing Python script');
        }

    }
}

function stopPython(req, res) {
    try {
        // Pythonプロセスが存在するかどうかを確認し、存在する場合は終了させる
        if (pythonProcess) {
            pythonProcess.kill();
            pythonProcess = null; // Pythonプロセス変数をクリア
            console.log('Python process has been terminated.');
            res.status(200).send('Python process has been terminated.');
        } else {
            console.log('Python process is not running.');
            res.status(200).send('Python process is not running.');
        }
    } catch (error) {
        console.error('Error stopping Python process:', error);
        res.status(500).send('Error stopping Python process');
    }
}
  
app.listen(httpPort, () => {
    console.log(`Express server running on port ${httpPort}`);
});