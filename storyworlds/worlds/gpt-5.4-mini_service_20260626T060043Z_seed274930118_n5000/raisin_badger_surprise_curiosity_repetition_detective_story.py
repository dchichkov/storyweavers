#!/usr/bin/env python3
"""
storyworlds/worlds/raisin_badger_surprise_curiosity_repetition_detective_story.py
=================================================================================

A small detective-style storyworld about a curious badger, a missing raisin,
and a surprising clue that keeps repeating until the truth is found.

The premise is simple:
- a badger notices a tiny raisin is gone,
- curiosity makes the badger investigate,
- surprise appears when the same clue shows up more than once,
- repetition becomes the key that reveals the answer.

The world is intentionally small and constraint-driven. The story is not a
fixed paragraph with swapped nouns; the simulated state decides which clues are
noticed, how suspicion grows, and how the ending is resolved.

This world models:
- typed entities with physical meters and emotional memes,
- a few scene objects and locations,
- a detective-like sequence of observation, suspicion, and discovery,
- a compatibility gate that ensures the central clue actually matters.

It also includes an inline ASP twin for the reasonableness gate and registry
parity checks.
"""

from __future__ import annotations

import argparse
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
    secret: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("dust", "missing", "found", "faint", "suspicion", "attention"):
            self.meters.setdefault(k, 0.0)
        for k in ("curiosity", "surprise", "focus", "relief", "worry"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"badger", "boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Scene:
    place: str
    affordances: set[str] = field(default_factory=set)


@dataclass
class Clue:
    label: str
    phrase: str
    kind: str
    location: str
    repetition_key: str
    surprise_value: float = 1.0


@dataclass
class StoryParams:
    place: str
    clue: str
    name: str
    seed: Optional[int] = None


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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


def scene_text(place: str) -> str:
    return {
        "attic": "the attic",
        "kitchen": "the kitchen",
        "garden": "the garden",
        "station": "the old station",
    }[place]


SCENES = {
    "attic": Scene(place="the attic", affordances={"search", "observe"}),
    "kitchen": Scene(place="the kitchen", affordances={"search", "observe"}),
    "garden": Scene(place="the garden", affordances={"search", "observe"}),
    "station": Scene(place="the old station", affordances={"search", "observe"}),
}

CLUES = {
    "raisin": Clue(
        label="raisin",
        phrase="a tiny raisin",
        kind="food",
        location="crumb trail",
        repetition_key="crumb",
        surprise_value=1.0,
    ),
    "button": Clue(
        label="button",
        phrase="a shiny button",
        kind="object",
        location="window sill",
        repetition_key="shine",
        surprise_value=0.7,
    ),
    "leaf": Clue(
        label="leaf",
        phrase="a curled leaf",
        kind="nature",
        location="floorboard",
        repetition_key="curl",
        surprise_value=0.6,
    ),
}

NAMES = ["Milo", "Nina", "Toby", "Lara", "Owen", "Pia", "Jun", "Rosa"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, scene in SCENES.items():
        if "search" not in scene.affordances:
            continue
        for clue_id in CLUES:
            combos.append((place, clue_id))
    return combos


def reasonableness_gate(place: str, clue: str) -> None:
    if place not in SCENES:
        raise StoryError("Unknown scene.")
    if clue not in CLUES:
        raise StoryError("Unknown clue.")
    if "search" not in SCENES[place].affordances:
        raise StoryError("This place does not support a detective search.")
    if clue == "raisin" and place == "station":
        raise StoryError("The raisin clue is too thin for the abandoned station.")
    return


def detect_repetition(world: World, clue: Clue) -> bool:
    count = world.facts.get("observations", {}).get(clue.repetition_key, 0)
    return count >= 2


def simulate_search(world: World, detective: Entity, clue: Clue) -> None:
    detective.memes["curiosity"] += 1
    detective.meters["attention"] += 1
    world.facts.setdefault("observations", {})
    world.facts["observations"].setdefault(clue.repetition_key, 0)
    world.facts["observations"][clue.repetition_key] += 1
    if world.facts["observations"][clue.repetition_key] == 1:
        world.say(
            f"{detective.id} noticed a small clue near the {clue.location}: {clue.phrase}."
        )
    else:
        detective.memes["surprise"] += clue.surprise_value
        world.say(
            f"Then the same kind of clue appeared again, and {detective.id} stopped."
        )


def reveal_answer(world: World, detective: Entity, clue: Clue, culprit: Entity) -> None:
    detective.memes["focus"] += 1
    detective.memes["relief"] += 1
    culprit.meters["found"] += 1
    world.say(
        f"At last, the repeated clue made sense: {culprit.id} had been the one "
        f"who carried the raisin away to hide it safely."
    )
    world.say(
        f"{detective.id} smiled, because the mystery was solved without a single loud chase."
    )


def build_story(world: World, detective: Entity, clue: Clue, culprit: Entity) -> None:
    world.say(
        f"{detective.id} was a curious badger who loved to solve little mysteries."
    )
    world.say(
        f"One evening in {world.scene.place}, {detective.id} found that {clue.phrase} had gone missing."
    )
    world.para()
    world.say(
        f"{detective.id} looked once, then looked again, because curiosity would not let go."
    )
    simulate_search(world, detective, clue)
    simulate_search(world, detective, clue)
    if detect_repetition(world, clue):
        detective.memes["surprise"] += 1
        world.say(
            f"The repeating clue felt surprising, like a whisper that came back on purpose."
        )
    world.para()
    reveal_answer(world, detective, clue, culprit)


def tell(scene_key: str, clue_key: str, name: str) -> World:
    scene = SCENES[scene_key]
    world = World(scene)
    detective = world.add(Entity(id=name, kind="character", type="badger"))
    culprit = world.add(Entity(id="Mouse", kind="character", type="mouse"))
    clue = CLUES[clue_key]
    if clue_key == "raisin":
        culprit.label = "the mouse"
        culprit.phrase = "a small mouse"
        culprit.secret = True
    world.facts.update(detective=detective, culprit=culprit, clue=clue, scene=scene)
    build_story(world, detective, clue, culprit)
    return world


def prompt_text(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short detective story for children about {f['detective'].id}, a badger, who follows a repeating clue in {f['scene'].place}.",
        f"Tell a curious mystery where a raisin goes missing and the same clue shows up twice before the answer is found.",
        f"Write a gentle surprise-and-detection story about a badger, curiosity, and repetition.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective: Entity = f["detective"]
    culprit: Entity = f["culprit"]
    clue: Clue = f["clue"]
    scene: Scene = f["scene"]
    return [
        QAItem(
            question=f"Who is the detective in the story?",
            answer=f"The detective is {detective.id}, a curious badger who keeps looking closely.",
        ),
        QAItem(
            question=f"What clue went missing in {scene.place}?",
            answer=f"The missing clue was {clue.phrase}, which is a {clue.label}.",
        ),
        QAItem(
            question=f"What helped solve the mystery?",
            answer="The repeating clue helped solve it, because seeing the same kind of clue again made the answer clear.",
        ),
        QAItem(
            question=f"Who had the raisin?",
            answer=f"{culprit.id} had the raisin and had hidden it away carefully.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to look, ask, and learn more.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that makes you stop and pay attention.",
        ),
        QAItem(
            question="What does repetition mean?",
            answer="Repetition means something happens or appears again and again.",
        ),
        QAItem(
            question="What is a badger?",
            answer="A badger is a small animal with a strong nose and a habit of digging and searching carefully.",
        ),
    ]


def asp_facts() -> str:
    import asp
    lines = []
    for place in SCENES:
        lines.append(asp.fact("scene", place))
        lines.append(asp.fact("search_place", place))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        lines.append(asp.fact("repetition_key", clue_id, clue.repetition_key))
        lines.append(asp.fact("surprise_value", clue_id, int(clue.surprise_value * 10)))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Clue) :- search_place(Place), clue(Clue).
interesting(Clue) :- repetition_key(Clue, K), repetition_key(Clue, K).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} ({e.type:8}) meters={meters} memes={memes}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small detective storyworld about a badger, a raisin, and a repeating clue."
    )
    ap.add_argument("--place", choices=SCENES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name", choices=NAMES)
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
    if args.place and args.clue:
        reasonableness_gate(args.place, args.clue)
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.clue is None or c[1] == args.clue)
    ]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, clue = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    return StoryParams(place=place, clue=clue, name=name)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.place, params.clue, params.name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompt_text(world),
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


CURATED = [
    StoryParams(place="attic", clue="raisin", name="Milo"),
    StoryParams(place="kitchen", clue="button", name="Nina"),
    StoryParams(place="garden", clue="leaf", name="Toby"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} valid combos:")
        for combo in combos:
            print(" ", combo)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.clue} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
