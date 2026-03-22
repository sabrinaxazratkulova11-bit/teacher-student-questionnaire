from flask import Flask, render_template, request
import json
from datetime import datetime

app = Flask(__name__)

RESULTS_FILE = "results.json"
QUESTIONS_FILE = "questions.json"


class Student:
    def __init__(self, surname, given_name, dob, student_id):
        self.surname = surname
        self.given_name = given_name
        self.dob = dob
        self.student_id = student_id


def load_questions():
    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_name(name):
    if len(name.strip()) == 0:
        return False

    for char in name:
        if not (char.isalpha() or char in ["-", "'", " "]):
            return False

    return True


def validate_dob(dob):
    try:
        date = datetime.strptime(dob, "%Y-%m-%d")
        return date <= datetime.now()
    except ValueError:
        return False


def validate_id(student_id):
    return student_id.isdigit()


def calculate_score(answer, reverse):
    if reverse:
        return 6 - answer
    return answer


def get_level(score, total_questions):
    if score >= total_questions * 4:
        return "High"
    elif score >= total_questions * 3:
        return "Moderate"
    return "Low"


def get_state(score):
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
    return "High Support Needed"


def generate_feedback(relationship_level, wellbeing_level):
    if relationship_level == "High" and wellbeing_level == "High":
        analysis = (
            "The student reports a strong teacher–student relationship and positive well-being. "
            "This suggests a supportive academic environment and healthy adjustment."
        )
        suggestion = (
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


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/student-form")
def student_form():
    return render_template("student_form.html")


@app.route("/start", methods=["POST"])
def start():
    surname = request.form["surname"]
    given_name = request.form["given_name"]
    dob = request.form["dob"]
    student_id = request.form["student_id"]

    if not validate_name(surname):
        return render_template("student_form.html", error="Invalid surname. Use letters only.")

    if not validate_name(given_name):
        return render_template("student_form.html", error="Invalid given name. Use letters only.")

    if not validate_dob(dob):
        return render_template("student_form.html", error="Invalid date of birth. Use YYYY-MM-DD.")

    if not validate_id(student_id):
        return render_template("student_form.html", error="Invalid student ID. Digits only are allowed.")

    student = Student(surname, given_name, dob, student_id)
    questions = load_questions()

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
    questions = load_questions()

    surname = request.form["surname"]
    given_name = request.form["given_name"]
    dob = request.form["dob"]
    student_id = request.form["student_id"]

    relationship_score = 0
    wellbeing_score = 0

    for i, question in enumerate(questions):
        answer = int(request.form.get(f"q{i}", 0))
        score = calculate_score(answer, question["reverse"])

        if question["section"] == "relationship":
            relationship_score += score
        else:
            wellbeing_score += score

    relationship_level = get_level(relationship_score, 10)
    wellbeing_level = get_level(wellbeing_score, 10)
    total_score = relationship_score + wellbeing_score
    state = get_state(total_score)
    analysis, suggestion = generate_feedback(relationship_level, wellbeing_level)

    result_data = {
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
        "state": state,
        "analysis": analysis,
        "suggestion": suggestion
    }

    try:
        with open(RESULTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []

    data.append(result_data)

    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    return render_template("result.html", result=result_data)


@app.route("/load-results")
def load_results():
    try:
        with open(RESULTS_FILE, "r", encoding="utf-8") as f:
            results = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        results = []

    return render_template("saved_results.html", results=results)


if __name__ == "__main__":
    app.run(debug=True)