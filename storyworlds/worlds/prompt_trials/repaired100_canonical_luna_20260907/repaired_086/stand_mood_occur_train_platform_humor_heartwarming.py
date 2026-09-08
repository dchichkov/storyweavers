#!/usr/bin/env python3
"""Heartwarming StoryWorld about a train-platform stand, a changing mood, and humor."""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
sys.path.insert(0, os.path.dirname(_storyworlds_dir))
from results import QAItem, StoryError, StorySample  # noqa: E402


NAMES = ["Luna", "Milo", "Priya", "Theo", "June", "Owen", "Ada", "Nico"]
HELPERS = ["Grandma Rose", "Mr. Bell", "Aunt May", "Conductor Sam"]
PLACES = ["the little town train platform", "Willow Platform", "the sunny platform by the clock"]
INCIDENT_IDS = ("trolley", "hat", "ticket", "umbrella", "lunch")
OPENINGS = (
    "On a bright morning",
    "Just before the noon train",
    "While the platform clock ticked gently",
    "On a chilly afternoon",
    "As golden light touched the rails",
)
JOKES = (
    '"Perhaps the train is wearing invisible socks," Luna joked.',
    '"I hope the conductor has checked the train\'s funny bone," Luna said.',
    '"Maybe the suitcase is practicing hide-and-seek," Luna laughed.',
    '"If the timetable sneezes, we will know," Luna said with a grin.',
)
BRIDGES = (
    "The joke made the worried faces soften enough for everyone to look closely.",
    "A small laugh gave the waiting crowd courage to help instead of complain.",
    "The silliness did not erase the trouble, but it made room for a kind idea.",
    "People smiled, then noticed the useful clue they had missed.",
)


@dataclass(frozen=True)
class Incident:
    id: str
    sign: str
    worry: str
    cause: str
    clue: str
    helper_action: str
    luna_action: str
    repair: str
    ending: str
    lesson: str


INCIDENTS = (
    Incident(
        "trolley",
        "a tiny luggage trolley rolling in slow circles",
        "the train might leave before an elderly traveler could find her bag",
        "one wheel had caught on a loose yellow strap",
        "the strap was looped around the wheel",
        "held the trolley steady",
        "followed the strap to its knot",
        "freeing the wheel and returning the suitcase",
        "the trolley standing quietly beside its grateful owner",
        "a calm look and a kind hand can turn a muddle into a welcome",
    ),
    Incident(
        "hat",
        "a blue hat bobbing along the edge of the platform",
        "someone might step too close to the rails while chasing it",
        "a warm gust had lifted the hat from a bench",
        "the hat had snagged on a safe fence post",
        "asked everyone to stay behind the line",
        "pointed out the snag instead of chasing the hat",
        "retrieving it with the conductor's long-handled hook",
        "the blue hat resting safely on its owner's head",
        "safety matters even when a problem looks funny",
    ),
    Incident(
        "ticket",
        "a family searching every pocket for one missing ticket",
        "their holiday trip would begin with tears",
        "the ticket had slipped inside a folded map",
        "the map was thicker at one corner",
        "offered a seat and a careful search",
        "noticed the map's secret paper pocket",
        "finding the ticket before boarding",
        "the family waving from the window with relieved smiles",
        "patience helps hidden answers appear",
    ),
    Incident(
        "umbrella",
        "an umbrella opening and closing like a nervous bird",
        "it might bump a passerby or block the station sign",
        "a bent spoke had caught in the fabric",
        "the umbrella clicked at the same spot each time",
        "made space around the owner",
        "listened for the repeated click",
        "folding it safely and tying it with a ribbon",
        "the umbrella resting like a sleepy flower",
        "noticing a pattern is better than blaming the person nearby",
    ),
    Incident(
        "lunch",
        "a lunchbox making a soft rattling sound",
        "someone might think a little creature was trapped inside",
        "a spoon had slipped from its loop",
        "the rattle stopped whenever the box was held upright",
        "kept curious children behind the bench",
        "tested the box gently instead of shaking it",
        "putting the spoon back beside the sandwiches",
        "the lunchbox quiet while its owner shared an apple",
        "gentle tests can replace alarming guesses",
    ),
)


@dataclass
class Entity:
    id: str
    type: str
    label: str
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    place: str
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

    def copy(self) -> "World":
        return copy.deepcopy(self)


@dataclass
class StoryParams:
    place: str
    traveler_name: str
    helper_name: str
    incident_id: str
    opening_id: int
    joke_id: int
    bridge_id: int
    seed: Optional[int] = None


def incident_for(identifier: str) -> Incident:
    for incident in INCIDENTS:
        if incident.id == identifier:
            return incident
    raise StoryError(f"Unknown platform incident: {identifier}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Heartwarming train-platform StoryWorld about stand, mood, occur, and humor."
    )
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--traveler-name", choices=NAMES)
    parser.add_argument("--helper-name", choices=HELPERS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument(f"--{flag}", action="store_true", dest=flag.replace("-", "_"))
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        place=args.place or rng.choice(PLACES),
        traveler_name=args.traveler_name or rng.choice(NAMES),
        helper_name=args.helper_name or rng.choice(HELPERS),
        incident_id=rng.choice(INCIDENT_IDS),
        opening_id=rng.randrange(len(OPENINGS)),
        joke_id=rng.randrange(len(JOKES)),
        bridge_id=rng.randrange(len(BRIDGES)),
    )


def tell(params: StoryParams) -> World:
    incident = incident_for(params.incident_id)
    world = World(params.place)
    traveler = world.add(
        Entity(
            id="traveler",
            type="child",
            label=params.traveler_name,
            role="observant platform helper",
            meters={"distance_to_safe_line": 1.0, "attention": 0.4},
            memes={"mood": 0.35, "worry": 0.65},
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            type="adult",
            label=params.helper_name,
            role="station helper",
            meters={"distance_to_safe_line": 1.0},
            memes={"patience": 0.9, "kindness": 0.9},
        )
    )
    world.add(
        Entity(
            id="platform",
            type="place",
            label=params.place,
            role="train platform",
            meters={"safe_line_width": 1.0},
            memes={"welcome": 0.8},
        )
    )
    world.facts.update(
        incident=incident,
        traveler=traveler,
        helper=helper,
        mood_before="worried",
        mood_after="hopeful",
        resolved=False,
        safe_stance=True,
    )

    world.say(f"{OPENINGS[params.opening_id]}, {traveler.label} came to {params.place} with {helper.label}.")
    world.say(f"They planned to stand behind the bright safety line and wait for the morning train.")
    world.say(f"Then {incident.sign} began to occur.")
    world.say(f"The platform's happy mood changed, because {incident.worry}.")
    world.para()

    world.say(f"{traveler.label} took one step toward the trouble, but {helper.label} gently raised a hand.")
    world.say(f'"We can help while we stand safely here," {helper.label} said.')
    world.say(f'"And we can think before we panic," {traveler.label} replied.')
    world.say(JOKES[params.joke_id])
    world.say(BRIDGES[params.bridge_id])
    world.say(f"The laugh helped {traveler.label} notice that {incident.clue}.")
    world.para()

    world.say(f"{helper.label} {incident.helper_action}, while {traveler.label} {incident.luna_action}.")
    world.say(f"Together they discovered that {incident.cause}.")
    world.say(f"They worked carefully on {incident.repair}.")
    world.say(f"The worried traveler thanked them, and the platform mood grew warm again.")
    world.say(f'"A good stand, a good plan, and one good joke," {helper.label} said.')
    world.say(f'"That is how a small rescue can occur," {traveler.label} answered.')
    world.para()

    world.say(f"When the train arrived, {incident.ending}.")
    world.say(f"{traveler.label} learned that {incident.lesson}.")
    world.say("Everyone boarded with lighter hearts, and the platform seemed to smile beneath its round clock.")

    traveler.meters.update(distance_to_safe_line=1.0, attention=1.0)
    traveler.memes.update(mood=0.95, worry=0.0, courage=0.9)
    world.facts.update(resolved=True, mood_before="worried", mood_after="hopeful")
    return world


def generation_prompts(world: World) -> list[str]:
    incident = world.facts["incident"]
    traveler = world.facts["traveler"].label
    return [
        f"Write a heartwarming train-platform story in which {traveler} must stand safely while {incident.sign} occurs.",
        f"Tell a humorous story about a platform problem that changes a worried mood into a hopeful one.",
        f"Use the words stand, mood, and occur, and end with a kind train-platform image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    incident = world.facts["incident"]
    traveler = world.facts["traveler"].label
    helper = world.facts["helper"].label
    return [
        QAItem(
            question=f"What caused {traveler}'s worried mood?",
            answer=f"{traveler} saw {incident.sign}, and worried that {incident.worry}.",
        ),
        QAItem(
            question="How did the characters stay safe?",
            answer=f"They stood behind the bright safety line while {helper} guided the help.",
        ),
        QAItem(
            question="What clue helped solve the problem?",
            answer=f"They noticed that {incident.clue}, which revealed that {incident.cause}.",
        ),
        QAItem(
            question="How did humor change the story?",
            answer="The joke made people laugh, softened the worried mood, and helped everyone think clearly enough to notice a useful clue.",
        ),
        QAItem(
            question="What happened at the end?",
            answer=f"They completed {incident.repair}, and then {incident.ending}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why should people stand behind a train-platform safety line?",
            answer="The line keeps waiting passengers away from the edge and gives trains room to pass safely.",
        ),
        QAItem(
            question="What is a mood?",
            answer="A mood is the feeling that colors how someone experiences a moment. It can change when people receive help or understand a problem.",
        ),
        QAItem(
            question="How can humor help during a small problem?",
            answer="Kind humor can lower fear and invite people to think together, but it should never make fun of someone who needs help.",
        ),
        QAItem(
            question="What does it mean for an event to occur?",
            answer="It means that the event happens. In this world, a safe response follows when something unexpected occurs on the platform.",
        ),
    ]


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


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("\n== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== (3) World questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: {entity.type} {entity.label} role={entity.role} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    for key in ("mood_before", "mood_after", "safe_stance", "resolved"):
        lines.append(f"  fact.{key}={world.facts.get(key)}")
    incident = world.facts["incident"]
    lines.append(f"  fact.cause={incident.cause}")
    lines.append(f"  fact.clue={incident.clue}")
    return "\n".join(lines)


ASP_RULES = """
valid_story :-
    setting(train_platform),
    feature(humor),
    style(heartwarming),
    seed_word(stand),
    seed_word(mood),
    seed_word(occur),
    safety(safe_stance),
    resolution(kind_help).
#show valid_story/0.
""".strip()


def asp_facts() -> str:
    import asp

    facts = [
        ("setting", "train_platform"),
        ("feature", "humor"),
        ("style", "heartwarming"),
        ("seed_word", "stand"),
        ("seed_word", "mood"),
        ("seed_word", "occur"),
        ("safety", "safe_stance"),
        ("resolution", "kind_help"),
    ]
    return "\n".join(asp.fact(name, value) for name, value in facts)


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    symbols = asp.one_model(asp_program())
    accepted = any(symbol.name == "valid_story" for symbol in symbols)
    if not accepted:
        print("Mismatch: ASP rejected the train-platform story.")
        return 1
    for params in CURATED:
        sample = generate(params)
        if not sample.story or not sample.world.facts["resolved"]:
            print("Mismatch: generated story failed its resolution gate.")
            return 1
    print("OK: ASP and Python accepted safe, humorous, heartwarming platform stories.")
    return 0


CURATED = [
    StoryParams("the little town train platform", "Luna", "Grandma Rose", "trolley", 0, 0, 0),
    StoryParams("Willow Platform", "Milo", "Mr. Bell", "hat", 1, 1, 1),
    StoryParams("the sunny platform by the clock", "Priya", "Aunt May", "ticket", 2, 2, 2),
    StoryParams("the little town train platform", "Theo", "Conductor Sam", "umbrella", 3, 3, 3),
    StoryParams("Willow Platform", "June", "Grandma Rose", "lunch", 4, 0, 1),
]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print("\n" + format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp

        symbols = asp.one_model(asp_program())
        print("compatible story:")
        for symbol in symbols:
            print(symbol)
        return

    base = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(100, args.n * 40):
            seed = base + attempt
            attempt += 1
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
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
