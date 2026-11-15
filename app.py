import streamlit as st
import json

from src.ai import (
    ask_career_question,
    analyze_resume,
    analyze_job_match,
    analyze_skill_gaps,
    create_learning_roadmap,
    start_mock_interview,
    evaluate_interview_answer,
    generate_interview_summary,
    explore_career_path,
)

from src.documents import (
    extract_pdf_text,
    validate_resume_text,
)

from src.retrieval import (
    add_uploaded_document,
    rebuild_vector_store,
)

from src.storage import (
    init_db,
    save_profile,
    get_profile,
    save_analysis,
    get_recent_analyses,
    delete_analysis,
    clear_analysis_history,
)

from src import ui


# =====================================================
# CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="Career GPS",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

ui.inject_css()

init_db()

if "user_id" not in st.session_state:
    st.session_state.user_id = "local_user"

if "messages" not in st.session_state:
    st.session_state.messages = []


# =====================================================
# MOCK INTERVIEW SESSION STATE
# =====================================================

INTERVIEW_DEFAULTS = {
    "interview_active": False,
    "interview_question_number": 1,
    "interview_question": "",
    "interview_target_role": "",
    "interview_experience": "",
    "interview_previous_questions": [],
    "interview_evaluations": [],
    "interview_answer_submitted": False,
    "interview_final_report": "",
}

for key, value in INTERVIEW_DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value.copy() if isinstance(value, list) else value


# =====================================================
# NAVIGATION CONFIG
# =====================================================

PAGES = [
    "Dashboard",
    "Career Chatbot",
    "Resume Analysis",
    "Job Matching",
    "Skill Gap Analysis",
    "Learning Roadmap",
    "Career Explorer",
    "Interview Preparation",
    "Knowledge Base",
    "My Profile",
    "Analysis History",
]

NAV_ICONS = {
    "Dashboard": "space_dashboard",
    "Career Chatbot": "smart_toy",
    "Resume Analysis": "description",
    "Job Matching": "work",
    "Skill Gap Analysis": "insights",
    "Learning Roadmap": "route",
    "Career Explorer": "explore",
    "Interview Preparation": "mic",
    "Knowledge Base": "library_books",
    "My Profile": "account_circle",
    "Analysis History": "history",
}

# Dashboard quick-access cards: (emoji, title, description, target page)
MODULES = [
    ("💬", "Career Chatbot", "Ask career questions across industries.", "Career Chatbot"),
    ("📄", "Resume Intelligence", "Analyze your resume and identify improvements.", "Resume Analysis"),
    ("🎯", "Job Matching", "Compare your resume against job requirements.", "Job Matching"),
    ("🧩", "Skill Gap Analysis", "Identify demonstrated and missing skills.", "Skill Gap Analysis"),
    ("🗺️", "Learning Roadmap", "Generate personalized learning plans.", "Learning Roadmap"),
    ("🚀", "Career Explorer", "Explore possible career paths.", "Career Explorer"),
    ("🎤", "Interview Preparation", "Practice interviews and receive AI feedback.", "Interview Preparation"),
    ("📚", "Knowledge Base", "Upload documents for retrieval-based answers.", "Knowledge Base"),
    ("📊", "Career Profile", "Store your professional background.", "My Profile"),
]

# Labels used by dashboard activity and stats (keyed by saved analysis_type)
ANALYSIS_META = {
    "career_chatbot": ("💬", "Career chat"),
    "resume_analysis": ("📄", "Resume analysis"),
    "job_matching": ("🎯", "Job match"),
    "skill_gap": ("🧩", "Skill gap analysis"),
    "learning_roadmap": ("🗺️", "Learning roadmap"),
    "career_explorer": ("🚀", "Career exploration"),
    "mock_interview_answer": ("🎤", "Mock interview answer"),
    "mock_interview_final_report": ("📊", "Interview report"),
}

CHAT_SUGGESTIONS = [
    "How do I move from my current field into data analytics?",
    "Which skills should I build to become a project manager?",
    "How can I prepare for a first interview in a new industry?",
    "What does a realistic learning plan for a career switch look like?",
]


# =====================================================
# HELPER FUNCTIONS
# =====================================================

def show_result(result):
    with ui.card(ui.unique_key("result")):
        st.markdown(result)


def save_result(analysis_type, input_data, result):
    save_analysis(
        st.session_state.user_id,
        analysis_type,
        input_data,
        result,
    )


def get_profile_text():
    profile = get_profile(st.session_state.user_id)

    if not profile:
        return "No career profile saved yet."

    return f"""
Name: {profile['full_name']}
Profession: {profile['profession']}
Education: {profile['education']}
Experience: {profile['experience']}
Skills: {', '.join(profile['skills'])}
Career Goal: {profile['career_goal']}
"""


def process_pdf(uploaded_file):
    if uploaded_file is None:
        raise ValueError("Please upload a PDF resume.")

    resume_data = extract_pdf_text(uploaded_file)
    validate_resume_text(resume_data["text"])

    return resume_data


def run_analysis(function, *args):
    try:
        with ui.ai_spinner("AI is processing your request..."):
            result = function(*args)

        show_result(result)
        return result

    except Exception as error:
        st.error(f"Analysis failed: {error}")
        return None


def reset_interview():
    for key, value in INTERVIEW_DEFAULTS.items():
        st.session_state[key] = (
            value.copy() if isinstance(value, list) else value
        )


def go_to(target_page):
    """Button callback used by dashboard cards to switch the sidebar page."""
    st.session_state.nav_page = target_page


def use_prompt(prompt_text):
    """Button callback used by chatbot suggestions."""
    st.session_state.pending_prompt = prompt_text


def clear_chat():
    st.session_state.messages = []


def profile_checklist(profile):
    profile = profile or {}
    return [
        ("Name", bool(profile.get("full_name"))),
        ("Profession", bool(profile.get("profession"))),
        ("Education", bool(profile.get("education"))),
        ("Experience", bool(profile.get("experience"))),
        ("Skills", bool(profile.get("skills"))),
        ("Career goal", bool(profile.get("career_goal"))),
    ]


# =====================================================
# SIDEBAR NAVIGATION
# =====================================================

with st.sidebar:

    ui.sidebar_brand()

    page = st.radio(
        "Navigation",
        PAGES,
        key="nav_page",
        format_func=lambda name: f":material/{NAV_ICONS[name]}: {name}",
        label_visibility="collapsed",
    )

    ui.sidebar_footer()


# =====================================================
# DASHBOARD
# =====================================================

if page == "Dashboard":

    profile = get_profile(st.session_state.user_id)

    history = get_recent_analyses(
        st.session_state.user_id,
        limit=100,
    )

    checklist_items = profile_checklist(profile)
    completed = sum(1 for _, done in checklist_items if done)
    completeness = round(completed / len(checklist_items) * 100)

    full_name = (profile or {}).get("full_name", "") or ""
    first_name = full_name.split()[0] if full_name.strip() else ""

    if first_name:
        greeting = f'Welcome back, <span class="cg-grad">{ui.esc(first_name)}</span>'
    else:
        greeting = 'Welcome to <span class="cg-grad">Career GPS</span>'

    ui.hero(
        greeting,
        "Your AI-powered career guide. Chat with an advisor, sharpen your resume, "
        "close skill gaps and practice interviews, across any profession.",
    )

    hero_col1, hero_col2, _ = st.columns([1.2, 1.2, 3])

    hero_col1.button(
        "Ask Career GPS",
        type="primary",
        icon=":material/smart_toy:",
        use_container_width=True,
        on_click=go_to,
        args=("Career Chatbot",),
    )

    hero_col2.button(
        "Analyze resume",
        icon=":material/description:",
        use_container_width=True,
        on_click=go_to,
        args=("Resume Analysis",),
    )

    ui.stat_cards([
        (
            "👤",
            "Profile Status",
            "Created" if profile else "Not Created",
            "Saved in your local database" if profile else "Add your details in My Profile",
        ),
        (
            "✅",
            "Profile Completeness",
            f"{completeness}%",
            f"{completed} of {len(checklist_items)} sections filled",
        ),
        (
            "🗂️",
            "Saved Analyses",
            len(history),
            "Across all tools",
        ),
        (
            "🧰",
            "Available Tools",
            len(MODULES),
            "Career intelligence modules",
        ),
    ])

    left, right = st.columns([1.15, 1])

    with left:

        with ui.card("progress"):

            ui.section("📈", "Career progress overview", "How complete your career profile is.")
            ui.progress_bar("Profile completeness", completeness)
            ui.checklist(checklist_items)

            if completeness < 100:
                st.button(
                    "Complete my profile",
                    icon=":material/account_circle:",
                    on_click=go_to,
                    args=("My Profile",),
                    key="dash_complete_profile",
                )

    with right:

        with ui.card("activity"):

            ui.section("🕘", "Recent activity", "Your latest saved work.")

            if not history:
                ui.empty_state(
                    "✨",
                    "Nothing here yet",
                    "Run any tool and it will appear here.",
                )

            else:
                rows = []

                for item in history[:5]:
                    emoji, label = ANALYSIS_META.get(
                        item["analysis_type"],
                        ("📌", item["analysis_type"].replace("_", " ").title()),
                    )
                    rows.append((emoji, label, str(item["created_at"])[:19].replace("T", " ")))

                ui.activity_list(rows)

    ui.heading("Career intelligence modules")

    for row_start in range(0, len(MODULES), 3):

        cols = st.columns(3)

        for col, (emoji, name, description, target) in zip(
            cols, MODULES[row_start:row_start + 3]
        ):
            with col:

                with ui.card(f"feature_{target.replace(' ', '_').lower()}"):

                    ui.section(emoji, name, description)

                    st.button(
                        "Open",
                        key=f"open_{target}",
                        use_container_width=True,
                        on_click=go_to,
                        args=(target,),
                    )


# =====================================================
# CAREER CHATBOT
# =====================================================

elif page == "Career Chatbot":

    ui.page_header(
        "💬",
        "Career Chatbot",
        "Ask questions about careers, education, skills, "
        "professional development and career transitions.",
    )

    pending_prompt = st.session_state.pop("pending_prompt", None)

    typed_question = st.chat_input(
        "Ask a career-related question..."
    )

    question = typed_question or pending_prompt

    if st.session_state.messages:

        st.button(
            "New chat",
            icon=":material/add:",
            on_click=clear_chat,
            key="new_chat",
        )

    if not st.session_state.messages and not question:

        ui.chat_welcome()

        suggestion_cols = st.columns(2)

        for index, suggestion in enumerate(CHAT_SUGGESTIONS):
            suggestion_cols[index % 2].button(
                suggestion,
                key=f"suggestion_{index}",
                use_container_width=True,
                on_click=use_prompt,
                args=(suggestion,),
            )

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if question:

        st.session_state.messages.append({
            "role": "user",
            "content": question,
        })

        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):

            try:
                typing_slot = st.empty()
                typing_slot.markdown(
                    ui.typing_indicator("Searching knowledge and generating answer"),
                    unsafe_allow_html=True,
                )

                try:
                    response = ask_career_question(question)
                finally:
                    typing_slot.empty()

                answer = response["answer"]

                st.markdown(answer)

                sources = response.get("sources", [])

                if sources:
                    st.caption(
                        "Retrieved sources: " + ", ".join(sources)
                    )

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                })

                save_result(
                    "career_chatbot",
                    {"question": question},
                    answer,
                )

            except Exception as error:
                st.error(f"Chatbot error: {error}")


# =====================================================
# RESUME ANALYSIS
# =====================================================

elif page == "Resume Analysis":

    ui.page_header(
        "📄",
        "Resume Intelligence",
        "Upload your resume to evaluate its content, "
        "skills, education, experience and improvement areas.",
    )

    upload_col, info_col = st.columns([1.5, 1])

    with upload_col:

        with ui.card("resume_upload"):

            ui.section("📎", "Upload your resume", "PDF files with selectable text work best.")

            uploaded_file = st.file_uploader(
                "Upload Resume (PDF)",
                type=["pdf"],
                key="resume_analysis",
            )

            analyze_clicked = st.button("Analyze Resume", type="primary")

    with info_col:

        with ui.card("resume_info"):

            ui.section("🔎", "What gets reviewed")
            st.markdown(
                "- Content and structure\n"
                "- Skills and education\n"
                "- Experience and achievements\n"
                "- Areas to improve"
            )

    if analyze_clicked:

        if uploaded_file is None:
            st.warning("Please upload your resume first.")

        else:
            try:
                with ui.ai_spinner("Extracting and analyzing resume..."):

                    resume_data = process_pdf(uploaded_file)

                    result = analyze_resume(
                        resume_data["text"]
                    )

                ui.heading("Resume Analysis Report")
                show_result(result)

                st.caption(
                    f"File: {resume_data['filename']} | "
                    f"Pages: {resume_data['total_pages']}"
                )

                save_result(
                    "resume_analysis",
                    {
                        "filename": resume_data["filename"],
                        "pages": resume_data["total_pages"],
                    },
                    result,
                )

            except Exception as error:
                st.error(f"Resume analysis failed: {error}")


# =====================================================
# JOB MATCHING
# =====================================================

elif page == "Job Matching":

    ui.page_header(
        "🎯",
        "Resume vs Job Description",
        "Evaluate how your documented qualifications "
        "and experience align with a job description.",
    )

    resume_col, job_col = st.columns(2)

    with resume_col:

        with ui.card("job_resume"):

            ui.section("📎", "Your resume")

            uploaded_file = st.file_uploader(
                "Upload Resume (PDF)",
                type=["pdf"],
                key="job_resume",
            )

    with job_col:

        with ui.card("job_description"):

            ui.section("📋", "The job")

            job_description = st.text_area(
                "Paste Job Description",
                height=250,
            )

    if st.button("Analyze Job Match", type="primary"):

        if uploaded_file is None or not job_description.strip():

            st.warning(
                "Upload your resume and enter the job description."
            )

        else:
            try:
                with ui.ai_spinner(
                    "Comparing resume with job requirements..."
                ):

                    resume_data = process_pdf(uploaded_file)

                    result = analyze_job_match(
                        resume_data["text"],
                        job_description,
                    )

                ui.heading("Job Match Report")
                show_result(result)

                save_result(
                    "job_matching",
                    {
                        "filename": resume_data["filename"],
                        "job_description": job_description,
                    },
                    result,
                )

            except Exception as error:
                st.error(f"Job matching failed: {error}")


# =====================================================
# SKILL GAP ANALYSIS
# =====================================================

elif page == "Skill Gap Analysis":

    ui.page_header(
        "🧩",
        "Skill Gap Analysis",
        "Identify existing skills, transferable abilities "
        "and areas that may require further development.",
    )

    with ui.card("skill_gap_input"):

        profile_text = st.text_area(
            "Your Background, Education, Experience and Skills",
            value=get_profile_text(),
            height=220,
        )

        target_role = st.text_input(
            "Target Profession / Role",
            placeholder="Example: Project Manager, Nurse, Data Analyst",
        )

        analyze_clicked = st.button("Analyze Skill Gaps", type="primary")

    if analyze_clicked:

        if not profile_text.strip() or not target_role.strip():

            st.warning(
                "Please provide your background and target role."
            )

        else:

            result = run_analysis(
                analyze_skill_gaps,
                profile_text,
                target_role,
            )

            if result:
                save_result(
                    "skill_gap",
                    {
                        "profile": profile_text,
                        "target_role": target_role,
                    },
                    result,
                )


# =====================================================
# LEARNING ROADMAP
# =====================================================

elif page == "Learning Roadmap":

    ui.page_header(
        "🗺️",
        "Personalized Learning Roadmap",
        "Turn your current background and goal into a step-by-step learning plan.",
    )

    with ui.card("roadmap_input"):

        profile_text = st.text_area(
            "Your Current Background",
            value=get_profile_text(),
            height=200,
        )

        goal_col, time_col = st.columns([2, 1])

        with goal_col:
            career_goal = st.text_input(
                "Your Career Goal",
                placeholder="Example: Become a Civil Engineer",
            )

        with time_col:
            study_time = st.selectbox(
                "Available Study Time",
                [
                    "30 minutes daily",
                    "1 hour daily",
                    "2 hours daily",
                    "3 hours daily",
                    "4+ hours daily",
                    "Flexible",
                ],
            )

        generate_clicked = st.button("Generate Roadmap", type="primary")

    if generate_clicked:

        if not profile_text.strip() or not career_goal.strip():

            st.warning(
                "Please provide your background and career goal."
            )

        else:

            result = run_analysis(
                create_learning_roadmap,
                profile_text,
                career_goal,
                study_time,
            )

            if result:
                save_result(
                    "learning_roadmap",
                    {
                        "career_goal": career_goal,
                        "study_time": study_time,
                    },
                    result,
                )


# =====================================================
# CAREER EXPLORER
# =====================================================

elif page == "Career Explorer":

    ui.page_header(
        "🚀",
        "Career Path Explorer",
        "Explore professional pathways based on your "
        "background, interests and transferable skills.",
    )

    with ui.card("explorer_input"):

        profile_text = st.text_area(
            "Your Background",
            value=get_profile_text(),
            height=200,
        )

        career_interest = st.text_input(
            "Career Field or Interest",
            placeholder="Example: Healthcare, Finance, Technology, Education",
        )

        explore_clicked = st.button("Explore Career Paths", type="primary")

    if explore_clicked:

        if not profile_text.strip() or not career_interest.strip():

            st.warning(
                "Please provide your background and career interests."
            )

        else:

            result = run_analysis(
                explore_career_path,
                profile_text,
                career_interest,
            )

            if result:
                save_result(
                    "career_explorer",
                    {"career_interest": career_interest},
                    result,
                )


# =====================================================
# INTERVIEW PREPARATION - MOCK INTERVIEW SYSTEM
# =====================================================

elif page == "Interview Preparation":

    ui.page_header(
        "🎤",
        "AI Mock Interview",
        "Complete a five-question interview. Each submitted answer "
        "is evaluated separately with detailed AI feedback.",
    )

    # -------------------------------------------------
    # INTERVIEW SETUP
    # -------------------------------------------------

    with st.form("start_interview_form"):

        target_role = st.text_input(
            "Target Job / Profession",
            value=st.session_state.interview_target_role,
            placeholder="Example: Data Scientist, Teacher, Accountant",
        )

        experience = st.text_area(
            "Your Experience and Background",
            value=(
                st.session_state.interview_experience
                or get_profile_text()
            ),
            height=180,
        )

        start_clicked = st.form_submit_button(
            "Start / Restart Mock Interview",
            type="primary",
        )

    if start_clicked:

        if not target_role.strip() or not experience.strip():

            st.warning(
                "Please provide your target role and background."
            )

        else:

            st.session_state.interview_active = False
            st.session_state.interview_question_number = 1
            st.session_state.interview_target_role = target_role
            st.session_state.interview_experience = experience
            st.session_state.interview_previous_questions = []
            st.session_state.interview_evaluations = []
            st.session_state.interview_answer_submitted = False
            st.session_state.interview_final_report = ""
            st.session_state.interview_question = ""

            try:
                with ui.ai_spinner(
                    "Preparing your first interview question..."
                ):

                    question = start_mock_interview(
                        target_role,
                        experience,
                        1,
                        [],
                    )

                st.session_state.interview_question = question
                st.session_state.interview_previous_questions.append(
                    question
                )
                st.session_state.interview_active = True

                st.rerun()

            except Exception as error:
                st.error(
                    f"Could not start interview: {error}"
                )

    # -------------------------------------------------
    # ACTIVE INTERVIEW
    # -------------------------------------------------

    if st.session_state.interview_active:

        question_number = st.session_state.interview_question_number

        st.divider()

        ui.heading(f"Interview Question {question_number} of 5")

        ui.stepper(question_number, 5)

        ui.question_box(
            st.session_state.interview_question
        )

        st.write("")

        # -------------------------------------------------
        # ANSWER SUBMISSION
        # -------------------------------------------------

        if not st.session_state.interview_answer_submitted:

            with st.form(
                f"answer_form_{question_number}"
            ):

                answer = st.text_area(
                    "Your Answer",
                    height=220,
                    placeholder="Write your interview answer here...",
                )

                submit_answer = st.form_submit_button(
                    "Submit Answer for Evaluation",
                    type="primary",
                )

            if submit_answer:

                if not answer.strip():

                    st.warning(
                        "Please write your answer first."
                    )

                else:

                    try:
                        with ui.ai_spinner(
                            "AI is evaluating your answer..."
                        ):

                            evaluation = evaluate_interview_answer(
                                st.session_state.interview_target_role,
                                st.session_state.interview_experience,
                                st.session_state.interview_question,
                                answer,
                            )

                        evaluation_record = {
                            "question_number": question_number,
                            "question": st.session_state.interview_question,
                            "answer": answer,
                            "evaluation": evaluation,
                        }

                        st.session_state.interview_evaluations.append(
                            evaluation_record
                        )

                        save_result(
                            "mock_interview_answer",
                            {
                                "target_role": st.session_state.interview_target_role,
                                "question_number": question_number,
                                "question": st.session_state.interview_question,
                                "answer": answer,
                            },
                            json.dumps(evaluation, ensure_ascii=False),
                        )

                        st.session_state.interview_answer_submitted = True

                        st.rerun()

                    except Exception as error:
                        st.error(
                            f"Evaluation failed: {error}"
                        )

        # -------------------------------------------------
        # ANSWER EVALUATION
        # -------------------------------------------------

        else:

            latest_evaluation = (
                st.session_state.interview_evaluations[-1]
            )

            evaluation = latest_evaluation["evaluation"]

            ui.heading("AI Answer Evaluation")

            score_col, assess_col = st.columns([1, 1.2])

            with score_col:

                with ui.card("scorecard"):

                    ui.section("📊", "Scorecard")
                    ui.total_score(evaluation["total_score"], 30)
                    ui.score_bars(evaluation["scores"], 5)

            with assess_col:

                with ui.card("assessment"):

                    ui.section("🧠", "Overall Assessment")
                    st.write(evaluation["overall_assessment"])

            good_col, missing_col, improve_col = st.columns(3)

            with good_col:

                with ui.card("tone_good"):

                    ui.section("✅", "What Went Well")
                    for item in evaluation["what_went_well"]:
                        st.write(f"- {item}")

            with missing_col:

                with ui.card("tone_warn"):

                    ui.section("⚠️", "Missing or Incorrect Points")
                    for item in evaluation["missing_or_incorrect_points"]:
                        st.write(f"- {item}")

            with improve_col:

                with ui.card("tone_info"):

                    ui.section("💡", "How to Improve")
                    for item in evaluation["how_to_improve"]:
                        st.write(f"- {item}")

            with ui.card("strong_answer"):

                ui.section("🏆", "Example of a Strong Answer")
                st.write(evaluation["example_strong_answer"])

            with ui.card("follow_up"):

                ui.section("💬", "Follow-up Question")
                st.write(evaluation["follow_up_question"])

            st.divider()

            # NEXT QUESTION

            if question_number < 5:

                if st.button(
                    "Next Interview Question",
                    type="primary",
                ):

                    try:
                        next_number = question_number + 1

                        with ui.ai_spinner(
                            "Preparing your next interview question..."
                        ):

                            next_question = start_mock_interview(
                                st.session_state.interview_target_role,
                                st.session_state.interview_experience,
                                next_number,
                                st.session_state.interview_previous_questions,
                            )

                        st.session_state.interview_question_number = next_number
                        st.session_state.interview_question = next_question

                        st.session_state.interview_previous_questions.append(
                            next_question
                        )

                        st.session_state.interview_answer_submitted = False

                        st.rerun()

                    except Exception as error:
                        st.error(
                            f"Could not generate next question: {error}"
                        )

            # FINAL QUESTION COMPLETED

            else:

                st.success(
                    "You have completed all five interview questions!"
                )

                if st.button(
                    "Generate Final Interview Report",
                    type="primary",
                ):

                    try:
                        with ui.ai_spinner(
                            "Generating your complete interview report..."
                        ):

                            report = generate_interview_summary(
                                st.session_state.interview_target_role,
                                st.session_state.interview_evaluations,
                            )

                        st.session_state.interview_final_report = report

                        save_result(
                            "mock_interview_final_report",
                            {
                                "target_role": (
                                    st.session_state.interview_target_role
                                ),
                                "total_questions": 5,
                            },
                            report,
                        )

                        st.rerun()

                    except Exception as error:
                        st.error(
                            f"Report generation failed: {error}"
                        )

    # -------------------------------------------------
    # FINAL INTERVIEW REPORT
    # -------------------------------------------------

    if st.session_state.interview_final_report:

        st.divider()

        ui.page_header(
            "📊",
            "Final Interview Performance Report",
            "Your complete five-question interview summary.",
        )

        with ui.card("final_report"):

            st.markdown(
                st.session_state.interview_final_report
            )

        st.download_button(
            "Download Interview Report",
            data=st.session_state.interview_final_report,
            file_name="interview_performance_report.txt",
            mime="text/plain",
        )

        if st.button("Start a New Interview"):

            reset_interview()
            st.rerun()


# =====================================================
# KNOWLEDGE BASE
# =====================================================

elif page == "Knowledge Base":

    ui.page_header(
        "📚",
        "Knowledge Base",
        "Upload career-related documents to build your "
        "retrieval-augmented knowledge base.",
    )

    with ui.card("kb_upload"):

        ui.section(
            "📤",
            "Add a document",
            "Supported formats: PDF, TXT and MD. "
            "Scanned PDFs without selectable text are not supported yet.",
        )

        uploaded_file = st.file_uploader(
            "Choose a document",
            type=["pdf", "txt", "md"],
            key="knowledge_document_upload",
        )

        upload_clicked = st.button("Upload Document", type="primary")

    if upload_clicked:

        if uploaded_file is None:

            st.warning(
                "Please select a document first."
            )

        else:

            try:
                result = add_uploaded_document(uploaded_file)

                st.success(
                    f"Successfully uploaded: {result['filename']}"
                )

                st.info(
                    "Now rebuild the FAISS index to make this document searchable."
                )

            except Exception as error:
                st.error(
                    f"Upload failed: {error}"
                )

    with ui.card("kb_rebuild"):

        ui.section(
            "🔄",
            "Rebuild Search Index",
            "Rebuild the index after adding or changing knowledge documents.",
        )

        rebuild_clicked = st.button("Rebuild FAISS Index")

    if rebuild_clicked:

        try:
            with ui.ai_spinner(
                "Reading documents, generating embeddings and rebuilding FAISS..."
            ):

                rebuild_vector_store()

            st.success(
                "FAISS knowledge index rebuilt successfully."
            )

        except Exception as error:
            st.error(
                f"Index rebuilding failed: {error}"
            )


# =====================================================
# MY PROFILE
# =====================================================

elif page == "My Profile":

    existing_profile = (
        get_profile(st.session_state.user_id) or {}
    )

    if "edit_profile_mode" not in st.session_state:
        st.session_state.edit_profile_mode = False

    # ==============================
    # PROFILE DISPLAY MODE
    # ==============================

    if not st.session_state.edit_profile_mode:

        with ui.card("profile_header"):

            col1, col2 = st.columns([3, 1])

            with col1:
                ui.render_profile_header(
                    existing_profile.get("full_name"),
                    existing_profile.get("profession"),
                )

            with col2:
                st.write("")
                if st.button(
                    "✏️ Edit Profile",
                    type="primary",
                    use_container_width=True,
                ):
                    st.session_state.edit_profile_mode = True
                    st.rerun()

        # Education
        with ui.card("profile_education"):

            ui.section("🎓", "Education")

            st.write(
                existing_profile.get("education")
                or "No education information added yet."
            )

        # Experience
        with ui.card("profile_experience"):

            ui.section("💼", "Professional Experience")

            st.write(
                existing_profile.get("experience")
                or "No experience information added yet."
            )

        # Skills
        with ui.card("profile_skills"):

            ui.section("🛠️", "Technical Skills")

            skills = existing_profile.get("skills", [])

            if skills:
                ui.badges(skills)
            else:
                st.info("No skills added yet.")

        # Career Goal
        with ui.card("profile_goal"):

            ui.section("🎯", "Career Goal")

            st.write(
                existing_profile.get("career_goal")
                or "No career goal added yet."
            )

    # ==============================
    # PROFILE EDIT MODE
    # ==============================

    else:

        ui.page_header(
            "✏️",
            "Edit Your Profile",
            "Your details are used to personalize every analysis.",
        )

        with st.form("career_profile_edit_form"):

            full_name = st.text_input(
                "Full Name",
                value=existing_profile.get("full_name", ""),
            )

            profession = st.text_input(
                "Current Profession",
                value=existing_profile.get("profession", ""),
            )

            education = st.text_area(
                "Education",
                value=existing_profile.get("education", ""),
            )

            experience = st.text_area(
                "Experience",
                value=existing_profile.get("experience", ""),
            )

            skills_text = st.text_area(
                "Skills (comma separated)",
                value=", ".join(
                    existing_profile.get("skills", [])
                ),
            )

            career_goal = st.text_area(
                "Career Goal",
                value=existing_profile.get("career_goal", ""),
            )

            col1, col2 = st.columns(2)

            with col1:
                save_clicked = st.form_submit_button(
                    "💾 Save Changes",
                    type="primary",
                    use_container_width=True,
                )

            with col2:
                cancel_clicked = st.form_submit_button(
                    "Cancel",
                    use_container_width=True,
                )

            if save_clicked:

                skills = [
                    skill.strip()
                    for skill in skills_text.split(",")
                    if skill.strip()
                ]

                try:
                    save_profile(
                        user_id=st.session_state.user_id,
                        full_name=full_name,
                        profession=profession,
                        education=education,
                        experience=experience,
                        skills=skills,
                        career_goal=career_goal,
                    )

                    st.session_state.edit_profile_mode = False

                    st.success("Profile updated successfully!")

                    st.rerun()

                except Exception as error:
                    st.error(f"Profile saving failed: {error}")

            elif cancel_clicked:

                st.session_state.edit_profile_mode = False
                st.rerun()


# =====================================================
# ANALYSIS HISTORY
# =====================================================

elif page == "Analysis History":

    ui.page_header(
        "🕘",
        "Analysis History",
        "Everything you have generated, saved and ready to revisit.",
    )

    history = get_recent_analyses(
        st.session_state.user_id,
        limit=50,
    )

    if not history:

        with ui.card("history_empty"):
            ui.empty_state(
                "🗂️",
                "No saved analyses yet",
                "Run any tool and your results will be saved here.",
            )

    else:
        ui.stat_cards([
            (
                "🗂️",
                "Total Saved Analyses",
                len(history),
                "Most recent 50 shown",
            ),
        ])

        # Clear all history
        with st.expander("Delete All History"):
            st.warning(
                "This will permanently delete all your saved analyses."
            )

            confirm_clear = st.checkbox(
                "I confirm that I want to delete all history.",
                key="confirm_clear_history",
            )

            if st.button(
                "Clear All History",
                disabled=not confirm_clear,
                type="primary",
            ):
                deleted_count = clear_analysis_history(
                    st.session_state.user_id
                )

                st.success(
                    f"{deleted_count} analyses deleted successfully."
                )

                st.rerun()

        st.divider()

        # Individual history records
        for item in history:

            title = (
                item["analysis_type"]
                .replace("_", " ")
                .title()
            )

            timestamp = item["created_at"][:19].replace("T", " ")

            with st.expander(
                f"{title} — {timestamp}"
            ):

                st.markdown("**Input Information**")
                st.json(item["input_data"])

                st.markdown("**Analysis Result**")
                st.markdown(item["result"])

                if st.button(
                    "🗑️ Delete This Analysis",
                    key=f"delete_analysis_{item['id']}",
                ):
                    deleted = delete_analysis(
                        item["id"],
                        st.session_state.user_id,
                    )

                    if deleted:
                        st.success("Analysis deleted successfully.")
                    else:
                        st.warning("Analysis was not found.")

                    st.rerun()