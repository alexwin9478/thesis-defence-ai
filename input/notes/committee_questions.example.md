# Committee Q&A Notes — Example Template
# Copy this file to committee_questions.md and fill in your own questions and rough notes.
# The committee_qa agent (Agent 11) reads this file and polishes your rough notes into
# defence-ready spoken answers with 3-tier structure.
#
# FORMAT: For each question, write the question followed by your rough notes.
# Separate questions with "---". No need to write polished answers — just your raw thoughts.
# The agent will do the polishing.

---

Q: Summarize your thesis in 3 sentences / 3 minutes
Notes: [Your rough notes — key points you want to hit, results to mention, framing you like]

---

Q: Why did you choose [method X] instead of [method Y]?
Notes: [Your reasoning — pros/cons you considered, references you can cite if pressed]

---

Q: What is the main limitation of your approach?
Notes: [Be honest here — the agent will help you frame it constructively. Mention: what the limitation is, why it exists, and what the path forward looks like]

---

Q: How would you transfer this to industrial application?
Notes: [Current industrial examples if any, what would need to change, safety/certification considerations]

---

Q: What is the Technology Readiness Level (TRL)?
Notes: [Your TRL estimate and what specifically you validated vs. what remains for higher TRL]

---

Q: What are the main contributions of your thesis?
Notes: [List 3–5 contributions in your own words — the agent will help you prioritise and articulate them]

---

Q: [Add your own known committee question here]
Notes: [Your rough notes]

---

# EXAMPLE (filled in — matches the format the agent expects)
# Q: Why a GRU instead of an LSTM?
# Notes: GRU has fewer parameters (no separate cell state), trains faster on our dataset,
# and the reduced gate structure means fewer dynamic states when embedded in the MPC OCP.
# LSTM would add ~2x the state dimension to the acados problem, hurting real-time performance.
# Also: GRU showed comparable accuracy on our validation set — no performance drop.
