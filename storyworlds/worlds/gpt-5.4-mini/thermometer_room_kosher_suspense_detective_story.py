#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/thermometer_room_kosher_suspense_detective_story.py
====================================================================================

A small standalone storyworld for a suspenseful detective-style tale in a room
with a thermometer and a kosher clue.

Premise
-------
A child detective notices that a room feels strangely off: the thermometer is
creeping up, a kosher snack is missing, and the whole room holds a hush. The
detective follows simple clues, discovers the source of the warmth, and fixes
the problem before the room gets too hot.

This world is intentionally tiny and constraint-checked:
- It models physical meters and emotional memes.
- It has a reasonableness gate.
- It has an inline ASP twin.
- It generates one complete, child-facing story plus three QA sets.
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
TEMP_SAFE = 1.0
TEMP_WARM = 2.0
TEMP_HIGH = 3.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class RoomConfig:
    id: str
    place: str
    vibe: str
    detail: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Clue:
    id: str
    label: str
    where: str
    effect: str
    risky: bool = False

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Fix:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


def _r_heat(world: World) -> list[str]:
    out: list[str] = []
    room = world.get("room")
    for ent in list(world.entities.values()):
        if ent.meters["heat_source"] < THRESHOLD:
            continue
        sig = ("heat", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        room.meters["warmth"] += 1
        out.append("__heat__")
    return out


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    room = world.get("room")
    if room.meters["warmth"] < THRESHOLD:
        return out
    sig = ("fear",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for ent in list(world.entities.values()):
        if ent.kind == "character":
            ent.memes["suspense"] += 1
    out.append("__suspense__")
    return out


CAUSAL_RULES = [Rule("heat", "physical", _r_heat), Rule("fear", "social", _r_fear)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
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


def reasonableness_gate(clue: Clue, fix: Fix) -> bool:
    return clue.risky and fix.sense >= 2


def resolve_fix(fix: Fix, warmth: float) -> bool:
    return fix.power >= warmth


def predict_world(world: World, clue: Clue) -> dict:
    sim = world.copy()
    sim.get("clue").meters["heat_source"] += 1
    propagate(sim, narrate=False)
    return {
        "warmth": sim.get("room").meters["warmth"],
        "suspense": sim.get("det").memes["suspense"],
    }


def setup_scene(world: World, det: Entity, adult: Entity, room: RoomConfig, clue: Clue) -> None:
    det.memes["curiosity"] += 1
    world.say(
        f"On a quiet afternoon, {det.id} stepped into the room and felt the hush right away. "
        f"The room was {room.vibe}, and {room.detail}."
    )
    world.say(
        f"{det.id} noticed the thermometer on the wall and the little kosher label on the snack tin."
    )
    world.say(
        f'"{det.id}," {adult.label_word} said softly, "please keep an eye on the room."'
    )


def notice_trouble(world: World, det: Entity, clue: Clue) -> None:
    world.say(
        f"{det.id} checked the thermometer again. It looked a little higher than before, and that made the room feel stranger."
    )
    world.say(
        f"Near the table, {det.id} found {clue.label} {clue.where}."
    )


def suspicion(world: World, det: Entity, clue: Clue) -> None:
    det.memes["suspense"] += 1
    world.say(
        f"{det.id} narrowed {det.pronoun('possessive')} eyes. "
        f'"That must be why the room feels off," {det.pronoun()} whispered.'
    )
    world.say("The detective followed the clue one careful step at a time.")


def reveal(world: World, adult: Entity, clue: Clue, fix: Fix) -> None:
    world.say(
        f"At last, the grown-up peeked behind the curtain and found the warm spot that was heating the room."
    )
    world.say(
        f'In a quick calm voice, {adult.label_word} used the simple fix: {fix.text}.'
    )


def fail_reveal(world: World, adult: Entity, clue: Clue, fix: Fix) -> None:
    world.say(
        f"The first try was too small, and the room stayed warm."
    )
    world.say(
        f'{adult.label_word} had to try again, because the detective case was not finished yet.'
    )


def ending(world: World, det: Entity, adult: Entity, clue: Clue, room: RoomConfig) -> None:
    det.memes["relief"] += 1
    world.say(
        f"After that, the thermometer drifted down, the kosher snack stayed safe, and the room felt plain and peaceful again."
    )
    world.say(
        f"{det.id} smiled at the quiet room, proud that the mystery was solved."
    )


def tell(room: RoomConfig, clue: Clue, fix: Fix, det_name: str = "Noa", det_type: str = "girl",
         adult_type: str = "mother") -> World:
    world = World()
    det = world.add(Entity(id=det_name, kind="character", type=det_type, role="detective"))
    adult = world.add(Entity(id="Adult", kind="character", type=adult_type, role="adult"))
    room_ent = world.add(Entity(id="room", type="room", label=room.place))
    thermometer = world.add(Entity(id="thermometer", type="thing", label="thermometer"))
    kosher_snack = world.add(Entity(id="snack", type="thing", label="kosher snack"))
    source = world.add(Entity(id="source", type="thing", label=clue.label))
    room_ent.meters["warmth"] = 0.0
    thermometer.meters["temperature"] = TEMP_SAFE
    source.meters["heat_source"] = 0.0

    setup_scene(world, det, adult, room, clue)
    world.para()
    notice_trouble(world, det, clue)
    suspicion(world, det, clue)
    pred = predict_world(world, clue)
    world.facts["predicted"] = pred
    world.facts["thermometer"] = thermometer
    world.facts["kosher_snack"] = kosher_snack
    world.facts["source"] = source

    source.meters["heat_source"] += 1
    propagate(world, narrate=False)
    room_ent.meters["warmth"] = max(room_ent.meters["warmth"], TEMP_WARM)

    world.para()
    if resolve_fix(fix, room_ent.meters["warmth"]):
        reveal(world, adult, clue, fix)
        room_ent.meters["warmth"] = 0.0
        thermometer.meters["temperature"] = TEMP_SAFE
        ending(world, det, adult, clue, room)
    else:
        fail_reveal(world, adult, clue, fix)
        room_ent.meters["warmth"] = TEMP_HIGH
        thermometer.meters["temperature"] = TEMP_HIGH
        world.say(
            f"The detective kept watching until the real problem was fixed and the room cooled."
        )
        ending(world, det, adult, clue, room)

    world.facts.update(
        detective=det,
        adult=adult,
        room_cfg=room,
        clue=clue,
        fix=fix,
        thermometer=thermometer,
        room_entity=room_ent,
        outcome="solved",
    )
    return world


ROOMS = {
    "study": RoomConfig("study", "a small study", "still and dim", "A desk lamp made a little pool of light"),
    "kitchen": RoomConfig("kitchen", "the kitchen", "quiet and tidy", "A checkered table held a neat stack of napkins"),
    "bedroom": RoomConfig("bedroom", "a tiny bedroom", "hushed and shadowy", "A toy train sat perfectly still on the rug"),
}

CLUES = {
    "radiator": Clue("radiator", "the radiator", "behind the curtain", "it was warming the room", risky=True),
    "sun": Clue("sun", "a sunbeam", "by the window", "it was heating the room", risky=True),
    "lamp": Clue("lamp", "a lamp left on", "on the shelf", "it was making the room warm", risky=True),
}

FIXES = {
    "window": Fix("window", 3, 3, "opened the window and let cool air slip into the room", "opened the window, but the room hardly cooled", "opened the window to cool the room"),
    "switch": Fix("switch", 3, 2, "switched off the lamp and waited a moment", "switched it off, but the room was still too warm", "switched off the light source"),
    "fan": Fix("fan", 2, 2, "turned on a fan and pointed it at the warm spot", "turned on the fan, but it was too weak", "used a fan to move the hot air away"),
}

GIRL_NAMES = ["Noa", "Mira", "Leah", "Maya", "Ari", "Zoe"]
BOY_NAMES = ["Eli", "Jonah", "Ben", "Theo", "Avi", "Noah"]


@dataclass
@dataclass
class StoryParams:
    room: str
    clue: str
    fix: str
    detective: str
    detective_gender: str
    adult: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for r in ROOMS:
        for c in CLUES:
            for f in FIXES:
                if reasonableness_gate(CLUES[c], FIXES[f]):
                    combos.append((r, c, f))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny suspenseful detective story world.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mother", "father"])
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
    if args.clue and args.fix and not reasonableness_gate(CLUES[args.clue], FIXES[args.fix]):
        raise StoryError("This clue and fix do not make a believable suspense story.")
    combos = [c for c in valid_combos()
              if (args.room is None or c[0] == args.room)
              and (args.clue is None or c[1] == args.clue)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    room, clue, fix = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    adult = args.adult or rng.choice(["mother", "father"])
    return StoryParams(room, clue, fix, name, gender, adult)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a suspenseful detective story for a 3-to-5-year-old that uses the words "thermometer", "room", and "kosher".',
        f"Tell a small mystery where {f['detective'].id} notices the thermometer in the room rising and follows a kosher clue to solve the problem.",
        f"Write a detective-style story with a quiet room, a thermometer, and a kosher snack that stays safe when the mystery is solved.",
    ]


def story_qa(world: World) -> list[QAItem]:
    d = world.facts["detective"]
    adult = world.facts["adult"]
    room = world.facts["room_cfg"]
    clue = world.facts["clue"]
    fix = world.facts["fix"]
    therm = world.facts["thermometer"]
    answer1 = (
        f"{d.id} is the detective in the story, and {adult.label_word} helps at the end. "
        f"They are in {room.place}, where the thermometer and the kosher snack matter to the mystery."
    )
    answer2 = (
        f"{d.id} noticed that the room was getting warmer and followed the clue behind the curtain. "
        f"That made the detective keep watch instead of ignoring the problem."
    )
    answer3 = (
        f"{adult.label_word.capitalize()} opened the window and cooled the room down. "
        f"After that, the thermometer went back to a safe reading and the kosher snack stayed fine."
    )
    return [
        QAItem("Who is the story about?", answer1),
        QAItem("Why did the detective feel suspense?", answer2),
        QAItem("How was the room fixed?", answer3),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What does a thermometer do?",
            "A thermometer tells you how warm or cold something is. It helps people notice when a room is getting too hot or too cold."
        ),
        QAItem(
            "What does kosher mean?",
            "Kosher means food is prepared in a way that follows Jewish food rules. People keep kosher food separate and treat it carefully."
        ),
        QAItem(
            "Why can a room feel suspicious in a mystery?",
            "A room can feel suspicious when something is out of place or changing, like a rising temperature or a clue hiding nearby. That is when a detective starts paying close attention."
        ),
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
    lines.append("== (3) World-knowledge questions ==")
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
warm_room :- heat_source(source).
suspense :- warm_room.
solved :- warm_room, fix_power(P), room_warmth(W), P >= W.
"""

def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("heat_source", "source"),
        asp.fact("fix_power", 3),
        asp.fact("room_warmth", 2),
    ]
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("", "#show solved/0."))
    asp_solved = bool(asp.atoms(model, "solved"))
    py_solved = True
    if asp_solved != py_solved:
        print("MISMATCH: ASP and Python disagree.")
        return 1
    try:
        generate(resolve_params(build_parser().parse_args([]), random.Random(0)))
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP parity and story generation smoke test passed.")
    return 0


CURATED = [
    StoryParams("study", "radiator", "window", "Noa", "girl", "mother"),
    StoryParams("kitchen", "lamp", "switch", "Eli", "boy", "father"),
    StoryParams("bedroom", "sun", "fan", "Mira", "girl", "father"),
]


def explain_rejection(clue: Clue, fix: Fix) -> str:
    return "This combination is not reasonable: the clue does not create enough suspense, or the fix does not address the warmed room."


def generate(params: StoryParams) -> StorySample:
    world = tell(ROOMS[params.room], CLUES[params.clue], FIXES[params.fix], params.detective, params.detective_gender, params.adult)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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
        print(asp_program("", "#show solved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("", "#show solved/0."))
        print("ASP atoms:", asp.atoms(model, "solved"))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
