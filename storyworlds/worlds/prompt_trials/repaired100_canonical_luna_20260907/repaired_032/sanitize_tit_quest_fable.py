#!/usr/bin/env python3
"""
A small fable storyworld about Luna, a tidy tit, and a quest to sanitize a
polluted spring before the forest animals lose their drinking water.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    id: str
    label: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    title: str
    blight: str
    remedy: str
    token: str
    image: str


@dataclass
class StoryParams:
    grove: str
    quest: str
    hero: str
    helper: str
    seed: Optional[int] = None
    telling: str = "fable"


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


GROVES = {
    "willow_grove": Place(
        "willow_grove",
        "Willow Grove",
        {"spring", "willow leaves", "smooth stones"},
    ),
    "moonlit_meadow": Place(
        "moonlit_meadow",
        "Moonlit Meadow",
        {"spring", "silver grass", "smooth stones"},
    ),
    "hazel_hollow": Place(
        "hazel_hollow",
        "Hazel Hollow",
        {"spring", "hazel leaves", "clay cups"},
    ),
}

QUESTS = {
    "clear_spring": Quest(
        "clear_spring",
        "The Quest of the Clear Spring",
        "a stripe of bitter dye spilled into the spring",
        "wash the spring with clean sand and a bed of smooth stones",
        "a bright blue feather",
        "the spring shone like a round piece of sky",
    ),
    "quiet_pool": Quest(
        "quiet_pool",
        "The Quest of the Quiet Pool",
        "a heap of soapy foam covered the pool",
        "skim away the foam and guide fresh water through reeds",
        "a white pebble",
        "the pool winked beneath the stars like a friendly eye",
    ),
    "sweet_stream": Quest(
        "sweet_stream",
        "The Quest of the Sweet Stream",
        "a sack of sour berry mash had clouded the stream",
        "strain the mash through woven grass and rinse the stones",
        "a red berry",
        "the stream sang a clean little song around every stone",
    ),
}

NAMES = ["Luna", "Pip", "Mira", "Tavi", "Nell", "Oren", "Sela", "Bram"]
HELPERS = ["Pip", "Mira", "Tavi", "Nell", "Oren", "Sela", "Bram"]
TELLINGS = {
    "fable": {
        "opening": "In {grove}, where the leaves whispered old lessons, {hero} the tit found a strange stain beside the spring.",
        "moral_hint": "The oldest willow murmured, \"A clean home is a promise made visible.\"",
        "ending": "The animals drank safely again, and even the smallest wing learned that care can carry a whole forest.",
    },
    "fireside": {
        "opening": "Listen closely, for this fable began when {hero} the tit heard the spring cough beneath the evening trees.",
        "moral_hint": "An old tortoise said, \"What we leave behind becomes another creature's beginning.\"",
        "ending": "That night, every animal found the spring sweet, and the forest slept with peaceful bellies.",
    },
    "bright": {
        "opening": "At sunrise, {hero} the tit saw the spring glitter strangely in {grove}.",
        "moral_hint": "A robin called, \"Little hands and little wings can mend a large mistake.\"",
        "ending": "The clean water returned, and the animals made a shining path of stones around it.",
    },
}

ASP_RULES = r"""
place(P) :- place_name(P).
quest(Q) :- quest_name(Q).
compatible(P, Q) :- place(P), quest(Q), affords(P, spring), remedy(Q, spring_cleaning).
valid_story(P, Q) :- compatible(P, Q).
#show valid_story/2.
"""

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A fable storyworld about Luna the tit and a sanitizing quest."
    )
    parser.add_argument("--grove", choices=sorted(GROVES))
    parser.add_argument("--quest", choices=sorted(QUESTS))
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--telling", choices=sorted(TELLINGS))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def valid_combos() -> list[tuple[str, str]]:
    return [
        (grove_id, quest_id)
        for grove_id, grove in GROVES.items()
        for quest_id in QUESTS
        if "spring" in grove.affords
    ]


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for grove_id, grove in GROVES.items():
        lines.append(asp.fact("place_name", grove_id))
        for affordance in sorted(grove.affords):
            lines.append(asp.fact("affords", grove_id, affordance))
    for quest_id in QUESTS:
        lines.append(asp.fact("quest_name", quest_id))
        lines.append(asp.fact("remedy", quest_id, "spring_cleaning"))
    return "\n".join(lines)


def asp_program(show: str = "#show valid_story/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    expected = set(valid_combos())
    actual = set(asp_valid_combos())
    if expected == actual:
        print(f"OK: ASP matches Python ({len(expected)} valid combinations).")
        return 0
    print("Mismatch between Python and ASP.")
    print("Only in Python:", sorted(expected - actual))
    print("Only in ASP:", sorted(actual - expected))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        combo for combo in valid_combos()
        if args.grove is None or combo[0] == args.grove
        if args.quest is None or combo[1] == args.quest
    ]
    if not combos:
        raise StoryError("No valid grove and quest combination matches the requested options.")

    grove, quest = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(NAMES)
    candidates = [name for name in HELPERS if name != hero]
    helper = args.helper or rng.choice(candidates)
    if helper == hero:
        raise StoryError("The helper must have a different name from the hero.")
    return StoryParams(
        grove=grove,
        quest=quest,
        hero=hero,
        helper=helper,
        seed=args.seed,
        telling=args.telling or rng.choice(sorted(TELLINGS)),
    )


def tell(params: StoryParams) -> World:
    place = GROVES[params.grove]
    quest = QUESTS[params.quest]
    telling = TELLINGS[params.telling]
    world = World(place)

    hero = world.add(Entity(
        params.hero,
        "character",
        params.hero,
        meters={"wing_strength": 1.0},
        memes={"care": 1.0, "courage": 0.5},
    ))
    helper = world.add(Entity(
        params.helper,
        "character",
        params.helper,
        meters={"wing_strength": 1.0},
        memes={"care": 0.8, "patience": 1.0},
    ))
    spring = world.add(Entity(
        "spring",
        "water",
        "the spring",
        meters={"cleanliness": 0.2, "flow": 1.0},
        memes={"trust": 0.0},
    ))
    token = world.add(Entity(
        "token",
        "token",
        quest.token,
        meters={"brightness": 1.0},
        memes={"promise": 1.0},
    ))

    world.facts.update({
        "hero": hero,
        "helper": helper,
        "spring": spring,
        "token": token,
        "quest": quest,
        "telling": telling,
        "cleaned": False,
        "clue": "",
        "method": "",
    })

    world.say(telling["opening"].format(hero=params.hero, grove=place.label))
    world.say(f"It was {quest.blight}, and the thirsty animals had stopped visiting.")
    world.say(telling["moral_hint"])
    world.say(
        f"{params.hero} discovered {quest.token} near the bank, beside a trail of "
        "tiny wet footprints."
    )

    world.para()
    world.say(
        f"\"We must sanitize the spring before anyone drinks,\" said {params.hero}."
    )
    world.say(
        f"\"Then I will gather what makes the water safe,\" answered {params.helper}. "
        "\"You watch the current and tell me where the trouble hides.\""
    )
    world.say(
        f"{params.hero} followed the footprints to a hollow reed. "
        f"{params.helper} brought {quest.remedy}."
    )
    world.facts["clue"] = (
        "The wet footprints showed that the stain was drifting from the hollow reed."
    )
    world.say(world.facts["clue"])

    world.para()
    world.say(
        f"Together, {params.hero} and {params.helper} blocked the reed with a leaf, "
        f"then used {quest.remedy} to draw the blight away from the spring."
    )
    world.facts["method"] = quest.remedy
    spring.meters["cleanliness"] = 1.0
    spring.memes["trust"] = 1.0
    hero.memes["courage"] = 1.0
    helper.memes["patience"] = 1.5
    world.facts["cleaned"] = True
    world.fired.update({"notice_blight", "follow_footprints", "sanitize_spring"})
    world.say(
        f"The water cleared because they stopped the source first and then sanitized "
        f"the spring carefully, instead of merely hiding the stain."
    )
    world.say(
        f"{params.hero} placed {quest.token} on the bank as a promise that the animals "
        "would keep the water clean."
    )
    world.say(telling["ending"])
    world.say(f"At last, {quest.image}.")
    return world


def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]
    quest: Quest = world.facts["quest"]
    return [
        "Write a child-facing fable about a small bird completing a careful quest.",
        f"Show how {hero.label} must sanitize a spring after discovering {quest.blight}.",
        "Include a brief dialogue exchange, a clue that changes the plan, and a clear moral ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    spring: Entity = world.facts["spring"]
    quest: Quest = world.facts["quest"]
    return [
        QAItem(
            question=f"What problem did {hero.label} find?",
            answer=f"{hero.label} found that {quest.blight}, so the animals could no longer safely drink.",
        ),
        QAItem(
            question=f"Who helped {hero.label}?",
            answer=f"{helper.label} helped {hero.label} gather the materials and work carefully at the spring.",
        ),
        QAItem(
            question="What clue changed the plan?",
            answer=f"The clue was {world.facts['clue']} It showed them to stop the source before cleaning the water.",
        ),
        QAItem(
            question="How did they sanitize the spring?",
            answer=f"They stopped the hollow reed and used {world.facts['method']} to draw the blight away, which raised the spring's cleanliness from {0.2} to {spring.meters['cleanliness']:.1f}.",
        ),
        QAItem(
            question="What happened at the end?",
            answer=f"The spring became safe again, and {quest.image}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does sanitize mean?",
            answer="To sanitize means to clean something so it becomes safer and free from harmful dirt or germs.",
        ),
        QAItem(
            question="What is a tit?",
            answer="A tit is a small, active songbird that often searches among leaves and twigs for food.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a purposeful journey or difficult task that someone undertakes to reach an important goal.",
        ),
        QAItem(
            question="What is the lesson of the fable?",
            answer="The lesson is that careful teamwork and responsible care can repair a shared home.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    sections = ["== (1) Generation prompts =="]
    sections.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    sections.append("\n== (2) Story questions ==")
    for item in sample.story_qa:
        sections.append(f"Q: {item.question}")
        sections.append(f"A: {item.answer}")
    sections.append("\n== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        sections.append(f"Q: {item.question}")
        sections.append(f"A: {item.answer}")
    return "\n".join(sections)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.label}: meters={entity.meters}, memes={entity.memes}"
        )
    lines.append(f"  place: {world.place.label}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    lines.append(f"  cleaned: {world.facts.get('cleaned')}")
    return "\n".join(lines)


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


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(
        grove="willow_grove",
        quest="clear_spring",
        hero="Luna",
        helper="Pip",
        telling="fable",
    ),
    StoryParams(
        grove="moonlit_meadow",
        quest="quiet_pool",
        hero="Mira",
        helper="Oren",
        telling="fireside",
    ),
    StoryParams(
        grove="hazel_hollow",
        quest="sweet_stream",
        hero="Tavi",
        helper="Nell",
        telling="bright",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        combinations = asp_valid_combos()
        print(f"{len(combinations)} valid stories:")
        for combination in combinations:
            print(" ", combination)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 50):
            attempts += 1
            try:
                params = resolve_params(
                    args,
                    random.Random(base_seed + attempts),
                )
            except StoryError as error:
                print(error)
                return
            params.seed = base_seed + attempts
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps(
                [sample.to_dict() for sample in samples],
                indent=2,
                ensure_ascii=False,
            ))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
