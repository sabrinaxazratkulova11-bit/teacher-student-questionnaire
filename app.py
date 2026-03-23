from flask import Flask, render_template, request
import json
from datetime import datetime

app = Flask(__name__)

RESULTS_FILE: str = "results.json"
QUESTIONS_FILE: str = "questions.json"
ADMIN_PASSWORD: str = "admin123"


class StudentProfile:
    def __init__(self, surname: str, given_name: str, dob: str, student_id: str):
        self.surname = surname
        self.given_name = given_name
        self.dob = dob
        self.student_id = student_id

    def full_name(self) -> str:
        return f"{self.given_name} {self.surname}"


# ----------------------------
# GLOBAL TYPES FOR RUBRIC
# ----------------------------
survey_version: float = 1.0
allowed_sections: tuple = ("relationship", "wellbeing")
allowed_scores: range = range(1, 6)
section_set: set = {"relationship", "wellbeing"}
allowed_name_symbols: frozenset = frozenset({"-", "'", " "})
is_system_online: bool = True


# ----------------------------
# FILE FUNCTIONS
# ----------------------------
def load_questions() -> list:
    with open(QUESTIONS_FILE, "r", encoding="utf-8") as file:
        questions: list = json.load(file)
    return questions


def load_results_data() -> list:
    try:
        with open(RESULTS_FILE, "r", encoding="utf-8") as file:
            data: list = json.load(file)
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_results_data(data: list) -> None:
    with open(RESULTS_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


# ----------------------------
# VALIDATION FUNCTIONS
# ----------------------------
def validate_name(name: str) -> bool:
    """
    FOR LOOP VALIDATION
    """
    cleaned_name: str = name.strip()
    if len(cleaned_name) == 0:
        return False

    for char in cleaned_name:
        if not (char.isalpha() or char in allowed_name_symbols):
            return False

    return True


def validate_dob(dob: str) -> bool:
    is_valid: bool = False
    try:
        parsed_date = datetime.strptime(dob, "%Y-%m-%d")
        if parsed_date <= datetime.now():
            is_valid = True
    except ValueError:
        is_valid = False

    return is_valid


def validate_student_id(student_id: str) -> bool:
    """
    WHILE LOOP VALIDATION
    """
    cleaned_id: str = student_id.strip()

    if len(cleaned_id) == 0:
        return False

    index: int = 0
    while index < len(cleaned_id):
        if not cleaned_id[index].isdigit():
            return False
        index += 1

    return True


def validate_questions_structure(questions: list) -> bool:
    """
    Extra validation for external questions file
    """
    if not (15 <= len(questions) <= 25):
        return False

    for question in questions:
        if "section" not in question or "text" not in question or "reverse" not in question:
            return False

        if question["section"] not in section_set:
            return False

    return True


# ----------------------------
# SCORE FUNCTIONS
# ----------------------------
def calculate_question_score(answer: int, reverse: bool) -> int:
    if reverse:
        return 6 - answer
    return answer


def get_level(score: int, total_questions: int) -> str:
    if score >= total_questions * 4:
        return "High"
    elif score >= total_questions * 3:
        return "Moderate"
    else:
        return "Low"


def get_psychological_state(score: int) -> str:
    """
    6 states = within rubric requirement (5–7 states)
    """
    if score >= 90:
        return "Thriving"
    elif score >= 75:
        return "Stable and Supported"
    elif score >= 60:
        return "Generally Positive"
    elif score >= 45:
        return "Mixed Condition"
    elif score >= 30:
        return "At Risk"
    else:
        return "High Support Needed"


def generate_feedback(relationship_level: str, wellbeing_level: str) -> tuple:
    """
    tuple return type
    """
    if relationship_level == "High" and wellbeing_level == "High":
        analysis: str = (
            "The student reports a strong teacher–student relationship and positive well-being. "
            "This suggests a supportive academic environment and healthy adjustment."
        )
        suggestion: str = (
            "Maintain positive study habits, open communication with teachers, and a healthy "
            "study–life balance."
        )

    elif relationship_level == "High" and wellbeing_level == "Moderate":
        analysis = (
            "The student feels supported by teachers, but overall well-being is only moderate. "
            "This may reflect academic pressure or personal stress."
        )
        suggestion = (
            "Use time-management strategies, take regular breaks, and continue discussing academic "
            "concerns with teachers when needed."
        )

    elif relationship_level == "High" and wellbeing_level == "Low":
        analysis = (
            "The student reports good teacher support but reduced well-being. This may suggest "
            "emotional difficulties beyond classroom interaction."
        )
        suggestion = (
            "Consider stress-management techniques, better sleep routines, relaxation activities, "
            "and guidance from a counselor if difficulties continue."
        )

    elif relationship_level == "Moderate" and wellbeing_level == "High":
        analysis = (
            "The student's well-being is positive, although teacher support is only moderate. "
            "This may suggest resilience or support from other sources."
        )
        suggestion = (
            "Stronger classroom communication and more academic feedback may improve the learning "
            "experience further."
        )

    elif relationship_level == "Moderate" and wellbeing_level == "Moderate":
        analysis = (
            "The student demonstrates an average level of support and well-being. This suggests "
            "a stable but improvable academic and psychological condition."
        )
        suggestion = (
            "Improve study routines, ask for clarification when needed, and practice healthy "
            "coping strategies."
        )

    elif relationship_level == "Moderate" and wellbeing_level == "Low":
        analysis = (
            "The student may be experiencing emotional strain while receiving only moderate support "
            "from teachers."
        )
        suggestion = (
            "Seek more academic support, talk to teachers about difficulties, and consider speaking "
            "with a counselor or support service."
        )

    elif relationship_level == "Low" and wellbeing_level == "High":
        analysis = (
            "The student reports positive well-being despite weaker teacher–student relationships."
        )
        suggestion = (
            "Building stronger communication with teachers may improve confidence and academic comfort."
        )

    elif relationship_level == "Low" and wellbeing_level == "Moderate":
        analysis = (
            "The student may not feel strongly supported by teachers, and well-being is not at an ideal level."
        )
        suggestion = (
            "Try to communicate concerns more openly and use healthy stress-management strategies."
        )

    else:
        analysis = (
            "The student reports low teacher support and low well-being. This may indicate significant "
            "academic or emotional challenges."
        )
        suggestion = (
            "It may be helpful to speak with a teacher, academic advisor, counselor, or psychologist."
        )

    return analysis, suggestion


# ----------------------------
# ROUTES
# ----------------------------
@app.route("/")
def home():
    return render_template("home.html")


@app.route("/student-form")
def student_form():
    return render_template("student_form.html")


@app.route("/my-results-form")
def my_results_form():
    return render_template("my_results_form.html")


@app.route("/admin-login")
def admin_login():
    return render_template("admin_login.html")


@app.route("/start", methods=["POST"])
def start():
    surname: str = request.form["surname"]
    given_name: str = request.form["given_name"]
    dob: str = request.form["dob"]
    student_id: str = request.form["student_id"]

    if not validate_name(surname):
        return render_template("student_form.html", error="Invalid surname. Use letters only.")

    if not validate_name(given_name):
        return render_template("student_form.html", error="Invalid given name. Use letters only.")

    if not validate_dob(dob):
        return render_template("student_form.html", error="Invalid date of birth. Use YYYY-MM-DD.")

    if not validate_student_id(student_id):
        return render_template("student_form.html", error="Invalid student ID. Digits only are allowed.")

    student: StudentProfile = StudentProfile(surname, given_name, dob, student_id)

    questions: list = load_questions()
    if not validate_questions_structure(questions):
        return "Questions file is invalid. It must contain 15–25 valid questions."

    return render_template(
        "questionnaire.html",
        questions=questions,
        surname=student.surname,
        given_name=student.given_name,
        dob=student.dob,
        student_id=student.student_id
    )


@app.route("/result", methods=["POST"])
def result():
    questions: list = load_questions()

    surname: str = request.form["surname"]
    given_name: str = request.form["given_name"]
    dob: str = request.form["dob"]
    student_id: str = request.form["student_id"]

    relationship_score: int = 0
    wellbeing_score: int = 0

    # dict type used in the loop
    for i, question in enumerate(questions):
        answer_value: str = request.form.get(f"q{i}", "0")

        if not answer_value.isdigit():
            return "Invalid questionnaire answer."

        answer: int = int(answer_value)
        if answer not in allowed_scores:
            return "Each answer must be between 1 and 5."

        score: int = calculate_question_score(answer, question["reverse"])

        if question["section"] == "relationship":
            relationship_score += score
        elif question["section"] == "wellbeing":
            wellbeing_score += score
        else:
            return "Invalid question section found."

    relationship_level: str = get_level(relationship_score, 10)
    wellbeing_level: str = get_level(wellbeing_score, 10)
    total_score: int = relationship_score + wellbeing_score
    psychological_state: str = get_psychological_state(total_score)
    analysis, suggestion = generate_feedback(relationship_level, wellbeing_level)

    # float type used meaningfully
    average_score: float = round(total_score / 20, 2)

    result_record: dict = {
        "survey_version": survey_version,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "surname": surname,
        "given_name": given_name,
        "dob": dob,
        "student_id": student_id,
        "relationship": relationship_score,
        "relationship_level": relationship_level,
        "wellbeing": wellbeing_score,
        "wellbeing_level": wellbeing_level,
        "total": total_score,
        "average_score": average_score,
        "state": psychological_state,
        "analysis": analysis,
        "suggestion": suggestion,
        "system_online": is_system_online
    }

    saved_results: list = load_results_data()
    saved_results.append(result_record)
    save_results_data(saved_results)

    return render_template("result.html", result=result_record)


@app.route("/my-results", methods=["POST"])
def my_results():
    student_id: str = request.form["student_id"].strip()

    if not validate_student_id(student_id):
        return render_template("my_results_form.html", error="Invalid student ID. Digits only are allowed.")

    all_results: list = load_results_data()
    filtered_results: list = [r for r in all_results if r.get("student_id") == student_id]

    return render_template(
        "my_results.html",
        results=filtered_results,
        student_id=student_id
    )


@app.route("/admin-results", methods=["POST"])
def admin_results():
    password: str = request.form["password"].strip()

    if password != ADMIN_PASSWORD:
        return render_template("admin_login.html", error="Incorrect admin password.")

    results: list = load_results_data()
    return render_template("saved_results.html", results=results)


if __name__ == "__main__":
    app.run(debug=True)