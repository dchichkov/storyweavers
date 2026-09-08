#!/usr/bin/env python3
"""A child-facing superhero quest about Luna, a grizzly, and a brave repair."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
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
    mood: str
    weather: str


@dataclass
class StoryParams:
    place: str
    power: str
    name: str
    helper: str
    grizzly: str
    quest: str = ""
    route: str = ""
    seed: Optional[int] = None


@dataclass(frozen=True)
class QuestCase:
    missing: str
    danger: str
    test: str
    obstacle: str
    discovery: str
    truth: str
    repair: str
    lesson: str
    ending: str


@dataclass
class World:
    scene: Scene
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


PLACES = {
    "canyon": Scene("the Echo Canyon", "red-rock", "a warm wind"),
    "forest": Scene("the Moonlit Forest", "pine-scented", "a silver drizzle"),
    "harbor": Scene("the Star Harbor", "glittering", "a brisk sea breeze"),
    "mountain": Scene("the Cloud Mountain", "snowy", "a bright, cold gust"),
}

POWERS = {
    "lumen": "a golden beam that reveals hidden paths",
    "echo": "a gentle voice that can reach across great distances",
    "shield": "a bright shield that protects everyone nearby",
    "wind": "a silver gust that can lift light objects",
}

HEROES = {"Luna": "girl", "Milo": "boy", "Ari": "child", "Sage": "child"}
HELPERS = {"Pip": "bird", "Nia": "girl", "Bo": "boy", "Rin": "child"}
GRIZZLIES = {"grizzly": "grizzly bear", "Bruno": "grizzly bear", "Maple": "grizzly bear"}

QUESTS = {
    "heart_lantern": QuestCase(
        "the Heart Lantern that guided lost travelers",
        "its dark glass made the mountain trail unsafe",
        "tested the lantern with a small mirror",
        "the mirror showed no flame, and the first guess failed",
        "a warm pawprint circled a nest of blue crystals",
        "the grizzly had carried the lantern away from falling rocks and sheltered it",
        "cleared the rocks, thanked the grizzly, and hung the lantern on a safer post",
        "a quiet helper may be protecting others",
        "the Heart Lantern glowed above the safe trail while the grizzly napped nearby",
    ),
    "sky_bell": QuestCase(
        "the silver Sky Bell from the harbor tower",
        "without its warning ring, boats could miss the fog channel",
        "followed the last clear note with a listening cup",
        "the echo bounced off the cliffs and sent the hero in the wrong direction",
        "a deep pawprint led to a canvas rescue raft",
        "the grizzly had pulled the bell down before a cracked tower beam could drop it",
        "mended the tower with the harbor crew and rehung the bell",
        "a brave rescue can look like a theft until its reason is known",
        "the Sky Bell rang over calm water as the grizzly waved one huge paw",
    ),
    "rainbow_map": QuestCase(
        "the rainbow map of hidden water springs",
        "the village wells were nearly dry",
        "used the lumen beam to scour the map for a missing mark",
        "the beam revealed many old marks but not the spring",
        "a grizzly claw had traced a line beneath a loose stone",
        "the grizzly knew the spring was blocked by a fallen tree",
        "moved the tree together and shared the fresh water",
        "asking for help can reveal knowledge that powers cannot",
        "rainbow marks shone beside a full spring while everyone drank safely",
    ),
    " comet_seed": QuestCase(
        "the comet seed meant to grow a shelter tree",
        "the seed had to be planted before the night wind ended",
        "tracked a trail of glitter from the launch garden",
        "the glitter stopped at a muddy stream",
        "large pawprints crossed the stream toward a hollow log",
        "the grizzly had carried the seed away from a hungry flock of crows",
        "built a small fence and planted the seed in rich soil",
        "protecting something precious is better than guarding it alone",
        "a silver-leaf tree opened above the smiling grizzly and the grateful team",
    ),
    "sun_bridge": QuestCase(
        "the Sun Bridge power crystal",
        "the bridge over the canyon had begun to flicker",
        "held the crystal near the bridge and watched its light",
        "the light went out whenever the wind struck the cables",
        "a grizzly-sized scrape marked a sheltered ledge",
        "the grizzly had found the crystal after it bounced off the bridge",
        "secured the cables, cleaned the crystal, and restored the bridge",
        "a safe solution must protect both people and the power source",
        "the Sun Bridge shone gold from cliff to cliff as the quest ended",
    ),
}

ROUTES = ("signal_first", "dialogue_first", "clue_first", "inner_voice", "map_first", "rescue_first")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A superhero quest about Luna and a helpful grizzly.")
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--power", choices=sorted(POWERS))
    parser.add_argument("--name")
    parser.add_argument("--helper", choices=sorted(HELPERS))
    parser.add_argument("--grizzly", choices=sorted(GRIZZLIES))
    parser.add_argument("--quest", choices=sorted(QUESTS))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument(f"--{flag}", action="store_true")
    return parser


def valid_combos() -> list[tuple[str, str]]:
    return [(place, power) for place in sorted(PLACES) for power in sorted(POWERS)]


ASP_RULES = """
valid(Place, Power) :- place(Place), power(Power).
hero_ready(Name) :- hero(Name), power(Power).
quest_safe(Quest) :- quest(Quest).
"""


def asp_facts() -> str:
    import asp
    facts = [
        *(asp.fact("place", value) for value in PLACES),
        *(asp.fact("power", value) for value in POWERS),
        *(asp.fact("hero", value) for value in HEROES),
        *(asp.fact("quest", value) for value in QUESTS),
    ]
    return "\n".join(facts)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_pairs = set(valid_combos())
    asp_pairs = set(asp_valid_combos())
    if python_pairs == asp_pairs:
        print(f"OK: clingo gate matches valid_combos() ({len(python_pairs)} combos).")
        return 0
    print("MISMATCH:", sorted(python_pairs - asp_pairs), sorted(asp_pairs - python_pairs))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        pair for pair in valid_combos()
        if not args.place or pair[0] == args.place
        if not args.power or pair[1] == args.power
    ]
    if not combos:
        raise StoryError("No valid superhero quest fits those options.")
    place, power = rng.choice(combos)
    name = args.name or "Luna"
    if name not in HEROES:
        raise StoryError(f"Unknown hero {name!r}; choose Luna, Milo, Ari, or Sage.")
    helpers = [value for value in sorted(HELPERS) if value != name] or sorted(HELPERS)
    return StoryParams(
        place=place,
        power=power,
        name=name,
        helper=args.helper or rng.choice(helpers),
        grizzly=args.grizzly or rng.choice(sorted(GRIZZLIES)),
        quest=args.quest or rng.choice(sorted(QUESTS)),
        route=rng.choice(ROUTES),
    )


def story_rng(params: StoryParams) -> random.Random:
    text = "|".join(
        str(value) for value in (
            params.seed, params.place, params.power, params.name,
            params.helper, params.grizzly, params.quest, params.route,
        )
    )
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def tell(params: StoryParams) -> World:
    scene = PLACES[params.place]
    case = QUESTS[params.quest]
    rng = story_rng(params)
    world = World(scene)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=HEROES[params.name],
        meters={"courage": 1.0, "energy": 1.0},
        memes={"hope": 1.0},
    ))
    helper = world.add(Entity(
        id=params.helper,
        kind="character",
        type=HELPERS[params.helper],
        meters={"helpfulness": 1.0},
        memes={"trust": 1.0},
    ))
    grizzly = world.add(Entity(
        id=params.grizzly,
        kind="character",
        type="grizzly bear",
        label="the grizzly",
        meters={"strength": 2.0, "distance": 1.0},
        memes={"loneliness": 1.0},
    ))

    openings = {
        "signal_first": (
            f"A red signal blinked over {scene.place}. "
            f"{hero.id} knew that {case.missing} had vanished, so the superhero began a quest."
        ),
        "dialogue_first": (
            f'"We need help," {helper.id} said at {scene.place}. '
            f"{case.missing.capitalize()} was gone, and the safety of many friends was at risk."
        ),
        "clue_first": (
            f"{hero.id} found a strange mark beside {scene.place}: "
            f"a clue that {case.missing} had been moved."
        ),
        "inner_voice": (
            f"{hero.id} stood beneath the {scene.weather} and watched {scene.place}. "
            f'"I feel worried," the hero thought, "but worry can point me toward careful work." '
            f"{case.missing.capitalize()} was missing."
        ),
        "map_first": (
            f"{hero.id} drew {scene.place} on a rescue map. "
            f"In the empty center, the hero wrote that {case.missing} was gone."
        ),
        "rescue_first": (
            f"The quest began when a distant cry rose from {scene.place}. "
            f"{hero.id} learned that {case.missing} had disappeared during the trouble."
        ),
    }
    world.say(openings[params.route])
    world.say(
        rng.choice([
            f"{hero.id} touched the badge on the hero suit and remembered that courage meant helping, not showing off.",
            f"{helper.id} opened the little field kit and promised to stay beside {hero.id}.",
            f"The superhero checked the path, the weather, and the people who might need a safe way home.",
        ])
    )
    world.para()

    world.say(f"The first danger was clear: {case.danger}.")
    world.say(
        rng.choice([
            f'"Should we rush?" {helper.id} asked. "We should move quickly, but carefully," {hero.id} replied.',
            f'"I can use my {params.power} power," {hero.id} said. '
            f'"Use it gently," {helper.id} answered. "The answer may need more than strength."',
            f"{hero.id} felt fear flutter in the chest. "
            f'"Fear is a warning, not a command," the hero thought, and took one steady breath.',
        ])
    )
    world.say(f"Near the trail, everyone suspected {grizzly.label} because {case.danger.lower()}.")
    world.say(
        f'"A grizzly can look scary," {helper.id} said, "but looking scary is not proof." '
        f'"Then we will scour the clues," {hero.id} promised. "We will not blame anyone too soon."'
    )
    grizzly.memes["blamed"] = 1
    hero.memes["fairness"] = 1
    world.para()

    world.say(f"First, {hero.id} {case.test}.")
    world.say(f"But {case.obstacle}. The test did not explain what had happened.")
    world.say(
        rng.choice([
            f"{hero.id} lowered the power and admitted, " + '"That idea did not work."',
            f'"A failed test is still useful," {helper.id} said. "Now we know which path to leave."',
            f"The hero felt the quest grow harder, but chose patience instead of a wild guess.",
        ])
    )
    world.say(f"Then they discovered {case.discovery}.")
    world.say(
        rng.choice([
            f"{hero.id} followed the clue without touching it, while {helper.id} marked each safe step.",
            f"The clue connected the empty place, the danger, and the grizzly's tracks.",
            f"{hero.id} let the inner voice speak: '" + '"Look for the reason behind the action."',
        ])
    )
    world.para()

    world.say(f"The truth was that {case.truth}. The grizzly had been trying to help.")
    grizzly.memes["blamed"] = 0
    grizzly.memes["trusted"] = 1
    grizzly.meters["distance"] = 0.0
    hero.meters["courage"] = 2.0
    world.say(
        f'"We are sorry we suspected you," {hero.id} told the grizzly. '
        f'The grizzly rumbled, "I wanted everyone to be safe." '
        f"{helper.id} smiled because the quest had changed fear into friendship."
    )
    world.say(f"Together, they {case.repair}.")
    world.say(f"{hero.id} remembered: {case.lesson}.")
    world.say(
        rng.choice([
            f"At last, {case.ending}.",
            f"When the happy ending arrived, {case.ending}.",
            f"The whole team cheered because {case.ending}.",
        ])
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        grizzly=grizzly,
        scene=scene,
        case=case,
        power=POWERS[params.power],
        truth=case.truth,
        lesson=case.lesson,
        ending=case.ending,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    case = facts["case"]
    return [
        f"Write a child-friendly superhero quest about {facts['hero'].id}, {facts['grizzly'].label}, and {case.missing}.",
        f"Include an inner monologue in which {facts['hero'].id} chooses careful courage instead of quick blame.",
        f"End happily after the heroes discover that {case.truth} and {case.ending}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    case = facts["case"]
    hero = facts["hero"].id
    helper = facts["helper"].id
    grizzly = facts["grizzly"].label
    return [
        QAItem(
            question=f"What began {hero}'s quest at {facts['scene'].place}?",
            answer=f"{case.missing.capitalize()} disappeared at {facts['scene'].place}, and its loss created the danger that began {hero}'s quest.",
        ),
        QAItem(
            question=f"Why did {hero} refuse to blame {grizzly too quickly?",
            answer=f"{grizzly.capitalize()} looked suspicious because {case.danger.lower()}, but {hero} and {helper} knew that appearance was not proof.",
        ),
        QAItem(
            question=f"What happened when {hero} tested the first idea?",
            answer=f"{hero} {case.test}, but {case.obstacle}. The failed test helped the team leave that weak explanation behind.",
        ),
        QAItem(
            question=f"What clue revealed the grizzly's real reason?",
            answer=f"They found that {case.discovery}. This showed that {case.truth}.",
        ),
        QAItem(
            question=f"How did the superheroes create a happy ending?",
            answer=f"They apologized to {grizzly}, then {case.repair}. They learned that {case.lesson}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why should a hero check clues before blaming someone?",
            answer="A nearby person or animal may have a good reason for being near a problem. Checking clues helps a hero protect innocent friends and find the real cause.",
        ),
        QAItem(
            question="What can an inner monologue do in a story?",
            answer="An inner monologue lets readers hear a character's private worry or plan. It can show how the character changes a feeling into a wise decision.",
        ),
        QAItem(
            question="What makes a superhero ending happy?",
            answer="A happy ending shows that danger has been reduced, a problem has been repaired, and characters have gained safety, understanding, or friendship.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{index}. {prompt}" for index, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.append("")
    lines.append("== world qa ==")
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
    lines.append(f"  truth={world.facts['truth']}")
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
        place="mountain",
        power="lumen",
        name="Luna",
        helper="Pip",
        grizzly="Bruno",
        quest="heart_lantern",
        route="inner_voice",
        seed=101,
    ),
    StoryParams(
        place="harbor",
        power="echo",
        name="Milo",
        helper="Nia",
        grizzly="Maple",
        quest="sky_bell",
        route="dialogue_first",
        seed=202,
    ),
    StoryParams(
        place="forest",
        power="shield",
        name="Ari",
        helper="Bo",
        grizzly="grizzly",
        quest="comet_seed",
        route="clue_first",
        seed=303,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2.\n#show hero_ready/1.\n#show quest_safe/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for place, power in combos:
            print(f"  {place:10} {power}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
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
