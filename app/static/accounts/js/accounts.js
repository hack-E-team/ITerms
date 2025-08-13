// // script.js

// // フォームの要素を取得
// const loginForm = document.getElementById('loginForm');

// // フォームの送信イベントをリッスン
// loginForm.addEventListener('submit', function(event) {
//     event.preventDefault(); // ページの再読み込みを防止

//     // 入力値を取得
//     const email = document.getElementById('email').value;
//     const password = document.getElementById('password').value;

//     // ここにログイン認証ロジックを記述
//     console.log('ログイン情報:', { email, password });
    
//     // ログイン成功/失敗のメッセージを表示
//     const messageBox = document.createElement('div');
//     messageBox.className = 'fixed top-4 right-4 p-4 rounded-md shadow-lg text-white font-medium z-50';
    
//     if (email === 'test@example.com' && password === 'password') {
//         messageBox.style.backgroundColor = '#10b981'; // green-500
//         messageBox.textContent = 'ログインに成功しました！';
//     } else {
//         messageBox.style.backgroundColor = '#ef4444'; // red-500
//         messageBox.textContent = 'ログインに失敗しました。メールアドレスまたはパスワードが間違っています。';
//     }
    
//     document.body.appendChild(messageBox);
    
//     // 3秒後にメッセージを非表示
//     setTimeout(() => {
//         messageBox.remove();
//     }, 3000);
// });
