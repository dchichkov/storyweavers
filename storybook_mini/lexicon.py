"""Small sense-specific lexicon; variation never changes semantic roles."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Verb:
    lemma: str
    past: str
    # Slots determine sentence-planning roles, not arbitrary finished sentences.
    object_required: bool = False
    target_preposition: str = ""
    participle: str = ""


LEXICON = {
    "live": (Verb("live", "lived", target_preposition="in"),),
    "have": (Verb("have", "had", True),),
    "need": (Verb("need", "needed", True, "at"),),
    "light": (Verb("light", "lit", True), Verb("kindle", "kindled", True)),
    "carry": (Verb("carry", "carried", True, "to"),),
    "extinguish": (Verb("blow out", "blew out", True, participle="blown out"),),
    "shield": (Verb("shield", "shielded", True),),
    "hang": (Verb("hang", "hung", True, "on"),),
    "thank": (Verb("thank", "thanked", True),),
    "shine": (Verb("shine", "shone", target_preposition="over"),),
    "go": (Verb("walk", "walked", target_preposition="to"),),
    "meet": (Verb("meet", "met", True),),
    "launch": (Verb("launch", "launched", True), Verb("send up", "sent up", True)),
    "snag": (Verb("catch", "caught", target_preposition="on"),),
    "retrieve": (Verb("take down", "took down", True, "from", participle="taken down"),),
    "give": (Verb("give", "gave", True, "to", participle="given"),),
    "mend": (Verb("mend", "mended", True, "with"),),
    "glow": (Verb("glow", "glowed", target_preposition="against"),),
    "feel": (Verb("feel", "felt"),),
    "be": (Verb("be", "was", participle="been"),),
    "say": (Verb("say", "said"),),
    "want": (Verb("want", "wanted"),),
    "stand": (Verb("stand", "stood", target_preposition="beside"),),
    "sit": (Verb("sit", "sat", target_preposition="on"),),
    "wait": (Verb("wait", "waited", target_preposition="beside"),),
    "look": (Verb("look at", "looked at", True),),
    "find": (Verb("find", "found", True), Verb("discover", "discovered", True)),
    "take": (Verb("take", "took", True, participle="taken"),),
    "put": (Verb("put", "put", True, "on"),),
    "put_in": (Verb("put", "put", True, "in"),),
    "open": (Verb("open", "opened", True),),
    "close": (Verb("close", "closed", True),),
    "check": (Verb("check", "checked", True), Verb("examine", "examined", True)),
    "turn": (Verb("turn", "turned", True),),
    "fill": (Verb("fill", "filled", True, "with"),),
    "pour": (Verb("pour", "poured", True, "into"),),
    "borrow": (Verb("borrow", "borrowed", True, "from"),),
    "lend": (Verb("lend", "lent", True, "to"),),
    "return": (Verb("return", "returned", True, "to"),),
    "need_for": (Verb("need", "needed", True, "for"),),
    "bake": (Verb("bake", "baked", True),),
    "burn": (Verb("burn", "burned"),),
    "leave": (Verb("leave", "left", True),),
    "keep": (Verb("keep", "kept", True),),
    "touch": (Verb("touch", "touched", True),),
    "smile": (Verb("smile", "smiled"),),
    "nod": (Verb("nod", "nodded"),),
    "arrive": (Verb("arrive", "arrived", target_preposition="at"),),
    "walk": (Verb("walk", "walked", target_preposition="along"),),
    "fade": (Verb("fade", "faded"),),
    "smell": (Verb("smell", "smelled", True),),
}


def choose_words(clauses, enabled=True):
    """Annotate by predicate frequency; preserve the input and proposition IDs."""
    from dataclasses import replace
    seen, result, previous = {}, [], None
    for c in clauses:
        options = LEXICON[c.predicate]
        n = seen.get(c.predicate, 0)
        verb = options[n % len(options)] if enabled else options[0]
        if (enabled and c.predicate == "say" and previous and previous.predicate == "say"
                and c.scene == previous.scene and c.listener == previous.subject
                and c.subject == previous.listener):
            verb = Verb("reply", "replied")
        seen[c.predicate] = n + 1
        # Embedded content shares the lexicon but has its own speech/goal scope.
        goal = replace(c.goal, verb=LEXICON[c.goal.predicate][0]) if c.goal else None
        speech = replace(c.speech, verb=LEXICON[c.speech.predicate][0]) if c.speech else None
        result.append(replace(c, verb=verb, goal=goal, speech=speech))
        previous = c
    return tuple(result)
