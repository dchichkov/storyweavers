"""A readable local research notebook: actual outputs and sentence provenance."""
from html import escape
from .content import EXTENDED_IDS
from .pipeline import CONFIGS


def export_research(out, outputs):
    # Imported lazily to keep the reporting module's helpers in one place.
    from .experiment import document, prose
    extended = [r for r in outputs if r["story_id"] in EXTENDED_IDS]
    if not extended:
        extended = outputs
    by_story = {r["story_id"]: r["title"] for r in extended}
    body = ('<div class="tag">STORYBOOK mini · expanded research prototype</div>'
            '<h1>A story has more than one telling.</h1>'
            '<div class="intro"><p>A borrowed lamp, a supper, and a measure of oil owed to its owner. '
            'The two longer stories follow different outcomes of this one small content family. '
            'Read each fixed trace with different prose components enabled.</p>'
            '<p>The expansion adds structured wants and speech, ownership-aware references, '
            'tense and agreement, four aggregation rules plus contrast, and paragraph planning. '
            'The five original treatments remain; two extra controls isolate markers and organization.</p>'
            '<p>No human preference results have been collected. These are rule-generated tellings '
            'from authored content, with no runtime model calls.</p>'
            '<p><a href="comparison.html">All stories and configurations</a> · '
            '<a href="report.md">Mechanical report</a> · <a href="traces.json">All traces</a></p></div>'
            '<label>Story <select id="story">')
    body += ''.join(f'<option value="{escape(sid)}">{escape(title)}</option>' for sid, title in by_story.items())
    body += '</select></label><label>Telling <select id="version">'
    body += ''.join(f'<option value="{v}">{v.replace("_", " ")}</option>' for v in CONFIGS)
    body += '</select></label><div id="readings">'
    first = True
    for r in extended:
        m = r["metrics"]
        body += (f'<section data-story="{r["story_id"]}" data-version="{r["version"]}"'
                 + ('' if first else ' hidden') + '>'
                 f'<h2>{escape(r["title"])}</h2><div class="meta">{r["version"].replace("_", " ")} · '
                 f'{m["facts"]} source facts · {m["sentences"]} realized sentence units · '
                 f'{m["words"]} words · {m["aggregations"]} revisions</div>'
                 '<article style="max-width:780px;margin-top:20px">' + prose(r["text"]) + '</article>'
                 '<details><summary>Inspect sentence plans and reference choices</summary>')
        for span in r["trace"]["sentences"]:
            body += (f'<details><summary>{escape(" + ".join(span["fact_ids"]))} · '
                     f'{span["relation"]} · paragraph {span["paragraph"] + 1}</summary>'
                     f'<p>{escape(span["text"])}</p><div class="meta">'
                     f'Boundary: {span["break_reason"]}; marker: {escape(span["marker"]) or "none"}; '
                     f'link: {span["link"] or "none"}</div><table><tr>'
                     '<th>Source</th><th>Role</th><th>Entity</th><th>Realization</th><th>Reason</th></tr>')
            for ref in r["trace"]["references"]:
                if ref["fact_id"] in span["fact_ids"]:
                    body += '<tr>' + ''.join(f'<td>{escape(str(value))}</td>' for value in (
                        ref["fact_id"], ref["role"], ref["entity"], ref["text"] or '(ellipsis)',
                        ref.get("reason", ""))) + '</tr>'
            body += '</table></details>'
        body += '</details></section>'
        first = False
    body += ('</div><h2>Research direction</h2><div class="intro">'
             '<p>The 2001 architecture motivates fixed-content component ablations. '
             'The 2002 pronoun work motivates boundary, distance, competing-reference and '
             'speaker/hearer checks. The 2003 marker work motivates selecting connectives '
             'together with clause revision. Our rules are smaller implementations inspired '
             'by these concerns, not reproductions of the published algorithms or scores.</p>'
             '<p><a href="https://intellimedia.ncsu.edu/wp-content/uploads/sites/42/npg-ijcai01.pdf">'
             'Callaway &amp; Lester 2001</a> · <a href="https://aclanthology.org/P02-1012/">'
             'Callaway &amp; Lester 2002</a> · <a href="https://aclanthology.org/P03-1034/">'
             'Callaway 2003</a></p><p>Mechanical checks cover fact and role preservation, '
             'not literary quality or every possible interpretation of the English. '
             'The two longer streams share most of their premise; they are two paths '
             'through one authored family, not evidence of broad story diversity.</p></div>')
    script = '''<script>
const story = document.getElementById('story'), version = document.getElementById('version');
function update() {
  for (const section of document.querySelectorAll('#readings > section')) {
    section.hidden = section.dataset.story !== story.value || section.dataset.version !== version.value;
  }
}
story.addEventListener('change', update); version.addEventListener('change', update);
</script>'''
    (out / "research.html").write_text(document("STORYBOOK — expanded research", body, script), encoding="utf-8")
