
import streamlit as st

from src.ai import (
    ask_career_question,
    analyze_resume,
    analyze_job_match,
    analyze_skill_gaps,
    create_learning_roadmap,
    prepare_interview,
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
)


# =====================================================
# CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="Universal AI Career Mentor",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()

if "user_id" not in st.session_state:
    st.session_state.user_id = "local_user"

if "messages" not in st.session_state:
    st.session_state.messages = []


# =====================================================
# HELPER FUNCTIONS
# =====================================================

def show_result(result):
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
        with st.spinner("AI is processing your request..."):
            result = function(*args)

        show_result(result)
        return result

    except Exception as error:
        st.error(f"Analysis failed: {error}")
        return None


# =====================================================
# SIDEBAR NAVIGATION
# =====================================================

st.sidebar.title("🎯 Career Mentor")
st.sidebar.caption("Universal AI-powered career guidance")

page = st.sidebar.radio(
    "Navigation",
    [
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
    ],
)

st.sidebar.divider()

st.sidebar.info(
    "Career guidance across technology, healthcare, "
    "education, business, finance, engineering, law, "
    "creative industries and other professions."
)

st.sidebar.caption("Powered by Gemini, LangChain and FAISS")


# =====================================================
# DASHBOARD
# =====================================================

if page == "Dashboard":

    st.title("🎯 Universal AI Career Mentor")

    st.write(
        "An AI-powered career intelligence platform "
        "designed to support people across professions "
        "and industries."
    )

    profile = get_profile(st.session_state.user_id)

    history = get_recent_analyses(
        st.session_state.user_id,
        limit=100,
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Profile Status",
        "Created" if profile else "Not Created",
    )

    col2.metric(
        "Saved Analyses",
        len(history),
    )

    col3.metric(
        "Available Tools",
        "9",
    )

    st.divider()

    st.subheader("Career Intelligence Modules")

    modules = [
        ("💬 Career Chatbot", "Ask career questions across industries."),
        ("📄 Resume Intelligence", "Analyze your resume and identify improvements."),
        ("🎯 Job Matching", "Compare your resume against job requirements."),
        ("🧩 Skill Gap Analysis", "Identify demonstrated and missing skills."),
        ("🗺️ Learning Roadmap", "Generate personalized learning plans."),
        ("🚀 Career Explorer", "Explore possible career paths."),
        ("🎤 Interview Preparation", "Generate profession-specific interview questions."),
        ("📚 Knowledge Base", "Upload documents for retrieval-based answers."),
        ("📊 Career Profile", "Store your professional background."),
    ]

    for name, description in modules:
        st.markdown(f"**{name}**")
        st.caption(description)


# =====================================================
# CAREER CHATBOT
# =====================================================

elif page == "Career Chatbot":

    st.title("💬 Universal Career Chatbot")

    st.write(
        "Ask questions about careers, education, skills, "
        "professional development and career transitions."
    )

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    question = st.chat_input(
        "Ask a career-related question..."
    )

    if question:

        st.session_state.messages.append({
            "role": "user",
            "content": question,
        })

        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):

            try:
                with st.spinner("Searching knowledge and generating answer..."):

                    response = ask_career_question(question)

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

    st.title("📄 Resume Intelligence")

    st.write(
        "Upload your resume to evaluate its content, "
        "skills, education, experience and improvement areas."
    )

    uploaded_file = st.file_uploader(
        "Upload Resume (PDF)",
        type=["pdf"],
        key="resume_analysis",
    )

    if st.button("Analyze Resume", type="primary"):

        if uploaded_file is None:
            st.warning("Please upload your resume first.")

        else:
            try:
                with st.spinner("Extracting and analyzing resume..."):

                    resume_data = process_pdf(uploaded_file)

                    result = analyze_resume(
                        resume_data["text"]
                    )

                st.subheader("Resume Analysis Report")
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

    st.title("🎯 Resume vs Job Description")

    st.write(
        "Evaluate how your documented qualifications "
        "and experience align with a job description."
    )

    uploaded_file = st.file_uploader(
        "Upload Resume (PDF)",
        type=["pdf"],
        key="job_resume",
    )

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
                with st.spinner("Comparing resume with job requirements..."):

                    resume_data = process_pdf(uploaded_file)

                    result = analyze_job_match(
                        resume_data["text"],
                        job_description,
                    )

                st.subheader("Job Match Report")
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

    st.title("🧩 Skill Gap Analysis")

    st.write(
        "Identify existing skills, transferable abilities "
        "and areas that may require further development."
    )

    profile_text = st.text_area(
        "Your Background, Education, Experience and Skills",
        value=get_profile_text(),
        height=220,
    )

    target_role = st.text_input(
        "Target Profession / Role",
        placeholder="Example: Project Manager, Nurse, Data Analyst",
    )

    if st.button("Analyze Skill Gaps", type="primary"):

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

    st.title("🗺️ Personalized Learning Roadmap")

    profile_text = st.text_area(
        "Your Current Background",
        value=get_profile_text(),
        height=200,
    )

    career_goal = st.text_input(
        "Your Career Goal",
        placeholder="Example: Become a Civil Engineer",
    )

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

    if st.button("Generate Roadmap", type="primary"):

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

    st.title("🚀 Career Path Explorer")

    st.write(
        "Explore professional pathways based on your "
        "background, interests and transferable skills."
    )

    profile_text = st.text_area(
        "Your Background",
        value=get_profile_text(),
        height=200,
    )

    career_interest = st.text_input(
        "Career Field or Interest",
        placeholder="Example: Healthcare, Finance, Technology, Education",
    )

    if st.button("Explore Career Paths", type="primary"):

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
# INTERVIEW PREPARATION
# =====================================================

elif page == "Interview Preparation":

    st.title("🎤 Interview Preparation")

    target_role = st.text_input(
        "Target Job / Profession",
        placeholder="Example: Software Engineer, Accountant, Teacher",
    )

    experience = st.text_area(
        "Your Experience and Background",
        value=get_profile_text(),
        height=200,
    )

    if st.button("Generate Interview Questions", type="primary"):

        if not target_role.strip() or not experience.strip():

            st.warning(
                "Please provide your target role and background."
            )

        else:

            result = run_analysis(
                prepare_interview,
                target_role,
                experience,
            )

            if result:
                save_result(
                    "interview_preparation",
                    {"target_role": target_role},
                    result,
                )


# =====================================================
# KNOWLEDGE BASE
# =====================================================

elif page == "Knowledge Base":

    st.title("📚 Knowledge Base")

    st.write(
        "Upload career-related documents to build your "
        "retrieval-augmented knowledge base."
    )

    st.info(
        "Supported formats: PDF, TXT and MD. "
        "Scanned PDFs without selectable text are not supported yet."
    )

    uploaded_file = st.file_uploader(
        "Choose a document",
        type=["pdf", "txt", "md"],
        key="knowledge_document_upload",
    )

    if st.button("Upload Document", type="primary"):

        if uploaded_file is None:

            st.warning("Please select a document first.")

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
                st.error(f"Upload failed: {error}")

    st.divider()

    st.subheader("Rebuild Search Index")

    st.write(
        "Rebuild the index after adding or changing knowledge documents."
    )

    if st.button("Rebuild FAISS Index"):

        try:
            with st.spinner(
                "Reading documents, generating embeddings and rebuilding FAISS..."
            ):

                rebuild_vector_store()

            st.success(
                "FAISS knowledge index rebuilt successfully."
            )

        except Exception as error:
            st.error(f"Index rebuilding failed: {error}")


# =====================================================
# MY PROFILE
# =====================================================

elif page == "My Profile":

    st.title("📊 My Career Profile")

    existing_profile = (
        get_profile(st.session_state.user_id) or {}
    )

    with st.form("career_profile_form"):

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

        submitted = st.form_submit_button(
            "Save Career Profile",
            type="primary",
        )

        if submitted:

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

                st.success(
                    "Your career profile has been saved successfully."
                )

            except Exception as error:
                st.error(f"Profile saving failed: {error}")


# =====================================================
# ANALYSIS HISTORY
# =====================================================

elif page == "Analysis History":

    st.title("📚 Analysis History")

    history = get_recent_analyses(
        st.session_state.user_id,
        limit=50,
    )

    if not history:

        st.info("No saved analyses yet.")

    else:

        st.write(
            f"Total saved analyses: {len(history)}"
        )

        for item in history:

            title = (
                item["analysis_type"]
                .replace("_", " ")
                .title()
            )

            timestamp = item["created_at"][:19]

            with st.expander(
                f"{title} — {timestamp}"
            ):

                st.markdown("**Input Information**")

                st.json(item["input_data"])

                st.markdown("**Analysis Result**")

                st.markdown(item["result"])
