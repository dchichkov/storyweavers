#!/usr/bin/env python3
"""
storyworlds/worlds/chitter_camouflage_curiosity_superhero_story.py
===================================================================

A small superhero story world about curiosity, a chittering mystery, and
camouflage that helps hide the answer until the hero looks carefully.

Premise:
- A young superhero hears a chittering sound in a city rooftop garden.
- The source is a tiny creature with camouflage.
- Curiosity pushes the hero to investigate instead of ignoring the sound.
- The hero uses a clever, gentle method to find the hidden creature and help it.

The world is intentionally small and constraint-checked: the sound must be real,
the camouflage must plausibly hide the source, and the resolution must come from
curiosity plus a superhero-style rescue.
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
@dataclass(frozen=True)
class Place:
    key: str
    name: str
    kind: str  # rooftop, alley, garden, park
    bright: bool
    has_hiding_spots: bool


@dataclass(frozen=True)
class HeroTemplate:
    key: str
    name: str
    alias: str
    age_word: str
    pronoun_subject: str
    pronoun_object: str
    pronoun_possessive: str
    costume: str
    power: str


@dataclass(frozen=True)
class Creature:
    key: str
    name: str
    size: str
    sound: str
    camouflage: str
    hiding_place: str
    needs_help: str
    is_harmless: bool = True


@dataclass(frozen=True)
class Tool:
    key: str
    name: str
    use: str
    can_reveal: bool


PLACES = {
    "rooftop_garden": Place(
        key="rooftop_garden",
        name="the rooftop garden",
        kind="rooftop",
        bright=True,
        has_hiding_spots=True,
    ),
    "lantern_alley": Place(
        key="lantern_alley",
        name="Lantern Alley",
        kind="alley",
        bright=False,
        has_hiding_spots=True,
    ),
    "city_park": Place(
        key="city_park",
        name="the city park",
        kind="park",
        bright=True,
        has_hiding_spots=True,
    ),
    "school_garden": Place(
        key="school_garden",
        name="the school garden",
        kind="garden",
        bright=True,
        has_hiding_spots=True,
    ),
}

HEROES = {
    "nova": HeroTemplate(
        key="nova",
        name="Nova",
        alias="Curiosity Spark",
        age_word="little",
        pronoun_subject="she",
        pronoun_object="her",
        pronoun_possessive="her",
        costume="a blue cape with silver stars",
        power="curiosity",
    ),
    "max": HeroTemplate(
        key="max",
        name="Max",
        alias="Captain Curio",
        age_word="young",
        pronoun_subject="he",
        pronoun_object="him",
        pronoun_possessive="his",
        costume="a red mask and a bright yellow belt",
        power="curiosity",
    ),
    "zoe": HeroTemplate(
        key="zoe",
        name="Zoe",
        alias="Wonder Flash",
        age_word="brave",
        pronoun_subject="she",
        pronoun_object="her",
        pronoun_possessive="her",
        costume="a green cape with a soft gold trim",
        power="curiosity",
    ),
}

CREATURES = {
    "sparrow": Creature(
        key="sparrow",
        name="a baby sparrow",
        size="tiny",
        sound="chitter-chitter",
        camouflage="speckled feathers that blended with the leaves",
        hiding_place="a nest tucked under a planter box",
        needs_help="its wing was tangled in a loose thread",
    ),
    "kitten": Creature(
        key="kitten",
        name="a lost kitten",
        size="small",
        sound="chitter",
        camouflage="gray stripes that blended with the shadows",
        hiding_place="behind a stack of flower pots",
        needs_help="it could not get past a narrow fence gap",
    ),
    "chipmunk": Creature(
        key="chipmunk",
        name="a chipmunk",
        size="tiny",
        sound="chitter-chitter",
        camouflage="brown stripes that blended with the bark",
        hiding_place="inside a hollow planter",
        needs_help="its snack bag had snagged on a twig",
    ),
}

TOOLS = {
    "mirror": Tool(
        key="mirror",
        name="a polished hand mirror",
        use="flash gentle sunlight into the shadows",
        can_reveal=True,
    ),
    "lantern": Tool(
        key="lantern",
        name="a small lantern",
        use="light the dark corners",
        can_reveal=True,
    ),
    "whistle": Tool(
        key="whistle",
        name="a tiny rescue whistle",
        use="call for help",
        can_reveal=False,
    ),
    "gloves": Tool(
        key="gloves",
        name="soft rescue gloves",
        use="carefully lift small things",
        can_reveal=False,
    ),
}

CURATED_KEYS = [
    ("nova", "rooftop_garden", "sparrow"),
    ("max", "lantern_alley", "kitten"),
    ("zoe", "city_park", "chipmunk"),
]


# ---------------------------------------------------------------------------
# Story params / world model
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    hero: str
    place: str
    creature: str
    tool: Optional[str] = None
    seed: Optional[int] = None


@dataclass
class World:
    hero: HeroTemplate
    place: Place
    creature: Creature
    tool: Tool
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)

    def note(self, text: str) -> None:
        self.trace.append(text)


def _m(world: World, key: str) -> float:
    return world.meters.get(key, 0.0)


def _add_meter(world: World, key: str, amount: float) -> None:
    world.meters[key] = world.meters.get(key, 0.0) + amount


def _add_meme(world: World, key: str, amount: float) -> None:
    world.memes[key] = world.memes.get(key, 0.0) + amount


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def reasonableness_check(params: StoryParams) -> None:
    if params.hero not in HEROES:
        raise StoryError("Unknown hero choice.")
    if params.place not in PLACES:
        raise StoryError("Unknown place choice.")
    if params.creature not in CREATURES:
        raise StoryError("Unknown creature choice.")
    if params.tool is not None and params.tool not in TOOLS:
        raise StoryError("Unknown tool choice.")

    place = PLACES[params.place]
    creature = CREATURES[params.creature]
    if not place.has_hiding_spots:
        raise StoryError("This place does not give the creature a believable way to hide.")

    if params.tool is not None and not TOOLS[params.tool].can_reveal:
        raise StoryError("That tool cannot plausibly reveal a camouflaged creature.")

    # The sound must be something the hero can follow in the chosen place.
    if place.kind == "rooftop" and params.creature == "chipmunk":
        # chipmunks on rooftops are a little odd but still possible in city stories.
        return

    if creature.size == "tiny" and not place.has_hiding_spots:
        raise StoryError("Tiny creatures need hiding places for the camouflage premise to work.")


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A creature is hidden when camouflage matches the place's hiding spots.
hidden(C,P) :- creature(C), place(P), camouflaged(C), hiding_spot(P).

% A reveal works when the chosen tool can reveal and the hero is curious enough.
can_find(H,C,P) :- hero(H), creature(C), place(P), hidden(C,P), tool(T), reveal_tool(T), curious(H).

% A valid story exists when the creature can be heard, hidden, and then found.
valid_story(H,P,C) :- hears_chitter(H,C,P), hidden(C,P), can_find(H,C,P).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for place in PLACES.values():
        lines.append(asp.fact("place", place.key))
        if place.has_hiding_spots:
            lines.append(asp.fact("hiding_spot", place.key))
    for hero in HEROES.values():
        lines.append(asp.fact("hero", hero.key))
        lines.append(asp.fact("curious", hero.key))
    for creature in CREATURES.values():
        lines.append(asp.fact("creature", creature.key))
        lines.append(asp.fact("camouflaged", creature.key))
    for tool in TOOLS.values():
        lines.append(asp.fact("tool", tool.key))
        if tool.can_reveal:
            lines.append(asp.fact("reveal_tool", tool.key))
    # Seeded relation present for all curated combinations.
    for hero_key, place_key, creature_key in CURATED_KEYS:
        lines.append(asp.fact("hears_chitter", hero_key, creature_key, place_key))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple[str, str, str]]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_stories())
    if py != asp_set:
        print("MISMATCH between ASP and Python:")
        if py - asp_set:
            print("  only in python:", sorted(py - asp_set))
        if asp_set - py:
            print("  only in ASP:", sorted(asp_set - py))
        return 1
    print(f"OK: ASP matches Python ({len(py)} valid stories).")
    return 0


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for hero in HEROES:
        for place in PLACES:
            for creature in CREATURES:
                combos.append((hero, place, creature))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    reasonableness_check(StoryParams(
        hero=args.hero or "nova",
        place=args.place or "rooftop_garden",
        creature=args.creature or "sparrow",
        tool=args.tool,
    ))

    choices = valid_combos()
    if args.hero:
        choices = [c for c in choices if c[0] == args.hero]
    if args.place:
        choices = [c for c in choices if c[1] == args.place]
    if args.creature:
        choices = [c for c in choices if c[2] == args.creature]
    if not choices:
        raise StoryError("No valid combination matches the given options.")

    hero, place, creature = rng.choice(choices)
    tool = args.tool or rng.choice(list(TOOLS))
    if not TOOLS[tool].can_reveal:
        tool = rng.choice([k for k, t in TOOLS.items() if t.can_reveal])
    return StoryParams(hero=hero, place=place, creature=creature, tool=tool)


def generate(params: StoryParams) -> StorySample:
    reasonableness_check(params)

    hero = HEROES[params.hero]
    place = PLACES[params.place]
    creature = CREATURES[params.creature]
    tool = TOOLS[params.tool or "mirror"]

    world = World(hero=hero, place=place, creature=creature, tool=tool)

    _add_meme(world, "curiosity", 1.0)
    _add_meme(world, "concern", 1.0)
    world.note(f"{hero.name} notices a chitter sound in {place.name}.")
    world.note(f"The sound is hidden by camouflage.")
    world.note(f"{hero.name} uses {tool.name} to reveal the source.")

    # Narration with a clear beginning, middle turn, and ending image.
    story_parts = []
    story_parts.append(
        f"{hero.name}, {hero.age_word} superhero {hero.alias}, stood in {place.name} "
        f"in {hero.costume}."
    )
    story_parts.append(
        f"Then {hero.pronoun_subject} heard a soft {creature.sound} from near a stack of "
        f"plants, and {hero.pronoun_subject} felt {hero.pronoun_possessive} curiosity wake up like a bright light."
    )
    story_parts.append(
        f"The little noise seemed to come from nowhere, because {creature.name} was hidden by "
        f"{creature.camouflage}."
    )
    story_parts.append(
        f"Instead of flying away, {hero.name} used {tool.name} to {tool.use}, and the tiny hidden shape appeared."
    )
    story_parts.append(
        f"{hero.name} found that {creature.name} was stuck because {creature.needs_help}."
    )
    story_parts.append(
        f"With a careful superhero lift and a gentle smile, {hero.name} helped the little creature safely free."
    )
    story_parts.append(
        f"At the end, the {creature.sound} was not a mystery anymore, and {hero.name} "
        f"stood happily beside a safe, blinking friend in the sunny {place.name}."
    )

    story = " ".join(story_parts)

    world.facts.update(
        hero=hero,
        place=place,
        creature=creature,
        tool=tool,
        heard_sound=creature.sound,
        hidden=True,
        resolved=True,
    )

    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short superhero story for a preschooler about a curious hero hearing a chittering sound and finding a hidden creature.',
        f"Tell a gentle superhero tale where {world.hero.name} uses curiosity to solve a camouflage mystery in {world.place.name}.",
        f'Write a child-facing story that includes the words "{world.creature.sound}" and "camouflage" and ends with a rescue.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.hero
    creature = world.creature
    place = world.place
    tool = world.tool
    return [
        QAItem(
            question=f"What did {hero.name} hear in {place.name}?",
            answer=f"{hero.name} heard a soft {creature.sound} coming from a hidden place in {place.name}.",
        ),
        QAItem(
            question=f"Why was it hard to see {creature.name} at first?",
            answer=f"It was hard to see because {creature.camouflage} helped it blend into the place where it was hiding.",
        ),
        QAItem(
            question=f"What did {hero.name} use to find the hidden creature?",
            answer=f"{hero.name} used {tool.name} to {tool.use} and reveal the little creature.",
        ),
        QAItem(
            question=f"What did curiosity help {hero.name} do?",
            answer=f"Curiosity helped {hero.name} keep looking, discover what made the {creature.sound}, and help the creature safely.",
        ),
        QAItem(
            question=f"How did the story end for {creature.name}?",
            answer=f"By the end, {creature.name} was safe, and {hero.name} was standing beside a new friend in {place.name}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is camouflage?",
            answer="Camouflage is a way of blending in so something is harder to see.",
        ),
        QAItem(
            question="What does curiosity do?",
            answer="Curiosity makes you want to look, learn, and ask questions about what is happening.",
        ),
        QAItem(
            question="What is a superhero?",
            answer="A superhero is a hero who uses special courage or powers to help others.",
        ),
        QAItem(
            question="Why do tiny animals hide?",
            answer="Tiny animals hide to stay safe, rest, or keep out of trouble.",
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
    lines.append(f"hero: {world.hero.name} ({world.hero.alias})")
    lines.append(f"place: {world.place.name}")
    lines.append(f"creature: {world.creature.name}")
    lines.append(f"tool: {world.tool.name}")
    lines.append(f"meters: {world.meters}")
    lines.append(f"memes: {world.memes}")
    lines.extend(f"trace: {t}" for t in world.trace)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world about curiosity, chitter, and camouflage.")
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--tool", choices=TOOLS)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} valid stories:")
        for item in stories:
            print("  ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for hero, place, creature in CURATED_KEYS:
            params = StoryParams(hero=hero, place=place, creature=creature, tool="mirror", seed=base_seed)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
                params.seed = seed
                sample = generate(params)
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.hero} / {p.place} / {p.creature}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
