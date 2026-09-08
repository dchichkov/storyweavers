#!/usr/bin/env python3
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
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    id: str
    label: str


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass(frozen=True)
class Adventure:
    key: str
    food: str
    danger: str
    twist: str
    repair: str
    ending: str
    opening: tuple[str, str]
    trouble: tuple[str, str]
    reveal: tuple[str, str]
    reconciliation: tuple[str, str]
    finale: tuple[str, str]


ADVENTURES = (
    Adventure(
        "skyship",
        "a sizzling bacon breakfast",
        "a smoky cloud monster stealing the town's morning smells",
        "the monster was lonely and had been following the heroes' cooking scent",
        "Captain Comet shared the bacon and asked the cloud to guard the kitchen chimney",
        "the cloud became a friendly silver shield above the town",
        (
            "At {place}, Captain Comet flipped bacon while Nova watched the sunrise.",
            "Their breakfast powered the Bright Beacon, the town's most important light.",
        ),
        (
            "Suddenly, a smoky cloud monster swooped down and swallowed the bacon smell.",
            '"I will chase it away!" cried Nova. "Wait," said Captain Comet. "Let us learn why."',
        ),
        (
            "Behind the cloud's dark curls, they found one tiny, trembling spark.",
            '"I did not want to frighten anyone," whispered the cloud. "I only wanted a warm friend."',
        ),
        (
            '"We are sorry we called you a monster," said Nova. "Help us protect the beacon."',
            "Captain Comet shared the bacon, and the cloud promised to remove the smoke from the sky.",
        ),
        (
            "The cloud curled around the beacon like a cape and kept the morning air clear.",
            "Below, everyone cheered as the heroes and their new friend watched the sun rise.",
        ),
    ),
    Adventure(
        "rooftop",
        "a pan of crispy bacon",
        "a gust-powered villain blowing breakfast off the rooftop",
        "the villain was a homesick wind who missed the mountain trees",
        "the heroes invited the wind to carry clean music instead of stealing food",
        "the wind returned the bacon and became the city's joyful bell ringer",
        (
            "On the rooftop of {place}, Solar Scout cooked bacon for the neighborhood.",
            "The smell curled through the chimneys like a tasty signal flare.",
        ),
        (
            "A wild gust blasted across the roof and swept the pan toward the edge.",
            '"Stop!" shouted Solar Scout. "Do not remove our breakfast!"',
        ),
        (
            "The gust slowed beside an old weather vane and spoke in a whisper.",
            '"I am not wicked," it said. "I am lonely for the high mountain trees."',
        ),
        (
            '"Then carry our music," said Solar Scout. "We will listen to your mountain song."',
            "They shared the bacon, and the wind agreed to remove only dangerous smoke.",
        ),
        (
            "The wind spun the weather vane and rang every rooftop bell in tune.",
            "The heroes waved from the roof while their new friend danced through the blue sky.",
        ),
    ),
    Adventure(
        "subway",
        "a basket of bacon sandwiches",
        "a shadow creature hiding the station's lost-and-found box",
        "the shadow was protecting a frightened kitten inside the box",
        "the heroes promised a quiet rescue and gave the shadow a safe job",
        "the shadow became the station's gentle night guardian",
        (
            "Under {place}, Metro Star packed bacon sandwiches for the night workers.",
            "Then every lost mitten and umbrella began to vanish from the platform.",
        ),
        (
            "A long shadow stretched across the tracks and tried to remove the lost-and-found box.",
            '"You cannot take that!" said Metro Star. "Please tell us what is wrong."',
        ),
        (
            "The shadow opened one corner of the box, and a tiny kitten peeked out.",
            '"I was hiding her from the loud trains," it said. "I thought nobody would help."',
        ),
        (
            '"You protected her," said Metro Star. "Now let us protect both of you."',
            "They shared a bacon sandwich, and the shadow agreed to return the missing things.",
        ),
        (
            "The kitten found a warm home, and the shadow watched the quiet platform.",
            "From then on, the night guardian kept every traveler safe beneath the city.",
        ),
    ),
    Adventure(
        "harbor",
        "a bacon picnic",
        "a giant tide of blue foam covering the harbor path",
        "the foam was made by a young sea dragon practicing bubbles",
        "the heroes taught the dragon to remove foam from the walking path",
        "the sea dragon became the harbor's cheerful rescue helper",
        (
            "By {place}, Harbor Hero packed bacon for a picnic beside the boats.",
            "The water glittered, and gulls swooped around the sunny pier.",
        ),
        (
            "A blue foam wave rolled over the path and hid the picnic basket.",
            '"We must remove this foam," said Harbor Hero. "But first, who made it?"',
        ),
        (
            "A small sea dragon rose beside the dock with bubbles on its nose.",
            '"I am sorry," it said. "I was practicing, and I cannot stop."',
        ),
        (
            '"We can practice together," said Harbor Hero. "Bubbles belong over the water."',
            "They shared the bacon, and the dragon learned to clear the path gently.",
        ),
        (
            "The dragon swept the last foam into the sea and guided a lost boat home.",
            "The hero saluted as their new friend sparkled proudly beside the harbor.",
        ),
    ),
)


@dataclass
class StoryParams:
    place: str
    hero_name: str
    partner_name: str
    hero_title: str = "Captain Comet"
    partner_title: str = "Nova"
    seed: Optional[int] = None


PLACES = {
    "beacon_tower": Place("beacon_tower", "the Beacon Tower"),
    "rooftop": Place("rooftop", "the Star Rooftop"),
    "subway": Place("subway", "the Moonline Station"),
    "harbor": Place("harbor", "the Spark Harbor"),
}

NAMES = ["Ari", "Mika", "Rae", "Jo", "Tess", "Kai"]
TITLES = ["Captain Comet", "Nova", "Solar Scout", "Metro Star", "Harbor Hero"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    hero = args.hero or rng.choice(NAMES)
    partner = args.partner or rng.choice([n for n in NAMES if n != hero])
    title = args.title or rng.choice(TITLES)
    partner_title = args.partner_title or rng.choice([t for t in TITLES if t != title])
    return StoryParams(place, hero, partner, title, partner_title, args.seed)


def tell(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}.")
    if params.hero_name == params.partner_name:
        raise StoryError("The two heroes must have different names.")
    if not params.hero_name.strip() or not params.partner_name.strip():
        raise StoryError("Hero names cannot be empty.")

    rng = random.Random(params.seed if params.seed is not None else sum(map(ord, params.place + params.hero_name)))
    adventure = ADVENTURES[rng.randrange(len(ADVENTURES))]
    world = World(PLACES[params.place])

    hero = world.add(Entity("hero", "character", params.hero_name, "hero"))
    partner = world.add(Entity("partner", "character", params.partner_name, "partner"))
    bacon = world.add(Entity("bacon", "food", adventure.food, "shared_food"))
    foe = world.add(Entity("foe", "creature", adventure.danger, "misunderstood_friend"))

    values = {
        "place": world.place.label,
        "hero": params.hero_title,
        "partner": params.partner_title,
    }

    for line in adventure.opening:
        world.say(line.format(**values))
    world.para()

    hero.memes["bravery"] = 1
    partner.memes["curiosity"] = 1
    foe.meters["danger"] = 1
    for line in adventure.trouble:
        world.say(line.format(**values))
    world.para()

    foe.meters["danger"] = 0
    foe.memes["loneliness"] = 1
    hero.memes["understanding"] = 1
    partner.memes["understanding"] = 1
    for line in adventure.reveal:
        world.say(line.format(**values))
    world.para()

    bacon.meters["shared"] = 1
    foe.meters["danger"] = 0
    foe.memes["friendship"] = 1
    for line in adventure.reconciliation:
        world.say(line.format(**values))
    world.para()

    foe.meters["helping"] = 1
    hero.memes["hope"] = 1
    partner.memes["hope"] = 1
    for line in adventure.finale:
        world.say(line.format(**values))

    world.facts.update(
        hero=params.hero_title,
        partner=params.partner_title,
        hero_name=params.hero_name,
        partner_name=params.partner_name,
        food=adventure.food,
        danger=adventure.danger,
        twist=adventure.twist,
        repair=adventure.repair,
        ending=adventure.ending,
        adventure=adventure.key,
        reconciled=True,
        bacon_shared=True,
        danger_removed=True,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    f = world.facts
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            "Write a child-friendly superhero story that includes bacon and the word remove.",
            f"Tell a superhero story in which {f['hero']} and {f['partner']} discover that {f['danger']} has a surprising reason.",
            f"Write a story with a twist and reconciliation: the heroes learn that {f['twist']}.",
        ],
        story_qa=[
            QAItem(
                "What danger did the heroes face?",
                f"The heroes faced {f['danger']}. They first thought it was a threat because it put their food or their town in danger."
            ),
            QAItem(
                "What was the twist?",
                f"The twist was that {f['twist']}. Learning this changed the heroes' choice from fighting to helping."
            ),
            QAItem(
                "How did reconciliation solve the problem?",
                f"The heroes reconciled by apologizing, sharing bacon, and agreeing to help. Then {f['repair']}, so the danger was removed."
            ),
            QAItem(
                "What showed that everything had changed?",
                f"The final image showed the new friendship clearly: {f['ending']}."
            ),
        ],
        world_qa=[
            QAItem(
                "Why can a superhero choose understanding instead of fighting?",
                "A superhero can choose understanding because learning the truth may reveal a safe way to solve the problem and help everyone."
            ),
            QAItem(
                "What does reconciliation mean?",
                "Reconciliation means making peace after a disagreement by listening, apologizing, and finding a caring way forward."
            ),
        ],
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"{entity.id}: type={entity.kind}, meters={meters}, memes={memes}")
    lines.append(f"facts: {world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
danger_removed :- danger_present, listened, reconciled, shared_food.
reconciled :- twist_understood, apology.
helper_friend :- reconciled, shared_food.
outcome(friendship) :- helper_friend.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("danger_present"),
            asp.fact("listened"),
            asp.fact("twist_understood"),
            asp.fact("apology"),
            asp.fact("shared_food"),
        ]
    )


def asp_program(show: str = "#show outcome/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    try:
        model = asp.one_model(asp_program())
        if not asp.atoms(model, "outcome"):
            print("ASP parity failed: no friendship outcome.")
            return 1
        sample = generate(
            StoryParams(
                place="beacon_tower",
                hero_name="Ari",
                partner_name="Mika",
                seed=7,
            )
        )
        if not sample.story.strip() or "bacon" not in sample.story.lower():
            print("Generation smoke test failed.")
            return 1
    except Exception as exc:
        print(f"Verification failed: {exc}")
        return 1
    print("OK: Python and ASP smoke tests passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A superhero storyworld about bacon, a twist, and reconciliation.")
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--hero")
    parser.add_argument("--partner")
    parser.add_argument("--title")
    parser.add_argument("--partner-title")
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


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print(asp.atoms(model, "outcome"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, place in enumerate(PLACES):
            params = StoryParams(
                place=place,
                hero_name=NAMES[i % len(NAMES)],
                partner_name=NAMES[(i + 1) % len(NAMES)],
                hero_title=TITLES[i % len(TITLES)],
                partner_title=TITLES[(i + 1) % len(TITLES)],
                seed=base_seed + i,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        for i in range(max(args.n, 1) * 20):
            if len(samples) >= max(args.n, 1):
                break
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {i + 1}" if len(samples) > 1 else "",
        )
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
