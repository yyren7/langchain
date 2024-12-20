const express = require('express');
const app = express();
const mqtt = require('mqtt');

// MQTTブローカーの設定
const brokerAddress = 'mqtt://localhost'; // MQTTブローカーのアドレス
const controlTopic = 'control_robot';
const feedbackTopic = 'feedback_robot';

const httpPort = 3002;

// MQTTクライアントの作成
const client = mqtt.connect(brokerAddress);

// client というEventEmitterインスタンスに登録されたすべてのイベントリスナーを削除
client.removeAllListeners('message');

// MQTTブローカーに接続したときの処理
client.on('connect', () => {
    console.log('Connected to MQTT broker');

    // サブスクライブするトピックを指定してサブスクライブ
    client.subscribe(feedbackTopic, (err) => {
        if (err) {
            console.error('Error subscribing to topic:', err);
        } else {
            console.log('Subscribed to topic:', feedbackTopic);
        }
    });
});

// エラーが発生したときの処理
client.on('error', (err) => {
    console.error('Error:', err);
});

// CORS設定
app.use((req, res, next) => {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, PATCH, DELETE');
    res.setHeader('Access-Control-Allow-Headers', 'X-Requested-With,content-type');
    res.setHeader('Access-Control-Allow-Credentials', true);
    next();
});

// メッセージをMQTTブローカーにパブリッシュする関数
function publishMessage(topic, message, callback) {
    client.publish(topic, message, (err) => {
        if (err) {
            console.error('Error publishing message:', err);
            callback(err);
        } else {
            console.log('Message published successfully');
            callback(null);
        }
    });
}

app.get('/:action', (req, res) => {
    const action = req.params.action;

    // URLパスに基づいて処理を分岐
    switch (action) {
        case 'runRobot':
        case 'pauseRobot':
        case 'setServo':
        case 'selectJog':
        case 'selectInching':
        case 'runPlusX':
        case 'runPlusY':
            sendCmd(req, res, action);
            break;
        case 'getRobotStatus':
            sendReceiveCmd(req, res, action);
            break;
        default:
            res.status(404).send('Not Found');
    }
});

function sendCmd(req, res, cmd) {
    publishMessage(controlTopic, cmd, (err) => {
        if (err) {
            res.status(500).send('Error publishing message');
        } else {
            res.status(200).send(`${cmd} published was executed.`);
        }
    });
};

function sendReceiveCmd(req, res, cmd) {
    let timeoutId; // タイムアウト処理のIDを保持する変数を定義

    // コールバック関数を一度だけ登録
    client.once('message', (topic, message) => {
        if (topic === feedbackTopic) {
            const receivedMessage = message.toString();
            res.status(200).send(receivedMessage);
            clearTimeout(timeoutId); // タイムアウト処理を解除
        }
    });

    // リクエストを送信
    publishMessage(controlTopic, cmd, (err) => {
        if (err) {
            res.status(500).send('Error publishing message');
            client.removeAllListeners('message');
            clearTimeout(timeoutId); // エラーが発生した場合もタイムアウト処理を解除
        }
    });

    // タイムアウト処理
    timeoutId = setTimeout(() => {
        // コールバック関数を解除
        client.removeAllListeners('message');
        res.status(500).send('Timeout: No response received');
    }, 5000); // 5秒後にタイムアウト
};


app.listen(httpPort, () => {
    console.log(`Express server running on port ${httpPort}`);
});