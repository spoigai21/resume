# ATS Playbook — what breaks, and the technique that works

**Purpose:** stop rediscovering the same failures. Before filling any application, find the
platform below and use the stated technique. Append a new entry every time something breaks.

**Companion files:** `formdriver.js` (inject first), `APPLICATION-ANSWERS.md` (what to answer).

---

## Universal rules, learned the hard way

| Rule | Why |
|---|---|
| **Inject `formdriver.js` first, dump the whole form** | One call replaces ~15 screenshots. Gives every field's name, label, type, value, required flag, options. |
| **NEVER batch open-dropdown + click-option** | Layout shifts between the screenshot and the click. This set work authorization to **No** on Allegion and veteran status to **"I am a veteran"** on Allegion. Open → screenshot → click, as separate calls. |
| **Verify writes by reading back, not by looking** | A value can *display* correctly while the framework's state is empty. CACI showed "Shayan" and still errored "First Name cannot be left blank." |
| **Check the JD location BEFORE filling anything** | Four of four recent roles required relocation and none were Bay Area. A "are you local to X" question is a knockout. |
| **Fill and advance BEFORE uploading a resume** where possible | Some parsers wipe already-entered fields; one freezes the renderer entirely. |
| **Run the pre-submit audit** | Every required field non-empty *and* every role description non-empty. The Adorus description went in blank at Allegion because only required fields were checked. |

---

## Batch runs over the Claude tab group (set 2026-09-12)

Work every tab in the Claude tab group of the applications window to completion. Do not stop the run.

| Situation | Do |
|---|---|
| Form fully filled + audit passes | **Submit it yourself**, confirm the confirmation page, next tab |
| Terms / privacy / attestation checkbox | **Tick it.** Never opt into marketing email |
| Relocate / on-site / "local to X" | **Yes** — no flag, no halt |
| How did you hear about us | **LinkedIn**, every form |
| Account + password required, unreachable upload/frame, broken page | **Skip, queue, continue** — report the exact issue at the end |

### Resume per application

Read the JD before choosing the file.

1. **ALWAYS tailor (his standing instruction, Sept 13 2026).** Every application gets its own company copy — never upload a
   prebuilt variant untouched. The variants in `variants/pdf/<ml|infra|backend|security|general>/` are only starting points.
2. **Tailor.** Pick the variant closest to the JD, then build a company copy:
   copy the closest variant to `app2026:2027/<Company>/ShayanPoigaiResume.tex`, then cut, reorder, or restore bullets
   (any bullet is cuttable, HerbsPro included; the commented-out state-machine bullet and RESUME-DETAILS.md facts can come back).
   For Adorus, pull from RESUME-DETAILS.md "Adorus — complete build record" (use its tailoring routing table);
   its figures supersede anything older in the repo (conflicts resolved Sept 13 2026).
   Preamble and macros stay byte-identical; nothing invented; APPLICATION-RESPONSES.md number rules apply; one page.
3. **Build:** `PYTHON=<venv>/bin/python ./build_resume.sh <tex> app2026:2027/<Company>/ShayanPoigaiResume.pdf` — pdflatex in Docker
   image `resume-tex:1` plus the §4/§28 parse checks; it refuses to write a PDF that fails or runs to two pages.
4. Upload file name is always `ShayanPoigaiResume.pdf`. Never a .docx.

---

## Technique ladder for setting a value

Try in this order. Stop at the first that sticks — **always read back to confirm**.

1. **Native setter + events** — works on plain `<select>` and `<input>`:
   ```js
   Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(el, v);
   ['input','change','blur'].forEach(e => el.dispatchEvent(new Event(e,{bubbles:true})));
   ```
2. **Real typing** via `computer` — needed when the framework validates on trusted events only.
3. **Click → type to filter → Enter** — the fastest pattern for React comboboxes.
4. **Click → screenshot → click the option** — when typing doesn't filter.

---

## File upload ladder

1. **`find` the `input[type=file]` → `file_upload` with its ref.** Works when the input is visible and top-level.
2. **Proxy + `xfer`** — when the input is hidden or inside a same-origin iframe (`find` can't see into iframes):
   create a visible `input[type=file]` at top level, `file_upload` to it, then move the `FileList`
   across via `DataTransfer`. Solved iCIMS.
3. **Synthetic `drop`** with `DataTransfer` on the drop zone.
4. **Call React's own handler**: read `el[Object.keys(el).find(k=>k.startsWith('__reactEventHandlers'))].onChange({target: el})`.
5. **If all four fail → hand to the user.** Only a real file-picker click will do it. Don't burn more turns.

---

## Per-platform registry

### Greenhouse (`job-boards.greenhouse.io`)
- **Has a Simplify "Autofill my application" button at the top of the form. USE IT FIRST.**
- Fields render as `role="combobox"` text inputs, not `<select>`. Native setter does nothing.
- **Works:** click → type to filter → `Enter`. Confirmed on Yes/No, school, graduation term.
- `<textarea>` (essay fields) accepts the native setter fine.
- Reading `.value` back on a combobox returns **empty even when correct** — verify by screenshot.
- Race/gender lists may have **no decline option** (Hudl). Requires the user's own choice.
- Long page: `window.scrollTo(0, window.scrollY + rect.y - 220)` — `scrollIntoView` sometimes no-ops.

### Brassring (`sjobs.brassring.com`)
- Session-timeout countdown shows in the tab title. **Do not JS-click a button matching /continue/** to keep it alive - on 09-12 that hit "Save and continue" (empty form -> validation errors only, nothing saved).
- Required: legal name, phone xxx-xxx-xxxx, street address, city (no abbreviations), state, zip, education history, work experience.

### Greenhouse (addendum 09-12)
- **Location (City) typeahead can sit on "Loading..." for 10+ seconds** after several searches in a row (3 Lyft tabs, 09-12). It does resolve: "Fremont, California" returned results after ~12 s. **Retyping restarts the delay** - don't clear it early. Type once, wait ~12 s across two waits, then read `[id^=react-select-candidate-location-option]`. If it is still Loading after ~20 s the request is hung: clear -> Escape -> re-click -> retype the same query **once**, then wait the full ~13 s again (this is what resolved the SF tab). Never press Enter while it says Loading.
- **Employment rows:** once any employment field has content, *Start date month* becomes required even though it shows no asterisk (Lyft 09-12). Fill month + year together; with "Current role" ticked the end date is disabled and not required.
- A "thank you" regex match is not a confirmation - check the URL ends in `/confirmation` and the Submit button is gone. An answer option literally named "Thank you" (Lyft's employment acknowledgement) produced a false positive.
- JS `setTimeout` in a background tab is throttled -> async JS helpers time out (45 s). Keep JS synchronous; do dropdowns with real clicks.
- `[role=option]` also matches the hidden intl-tel-input country list - scope option reads to the open react-select menu.
- Focus-via-JS + keyboard typing can land in the phone-country flyout. Click the field itself, type, wait, zoom, then click the option.

### Ashby (`jobs.ashbyhq.com`)
- **Ashby ignores every JS-set value.** Native-setter email, JS `.click()` on the Yes/No buttons, label-click radios, and `form_input` on the End Date selects all *displayed* correctly and read back correctly from the DOM - and the submit still failed: "Missing entry for required field: Email / authorized to work / sponsorship / relocate" + "Invalid value: Education History" (Ibotta 09-12). Use real clicks and real typing for every field. A DOM read-back is not proof on Ashby.
- **Yes/No buttons and EEO radios toggle on real click.** If an earlier JS click left a button looking active, a real click *deselects* it (Ibotta 09-12: all three Yes/No went blank and gender/race/veteran radios unchecked). Read each control's state first, then click only the ones that are off.
- School is a typeahead ("Search schools..."): the first option is pre-highlighted, ArrowDown moves off it. Click the option row.
- "How did you hear" is a typeahead; LinkedIn filters to one option.
- **Radios/checkboxes that were JS-clicked stay unregistered even though they look selected.** Clicking the already-selected option is a no-op. Force a real change: click a different option, then the right one (radio), or click the checkbox off and on. This cleared "Missing entry: relocate" and "Invalid value: Education History" (Ibotta 09-12).
- Re-checking "Still Student?" clears the End Date month/year (they grey out). Ashby then accepts the education entry with no end date.
- **Yes/No buttons: `find`-ref clicks can leave the button looking pressed while the hidden checkbox stays `false`** (Pylon 09-13 -> "Missing entry" on submit). Scroll the buttons into view, coordinate-click the *other* option, then the right one.
- Job description: script fetches of the posting are output-blocked; click the page's **Overview** tab and read the page text instead.
- Success = inline text "application was successfully submitted" + Submit button gone. The URL does not change. The Jobright extension overlays an "Application Submitted!" popup with other jobs - ignore it.

### Tesla (`tesla.com/careers/.../apply/<req>`)
- 4 steps: Personal -> Work Experience -> Legal Acknowledgment -> EEO. Native inputs, but React state only takes **real** input.
- **Radios: click the LABEL text, not the circle.** Clicking the 24x24 input left every group unset ("Required" on Next).
- **Selects:** `form_input` from the placeholder can silently revert; flipping to another option and back registered. Never press Enter on a focused select - on 09-12 it triggered *Previous* and bounced back a step (answers survived).
- **Date pickers** (start date, graduation date) are read-only calendars: click the field, click the next-month arrow N times, confirm the header, then click the day.
- **EEO acknowledgment checkbox stays `disabled` until the disclosure box is scrolled to the bottom** - with the mouse wheel *inside* the box. The page scrolls inside a container, so `window.scrollTo`/`scrollIntoView` do nothing; wheel-scroll a neutral area to bring the box on screen first.
- Cookie banner: click Reject by ref (coordinate click missed).
- Success: heading "Your Application Has Been Received", tab title ends "Application Submitted". Jobright overlay pops over it - ignore.

### Workday (`*.myworkdayjobs.com`)
- Custom button dropdowns (`button[aria-haspopup="listbox"]`). `form_input` errors: *"Element type BUTTON is not a supported form input"*.
- **Layout shifts after each answer** as validation clears. Re-read coordinates every time.
- Its resume parser is good (all bullets survived) but **invents phantom duplicate entries** — one with the company name as the job title and blank dates.
- **Before deleting any duplicate, read its Role Description.** The phantom held the only copy of the Adorus bullets; deleting it discarded them.
- Truncates titles at special characters: `Lab Teaching Assistant (C++)` → `Lab Teaching Assistant (C`.
- Account creation with password is required up front → user only.

### iCIMS (`*.icims.com`)
- Real form is in a **same-origin iframe** `#icims_content_iframe`. `find` / `read_page` cannot see in; **JS can**.
- Plain `<select>`/`<input>` inside — the native setter works.
- **Upload:** proxy + `xfer` (ladder step 2). Confirmed working.
- Uploading the resume **pre-fills and can overwrite** fields — upload first, then fill.
- Address is a typeahead `<select>`: click → type → pick the geocoded match.
- Deeper form frames (`#icims_formFrame`) are **cross-origin — unreachable.** Hand those to the user.
- Screenshots time out on the self-identification step; use JS.
- 09-12 Garmin: custom `dropdown-select` widgets wrap native selects; native setter + `jQuery(s).trigger('change')` updates both, and dependent selects (source details) repopulate synchronously.
- Step 3 "Confirm Application" review form is in a cross-origin frame: scroll + screenshot + real click only.
- Native `<select>` popups there don't render in screenshots. Pick by: click -> `Escape` -> type a prefix (e.g. "I do not") -> `Tab`, then screenshot. **Never press Return** - it submits the form (09-12 it submitted the self-ID page early; validation rejected it, no harm).

### Lever (`jobs.lever.co`)
- Plain server-rendered form: native setter + `input`/`change` events work on text, textarea, select; `el.click()` works on checkboxes/radios.
- `file_upload` on the `resume` input works directly (verify `files[0].size`).
- Job description is not on the /apply page: fetch `/company/<id>` same-origin with a sync XHR and parse it.
- **Extension site permissions can deny `left_click` on this domain** — ask the user to allow it or to click Submit.
- Simplify autofill over-ticks multi-select cards (all office locations) and guesses languages — audit every checkbox.

### Phenom (`careers.activision.com`, many others)
- Native `<select>` + text inputs everywhere. **Native setter works.** Fastest platform so far.
- IDs are dotted (`cntryFields.region`) and `name` is empty → look up by **`getElementById`**, not `[name=]`.
- **The renderer FREEZES for minutes after a resume upload.** Reproduced twice. It does recover; the resume does land. Fill and advance first if you can.
- **A reload wipes every field.** Don't reload to fix a freeze — wait it out.
- School field is a **typeahead that rejects typed text**: must click the suggestion or it errors *"Enter school name"* even though the text is visible.
- Multi-step: `?step=N&stepname=...`. Advance with `button.btn-next`.
- **Watch the job ID.** The tab drifted from `R028039` (Software Engineering) to `R028046` (User Research Data Analytics) between sessions.

### CACI (`searchcareers.caci.com`) — worst case so far
- React 16. **Rejects every programmatic input.** Values display but validate as blank.
- **Everything must be typed with real keystrokes.**
- **Resume upload is impossible programmatically.** All four ladder steps fail, including calling React's own `onChange` (it returns "ok" and the component ignores it).
- Pops a **Data Privacy Agreement** on upload that bundles marketing-email consent — close it, don't accept.
- ~15 unlabeled `Select` comboboxes; labels don't resolve from the DOM. Read the page text to map them.
- **09-12 run (resume uploaded by the user) — what worked:**
  - Map comboboxes by walking up from each `input-N` to the first ancestor with real text — gives the question label.
  - Per field: JS `scrollIntoView({block:'center'})` → real click at the viewport centre → type a filter → **wait one zoom for the list animation to settle** → click the single option just below the input → `Escape` → read `input.value`. Clicking during the animation leaves typed text, not a selection, and it clears on blur.
  - **Typed text goes to whichever combobox still holds focus.** Always `Escape` + `blur()` before moving on, or a filter lands in the previous field (e.g. "Open" replaced Military = No; "do not" went into the wrong box).
  - Text fields typed once can still error "cannot be left blank". Fix: click in, `End`, space, `Backspace`, `Tab` — the error clears.
  - Selecting a Country reveals an extra **Candidate name + address** block (first/last, address, city, State combobox, postal code). Selecting Language reveals the disability Name + status radios.
  - An open dropdown scrolls the page back to itself when it closes, so a coordinate click right after can hit the wrong spot — re-scroll first.
  - "How did you hear": no LinkedIn at the top level; choose **Social Media** → "Which social media platform?" → **LinkedIn**. (Job Board's list has no LinkedIn.)
  - Salary is range-only (no "Open"): $25/h ≈ $52k → **$40,000-$60,000**.
  - Clearance agency list starts with "I do not possess an active security clearance."

---

## Extensions

- **Simplify Copilot** — profile is filled and correct. Autofill button appears on Greenhouse and similar. Use before hand-filling.
- **Claude in Chrome** — tools only reach the tab group *this session* created (`tabs_context_mcp` createIfEmpty); an older "Claude" group is unreachable, so the user moves application tabs into the new group. **Never close the New Tab the extension created with the group** — on 09-12 closing it dropped the session's access to all 14 moved tabs, and they had to be moved again.
- **Jobright** — also installed. Took over the CACI page. **Two autofill extensions conflict; disable one.**

---

## Log

| Date | Company | Platform | Outcome |
|---|---|---|---|
| 09-09 | Allegion | Workday | Submitted. Caught work-auth flip, veteran flip, C++ truncation. **Missed:** Adorus description blank. |
| 09-10 | Planview | iCIMS | Steps 1–3 submitted; step 4 self-ID in an unreachable cross-origin frame. |
| 09-10 | Hudl | Greenhouse | Submitted. Tailored essay; user completed gender/race (no decline option). |
| 09-10 | CACI | CACI own | Blocked — resume upload impossible programmatically. |
| 09-10 | Activision | Phenom | Steps 1–3 done on the correct SWE req after fixing a job-ID drift. |
| 09-12 | Vercel | Greenhouse-embedded (vercel.com) | Submitted, `backend` variant. Radios need `el.click()`; phone input (react-phone-number-input) ignores the native setter - had to type it. Confirmation: "Your job application was submitted." |
| 09-12 | Klaviyo | Greenhouse | Submitted, `backend` variant. Every dropdown done by real click -> type -> zoom -> click/Enter; JS dropdown helpers failed (background-tab timer throttling). Confirmation: "Thank you for applying!" (/confirmation). |
| 09-12 | CACI | CACI own | Blocked again - `file_upload` reports success on the hidden resume input but `input.files` stays empty. Queued for the user. |
| 09-12 | Motorola Solutions | Workday | Tab disappeared from the session group mid-run (not closed by the agent). Queued. |
| 09-12 | Amperesand | Greenhouse | Submitted, `general` variant + typed cover letter ("Enter manually"). Session = Summer 2027, SF. Page scroll drifts between calls on this board - click dropdowns by `find` ref, not coordinates. Phone Country combobox starts blank and is required. Duplicate tab of the same req left unapplied. Confirmation: /confirmation, "Thanks again for applying!" |
| 09-12 | Lyft (SWE Intern, Backend) | Greenhouse embed via careerpuck | Submitted on 2nd attempt, `backend` variant. careerpuck wraps a cross-origin Greenhouse iframe - navigate the tab to `job-boards.greenhouse.io/embed/job_app?for=lyft&token=<gh_jid>`. First submit failed: employment Start date month required. Certify field wants full name + today's date. Confirmation: /embed/job_app/confirmation, "Thank you for your interest in Lyft!" |
| 09-12 | Lyft (SWE Intern, Fullstack) | Greenhouse embed | Submitted first try, `backend` variant. Keystrokes are dropped until the tab is foregrounded - take a screenshot first, then verify `document.activeElement` after the first click. Location typeahead can sit on "Loading..." - type once and wait ~12 s (see Greenhouse addendum); retyping restarts the delay. Confirmation: /embed/job_app/confirmation. |
| 09-12 | BAE Systems (SWE Intern III) | Brassring | Session timed out mid-run (~20 min idle); tab fell back to the job-search home and the partly-filled profile was lost. |
| 09-12 | BAE Systems (SWE Intern III, req 301154) | Brassring | BLOCKED - after the session timeout the tab asks to sign in again with email + password. Password entry is user-only. Queued for the user. |
| 09-12 | Lyft (Data Science Intern, Algorithms - NY) | Greenhouse embed | Submitted, `ml` variant. Track question -> Machine Learning. Location typeahead stalled on "Fremont" through two retypes; querying "Fremont, California" returned one option immediately. Confirmation: /embed/job_app/confirmation. |
| 09-12 | Lyft (Data Science Intern, Algorithms - SF) | Greenhouse embed | Submitted, `ml` variant. Track -> Machine Learning. Location typeahead needed ~13 s on a single typed query; early retypes kept restarting it. Confirmation: /embed/job_app/confirmation. |
| 09-12 | Lyft (Data Analyst Intern) | Greenhouse embed | Submitted, `general` variant. Location typeahead hung >20 s on first query; one clear+retype then ~14 s wait resolved it. Confirmation: /embed/job_app/confirmation. All 5 Lyft tabs done. |
| 09-12 | Ibotta (SWE Intern) | Ashby | Submitted on 3rd attempt, `general` variant. Attempt 1 failed: every JS-set value ignored (email, Yes/No, relocate, Education History). Attempt 2: real clicks fixed email + Yes/No; relocate + Education History still unregistered. Attempt 3: forced radio/checkbox changes -> success. Education went in as current student, no end date shown. |
| 09-12 | Tesla (Data Engineer Intern, Fleet Analytics, Winter/Spring 2027, req 283138) | Tesla | Submitted, `backend` variant. Start Jan 4 2027, 3 months, graduation entered as Dec 15 2027, notice "More than 12 weeks", SMS consent Yes (application updates only). Needed label-clicks for radios and a scroll-to-bottom of the EEO disclosure to unlock the acknowledgment. |
| 09-12 | CACI (SWE Intern, Summer 2027) | CACI own | Resume uploaded by the user; every field filled by real keystrokes and verified by read-back. 1st submit rejected (U.S. Person = Yes reveals a required "U.S. citizen?" select; the clearance select lost its selection). Fixed, audit clean, 2nd submit clicked - page showed a spinner, then the tab left the session group before the result could be read. **Outcome unverified.** |
| 09-12 | Palantir (SWE Intern, Defense Tech) | Lever | Tailored resume `app2026:2027/Palantir/` (restored CloudFront/OAC/IAM bullet, Java-first languages, Social Network cut). Autofill had ticked all 5 office locations (form allows 1-3) - fixed to Palo Alto. Essays: S3 for hardest challenge, Kuhn Poker for not-on-resume, SWE over FDSE. **BLOCKED at submit: the extension has no click permission on jobs.lever.co** (JS reads/writes still work; do not script around it). JD requires graduating in 2028 - he graduates Dec 2027. |
| 09-12 | Garmin (SWE Intern, Olathe KS, req 19693) | iCIMS | Signed-in profile. Replaced the Dec 2025 resume with `backend` variant via proxy+xfer. Fixed autofill errors: phone Home->Mobile, source Company Website->Social Media/LinkedIn, graduated No->In Progress, school city Fremont->Santa Clara, TA end date Jun 2026. SMS consent declined (covers recruitment events). Step 2: 19 questions set via native setter + jQuery change, all read back. Step 3 review sits in a **cross-origin frame** (screenshots/real clicks only) and needs two signature checkboxes, one of which signs a **Mutual Arbitration Agreement** (waives court/class claims). User approved signing both. **Submitted** - confirmation: "Your application was submitted successfully" (job?mode=submit_apply). Part 2/2 is voluntary self-ID in the same cross-origin frame: veteran / Race / Gender native selects (decline = "I Prefer Not To Answer") + disability radios + signature; **Race, Gender, Disability and Signature are required there.** |
| 09-13 | Pylon (SWE Intern, SF on-site) | Ashby | **Submitted** on 2nd attempt with tailored resume `app2026:2027/Pylon/` (solo full-stack scope, CLIP/YOLO11 retrieval, CORS outage, 590 tests + API-contract gate; MCP bullet leads HerbsPro; tax bug + Social Network cut; Go/GraphQL not claimed). Answers: Bay Area/on-site 5 days, startups = Adorus (3 sentences), sponsorship No, visa "U.S. citizen (no visa required)". 1st submit rejected: "Missing entry: sponsorship" - the `find`-ref click made No look pressed (aria-pressed=true) but the hidden checkbox stayed false. Fixed by coordinate-clicking Yes then No. Success = inline "successfully submitted"; Jobright popup ignored. |
| 09-12 | RUN SUMMARY | - | 10 submitted (Vercel, Klaviyo, Amperesand, Lyft x5, Ibotta, Tesla). Queued for user: CACI (resume upload), BAE Systems (password sign-in), Motorola (tab left group). Amperesand duplicate tab skipped. |
