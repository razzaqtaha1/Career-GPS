
import json
import re

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


def generate_response(
    user_prompt,
    system_prompt=CAREER_MENTOR_SYSTEM_PROMPT
):
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
    if not resume_text or not resume_text.strip():
        raise ValueError("Resume text cannot be empty.")

    if not job_description or not job_description.strip():
        raise ValueError("Job description cannot be empty.")

    prompt = JOB_MATCH_PROMPT.format(
        resume_text=resume_text,
        job_description=job_description
    )

    return generate_response(prompt)


def analyze_skill_gaps(profile, target_role):
    if not target_role or not target_role.strip():
        raise ValueError("Please enter a target career.")

    prompt = SKILL_GAP_PROMPT.format(
        profile=profile,
        target_role=target_role
    )

    return generate_response(prompt)


def create_learning_roadmap(profile, career_goal, study_time):
    if not career_goal or not career_goal.strip():
        raise ValueError("Please enter a career goal.")

    prompt = ROADMAP_PROMPT.format(
        profile=profile,
        career_goal=career_goal,
        study_time=study_time
    )

    return generate_response(prompt)


def prepare_interview(target_role, experience):
    if not target_role or not target_role.strip():
        raise ValueError("Please enter a target role.")

    prompt = INTERVIEW_PROMPT.format(
        target_role=target_role,
        experience=experience
    )

    return generate_response(prompt)


def start_mock_interview(
    target_role,
    experience,
    question_number=1,
    previous_questions=None
):
    if not target_role or not target_role.strip():
        raise ValueError("Please enter a target role.")

    previous_questions = previous_questions or []

    prompt = f"""
You are a professional interviewer conducting a realistic job interview.

TARGET ROLE:
{target_role}

CANDIDATE BACKGROUND:
{experience}

QUESTION NUMBER:
{question_number} out of 5

PREVIOUS QUESTIONS:
{previous_questions}

Instructions:
1. Generate exactly ONE interview question.
2. Make it relevant to the target role and candidate background.
3. Adjust difficulty appropriately for the candidate's experience.
4. Do not repeat previous questions.
5. Do not provide the answer, hints, or evaluation.
6. Do not generate multiple questions.
7. Return only the interview question.
"""

    return generate_response(
        prompt,
        "You are an experienced professional interviewer. "
        "Ask one clear interview question at a time."
    )


def evaluate_interview_answer(
    target_role,
    experience,
    question,
    answer
):
    if not answer or not answer.strip():
        raise ValueError("Please submit an interview answer.")

    criteria = [
        "Technical Accuracy",
        "Conceptual Understanding",
        "Problem-Solving Approach",
        "Practical Application",
        "Communication and Clarity",
        "Completeness and Relevance"
    ]

    prompt = f"""
You are a strict, fair, and evidence-based professional interview evaluator.

Evaluate ONLY the candidate's actual submitted answer.

TARGET ROLE:
{target_role}

CANDIDATE BACKGROUND:
{experience}

INTERVIEW QUESTION:
{question}

CANDIDATE ANSWER:
{answer}

EVALUATION RULES:

1. Evaluate only information explicitly demonstrated in the answer.
2. Use the candidate background for context, not as proof of skills.
3. Never invent projects, datasets, algorithms, tools, metrics,
   achievements, responsibilities, or professional experience.
4. Never assume a technique was implemented just because it is
   appropriate for the project.
5. Do not penalize a fresh graduate for lacking professional experience.
6. Distinguish between demonstrated knowledge, unsupported claims,
   and information that was not provided.
7. A correct theoretical explanation is not automatically proof
   of practical implementation.
8. Do not reward technical keywords without meaningful explanation.
9. Evaluate communication based on clarity, structure, relevance,
   and professional language.
10. Do not assume that missing details mean the candidate never
    performed that work.

SCORING CRITERIA:

Score each criterion from 1 to 5:

1. Technical Accuracy
2. Conceptual Understanding
3. Problem-Solving Approach
4. Practical Application
5. Communication and Clarity
6. Completeness and Relevance

SCORING GUIDE:

1 = Incorrect, irrelevant, or almost no demonstrated understanding.
2 = Limited understanding with significant gaps.
3 = Basic acceptable understanding with some missing details.
4 = Good answer with accurate explanations and minor gaps.
5 = Excellent, accurate, detailed, and relevant answer.

SCORING REQUIREMENTS:

- Give every score based on evidence in the actual answer.
- Do not automatically award high marks for good writing.
- Do not automatically give low marks because the candidate
  has no professional experience.
- If practical implementation is not demonstrated, explain
  that limitation without claiming it never happened.
- Avoid penalizing the same weakness unfairly across criteria.

EXAMPLE ANSWER REQUIREMENTS:

- Provide a technically accurate example relevant to the question.
- Never invent the candidate's name or achievements.
- Never invent dataset sizes, accuracy scores, project results,
  algorithms, or implementation details.
- Use only details supported by the supplied information.
- If details are missing, use placeholders such as
  [Insert actual algorithm] or explain what information is needed.
- Never present hypothetical details as candidate achievements.

FOLLOW-UP QUESTION REQUIREMENTS:

- Ask one relevant question about an area not sufficiently
  demonstrated in the submitted answer.
- Do not assume an implementation detail that has not been established.

Return ONLY valid JSON. Do not use Markdown code fences.

Use exactly this structure:

{{
    "scores": {{
        "Technical Accuracy": 1,
        "Conceptual Understanding": 1,
        "Problem-Solving Approach": 1,
        "Practical Application": 1,
        "Communication and Clarity": 1,
        "Completeness and Relevance": 1
    }},
    "overall_assessment": "Evidence-based assessment",
    "what_went_well": [
        "Specific demonstrated strength"
    ],
    "missing_or_incorrect_points": [
        "Specific missing detail or actual inaccuracy"
    ],
    "how_to_improve": [
        "Actionable improvement"
    ],
    "example_strong_answer": "Accurate example without invented achievements",
    "follow_up_question": "One relevant follow-up question"
}}

FINAL VALIDATION:

- All six scores must be integers from 1 to 5.
- Do not include extra scoring criteria.
- Do not invent facts.
- Ensure feedback matches the actual submitted answer.
- Return valid JSON only.
"""

    raw_response = generate_response(
        prompt,
        "You are an objective, evidence-based interview evaluator. "
        "Return valid JSON only. Never fabricate candidate information."
    )

    try:
        cleaned = raw_response.strip()

        cleaned = re.sub(
            r"^```(?:json)?\s*",
            "",
            cleaned,
            flags=re.IGNORECASE
        )

        cleaned = re.sub(r"\s*```$", "", cleaned)

        evaluation = json.loads(cleaned)

    except (json.JSONDecodeError, TypeError, AttributeError):
        raise ValueError(
            "Could not read the AI evaluation. "
            "Please try submitting the answer again."
        )

    if not isinstance(evaluation, dict):
        raise ValueError("AI evaluation must be a JSON object.")

    scores = evaluation.get("scores")

    if not isinstance(scores, dict):
        raise ValueError(
            "AI evaluation did not return a valid scorecard."
        )

    validated_scores = {}

    for criterion in criteria:
        score = scores.get(criterion)

        if (
            isinstance(score, bool)
            or not isinstance(score, (int, float))
        ):
            raise ValueError(f"Invalid score for {criterion}.")

        if not 1 <= score <= 5 or not float(score).is_integer():
            raise ValueError(
                f"Score for {criterion} must be an integer from 1 to 5."
            )

        validated_scores[criterion] = int(score)

    text_fields = [
        "overall_assessment",
        "example_strong_answer",
        "follow_up_question"
    ]

    list_fields = [
        "what_went_well",
        "missing_or_incorrect_points",
        "how_to_improve"
    ]

    for field in text_fields:
        if not isinstance(evaluation.get(field), str):
            raise ValueError(
                f"Invalid or missing evaluation field: {field}"
            )

    for field in list_fields:
        value = evaluation.get(field)

        if (
            not isinstance(value, list)
            or not all(isinstance(item, str) for item in value)
        ):
            raise ValueError(
                f"Invalid or missing evaluation field: {field}"
            )

    total_score = sum(validated_scores.values())

    evaluation["scores"] = validated_scores
    evaluation["total_score"] = total_score
    evaluation["maximum_score"] = 30

    return evaluation


def generate_interview_summary(target_role, evaluations):
    if not evaluations:
        raise ValueError("No interview evaluations are available.")

    criteria = [
        "Technical Accuracy",
        "Conceptual Understanding",
        "Problem-Solving Approach",
        "Practical Application",
        "Communication and Clarity",
        "Completeness and Relevance"
    ]

    total_score = 0
    maximum_score = len(evaluations) * 30
    question_details = []

    for record in evaluations:
        evaluation = record.get("evaluation")

        if not isinstance(evaluation, dict):
            raise ValueError(
                "An interview evaluation is in an old or unsupported format. "
                "Please start a new mock interview before generating the report."
            )

        scores = evaluation.get("scores", {})

        for criterion in criteria:
            score = scores.get(criterion)

            if (
                isinstance(score, bool)
                or not isinstance(score, int)
                or not 1 <= score <= 5
            ):
                raise ValueError(
                    f"Invalid or missing score for {criterion}. "
                    "Please evaluate the interview answers again."
                )

        question_total = sum(scores.values())
        total_score += question_total

        question_details.append({
            "question_number": record.get("question_number"),
            "question": record.get("question", ""),
            "answer": record.get("answer", ""),
            "scores": scores,
            "total_score": question_total,
            "overall_assessment": evaluation.get(
                "overall_assessment", ""
            ),
            "what_went_well": evaluation.get(
                "what_went_well", []
            ),
            "missing_or_incorrect_points": evaluation.get(
                "missing_or_incorrect_points", []
            ),
            "how_to_improve": evaluation.get(
                "how_to_improve", []
            )
        })

    percentage = (total_score / maximum_score) * 100

    criterion_averages = {}

    for criterion in criteria:
        criterion_total = sum(
            item["scores"][criterion]
            for item in question_details
        )

        criterion_averages[criterion] = round(
            criterion_total / len(question_details), 2
        )

    scorecard = "\n".join(
        f"- {criterion}: {average}/5 average"
        for criterion, average in criterion_averages.items()
    )

    prompt = f"""
You are a professional interview assessment specialist.

Prepare a realistic final interview report using ONLY the supplied
questions, candidate answers, and evaluation feedback.

TARGET ROLE:
{target_role}

VERIFIED SCORE SUMMARY (calculated by Python; do not change these values):

Questions evaluated: {len(evaluations)}
Obtained marks: {total_score}
Maximum possible marks: {maximum_score}
Percentage: {percentage:.2f}%

CRITERION AVERAGES:
{scorecard}

ACTUAL INTERVIEW RECORDS:
{json.dumps(question_details, ensure_ascii=False, indent=2)}

Write the report using these sections:

## 1. Interview Overview
Summarize the interview and topics assessed.

## 2. Overall Performance
Explain the verified score and what it indicates.
Do not recalculate, alter, or invent marks.

## 3. Strongest Areas
Identify the strongest criteria and demonstrated skills.

## 4. Areas Requiring Improvement
Identify actual weaknesses from the evaluations.

## 5. Technical Knowledge Assessment
Discuss the technical understanding demonstrated in the answers.

## 6. Communication Assessment
Assess clarity, structure, and relevance based on actual answers.

## 7. Seven-Day Improvement Plan
Create a practical day-by-day plan based on identified weaknesses.

## 8. Final Assessment
Give a realistic assessment of interview readiness for this role.
Distinguish demonstrated knowledge from topics that were not assessed.

Important:
- Use only the supplied evidence.
- Do not invent answers, scores, qualifications, or experience.
- Do not claim professional experience that was not demonstrated.
- Do not describe an answer as empty or irrelevant unless its
  actual content supports that conclusion.
- Do not treat unassessed skills as proven weaknesses.
- Be constructive and specific.
- Do not change the verified score summary.
"""

    qualitative_report = generate_response(
        prompt,
        "You are a professional interview assessment specialist. "
        "Write evidence-based reports and never fabricate candidate performance."
    )

    verified_score = (
        f"## Verified Interview Score\n\n"
        f"**Obtained Marks:** {total_score}/{maximum_score}\n\n"
        f"**Percentage:** {percentage:.2f}%\n\n"
        f"**Questions Evaluated:** {len(evaluations)}\n\n"
        f"### Criterion Averages\n\n{scorecard}\n\n"
        f"---\n\n"
    )

    return verified_score + qualitative_report


def explore_career_path(profile, career_interest):
    if not career_interest or not career_interest.strip():
        raise ValueError("Please enter a career interest.")

    prompt = CAREER_PATH_PROMPT.format(
        profile=profile,
        career_interest=career_interest
    )

    return generate_response(prompt)
