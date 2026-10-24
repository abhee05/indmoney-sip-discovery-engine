# Independent manual labelling

Open data/manual_labels_blank.json or use the app's Manual labels tab. Read the original source, not the AI-assisted paraphrase. The supplied excerpt is short and may not contain the full context. If the original cannot be located, mark it unassessable and replace it before freezing the golden set.

For each of the 20 records fill:

- mf_relevance: yes / no / unclear. A stock SIP is not a mutual-fund SIP.
- first_time_status: explicit_first_time / explicit_experienced / unknown.
- journey_stage: pre_start / registration / first_payment / ongoing / pause_stop / restart / unknown. Do not infer months from review date.
- continuation_status: continuing / considering_pause_stop / paused_stopped / failed_payment / unknown. A request to add a pause feature is not proof of pausing.
- primary_theme: use a short phrase in your own words; other/unknown is valid. We will consolidate overlapping phrases after the development labels.
- evidence_quote: a short phrase from the original supporting the labels.
- confidence: high / medium / low.
- notes: missing context, alternative interpretation, explicit segment details, contradiction.

Do not provide account numbers, PAN details or portfolio screenshots. Do not guess income stability, age, tenure or the investor's source of money.

After labelling: freeze a copy and assign 12 development / 8 holdout records by thread. Improve prompts on development items only. Report accuracy per field (correct / assessable), abstention coverage, macro F1 for themes where counts permit, and item-level disagreements. An 8-item holdout is directional, not strong statistical evidence. Do not report results before predictions and labels exist.
