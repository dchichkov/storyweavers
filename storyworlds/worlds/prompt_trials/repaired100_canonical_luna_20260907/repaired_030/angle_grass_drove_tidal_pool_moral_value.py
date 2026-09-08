#!/usr/bin/env python3
"""
A comic tidal-pool storyworld about angle, grass, and a determined drove of crabs.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE)))))
sys.path.insert(0, os.path.join(ROOT, "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    location: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)
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


@dataclass
class StoryParams:
    name: str
    friend: str
    helper: str
    angle: str
    grass: str
    drove: str
    surprise: str
    bravery: str
    ending: str
    seed: int | None = None


@dataclass(frozen=True)
class Incident:
    angle: str
    grass: str
    drove: str
    danger: str
    fix: str
    result: str


@dataclass(frozen=True)
class Surprise:
    setup: str
    reveal: str
    joke: str


@dataclass(frozen=True)
class Bravery:
    temptation: str
    choice: str
    consequence: str


@dataclass(frozen=True)
class Ending:
    image: str
    line: str


SETTINGS = {"tidal_pool": "the tidal pool"}

ANGLES = {
    "wide": "the wide angle between the rocks and the seaweed",
    "crooked": "a crooked angle beside a pink anemone",
    "secret": "a secret angle beneath a shelf of shell",
    "silly": "a silly angle that made every crab walk sideways twice",
    "moonlit": "the moonlit angle where the water looked like a silver bowl",
}

GRASSES = {
    "eelgrass": "a thick patch of eelgrass",
    "sea_grass": "a soft bed of sea grass",
    "green_ribbon": "long green ribbons of grass",
    "tiny_lawn": "a tiny lawn of grass between the stones",
    "floating": "floating grass that tickled every passing claw",
}

DROVES = {
    "crabs": "a drove of bright little crabs",
    "snails": "a drove of patient sea snails",
    "shrimp": "a drove of jumping shrimp",
    "minnows": "a drove of silver minnows",
    "hermits": "a drove of bashful hermit crabs",
}

INCIDENTS = {
    "shell_bridge": Incident(
        angle=ANGLES["wide"],
        grass=GRASSES["eelgrass"],
        drove=DROVES["crabs"],
        danger="the drove had crowded onto a loose shell bridge, which was wobbling like a pudding",
        fix="make a calm path through the eelgrass and invite the smallest crabs across first",
        result="the shell bridge was emptied before it could flop into the deepest part of the pool",
    ),
    "foam_hat": Incident(
        angle=ANGLES["crooked"],
        grass=GRASSES["floating"],
        drove=DROVES["hermits"],
        danger="the drove had mistaken a cap of sea foam for a royal hat and was marching toward a drain",
        fix="follow the crooked angle around the grass and turn the procession toward a safe stone",
        result="the foam hat bobbed away while every hermit crab reached the stone",
    ),
    "pebble parade": Incident(
        angle=ANGLES["secret"],
        grass=GRASSES["tiny_lawn"],
        drove=DROVES["snails"],
        danger="the drove was carrying one enormous pebble and blocking the only shady route",
        fix="ask the snails to rest the pebble beside the grass, then open the route one shell at a time",
        result="the pebble became a useful shade and the route stayed open",
    ),
    "splash line": Incident(
        angle=ANGLES["silly"],
        grass=GRASSES["sea_grass"],
        drove=DROVES["shrimp"],
        danger="the drove kept leaping in one line toward a puddle that was shrinking by the minute",
        fix="stand at the silly angle and count each leap toward the deeper water",
        result="the shrimp reached the deep pool and stopped bouncing on everyone's toes",
    ),
    "silver turn": Incident(
        angle=ANGLES["moonlit"],
        grass=GRASSES["green_ribbon"],
        drove=DROVES["minnows"],
        danger="the drove had followed a shiny button into a pocket of grass with no easy exit",
        fix="hold the grass aside and guide the minnows around the button",
        result="the button stayed behind and the minnows flashed back into open water",
    ),
}

SURPRISES = {
    "octopus": Surprise(
        setup="Just as the brave plan began, a tiny octopus popped up wearing a seaweed mustache.",
        reveal="It had been the mysterious guide making the grass wiggle.",
        joke="It bowed so deeply that one arm landed in a limpet's soup.",
    ),
    "pearl": Surprise(
        setup="Then a round white pearl rolled out from under the grass.",
        reveal="It was not a treasure at all, but a bubble made by a sleeping clam.",
        joke="The clam snored once, and the pearl bounced onto the hero's nose.",
    ),
    "mirror": Surprise(
        setup="A sudden wave polished a flat stone until it became a shining mirror.",
        reveal="The frightening shadow was only the friends looking very serious.",
        joke="They practiced brave faces and accidentally looked like surprised potatoes.",
    ),
    "jelly": Surprise(
        setup="A jellyfish drifted over the pool like a floating umbrella.",
        reveal="It was carrying a lost red ribbon in two gentle arms.",
        joke="The ribbon wrapped around its bell and made it look ready for a parade.",
    ),
    "whistle": Surprise(
        setup="A sharp whistle rang from the grass.",
        reveal="The sound came from a tiny whelk blowing through an empty shell.",
        joke="The whelk tried a second note and startled itself into a slow somersault.",
    ),
}

BRAVERIES = {
    "speak": Bravery(
        temptation="hide behind a rock and let everyone else guess what to do",
        choice="speak clearly, even though the voice came out squeaky",
        consequence="the creatures heard the warning and stopped bumping into one another",
    ),
    "share": Bravery(
        temptation="keep the safest stone for one friend",
        choice="share the safe place with the smallest creature first",
        consequence="the whole pool became calmer because nobody was pushed aside",
    ),
    "ask": Bravery(
        temptation="pretend to know the route",
        choice="ask the oldest limpet for help",
        consequence="the limpet knew a secret turn that made the rescue simple",
    ),
    "wait": Bravery(
        temptation="rush into the water before checking the tide",
        choice="wait for the wave to settle",
        consequence="the careful pause revealed a dry path under the foam",
    ),
    "laugh": Bravery(
        temptation="laugh at a frightened friend",
        choice="laugh kindly at the silly mistake and help fix it",
        consequence="everyone relaxed enough to notice the real danger",
    ),
}

ENDINGS = {
    "dance": Ending(
        "At sunset, the drove made a wiggly dance around the grass",
        "The hero bowed, but a crab stole the bow and wore it as a hat.",
    ),
    "snack": Ending(
        "The friends shared crumbs beside the quiet tidal pool",
        "Even the bravest snack was better when nobody had to eat it alone.",
    ),
    "flag": Ending(
        "They planted a blade of grass like a green flag at the safe angle",
        "Whenever it waved, the creatures remembered to help before they hurried.",
    ),
    "tide": Ending(
        "The returning tide filled the pool with bright, dancing water",
        "The drove floated home, while the friends walked proudly and only a little sideways.",
    ),
    "shell": Ending(
        "A small shell was placed beside the grass as a marker of the rescue",
        "It looked ordinary, but everyone knew it had witnessed extraordinary silliness.",
    ),
}

NAMES = ["Luna", "Milo", "Pip", "Nora", "Tavi", "Mara", "Bix", "Cleo"]
HELPERS = ["an old limpet", "a kindly sea star", "the pool keeper", "a purple anemone"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Comedy tidal-pool storyworld.")
    parser.add_argument("--setting", choices=SETTINGS, default=None)
    parser.add_argument("--angle", choices=ANGLES, default=None)
    parser.add_argument("--grass", choices=GRASSES, default=None)
    parser.add_argument("--drove", choices=DROVES, default=None)
    parser.add_argument("--surprise", choices=SURPRISES, default=None)
    parser.add_argument("--bravery", choices=BRAVERIES, default=None)
    parser.add_argument("--ending", choices=ENDINGS, default=None)
    parser.add_argument("--name")
    parser.add_argument("--friend")
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
    if args.setting not in (None, "tidal_pool"):
        raise StoryError("This storyworld only supports the tidal pool.")
    name = args.name or rng.choice(NAMES)
    friend = args.friend or rng.choice([x for x in NAMES if x != name])
    if name == friend:
        raise StoryError("The hero and friend need different names.")
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(
        name=name,
        friend=friend,
        helper=helper,
        angle=args.angle or rng.choice(tuple(ANGLES)),
        grass=args.grass or rng.choice(tuple(GRASSES)),
        drove=args.drove or rng.choice(tuple(DROVES)),
        surprise=args.surprise or rng.choice(tuple(SURPRISES)),
        bravery=args.bravery or rng.choice(tuple(BRAVERIES)),
        ending=args.ending or rng.choice(tuple(ENDINGS)),
    )


def tell(params: StoryParams) -> World:
    incident = next(
        value for value in INCIDENTS.values()
        if value.angle == ANGLES[params.angle]
        and value.grass == GRASSES[params.grass]
        and value.drove == DROVES[params.drove]
    )
    surprise = SURPRISES[params.surprise]
    bravery = BRAVERIES[params.bravery]
    ending = ENDINGS[params.ending]

    world = World(SETTINGS["tidal_pool"])
    hero = world.add(Entity(params.name, "character", params.name, "tidal pool"))
    friend = world.add(Entity(params.friend, "character", params.friend, "tidal pool"))
    helper = world.add(Entity("helper", "helper", params.helper, "tidal pool"))
    creatures = world.add(Entity("drove", "group", incident.drove, "tidal pool"))
    grass = world.add(Entity("grass", "plant", incident.grass, "tidal pool"))

    world.facts.update(
        hero=hero,
        friend=friend,
        helper=helper,
        creatures=creatures,
        grass=grass,
        incident=incident,
        surprise=surprise,
        bravery=bravery,
        ending=ending,
        moral="bravery means choosing a helpful action even when the easy choice is to hide",
    )

    world.say(
        f"One bright morning, {hero.label} and {friend.label} explored the tidal pool, "
        f"where {incident.drove} marched through {incident.grass}."
    )
    world.say(
        f"They were studying {incident.angle} when {incident.danger}."
    )

    world.para()
    world.say(f'"We should do something," said {hero.label}.')
    world.say(f'"You always say that just before something splashes you," replied {friend.label}.')
    world.say(f'Then {hero.label} answered, "Perhaps, but this time I have a plan."')
    world.say(f"The plan was to {incident.fix}.")

    world.para()
    world.say(f"{bravery.temptation.capitalize()}.")
    hero.memes["fear"] = 1.0
    friend.memes["worry"] = 1.0
    world.say(f"{hero.label} took a breath and chose to {bravery.choice}.")
    world.say(f'"I may be nervous," {hero.label} said, "but I can still help."')
    world.say(f'"That is the bravest sentence I have heard all morning," said {friend.label}.')
    hero.memes["bravery"] = 1.0
    friend.memes["trust"] = 1.0
    world.say(f"Because of that choice, {bravery.consequence}.")

    world.para()
    world.say(surprise.setup)
    world.say(surprise.reveal)
    world.say(f"{surprise.joke} {friend.label} laughed, and even {params.helper} seemed to smile.")
    world.say(f"Together, the friends followed the plan, and {incident.result}.")
    world.facts["resolved"] = True

    world.para()
    world.say(f'"Thank you," said {hero.label}. "We helped because nobody should face a tricky tide alone."')
    world.say(f'"And because you finally asked before jumping," said {friend.label}.')
    world.say(f"They understood that {world.facts['moral']}.")
    world.say(f"{ending.image}.")
    world.say(ending.line)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    incident: Incident = world.facts["incident"]  # type: ignore[assignment]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f"Write a comic tidal-pool tale involving {incident.angle}.",
            f"Include {incident.grass}, {incident.drove}, a surprise, and a brave moral choice.",
            "Show how the characters' spoken words change their plan.",
        ],
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(),
        world=world,
    )


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]
    incident: Incident = world.facts["incident"]  # type: ignore[assignment]
    bravery: Bravery = world.facts["bravery"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What trouble did {hero.label} and {friend.label} discover?",
            answer=f"They discovered that {incident.danger}.",
        ),
        QAItem(
            question="What did the friends decide to do?",
            answer=f"They decided to {incident.fix}.",
        ),
        QAItem(
            question="How did bravery change the story?",
            answer=f"The hero chose to {bravery.choice}, so {bravery.consequence}.",
        ),
        QAItem(
            question="What moral value did the friends learn?",
            answer="They learned that bravery means choosing a helpful action even when hiding would be easier.",
        ),
    ]


def world_knowledge_qa() -> list[QAItem]:
    return [
        QAItem(
            question="What is a tidal pool?",
            answer="A tidal pool is a small pool of seawater left among rocks when the tide goes out.",
        ),
        QAItem(
            question="Why can a tide change a tidal pool?",
            answer="The tide can bring in more water, move objects, and change which paths are safe.",
        ),
        QAItem(
            question="What is grass?",
            answer="Grass is a green plant with narrow leaves that can grow in soil or, in this story, resemble sea grass.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: kind={entity.kind}, location={entity.location}, "
            f"meters={entity.meters}, memes={entity.memes}"
        )
    lines.append(f"  resolved={world.facts.get('resolved')}")
    return "\n".join(lines)


ASP_RULES = r"""
place(tidal_pool).
feature(angle).
feature(grass).
feature(drove).
value(moral_value).
value(surprise).
value(bravery).
style(comedy).
valid(tidal_pool,angle,grass,drove).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("place", "tidal_pool"),
            asp.fact("feature", "angle"),
            asp.fact("feature", "grass"),
            asp.fact("feature", "drove"),
            asp.fact("value", "moral_value"),
            asp.fact("value", "surprise"),
            asp.fact("value", "bravery"),
            asp.fact("style", "comedy"),
        ]
    )


def asp_program(show: str = "#show valid/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [("tidal_pool", "angle", "grass", "drove")]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    clingo_values = set(asp_valid_combos())
    if py == clingo_values:
        print("OK: ASP and Python validation agree.")
        return 0
    print("Mismatch between ASP and Python validation.")
    print("Python only:", sorted(py - clingo_values))
    print("ASP only:", sorted(clingo_values - py))
    return 1


def emit(sample: StorySample, *, trace: bool, qa: bool, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        for prompt in sample.prompts:
            print(f"\n[Prompt] {prompt}")
        for item in sample.story_qa + sample.world_qa:
            print(f"\nQ: {item.question}\nA: {item.answer}")


CURATED = [
    StoryParams("Luna", "Milo", "an old limpet", "wide", "eelgrass", "crabs", "octopus", "speak", "dance"),
    StoryParams("Nora", "Pip", "a kindly sea star", "crooked", "floating", "hermits", "mirror", "share", "flag"),
    StoryParams("Tavi", "Cleo", "the pool keeper", "secret", "tiny_lawn", "snails", "pearl", "ask", "shell"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        for index in range(max(1, args.n)):
            seed = base_seed + index
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
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

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
