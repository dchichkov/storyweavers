#!/usr/bin/env python3
"""
Storyworld: glee_queer_reign_conflict_myth

A small mythic world about a joyful queer ruler whose reign is tested by
conflict, and strengthened when many kinds of people share responsibility.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Person:
    id: str
    name: str
    role: str
    identity: str
    home: str
    meters: dict[str, float] = field(
        default_factory=lambda: {"courage": 0.0, "conflict": 0.0, "trust": 0.0}
    )
    memes: dict[str, float] = field(
        default_factory=lambda: {"glee": 0.0, "worry": 0.0, "belonging": 0.0}
    )


@dataclass
class Relic:
    id: str
    label: str
    kind: str
    owner: str = ""
    meters: dict[str, float] = field(
        default_factory=lambda: {"power": 0.0, "danger": 0.0, "harmony": 0.0}
    )


@dataclass
class StoryParams:
    hero_name: str
    companion_name: str
    elder_name: str
    kingdom: str
    relic: str
    conflict: str
    custom: str = "a bright queer festival"
    telling_mode: str = "dawn"
    seed: Optional[int] = None


KINGDOMS = {
    "Moon Orchard": {
        "relic": "the Prism Crown",
        "conflicts": [
            "two valleys argued over who could ring the harvest bell",
            "the river clans blamed one another for a vanished bridge",
            "the hill folk and marsh folk disputed the path to the spring",
        ],
        "customs": ["a lantern procession", "a bright queer festival", "a moonlit song circle"],
    },
    "Star Harbor": {
        "relic": "the Tideglass Scepter",
        "conflicts": [
            "sailors and sky-watchers quarreled over the harbor beacon",
            "three neighborhoods claimed the same safe dock",
            "the old lighthouse bell rang warnings that no one could interpret",
        ],
        "customs": ["a rainbow sail parade", "a bright queer festival", "a dawn boat dance"],
    },
    "Willow Crown": {
        "relic": "the Listening Branch",
        "conflicts": [
            "the gardeners and stonecutters fought over a narrow courtyard",
            "two villages claimed the shade of one ancient tree",
            "the bell makers and storytellers disagreed about the town square",
        ],
        "customs": ["a garland feast", "a bright queer festival", "a midsummer story night"],
    },
}

HERO_NAMES = ["Luna", "Ari", "Sable", "Mika", "Jules"]
COMPANION_NAMES = ["Neri", "Pax", "Sol", "Rin", "Tavi"]
ELDER_NAMES = ["Orin", "Maia", "Bram", "Ione", "Sen"]

CONFLICTS = (
    "two valleys argued over who could ring the harvest bell",
    "the river clans blamed one another for a vanished bridge",
    "the hill folk and marsh folk disputed the path to the spring",
    "sailors and sky-watchers quarreled over the harbor beacon",
    "three neighborhoods claimed the same safe dock",
    "the gardeners and stonecutters fought over a narrow courtyard",
)

TELLING_MODES = (
    "dawn",
    "prophecy",
    "dialogue",
    "storm",
    "festival",
    "memory",
    "moonrise",
)

RELICS = (
    "the Prism Crown",
    "the Tideglass Scepter",
    "the Listening Branch",
    "the Silver Drum",
    "the Lantern of Many Colors",
)

ASP_RULES = r"""
peaceful_reign(S) :- story(S), queer_ruler(S), shared_power(S), conflict_faced(S).
conflict_faced(S) :- story(S), conflict(S).
shared_power(S) :- story(S), listens(S), shared_decision(S).
queer_ruler(S) :- story(S), ruler_queer(S).
"""


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.people: dict[str, Person] = {}
        self.relics: dict[str, Relic] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        paragraphs: list[str] = []
        current: list[str] = []
        for line in self.lines:
            if line == "":
                if current:
                    paragraphs.append(" ".join(current))
                    current = []
            else:
                current.append(line)
        if current:
            paragraphs.append(" ".join(current))
        return "\n\n".join(paragraphs)


def build_world(params: StoryParams) -> World:
    if params.hero_name == params.companion_name:
        raise StoryError("hero_name and companion_name must be different.")
    if not params.kingdom.strip():
        raise StoryError("kingdom must not be empty.")
    if not params.relic.strip():
        raise StoryError("relic must not be empty.")

    world = World(params)
    hero = Person(
        "hero",
        params.hero_name,
        "queer ruler",
        "queer",
        params.kingdom,
        {"courage": 1.0, "conflict": 0.0, "trust": 0.0},
        {"glee": 1.0, "worry": 0.0, "belonging": 1.0},
    )
    companion = Person(
        "companion",
        params.companion_name,
        "truth-teller",
        "queer ally",
        params.kingdom,
        {"courage": 0.5, "conflict": 0.0, "trust": 0.5},
        {"glee": 0.5, "worry": 0.0, "belonging": 0.5},
    )
    elder = Person(
        "elder",
        params.elder_name,
        "keeper of old laws",
        "elder",
        params.kingdom,
        {"courage": 0.5, "conflict": 0.0, "trust": 0.5},
        {"glee": 0.0, "worry": 0.5, "belonging": 0.5},
    )
    relic = Relic(
        "relic",
        params.relic,
        "royal symbol",
        hero.id,
        {"power": 1.0, "danger": 0.5, "harmony": 0.0},
    )
    world.people.update({p.id: p for p in (hero, companion, elder)})
    world.relics[relic.id] = relic

    conflict = params.conflict
    openings = {
        "dawn": f"At dawn in {params.kingdom}, {hero.name}, the queer ruler, woke to the sound of horns: {conflict}.",
        "prophecy": f"An old prophecy said that when {conflict}, the reign of a joyful ruler would be tested in {params.kingdom}.",
        "dialogue": f'"The realm is restless," said {hero.name} at sunrise. In {params.kingdom}, {conflict}.',
        "storm": f"Thunder rolled above {params.kingdom} when {conflict}, and even the clouds seemed to take sides.",
        "festival": f"On the morning of {params.custom}, {conflict} across {params.kingdom}.",
        "memory": f"{hero.name} remembered a childhood lesson as {conflict} in {params.kingdom}.",
        "moonrise": f"By moonrise, the people of {params.kingdom} had learned that {conflict}.",
    }
    world.say(openings[params.telling_mode])
    world.say(
        f"{hero.name} wore {params.relic}, but the shining relic could not command hearts; it could only remind the realm that every person carried a story."
    )
    world.say(
        f"The frightened court urged {hero.name} to choose a winner quickly, yet the ruler felt worry beneath the kingdom's usual glee."
    )
    world.para()

    hero.meters["conflict"] += 1
    companion.meters["conflict"] += 1
    elder.meters["conflict"] += 1
    hero.memes["worry"] += 1
    companion.memes["worry"] += 1

    world.say(f'{companion.name} stepped close and said, "A reign is not a throne speaking alone. Ask who has been unheard."')
    world.say(
        f'{hero.name} answered, "Then let the doors open. No clan will be asked to hide its name, its love, or its truth before it may speak."'
    )
    world.say(
        f"{elder.name} brought an ancient basin to the courtyard and explained that old conflicts grew sharp when people mistook silence for agreement."
    )
    world.say(
        f"The three leaders invited the quarreling groups to place one token in the basin for what they needed and one token for what they could share."
    )
    world.para()

    rng = random.Random((params.seed or 0) ^ 0x9E3779B9)
    clue = rng.choice(
        (
            "both sides had been protecting the same children from a dangerous crossing",
            "each group knew one part of the map, but no group knew the whole path",
            "the disputed object had been moved by weather, not stolen by either side",
            "the loudest argument hid a quiet wish for a place where everyone could belong",
        )
    )
    world.say(f"Then {params.companion_name} noticed the turning clue: {clue}.")
    world.say(
        f'"We were guarding pieces of the same hope," {params.companion_name} said. "What if the answer has room for all of us?"'
    )
    world.say(
        f"{hero.name} removed {params.relic} and set it beside the basin. The ruler declared that no symbol of power would be lifted until the people designed a shared answer."
    )
    world.say(
        f"Together, the groups drew a new plan: {params.custom} would begin at the disputed place, and every group would take a turn caring for it."
    )
    hero.meters["trust"] += 1
    companion.meters["trust"] += 1
    elder.meters["trust"] += 1
    hero.memes["belonging"] += 1
    companion.memes["belonging"] += 1
    relic.meters["harmony"] += 1
    world.para()

    world.say(
        f"The plan worked. The conflict did not vanish like smoke; people faced it, named it, and changed the rules that had kept them apart."
    )
    world.say(
        f"At sunset, {params.custom} filled {params.kingdom} with drums, lanterns, and many kinds of families. {hero.name} danced without pretending to be anyone else."
    )
    world.say(
        f"{elder.name} bowed and said, 'Your reign became strong when you shared its weight.' {hero.name} replied, 'A kingdom is happiest when every true voice has a place in its song.'"
    )
    world.say(
        f"The people cheered with glee, and {params.relic} shone again—not as a weapon of command, but as a promise that power could protect belonging."
    )
    world.say(
        f"From that night onward, {hero.name}'s queer reign was remembered as the season when conflict became a bridge, and the whole realm learned to cross together."
    )

    world.facts.update(
        hero=hero,
        companion=companion,
        elder=elder,
        relic=relic,
        conflict=conflict,
        clue=clue,
        custom=params.custom,
        kingdom=params.kingdom,
        resolution="the people created a shared plan and took turns caring for the disputed place",
        lesson="a reign grows stronger when a ruler listens and shares power",
        ending=f"{params.relic} shone as a promise that power could protect belonging",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Person = f["hero"]
    return [
        f"Write a short myth about {hero.name}, a queer ruler whose reign is tested by conflict in {f['kingdom']}.",
        f"Tell a mythic story in which glee returns after {hero.name} listens to every side and shares power.",
        f"Write a child-friendly myth about a royal relic that becomes a symbol of belonging instead of command.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Person = f["hero"]
    companion: Person = f["companion"]
    relic: Relic = f["relic"]
    return [
        QAItem(
            question=f"What conflict challenged {hero.name}'s reign?",
            answer=f"The conflict was that {f['conflict']}. It threatened the peace of {f['kingdom']} because the groups had stopped trusting one another.",
        ),
        QAItem(
            question=f"What did {companion.name} tell {hero.name} to do?",
            answer=f"{companion.name} told {hero.name} that a reign should not be a throne speaking alone and urged the ruler to ask who had been unheard.",
        ),
        QAItem(
            question="What clue helped the people find a solution?",
            answer=f"The turning clue was that {f['clue']}. This showed that the arguing groups shared a deeper hope.",
        ),
        QAItem(
            question=f"How did {hero.name} resolve the conflict?",
            answer=f"{hero.name} set {relic.label} beside the listening basin and refused to choose a winner before everyone helped design a shared plan. The groups then took turns caring for the disputed place.",
        ),
        QAItem(
            question="What final image proves that the realm changed?",
            answer=f"At sunset, {f['custom']} filled {f['kingdom']} with drums, lanterns, and many kinds of families, while {relic.label} shone as a promise of belonging.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does glee mean?",
            answer="Glee means bright, excited happiness that people may show through laughter, singing, or joyful movement.",
        ),
        QAItem(
            question="What does queer mean in this story?",
            answer="Queer describes people whose identities or loves do not fit narrow old expectations; in this story, queer belonging is honored openly and safely.",
        ),
        QAItem(
            question="What is a reign?",
            answer="A reign is the time during which a ruler leads a kingdom or people.",
        ),
        QAItem(
            question="What is conflict?",
            answer="Conflict is a serious disagreement or struggle between people or groups. Listening and fair choices can help resolve it.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for person in world.people.values():
        lines.append(
            f"{person.id}: role={person.role} identity={person.identity} "
            f"meters={dict(person.meters)} memes={dict(person.memes)}"
        )
    for relic in world.relics.values():
        lines.append(
            f"{relic.id}: label={relic.label} kind={relic.kind} owner={relic.owner} "
            f"meters={dict(relic.meters)}"
        )
    return "\n".join(lines)


def asp_facts(params: StoryParams) -> str:
    import asp

    return "\n".join(
        [
            asp.fact("story", "s1"),
            asp.fact("ruler_queer", "s1"),
            asp.fact("conflict", "s1"),
            asp.fact("listens", "s1"),
            asp.fact("shared_decision", "s1"),
        ]
    )


def asp_program(params: Optional[StoryParams] = None) -> str:
    if params is None:
        params = StoryParams(
            hero_name="Luna",
            companion_name="Neri",
            elder_name="Orin",
            kingdom="Moon Orchard",
            relic="the Prism Crown",
            conflict=CONFLICTS[0],
            custom="a bright queer festival",
        )
    return f"{asp_facts(params)}\n{ASP_RULES}\n#show peaceful_reign/1.\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    found = set(asp.atoms(model, "peaceful_reign"))
    if found != {("s1",)}:
        print("MISMATCH: ASP did not recognize the shared peaceful reign.")
        return 1

    params = StoryParams(
        hero_name="Luna",
        companion_name="Neri",
        elder_name="Orin",
        kingdom="Moon Orchard",
        relic="the Prism Crown",
        conflict=CONFLICTS[0],
        custom="a bright queer festival",
        seed=17,
    )
    sample = generate(params)
    required = ("glee", "queer", "reign", "conflict")
    lowered = sample.story.lower()
    if not all(word in lowered for word in required):
        print("MISMATCH: generated story lacks a required narrative word.")
        return 1
    if len(sample.story_qa) < 4:
        print("MISMATCH: generated story lacks grounded questions.")
        return 1
    print("OK: ASP gate and generated-story checks passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Mythic story world about glee, queer belonging, reign, and conflict."
    )
    parser.add_argument("--hero-name")
    parser.add_argument("--companion-name")
    parser.add_argument("--elder-name")
    parser.add_argument("--kingdom", choices=sorted(KINGDOMS))
    parser.add_argument("--relic")
    parser.add_argument("--conflict", choices=sorted(set(CONFLICTS)))
    parser.add_argument("--custom")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    kingdom = args.kingdom or rng.choice(sorted(KINGDOMS))
    config = KINGDOMS[kingdom]
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    companion_name = args.companion_name or rng.choice(
        [name for name in COMPANION_NAMES if name != hero_name]
    )
    elder_name = args.elder_name or rng.choice(ELDER_NAMES)
    conflict = args.conflict or rng.choice(config["conflicts"])
    custom = args.custom or rng.choice(config["customs"])
    relic = args.relic or config["relic"]
    return StoryParams(
        hero_name=hero_name,
        companion_name=companion_name,
        elder_name=elder_name,
        kingdom=kingdom,
        relic=relic,
        conflict=conflict,
        custom=custom,
        telling_mode=rng.choice(TELLING_MODES),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        hero_name="Luna",
        companion_name="Neri",
        elder_name="Orin",
        kingdom="Moon Orchard",
        relic="the Prism Crown",
        conflict="two valleys argued over who could ring the harvest bell",
        custom="a bright queer festival",
        telling_mode="dawn",
    ),
    StoryParams(
        hero_name="Ari",
        companion_name="Pax",
        elder_name="Maia",
        kingdom="Star Harbor",
        relic="the Tideglass Scepter",
        conflict="sailors and sky-watchers quarreled over the harbor beacon",
        custom="a rainbow sail parade",
        telling_mode="storm",
    ),
    StoryParams(
        hero_name="Sable",
        companion_name="Sol",
        elder_name="Ione",
        kingdom="Willow Crown",
        relic="the Listening Branch",
        conflict="the gardeners and stonecutters fought over a narrow courtyard",
        custom="a midsummer story night",
        telling_mode="dialogue",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        print(model)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 20):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            index += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
