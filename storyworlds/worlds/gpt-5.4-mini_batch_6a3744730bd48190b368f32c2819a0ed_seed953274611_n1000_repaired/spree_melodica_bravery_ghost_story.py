#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/spree_melodica_bravery_ghost_story.py
======================================================================

A tiny storyworld in a ghost-story mood: a child hears a spooky music-box
melody in an old house, feels too nervous to investigate, then finds bravery,
follows the sound, and discovers the "ghost" was only an honest helper with a
melodica and a need for one last joyful spree.

Seed words: spree, melodica
Feature: bravery
Style: ghost story
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
BRAVERY_MIN = 3.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
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
class Place:
    id: str
    label: str
    spooky: str
    sound: str
    detail: str
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
class Instrument:
    id: str
    label: str
    phrase: str
    sound: str
    safe: bool = True
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
class Helper:
    id: str
    label: str
    kind: str
    phrase: str
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


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if not child:
        return out
    if child.memes["fear"] < THRESHOLD:
        return out
    sig = ("fear",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["bravery"] += 1
    out.append("__fear__")
    return out


CAUSAL_RULES = [Rule("fear", _r_fear)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                changed = True
                produced.extend(x for x in s if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def select_helper(bravery: float) -> Helper:
    return HELPERS["lantern"] if bravery >= BRAVERY_MIN else HELPERS["call_neighbor"]


def can_follow(place: Place, instrument: Instrument) -> bool:
    return "music" in place.tags and instrument.safe


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for iid, inst in INSTRUMENTS.items():
            for hid, helper in HELPERS.items():
                if can_follow(place, inst) and helper.kind in {"comfort", "help"}:
                    combos.append((pid, iid, hid))
    return combos


@dataclass
class StoryParams:
    place: str
    instrument: str
    helper: str
    child_name: str
    child_gender: str
    parent_name: str
    seed: Optional[int] = None
    bravery: int = 3
    night: bool = True
    spree: str = "spree"
    extra_visitor: str = ""
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


PLACES = {
    "attic": Place(
        id="attic",
        label="the attic",
        spooky="dusty beams and a cold window",
        sound="a thin tune from the rafters",
        detail="The stairs creaked like a sleepy old beast, and the attic kept its secrets in shadows.",
        tags={"music", "ghost", "old_house"},
    ),
    "hall": Place(
        id="hall",
        label="the hallway",
        spooky="a long mirror and a cracked wallpaper rose",
        sound="a wavery tune behind the closed door",
        detail="The hallway was narrow and dim, with a mirror that made the candlelight look nervous.",
        tags={"music", "ghost", "old_house"},
    ),
}

INSTRUMENTS = {
    "melodica": Instrument(
        id="melodica",
        label="melodica",
        phrase="a melodica",
        sound="a soft honk of bright notes",
        safe=True,
        tags={"melodica", "music"},
    ),
    "music_box": Instrument(
        id="music_box",
        label="music box",
        phrase="an old music box",
        sound="a tiny tinkling waltz",
        safe=True,
        tags={"music_box", "music"},
    ),
}

HELPERS = {
    "lantern": Helper(id="lantern", label="lantern", kind="comfort", phrase="a warm lantern", tags={"light"}),
    "call_neighbor": Helper(id="call_neighbor", label="neighbor", kind="help", phrase="the brave neighbor", tags={"help"}),
}

CURATED = [
    StoryParams(place="attic", instrument="melodica", helper="lantern", child_name="Mina", child_gender="girl", parent_name="Mom", bravery=4, night=True, spree="spree"),
    StoryParams(place="hall", instrument="melodica", helper="call_neighbor", child_name="Theo", child_gender="boy", parent_name="Dad", bravery=2, night=True, spree="spree"),
]


def explain_rejection(place: Place, instrument: Instrument) -> str:
    if not can_follow(place, instrument):
        return f"(No story: {instrument.label} does not fit this haunted place idea.)"
    return "(No story: this combination is not reasonable.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A ghost-story world about bravery, a spree, and a melodica.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--instrument", choices=INSTRUMENTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mom", "dad"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.instrument:
        if not can_follow(PLACES[args.place], INSTRUMENTS[args.instrument]):
            raise StoryError(explain_rejection(PLACES[args.place], INSTRUMENTS[args.instrument]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.instrument is None or c[1] == args.instrument)
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, instrument, helper = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(["Mina", "Theo", "Pia", "Owen", "Luna", "Eli"])
    parent = args.parent or rng.choice(["mom", "dad"])
    bravery = rng.randint(1, 5)
    return StoryParams(place=place, instrument=instrument, helper=helper, child_name=name, child_gender=gender, parent_name=parent, bravery=bravery, night=True, spree="spree")


def tell(world: World, place: Place, inst: Instrument, helper: Helper, params: StoryParams) -> None:
    child = world.add(Entity(id="child", kind="character", type=params.child_gender, label=params.child_name))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=params.parent_name))
    ghost = world.add(Entity(id="ghost", kind="character", type="thing", label="the ghost", role="helper"))
    child.memes["fear"] = 0.0
    child.memes["bravery"] = float(params.bravery)

    world.say(
        f"On a dark night, {child.id} and {parent.label_word} stood at {place.label}. "
        f"{place.detail}"
    )
    world.say(
        f"Then came {place.sound}, and {child.id} heard what sounded like a ghost having a little {params.spree}."
    )
    world.para()
    world.say(
        f"{child.id} peered toward the dark and saw {inst.phrase} by the old stairs. "
        f"It made {inst.sound}, and it felt spooky enough to make {child.id}'s knees go wobbly."
    )
    child.memes["fear"] += 1
    propagate(world, narrate=False)
    if child.memes["bravery"] >= BRAVERY_MIN:
        world.say(
            f"But {child.id} took a slow breath and stood tall. "
            f"'{child.id} can be brave,' {child.id} whispered, and went closer instead of running away."
        )
    else:
        world.say(
            f"But {child.id} held tight to {parent.label_word}'s hand, trying to be brave enough to look."
        )

    world.para()
    if helper.kind == "comfort":
        world.say(
            f"At the top step, {child.id} found {helper.phrase} and the surprise turned gentle at once. "
            f"It was only a grown-up helping to make music, not a ghost at all."
        )
    else:
        world.say(
            f"At the top step, {child.id} called for help, and the brave neighbor came with a lamp. "
            f"Together they found the source of the tune and learned it was only a person, not a ghost."
        )
    world.say(
        f"{child.id} lifted the {inst.label}, pressed the keys, and answered the spooky tune with a bright little song."
    )
    world.say(
        f"The house no longer felt haunted. It felt friendly, and the old dark place filled with music instead of fear."
    )

    world.facts.update(
        child=child,
        parent=parent,
        ghost=ghost,
        place=place,
        instrument=inst,
        helper=helper,
        bravery=float(params.bravery),
        outcome="brave",
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a ghost-story for a young child that includes the words "{f["spree"].id if False else "spree"}" and "{f["instrument"].label}".',
        f"Tell a spooky-but-kind story where {f['child'].id} hears a mysterious tune in {f['place'].label} and finds the courage to investigate.",
        f"Write a short story about bravery, a {f['instrument'].label}, and a scary sound that turns out to be safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    place = f["place"]
    inst = f["instrument"]
    return [
        QAItem(
            question=f"What did {child.id} hear in {place.label}?",
            answer=f"{child.id} heard a spooky tune that seemed ghostly at first. It turned out to come from {inst.phrase}, not from a real ghost.",
        ),
        QAItem(
            question=f"How did {child.id} show bravery?",
            answer=f"{child.id} took a deep breath and went closer instead of running away. That brave choice let {child.id} discover the music was safe.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with music instead of fear. The old house felt friendly again, and {child.id} was proud of being brave.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a melodica?",
            answer="A melodica is a small keyboard instrument you blow into to make notes. It can sound cheerful and strange at the same time.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery is doing the hard thing even when you feel scared. It does not mean you feel no fear; it means you keep going anyway.",
        ),
        QAItem(
            question="What does a ghost story try to feel like?",
            answer="A ghost story tries to feel spooky and mysterious, but it can still end safely. The best ones leave you a little shivery and a little glad.",
        ),
    ]


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
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.instrument not in INSTRUMENTS or params.helper not in HELPERS:
        raise StoryError("(Invalid params for this storyworld.)")
    world = World()
    tell(world, PLACES[params.place], INSTRUMENTS[params.instrument], HELPERS[params.helper], params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
valid(P, I, H) :- place(P), instrument(I), helper(H), safe(I), haunted(P).
"""
def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("haunted", pid))
    for iid, inst in INSTRUMENTS.items():
        lines.append(asp.fact("instrument", iid))
        if inst.safe:
            lines.append(asp.fact("safe", iid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    from contextlib import redirect_stdout

    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in ASP gate")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, instrument=None, helper=None, name=None, gender=None, parent=None), random.Random(777)))
        with redirect_stdout(io.StringIO()):
            emit(sample)
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP gate matches and smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    return globals()["build_parser"]  # placeholder overwritten below


def _build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story world with bravery and a melodica.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--instrument", choices=INSTRUMENTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mom", "dad"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap

build_parser = _build_parser


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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("", "#show valid/3."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
