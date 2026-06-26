#!/usr/bin/env python3
"""
A cautionary slice-of-life storyworld set in a daycare room.

Premise:
A child in a daycare room wants a creamy treat from a small creamery cart, but
the cart's labels are mixed up with gibberish. A caregiver notices the confusion
and helps the child slow down, read carefully, and choose the right cup.

World model:
- Physical meters: spilled, sticky, cold, full, clean
- Emotional memes: curiosity, worry, relief, pride, patience, trust

The story turns on a small, concrete caution: when labels are gibberish, you
should not grab the first cup you see. The solution is social and gentle:
pause, ask for help, and choose carefully.
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


# ---------------------------------------------------------------------------
# Entities and world
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "caregiver"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    child_name: str
    child_gender: str
    caregiver_role: str
    treat: str
    flavor: str
    seed: Optional[int] = None


CHILD_NAMES_GIRL = ["Maya", "Lina", "June", "Nora", "Ava", "Zoe"]
CHILD_NAMES_BOY = ["Owen", "Milo", "Toby", "Eli", "Finn", "Leo"]
FLAVORS = ["vanilla", "strawberry", "banana", "blueberry"]
TREATS = {
    "cup": "a small paper cup of cream",
    "cone": "a tiny cone with a swirl of cream",
    "spooncup": "a little cup with a spoon tucked inside",
}
CAREGIVER_ROLES = ["teacher", "helper", "caregiver"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def pronoun_for_gender(gender: str, case: str = "subject") -> str:
    return {"girl": {"subject": "she", "object": "her", "possessive": "her"},
            "boy": {"subject": "he", "object": "him", "possessive": "his"}}[gender][case]


def pick_child_name(gender: str, rng: random.Random) -> str:
    return rng.choice(CHILD_NAMES_GIRL if gender == "girl" else CHILD_NAMES_BOY)


def clamp_nonnegative(v: float) -> float:
    return 0.0 if v < 0 else v


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    world = World(setting="daycare room")

    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_gender,
        label=params.child_name,
        owner=None,
        meters={"clean": 1.0},
        memes={"curiosity": 1.0, "patience": 0.0, "trust": 0.0},
    ))
    caregiver = world.add(Entity(
        id="caregiver",
        kind="character",
        type=params.caregiver_role,
        label=f"the {params.caregiver_role}",
        meters={},
        memes={"worry": 0.0, "relief": 0.0, "patience": 1.0},
    ))
    treat = world.add(Entity(
        id="treat",
        kind="thing",
        type="treat",
        label="treat",
        phrase=TREATS[params.treat],
        owner=params.child_name,
        caretaker="caregiver",
        meters={"full": 1.0, "cold": 1.0, "sticky": 0.0, "spilled": 0.0},
    ))
    cart = world.add(Entity(
        id="creamery_cart",
        kind="thing",
        type="cart",
        label="creamery cart",
        phrase="a small creamery cart with bright lids",
        meters={"full": 1.0},
    ))
    sign = world.add(Entity(
        id="sign",
        kind="thing",
        type="sign",
        label="sign",
        phrase="a sign with gibberish words",
        meters={"clean": 1.0},
    ))

    # Act 1: gentle setup.
    world.say(
        f"It was a quiet day in the daycare room, and {child.label} noticed the little "
        f"creamery cart by the wall."
    )
    world.say(
        f"{child.label.capitalize()} liked {params.flavor} cream, and the cart promised "
        f"{treat.phrase}."
    )
    world.say(
        f"Beside the cart hung a sign covered in gibberish, with words like "
        f"\"{params.flavor[:2]}-blip\" and \"wum wum\"."
    )

    # Act 2: cautionary turn.
    world.para()
    child.memes["curiosity"] += 1.0
    caregiver.memes["worry"] += 1.0
    world.say(
        f"{child.label.capitalize()} reached for the first cup, but the labels did not make sense."
    )
    world.say(
        f"The {params.caregiver_role} saw the gibberish and said, "
        f"\"Wait a moment. When words look mixed up, we stop and ask.\""
    )
    child.memes["patience"] += 1.0
    child.memes["trust"] += 1.0

    # Small consequence if child rushes.
    treat.meters["spilled"] += 0.0
    if child.memes["curiosity"] > 1.5 and child.memes["patience"] < 1.0:
        treat.meters["spilled"] += 1.0
        treat.meters["sticky"] += 1.0
        caregiver.memes["worry"] += 1.0
    else:
        world.say(
            f"{child.label.capitalize()} held still and listened, so nothing tipped over."
        )

    # Act 3: resolution.
    world.para()
    world.say(
        f"Together they pointed to the picture instead of the gibberish, and the right cup "
        f"came out."
    )
    world.say(
        f"{child.label.capitalize()} took a careful sip of {params.flavor} cream, and the day "
        f"felt calm again."
    )
    caregiver.memes["relief"] += 1.0
    child.memes["patience"] += 1.0
    child.meters["clean"] = 1.0

    world.facts.update(
        child=child,
        caregiver=caregiver,
        treat=treat,
        cart=cart,
        sign=sign,
        params=params,
        flavor=params.flavor,
        room="daycare room",
    )
    return world


# ---------------------------------------------------------------------------
# Narrative generation
# ---------------------------------------------------------------------------
def generate_story(world: World) -> str:
    return world.render()


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a gentle cautionary story for a young child set in a {world.setting}.',
        f'Tell a slice-of-life story about {p.child_name} noticing gibberish on a creamery sign.',
        f'Write a short story where a daycare room, a creamery cart, and careful reading lead to a safe treat.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    child = world.facts["child"]
    caregiver = world.facts["caregiver"]
    treat = world.facts["treat"]
    return [
        QAItem(
            question=f"Where does the story happen?",
            answer="It happens in a daycare room.",
        ),
        QAItem(
            question=f"What did {child.label} notice on the sign?",
            answer="The sign was covered in gibberish words that were hard to read.",
        ),
        QAItem(
            question=f"Why did the {caregiver.type} tell {child.label} to stop for a moment?",
            answer="Because the labels were gibberish, and it was safer to pause and ask before choosing a cup.",
        ),
        QAItem(
            question=f"What treat did {child.label} finally get?",
            answer=f"{child.label} got {treat.phrase} after they chose carefully.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is gibberish?",
            answer="Gibberish is language that sounds like words but does not make sense, so it can be hard to read or understand.",
        ),
        QAItem(
            question="What is a creamery?",
            answer="A creamery is a place where creamy foods like ice cream or soft treats are made and served.",
        ),
        QAItem(
            question="Why should you ask an adult when a label is confusing?",
            answer="An adult can help you read it carefully and choose safely instead of guessing.",
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:12} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is valid when it is set in a daycare room, includes a creamery item,
% and features gibberish that leads to a cautionary pause and a safe choice.
valid_story(room, creamery, gibberish, cautionary).

has_setting(daycare_room).
has_feature(creamery).
has_feature(gibberish).
has_style(slice_of_life).
has_tone(cautionary).

compatible(daycare_room, creamery, gibberish, cautionary, slice_of_life).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "daycare_room"),
        asp.fact("feature", "creamery"),
        asp.fact("feature", "gibberish"),
        asp.fact("tone", "cautionary"),
        asp.fact("style", "slice_of_life"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show compatible/5."))
    atoms = set(asp.atoms(model, "compatible"))
    expected = {("daycare_room", "creamery", "gibberish", "cautionary", "slice_of_life")}
    if atoms == expected:
        print("OK: clingo gate matches the Python reasonableness gate (1 combo).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    print("  clingo:", sorted(atoms))
    print("  python:", sorted(expected))
    return 1


# ---------------------------------------------------------------------------
# Parameter resolution and story generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Cautionary slice-of-life storyworld set in a daycare room."
    )
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--caregiver", choices=CAREGIVER_ROLES)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--flavor", choices=FLAVORS)
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or pick_child_name(gender, rng)
    caregiver = args.caregiver or rng.choice(CAREGIVER_ROLES)
    treat = args.treat or rng.choice(list(TREATS))
    flavor = args.flavor or rng.choice(FLAVORS)
    if args.gender and args.name is None:
        # If the user pins gender, choose a matching familiar name.
        name = pick_child_name(gender, rng)
    return StoryParams(
        child_name=name,
        child_gender=gender,
        caregiver_role=caregiver,
        treat=treat,
        flavor=flavor,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=generate_story(world),
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


CURATED = [
    StoryParams(child_name="Maya", child_gender="girl", caregiver_role="teacher", treat="cup", flavor="vanilla"),
    StoryParams(child_name="Owen", child_gender="boy", caregiver_role="caregiver", treat="cone", flavor="strawberry"),
    StoryParams(child_name="Nora", child_gender="girl", caregiver_role="helper", treat="spooncup", flavor="banana"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show compatible/5."))
        print(sorted(asp.atoms(model, "compatible")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 25):
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
            header = f"### {p.child_name}: daycare room / creamery / gibberish"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
