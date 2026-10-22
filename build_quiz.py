# -*- coding: utf-8 -*-
"""Đọc đề cương và tạo web quiz một file HTML."""
import json
import re
from pathlib import Path

SRC = Path(r"c:\test\tao_de_cuong_sinh.py")
OUT = Path(r"c:\test\quiz_sinh\index.html")
DESKTOP = Path(r"C:\Users\Admin\Desktop\Quiz_Sinh_hoc.html")


def parse_questions(text: str):
    start = text.find('h(doc, "BÀI 1')
    end = text.find("doc.save")
    body = text[start:end]
    section = ""
    part = ""
    items = []
    current = None

    def flush():
        nonlocal current
        if current:
            items.append(current)
            current = None

    for raw in body.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r'h\(doc,\s*"(.*)"\s*,', line)
        if m:
            flush()
            section = m.group(1)
            part = ""
            continue
        m = re.match(r'add\(doc,\s*"(.*)"', line)
        if m:
            content = m.group(1)
            if content.startswith("PHẦN"):
                part = content
            elif current is not None:
                if not current["choices"] and not current["answers"]:
                    current["stem"].append(content)
                else:
                    current["explain"].append(content)
            continue
        m = re.match(r'q\(doc,\s*"(.*)"\s*\)', line)
        if m:
            flush()
            current = {
                "section": section,
                "part": part,
                "prompt": m.group(1),
                "stem": [],
                "choices": [],
                "answers": [],
                "explain": [],
            }
            continue
        m = re.match(r'choice\(doc,\s*"([A-D])",\s*"(.*)"(?:,\s*(True|False))?\)', line)
        if m and current is not None:
            current["choices"].append(
                {"label": m.group(1), "text": m.group(2), "correct": m.group(3) == "True"}
            )
            continue
        m = re.match(r'ans\(doc,\s*"(.*)"\s*\)', line)
        if m and current is not None:
            current["answers"].append(m.group(1))
            continue
    flush()
    return items


def to_quiz(items):
    quiz = []
    n = 0
    for item in items:
        stem = item["prompt"]
        if item["stem"]:
            stem += "\n" + "\n".join(item["stem"])
        explain = " ".join(item["explain"]).strip()
        if item["choices"]:
            n += 1
            correct = next((c["label"] for c in item["choices"] if c["correct"]), "")
            quiz.append({
                "id": n,
                "type": "mcq",
                "section": item["section"],
                "part": item["part"],
                "prompt": stem,
                "choices": [{"label": c["label"], "text": c["text"]} for c in item["choices"]],
                "answer": correct,
                "explain": explain,
            })
            continue
        tf = []
        shorts = []
        for ans in item["answers"]:
            m = re.match(r"^(.*?)\s+[—–-]\s*(Đúng|Sai)\b(.*)$", ans)
            if m:
                tf.append({
                    "statement": m.group(1).strip(),
                    "answer": "Đ" if m.group(2) == "Đúng" else "S",
                    "note": m.group(3).strip(" .()"),
                })
            else:
                shorts.append(ans)
        if tf:
            for row in tf:
                n += 1
                quiz.append({
                    "id": n,
                    "type": "tf",
                    "section": item["section"],
                    "part": item["part"],
                    "prompt": item["prompt"],
                    "statement": row["statement"],
                    "answer": row["answer"],
                    "explain": row["note"] or explain,
                })
        if shorts:
            n += 1
            quiz.append({
                "id": n,
                "type": "short",
                "section": item["section"],
                "part": item["part"],
                "prompt": stem,
                "answer": " ".join(shorts),
                "explain": explain,
            })
    return quiz


HTML = r"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Quiz Sinh học 11 — Giữa kì I</title>
<style>
  :root {
    --ink: #1b2420;
    --muted: #5d6b64;
    --paper: #f4f1e8;
    --card: #fffdf8;
    --line: #e3dccb;
    --green: #1f6b45;
    --green-2: #e7f5ec;
    --yellow: #ffe56a;
    --red: #b42318;
    --red-bg: #fdecea;
    --shadow: 0 10px 30px rgba(40, 50, 40, .08);
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    font-family: "Segoe UI", "Be Vietnam Pro", sans-serif;
    color: var(--ink);
    background:
      radial-gradient(900px 400px at 100% -10%, #d9efe2 0%, transparent 55%),
      var(--paper);
    min-height: 100vh;
  }
  header {
    position: sticky; top: 0; z-index: 5;
    background: rgba(244, 241, 232, .92);
    backdrop-filter: blur(8px);
    border-bottom: 1px solid var(--line);
  }
  .wrap { width: min(920px, calc(100% - 28px)); margin: 0 auto; }
  .top { display: flex; justify-content: space-between; gap: 12px; align-items: center; padding: 14px 0; }
  h1 { font-size: 18px; margin: 0; letter-spacing: -.02em; }
  h1 span { color: var(--green); }
  .sub { color: var(--muted); font-size: 13px; margin-top: 2px; }
  button, .chip {
    font: inherit; cursor: pointer; border: 1px solid var(--line);
    background: white; color: var(--ink); border-radius: 999px; padding: 8px 14px;
  }
  button.primary { background: var(--green); color: white; border-color: var(--green); }
  button:disabled { opacity: .45; cursor: not-allowed; }
  main { padding: 22px 0 64px; }
  .hero, .card {
    background: var(--card); border: 1px solid var(--line); border-radius: 18px;
    box-shadow: var(--shadow); padding: 22px;
  }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; margin-top: 16px; }
  .pick {
    text-align: left; border-radius: 16px; padding: 16px; background: white;
  }
  .pick b { display: block; margin-bottom: 4px; }
  .pick small { color: var(--muted); }
  .filters { display: flex; flex-wrap: wrap; gap: 8px; margin: 8px 0 14px; }
  .chip.active { background: var(--green); color: white; border-color: var(--green); }
  .progress { height: 8px; background: #ece7da; border-radius: 99px; overflow: hidden; margin: 8px 0 14px; }
  .progress > div { height: 100%; background: var(--green); width: 0; }
  .meta { color: var(--muted); font-size: 13px; display: flex; justify-content: space-between; gap: 8px; }
  .prompt { font-size: 18px; line-height: 1.45; margin: 8px 0 6px; white-space: pre-wrap; }
  .statement { background: #f7f4ea; border-radius: 12px; padding: 12px 14px; margin: 10px 0 14px; }
  .options { display: grid; gap: 10px; margin-top: 14px; }
  .opt, .tfbtn {
    text-align: left; border-radius: 14px; padding: 12px 14px; background: white; width: 100%;
  }
  .opt.selected { border-color: var(--green); background: var(--green-2); }
  .opt.good, .tfbtn.good { background: var(--yellow); border-color: #e2c84a; }
  .opt.bad, .tfbtn.bad { background: var(--red-bg); border-color: #f0b4ae; color: var(--red); }
  .explain { margin-top: 12px; padding: 12px 14px; border-radius: 12px; background: #fff8d6; }
  .nav { display: flex; justify-content: space-between; gap: 10px; margin-top: 16px; }
  .map { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 18px; max-height: 180px; overflow: auto; padding: 4px; }
  .dot {
    width: 34px; height: 34px; border-radius: 10px; padding: 0;
    font-size: 12px;
  }
  .dot.now { outline: 2px solid var(--green); }
  .dot.ok { background: var(--green-2); }
  .dot.no { background: var(--red-bg); }
  .score { font-size: 42px; font-weight: 700; color: var(--green); margin: 0; }
  .miss { border-top: 1px solid var(--line); padding-top: 10px; margin-top: 10px; }
  .hide { display: none; }
</style>
</head>
<body>
<header>
  <div class="wrap top">
    <div>
      <h1>Quiz <span>Sinh học 11</span></h1>
      <div class="sub">Ôn tập giữa kì I · toàn bộ câu trong đề cương</div>
    </div>
    <button id="homeBtn" class="hide" type="button">Về trang chủ</button>
  </div>
</header>
<main class="wrap">
  <section id="home" class="hero">
    <h2 style="margin:0 0 6px">Chọn phần muốn làm</h2>
    <p style="color:var(--muted);margin:0">Trắc nghiệm và đúng/sai được chấm tự động. Câu trả lời ngắn hiện đáp án để bạn tự đối chiếu.</p>
    <div class="grid" id="picks"></div>
  </section>
  <section id="quiz" class="hide">
    <div class="filters" id="filters"></div>
    <div class="card">
      <div class="meta"><span id="pos"></span><span id="live"></span></div>
      <div class="progress"><div id="bar"></div></div>
      <div class="meta" id="tag"></div>
      <div class="prompt" id="prompt"></div>
      <div id="statement" class="statement hide"></div>
      <div id="options" class="options"></div>
      <div id="explain" class="explain hide"></div>
      <div class="nav">
        <button id="prev" type="button">Câu trước</button>
        <button id="check" class="primary" type="button">Kiểm tra</button>
        <button id="next" type="button">Câu sau</button>
      </div>
    </div>
    <div class="map" id="map"></div>
    <p style="text-align:center;margin-top:18px"><button id="finish" class="primary" type="button">Nộp bài và xem điểm</button></p>
  </section>
  <section id="result" class="hide card">
    <p class="score" id="score"></p>
    <p id="scoreText"></p>
    <div id="byBai"></div>
    <h3>Những câu chưa đúng</h3>
    <div id="misses"></div>
    <div class="nav">
      <button id="review" type="button">Xem lại bài</button>
      <button id="again" class="primary" type="button">Làm lại</button>
    </div>
  </section>
</main>
<script>
const DATA = __DATA__;
const state = { pool: DATA, index: 0, picks: {}, revealed: {}, filter: "Tất cả" };

const home = document.getElementById("home");
const quiz = document.getElementById("quiz");
const result = document.getElementById("result");
const homeBtn = document.getElementById("homeBtn");

function baiName(section) {
  return (section || "").split(".")[0];
}
function sections() {
  const seen = [];
  DATA.forEach(q => { if (!seen.includes(q.section)) seen.push(q.section); });
  return seen;
}
function filtered() {
  if (state.filter === "Tất cả") return DATA;
  return DATA.filter(q => q.section === state.filter);
}
function renderHome() {
  const box = document.getElementById("picks");
  const all = [{ name: "Làm tất cả", section: "Tất cả", count: DATA.length }];
  sections().forEach(s => all.push({ name: s, section: s, count: DATA.filter(q => q.section === s).length }));
  box.innerHTML = all.map(x => `<button class="pick" data-section="${x.section.replaceAll('"', "&quot;")}"><b>${x.name}</b><small>${x.count} câu</small></button>`).join("");
  box.querySelectorAll("button").forEach(btn => btn.onclick = () => start(btn.dataset.section));
}
function start(section) {
  state.filter = section;
  state.pool = filtered();
  state.index = 0;
  state.picks = {};
  state.revealed = {};
  home.classList.add("hide");
  result.classList.add("hide");
  quiz.classList.remove("hide");
  homeBtn.classList.remove("hide");
  renderFilters();
  render();
}
function renderFilters() {
  const names = ["Tất cả", ...sections()];
  document.getElementById("filters").innerHTML = names.map(n => {
    const label = n === "Tất cả" ? "Tất cả" : baiName(n);
    return `<button class="chip ${n === state.filter ? "active" : ""}" data-f="${n.replaceAll('"', "&quot;")}">${label}</button>`;
  }).join("");
  document.querySelectorAll("#filters .chip").forEach(chip => chip.onclick = () => {
    state.filter = chip.dataset.f;
    state.pool = filtered();
    state.index = 0;
    renderFilters();
    render();
  });
}
function keyOf(q) { return String(q.id); }
function render() {
  const list = state.pool;
  if (!list.length) return;
  if (state.index >= list.length) state.index = list.length - 1;
  const q = list[state.index];
  const k = keyOf(q);
  document.getElementById("pos").textContent = `Câu ${state.index + 1} / ${list.length}`;
  document.getElementById("bar").style.width = `${((state.index + 1) / list.length) * 100}%`;
  document.getElementById("tag").textContent = `${baiName(q.section)} · ${q.part || ""}`;
  document.getElementById("prompt").textContent = q.prompt;
  const st = document.getElementById("statement");
  const box = document.getElementById("options");
  const exp = document.getElementById("explain");
  const revealed = !!state.revealed[k];
  st.classList.add("hide");
  exp.classList.add("hide");
  box.innerHTML = "";
  if (q.type === "tf") {
    st.classList.remove("hide");
    st.textContent = q.statement;
    ["Đ", "S"].forEach(label => {
      const b = document.createElement("button");
      b.className = "tfbtn";
      b.textContent = label === "Đ" ? "Đúng" : "Sai";
      if (state.picks[k] === label) b.classList.add("selected");
      if (revealed && label === q.answer) b.classList.add("good");
      if (revealed && state.picks[k] === label && label !== q.answer) b.classList.add("bad");
      b.onclick = () => { if (!revealed) { state.picks[k] = label; render(); } };
      box.appendChild(b);
    });
  } else if (q.type === "mcq") {
    q.choices.forEach(c => {
      const b = document.createElement("button");
      b.className = "opt";
      b.textContent = `${c.label}. ${c.text}`;
      if (state.picks[k] === c.label) b.classList.add("selected");
      if (revealed && c.label === q.answer) b.classList.add("good");
      if (revealed && state.picks[k] === c.label && c.label !== q.answer) b.classList.add("bad");
      b.onclick = () => { if (!revealed) { state.picks[k] = c.label; render(); } };
      box.appendChild(b);
    });
  } else {
    const b = document.createElement("button");
    b.className = "primary";
    b.textContent = revealed ? "Đã hiện đáp án" : "Hiện đáp án";
    b.disabled = revealed;
    b.onclick = () => { state.revealed[k] = true; state.picks[k] = "seen"; render(); };
    box.appendChild(b);
  }
  if (revealed) {
    exp.classList.remove("hide");
    const ans = q.type === "tf" ? (q.answer === "Đ" ? "Đúng" : "Sai") : (q.type === "mcq" ? q.answer : q.answer);
    exp.innerHTML = `<b>Đáp án:</b> ${ans}${q.explain ? `<br>${q.explain}` : ""}`;
  }
  const graded = list.filter(item => item.type !== "short");
  const done = graded.filter(item => state.revealed[keyOf(item)]).length;
  const right = graded.filter(item => state.revealed[keyOf(item)] && state.picks[keyOf(item)] === item.answer).length;
  document.getElementById("live").textContent = done ? `Đúng ${right}/${done} câu đã chấm` : "";
  document.getElementById("prev").disabled = state.index === 0;
  document.getElementById("next").disabled = state.index === list.length - 1;
  document.getElementById("check").textContent = q.type === "short" ? "Hiện đáp án" : "Kiểm tra";
  document.getElementById("check").disabled = revealed || (q.type !== "short" && !state.picks[k]);
  const map = document.getElementById("map");
  map.innerHTML = "";
  list.forEach((item, i) => {
    const d = document.createElement("button");
    d.className = "dot";
    d.textContent = i + 1;
    if (i === state.index) d.classList.add("now");
    const kk = keyOf(item);
    if (state.revealed[kk]) {
      if (item.type === "short" || state.picks[kk] === item.answer) d.classList.add("ok");
      else d.classList.add("no");
    }
    d.onclick = () => { state.index = i; render(); };
    map.appendChild(d);
  });
}
document.getElementById("prev").onclick = () => { if (state.index > 0) { state.index--; render(); } };
document.getElementById("next").onclick = () => { if (state.index < state.pool.length - 1) { state.index++; render(); } };
document.getElementById("check").onclick = () => {
  const q = state.pool[state.index];
  state.revealed[keyOf(q)] = true;
  if (q.type === "short") state.picks[keyOf(q)] = "seen";
  render();
};
function scoreOf(list) {
  const graded = list.filter(q => q.type !== "short");
  const right = graded.filter(q => state.picks[keyOf(q)] === q.answer).length;
  return { right, total: graded.length };
}
document.getElementById("finish").onclick = () => {
  const list = state.pool;
  list.forEach(q => {
    if (q.type !== "short" && state.picks[keyOf(q)]) state.revealed[keyOf(q)] = true;
  });
  const s = scoreOf(list);
  const answered = list.filter(q => q.type !== "short" && state.picks[keyOf(q)]);
  const wrong = answered.filter(q => state.picks[keyOf(q)] !== q.answer);
  const skipped = list.filter(q => q.type !== "short" && !state.picks[keyOf(q)]).length;
  quiz.classList.add("hide");
  result.classList.remove("hide");
  const pct = s.total ? Math.round(s.right / s.total * 100) : 0;
  document.getElementById("score").textContent = `${s.right}/${s.total}`;
  document.getElementById("scoreText").textContent = `Đúng ${s.right} câu, sai ${wrong.length} câu, chưa làm ${skipped} câu. Tỷ lệ trên toàn bộ câu chấm được là ${pct}%. Câu trả lời ngắn không tính điểm.`;
  const baiBox = document.getElementById("byBai");
  baiBox.innerHTML = sections().filter(sec => list.some(q => q.section === sec)).map(sec => {
    const part = scoreOf(list.filter(q => q.section === sec));
    return `<p><b>${baiName(sec)}:</b> ${part.right}/${part.total}</p>`;
  }).join("");
  const misses = wrong;
  document.getElementById("misses").innerHTML = misses.length ? misses.map(q => {
    const yours = state.picks[keyOf(q)] || "bỏ trống";
    const ans = q.type === "tf" ? (q.answer === "Đ" ? "Đúng" : "Sai") : q.answer;
    const extra = q.statement ? `<br><i>${q.statement}</i>` : "";
    return `<div class="miss"><b>${q.prompt}</b>${extra}<br>Bạn chọn: ${yours} · Đáp án: <span style="background:var(--yellow)">${ans}</span></div>`;
  }).join("") : "<p>Không có câu sai.</p>";
};
document.getElementById("review").onclick = () => { result.classList.add("hide"); quiz.classList.remove("hide"); render(); };
document.getElementById("again").onclick = () => start(state.filter);
homeBtn.onclick = () => { quiz.classList.add("hide"); result.classList.add("hide"); home.classList.remove("hide"); homeBtn.classList.add("hide"); };
document.addEventListener("keydown", e => {
  if (quiz.classList.contains("hide")) return;
  const q = state.pool[state.index];
  if (!q || state.revealed[keyOf(q)]) {
    if (e.key === "ArrowRight") document.getElementById("next").click();
    if (e.key === "ArrowLeft") document.getElementById("prev").click();
    return;
  }
  const map = { a: "A", b: "B", c: "C", d: "D", "1": "A", "2": "B", "3": "C", "4": "D" };
  if (q.type === "mcq" && map[e.key.toLowerCase()]) { state.picks[keyOf(q)] = map[e.key.toLowerCase()]; render(); }
  if (q.type === "tf" && (e.key.toLowerCase() === "d" || e.key === "1")) { state.picks[keyOf(q)] = "Đ"; render(); }
  if (q.type === "tf" && (e.key.toLowerCase() === "s" || e.key === "2")) { state.picks[keyOf(q)] = "S"; render(); }
  if (e.key === "Enter") document.getElementById("check").click();
});
renderHome();
</script>
</body>
</html>
"""


def main():
    items = parse_questions(SRC.read_text(encoding="utf-8"))
    quiz = to_quiz(items)
    if not quiz:
        raise SystemExit("Không đọc được câu hỏi")
    html = HTML.replace("__DATA__", json.dumps(quiz, ensure_ascii=False))
    OUT.write_text(html, encoding="utf-8")
    DESKTOP.write_text(html, encoding="utf-8")
    from collections import Counter
    c = Counter(q["section"].split(".")[0] + " / " + q["type"] for q in quiz)
    print(f"{len(quiz)} câu")
    for k, v in c.items():
        print(f"  {k}: {v}")
    print(OUT)
    print(DESKTOP)


if __name__ == "__main__":
    main()
