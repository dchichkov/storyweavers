#!/usr/bin/env python3
"""
A small animal-story world about an alphabetic husk and a happy ending.

Seed tale:
A tiny squirrel finds a dry husk that is covered in odd little marks. The marks
look like letters, but they are scrambled. The squirrel wants to keep the husk
as a treasure, while a friend worries it will fall apart. Together they clean
it, sort the letters in order, and discover that the husk is actually a game
made by a friendly bird. The animals laugh, share the prize, and everyone ends
the day happy.

The world model tracks:
- physical meters: cleanliness, neatness, damage, and how much the husk holds
- emotional memes: curiosity, worry, delight, and friendship
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

HUSK_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    contains: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"squirrel", "rabbit", "mouse", "bird", "fox", "bear"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

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
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    hero_kind: str
    friend_kind: str
    name: str
    seed: Optional[int] = None


PLACES = {
    "meadow": "the meadow",
    "orchard": "the orchard",
    "barnyard": "the barnyard",
    "garden": "the garden",
}

HEROES = {
    "squirrel": {
        "label": "a squirrel",
        "phrase": "a quick little squirrel",
        "animal_name": "Squirrel",
    },
    "rabbit": {
        "label": "a rabbit",
        "phrase": "a bright little rabbit",
        "animal_name": "Rabbit",
    },
    "mouse": {
        "label": "a mouse",
        "phrase": "a tiny mouse",
        "animal_name": "Mouse",
    },
}

FRIENDS = {
    "bird": {
        "label": "a bird",
        "phrase": "a cheerful bird",
    },
    "fox": {
        "label": "a fox",
        "phrase": "a careful fox",
    },
    "bear": {
        "label": "a bear",
        "phrase": "a gentle bear",
    },
}


def _cleanliness(world: World, actor: Entity) -> None:
    if actor.meters.get("dusty", 0) >= HUSK_THRESHOLD and actor.meters.get("washed", 0) < HUSK_THRESHOLD:
        actor.meters["dusty"] = 0
        actor.meters["washed"] = 1
        world.say(f"{actor.id} got cleaned up and looked much tidier.")


def _husk_rule(world: World) -> None:
    husk = world.get("husk")
    sort = world.get("sort")
    reader = world.get("reader")
    if husk.meters.get("scrambled", 0) >= HUSK_THRESHOLD and sort.meters.get("done", 0) >= HUSK_THRESHOLD:
        sig = ("readable",)
        if sig not in world.fired:
            world.fired.add(sig)
            husk.meters["scrambled"] = 0
            husk.meters["readable"] = 1
            reader.memes["delight"] += 1
            world.say("The marks lined up into a neat alphabetic path, and the husk became readable.")
    if husk.meters.get("readable", 0) >= HUSK_THRESHOLD and reader.memes.get("delight", 0) >= HUSK_THRESHOLD:
        sig = ("happy_end",)
        if sig not in world.fired:
            world.fired.add(sig)
            reader.memes["joy"] += 1
            world.say("Everyone felt glad that the puzzle had turned into a happy surprise.")


def propagate(world: World) -> None:
    changed = True
    while changed:
        before = len(world.fired)
        _husk_rule(world)
        for ent in list(world.entities.values()):
            _cleanliness(world, ent)
        changed = len(world.fired) != before


def predict_story(world: World) -> bool:
    sim = world.copy()
    sim.get("husk").meters["scrambled"] = 1
    sim.get("sort").meters["done"] = 1
    propagate(sim)
    return bool(sim.get("husk").meters.get("readable", 0) >= HUSK_THRESHOLD)


def tell(params: StoryParams) -> World:
    world = World(PLACES[params.place])

    hero_info = HEROES[params.hero_kind]
    friend_info = FRIENDS[params.friend_kind]

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.hero_kind,
        label=hero_info["label"],
        phrase=hero_info["phrase"],
        meters={"dusty": 0.0, "washed": 0.0},
        memes={"curiosity": 1.0, "joy": 0.0, "worry": 0.0, "friendship": 1.0},
    ))
    friend = world.add(Entity(
        id="Friend",
        kind="character",
        type=params.friend_kind,
        label=friend_info["label"],
        phrase=friend_info["phrase"],
        meters={"dusty": 0.0, "washed": 0.0},
        memes={"care": 1.0, "worry": 0.0, "joy": 0.0},
    ))
    reader = world.add(Entity(
        id="reader",
        kind="character",
        type="bird",
        label="the bird",
        phrase="the bird",
        meters={"dusty": 0.0, "washed": 0.0},
        memes={"delight": 0.0, "joy": 0.0},
    ))
    husk = world.add(Entity(
        id="husk",
        type="husk",
        label="a dry husk",
        phrase="a dry husk with marks on it",
        meters={"scrambled": 0.0, "readable": 0.0, "fragile": 1.0},
        memes={"mystery": 1.0},
    ))
    sorter = world.add(Entity(
        id="sort",
        type="action",
        label="sorting",
        phrase="sorting the marks",
        meters={"done": 0.0},
        memes={"care": 0.0},
    ))

    world.say(
        f"One morning in {world.place}, {hero.phrase} found {husk.phrase} tucked beside a path."
    )
    world.say(
        f"{hero.id} liked the husk at once, because the marks looked like an alphabetic game."
    )

    world.para()
    world.say(
        f"{friend.phrase} came over and frowned. \"Be gentle,\" {friend.pronoun()} said, "
        f"\"or the husk might break.\""
    )
    hero.memes["worry"] += 1.0
    world.get("husk").meters["scrambled"] += 1.0
    world.get("husk").meters["fragile"] += 0.0
    world.say(
        f"{hero.id} did not want to give up the treasure, but the scrambled letters made the puzzle hard to read."
    )

    world.para()
    if predict_story(world):
        world.say(
            f"So the friends made a careful plan: they sat together, smoothed the husk, and began to sort the marks."
        )
        sorter.meters["done"] += 1.0
        hero.memes["joy"] += 1.0
        friend.memes["joy"] += 1.0
        propagate(world)
        world.say(
            f"The bird watched closely, then chirped happily when the alphabetic line finally made sense."
        )
        reader.memes["joy"] += 1.0
        world.get("husk").meters["readable"] = 1.0
        world.say(
            f"It turned out the husk was a tiny game from the bird, and the three animals shared a laugh."
        )
        world.say(
            f"{hero.id} kept the husk as a special prize, and nobody was upset anymore."
        )
    else:
        raise StoryError("This story needs a readable husk ending, but the world model could not make one.")

    world.facts.update(
        hero=hero,
        friend=friend,
        reader=reader,
        husk=husk,
        sorter=sorter,
        place=params.place,
        hero_kind=params.hero_kind,
        friend_kind=params.friend_kind,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short animal story about an alphabetic husk found in {world.place}.',
        f"Tell a gentle story where {f['hero'].phrase} finds a husk with scrambled letters, "
        f"worries a friend, and ends with a happy ending.",
        "Write a child-friendly story about animals sorting letters and learning that a strange husk was really a friendly game.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, husk = f["hero"], f["friend"], f["husk"]
    return [
        QAItem(
            question=f"What did {hero.id} find in {world.place}?",
            answer=f"{hero.id} found {husk.phrase} in {world.place}. The husk had marks that looked alphabetic and a little scrambled.",
        ),
        QAItem(
            question=f"Why did {friend.id} worry about the husk?",
            answer=f"{friend.id} worried because the husk was dry and fragile, so rough handling might have made it break.",
        ),
        QAItem(
            question="What made the ending happy?",
            answer="The animals sorted the marks, the husk became readable, and they learned it was a friendly game from the bird.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does alphabetic mean?",
            answer="Alphabetic means arranged in the order of letters from A to Z.",
        ),
        QAItem(
            question="What is a husk?",
            answer="A husk is the dry outer part of something like a seed or nut after the inside is gone.",
        ),
        QAItem(
            question="Why can sorting help with a puzzle?",
            answer="Sorting can help because putting things in order makes patterns easier to see and understand.",
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
husk_readable :- scrambled(husk), sorted(husk).
happy_ending :- husk_readable, delight(reader).
sorted(husk) :- action(sort).
delight(reader) :- husk_readable.
"""

def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("scrambled", "husk"),
        asp.fact("action", "sort"),
        asp.fact("reader", "reader"),
        asp.fact("place", "meadow"),
        asp.fact("place", "orchard"),
        asp.fact("place", "barnyard"),
        asp.fact("place", "garden"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show husk_readable/0.\n#show happy_ending/0."))
    atoms = {str(a) for a in model}
    ok = {"husk_readable", "happy_ending"} <= atoms
    if ok:
        print("OK: ASP rules derive the happy ending.")
        return 0
    print("MISMATCH: ASP rules did not derive the expected ending.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world about an alphabetic husk and a happy ending.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--hero-kind", choices=sorted(HEROES))
    ap.add_argument("--friend-kind", choices=sorted(FRIENDS))
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
    place = args.place or rng.choice(list(PLACES))
    hero_kind = args.hero_kind or rng.choice(list(HEROES))
    friend_kind = args.friend_kind or rng.choice(list(FRIENDS))
    if hero_kind == friend_kind and len(FRIENDS) > 1:
        friend_kind = rng.choice([k for k in FRIENDS if k != hero_kind])
    name = args.name or rng.choice(["Milo", "Pip", "Nina", "Toby", "Luna"])
    return StoryParams(place=place, hero_kind=hero_kind, friend_kind=friend_kind, name=name)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


CURATED = [
    StoryParams(place="meadow", hero_kind="squirrel", friend_kind="bird", name="Milo"),
    StoryParams(place="orchard", hero_kind="rabbit", friend_kind="fox", name="Pip"),
    StoryParams(place="garden", hero_kind="mouse", friend_kind="bear", name="Nina"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show husk_readable/0.\n#show happy_ending/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
