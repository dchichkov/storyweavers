#!/usr/bin/env python3
"""
storyworlds/worlds/honcho_suspense_reconciliation_adventure.py
==============================================================

A small adventure storyworld about a proud little honcho, a tense search, and
a warm reconciliation after the missing trail sign is found.

The domain is intentionally narrow:
- one trail setting
- one suspenseful problem
- one reconciliation turn
- clear physical meters and emotional memes
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "it"


@dataclass
class Trail:
    place: str = "the pine trail"
    features: tuple[str, ...] = ("bridge", "cave", "river bend")


@dataclass
class GuideItem:
    id: str
    label: str
    phrase: str
    use: str


@dataclass
class StoryParams:
    trail: str
    item: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, trail: Trail) -> None:
        self.trail = trail
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.pulse: int = 0
        self.found: bool = False

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

    def copy(self) -> "World":
        import copy

        w = World(self.trail)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.pulse = self.pulse
        w.found = self.found
        return w


SETTINGS = {
    "pine": Trail(place="the pine trail", features=("bridge", "river bend")),
    "ridge": Trail(place="the windy ridge trail", features=("stone arch", "forked path")),
    "creek": Trail(place="the creek trail", features=("fallen log", "reed bend")),
}

ITEMS = {
    "map": GuideItem(
        id="map",
        label="trail map",
        phrase="a folded trail map with bright arrows",
        use="find the way",
    ),
    "lantern": GuideItem(
        id="lantern",
        label="lantern",
        phrase="a small brass lantern",
        use="light the path",
    ),
    "compass": GuideItem(
        id="compass",
        label="compass",
        phrase="a round compass on a cord",
        use="keep the direction straight",
    ),
}

HERO_NAMES = ["Ari", "Milo", "Nina", "Tess", "Jules", "Rae", "Ivy", "Kai"]
HELPER_NAMES = ["Pip", "Mara", "Bo", "Lena", "Otis", "Nell"]
TRAITS = ["brave", "curious", "quick", "careful", "spirited", "stubborn"]


ASP_RULES = r"""
#show valid/3.
#show valid_story/4.

valid(Place, Item, HeroType) :- trail(Place), guide(Item), hero_type(HeroType).
valid_story(Place, Item, HeroType, HelperType) :- valid(Place, Item, HeroType), helper_type(HelperType).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for key in SETTINGS:
        lines.append(asp.fact("trail", key))
    for key in ITEMS:
        lines.append(asp.fact("guide", key))
    for ht in ["girl", "boy"]:
        lines.append(asp.fact("hero_type", ht))
    for ht in ["girl", "boy"]:
        lines.append(asp.fact("helper_type", ht))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for item in ITEMS:
            for hero_type in ["girl", "boy"]:
                combos.append((place, item, hero_type))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: a honcho, suspense, and reconciliation.")
    ap.add_argument("--trail", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = [c for c in valid_combos()
              if (args.trail is None or c[0] == args.trail)
              and (args.item is None or c[1] == args.item)
              and (args.gender is None or c[2] == args.gender)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    trail, item, hero_type = rng.choice(combos)
    helper_type = args.helper or ("boy" if hero_type == "girl" else "girl")
    hero_name = args.name or rng.choice(HERO_NAMES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        trail=trail,
        item=item,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
        trait=trait,
    )


def reasonableness_gate(params: StoryParams) -> None:
    if params.item not in ITEMS:
        raise StoryError("Unknown guide item.")
    if params.trail not in SETTINGS:
        raise StoryError("Unknown trail setting.")


def tell(params: StoryParams) -> World:
    reasonableness_gate(params)
    world = World(SETTINGS[params.trail])

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        traits=["little", "honcho", params.trait],
        meters={"hurry": 0.0},
        memes={"pride": 1.0, "worry": 0.0, "suspense": 0.0, "relief": 0.0, "trust": 0.0, "reconciliation": 0.0},
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type=params.helper_type,
        traits=["little", "helper"],
        meters={"search": 0.0},
        memes={"worry": 0.0, "trust": 0.0, "reconciliation": 0.0},
    ))
    item_def = ITEMS[params.item]
    guide = world.add(Entity(
        id=item_def.id,
        kind="thing",
        type="thing",
        label=item_def.label,
        phrase=item_def.phrase,
        owner=hero.id,
        carried_by=hero.id,
        meters={"lost": 0.0},
        memes={"important": 1.0},
    ))

    world.say(
        f"{hero.id} was the little honcho of the trail club, and {hero.pronoun()} liked to lead the way."
    )
    world.say(
        f"{hero.id} carried {hero.pronoun('possessive')} {guide.label} because it helped {item_def.use}."
    )

    world.para()
    world.say(
        f"One afternoon on {world.trail.place}, {hero.id} hurried ahead toward the {world.trail.features[0]}."
    )
    hero.meters["hurry"] += 1
    guide.carried_by = None
    guide.meters["lost"] += 1
    hero.memes["suspense"] += 1
    world.say(
        f"Then the {guide.label} slipped away near the path, and the woods went quiet."
    )
    world.say(
        f"{hero.id} stared at the empty hands and felt the suspense rise like a tight knot."
    )

    world.para()
    helper.memes["worry"] += 1
    helper.meters["search"] += 1
    world.say(
        f"{params.helper_name} joined the search beside {hero.id}, peering under roots and around stones."
    )
    world.say(
        f"They followed a tiny scrape in the dirt to the {world.trail.features[1]} and found the {guide.label} tucked behind a log."
    )
    guide.meters["lost"] = 0.0
    guide.carried_by = hero.id
    world.found = True
    hero.memes["suspense"] = 0.0
    hero.memes["relief"] += 1
    helper.memes["trust"] += 1
    hero.memes["reconciliation"] += 1
    helper.memes["reconciliation"] += 1

    world.para()
    world.say(
        f"{hero.id} looked at {params.helper_name} and smiled a sorry smile."
    )
    world.say(
        f'"Thanks for staying with me," {hero.pronoun()} said. "{params.helper_name} nodded, and the two friends set off together again.'
    )
    world.say(
        f"This time {hero.id} held the {guide.label} tightly, and the little honcho led the way more carefully than before."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        guide=guide,
        trail=world.trail,
        params=params,
        resolved=True,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a short adventure story for a young child about a honcho named {p.hero_name} on {world.trail.place}.',
        f"Tell a suspenseful, gentle story where {p.hero_name} loses {p.hero_name}'s {ITEMS[p.item].label} and a helper helps find it.",
        "Write a child-friendly adventure with a tense search and a friendly reconciliation at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    guide: Entity = world.facts["guide"]
    return [
        QAItem(
            question=f"Who was the little honcho in the story?",
            answer=f"{hero.id} was the little honcho who led the trail club on {world.trail.place}.",
        ),
        QAItem(
            question=f"What did {hero.id} lose on the trail?",
            answer=f"{hero.id} lost {hero.pronoun('possessive')} {guide.label} near the trail, which made the story suspenseful.",
        ),
        QAItem(
            question=f"How did {hero.id} and {p.helper_name} solve the problem?",
            answer=f"They searched together, found the {guide.label} near the {world.trail.features[1]}, and made up after the scare.",
        ),
        QAItem(
            question=f"How did {hero.id} feel when the {guide.label} was found?",
            answer=f"{hero.id} felt relief, and the suspense melted away when the {guide.label} came back.",
        ),
        QAItem(
            question=f"What changed between {hero.id} and {p.helper_name} by the end?",
            answer=f"They felt more trust and reconciliation after helping each other on the trail.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a trail club?",
            answer="A trail club is a small group of people who walk or explore together and help each other stay safe.",
        ),
        QAItem(
            question="What does suspense mean in a story?",
            answer="Suspense is the nervous feeling you get when you do not know what will happen next.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people who felt upset make up and become friendly again.",
        ),
        QAItem(
            question="Why is a map useful on a trail?",
            answer="A map helps you know where to go so you do not get lost.",
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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  found: {world.found}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def valid_pairs() -> list[tuple[str, str, str]]:
    return valid_combos()


def asp_verify_gate() -> int:
    return asp_verify()


CURATED = [
    StoryParams(trail="pine", item="map", hero_name="Ari", hero_type="girl", helper_name="Pip", helper_type="boy", trait="brave"),
    StoryParams(trail="ridge", item="lantern", hero_name="Milo", hero_type="boy", helper_name="Mara", helper_type="girl", trait="careful"),
    StoryParams(trail="creek", item="compass", hero_name="Nina", hero_type="girl", helper_name="Bo", helper_type="boy", trait="spirited"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify_gate())
    if args.asp:
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible combos ({len(stories)} with helper type):\n")
        for place, item, hero_type in triples:
            helpers = sorted(g for (pl, it, ht, g) in stories if (pl, it, ht) == (place, item, hero_type))
            print(f"  {place:8} {item:8} {hero_type:5}  [{', '.join(helpers)}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.hero_name}: {p.item} on {p.trail}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
