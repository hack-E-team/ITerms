// サンプル用語データ（タグ付き）
const terms = [
    { name: "API", tags: ["プログラミング"] },
    { name: "クラウド", tags: ["ネットワーク"] },
    { name: "アルゴリズム", tags: ["プログラミング"] },
    { name: "データベース", tags: ["データベース"] },
    { name: "ファイアウォール", tags: ["セキュリティ", "ネットワーク"] },
    { name: "SQL", tags: ["データベース", "プログラミング"] },
    { name: "VPN", tags: ["ネットワーク", "セキュリティ"] },
    { name: "HTML", tags: ["プログラミング"] },
    { name: "ルーター", tags: ["ネットワーク"] },
    { name: "暗号化", tags: ["セキュリティ"] }
];

// チェック状態を保持するセット
const checkedTerms = new Set();

// 用語リストを表示する関数
function renderTerms(tag) {
    const ul = document.getElementById('terms-list');
    ul.innerHTML = '';
    const filtered = tag === 'all'
        ? terms
        : terms.filter(term => term.tags.includes(tag));
    filtered.forEach(term => {
        const li = document.createElement('li');
        li.innerHTML = `
            <input type="checkbox" name="terms" value="${term.name}" id="term-${term.name}">
            <label for="term-${term.name}" style="font-size:16px;">${term.name}</label>
        `;
        ul.appendChild(li);

        // チェック状態を復元
        const checkbox = li.querySelector('input[type="checkbox"]');
        if (checkedTerms.has(term.name)) {
            checkbox.checked = true;
        }
        // チェックボックスの変更を監視
        checkbox.addEventListener('change', function() {
            if (this.checked) {
                checkedTerms.add(term.name);
            } else {
                checkedTerms.delete(term.name);
            }
        });
    });
}

// タグ選択時のイベント
document.getElementById('tag-select').addEventListener('change', function() {
    renderTerms(this.value);
});

// 初期表示
renderTerms('all');

// 作成完了ボタンの送信イベント（仮実装）
document.getElementById('terms-form').addEventListener('submit', function(e) {
    e.preventDefault();
    const title = document.getElementById('vocab-title').value;
    const checked = Array.from(checkedTerms);
    if (!title) {
        alert('用語帳タイトルを入力してください');
        return;
    }
    if (checked.length === 0) {
        alert('用語を1つ以上選択してください');
        return;
    }
    alert(`「${title}」で${checked.length}件の用語帳を作成します`);
    // ここでサーバー送信などの処理を追加
});