from pathlib import Path
import math, uuid, json

def generate_sheet_data(exam, questions):
    uid = uuid.uuid4().hex[:12].upper()
    return {
        "sheet_uid": uid,
        "exam": exam,
        "questions": questions,
        "roll_rows": 6,
        "options": 4
    }

def score_answers(questions, answers, per_question=1, negative=False, deduction=0):
    marks = 0.0
    for q in questions:
        n=str(q["question_no"])
        ans=answers.get(n)
        correct=q["correct_answer"]
        if not ans:
            continue
        if ans == correct:
            marks += per_question
        elif negative:
            marks -= deduction
    return max(0.0, marks)

def confidence_for_bubble(fill_ratio):
    # conservative generic OMR confidence model
    if fill_ratio >= .70: return 0.99
    if fill_ratio >= .55: return .90
    if fill_ratio >= .40: return .70
    return .25