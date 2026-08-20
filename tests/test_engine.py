from omr_engine.engine import score_answers
def test_score():
    q=[{'question_no':1,'correct_answer':'A'},{'question_no':2,'correct_answer':'B'}]
    assert score_answers(q,{'1':'A','2':'C'},1,False,0)==1
