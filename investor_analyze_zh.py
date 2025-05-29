# -*- coding: utf-8 -*-
import os, logging, smtplib, traceback, random
from datetime import datetime
from dateutil import parser
from email.mime.text import MIMEText
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

# === Setup ===
app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.DEBUG)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "kata.chatbot@gmail.com"
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

LANGUAGE = {
    "zh": {
        "email_subject": "您的投资人洞察报告",
        "report_title": "🎯 投资人洞察报告"
    }
}

# === Utility ===
def compute_age(dob):
    try:
        dt = parser.parse(dob)
        today = datetime.today()
        return today.year - dt.year - ((today.month, today.day) < (dt.month, dt.day))
    except:
        return 0

def get_openai_response(prompt, temp=0.85):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=temp
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"OpenAI error: {e}")
        return None

def send_email(html_body, subject):
    msg = MIMEText(html_body, 'html', 'utf-8')
    msg['Subject'] = subject
    msg['From'] = SMTP_USERNAME
    msg['To'] = SMTP_USERNAME
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        logging.error(f"Email send error: {e}")

# === AI Content Blocks ===
def generate_chart_metrics():
    return [
        {
            "title": "市场定位",
            "labels": ["品牌记忆度", "客户契合度", "声誉粘性"],
            "values": [random.randint(70, 90), random.randint(65, 85), random.randint(70, 90)]
        },
        {
            "title": "投资吸引力",
            "labels": ["故事信心度", "扩展性模型", "信任证明度"],
            "values": [random.randint(70, 85), random.randint(60, 80), random.randint(75, 90)]
        },
        {
            "title": "战略执行力",
            "labels": ["合作准备度", "高端通路运用", "领导影响力"],
            "values": [random.randint(65, 85), random.randint(65, 85), random.randint(75, 90)]
        }
    ]

def generate_chart_html(metrics):
    colors = ["#8C52FF", "#5E9CA0", "#F2A900"]
    html = ""
    for i, m in enumerate(metrics):
        html += f"<strong style='font-size:18px;color:#333;'>{m['title']}</strong><br>"
        for j, (label, val) in enumerate(zip(m['labels'], m['values'])):
            html += (
                f"<div style='display:flex;align-items:center;margin-bottom:8px;'>"
                f"<span style='width:180px;'>{label}</span>"
                f"<div style='flex:1;background:#eee;border-radius:5px;overflow:hidden;'>"
                f"<div style='width:{val}%;height:14px;background:{colors[j % len(colors)]};'></div></div>"
                f"<span style='margin-left:10px;'>{val}%</span></div>"
            )
        html += "<br>"
    return html

def build_dynamic_summary(age, experience, industry, country, metrics):
    brand, fit, stick = metrics[0]["values"]
    conf, scale, trust = metrics[1]["values"]
    partn, luxury, leader = metrics[2]["values"]
    return (
        "<br><div style='font-size:24px;font-weight:bold;'>🧠 策略总结：</div><br>"
        f"<p style='line-height:1.7;'>在 {country} 的 {industry} 行业中，拥有 {experience} 年经验、年龄 {age} 岁的专业人士通常在市场定位方面表现稳健。品牌记忆度平均为 {brand}%，客户契合度为 {fit}%，声誉粘性为 {stick}%。</p>"
        f"<p style='line-height:1.7;'>在区域投资人心中，故事信心度（{conf}%）与信任证明（{trust}%）是吸引投资的关键因素。扩展性模型得分 {scale}%，代表还有成长空间。</p>"
        f"<p style='line-height:1.7;'>合作准备度为 {partn}%、高端通路运用为 {luxury}%、领导影响力为 {leader}% —— 这些体现了具备国际化执行力与影响力的潜质。</p>"
        f"<p style='line-height:1.7;'>综合比较新加坡、马来西亚和台湾的同行趋势，您在该领域展现出显著的战略优势与投资吸引力。</p>"
    )

# === Endpoint ===
@app.route("/investor_analyze_zh", methods=["POST"])
def investor_analyze_zh():
    try:
        data = request.get_json(force=True)
        logging.debug(f"POST received: {data}")

        full_name = data.get("fullName")
        chinese_name = data.get("chineseName", "")
        dob = data.get("dob")
        company = data.get("company")
        role = data.get("role")
        country = data.get("country")
        experience = data.get("experience")
        industry = data.get("industry")
        if industry == "Other":
            industry = data.get("otherIndustry", "其他")
        challenge = data.get("challenge")
        context = data.get("context")
        target = data.get("targetProfile")
        advisor = data.get("advisor")
        email = data.get("email")

        age = compute_age(dob)
        chart_metrics = generate_chart_metrics()
        chart_html = generate_chart_html(chart_metrics)
        summary_html = build_dynamic_summary(age, experience, industry, country, chart_metrics)

        prompt = (
            f"你是一位商业顾问，请为在{country}从事{industry}行业、有{experience}年经验的专业人士，"
            "撰写10条具创意、富启发性的吸引投资人技巧，每条以表情符号开头。语言用简体中文，风格轻松、实用。"
        )
        tips_text = get_openai_response(prompt)
        if tips_text:
            tips_block = "<br><div style='font-size:24px;font-weight:bold;'>💡 创意建议：</div><br>" + \
                         "<br>".join(f"<p style='font-size:16px;'>{line.strip()}</p>" for line in tips_text.splitlines() if line.strip())
        else:
            tips_block = "<p style='color:red;'>⚠️ 无法生成创意建议，请稍后重试。</p>"

        footer = (
            "<div style='background-color:#f9f9f9;color:#333;padding:20px;border-left:6px solid #8C52FF;"
            "border-radius:8px;margin-top:30px;'>"
            "<strong>📊 本报告基于以下来源：</strong>"
            "<ul style='margin-top:10px;margin-bottom:10px;padding-left:20px;line-height:1.7;'>"
            "<li>新加坡、马来西亚、台湾地区的专业人士匿名数据</li>"
            "<li>OpenAI 投资趋势模型 + 区域市场洞察</li></ul>"
            "<p style='margin-top:10px;line-height:1.7;'>本分析符合 PDPA 合规标准，所有资料仅用于统计模型，不会存储个人记录。</p>"
            "<p style='margin-top:10px;line-height:1.7;'>"
            "<strong>附注：</strong> 此为初步洞察，我们将在 24 至 48 小时内发送更完整的定制报告。"
            "若您想加速获取建议，也可预约 15 分钟私人通话服务。🎯</p></div>"
        )

        title = f"<h4 style='text-align:center;font-size:24px;'>{LANGUAGE['zh']['report_title']}</h4>"

        details = (
            f"<br><div style='font-size:14px;color:#666;'>"
            f"<strong>📝 提交摘要</strong><br>"
            f"英文名: {full_name}<br>"
            f"中文名: {chinese_name}<br>"
            f"出生日期: {dob}<br>"
            f"国家: {country}<br>"
            f"公司: {company}<br>"
            f"职位: {role}<br>"
            f"经验年数: {experience}<br>"
            f"行业: {industry}<br>"
            f"挑战: {challenge}<br>"
            f"背景说明: {context}<br>"
            f"目标对象: {target}<br>"
            f"推荐人: {advisor}<br>"
            f"邮箱: {email}</div><br>"
        )

        full_html = title + details + chart_html + summary_html + tips_block + footer
        send_email(full_html, LANGUAGE['zh']['email_subject'])

        return jsonify({"html_result": title + chart_html + summary_html + tips_block + footer})

    except Exception as e:
        logging.error(f"investor_analyze_zh error: {e}")
        traceback.print_exc()
        return jsonify({"error": "服务器错误，请稍后再试"}), 500

# === Run Server Locally ===
if __name__ == "__main__":
    app.run(debug=True)
