#!/usr/bin/env python3
"""
A small superhero story world about a quest, an inner monologue, and a happy ending.

The premise is simple: a young hero must terminate a grizzly threat before it
can scour the city garden, but the real turning point comes from thoughtfulness
instead of force.
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

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None


@dataclass
class StoryParams:
    hero_name: str = "Maya"
    helper_name: str = "Bram"
    city: str = "Sunrise City"
    place: str = "the rooftop garden"
    threat: str = "grizzly"
    mission: str = "quest"
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


HERO_NAMES = ["Maya", "Lena", "Theo", "Iris", "Noah", "Zuri"]
HELPER_NAMES = ["Bram", "Nico", "Pia", "Jett", "Rosa", "Quin"]
CITIES = ["Sunrise City", "Harborlight", "Maple Metro", "Skybridge", "Riverglow"]
PLACES = ["the rooftop garden", "the moonlit alley", "the river park", "the glass plaza", "the school courtyard"]
MISSIONS = ["quest", "patrol", "rescue mission", "night watch"]

PARAM_REGISTRY = {
    "hero_name": HERO_NAMES,
    "helper_name": HELPER_NAMES,
    "city": CITIES,
    "place": PLACES,
    "mission": MISSIONS,
}

ASP_RULES = r"""
hero(H) :- hero_name(H).
helper(H) :- helper_name(H).
place(P) :- place_name(P).
threat(T) :- threat_name(T).
resolved :- threat_terminated, garden_safe.
happy_ending :- resolved.
"""

STORY_BEATS = {
    "storm": {
        "problem": "A grizzly in a torn purple coat had wandered into {place} and began to scour the flower beds with heavy paws.",
        "mistake": "{hero} tried to scare it away with a bright flash, but the grizzly only backed into the tulips.",
        "clue": "{helper} pointed to the berry trail on the path and said, “It is not hunting people. It is following food.”",
        "turn": "They found the tipped snack crate and noticed a thorny vine pinning the lid open.",
        "resolve": "Together they lifted the crate, tucked the berries into a safe box, and guided the grizzly toward the park gate.",
        "ending": "By sunrise, the flowers stood straight again, and the grizzly was peacefully napping under a tree outside the gate.",
    },
    "lost": {
        "problem": "A grizzly cub had padded into {place}, sniffing the benches and leaving muddy prints as it tried to scour for honey.",
        "mistake": "{hero} rushed closer, but the cub skittered deeper between the planters.",
        "clue": "{helper} whispered, “Listen. It sounds scared, not mean.”",
        "turn": "They noticed a broken bee box and a trail of sticky paw prints leading back to the fence.",
        "resolve": "They opened a side gate, set out a bowl of fruit, and waited until the cub followed the smell home.",
        "ending": "When the moon rose, the garden was calm, and the little grizzly was safe with its family in the woods.",
    },
    "alarm": {
        "problem": "The city siren rang because a grizzly had climbed the sculpture steps and begun to scour the plaza trash bins.",
        "mistake": "{hero} thought the only answer was to charge forward, but that only made the bear rear up in surprise.",
        "clue": "{helper} held up a calm hand and said, “Look at its fur. It has a tag from the wildlife center.”",
        "turn": "They realized the grizzly had escaped a transport cage after a bent latch snapped open.",
        "resolve": "The hero spoke softly, and the helper used a rope loop to close the broken gate until the rangers arrived.",
        "ending": "The siren stopped, the crowd cheered, and the grizzly rolled away in a waiting rescue truck with a happy huff.",
    },
    "river": {
        "problem": "Near the river path, a grizzly was splashing through the reeds and trying to scour fish from the shallows.",
        "mistake": "{hero} lifted a shield, but the shining metal startled the bear into the rushes.",
        "clue": "{helper} noticed that the bear kept glancing toward a fallen honey bucket on the bank.",
        "turn": "They followed the bucket to a picnic spot where campers had left snacks and a tipped cooler behind.",
        "resolve": "The two friends cleared the food, rang the ranger bell, and made a wide path for the grizzly to leave.",
        "ending": "The river glittered again, and the grizzly ambled into the woods while dragonflies danced above the water.",
    },
}

ASP_SHOW = "#show threat_terminated/0.\n#show garden_safe/0.\n#show happy_ending/0.\n"


def asp_facts() -> str:
    import asp

    facts = [
        asp.fact("hero_name", "hero"),
        asp.fact("helper_name", "helper"),
        asp.fact("place_name", "place"),
        asp.fact("threat_name", "grizzly"),
        asp.fact("threat_terminated"),
        asp.fact("garden_safe"),
    ]
    return "\n".join(facts)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{ASP_SHOW}"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero story world about a quest to stop a grizzly from scouring the city.")
    ap.add_argument("--name", dest="hero_name")
    ap.add_argument("--helper")
    ap.add_argument("--city")
    ap.add_argument("--place")
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
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    helper_name = args.helper or rng.choice([h for h in HELPER_NAMES if h != hero_name])
    if helper_name == hero_name:
        raise StoryError("The helper must be a different person from the hero.")
    return StoryParams(
        hero_name=hero_name,
        helper_name=helper_name,
        city=args.city or rng.choice(CITIES),
        place=args.place or rng.choice(PLACES),
        threat="grizzly",
        mission=rng.choice(MISSIONS),
    )


def verify_reasonable(params: StoryParams) -> None:
    if params.threat != "grizzly":
        raise StoryError("This world only simulates a grizzly threat.")
    if not params.place:
        raise StoryError("A place is required for the story.")
    if not params.hero_name or not params.helper_name:
        raise StoryError("Both hero and helper names are required.")


def generate(params: StoryParams) -> StorySample:
    verify_reasonable(params)
    rng = random.Random(params.seed if params.seed is not None else f"{params.hero_name}:{params.helper_name}:{params.city}:{params.place}")
    world = World()

    hero = world.add(Entity("hero", "character", params.hero_name, memes={"courage": 1.0, "worry": 0.3}))
    helper = world.add(Entity("helper", "character", params.helper_name, memes={"calm": 1.0, "trust": 0.7}))
    grizzly = world.add(Entity("grizzly", "animal", "grizzly", meters={"distance": 12.0, "damage": 4.0}, memes={"restless": 1.0}))

    trope = rng.choice(list(STORY_BEATS.values()))
    opening = f"In {params.city}, the hero known as {params.hero_name} was sent on a {params.mission} to {params.place}."
    world.say(opening)
    world.say(f"An inner monologue flickered through {params.hero_name}'s mind: “I can do this. I just have to think before I leap.”")
    world.say(trope["problem"].format(place=params.place))
    world.say(f'“We need to terminate the danger without hurting the city garden,” {params.hero_name} said.')
    world.say(f'“Then let us scour the scene first,” {params.helper_name} replied, “and find out what the grizzly is really after.”')
    world.say(trope["mistake"].format(hero=params.hero_name))
    world.say(trope["clue"].format(helper=params.helper_name))
    world.say(f"{params.hero_name} thought, “A true hero solves the puzzle, not just the noise.”")
    world.say(trope["turn"].format(hero=params.hero_name, helper=params.helper_name))
    world.say(f'“Now we know the cause,” {params.helper_name} said. “We can change the ending.”')
    world.say(trope["resolve"].format(hero=params.hero_name, helper=params.helper_name))

    grizzly.meters["distance"] = 40.0
    grizzly.meters["damage"] = 0.0
    grizzly.memes["restless"] = 0.0
    hero.memes["courage"] = 2.0
    hero.memes["joy"] = 1.0
    helper.memes["trust"] = 1.0

    world.say("The grizzly stopped scouring the beds, and the flowers finally had room to bloom again.")
    world.say("The hero smiled at the helper and said, “That was a real quest.”")
    world.say("“And a happy ending,” the helper answered, as the city lights twinkled over the safe, quiet garden.")
    world.say(trope["ending"])

    world.facts.update({
        "hero": hero,
        "helper": helper,
        "grizzly": grizzly,
        "quest": params.mission,
        "place": params.place,
        "city": params.city,
        "happy_ending": True,
    })

    prompts = [
        f"Write a superhero story about {params.hero_name} and {params.helper_name} on a {params.mission} in {params.city}.",
        "Include an inner monologue, a brief spoken exchange, and a happy ending.",
        "Use the words terminate, grizzly, and scour in a child-facing adventure.",
    ]

    story_qa = [
        QAItem(
            question="What was the hero trying to do?",
            answer=f"{params.hero_name} was trying to terminate the grizzly threat without hurting the city garden.",
        ),
        QAItem(
            question="What helped the hero understand the grizzly?",
            answer=f"{params.helper_name} helped by looking for clues and noticing what the grizzly was after.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer="The grizzly was guided away, the garden was safe again, and the quest ended happily.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a grizzly?",
            answer="A grizzly is a large bear with thick fur that can be powerful and fast.",
        ),
        QAItem(
            question="What does scour mean?",
            answer="To scour means to search through something thoroughly or to scrape and sweep across a surface.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is a character's private thoughts, shown to the reader but not spoken out loud.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- trace ---")
        for k, ent in sample.world.entities.items():
            print(f"{k}: {ent.label} meters={ent.meters} memes={ent.memes}")
    if qa:
        print("\n== prompts ==")
        for p in sample.prompts:
            print(p)
        print("\n== story qa ==")
        for q in sample.story_qa:
            print(f"Q: {q.question}")
            print(f"A: {q.answer}")
        print("\n== world qa ==")
        for q in sample.world_qa:
            print(f"Q: {q.question}")
            print(f"A: {q.answer}")


def asp_verify() -> int:
    import asp

    program = asp_program()
    model = asp.one_model(program)
    names = {(sym.name, tuple(getattr(a, "name", getattr(a, "string", getattr(a, "number", None))) for a in sym.arguments)) for sym in model}
    wanted = {("threat_terminated", ()), ("garden_safe", ()), ("happy_ending", ())}
    if names == wanted:
        print("OK: ASP and Python parity looks good.")
        return 0
    print("MISMATCH between ASP and Python reasoning.")
    print(sorted(names))
    print(sorted(wanted))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for hero_name in HERO_NAMES[:3]:
            params = StoryParams(hero_name=hero_name, helper_name=HELPER_NAMES[0], city=CITIES[0], place=PLACES[0], seed=base_seed)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
