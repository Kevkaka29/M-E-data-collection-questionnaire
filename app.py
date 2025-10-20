# app.py
import streamlit as st
import pandas as pd
import csv
import os, io
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# ---------------- CONFIG ----------------
ADMIN_USERNAME = "Bigkev"
ADMIN_PASSWORD = "kevlise"

SERVICE_ACCOUNT_FILE = "service_account.json"
GSHEET_NAME = "M&E_Soccer_Clubs_Responses"
WORKSHEET_NAME = "responses"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

# -------------- GOOGLE SHEETS UTILS --------------
@st.cache_resource
def get_gsheet_client():
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return gspread.authorize(creds)

def append_row_to_sheet(row: dict):
    client = get_gsheet_client()
    sh = client.open(GSHEET_NAME)
    try:
        ws = sh.worksheet(WORKSHEET_NAME)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=WORKSHEET_NAME, rows="1000", cols="50")
        ws.append_row(list(row.keys()))
    ws.append_row(list(row.values()))

def read_all_responses():
    client = get_gsheet_client()
    sh = client.open(GSHEET_NAME)
    try:
        ws = sh.worksheet(WORKSHEET_NAME)
    except gspread.WorksheetNotFound:
        return pd.DataFrame()
    data = ws.get_all_values()
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(data[1:], columns=data[0])

# ---------------- STREAMLIT SETUP ----------------
st.set_page_config(
    page_title="Assessment of Monitoring & Evaluation Strategies on the Performance of Professional Soccer Clubs in Kenya",
    layout="centered"
)

st.title("Assessment of Monitoring & Evaluation Strategies on the Performance of Professional Soccer Clubs in Kenya")


menu = st.sidebar.radio("Menu", ["Fill Questionnaire", "Admin Login"])

# ---------------- CONSENT FUNCTION ----------------
def consent_section():
    st.header("🧾 Research Consent")
    st.write("""
    You are invited to participate in a study on how Monitoring & Evaluation (M&E) strategies influence the performance of professional soccer clubs in Kenya.
    
    **Your participation is voluntary**, and all information provided will be treated confidentially.  
    You may skip any question or stop at any point. Your honest responses will help improve club management and performance evaluation in Kenya.
    """)
    agree = st.checkbox("✅ I have read and understood the above, and I voluntarily agree to participate.")
    return agree

# ---------------- THANK YOU PAGE ----------------
def thank_you_page():
    st.success("🎉 Thank you for participating!")
    st.markdown("""
    Your response has been **successfully recorded** and securely stored.  
    Your contribution helps improve the understanding and effectiveness of M&E in Kenyan soccer clubs.  
    We truly appreciate your time and input. 🙏
    """)
    st.balloons()

    if st.button("Submit another response"):
        # Clear everything for a new session
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

# ---------------- QUESTIONNAIRE ----------------
def questionnaire():
    if not consent_section():
        st.info("Please provide your consent to continue.")
        st.stop()

    if "step" not in st.session_state:
        st.session_state.step = 1
    if "answers" not in st.session_state:
        st.session_state.answers = {}

    step = st.session_state.step
    total_steps = 6

    st.progress(step / total_steps)
    st.caption(f"Step {step} of {total_steps}")

    # ---------- SECTION A ----------
    if step == 1:
        st.header("Section A: Background Information")
        st.caption("This section helps us understand your role and background.")

        club_name = st.text_input("Club’s name", placeholder="e.g., Gor Mahia, AFC Leopards, Bandari FC")
        league = st.selectbox(
            "League you are participating in",
            ["— Select your league —", "Kenya Premier League", "National Super League", "Other"]
        )
        if league == "— Select your league —":
            league = ""

        role = st.selectbox(
            "Your role in the club",
            ["— Select your role —", "President", "Secretary General", "Treasurer", "Team Manager",
             "Coach", "Player", "Performance Analyst", "Other (specify)"]
        )
        if role == "— Select your role —":
            role = ""
        elif role == "Other (specify)":
            role = "Other: " + st.text_input("If Other, specify your role")

        duration = st.selectbox(
            "How long have you been in the club?",
            ["— Select duration —", "Less than 1 year", "1–4 years", "5–8 years", "More than 8 years"]
        )
        if duration == "— Select duration —":
            duration = ""

        if st.button("Next ➡️"):
            st.session_state.answers.update({
                "club_name": club_name,
                "league": league,
                "role": role,
                "duration_in_club": duration
            })
            st.session_state.step += 1
            st.rerun()

    # ---------- SECTION B ----------
    elif step == 2:
        st.header("Section B: Monitoring and Evaluation (M&E) Strategies")
        with st.expander("💡 What is M&E?"):
            st.write("Monitoring and Evaluation (M&E) involves tracking activities and assessing performance to improve club management and outcomes.")

        q5 = st.radio("5. Do you have any idea of monitoring and evaluation in managing a soccer club?", ["Yes", "No"], index=None)
        q6 = st.radio("6. Is there a monitoring and evaluation system currently in place in your club?", ["Yes", "No", "Not sure"], index=None)
        q7 = st.selectbox(
            "7. If M&E has been implemented, how long has it been in use?",
            ["— Select duration —", "Less than 1 year", "1–3 years", "More than 3 years", "Not sure"]
        )
        if q7 == "— Select duration —":
            q7 = ""

        aspects = st.multiselect(
            "8. What aspects of your club does M&E focus on?",
            ["Player performance", "Staff performance (e.g., coaches, trainers)", "Club governance",
             "Financial management", "Community involvement", "Other (specify)"]
        )
        aspects_other = ""
        if "Other (specify)" in aspects:
            aspects_other = st.text_input("If Other, specify aspects")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ Back"):
                st.session_state.step -= 1
                st.rerun()
        with col2:
            if st.button("Next ➡️"):
                st.session_state.answers.update({
                    "q5_know_M&E": q5,
                    "q6_M&E_system_in_place": q6,
                    "q7_M&E_duration": q7,
                    "q8_aspects": "; ".join(aspects) + (("; " + aspects_other) if aspects_other else "")
                })
                st.session_state.step += 1
                st.rerun()

    # ---------- SECTION C ----------
    elif step == 3:
        st.header("Section C: Effectiveness of M&E Strategies")
        q9 = st.radio(
            "9. To what extent would you say M&E strategies are effective in enhancing club performance?",
            ["Very effective", "Moderately effective", "Slightly effective", "Not effective", "Not applicable"], index=None
        )
        st.caption("💡 Think of how much M&E has helped improve your club’s performance, organization, or decision-making.")

        metrics = st.multiselect(
            "10. What metrics does your club’s M&E system measure?",
            ["Player performance", "Financial management", "Club administration", "Coaching strategies",
             "Fan engagement", "Talent scouting", "Other (specify)"]
        )
        metrics_other = ""
        if "Other (specify)" in metrics:
            metrics_other = st.text_input("If Other, specify metrics")

        q11 = st.selectbox(
            "11. When are M&E reports conducted?",
            ["— Select frequency —", "Weekly", "Monthly", "Quarterly", "Annually", "Not applicable"]
        )
        if q11 == "— Select frequency —":
            q11 = ""

        improvements = st.multiselect(
            "12. Where has M&E brought the most improvement?",
            ["Player performance", "Financial management", "Club administration", "Coaching strategies",
             "Talent scouting", "Fan engagement", "Other (specify)"]
        )
        improvements_other = ""
        if "Other (specify)" in improvements:
            improvements_other = st.text_input("If Other, specify improvements")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ Back"):
                st.session_state.step -= 1
                st.rerun()
        with col2:
            if st.button("Next ➡️"):
                st.session_state.answers.update({
                    "q9_effectiveness": q9,
                    "q10_metrics": "; ".join(metrics) + (("; " + metrics_other) if metrics_other else ""),
                    "q11_report_frequency": q11,
                    "q12_most_improvement": "; ".join(improvements) + (("; " + improvements_other) if improvements_other else "")
                })
                st.session_state.step += 1
                st.rerun()

    # ---------- SECTION D ----------
    elif step == 4:
        st.header("Section D: Implementing M&E Strategies")
        challenges = st.multiselect(
            "What challenges has your club faced in implementing M&E?",
            ["Lack of funding", "Inadequate training", "Resistance from staff",
             "Lack of technology", "Time constraints", "Other (specify)"]
        )
        challenges_other = ""
        if "Other (specify)" in challenges:
            challenges_other = st.text_input("If Other, specify challenges")

        measures = st.text_area("What measures does the club take to handle the challenges above?")
        q_do_more = st.radio(
            "Do you believe a more detailed M&E system would improve performance?",
            ["Strongly agree", "Agree", "Neutral", "Disagree", "Strongly disagree"], index=None
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ Back"):
                st.session_state.step -= 1
                st.rerun()
        with col2:
            if st.button("Next ➡️"):
                st.session_state.answers.update({
                    "qD_challenges": "; ".join(challenges) + (("; " + challenges_other) if challenges_other else ""),
                    "qD_measures": measures,
                    "q_do_more_detailed_M&E": q_do_more
                })
                st.session_state.step += 1
                st.rerun()

    # ---------- SECTION E ----------
    elif step == 5:
        st.header("Section E: Suggestions for Improvement")
        resources = st.multiselect(
            "What resources would make your M&E system better?",
            ["More funding", "Better technology", "External experts", "Staff training",
             "Collaboration with other clubs", "Other (specify)"]
        )
        resources_other = ""
        if "Other (specify)" in resources:
            resources_other = st.text_input("If Other, specify")
        q17 = st.text_area("What concrete changes could improve your club’s M&E system?")
        q18 = st.text_area("Any additional comments?")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ Back"):
                st.session_state.step -= 1
                st.rerun()
        with col2:
            if st.button("Submit ✅"):
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                row = {"timestamp": timestamp, **st.session_state.answers,
                       "q16_resources": "; ".join(resources) + (("; " + resources_other) if resources_other else ""),
                       "q17_concrete_changes": q17, "q18_other_comments": q18}

                try:
                    append_row_to_sheet(row)
                    st.session_state.step = 6  # Move to thank-you page
                    st.rerun()
                except Exception as e:
                    st.warning(f"⚠️ Google Sheets failed: {e}")
                    st.info("Saving locally as backup...")
                    backup_file = "responses_backup.csv"
                    file_exists = os.path.isfile(backup_file)
                    with open(backup_file, "a", newline="", encoding="utf-8") as f:
                        writer = csv.DictWriter(f, fieldnames=row.keys())
                        if not file_exists:
                            writer.writeheader()
                        writer.writerow(row)
                    st.session_state.step = 6
                    st.rerun()

    # ---------- THANK YOU PAGE ----------
    elif step == 6:
        thank_you_page()

# ---------------- ADMIN PAGE ----------------
def admin_page():
    st.header("Admin Panel")
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if not st.session_state.logged_in:
        user = st.text_input("Username")
        pw = st.text_input("Password", type="password")
        if st.button("Login"):
            if user == ADMIN_USERNAME and pw == ADMIN_PASSWORD:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Invalid credentials.")
    else:
        df = read_all_responses()
        if df is None or df.empty:
            st.info("No responses yet.")
        else:
            st.success(f"{len(df)} responses loaded.")
            st.dataframe(df)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Download CSV", csv, "M&E_responses.csv", "text/csv")
            towrite = io.BytesIO()
            df.to_excel(towrite, index=False, engine="openpyxl")
            towrite.seek(0)
            st.download_button("Download Excel", towrite, "M&E_responses.xlsx",
                               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

# ---------------- MAIN ----------------
if menu == "Fill Questionnaire":
    questionnaire()
else:
    admin_page()
