# Finish the AI-off exercise, then record the videos

You can record the prepared demonstrations now using the completed AI-assisted
retrospective COST-01 example. It must be described that way. The separate
AI-off requirement still follows **predict → GitHub commit → first run → result**.
You will handle GitHub publishing. Nothing in this guide is a prediction or
evidence that the exercise has been completed.

## 1. Prepare the baseline before the independent exercise

Publish the contents of this Project2_Final folder, including its subfolders,
to your own repository. Do not publish just the ZIP or the earlier standalone
robo_app.py. Start the combined app using the repository README:

```console
python -m streamlit run app.py
```

From the shared course workspace, the equivalent command is:

```powershell
.\.venv\Scripts\python.exe -m streamlit run .\Projects\Meridian\Project2_Final\app.py
```

Use **Meridian mandate — Project 2** mode, **Saved Project 2 funds**, default
controls, no uploaded CSV. Confirm objective 6.50%, reserve 3%, annual cost
25 bp, 36-month toggle off, required vintage available, and SGOV as the only
reserve-eligible fund. Keep the data and code unchanged during the exercise.
The default result is already disclosed and can be used as the baseline.

Open the two blank worksheets in `validation/templates/`. They are instructions,
not completed records. Take a baseline screenshot showing the current controls,
weights and mandate-verdict table. Also retain the published code's commit URL.

To record UTC time and local source hashes from the repository folder:

```powershell
(Get-Date).ToUniversalTime().ToString("o")
Get-FileHash -LiteralPath .\app.py, .\portfolio.py, .\review.py, .\project.json, .\data\prices.csv -Algorithm SHA256
```

## 2. Close AI and write your own prediction

Close this chat and other AI tools, including coding/chat assistance. After
that, choose **one previously unrun input change yourself**. Do not ask AI to
choose, predict or test it. Do not make the change in the app yet.

Use a main Meridian control so you can predict both the portfolio effect and
its mandate verdict. Keep all other controls fixed. Avoid every result already
disclosed in the app, scripts, tests and prior work, including the published
cost/window/estimate/reserve stress demonstrations and personal-mode probes.
An already seen outcome is not an unseen test.

On GitHub, choose **Add file → Create new file** and name it
`validation/ai_off_prediction.md`. Copy the *blank headings* from the prediction
worksheet. Fill the values, reasoning and predicted direction/range in **your
own words**, with AI closed. Include what you expect the mandate verdict to be
and what result would change your recommendation. Do not leave blanks.

The template was prepared by Codex before the session; disclose that fact.
Your substantive prediction and reasoning must be yours. Only attest that AI
was closed if that is true.

Click **Commit changes**, with a message such as “Lock independent prediction
before changed-input run,” and commit to your submission branch. Open the
committed file to verify it is actually on GitHub. Save the commit URL/SHA and
the displayed commit time. For an immutable file link, press **y** while viewing
the file and copy the resulting URL. **Do not run until the prediction is
committed and visible.**

## 3. Make the one change and retain the first result

Keep AI closed. Record the UTC time. Start from the baseline, change only the
locked input to your committed value, and let Streamlit rerun. For typed numeric
values, finish entering the value and press Enter; avoid stepping through a
series of exploratory values. Record any unintended intermediate run honestly.

Capture the **first result**: exact input values, current allocation, gross/net
estimate, risk, reserve, current-control mandate verdict and any stop message.
If the change is infeasible or stops the process, that is the result. Do not
try another value to obtain a nicer outcome.

Use `validation/ai_off_result.md` for the completed result worksheet. Record
actual versus predicted, why they agreed/differed, and whether the mandate
verdict or recommendation changed. Save screenshots under
`validation/ai_off_evidence/`. Record the run time separately from the later
upload/commit time. Keep the original prediction intact. Restore the defaults
only after the result has been captured.

Commit the result file and evidence to GitHub in a **later commit**. Save that
commit URL/SHA. You can return to AI after both commits; disclose any assistance
received after the prediction was locked. An incorrect prediction is acceptable;
an altered or backdated prediction is not.

## 4. Assemble the record and decide what you own

Keep the prediction and first-result files as primary evidence. Put both commit
links, the actual comparison and the decision consequence into
`docs/validation-and-ai-use.md` and
`validation/LOCKED_CHANGED_INPUT_RECORD.md`. You can send the two links and
evidence back to Codex for help incorporating them after your exercise.

Then review the memo and scripts. When you can truthfully stand behind the
analysis and recommendation, confirm the ownership statement. You can rehearse
earlier, but record the final first-person statement only after that review.
AI assistance with code/drafts and your own ownership can both be disclosed.

## 5. Recording setup

Use your preferred screen recorder with microphone audio. Aim for about
3–4 minutes per video unless the course gives another limit. Show readable
browser/editor text; hide unrelated windows and notifications. A webcam is not
specified in the supplied requirements. Make a short audio check before the
final takes.

Open the live app, the README, decision memo, validation record and relevant code
tabs in advance. Show the app as the app; the terminal runner is supporting
evidence. Read the two opening statements in every video. Do not read bracketed
screen directions, editing notes or placeholders aloud.

| Video | Screen order | Full read-aloud script |
| --- | --- | --- |
| 1 — How it changed | Original Lab 13 mandate → default app/baselines → COST-01 evidence → your completed locked record → selected Rule B | [Video 1](videos/VIDEO_1_HOW_IT_CHANGED.md) |
| 2 — Code walkthrough | README/start command → live app → portfolio.py/review.py → source card → disclosed stresses/process halt → optional short personal-mode example | [Video 2](videos/VIDEO_2_TECHNICAL.md) |
| 3 — Committee presentation | **First frame: app running live in Meridian mode.** Keep it visible for the opening statements → baseline verdicts → decision memo → allocation range/conditions/triggers | [Video 3](videos/VIDEO_3_COMMITTEE.md) |

Video 1 now has complete draft narration using the current pending exercise
status and proposed personal reflection. After the exercise, update that passage
with the actual result and review the reflection so it matches your thinking.
The other scripts also need your review; do not imply a human exercise or
acceptance you have not completed. Preserve adverse results in your presentation.

## 6. YouTube, transcripts and the final files

Upload three separate recordings to YouTube. Use Public or Unlisted access
that your instructor can open, subject to course instructions. Video files do
not go in the repository or Brightspace submission.

In **YouTube Studio → Subtitles**, select each video, set the language, and
publish/add or review its caption track. Automatic captions may take time;
review them, especially percentages, fund tickers and disclosure wording.
Verify the video has usable captions and a transcript before submitting.
Save a transcript that matches what you actually said, for example:

```text
videos/transcripts/video-1.md
videos/transcripts/video-2.md
videos/transcripts/video-3.md
```

Each transcript should include its video title/link and actual spoken words.
A script is not a verified transcript. Set the repository, video, transcript
and prediction/result commit locations in `delivery.json`. After the records
and ownership wording are finalized, run:

```console
python tools/prepare_delivery.py
```

Verify the manifest links. Re-upload the finalized Markdown files to GitHub and
attach the *same versions* of `docs/decision-memo.md`,
`docs/validation-and-ai-use.md`, and the manifest to Brightspace. The generated
`Project2_Brightspace_Attachments` folder holds matching copies.

Official interface help: [create GitHub files](https://docs.github.com/en/repositories/working-with-files/managing-files/creating-new-files),
[GitHub permanent links](https://docs.github.com/en/repositories/working-with-files/using-files/getting-permanent-links-to-files),
[add YouTube captions](https://support.google.com/youtube/answer/2734796),
[review automatic captions](https://support.google.com/youtube/answer/6373554).
