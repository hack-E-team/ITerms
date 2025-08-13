# 開発環境設定

## 手順

1. git clone して、ブランチを切り替える
2. 仮想環境を作成する
3. 依存ファイルを読み込む
4. 環境変数ファイルを作成する
5. Dockerを起動する
6. 開発スタート

## githubの操作

``` bash
# 1. リポジトリをcloneする
git clone https://github.com/your-username/your-repo.git
cd your-repo

# 2. devブランチを取得して作業用ブランチにチェックアウト
git fetch origin dev
git checkout -b feature/some-task origin/dev # 例

# 3. コードを編集する

# 4. 変更をステージング＆コミット
git add ～
git commit -m "説明"

# 5. リモートにプッシュ（初回は `-u` をつける）
git push -u origin feature/some-task
```

## 仮想環境の作成・起動

``` bash
# ルートディレクトリで作成
python3 -m venv venv
# 起動
source venv/bin/activate
# windowsの場合は .\venv\Scripts\activate

# 停止
deactivate
```

一応、仮想環境の名前はvenvにしておいてください。そうしないとgithubに上がってしまう可能性があります。

## 依存ファイルの読み込み

仮想環境に必要なパッケージをインストールします。

``` bash
pip install -r requirements.txt
```

## 環境変数ファイルの作成

ルートディレクトリに.env.devファイルを作成し、.env.exampleの中身をコピペしてください。（本番環境は.env.prod）
以下のコマンドで自動で作成されます。
作成したら、your～となっている変数を自分で分かりやすいものに書き換えてください。
中身は空でいいので.env.prodファイルも作っておいてください。

``` bash
cp .env.example .env.dev
touch .env.prod
```

## Dockerの起動

``` bash
docker compose up
```

必要に応じて以下のオプションを追加

``` bash
--build # ビルドもする場合
-d # バックグラウンド実行
```

[開発環境のアドレス](http://localhost:8000)

## Docker内の操作

いろいろやり方があるので一例ですが、

``` bash
docker compose exec [コンテナのサービス名] [コマンド]

# 例
docker compose exec django python manage.py startapp accounts
```

``` bash
# Dockerの中に入る場合
docker compose exec db bash
```

- VSCodeの拡張機能「Dev Containers」を使う

## （本番のみ）本番環境の起動

``` bash
docker compose -f docker-compose.yml --profile production up
```

- docker-compose.ymlを指定して、本番環境のコンテナを起動。
- nginx コンテナは profiles: ["production"] に設定しているため、開発環境では起動せず、本番環境でのみ起動するようにしています。
- 本番環境では --profile production を指定して起動します。
- 開発環境では docker compose up のみで nginx を除いたサービスが起動します。
