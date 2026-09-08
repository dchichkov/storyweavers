#!/usr/bin/env python3
"""
A standalone fairy-tale storyworld about a speck, a guarantee, and a promise
that must be tested by action.

The world follows Luna, a young keeper of the Moon Tower. A single dark speck
appears on the tower's silver beacon. The royal guarantee says the beacon must
shine every night, but a frightened moth has hidden inside the lamp. Luna's
inner thoughts, repeated words, and bright sound effects guide her from worry
to a gentle repair.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while ROOT != os.path.dirname(ROOT):
    if os.path.exists(os.path.join(ROOT, "results.py")):
        break
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)

from results import QAItem, StoryError, StorySample  # noqa: E402


ENTITY_HUMAN = "human"
ENTITY_ANIMAL = "animal"
ENTITY_OBJECT = "object"


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    phrase: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = ""
    owner: Optional[str] = None


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


@dataclass
class StoryParams:
    setting: str
    hero: str
    moth: str
    beacon: str
    trial: str = "speck"
    opening_style: int = 0
    echo_style: int = 0
    sound_style: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class Trial:
    concern: str
    discovery: str
    first_attempt: str
    need: str
    promise: str
    repair: str
    ending: str
    lesson: str


SETTINGS = {
    "moon_tower": "the Moon Tower",
    "cloud_castle": "the Cloud Castle",
    "silver_hill": "Silver Hill",
    "star_village": "Star Village",
}

HERO_NAMES = ["Luna", "Mira", "Elin", "Tessa", "Nell", "Orla"]
MOTH_NAMES = ["Moth", "Mimi", "Flick", "Dusk", "Pip"]
BEACON_NAMES = ["Moonbeam", "Silver Eye", "Night Star", "Lantern Crown"]

TRIALS = {
    "speck": Trial(
        concern="A tiny black speck dimmed the great silver beacon",
        discovery="heard a soft shiver inside the glass",
        first_attempt="polished the outside until her cloth shone, but the speck stayed",
        need="was hiding from the cold wind and had mistaken the warm beacon for a flower",
        promise="I will keep the night bright, and I will keep you safe",
        repair="opened the little service door, held a warm cup of tea nearby, and guided the moth toward a velvet-lined box",
        ending="When the beacon shone again, the rescued moth rested on its rim like a small brown star",
        lesson="A guarantee is strongest when it protects the small life inside the promise.",
    ),
    "crumb": Trial(
        concern="A golden crumb blocked one of the beacon's star-shaped windows",
        discovery="saw tiny teeth marks along the crumb",
        first_attempt="scrubbed at it with a silver brush, but the crumb only broke into more crumbs",
        need="had carried food into the warm tower after losing its way in the snow",
        promise="I will make the window clear, and I will not leave you hungry",
        repair="placed a little dish of oats by the stair and rolled the crumbs onto it",
        ending="The last crumb became a moon-shaped biscuit shared beneath the shining window",
        lesson="A promise can be kept without making a frightened guest pay for being hungry.",
    ),
    "thread": Trial(
        concern="A red thread stretched across the beacon and painted a crooked line on the sky",
        discovery="heard a faint, tired whimper behind the winding glass",
        first_attempt="pulled the thread sharply, and the whole lantern trembled",
        need="had tangled its wing in the thread while carrying it from a torn festival banner",
        promise="I will mend the banner and free your wing gently",
        repair="cut the thread beside the knot, freed the wing, and stitched the banner with moon-silver cord",
        ending="The repaired banner fluttered above the tower while the beacon drew a straight road of light",
        lesson="Gentle hands can mend both a creature and the work it tried to save.",
    ),
    "rain": Trial(
        concern="A cold drop slid through the beacon and made its flame blink",
        discovery="found a shivering moth beneath the lamp's copper hood",
        first_attempt="held a cloth under the leak, but the cloth soon became heavy",
        need="had flown into the tower to escape a sudden storm",
        promise="I will stop the rain without trapping you",
        repair="tilted a copper leaf over the crack and left a warm path open toward the window",
        ending="Rain drummed on the roof while the beacon glowed steadily over the wet kingdom",
        lesson="Safety needs both shelter and a way out.",
    ),
}

OPENINGS = [
    "{hero} was the youngest keeper of {setting}, where one silver beacon watched over the sleeping land.",
    "At the tallest window of {setting}, {hero} polished the night light before the stars came out.",
    "Long ago, {hero} learned that even a great promise might hide a very small problem.",
    "Every evening, {hero} climbed the moonlit stairs of {setting} with a lantern, a cloth, and a careful heart.",
]

ECHOES = [
    "Keep the light, keep the light, keep the light.",
    "A promise is a promise. A promise is a promise.",
    "Look closely, look closely, look closely.",
    "Small things matter. Small things matter.",
]

SOUNDS = [
    "Clink-clink went the little key.",
    "Whirr, whirr, whispered the turning wheel.",
    "Tap! Tap! answered the rain.",
    "Ffffft! fluttered the moth's wings.",
    "Hushhh went the moonlit stair.",
    "Ping! sang the silver latch.",
]

ASP_RULES = r"""
% The beacon is troubled when a speck remains and its light is not steady.
troubled(B) :- beacon(B), speck(B), not steady(B).

% A gentle repair makes the promise reliable and protects the hidden guest.
reliable(B) :- beacon(B), opened(B), guided_guest(B), steady(B).

% A valid fairy-tale trial must move from trouble to a protective repair.
valid_story(T) :- trial(T), troubled(beacon), reliable(beacon), guarantee_kept(T).
"""


def asp_facts() -> str:
    import asp

    lines = [asp.fact("beacon", "beacon")]
    for trial in TRIALS:
        lines.append(asp.fact("trial", trial))
    lines.extend(
        [
            asp.fact("speck", "beacon"),
            asp.fact("opened", "beacon"),
            asp.fact("guided_guest", "beacon"),
            asp.fact("steady", "beacon"),
            asp.fact("guarantee_kept", "speck"),
            asp.fact("guarantee_kept", "crumb"),
            asp.fact("guarantee_kept", "thread"),
            asp.fact("guarantee_kept", "rain"),
        ]
    )
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    expected = set(TRIALS)
    actual = {trial for (trial,) in asp_valid()}
    if expected == actual:
        print(f"OK: ASP model covers {len(expected)} fairy-tale trials.")
        return 0
    print("MISMATCH between Python and ASP trial coverage.")
    print("only python:", sorted(expected - actual))
    print("only asp:", sorted(actual - expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A fairy-tale storyworld about Luna, a speck, and a guarantee."
    )
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--hero")
    parser.add_argument("--moth")
    parser.add_argument("--beacon")
    parser.add_argument("--trial", choices=TRIALS)
    parser.add_argument("--opening-style", type=int)
    parser.add_argument("--echo-style", type=int)
    parser.add_argument("--sound-style", type=int)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    hero = args.hero or rng.choice(HERO_NAMES)
    moth = args.moth or rng.choice(MOTH_NAMES)
    beacon = args.beacon or rng.choice(BEACON_NAMES)
    trial = args.trial or rng.choice(list(TRIALS))
    opening_style = (
        args.opening_style
        if args.opening_style is not None
        else rng.randrange(len(OPENINGS))
    )
    echo_style = (
        args.echo_style
        if args.echo_style is not None
        else rng.randrange(len(ECHOES))
    )
    sound_style = (
        args.sound_style
        if args.sound_style is not None
        else rng.randrange(len(SOUNDS))
    )
    return StoryParams(
        setting=setting,
        hero=hero,
        moth=moth,
        beacon=beacon,
        trial=trial,
        opening_style=opening_style % len(OPENINGS),
        echo_style=echo_style % len(ECHOES),
        sound_style=sound_style % len(SOUNDS),
    )


def validate_params(params: StoryParams) -> None:
    if not params.hero.strip() or not params.moth.strip() or not params.beacon.strip():
        raise StoryError("Hero, guest, and beacon names must not be empty.")
    if params.hero.casefold() == params.moth.casefold():
        raise StoryError("The keeper and the moth need different names.")
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}.")
    if params.trial not in TRIALS:
        raise StoryError(f"Unknown trial: {params.trial}.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(SETTINGS[params.setting])

    hero = world.add(
        Entity(
            id="hero",
            kind=ENTITY_HUMAN,
            type="keeper",
            label=params.hero,
            phrase=f"the young keeper {params.hero}",
            meters={"care": 0.0, "promise": 0.0},
            memes={"worry": 0.0, "courage": 0.0, "wonder": 0.0},
            location="tower stair",
        )
    )
    moth = world.add(
        Entity(
            id="moth",
            kind=ENTITY_ANIMAL,
            type="moth",
            label=params.moth,
            phrase=f"a small moth named {params.moth}",
            meters={"hidden": 1.0, "safe": 0.0, "flutter": 1.0},
            memes={"fear": 1.0, "trust": 0.0},
            location="inside beacon",
        )
    )
    beacon = world.add(
        Entity(
            id="beacon",
            kind=ENTITY_OBJECT,
            type="silver beacon",
            label=params.beacon,
            phrase=f"the silver beacon called {params.beacon}",
            meters={"bright": 0.0, "speck": 1.0, "steady": 0.0},
            memes={"duty": 1.0},
            location="tower crown",
        )
    )
    guarantee = world.add(
        Entity(
            id="guarantee",
            kind=ENTITY_OBJECT,
            type="royal guarantee",
            label="guarantee",
            phrase="the royal guarantee",
            meters={"kept": 0.0},
            memes={"trust": 1.0},
            location="tower wall",
        )
    )

    world.facts.update(
        params=params,
        trial=TRIALS[params.trial],
        hero=hero,
        moth=moth,
        beacon=beacon,
        guarantee=guarantee,
        clue_found=False,
        dialogue_changed_action=False,
        guest_guided=False,
        resolved=False,
    )
    return world


def act_opening(world: World) -> None:
    params = world.facts["params"]
    trial = world.facts["trial"]
    hero = world.get("hero")
    beacon = world.get("beacon")
    guarantee = world.get("guarantee")

    world.say(
        OPENINGS[params.opening_style].format(
            hero=hero.label,
            setting=world.setting,
        )
    )
    world.say(
        f"On that evening, {hero.label} found {trial.concern} in {beacon.phrase}."
    )
    world.say(
        f"The {guarantee.label} written on the wall said, "
        f"\"The light shall guide every traveler home.\""
    )
    world.say(
        f"{hero.label} thought, \"If I cannot mend this, the whole valley may lose its road. "
        f"But what if the speck is not a stain?\""
    )
    world.say(ECHOES[params.echo_style])


def act_first_try(world: World) -> None:
    hero = world.get("hero")
    beacon = world.get("beacon")
    trial = world.facts["trial"]

    hero.memes["worry"] = 1.0
    world.say(f"{hero.label} lifted {beacon.phrase} toward the moon and listened.")
    world.say(SOUNDS[world.facts["params"].sound_style])
    world.say(
        f"First, {hero.label} {trial.first_attempt}. "
        f"The {beacon.label} still gave only a weak, winking glow."
    )
    beacon.meters["bright"] = 0.2
    world.say(
        f"\"Again,\" whispered {hero.label}. \"Again, again.\" "
        f"Yet the repeated rubbing changed nothing."
    )


def act_discovery(world: World) -> None:
    hero = world.get("hero")
    moth = world.get("moth")
    trial = world.facts["trial"]

    world.say(f"Then {hero.label} {trial.discovery}.")
    world.say(
        f"\"Who is there?\" asked {hero.label}. "
        f"From inside the glass came a tiny voice: \"Please do not make the dark angry.\""
    )
    world.say(
        f"{hero.label} answered, \"I will not. Tell me what you need.\" "
        f"The voice replied, \"I {trial.need}.\""
    )
    world.facts["clue_found"] = True
    world.facts["dialogue_changed_action"] = True
    world.get("hero").memes["wonder"] = 1.0
    world.get("moth").memes["fear"] = 0.5


def act_guarantee(world: World) -> None:
    hero = world.get("hero")
    moth = world.get("moth")
    guarantee = world.get("guarantee")
    trial = world.facts["trial"]

    hero.memes["courage"] = 1.0
    hero.meters["care"] = 1.0
    hero.meters["promise"] = 1.0
    guarantee.meters["kept"] = 1.0

    world.say(
        f"{hero.label} read the {guarantee.label} once more, then changed what its words meant."
    )
    world.say(f"\"{trial.promise},\" said {hero.label}.")
    world.say(
        f"{moth.label} asked, \"Even if I am only a speck in your grand light?\" "
        f"{hero.label} replied, \"Especially then.\""
    )
    world.say(
        f"That answer mattered. {moth.label} stopped trembling, and {hero.label} "
        f"opened the small silver door."
    )
    world.say(SOUNDS[(world.facts["params"].sound_style + 2) % len(SOUNDS)])

    moth.meters["hidden"] = 0.0
    moth.memes["trust"] = 1.0
    world.facts["guest_guided"] = True


def act_repair(world: World) -> None:
    hero = world.get("hero")
    moth = world.get("moth")
    beacon = world.get("beacon")
    trial = world.facts["trial"]

    world.say(f"Carefully, {hero.label} {trial.repair}.")
    world.say(
        f"{moth.label} fluttered toward the safe box. "
        f"Ffffft! Ffffft! went the little wings, slower each time."
    )
    moth.location = "velvet-lined box"
    moth.meters["safe"] = 1.0
    moth.meters["flutter"] = 0.3
    beacon.meters["speck"] = 0.0
    beacon.meters["bright"] = 1.0
    beacon.meters["steady"] = 1.0
    world.facts["resolved"] = True


def act_ending(world: World) -> None:
    hero = world.get("hero")
    beacon = world.get("beacon")
    trial = world.facts["trial"]

    world.para()
    world.say(
        f"The speck was gone, not because {hero.label} had crushed it, "
        f"but because {hero.label} had understood it."
    )
    world.say(
        f"{beacon.phrase} shone across the roofs, steady and warm, while {hero.label} "
        f"watched the safe box beside the open window."
    )
    world.say(trial.ending)
    world.say(
        f"\"The guarantee is kept,\" said {hero.label}. "
        f"\"The light for the travelers, and the shelter for the small.\""
    )
    world.say(ECHOES[(world.facts["params"].echo_style + 1) % len(ECHOES)])
    world.say(trial.lesson)


def tell_story(params: StoryParams) -> World:
    world = build_world(params)
    act_opening(world)
    world.para()
    act_first_try(world)
    act_discovery(world)
    act_guarantee(world)
    act_repair(world)
    act_ending(world)
    return world


def generation_prompts(world: World) -> list[str]:
    params = world.facts["params"]
    trial = world.facts["trial"]
    return [
        f"Write a child-friendly fairy tale about {params.hero}, a speck, and a guarantee in {world.setting}.",
        f"Use inner monologue, repetition, and sound effects as {params.hero} discovers that {params.moth} {trial.need}.",
        f"End with a concrete image showing that the beacon is bright and the hidden guest is safe: {trial.ending}",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.get("hero")
    moth = world.get("moth")
    beacon = world.get("beacon")
    trial = world.facts["trial"]

    return [
        QAItem(
            question=f"What trouble did {hero.label} find in {world.setting}?",
            answer=f"{hero.label} found {trial.concern} in {beacon.phrase}.",
        ),
        QAItem(
            question=f"Why did the speck appear in the beacon?",
            answer=f"The speck was actually connected to {moth.label}, who {trial.need}.",
        ),
        QAItem(
            question=f"What did {hero.label} first try?",
            answer=f"{hero.label} {trial.first_attempt}.",
        ),
        QAItem(
            question=f"What did {hero.label} promise?",
            answer=f"{hero.label} promised, \"{trial.promise}.\"",
        ),
        QAItem(
            question=f"How did the spoken exchange change the story?",
            answer=f"When {moth.label} explained the need, {hero.label} stopped treating the speck as a mere stain and chose a careful repair.",
        ),
        QAItem(
            question="How was the guarantee kept?",
            answer=f"{hero.label} repaired the beacon so it shone steadily while also protecting {moth.label}; {trial.ending}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a speck?",
            answer="A speck is a very small spot or particle.",
        ),
        QAItem(
            question="What is a guarantee?",
            answer="A guarantee is a promise that something will happen or be protected.",
        ),
        QAItem(
            question="What is inner monologue?",
            answer="Inner monologue is a character's unspoken thought, shown so readers can understand the character's feelings or decision.",
        ),
        QAItem(
            question="Why can repetition help a fairy tale?",
            answer="Repetition gives important words a memorable rhythm and can show growing courage or certainty.",
        ),
        QAItem(
            question="What do sound effects do in a story?",
            answer="Sound effects such as 'Clink-clink' or 'Ffffft' let readers imagine the action more vividly.",
        ),
        QAItem(
            question="What kind of transformation happens in this story?",
            answer="The transformation is a change in understanding: a frightening speck becomes a small guest to protect, and the promise becomes a caring action.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
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
        details = []
        if entity.meters:
            details.append(f"meters={entity.meters}")
        if entity.memes:
            details.append(f"memes={entity.memes}")
        if entity.location:
            details.append(f"location={entity.location}")
        lines.append(
            f"{entity.id}: {entity.label} ({entity.type}) {' '.join(details)}"
        )
    lines.append(f"facts: {world.facts}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(
        setting="moon_tower",
        hero="Luna",
        moth="Mimi",
        beacon="Moonbeam",
        trial="speck",
        opening_style=0,
        echo_style=0,
        sound_style=0,
    ),
    StoryParams(
        setting="cloud_castle",
        hero="Mira",
        moth="Flick",
        beacon="Silver Eye",
        trial="crumb",
        opening_style=1,
        echo_style=1,
        sound_style=1,
    ),
    StoryParams(
        setting="silver_hill",
        hero="Elin",
        moth="Dusk",
        beacon="Night Star",
        trial="thread",
        opening_style=2,
        echo_style=2,
        sound_style=2,
    ),
    StoryParams(
        setting="star_village",
        hero="Orla",
        moth="Pip",
        beacon="Lantern Crown",
        trial="rain",
        opening_style=3,
        echo_style=3,
        sound_style=3,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        print("Compatible ASP fairy-tale trials:")
        for trial, in asp_valid():
            print(f"  {trial}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for params in CURATED:
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 30):
            seed = base_seed + attempts
            attempts += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            try:
                sample = generate(params)
            except StoryError as exc:
                print(exc)
                return
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if not samples:
        raise StoryError("No stories could be generated.")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            params = sample.params
            header = (
                f"### {params.hero} / {params.moth} / {params.beacon} "
                f"in {params.setting}"
            )
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
