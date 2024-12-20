fetch('http://localhost:3000')
  .then(response => response.text())
  .then(yamlData => {
    // YAMLデータをJavaScriptオブジェクトに変換
    const dataObject = jsyaml.load(yamlData);
    
    // JavaScriptオブジェクトを使用してHTMLを操作
    const dataListElement = document.getElementById('dataList');
    
    // オブジェクトの内容をリストとしてHTMLに追加
    for (const key in dataObject) {
      const listItem = document.createElement('li');
      listItem.textContent = `${key}: ${dataObject[key]}`;
      dataListElement.appendChild(listItem);
    }
  })
  .catch(error => console.error('Error fetching YAML data:', error));