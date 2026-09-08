#!/usr/bin/env python3
"""
A small standalone Superhero Story world about bacon, a surprising twist,
and reconciliation after a hasty attempt to remove a problem.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"heroine", "girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"hero", "boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}


@dataclass
class World:
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
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    hero: str
    helper: str
    city: str
    hideout: str
    seed: Optional[int] = None
    scenario: Optional[str] = None
    telling_mode: Optional[str] = None


@dataclass(frozen=True)
class Scenario:
    key: str
    premise: str
    bacon_problem: str
    rushed_action: str
    consequence: str
    clue: str
    twist: str
    careful_action: str
    apology: str
    repair: str
    outcome: str
    lesson: str
    ending: str


HERO_NAMES = ["Luna", "Maya", "Ruby", "Nia", "Zara", "Piper"]
HELPER_NAMES = ["Finn", "Theo", "Jo", "Milo", "Sam", "Kai"]
CITIES = [
    "Brighton City",
    "Sunbeam City",
    "Moonrise City",
    "Maple City",
]
HIDEOUTS = [
    "the rooftop kitchen",
    "the old clock tower",
    "the bright garage",
    "the garden clubhouse",
]
TELLING_MODES = ["alarm", "dialogue", "mystery", "promise", "countdown", "arrival"]

SCENARIOS = [
    Scenario(
        key="breakfast_bridge",
        premise="was carrying a giant breakfast tray to the workers repairing the city bridge",
        bacon_problem="a long strip of sizzling bacon had wrapped around the bridge's emergency lever",
        rushed_action="used a gust of super-breath to remove the bacon",
        consequence="the lever flipped and lowered the bridge before the workers were ready",
        clue="the bacon twitched whenever the bridge bell rang",
        twist="the bacon was actually a tiny sound-loving rescue creature hiding from the storm",
        careful_action="matched the bridge bell with a soft hum and waited for the creature to loosen its grip",
        apology="admitted that the first blast had frightened the little creature and startled the bridge workers",
        repair="guided the creature into a warm basket and reset the lever with the workers",
        outcome="the bridge opened safely, and the creature helped warn everyone when the bell rang",
        lesson="a strange thing may need understanding before anyone tries to remove it",
        ending="the rescue creature shared a crisp bacon-shaped snack with the grateful bridge crew",
    ),
    Scenario(
        key="festival_griddle",
        premise="was delivering breakfast for the city's annual Lantern Festival",
        bacon_problem="a sparkling bacon ribbon had plugged the festival griddle",
        rushed_action="pulled hard to remove the ribbon",
        consequence="the griddle bounced across the square and sent pancake batter toward the lanterns",
        clue="the ribbon glowed in the same rhythm as the lantern music",
        twist="the bacon ribbon was a lost parade dragon's tail, and the dragon was stuck beneath the griddle",
        careful_action="played the festival rhythm while lifting the griddle one inch at a time",
        apology="said that pulling first had made the parade dragon more scared",
        repair="freed the dragon and helped it rejoin the parade",
        outcome="the dragon danced safely while cooks served warm breakfasts",
        lesson="careful listening can reveal who needs help",
        ending="lanterns bobbed above the square as the dragon wagged its bacon-bright tail",
    ),
    Scenario(
        key="powerhouse_picnic",
        premise="was bringing bacon sandwiches to families waiting beside the city's power station",
        bacon_problem="a greasy bacon bundle had blocked the station's cooling fan",
        rushed_action="used a magnetic glove to remove the bundle",
        consequence="the fan stopped and the station began to overheat",
        clue="the bundle's loose threads pointed toward a trapped maintenance drone",
        twist="the bacon was not trash at all; it was a heat-proof blanket wrapped around the drone",
        careful_action="used a cool beam to lower the temperature before opening the blanket",
        apology="explained that the quick removal had nearly left the drone in the heat",
        repair="cooled the fan, freed the drone, and secured the blanket properly",
        outcome="the station hummed again and the families received their sandwiches",
        lesson="protecting something often matters more than making it look tidy",
        ending="the little drone beeped thanks beside a picnic basket full of bacon sandwiches",
    ),
    Scenario(
        key="museum_alarm",
        premise="was guarding a school visit at the city's superhero museum",
        bacon_problem="a strip of glowing bacon had curled around the museum alarm button",
        rushed_action="tried to remove it with a laser finger",
        consequence="the alarm rang and every superhero statue began to spin",
        clue="the strip displayed tiny pictures whenever a child told a brave story",
        twist="the bacon was a magical story-scroll that had escaped from an old hero's lunchbox",
        careful_action="asked the children to tell a calm story about helping a friend",
        apology="admitted that the laser had erased one corner of the story-scroll",
        repair="rewrote the missing corner and returned the scroll to its lunchbox",
        outcome="the statues stopped spinning and the museum alarm became a gentle story bell",
        lesson="a mistake can be repaired when people tell the truth and help",
        ending="the children heard the story bell and saw the glowing bacon curl safely back into place",
    ),
    Scenario(
        key="rainy_rooftop",
        premise="was delivering warm food to neighbors sheltering on a rooftop",
        bacon_problem="a bacon-shaped cloud had clogged the rain collector",
        rushed_action="used a thunder clap to remove the cloud",
        consequence="rainwater splashed over the roof and soaked the food",
        clue="the cloud released drops only when a lonely neighbor laughed",
        twist="the cloud was a shy weather helper trying to make a private umbrella",
        careful_action="invited the neighbor to share a joke while shaping the cloud into a wide canopy",
        apology="said the thunder clap had ruined the first meal and frightened the weather helper",
        repair="cleared the collector gently and taught the cloud how to gather rain safely",
        outcome="the roof stayed dry and everyone shared a fresh second meal",
        lesson="kindness can turn a troublesome surprise into a helpful friend",
        ending="the bacon-shaped cloud floated above the roof like a soft silver umbrella",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Superhero Story world about bacon, removal, twist, and reconciliation."
    )
    parser.add_argument("--hero", choices=HERO_NAMES)
    parser.add_argument("--helper", choices=HELPER_NAMES)
    parser.add_argument("--city", choices=CITIES)
    parser.add_argument("--hideout", choices=HIDEOUTS)
    parser.add_argument("--scenario", choices=[s.key for s in SCENARIOS])
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
    return StoryParams(
        hero=hero,
        helper=helper,
        city=args.city or rng.choice(CITIES),
        hideout=args.hideout or rng.choice(HIDEOUTS),
        scenario=args.scenario or rng.choice(SCENARIOS).key,
        telling_mode=args.telling_mode or rng.choice(TELLING_MODES),
    )


def _opening(params: StoryParams, scenario: Scenario) -> list[str]:
    mode = params.telling_mode or "arrival"
    if mode == "alarm":
        return [
            f'"Bacon trouble at the bridge!" {params.helper} cried from {params.hideout}.',
            f"Hero {params.hero} raced across {params.city} because the team {scenario.premise}.",
        ]
    if mode == "dialogue":
        return [
            f'"Ready for a simple delivery?" {params.hero} asked.',
            f'"With us, nothing stays simple," {params.helper} replied as they left {params.hideout}.',
        ]
    if mode == "mystery":
        return [
            f"A strange sizzling sound drifted over {params.city}.",
            f"Hero {params.hero} and {params.helper} followed it from {params.hideout} while the team {scenario.premise}.",
        ]
    if mode == "promise":
        return [
            f"Hero {params.hero} had promised to help the people of {params.city}.",
            f"From {params.hideout}, the hero and {params.helper} hurried out because the team {scenario.premise}.",
        ]
    if mode == "countdown":
        return [
            f"The warning clock above {params.city} blinked ten red times.",
            f"Before it reached zero, Hero {params.hero} and {params.helper} had to act while the team {scenario.premise}.",
        ]
    return [
        f"Hero {params.hero} and {params.helper} left {params.hideout} to help {params.city}.",
        f"The team {scenario.premise}.",
    ]


def generate(params: StoryParams) -> StorySample:
    if params.hero == params.helper:
        raise StoryError("The hero and helper must have different names.")
    if params.scenario not in {scenario.key for scenario in SCENARIOS}:
        raise StoryError(f"Unknown scenario: {params.scenario}")
    scenario = next(item for item in SCENARIOS if item.key == params.scenario)

    world = World()
    hero = world.add(
        Entity(
            id=params.hero,
            kind="character",
            type="heroine",
            label="superhero",
            phrase=f"Hero {params.hero}",
            location=params.city,
            meters={"courage": 1.0, "power": 1.0},
            memes={"helpfulness": 1.0},
            traits=["brave", "curious"],
        )
    )
    helper = world.add(
        Entity(
            id=params.helper,
            kind="character",
            type="helper",
            label="sidekick",
            phrase=params.helper,
            location=params.city,
            meters={"care": 1.0},
            memes={"trust": 1.0},
            traits=["observant", "kind"],
        )
    )
    bacon = world.add(
        Entity(
            id="bacon",
            kind="thing",
            type="bacon",
            label="bacon",
            phrase="the strange bacon",
            location=params.city,
            meters={"sizzle": 1.0, "danger": 0.7},
            memes={"mystery": 1.0, "friendship": 0.0},
        )
    )
    world.facts.update(
        hero=hero,
        helper=helper,
        bacon=bacon,
        city=params.city,
        scenario=scenario.key,
        premise=scenario.premise,
        bacon_problem=scenario.bacon_problem,
        rushed_action=scenario.rushed_action,
        consequence=scenario.consequence,
        clue=scenario.clue,
        twist=scenario.twist,
        careful_action=scenario.careful_action,
        apology=scenario.apology,
        repair=scenario.repair,
        outcome=scenario.outcome,
        reconciliation=False,
    )

    for sentence in _opening(params, scenario):
        world.say(sentence)
    world.say(f"Then they discovered that {scenario.bacon_problem}.")

    world.para()
    world.say(
        f'"I will remove it before anyone gets hurt," {params.hero} promised, and {params.hero} {scenario.rushed_action}.'
    )
    world.say(f"But the rushed choice caused a new problem: {scenario.consequence}.")
    world.say(
        f'"Wait," {params.helper} said. "The bacon is reacting to something. Let us watch before we act again."'
    )

    world.para()
    world.say(f"Together they noticed that {scenario.clue}.")
    world.say(f"That clue revealed the twist: {scenario.twist}.")
    world.say(f"Hero {params.hero} chose a gentler plan and {scenario.careful_action}.")
    world.say(
        f"The danger softened, but the first mistake still needed an honest answer. {params.helper} {scenario.apology}."
    )

    world.para()
    world.say(
        f'"Thank you for telling me," Hero {params.hero} replied. "We can repair this together."'
    )
    world.say(f"Together they {scenario.repair}.")
    world.say(f"At last, {scenario.outcome}.")

    world.para()
    world.say(f"The heroes learned that {scenario.lesson}.")
    world.say(
        f"Their reconciliation made the rescue stronger because both friends could trust one another again."
    )
    world.say(f"As evening settled over {params.city}, {scenario.ending}.")

    bacon.location = "safe and understood"
    bacon.meters["danger"] = 0.0
    bacon.meters["sizzle"] = 0.4
    bacon.memes["mystery"] = 0.0
    bacon.memes["friendship"] = 1.0
    helper.memes["trust"] = 1.0
    hero.memes["reconciliation"] = 1.0
    world.facts["reconciliation"] = True
    world.facts["story_end"] = "safe friendship"

    prompts = [
        f"Write a child-friendly Superhero Story about {params.hero} and {params.helper}, including bacon that someone tries to remove.",
        f"Tell a story with a surprising twist: {scenario.twist}. End with reconciliation.",
        f"Write a superhero rescue in {params.city} that shows this lesson: {scenario.lesson}.",
    ]
    story_qa = [
        QAItem(
            question="What bacon problem did the heroes discover?",
            answer=f"They discovered that {scenario.bacon_problem}.",
        ),
        QAItem(
            question=f"Why did {params.hero}'s first attempt cause trouble?",
            answer=f"{params.hero} {scenario.rushed_action}, and that caused {scenario.consequence}.",
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that {scenario.twist}.",
        ),
        QAItem(
            question="How did the heroes repair the mistake?",
            answer=f"They listened, apologized, and then {scenario.repair}. This led to the result that {scenario.outcome}.",
        ),
        QAItem(
            question="What did reconciliation change?",
            answer="Reconciliation restored trust between the heroes, so they could finish the rescue as a team.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change in what the characters thought was happening.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making peace and rebuilding trust after a mistake or disagreement.",
        ),
        QAItem(
            question="Why should a superhero pause before removing something strange?",
            answer="Pausing can reveal whether the strange object is dangerous, helpful, or someone who needs care.",
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
            details = []
            if entity.location:
                details.append(f"location={entity.location}")
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
    import asp

    return "\n".join(
        [
            asp.fact("domain", "superhero_story"),
            asp.fact("seed_word", "bacon"),
            asp.fact("seed_word", "remove"),
            asp.fact("feature", "twist"),
            asp.fact("feature", "reconciliation"),
            asp.fact("object", "bacon"),
            asp.fact("action", "remove"),
            asp.fact("requires", "bacon", "understanding"),
            asp.fact("requires", "mistake", "apology"),
        ]
    )


ASP_RULES = r"""
#show feature/1.
#show seed_word/1.
#show object/1.
#show action/1.
#show valid/1.

valid(story) :- feature(twist), feature(reconciliation), object(bacon), action(remove).
"""


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show valid/1."))
    valid = asp.atoms(model, "valid")
    features = sorted(asp.atoms(model, "feature"))
    if valid != [("story",)] or features != [("reconciliation",), ("twist",)]:
        print("MISMATCH: ASP story requirements are incomplete.")
        return 1
    try:
        sample = generate(
            StoryParams(
                hero="Luna",
                helper="Finn",
                city="Brighton City",
                hideout="the rooftop kitchen",
                seed=7,
                scenario="breakfast_bridge",
                telling_mode="dialogue",
            )
        )
    except StoryError as exc:
        print(f"MISMATCH: generated story rejected: {exc}")
        return 1
    required = ["bacon", "remove", "twist", "reconciliation"]
    if not all(word in (sample.story.lower() + " " + " ".join(q.answer.lower() for q in sample.story_qa)) for word in required):
        print("MISMATCH: generated story does not exercise required narrative instruments.")
        return 1
    print("OK: ASP and Python story requirements agree.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show feature/1."))
        return
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show feature/1."))
        print(json.dumps({"features": asp.atoms(model, "feature")}, indent=2))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(
                hero="Luna",
                helper="Finn",
                city="Brighton City",
                hideout="the rooftop kitchen",
                seed=101,
                scenario="breakfast_bridge",
                telling_mode="dialogue",
            ),
            StoryParams(
                hero="Maya",
                helper="Theo",
                city="Sunbeam City",
                hideout="the old clock tower",
                seed=202,
                scenario="festival_griddle",
                telling_mode="mystery",
            ),
            StoryParams(
                hero="Ruby",
                helper="Jo",
                city="Moonrise City",
                hideout="the bright garage",
                seed=303,
                scenario="museum_alarm",
                telling_mode="alarm",
            ),
        ]
        samples = [generate(params) for params in curated]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 20):
            attempt += 1
            attempt_seed = base_seed + attempt
            params = resolve_params(args, random.Random(attempt_seed))
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
        if args.all:
            params = sample.params
            header = f"### {params.hero} and {params.helper} in {params.city}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
