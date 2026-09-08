#!/usr/bin/env python3
"""
A small superhero storyworld about a bride whose wedding day is saved by courage,
kindness, and a very practical cape.
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
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = ""

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"bride", "woman", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"groom", "man", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    id: str
    label: str
    features: set[str] = field(default_factory=set)


@dataclass
class RescuePlan:
    id: str
    label: str
    action: str
    protects: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    trace_events: list[str] = field(default_factory=list)

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


OPENERS = [
    "On the brightest wedding morning in the city,",
    "High above the busy streets,",
    "In a town where every wedding bell could be heard from the rooftops,",
    "One sunny day, just before the wedding began,",
]

SCENES = [
    "The garden was full of white chairs, golden ribbons, and flowers that nodded in the warm breeze.",
    "Guests gathered beneath a glass roof while bells chimed softly over the shining city.",
    "The wedding hall glowed with lanterns, and the aisle looked like a silver path.",
]

TROUBLES = {
    "wind": {
        "warning": "A wild wind is racing toward the wedding garden",
        "event": "A sudden gust tore the flower arch loose and sent the ceremony program sailing toward the fountain.",
        "clue": "the arch ropes snapping above the guests",
        "risk": "the guests and the wedding flowers",
    },
    "rain": {
        "warning": "A storm cloud is rolling over the wedding garden",
        "event": "Rain burst through the open roof, and the rings' little velvet box began sliding across the wet table.",
        "clue": "water gathering beside the ring box",
        "risk": "the wedding rings and the people beneath the roof",
    },
    "power": {
        "warning": "The city lights are flickering before the ceremony",
        "event": "The hall went dark, and a frightened flower girl could not find her way back to the aisle.",
        "clue": "the small footsteps stopping in the darkness",
        "risk": "the flower girl and the waiting ceremony",
    },
}

PLANS = {
    "cape": RescuePlan(
        "cape",
        "the bright rescue cape",
        "spread the cape beneath the loose decorations and guide them safely down",
        "the guests from falling ribbons and flowers",
    ),
    "umbrella": RescuePlan(
        "umbrella",
        "the silver rescue umbrella",
        "open the umbrella over the ring box and carry it across the wet table",
        "the rings from the rain",
    ),
    "lantern": RescuePlan(
        "lantern",
        "the glowing rescue lantern",
        "lift the lantern high and lead the flower girl back to the aisle",
        "the flower girl from the dark hall",
    ),
}

ENDINGS = {
    "bells": "When the bells rang, the bride and groom smiled beneath the repaired arch, while the city cheered for its newest gentle superhero.",
    "stars": "That night, stars shone above the wedding roof, and the bride's cape rested over two chairs like a promise that help would always arrive.",
    "flowers": "At the happy ending, every guest danced among the flowers, and the bride kept one bright petal beside her heart.",
}


@dataclass
class StoryParams:
    trouble: str = "wind"
    plan: str = "cape"
    ending: str = "bells"
    bride: str = "Luna"
    partner: str = "Sol"
    seed: Optional[int] = None


KNOWLEDGE = {
    "bride": [
        QAItem(
            "What is a bride?",
            "A bride is a person who is getting married or has just been married.",
        )
    ],
    "superhero": [
        QAItem(
            "What makes someone a superhero?",
            "A superhero helps others with courage, care, and useful actions when people need help.",
        )
    ],
    "wedding": [
        QAItem(
            "Why might people gather at a wedding?",
            "People gather at a wedding to celebrate two people promising to share their lives.",
        )
    ],
    "happy_ending": [
        QAItem(
            "What is a happy ending?",
            "A happy ending resolves the trouble safely and leaves the characters hopeful and glad.",
        )
    ],
}


def validate(params: StoryParams) -> None:
    if params.trouble not in TROUBLES:
        raise StoryError(f"Unknown trouble: {params.trouble}")
    if params.plan not in PLANS:
        raise StoryError(f"Unknown rescue plan: {params.plan}")
    if params.ending not in ENDINGS:
        raise StoryError(f"Unknown ending: {params.ending}")
    compatible = {
        "wind": "cape",
        "rain": "umbrella",
        "power": "lantern",
    }
    if compatible[params.trouble] != params.plan:
        raise StoryError(
            f"The {params.plan} cannot solve the {params.trouble} trouble; "
            f"use the {compatible[params.trouble]} plan."
        )
    if not params.bride.strip() or not params.partner.strip():
        raise StoryError("The bride and partner must have names.")


def build_world(params: StoryParams, rng: random.Random) -> World:
    validate(params)
    setting = Setting(
        "wedding_garden",
        "the wedding garden",
        {"wedding", "guests", "flowers", "ceremony"},
    )
    world = World(setting)
    bride = world.add(
        Entity(
            params.bride,
            "character",
            "bride",
            "the bride",
            memes={"courage": 0.0, "worry": 0.0, "joy": 0.0},
            location="wedding_garden",
        )
    )
    partner = world.add(
        Entity(
            params.partner,
            "character",
            "groom",
            "the partner",
            memes={"hope": 1.0, "worry": 0.0},
            location="wedding_garden",
        )
    )
    world.add(
        Entity(
            "guests",
            "group",
            "guests",
            "the guests",
            meters={"number": 12.0},
            location="wedding_garden",
        )
    )
    world.facts.update(
        bride=bride,
        partner=partner,
        trouble=TROUBLES[params.trouble],
        plan=PLANS[params.plan],
        scene=rng.choice(SCENES),
        opener=rng.choice(OPENERS),
        ending=ENDINGS[params.ending],
        trouble_id=params.trouble,
        plan_id=params.plan,
    )
    return world


def tell_story(world: World) -> None:
    f = world.facts
    bride = f["bride"]
    partner = f["partner"]
    trouble = f["trouble"]
    plan = f["plan"]

    world.say(
        f"{f['opener']} there lived {bride.id}, a bride with a brave heart and a secret superhero cape beneath her wedding dress."
    )
    world.say(
        f"She was ready to marry {partner.id}, and {f['scene']}"
    )
    world.para()

    bride.memes["joy"] += 1
    world.say(
        f'"Today will be wonderful," {bride.id} told {partner.id}. '
        f'"It will," {partner.id} replied. "We will face every surprise together."'
    )
    world.say(f"Then {trouble['warning'].lower()}.")
    bride.memes["worry"] += 1
    world.trace_events.append("danger appeared before the ceremony")
    world.say(
        f"{trouble['event']} {trouble['clue'].capitalize()} showed that {trouble['risk']} needed help."
    )
    world.para()

    world.say(
        f'"The wedding can wait one minute," {bride.id} said. '
        f'"What will you do?" {partner.id} asked. '
        f'"I will help everyone first," said the bride.'
    )
    bride.memes["courage"] += 1
    world.say(
        f"She stepped forward and used {plan.label} to {plan.action}. "
        f"Her careful move protected {plan.protects}."
    )
    world.trace_events.append(f"{plan.id} plan solved the {f['trouble_id']} danger")
    world.say(
        f"{partner.id} joined her at once. Together they made the place safe, and the guests clapped instead of panicking."
    )
    world.para()

    bride.memes["worry"] = 0.0
    bride.memes["joy"] += 2
    partner.memes["hope"] += 1
    world.say(
        f'"You were a superhero bride," {partner.id} said. '
        f'"Only because everyone helped," {bride.id} answered.'
    )
    world.say(
        f"The ceremony began, the promises were spoken, and the happy ending arrived: {f['ending']}"
    )
    world.trace_events.append("the wedding ended safely and happily")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a superhero story for children about bride {f['bride'].id}, who must protect {f['trouble']['risk']} at a wedding.",
        f"Include this turning point: {f['trouble']['event']} The bride should use {f['plan'].label} to solve the problem.",
        f"End with a happy wedding image: {f['ending']}",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    bride = f["bride"]
    partner = f["partner"]
    trouble = f["trouble"]
    plan = f["plan"]
    return [
        QAItem(
            "Who was the superhero in the story?",
            f"{bride.id}, the bride, was the superhero. She used courage and {plan.label} to help everyone at the wedding.",
        ),
        QAItem(
            "What trouble threatened the wedding?",
            f"{trouble['event']} The danger threatened {trouble['risk']}.",
        ),
        QAItem(
            f"How did {bride.id} solve the problem?",
            f"{bride.id} used {plan.label} to {plan.action}. {partner.id} helped her, and together they made the wedding safe.",
        ),
        QAItem(
            "How did the story end?",
            f"The ceremony began after the danger passed, and {f['ending']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        item
        for topic in ("bride", "superhero", "wedding", "happy_ending")
        for item in KNOWLEDGE[topic]
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World knowledge Q&A ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id}: location={entity.location} meters={meters} memes={memes}"
        )
    lines.append("  events:")
    lines.extend(f"    - {event}" for event in world.trace_events)
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    validate(params)
    rng = random.Random(params.seed if params.seed is not None else 0)
    world = build_world(params, rng)
    tell_story(world)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    trouble = args.trouble or rng.choice(list(TROUBLES))
    plan = args.plan or {
        "wind": "cape",
        "rain": "umbrella",
        "power": "lantern",
    }[trouble]
    return StoryParams(
        trouble=trouble,
        plan=plan,
        ending=args.ending or rng.choice(list(ENDINGS)),
        bride=args.bride or rng.choice(["Luna", "Mira", "Nova", "Ruby"]),
        partner=args.partner or rng.choice(["Sol", "Theo", "Arlo", "Kai"]),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A superhero wedding storyworld about a brave bride."
    )
    parser.add_argument("--trouble", choices=TROUBLES)
    parser.add_argument("--plan", choices=PLANS)
    parser.add_argument("--ending", choices=ENDINGS)
    parser.add_argument("--bride")
    parser.add_argument("--partner")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


ASP_RULES = r"""
setting(wedding_garden).
character(bride).
character(partner).
danger(wind).
danger(rain).
danger(power).
plan(cape).
plan(umbrella).
plan(lantern).
solves(cape, wind).
solves(umbrella, rain).
solves(lantern, power).
happy_ending(wedding_garden).
valid_story(S, D, P) :- setting(S), danger(D), plan(P), solves(P, D), happy_ending(S).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("setting", "wedding_garden"),
            asp.fact("character", "bride"),
            asp.fact("character", "partner"),
            asp.fact("danger", "wind"),
            asp.fact("danger", "rain"),
            asp.fact("danger", "power"),
            asp.fact("plan", "cape"),
            asp.fact("plan", "umbrella"),
            asp.fact("plan", "lantern"),
            asp.fact("solves", "cape", "wind"),
            asp.fact("solves", "umbrella", "rain"),
            asp.fact("solves", "lantern", "power"),
            asp.fact("happy_ending", "wedding_garden"),
        ]
    )


def asp_program(show: str = "#show valid_story/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_valid_combos() -> set[tuple[str, str, str]]:
    return {
        ("wedding_garden", "wind", "cape"),
        ("wedding_garden", "rain", "umbrella"),
        ("wedding_garden", "power", "lantern"),
    }


def asp_valid_combos() -> set[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return set(asp.atoms(model, "valid_story"))


def asp_verify() -> int:
    try:
        actual = asp_valid_combos()
    except ImportError:
        print("ASP verification skipped: clingo is not installed.")
        return 0
    expected = python_valid_combos()
    if actual != expected:
        print(f"ASP mismatch: expected {sorted(expected)}, got {sorted(actual)}")
        return 1
    for trouble, plan in (("wind", "cape"), ("rain", "umbrella"), ("power", "lantern")):
        sample = generate(
            StoryParams(trouble=trouble, plan=plan, ending="bells", seed=17)
        )
        if not sample.story or "happy ending" not in sample.story:
            print(f"Generated story verification failed for {trouble}.")
            return 1
    print(f"OK: ASP/Python parity verified for {len(expected)} story combinations.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        combos = [
            ("wind", "cape"),
            ("rain", "umbrella"),
            ("power", "lantern"),
        ]
        for index, (trouble, plan) in enumerate(combos):
            samples.append(
                generate(
                    StoryParams(
                        trouble=trouble,
                        plan=plan,
                        ending=list(ENDINGS)[index % len(ENDINGS)],
                        bride="Luna",
                        partner="Sol",
                        seed=base_seed + index,
                    )
                )
            )
    else:
        for index in range(max(1, args.n)):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.asp:
        try:
            print(asp_program())
        except Exception as exc:
            raise StoryError(f"Unable to produce ASP program: {exc}") from exc
        return

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
