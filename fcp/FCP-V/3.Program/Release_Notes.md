# Version管理の基本方針　Ver X.Y.Z.A

```
X：互換性がなくなるようなアップデートがない限りは変更しない
Y：共通機能にアップデートorバグ修正を加えた時にカウントアップ
Z：検査レシピの追加でカウントアップ
A：検査レシピのバグ修正 or 機能追加でカウントアップ
```

## Version 4.0.0.0 (2024/10/04) 杉野 
【共通】
- アドレス変数の動的割付(makeGlovalVar)が分かりにくいため、ローコード版VASTと同様の方式へ変更
- キャリブレーションシートのロードが遅い問題を解決
- Facileaの判定結果の数値に誤りがあったため、VAST TCP通信フォーマット通りになるように変更