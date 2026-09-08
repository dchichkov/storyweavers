#!/usr/bin/env python3
"""A gentle fairy tale about a brittle moon token and a remembered promise."""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import hashlib
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Scene:
    place: str
    weather: str
    light: str


@dataclass
class StoryParams:
    place: str
    token: str
    name: str
    helper: str
    promise: str = ""
    route: str = ""
    seed: Optional[int] = None


@dataclass(frozen=True)
class Tale:
    missing: str
    danger: str
    flashback: str
    discovery: str
    repair: str
    lesson: str
    ending: str


PLACES = {
    "bell_tower": Scene("the old bell tower", "a silver wind", "a pale moon"),
    "thorn_garden": Scene("the thorn garden", "a warm night breeze", "a round moon"),
    "river_bridge": Scene("the moonlit bridge", "a whispering mist", "a bright moon"),
}

TOKENS = {
    "silver": "a brittle silver token stamped with a crescent moon",
    "glass": "a brittle glass token that held a tiny moon inside",
    "pearl": "a brittle pearl token marked with three moonbeams",
}

FRIENDS = {"Anya": "girl", "Bram": "boy", "Cora": "girl", "Dain": "boy"}

TALES = {
    "silver": Tale(
        "the silver token that opened the moon gate",
        "the token had cracked near the sleeping queen's door",
        "Long ago, the queen had told Anya, 'A promise is strongest when it is carried gently.'",
        "a thread of moonlight still joined the two pieces beneath the gate",
        "wrapped the pieces in velvet and asked the moon smith to mend them with soft silver",
        "Brittle things and tender promises both need careful hands",
        "the repaired token shone in the queen's palm as the moon gate opened",
    ),
    "glass": Tale(
        "the glass token that guided lost travelers",
        "the token had vanished during a storm",
        "Once, the old owl had warned Bram, 'Follow the quiet light, not the loudest sound.'",
        "rainwater had carried the token into a hollow reed beside the bridge",
        "lifted the reed, dried the token with linen, and placed a small guard around it",
        "A calm search can hear what panic misses",
        "the glass moon glimmered beside the road and guided every traveler home",
    ),
    "pearl": Tale(
        "the pearl token that called the moon deer",
        "the token had fallen from the princess's crown",
        "Years before, Cora had promised her grandmother, 'I will return what belongs to the night.'",
        "three pale marks led from the crown to a nest beneath the garden roses",
        "carried the token back in a leaf-lined basket and tied the crown with a safer ribbon",
        "Returning what is borrowed restores more than an object",
        "the moon deer bowed beneath the roses when the pearl token returned",
    ),
}

ROUTES = ("flashback_first", "garden_first", "dialogue_first", "moon_first", "clue_first")


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy tale about a brittle moon token.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--token", choices=sorted(TOKENS))
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=sorted(FRIENDS))
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        ap.add_argument(f"--{flag}", action="store_true")
    return ap


def valid_combos() -> list[tuple[str, str]]:
    return [(place, token) for place in sorted(PLACES) for token in sorted(TOKENS)]


ASP_RULES = """
valid(Place, Token) :- place(Place), token(Token).
moon_token(Token) :- token(Token).
reasonable(Place, Token) :- valid(Place, Token), moon_token(Token).
#show valid/2.
#show reasonable/2.
""".strip()


def asp_facts() -> str:
    import asp
    facts = [asp.fact("place", place) for place in PLACES]
    facts.extend(asp.fact("token", token) for token in TOKENS)
    return "\n".join(facts)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    symbols = asp.one_model(asp_program())
    return sorted(set(asp.atoms(symbols, "valid")))


def asp_verify() -> int:
    expected = set(valid_combos())
    actual = set(asp_valid_combos())
    if expected == actual:
        print(f"OK: clingo gate matches valid_combos() ({len(expected)} combos).")
        return 0
    print("MISMATCH:", sorted(expected - actual), sorted(actual - expected))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        combo for combo in valid_combos()
        if not args.place or combo[0] == args.place
        if not args.token or combo[1] == args.token
    ]
    if not combos:
        raise StoryError("No valid fairy tale fits those moon-token options.")
    place, token = rng.choice(combos)
    name = args.name or "Luna"
    if name == args.helper:
        raise StoryError("The moon child and helper must have different names.")
    choices = [person for person in sorted(FRIENDS) if person != name]
    helper = args.helper or rng.choice(choices)
    return StoryParams(
        place=place,
        token=token,
        name=name,
        helper=helper,
        promise=rng.choice(sorted(TALES)),
        route=rng.choice(ROUTES),
    )


def story_rng(params: StoryParams) -> random.Random:
    text = "|".join(
        str(value)
        for value in (
            params.seed,
            params.place,
            params.token,
            params.name,
            params.helper,
            params.promise,
            params.route,
        )
    )
    return random.Random(int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big"))


def tell(params: StoryParams) -> World:
    scene = PLACES[params.place]
    tale = TALES[params.promise]
    rng = story_rng(params)
    world = World(scene)
    hero = world.add(
        Entity(
            id=params.name,
            kind="character",
            type="girl",
            memes={"courage": 0.3, "care": 0.4},
        )
    )
    helper = world.add(
        Entity(
            id=params.helper,
            kind="character",
            type=FRIENDS[params.helper],
            memes={"patience": 0.4},
        )
    )
    token = world.add(
        Entity(
            id="moon_token",
            kind="artifact",
            type="brittle_token",
            label=TOKENS[params.token],
            meters={"integrity": 0.35, "distance_to_home": 4.0},
            memes={"belonging": 1.0},
        )
    )

    openings = {
        "flashback_first": (
            f"Before the moon rose over {scene.place}, {hero.id} remembered a promise. "
            f"{tale.flashback} That memory mattered because {tale.missing} was missing."
        ),
        "garden_first": (
            f"At {scene.place}, beneath {scene.light}, {hero.id} found a velvet mark in the dust. "
            f"It belonged to {tale.missing}, which had vanished before the night bell."
        ),
        "dialogue_first": (
            f'"Something is wrong," {hero.id} said at {scene.place}. '
            f"{tale.missing.capitalize()} had disappeared while {scene.weather} moved through the stones."
        ),
        "moon_first": (
            f"The moon climbed above {scene.place}, but its light looked worried. "
            f"{hero.id} soon learned that {tale.missing} had gone missing."
        ),
        "clue_first": (
            f"A pale trail crossed {scene.place}. {hero.id} followed it and discovered that "
            f"{tale.missing} was gone, leaving only a small mark behind."
        ),
    }
    world.say(openings[params.route])
    world.say(
        rng.choice(
            [
                f"{params.helper} hurried to {hero.id}'s side, carrying a lantern.",
                f"{hero.id} asked {params.helper} to help before anyone stepped on the moonlit trail.",
                f"Together, {hero.id} and {params.helper} promised to search slowly.",
            ]
        )
    )
    world.para()

    world.say(f"The danger was clear: {tale.danger}.")
    world.say(
        rng.choice(
            [
                f'"We must not grab it if we find it," {params.helper} warned. "A brittle token may break."',
                f'"Let us use soft cloth," {hero.id} replied. "The moon trusted us with its token."',
                f'{params.helper} pointed to the dark path. "Careful steps will take us farther than frightened ones."',
            ]
        )
    )
    world.say(
        f"{hero.id} remembered the old words again: {tale.flashback}"
    )
    hero.memes["courage"] = 0.8
    helper.memes["patience"] = 0.9
    world.para()

    world.say(f"At last, they discovered that {tale.discovery}.")
    world.say(
        rng.choice(
            [
                f"{hero.id} reached for a ribbon, while {params.helper} held the lantern low.",
                f"They tested the ground with a willow twig before touching the hidden token.",
                f"The children worked as one: {hero.id} guarded the moonlight and {params.helper} cleared the path.",
            ]
        )
    )
    world.say(
        f'"I know what to do now," {hero.id} said. "We can bring it home without making it worse."'
    )
    world.say(
        f'"Then we will do it together," {params.helper} answered.'
    )
    world.para()

    world.say(f"They {tale.repair}.")
    token.meters["integrity"] = 1.0
    token.meters["distance_to_home"] = 0.0
    hero.memes["care"] = 1.0
    world.say(
        rng.choice(
            [
                f"The moon brightened when {hero.id} returned {tale.missing}.",
                f"{params.helper} smiled as the fragile token rested safely in its velvet place.",
                f"The night grew quiet, as if the stars had been holding their breath.",
            ]
        )
    )
    world.say(f"{hero.id} carried the lesson in their heart: {tale.lesson}.")
    world.say(f"At dawn, {tale.ending}.")
    world.facts.update(
        hero=hero,
        helper=helper,
        token=token,
        scene=scene,
        tale=tale,
        token_description=TOKENS[params.token],
    )
    return world


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    tale = facts["tale"]
    hero = facts["hero"]
    return [
        f"Write a fairy tale for a young child about {hero.id}, the moon, and {facts['token_description']}.",
        f"Tell a story with a flashback in which {hero.id} remembers: {tale.flashback}",
        f"Write a gentle tale showing that {tale.lesson}, ending with {tale.ending}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    tale = facts["tale"]
    hero = facts["hero"]
    helper = facts["helper"]
    return [
        QAItem(
            question=f"What was missing when {hero.id} began searching at {facts['scene'].place}?",
            answer=f"{tale.missing.capitalize()} was missing from {facts['scene'].place}.",
        ),
        QAItem(
            question=f"What did {hero.id} remember in the flashback?",
            answer=f"{hero.id} remembered these words: {tale.flashback}",
        ),
        QAItem(
            question=f"Why did {hero.id} and {helper.id} handle the token carefully?",
            answer=f"They handled it carefully because {tale.danger}. The token was brittle and could break.",
        ),
        QAItem(
            question=f"How did the children find the moon token?",
            answer=f"They discovered that {tale.discovery}. This clue showed them where to search.",
        ),
        QAItem(
            question=f"How did {hero.id} and {helper.id} solve the problem?",
            answer=f"They {tale.repair}. The moon token returned safely to its proper place.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why should someone handle a brittle object gently?",
            answer="A brittle object can crack or break under a sudden squeeze, bump, or drop, so gentle hands help protect it.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of a story that briefly returns to an earlier event or memory so the past can explain the present.",
        ),
        QAItem(
            question="Why can a token be important in a fairy tale?",
            answer="A token can stand for a promise, belonging, or responsibility, so returning it may repair trust as well as solve a problem.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = [
        "== prompts ==",
        *(f"{index}. {prompt}" for index, prompt in enumerate(sample.prompts, 1)),
        "",
        "== story qa ==",
    ]
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.extend(("", "== world qa =="))
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id} ({entity.kind}/{entity.type}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  place={world.scene.place}")
    lines.append(f"  ending={world.facts['tale'].ending}")
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
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print("\n" + format_qa(sample))


CURATED = [
    StoryParams(
        place="bell_tower",
        token="silver",
        name="Luna",
        helper="Bram",
        promise="silver",
        route="flashback_first",
        seed=101,
    ),
    StoryParams(
        place="thorn_garden",
        token="pearl",
        name="Luna",
        helper="Cora",
        promise="pearl",
        route="garden_first",
        seed=202,
    ),
    StoryParams(
        place="river_bridge",
        token="glass",
        name="Luna",
        helper="Dain",
        promise="glass",
        route="dialogue_first",
        seed=303,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2.\n#show reasonable/2."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible moon-token settings:\n")
        for place, token in combos:
            print(f"  {place:14} {token}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(args.n * 50, 50):
            seed = base_seed + attempts
            attempts += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as error:
                print(error)
                return
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = "### curated story" if args.all else (
            f"### variant {index + 1}" if len(samples) > 1 else ""
        )
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
