#!/usr/bin/env python3
"""
A small bedtime story world about a gentle mystery in the kitchen.

Seed tale:
A sleepy child notices that the kitchen smells sweet and tangy at bedtime.
A bowl of tamarind is on the counter, and an omelette is waiting on a plate.
The child thinks something important is missing, follows little clues, and
solves the mystery before going to sleep.

World model:
- physical meters: smell, warmth, hunger, tang, tidiness, mystery, calm
- emotional memes: curiosity, worry, comfort, pride, sleepiness

The story is built from state changes:
- foreshadowing clues raise mystery before the reveal
- the child investigates the kitchen
- a small missing ingredient is found
- the bedtime ending shows the world has become calm and safe
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    eaten: bool = False
    hidden: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Kitchen:
    place: str = "the kitchen"
    bedtime: bool = True
    warm_light: bool = True
    quiet: bool = True
    clues: list[str] = field(default_factory=list)


@dataclass
class StoryParams:
    name: str
    gender: str
    caretaker: str
    seed: Optional[int] = None


REG_NAMES_GIRL = ["Mia", "Luna", "Nora", "Ivy", "Ada", "Mira"]
REG_NAMES_BOY = ["Eli", "Noah", "Theo", "Finn", "Owen", "Leo"]
REG_CARETAKERS = ["mom", "dad", "grandma", "grandpa"]


def _make_world_name(name: str, gender: str, caretaker: str) -> "World":
    return World(Kitchen(), name=name, gender=gender, caretaker=caretaker)


class World:
    def __init__(self, kitchen: Kitchen, name: str, gender: str, caretaker: str) -> None:
        self.kitchen = kitchen
        self.name = name
        self.gender = gender
        self.caretaker = caretaker
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


def pronoun(gender: str, case: str = "subject") -> str:
    return {"girl": {"subject": "she", "object": "her", "possessive": "her"},
            "boy": {"subject": "he", "object": "him", "possessive": "his"}}[gender][case]


def create_world(params: StoryParams) -> World:
    world = _make_world_name(params.name, params.gender, params.caretaker)
    child = world.add(Entity(id="child", kind="character", type=params.gender, label=params.name))
    care = world.add(Entity(id="caregiver", kind="character", type=params.caretaker, label=params.caretaker))
    tamarind = world.add(Entity(
        id="tamarind", type="food", label="tamarind",
        phrase="a small bowl of tamarind",
        owner="caregiver",
        meters={"tang": 1.0, "smell": 1.0, "tidiness": 1.0},
        memes={"mystery": 1.0},
    ))
    omelette = world.add(Entity(
        id="omelette", type="food", label="omelette",
        phrase="a fluffy omelette on a plate",
        owner="caregiver",
        meters={"warmth": 1.0, "smell": 1.0, "tidiness": 1.0, "hunger": 1.0},
        memes={"comfort": 1.0},
    ))
    spoon = world.add(Entity(
        id="spoon", type="tool", label="little spoon",
        phrase="a little spoon",
        owner="child",
        meters={"shine": 1.0},
    ))
    world.facts.update(child=child, care=care, tamarind=tamarind, omelette=omelette, spoon=spoon)
    return world


def foreshadow(world: World) -> None:
    c = world.get("child")
    tam = world.get("tamarind")
    om = world.get("omelette")
    world.say(f"At bedtime, {c.label} wandered into {world.kitchen.place} and paused.")
    world.say("The light was soft, and the room felt quiet enough for a secret.")
    world.say(f"A little bowl of {tam.label} sat nearby, and an {om.label} waited on a plate.")
    c.memes["curiosity"] = c.memes.get("curiosity", 0) + 1
    c.memes["worry"] = c.memes.get("worry", 0) + 1
    c.meters["mystery"] = c.meters.get("mystery", 0) + 1
    world.kitchen.clues.extend(["tamarind bowl", "warm plate", "tiny spoon"])


def investigate(world: World) -> None:
    c = world.get("child")
    tam = world.get("tamarind")
    om = world.get("omelette")
    spoon = world.get("spoon")
    world.para()
    world.say(f"{c.label} looked at the sweet-tangy bowl, then at the warm {om.label}.")
    world.say("Something did not match, and that made the mystery feel bigger.")
    c.memes["curiosity"] += 1
    c.meters["mystery"] += 1
    c.meters["calm"] = c.meters.get("calm", 0)
    if not spoon.hidden:
        world.say(f"A tiny {spoon.label} by the napkin was a clue, like a whisper.")
        world.kitchen.clues.append("spoon")
    world.say("The child sniffed once more and noticed the bowl had been opened already.")


def solve_mystery(world: World) -> None:
    c = world.get("child")
    care = world.get("caregiver")
    tam = world.get("tamarind")
    om = world.get("omelette")
    spoon = world.get("spoon")
    world.para()
    if "spoon" not in world.kitchen.clues:
        raise StoryError("The mystery needs a clue to solve; the spoon clue is missing.")
    world.say(f"Then {c.label} understood: the omelette was waiting for one last bright spoonful of tamarind.")
    world.say(f"{c.label} carried the little spoon to {care.label} and asked for help.")
    world.say(f"Together they stirred in the tamarind, and the omelette became sweet, tangy, and warm.")
    tam.eaten = True
    om.meters["taste"] = om.meters.get("taste", 0) + 1
    om.memes["comfort"] = om.memes.get("comfort", 0) + 1
    c.memes["worry"] = max(0.0, c.memes.get("worry", 0) - 1)
    c.memes["pride"] = c.memes.get("pride", 0) + 1
    c.meters["mystery"] = max(0.0, c.meters.get("mystery", 0) - 1)
    c.meters["calm"] = c.meters.get("calm", 0) + 1
    care.memes["comfort"] = care.memes.get("comfort", 0) + 1
    world.say(f"The room felt cozy again, and {c.label} smiled at the solved little mystery.")


def bedtime_end(world: World) -> None:
    c = world.get("child")
    care = world.get("caregiver")
    world.para()
    world.say(f"After that, {c.label} washed the spoon and yawned.")
    world.say(f"{care.label} tucked {c.label} in, and the kitchen grew still and sleepy.")
    world.say(f"{c.label} drifted off, thinking of the warm omelette and the sweet tamarind clue.")
    c.memes["sleepiness"] = c.memes.get("sleepiness", 0) + 1
    c.memes["comfort"] = c.memes.get("comfort", 0) + 1


def tell_story(params: StoryParams) -> World:
    world = create_world(params)
    foreshadow(world)
    investigate(world)
    solve_mystery(world)
    bedtime_end(world)
    world.facts["solved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    c = world.facts["child"]
    return [
        f"Write a bedtime story about {c.label} solving a tiny kitchen mystery with tamarind and an omelette.",
        "Tell a gentle bedtime story with a clue, a guess, and a cozy solution.",
        "Write a child-friendly mystery story set in a quiet kitchen at bedtime.",
    ]


def story_qa(world: World) -> list[QAItem]:
    c = world.facts["child"]
    care = world.facts["care"]
    return [
        QAItem(
            question=f"Who solved the little mystery in the kitchen?",
            answer=f"{c.label} solved it with help from {care.label}.",
        ),
        QAItem(
            question="What clue helped solve the mystery?",
            answer="A tiny spoon was the clue that showed the omelette needed tamarind.",
        ),
        QAItem(
            question="What happened to the omelette at the end?",
            answer="It became sweet, tangy, and warm after the tamarind was stirred in.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is tamarind?",
            answer="Tamarind is a tangy fruit that can taste sweet and sour at the same time.",
        ),
        QAItem(
            question="What is an omelette?",
            answer="An omelette is a soft egg dish that is cooked in a pan and folded over.",
        ),
        QAItem(
            question="Why do bedtime stories feel calming?",
            answer="Bedtime stories feel calming because they are gentle, quiet, and often end with everything safe again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  clues: {world.kitchen.clues}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("entity", "child"),
        asp.fact("entity", "caregiver"),
        asp.fact("entity", "tamarind"),
        asp.fact("entity", "omelette"),
        asp.fact("entity", "spoon"),
        asp.fact("food", "tamarind"),
        asp.fact("food", "omelette"),
        asp.fact("clue", "spoon"),
        asp.fact("calming_setting", "kitchen"),
        asp.fact("bedtime"),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
% A mystery exists if a bedtime kitchen contains both tamarind and an omelette.
mystery_exists :- entity(child), entity(caregiver), food(tamarind), food(omelette), bedtime, calming_setting(kitchen).

% The spoon clue resolves the mystery because tamarind is the missing bright flavor.
solved_mystery :- mystery_exists, clue(spoon).

% A cozy ending follows when the mystery is solved.
cozy_end :- solved_mystery.
#show mystery_exists/0.
#show solved_mystery/0.
#show cozy_end/0.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show mystery_exists/0. #show solved_mystery/0. #show cozy_end/0."))
    atoms = {str(a) for a in model}
    needed = {"mystery_exists", "solved_mystery", "cozy_end"}
    if needed.issubset(atoms):
        print("OK: ASP twin matches the Python story logic.")
        return 0
    print("MISMATCH: ASP twin did not derive the expected story states.")
    print("Got:", sorted(atoms))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime mystery story world with tamarind and an omelette.")
    ap.add_argument("--name", choices=REG_NAMES_GIRL + REG_NAMES_BOY)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--caretaker", choices=REG_CARETAKERS)
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
    if args.name:
        name = args.name
    else:
        name = rng.choice(REG_NAMES_GIRL if gender == "girl" else REG_NAMES_BOY)
    caretaker = args.caretaker or rng.choice(REG_CARETAKERS)
    return StoryParams(name=name, gender=gender, caretaker=caretaker)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
        print(asp_program("#show mystery_exists/0. #show solved_mystery/0. #show cozy_end/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show mystery_exists/0. #show solved_mystery/0. #show cozy_end/0."))
        print("ASP atoms:", ", ".join(str(a) for a in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        params_list = [
            StoryParams(name="Mia", gender="girl", caretaker="mom"),
            StoryParams(name="Leo", gender="boy", caretaker="dad"),
            StoryParams(name="Nora", gender="girl", caretaker="grandma"),
        ]
        samples = [generate(p) for p in params_list]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
