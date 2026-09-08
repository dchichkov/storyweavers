#!/usr/bin/env python3
"""
A small adventure storyworld about Curiosity, a blase mason, and a humorous,
suspenseful discovery beneath an old garden wall.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = next(
    parent for parent in Path(__file__).resolve().parents if (parent / "results.py").is_file()
)
sys.path.insert(0, str(ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


PLACES = [
    "the ivy gate",
    "the ruined tower",
    "the lantern courtyard",
    "the mossy bridge",
]
HEROES = ["Luna", "Milo", "Nia", "Theo", "Pip"]
MASON_NAMES = ["Bram", "Mason Jo", "Ari", "Mason Bea"]
TREASURES = ["a brass compass", "a blue glass marble", "a tiny silver bell", "a painted stone"]
HUMOR_LINES = [
    "{mason} said the wall had excellent manners because it kept its secrets to itself.",
    "The loose brick gave one tiny cough, as if it had swallowed a crumb.",
    "{hero} joked that even the castle mice needed a front door.",
    "{mason} called the hidden passage a very narrow hallway for very polite ants.",
    "A pebble bounced away, looking as though it had suddenly remembered an appointment.",
]

@dataclass
class StoryParams:
    hero: str
    mason: str
    place: str
    treasure: str
    seed: Optional[int] = None

@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]

    def add(self, entity: Entity) -> None:
        self.entities[entity.id] = entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass(frozen=True)
class Arc:
    mission: str
    trouble: str
    mistaken: str
    clue: str
    test: str
    cause: str
    hero_action: str
    mason_action: str
    solution: str
    ending: str
    worried: str
    reply: str


ARCS = [
    Arc(
        "find the bell that once warned travelers",
        "a deep knock sounded behind the stones",
        "the tower was about to fall",
        "a line of fresh dust curled from one low brick",
        "pressed a feather beside the crack and watched it tremble",
        "wind was moving through a hidden passage",
        "followed the dust trail without touching the loose stones",
        "braced the wall and removed one safe brick",
        "they opened the passage and found the bell resting on a shelf",
        "the little brass bell rang over the courtyard once more",
        "That wall just knocked back!",
        "It may be hiding a doorway, not planning a collapse.",
    ),
    Arc(
        "map a safe path through the old garden",
        "a shadow slipped across the path when nobody moved",
        "a stone giant was creeping through the ivy",
        "the shadow matched a broken arch whenever the lantern swung",
        "covered the lantern and watched the shadow vanish",
        "the lantern flame was casting the arch onto the path",
        "marked the safe stones with white pebbles",
        "shielded the lantern with a curved piece of tin",
        "the travelers could cross while the shadow stayed still",
        "the arch-shaped shadow pointed like a finger toward the next hill",
        "Something enormous is following us!",
        "Let's test the light before we blame a giant.",
    ),
    Arc(
        "recover a missing builder's token",
        "a hollow clink came from under the bridge",
        "someone was trapped beneath the moss",
        "three pebbles had fallen into a neat row near a drain",
        "rolled a small acorn toward the drain and listened",
        "water was carrying pebbles through an old channel",
        "cleared leaves from the drain with a stick",
        "lifted the loose grate with a rope",
        "they reached the dry channel and found the token",
        "the builder's token shone beside the trickling water",
        "What if a cave creature is clinking down there?",
        "We can listen and look before we imagine claws.",
    ),
    Arc(
        "discover why the garden roses opened at night",
        "a red glow blinked between the wall stones",
        "a dragon was breathing behind the wall",
        "the glow appeared only after the moon touched a glass shard",
        "held a leaf over the shard and watched the red light disappear",
        "moonlight was reflecting through a buried bottle",
        "dug around the bottle with a small trowel",
        "protected the loose stones while lifting it free",
        "they turned the bottle into a lantern for the garden path",
        "the roses glowed softly beneath their new moon lantern",
        "I saw a dragon eye!",
        "It is bright, but curiosity can check what fear guesses.",
    ),
    Arc(
        "reach the old lookout before sunset",
        "the path ended at a wall that seemed much taller than before",
        "the wall had grown while they were walking",
        "its top was hidden by a low cloud",
        "held a ribbon beside the wall and saw the wind pull it sideways",
        "the cloud and a sloping path were making the wall look taller",
        "searched for the shortest route around the garden",
        "tied a guide rope between two sturdy posts",
        "they climbed the safe slope and reached the lookout",
        "sunset painted the wall gold below their triumphant flag",
        "That wall is growing!",
        "The cloud may be changing our view. Let's measure the path.",
    ),
]

OPENINGS = [
    "{hero} loved questions, and {mason} was a blase mason who claimed that old walls never surprised him.",
    "At {place}, curious {hero} met {mason}, a blase mason polishing a trowel beside the ancient stones.",
    "{hero} arrived at {place} with a map, a snack, and enough curiosity to bother even {mason}, the blase mason.",
]

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Curiosity, humor, and suspense adventure storyworld.")
    parser.add_argument("--hero", choices=HEROES)
    parser.add_argument("--mason", choices=MASON_NAMES)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--treasure", choices=TREASURES)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        hero=args.hero or rng.choice(HEROES),
        mason=args.mason or rng.choice(MASON_NAMES),
        place=args.place or rng.choice(PLACES),
        treasure=args.treasure or rng.choice(TREASURES),
    )

def build_world(params: StoryParams) -> World:
    if params.hero == params.mason:
        raise StoryError("The hero and mason must have different names.")
    world = World(params)
    world.add(Entity("hero", "character", params.hero, memes={"curiosity": 1.0}))
    world.add(Entity("mason", "character", params.mason, memes={"blase": 1.0}))
    world.add(Entity("place", "place", params.place, meters={"distance": 1.0}))
    world.add(Entity("treasure", "thing", params.treasure, memes={"mystery": 1.0}))
    return world

def generate_story(world: World) -> None:
    p = world.params
    rng = random.Random(p.seed if p.seed is not None else sum(map(ord, "|".join(vars(p).values()[:-1]))))
    arc = rng.choice(ARCS)
    opening = rng.choice(OPENINGS).format(hero=p.hero, mason=p.mason, place=p.place)

    world.say(opening)
    world.say(
        f"{p.hero} had come to {p.place} to {arc.mission}, while {p.mason} insisted that "
        f"the day would be as exciting as watching mortar dry."
    )
    world.para()
    world.say(f"Then {arc.trouble}. The stones seemed to hold their breath.")
    world.say(f"'{arc.worried}' asked {p.mason}.")
    world.say(f"'{arc.reply}' said {p.hero}.")
    world.say(f"For a moment, they believed {arc.mistaken}.")
    world.facts["trouble"] = arc.trouble
    world.facts["mistaken"] = arc.mistaken
    world.facts["suspense"] = True
    world.entities["hero"].memes.update({"curiosity": 2.0, "worry": 1.0})
    world.entities["mason"].memes["blase"] = 0.5

    world.para()
    world.say(f"Curiosity led {p.hero} to notice that {arc.clue}.")
    world.say(f"Together they {arc.test}.")
    world.say(f"That small test revealed the truth: {arc.cause}.")
    world.say(rng.choice(HUMOR_LINES).format(hero=p.hero, mason=p.mason))
    world.facts["clue"] = arc.clue
    world.facts["test"] = arc.test
    world.facts["cause"] = arc.cause
    world.facts["humor"] = True

    world.para()
    world.say(f"{p.hero} {arc.hero_action}, while {p.mason} {arc.mason_action}.")
    world.say(f"Their careful plan worked because {arc.solution}.")
    world.say(f"Inside, they also found {p.treasure}, which had been hidden by time and dust.")
    world.say(f"At last, {arc.ending}.")
    world.facts.update(
        mission=arc.mission,
        solution=arc.solution,
        ending=arc.ending,
        settled=True,
        treasure=p.treasure,
    )
    world.entities["hero"].memes.update({"curiosity": 3.0, "pride": 1.0})
    world.entities["mason"].memes.update({"blase": 0.0, "respect": 1.0})

def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    generate_story(world)
    p = params
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f"Write an adventure about {p.hero}'s curiosity and {p.mason}, a blase mason, at {p.place}.",
            f"Include humor and suspense while they investigate a strange clue and find {p.treasure}.",
            "End with a concrete image showing how curiosity solved the mystery.",
        ],
        story_qa=[
            QAItem(
                f"What mission did {p.hero} begin at {p.place}?",
                f"{p.hero} went to {p.place} to {world.facts['mission']}.",
            ),
            QAItem(
                "What did the characters first think was happening?",
                f"They first thought {world.facts['mistaken']}, but that guess was wrong.",
            ),
            QAItem(
                "What clue helped solve the mystery?",
                f"They noticed that {world.facts['clue']} and tested it by {world.facts['test']}.",
            ),
            QAItem(
                "How did the adventure end?",
                f"They solved the problem because {world.facts['solution']}. In the end, {world.facts['ending']}.",
            ),
        ],
        world_qa=[
            QAItem("What is curiosity?", "Curiosity is the wish to learn or discover something by asking questions and looking closely."),
            QAItem("What does blase mean?", "Blase means acting unimpressed or unsurprised, even when something may be exciting."),
            QAItem("What does a mason do?", "A mason builds or repairs structures with materials such as bricks and stone."),
        ],
        world=world,
    )

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: {entity.label}; meters={entity.meters}; memes={entity.memes}"
        )
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)

def asp_facts() -> str:
    import asp
    lines = []
    for place in PLACES:
        lines.append(asp.fact("place", place))
    for treasure in TREASURES:
        lines.append(asp.fact("treasure", treasure))
    lines.extend([
        asp.fact("feature", "curiosity"),
        asp.fact("feature", "blase"),
        asp.fact("feature", "mason"),
        asp.fact("feature", "humor"),
        asp.fact("feature", "suspense"),
        asp.fact("style", "adventure"),
    ])
    return "\n".join(lines)

ASP_RULES = r"""
adventure(P,T) :- place(P), treasure(T), feature(curiosity), feature(mason).
humorous(P) :- place(P), feature(humor).
suspenseful(P) :- place(P), feature(suspense).
complete(P,T) :- adventure(P,T), humorous(P), suspenseful(P).
"""

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_verify() -> int:
    try:
        import asp
        model = asp.one_model(asp_program("#show adventure/2.\n#show humorous/1.\n#show suspenseful/1.\n#show complete/2."))
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    adventure = set(asp.atoms(model, "adventure"))
    humorous = set(asp.atoms(model, "humorous"))
    suspenseful = set(asp.atoms(model, "suspenseful"))
    complete = set(asp.atoms(model, "complete"))
    want_adventure = {(place, treasure) for place in PLACES for treasure in TREASURES}
    want_places = {(place,) for place in PLACES}
    ok = (
        adventure == want_adventure
        and humorous == want_places
        and suspenseful == want_places
        and complete == want_adventure
    )
    if not ok:
        print("Mismatch between ASP and Python registries.")
        return 1
    for params in [
        StoryParams("Luna", "Bram", PLACES[0], TREASURES[0]),
        StoryParams("Milo", "Ari", PLACES[1], TREASURES[1]),
    ]:
        sample = generate(params)
        if not sample.story or len(sample.story_qa) < 3:
            print("Generated story verification failed.")
            return 1
    print("OK: ASP parity and generated-story checks passed.")
    return 0

def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        for prompt in sample.prompts:
            print(f"P: {prompt}")
        for item in sample.story_qa + sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")

CURATED = [
    StoryParams("Luna", "Bram", "the ruined tower", "a brass compass"),
    StoryParams("Milo", "Mason Jo", "the ivy gate", "a blue glass marble"),
    StoryParams("Nia", "Ari", "the mossy bridge", "a tiny silver bell"),
]

def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show adventure/2.\n#show humorous/1.\n#show suspenseful/1.\n#show complete/2."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show adventure/2.\n#show humorous/1.\n#show suspenseful/1.\n#show complete/2."))
        for name in ("adventure", "humorous", "suspenseful", "complete"):
            print(f"{name}={len(asp.atoms(model, name))}")
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1.")
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen = set()
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                samples.append(sample)
                seen.add(sample.story)

    if args.json:
        print(
            samples[0].to_json()
            if len(samples) == 1
            else json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False)
        )
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.hero} at {sample.params.place}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
