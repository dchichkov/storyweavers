"""Five faithful switch settings, with machine-inspectable content accounting."""
from dataclasses import asdict, dataclass
from collections import Counter
import re
from .lexicon import choose_words
from .planning import plan_sentences
from .realization import realize
from .revision import revise


@dataclass(frozen=True)
class Config:
    discourse: bool = True
    lexical: bool = True
    revision: bool = True
    markers: bool = True
    organization: bool = True


VERSIONS = {"full": Config(), "no_revision": Config(revision=False),
            "no_lexical": Config(lexical=False), "no_discourse": Config(discourse=False),
            "all_off": Config(False, False, False)}

# Keep the five original treatments intact. These two isolate later additions.
DIAGNOSTICS = {"no_markers": Config(markers=False),
               "no_organization": Config(organization=False)}
CONFIGS = {**VERSIONS, **DIAGNOSTICS}


def content_roles(fact):
    roles = [(role, getattr(fact, role)) for role in ("subject", "object", "target", "listener", "companion")
             if getattr(fact, role)]
    for kind in ("goal", "speech"):
        child = getattr(fact, kind)
        if child:
            roles.extend((kind + "." + role, getattr(child, role)) for role in
                         ("subject", "object", "target") if getattr(child, role))
    return roles


def audit_realization(snapshot, spans, references):
    expected = [f.id for f in snapshot.story.facts]
    actual = [fid for span in spans for fid in span["fact_ids"]]
    if actual != expected:
        raise ValueError("Realization dropped, duplicated, or reordered content")
    for fact in snapshot.story.facts:
        actual_roles = Counter((r["role"], r["entity"]) for r in references if r["fact_id"] == fact.id)
        if actual_roles != Counter(content_roles(fact)):
            raise ValueError(f"{fact.id}: realization changed a semantic role")
    for span in spans:
        if span["marker"] and not span["link"]:
            raise ValueError("Ungrounded discourse marker")
    return {"ordered_facts": len(expected), "realized_roles": len(references),
            "content_preserved": True, "scope": "structural; not a proof about all English interpretations"}


def generate(snapshot, version="full"):
    config = CONFIGS[version]
    planned = plan_sentences(snapshot)
    lexicalized = choose_words(planned, config.lexical)
    revised = revise(lexicalized, config.revision, markers=config.markers)
    text, spans, references = realize(revised, snapshot.story.entities, config.discourse,
                                     organization=config.organization)
    audit = audit_realization(snapshot, spans, references)
    word_count = len(re.findall(r"\b[\w’]+\b", text))
    return {"story_id": snapshot.story.id, "title": snapshot.story.title, "version": version,
            "config": asdict(config), "content_sha256": snapshot.fingerprint,
            "text": text, "audit": audit,
            "metrics": {"facts": audit["ordered_facts"], "sentences": len(spans),
            "words": word_count, "words_per_sentence": round(word_count / len(spans), 2),
            "subject_pronouns": sum(r["pronoun"] and r["role"] == "subject" for r in references),
            "pronouns": sum(r["pronoun"] for r in references),
            "aggregations": sum(s["relation"] != "single" for s in spans),
            "paragraphs": text.count("\n\n") + 1,
            "markers": sum(bool(s["marker"]) for s in spans),
            "revision_rules": dict(Counter(s["relation"] for s in spans if s["relation"] != "single")),
            "structured_utterances": sum(bool(c.speech) for c in planned),
            "grounded_possessives": sum(r.get("reason") == "grounded_possessor" for r in references),
            "verb_forms": len({c.verb.past for c in lexicalized})},
            "trace": {"planned": [asdict(c) for c in planned],
                      "lexicalized": [asdict(c) for c in lexicalized],
                      "revised": [asdict(s) for s in revised],
                      "sentences": spans, "references": references}}
