#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/cheek_dim_conflict_rhyme_sharing_fable.py
=========================================================================

A small fable-style storyworld about two woodland friends, a shared prize, a
rhyming dispute, and a gentle turn toward sharing.

The world is intentionally tiny:
- typed entities with physical meters and emotional memes
- a forward causal model
- a reasonableness gate
- an inline ASP twin
- three QA sets grounded in the simulated world

Seed words / instruments:
- cheek-dim
- Conflict
- Rhyme
- Sharing
- Style: Fable
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
RHYME_MIN = 2
SHARE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
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


@dataclass
class Grove:
    id: str
    place: str
    quiet: str
    prize_spot: str
    shade: str
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
class Prize:
    id: str
    label: str
    phrase: str
    value: str
    shared: bool = True
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
class ConflictCue:
    id: str
    trigger: str
    line: str
    force: int
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
class RhymeTool:
    id: str
    line: str
    charm: str
    strength: int
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
class SharingWay:
    id: str
    action: str
    ending: str
    warmth: str
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


@dataclass
class StoryParams:
    grove: str
    prize: str
    conflict: str
    rhyme: str
    sharing: str
    teller: str
    teller_gender: str
    listener: str
    listener_gender: str
    elder: str
    elder_gender: str
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    teller = world.get("teller")
    listener = world.get("listener")
    if teller.memes["boast"] < THRESHOLD:
        return out
    sig = ("conflict",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    teller.memes["stiff"] += 1
    listener.memes["hurt"] += 1
    listener.memes["worry"] += 1
    out.append("__conflict__")
    return out


def _r_rhyme(world: World) -> list[str]:
    out: list[str] = []
    elder = world.get("elder")
    if elder.memes["rhyme"] < THRESHOLD:
        return out
    sig = ("rhyme",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    elder.memes["calm"] += 1
    out.append("__rhyme__")
    return out


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    if world.get("listener").memes["share"] < THRESHOLD:
        return out
    sig = ("share",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    prize = world.get("prize")
    prize.meters["held"] = 0
    world.get("teller").memes["joy"] += 1
    world.get("listener").memes["joy"] += 1
    out.append("__share__")
    return out


CAUSAL_RULES = [Rule("conflict", _r_conflict), Rule("rhyme", _r_rhyme), Rule("share", _r_share)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def rhyme_strength(word: str) -> int:
    return 3 if word in {"stream", "dream", "gleam"} else 2


def can_share(prize: Prize, way: SharingWay) -> bool:
    return prize.shared and way.power >= SHARE_MIN


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for gid in GROVES:
        for cid, c in CONFLICTS.items():
            for rid, r in RHYMES.items():
                for sid, s in SHARES.items():
                    if can_share(PRIZES["acorn"], s):
                        combos.append((gid, cid, rid))
    return combos


def predict_turn(world: World, cue: ConflictCue, rhyme: RhymeTool, way: SharingWay) -> dict:
    sim = world.copy()
    sim.get("teller").memes["boast"] += 1
    sim.get("listener").memes["rhyme"] += rhyme.strength
    sim.get("listener").memes["share"] += way.power
    propagate(sim, narrate=False)
    return {
        "conflict": sim.get("listener").memes["hurt"] >= THRESHOLD,
        "shared": sim.get("prize").meters["held"] <= 0,
        "calm": sim.get("elder").memes["calm"] >= THRESHOLD,
    }


def narrate_opening(world: World, grove: Grove, teller: Entity, listener: Entity, prize: Prize) -> None:
    world.say(
        f"Once in {grove.place}, where {grove.quiet} and {grove.shade} lived together, "
        f"{teller.id} and {listener.id} found {prize.phrase} beneath {grove.prize_spot}."
    )
    world.say(
        f"{teller.id} said it was {teller.pronoun('possessive')} first, and {listener.id} "
        f"said it was meant to be shared."
    )


def narrate_conflict(world: World, cue: ConflictCue, teller: Entity, listener: Entity, prize: Prize) -> None:
    teller.memes["boast"] += 1
    listener.memes["hurt"] += 1
    world.say(
        f"{teller.id}'s cheeks went cheek-dim with stubborn pride. {cue.line} "
        f"{listener.id} frowned at the same little prize."
    )


def narrate_rhyme(world: World, rhyme: RhymeTool, elder: Entity) -> None:
    elder.memes["rhyme"] += rhyme.strength
    world.say(
        f"Then {elder.id} stepped between them and sang, {rhyme.line} "
        f"{rhyme.charm}"
    )


def narrate_turn(world: World, way: SharingWay, teller: Entity, listener: Entity, elder: Entity, prize: Prize) -> None:
    listener.memes["share"] += way.power
    teller.memes["soft"] += 1
    world.say(
        f"{elder.id} nodded and showed them a kinder way: {way.action}."
    )
    world.say(
        f"{teller.id} and {listener.id} tried it, {way.ending}, and the {prize.label} "
        f"became brighter when it was no longer pulled at."
    )


def narrate_ending(world: World, grove: Grove, teller: Entity, listener: Entity, elder: Entity, prize: Prize) -> None:
    teller.memes["joy"] += 1
    listener.memes["joy"] += 1
    world.say(
        f"In the end, the two children sat under {grove.shade}, each with a fair share, "
        f"while {elder.id} smiled like a lantern at dusk."
    )
    world.say(
        f"The little {prize.label} stayed whole, and the friends learned that a thing "
        f"held together grows kinder when it is shared."
    )


def tell(grove: Grove, prize: Prize, cue: ConflictCue, rhyme: RhymeTool, way: SharingWay,
         teller_name: str = "Milo", teller_gender: str = "boy",
         listener_name: str = "Nia", listener_gender: str = "girl",
         elder_name: str = "Wren", elder_gender: str = "girl") -> World:
    world = World()
    teller = world.add(Entity(id="teller", kind="character", type=teller_gender, label=teller_name, role="teller"))
    listener = world.add(Entity(id="listener", kind="character", type=listener_gender, label=listener_name, role="listener"))
    elder = world.add(Entity(id="elder", kind="character", type=elder_gender, label=elder_name, role="elder"))
    prize_ent = world.add(Entity(id="prize", kind="thing", type="thing", label=prize.label))
    prize_ent.meters["held"] = 1
    world.facts["grove"] = grove
    world.facts["prize"] = prize
    world.facts["conflict"] = cue
    world.facts["rhyme"] = rhyme
    world.facts["sharing"] = way

    narrate_opening(world, grove, teller, listener, prize)
    world.para()
    narrate_conflict(world, cue, teller, listener, prize)
    pred = predict_turn(world, cue, rhyme, way)
    world.facts["prediction"] = pred
    narrate_rhyme(world, rhyme, elder)
    world.para()
    narrate_turn(world, way, teller, listener, elder, prize)
    narrate_ending(world, grove, teller, listener, elder, prize)

    world.facts.update(outcome="shared" if can_share(prize, way) else "unshared")
    return world


GROVES = {
    "oak: ":
        Grove(id="oak", place="the old oak grove", quiet="bird-quiet mornings", prize_spot="the mossy root", shade="the wide leaves", tags={"grove"}),
    "brook":
        Grove(id="brook", place="the brook by the hill", quiet="soft water songs", prize_spot="a stone in the stream", shade="the cool bank", tags={"grove"}),
    "field":
        Grove(id="field", place="the sunlit field", quiet="warm breezes", prize_spot="the clover patch", shade="the single big tree", tags={"grove"}),
}

PRIZES = {
    "acorn": Prize(id="acorn", label="acorn", phrase="a shiny acorn", value="small treasure", shared=True, tags={"prize"}),
    "berry": Prize(id="berry", label="berry", phrase="a bright red berry", value="sweet treasure", shared=True, tags={"prize"}),
}

CONFLICTS = {
    "claim": ConflictCue(id="claim", trigger="claim", line="\"Mine!\" said one, \"Mine!\" said the other.", force=2, tags={"conflict"}),
    "snatch": ConflictCue(id="snatch", trigger="snatch", line="One reached first and tried to snatch it away.", force=3, tags={"conflict"}),
}

RHYMES = {
    "stream": RhymeTool(id="stream", line="\"A shared delight is twice as bright, like moon on a stream,\"", charm="The words fell softly and smoothly.", strength=3, tags={"rhyme"}),
    "gleam": RhymeTool(id="gleam", line="\"A little light is best at night, and sharing gives it gleam,\"", charm="It sounded like a tiny bell.", strength=2, tags={"rhyme"}),
}

SHARES = {
    "split": SharingWay(id="split", action="splitting the prize into equal turns", ending="and they took turns smiling", warmth="gentle", power=2, tags={"sharing"}),
    "nest": SharingWay(id="nest", action="placing the prize in a nest for both to admire", ending="and both friends leaned close together", warmth="warm", power=2, tags={"sharing"}),
}

TRAITS = ["gentle", "curious", "thoughtful", "bold"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable-like story world about conflict, rhyme, and sharing.")
    ap.add_argument("--grove", choices=GROVES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--conflict", choices=CONFLICTS)
    ap.add_argument("--rhyme", choices=RHYMES)
    ap.add_argument("--sharing", choices=SHARES)
    ap.add_argument("--name")
    ap.add_argument("--listener")
    ap.add_argument("--elder")
    ap.add_argument("--gender", choices=["boy", "girl"])
    ap.add_argument("--listener-gender", choices=["boy", "girl"])
    ap.add_argument("--elder-gender", choices=["boy", "girl"])
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
    if args.sharing and not can_share(PRIZES["acorn"], SHARES[args.sharing]):
        raise StoryError("That sharing plan is too weak for the tale.")
    choices = valid_combos()
    if not choices:
        raise StoryError("No valid fable can be made from these choices.")
    grove, conflict, rhyme = rng.choice(sorted(choices))
    sharing = args.sharing or rng.choice(sorted(SHARES))
    teller_gender = args.gender or rng.choice(["boy", "girl"])
    listener_gender = args.listener_gender or ("girl" if teller_gender == "boy" else "boy")
    elder_gender = args.elder_gender or rng.choice(["boy", "girl"])
    return StoryParams(
        grove=grove,
        prize=args.prize or "acorn",
        conflict=args.conflict or conflict,
        rhyme=args.rhyme or rhyme,
        sharing=sharing,
        teller=args.name or rng.choice(["Milo", "Iris", "Pip", "Roo"]),
        teller_gender=teller_gender,
        listener=args.listener or rng.choice(["Nia", "Jun", "Tess", "Bo"]),
        listener_gender=listener_gender,
        elder=args.elder or rng.choice(["Wren", "Mara", "Sage", "Orin"]),
        elder_gender=elder_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.grove not in GROVES or params.prize not in PRIZES or params.conflict not in CONFLICTS or params.rhyme not in RHYMES or params.sharing not in SHARES:
        raise StoryError("Invalid story parameters.")
    world = tell(GROVES[params.grove], PRIZES[params.prize], CONFLICTS[params.conflict], RHYMES[params.rhyme], SHARES[params.sharing], params.teller, params.teller_gender, params.listener, params.listener_gender, params.elder, params.elder_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable about {f["conflict"].line.lower()} Include the word "cheek-dim".',
        f"Tell a child-friendly fable where {f['teller'].id} and {f['listener'].id} clash over a shared treasure, then resolve it with rhyme and sharing.",
        "Write a tiny moral story in which pride grows dim, rhyme calms the room, and sharing wins the day.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    p: Prize = f["prize"]
    c: ConflictCue = f["conflict"]
    r: RhymeTool = f["rhyme"]
    s: SharingWay = f["sharing"]
    return [
        ("What were the children arguing about?", f"They were arguing about {p.phrase}. One wanted to keep it, and the other wanted it shared."),
        ("Why did the conflict start?", f"It started because {c.line} Their voices grew sharp before anyone found a gentler way."),
        ("How did the elder help?", f"{f['elder'].id} sang a rhyme: {r.line} The rhyme slowed the argument and made everyone listen."),
        ("How did they solve the problem?", f"They used {s.action}. That let both children enjoy the prize instead of fighting over it."),
        ("What changed by the end?", f"The conflict faded and both children were calm. The prize was shared, so the little fable ended in peace."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is sharing?", "Sharing means letting more than one person enjoy the same thing in a fair way."),
        ("Why can a rhyme help in a fable?", "A rhyme can sound calm and memorable, so it can help characters stop, listen, and think."),
        ("What does conflict mean?", "Conflict is when characters want different things and their wishes bump into each other."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:7}) meters={meters} memes={memes} role={e.role}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
conflict :- teller_boast, listener_hurt.
rhyme :- elder_rhyme.
share :- listener_share.

outcome(shared) :- share.
outcome(conflicted) :- conflict, not share.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for gid in GROVES:
        lines.append(asp.fact("grove", gid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    for cid in CONFLICTS:
        lines.append(asp.fact("conflict_kind", cid))
    for rid in RHYMES:
        lines.append(asp.fact("rhyme_kind", rid))
    for sid in SHARES:
        lines.append(asp.fact("sharing_kind", sid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_outcome() -> str:
    import asp
    model = asp.one_model(asp_program("teller_boast. listener_hurt. elder_rhyme. listener_share."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    import asp
    prog = asp_program("", "#show outcome/1.")
    model = asp.one_model(prog)
    ok = bool(asp.atoms(model, "outcome")) and asp_outcome() == "shared"
    sample = generate(resolve_params(build_parser().parse_args([]), random.Random(1)))
    if not sample.story:
        return 1
    if ok:
        print("OK: ASP twin and smoke test passed.")
        return 0
    print("MISMATCH in ASP twin.")
    return 1


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def _asp_module():
    import asp
    return asp


def asp_valid_combos() -> list[tuple]:
    asp = _asp_module()
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("No extra ASP browsing mode; use --verify or --show-asp.")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(grove="oak", prize="acorn", conflict="claim", rhyme="stream", sharing="split", teller="Milo", teller_gender="boy", listener="Nia", listener_gender="girl", elder="Wren", elder_gender="girl"),
            StoryParams(grove="brook", prize="berry", conflict="snatch", rhyme="gleam", sharing="nest", teller="Iris", teller_gender="girl", listener="Bo", listener_gender="boy", elder="Sage", elder_gender="boy"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            sample = generate(p)
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
