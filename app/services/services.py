import csv, json, hashlib
from datetime import datetime
from pathlib import Path
from app.infrastructure.database import query, execute, connect
from omr_engine.engine import score_answers

def now(): return datetime.now().isoformat(timespec="seconds")

def school():
    r=query("SELECT * FROM school WHERE id=1"); return dict(r[0]) if r else {}

def save_school(data):
    try:
        fields = ["name","phone","email","address1","address2","country","state","city","pincode","logo_path"]
        values = tuple(data.get(k,"") for k in fields)
        execute("""UPDATE school SET name=?,phone=?,email=?,address1=?,address2=?,country=?,state=?,city=?,pincode=?,logo_path=? WHERE id=1""",values)
        return True
    except Exception as e:
        print(f"Error saving school: {e}")
        return False

def students(search=""):
    if search:
        q=f"%{search}%"
        return [dict(r) for r in query("""SELECT * FROM students WHERE student_code LIKE ? OR first_name LIKE ? OR last_name LIKE ? ORDER BY student_code""",(q,q,q))]
    return [dict(r) for r in query("SELECT * FROM students ORDER BY student_code")]

def add_student(d):
    try:
        if not d.get("student_code"):
            raise ValueError("Student code is required")
        return execute("""INSERT INTO students(student_code,first_name,last_name,phone,class_name,section,email,created_at)
                          VALUES(?,?,?,?,?,?,?,?)""",
                       (d["student_code"],d.get("first_name",""),d.get("last_name",""),d.get("phone",""),
                        d.get("class_name",""),d.get("section",""),d.get("email",""),now()))
    except Exception as e:
        print(f"Error adding student: {e}")
        raise

def import_students(path):
    path=Path(path); rows=[]; ok=bad=0
    try:
        with path.open(newline="",encoding="utf-8-sig") as f:
            reader=csv.DictReader(f)
            for row in reader:
                try:
                    student_code = row.get("ID") or row.get("student_code") or row.get("Roll Number")
                    if not student_code:
                        bad+=1; rows.append((row,"Missing student code")); continue
                    add_student({
                        "student_code": student_code,
                        "first_name": row.get("First Name") or row.get("first_name") or "",
                        "last_name": row.get("Last Name") or row.get("last_name") or "",
                        "phone": row.get("Phone number") or row.get("phone") or "",
                        "class_name": row.get("Class") or row.get("class_name") or "",
                        "section": row.get("Section") or row.get("section") or "",
                        "email": row.get("Email") or row.get("email") or ""
                    }); ok+=1
                except Exception as e: 
                    bad+=1; rows.append((row,str(e)))
        execute("INSERT INTO imports(file_name,imported_at,total,success,failed) VALUES(?,?,?,?,?)",(path.name,now(),ok+bad,ok,bad))
    except Exception as e:
        print(f"Error importing CSV: {e}")
    return ok,bad

def examinations():
    return [dict(r) for r in query("SELECT * FROM examinations ORDER BY id DESC")]

def create_exam(d, questions):
    try:
        if not d.get("name"):
            raise ValueError("Examination name is required")
        if not questions:
            raise ValueError("At least one question is required")
        eid=execute("""INSERT INTO examinations(name,session,class_name,section,subject,exam_date,template_id,per_question,negative_marking,negative_deduction,total_questions,status,created_at)
                       VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (d["name"],d.get("session",""),d.get("class_name",""),d.get("section",""),d.get("subject",""),
                     d.get("exam_date",""),d.get("template_id","TPL-02"),d.get("per_question",1),
                     int(d.get("negative_marking",False)),d.get("negative_deduction",0),len(questions),"Ready",now()))
        con=connect()
        for i,q in enumerate(questions,1):
            con.execute("INSERT INTO questions(exam_id,question_no,question_text,options_json,correct_answer,marks) VALUES(?,?,?,?,?,?)",
                        (eid,i,q.get("text",""),json.dumps(q.get("options",[])),q.get("correct",""),d.get("per_question",1)))
        con.commit(); con.close()
        return eid
    except Exception as e:
        print(f"Error creating exam: {e}")
        raise

def get_questions(exam_id):
    return [dict(r) for r in query("SELECT * FROM questions WHERE exam_id=? ORDER BY question_no",(exam_id,))]

def add_sheet(exam_id, roll, image_path="", status="Pending", answers=None, confidence=None):
    try:
        if not exam_id or not roll:
            raise ValueError("Exam ID and roll number are required")
        return execute("""INSERT INTO omr_sheets(exam_id,sheet_uid,roll_number,image_path,scan_status,confidence,recognized_answers_json,scanned_at)
                          VALUES(?,?,?,?,?,?,?,?)""",
                       (exam_id,hashlib.sha1(f"{exam_id}-{roll}-{now()}".encode()).hexdigest()[:12].upper(),roll,
                        image_path,status,confidence or 0.0,json.dumps(answers or {}),now()))
    except Exception as e:
        print(f"Error adding sheet: {e}")
        raise

def evaluate_exam(exam_id):
    try:
        ex=query("SELECT * FROM examinations WHERE id=?",(exam_id,))
        if not ex:
            raise ValueError(f"Examination {exam_id} not found")
        ex=ex[0]
        qs=get_questions(exam_id)
        sheets=query("SELECT * FROM omr_sheets WHERE exam_id=?",(exam_id,))
        if not sheets:
            raise ValueError("No OMR sheets found for evaluation")
        eval_count=0
        for s in sheets:
            stu=query("SELECT * FROM students WHERE student_code=?",(s["roll_number"],))
            if not stu: continue
            answers=json.loads(s["recognized_answers_json"] or "{}")
            auto=score_answers(qs,answers,ex["per_question"],bool(ex["negative_marking"]),ex["negative_deduction"])
            execute("""INSERT INTO evaluations(exam_id,student_id,sheet_id,automatic_marks,final_marks,status)
                       VALUES(?,?,?,?,?,?)""",
                   (exam_id,stu[0]["id"],s["id"],auto,auto,"Pending Review" if s["scan_status"]!="Success" else "Evaluated"))
            eval_count+=1
        execute("UPDATE examinations SET status='Evaluated' WHERE id=?",(exam_id,))
        print(f"Successfully evaluated {eval_count} sheets for exam {exam_id}")
    except Exception as e:
        print(f"Error evaluating exam: {e}")
        raise

def results(exam_id):
    return [dict(r) for r in query("""SELECT e.*,s.student_code,s.first_name,s.last_name,s.class_name,s.section
        FROM evaluations e JOIN students s ON s.id=e.student_id WHERE e.exam_id=? ORDER BY s.student_code""",(exam_id,))]

def grade_for(pct):
    rows=query("SELECT * FROM grades ORDER BY min_pct DESC")
    for r in rows:
        if r["min_pct"] <= pct <= r["max_pct"]: return r["name"]
    return ""

def audit(username, student, exam, q, old, new, oldm, newm, reason):
    execute("""INSERT INTO audit_log(username,event_time,student,examination,question_no,old_value,new_value,old_marks,new_marks,reason)
               VALUES(?,?,?,?,?,?,?,?,?,?)""",(username,now(),student,exam,q,old,new,oldm,newm,reason))