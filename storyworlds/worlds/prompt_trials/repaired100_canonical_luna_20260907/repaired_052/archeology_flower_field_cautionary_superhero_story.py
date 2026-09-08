#!/usr/bin/env python3
"""
A small standalone storyworld about an archeology rescue in a flower field.
The story uses superhero energy while showing why careful choices matter.
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

STORYWORLDS_ROOT = Path(__file__).resolve().parents[2]
if str(STORYWORLDS_ROOT) not in sys.path:
    sys.path.insert(0, str(STORYWORLDS_ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    type: str
    label: str
    location: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "hero"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

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
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


@dataclass
class StoryParams:
    hero: str
    helper: str
    field: str
    artifact: str
    seed: Optional[int] = None
    scenario: Optional[str] = None
    telling_mode: Optional[str] = None


@dataclass(frozen=True)
class Scenario:
    key: str
    discovery: str
    danger: str
    rash_action: str
    consequence: str
    clue: str
    careful_action: str
    truth: str
    repair: str
    rescue: str
    lesson: str
    ending: str


HERO_NAMES = ["Luna", "Mara", "Sora", "Tess", "Nia", "Pia"]
HELPER_NAMES = ["Ollie", "Ben", "Milo", "Ren", "Kai", "Jo"]
FIELDS = [
    "the golden flower field",
    "the red poppy meadow",
    "the bluebell field",
    "the sunflower plain",
]
ARTIFACTS = [
    "a buried moon-clay mask",
    "an old sunstone",
    "a tiny bronze bell",
    "a painted seed jar",
]
TELLING_MODES = ["arrival", "warning", "dialogue", "mystery", "countdown", "promise"]

SCENARIOS = [
    Scenario(
        key="moon_mask",
        discovery="was studying a buried moon-clay mask beneath a ring of daisies",
        danger="a bright crack opened under the flower roots",
        rash_action="lifted the mask with her super-strength",
        consequence="the ground shuddered and the flowers began sliding toward the crack",
        clue="the mask's painted eyes pointed toward three flat stones nearby",
        careful_action="used her careful vision to read the faded marks before touching anything else",
        truth="the mask was a marker for a safe path around an old spring",
        repair="placed the mask back on its stone stand and set the three stones in a gentle arc",
        rescue="the crack closed and the flowers rose safely from the loosened soil",
        lesson="a strong hero must use patience before power",
        ending="the moon-clay mask rested among the daisies while Luna guarded the quiet field",
    ),
    Scenario(
        key="sunstone",
        discovery="had found an old sunstone beneath a bed of yellow flowers",
        danger="the stone began pulling every metal garden tool toward it",
        rash_action="wrapped it in her cape and flew upward",
        consequence="the tools followed in a spinning cloud above the field",
        clue="the sunstone dimmed whenever the helper hummed a slow tune",
        careful_action="asked her helper to keep humming while she lowered the stone into a clay basket",
        truth="the sunstone was an ancient alarm that answered only a calm keeper's song",
        repair="returned the basket to its marked hollow and sang the old tune together",
        rescue="the tools dropped harmlessly and the flower field became still again",
        lesson="speed and strength are less useful than listening when a mystery is old",
        ending="the sunstone gave one warm blink beneath the flowers, as if thanking its careful keepers",
    ),
    Scenario(
        key="bronze_bell",
        discovery="was brushing soil from a tiny bronze bell in the middle of the field",
        danger="the bell's first ring woke a gust that bent the tallest flowers",
        rash_action="grabbed the bell and tried to fly it away",
        consequence="the gust chased her across the meadow and scattered loose seed packets",
        clue="the bell rang softly only when its shadow touched a circle of white petals",
        careful_action="followed the shadow and placed the bell inside that petal circle",
        truth="the bell was an old weather signal meant to call gentle rain, not a weapon",
        repair="cleared the petal circle and rang the bell once at the proper mark",
        rescue="the wind softened and a silver drizzle watered the thirsty flowers",
        lesson="an object should be understood before a hero tries to control it",
        ending="tiny raindrops shone on every petal while the bronze bell slept in its circle",
    ),
    Scenario(
        key="seed_jar",
        discovery="was uncovering a painted seed jar hidden below the flower field",
        danger="the jar's lid popped open and a cloud of glowing seeds rose into the air",
        rash_action="used her super-breath to blow the seeds back down",
        consequence="the seeds scattered beyond the field toward a busy road",
        clue="each seed glowed brightest beside a flower of the same color",
        careful_action="asked her helper to name the colors while she caught each seed in a soft net",
        truth="the jar held a careful planting map made by the field's first gardeners",
        repair="matched every seed to its color and returned the map to the jar",
        rescue="the seeds settled into safe furrows and the road stayed clear",
        lesson="even a helpful power can cause harm when used without a plan",
        ending="new colored rows curved through the field like a rainbow drawn by gardeners",
    ),
    Scenario(
        key="stone_bee",
        discovery="was tracing an ancient bee symbol carved on a flat stone",
        danger="the stone vibrated and a giant shadow swept over the flowers",
        rash_action="leaped into the air and punched at the shadow",
        consequence="the startled bees abandoned their hives and the field grew suddenly quiet",
        clue="the bee symbol matched a small crack beside the oldest hive",
        careful_action="lowered her fists and placed the stone beside the crack",
        truth="the stone was a welcome sign for a gentle guardian bee, not a monster's trap",
        repair="reopened the hive path and waited quietly for the guardian to return",
        rescue="the bees came back and carried pollen between the flowers once more",
        lesson="bravery means knowing when not to fight",
        ending="a golden bee circled Luna's badge before returning to the humming flowers",
    ),
    Scenario(
        key="rainbow_tile",
        discovery="was mapping a rainbow tile found beneath a patch of clover",
        danger="the tile flashed and made the field's paths twist into a maze",
        rash_action="ran forward at superhero speed to find the exit",
        consequence="she became lost while her helper waited alone near the dig",
        clue="the tile's colors repeated in the order of the flowers around the field",
        careful_action="walked slowly and copied the color order with flower petals",
        truth="the tile was an ancient direction sign designed to be read at walking speed",
        repair="placed the petals along the correct path and returned the tile to its shallow bed",
        rescue="the maze straightened and the two friends found one another safely",
        lesson="going fast is not the same as making progress",
        ending="a clear path led through the flowers, marked by six bright petals and a careful smile",
    ),
]

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Cautionary superhero archeology stories in a flower field."
    )
    parser.add_argument("--hero", choices=HERO_NAMES)
    parser.add_argument("--helper", choices=HELPER_NAMES)
    parser.add_argument("--field", choices=FIELDS)
    parser.add_argument("--artifact", choices=ARTIFACTS)
    parser.add_argument("--scenario", choices=[item.key for item in SCENARIOS])
    parser.add_argument("--telling-mode", choices=TELLING_MODES)
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
    hero = args.hero or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice([name for name in HELPER_NAMES if name != hero])
    field = args.field or rng.choice(FIELDS)
    artifact = args.artifact or rng.choice(ARTIFACTS)
    return StoryParams(
        hero=hero,
        helper=helper,
        field=field,
        artifact=artifact,
        seed=args.seed,
        scenario=args.scenario or rng.choice(SCENARIOS).key,
        telling_mode=args.telling_mode or rng.choice(TELLING_MODES),
    )


def _opening(params: StoryParams, scenario: Scenario) -> list[str]:
    hero = params.hero
    helper = params.helper
    mode = params.telling_mode or "arrival"
    if mode == "warning":
        return [
            f'"Careful, {hero}," {helper} warned as they entered {params.field}.',
            f"The young superhero had come for archeology: she {scenario.discovery}.",
        ]
    if mode == "dialogue":
        return [
            f'"Do we touch the artifact yet?" {helper} asked. "Not until we understand it," {hero} replied.',
            f"Together they entered {params.field}, where the archeology dig had uncovered something important.",
        ]
    if mode == "mystery":
        return [
            f"Something under {params.field} made the flowers tremble.",
            f"{hero} and {helper} followed the clue and found that the dig {scenario.discovery}.",
        ]
    if mode == "countdown":
        return [
            f"The field's old warning flag fluttered three times as {hero} arrived.",
            f"Before the last flutter, the superhero and {helper} discovered that the dig {scenario.discovery}.",
        ]
    if mode == "promise":
        return [
            f"{hero} had promised to protect the flower field while learning its history.",
            f"With {helper} beside her, she began the archeology dig and {scenario.discovery}.",
        ]
    return [
        f"{hero} came to {params.field} wearing a bright cape and carrying a small archeology brush.",
        f"Her helper, {helper}, watched as she {scenario.discovery}.",
    ]


def generate(params: StoryParams) -> StorySample:
    if not params.hero or not params.helper:
        raise StoryError("A hero and helper are required.")
    if params.hero == params.helper:
        raise StoryError("The hero and helper must have different names.")
    if params.scenario not in {item.key for item in SCENARIOS}:
        raise StoryError(f"Unknown scenario: {params.scenario}")

    scenario = next(item for item in SCENARIOS if item.key == params.scenario)
    world = World(setting=params.field)

    hero = world.add(
        Entity(
            id=params.hero,
            type="hero",
            label="young superhero",
            location=params.field,
            meters={"strength": 1.0, "flight": 1.0, "care": 0.4},
            memes={"curiosity": 1.0, "caution": 0.5},
        )
    )
    helper = world.add(
        Entity(
            id=params.helper,
            type="boy",
            label="archeology helper",
            location=params.field,
            meters={"observation": 1.0, "voice": 0.8},
            memes={"trust": 1.0, "caution": 1.0},
        )
    )
    artifact = world.add(
        Entity(
            id="artifact",
            type="artifact",
            label=params.artifact,
            location="shallow dig",
            meters={"mystery": 1.0, "danger": 0.7},
            memes={"history": 1.0, "meaning": 0.2},
        )
    )
    world.facts.update(
        scenario=scenario.key,
        discovery=scenario.discovery,
        danger=scenario.danger,
        rash_action=scenario.rash_action,
        consequence=scenario.consequence,
        clue=scenario.clue,
        truth=scenario.truth,
        repair=scenario.repair,
        rescue=scenario.rescue,
        lesson=scenario.lesson,
        setting=params.field,
        theme="archeology",
        feature="Cautionary",
        style="Superhero Story",
    )

    for sentence in _opening(params, scenario):
        world.say(sentence)
    world.say(f"Then the dig changed: {scenario.danger}.")

    world.para()
    world.say(
        f'"I can handle it!" {hero.id} cried, and {hero.pronoun()} {scenario.rash_action}.'
    )
    world.say(f"But the hurried choice had a cost: {scenario.consequence}.")
    world.say(
        f'"Wait," {helper.id} said. "The past is trying to tell us something." '
        f'{hero.id} lowered {hero.pronoun("possessive")} hands.'
    )

    world.para()
    world.say(f"Together they watched the artifact instead of guessing. They noticed that {scenario.clue}.")
    world.say(f"{hero.id} chose a safer power and {scenario.careful_action}.")
    world.say(f"The hidden history became clear: {scenario.truth}.")

    world.para()
    world.say(
        f'"I used my power before I understood the danger," {hero.id} admitted. '
        f'"Next time, we investigate first."'
    )
    world.say(
        f'"That is what makes a hero careful," {helper.id} answered. '
        f'"Let us repair the dig together."'
    )
    world.say(f"Working side by side, they {scenario.repair}.")
    world.say(f"At once, {scenario.rescue}.")

    world.para()
    world.say(f"They remembered that {scenario.lesson}.")
    world.say(f"The lesson mattered because the field was not just a place to save; it was a piece of history to respect.")
    world.say(scenario.ending)

    artifact.location = "protected display hollow"
    artifact.meters["danger"] = 0.0
    artifact.meters["mystery"] = 0.2
    artifact.memes["meaning"] = 1.0
    hero.meters["care"] = 1.0
    hero.memes["caution"] = 1.0
    world.facts.update(resolved=True, repaired=True, caution_learned=True)

    prompts = [
        f"Write a Cautionary Superhero Story about {params.hero} investigating {params.field}. Include archeology and the danger that {scenario.danger}.",
        f"Tell a child-friendly superhero tale where {params.hero} learns that {scenario.lesson}.",
        f"Create a flower-field adventure in which {params.hero} and {params.helper} use evidence to solve an old mystery.",
    ]
    story_qa = [
        QAItem(
            question=f"What did {params.hero} discover during the archeology dig?",
            answer=f"{params.hero} discovered that the dig {scenario.discovery}.",
        ),
        QAItem(
            question="What danger appeared?",
            answer=f"The danger was that {scenario.danger}.",
        ),
        QAItem(
            question=f"Why did {params.hero}'s first choice cause trouble?",
            answer=f"{params.hero} acted before understanding the artifact, so {scenario.consequence}.",
        ),
        QAItem(
            question="What clue helped the friends solve the mystery?",
            answer=f"They noticed that {scenario.clue}. That clue showed them that {scenario.truth}.",
        ),
        QAItem(
            question="How did the story end safely?",
            answer=f"They repaired the dig by making sure that {scenario.repair}. As a result, {scenario.rescue}.",
        ),
        QAItem(
            question="What cautionary lesson did the hero learn?",
            answer=f"The hero learned that {scenario.lesson}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is archeology?",
            answer="Archeology is the careful study of objects and places from long ago to learn how people lived.",
        ),
        QAItem(
            question="Why should an explorer investigate before using great power?",
            answer="An explorer should investigate first because an unfamiliar object may have a purpose, and a rushed action can damage it or make danger worse.",
        ),
        QAItem(
            question="What makes a superhero story cautionary?",
            answer="A cautionary superhero story shows that bravery needs judgment, so the hero learns from a risky choice and uses power more wisely.",
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
        print("--- world model state ---")
        for entity in sample.world.entities.values():
            details = [f"location={entity.location}"]
            if entity.meters:
                details.append(f"meters={entity.meters}")
            if entity.memes:
                details.append(f"memes={entity.memes}")
            print(f"  {entity.id}: {entity.type} {' '.join(details)}")
    if qa:
        print("\n== prompts ==")
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"{index}. {prompt}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def asp_facts() -> str:
    from asp import fact
    return "\n".join(
        [
            fact("domain", "archeology"),
            fact("setting", "flower_field"),
            fact("feature", "cautionary"),
            fact("style", "superhero_story"),
            fact("requires", "careful_investigation"),
            fact("requires", "repair"),
        ]
    )


ASP_RULES = r"""
valid :- domain(archeology), setting(flower_field), feature(cautionary),
         style(superhero_story), requires(careful_investigation),
         requires(repair).
#show valid/0.
#show domain/1.
#show setting/1.
#show feature/1.
#show style/1.
#show requires/1.
"""


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    valid = asp.atoms(model, "valid")
    required = sorted(asp.atoms(model, "requires"))
    if valid and required == [("careful_investigation",), ("repair",)]:
        sample = generate(
            StoryParams(
                hero="Luna",
                helper="Ollie",
                field=FIELDS[0],
                artifact=ARTIFACTS[0],
                seed=17,
                scenario="moon_mask",
                telling_mode="dialogue",
            )
        )
        checks = [
            "archeology" in sample.story.lower(),
            "flower" in sample.story.lower(),
            "careful" in sample.story.lower(),
            len(sample.story_qa) >= 5,
            "artifact" not in sample.story_qa[0].answer.lower(),
        ]
        if all(checks):
            print("OK: ASP/Python parity and generated-story checks passed.")
            return 0
    print("MISMATCH: ASP/Python parity or story checks failed.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/0."))
        return
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print(json.dumps({"valid": bool(asp.atoms(model, "valid")), "facts": asp_facts().splitlines()}, indent=2))
        return
    if args.verify:
        raise SystemExit(asp_verify())

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Luna", "Ollie", FIELDS[0], ARTIFACTS[0], 101, "moon_mask", "dialogue"),
            StoryParams("Mara", "Ben", FIELDS[1], ARTIFACTS[1], 202, "sunstone", "warning"),
            StoryParams("Sora", "Milo", FIELDS[2], ARTIFACTS[2], 303, "bronze_bell", "mystery"),
            StoryParams("Tess", "Ren", FIELDS[3], ARTIFACTS[3], 404, "seed_jar", "promise"),
            StoryParams("Nia", "Kai", FIELDS[0], ARTIFACTS[0], 505, "stone_bee", "arrival"),
            StoryParams("Pia", "Jo", FIELDS[1], ARTIFACTS[1], 606, "rainbow_tile", "countdown"),
        ]
        samples = [generate(item) for item in curated]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n:
            attempt += 1
            if attempt > max(100, args.n * 30):
                raise StoryError("Could not produce enough distinct stories.")
            attempt_seed = base_seed + attempt
            rng = random.Random(attempt_seed)
            params = resolve_params(args, rng)
            params.seed = attempt_seed
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
            header = f"### {sample.params.hero} in {sample.params.field}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
