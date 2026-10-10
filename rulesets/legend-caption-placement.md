# Legend-caption placement

Statement: Any statement on the legend should not be repeated on the map.

Implementation: `qgis_meta.cartography.check_legend_label_repetition`, called for each linked native layout legend. Violations fail project loading/cartographic validation; unsupported labeling remains blocked. See `governance/legends-and-notes.md` for normalization, the `qgis_meta/label_role=legend-caption` contract, preserved place/index labels and scope limitations.

Regression checks: `tests/test_legend_caption_policy.py` exercises repeated field text, normalized punctuation/case, expressions, permitted place names and numbers, paraphrases on declared caption layers, empty labels and disabled labels.
