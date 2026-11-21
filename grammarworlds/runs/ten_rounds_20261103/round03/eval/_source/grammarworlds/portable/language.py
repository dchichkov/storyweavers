"""Small authoring facade over the ported, typed construction modules."""
from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path

from ..grammar import choice, seq
from . import clauses, nouns, verbs
from .discourse import Discourse
from .features import AP, Adv, CN, NP, VP, Sentence
from .morphology import verb
from .catalog import rule

ROOT = Path(__file__).resolve().parent


@lru_cache(maxsize=1)
def load_lexicon():
    data = {k: {} for k in ("names", "nouns", "adjectives", "prepositions", "adverbs", "verbs")}
    for path in sorted((ROOT / "lexicon").glob("*.json")):
        for kind, entries in json.loads(path.read_text()).items():
            if isinstance(entries, list):
                entries = dict.fromkeys(entries, {})
            for word, entry in entries.items():
                if word in data[kind]:
                    raise ValueError(f"duplicate lexicon entry {kind}/{word}")
                data[kind][word] = entry
    return data


class Language:
    def __init__(self, world, tense="past"):
        if tense not in {"past", "present"}:
            raise ValueError("supported tenses: past, present")
        self.world, self.tense = world, tense
        self.lexicon = load_lexicon()
        self.discourse = Discourse.from_world(world)

    def cn(self, word, *adjectives):
        result = nouns.use_n(word, self.lexicon["nouns"][word])
        for adjective in reversed(adjectives):
            result = nouns.adj_cn(self.a(adjective), result)
        return result

    def n(self, word, *adjectives, det="the", number="singular"):
        return nouns.det_cn(self.cn(word, *adjectives), det, number)

    def a(self, word):
        if word not in self.lexicon["adjectives"]:
            raise KeyError(f"add adjective {word!r} to a lexicon module")
        return AP(seq("lexical.adjective", word))

    def ref(self, entity_id, *, subject=False, first=False, adjectives=()):
        entity = self.world.entities[entity_id]  # unknown/unembedded referent fails closed
        known = entity_id in self.discourse.resolve()
        if entity.kind == "person":
            result = nouns.proper(entity.noun, entity.number)
        else:
            # These are lexicon decompositions, not sentence templates.
            aliases = {"little drum": ("drum", "little"), "second drum": ("drum", "second")}
            word, *modifiers = aliases.get(entity.noun, (entity.noun,))
            entry = self.lexicon["nouns"][word]
            det = "the" if known and not first else ("bare" if entry.get("mass") else "a")
            result = self.n(word, *(tuple(modifiers) + tuple(adjectives)), det=det, number=entity.number)
        if (subject and known and self.world.focus == entity_id
                and self.discourse.resolve(pronoun=entity.pronoun, number=entity.number) == [entity_id]):
            pro = nouns.pronoun(entity.pronoun)
            if pro.agreement == result.agreement:
                result = NP(*(choice("local.reference.choice", getattr(result, case), getattr(pro, case), weights=(1, 4))
                              for case in ("subject", "object", "possessive")), result.agreement)
        return NP(*(seq("referent:" + entity_id, getattr(result, case))
                    for case in ("subject", "object", "possessive")), result.agreement)

    def v(self, word, *complements):
        lexical = verb(word, self.lexicon["verbs"][word])
        if not complements:
            return verbs.use_v(lexical)
        if len(complements) == 1:
            obj, = complements
            if isinstance(obj, NP):
                return verbs.transitive(lexical, obj)
            if isinstance(obj, VP):
                return verbs.intention(lexical, obj)
            if isinstance(obj, Sentence):
                return verbs.report(lexical, obj)
        if len(complements) == 2:
            first, second = complements
            if isinstance(first, NP) and isinstance(second, NP):
                return verbs.give(lexical, first, second)
            if isinstance(first, NP) and isinstance(second, VP):
                return verbs.request(lexical, first, second)
        raise TypeError(f"unsupported complement signature for {word}: {[type(c).__name__ for c in complements]}")

    def pp(self, preposition, obj):
        if preposition not in self.lexicon["prepositions"]:
            raise KeyError(f"add preposition {preposition!r} to a lexicon module")
        return verbs.prep_np(preposition, obj)

    def adv(self, action, *modifiers):
        for modifier in modifiers:
            if isinstance(modifier, str):
                if modifier not in self.lexicon["adverbs"]:
                    raise KeyError(f"add adverb {modifier!r} to a lexicon module")
                modifier = Adv(seq("lexical.adverb", modifier))
            action = verbs.modify(action, modifier)
        return action

    def be(self, complement):
        return verbs.copula(self.a(complement) if isinstance(complement, str) else complement)

    def s(self, subject, predicate, *, negative=False, tense=None):
        if isinstance(subject, str):
            subject = self.ref(subject, subject=True)
        return clauses.use_cl(clauses.pred(subject, predicate), tense or self.tense, negative)

    def either(self, *sentences, weights=()):
        if not all(isinstance(s, Sentence) for s in sentences):
            raise TypeError("sentence alternatives must all have type Sentence")
        return Sentence(choice("local.paraphrase", *(s.node for s in sentences), weights=weights))

    def bound(self, entity_id):
        """Explicit local coreference; used only under an introducing construction."""
        entity = self.world.entities[entity_id]
        result = nouns.pronoun(entity.pronoun)
        return NP(*(seq("referent:" + entity_id, getattr(result, case))
                    for case in ("subject", "object", "possessive")), result.agreement)

    @rule("local.ReportSelf", "local", "explicit speaker binding", dependencies=("gf.ComplVS", "gf.PredVP"),
          tags=("report", "reference", "speaker", "coherence"))
    def reporting(self, speaker, verb_word, content):
        """Build 'Mateo said that he ...'; content receives a bound, case-aware NP."""
        return self.s(speaker, self.v(verb_word, content(self.bound(speaker))))

    @rule("local.SequenceActions", "local", "explicit same-actor binding", dependencies=("local.ConjS",),
          tags=("coordination", "reference", "coherence"))
    def sequence(self, actor, first, second):
        """Two actions with the same actor: Nia carried it, and she wrapped it."""
        return self.join(self.s(actor, first), self.s(self.bound(actor), second))

    join = staticmethod(clauses.join)
    utter = staticmethod(clauses.utter)
    both = staticmethod(nouns.both)
    can = staticmethod(verbs.can)
    possess = staticmethod(nouns.possess)
