"""Realize functional clauses after revision, with scoped dialogue and morphology."""
from .discourse import DiscourseHistory
from .morphology import verb_phrase
from .organization import organize
from .revision import is_dialogue


def capitalize(text):
    return text[:1].upper() + text[1:]


def realize(sentences, entities, discourse=True, *, organization=True, paragraph_sentences=4):
    history = DiscourseHistory(entities, discourse)
    by_id = history.entities
    paragraphs, paragraph, spans = [], [], []
    current_paragraph = 0
    last_dialogue = None
    def ent_is_person(eid):
        return bool(by_id[eid].name) or by_id[eid].pronoun in {"he", "she"}
    for organized in organize(sentences, organization, paragraph_sentences):
        sentence = organized.sentence
        a = sentence.clauses[0]
        if organized.paragraph != current_paragraph and paragraph:
            paragraphs.append(" ".join(paragraph))
            paragraph = []
        current_paragraph = organized.paragraph
        history.start_sentence(a.scene)

        def clause(c, *, omit_subject=False, omit_verb=False, relative=False,
                   force_name=False, force_object=False, prefix="", scope="narration",
                   speaker="", listener="", infinitive=False):
            owners = dict(c.owners)
            refs = [r for r in (c.object, c.target, c.companion) if r]

            def reference(eid, role, force=False):
                return history.refer(eid, prefix + role, c.fact_id,
                    refs if role == "subject" else (), force,
                    owner=owners.get(eid, ""), binding=c.subject,
                    scope=scope, speaker=speaker, listener=listener, possessive=c.predicate != "have")

            if omit_subject or relative:
                history.elide(c.subject, prefix + "subject", c.fact_id,
                              "relative_subject" if relative else "shared_subject")
                subject = ("who" if ent_is_person(c.subject) else "which") if relative else ""
            else:
                subject = reference(c.subject, "subject", force_name)
            ent = by_id[c.subject]
            person = 1 if scope == "speech" and c.subject == speaker else (
                2 if scope == "speech" and c.subject == listener else 3)
            parts = [subject]
            if not omit_verb:
                parts.append(verb_phrase(c.verb, "infinitive" if infinitive else c.tense,
                                         c.negative, person=person,
                                         plural=ent.number == "plural" or (person == 3 and ent.pronoun == "they")))
            if c.object:
                parts.append(reference(c.object, "object", force_object))
            if c.companion:
                parts.extend(("with", reference(c.companion, "companion", force=True)))
            if c.target:
                parts.extend((c.verb.target_preposition, reference(c.target, "target")))
            if c.complement:
                parts.append(c.complement)
            if c.goal:
                parts.extend(("to", clause(c.goal, omit_subject=True, infinitive=True,
                                          prefix="goal.", scope=scope, speaker=speaker, listener=listener)))
            text = " ".join(p for p in parts if p)
            if c.cue:
                text = c.cue + ", " + text
            return text

        if is_dialogue(a):
            tag = clause(a, force_name=True)
            if a.listener:
                pair = frozenset((a.subject, a.listener))
                if (discourse and last_dialogue and last_dialogue[0] == pair
                        and last_dialogue[1] == a.scene and history.index - last_dialogue[2] <= 2):
                    history.elide(a.listener, "listener", a.fact_id, "active_conversation")
                else:
                    tag += " to " + history.refer(a.listener, "listener", a.fact_id, force_name=True)
                last_dialogue = (pair, a.scene, history.index)
            if a.speech:
                quote = capitalize(clause(a.speech, prefix="speech.", scope="speech",
                                          speaker=a.subject, listener=a.listener))
                text = f'“{quote},” {tag}.'
            else:
                if not a.quote.endswith((".", "!", "?")):
                    raise ValueError(f"{a.fact_id}: dialogue needs terminal punctuation")
                if a.listener:
                    quote = a.quote[:-1] + "," if a.quote.endswith(".") else a.quote
                    text = f'“{quote}” {tag}.'
                else:
                    text = capitalize(tag) + ', “' + a.quote + '”'
        elif sentence.relation == "coordinate":
            text = capitalize(clause(a)) + " and " + clause(sentence.clauses[1], omit_subject=True) + "."
        elif sentence.relation == "shared_verb":
            text = capitalize(clause(a, force_object=True)) + " and " + clause(
                sentence.clauses[1], omit_subject=True, omit_verb=True, force_object=True) + "."
        elif sentence.relation == "relative":
            text = capitalize(clause(a, force_object=True)) + ", " + clause(sentence.clauses[1], relative=True) + "."
        elif sentence.relation == "cause":
            text = "Because " + clause(a, force_name=True) + ", " + clause(sentence.clauses[1], force_name=True) + "."
        elif sentence.relation == "contrast":
            b = sentence.clauses[1]
            text = capitalize(clause(a, force_name=True)) + ", but " + clause(
                b, omit_subject=a.subject == b.subject, force_name=True) + "."
        else:
            text = capitalize(clause(a)) + "."
            if sentence.marker:
                # Lowercase a common-noun/pronoun clause start after a cue, preserving proper names.
                raw = text
                # Use the realized start: a proper-name entity may have become a pronoun.
                if raw.split(" ", 1)[0] in {"He", "She", "It", "They", "The", "A", "An", "Some"}:
                    raw = text[:1].lower() + text[1:]
                text = sentence.marker + ", " + raw
        paragraph.append(text)
        spans.append({"text": text, "fact_ids": [c.fact_id for c in sentence.clauses],
                      "relation": sentence.relation, "scene": a.scene,
                      "marker": sentence.marker, "link": sentence.link,
                      "paragraph": organized.paragraph, "break_reason": organized.break_reason})
        history.end_sentence(sentence.clauses[-1].subject, is_dialogue(a))
    if paragraph:
        paragraphs.append(" ".join(paragraph))
    return "\n\n".join(paragraphs), spans, history.choices
