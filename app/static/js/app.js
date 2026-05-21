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
        if (!res.ok) return;
        const data  = await res.json();
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
  document.querySelectorAll(".flash").forEach(f => {
    setTimeout(() => {
      f.style.transition = "opacity .5s";
      f.style.opacity    = "0";
      setTimeout(() => f.remove(), 500);
    }, 4000);
  });

  // ========================
  // チェックアウト ラジオ選択ハイライト
  // ========================
  document.querySelectorAll('input[type="radio"]').forEach(radio => {
    radio.addEventListener("change", () => {
      const name = radio.name;
      document.querySelectorAll(`input[name="${name}"]`).forEach(r => {
        r.closest(".addr-card, .pay-card")
         ?.classList.toggle("selected", r.checked);
      });
    });
  });

});

// ========================
// ポップアニメーション
// ========================
function animatePop(el) {
  el.style.transform = "scale(1.15)";
  setTimeout(() => { el.style.transform = ""; }, 200);
}
