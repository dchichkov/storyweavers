#!/usr/bin/env python3
"""
A standalone heartwarming storyworld about a gator, a silly mistake, and
kindness that turns a muddy mishap into shared laughter.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"mud": 0.0, "wobble": 0.0, "clean": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "love": 0.0, "bravery": 0.0}


@dataclass
class Setting:
    key: str
    place: str
    feature: str


@dataclass
class StoryParams:
    place: str
    hero_type: str
    friend_type: str
    name: str
    friend_name: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Incident:
    title: str
    task: str
    mishap: str
    clue: str
    joke: str
    repair: str
    lesson: str
    ending: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple[str, str]] = set()

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
    "pond": Setting("pond", "the sunny pond", "a dock with lily-pad stepping stones"),
    "marsh": Setting("marsh", "the green marsh", "a boardwalk beside cattails"),
    "riverbank": Setting("riverbank", "the quiet riverbank", "a picnic blanket near the reeds"),
}

HERO_TYPES = ["gator"]
FRIEND_TYPES = ["turtle", "heron", "frog", "otter"]

CHARACTER_NAMES = {
    "gator": ["Gus", "Luna", "Moss"],
    "turtle": ["Tilly", "Theo", "Pip"],
    "heron": ["Hazel", "Hugo", "Iris"],
    "frog": ["Fifi", "Finn", "Mimi"],
    "otter": ["Ollie", "Opal", "Nori"],
}

INCIDENTS = [
    Incident(
        title="the welcome picnic",
        task="hang a bright banner for the marsh animals' welcome picnic",
        mishap="Gator Luna pulled the ribbon with such a grand flourish that the banner landed on her snout",
        clue="a trail of blue paint led from the banner to one muddy footprint",
        joke="the banner announced WELCOME, but it was currently welcoming Luna's nose",
        repair="washed the paint from Luna's snout, tied the banner with two gentle loops, and placed a smooth stick beneath its middle",
        lesson="A funny mistake feels smaller when friends help instead of pointing and laughing",
        ending="When the guests arrived, Luna's clean nose peeked beneath the banner, and everyone laughed with her",
    ),
    Incident(
        title="the lily-pad concert",
        task="carry a tiny drum to the pond's lily-pad concert",
        mishap="Gator Gus stepped backward onto the drum and made one enormous boom",
        clue="the drum's wobbly strap was caught under a flat stone",
        joke="the concert had not begun, but Gus had already played the loudest solo",
        repair="lifted the stone, straightened the strap, and tested the drum with one polite tap",
        lesson="Making room for a mistake lets courage grow again",
        ending="Gus tapped the opening beat, and the frogs answered with a happy chorus",
    ),
    Incident(
        title="the lost-hat parade",
        task="lead a parade of animals wearing leaf hats",
        mishap="Gator Moss sneezed, and three leaf hats flew into the cattails",
        clue="the hats had followed a breeze toward the tallest reed",
        joke="Moss declared that the parade now had a very leafy audience",
        repair="waited for the breeze to settle, gathered the hats with a long reed, and fastened each one with soft grass",
        lesson="Patience can turn a surprising mess into a new kind of fun",
        ending="The parade marched on, and Moss wore the biggest leaf hat with great pride",
    ),
    Incident(
        title="the floating cake",
        task="help carry a small berry cake to a birthday table",
        mishap="a turtle bumped the tray, and Gator Luna caught the cake before it slid into the water",
        clue="one tray handle was loose and made the cake tilt",
        joke="the cake was saved, though it had briefly planned to become a berry boat",
        repair="held the tray level, tightened the handle with a vine, and carried it together with a helper on each side",
        lesson="Asking for help protects both the treat and the friends carrying it",
        ending="The cake reached the table with every berry aboard, and Luna received the first slice",
    ),
    Incident(
        title="the moonlit puppet show",
        task="set up a cloth stage for a moonlit puppet show",
        mishap="Gator Gus backed into the stage pole and made the puppet curtain bow like a sleepy whale",
        clue="the pole stood in soft mud instead of firm sand",
        joke="the curtain gave such a deep bow that the puppets looked very important",
        repair="moved the pole to firmer ground, packed sand around its base, and tied the curtain with a bright knot",
        lesson="A gentle reset can make a wobbly plan strong again",
        ending="The curtain rose steadily, and Gus bowed back before the first puppet spoke",
    ),
]

OPENINGS = [
    "At {place}, {hero} the {hero_type} woke early because {friend} the {friend_type} had invited {hero} to help with {title}.",
    "The morning sun glittered at {place} when {hero} the {hero_type} arrived with a grin and {friend} the {friend_type} arrived with a careful plan.",
    "Near {feature}, {hero} the {hero_type} promised to be extra helpful during {title}.",
    "Everyone at {place} was getting ready for {title}, and {hero} the {hero_type} was certain that nothing could possibly go wrong.",
]

DIALOGUES = [
    '"I have a very careful plan," said {hero}. "Does it include keeping your tail away from the supplies?" asked {friend}.',
    '"That was not my best landing," {hero} admitted. "It was certainly your most memorable one," {friend} said kindly.',
    '"Should we hide the mistake?" asked {hero}. "No," said {friend}. "We can fix it, and then we can laugh together."',
    '"I meant to do that," said {hero}. "Then you meant to give us a wonderful clue," replied {friend}.',
]

REFLECTIONS = [
    "They worked slowly now, checking each part before moving to the next.",
    "The task took longer, but nobody felt alone.",
    "Even the smallest helper found a safe job to do.",
    "When the work was finished, they checked the ground for anything left behind.",
]


def _stable_seed(*parts: str) -> int:
    return sum((i + 1) * ord(ch) for i, ch in enumerate("|".join(parts)))


def muddy(entity: Entity) -> bool:
    return entity.meters.get("mud", 0.0) >= THRESHOLD


def wobbly(entity: Entity) -> bool:
    return entity.meters.get("wobble", 0.0) >= THRESHOLD


def can_repair(world: World) -> bool:
    return "helper" in world.entities and "vine" in world.entities


def clean_gator(gator: Entity) -> None:
    gator.meters["mud"] = 0.0
    gator.meters["clean"] += 1.0


def steady_object(obj: Entity) -> None:
    obj.meters["wobble"] = 0.0
    obj.meters["clean"] += 1.0


def story_text(
    setting: Setting,
    hero: Entity,
    friend: Entity,
    incident: Incident,
    rng: random.Random,
) -> list[str]:
    values = {
        "place": setting.place,
        "feature": setting.feature,
        "hero": hero.id,
        "hero_type": hero.type,
        "friend": friend.id,
        "friend_type": friend.type,
        "title": incident.title,
    }
    opening = rng.choice(OPENINGS).format(**values)
    dialogue = rng.choice(DIALOGUES).format(**values)
    reflection = rng.choice(REFLECTIONS)
    premise = f"They needed to {incident.task}."
    trouble = f"Then {incident.mishap}."
    clue = f"They looked closely and found that {incident.clue}."
    joke = f"{incident.joke.capitalize()}."
    repair = f"Together they {incident.repair}."
    lesson = f'"{incident.lesson}," said {friend.id}.'
    ending = f"{incident.ending}."

    return [
        f"{opening} {premise}",
        f"{trouble} {joke} {hero.id} blinked, and a little worry replaced the grin.",
        f"{dialogue} {clue}",
        f"{repair} {reflection}",
        f"The work was finished. {lesson} {ending}",
    ]


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    seed = params.seed if params.seed is not None else _stable_seed(
        params.place, params.name, params.friend_name
    )
    rng = random.Random(seed)
    incident = rng.choice(INCIDENTS)

    world = World(setting)
    hero = world.add(Entity(params.name, "character", params.hero_type))
    friend = world.add(Entity(params.friend_name, "character", params.friend_type))
    object_entity = world.add(Entity("project", "thing", "project", incident.title))
    world.add(Entity("helper", "thing", "tool", "a soft cleaning cloth"))
    world.add(Entity("vine", "thing", "vine", "a strong green vine"))

    hero.memes.update({"love": 1.0, "curiosity": 1.0})
    friend.memes.update({"love": 1.0, "patience": 1.0})
    hero.meters["mud"] = 1.0
    object_entity.meters["wobble"] = 1.0
    hero.memes["worry"] = 1.0
    friend.memes["worry"] = 1.0

    if not can_repair(world):
        raise StoryError("The story needs a soft helper and a strong vine for a safe repair.")

    clean_gator(hero)
    steady_object(object_entity)
    hero.memes["worry"] = 0.0
    friend.memes["worry"] = 0.0
    hero.memes["joy"] = 2.0
    friend.memes["joy"] = 2.0
    hero.memes["bravery"] = 1.0

    for paragraph in story_text(setting, hero, friend, incident, rng):
        world.say(paragraph)
        world.para()

    world.facts = {
        "hero": hero,
        "friend": friend,
        "project": object_entity,
        "incident": incident,
        "setting": setting,
        "mud_fixed": not muddy(hero),
        "project_fixed": not wobbly(object_entity),
    }
    return world


def generation_prompts(world: World) -> list[str]:
    incident: Incident = world.facts["incident"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]
    return [
        f"Write a heartwarming humorous story about {hero.id} the gator helping with {incident.title}.",
        f"Tell a child-friendly story where {hero.id} and {friend.id} repair a funny mishap through kindness and teamwork.",
        f"Write a gentle story showing that friends can laugh with someone while still helping them.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]
    incident: Incident = world.facts["incident"]  # type: ignore[assignment]
    setting: Setting = world.facts["setting"]  # type: ignore[assignment]
    return [
        QAItem(
            f"Where did {hero.id} and {friend.id} work?",
            f"They worked at {setting.place}, near {setting.feature}.",
        ),
        QAItem(
            f"What was {hero.id} trying to do?",
            f"{hero.id} was trying to {incident.task}.",
        ),
        QAItem(
            "What funny trouble happened?",
            f"{incident.mishap}. {incident.joke.capitalize()}.",
        ),
        QAItem(
            "How did the friends repair the trouble?",
            f"They {incident.repair}.",
        ),
        QAItem(
            f"What did {friend.id} help {hero.id} understand?",
            f"{friend.id} helped {hero.id} learn that {incident.lesson.lower()}",
        ),
        QAItem(
            "How did the story end?",
            incident.ending + ".",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a gator?",
            "A gator, or alligator, is a large reptile with a broad snout, strong tail, and tough skin.",
        ),
        QAItem(
            "Why is teamwork useful?",
            "Teamwork lets people share jobs, notice problems, and help one another finish safely.",
        ),
        QAItem(
            "How can humor help after a mistake?",
            "Gentle humor can ease worry when it laughs with someone rather than making fun of them.",
        ),
        QAItem(
            "What makes a repair safe?",
            "A safe repair first stops the trouble, uses suitable materials, and checks the result gently.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
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
gator_type(gator).
animal(turtle).
animal(heron).
animal(frog).
animal(otter).

setting(pond).
setting(marsh).
setting(riverbank).

has_helper :- helper(cleaning_cloth), vine(strong_vine).
reasonable(P, H, F) :-
    setting(P),
    gator_type(H),
    animal(F),
    has_helper.
"""


def asp_facts() -> str:
    import asp

    facts = []
    for setting in SETTINGS:
        facts.append(asp.fact("setting", setting))
    facts.append(asp.fact("gator_type", "gator"))
    for friend in FRIEND_TYPES:
        facts.append(asp.fact("animal", friend))
    facts.append(asp.fact("helper", "cleaning_cloth"))
    facts.append(asp.fact("vine", "strong_vine"))
    return "\n".join(facts)


def asp_program(show: str = "#show reasonable/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_verify() -> int:
    expected = {
        (place, "gator", friend)
        for place in SETTINGS
        for friend in FRIEND_TYPES
    }
    actual = set(asp_valid_stories())
    if actual == expected:
        print(f"OK: ASP gate matches Python expectations ({len(actual)} combinations).")
        return 0
    print("MISMATCH between ASP and Python expectations:")
    print("only in ASP:", sorted(actual - expected))
    print("only in Python:", sorted(expected - actual))
    return 1


CURATED = [
    StoryParams("pond", "gator", "frog", "Luna", "Fifi"),
    StoryParams("marsh", "gator", "turtle", "Gus", "Tilly"),
    StoryParams("riverbank", "gator", "heron", "Moss", "Hazel"),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Heartwarming humorous gator storyworld."
    )
    parser.add_argument("--place", choices=SETTINGS)
    parser.add_argument("--hero-type", choices=HERO_TYPES)
    parser.add_argument("--friend-type", choices=FRIEND_TYPES)
    parser.add_argument("--name")
    parser.add_argument("--friend-name")
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
    place = args.place or rng.choice(list(SETTINGS))
    hero_type = args.hero_type or "gator"
    friend_type = args.friend_type or rng.choice(FRIEND_TYPES)
    name = args.name or rng.choice(CHARACTER_NAMES[hero_type])
    friend_name = args.friend_name or rng.choice(CHARACTER_NAMES[friend_type])
    if name == friend_name:
        choices = [n for n in CHARACTER_NAMES[friend_type] if n != name]
        friend_name = rng.choice(choices)
    return StoryParams(place, hero_type, friend_type, name, friend_name)


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id:10} ({entity.type:10}) "
            f"meters={meters} memes={memes}"
        )
    return "\n".join(lines)


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
        rows = asp_valid_stories()
        print(f"{len(rows)} compatible story combinations:")
        for row in rows:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n:
            seed = base_seed + index
            index += 1
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.place} ({p.hero_type} + {p.friend_type})"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
