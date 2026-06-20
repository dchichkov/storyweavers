#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/plaque_gloop_eleventh_suspense_dialogue_flashback_animal.py
=============================================================================================

A standalone story world about a small animal adventure in a quiet hallway:
a curious animal notices an eleventh plaque, a mysterious gloop stain, pauses
in suspense, remembers an earlier flashback, talks it through in dialogue, and
cleans up the mess with help.

The world is built to satisfy the storyworld contract:
- typed entities with meters and memes
- state-driven prose
- reasonableness gates
- inline ASP twin
- three QA sets grounded in world state
- complete CLI with default, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, --show-asp
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
SUSPENSE_MIN = 2


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

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"cat", "tomcat", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "mouse", "rabbit", "fox", "bird"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Animal:
    id: str
    type: str
    label: str
    habitat: str
    voice: str
    curiosity: int
    tidiness: int
    flashback_note: str
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class ObjectThing:
    id: str
    label: str
    phrase: str
    kind: str
    place: str
    can_gloop: bool = False
    numbered: bool = False
    number: int = 0
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class GloopSource:
    id: str
    label: str
    phrase: str
    splash: str
    sticky: int
    safe_handled: bool
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self) -> None:
        self.entities: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_suspense(world: World) -> list[str]:
    out = []
    animal = world.get("animal")
    plaque = world.get("plaque")
    gloop = world.get("gloop")
    if plaque.meters["glooped"] >= THRESHOLD and ("suspense", "start") not in world.fired:
        world.fired.add(("suspense", "start"))
        animal.memes["suspense"] += 1
        out.append("__suspense__")
    if gloop.meters["revealed"] >= THRESHOLD and ("suspense", "fade") not in world.fired:
        world.fired.add(("suspense", "fade"))
        animal.memes["relief"] += 1
        out.append("__relief__")
    return out


def _r_cleanup(world: World) -> list[str]:
    out = []
    cleaner = world.get("animal")
    plaque = world.get("plaque")
    if cleaner.meters["cleaning"] < THRESHOLD:
        return out
    if plaque.meters["glooped"] < THRESHOLD:
        return out
    if ("cleanup", "done") in world.fired:
        return out
    world.fired.add(("cleanup", "done"))
    plaque.meters["glooped"] = 0.0
    gloop = world.get("gloop")
    gloop.meters["revealed"] += 1
    cleaner.memes["pride"] += 1
    out.append("__cleanup__")
    return out


CAUSAL_RULES = [
    Rule("suspense", "social", _r_suspense),
    Rule("cleanup", "physical", _r_cleanup),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
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


def is_reasonable(params: "StoryParams") -> bool:
    return params.scene in SCENES and params.cleaner in ANIMALS and params.gloop in GLOOPS


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for scene in SCENES:
        for cleaner in ANIMALS:
            for gloop in GLOOPS:
                if scene.supports_gloop and gloop.sticky >= 1:
                    out.append((scene.id, cleaner.id, gloop.id))
    return out


def reason_for_rejection(scene: "Scene", gloop: GloopSource) -> str:
    if not scene.supports_gloop:
        return "(No story: that scene has no plaque for gloop to stick to.)"
    return "(No story: that gloop is too harmless for a suspenseful plaque story.)"


def _animal_name(rng: random.Random, species: str) -> str:
    pool = {
        "cat": ["Milo", "Pip", "Toby", "Mimi"],
        "mouse": ["Nip", "Mina", "Tansy", "Dot"],
        "rabbit": ["Bun", "Lola", "Poppy", "Fenn"],
        "fox": ["Ruby", "Sly", "Junie", "Flick"],
        "bird": ["Wren", "Sky", "Tiki", "Peep"],
    }[species]
    return rng.choice(pool)


@dataclass
class Scene:
    id: str
    place: str
    mood: str
    plaque_text: str
    support_line: str
    supports_gloop: bool = True

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
@dataclass
class StoryParams:
    scene: str
    cleaner: str
    gloop: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


SCENES = {
    "hall": Scene("hall", "the museum hall", "quiet", "Eleventh Plaque", "The hall was quiet and full of little echoes.", True),
    "barn": Scene("barn", "the barn wall", "still", "Eleventh Prize Plaque", "The barn was still, with soft straw underfoot.", True),
    "library": Scene("library", "the animal library", "hushed", "Eleventh Reading Plaque", "The library was hushed, and every step sounded tiny.", True),
}

ANIMALS = {
    "cat": Animal("cat", "cat", "cat", "window-sill", "meow", 6, 6, "The cat had once knocked over a paint cup and learned to slow down."),
    "mouse": Animal("mouse", "mouse", "mouse", "wall-crack", "squeak", 8, 7, "The mouse had once followed crumbs into trouble and had remembered to ask first."),
    "rabbit": Animal("rabbit", "rabbit", "rabbit", "hay-corner", "thump", 7, 8, "The rabbit had once found sticky jam on a bench and cleaned it with help."),
    "fox": Animal("fox", "fox", "fox", "quiet den", "whisper", 6, 5, "The fox had once hidden in a pile of leaves and watched carefully."),
}

GLOOPS = {
    "jam": GloopSource("jam", "jam", "a jar of jam", "spilled", 2, False),
    "paint": GloopSource("paint", "paint", "a tipped paint cup", "dripped", 2, False),
    "mud": GloopSource("mud", "mud", "a muddy pawprint", "splashed", 1, False),
}


def tell(scene: Scene, cleaner: Animal, gloop: GloopSource) -> World:
    world = World()
    animal = world.add(Entity(id="animal", kind="character", type=cleaner.type, label=cleaner.label, role="hero",
                              traits=["curious", "careful"]))
    plaque = world.add(ObjectThing(id="plaque", label="plaque", phrase=scene.plaque_text, kind="plaque", place=scene.place, can_gloop=True, numbered=True, number=11))
    source = world.add(Entity(id="gloop", kind="thing", type="thing", label=gloop.label, role="source"))
    source.meters["sticky"] = float(gloop.sticky)
    animal.memes["curiosity"] += cleaner.curiosity
    animal.memes["tidiness"] += cleaner.tidiness
    plaque.meters["glooped"] = 1.0
    animal.meters["waiting"] = 1.0

    world.say(f"In {scene.place}, {cleaner.label} found the {scene.plaque_text}.")
    world.say(f"At the eleventh plaque, a dark patch of gloop looked strange and a little scary.")
    world.say(f'"What is that?" {cleaner.label} asked, leaning close. "{gloop.label}?"')
    world.para()
    world.say(f"{scene.support_line}")
    world.say(f'{cleaner.label} remembered a flashback: {cleaner.flashback_note}')
    world.say(f'"Not this time," {cleaner.label} whispered. "We can clean it carefully."')
    world.say(f'"Do you think it will come off?" a tiny voice asked from behind the bench.')
    world.say(f'"If we take it slow, yes," {cleaner.label} said.')
    world.para()
    animal.meters["cleaning"] += 1
    propagate(world, narrate=False)
    world.say(f"{cleaner.label} used a damp cloth and worked at the gloop until the plaque shone again.")
    world.say(f"The eleventh plaque was clean, and the hallway felt safe and bright once more.")
    world.say(f"Outside, the little animal smiled at the neat sign and walked away with a proud step.")

    world.facts.update(
        scene=scene,
        cleaner=cleaner,
        gloop=gloop,
        plaque=plaque,
        outcome="cleaned",
        plaque_number=11,
        flashback=cleaner.flashback_note,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    cleaner = f["cleaner"]
    gloop = f["gloop"]
    scene = f["scene"]
    return [
        f'Write an animal story with the words "plaque", "gloop", and "eleventh".',
        f"Tell a suspenseful animal story where {cleaner.label} spots gloop on an eleventh plaque and decides what to do.",
        f'Write a story with dialogue and a flashback about {cleaner.label} cleaning a sticky plaque in {scene.place}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    cleaner = f["cleaner"]
    scene = f["scene"]
    plaque = f["plaque"]
    gloop = f["gloop"]
    return [
        QAItem(
            question="What did the animal find?",
            answer=f"{cleaner.label} found the eleventh plaque and noticed gloop stuck on it. The stain looked strange, so the animal stopped to figure out what had happened."
        ),
        QAItem(
            question="Why was the scene suspenseful?",
            answer=f"It was suspenseful because the gloop looked mysterious at first and nobody knew if it would come off. The animal had to decide carefully before touching it."
        ),
        QAItem(
            question="What helped the animal know what to do?",
            answer=f"A flashback helped. {cleaner.label} remembered {f['flashback']}, so the animal chose a careful way to clean the plaque."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The plaque ended up clean and shiny again. {cleaner.label} left the {scene.place} feeling proud because the mess was gone."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="What is a plaque?",
            answer="A plaque is a sign or flat marker that can hold words, a number, or a message. It is often attached to a wall or stand."
        ),
        QAItem(
            question="What is gloop?",
            answer="Gloop is a sticky mess. It can smear on things and usually needs careful cleaning."
        ),
        QAItem(
            question="What does eleventh mean?",
            answer="Eleventh means number 11. It comes after tenth and before twelfth."
        ),
        QAItem(
            question="Why do animals in stories often talk?",
            answer="Talking animals make the story feel playful and easy to follow. Their dialogue lets readers hear what they think and feel."
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("hall", "cat", "jam"),
    StoryParams("barn", "mouse", "paint"),
    StoryParams("library", "rabbit", "mud"),
    StoryParams("hall", "fox", "paint"),
]


def valid_story_params(params: StoryParams) -> bool:
    return params.scene in SCENES and params.cleaner in ANIMALS and params.gloop in GLOOPS


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SCENES.items():
        lines.append(asp.fact("scene", sid))
        if s.supports_gloop:
            lines.append(asp.fact("supports_gloop", sid))
    for aid in ANIMALS:
        lines.append(asp.fact("animal", aid))
    for gid, g in GLOOPS.items():
        lines.append(asp.fact("gloop", gid))
        lines.append(asp.fact("sticky", gid, g.sticky))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, A, G) :- scene(S), animal(A), gloop(G), supports_gloop(S), sticky(G, N), N >= 1.
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    try:
        sample = generate(CURATED[0])
        assert sample.story
        print("OK: generate smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"MISMATCH: generate smoke test failed: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: plaque, gloop, eleventh, suspense, dialogue, flashback.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--cleaner", choices=ANIMALS)
    ap.add_argument("--gloop", choices=GLOOPS)
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
    combos = [c for c in valid_combos()
              if (args.scene is None or c[0] == args.scene)
              and (args.cleaner is None or c[1] == args.cleaner)
              and (args.gloop is None or c[2] == args.gloop)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, cleaner, gloop = rng.choice(sorted(combos))
    return StoryParams(scene, cleaner, gloop, seed=None)


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, scene in SCENES.items():
        for aid in ANIMALS:
            for gid, g in GLOOPS.items():
                if scene.supports_gloop and g.sticky >= 1:
                    out.append((sid, aid, gid))
    return out


def generate(params: StoryParams) -> StorySample:
    animal_cfg = ANIMALS[params.cleaner]
    world = tell(SCENES[params.scene], animal_cfg, GLOOPS[params.gloop])
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible (scene, cleaner, gloop) combos:")
        for c in asp_valid_combos():
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen = set()
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
