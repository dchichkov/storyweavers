#!/usr/bin/env python3
"""
A tall-tale story world about digestion and one very noisy supper.

Luna eats a mountain-sized pancake, learns that digestion takes time, and
follows the comic sound effects through a small simulated adventure.
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
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("hunger", "fullness", "energy", "rumble", "comfort", "worry"):
            self.meters.setdefault(key, 0.0)
        for key in ("patience", "pride", "curiosity", "care"):
            self.memes.setdefault(key, 0.0)


@dataclass
class StoryParams:
    hero: str
    feast: str = "a pancake as wide as a wagon wheel"
    style: str = "tall_tale"
    sound_effects: bool = True
    seed: Optional[int] = None
    variation: int = 0


@dataclass(frozen=True)
class Feast:
    name: str
    size: str
    taste: str
    first_sound: str
    middle_sound: str
    final_sound: str
    consequence: str


FEASTS = [
    Feast(
        "a pancake as wide as a wagon wheel",
        "wagon-wide",
        "buttery and bright with berry jam",
        "FLAP-FLOP!",
        "GLOMP-GRUMBLE!",
        "PLOP!",
        "Luna's belly became so round that it could shade three hens.",
    ),
    Feast(
        "a pie as tall as the village water tower",
        "tower-tall",
        "warm with apples, cinnamon, and a brave pinch of pepper",
        "WHUMP!",
        "GURGLE-GAROO!",
        "PFFT!",
        "Luna's belly rolled downhill and rang the town bell by accident.",
    ),
    Feast(
        "a stack of dumplings higher than a hay barn",
        "barn-high",
        "steamy, savory, and sprinkled with chives",
        "PLOP-PLOP!",
        "BLORP-BLORP!",
        "TOOT!",
        "Luna's coat buttons flew off and landed in a farmer's soup.",
    ),
    Feast(
        "a noodle braid longer than the mayor's train",
        "train-long",
        "salty, slippery, and twirled with cheese",
        "SLURP-SNAP!",
        "WIGGLE-GURGLE!",
        "FWOOP!",
        "Luna's belly made a soft hill beneath the town's wandering goats.",
    ),
]

SOUND_MODES = [
    ("bold", "The sound effects were so loud that dust danced from the rafters."),
    ("whisper", "Even the quietest sound effects made the spoons tremble."),
    ("echo", "Every sound effect bounced from hill to hill before settling down."),
    ("drumroll", "The whole village beat a drum whenever Luna's belly spoke."),
]


class World:
    def __init__(self, params: StoryParams, feast: Feast, sound_mode: str) -> None:
        self.params = params
        self.feast = feast
        self.sound_mode = sound_mode
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, entity: Entity) -> None:
        self.entities[entity.id] = entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def setup_world(params: StoryParams, feast: Feast, sound_mode: str) -> World:
    world = World(params, feast, sound_mode)
    world.add(Entity(
        "hero", "character", params.hero, "village square",
        meters={"hunger": 7.0, "fullness": 0.0, "energy": 4.0, "rumble": 0.0, "comfort": 2.0, "worry": 0.0},
        memes={"patience": 1.0, "pride": 4.0, "curiosity": 3.0, "care": 1.0},
    ))
    world.add(Entity(
        "cook", "character", "Aunt Bramble", "village square",
        meters={"hunger": 2.0, "fullness": 0.0, "energy": 5.0, "rumble": 0.0, "comfort": 4.0, "worry": 1.0},
        memes={"patience": 5.0, "pride": 3.0, "curiosity": 2.0, "care": 6.0},
    ))
    world.add(Entity(
        "feast", "food", feast.name, "village square",
        meters={"hunger": 0.0, "fullness": 0.0, "energy": 0.0, "rumble": 0.0, "comfort": 0.0, "worry": 0.0},
        memes={"patience": 0.0, "pride": 0.0, "curiosity": 1.0, "care": 2.0},
    ))
    return world


def tell_story(world: World) -> None:
    hero = world.entities["hero"]
    cook = world.entities["cook"]
    feast = world.feast
    mode_text = dict(SOUND_MODES)[world.sound_mode]

    world.say(
        f"In the village of Big Little Things lived {hero.label}, who was famous for having "
        f"the hungriest appetite in seven counties."
    )
    world.say(
        f"One morning, Aunt Bramble cooked {feast.name}. It was {feast.size}, and its "
        f"{feast.taste} smell curled over the rooftops."
    )
    world.say(
        f'"That is breakfast, lunch, and perhaps tomorrow," said {hero.label}. '
        f'"It is only one bite," said Aunt Bramble, though she raised one doubtful eyebrow.'
    )
    if world.params.sound_effects:
        world.say(feast.first_sound)
    world.say(
        f"{hero.label} took the first bite, then the second, then a bite so enormous "
        f"that three sparrows mistook it for a thundercloud."
    )
    hero.meters["hunger"] = 0.0
    hero.meters["fullness"] = 9.0
    hero.meters["energy"] = 5.0
    hero.meters["rumble"] = 1.0
    hero.memes["pride"] += 2.0

    world.para()
    world.say(
        f"At once, {hero.label}'s digestion began its slow, busy work. The great meal "
        f"settled inside, where warm juices and tiny helpers broke it into useful energy."
    )
    world.say(
        f'"Why am I not ready to race the wind?" asked {hero.label}. '
        f'"Because digestion is a journey, not a magic button," said Aunt Bramble.'
    )
    world.say(mode_text)
    if world.params.sound_effects:
        world.say(f"{feast.middle_sound} The noise rolled under the table and woke a sleeping rooster.")
    hero.meters["fullness"] = 7.0
    hero.meters["rumble"] = 5.0
    hero.meters["energy"] = 6.0
    hero.meters["comfort"] = 1.0
    hero.meters["worry"] = 3.0
    hero.memes["patience"] += 2.0
    cook.memes["care"] += 1.0

    world.para()
    world.say(
        f"A loud rumble sent {hero.label} marching in a circle around the square. "
        f"The villagers followed, carrying napkins like flags."
    )
    world.say(
        f'"Should I panic?" cried {hero.label}. '
        f'"No," said Aunt Bramble. "Rest, sip water, and let your body do its clever work."'
    )
    world.say(
        f"{hero.label} sat beneath an elm, took small sips, and watched the clouds "
        f"while the meal traveled onward through digestion."
    )
    hero.meters["fullness"] = 3.0
    hero.meters["rumble"] = 1.0
    hero.meters["energy"] = 9.0
    hero.meters["comfort"] = 8.0
    hero.meters["worry"] = 0.0
    hero.memes["patience"] += 3.0
    hero.memes["care"] += 2.0

    world.para()
    if world.params.sound_effects:
        world.say(f"{feast.final_sound} The last little bubble popped like a cheerful button.")
    world.say(
        f"At last, {hero.label} sprang up, light enough to leap over a puddle but wise "
        f"enough not to swallow a whole bakery."
    )
    world.say(feast.consequence)
    world.say(
        f'"What did you learn?" asked Aunt Bramble. '
        f'"A big meal needs time, water, and patience," said {hero.label}. '
        f'"And perhaps a smaller second bite."'
    )
    world.say(
        "From that day on, the villagers called the rumble a warning bell, not a monster. "
        "Whenever it rang, everyone paused, breathed, and let digestion finish its work."
    )

    world.facts.update(
        hero=hero,
        cook=cook,
        feast=feast,
        sound_mode=world.sound_mode,
        lesson="Digestion takes time, and patience, water, and rest help the body use food.",
        ending=feast.consequence,
    )


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    feast: Feast = world.facts["feast"]
    return [
        QAItem(
            "Who ate the enormous meal?",
            f"{hero.label} ate the enormous meal.",
        ),
        QAItem(
            "What did the meal look like?",
            f"It was {feast.name}, and it was {feast.size}.",
        ),
        QAItem(
            "What problem did the meal cause at first?",
            f"{hero.label} felt very full, and their belly rumbled while digestion began.",
        ),
        QAItem(
            "What did Aunt Bramble tell the hero to do?",
            f"Aunt Bramble said to rest, sip water, and let digestion do its work.",
        ),
        QAItem(
            "What happened after the meal finished digesting?",
            f"{hero.label} felt comfortable and energetic again, but remembered to eat more patiently.",
        ),
        QAItem(
            "What lesson did the hero learn?",
            world.facts["lesson"],
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is digestion?",
            "Digestion is the body's process of breaking food into smaller parts that can provide useful energy.",
        ),
        QAItem(
            "Why can someone feel full after eating a lot?",
            "A large meal fills the stomach, so the body may need time before the person feels comfortable again.",
        ),
        QAItem(
            "Why are sound effects useful in a tall tale?",
            "Sound effects make enormous and funny events feel vivid, playful, and easy to imagine.",
        ),
    ]


def generation_prompts() -> list[str]:
    return [
        "Write a child-friendly tall tale about digestion with exaggerated food and comic sound effects.",
        "Tell a tall tale in which a huge meal causes a noisy but harmless digestion adventure.",
        "Use sound effects and dialogue to show why digestion takes patience.",
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Tall-tale story world about digestion and sound effects."
    )
    parser.add_argument("--hero")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(["Luna", "Mabel", "Toby", "Nell", "Otis"])
    if not hero.strip():
        raise StoryError("The hero's name cannot be empty.")
    if any(ch.isdigit() for ch in hero):
        raise StoryError("The hero's name must be a readable name, not a number.")
    return StoryParams(
        hero=hero,
        seed=args.seed,
        variation=rng.getrandbits(63),
    )


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.variation)
    feast = rng.choice(FEASTS)
    sound_mode = rng.choice([item[0] for item in SOUND_MODES])
    world = setup_world(params, feast, sound_mode)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


ASP_RULES = r"""
child(hero).
food(giant_meal).
eats(hero, giant_meal).
digestion_begins(hero) :- eats(hero, giant_meal).
needs_time(hero) :- digestion_begins(hero).
feels_better(hero) :- needs_time(hero), rests(hero), drinks_water(hero).
lesson(patience) :- feels_better(hero).
#show digestion_begins/1.
#show needs_time/1.
#show feels_better/1.
#show lesson/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("child", "hero"),
        asp.fact("food", "giant_meal"),
        asp.fact("eats", "hero", "giant_meal"),
        asp.fact("rests", "hero"),
        asp.fact("drinks_water", "hero"),
    ])


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
        model = asp.one_model(asp_program())
    except Exception as exc:
        print(f"ASP verification unavailable: {exc}")
        return 1
    names = {symbol.name for symbol in model}
    expected = {"digestion_begins", "needs_time", "feels_better", "lesson"}
    if expected.issubset(names):
        sample = generate(StoryParams("Luna", variation=17))
        if "digestion" in sample.story.lower() and "patience" in sample.story.lower():
            print("OK: Python and ASP digestion paths agree.")
            return 0
    print("MISMATCH: digestion parity check failed.")
    return 1


CURATED = [
    StoryParams("Luna", feast="a pancake as wide as a wagon wheel", variation=11),
    StoryParams("Mabel", feast="a pie as tall as the village water tower", variation=22),
    StoryParams("Toby", feast="a stack of dumplings higher than a hay barn", variation=33),
]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        lines.append(
            f"{entity.label}: location={entity.location}; meters={meters}; memes={memes}"
        )
    return "\n".join(lines)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show digestion_begins/1."))
        return
    if args.verify:
        raise SystemExit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        for index in range(max(1, args.n)):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        print(sample.story)
        if args.trace and sample.world is not None:
            print(dump_trace(sample.world))
        if args.qa:
            print()
            print(format_qa(sample))
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
