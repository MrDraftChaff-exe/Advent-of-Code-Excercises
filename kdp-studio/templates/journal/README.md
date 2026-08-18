# Journal / logbook template notes

Typical trim: `trade` (6×9) or `a5ish` (5.5×8.5).  
Cream paper feels more “notebook.” Single-sided usually off (print both sides).

Page ideas: lined, dotted, prompt pages, gratitude, reading log, garden log, hiking log.

```bash
cd kdp-studio/tools
python3 -m kdp_studio new --slug my-journal --type journal --title "..." --trim trade --designs 100
```

Set `"single_sided": false` in `meta.json` when pages should print double-sided.
