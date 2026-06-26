#!/usr/bin/env python3
"""
Tall-tale storyworld: Mickey, the amenity, and Mhiabbi.

A small classical simulation with:
- physical meters and emotional memes
- inner monologue
- magic
- dialogue
- one turning problem and one turn toward a solution
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
# Data model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    label: str = ""
    phrase: str = ""
    type: str = "thing"
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "man", "uncle", "cowboy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "aunt", "cowgirl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def ref(self) -> str:
        return self.label or self.id


@dataclass
class StoryParams:
    place: str
    mickey_kind: str
    amenity_kind: str
    mhiabbi_kind: str
    seed: Optional[int] = None


@dataclass
class Setting:
    name: str
    sky: str
    place_line: str
    wonder: str


@dataclass
class MickeySpec:
    type: str
    name: str
    trait: str
    wish: str
    action: str
    risk: str
    inner_line: str


@dataclass
class AmenitySpec:
    label: str
    phrase: str
    magic_needed: int
    magic_name: str
    protects_from: str
    story_role: str


@dataclass
class MhiabbiSpec:
    label: str
    phrase: str
    type: str
    aid_line: str
    dialogue_line: str
    magic_line: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
SETTINGS = {
    "prairie": Setting(
        name="the prairie",
        sky="blue as a wash tub",
        place_line="The prairie rolled on like a bright quilt under a giant blue sky.",
        wonder="wide grass and old wagon ruts",
    ),
    "harbor": Setting(
        name="the harbor",
        sky="silver as a fish scale",
        place_line="The harbor glittered with ropes, gulls, and water that winked at the sun.",
        wonder="salt wind and bobbing boats",
    ),
    "fair": Setting(
        name="the county fair",
        sky="yellow as butter",
        place_line="The fair was loud with fiddles, banners, and the smell of caramel apples.",
        wonder="music, dust, and spinning lights",
    ),
}

MICKEYS = {
    "cowpoke": MickeySpec(
        type="cowboy",
        name="Mickey",
        trait="stouthearted",
        wish="sing to the whole horizon",
        action="ride the line between dust and dawn",
        risk="his boots would fill with mud",
        inner_line="Mickey thought, 'A tall day calls for a taller step.'",
    ),
    "riverhand": MickeySpec(
        type="man",
        name="Mickey",
        trait="lively",
        wish="dance with the wind off the water",
        action="skip along the dock planks",
        risk="his socks would get soggy",
        inner_line="Mickey thought, 'The river is a big mirror, and I want it to grin back.'",
    ),
    "ringmaster": MickeySpec(
        type="boy",
        name="Mickey",
        trait="bright-eyed",
        wish="make the crowd laugh like thunder",
        action="clap on the highest beam",
        risk="his sleeves would pick up glitter and dust",
        inner_line="Mickey thought, 'If I stand still, the whole fair might hear my heart.'",
    ),
}

AMENITIES = {
    "well": AmenitySpec(
        label="the old wishing well",
        phrase="an old wishing well with a silver chain",
        magic_needed=1,
        magic_name="a drop of moon-water",
        protects_from="dust",
        story_role="cooling stop",
    ),
    "lantern": AmenitySpec(
        label="the lantern porch",
        phrase="a lantern porch with a creaky bench",
        magic_needed=1,
        magic_name="a spark in a glass jar",
        protects_from="dark",
        story_role="warm stop",
    ),
    "fountain": AmenitySpec(
        label="the singing fountain",
        phrase="a singing fountain with a marble lip",
        magic_needed=2,
        magic_name="a penny of courage",
        protects_from="thirst",
        story_role="rest stop",
    ),
}

MHIABBIS = {
    "sparrow": MhiabbiSpec(
        label="Mhiabbi",
        phrase="a tiny helper with star-bright eyes",
        type="sprite",
        aid_line="Mhiabbi flitted in and tucked a spell into Mickey's pocket.",
        dialogue_line='Mhiabbi said, "A tall tale grows tallest when the heart keeps time."',
        magic_line="Mhiabbi's wings turned the air into a humming ladder of light.",
    ),
    "goat": MhiabbiSpec(
        label="Mhiabbi",
        phrase="a shaggy helper with a beard like a broom",
        type="goat",
        aid_line="Mhiabbi stomped once, and the ground answered like a drum.",
        dialogue_line='Mhiabbi said, "If the trail is crooked, we can still sing it straight."',
        magic_line="Mhiabbi's horn gave off a glow like lantern smoke at supper time.",
    ),
    "cat": MhiabbiSpec(
        label="Mhiabbi",
        phrase="a sly helper with a tail curled like a question mark",
        type="cat",
        aid_line="Mhiabbi brushed against Mickey's sleeve and left a ribbon of sparks.",
        dialogue_line='Mhiabbi said, "Every knot has a story. Every story has a knot."',
        magic_line="Mhiabbi's purr turned worry into a soft, round pebble.",
    ),
}

NAMES = ["Mickey"]
TRAITS = ["stouthearted", "lively", "bright-eyed", "merry", "sun-brave"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def make_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)
    mickey_spec = MICKEYS[params.mickey_kind]
    amenity_spec = AMENITIES[params.amenity_kind]
    mhiabbi_spec = MHIABBIS[params.mhiabbi_kind]

    mickey = world.add(Entity(
        id="mickey",
        kind="character",
        type=mickey_spec.type,
        label=mickey_spec.name,
        phrase=f"{mickey_spec.trait} Mickey",
        meters={"dust": 0.0, "magic": 0.0, "travel": 0.0},
        memes={"hope": 1.0, "worry": 0.0, "joy": 0.0, "resolve": 0.0},
    ))
    amenity = world.add(Entity(
        id="amenity",
        kind="thing",
        type="amenity",
        label=amenity_spec.label,
        phrase=amenity_spec.phrase,
        meters={"magic": 0.0, "shine": 1.0},
    ))
    mhiabbi = world.add(Entity(
        id="mhiabbi",
        kind="character",
        type=mhiabbi_spec.type,
        label=mhiabbi_spec.label,
        phrase=mhiabbi_spec.phrase,
        meters={"magic": 1.0},
        memes={"mischief": 1.0, "kindness": 1.0},
    ))

    world.facts.update(
        mickey=mickey,
        amenity=amenity,
        mhiabbi=mhiabbi,
        mickey_spec=mickey_spec,
        amenity_spec=amenity_spec,
        mhiabbi_spec=mhiabbi_spec,
        setting=setting,
    )
    return world


def opening(world: World) -> None:
    ms: MickeySpec = world.facts["mickey_spec"]
    setting: Setting = world.facts["setting"]
    world.say(
        f"Mickey was a {ms.trait} fellow who lived for a tall horizon and a brave idea."
    )
    world.say(
        f"He longed to {ms.wish}, though he knew the road could be a scrappy one."
    )
    world.para()
    world.say(setting.place_line)
    world.say(f"And in that wide place stood {world.facts['amenity'].phrase}, waiting like a small promise.")


def tension(world: World) -> None:
    ms: MickeySpec = world.facts["mickey_spec"]
    am: AmenitySpec = world.facts["amenity_spec"]
    mickey: Entity = world.facts["mickey"]
    mickey.memes["worry"] += 1.0
    world.say(ms.inner_line)
    world.say(
        f"But Mickey peered at {world.facts['amenity'].label} and frowned, because {ms.risk} if he hurried on."
    )
    world.say(
        f"He thought the {am.story_role} might be the very thing he needed, if only it would wake up."
    )


def magic_event(world: World) -> None:
    mickey: Entity = world.facts["mickey"]
    amenity: Entity = world.facts["amenity"]
    ms: MickeySpec = world.facts["mickey_spec"]
    am: AmenitySpec = world.facts["amenity_spec"]
    mh: MhiabbiSpec = world.facts["mhiabbi_spec"]

    world.para()
    world.say(mh.aid_line)
    world.say(mh.dialogue_line)
    world.say(mh.magic_line)

    mickey.meters["magic"] += 1.0
    amenity.meters["magic"] += am.magic_needed
    mickey.memes["resolve"] += 1.0
    mickey.memes["joy"] += 1.0

    world.say(
        f"Mickey answered, 'Then let's make a little thunder of our own,' and he reached for the spell."
    )
    world.say(
        f"With that, the {am.label} gave a bright shiver, and {am.magic_name} flashed through the air."
    )


def dialogue_turn(world: World) -> None:
    ms: MickeySpec = world.facts["mickey_spec"]
    am: AmenitySpec = world.facts["amenity_spec"]
    mh: MhiabbiSpec = world.facts["mhiabbi_spec"]
    mickey: Entity = world.facts["mickey"]

    world.para()
    world.say(f'Mickey said, "{ms.wish.capitalize()}, but I will not let a little trouble out-talk me."')
    world.say(mh.dialogue_line)
    world.say(
        f'Mickey laughed and said, "Ain\'t that the truth? A tired trail gets lighter when you name it out loud."'
    )
    world.say(
        f"Together they chose {am.label}, where the magic could gather under the {am.protects_from or 'open'} sky."
    )


def resolution(world: World) -> None:
    ms: MickeySpec = world.facts["mickey_spec"]
    am: AmenitySpec = world.facts["amenity_spec"]
    mh: MhiabbiSpec = world.facts["mhiabbi_spec"]
    mickey: Entity = world.facts["mickey"]
    amenity: Entity = world.facts["amenity"]

    mickey.meters["travel"] += 1.0
    mickey.memes["worry"] = 0.0
    world.say(
        f"At last Mickey did what he had wanted all along: he set out to {ms.action}, and the road felt grand instead of grim."
    )
    world.say(
        f"The {am.label} glowed behind him, and {mh.label} stayed at his shoulder like a small, loyal star."
    )
    world.say(
        f"By sundown, Mickey had a pocket full of wonder, a heart full of song, and not a speck of trouble where he could not laugh at it."
    )
    world.say(
        f"He looked back once and said, 'Well, if that wasn't a tall tale, I don't know a fence post from a sunrise.'"
    )


def tell_story(world: World) -> None:
    opening(world)
    tension(world)
    magic_event(world)
    dialogue_turn(world)
    resolution(world)


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    ms: MickeySpec = world.facts["mickey_spec"]
    am: AmenitySpec = world.facts["amenity_spec"]
    mh: MhiabbiSpec = world.facts["mhiabbi_spec"]
    setting: Setting = world.facts["setting"]
    return [
        f"Write a tall tale about Mickey, {am.label}, and {mh.label} in {setting.name}.",
        f"Tell a child-friendly story where Mickey wants to {ms.wish}, but needs magic and a helpful amenity.",
        f"Write a short story with inner monologue, dialogue, and magic set at {setting.name}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    ms: MickeySpec = world.facts["mickey_spec"]
    am: AmenitySpec = world.facts["amenity_spec"]
    mh: MhiabbiSpec = world.facts["mhiabbi_spec"]
    setting: Setting = world.facts["setting"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"The story is about Mickey, a {ms.trait} hero who faces a big day in {setting.name}.",
        ),
        QAItem(
            question="What did Mickey want to do?",
            answer=f"Mickey wanted to {ms.wish}, and he kept thinking about it even when the road looked tricky.",
        ),
        QAItem(
            question="What helped Mickey change the hard moment?",
            answer=f"{mh.label} helped Mickey, and the magic from {am.label} turned worry into resolve.",
        ),
        QAItem(
            question="How did Mickey feel at the end?",
            answer="He felt proud, cheerful, and ready to keep going, because the trouble had turned into a bright adventure.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    setting: Setting = world.facts["setting"]
    am: AmenitySpec = world.facts["amenity_spec"]
    return [
        QAItem(
            question=f"What is special about {setting.name}?",
            answer=f"{setting.name} is a place with {setting.wonder}, and it feels big enough for a tall tale.",
        ),
        QAItem(
            question="What is an amenity in this storyworld?",
            answer=f"An amenity is a helpful place or object, like {am.label}, that can offer rest, comfort, or a little magic.",
        ),
        QAItem(
            question="What is a tall tale?",
            answer="A tall tale is a funny, larger-than-life story that makes ordinary things sound grand and full of wonder.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(prairie).
place(harbor).
place(fair).

mickey_kind(cowpoke).
mickey_kind(riverhand).
mickey_kind(ringmaster).

amenity_kind(well).
amenity_kind(lantern).
amenity_kind(fountain).

mhiabbi_kind(sparrow).
mhiabbi_kind(goat).
mhiabbi_kind(cat).

valid_story(P, M, A, H) :- place(P), mickey_kind(M), amenity_kind(A), mhiabbi_kind(H).
#show valid_story/4.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for m in MICKEYS:
        lines.append(asp.fact("mickey_kind", m))
    for a in AMENITIES:
        lines.append(asp.fact("amenity_kind", a))
    for h in MHIABBIS:
        lines.append(asp.fact("mhiabbi_kind", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p, m, a, h) for p in SETTINGS for m in MICKEYS for a in AMENITIES for h in MHIABBIS}
    asp_set = set(asp_valid_stories())
    if py == asp_set:
        print(f"OK: ASP parity matches Python ({len(py)} combinations).")
        return 0
    print("MISMATCH between ASP and Python.")
    if py - asp_set:
        print("Only in Python:", sorted(py - asp_set))
    if asp_set - py:
        print("Only in ASP:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Generation and CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="prairie", mickey_kind="cowpoke", amenity_kind="well", mhiabbi_kind="goat"),
    StoryParams(place="harbor", mickey_kind="riverhand", amenity_kind="lantern", mhiabbi_kind="cat"),
    StoryParams(place="fair", mickey_kind="ringmaster", amenity_kind="fountain", mhiabbi_kind="sparrow"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld with Mickey, amenity, and Mhiabbi.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mickey-kind", choices=MICKEYS)
    ap.add_argument("--amenity-kind", choices=AMENITIES)
    ap.add_argument("--mhiabbi-kind", choices=MHIABBIS)
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
    place = args.place or rng.choice(list(SETTINGS))
    mickey_kind = args.mickey_kind or rng.choice(list(MICKEYS))
    amenity_kind = args.amenity_kind or rng.choice(list(AMENITIES))
    mhiabbi_kind = args.mhiabbi_kind or rng.choice(list(MHIABBIS))
    return StoryParams(place=place, mickey_kind=mickey_kind, amenity_kind=amenity_kind, mhiabbi_kind=mhiabbi_kind)


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.kind} {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    out.extend(f"{i+1}. {p}" for i, p in enumerate(sample.prompts))
    out.append("")
    out.append("== Story Q&A ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} valid story combinations:")
        for item in stories:
            print(" ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
