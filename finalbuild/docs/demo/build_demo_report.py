"""Build the editable demo deck and layout previews from captured evidence.

Run here: python build_demo_report.py
Requires python-pptx and Pillow; captures are real Qt/Compose output, with
fixture/demo data. Preview PNGs use the same layout, not a PowerPoint renderer.
"""
from pathlib import Path
import json, math
from PIL import Image, ImageDraw, ImageFont
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

ROOT = Path(__file__).resolve().parent
SHOTS = ROOT / 'screenshots'
OUT = ROOT / 'previews'
OUT.mkdir(exist_ok=True)
W,H=1600,900
SCALE=120
BG='#071727'; PANEL='#10283E'; BORDER='#205374'; WHITE='#F1F7FC'; MUTED='#A8BED2'; CYAN='#34C7EE'; BLUE='#2388FF'; GREEN='#34D4A0'; GOLD='#EBC15B'; RED='#F5718C'
FONT_PATH='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD_PATH='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
if not Path(FONT_PATH).exists():
    FONT_PATH='DejaVuSans.ttf';BOLD_PATH='DejaVuSans-Bold.ttf'
prs=Presentation();prs.slide_width=Inches(W/SCALE);prs.slide_height=Inches(H/SCALE)
prs.core_properties.title='AI CAR SCANNER — Demo & QA Report'
prs.core_properties.subject='Session privacy, native UI, engineering and measured test evidence'
prs.core_properties.author='AI CAR SCANNER project'
prs.core_properties.language='hy-AM'
manifest=[]

def rgb(c): return RGBColor.from_string(c.lstrip('#'))
def font(size,bold=False): return ImageFont.truetype(BOLD_PATH if bold else FONT_PATH,round(size*SCALE/72))
def wrap(value,width,size,bold=False):
    f=font(size,bold);lines=[]
    for para in value.split('\n'):
        line=''
        for word in para.split(' '):
            candidate=(line+' '+word).strip()
            if f.getlength(candidate)>width and line:
                lines.append(line);line=word
            else:line=candidate
        lines.append(line)
    return lines

class Page:
    def __init__(self,title,kicker='PRODUCT / ENGINEERING / EVIDENCE'):
        self.slide=prs.slides.add_slide(prs.slide_layouts[6]);self.im=Image.new('RGB',(W,H),BG);self.draw=ImageDraw.Draw(self.im)
        self.slide.background.fill.solid();self.slide.background.fill.fore_color.rgb=rgb(BG)
        self.text(kicker,64,32,1450,28,11,CYAN,True)
        self.text(title,64,80,1460,100,30,WHITE,True)
        self.box(64,182,1470,3,CYAN,rounding=False)
        self.title=title;self.sources=[]
    def box(self,x,y,w,h,fill=PANEL,line=None,rounding=True):
        shape=self.slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if rounding else MSO_SHAPE.RECTANGLE,Inches(x/SCALE),Inches(y/SCALE),Inches(w/SCALE),Inches(h/SCALE))
        shape.fill.solid();shape.fill.fore_color.rgb=rgb(fill)
        if line:shape.line.color.rgb=rgb(line)
        else:shape.line.fill.background()
        if rounding:shape.adjustments[0]=.12
        self.draw.rounded_rectangle((x,y,x+w,y+h),radius=min(18,h/4),fill=fill,outline=line,width=2) if rounding else self.draw.rectangle((x,y,x+w,y+h),fill=fill)
        return shape
    def text(self,value,x,y,w,h,size=18,color=WHITE,bold=False):
        lines=wrap(value,w,size,bold)
        lineheight=size*SCALE/72*1.26
        minimum = 12 if size >= 12 else 8
        while len(lines)*lineheight > h+4 and size > minimum:
            size -= 1
            lines=wrap(value,w,size,bold)
            lineheight=size*SCALE/72*1.26
        if len(lines)*lineheight>h+4:
            raise ValueError(f'Text overflows {self.title}: {value[:65]} ({len(lines)*lineheight:.0f}>{h})')
        shape=self.slide.shapes.add_textbox(Inches(x/SCALE),Inches(y/SCALE),Inches(w/SCALE),Inches(h/SCALE));tf=shape.text_frame;tf.clear();tf.word_wrap=False
        tf.margin_left=tf.margin_top=tf.margin_right=tf.margin_bottom=0
        for i,line in enumerate(lines):
            p=tf.paragraphs[0] if i==0 else tf.add_paragraph();p.text=line;p.font.name='DejaVu Sans';p.font.size=Pt(size);p.font.bold=bold;p.font.color.rgb=rgb(color);p.space_before=Pt(0);p.space_after=Pt(0);p.line_spacing=1.26
            self.draw.text((x,y+i*lineheight),line,font=font(size,bold),fill=color,stroke_width=0)
        return shape
    def image(self,name,x,y,w,h,crop=None):
        path=SHOTS/name
        im=Image.open(path).convert('RGBA')
        if crop:im=im.crop(crop)
        if crop:
            cache=OUT/(path.stem+'-crop.png');im.save(cache);path=cache
        factor=min(w/im.width,h/im.height);ww=im.width*factor;hh=im.height*factor;xx=x+(w-ww)/2;yy=y+(h-hh)/2
        self.slide.shapes.add_picture(str(path),Inches(xx/SCALE),Inches(yy/SCALE),width=Inches(ww/SCALE),height=Inches(hh/SCALE))
        resized=im.resize((round(ww),round(hh)),Image.Resampling.LANCZOS);self.im.paste(resized,(round(xx),round(yy)),resized)
        self.sources.append(name)
    def bullets(self,items,x=80,y=225,w=650,size=19,gap=24,color=WHITE):
        for item in items:
            lines=wrap(item,w-30,size)
            hh=len(lines)*size*SCALE/72*1.26+6
            self.text('•',x,y,25,40,size,CYAN,True);self.text(item,x+30,y,w-30,hh,size,color);y+=hh+gap
        return y
    def caption(self,value,x=70,y=797,w=1460):self.text(value,x,y,w,46,10,MUTED)
    def finish(self,notes=''):
        index=len(manifest)+1
        self.text('AI CAR SCANNER  •  DEMO / QA  •  22 OCT 2026',64,862,1350,22,9,MUTED)
        self.text(f'{index:02d}',1480,856,55,30,12,CYAN,True)
        self.slide.notes_slide.notes_text_frame.text=notes+'\nScreenshot sources: '+', '.join(self.sources)
        self.im.save(OUT/f'slide-{index:02d}.png')
        manifest.append({'slide':index,'title':self.title,'screenshot_sources':self.sources,'notes':notes})

def metric(p,x,y,w,label,value,detail,color=CYAN):
    p.box(x,y,w,180,line=BORDER);p.text(value,x+24,y+20,w-48,72,38,color,True);p.text(label,x+24,y+100,w-48,38,15,WHITE,True);p.text(detail,x+24,y+143,w-48,27,10,MUTED)
def shotpage(title,name,items,caption):
    p=Page(title);p.box(60,210,1110,550,line=BORDER);p.image(name,72,222,1086,526);p.bullets(items,1200,230,330,16,24);p.caption(caption);p.finish('Actual native Qt UI rendering using seeded demo data, captured after the privacy change. No physical adapter connected.')

# 01
p=Page('AI CAR SCANNER','NATIVE DIAGNOSTICS • DEMO & QA REPORT')
p.text('Մեկ հարթակ՝ ախտորոշման ամբողջ ընթացքի համար',70,235,1000,150,32,WHITE,True)
p.text('Desktop • Android • iOS\nUI, կոդ, թեստեր և իրական screenshot-ներ',72,410,1000,110,21,MUTED)
p.box(72,570,1460,115,line=BORDER);p.text('Այս թողարկման առանցքը',94,585,1000,35,14,CYAN,True);p.text('Session ID-ն ներքին է․ օգտատերը տեսնում է մեքենան և ախտորոշումը։',94,632,1390,45,18)
p.image('cover-car.png',1080,340,440,205)
p.text('22 ՀՈԿՏԵՄԲԵՐԻ 2026',72,750,1400,45,15,CYAN,True)
p.finish('Presentation prepared 22 October 2026. Test evidence was captured in the cloud; test counts are suite executions, not necessarily unique test cases across suites.')
# 02
p=Page('Թողարկման ամփոփում')
metric(p,64,228,465,'Desktop regression','341 PASS','Qt logic / E2E / negative / UI',GREEN)
metric(p,562,228,465,'Android unit + native UI','89 + 14','103 executed checks; 0 failures',GREEN)
metric(p,1060,228,474,'Backend / protocol','541 PASS','1 PostgreSQL integration skipped',CYAN)
p.bullets(['Session ID-ն հեռացված է տեսանելի էջերից և օգտատիրոջ export-ներից։','Վերլուծությունն ու դիագրամները թարմացվում են թեստի արդյունքից հետո։','iOS-ը ստուգված է միայն շարահյուսական մակարդակով․ Xcode execution չկա։'],80,470,1420,21,25)
p.caption('Թվերը չափված են թեստերի log/JUnit/coverage հաշվետվություններից։ Suite-երի միջև կարող են կրկնվել նույն դեպքերը։');p.finish()
# 03
p=Page('Օգտատիրոջ ախտորոշման ուղին')
steps=[('01','Մեքենայի ընտրություն','Make / model / chassis / engine'),('02','Ախտանշաններ և DTC','Վարորդի դիտարկում + սխալի կոդ'),('03','Վերլուծություն','Վարկածներ և հաջորդ ստուգումներ'),('04','Թեստի կատարում','Նորմալ / Խնդիր կա / Անավարտ'),('05','Վերահաշվարկ','Արդյունքը փոխում է ապացույցները'),('06','Պատմություն / report','Բովանդակություն՝ առանց Session ID-ի')]
for i,(n,title,body) in enumerate(steps):
 x=64+(i%3)*500;y=225+(i//3)*265;p.box(x,y,470,225,line=BORDER);p.text(n,x+22,y+16,410,65,30,CYAN,True);p.text(title,x+22,y+92,425,60,20,WHITE,True);p.text(body,x+22,y+163,425,50,14,MUTED)
p.finish('PASS/FAIL/INCOMPLETE remain canonical backend values. Visible translations do not change the API contract.')
# 04
p=Page('Ճարտարապետություն և տվյալների հոսք')
for x,title,body in [(64,'Desktop','PySide6 / Python'),(566,'Android','Kotlin / Jetpack Compose'),(1068,'iOS','SwiftUI / Swift Charts')]:
 p.box(x,228,466,145,line=BORDER);p.text(title,x+22,248,420,46,24,CYAN,True);p.text(body,x+22,312,420,38,15)
p.text('↓  HTTPS / JSON API  ↓',80,402,1450,45,23,MUTED,True)
p.box(64,472,1470,105,BLUE);p.text('FastAPI • Diagnostic session • Localization • Test result recording',90,499,1400,58,23,WHITE,True)
p.box(64,626,716,125,line=BORDER);p.text('Reasoning engine',88,646,660,40,21,CYAN,True);p.text('Ապացույցներ → վարկածներ → առաջարկվող թեստեր',88,698,650,40,15)
p.box(815,626,719,125,line=BORDER);p.text('Persistence / device boundaries',840,646,650,40,21,CYAN,True);p.text('SQLite / PostgreSQL • OBD adapters • telemetry',840,698,650,40,15)
p.finish('Logical architecture. Full functional parity is not claimed: iOS supports BLE discovery only; physical transport integration still requires device testing.')
# 05
p=Page('Session ID․ տեսանելիությունից դեպի ներքին տվյալ')
p.box(64,230,710,430,line=BORDER);p.text('ՕԳՏԱՏԵՐԸ ՏԵՍՆՈՒՄ Է',88,250,660,45,18,CYAN,True)
p.bullets(['Մեքենայի անունը և ախտորոշման վիճակը','DTC-ները, վարկածները և թեստերի արդյունքները','Պատմություն և report՝ առանց ներքին ID-ի'],88,325,655,19,25)
p.box(810,230,724,430,line=BORDER);p.text('ՀԱՄԱԿԱՐԳԸ ՊԱՀՊԱՆՈՒՄ Է',838,250,660,45,18,GREEN,True)
p.bullets(['Նույն session_id-ն՝ API և persistence աշխատանքի համար','Պատմությունից սեսիայի ճիշտ վերաբացում','Export snapshot՝ առանց բնօրինակը փոփոխելու'],838,325,650,19,25)
p.text('Կիրառված է Desktop, Android և iOS միջերեսներում։',80,718,1440,60,24,WHITE,True)
p.caption('Սա UI/export privacy փոփոխություն է․ սերվերի routing-ն ու տվյալների պահպանումը շարունակում են աշխատել ներքին ID-ներով։');p.finish()
# 06 / 07 / 08
shotpage('Desktop • dashboard-ի իրական տեսք','desktop-dashboard.png',['Մեքենայի թափանցիկ նկար','Ախտորոշման հաշվիչներ','Արագ անցումներ','Live Data-ի դատարկ վիճակ'], 'Actual Qt capture • seeded demo session • telemetry not connected • no rendered mockup')
shotpage('Desktop • ախտորոշման աշխատանքային էջ','desktop-analysis.png',['Ախտանշանների մուտք','DTC-ի ավելացում','Վարկածներ և տվյալներ','Header-ում Session ID չկա'], 'Actual Qt capture • demo diagnostic dataset • screenshot captured after privacy change')
shotpage('Desktop • պատմություն և report','desktop-reports.png',['Մեքենա + վիճակ','ID-ն ցուցակում չի երևում','Ներքին ID-ով վերաբացում','PDF / HTML / JSON export'], 'Actual Qt capture • export tests verify hidden Session ID while retaining P0302 content')
# 09
p=Page('Android • մուգ և բաց թեմաներ')
p.image('android-home-hy.png',72,210,480,570);p.image('android-home-ru-light.png',590,210,480,570)
p.bullets(['Իրական Compose rendering','Հայերեն և ռուսերեն','Նույն տվյալները՝ տարբեր թեմաներով','Cloud native-graphics capture'],1110,255,420,18,26)
p.caption('API 35 / Robolectric • fixture data • սա ֆիզիկական հեռախոսից կամ emulator-ից նկար չէ։');p.finish('Actual Compose UI rendered by Robolectric native graphics, using seeded diagnostic data.')
# 10
p=Page('Android • վերլուծություն և թեստերի արդյունքներ')
p.image('android-analysis-recalculated.png',72,215,550,570,crop=(0,0,824,1000));p.image('android-tests-hy.png',640,215,440,570)
p.bullets(['Թեստերը հասանելի են Analysis-ի մեջ','PASS / FAIL / INCOMPLETE','Սերվերի պատասխանից հետո՝ թարմացված վարկածներ','Կրկնակի analyze հարցում չի ուղարկվում'],1100,235,420,16,25)
p.caption('Actual Compose captures • analysis screenshot is a UI excerpt from a controlled result-update test.');p.finish()
# 11
p=Page('Դիագրամներ • գնահատականներ և արդյունքներ')
p.image('android-diagram-hy-dark.png',70,210,690,570,crop=(0,0,824,750));p.image('android-diagram-ru-light.png',820,210,690,570,crop=(0,0,824,820))
p.caption('Actual Compose UI excerpts • վերջին արդյունքը փոխարինում է նույն թեստի նախորդ արդյունքին․ կրկնակի հաշվարկ չկա։');p.finish('Evidence scores are not confirmed faults. The chart only shows valid numeric scores supplied by the server; missing scores are not invented.')
# 12
p=Page('OBD adapter • ավելի մշակված պատկերակ')
p.image('android-adapter-refined.png',80,230,820,510,crop=(0,0,824,550))
p.bullets(['Կլորացված միակցիչի կորպուս','16 կոնտակտ','Մեղմ կապույտ լուսավորություն','Գույնը՝ ըստ կապի վիճակի'],980,255,520,20,30)
p.caption('Actual Compose component capture • ցուցադրված է Bluetooth / ELM327 demo label, ոչ hardware connection-ի ապացույց։');p.finish()
# 13
p=Page('Mobile report • ներքին ID-ն թաքցված է')
p.image('android-reports-private.png',80,215,610,560,crop=(0,0,824,650))
p.bullets(['Մեքենայի անունն ու վիճակը մնում են տեսանելի։','JSON snapshot-ից session_id դաշտերը հեռացվում են։','Unit/UI թեստերը հաստատում են, որ ID-ն չի երևում։','Ներքին օբյեկտի session_id-ն չի փոփոխվում։'],760,245,735,20,27)
p.caption('Actual Compose report component • privacy assertion passed; shared payload tested separately.');p.finish()
# 14
p=Page('Կոդ • export-ի անվտանգ snapshot')
p.image('source-privacy.png',70,215,1040,560)
p.bullets(['Recursive filtering','Բնօրինակը չի փոփոխվում','Նույն սկզբունքը՝ Kotlin և Swift-ում','API payload-ն անփոփոխ է'],1150,245,370,17,25)
p.caption('Իրական source-ի Qt viewer capture • apps/desktop/models.py • սա IDE-ի screenshot չի ներկայացվում։');p.finish('The source viewer displays the actual production helper used for Desktop report export; matching tests inspect nested data and original-object preservation.')
# 15
p=Page('Թեստավորում • ամբողջական regression matrix')
rows=[('Backend / protocol','541 PASS + 1 SKIP','97.42% lines'),('Desktop','341 PASS','90.14% source / 91.09% core'),('Android JVM','89 PASS','33.83% JVM line coverage'),('Android native UI','14 PASS','Supplemental cloud UI checks'),('iOS','29 declared tests','Syntax checked; XCTest not run')]
y=225
for a,b,c in rows:
 p.box(64,y,1470,100,line=BORDER);p.text(a,86,y+27,450,60,19,WHITE,True);p.text(b,550,y+27,390,60,20,GREEN if 'PASS' in b else GOLD,True);p.text(c,960,y+29,540,60,16,MUTED);y+=114
p.caption('Coverage-ի scope-երը տարբեր են․ թվերը միավորել կամ համեմատել որպես նույն չափում ճիշտ չէ։',y=818);p.finish('Counts reflect latest privacy-change runs. Android JVM coverage includes unexercised presentation classes. Supplemental native checks do not constitute connected-device coverage.')
# 16
p=Page('Coverage • ուժեղ մասերը և բացերը')
for i,(label,value,color) in enumerate([('Backend / protocol lines',97.42,CYAN),('Desktop complete source',90.14,GREEN),('Desktop production core',91.09,GREEN),('Android JVM lines',33.83,GOLD)]):
 y=235+i*125;p.text(label,72,y,1000,42,20,WHITE,True);p.box(72,y+58,1320,24,PANEL);p.box(72,y+58,1320*value/100,24,color);p.text(f'{value:.2f}%',1410,y+40,145,55,21,color,True)
p.caption('Backend branches՝ 87.52%։ Android UI-ի ամբողջական coverage-ը դեռ պահանջում է emulator/device instrumentation։');p.finish('These are deliberately scoped metrics, not whole-repository coverage. No exclusions or lowered thresholds were introduced to make a gate pass.')
# 17
p=Page('Թեստերի իրական output • Desktop')
p.image('test-evidence.png',64,210,1130,570)
p.bullets(['5 անկախ test group','UI teardown՝ առանց crash-ի','90% շեմերը անցած են','JUnit + coverage artifacts'],1220,240,310,16,25)
p.caption('Qt log viewer capture՝ ավարտված regression run-ի իրական log-ից։ Test count-ը նկարում պահպանված է բնօրինակից։');p.finish('Actual completed test-run output viewed in a native Qt read-only log viewer. This is not represented as an interactive terminal screenshot.')
# 18
p=Page('Իրական backend startup և performance')
p.image('backend-evidence.png',70,225,1060,520)
metric(p,1160,235,365,'Startup','2.16 s','Actual local launcher',CYAN)
metric(p,1160,445,365,'Reasoning p95','2.32 ms','Budget: < 90 ms',GREEN)
p.caption('Ստուգված են 369 մեքենայի կատալոգը, ախտորոշման ընթացքը և restart-ից հետո տվյալների պահպանումը։');p.finish('The startup log comes from an actual local Uvicorn child process with isolated SQLite storage. The benchmark measures deterministic in-process reasoning, not LLM/network latency.')
# 19
p=Page('iOS • իրականացվածը և ստուգման սահմանը')
p.bullets(['Session ID-ն հեռացված է header-ից, պատմությունից և report export-ից։','Թեստի սխալի դեպքում sheet-ն ու նշումները մնում են՝ կրկին ուղարկելու համար։','Swift Charts դիագրամներ, արդյունքների թարգմանություններ և ներքին ID-ի privacy թեստ։','29 XCTest case սահմանված է․ 10 Swift ֆայլի syntax ստուգումն անցած է։'],80,235,1410,20,25)
p.box(80,715,1440,90,line=BORDER);p.text('Xcode / simulator run և իրական iOS screenshot այս միջավայրում չկան։',105,738,1385,60,20,GOLD,True)
p.finish('No iOS screenshot is fabricated or included. Swift syntax parsing is not Swift type checking, compilation or runtime validation. Native test execution and numeric iOS coverage remain pending.')
# 20
p=Page('Ուղղված խնդիրներ և անվտանգության audit')
items=[('Desktop','Widget teardown crash → deferred deletion + clean process exit'),('Android','Bluetooth permission/cancellation → explicit failure + cleanup'),('iOS','Failed result submission → retain notes and retry'),('Dependencies','Pillow 13.0.0 / pytest 9.1.1 → 0 known findings in 64 packages')]
for i,(title,body) in enumerate(items):
 y=225+i*136;p.box(64,y,1470,114,line=BORDER);p.text(title,88,y+27,275,55,21,CYAN,True);p.text(body,390,y+25,1100,80,18)
p.caption('Անվտանգության արդյունքը վերաբերում է չափված Python inventory-ին և audit-ի պահին հայտնի advisory-ներին։');p.finish('Dependency audit is not a guarantee of absence of all vulnerabilities or a mobile dependency audit. Android lint separately reports 0 errors and 21 warnings.')
# 21
p=Page('Demo-ի սցենար և հաջորդ ստուգումները')
p.bullets(['Ընտրել մեքենան → մուտքագրել ախտանշան և P0302։','Գործարկել Analysis → բացել առաջարկվող թեստերը։','Գրանցել արդյունքը → տեսնել նոր վարկածներն ու դիագրամը։','Բացել History / Report → հաստատել, որ Session ID-ն չի երևում։'],80,225,1400,23,25)
p.box(80,650,1440,135,line=BORDER);p.text('Հաջորդ validation քայլերը',104,668,1360,40,18,CYAN,True);p.text('iOS Xcode • Android connected coverage • PostgreSQL/pgvector • իրական OBD սարքեր • Windows EXE',104,723,1360,65,18)
p.finish('User-facing demo flow. Physical-device tests, PostgreSQL integration and Windows packaging are explicitly not certified by the cloud evidence.')
# 22
p=Page('Վերագործարկում և evidence աղբյուրներ')
p.text('finalbuild պանակից',80,230,1400,45,21,CYAN,True)
p.text('git pull --ff-only origin main\npython -m pip install -r backend/requirements-dev.txt -r apps/desktop/requirements-dev.txt',80,302,1430,135,16,WHITE)
p.text('Android',80,480,1400,45,21,CYAN,True)
p.text('cd apps/mobile-android\n./gradlew :app:installDebug',80,548,1430,100,18,WHITE)
p.text('docs/testing/full-qa-audit-2026-10-21.md\ndocs/demo/README.md • screenshots/ • evidence-summary.json',80,705,1430,85,16,MUTED)
p.finish('Open the deck with PowerPoint or LibreOffice. Text, diagrams, tables and metrics are editable; screenshots are embedded as evidence images. Layout-preview images are generated from the same layout specification, not by a native PowerPoint renderer.')

output=ROOT/'AI-Car-Scanner-Demo-Report-2026-10-22.pptx'
prs.save(output)
(ROOT/'slides-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
thumbs=[]
for item in manifest:
 im=Image.open(OUT/f'slide-{item["slide"]:02d}.png');im.thumbnail((400,225));thumbs.append(im)
contact=Image.new('RGB',(4*400,math.ceil(len(thumbs)/4)*225),'#06101A')
for i,im in enumerate(thumbs):contact.paste(im,((i%4)*400,(i//4)*225))
contact.save(ROOT/'slide-overview.png')
# Reopen and validate package shape bounds and screenshot assets.
check=Presentation(output)
assert len(check.slides)==22
for sl in check.slides:
 for sh in sl.shapes:
  assert sh.left>=0 and sh.top>=0
  assert sh.left+sh.width<=check.slide_width+1000
  assert sh.top+sh.height<=check.slide_height+1000
print(f'Created {len(check.slides)} slides: {output} ({output.stat().st_size:,} bytes)')
