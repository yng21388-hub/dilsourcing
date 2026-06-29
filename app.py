from flask import Flask, render_template_string, request, jsonify
import requests
import os

app = Flask(__name__)

CLIENT_ID = "7BHh60nWdPEztgS9O6DM"
CLIENT_SECRET = "RxKIQpjyzn"

HTML_PAGE = """
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>딜소싱 체크리스트 자동조사</title>
<style>
  body { font-family: 'Malgun Gothic', sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; background: #f7f7f9; }
  h1 { font-size: 22px; color: #222; }
  .box { background: white; border-radius: 10px; padding: 20px; margin-bottom: 20px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }
  input[type=text] { width: 70%; padding: 10px; font-size: 15px; border: 1px solid #ccc; border-radius: 6px; }
  button { padding: 10px 18px; font-size: 15px; border: none; border-radius: 6px; background: #4a6cf7; color: white; cursor: pointer; }
  button:hover { background: #3a5ce5; }
  textarea { width: 100%; height: 150px; font-size: 13px; padding: 10px; border-radius: 6px; border: 1px solid #ccc; box-sizing: border-box; }
  .ok { color: green; font-weight: bold; }
  .err { color: red; font-weight: bold; }
  .step { font-weight: bold; margin-top: 10px; color: #444; margin-bottom: 8px; }
  table { width: 100%; border-collapse: collapse; margin-top: 12px; }
  td { padding: 8px; border: 1px solid #ddd; font-size: 14px; }
  .label { font-weight: bold; width: 35%; background: #fafafa; }
  .yes { background: #d4f4dd; }
  .no { background: #fbdada; }
</style>
</head>
<body>
  <h1>📊 딜소싱 체크리스트 자동조사</h1>

  <div class="box">
    <div class="step">1️⃣ 기업명 입력 후 검색</div>
    <input type="text" id="company" placeholder="기업명을 입력하세요">
    <button onclick="search()">검색</button>
    <div id="searchStatus"></div>
  </div>

  <div class="box" id="resultBox" style="display:none;">
    <div class="step">2️⃣ 아래 프롬프트를 복사해서 Claude.ai에 붙여넣으세요</div>
    <textarea id="promptText" readonly></textarea>
    <br><br>
    <button onclick="copyPrompt()">📋 프롬프트 복사</button>
    <span id="copyStatus"></span>
  </div>

  <div class="box" id="pasteBox" style="display:none;">
    <div class="step">3️⃣ Claude 답변을 여기에 붙여넣으세요</div>
    <textarea id="claudeAnswer" placeholder="여기에 Claude 답변을 붙여넣으세요"></textarea>
    <br><br>
    <button onclick="showResult()">📊 결과 확인</button>
    <div id="resultDisplay" style="display:none;"></div>
  </div>

<script>
let currentCompany = "";

async function search() {
    const company = document.getElementById('company').value.trim();
    if (!company) { alert("기업명을 입력하세요"); return; }
    currentCompany = company;
    document.getElementById('searchStatus').innerHTML = "🔍 검색 중...";
    document.getElementById('resultBox').style.display = "none";
    document.getElementById('pasteBox').style.display = "none";
    document.getElementById('resultDisplay').style.display = "none";

    const res = await fetch('/search', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({company: company})
    });
    const data = await res.json();
    document.getElementById('searchStatus').innerHTML = "<span class='ok'>✅ 검색 완료!</span>";
    document.getElementById('promptText').value = data.prompt;
    document.getElementById('resultBox').style.display = "block";
    document.getElementById('pasteBox').style.display = "block";
}

function copyPrompt() {
    const text = document.getElementById('promptText');
    text.select();
    document.execCommand('copy');
    document.getElementById('copyStatus').innerHTML = "<span class='ok'>✅ 복사됨! Claude.ai에 붙여넣으세요</span>";
}

function rowHtml(label, value) {
    let cls = "";
    if (value === "여") cls = "yes";
    if (value === "부") cls = "no";
    return "<tr><td class='label'>" + label + "</td><td class='" + cls + "'>" + value + "</td></tr>";
}

async function showResult() {
    const answer = document.getElementById('claudeAnswer').value.trim();
    if (!answer) { alert("Claude 답변을 붙여넣어주세요"); return; }

    const res = await fetch('/parse', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({company: currentCompany, answer: answer})
    });
    const r = await res.json();

    let html = "<table>";
    html += rowHtml("회사명", r.company);
    html += rowHtml("주요사업", r.business);
    html += rowHtml("설립일자", r.est_date);
    html += rowHtml("① 팁스 선정", r.answers[0]);
    html += rowHtml("② 3년이내/20억미만", r.answers[1]);
    html += rowHtml("③ 소부장/헬스케어", r.answers[2]);
    html += rowHtml("④ 피지컬AI", r.answers[3]);
    html += rowHtml("⑤ 지방소재", r.answers[4]);
    html += rowHtml("⑥ 서울소재", r.answers[5]);
    html += rowHtml("⑦ 서울창업지원시설", r.answers[6]);
    html += rowHtml("근거", r.reason);
    html += "</table>";

    document.getElementById('resultDisplay').innerHTML = html;
    document.getElementById('resultDisplay').style.display = "block";
}
</script>
</body>
</html>
"""

def search_naver(query):
    url = "https://openapi.naver.com/v1/search/webkr.json"
    headers = {
        "X-Naver-Client-Id": CLIENT_ID,
        "X-Naver-Client-Secret": CLIENT_SECRET
    }
    params = {"query": query, "display": 5}
    response = requests.get(url, headers=headers, params=params)
    items = response.json().get("items", [])
    result = ""
    for item in items:
        title = item["title"].replace("<b>", "").replace("</b>", "")
        desc = item["description"].replace("<b>", "").replace("</b>", "")
        result += f"- {title}: {desc}\n"
    return result

def make_prompt(company_name, search_result):
    return f"""아래는 "{company_name}"에 대한 네이버 검색 결과야.
이 정보를 바탕으로 아래 7개 항목을 판단해줘.
정보가 불충분하면 "확인필요"라고 써줘.

=== 검색 결과 ===
{search_result}

아래 형식으로 정확히 답해줘 (여/부/확인필요 중 하나만):
회사명: {company_name}
1. 팁스 선정: 
2. 3년이내/20억미만: 
3. 소부장/헬스케어: 
4. 피지컬AI: 
5. 지방소재: 
6. 서울소재: 
7. 서울창업지원시설: 
설립일자: (YYYY-MM-DD 형식, 모르면 확인필요)
주요사업: (한 줄 요약)
근거: (간단히 한 줄로)
"""

def parse_answers(result_text):
    answers = []
    keys = ["팁스 선정", "3년이내/20억미만", "소부장/헬스케어",
            "피지컬AI", "지방소재", "서울소재", "서울창업지원시설"]
    for key in keys:
        found = "확인필요"
        for line in result_text.split("\n"):
            if key in line:
                val = line.split(":", 1)[-1].strip()
                if "여" in val:
                    found = "여"
                elif "부" in val:
                    found = "부"
                break
        answers.append(found)

    est_date = ""
    business = ""
    reason = ""
    for line in result_text.split("\n"):
        if "설립일자" in line:
            est_date = line.split(":", 1)[-1].strip()
        if "주요사업" in line:
            business = line.split(":", 1)[-1].strip()
        if "근거" in line:
            reason = line.split(":", 1)[-1].strip()

    return answers, est_date, business, reason

@app.route('/')
def home():
    return render_template_string(HTML_PAGE)

@app.route('/search', methods=['POST'])
def search():
    data = request.json
    company = data['company']

    all_results = ""
    queries = [
        f"{company} 스타트업 사업 소개",
        f"{company} 소재지 설립연도",
        f"{company} TIPS 팁스 선정",
        f"{company} 매출 투자유치"
    ]
    for q in queries:
        result = search_naver(q)
        all_results += f"\n[{q}]\n{result}"

    prompt = make_prompt(company, all_results)
    return jsonify({"prompt": prompt})

@app.route('/parse', methods=['POST'])
def parse():
    data = request.json
    company = data['company']
    answer = data['answer']

    answers, est_date, business, reason = parse_answers(answer)

    return jsonify({
        "company": company,
        "business": business,
        "est_date": est_date,
        "answers": answers,
        "reason": reason
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)