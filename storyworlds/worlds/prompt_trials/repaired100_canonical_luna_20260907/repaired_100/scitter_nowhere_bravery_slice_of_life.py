#!/usr/bin/env python3
"""
A small slice-of-life storyworld about Scitter, nowhere, and everyday bravery.
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

_repo_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_repo_root))
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "character"
    type: str = "person"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    id: str
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    setting: str
    hero_name: str
    helper_name: str
    seed: Optional[int] = None


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


SETTINGS = {
    "corner": Place(
        id="corner",
        name="the corner shop at the end of Willow Street",
        kind="shop",
        meters={"distance_to_home": 0.4, "shelter": 1.0},
        memes={"familiarity": 1.0},
    ),
    "laundromat": Place(
        id="laundromat",
        name="the small laundromat beside the bus stop",
        kind="laundromat",
        meters={"distance_to_home": 0.6, "shelter": 1.0},
        memes={"familiarity": 0.7},
    ),
    "library": Place(
        id="library",
        name="the neighborhood library on Maple Road",
        kind="library",
        meters={"distance_to_home": 0.8, "shelter": 1.0},
        memes={"familiarity": 0.8},
    ),
}

NAMES = ["Luna", "Mara", "Niko", "Tess", "Ari", "Jo", "Milo", "Pia"]

SCENES = [
    {
        "key": "missed_bus",
        "premise": "a sudden rain began just after the last bus pulled away",
        "worry": "the quiet street seemed to lead nowhere",
        "scitter": "A small scitter ran beneath the bench, making the ticket machine blink",
        "clue": "the scitter stopped beside a bright yellow path marker",
        "action": "followed the marker only as far as the covered crossing",
        "repair": "asked the shopkeeper to call home and waited under the awning",
        "ending": "the rain softened, and the yellow marker shone beside the safe way home",
        "lesson": "bravery can mean asking for help before a small worry grows",
    },
    {
        "key": "dark_hall",
        "premise": "the hallway light went out while a parcel had to be carried upstairs",
        "worry": "the dark made the familiar stairs feel like nowhere at all",
        "scitter": "a quick scitter moved over the welcome mat and nudged a dropped key",
        "clue": "the key belonged to the little lamp kept by the mailboxes",
        "action": "picked up the key and asked a neighbor to walk alongside",
        "repair": "turned on the lamp, carried the parcel slowly, and left the light where everyone could reach it",
        "ending": "the hallway glowed softly while the parcel rested safely outside the right door",
        "lesson": "bravery can be taking one careful step with a friend",
    },
    {
        "key": "wrong_room",
        "premise": "a community music practice ended with one room still unlocked",
        "worry": "the empty room felt like nowhere to belong",
        "scitter": "a gentle scitter crossed the floor and stopped beside a paper sign",
        "clue": "the sign said that the quiet reading group met in the next room",
        "action": "read the sign aloud and knocked before entering",
        "repair": "joined the reading group for five minutes, then returned to find the music friends",
        "ending": "a borrowed book sat beside the music case, proving that the wrong room could still lead somewhere kind",
        "lesson": "bravery can be admitting you are unsure and checking instead of pretending",
    },
    {
        "key": "lost_glove",
        "premise": "one warm glove disappeared during a walk to collect bread",
        "worry": "the cold pavement made the walk home seem to stretch toward nowhere",
        "scitter": "a tiny scitter slipped beneath a newspaper box",
        "clue": "the glove's red thread showed between two dry leaves",
        "action": "stood still, asked a passerby to watch the bag, and reached carefully",
        "repair": "retrieved the glove without climbing into the box and thanked the passerby",
        "ending": "both gloves warmed the hands on the way home, with the red thread mended at the thumb",
        "lesson": "bravery is not rushing; it is choosing a safe way through a problem",
    },
]

OPENINGS = [
    "On an ordinary Tuesday afternoon,",
    "Just before dinner,",
    "After the kettle clicked off,",
    "Near the end of a small, busy day,",
    "While the neighborhood was settling down,",
]

CONCERNS = [
    "I do not know where to go next",
    "This feels bigger than I expected",
    "Can we stop and look before we move",
    "I am worried that I will make it worse",
]

RESPONSES = [
    "You do not have to solve it alone",
    "Let us take one safe step",
    "We can ask someone who knows",
    "Being scared does not mean we have to hurry",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A slice-of-life storyworld about everyday bravery.")
    parser.add_argument("--setting", choices=SETTINGS.keys())
    parser.add_argument("--name")
    parser.add_argument("--helper")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    hero_name = args.name or rng.choice(NAMES)
    helper_name = args.helper or rng.choice([name for name in NAMES if name != hero_name])
    if hero_name == helper_name:
        raise StoryError("The hero and helper must have different names.")
    return StoryParams(setting=setting, hero_name=hero_name, helper_name=helper_name)


def tell(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.hero_name == params.helper_name:
        raise StoryError("The hero and helper must have different names.")

    template = SETTINGS[params.setting]
    place = Place(
        id=template.id,
        name=template.name,
        kind=template.kind,
        meters=dict(template.meters),
        memes=dict(template.memes),
    )
    world = World(place=place)
    hero = world.add(Entity(
        id=params.hero_name,
        type="child",
        label="the person learning to be brave",
        meters={"confidence": 0.3, "distance_walked": 0.0},
        memes={"worry": 1.0, "bravery": 0.0},
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        type="neighbor",
        label="a patient helper",
        meters={"confidence": 0.8},
        memes={"patience": 1.0, "bravery": 0.5},
    ))

    rng = random.Random(params.seed if params.seed is not None else 0)
    scene = rng.choice(SCENES)
    opening = rng.choice(OPENINGS)
    concern = rng.choice(CONCERNS)
    response = rng.choice(RESPONSES)

    world.say(
        f"{opening} {hero.id} was walking near {world.place.name}, carrying an ordinary bag "
        f"and thinking about getting home."
    )
    world.say(f"Then {scene['premise']}. {scene['worry'].capitalize()}.")
    world.para()

    world.say(f"{scene['scitter']}. {hero.id} stopped instead of hurrying.")
    world.say(f"'{concern},' {hero.id} said.")
    world.say(f"'{response},' {helper.id} answered, arriving with an umbrella.")
    world.say(
        f"Together they noticed that {scene['clue']}. The little scitter vanished beneath "
        f"the nearest step, but it had helped them look closely."
    )
    world.para()

    world.say(f"{hero.id} took a slow breath and {scene['action']}.")
    world.say(f"{helper.id} stayed close without taking over.")
    world.say(
        f"After that, they {scene['repair']}. {hero.id} was still uneasy, but the worry "
        f"had become a plan."
    )
    world.para()

    hero.meters["confidence"] = 1.0
    hero.meters["distance_walked"] = 1.0
    hero.memes["worry"] = 0.2
    hero.memes["bravery"] = 1.0
    helper.memes["patience"] = 1.2
    world.say(
        f"{hero.id} learned that {scene['lesson']}. Bravery did not erase the ordinary "
        f"feeling of fear; it helped {hero.id} choose the next useful action."
    )
    world.say(f"At the end, {scene['ending']}.")

    world.facts.update(
        hero=hero,
        helper=helper,
        scene=scene,
        opening=opening,
        concern=concern,
        response=response,
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
    scene = world.facts["scene"]
    return [
        f"Write a slice-of-life story in which {scene['premise']}.",
        f"Tell a gentle story about {world.facts['hero'].id} finding bravery through an ordinary problem.",
        f"Include a scitter, the feeling of nowhere, and a helpful conversation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    scene = world.facts["scene"]
    return [
        QAItem(
            question=f"What problem did {hero.id} face?",
            answer=f"{scene['premise'].capitalize()} The situation made {scene['worry']}.",
        ),
        QAItem(
            question="What did the scitter help the characters notice?",
            answer=f"The scitter helped them slow down and notice that {scene['clue']}.",
        ),
        QAItem(
            question=f"How did {helper.id} help {hero.id}?",
            answer=f"{helper.id} listened, stayed close, and helped {hero.id} {scene['action']}.",
        ),
        QAItem(
            question=f"What brave choice did {hero.id} make?",
            answer=f"{hero.id} chose a careful action instead of rushing: {scene['action'].capitalize()}.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer=f"{scene['ending'].capitalize()} The ending showed that the problem had become manageable and that bravery had guided a safe choice.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a scitter?",
            answer="A scitter is a quick, light movement, often made by a small creature or something tiny moving across a surface.",
        ),
        QAItem(
            question="What does nowhere mean?",
            answer="Nowhere means no particular place. In the story, feeling nowhere described uncertainty, not a permanent lack of home.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery is doing a careful, worthwhile thing even when you feel afraid or unsure.",
        ),
        QAItem(
            question="Why can asking for help be brave?",
            answer="Asking for help can be brave because it admits what you need and makes room for a safer, wiser choice.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"- {prompt}" for prompt in sample.prompts)
    lines.append("\n== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("\n== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---", f"place={world.place.name}"]
    for entity in world.entities.values():
        lines.append(f"{entity.id}: meters={entity.meters} memes={entity.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(corner).
setting(laundromat).
setting(library).
feature(scitter).
feature(nowhere).
feature(bravery).
style(slice_of_life).
has_feature(S) :- setting(S), feature(scitter), feature(nowhere), feature(bravery).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join([
        asp.fact("setting", "corner"),
        asp.fact("setting", "laundromat"),
        asp.fact("setting", "library"),
        asp.fact("feature", "scitter"),
        asp.fact("feature", "nowhere"),
        asp.fact("feature", "bravery"),
        asp.fact("style", "slice_of_life"),
    ])


def asp_program(show: str = "#show feature/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show feature/1."))
    features = set(asp.atoms(model, "feature"))
    expected = {("scitter",), ("nowhere",), ("bravery",)}
    if features != expected:
        print(f"Mismatch in ASP features: got {features!r}, expected {expected!r}.")
        return 1

    params = StoryParams(setting="corner", hero_name="Luna", helper_name="Mara", seed=17)
    sample = generate(params)
    required = ["scitter", "nowhere", "bravery", "Luna", "Mara"]
    if not all(word.lower() in sample.story.lower() for word in required):
        print("Generated story failed required narrative checks.")
        return 1
    print("OK: ASP/Python parity and generated-story checks passed.")
    return 0


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show feature/1."))
        print(sorted(set(asp.atoms(model, "feature"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, setting in enumerate(SETTINGS):
            params = StoryParams(
                setting=setting,
                hero_name=NAMES[index],
                helper_name=NAMES[index + 1],
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 20):
            rng = random.Random(base_seed + attempt)
            attempt += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + attempt
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if not samples:
        raise StoryError("No stories were generated.")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
