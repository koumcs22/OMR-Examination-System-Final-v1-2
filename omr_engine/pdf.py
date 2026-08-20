from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

def draw_bubble(c,x,y,r,label):
    c.circle(x,y,r,stroke=1,fill=0)
    c.setFont("Helvetica",7); c.drawCentredString(x,y-r-9,label)

def generate_omr_pdf(path, school, exam, questions, sheets=1):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    c=canvas.Canvas(str(path),pagesize=A4)
    W,H=A4
    for sheet in range(sheets):
        c.setFont("Helvetica-Bold",15); c.drawCentredString(W/2,H-25*mm,school)
        c.setFont("Helvetica-Bold",12); c.drawCentredString(W/2,H-33*mm,exam["name"])
        c.setFont("Helvetica",9); c.drawString(18*mm,H-45*mm,"Roll Number")
        x0=45*mm
        for row in range(6):
            y=H-(53+row*9)*mm
            c.drawString(18*mm,y-2,"" if row else "")
            for digit in range(10):
                draw_bubble(c,x0+digit*11*mm,y,3.2*mm,str(digit))
        c.drawString(18*mm,H-112*mm,"Test Booklet No: __________________")
        y=H-130*mm
        for q in questions:
            if y < 20*mm:
                c.showPage(); y=H-20*mm
            c.setFont("Helvetica",8)
            c.drawString(18*mm,y,f"Q{q['question_no']}. {q['question_text'][:85]}")
            for i,opt in enumerate(q["options"]):
                draw_bubble(c,55*mm+i*25*mm,y,3.0*mm,chr(65+i))
            y-=10*mm
        c.setFont("Helvetica",7); c.drawString(18*mm,10*mm,"OMR Examination Management System")
        c.showPage()
    c.save()
    return path