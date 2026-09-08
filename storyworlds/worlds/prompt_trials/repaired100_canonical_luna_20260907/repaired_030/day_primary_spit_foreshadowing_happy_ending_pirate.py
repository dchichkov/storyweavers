#!/usr/bin/env python3
"""
A small pirate-tale storyworld about a bright day, a primary-school crew,
and a silly spit of sea spray that warns them of a coming squall.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE)))))
sys.path.insert(0, os.path.join(ROOT, "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)

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
    day: str
    primary: str
    spit: str
    captain: str
    mate: str
    helper: str
    lesson: str
    ending: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Day:
    name: str
    opening: str
    weather_hint: str
    treasure: str


@dataclass(frozen=True)
class Primary:
    name: str
    phrase: str
    skill: str


@dataclass(frozen=True)
class Spit:
    name: str
    phrase: str
    clue: str
    danger: str
    fix: str


DAYS = {
    "bright_monday": Day(
        "bright Monday",
        "The sun spilled gold across the harbor on a bright Monday.",
        "a thin gray feather rested beneath the sunny sky",
        "a brass school bell hidden in a sea chest",
    ),
    "blue_tuesday": Day(
        "blue Tuesday",
        "The sea shone blue on a breezy Tuesday morning.",
        "the gulls flew inland instead of circling the waves",
        "a pearl compass tucked inside a barrel",
    ),
    "golden_wednesday": Day(
        "golden Wednesday",
        "A golden Wednesday warmed the little pirate ship.",
        "the warm wind suddenly smelled of wet rope",
        "a map stamped with a smiling kraken",
    ),
    "quiet_thursday": Day(
        "quiet Thursday",
        "On a quiet Thursday, the harbor barely rocked.",
        "the quiet water began to tap against the hull",
        "a silver whistle beneath the captain's chair",
    ),
    "cheerful_friday": Day(
        "cheerful Friday",
        "A cheerful Friday found the young crew polishing the deck.",
        "one far cloud folded itself into a dark tower",
        "a box of cinnamon biscuits for the whole crew",
    ),
}

PRIMARYS = {
    "school": Primary("primary school", "the harbor primary school", "reading tiny marks on old sea maps"),
    "class": Primary("primary class", "the island primary class", "tying knots that held firm but came loose easily"),
    "club": Primary("primary club", "the primary-school sailing club", "spotting safe paths through busy water"),
    "crew": Primary("primary crew", "the primary-school pirate crew", "sharing jobs without leaving anyone behind"),
}

SPITS = {
    "seaspray": Spit(
        "sea spit",
        "a bright spit of sea spray",
        "the sea was breathing hard beneath the calm",
        "a squall would soon shove the ship toward the black rocks",
        "reef the sail, tie down the treasure chest, and steer into the sheltered cove",
    ),
    "foam": Spit(
        "foam spit",
        "a little spit of white foam",
        "a strong current was turning beneath the boat",
        "the ship would drift across the ferry lane",
        "raise the blue flag, ring the bell, and row toward the quiet inlet",
    ),
    "spray": Spit(
        "spray spit",
        "a cold spit of spray",
        "rain was hiding beyond the sunny horizon",
        "the deck would soon become slippery",
        "rub sand on the deck, lower the ladder, and guide everyone below",
    ),
    "salt": Spit(
        "salt spit",
        "a salty spit from the waves",
        "the tide had begun to rise faster than expected",
        "the low dock would soon disappear under the water",
        "move the rowboats uphill and carry the supplies to the lighthouse",
    ),
}

CAPTAINS = ["Luna", "Pip", "Mara", "Cato", "Nia", "Rafi"]
MATES = ["Tess", "Finn", "Jo", "Omar", "Bea", "Sol"]
HELPERS = ["the kindly harbor teacher", "the old lighthouse keeper", "the smiling dock cook"]

LESSONS = {
    "listen": "careful listeners notice danger before loud sailors do",
    "share": "a crew is strongest when every small hand has a useful job",
    "ask": "asking for help is a brave part of being a captain",
    "wait": "waiting for the right moment can save a whole ship",
}

ENDINGS = {
    "feast": "That evening, the harbor held a feast, and every child received the first warm biscuit.",
    "lanterns": "At sunset, the crew lit lanterns along the cove, and their safe ship glowed like a little star.",
    "bell": "The brass bell rang from the mast, not for danger, but to celebrate the crew's happy return.",
    "rainbow": "When the clouds opened, a rainbow arched above the sheltered cove like a promise kept.",
}

VALID_COMBOS = [("harbor", p, s) for p in PRIMARYS for s in SPITS]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Primary-school pirate tale storyworld.")
    parser.add_argument("--day", choices=DAYS)
    parser.add_argument("--primary", choices=PRIMARYS)
    parser.add_argument("--spit", choices=SPITS)
    parser.add_argument("--captain")
    parser.add_argument("--mate")
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--lesson", choices=LESSONS)
    parser.add_argument("--ending", choices=ENDINGS)
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
    if args.primary and args.primary not in PRIMARYS:
        raise StoryError("Choose a primary-school setting from the available choices.")
    if args.spit and args.spit not in SPITS:
        raise StoryError("Choose a recognized kind of sea spit.")
    captain = args.captain or rng.choice(CAPTAINS)
    mate = args.mate or rng.choice([x for x in MATES if x != captain])
    if captain == mate:
        raise StoryError("The captain and mate need different names.")
    return StoryParams(
        day=args.day or rng.choice(tuple(DAYS)),
        primary=args.primary or rng.choice(tuple(PRIMARYS)),
        spit=args.spit or rng.choice(tuple(SPITS)),
        captain=captain,
        mate=mate,
        helper=args.helper or rng.choice(HELPERS),
        lesson=args.lesson or rng.choice(tuple(LESSONS)),
        ending=args.ending or rng.choice(tuple(ENDINGS)),
    )


def tell(params: StoryParams) -> World:
    day = DAYS[params.day]
    primary = PRIMARYS[params.primary]
    spit = SPITS[params.spit]
    world = World()
    captain = world.add(Entity(params.captain, "character", "child", params.captain, "deck"))
    mate = world.add(Entity(params.mate, "character", "child", params.mate, "deck"))
    helper = world.add(Entity("helper", "character", "adult", params.helper, "harbor"))
    ship = world.add(Entity("ship", "vehicle", "boat", "the little ship", "harbor"))
    sea = world.add(Entity("sea", "nature", "sea", "the sea", "harbor"))
    world.facts.update(day=day, primary=primary, spit=spit, captain=captain, mate=mate, helper=helper, ship=ship, sea=sea)

    world.say(f"On {day.name}, {primary.phrase} came aboard a little pirate ship in the harbor.")
    world.say(f"Captain {captain.id} held the wheel, while {mate.id} practiced {primary.skill}.")
    world.say(f"They hoped to find {day.treasure} before lunch.")
    world.para()

    world.say(f"The morning looked calm, but {day.weather_hint}.")
    world.say(f"Then {spit.phrase} flew over the rail and landed on Captain {captain.id}'s boot.")
    world.say(f'"That is only a silly splash," said {mate.id}. "Can we sail on?"')
    world.say(f'"A spit can be a message," Captain {captain.id} replied. "What do you think it tells us?"')
    world.facts["foreshadowing"] = spit.clue
    world.say(f"The {spit.name} was a warning: {spit.clue}.")
    world.para()

    captain.meters["attention"] = 1.0
    mate.meters["attention"] = 1.0
    captain.memes["responsibility"] = 1.0
    mate.memes["curiosity"] = 1.0
    world.say(f"Just then, {params.helper} called from the dock, 'The clouds are changing! Check the water before you choose a course.'")
    world.say(f'"I want to race toward the treasure," {mate.id} admitted.')
    world.say(f'"And I want everyone safe," {captain.id} answered. "Let us use the clue before we move."')
    world.say(f"They watched the sea, listened to {params.helper}, and chose to {spit.fix}.")
    world.facts["plan"] = spit.fix
    world.para()

    world.say(f"The warning proved true. {spit.danger.capitalize()}.")
    world.say(f"Because the children had noticed the {spit.name}, they were ready instead of frightened.")
    world.say(f"{captain.id} gave {mate.id} the rope, and {mate.id} gave the captain the map.")
    world.say(f"Together, they followed the safe plan while {params.helper} guided them from the shore.")
    world.facts["changed"] = "the ship reached the sheltered cove with every sailor safe"
    world.say("The squall passed over the open water, and the little ship reached the sheltered cove with every sailor safe.")
    world.para()

    lesson = LESSONS[params.lesson]
    world.say(f"Captain {captain.id} smiled. 'Today we learned that {lesson}.'")
    world.say(f"{mate.id} nodded. 'Next time I see a spit, I will listen before I laugh.'")
    world.say(ENDINGS[params.ending])
    world.say("The primary-school pirates cheered, and the sea shone peacefully behind them.")
    world.facts["lesson"] = lesson
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    day = world.facts["day"]
    primary = world.facts["primary"]
    spit = world.facts["spit"]
    return [
        f"Write a Pirate Tale set on {day.name} with a {primary.name} crew.",
        f"Use {spit.phrase} as foreshadowing for a danger at sea.",
        "Give the children a spoken exchange, a careful choice, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    captain = world.facts["captain"]
    mate = world.facts["mate"]
    helper = world.facts["helper"]
    spit = world.facts["spit"]
    return [
        QAItem(
            f"Who sailed the little pirate ship?",
            f"Captain {captain.id} and {mate.id} sailed it with help from {helper.label}.",
        ),
        QAItem(
            "What did the spit foreshadow?",
            f"The {spit.name} foreshadowed that {spit.clue}, so the crew needed to act carefully.",
        ),
        QAItem(
            "How did the crew stay safe?",
            f"They chose to {world.facts['plan']}, and the ship reached the sheltered cove with every sailor safe.",
        ),
        QAItem(
            "What did the children learn?",
            f"They learned that {world.facts['lesson']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a pirate ship?",
            "A pirate ship is a boat used in a sea adventure, often with a captain, a crew, sails, and a map.",
        ),
        QAItem(
            "Why can a small sign such as sea spray matter?",
            "A small sign can matter because it may reveal a larger change in the weather or water before the danger arrives.",
        ),
        QAItem(
            "Why should a crew listen to one another?",
            "A crew should listen to one another because shared information helps everyone make safer choices.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:8} ({entity.type:7}) location={entity.location} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  foreshadowing: {world.facts.get('foreshadowing')}")
    lines.append(f"  plan: {world.facts.get('plan')}")
    lines.append(f"  resolved: {world.facts.get('resolved')}")
    return "\n".join(lines)


ASP_RULES = r"""
place(harbor).
setting(harbor).
primary(school).
primary(class).
primary(club).
primary(crew).
spit(seaspray).
spit(foam).
spit(spray).
spit(salt).

valid(harbor, school, seaspray).
valid(harbor, school, foam).
valid(harbor, school, spray).
valid(harbor, school, salt).
valid(harbor, class, seaspray).
valid(harbor, class, foam).
valid(harbor, class, spray).
valid(harbor, class, salt).
valid(harbor, club, seaspray).
valid(harbor, club, foam).
valid(harbor, club, spray).
valid(harbor, club, salt).
valid(harbor, crew, seaspray).
valid(harbor, crew, foam).
valid(harbor, crew, spray).
valid(harbor, crew, salt).

happy_ending_required.
foreshadowing_required.
"""


def asp_facts() -> str:
    import asp
    facts = [asp.fact("place", "harbor")]
    facts.extend(asp.fact("primary", key) for key in PRIMARYS)
    facts.extend(asp.fact("spit", key) for key in SPITS)
    return "\n".join(facts)


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(VALID_COMBOS)
    clingo_combos = set(asp_valid_combos())
    if py != clingo_combos:
        print("MISMATCH between Python and ASP valid combinations.")
        print("Only in Python:", sorted(py - clingo_combos))
        print("Only in ASP:", sorted(clingo_combos - py))
        return 1
    rng = random.Random(19)
    for _ in range(3):
        params = resolve_params(build_parser().parse_args([]), rng)
        sample = generate(params)
        if not sample.story or "safely" not in sample.story:
            print("Generated-story verification failed.")
            return 1
    print(f"OK: ASP/Python parity holds for {len(py)} combinations, and stories resolve safely.")
    return 0


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


def show_qa_item(item: QAItem) -> str:
    return f"Q: {item.question}\nA: {item.answer}"


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        for prompt in sample.prompts:
            print(f"\n[Prompt] {prompt}")
        for item in sample.story_qa + sample.world_qa:
            print("\n" + show_qa_item(item))


CURATED = [
    StoryParams("bright_monday", "school", "seaspray", "Luna", "Finn", "the kindly harbor teacher", "listen", "lanterns"),
    StoryParams("blue_tuesday", "club", "foam", "Mara", "Jo", "the old lighthouse keeper", "share", "rainbow"),
    StoryParams("golden_wednesday", "crew", "spray", "Pip", "Tess", "the smiling dock cook", "ask", "feast"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combinations:")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        for offset in range(max(args.n * 20, 50)):
            if len(samples) >= args.n:
                break
            try:
                params = resolve_params(args, random.Random(base_seed + offset))
            except StoryError as error:
                print(error)
                return
            params.seed = base_seed + offset
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
