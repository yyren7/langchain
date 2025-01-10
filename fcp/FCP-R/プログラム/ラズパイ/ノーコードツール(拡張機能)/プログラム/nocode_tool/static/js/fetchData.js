function fetchData() {
    // サーバーからYAMLデータを取得
    return fetch('http://127.0.0.1:3000/jsonData')
    .then(response => {
        return response.json() // レスポンスをJSONに変換
    })
    .catch(error => console.error('Error fetching YAML data', error));
}