#!/usr/bin/env python3
"""
A small mystery storyworld about elapsed time, a bad ending avoided, and sharing
the clues that solve a disappearing picnic bell puzzle.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)

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
    place: str
    activity: str
    prize: str
    name: str
    companion: str
    trait: str
    case: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Case:
    title: str
    opening: str
    clue: str
    false_lead: str
    sharing: str
    reveal: str
    resolution: str
    bad_ending: str
    ending: str
    question: str
    answer: str


CASES = [
    Case(
        "the bell beneath the blanket",
        "At the park, the picnic bell vanished just before the lunch game began.",
        "Luna found a silver thread on the grass and noticed that the blanket had a fresh round bump.",
        "She thought a squirrel had dragged the bell away, so she searched the bushes.",
        "Luna showed the thread to Ivo instead of keeping her clue secret.",
        "Ivo remembered that he had folded the bell inside the blanket to carry it, then forgotten.",
        "They opened the blanket, found the bell, and shared the mystery with everyone before starting the game.",
        "If Luna had hidden the clue and blamed the squirrel, the game might have ended with hurt feelings and no bell.",
        "The bell rang from the blanket, and every child took a turn listening for its bright answer.",
        "Where was the missing bell?",
        "The bell was folded inside the picnic blanket because Ivo had tucked it there while carrying it.",
    ),
    Case(
        "the footprints that stopped",
        "A trail of tiny footprints led toward the garden gate, but the missing cookie tin was nowhere beyond it.",
        "Luna saw that the footprints stopped at a puddle and that one muddy mark pointed back toward the picnic table.",
        "She first suspected the gatekeeper's cat.",
        "She shared the muddy mark with her companion, who compared it with the flour on the tablecloth.",
        "The marks belonged to a floury shoe; the tin had been carried back to the table, not taken through the gate.",
        "They lifted the tablecloth and found the tin beside the basket, then shared cookies fairly.",
        "If they had chased the cat, the cookie game would have ended with a false accusation and no snack.",
        "The tin opened beside the table, and the last cookie was broken neatly in two.",
        "What showed that the cookie tin had not gone through the gate?",
        "The footprints stopped at a puddle, and a muddy mark pointed back toward the picnic table.",
    ),
    Case(
        "the clock with no hands",
        "The old garden clock had no hands, so nobody knew how long the treasure hunt had lasted.",
        "Luna noticed that the sunbeam had crossed three stepping stones and that the lunch bell usually rang after four.",
        "She wanted to declare the hunt over immediately.",
        "She shared the sunbeam clue with the other children and listened to their observations.",
        "The group realized only a short time had elapsed, so they searched one final safe place.",
        "They found the treasure under the blue bench and ended the hunt together.",
        "If Luna had stopped the hunt alone, the hidden treasure would have made a gloomy, unfair ending.",
        "The blue bench held the treasure while the sunbeam rested on the fourth stone.",
        "How did the children estimate the time?",
        "They watched how far the sunbeam had moved across the stepping stones and compared it with the usual bell time.",
    ),
]


NAMES = ["Luna", "Maya", "Nora", "Zoe", "Mina"]
COMPANIONS = ["Ivo", "Theo", "Sam", "Finn", "Ari"]
TRAITS = ["curious", "patient", "brave", "careful", "bright"]


@dataclass
class Registry:
    places: tuple[str, ...] = ("park",)
    activities: tuple[str, ...] = ("investigate",)
    prizes: tuple[str, ...] = ("mystery",)


REGISTRY = Registry()


def can_story(place: str, activity: str, prize: str) -> bool:
    return (place, activity, prize) == ("park", "investigate", "mystery")


ASP_RULES = r"""
place(park).
activity(investigate).
prize(mystery).
feature(elapse).
feature(bad_ending).
feature(sharing).
compatible(P,A,R) :- place(P), activity(A), prize(R),
    P = park, A = investigate, R = mystery.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("place", "park"),
            asp.fact("activity", "investigate"),
            asp.fact("prize", "mystery"),
            asp.fact("feature", "elapse"),
            asp.fact("feature", "bad_ending"),
            asp.fact("feature", "sharing"),
        ]
    )


def asp_program(show: str = "#show compatible/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    return [("park", "investigate", "mystery")]


def tell(params: StoryParams) -> World:
    case = CASES[int(params.case.rsplit("_", 1)[1]) % len(CASES)]
    world = World()
    luna = world.add(Entity("child", "character", params.name))
    companion = world.add(Entity("companion", "character", params.companion))
    clue = world.add(Entity("clue", "object", "a small clue"))
    world.facts.update(case=case, child=luna, companion=companion, clue=clue)

    world.say(f"{params.name} was a {params.trait} mystery solver who loved sharing clues.")
    world.say(f"One afternoon, {params.name} and {params.companion} went to the park to investigate a small picnic puzzle.")
    world.para()
    world.say(case.opening)
    world.say(f'"We should solve it before too much time can elapse," {params.name} said.')
    world.say(f'"Then let us look carefully, not wildly," {params.companion} replied.')
    world.say(case.clue)
    world.say(case.false_lead)
    world.para()
    world.say(f'"I found this clue," {params.name} said. "Will you help me test it?"')
    world.say(f'"Yes," said {params.companion}. "A shared clue is stronger than a secret guess."')
    world.say(case.sharing)
    world.say(case.reveal)
    world.fired.add("clue_shared")
    luna.memes["trust"] = 1.0
    companion.memes["cooperation"] = 1.0
    world.para()
    world.say(case.resolution)
    world.say(f"The mystery had a warning hidden inside it: {case.bad_ending}")
    world.say(case.ending)
    world.facts["elapsed_change"] = "time passed, but careful sharing prevented a bad ending"
    return world


def generation_prompts(world: World) -> list[str]:
    case = world.facts["case"]
    child = world.facts["child"]
    return [
        "Write a child-friendly mystery about elapsed time, sharing clues, and avoiding a bad ending.",
        f"Tell a mystery in which {child.label} investigates {case.title} with a companion.",
        f"Use this clue to turn the story: {case.clue}",
    ]


def story_qa(world: World) -> list[QAItem]:
    case: Case = world.facts["case"]  # type: ignore[assignment]
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What mystery did {child.label} investigate?",
            answer=case.opening,
        ),
        QAItem(
            question=case.question,
            answer=case.answer,
        ),
        QAItem(
            question=f"How did sharing help {child.label} solve {case.title}?",
            answer=case.sharing,
        ),
        QAItem(
            question=f"What bad ending did {child.label} avoid?",
            answer=case.bad_ending,
        ),
        QAItem(
            question=f"What proved that {case.title} was solved?",
            answer=case.ending,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does elapse mean?",
            answer="Elapse means that time passes.",
        ),
        QAItem(
            question="Why can sharing a clue help in a mystery?",
            answer="Sharing a clue lets another person check it, add knowledge, and notice a better explanation.",
        ),
        QAItem(
            question="What is a bad ending in a story?",
            answer="A bad ending is an unhappy or harmful result that the characters may prevent through wiser choices.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:10} ({entity.kind:10}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random, seed: int) -> StoryParams:
    if args.place and args.place != "park":
        raise StoryError("This mystery storyworld only supports the park.")
    if args.activity and args.activity != "investigate":
        raise StoryError("The activity must be investigate.")
    if args.prize and args.prize != "mystery":
        raise StoryError("The prize must be mystery.")
    if args.name and args.name not in NAMES:
        raise StoryError("Name must be one of the registered child names.")
    if args.companion and args.companion not in COMPANIONS:
        raise StoryError("Companion must be one of the registered companion names.")
    if args.trait and args.trait not in TRAITS:
        raise StoryError("Trait must be one of the registered traits.")

    name = args.name or rng.choice(NAMES)
    companion = args.companion or rng.choice([x for x in COMPANIONS if x != name])
    return StoryParams(
        place="park",
        activity="investigate",
        prize="mystery",
        name=name,
        companion=companion,
        trait=args.trait or rng.choice(TRAITS),
        case=f"case_{seed % len(CASES):02d}",
        seed=seed,
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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A mystery storyworld about elapsed time, sharing, and avoiding a bad ending."
    )
    parser.add_argument("--place", choices=["park"])
    parser.add_argument("--activity", choices=["investigate"])
    parser.add_argument("--prize", choices=["mystery"])
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--companion", choices=COMPANIONS)
    parser.add_argument("--trait", choices=TRAITS)
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


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    clingo = set(asp_valid_combos())
    if py != clingo:
        print("MISMATCH between Python and ASP combinations.")
        print("Only in Python:", sorted(py - clingo))
        print("Only in ASP:", sorted(clingo - py))
        return 1

    for seed in range(5):
        params = resolve_params(argparse.Namespace(
            place=None, activity=None, prize=None, name=None,
            companion=None, trait=None,
        ), random.Random(seed), seed)
        sample = generate(params)
        if "sharing" not in sample.story.lower() and "shared" not in sample.story.lower():
            print("Generated story failed sharing check.")
            return 1
        if "elapse" not in sample.story.lower():
            print("Generated story failed elapse check.")
            return 1
    print(f"OK: ASP/Python parity verified ({len(py)} combo).")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index in range(len(CASES)):
            seed = base_seed + index
            params = resolve_params(args, random.Random(seed), seed)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        for index in range(max(1, args.n)):
            seed = base_seed + index
            params = resolve_params(args, random.Random(seed), seed)
            sample = generate(params)
            if sample.story not in seen:
                samples.append(sample)
                seen.add(sample.story)

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
