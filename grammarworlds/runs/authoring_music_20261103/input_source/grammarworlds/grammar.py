"""A small weighted compositional grammar and an exact prefix distribution.

Semantic frames stay latent while words are sampled. A bounded derivation forest
is compiled from reusable phrase rules, not a list of prewritten stories. Every
word probability is the sum of compatible derivation mass divided by prefix mass.
The implementation enumerates this small forest; scaling to a large grammar
would require a packed chart. Never count surface variants as authored rules.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import math
import re

from .world import Frame, World


@dataclass(frozen=True)
class Node:
    kind: str
    label: str
    children: tuple = ()
    weights: tuple[float, ...] = ()


def text(words: str) -> Node:
    return Node("text", "lexical", tuple(re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?|[,;.!?]", words)))


def seq(label: str, *parts: Node | str) -> Node:
    return Node("sequence", label, tuple(text(p) if isinstance(p, str) else p for p in parts))


def choice(label: str, *alternatives: Node | str, weights: tuple[float, ...] = ()) -> Node:
    if not alternatives:
        raise ValueError("empty grammatical choice")
    if not weights:
        weights = (1.0,) * len(alternatives)
    if len(weights) != len(alternatives) or any(not math.isfinite(w) or w <= 0 for w in weights):
        raise ValueError("choice weights must be positive and finite")
    return Node("choice", label, tuple(text(a) if isinstance(a, str) else a for a in alternatives), weights)


def expand(node: Node):
    """Yield (token sequence, normalized grammar probability, rule path)."""
    if node.kind == "text":
        yield node.children, 1.0, ()
    elif node.kind == "choice":
        total = sum(node.weights)
        for child, weight in zip(node.children, node.weights):
            for words, probability, rules in expand(child):
                yield words, weight / total * probability, (node.label,) + rules
    else:
        rows = [((), 1.0, (node.label,))]
        for child in node.children:
            branches = list(expand(child))
            rows = [(left + right, p * q, lr + rr)
                    for left, p, lr in rows for right, q, rr in branches]
        yield from rows


FORMS = {
    "notice": ("noticed", "notices"), "spot": ("spotted", "spots"),
    "see": ("saw", "sees"), "want": ("wanted", "wants"),
    "hope": ("hoped", "hopes"), "try": ("tried", "tries"),
    "reach": ("reached", "reaches"), "toss": ("tossed", "tosses"),
    "look": ("looked", "looks"), "ask": ("asked", "asks"),
    "suggest": ("suggested", "suggests"), "realize": ("realized", "realizes"),
    "remember": ("remembered", "remembers"), "fetch": ("fetched", "fetches"),
    "bring": ("brought", "brings"), "give": ("gave", "gives"),
    "use": ("used", "uses"), "climb": ("climbed", "climbs"),
    "lift": ("lifted", "lifts"), "patch": ("patched", "patches"),
    "mend": ("mended", "mends"), "shine": ("shone", "shines"),
    "find": ("found", "finds"), "carry": ("carried", "carries"),
    "wrap": ("wrapped", "wraps"), "launch": ("launched", "launches"),
    "send": ("sent", "sends"), "unlock": ("unlocked", "unlocks"),
    "turn": ("turned", "turns"), "open": ("opened", "opens"),
    "thank": ("thanked", "thanks"), "smile": ("smiled", "smiles"),
    "curl": ("curled", "curls"), "rest": ("rested", "rests"),
    "dance": ("danced", "dances"), "float": ("floated", "floats"),
    "step": ("stepped", "steps"), "remain": ("remained", "remains"),
    "stay": ("stayed", "stays"), "slip": ("slipped", "slips"),
    "help": ("helped", "helps"), "make": ("made", "makes"),
    "fall": ("fell", "falls"),
}


class Grammar:
    def __init__(self, world: World, tense: str = "past"):
        if tense not in {"past", "present"}:
            raise ValueError("tense must be past or present")
        self.world, self.tense = world, tense

    def verb(self, base: str, actor: str | None = None) -> str:
        if self.tense == "past":
            return FORMS[base][0]
        if actor and self.world.entities[actor].number == "plural":
            return base
        return FORMS[base][1]

    def be(self, entity: str | None = None) -> str:
        plural = entity is not None and self.world.entities[entity].number == "plural"
        return ("were" if plural else "was") if self.tense == "past" else ("are" if plural else "is")

    def ref(self, entity_id: str, *, subject: bool = False, first: bool = False,
            describe: tuple[str, ...] = ()) -> Node:
        entity = self.world.entities[entity_id]
        if entity.kind == "person":
            proper = text(entity.noun)
            if subject and self.world.focus == entity_id:
                return choice("subject.reference", proper, entity.pronoun, weights=(1, 4))
            return proper
        determiner = "a" if first else "the"
        bare = seq("noun_phrase.bare", determiner, entity.noun)
        if not describe:
            return bare
        # Descriptions are supplied by semantic guards, not freely combined.
        decorated = [seq("noun_phrase.modified", determiner, adjective, entity.noun)
                     for adjective in describe]
        return choice("noun_phrase.description", bare, *decorated,
                      weights=(1,) + (2,) * len(decorated))

    def sentence(self, clause: Node, *, marker: bool = True) -> Node:
        if marker and self.world.history:
            clause = choice("discourse.transition", clause, seq("discourse.then", "then", clause),
                            weights=(5, 1))
        return seq("sentence", clause, ".")

    def action(self, actor: str, verb: str | Node, *complements: Node | str) -> Node:
        return seq("clause.subject_predicate", self.ref(actor, subject=True), verb, *complements)

    def infinitive_goal(self) -> Node:
        w = self.world
        return {
            "rescue": seq("goal.rescue", "bring", self.ref(w.target), "down safely"),
            "kite": seq("goal.repair", "make", self.ref(w.target), "fly again"),
            "key": seq("goal.recover", "find", self.ref(w.target), "and open the door"),
        }[w.scenario]

    def for_frame(self, f: Frame) -> Node:
        w = self.world
        hero, target, helper, tool = w.hero, w.target, w.helper, w.tool
        v = lambda base: self.verb(base, hero)
        subject = self.ref(hero, subject=True)
        obj, instrument = self.ref(target), self.ref(tool)
        kind = f.kind
        if kind == "notice":
            if w.scenario == "rescue":
                # All these states are present on the physical animal.
                adjectives = tuple(a for a, state in (("shivering", "cold"), ("frightened", "frightened"))
                                   if state in w.entities[target].state)
                predicate = seq("perception.stranded", choice("verb.perception", v("notice"), v("spot")),
                                self.ref(target, first=True, describe=adjectives),
                                choice("location.ledge", "on a high ledge", "stranded above the garden"))
            elif w.scenario == "kite":
                predicate = seq("perception.damage", choice("verb.perception", v("notice"), v("see")),
                                choice("damage.phrase", "a tear in the kite", "the torn kite on the grass"))
            else:
                predicate = seq("perception.lock", choice("verb.perception", v("notice"), v("see")),
                                "that the door", self.be(), "locked and the key", self.be(), "missing")
            clause = seq("clause.subject_predicate", subject, predicate)
            scene = f"at dusk in the {w.setting}" if w.scenario == "key" else f"in the {w.setting}"
            return self.sentence(choice("opening.location", clause,
                seq("opening.scene", scene, ",", clause), weights=(2, 3)), marker=False)
        if kind == "want":
            return self.sentence(self.action(hero, choice("verb.intention", v("want"), v("hope")),
                                             "to", self.infinitive_goal()))
        if kind == "attempt":
            if w.scenario == "rescue":
                attempt = self.action(hero, v("reach"), "up for", obj)
                obstacle = seq("obstacle.height", "the ledge", self.be(), "too high")
            elif w.scenario == "kite":
                attempt = self.action(hero, v("toss"), obj, "into the wind")
                obstacle = seq("obstacle.damage", "it", self.verb("fall", target), "back onto the grass")
            else:
                attempt = self.action(hero, v("look"), "under the bench")
                obstacle = seq("obstacle.darkness", "the key", self.verb("remain", target), "hidden in the dark")
            return self.sentence(seq("clause.contrast", attempt, ",", "but", obstacle), marker=False)
        if kind == "ask":
            ask = self.action(hero, v("ask"), self.ref(helper), "for help")
            advice = seq("clause.advice", self.ref(helper), self.verb("suggest", helper), "using", instrument)
            return self.sentence(seq("clause.coordination", ask, ",", "and", advice))
        if kind == "think":
            plan = {"rescue": "reach the ledge", "kite": "cover the tear", "key": "light the dark space"}[w.scenario]
            # Realization creates a grounded plan; it does not assert prior memories.
            return self.sentence(self.action(hero, v("realize"), "that", instrument,
                                             "could" if self.tense == "past" else "can", plan))
        if kind == "fetch":
            return self.sentence(self.action(hero, v("fetch"), instrument,
                                             "from the", w.entities[tool].location))
        if kind == "receive":
            return self.sentence(self.action(helper, self.verb("bring", helper),
                                             self.ref(hero), instrument))
        if kind == "solve":
            if w.scenario == "rescue":
                direct = self.action(hero, v("use"), instrument, "to lift", obj, "down")
                compound = self.action(hero, v("climb"), instrument, "and", v("lift"), obj, "to safety")
            elif w.scenario == "kite":
                direct = self.action(hero, choice("verb.repair", v("patch"), v("mend")), obj, "with", instrument)
                compound = self.action(hero, v("use"), instrument, "to cover the tear in", obj)
            else:
                direct = self.action(hero, v("use"), instrument, "to find", obj, "under the bench")
                compound = self.action(hero, v("shine"), instrument, "under the bench and", v("find"), obj)
            return self.sentence(choice("action.instrument_construction", direct, compound))
        if kind == "finish":
            if w.scenario == "rescue":
                clause = self.action(hero, v("carry"), obj, "into the cottage and", v("wrap"), "it in a warm blanket")
            elif w.scenario == "kite":
                clause = choice("action.launch_construction",
                    self.action(hero, v("launch"), "the repaired kite into the wind"),
                    self.action(hero, v("send"), "the repaired kite soaring above the meadow"))
            else:
                clause = choice("action.unlock_construction",
                    self.action(hero, v("use"), obj, "to unlock and open the cottage door"),
                    self.action(hero, v("turn"), obj, "and", v("open"), "the cottage door"))
            return self.sentence(clause)
        if kind == "thank":
            return self.sentence(self.action(hero, v("thank"), self.ref(helper),
                                             choice("thanks.reason", "for the help", "with a smile")), marker=False)
        if kind == "ending":
            if w.scenario == "rescue":
                clause = seq("ending.physical_image", self.ref(target),
                    choice("ending.rest", self.verb("curl", target) + " up",
                           self.verb("rest", target)),
                    "in the blanket", ",", "safe and warm")
            elif w.scenario == "kite":
                clause = seq("ending.physical_image", obj,
                    choice("ending.flight", self.verb("dance", target), self.verb("float", target)),
                    "above the meadow", ",", "whole again against the sky")
            else:
                clause = self.action(hero, v("step"), "through the open doorway", ",",
                                     "the key held tightly in", "her" if w.entities[hero].pronoun == "she" else "his", "hand")
            return self.sentence(clause, marker=False)
        raise ValueError(f"no grammar for kernel {kind}")


def detokenize(tokens: tuple[str, ...] | list[str]) -> str:
    result = " ".join(tokens)
    result = re.sub(r"\s+([,.;!?])", r"\1", result)
    return result[:1].upper() + result[1:]


def tokenize(prefix: str) -> tuple[str, ...]:
    return tuple(re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?|[,;.!?]", prefix.lower()))


@dataclass(frozen=True)
class Derivation:
    tokens: tuple[str, ...]
    probability: float
    frame: Frame
    rules: tuple[str, ...]


class Forest:
    """Finite weighted grammar forest, conditioned by incremental word prefixes."""

    def __init__(self, derivations: list[Derivation], frame_evidence: dict):
        if not derivations:
            raise ValueError("no grounded grammatical continuations")
        total = sum(d.probability for d in derivations)
        self.derivations = [Derivation(d.tokens, d.probability / total, d.frame, d.rules)
                            for d in derivations]
        self.evidence = frame_evidence

    def survivors(self, prefix: tuple[str, ...]) -> list[Derivation]:
        normalized = tuple(w.lower() for w in prefix)
        return [d for d in self.derivations
                if tuple(w.lower() for w in d.tokens[:len(prefix)]) == normalized]

    def predict(self, prefix: tuple[str, ...] = ()) -> dict:
        rows = self.survivors(prefix)
        if not rows:
            return {"prefix": list(prefix), "choices": [], "prefix_probability": 0,
                    "complete": False, "error": "unsupported prefix in this grammar and world"}
        total = sum(d.probability for d in rows)
        mass, explanations = defaultdict(float), defaultdict(lambda: defaultdict(float))
        rules = defaultdict(set)
        for d in rows:
            word = d.tokens[len(prefix)] if len(prefix) < len(d.tokens) else "<END>"
            mass[word] += d.probability
            explanations[word][d.frame.kind] += d.probability
            rules[word].update(d.rules)
        choices = []
        for word in sorted(mass, key=lambda w: (-mass[w], w)):
            choices.append({"word": word, "probability": mass[word] / total,
                            "events": {kind: p / mass[word] for kind, p in sorted(explanations[word].items())},
                            "grammar_rules": sorted(rules[word])})
        return {"prefix": list(prefix), "choices": choices,
                "prefix_probability": total, "complete": "<END>" in mass,
                "surviving_derivations": len(rows)}

    def event_posterior(self, tokens: tuple[str, ...]) -> dict:
        rows = [d for d in self.survivors(tokens) if len(d.tokens) == len(tokens)]
        mass = defaultdict(float)
        for d in rows:
            mass[d.frame] += d.probability
        total = sum(mass.values())
        return {frame: value / total for frame, value in mass.items()} if total else {}
