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

document.getElementById('submit-btn').onclick = function() {
    const forms = document.querySelectorAll('.term-form');
    let hasEmptyField = false;

    forms.forEach(form => {
        const termInput = form.querySelector('input:not([type="checkbox"])[name="term"]');
        const descriptionInput = form.querySelector('textarea');
        const tagCheckboxes = form.querySelectorAll('input[name="tag"]:checked');

        if (!termInput || termInput.value.trim() === '' || !descriptionInput || descriptionInput.value.trim() === '' || tagCheckboxes.length === 0) {
            hasEmptyField = true;
        }
    });

    if (hasEmptyField) {
        alert('全ての項目を入力してください！');
    } else {
        alert('登録が完了しました！');
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