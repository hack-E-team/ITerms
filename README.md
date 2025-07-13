# 開発環境設定

## githubの操作

``` bash
# 1. リポジトリをcloneする（mainブランチがデフォルト）
git clone https://github.com/your-username/your-repo.git
cd your-repo

# 2. devブランチを取得して作業用ブランチにチェックアウト
git fetch origin dev
git checkout -b feature/some-task origin/dev

# 3. コードを編集する

# 4. 変更をステージング＆コミット
git add ～
git commit -m "説明"

# 5. リモートにプッシュ（初回なので `-u` をつける）
git push -u origin feature/some-task
```

## 環境変数ファイルの作成

ルートディレクトリに.env.devファイルを作成し、.env.exampleの中身をコピペしてください。（本番環境は.env.prod）
以下のコマンドで自動で作成されます。
作成したら、your～となっている変数を自分で分かりやすいものに書き換えてください。

``` bash
cp .env.example .env.dev
```

## 開発環境の起動

``` bash
docker compose up
```

必要に応じて以下のオプションを追加

``` bash
--build # ビルドもする場合
-d # バックグラウンド実行
```

[開発環境のアドレス](http://localhost:8000)

## 本番環境の起動

``` bash
docker compose -f docker-compose.yml --profile production up
```

- docker-compose.ymlを指定して、本番環境のコンテナを起動。
- nginx コンテナは profiles: ["production"] に設定しているため、開発環境では起動せず、本番環境でのみ起動するようにしています。
- 本番環境では --profile production を指定して起動します。
- 開発環境では docker compose up のみで nginx を除いたサービスが起動します。
