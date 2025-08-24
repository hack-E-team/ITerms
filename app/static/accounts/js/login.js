document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const loginButton = document.getElementById('loginButton');
    const showPasswordCheckbox = document.getElementById('show-password-checkbox');
    const errorMessageDiv = document.getElementById('errorMessage');

    // パスワードの表示/非表示を切り替える
    showPasswordCheckbox.addEventListener('change', function() {
        if (this.checked) {
            passwordInput.type = 'text';
        } else {
            passwordInput.type = 'password';
        }
    });

    // ログインフォームの送信イベントを処理する
    loginForm.addEventListener('submit', function(event) {
        // フォームのデフォルト送信をキャンセル
        event.preventDefault();

        // 簡易的な入力値チェック
        if (emailInput.value === '' || passwordInput.value === '') {
            errorMessageDiv.textContent = 'メールアドレスとパスワードを入力してください。';
            errorMessageDiv.style.display = 'block';
            return;
        }

        // ここに非同期通信（Ajax）を実装してサーバーに認証情報を送信
        // 以下のコードは認証成功/失敗をシミュレートする例です
        const mockAuthSuccessful = (emailInput.value === 'user@example.com' && passwordInput.value === 'password');

        if (mockAuthSuccessful) {
            // 認証成功時
            errorMessageDiv.style.display = 'none';
            alert('ログインに成功しました！');
            // 実際のアプリケーションでは、ページをリダイレクトする
            // window.location.href = '/dashboard';
        } else {
            // 認証失敗時
            errorMessageDiv.textContent = 'メールアドレスまたはパスワードが間違っています。';
            errorMessageDiv.style.display = 'block';
        }
    });
});