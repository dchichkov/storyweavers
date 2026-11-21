"""Typed speech/scene constructions layered over the frozen portable grammar."""
from copy import deepcopy
from dataclasses import dataclass, field

from ..grammar import Node, seq
from ..portable.language import Language
from ..portable.nouns import pronoun

EXTRA = {
    "nouns": {"cup": {}, "handle": {}, "thumb": {}, "thumb rest": {}, "dent": {},
              "tea": {"mass": True}, "kiln": {}, "workshop": {}, "atlas": {},
              "crater": {}, "class": {}, "book": {}, "star": {}, "finger": {}},
    "adjectives": {w: {} for w in ("stiff", "wide", "thick", "smooth", "dented", "steady", "hot", "cool")},
    "adverbs": {w: {} for w in ("together", "twice", "gently", "out")},
    "prepositions": {"into": {}},
    "verbs": {
        "need": {"forms": ["need", "needed", "needed"], "valencies": ["V2", "VV"]},
        "give": {"forms": ["give", "gave", "given"], "valencies": ["V3"]},
        "help": {"forms": ["help", "helped", "helped"], "valencies": ["V2"]},
        "read": {"forms": ["read", "read", "read"], "valencies": ["V", "V2"]},
        "sketch": {"forms": ["sketch", "sketched", "sketched"], "valencies": ["V2"]},
        "promise": {"forms": ["promise", "promised", "promised"], "valencies": ["VV"]},
        "search": {"forms": ["search", "searched", "searched"], "valencies": ["V2"]},
        "save": {"forms": ["save", "saved", "saved"], "valencies": ["V2"]},
        "pour": {"forms": ["pour", "poured", "poured"], "valencies": ["V2"]},
        "fire": {"forms": ["fire", "fired", "fired"], "valencies": ["V2"]},
        "glaze": {"forms": ["glaze", "glazed", "glazed"], "valencies": ["V2"]},
        "smooth": {"forms": ["smooth", "smoothed", "smoothed"], "valencies": ["V2"]},
        "shape": {"forms": ["shape", "shaped", "shaped"], "valencies": ["V2"]},
        "slip": {"forms": ["slip", "slipped", "slipped"], "valencies": ["V"]},
    },
}


class SpeechLanguage(Language):
    def __init__(self, world, tense="past", lexicon=None):
        super().__init__(world, tense)
        self.lexicon = deepcopy(self.lexicon)
        for additions in (EXTRA, lexicon or {}):
            for category, entries in additions.items():
                self.lexicon[category].update(deepcopy(entries))

    def ref(self, entity_id, *, subject=False, first=False, adjectives=()):
        # Short scenes name actors explicitly; local dialogue binds I/you instead.
        e = self.world.entities[entity_id]
        self.discourse.introduce(entity_id, pronoun=e.pronoun, number=e.number)
        return super().ref(entity_id, subject=False, first=first, adjectives=adjectives)

    def line(self, speaker, content, *, listener=None):
        if speaker not in self.world.entities or self.world.entities[speaker].kind != "person":
            raise ValueError("dialogue needs a physical speaker")
        if listener is not None and self.world.entities[speaker].location != self.world.entities[listener].location:
            raise ValueError("dialogue participants must be together")
        # Quotes are explicit grammar terminals, not lost to legacy text tokenization.
        return seq("dialogue.speaker:" + speaker, self.ref(speaker).subject,
                   "said" if self.tense == "past" else "says", ",",
                   Node("text", "quote.open", ("“",)), content.node, ".",
                   Node("text", "quote.close", ("”",)))

    def me(self, vp, *, negative=False):
        return self.s(pronoun("I"), vp, tense="present", negative=negative)

    def you(self, vp, *, negative=False):
        return self.s(pronoun("you"), vp, tense="present", negative=negative)

    def using(self, actor, action, instrument):
        """Two constructions for the same grounded instrument/action relation."""
        return self.either(self.s(actor, self.v("use", instrument, action)),
                           self.s(actor, self.adv(action, self.pp("with", instrument))))


@dataclass
class Scene:
    node: Node
    claims: list[dict] = field(default_factory=list)


def scene(*parts, qa=()):
    """Claims annotate the selected scene; only visible realized scenes feed QA."""
    from ..portable.features import Sentence
    nodes = [Language.utter(p) if isinstance(p, Sentence) else p for p in parts]
    return Scene(seq("story.scene", *nodes), list(qa))


def claim(key, kind, question, answer, *entities):
    return dict(key=key, kind=kind, question=question, answer=answer, entities=list(entities))


def detokenize(tokens):
    """Punctuation formatting only; words/quotes all come from the sampled forest."""
    out, capitalize = "", True
    for token in tokens:
        if token in {",", ";", ".", "!", "?", "”"}:
            out += token
            if token in {".", "!", "?"}:
                capitalize = True
        elif token == "“":
            out += (" " if out else "") + token
            capitalize = True
        else:
            if capitalize:
                token = token[:1].upper() + token[1:]
            out += ("" if not out or out.endswith("“") else " ") + token
            capitalize = False
    return out
