import sys, csv, json
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import *
from PySide6.QtGui import QPixmap, QColor, QFont
from app.infrastructure.database import init_db, query, execute
from app.services import services
from omr_engine.pdf import generate_omr_pdf

NAV=["Dashboard","School Setup","OMR Templates","Examinations","OMR Scanning","Evaluation","Results","Marksheets","Communication","Grade Configuration","Audit Log","Settings"]

class Main(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle("OMR Examination Management System"); self.resize(1280,820); self.setMinimumSize(1100,720)
        self.current_exam=None; self.build(); self.open_page("Dashboard")

    def build(self):
        root=QWidget()
        lay=QVBoxLayout(root)
        lay.setContentsMargins(0,0,0,0)
        lay.setSpacing(0)

        body=QWidget(); bl=QHBoxLayout(body); bl.setContentsMargins(0,0,0,0); bl.setSpacing(0)

        side=QFrame(); side.setObjectName("sidebar"); side.setFixedWidth(264)
        sl=QVBoxLayout(side); sl.setContentsMargins(18,22,18,18); sl.setSpacing(4)

        mark=QLabel("O"); mark.setObjectName("appmark")
        logo=QLabel("OMR Suite"); logo.setObjectName("brand")
        brandrow=QHBoxLayout(); brandrow.setSpacing(10); brandrow.addWidget(mark); brandrow.addWidget(logo); brandrow.addStretch()
        sl.addLayout(brandrow)
        sub=QLabel("Sunrise Public School\nAcademic year 2025–26"); sub.setObjectName("schoollabel")
        sl.addWidget(sub); sl.addSpacing(18)

        self.nav={}
        for n in NAV:
            b=QPushButton(n); b.setObjectName("nav")
            b.clicked.connect(lambda _,x=n:self.open_page(x))
            sl.addWidget(b); self.nav[n]=b

        sl.addStretch()
        local=QLabel("v1.0.0  ·  Local desktop"); local.setObjectName("sidefooter"); sl.addWidget(local)
        bl.addWidget(side)

        right=QWidget()
        right_l=QVBoxLayout(right); right_l.setContentsMargins(0,0,0,0); right_l.setSpacing(0)

        head=QFrame(); head.setObjectName("header"); head.setFixedHeight(92)
        hl=QHBoxLayout(head); hl.setContentsMargins(32,16,32,14); hl.setSpacing(18)
        titlebox=QVBoxLayout(); titlebox.setSpacing(4)
        self.title=QLabel("Dashboard"); self.title.setObjectName("title")
        self.subtitle=QLabel("Overview of the current academic session"); self.subtitle.setObjectName("subtitle")
        titlebox.addWidget(self.title); titlebox.addWidget(self.subtitle)
        hl.addLayout(titlebox); hl.addStretch()
        for text in ["Online","Scanner connected","Licence active"]:
            status=QLabel(text); status.setObjectName("statuspill"); hl.addWidget(status)
        user=QLabel("Administrator"); user.setObjectName("userpill"); hl.addWidget(user)
        right_l.addWidget(head)

        self.content=QStackedWidget(); self.content.setObjectName("content")
        right_l.addWidget(self.content,1)

        foot=QLabel("Sunrise Public School · AY 2025–26 · Administrator · Scanner connected · Licence active")
        foot.setObjectName("footer"); right_l.addWidget(foot)
        bl.addWidget(right,1)

        lay.addWidget(body,1)
        self.setCentralWidget(root)

    def page(self):
        w=QWidget(); w.setObjectName("page")
        l=QVBoxLayout(w); l.setContentsMargins(32,28,32,24); l.setSpacing(16); return w,l

    def open_page(self,name):
        subtitles={
            "Dashboard":"Overview of the current academic session",
            "School Setup":"Profile, faculty and student records",
            "OMR Templates":"Select and configure the answer-sheet layout",
            "Examinations":"Create and manage examinations",
            "OMR Scanning":"Scan answer sheets with the connected scanner",
            "Evaluation":"Automatic evaluation and manual review",
            "Results":"Final review and result finalisation",
            "Marksheets":"Generate, preview and print marksheets",
            "Communication":"Distribute results over WhatsApp and Email",
            "Grade Configuration":"Grade bands used for marksheets",
            "Audit Log":"Traceability of every manual correction",
            "Settings":"Application-level configuration"
        }
        self.title.setText(name)
        self.subtitle.setText(subtitles.get(name,""))
        for n,b in self.nav.items():
            b.setProperty("active", n==name)
            b.style().unpolish(b); b.style().polish(b)
        while self.content.count():
            widget=self.content.widget(0); self.content.removeWidget(widget); widget.deleteLater()
        builders={"Dashboard":self.dashboard,"School Setup":self.school,"OMR Templates":self.templates,"Examinations":self.exams,
                  "OMR Scanning":self.scanning,"Evaluation":self.evaluation,"Results":self.results_page,"Marksheets":self.marksheets,
                  "Communication":self.communication,"Grade Configuration":self.grades,"Audit Log":self.audit,"Settings":self.settings}
        w=builders[name](); self.content.addWidget(w); self.content.setCurrentWidget(w)

    def header(self,l,title,sub=""):
        return

    def card(self,title,value,sub):
        f=QFrame(); f.setObjectName("card"); x=QVBoxLayout(f); x.addWidget(QLabel(title)); v=QLabel(str(value)); v.setObjectName("value"); x.addWidget(v); x.addWidget(QLabel(sub)); return f

    def polish_table(self,t, editable=False):
        t.verticalHeader().setVisible(False)
        t.setAlternatingRowColors(True)
        t.setShowGrid(False)
        t.setSelectionBehavior(QAbstractItemView.SelectRows)
        t.setEditTriggers(QAbstractItemView.DoubleClicked|QAbstractItemView.EditKeyPressed if editable else QAbstractItemView.NoEditTriggers)
        t.setWordWrap(False)
        t.verticalHeader().setDefaultSectionSize(44)
        t.horizontalHeader().setMinimumHeight(42)
        return t

    def dashboard(self):
        w,l=self.page()
        g=QGridLayout(); g.setHorizontalSpacing(16); g.setVerticalSpacing(16)
        ex=services.examinations(); st=services.students()
        scanned_count=sum(1 for e in ex if e["status"] in ("Ready","Evaluated"))
        evaluated_count=sum(1 for e in ex if e["status"]=="Evaluated")
        completed_count=sum(1 for e in ex if e["status"]=="Completed")
        stats=[
            ("Total examinations",len(ex),"Created in this workspace","#23313d"),
            ("Pending evaluation",max(scanned_count-evaluated_count,0),"Sheets waiting for review","#c05a1a"),
            ("Completed",completed_count,"Results finalised","#117a56"),
            ("Students",len(st),"Active student records","#415365")
        ]
        for i,x in enumerate(stats): g.addWidget(self.dashboard_card(*x),0,i)
        l.addLayout(g)

        qa=QFrame(); qa.setObjectName("quickpanel")
        ql=QHBoxLayout(qa); ql.setContentsMargins(18,14,18,14); ql.setSpacing(12)
        labelbox=QVBoxLayout(); labelbox.setSpacing(2)
        qtitle=QLabel("Quick actions"); qtitle.setObjectName("paneltitle")
        qsub=QLabel("Common workflows"); qsub.setObjectName("panelsubtitle")
        labelbox.addWidget(qtitle); labelbox.addWidget(qsub); ql.addLayout(labelbox); ql.addStretch()
        actions=[("New exam","OMR Templates"),("Generate OMR","Examinations"),("Scan sheets","OMR Scanning"),("Evaluate","Evaluation"),("Marksheets","Marksheets")]
        for txt,page in actions:
            b=QPushButton(txt); b.setObjectName("quickaction"); b.clicked.connect(lambda _,p=page:self.open_page(p)); ql.addWidget(b)
        l.addWidget(qa)

        container=QHBoxLayout(); container.setSpacing(18)
        left=QFrame(); left.setObjectName("panel"); left_l=QVBoxLayout(left); left_l.setContentsMargins(18,16,18,18); left_l.setSpacing(12)
        title=QLabel("Recent examinations"); title.setObjectName("paneltitle"); left_l.addWidget(title)
        t=QTableWidget(len(ex),6); t.setObjectName("dashboardtable"); t.setHorizontalHeaderLabels(["Examination","Class","Date","Status","Marks","Action"])
        t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); t.horizontalHeader().setSectionResizeMode(0,QHeaderView.ResizeToContents)
        self.polish_table(t)
        status_colors={"scanned":"#117a56","completed":"#117a56","evaluated":"#2368a2","scheduled":"#667085","draft":"#8a3a3a","ready":"#c05a1a"}
        for r,e in enumerate(ex):
            vals=[e["name"],e["class_name"],e["exam_date"],e["status"],"—","→"]
            for c,v in enumerate(vals): 
                item=QTableWidgetItem(str(v))
                if c==3:
                    status_key=e["status"].lower().replace(" ","_")
                    color=status_colors.get(status_key,"#2a2825")
                    item.setForeground(QColor(color))
                    font=QFont(); font.setBold(True); item.setFont(font)
                t.setItem(r,c,item)
        if not ex:
            t.setRowCount(1)
            empty=QTableWidgetItem("No examinations yet. Create one to begin.")
            t.setItem(0,0,empty)
        left_l.addWidget(t); container.addWidget(left,1)

        right=QFrame(); right.setObjectName("panel"); right.setMinimumWidth(300); right.setMaximumWidth(360)
        right_l=QVBoxLayout(right); right_l.setContentsMargins(18,16,18,18); right_l.setSpacing(12)
        summary_title=QLabel("Examination summary"); summary_title.setObjectName("paneltitle"); right_l.addWidget(summary_title)
        total_sheets=(query("SELECT COUNT(*) c FROM omr_sheets") or [{"c":0}])[0]["c"]
        scanned_sheets=(query("SELECT COUNT(*) c FROM omr_sheets WHERE scan_status!='Pending'") or [{"c":0}])[0]["c"]
        evaluated=(query("SELECT COUNT(*) c FROM evaluations") or [{"c":0}])[0]["c"]
        manual_review=(query("SELECT COUNT(*) c FROM evaluations WHERE status LIKE '%Review%'") or [{"c":0}])[0]["c"]
        finalised=(query("SELECT COUNT(*) c FROM evaluations WHERE finalized=1") or [{"c":0}])[0]["c"]
        dispatched=(query("SELECT COUNT(*) c FROM distributions WHERE status='Sent'") or [{"c":0}])[0]["c"]
        sheet_denominator=total_sheets or len(st) or 0
        summary_data=[
            ("Scanned",f"{scanned_sheets} / {sheet_denominator}","#117a56"),
            ("Evaluated",f"{evaluated} / {sheet_denominator}","#2368a2"),
            ("Manual review",str(manual_review),"#c05a1a"),
            ("Finalised",str(finalised),"#23313d"),
            ("Dispatched",str(dispatched),"#667085")
        ]
        for label,value,color in summary_data:
            row_w=QWidget(); row_w.setObjectName("summaryrow"); row_l=QHBoxLayout(row_w); row_l.setContentsMargins(0,6,0,6)
            lbl=QLabel(label); lbl.setObjectName("summary_label"); row_l.addWidget(lbl)
            row_l.addStretch()
            val=QLabel(value); val.setObjectName("summary_value"); val.setStyleSheet(f"color:{color};"); row_l.addWidget(val)
            right_l.addWidget(row_w)
        progress=QProgressBar(); progress.setRange(0,max(sheet_denominator,1)); progress.setValue(min(evaluated,max(sheet_denominator,1))); progress.setTextVisible(False); right_l.addWidget(progress)
        right_l.addStretch(); container.addWidget(right,0)
        l.addLayout(container,1); return w
    
    def dashboard_card(self,title,value,sub,color="#2a2825"):
        f=QFrame(); f.setObjectName("dashcard"); f.setMinimumHeight(128)
        x=QVBoxLayout(f); x.setContentsMargins(18,16,18,16); x.setSpacing(8)
        t=QLabel(title); t.setObjectName("card_title"); x.addWidget(t)
        v=QLabel(str(value)); v.setObjectName("card_value"); v.setStyleSheet(f"color: {color};"); x.addWidget(v)
        s=QLabel(sub); s.setObjectName("card_subtitle"); x.addWidget(s)
        x.addStretch()
        return f

    def school(self):
        w,l=self.page(); self.header(l,"School Setup","Profile, faculty and student records"); tabs=QTabWidget()
        f=QWidget(); form=QFormLayout(f); s=services.school(); edits={}
        for k,label in [("name","School Name"),("phone","Phone Number"),("email","Email ID"),("address1","Address line1"),("address2","Address line2"),("country","Country"),("state","State"),("city","City"),("pincode","Pincode")]:
            e=QLineEdit(s.get(k,"")); edits[k]=e; form.addRow(label,e)
        save=QPushButton("Save School Profile"); save.clicked.connect(lambda: (services.save_school({k:e.text() for k,e in edits.items()}), QMessageBox.information(self,"Saved","School profile saved."))); form.addRow(save); tabs.addTab(f,"School Profile")
        fac=QWidget(); fl=QVBoxLayout(fac); add=QPushButton("+ Add Faculty"); add.clicked.connect(lambda:self.faculty_dialog()); fl.addWidget(add); self.faculty_table=QTableWidget(); self.refresh_faculty(); fl.addWidget(self.faculty_table); tabs.addTab(fac,"Faculty")
        stu=QWidget(); sl=QVBoxLayout(stu); rr=QHBoxLayout(); add=QPushButton("+ Add Student"); add.clicked.connect(self.student_dialog); imp=QPushButton("Bulk Import CSV"); imp.clicked.connect(self.import_csv); rr.addWidget(add); rr.addWidget(imp); rr.addStretch(); sl.addLayout(rr)
        self.student_table=QTableWidget(); self.refresh_students(); sl.addWidget(self.student_table); tabs.addTab(stu,"Students"); l.addWidget(tabs,1); return w

    def refresh_faculty(self):
        if not hasattr(self,"faculty_table"): return
        rows=query("SELECT * FROM users WHERE role='Faculty'")
        self.faculty_table.setRowCount(len(rows)); self.faculty_table.setColumnCount(5)
        self.faculty_table.setHorizontalHeaderLabels(["Name","Email","Phone","Role","Status"])
        self.faculty_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.polish_table(self.faculty_table)
        for r,x in enumerate(rows):
            for c,v in enumerate([f"{x['first_name']} {x['last_name']}",x["email"],x["phone"],x["role"],"Active" if x["active"] else "Inactive"]):
                self.faculty_table.setItem(r,c,QTableWidgetItem(str(v)))

    def refresh_students(self):
        if not hasattr(self,"student_table"): return
        rows=services.students(); self.student_table.setRowCount(len(rows)); self.student_table.setColumnCount(7); self.student_table.setHorizontalHeaderLabels(["ID","First Name","Last Name","Phone","Class","Section","Email"]); self.student_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); self.polish_table(self.student_table)
        for r,x in enumerate(rows):
            for c,v in enumerate([x["student_code"],x["first_name"],x["last_name"],x["phone"],x["class_name"],x["section"],x["email"]]): self.student_table.setItem(r,c,QTableWidgetItem(str(v)))

    def faculty_dialog(self):
        d=QDialog(self); d.setWindowTitle("Add Faculty"); f=QFormLayout(d); e={}
        for k in ["First Name","Last Name","Phone","Email","Username","Password"]:
            e[k]=QLineEdit(); e[k].setEchoMode(QLineEdit.Password if k=="Password" else QLineEdit.Normal); f.addRow(k,e[k])
        b=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel); f.addRow(b)
        def save_fac():
            try:
                if not e["First Name"].text():
                    QMessageBox.warning(d,"Error","First Name is required")
                    return
                if not e["Username"].text():
                    QMessageBox.warning(d,"Error","Username is required")
                    return
                execute("INSERT INTO users(username,password_hash,role,first_name,last_name,phone,email,created_at) VALUES(?,?,?,?,?,?,?,?)",
                       (e["Username"].text(),e["Password"].text(),"Faculty",e["First Name"].text(),e["Last Name"].text(),e["Phone"].text(),e["Email"].text(),services.now()))
                d.accept()
                QMessageBox.information(self,"Saved",f"Faculty {e['First Name'].text()} {e['Last Name'].text()} added successfully.")
                self.refresh_faculty()
            except Exception as ex:
                QMessageBox.warning(d,"Error",str(ex))
        b.accepted.connect(save_fac); b.rejected.connect(d.reject); d.exec()

    def student_dialog(self):
        d=QDialog(self); d.setWindowTitle("Add Student"); f=QFormLayout(d); e={}
        for k in ["ID","First Name","Last Name","Phone","Class","Section","Email"]: e[k]=QLineEdit(); f.addRow(k,e[k])
        b=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel); f.addRow(b)
        def save():
            try:
                if not e["ID"].text():
                    QMessageBox.warning(d,"Error","Student ID is required")
                    return
                services.add_student({
                    "student_code":e["ID"].text(),"first_name":e["First Name"].text(),"last_name":e["Last Name"].text(),
                    "phone":e["Phone"].text(),"class_name":e["Class"].text(),"section":e["Section"].text(),"email":e["Email"].text()
                })
                d.accept()
                QMessageBox.information(self,"Success",f"Student {e['First Name'].text()} {e['Last Name'].text()} added successfully.")
                self.refresh_students()
            except Exception as ex:
                QMessageBox.warning(d,"Error",f"Failed to add student:\n{str(ex)}")
        b.accepted.connect(save); b.rejected.connect(d.reject); d.exec()

    def import_csv(self):
        p,_=QFileDialog.getOpenFileName(self,"Select CSV","","CSV Files (*.csv)")
        if p:
            try:
                ok,bad=services.import_students(p)
                QMessageBox.information(self,"Import Complete",f"Successfully Imported: {ok}\nFailed: {bad}")
                self.refresh_students()
            except Exception as ex:
                QMessageBox.warning(self,"Import Error",f"Failed to import CSV:\n{str(ex)}")

    def templates(self):
        w,l=self.page(); self.header(l,"OMR Templates","Select and configure the answer-sheet layout")
        group=QGroupBox("Available Templates"); gl=QHBoxLayout(group)
        for tid,txt in [("TPL-01","A4 · 50 Questions · 4 Options"),("TPL-02","A4 · 100 Questions · 4 Options"),("TPL-03","A4 · 100 Questions · 5 Options")]:
            f=QFrame(); f.setObjectName("card"); x=QVBoxLayout(f); x.addWidget(QLabel(tid)); x.addWidget(QLabel(txt)); b=QPushButton("Select"); b.clicked.connect(lambda _,i=tid:self.select_template(i)); x.addWidget(b); gl.addWidget(f)
        l.addWidget(group); p=QGroupBox("OMR Customization"); pl=QVBoxLayout(p)
        for text in ["Show School Name","Show School Logo","Student Roll Number","Test Booklet No"]:
            cb=QCheckBox(text); cb.setChecked(True); pl.addWidget(cb)
        l.addWidget(p); b=QPushButton("Next → Create Examination"); b.clicked.connect(lambda:self.open_page("Examinations")); l.addWidget(b); l.addStretch(); return w

    def select_template(self,tid): self.selected_template=tid; QMessageBox.information(self,"Template Selected",tid+" selected.")

    def exams(self):
        w,l=self.page(); self.header(l,"Examinations","Create and manage examinations"); b=QPushButton("+ New Examination"); b.clicked.connect(self.exam_dialog); l.addWidget(b,alignment=Qt.AlignRight)
        rows=services.examinations(); t=QTableWidget(len(rows),7); t.setHorizontalHeaderLabels(["Name","Class","Section","Subject","Date","Questions","Status"]); t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); self.polish_table(t)
        for r,e in enumerate(rows):
            for c,v in enumerate([e["name"],e["class_name"],e["section"],e["subject"],e["exam_date"],e["total_questions"],e["status"]]): t.setItem(r,c,QTableWidgetItem(str(v)))
        t.cellDoubleClicked.connect(lambda r,c:self.choose_exam(rows[r]["id"])); l.addWidget(t,1); return w

    def exam_dialog(self):
        d=QDialog(self); d.setWindowTitle("Create Examination"); d.resize(850,620); l=QVBoxLayout(d); tabs=QTabWidget()
        f=QWidget(); form=QFormLayout(f); e={}
        for k,v in [("name","Unit Test II — Mathematics"),("session","2025–26"),("class_name","X"),("section","A"),("subject","Mathematics"),("exam_date","2026-08-24"),("per_question","1"),("negative_deduction","0.25")]:
            e[k]=QLineEdit(v); form.addRow(k.replace("_"," ").title(),e[k])
        neg=QCheckBox("Enable Negative Marking"); form.addRow(neg); tabs.addTab(f,"1. Examination Details")
        q=QWidget(); ql=QVBoxLayout(q); self.qtable=QTableWidget(3,7); self.qtable.setHorizontalHeaderLabels(["#","Question","A","B","C","D","Correct"])
        qs=[("The value of √144 is","10","11","12","14","C"),("If 3x + 5 = 20, x equals","3","5","7","15","B"),("Triangle angle sum is","90","180","270","360","B")]
        for r,row in enumerate(qs):
            vals=[r+1,*row]
            for c,v in enumerate(vals): self.qtable.setItem(r,c,QTableWidgetItem(str(v)))
        self.qtable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); self.polish_table(self.qtable, editable=True); ql.addWidget(self.qtable); addq=QPushButton("Add Question"); addq.clicked.connect(lambda:self.qtable.insertRow(self.qtable.rowCount())); ql.addWidget(addq); tabs.addTab(q,"2. Question Creation")
        m=QWidget(); ml=QFormLayout(m); ml.addRow("Maximum Marks",QLabel("Calculated from questions")); ml.addRow("Negative Marking",neg); tabs.addTab(m,"3. Marks Configuration")
        prev=QWidget(); pv=QVBoxLayout(prev); pv.addWidget(QLabel("OMR Preview")); pv.addWidget(QLabel("School Name\nExamination Name\n\nRoll Number: 0 1 2 3 4 5 6 7 8 9\n\nQ1   ○ A   ○ B   ○ C   ○ D\nQ2   ○ A   ○ B   ○ C   ○ D\nQ3   ○ A   ○ B   ○ C   ○ D")); tabs.addTab(prev,"4. OMR Preview")
        l.addWidget(tabs,1); b=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel); l.addWidget(b)
        def save():
            questions=[]
            for r in range(self.qtable.rowCount()):
                def val(c): return self.qtable.item(r,c).text() if self.qtable.item(r,c) else ""
                q_text,q_opts,q_correct=val(1),[val(2),val(3),val(4),val(5)],val(6)
                if q_text and q_correct:
                    questions.append({"text":q_text,"options":q_opts,"correct":q_correct})
            if not questions:
                QMessageBox.warning(d,"Error","Please add at least one question with correct answer.")
                return
            try:
                exam_data={
                    "name":e["name"].text(),"session":e["session"].text(),"class_name":e["class_name"].text(),
                    "section":e["section"].text(),"subject":e["subject"].text(),"exam_date":e["exam_date"].text(),
                    "template_id":getattr(self,"selected_template","TPL-02"),"per_question":float(e["per_question"].text() or 1),
                    "negative_marking":neg.isChecked(),"negative_deduction":float(e["negative_deduction"].text() or 0)
                }
                eid=services.create_exam(exam_data,questions)
                self.current_exam=eid; d.accept(); QMessageBox.information(self,"Created",f"Examination created.\nID: {eid}\nQuestions: {len(questions)}")
            except Exception as ex: QMessageBox.warning(d,"Error",f"Failed to create exam:\n{str(ex)}")
        b.accepted.connect(save); b.rejected.connect(d.reject); d.exec()

    def choose_exam(self,eid): self.current_exam=eid; QMessageBox.information(self,"Examination Selected",f"Exam {eid} selected for scanning/evaluation.")

    def scanning(self):
        w,l=self.page(); self.header(l,"OMR Scanning","Read physical OMR sheets and prepare recognition")
        if not self.current_exam:
            ex=services.examinations()
            if ex: self.current_exam=ex[0]["id"]
        exs=services.examinations(); combo=QComboBox(); combo.addItems([f'{e["id"]} · {e["name"]}' for e in exs]); l.addWidget(combo)
        row=QHBoxLayout(); folder=QPushButton("Import Scanned Images"); folder.clicked.connect(lambda:self.import_scans(combo.currentData() or (exs[combo.currentIndex()]["id"] if exs else None))); row.addWidget(folder)
        start=QPushButton("Start Scan"); start.clicked.connect(lambda:QMessageBox.information(self,"Scanner","For production hardware, connect the supported TWAIN/WIA scanner. This build also supports importing scanned image files for recognition/testing.")); row.addWidget(start); l.addLayout(row)
        l.addWidget(QLabel("Scan Summary")); l.addWidget(QLabel("Expected Sheets • Scanned Sheets • Successfully Scanned • Manual Review Required")); return w

    def import_scans(self,eid):
        if not eid:
            QMessageBox.warning(self,"Error","No examination selected")
            return
        files,_=QFileDialog.getOpenFileNames(self,"Select scanned OMR images","","Images (*.png *.jpg *.jpeg *.bmp)")
        if not files:
            return
        imported=failed=0
        for p in files:
            try:
                roll=Path(p).stem.split("_")[0]
                if not roll:
                    failed+=1; continue
                services.add_sheet(eid,roll,p,"Review Required",{},0.25)
                imported+=1
            except Exception as e:
                failed+=1; print(f"Error importing {p}: {e}")
        QMessageBox.information(self,"Imported",f"Successfully imported: {imported}\nFailed: {failed}\nLow-confidence sheets marked for manual review.")

    def evaluation(self):
        w,l=self.page(); self.header(l,"Evaluation","Automatic evaluation and manual review")
        exs=services.examinations(); combo=QComboBox(); combo.addItems([f'{e["id"]} · {e["name"]}' for e in exs]); l.addWidget(combo)
        run=QPushButton("Run Automatic Evaluation"); run.clicked.connect(lambda:self.run_eval(exs[combo.currentIndex()]["id"] if exs else None)); l.addWidget(run,alignment=Qt.AlignRight)
        t=QTableWidget(); t.setColumnCount(7); t.setHorizontalHeaderLabels(["Roll","Student","Automatic Marks","Correction","Grace","Final","Status"]); t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); self.polish_table(t)
        if exs:
            rows=services.results(exs[combo.currentIndex()]["id"]); t.setRowCount(len(rows))
            for r,x in enumerate(rows):
                vals=[x["student_code"],f'{x["first_name"]} {x["last_name"]}',x["automatic_marks"],x["correction_marks"],x["grace_marks"],x["final_marks"],x["status"]]
                for c,v in enumerate(vals): t.setItem(r,c,QTableWidgetItem(str(v)))
        l.addWidget(t,1); b=QPushButton("Manual Review & Correction"); b.clicked.connect(self.correction_dialog); l.addWidget(b); return w

    def run_eval(self,eid):
        if not eid: return
        try: services.evaluate_exam(eid); QMessageBox.information(self,"Evaluation","Automatic evaluation completed. Review exceptions before finalisation."); self.open_page("Evaluation")
        except Exception as ex: QMessageBox.warning(self,"Error",str(ex))

    def correction_dialog(self):
        d=QDialog(self); d.setWindowTitle("Manual Review & Correction"); f=QFormLayout(d)
        roll=QLineEdit(); answer=QLineEdit(); marks=QLineEdit("0"); grace=QLineEdit("0"); reason=QLineEdit()
        for n,e in [("Roll Number",roll),("Corrected Answer",answer),("Correction Marks",marks),("Grace Marks",grace),("Reason",reason)]: f.addRow(n,e)
        b=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel); f.addRow(b)
        def save():
            try:
                if not self.current_exam:
                    QMessageBox.warning(d,"Error","No examination selected"); d.reject(); return
                if not roll.text():
                    QMessageBox.warning(d,"Error","Roll number is required"); return
                rows=query("SELECT * FROM evaluations e JOIN students s ON s.id=e.student_id WHERE e.exam_id=? AND s.student_code=?",(self.current_exam,roll.text()))
                if not rows:
                    QMessageBox.warning(d,"Error",f"No student with roll {roll.text()} found"); return
                r=rows[0]
                try:
                    cm=float(marks.text() or 0); gm=float(grace.text() or 0)
                except ValueError:
                    QMessageBox.warning(d,"Error","Marks must be numeric"); return
                final=r["automatic_marks"]+cm+gm
                execute("UPDATE evaluations SET correction_marks=?,grace_marks=?,final_marks=?,status='Reviewed' WHERE id=?",(cm,gm,final,r["id"]))
                services.audit("Administrator",f'{r["first_name"]} {r["last_name"]}',"Manual Correction","","","",r["automatic_marks"],final,reason.text())
                d.accept(); QMessageBox.information(self,"Saved","Correction saved successfully and audit log updated.")
            except Exception as ex:
                QMessageBox.warning(d,"Error",f"Failed to save correction:\n{str(ex)}")
        b.accepted.connect(save); b.rejected.connect(d.reject); d.exec()

    def results_page(self):
        w,l=self.page(); self.header(l,"Results","Final review and result finalisation")
        exs=services.examinations(); 
        if not exs: l.addWidget(QLabel("No examinations available.")); return w
        eid=self.current_exam or exs[0]["id"]; rows=services.results(eid); l.addWidget(QLabel(f"Total Students: {len(rows)}   Evaluated: {sum(r['status'] in ('Evaluated','Reviewed') for r in rows)}"))
        t=QTableWidget(len(rows),7); t.setHorizontalHeaderLabels(["Student","Roll","Automatic","Grace","Final","Percentage","Grade"]); t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); self.polish_table(t)
        ex=query("SELECT * FROM examinations WHERE id=?",(eid,))[0]; maxm=ex["total_questions"]*ex["per_question"]
        for r,x in enumerate(rows):
            pct=(x["final_marks"]/maxm*100) if maxm else 0
            vals=[f'{x["first_name"]} {x["last_name"]}',x["student_code"],x["automatic_marks"],x["grace_marks"],x["final_marks"],f"{pct:.1f}%",services.grade_for(pct)]
            for c,v in enumerate(vals): t.setItem(r,c,QTableWidgetItem(str(v)))
        l.addWidget(t,1); fin=QPushButton("Finalise Results"); fin.clicked.connect(lambda:self.finalize(eid)); l.addWidget(fin,alignment=Qt.AlignRight); return w

    def finalize(self,eid):
        execute("UPDATE evaluations SET finalized=1 WHERE exam_id=?",(eid,)); execute("UPDATE examinations SET status='Completed' WHERE id=?",(eid,)); QMessageBox.information(self,"Finalised","Results finalised. Marksheets are now ready.")

    def marksheets(self):
        w,l=self.page(); self.header(l,"Marksheets","Generate, preview and print marksheets")
        exs=services.examinations(); 
        if not exs: l.addWidget(QLabel("No examination available.")); return w
        eid=self.current_exam or exs[0]["id"]; rows=services.results(eid)
        row=QHBoxLayout()
        for txt,fn in [("Generate Marksheets",lambda:self.gen_marksheets(eid)),("Preview",lambda:self.preview_marksheet(eid)),("Download PDF",lambda:self.gen_marksheets(eid)),("Print",lambda:QMessageBox.information(self,"Print","Send generated PDF to the system printer."))]:
            b=QPushButton(txt); b.clicked.connect(fn); row.addWidget(b)
        l.addLayout(row)
        t=QTableWidget(len(rows),6); t.setHorizontalHeaderLabels(["Roll","Student","Total","Percentage","Grade","Result"]); t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); self.polish_table(t)
        ex=query("SELECT * FROM examinations WHERE id=?",(eid,))[0]; maxm=ex["total_questions"]*ex["per_question"]
        for r,x in enumerate(rows):
            pct=(x["final_marks"]/maxm*100) if maxm else 0; vals=[x["student_code"],f'{x["first_name"]} {x["last_name"]}',f'{x["final_marks"]} / {maxm}',f"{pct:.1f}%",services.grade_for(pct),"Pass" if pct>=40 else "Fail"]
            for c,v in enumerate(vals): t.setItem(r,c,QTableWidgetItem(str(v)))
        l.addWidget(t,1); return w

    def gen_marksheets(self,eid):
        out=Path.home()/"OMRExaminationSystem"/"exports"; out.mkdir(exist_ok=True)
        ex=query("SELECT * FROM examinations WHERE id=?",(eid,))[0]; school=services.school()
        p=out/f"exam-{eid}-marksheets.pdf"
        # One consolidated simple PDF; production template can be styled further.
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        c=canvas.Canvas(str(p),pagesize=A4); W,H=A4; rows=services.results(eid); maxm=ex["total_questions"]*ex["per_question"]
        for x in rows:
            c.setFont("Helvetica-Bold",16); c.drawCentredString(W/2,H-45,"MARKSHEET")
            c.setFont("Helvetica",10); c.drawString(45,H-70,f"School: {school['name']}"); c.drawString(45,H-88,f"Examination: {ex['name']}")
            c.drawString(45,H-110,f"Student: {x['first_name']} {x['last_name']}"); c.drawString(45,H-128,f"Roll Number: {x['student_code']}")
            pct=(x["final_marks"]/maxm*100) if maxm else 0
            c.drawString(45,H-160,f"Total Marks: {x['final_marks']} / {maxm}"); c.drawString(45,H-178,f"Percentage: {pct:.1f}%")
            c.drawString(45,H-196,f"Grade: {services.grade_for(pct)}"); c.drawString(45,H-214,f"Result: {'Pass' if pct>=40 else 'Fail'}")
            c.drawString(45,H-250,"Automatic marks are retained separately from corrections and grace marks.")
            c.showPage()
        c.save(); QMessageBox.information(self,"Generated",f"Created:\n{p}")

    def preview_marksheet(self,eid): self.gen_marksheets(eid)

    def communication(self):
        w,l=self.page(); self.header(l,"Communication","Distribute results over WhatsApp and Email")
        tabs=QTabWidget()
        for channel in ["WhatsApp","Email"]:
            x=QWidget(); xl=QVBoxLayout(x); b=QPushButton(f"Send Finalised Results via {channel}"); b.clicked.connect(lambda _,c=channel:self.send_distribution(c)); xl.addWidget(b,alignment=Qt.AlignRight)
            rows=query("SELECT * FROM distributions ORDER BY id DESC"); t=QTableWidget(len(rows),6); t.setHorizontalHeaderLabels(["Examination","Recipient","Date/Time","Status","Error","Channel"]); t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); self.polish_table(t)
            for r,z in enumerate(rows):
                vals=["—",z["recipient"],z["sent_at"],z["status"],z["error_message"],z["channel"]]
                for c,v in enumerate(vals): t.setItem(r,c,QTableWidgetItem(str(v)))
            xl.addWidget(t,1); tabs.addTab(x,channel)
        l.addWidget(tabs,1); return w

    def send_distribution(self,channel):
        QMessageBox.information(self,"Distribution",f"{channel} queue created.\nConfigure provider credentials in Settings to send actual messages.")

    def grades(self):
        w,l=self.page(); self.header(l,"Grade Configuration","Configurable grading bands"); b=QPushButton("+ Add Grade"); b.clicked.connect(self.grade_dialog); l.addWidget(b,alignment=Qt.AlignRight)
        rows=query("SELECT * FROM grades ORDER BY min_pct DESC"); t=QTableWidget(len(rows),4); t.setHorizontalHeaderLabels(["Grade","Minimum %","Maximum %","Action"]); t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); self.polish_table(t)
        for r,x in enumerate(rows):
            for c,v in enumerate([x["name"],x["min_pct"],x["max_pct"],"Edit / Delete"]): t.setItem(r,c,QTableWidgetItem(str(v)))
        l.addWidget(t,1); return w

    def grade_dialog(self):
        d=QDialog(self); d.setWindowTitle("Add Grade"); f=QFormLayout(d); n=QLineEdit(); mi=QLineEdit(); ma=QLineEdit(); f.addRow("Grade Name",n); f.addRow("Minimum Percentage",mi); f.addRow("Maximum Percentage",ma); b=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel); f.addRow(b); b.accepted.connect(lambda:(execute("INSERT INTO grades(name,min_pct,max_pct) VALUES(?,?,?)",(n.text(),float(mi.text()),float(ma.text()))),d.accept())); b.rejected.connect(d.reject); d.exec()

    def audit(self):
        w,l=self.page(); self.header(l,"Audit Log","Traceability of every manual correction"); rows=query("SELECT * FROM audit_log ORDER BY id DESC"); t=QTableWidget(len(rows),10); t.setHorizontalHeaderLabels(["User","Date/Time","Student","Examination","Question","Old","New","Old Marks","New Marks","Reason"]); t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents); self.polish_table(t)
        for r,x in enumerate(rows):
            vals=[x["username"],x["event_time"],x["student"],x["examination"],x["question_no"],x["old_value"],x["new_value"],x["old_marks"],x["new_marks"],x["reason"]]
            for c,v in enumerate(vals): t.setItem(r,c,QTableWidgetItem(str(v)))
        l.addWidget(t,1); return w

    def settings(self):
        w,l=self.page(); self.header(l,"Settings","Application-level configuration"); tabs=QTabWidget()
        for name,text in [("Application","OMR Examination Management System\nVersion 1.0.0"),("License","Local licence state: Active\nProduction licensing server can be connected here."),("Scanner","Supported workflow: TWAIN/WIA scanner or scanned-image import."),("Backup","Database location: ~/OMRExaminationSystem/omr.db\nUse the button below to copy a backup."),("Communication","WhatsApp Cloud API and SMTP/API provider credentials belong here.")]:
            x=QWidget(); xl=QVBoxLayout(x); xl.addWidget(QLabel(text)); ifb=QPushButton("Save Settings"); xl.addWidget(ifb); xl.addStretch(); tabs.addTab(x,name)
        l.addWidget(tabs,1); return w

def style(app):
    app.setStyle("Fusion")
    app.setStyleSheet("""
    * { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial; }
    QWidget { background:#f6f4f0; color:#202326; font-size:13px; }
    #sidebar { background:#16212b; border:0; }
    #appmark { background:#be4b36; color:#fff; border-radius:6px; min-width:28px; max-width:28px; min-height:28px; max-height:28px; font-size:14px; font-weight:800; qproperty-alignment:AlignCenter; }
    #brand { background:#16212b; color:#ffffff; font-size:19px; font-weight:800; }
    #schoollabel { background:#16212b; color:#aab7c3; font-size:12px; padding:2px 0 0 0; }
    #sidefooter { background:#16212b; color:#7f8c98; font-size:11px; padding-top:12px; }
    #nav { background:transparent; border:0; text-align:left; color:#c8d1da; padding:10px 12px; border-radius:7px; font-size:13px; font-weight:650; }
    #nav:hover { background:#223240; color:#ffffff; }
    #nav[active="true"] { background:#ffffff; color:#963925; }
    #header { background:#ffffff; border-bottom:1px solid #e5e0d8; }
    #title { background:#ffffff; color:#182029; font-size:24px; font-weight:800; }
    #subtitle { background:#ffffff; color:#667085; font-size:13px; }
    #statuspill { background:#eaf6f0; color:#136947; border:1px solid #caeadb; border-radius:7px; padding:6px 10px; font-size:12px; font-weight:700; }
    #userpill { background:#f3f0eb; color:#344054; border:1px solid #e3ddd3; border-radius:7px; padding:6px 10px; font-size:12px; font-weight:700; }
    #content, #page { background:#f6f4f0; }
    #footer { background:#ede9e2; color:#776f64; padding:7px 16px; font-size:11px; border-top:1px solid #ded8ce; }
    #panel, #quickpanel, #card, #dashcard { background:#ffffff; border:1px solid #e3ded5; border-radius:8px; }
    #panel QLabel, #quickpanel QLabel, #card QLabel, #dashcard QLabel { background:#ffffff; }
    #paneltitle { color:#202326; font-size:15px; font-weight:800; }
    #panelsubtitle { color:#667085; font-size:12px; }
    #value { font-size:28px; font-weight:800; background:#ffffff; color:#182029; padding:2px 0; }
    #dashcard #card_title { font-size:12px; font-weight:700; color:#667085; background:#ffffff; }
    #dashcard #card_value { font-size:34px; font-weight:850; background:#ffffff; }
    #dashcard #card_subtitle { font-size:12px; color:#8a8176; background:#ffffff; }
    QPushButton { background:#ffffff; border:1px solid #d6d0c7; border-radius:7px; padding:9px 14px; color:#202326; font-size:13px; font-weight:700; }
    QPushButton:hover { border-color:#be4b36; color:#963925; background:#fffaf7; }
    QPushButton:pressed { background:#f3e8e2; }
    #quickaction { min-width:96px; background:#182029; color:#ffffff; border:1px solid #182029; padding:9px 12px; }
    #quickaction:hover { background:#963925; border-color:#963925; color:#ffffff; }
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit { background:#ffffff; border:1px solid #d6d0c7; border-radius:7px; padding:8px 9px; color:#202326; selection-background-color:#f2cabf; }
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTextEdit:focus { border:1px solid #be4b36; }
    QComboBox::drop-down { border:0; width:26px; }
    QTableWidget { background:#ffffff; border:1px solid #e3ded5; border-radius:8px; alternate-background-color:#faf9f7; selection-background-color:#f3e8e2; selection-color:#202326; }
    QTableWidget::item { padding:8px 10px; border:0; }
    QHeaderView::section { background:#f7f5f1; color:#667085; padding:9px 10px; border:0; border-bottom:1px solid #e3ded5; font-size:11px; font-weight:800; }
    QTableCornerButton::section { background:#f7f5f1; border:0; border-bottom:1px solid #e3ded5; }
    #summaryrow { background:#ffffff; }
    #summary_label { color:#667085; font-size:12px; background:#ffffff; }
    #summary_value { font-size:14px; font-weight:800; background:#ffffff; }
    QTabWidget::pane { background:#ffffff; border:1px solid #e3ded5; border-radius:8px; padding:12px; }
    QTabBar::tab { background:#ede9e2; color:#667085; padding:9px 16px; border-top-left-radius:7px; border-top-right-radius:7px; margin-right:3px; font-weight:700; }
    QTabBar::tab:selected { background:#ffffff; color:#963925; }
    QGroupBox { background:#ffffff; border:1px solid #e3ded5; border-radius:8px; margin-top:16px; padding:16px; font-weight:800; color:#202326; }
    QGroupBox::title { subcontrol-origin:margin; left:12px; padding:0 5px; color:#344054; background:#f6f4f0; }
    QCheckBox { spacing:8px; background:#ffffff; color:#202326; }
    QProgressBar { background:#ebe6de; border:0; border-radius:4px; min-height:8px; max-height:8px; }
    QProgressBar::chunk { background:#2368a2; border-radius:4px; }
    QScrollBar:vertical { background:#f6f4f0; width:11px; margin:0; }
    QScrollBar::handle:vertical { background:#c8c0b6; border-radius:5px; min-height:30px; }
    QScrollBar:horizontal { background:#f6f4f0; height:11px; margin:0; }
    QScrollBar::handle:horizontal { background:#c8c0b6; border-radius:5px; min-width:30px; }
    QDialog { background:#f6f4f0; }
    """)



if __name__=="__main__":
    init_db(); app=QApplication(sys.argv); style(app); win=Main(); win.show(); sys.exit(app.exec())
