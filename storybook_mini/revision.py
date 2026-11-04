"""Conservative tree revisions coupled to rhetorical marker selection."""
from dataclasses import dataclass
from .planning import Clause


@dataclass(frozen=True)
class Sentence:
    clauses: tuple[Clause, ...]
    relation: str = "single"
    marker: str = ""
    link: str = ""


def is_dialogue(c):
    return bool(c.quote or c.speech)


def boundary(a, b):
    return (a.scene != b.scene or b.paragraph_break or b.topic != a.topic
            or is_dialogue(a) or is_dialogue(b) or bool(b.cue))


def estimate(c):
    return (4 + len(c.complement.split()) + bool(c.object) * 3 + bool(c.target) * 4
            + bool(c.goal) * 7 + bool(c.companion) * 3)


def revise(clauses, enabled=True, *, markers=True, max_words=28):
    result, i = [], 0
    while i < len(clauses):
        a = clauses[i]
        b = clauses[i + 1] if i + 1 < len(clauses) else None
        relation, marker, link = "single", "", ""
        if enabled and b and not boundary(a, b) and estimate(a) + estimate(b) <= max_words:
            if b.cause == a.fact_id and not a.cue and markers:
                relation, marker, link = "cause", "because", b.cause
            elif b.contrast == a.fact_id and markers:
                relation, marker, link = "contrast", "but", b.contrast
            elif not (b.cause or b.contrast):
                if (a.object and not (a.target or a.companion) and b.subject == a.object and b.predicate == "be"
                        and not b.negative and b.tense == a.tense and not a.goal):
                    relation = "relative"
                elif (a.subject == b.subject and a.predicate == b.predicate
                      and a.object and b.object and a.object != b.object
                      and a.verb == b.verb and not (a.target or b.target)
                      and not (a.companion or b.companion)
                      and a.tense == b.tense and not (a.negative or b.negative)
                      and not (a.goal or b.goal or a.complement or b.complement)):
                    relation = "shared_verb"
                elif a.subject == b.subject:
                    relation = "coordinate"
        if relation == "single":
            if markers and i and not a.cue and clauses[i-1].scene == a.scene:
                if a.cause == clauses[i-1].fact_id:
                    marker, link = "As a result", a.cause
                elif a.contrast == clauses[i-1].fact_id:
                    marker, link = "However", a.contrast
            result.append(Sentence((a,), relation, marker, link))
            i += 1
        else:
            result.append(Sentence((a, b), relation, marker, link))
            i += 2
    return tuple(result)
