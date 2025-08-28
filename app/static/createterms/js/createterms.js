// ページ読み込み時に既存のすべてのフォームにイベントリスナーを付与
document.querySelectorAll('.term-form').forEach(attachEventListenersToForm);

document.getElementById('add-form-btn').onclick = function() {
    const formList = document.getElementById('form-list');
    const lastForm = formList.querySelector('.term-form:last-child');
    const newForm = lastForm.cloneNode(true);

    // 新しいフォームの入力値をリセット
    newForm.querySelectorAll('input:not([type="checkbox"]), textarea').forEach(el => el.value = '');
    newForm.querySelectorAll('input:checked').forEach(el => el.checked = false);
    newForm.querySelector('.selected-tags').textContent = 'タグを選択...';

    // 既存のremoveボタンがあれば削除
    const oldRemoveBtn = newForm.querySelector('.remove-form-btn');
    if (oldRemoveBtn) oldRemoveBtn.remove();

    // 新しいremoveボタンを作成
    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.className = 'remove-form-btn';
    removeBtn.textContent = '×';
    removeBtn.style.alignSelf = 'flex-end';
    newForm.insertBefore(removeBtn, newForm.firstChild);

    formList.appendChild(newForm);

    // 新しいフォームにもイベントリスナーを付与
    attachEventListenersToForm(newForm);
};

// 追加：CSRFクッキー取得
function getCookie(name){
  const m = document.cookie.match(new RegExp('(?:^|; )'+name+'=([^;]*)'));
  return m ? decodeURIComponent(m[1]) : null;
}

document.getElementById('submit-btn').onclick = async function() {
  const btn = this;
  const createUrl = btn.dataset.createUrl;   // ← ここ！
  const listUrl   = btn.dataset.listUrl;     // ← ここ！
  const forms = document.querySelectorAll('.term-form');

  let hasEmptyField = false;
  const items = [];

  forms.forEach(form => {
    const term = (form.querySelector('input[name="term"]')?.value || '').trim();
    const description = (form.querySelector('textarea[name="description"]')?.value || '').trim();
    const tag_ids = Array.from(form.querySelectorAll('input[name="tag_ids"]:checked')).map(cb => Number(cb.value));
    if (!term || !description || tag_ids.length === 0) hasEmptyField = true;
    else items.push({ term, description, tag_ids });
  });

  if (hasEmptyField) { alert('全ての項目を入力してください！'); return; }

  try {
    btn.disabled = true; btn.textContent = '登録中...';

    const res = await fetch(createUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken') || '',
        'X-Requested-With': 'XMLHttpRequest'
      },
      credentials: 'include',
      body: JSON.stringify(items)
    });

    const data = await res.json().catch(() => ({}));
    console.debug('create_post response', res.status, data);

    if (res.ok) {
      const ok = data.created?.length || 0;
      const ng = data.errors?.length || 0;
      if (ng === 0) {
        alert(`${ok}件 登録しました。`);
        location.href = listUrl;
      } else {
        alert(`一部失敗: 成功 ${ok} / 失敗 ${ng}`);
        console.warn('errors:', data.errors);
      }
    } else {
      // ステータス別ヒント
      if (res.status === 415) {
        alert('登録に失敗: Content-Type が JSON になっていません。');
      } else if (res.status === 403) {
        alert('登録に失敗: CSRF が通っていません。');
      } else {
        alert(`登録に失敗しました (HTTP ${res.status})`);
      }
      console.error('response:', res, data);
    }
  } catch (e) {
    alert('通信エラーが発生しました。');
    console.error(e);
  } finally {
    btn.disabled = false; btn.textContent = '登録完了';
  }
};

/**
 * 指定されたフォームにイベントリスナーを付与する関数
 * @param {HTMLElement} form - イベントリスナーを付与するフォーム要素
 */
function attachEventListenersToForm(form) {
    const selectContainer = form.querySelector('.custom-select-container');
    const selectedTagsDisplay = form.querySelector('.selected-tags');
    const dropdownMenu = form.querySelector('.dropdown-menu');
    const checkboxes = dropdownMenu.querySelectorAll('input[type="checkbox"]');

    // selected-tagsをクリックしたときに、dropdown-menuの表示・非表示を切り替える
    selectedTagsDisplay.addEventListener('click', () => {
        dropdownMenu.classList.toggle('show');
        adjustDropdownPosition(dropdownMenu);
    });

    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', () => {
            const selected = Array.from(checkboxes)
                .filter(cb => cb.checked)
                .map(cb => cb.value);
            selectedTagsDisplay.textContent = selected.length > 0 ? selected.join(', ') : 'タグを選択...';
        });
    });

    // プルダウンメニューの外側をクリックしたら閉じる
    document.addEventListener('click', (e) => {
        if (!selectContainer.contains(e.target)) {
            dropdownMenu.classList.remove('show');
        }
    });

    // フォーム削除ボタンのイベント付与
    attachRemoveBtnListener(form);
}

/**
 * ドロップダウンメニューが画面下部で見切れないように位置を調整する関数
 * @param {HTMLElement} dropdown - 調整するドロップダウンメニュー要素
 */
function adjustDropdownPosition(dropdown) {
    const rect = dropdown.getBoundingClientRect();
    const windowHeight = window.innerHeight || document.documentElement.clientHeight;
    const isOverflowing = rect.bottom > windowHeight;

    if (isOverflowing) {
        dropdown.style.top = 'auto';
        dropdown.style.bottom = '100%';
    } else {
        dropdown.style.top = '100%';
        dropdown.style.bottom = 'auto';
    }
}

/**
 * フォーム削除ボタンのイベントリスナーを付与
 * @param {HTMLElement} form - 対象フォーム
 */
function attachRemoveBtnListener(form) {
    const removeBtn = form.querySelector('.remove-form-btn');
    if (removeBtn) {
        removeBtn.onclick = function() {
            if (document.querySelectorAll('.term-form').length > 1) {
                form.remove();
            } else {
                alert('最低1つのフォームは必要です');
            }
        };
    }
}