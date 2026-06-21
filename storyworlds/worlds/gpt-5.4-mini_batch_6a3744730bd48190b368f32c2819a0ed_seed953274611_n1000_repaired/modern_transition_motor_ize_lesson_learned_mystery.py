#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/modern_transition_motor_ize_lesson_learned_mystery.py
======================================================================================

A small slice-of-life storyworld about a curious child who notices a modern
machine behaving strangely, follows clues through a simple transition, and learns
a lesson by the end. The domain is built around the seed words:

- modern
- transition
- motor-ize

and the features:

- Lesson Learned
- Mystery to Solve
- Curiosity

The world is intentionally small and concrete: a child, a grown-up, one home
setting, one machine, one missing thing, and one sensible fix. Stories are
state-driven rather than frozen paraphrases, and the ending image proves what
changed.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
CURIOUS_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
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
class Place:
    id: str
    label: str
    scene: str
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
class Machine:
    id: str
    label: str
    phrase: str
    makes_noise: str
    modern: bool = True
    motorized: bool = True
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
class MissingThing:
    id: str
    label: str
    clue: str
    where_found: str
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
class Fix:
    id: str
    label: str
    action: str
    result: str
    sense: int
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
    place: str
    machine: str
    missing: str
    fix: str
    child: str
    child_gender: str
    grownup: str
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


@dataclass
class World:
    place: Place
    child: Entity
    grownup: Entity
    machine: Entity
    missing: Entity
    fixed: bool = False
    solved: bool = False
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = copy.deepcopy(self)
        clone.paragraphs = [[]]
        return clone
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
    "kitchen": Place(id="kitchen", label="the kitchen", scene="a tidy kitchen table", tags={"home", "modern"}),
    "laundry": Place(id="laundry", label="the laundry room", scene="a bright laundry nook", tags={"home", "modern"}),
    "hall": Place(id="hall", label="the hallway", scene="a narrow hallway with a shoe bench", tags={"home", "transition"}),
}

MACHINES = {
    "vacuum": Machine(id="vacuum", label="vacuum", phrase="a modern vacuum", makes_noise="whirr", tags={"modern", "motor-ize"}),
    "toy_car": Machine(id="toy_car", label="toy car", phrase="a motor-ized toy car", makes_noise="brrr", tags={"motor-ize"}),
    "fan": Machine(id="fan", label="fan", phrase="a modern fan", makes_noise="hum", tags={"modern"}),
}

MISSING = {
    "remote": MissingThing(id="remote", label="remote", clue="the little remote was missing", where_found="on the couch", tags={"mystery", "modern"}),
    "battery": MissingThing(id="battery", label="battery", clue="one battery had rolled away", where_found="under a chair", tags={"mystery", "motor-ize"}),
    "sock": MissingThing(id="sock", label="sock", clue="one sock had slipped off", where_found="behind a basket", tags={"mystery", "transition"}),
}

FIXES = {
    "look": Fix(id="look", label="look carefully", action="looked carefully", result="found the missing thing", sense=3, tags={"curiosity"}),
    "ask": Fix(id="ask", label="ask for help", action="asked for help", result="got a clue from a grown-up", sense=3, tags={"lesson"}),
    "clean": Fix(id="clean", label="clean up the space", action="cleared the floor", result="made room to see better", sense=2, tags={"lesson"}),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Theo", "Ben", "Max", "Leo", "Finn", "Eli"]


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= 2]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for machine_id, machine in MACHINES.items():
            if "modern" not in place.tags and "modern" not in machine.tags:
                continue
            for missing_id, miss in MISSING.items():
                if "mystery" not in miss.tags:
                    continue
                for fix_id, fix in FIXES.items():
                    if fix.sense >= 2:
                        combos.append((place_id, machine_id, missing_id, fix_id))
    return combos


def reason_invalid(place: Place, machine: Machine, missing: MissingThing, fix: Fix) -> str:
    if fix.sense < 2:
        return f"(No story: '{fix.label}' is too weak a fix for a real mystery.)"
    return "(No story: this combination does not support a small, sensible home mystery.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: modern life, a small transition, a motor-ized mystery, and a lesson learned."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--machine", choices=MACHINES)
    ap.add_argument("--missing", choices=MISSING)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--grownup", choices=["mother", "father"])
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


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for mid, m in MACHINES.items():
        lines.append(asp.fact("machine", mid))
        if m.modern:
            lines.append(asp.fact("modern", mid))
        if m.motorized:
            lines.append(asp.fact("motorized", mid))
    for iid in MISSING:
        lines.append(asp.fact("missing", iid))
        lines.append(asp.fact("mystery_item", iid))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, f.sense))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,M,I,F) :- place(P), machine(M), missing(I), fix(F), sense(F,S), sense_min(Min), S >= Min.
"""

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = set(asp_valid_combos()) == set(valid_combos())
    print("OK: ASP parity matches Python." if ok else "MISMATCH: ASP and Python differ.")
    return 0 if ok else 1


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.machine is None or c[1] == args.machine)
              and (args.missing is None or c[2] == args.missing)
              and (args.fix is None or c[3] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, machine, missing, fix = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or _pick_name(rng, gender)
    grownup = args.grownup or rng.choice(["mother", "father"])
    return StoryParams(place=place, machine=machine, missing=missing, fix=fix, child=name, child_gender=gender, grownup=grownup)


def _do_mystery(world: World) -> None:
    kid = world.child
    kid.memes["curiosity"] += 1
    world.say(f"{kid.id} noticed {world.machine.label_word if hasattr(world.machine, 'label_word') else world.machine.label}.")
    world.say(f"It made a {world.machine.attrs['sound']} sound and looked very {world.machine.attrs['style']}.")
    world.say(f"But then {world.missing.label} was gone, and {kid.id} wanted to know why.")


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.machine not in MACHINES or params.missing not in MISSING or params.fix not in FIXES:
        raise StoryError("Invalid story parameters.")
    place = PLACES[params.place]
    machine_cfg = MACHINES[params.machine]
    missing_cfg = MISSING[params.missing]
    fix_cfg = FIXES[params.fix]
    if fix_cfg.sense < 2:
        raise StoryError(reason_invalid(place, machine_cfg, missing_cfg, fix_cfg))

    child = Entity(id=params.child, kind="character", type=params.child_gender, role="child", attrs={"age": 6})
    grownup = Entity(id="Parent", kind="character", type=params.grownup, role="grownup")
    machine = Entity(id=machine_cfg.id, kind="thing", type="machine", label=machine_cfg.label,
                     attrs={"phrase": machine_cfg.phrase, "sound": machine_cfg.makes_noise, "style": "modern"})
    missing = Entity(id=missing_cfg.id, kind="thing", type="missing", label=missing_cfg.label,
                     attrs={"clue": missing_cfg.clue, "where_found": missing_cfg.where_found})

    world = World(place=place, child=child, grownup=grownup, machine=machine, missing=missing)
    child.memes["curiosity"] += 2
    world.say(f"One afternoon, {child.id} was in {place.label}.")
    world.say(f"{child.id} saw {machine_cfg.phrase} and thought it looked very modern.")
    world.say(f"{missing_cfg.clue.capitalize()}.")

    world.para()
    world.say(f"{child.id} stayed curious and chose a small transition: instead of rushing, {child.pronoun().capitalize()} took a slow look around.")
    if fix_cfg.id == "look":
        world.say(f"{child.id} {fix_cfg.action} under the table and behind the chair.")
    elif fix_cfg.id == "ask":
        world.say(f"{child.id} {fix_cfg.action}, and the grown-up pointed to where things usually roll.")
    else:
        world.say(f"{child.id} {fix_cfg.action} first so the room was easier to search.")

    world.para()
    child.memes["lesson"] += 1
    world.fixed = True
    world.solved = True
    world.say(f"At last, {child.id} {fix_cfg.result} at {missing_cfg.where_found}.")
    world.say(f"That solved the little mystery, and {child.id} learned that curiosity works best when it moves step by step.")
    world.say(f"By evening, the room felt calm again, and the modern machine sat ready for tomorrow.")

    world.facts.update(
        place=place, machine_cfg=machine_cfg, missing_cfg=missing_cfg, fix_cfg=fix_cfg,
        child=child, grownup=grownup, outcome="solved", discovered=True,
    )

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
        f"Write a slice-of-life mystery story for a young child that includes the word 'modern' and ends with a lesson learned.",
        f"Tell a gentle home story where {f['child'].id} notices something missing near a {f['machine_cfg'].label} and solves the mystery with curiosity.",
        f"Write a story about a small transition from confusion to understanding using the words modern, transition, and motor-ize.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    grownup = f["grownup"]
    miss = f["missing_cfg"]
    machine = f["machine_cfg"]
    return [
        ("Who is the story about?", f"It is about {child.id}, who notices a little mystery at home and then solves it."),
        ("Why was {0} curious?".format(child.id), f"{child.id} was curious because something important was missing near the {machine.label}. That made the room feel puzzling until {child.id} looked more carefully."),
        ("What lesson did {0} learn?".format(child.id), f"{child.id} learned that curiosity works best when it is calm and step by step. Asking, looking, and cleaning up a little can solve a mystery without turning it into a bigger problem."),
        ("How did the grown-up help?", f"{grownup.id} gave a clue about where things usually roll or hide, which helped {child.id} solve the mystery."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["machine_cfg"].tags) | set(f["missing_cfg"].tags) | {"curiosity", "lesson"}
    items = {
        "modern": ("What does modern mean?", "Modern means new or up-to-date, like things people use in everyday life now."),
        "motor-ize": ("What does motor-ize mean?", "To motor-ize something means to give it a motor so it can move on its own."),
        "curiosity": ("What is curiosity?", "Curiosity is the feeling that makes you want to look, ask, and learn more."),
        "mystery": ("What is a mystery?", "A mystery is something puzzling that you do not understand yet."),
        "lesson": ("What is a lesson learned?", "A lesson learned is a good idea you remember after something happens."),
    }
    out = []
    for key in ["modern", "motor-ize", "curiosity", "mystery", "lesson"]:
        if key in tags:
            out.append(items[key])
    return out


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in [world.child, world.grownup, world.machine, world.missing]:
        lines.append(f"  {e.id:8} ({e.kind:7}) meters={dict((k, v) for k, v in e.meters.items() if v)} memes={dict((k, v) for k, v in e.memes.items() if v)} attrs={e.attrs}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", machine="vacuum", missing="remote", fix="look", child="Mia", child_gender="girl", grownup="mother"),
    StoryParams(place="hall", machine="toy_car", missing="battery", fix="ask", child="Theo", child_gender="boy", grownup="father"),
    StoryParams(place="laundry", machine="fan", missing="sock", fix="clean", child="Nora", child_gender="girl", grownup="mother"),
]


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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
