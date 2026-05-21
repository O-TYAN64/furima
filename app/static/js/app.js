// ========================
// app.js
// ========================

document.addEventListener("DOMContentLoaded", () => {

  // ========================
  // いいねボタン（Ajax）
  // ========================
  const likeBtn = document.querySelector(".like-btn");
  if (likeBtn) {
    likeBtn.addEventListener("click", async () => {
      const itemId = likeBtn.dataset.id;
      try {
        const res = await fetch(`/item/${itemId}/like`, {
          method: "POST",
          headers: { "X-Requested-With": "XMLHttpRequest" },
        });
        if (!res.ok) {
          // 未ログイン等
          return;
        }
        const data = await res.json();
        const icon  = likeBtn.querySelector(".like-icon");
        const count = likeBtn.querySelector(".like-count");

        count.textContent = data.count;

        if (data.liked) {
          likeBtn.classList.add("liked");
          icon.textContent = "♥";
          animatePop(likeBtn);
        } else {
          likeBtn.classList.remove("liked");
          icon.textContent = "♡";
        }
      } catch (e) {
        console.error(e);
      }
    });
  }

  // ========================
  // フラッシュメッセージ 自動フェード
  // ========================
  const flashes = document.querySelectorAll(".flash");
  flashes.forEach(f => {
    setTimeout(() => {
      f.style.transition = "opacity .5s";
      f.style.opacity = "0";
      setTimeout(() => f.remove(), 500);
    }, 4000);
  });

});

// ========================
// ポップアニメーション
// ========================
function animatePop(el) {
  el.style.transform = "scale(1.15)";
  setTimeout(() => { el.style.transform = ""; }, 200);
}
