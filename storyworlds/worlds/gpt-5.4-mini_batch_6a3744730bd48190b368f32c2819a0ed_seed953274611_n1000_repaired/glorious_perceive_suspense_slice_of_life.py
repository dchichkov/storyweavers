#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/glorious_perceive_suspense_slice_of_life.py
===========================================================================

A small standalone storyworld for a slice-of-life suspense tale about noticing
small clues, waiting for a reveal, and ending on a gentle resolved image.

The seed words are woven into the prose:
- glorious
- perceive

The domain is intentionally modest: a child notices a strange missing sound at
home, worries briefly, investigates with a parent, and discovers a simple,
everyday explanation. The suspense comes from delayed understanding rather than
danger.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

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
class Place:
    id: str
    label: str
    indoors: bool = True
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


@dataclass
class SoundSource:
    id: str
    label: str
    sound: str
    can_be_missing: bool = True
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


@dataclass
class Clue:
    id: str
    label: str
    kind: str
    clue_text: str
    reveals: str
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


@dataclass
class Resolution:
    id: str
    label: str
    action: str
    comfort: str
    applause: str
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for kid in list(world.entities.values()):
        if kid.role != "child" or kid.memes["worry"] < THRESHOLD:
            continue
        sig = ("worry", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "parent" in world.entities:
            world.get("parent").memes["alert"] += 1
        out.append("__worry__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("resolved") and "child" in world.entities:
        child = world.get("child")
        sig = ("relief", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["relief"] += 1
            out.append("__relief__")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry), Rule("relief", _r_relief)]


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


def predict_missing_sound(world: World, source_id: str) -> dict:
    sim = world.copy()
    sim.get(source_id).meters["silence"] += 1
    propagate(sim, narrate=False)
    return {
        "missing": sim.get(source_id).meters["silence"] >= THRESHOLD,
        "worry": sim.get("child").memes["worry"] if "child" in sim.entities else 0,
    }


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for source_id, source in SOURCES.items():
            if not source.can_be_missing:
                continue
            for clue_id, clue in CLUES.items():
                if clue.kind == source_id:
                    combos.append((place_id, source_id, clue_id))
    return combos


@dataclass
class StoryParams:
    place: str
    source: str
    clue: str
    child_name: str
    child_gender: str
    parent_type: str
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


PLACES = {
    "kitchen": Place(id="kitchen", label="the kitchen"),
    "hallway": Place(id="hallway", label="the hallway"),
    "laundry": Place(id="laundry", label="the laundry room"),
}

SOURCES = {
    "kettle": SoundSource(id="kettle", label="the kettle", sound="a low whistle"),
    "washing_machine": SoundSource(id="washing_machine", label="the washing machine", sound="a soft thump"),
    "oven_timer": SoundSource(id="oven_timer", label="the oven timer", sound="a tiny ring"),
}

CLUES = {
    "steam": Clue(id="steam", label="a curl of steam", kind="kettle", clue_text="They could see a thin curl of steam near it.", reveals="the kettle had gone quiet because the water had finished."),
    "thump": Clue(id="thump", label="a steady thump", kind="washing_machine", clue_text="They heard a steady thump from behind the door.", reveals="the washing machine was turning a blanket and a load of towels."),
    "ring": Clue(id="ring", label="a ringing beep", kind="oven_timer", clue_text="They heard a ringing beep from the warm room.", reveals="the oven timer had finished while a pan cooled safely inside."),
}

RESOLUTIONS = {
    "check": Resolution(id="check", label="check on it", action="went to check", comfort="stood by the doorway", applause="smiled with relief"),
    "wait": Resolution(id="wait", label="wait a moment", action="waited a moment", comfort="kept watching calmly", applause="nodded when the answer came"),
    "ask": Resolution(id="ask", label="ask a grown-up", action="asked a grown-up", comfort="held their hand", applause="said the safest thing was to ask"),
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "June", "Tessa", "Ada"]
BOY_NAMES = ["Theo", "Ben", "Milo", "Eli", "Finn", "Owen"]


def explain_rejection(place: Place, source: SoundSource, clue: Clue) -> str:
    return "(No story: this clue does not match the chosen sound source.)"


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for sid in SOURCES:
        lines.append(asp.fact("source", sid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("clue_kind", cid, clue.kind))
    for rid in RESOLUTIONS:
        lines.append(asp.fact("resolution", rid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,S,C) :- place(P), source(S), clue(C), clue_kind(C,S).
suspense(C) :- clue(C).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    p = set(valid_combos())
    if a != p:
        print("MISMATCH between ASP and Python valid_combos():")
        if a - p:
            print("  only in ASP:", sorted(a - p))
        if p - a:
            print("  only in Python:", sorted(p - a))
        return 1

    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, source=None, clue=None, name=None, gender=None, parent=None), random.Random(777)))
        _ = sample.story
        _ = sample.to_json()
    except Exception as exc:  # pragma: no cover
        print(f"SMOKE TEST FAILED: {exc}")
        return 1

    print(f"OK: ASP matches Python on {len(a)} combos, and generation smoke test passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small suspenseful slice-of-life storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--resolution", choices=RESOLUTIONS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.source and args.clue and CLUES[args.clue].kind != args.source:
        raise StoryError(explain_rejection(PLACES[args.place or "kitchen"], SOURCES[args.source], CLUES[args.clue]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.source is None or c[1] == args.source)
              and (args.clue is None or c[2] == args.clue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, source, clue = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    return StoryParams(
        place=place,
        source=source,
        clue=clue,
        child_name=args.name or rng.choice(name_pool),
        child_gender=gender,
        parent_type=args.parent or rng.choice(["mother", "father"]),
    )


def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=params.child_gender, role="child", attrs={"name": params.child_name}))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent_type, role="parent"))
    place = PLACES[params.place]
    source = SOURCES[params.source]
    clue = CLUES[params.clue]
    resolution = RESOLUTIONS["check" if params.parent_type == "mother" else "ask"]

    child.id = params.child_name
    child.attrs["place"] = place.id
    child.attrs["source"] = source.id
    child.attrs["clue"] = clue.id
    world.facts["place"] = place
    world.facts["source"] = source
    world.facts["clue"] = clue
    world.facts["resolution"] = resolution

    child.memes["curiosity"] += 1
    world.say(f"On a quiet afternoon, {child.id} was moving through {place.label}.")
    world.say(f"Everything felt ordinary, yet {child.id} could perceive that something was off.")

    world.para()
    world.say(f"From somewhere nearby came {source.sound}, but no clear clue answered it at first.")
    child.memes["worry"] += 1
    if clue.id == "steam":
        world.say("A pause stretched out, and the hush felt almost glorious in its stillness.")
    world.say(f"{clue.clue_text}")

    pred = predict_missing_sound(world, "source")
    world.facts["predicted_missing"] = pred["missing"]

    world.para()
    world.say(f"{child.id} frowned, then {parent.label_word} came closer and listened too.")
    world.say(f'"Let\'s {resolution.label}," {parent.label_word} said, calm but alert.')
    world.say(f"They {resolution.action} together, with {parent.label_word} {resolution.comfort}.")

    world.para()
    world.say(f"At last, the mystery was simple: {clue.reveals}")
    world.say(f"{child.id} felt relief wash over the room like warm light after rain.")
    world.say(f"It was a small, glorious moment of understanding, the kind one can only perceive after waiting long enough.")

    child.memes["worry"] = 0.0
    child.memes["relief"] += 1
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a slice-of-life suspense story that includes the words 'glorious' and 'perceive' and takes place in {f['place'].label}.",
        f"Tell a gentle story where a child hears {f['source'].sound}, waits, and then learns the answer with a parent.",
        f"Write a quiet suspense story about noticing a small clue: {f['clue'].label}, and ending with relief.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = world.get("child")
    parent = world.get("parent")
    source = f["source"]
    clue = f["clue"]
    return [
        ("What was the story about?", f"It was about {child.id} and {parent.label_word} noticing a small mystery at home. The suspense came from not understanding the sound right away."),
        (f"Why was {child.id} worried?", f"{child.id} heard {source.sound} and could not immediately tell what made it. That uncertainty made the moment feel suspenseful."),
        ("How did the mystery get solved?", f"They looked and listened together, and the clue turned out to be {clue.reveals}. The answer was ordinary, which made the ending peaceful."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does it mean to perceive something?", "To perceive something means to notice or understand it through your senses or your mind."),
        ("What does glorious mean?", "Glorious means wonderfully bright, beautiful, or full of praise and joy."),
        ("What is suspense?", "Suspense is the feeling of waiting to find out what is happening or what will happen next."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i+1}. {p}" for i, p in enumerate(sample.prompts))
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.source not in SOURCES or params.clue not in CLUES:
        raise StoryError("Invalid params for this storyworld.")
    source = SOURCES[params.source]
    clue = CLUES[params.clue]
    if clue.kind != source.id:
        raise StoryError(explain_rejection(PLACES[params.place], source, clue))
    world = tell(params)
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


CURATED = [
    StoryParams(place="kitchen", source="kettle", clue="steam", child_name="Mina", child_gender="girl", parent_type="mother"),
    StoryParams(place="laundry", source="washing_machine", clue="thump", child_name="Theo", child_gender="boy", parent_type="father"),
    StoryParams(place="kitchen", source="oven_timer", clue="ring", child_name="Lily", child_gender="girl", parent_type="mother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for p, s, c in combos:
            print(f"  {p:10} {s:16} {c}")
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
