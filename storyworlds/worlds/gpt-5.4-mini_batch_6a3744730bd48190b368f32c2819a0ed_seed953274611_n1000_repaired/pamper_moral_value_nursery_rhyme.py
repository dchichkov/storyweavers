#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/pamper_moral_value_nursery_rhyme.py
====================================================================

A tiny nursery-rhyme-style storyworld about a child learning that real
pampering means kind, sensible care rather than fussing or selfishness.

The seed word is ``pamper``. The moral value is kindness-with-restraint:
help the one who needs help, share the comfort, and do not hoard the best bits.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSITIVE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    age: int = 0
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Kind:
    id: str
    label: str
    needs: set[str]
    sings: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Pamper:
    id: str
    label: str
    phrase: str
    gives: set[str]
    warms: bool = False
    sweet: bool = False
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Moral:
    id: str
    line: str
    lesson: str
    sense: int
    power: int
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_needs(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    pal = world.entities.get("pal")
    if not child or not pal:
        return out
    if pal.meters["tired"] < THRESHOLD:
        return out
    sig = ("needs",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["care"] += 1
    out.append("The little heart in the room felt a bit more kind.")
    return out


def _r_overpamper(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    pal = world.entities.get("pal")
    if not child or not pal:
        return out
    if child.memes["greedy"] < THRESHOLD:
        return out
    sig = ("overpamper",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    pal.meters["sticky"] += 1
    out.append("Too much sweet cream made the little nose sticky.")
    return out


CAUSAL_RULES = [Rule("needs", _r_needs), Rule("overpamper", _r_overpamper)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def sensible(p: Pamper) -> bool:
    return p.sense >= SENSITIVE_MIN


def valid_combo(kind: Kind, pamper: Pamper) -> bool:
    return bool(kind.needs & pamper.gives)


def best_pamper() -> Pamper:
    return max(PAMPERS.values(), key=lambda p: p.sense)


def predict(world: World, pamper: Pamper, kind: Kind) -> dict:
    sim = world.copy()
    sim.get("pal").meters["tired"] += 1
    if pamper.sweet:
        sim.get("child").memes["greedy"] += 1
        propagate(sim, narrate=False)
    return {"sticky": sim.get("pal").meters["sticky"], "care": sim.get("child").memes["care"]}


def play_setup(world: World, child: Entity, pal: Entity, kind: Kind) -> None:
    child.memes["joy"] += 1
    world.say(
        f"Little {child.id} sang a tune, tra-la-la, as {pal.label} lay by the window "
        f"and the rain went pitter-pat on the sill."
    )
    world.say(
        f"{pal.label_word.capitalize()} saw the tired little {kind.label} and said, "
        f'"Oh dear, oh dear, you need a rest and a cheer."'
    )


def tempt(world: World, child: Entity, pamper: Pamper, kind: Kind) -> None:
    child.memes["greedy"] += 1
    world.say(
        f'Then {child.id} clapped {child.pronoun("possessive")} hands and cried, '
        f'"I know! I shall pamper {pal_line(kind)} with {pamper.phrase}!"'
    )


def pal_line(kind: Kind) -> str:
    return f"the little {kind.label}"


def warn(world: World, parent: Entity, child: Entity, pamper: Pamper, kind: Kind) -> None:
    pred = predict(world, pamper, kind)
    world.facts["pred"] = pred
    if pamper.sweet:
        world.say(
            f'"Not all pamperings are wise," {parent.label_word.capitalize()} said. '
            f'"A sweet can be a treat, but too much can make {kind.label} sticky."'
        )
    else:
        world.say(
            f'"That is a good pamper," {parent.label_word.capitalize()} nodded. '
            f'"Soft care suits a tired little one."'
        )


def choose_kind(world: World, child: Entity, pamper: Pamper, kind: Kind) -> None:
    if pamper.sweet:
        world.say(
            f'"But I want the frosting too!" {child.id} said, and the spoon wobbled in '
            f'{child.pronoun("possessive")} fist.'
        )
    else:
        world.say(f'{child.id} held the towel and the blanket as if they were little clouds.')


def resolve(world: World, child: Entity, parent: Entity, pal: Entity, pamper: Pamper, kind: Kind) -> None:
    if pamper.sweet:
        world.say(
            f'The {kind.label} got a lick, and then another; the cream began to cling, '
            f'and the poor nose turned sticky.'
        )
        world.say(
            f"{parent.label_word.capitalize()} laughed a gentle laugh and found a clean cloth."
        )
    else:
        world.say(
            f"{child.id} tucked {pal.label} into the warm nest and brushed the fluff so neat."
        )
        world.say(
            f"{pal.label_word.capitalize()} smiled a sleepy smile, and the room felt sweet."
        )


def lesson(world: World, parent: Entity, child: Entity, pamper: Pamper, kind: Kind) -> None:
    child.memes["care"] += 1
    child.memes["greedy"] = 0.0
    if pamper.sweet:
        world.say(
            f'"Pamper means care, not taking the best," {parent.label_word.capitalize()} said. '
            f'"A kind hand shares and knows what is best."'
        )
    else:
        world.say(
            f'"Pamper means care," {parent.label_word.capitalize()} said, '
            f'"and caring is nicest when it helps the one in need."'
        )
    world.say(
        f'{child.id} nodded, and {child.pronoun("possessive")} small heart felt light as a bird.'
    )


def ending(world: World, child: Entity, pal: Entity, kind: Kind, pamper: Pamper) -> None:
    if pamper.sweet:
        world.say(
            f"By and by, they shared a simple snack, and {kind.label} was clean again."
        )
        world.say(
            f"{child.id} learned that a gentle choice can be the kindest thing of all."
        )
    else:
        world.say(
            f"By and by, {pal.label} slept in a warm little nest, and the rain sang outside."
        )
        world.say(
            f"{child.id} learned that to pamper is to help, not to boast."
        )


def tell(kind: Kind, pamper: Pamper, child_name: str = "Milly", child_gender: str = "girl",
         parent_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent"))
    pal = world.add(Entity(id="pal", kind="thing", type="thing", label=kind.label))
    child.memes["joy"] = 1
    pal.meters["tired"] = 1
    play_setup(world, child, pal, kind)
    world.para()
    tempt(world, child, pamper, kind)
    warn(world, parent, child, pamper, kind)
    choose_kind(world, child, pamper, kind)
    world.para()
    resolve(world, child, parent, pal, pamper, kind)
    lesson(world, parent, child, pamper, kind)
    ending(world, child, pal, kind, pamper)
    world.facts.update(child=child, parent=parent, pal=pal, kind=kind, pamper=pamper,
                       outcome="sticky" if pamper.sweet else "kind")
    return world


KINDS = {
    "lamb": Kind(id="lamb", label="lamb", needs={"warm", "soft"}, sings="baa", tags={"animal", "soft"}),
    "kitten": Kind(id="kitten", label="kitten", needs={"warm", "soft"}, sings="mew", tags={"animal", "soft"}),
    "duckling": Kind(id="duckling", label="duckling", needs={"warm", "clean"}, sings="peep", tags={"animal", "clean"}),
}

PAMPERS = {
    "blanket": Pamper(id="blanket", label="blanket", phrase="a soft blanket", gives={"warm", "soft"}, warms=True, tags={"warm", "soft"}),
    "brush": Pamper(id="brush", label="brush", phrase="a gentle brush", gives={"soft", "clean"}, tags={"soft", "clean"}),
    "cake": Pamper(id="cake", label="cake", phrase="a little frosted cake", gives={"sweet"}, sweet=True, tags={"sweet"}),
    "milk": Pamper(id="milk", label="milk", phrase="a cup of warm milk", gives={"warm", "clean"}, warms=True, tags={"warm", "clean"}),
}

KNOWLEDGE = {
    "pamper": [("What does pamper mean?",
                "To pamper means to give kind, gentle care and help someone feel comfortable and happy.")],
    "blanket": [("What is a blanket for?",
                 "A blanket helps keep someone warm and snug.")],
    "brush": [("What does a brush do?",
               "A brush can smooth fur or hair and help it look neat.")],
    "cake": [("Why can too much cake be a bad idea?",
               "Cake is a treat, but too much sweet food can be sticky or unkind if it replaces real care.")],
    "milk": [("Why do warm drinks feel nice?",
               "Warm drinks can make a chilly little tummy feel cozy and calm.")],
    "kindness": [("What is kindness?",
                  "Kindness is choosing to help, share, and be gentle with others.")],
    "sharing": [("Why should you share?",
                  "Sharing means everyone gets a turn, and that helps people feel cared for.")],
}
KNOWLEDGE_ORDER = ["pamper", "blanket", "brush", "cake", "milk", "kindness", "sharing"]


@dataclass
class StoryParams:
    kind: str
    pamper: str
    child: str = "Milly"
    child_gender: str = "girl"
    parent: str = "mother"
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


CURATED = [
    StoryParams(kind="lamb", pamper="blanket", child="Milly", child_gender="girl", parent="mother"),
    StoryParams(kind="kitten", pamper="brush", child="Nora", child_gender="girl", parent="father"),
    StoryParams(kind="duckling", pamper="milk", child="Pip", child_gender="boy", parent="mother"),
    StoryParams(kind="kitten", pamper="cake", child="Toby", child_gender="boy", parent="father"),
]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for kid in KINDS.values():
        for pam in PAMPERS.values():
            if valid_combo(kid, pam) and sensible(pam):
                combos.append((kid.id, pam.id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme-style story that uses the word "pamper" and shows {f["kind"].label} getting kind care.',
        f"Tell a short moral story where {f['child'].id} wants to pamper a little {f['kind'].label}, but learns to choose the gentlest and wisest care.",
        f'Write a gentle rhyme-like tale about kindness and sharing, ending with a child learning what it means to pamper well.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, parent, kind, pamper = f["child"], f["parent"], f["kind"], f["pamper"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id}, {child.pronoun('possessive')} {parent.label_word}, and a little {kind.label} that needed care."),
        (f"What did {child.id} want to do?",
         f"{child.id} wanted to pamper the little {kind.label}. {child.id} thought {pamper.phrase} might help, and the day turned into a lesson about care."),
        ("What was the moral of the story?",
         f"Pamper means kind care, not greedy fussing. The story shows that sharing gently is better than taking the sweetest thing for yourself."),
    ]
    if f["pamper"].sweet:
        qa.append((f"Why did the parent warn {child.id}?",
                   f"The parent warned {child.id} because the sweet treat could make the little {kind.label} sticky instead of truly cared for. A real pamper should help, not simply pile on sugar."))
        qa.append(("How did the story end?",
                   f"It ended with {child.id} learning to choose gentler care and share wisely. The sticky mistake became a useful lesson about kindness."))
    else:
        qa.append((f"How did {child.id} help the little {kind.label}?",
                   f"{child.id} used {pamper.phrase} to give warm, gentle care. That helped the little {kind.label} feel snug and safe."))
        qa.append(("How did the story end?",
                   f"It ended with the little {kind.label} resting happily while {child.id} learned that to pamper is to help. The room felt calm and caring at the end."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["pamper"].tags) | set(world.facts["kind"].tags) | {"kindness", "sharing", "pamper"}
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.role:
            parts.append(f"role={e.role}")
        if e.attrs:
            parts.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(parts)}")
    return "\n".join(lines)


ASP_RULES = r"""
kind_need(K, warm) :- kind(K), needs(K, warm).
kind_need(K, soft) :- kind(K), needs(K, soft).
kind_need(K, clean) :- kind(K), needs(K, clean).

good_pamper(P, K) :- pamper(P), kind(K), gives(P, X), needs(K, X).
sensible(P) :- pamper(P), sense(P, S), sense_min(M), S >= M.
valid(K, P) :- kind(K), pamper(P), good_pamper(P, K), sensible(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for kid in KINDS.values():
        lines.append(asp.fact("kind", kid.id))
        for n in sorted(kid.needs):
            lines.append(asp.fact("needs", kid.id, n))
    for pam in PAMPERS.values():
        lines.append(asp.fact("pamper", pam.id))
        lines.append(asp.fact("sense", pam.id, 3 if not pam.sweet else 1))
        for g in sorted(pam.gives):
            lines.append(asp.fact("gives", pam.id, g))
    lines.append(asp.fact("sense_min", SENSITIVE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH: ASP gate does not match valid_combos().")
    if set(asp_sensible()) == {p.id for p in PAMPERS.values() if sensible(p)}:
        print("OK: sensible pamper choices match.")
    else:
        rc = 1
        print("MISMATCH: sensible pamper choices differ.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld about pampering with a moral value.")
    ap.add_argument("--kind", choices=KINDS)
    ap.add_argument("--pamper", choices=PAMPERS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.pamper and not sensible(PAMPERS[args.pamper]):
        raise StoryError("That pamper choice is too unwise for this nursery-rhyme story.")
    combos = [c for c in valid_combos()
              if (args.kind is None or c[0] == args.kind)
              and (args.pamper is None or c[1] == args.pamper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    kind, pamper = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(["Milly", "Nora", "Pip", "Toby", "Luna", "Otis"])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(kind=kind, pamper=pamper, child=child, child_gender=child_gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    if params.kind not in KINDS or params.pamper not in PAMPERS:
        raise StoryError("Invalid StoryParams keys.")
    kind = KINDS[params.kind]
    pamper = PAMPERS[params.pamper]
    if not valid_combo(kind, pamper):
        raise StoryError("That pamper choice does not fit the little one's needs.")
    world = tell(kind, pamper, params.child, params.child_gender, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible pamper choices: {', '.join(asp_sensible())}\n")
        for k, p in asp_valid_combos():
            print(f"  {k:8} {p}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        if args.all:
            p = sample.params
            header = f"### {p.child} and the {p.kind} ({p.pamper})"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
