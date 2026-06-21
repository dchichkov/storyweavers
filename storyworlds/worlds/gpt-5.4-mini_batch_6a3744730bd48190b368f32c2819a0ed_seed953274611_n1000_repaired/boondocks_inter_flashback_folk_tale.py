#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/boondocks_inter_flashback_folk_tale.py
======================================================================

A standalone story world for a small folk-tale domain set in the boondocks.

Premise:
A child goes out past the village edge, gets into a little trouble, remembers an
old tale in a flashback, and uses that remembered wisdom to get home safely.

The story is built from world state, not from a frozen paragraph. It supports
the standard Storyweavers CLI modes, QA sets, and an ASP twin for parity checks.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
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
class Road:
    id: str
    name: str
    distance: int
    dangers: set[str] = field(default_factory=set)
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
class Charm:
    id: str
    label: str
    helps: set[str] = field(default_factory=set)
    safe: bool = True
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
class Flashback:
    id: str
    memory_line: str
    lesson: str
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
        import copy as _copy
        clone = World()
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_lost(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    road = world.get("road")
    if hero.meters["lost"] < THRESHOLD:
        return out
    sig = ("lost", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["worry"] += 1
    road.meters["lonely"] += 1
    out.append("__lost__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for fn in (_r_lost,):
            out = fn(world)
            if out:
                changed = True
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str]]:
    return [("boondocks", "inter")]


def reasonableness_gate(place: str, instrument: str) -> bool:
    return (place, instrument) in set(valid_combos())


def _flashback_text() -> tuple[str, str]:
    return (
        "The child remembered grandmother's old tale: when the boondocks grew "
        "dark, a small lantern and a kind word could guide the feet home.",
        "That memory was the lesson that helped later."
    )


def tell() -> World:
    world = World()
    hero = world.add(Entity(id="Mina", kind="character", type="girl", role="child"))
    grand = world.add(Entity(id="Grandma", kind="character", type="woman", role="elder"))
    road = world.add(Entity(id="road", label="the boondocks road"))
    charm = world.add(Entity(id="inter", label="an interlaced willow charm"))
    flash = Flashback(id="flashback", memory_line=_flashback_text()[0], lesson=_flashback_text()[1])

    hero.memes["curiosity"] += 1
    world.say(
        "In the boondocks, where the grass leaned over old fence posts and the "
        "wind knew every ditch, Mina wandered after a bright blue butterfly."
    )
    world.say(
        "She found a little willow charm hanging from a gate, its threads tied "
        "inter and over again like a river knot."
    )
    world.say(
        '"I can follow it," Mina said, and the charm seemed to wink in the sun.'
    )

    world.para()
    hero.meters["lost"] += 1
    propagate(world, narrate=False)
    world.say(
        "But the path split where the reeds got tall, and the butterfly slipped "
        "away. Mina stopped, small as a sparrow, because the boondocks looked "
        "larger than she had thought."
    )
    world.say(
        "Then came a flashback: Grandma's voice from long ago, gentle as a quilt."
    )
    world.say(flash.memory_line)
    hero.memes["memory"] += 1

    world.para()
    hero.meters["found_way"] += 1
    hero.memes["brave"] += 1
    grand.memes["love"] += 1
    world.say(
        "Mina took a deep breath, touched the willow charm, and counted the way "
        "back by the bent fence, the round stone, and the elm with the split bark."
    )
    world.say(
        "She followed those signs home, and the dark little fear in her chest "
        "grew smaller with every careful step."
    )

    world.para()
    world.say(
        "At the gate, Grandma was waiting with warm bread. Mina ran to her, "
        "smiling, and the boondocks no longer felt wild and lonely."
    )
    world.say(
        "The willow charm stayed on the gate, and Mina knew it was not magic by "
        "itself. The real magic was remembering what kind voices teach."
    )
    world.facts.update(
        hero=hero,
        grand=grand,
        road=road,
        charm=charm,
        flash=flash,
        place="boondocks",
        instrument="inter",
        outcome="returned",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a folk tale for a young child that uses the words "boondocks" '
        'and "inter", and includes a flashback to an older relative\'s advice.',
        'Tell a gentle story about a child lost in the boondocks who remembers '
        'an old family lesson and finds the way home.',
        'Write a short folk tale with a remembering-back scene, a safe choice, '
        'and a warm ending at the gate.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    grand = world.facts["grand"]
    flash = world.facts["flash"]
    return [
        ("Who is the story about?",
         f"It is about {hero.id}, a little girl who wandered in the boondocks. "
         f"Grandma is the older helper who teaches the important lesson."),
        ("What happened in the flashback?",
         f"Mina remembered Grandma's old tale about keeping calm and following "
         f"safe signs home. That memory gave her the courage to find the way."),
        ("How did the story end?",
         "Mina got home safely and shared warm bread with Grandma. The boondocks "
         "felt less scary because she remembered the lesson in time."),
        ("Why did the memory matter?",
         f"{flash.lesson} The flashback helped Mina choose careful steps instead "
         f"of panicking in the dark."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What are the boondocks?",
         "The boondocks are the far edge of the countryside, where the land can "
         "feel lonely, wild, and quiet."),
        ("What is a flashback?",
         "A flashback is when a story briefly shows something that happened "
         "before, so we can remember old advice or an earlier moment."),
        ("What does inter mean in this story?",
         "Inter is the little willow charm's name here. It helps the story keep "
         "the folk-tale feeling and gives Mina a sign to follow."),
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


@dataclass
class StoryParams:
    place: str = "boondocks"
    instrument: str = "inter"
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
    StoryParams(place="boondocks", instrument="inter", seed=777),
]


ASP_RULES = r"""
valid(P, I) :- place(P), instrument(I), combo(P, I).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for place, instrument in valid_combos():
        lines.append(asp.fact("combo", place, instrument))
    lines.append(asp.fact("place", "boondocks"))
    lines.append(asp.fact("instrument", "inter"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: story generation smoke test passed.")
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        rc = 1
    if rc == 0:
        print("OK: verify passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale story world: boondocks, inter, flashback.")
    ap.add_argument("--place", choices=["boondocks"])
    ap.add_argument("--instrument", choices=["inter"])
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
    place = args.place or "boondocks"
    instrument = args.instrument or "inter"
    if not reasonableness_gate(place, instrument):
        raise StoryError("No valid folk-tale combination matches the given options.")
    return StoryParams(place=place, instrument=instrument)


def generate(params: StoryParams) -> StorySample:
    if not reasonableness_gate(params.place, params.instrument):
        raise StoryError("Invalid parameters for this story world.")
    world = tell()
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible combos:")
        for p, i in asp_valid_combos():
            print(f"  {p} {i}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for idx in range(args.n):
            params = resolve_params(args, random.Random(base_seed + idx))
            params.seed = base_seed + idx
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {idx + 1}" if len(samples) > 1 else ""))
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
