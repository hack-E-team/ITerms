let currentIndex = 0;

// DOM要素の取得
const flashcard = document.getElementById('flashcard');
const frontContent = document.getElementById('front');
const backContent = document.getElementById('back');
const prevBtn = document.getElementById('prev-btn');
const nextBtn = document.getElementById('next-btn');

// 現在のインデックスに基づいてカードの内容を更新する関数
function updateCard() {
    flashcard.classList.remove('is-flipped');

    const currentCard = cards[currentIndex];
    frontContent.textContent = currentCard.term;
    backContent.textContent = currentCard.desc;

    prevBtn.disabled = currentIndex === 0;
    nextBtn.disabled = currentIndex === cards.length - 1;
}

// カードをタップした時の処理
flashcard.addEventListener('click', () => {
    flashcard.classList.toggle('is-flipped');
});

// 前のボタンを押した時の処理
prevBtn.addEventListener('click', () => {
    if (currentIndex > 0) {
        currentIndex--;
        updateCard();
    }
});

// 次のボタンを押した時の処理
nextBtn.addEventListener('click', () => {
    if (currentIndex < cards.length - 1) {
        currentIndex++;
        updateCard();
    }
});

// ページ読み込み時に最初のカードを表示
updateCard();

window.getFlashIndex = () => currentIndex;
window.setFlashIndex = (i) => {
  const n = Math.max(0, Math.min(i, cards.length - 1));
  currentIndex = n;
  updateCard();
};