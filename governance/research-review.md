# Research review and publication boundary

Maintain a separate `research_review` reference in the project's overall location JSON. Its target uses `schemas/research-review.schema.json`. Unknowns are first-class records, not unofficial facts embedded in the published location list.

Each candidate has a stable ID, approximate or unknown location, jurisdiction, hypothesis, separate activity claims, evidence, questions, field observations and a review decision. Stages: inbox -> researching -> field_checked -> ready_for_review -> promoted, or rejected. Field checking records what was seen; it does not automatically verify ownership or permission. Use separate candidates for independent claims that mature at different times.

Evidence kinds distinguish authority, activity traces, on-site observations and map references. Strava/AllTrails activity is evidence of reported use, not permission, ownership, safety, current passability or parking rights. Absence of heat does not imply a closure. Capture sport, displayed period, view date, scale and licensing/access limitations in the evidence summary. Do not record a heatmap observation before actually viewing it. Use platform links until an authorized portable dataset/export is available; do not embed session credentials or signed tile URLs.

Every queue record has publish=false, including promoted records. Promotion is an explicit reviewed copy of supported claims into the official records, linked through official_record_id, reviewer, date and rationale. The queue remains an audit trail. Activity-specific authoritative evidence is required for any non-unknown permission claim; unresolved claims must be split out before promotion. Schema validation checks structure and evidence categories, not the truth of cited pages.

Research QGIS layers carry `qgis_meta/research_only=true`; research layouts carry `qgis_meta/layout_purpose=research` and a visible RESEARCH / NOT PUBLISHED heading. The native validator rejects tagged research layers in publication layouts even if the layer is hidden in the project tree. Never add a research overlay to a published layout's saved map layer set. Separate research projects are preferred while a user is editing a production project.

Run `qgis-meta research-check <review.json>` before committing research. Run full QGIS validation for registered production projects. This queue check is separate from, and does not claim to replace, native cartographic tests. `tests/test_research_review.py` exercises invalid promotion, trace-based permissions, missing references and publication leakage.
