# Montanna Marsh — Job Apply Workflow

Human-in-the-loop job search for **Montanna Marsh** (Reynoldsburg, OH `43068`).

## Criteria
- Full-time
- At least **$18/hour**
- Within ~30 minutes of 43068 **or remote**
- Avoid extremely physically demanding roles

## Notion board (private draft)
- Hub: https://app.notion.com/p/3df24afc3e6081698029fff967f94049
- Database / board: https://app.notion.com/p/1345ba1e1f6a45fb918a61d31736de4a

Stages: Saved → Ready to Apply → Applied → Interview → Offer / Rejected / Skipped

## Resume
- Original: `resume/Montanna_Marsh_Sunbury_Vet_Clinic_Resume_2030.docx`
- Enhanced: `resume/Montanna_Marsh_Enhanced_Resume.docx` (+ `.md`)

Enhancements (truthful only):
- Clearer target roles (patient services / medical admin / collections / remote CSR)
- Stronger summary highlighting Red Cross collections + customer service
- Fixed city spelling to Pataskala
- Added target-role line for ATS keyword coverage

## Local workflow
```bash
python3 job-apply/scripts/match_jobs.py
python3 job-apply/scripts/make_cover_letters.py
```

Outputs land in `job-apply/output/`.

## Apply order (recommended)
1. **Quantum Health** — Patient Service Representative ($19/hr, Dublin hybrid path)
2. **COPC** — Patient Service Rep, Reynoldsburg (best commute)
3. **AAA** — Remote Insurance CSR, Ohio residents ($21/hr)
4. Review **Red Cross Donor Center Phlebotomist** only if physical requirements feel OK
5. Sweep medical receptionist / front desk FT postings ≥ $18

## Important
This does **not** silently auto-submit applications. Open each Apply URL, submit with the enhanced resume, then drag the Notion card to **Applied**.
