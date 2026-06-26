#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/thousand_cautionary_transformation_bedtime_story.py
===================================================================================================

A small bedtime story world about a child, a glowing thousand, and a gentle
warning that leads to a cozy transformation.

Premise used to build the world:
---
A child loves one magical thing very much: a little jar of one thousand tiny
glow-stones. The glow-stones are lovely at bedtime, but if the child keeps them
all bright too long, the room becomes too lively and the child cannot rest. A
caregiver warns about the tired eyes and the restless room. The child first
reaches for more glow, then accepts a soft compromise: dim the jar, tuck the
glow-stones into a blanket pocket, and let the room change from bright and
busy into calm and sleepy.

World model:
---
- meters track light, tiredness, tidiness, and coziness
- memes track worry, delight, defiance, and relief
- the thousand glow-stones are a physical object with a count
- the story turns when the child transforms the room and the glow-stones from
  bright play into bedtime calm

This script keeps the tone child-facing, concrete, and bedtime-gentle.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the bedtime room"
    warm: bool = True
    quiet: bool = True


@dataclass
class Treasure:
    label: str
    phrase: str
    sparkle: str
    count: int
    calm_use: str


@dataclass
class StoryParams:
    name: str
    gender: str
    caregiver: str
    treasure: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.phase: str = "begin"

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.phase = self.phase
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _light_bright(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    jar = world.get("jar")
    if child.memes.get("delight", 0.0) < THRESHOLD:
        return out
    sig = ("bright",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    jar.meters["light"] = 2.0
    world.get("room").meters["light"] = 2.0
    out.append("The tiny glow-stones shone bright enough to make the pillows look awake.")
    return out


def _restless_room(world: World) -> list[str]:
    child = world.get("child")
    room = world.get("room")
    if room.meters.get("light", 0.0) < 2.0:
        return []
    if child.memes.get("worry", 0.0) < THRESHOLD:
        return []
    sig = ("restless",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.meters["tired"] = max(child.meters.get("tired", 0.0), 1.0)
    child.memes["restless"] = 1.0
    return ["The bright room made the child feel too wakeful for sleep."]


def _calm_down(world: World) -> list[str]:
    child = world.get("child")
    jar = world.get("jar")
    blanket = world.get("blanket")
    if child.memes.get("relief", 0.0) < THRESHOLD:
        return []
    sig = ("calm",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    jar.meters["light"] = 0.5
    blanket.meters["warmth"] = 1.0
    world.get("room").meters["light"] = 0.5
    world.get("room").meters["coziness"] = 2.0
    child.memes["restless"] = 0.0
    return ["The glowing jar softened, and the room grew cozy and quiet."]


RULES = [
    _light_bright,
    _restless_room,
    _calm_down,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_restlessness(world: World) -> bool:
    sim = world.copy()
    sim.get("child").memes["delight"] = 1.0
    propagate(sim, narrate=False)
    return sim.get("child").memes.get("restless", 0.0) >= THRESHOLD


def build_world(params: StoryParams) -> World:
    world = World(Setting())
    child = world.add(Entity(id="child", kind="character", type=params.gender, label=params.name))
    caregiver = world.add(Entity(
        id="caregiver",
        kind="character",
        type=params.caregiver,
        label={"mother": "mom", "father": "dad"}.get(params.caregiver, "grown-up"),
    ))
    room = world.add(Entity(id="room", label="the room", meters={"light": 0.0, "coziness": 0.0}))
    jar = world.add(Entity(
        id="jar",
        type="jar",
        label="glow-jar",
        phrase="a little glass jar",
        owner=child.id,
        caretaker=caregiver.id,
        meters={"light": 0.0},
    ))
    blanket = world.add(Entity(
        id="blanket",
        type="blanket",
        label="blanket pocket",
        phrase="a soft blanket pocket",
        owner=child.id,
        caretaker=caregiver.id,
        meters={"warmth": 0.0},
    ))

    treasure = TREASURES[params.treasure]
    world.facts.update(child=child, caregiver=caregiver, room=room, jar=jar, blanket=blanket, treasure=treasure)

    child.memes["delight"] = 1.0
    child.meters["tired"] = 0.0
    world.say(f"{child.label} was a sleepy little {params.gender} who loved {treasure.phrase}.")
    world.say(
        f"Each night, {child.pronoun('subject')} counted the {treasure.count} glow-stones "
        f"and watched them twinkle like tiny bedtime stars."
    )

    world.para()
    world.say(f"At bedtime, {params.caregiver} led {child.pronoun('object')} to the room and turned down the lamp.")
    world.say(
        f"{child.label} wanted the glow-stones bright and sparkly, because the shimmer felt like a secret game."
    )

    if predict_restlessness(world):
        world.say(
            f'"If they stay that bright," {caregiver.label} said, "your eyes will grow tired, and the room will not get sleepy with you."'
        )

    child.memes["worry"] = 1.0
    child.memes["defiance"] = 1.0
    world.say(f"{child.label} held the jar close and reached for one more twinkle.")
    world.say(f"{child.pronoun('subject').capitalize()} tried to keep the whole thousand of them shining at once.")
    propagate(world, narrate=True)

    world.para()
    child.memes["relief"] = 1.0
    world.say(
        f"Then {params.caregiver} opened the blanket pocket and showed {child.pronoun('object')} a gentler way."
    )
    world.say(
        f'Together they tucked the glow-stones in, and the bright little lights changed into a soft, sleepy glow.'
    )
    propagate(world, narrate=True)

    child.memes["joy"] = 1.0
    child.meters["tired"] = 1.0
    world.say(
        f"{child.label} yawned, hugged the blanket, and watched the thousand glow-stones become a quiet lantern for dreams."
    )
    world.say(f"The room stayed warm, the jar stayed safe, and bedtime finally felt bigger than the sparkle.")
    return world


TREASURES = {
    "glow-stones": Treasure(
        label="glow-stones",
        phrase="one thousand tiny glow-stones",
        sparkle="bright",
        count=1000,
        calm_use="a soft lantern for dreams",
    ),
    "paper-stars": Treasure(
        label="paper-stars",
        phrase="one thousand folded paper stars",
        sparkle="shimmery",
        count=1000,
        calm_use="a bedtime garland",
    ),
    "shell-beads": Treasure(
        label="shell-beads",
        phrase="one thousand little shell beads",
        sparkle="pearly",
        count=1000,
        calm_use="a quiet treasure string",
    ),
}

GIRL_NAMES = ["Lily", "Mina", "Ivy", "Nora", "Maya", "Ella"]
BOY_NAMES = ["Theo", "Finn", "Leo", "Owen", "Ben", "Sam"]


def valid_combos() -> list[tuple[str, str]]:
    return [("bedtime room", t) for t in TREASURES]


@dataclass
class _AspStub:
    pass


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    treasure = f["treasure"]
    caregiver = f["caregiver"]
    return [
        f'Write a gentle bedtime story for a young child that includes the word "thousand" and a soft warning about {treasure.phrase}.',
        f"Tell a cozy story where {child.label} wants to keep {treasure.phrase} glowing, but {caregiver.label} knows bedtime should stay calm.",
        f"Write a bedtime story about a little one who learns to turn bright play into a sleepy transformation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    caregiver = f["caregiver"]
    treasure = f["treasure"]
    qa = [
        QAItem(
            question=f"What did {child.label} love at bedtime?",
            answer=f"{child.label} loved {treasure.phrase} and watched the thousand little pieces shine before sleep.",
        ),
        QAItem(
            question=f"Why did {caregiver.label} warn {child.label} about the glow-stones?",
            answer=(
                f"{caregiver.label} warned {child.label} because if the glow-stones stayed too bright, the room would feel wakeful "
                f"and {child.label} would have trouble resting."
            ),
        ),
        QAItem(
            question="What changed at the end of the story?",
            answer=(
                f"The bright, lively glow turned soft and sleepy, and the room became cozy enough for bedtime."
            ),
        ),
        QAItem(
            question=f"How did {child.label} use the blanket pocket?",
            answer=(
                f"{child.label} tucked the glow-stones into the blanket pocket so the lights could rest instead of shining too hard."
            ),
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    treasure = f["treasure"]
    return [
        QAItem(
            question="Why do bedtime routines help children fall asleep?",
            answer="Bedtime routines help because they make the night feel safe, calm, and familiar, which tells the body it is time to rest.",
        ),
        QAItem(
            question="What does it mean to soften a light?",
            answer="To soften a light means to make it dimmer and gentler, so it does not feel sharp or too bright.",
        ),
        QAItem(
            question=f"What is a good calm use for {treasure.label}?",
            answer=f"A good calm use for {treasure.label} is {treasure.calm_use}.",
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cozy bedtime story world about a thousand tiny lights.")
    ap.add_argument("--name", choices=GIRL_NAMES + BOY_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--caregiver", choices=["mother", "father"])
    ap.add_argument("--treasure", choices=TREASURES)
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
    gender = args.gender or rng.choice(["girl", "boy"])
    caregiver = args.caregiver or rng.choice(["mother", "father"])
    treasure = args.treasure or rng.choice(list(TREASURES))
    if args.name:
        name = args.name
    else:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(name=name, gender=gender, caregiver=caregiver, treasure=treasure)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


ASP_RULES = r"""
% A treasure is bedtime-safe when it can become a soft calm object.
safe(treasure) :- treasure(treasure).

% The thousand belongs to the bedtime room stories.
setting_ok(bedtime_room) :- room(bedtime_room).

% A valid story is one where the child and caregiver can transform brightness
% into calm without losing the treasure.
valid_story(bedtime_room, treasure) :- setting_ok(bedtime_room), safe(treasure).

#show valid_story/2.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [asp.fact("room", "bedtime_room")]
    for tid in TREASURES:
        lines.append(asp.fact("treasure", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - asp_set:
        print("  only in python:", sorted(python_set - asp_set))
    if asp_set - python_set:
        print("  only in clingo:", sorted(asp_set - python_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for item in combos:
            print(" ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(StoryParams(name="Lily", gender="girl", caregiver="mother", treasure=t, seed=0)) for t in TREASURES]
    else:
        seen: set[str] = set()
        i = 0
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
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.treasure}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
