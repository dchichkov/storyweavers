#!/usr/bin/env python3
"""
A standalone Comedy storyworld about a limousine, an accord, and a lesson learned.

The simulation follows Luna, a young helper whose grand plan for a limousine
ride goes awry when two passengers make a very different accord. Physical
meters track the limousine, its loose horn, and a rolled-up banner; emotional
memes track pride, worry, trust, and amusement. The prose is driven by the
state changes and ends with a clear lesson learned.
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
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


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
            self.meters = {"loose": 0.0, "clean": 0.0, "ready": 0.0}
        if not self.memes:
            self.memes = {"pride": 0.0, "worry": 0.0, "trust": 0.0, "amusement": 0.0}


@dataclass
class Setting:
    name: str
    place: str
    affordances: set[str]


@dataclass
class StoryParams:
    setting: str
    hero_type: str
    companion_type: str
    hero_name: str
    companion_name: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Incident:
    title: str
    destination: str
    passenger_problem: str
    horn_clue: str
    banner_clue: str
    foolish_try: str
    repair: str
    lesson: str
    ending: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def paragraph(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "station": Setting("station", "the old train station", {"park", "inspect", "repair"}),
    "theater": Setting("theater", "the little theater", {"park", "inspect", "repair"}),
    "garden": Setting("garden", "the community garden", {"park", "inspect", "repair"}),
}

HERO_TYPES = ["rabbit", "fox", "squirrel", "bear"]
COMPANION_TYPES = ["rabbit", "fox", "squirrel", "bear"]

NAMES = {
    "rabbit": ["Luna", "Pip", "Mabel"],
    "fox": ["Finn", "Tara", "Roo"],
    "squirrel": ["Suki", "Jax", "Nell"],
    "bear": ["Benny", "Mara", "Tess"],
}

INCIDENTS = [
    Incident(
        title="the backwards parade",
        destination="the town parade",
        passenger_problem="the passengers had made an accord to wave only with their left paws",
        horn_clue="the horn gave a tiny honk whenever the limousine rolled over a pebble",
        banner_clue="the welcome banner kept sliding out of its neat roll",
        foolish_try="Luna tried to solve everything by driving in a slow circle around a flower pot",
        repair="parked on level ground, tightened the horn's loose wire with a grown-up, and tied the banner with a proper ribbon",
        lesson="A clever promise still needs a sensible plan",
        ending="the limousine led the parade with one polite beep while every passenger waved on the agreed side",
    ),
    Incident(
        title="the royal picnic",
        destination="a picnic under the clock tree",
        passenger_problem="the passengers had made an accord that nobody would say the word sandwich until lunch",
        horn_clue="the horn squeaked whenever the front wheel bounced",
        banner_clue="the picnic banner covered the basket instead of the table",
        foolish_try="Luna announced that the limousine could become a submarine if everyone held their breath",
        repair="stopped the limousine, checked the loose horn wire, and folded the banner into a tidy table runner",
        lesson="A lesson learned is better than a boast repeated",
        ending="the limousine arrived with the sandwiches safe, and nobody had to become a submarine",
    ),
    Incident(
        title="the surprise concert",
        destination="the courtyard concert",
        passenger_problem="the musicians had made an accord to begin only after the limousine gave one grand signal",
        horn_clue="the horn honked before anyone touched it",
        banner_clue="the concert banner fluttered from the trunk like a cape",
        foolish_try="Luna bowed to the empty seats and claimed the accidental honk was a new musical style",
        repair="secured the loose horn wire, closed the trunk, and clipped the banner to its proper stand",
        lesson="Admitting a small mistake can save a very large performance",
        ending="the limousine gave one deliberate beep, and the concert began with smiles instead of surprises",
    ),
    Incident(
        title="the hat parade",
        destination="the hat parade beside the fountain",
        passenger_problem="the passengers had made an accord to keep their hats perfectly still",
        horn_clue="the horn chirped when the limousine crossed a crack",
        banner_clue="the hat sign kept flapping across the driver's window",
        foolish_try="Luna wore three hats at once to prove that balance was easy",
        repair="pulled over, fixed the horn wire with help, and moved the sign away from the window",
        lesson="Showing off is not the same as being ready",
        ending="the limousine rolled gently beside the fountain while every hat stayed proudly in place",
    ),
    Incident(
        title="the moonlight delivery",
        destination="the observatory hill",
        passenger_problem="the passengers had made an accord to whisper until the first star appeared",
        horn_clue="the horn made a comic squeak whenever the road dipped",
        banner_clue="the delivery banner was tucked beneath the spare tire",
        foolish_try="Luna whispered so loudly that the pigeons covered their ears",
        repair="stopped safely, checked the horn, and placed the banner where the receivers could see it",
        lesson="Quiet listening can reveal what a loud plan misses",
        ending="the limousine climbed the hill with a soft engine hum, and the first star appeared above the banner",
    ),
]

DIALOGUES = [
    '"The limousine is not supposed to honk by itself," said {hero}. "Then let us inspect it instead of blaming the moon," replied {companion}.',
    '"Our accord says we wave with one paw," said {companion}. "Good," said {hero}. "Our repair plan should use both eyes."',
    '"I can fix this with a grand announcement!" cried {hero}. "Or with one small careful check," said {companion}.',
    '"Did you hear that squeak?" asked {hero}. "Yes," said {companion}. "The funny sound is also a clue."',
    '"I made the plan too fancy," {hero} admitted. "{lesson}," said {companion}.',
]

OPENINGS = [
    "At {place}, {hero} the {hero_type} polished a limousine until it reflected the clouds.",
    "Morning found {hero} the {hero_type} beside a shiny limousine at {place}.",
    "The limousine waited at {place}, looking grand enough to carry a king, a cake, or both.",
    "At {place}, {hero} the {hero_type} announced that today would be perfectly organized.",
]

REACTIONS = [
    "{hero} felt pride wobble into worry, while {companion} kept a calm paw on the door.",
    "The passengers giggled, but {hero} noticed that giggles did not make the limousine safer.",
    "{hero} wanted to hurry. {companion} pointed to the loose wire and asked everyone to wait.",
    "The grand plan had become a small muddle, which was exactly when careful thinking mattered most.",
]

REFLECTIONS = [
    "They tested the limousine once, slowly, before inviting everyone back inside.",
    "The passengers repeated their accord and added a new rule: inspect first, boast later.",
    "Luna wrote the repair on a card so the next driver would know what to check.",
    "Everyone laughed kindly at the earlier fuss, because the danger had passed and the lesson was clear.",
]


def _stable_seed(*parts: str) -> int:
    return sum((i + 1) * ord(c) for i, c in enumerate("|".join(parts)))


def horn_is_loose(world: World) -> bool:
    return world.entities["limousine"].meters["loose"] >= 1.0


def banner_is_unready(world: World) -> bool:
    return world.entities["banner"].meters["ready"] < 1.0


def fix_limousine(world: World) -> None:
    if "limousine_fixed" in world.fired:
        return
    world.fired.add("limousine_fixed")
    world.entities["limousine"].meters["loose"] = 0.0
    world.entities["limousine"].meters["clean"] += 1.0
    world.entities["limousine"].meters["ready"] = 1.0


def arrange_banner(world: World) -> None:
    if "banner_arranged" in world.fired:
        return
    world.fired.add("banner_arranged")
    world.entities["banner"].meters["ready"] = 1.0


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    world = World(setting)
    rng = random.Random(
        params.seed
        if params.seed is not None
        else _stable_seed(params.setting, params.hero_name, params.companion_name)
    )
    incident = rng.choice(INCIDENTS)

    hero = world.add(Entity(params.hero_name, "character", params.hero_type))
    companion = world.add(Entity(params.companion_name, "character", params.companion_type))
    limousine = world.add(Entity("limousine", label="the limousine"))
    banner = world.add(Entity("banner", label="the welcome banner"))
    ribbon = world.add(Entity("ribbon", label="a strong ribbon"))

    hero.memes["pride"] = 1.0
    hero.memes["trust"] = 0.5
    companion.memes["trust"] = 1.0
    limousine.meters["clean"] = 1.0
    limousine.meters["loose"] = 1.0
    banner.meters["ready"] = 0.0

    if "repair" not in setting.affordances:
        raise StoryError(f"{setting.place} has no safe place to repair the limousine.")
    if params.hero_name == params.companion_name:
        raise StoryError("The hero and companion need different names for a dialogue.")

    opening = rng.choice(OPENINGS).format(
        place=setting.place,
        hero=params.hero_name,
        hero_type=params.hero_type,
    )
    dialogue = rng.choice(DIALOGUES).format(
        hero=params.hero_name,
        companion=params.companion_name,
        lesson=incident.lesson,
    )
    reaction = rng.choice(REACTIONS).format(
        hero=params.hero_name,
        companion=params.companion_name,
    )
    reflection = rng.choice(REFLECTIONS).format(hero=params.hero_name)

    world.say(f"{opening} They were preparing for {incident.title}, a trip to {incident.destination}.")
    world.paragraph()
    world.say(
        f"The passengers had made an accord: {incident.passenger_problem}. "
        f"Then {incident.horn_clue}, and {incident.banner_clue}."
    )
    world.paragraph()
    world.say(f"{dialogue} {reaction}")
    world.paragraph()
    world.say(
        f"At first, {incident.foolish_try}. That made the passengers laugh, "
        "but it did not make the limousine ready."
    )
    world.paragraph()
    world.say(
        f"They looked again. The horn wire was loose, and the banner needed a better tie. "
        f"Together they {incident.repair}."
    )
    fix_limousine(world)
    arrange_banner(world)
    hero.memes["pride"] = 0.0
    hero.memes["worry"] = 0.0
    hero.memes["trust"] = 1.0
    companion.memes["trust"] = 1.5
    companion.memes["amusement"] = 1.0
    world.paragraph()
    world.say(
        f"{reflection} {companion.id} smiled and said, "
        f'"{incident.lesson}."'
    )
    world.paragraph()
    world.say(f"At last, {incident.ending}.")
    world.facts = {
        "hero": hero,
        "companion": companion,
        "limousine": limousine,
        "banner": banner,
        "ribbon": ribbon,
        "incident": incident,
        "setting": setting,
        "accord": incident.passenger_problem,
        "limousine_fixed": not horn_is_loose(world),
        "banner_ready": not banner_is_unready(world),
    }
    return world


def generation_prompts(world: World) -> list[str]:
    incident: Incident = world.facts["incident"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    companion: Entity = world.facts["companion"]  # type: ignore[assignment]
    return [
        f"Write a funny child-facing story about {hero.id}, {companion.id}, a limousine, and an accord that becomes difficult to keep.",
        f"Tell a Comedy story in which a loose limousine horn creates a silly problem and dialogue leads to a lesson learned.",
        f"Write a story ending with this lesson: {incident.lesson}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    incident: Incident = world.facts["incident"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    companion: Entity = world.facts["companion"]  # type: ignore[assignment]
    setting: Setting = world.facts["setting"]  # type: ignore[assignment]
    return [
        QAItem(
            f"Where were {hero.id} and {companion.id} preparing the limousine?",
            f"They were at {setting.place}, preparing the limousine for {incident.title} and a trip to {incident.destination}.",
        ),
        QAItem(
            "What accord had the passengers made?",
            f"They had made an accord that {incident.passenger_problem}.",
        ),
        QAItem(
            "What clues showed that something was wrong?",
            f"The clues were that {incident.horn_clue} Also, {incident.banner_clue}.",
        ),
        QAItem(
            "How did the characters solve the problem?",
            f"They {incident.repair}. This fixed the limousine and made the banner ready.",
        ),
        QAItem(
            f"What did {companion.id} say was the lesson learned?",
            f'{companion.id} said, "{incident.lesson}."',
        ),
        QAItem(
            "How did the ending show that the repair worked?",
            f"The ending showed success because {incident.ending}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a limousine?",
            "A limousine is a long passenger car often used for special trips or celebrations.",
        ),
        QAItem(
            "What is an accord?",
            "An accord is an agreement or shared promise between people.",
        ),
        QAItem(
            "Why should a loose wire be checked?",
            "A loose wire can make a device behave strangely, so it should be checked safely by a knowledgeable grown-up.",
        ),
        QAItem(
            "What does a lesson learned do?",
            "A lesson learned helps someone make a wiser choice the next time a similar problem appears.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
broken_horn(L) :- limousine(L), loose(L).
unready_banner(B) :- banner(B), not ready(B).
has_repair_place(P) :- setting(P), repair(P).
valid_story(P,H,C) :-
    setting(P),
    animal(H),
    animal(C),
    limousine(L),
    banner(B),
    ribbon(R),
    broken_horn(L),
    unready_banner(B),
    has_repair_place(P),
    H != C.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for key in SETTINGS:
        lines.append(asp.fact("setting", key))
        for affordance in SETTINGS[key].affordances:
            lines.append(asp.fact(affordance, key))
    for animal in sorted(set(HERO_TYPES + COMPANION_TYPES)):
        lines.append(asp.fact("animal", animal))
    lines.extend(
        [
            asp.fact("limousine", "limousine"),
            asp.fact("banner", "banner"),
            asp.fact("ribbon", "ribbon"),
            asp.fact("loose", "limousine"),
        ]
    )
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    expected = {
        (place, hero, companion)
        for place in SETTINGS
        for hero in set(HERO_TYPES)
        for companion in set(COMPANION_TYPES)
        if hero != companion
    }
    got = set(asp_valid_stories())
    if got == expected:
        print(f"OK: ASP gate matches Python expectations ({len(got)} combinations).")
        return 0
    print("MISMATCH between ASP and Python expectations:")
    print("only in ASP:", sorted(got - expected))
    print("only in Python:", sorted(expected - got))
    return 1


CURATED = [
    StoryParams("station", "rabbit", "fox", "Luna", "Finn"),
    StoryParams("theater", "squirrel", "bear", "Suki", "Benny"),
    StoryParams("garden", "fox", "rabbit", "Tara", "Pip"),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Comedy storyworld about a limousine, an accord, and a lesson learned."
    )
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--hero-type", choices=HERO_TYPES)
    parser.add_argument("--companion-type", choices=COMPANION_TYPES)
    parser.add_argument("--hero-name")
    parser.add_argument("--companion-name")
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
    setting = args.setting or rng.choice(list(SETTINGS))
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    companion_type = args.companion_type or rng.choice(COMPANION_TYPES)
    hero_name = args.hero_name or rng.choice(NAMES[hero_type])
    companion_name = args.companion_name or rng.choice(NAMES[companion_type])
    if hero_name == companion_name:
        choices = [name for name in NAMES[companion_type] if name != hero_name]
        companion_name = rng.choice(choices)
    return StoryParams(
        setting=setting,
        hero_type=hero_type,
        companion_type=companion_type,
        hero_name=hero_name,
        companion_name=companion_name,
    )


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
            f"  {entity.id:12} ({entity.type:9}) meters={meters} memes={memes}"
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        rows = asp_valid_stories()
        print(f"{len(rows)} compatible story combinations:")
        for row in rows:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, params in enumerate(CURATED):
            params.seed = base_seed + index
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        limit = max(50, args.n * 50)
        while len(samples) < args.n and index < limit:
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
            params = sample.params
            header = (
                f"### {params.hero_name}: {params.setting} "
                f"({params.hero_type} + {params.companion_type})"
            )
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
