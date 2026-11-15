
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

from config import GEMINI_API_KEY, GEMINI_MODEL, validate_config
from src.retrieval import retrieve_context
from src.prompts import (
    CAREER_MENTOR_SYSTEM_PROMPT,
    RAG_SYSTEM_PROMPT,
    RESUME_ANALYSIS_PROMPT,
    JOB_MATCH_PROMPT,
    SKILL_GAP_PROMPT,
    ROADMAP_PROMPT,
    INTERVIEW_PROMPT,
    CAREER_PATH_PROMPT
)


def get_llm():
    validate_config()

    return ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        google_api_key=GEMINI_API_KEY,
        timeout=60,
        max_retries=2
    )


def normalize_response(response):
    content = response.content

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts = []

        for item in content:
            if isinstance(item, dict):
                text = item.get("text", "")
                if text:
                    parts.append(text)
            elif isinstance(item, str):
                parts.append(item)

        return "\n".join(parts)

    return str(content)


def generate_response(user_prompt, system_prompt=CAREER_MENTOR_SYSTEM_PROMPT):
    llm = get_llm()

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]

    response = llm.invoke(messages)
    return normalize_response(response)


def ask_career_question(question):
    if not question or not question.strip():
        raise ValueError("Please enter a career question.")

    retrieved = retrieve_context(question)

    prompt = RAG_SYSTEM_PROMPT.format(
        context=retrieved["context"],
        question=question
    )

    answer = generate_response(
        prompt,
        CAREER_MENTOR_SYSTEM_PROMPT
    )

    return {
        "answer": answer,
        "sources": retrieved["sources"]
    }


def analyze_resume(resume_text):
    if not resume_text or not resume_text.strip():
        raise ValueError("Resume text cannot be empty.")

    prompt = RESUME_ANALYSIS_PROMPT.format(
        resume_text=resume_text
    )

    return generate_response(prompt)


def analyze_job_match(resume_text, job_description):
    if not resume_text.strip():
        raise ValueError("Resume text cannot be empty.")

    if not job_description.strip():
        raise ValueError("Job description cannot be empty.")

    prompt = JOB_MATCH_PROMPT.format(
        resume_text=resume_text,
        job_description=job_description
    )

    return generate_response(prompt)


def analyze_skill_gaps(profile, target_role):
    if not target_role.strip():
        raise ValueError("Please enter a target career.")

    prompt = SKILL_GAP_PROMPT.format(
        profile=profile,
        target_role=target_role
    )

    return generate_response(prompt)


def create_learning_roadmap(profile, career_goal, study_time):
    if not career_goal.strip():
        raise ValueError("Please enter a career goal.")

    prompt = ROADMAP_PROMPT.format(
        profile=profile,
        career_goal=career_goal,
        study_time=study_time
    )

    return generate_response(prompt)


def prepare_interview(target_role, experience):
    if not target_role.strip():
        raise ValueError("Please enter a target role.")

    prompt = INTERVIEW_PROMPT.format(
        target_role=target_role,
        experience=experience
    )

    return generate_response(prompt)


def explore_career_path(profile, career_interest):
    if not career_interest.strip():
        raise ValueError("Please enter a career interest.")

    prompt = CAREER_PATH_PROMPT.format(
        profile=profile,
        career_interest=career_interest
    )

    return generate_response(prompt)
