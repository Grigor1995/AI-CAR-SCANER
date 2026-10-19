# AI-CAR-SCANER Desktop v1.0 — Local Real UI Acceptance Pack

Այս pack-ը նախատեսված է **Windows 11 / Git Bash / Python 3.14 `.venv`** միջավայրի համար և **CI/CD չի օգտագործում**։ Թեստը գործարկվում է իրական (visible) Qt/Windows display-ով, ոչ թե `offscreen`-ով։

## 1. Տեղադրում

Գտնվիր `finalbuild/` պանակում և տեղադրիր մեկ Python file-ը՝

```bash
cd ~/Desktop/AI-CAR-SCANER/git/finalbuild
cp ~/Downloads/real_ui_acceptance.py scripts/real_ui_acceptance.py
```

Եթե ֆայլը բացել ես ZIP-ից, տեղափոխիր դրա `real_ui_acceptance.py`-ը `finalbuild/scripts/`։ Օգտագործում է արդեն առկա `PySide6` և `Pillow` packages-ը։

## 2. Source UI — առաջին գործարկում

```bash
python scripts/real_ui_acceptance.py --mode source --hold-seconds 8
```

Սա բացում է իրական Windows Qt պատուհան, սեղմում navigation/buttons-ը, մուտքագրում ցուցադրական diagnostic case, փոխում settings-ը **միայն RAM-ում** և նկարում UI screenshots։ API-ը mocked է՝ **չի կապվում իրական backend-ին կամ OBD-ին**։

## 3. Packaged Windows EXE — visible startup + clean shutdown

Եթե արդեն ունես `finalbuild/dist-release/icon-preview/AICarScanner.exe`՝

```bash
python scripts/real_ui_acceptance.py --mode all \
  --exe dist-release/icon-preview/AICarScanner.exe \
  --hold-seconds 8
```

Այս հրամանը նորից գործարկում է source UI tests-ը և բացում է իրական **packaged EXE**-ն visible Windows GUI-ով՝ մոտ 18 վրկ ինքնափակմամբ, որպեսզի ստուգի startup/screenshot/shutdown։ EXE-ն ստանում է ժամանակավոր loopback fake HTTP backend (`/health`, `/api/v1/devices`), ոչ իրական Render/API/LLM։ `APPDATA` ուղղվում է ժամանակավոր folder, իսկ քո source test-ը QSettings-ն ու VehicleStore-ն փոխարինում է RAM-only տարբերակներով։

Եթե EXE-ն ուրիշ տեղում է՝ `--exe`-ի արժեքում տեղադրիր ճիշտ path-ը։ Եթե չկա, source mode-ը միևնույն է աշխատում է։

**Կարևոր․** գործարկիր unlocked Windows desktop-ում և մի՛ փակիր ծրագրի պատուհանը test-ի ընթացքում։ Tk/Qt offscreen environment-ում կամ SSH session-ում UI rendering-ը չի համարվում իրական։

## 4. Ապացույց և report

Տվյալները՝ `finalbuild/desktop-test-reports/real-ui-acceptance/`՝

- `report.html` — results + screenshots gallery
- `results.json` — machine-readable PASS/FAIL, Git commit, limitations
- `screenshots/*.png` — visible UI captures
- `exe-shutdown.log`, `exe-console.log` — packaged app startup/shutdown evidence (`--mode exe` կամ `all`)
- `exe-sha256.txt` — EXE-ի SHA256 hash-ը
- `MANUAL_CHECKLIST.md` — release go/no-go checklist

Windows-ում բացիր `report.html`-ը և դիտիր screenshots-ը, ոչ միայն PASS/FAIL։

## 5. Release v1.0 Gate

`Automated PASS` դեռ **Release GO** չէ, քանի որ այս pack-ի source UI-ն օգտագործում է fake backend։ Release-ի համար պետք է նաև actual/backend diagnostic scenario, հայերեն/ռուսերեն UI, DPI, icon և persistence ձեռքով ստուգել `MANUAL_CHECKLIST.md`-ով, ինչպես նաև հաշվի առնել քո արդեն անցած Desktop pytest 310/310 + coverage 91.09% և EXE 3/3 stability evidence-ը։

Նշում՝ scripts-ը **ոչինչ չեն commit/push անում**, չեն ջնջում քո local profiles-ը և չեն գործարկում CI/CD։

## 6. Integrated main-branch Windows release runner (2026-10-19)

Այս թեստերն այժմ repository-ի `main` branch-ում են, ուստի ֆայլերը `Downloads`-ից պատճենելու կարիք չկա։

```bash
cd ~/Desktop/AI-CAR-SCANER/git/finalbuild
git pull --ff-only origin main

# Default release-candidate gate: 90% source/core, fresh build, frozen EXE
# smoke, 3-repeat packaged stability, performance budgets and visible UI.
bash windows_test_runner.sh

# Faster when the EXE already exists; build freshness is not certified.
bash windows_test_runner.sh --reuse-exe

# Visible source UI and source/performance checks only; not a release gate.
bash windows_test_runner.sh --source-only
```

Գործարկիր unlocked Windows session-ում, Git Bash-ից և ակտիվ Python 3.14 `.venv`-ով։ Պատուհանի վրա մի՛ սեղմիր test-ի աշխատանքի ընթացքում։ `windows_test_runner.sh`-ը կիրառում է `scripts/run_full_desktop_qa_git_bash.sh`-ը և report-ի համար `scripts/desktop_v1_readiness.py`-ը։

Արտածվում է նաև `desktop-test-reports/release-v1-readiness.json`, որտեղ կլինեն source/production coverage, performance gate-ը, executable-ի SHA256-ը, 3/3 startup/shutdown evidence և visible UI PASS/FAIL։ Դրա `manual_acceptance`-ը մնում է `PENDING`, մինչև իրական backend + localization + visual checks-ը ձեռքով հաստատվեն։

Ամբողջ runner-ը գործում է **local**. GitHub Actions/CI/CD չի գործարկում, commit կամ push չի կատարում։ Full mode-ում build script-ը կարող է տեղադրել Python requirements արդեն ակտիվ `.venv`-ում և վերակառուցում է միայն `dist-release/`/`build-release/` generated artifacts-ը՝ օգտագործելով staged icon source։ User profiles-ը, tracked icons-ը և Git history-ն չեն վերագրվում։
