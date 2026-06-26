#!/usr/bin/env python3
"""
Story world: a folk-tale mystery beside a canal, with a bureau, scoria, and a
small puzzle to solve.

A little tale premise:
- A careful child hears a strange bumping sound near a canal.
- A dusty bureau by the water has a stuck drawer.
- Inside and around the bureau are bits of scoria, which look like dark little
  stones but turn out to be clues.
- The child, a helper, and a patient elder follow the clues, solve the mystery,
  and restore calm.

The world tracks physical meters and emotional memes:
- meters: dust, weight, wetness, hidden, open, clean
- memes: worry, curiosity, relief, pride, kindness

The mystery is resolved when the drawer is opened by using the right clue:
the scoria pieces are found to be tracks from a canal-latch key, leading to the
lost key under the bureau.
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
# Domain registries
# ---------------------------------------------------------------------------

@dataclass
class CharacterProfile:
    kind: str
    name: str
    role: str
    age_word: str
    traits: list[str] = field(default_factory=list)


@dataclass
class PlaceProfile:
    id: str
    label: str
    mood: str
    near_water: bool = False


@dataclass
class ClueProfile:
    id: str
    label: str
    reveals: str
    note: str


@dataclass
class StoryParams:
    hero: str
    helper: str
    elder: str
    place: str
    clue: str
    seed: Optional[int] = None


CHARACTERS = {
    "Mina": CharacterProfile("child", "Mina", "girl", "small", ["curious", "kind"]),
    "Tobin": CharacterProfile("child", "Tobin", "boy", "small", ["careful", "bright"]),
    "Iris": CharacterProfile("elder", "Iris", "grandmother", "old", ["patient", "wise"]),
    "Hollis": CharacterProfile("helper", "Hollis", "neighbor", "grown", ["gentle", "steady"]),
}

PLACES = {
    "canalbank": PlaceProfile("canalbank", "the canal bank", "quiet", near_water=True),
    "lane": PlaceProfile("lane", "the old lane", "dusty", near_water=False),
    "yard": PlaceProfile("yard", "the willow yard", "soft", near_water=False),
}

CLUES = {
    "scoria": ClueProfile(
        "scoria",
        "a little trail of scoria",
        "the bureau drawer had a hidden catch",
        "dark crumbs that clinked like tiny stones",
    ),
    "ribbon": ClueProfile(
        "ribbon",
        "a blue ribbon",
        "the ribbon had been tied to the lost key",
        "a scrap that fluttered near the drawer knob",
    ),
    "shell": ClueProfile(
        "shell",
        "a bright shell",
        "someone had reached down by the canal",
        "a shell left in a wet footprint",
    ),
}

NAME_CHOICES = ["Mina", "Tobin"]
HELPER_CHOICES = ["Hollis"]
ELDER_CHOICES = ["Iris"]
PLACE_CHOICES = ["canalbank", "lane", "yard"]
CLUE_CHOICES = ["scoria", "ribbon", "shell"]

ASP_RULES = r"""
% A story is valid when the clue can point to the bureau mystery.
valid_story(Hero, Helper, Elder, Place, Clue) :-
    child(Hero), helper(Helper), elder(Elder), place(Place), clue(Clue),
    solvable(Place, Clue).
"""

# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str
    label: str
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: {
        "dust": 0.0,
        "weight": 0.0,
        "wetness": 0.0,
        "hidden": 0.0,
        "open": 0.0,
        "clean": 0.0,
    })
    memes: dict[str, float] = field(default_factory=lambda: {
        "worry": 0.0,
        "curiosity": 0.0,
        "relief": 0.0,
        "pride": 0.0,
        "kindness": 0.0,
    })

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "child":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "elder":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    place: PlaceProfile
    hero: Entity
    helper: Entity
    elder: Entity
    bureau: Entity
    clue: ClueProfile
    facts: dict = field(default_factory=dict)
    story_parts: list[str] = field(default_factory=list)
    fired: set[str] = field(default_factory=set)

    def say(self, text: str) -> None:
        self.story_parts.append(text)

    def render(self) -> str:
        return "\n\n".join(self.story_parts)

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale mystery by the canal.")
    ap.add_argument("--hero", choices=sorted(NAME_CHOICES))
    ap.add_argument("--helper", choices=sorted(HELPER_CHOICES))
    ap.add_argument("--elder", choices=sorted(ELDER_CHOICES))
    ap.add_argument("--place", choices=sorted(PLACE_CHOICES))
    ap.add_argument("--clue", choices=sorted(CLUE_CHOICES))
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


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos = []
    for hero in NAME_CHOICES:
        for helper in HELPER_CHOICES:
            for elder in ELDER_CHOICES:
                for place in PLACE_CHOICES:
                    for clue in CLUE_CHOICES:
                        if place == "canalbank":
                            combos.append((hero, helper, elder, place, clue))
                        elif clue in {"scoria", "shell"}:
                            combos.append((hero, helper, elder, place, clue))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    filtered = [
        c for c in combos
        if (args.hero is None or c[0] == args.hero)
        and (args.helper is None or c[1] == args.helper)
        and (args.elder is None or c[2] == args.elder)
        and (args.place is None or c[3] == args.place)
        and (args.clue is None or c[4] == args.clue)
    ]
    if not filtered:
        raise StoryError("No valid folk-tale mystery matches the given options.")
    hero, helper, elder, place, clue = rng.choice(sorted(filtered))
    return StoryParams(hero=hero, helper=helper, elder=elder, place=place, clue=clue)


def _entity_from_profile(name: str, profile: CharacterProfile) -> Entity:
    return Entity(id=name, kind=profile.kind, label=name, role=profile.role)


def build_world(params: StoryParams) -> World:
    hero_p = CHARACTERS[params.hero]
    helper_p = CHARACTERS[params.helper]
    elder_p = CHARACTERS[params.elder]
    place_p = PLACES[params.place]
    clue_p = CLUES[params.clue]

    hero = _entity_from_profile(hero_p.name, hero_p)
    helper = _entity_from_profile(helper_p.name, helper_p)
    elder = _entity_from_profile(elder_p.name, elder_p)

    bureau = Entity(id="bureau", kind="thing", label="a walnut bureau")
    bureau.meters["dust"] = 2.0
    bureau.meters["hidden"] = 1.0

    return World(
        place=place_p,
        hero=hero,
        helper=helper,
        elder=elder,
        bureau=bureau,
        clue=clue_p,
    )


def tell(world: World) -> None:
    hero = world.hero
    helper = world.helper
    elder = world.elder
    place = world.place
    bureau = world.bureau
    clue = world.clue

    world.say(
        f"Once, {hero.label} lived near {place.label}, where the wind sang softly "
        f"over the water and the reeds bent like listeners."
    )
    world.say(
        f"At the edge of the path stood {bureau.label}, an old piece of furniture "
        f"that looked too fine for the muddy bank."
    )
    world.say(
        f"{hero.label} was a curious child, and {hero.pronoun('subject')} noticed "
        f"that {bureau.label} made a little bumping sound each time the canal breeze "
        f"moved the boards."
    )

    world.facts["mystery"] = "stuck drawer"
    world.facts["place"] = place.id
    world.facts["clue"] = clue.id

    hero.memes["curiosity"] += 1.0
    bureau.meters["hidden"] += 1.0

    world.say(
        f"That night, {hero.label} called for {helper.label} and {elder.label}, "
        f"for a mystery had taken root beside the canal."
    )
    world.say(
        f"The next morning, the three of them knelt by the bureau. {clue.note} "
        f"lay near the leg, and {hero.label} brushed it into a tiny pile."
    )

    if clue.id == "scoria":
        bureau.meters["dust"] += 1.0
        hero.memes["worry"] += 0.5
        world.say(
            f"{hero.label} thought the dark crumbs were only dirt at first, but "
            f"{helper.label} said they looked placed there on purpose, like a trail."
        )
        world.say(
            f"{elder.label} nodded and told a folk tale truth: the smallest stone can "
            f"point the way when a bigger thing is stuck."
        )
        world.facts["trail"] = "scoria trail"
        world.facts["solution"] = "hidden catch"
    elif clue.id == "ribbon":
        world.say(
            f"A blue ribbon was knotted tight around the drawer knob, and when "
            f"{hero.label} tugged it, the ribbon slid toward a little latch."
        )
        world.facts["trail"] = "ribbon knot"
        world.facts["solution"] = "lost key"
    else:
        world.say(
            f"A bright shell sat in a wet footprint, and {elder.label} said the "
            f"mystery must have walked from the canal to the bureau."
        )
        world.facts["trail"] = "wet footprint"
        world.facts["solution"] = "water path"

    world.say(
        f"{helper.label} wiped the drawer front clean while {hero.label} listened "
        f"closely for the catch."
    )
    bureau.meters["clean"] += 1.0
    helper.memes["kindness"] += 1.0

    if clue.id == "scoria":
        world.say(
            f"Then {elder.label} pressed one scoria piece against the side seam, and "
            f"the bureau clicked open at last."
        )
        bureau.meters["open"] += 1.0
        hero.memes["relief"] += 1.0
        hero.memes["pride"] += 0.5
        world.say(
            f"Inside was the lost key, tucked in a soft fold of cloth, shining like a "
            f"pale fish under moon water."
        )
        world.say(
            f"The key fit the canal gate, and the gate stopped rattling in the wind. "
            f"{hero.label} smiled, because the noise had not been a monster after all, "
            f"only a lonely latch waiting to be understood."
        )
    elif clue.id == "ribbon":
        world.say(
            f"The ribbon led to a tiny key hidden in the bureau drawer, and the puzzle "
            f"came apart like a knot loosened by patient fingers."
        )
        bureau.meters["open"] += 1.0
        hero.memes["relief"] += 1.0
        hero.memes["pride"] += 0.5
        world.say(
            f"The key opened the little lock at the canal fence, and the waterway grew "
            f"still and safe."
        )
    else:
        world.say(
            f"By following the wet print to a loose board, they found the missing key "
            f"resting in a dry pocket under the bureau."
        )
        bureau.meters["open"] += 1.0
        hero.memes["relief"] += 1.0
        hero.memes["pride"] += 0.5
        world.say(
            f"The key turned once, the drawer opened, and the old noise became a quiet "
            f"memory."
        )

    world.facts["resolved"] = True


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a gentle folk tale about a child who finds a mystery near a canal and solves it with help.",
        f"Tell a short story about {world.hero.label}, {world.helper.label}, and "
        f"{world.elder.label} around {world.place.label} and a bureau.",
        f"Write a children's mystery story that includes scoria, a bureau, and a canal.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question=f"What did {world.hero.label} notice by the canal?",
            answer=(
                f"{world.hero.label} noticed an old bureau making a strange bumping sound, "
                f"which meant something inside or beside it needed help."
            ),
        ),
        QAItem(
            question=f"What were the scoria pieces used for in the story?",
            answer=(
                f"The scoria pieces were clues. They showed {world.elder.label} where to "
                f"press, and that helped open the bureau drawer."
            ),
        ),
        QAItem(
            question="What was found at the end of the mystery?",
            answer=(
                "The lost key was found, and the drawer opened. The canal gate stopped "
                "rattling, so the story ended in peace."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is scoria?",
            answer=(
                "Scoria is a rough, dark volcanic rock with little holes in it. It can "
                "look like crumbs or tiny stones."
            ),
        ),
        QAItem(
            question="What is a bureau?",
            answer=(
                "A bureau is a piece of furniture with drawers, often used for storing "
                "clothes or small things."
            ),
        ),
        QAItem(
            question="What is a canal?",
            answer=(
                "A canal is a long waterway made for boats, moving water, or helping "
                "a place carry water."
            ),
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in [world.hero, world.helper, world.elder, world.bureau]:
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.kind:6}) {' '.join(bits)}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for name in NAME_CHOICES:
        lines.append(asp.fact("child", name))
    for name in HELPER_CHOICES:
        lines.append(asp.fact("helper", name))
    for name in ELDER_CHOICES:
        lines.append(asp.fact("elder", name))
    for place in PLACE_CHOICES:
        lines.append(asp.fact("place", place))
    for clue in CLUE_CHOICES:
        lines.append(asp.fact("clue", clue))
    for place in PLACE_CHOICES:
        if place == "canalbank":
            lines.append(asp.fact("solvable", place, "scoria"))
            lines.append(asp.fact("solvable", place, "ribbon"))
            lines.append(asp.fact("solvable", place, "shell"))
        else:
            lines.append(asp.fact("solvable", place, "scoria"))
            lines.append(asp.fact("solvable", place, "shell"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/5."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    py_set = set(
        (h, he, e, p, c)
        for h, he, e, p, c in valid_combos()
        if c in CLUE_CHOICES and p in PLACE_CHOICES
    )
    if clingo_set == py_set:
        print(f"OK: ASP gate matches Python gate ({len(py_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("only in ASP:", sorted(clingo_set - py_set))
    print("only in Python:", sorted(py_set - clingo_set))
    return 1


def build_story_from_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


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
    StoryParams(hero="Mina", helper="Hollis", elder="Iris", place="canalbank", clue="scoria"),
    StoryParams(hero="Tobin", helper="Hollis", elder="Iris", place="lane", clue="ribbon"),
    StoryParams(hero="Mina", helper="Hollis", elder="Iris", place="yard", clue="shell"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/5."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/5."))
        stories = sorted(set(asp.atoms(model, "valid_story")))
        for row in stories:
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
            seed = base_seed + i
            i += 1
            try:
                params = build_story_from_args(args, random.Random(seed))
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
            header = f"### {p.hero} at {p.place} with {p.clue}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
