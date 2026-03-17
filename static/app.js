const button = document.getElementById("send");
const result = document.getElementById("result");

button.addEventListener("click", async () => {
  const color = document.getElementById("color").value.trim();
  if (!color) {
    result.textContent = "값을 입력해 주세요.";
    return;
  }

  const payload = {
    color,
    time: new Date().toISOString(),
  };

  const res = await fetch("/save", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const body = await res.text();
    result.textContent = `저장 실패: ${res.status} ${body}`;
    return;
  }

  const data = await res.json();
  result.textContent = `저장 완료: id=${data.id}, color=${data.color}, time=${data.time}`;
  document.getElementById("color").value = "";
});
