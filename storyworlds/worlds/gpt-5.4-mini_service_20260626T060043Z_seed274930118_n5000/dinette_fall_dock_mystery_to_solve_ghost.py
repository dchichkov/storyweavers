#!/usr/bin/env python3
"""
A small standalone storyworld: a dockside ghost mystery about a dinette set,
a fall, and a gentle solving of what happened.

The world is intentionally tiny and constraint-checked: the dock is the only
setting, the mystery centers on a missing/dropped dinette chair, and the ghost
style stays child-facing and concrete.
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
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False
    spooky: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.plural:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the dock"
    detail: str = "wooden planks and a soft mist"


@dataclass
class Mystery:
    title: str
    missing_item: str
    clue_word: str
    cause: str
    solution: str


@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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


SETTINGS = {
    "dock": Setting(place="the dock", detail="a row of pilings, a little lantern, and water slapping the wood"),
}

MYSTERIES = {
    "dinette_fall": Mystery(
        title="The Dinette Fall",
        missing_item="dinette chair",
        clue_word="fall",
        cause="a loose rope tipped the chair overboard",
        solution="the ghost pointed to the rope knot and showed where the chair had slid",
    )
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Zoe", "Ava", "Ella"]
BOY_NAMES = ["Leo", "Finn", "Sam", "Noah", "Eli", "Theo"]
TRAITS = ["curious", "gentle", "brave", "careful", "lively"]


def valid_combos() -> list[tuple[str, str]]:
    return [("dock", "dinette_fall")]


def reasonableness_gate(place: str, mystery: str) -> None:
    if (place, mystery) not in valid_combos():
        raise StoryError("This story only works as a dock mystery about a dinette fall.")


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    mystery = MYSTERIES[params.mystery]
    world = World(setting)

    hero = world.add(Entity(
        id=params.name, kind="character", type=params.gender,
        meters={"curiosity": 0.0}, memes={"worry": 0.0, "hope": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent", kind="character", type=params.parent, label=f"the {params.parent}",
        meters={"patience": 1.0}, memes={"worry": 0.0},
    ))
    ghost = world.add(Entity(
        id="Ghost", kind="character", type="ghost", label="the little ghost",
        spooky=True, meters={"mist": 1.0}, memes={"kindness": 1.0, "mystery": 1.0},
    ))
    table = world.add(Entity(
        id="dinette", type="table", label="dinette set", phrase="a small white dinette set",
        meters={"stable": 1.0},
    ))
    chair = world.add(Entity(
        id="chair", type="chair", label=mystery.missing_item, phrase="one missing dinette chair",
        owner="dinette", meters={"washed_up": 0.0, "found": 0.0}, memes={"lost": 1.0},
    ))
    rope = world.add(Entity(
        id="rope", type="rope", label="rope", phrase="a rope tied to the chair",
        meters={"looseness": 1.0},
    ))

    # Act 1: setup
    world.say(
        f"{hero.id} was a little {params.gender} who loved quiet places and noticed every small thing."
    )
    world.say(
        f"At {setting.place}, {hero.id} saw {table.phrase} and one missing chair."
    )
    world.say(
        f"The water below shimmered, and the whole dock felt like it was waiting to tell a secret."
    )
    world.para()

    # Act 2: mystery and tension
    hero.meters["curiosity"] += 1
    hero.memes["worry"] += 1
    parent.memes["worry"] += 1
    world.say(
        f"{hero.id} wanted to solve the mystery, but {hero.pronoun('possessive')} heart thumped with worry."
    )
    world.say(
        f"Then a little ghost drifted out from behind the lantern, as pale as fog and as soft as a whisper."
    )
    world.say(
        f'"Something fell," the ghost said. "The chair did not vanish. It went down."'
    )
    world.say(
        f"{hero.id} looked at the ropes and the wet boards and saw a place where something had slid."
    )

    # fall event as physical state
    chair.meters["found"] += 1
    chair.memes["lost"] = 0.0
    rope.meters["looseness"] = 0.0
    ghost.memes["mystery"] += 1
    world.facts["cause"] = mystery.cause
    world.facts["solution"] = mystery.solution
    world.facts["chair"] = chair
    world.facts["hero"] = hero
    world.facts["parent"] = parent
    world.facts["ghost"] = ghost
    world.facts["mystery"] = mystery

    world.para()

    # Act 3: solving
    world.say(
        f"The ghost pointed to a loose knot near the edge and to a scrape on the boards."
    )
    world.say(
        f"That made the answer clear: {mystery.cause}."
    )
    hero.memes["hope"] += 1
    parent.memes["worry"] = 0.0
    hero.meters["curiosity"] += 1
    chair.meters["washed_up"] = 1.0
    world.say(
        f"{hero.id} and {parent.label} pulled the chair back, and {hero.id} tied the rope tight again."
    )
    world.say(
        f"The little ghost smiled, faded into the mist, and left the dock peaceful."
    )
    world.say(
        f"By the end, the dinette set stood steady again, and the mystery had been solved."
    )

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mystery = f["mystery"]
    return [
        f"Write a gentle ghost story set on a dock about {hero.id} solving the {mystery.title.lower()}.",
        f"Tell a child-friendly mystery story with a fall, a dinette set, and a little ghost who helps explain what happened.",
        f"Write a short spooky-but-kind story where a child finds out why one dinette chair fell near the dock.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    ghost = f["ghost"]
    mystery = f["mystery"]
    chair = f["chair"]
    return [
        QAItem(
            question=f"Where did {hero.id} solve the mystery?",
            answer=f"{hero.id} solved the mystery on the dock, beside the water and the lantern.",
        ),
        QAItem(
            question=f"What was missing from the dinette set?",
            answer=f"The missing piece was the {chair.label}, one little chair from the dinette set.",
        ),
        QAItem(
            question=f"Who helped point to the answer?",
            answer=f"The little ghost helped by showing the loose knot and the scrape on the boards.",
        ),
        QAItem(
            question=f"Why had the chair fallen?",
            answer=f"It had fallen because {mystery.cause}.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the chair was back, the rope was tied tight, and everyone felt calmer.",
        ),
        QAItem(
            question=f"How did {hero.id} feel after the mystery was solved?",
            answer=f"{hero.id} felt more hopeful and brave after the answer was found.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a dock?",
            answer="A dock is a wooden place near water where boats can stop and people can stand or walk.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a question about something that happened, and people look for clues to solve it.",
        ),
        QAItem(
            question="What is a ghost in a story?",
            answer="A ghost in a story is a spooky-looking character, and it can be kind or helpful.",
        ),
        QAItem(
            question="What is a dinette set?",
            answer="A dinette set is a small table with chairs, often used for eating or sitting together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.spooky:
            bits.append("spooky=True")
        out.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(out)


ASP_RULES = r"""
valid_story(dock,dinette_fall).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([asp.fact("place", "dock"), asp.fact("mystery", "dinette_fall")])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    py_set = set(valid_combos())
    if clingo_set == py_set:
        print("OK: clingo gate matches valid_combos() (1 combo).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  clingo:", sorted(clingo_set))
    print("  python:", sorted(py_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A dockside ghost mystery with a dinette fall.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--mystery", choices=MYSTERIES.keys())
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    place = args.place or "dock"
    mystery = args.mystery or "dinette_fall"
    reasonableness_gate(place, mystery)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, mystery=mystery, name=name, gender=gender, parent=parent)


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(combos)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        params = StoryParams(place="dock", mystery="dinette_fall", name="Mia", gender="girl", parent="mother")
        samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
