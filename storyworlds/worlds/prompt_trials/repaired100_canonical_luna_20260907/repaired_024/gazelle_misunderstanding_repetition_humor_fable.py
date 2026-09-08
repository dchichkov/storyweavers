#!/usr/bin/env python3
"""
A small fable about a gazelle, a mistaken word, and the value of asking twice.

The world simulates a gazelle who misunderstands a warning, repeats the same
mistake, and finally learns through gentle humor that a clear question can
save a great deal of running.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = next(
    parent for parent in Path(__file__).resolve().parents
    if (parent / "storyworlds" / "results.py").is_file()
)
sys.path.insert(0, str(ROOT / "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None


@dataclass(frozen=True)
class FableArc:
    id: str
    setting: str
    warning: str
    misunderstanding: str
    repeated_action: str
    consequence: str
    helper_line: str
    truth: str
    final_image: str
    lesson: str
    object_label: str


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)

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
    name: str
    place: str
    trait: str
    seed: Optional[int] = None


NAMES = ["Luna", "Zara", "Nia", "Mara", "Tali", "Suri"]
PLACES = ["the acacia plain", "the silver grassland", "the watering hollow"]
TRAITS = ["quick", "cheerful", "curious", "proud"]

ARCS = [
    FableArc(
        "shadow_stone",
        "the acacia plain",
        "Do not leap over the round stone until the sun is high.",
        "Luna thought the warning meant she should leap over the stone twice before noon.",
        "leaped over the stone, turned around, and leaped back over it",
        "On the second leap, she landed in a patch of sticky burrs.",
        "The tortoise blinked. \"I said wait for the sun, not race the stone.\"",
        "The low morning shadow had hidden a puddle beside the stone.",
        "The gazelle stood sparkling with burrs while the stone looked very pleased with itself.",
        "When a warning sounds puzzling, ask before repeating the mistake.",
        "the round stone",
    ),
    FableArc(
        "quiet_pool",
        "the silver grassland",
        "Keep your hooves quiet near the little pool.",
        "Luna heard 'quiet pool' and decided the pool must be sleeping, so she tiptoed in circles around it.",
        "tiptoed around the water three times, each time nearer the middle",
        "Her hoof slipped, and she sat down with a splash that startled every frog.",
        "The frog croaked, \"Quiet means soft steps, not a parade for one hoof.\"",
        "The frogs had been resting beneath the reeds and needed still water.",
        "Luna wore a necklace of pondweed, and the frogs applauded from the mud.",
        "A repeated guess does not become true just because it is repeated.",
        "the little pool",
    ),
    FableArc(
        "thorn_gate",
        "the watering hollow",
        "Pass the thorn gate slowly.",
        "Luna thought slowly meant she should walk the same tiny step again and again.",
        "took one tiny step, stopped, and took the same tiny step again and again",
        "The gate did not hurt her, but her own careful circle made her late for the cool water.",
        "The old owl chuckled. \"Slow is a road, not a song stuck on one note.\"",
        "The safe path curved around the thorns and needed patience, not endless stopping.",
        "By sunset, Luna had made a perfect little trail shaped like a comma.",
        "Careful action needs understanding, not merely repetition.",
        "the thorn gate",
    ),
    FableArc(
        "red_feather",
        "the acacia plain",
        "Leave the red feather where it lies.",
        "Luna believed 'leave it' meant carry it away before someone else did.",
        "picked up the feather, put it down, and picked it up again",
        "A breeze blew the feather onto her nose, where it tickled until she sneezed.",
        "The monkey laughed. \"You have made a feather into a hat, a broom, and now a mustache.\"",
        "The feather belonged to a bird building a nest nearby.",
        "Luna sneezed the feather back toward the nest and bowed to her own ridiculous mustache.",
        "A word can be heard wrongly even when the ears are working well.",
        "the red feather",
    ),
    FableArc(
        "echo_bush",
        "the silver grassland",
        "Do not answer the echo from the thorn bush.",
        "Luna thought the echo was a lonely animal asking to play.",
        "called 'Hello!' once, twice, and then louder each time",
        "The echo bounced back so loudly that Luna hid behind her own tail.",
        "The weaverbird said, \"That friend always agrees with you, but it never knows anything.\"",
        "The bush was empty; the strange voice was only Luna's words returning.",
        "The gazelle and her tail peeped from opposite sides of the bush, both pretending not to be scared.",
        "A repeated answer is not proof that another creature understands you.",
        "the thorn bush",
    ),
]

OPENINGS = [
    "One bright morning",
    "At the first gold of day",
    "When the grass still held drops of dew",
    "Before the warm wind woke",
]

PAUSES = [
    "Luna tilted one ear and tried to make sense of the warning",
    "Luna nodded quickly, though one ear was listening and the other was guessing",
    "Luna looked at the ground, then at the sky, then back at the ground",
]

REFLECTIONS = [
    "The plain had not changed; only Luna's meaning had changed.",
    "The funniest part was that the warning had been short, but Luna had made her answer very long.",
    "Even the birds learned something: a second question is lighter than a third mistake.",
]

ASP_RULES = r"""
misunderstands(G) :- gazelle(G), hears_warning(G), not asks_question(G).
repeats(G) :- misunderstands(G), repeats_action(G).
comic_cost(G) :- repeats(G), obstacle_near(G).
learns(G) :- comic_cost(G), asks_question_after(G).
safe_ending(G) :- learns(G).
#show misunderstands/1.
#show repeats/1.
#show comic_cost/1.
#show learns/1.
#show safe_ending/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("gazelle", "luna"),
            asp.fact("hears_warning", "luna"),
            asp.fact("repeats_action", "luna"),
            asp.fact("obstacle_near", "luna"),
            asp.fact("asks_question_after", "luna"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    names = {atom.name for atom in model}
    expected = {"misunderstands", "repeats", "comic_cost", "learns", "safe_ending"}
    if expected.issubset(names):
        print("OK: ASP and Python agree that misunderstanding, repetition, humor, and learning occur.")
        return 0
    print("MISMATCH: ASP did not derive the complete fable arc.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a humorous fable about a gazelle's misunderstanding."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--trait", choices=TRAITS)
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
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        place=args.place or rng.choice(PLACES),
        trait=args.trait or rng.choice(TRAITS),
        seed=None,
    )


def tell(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError(f"Unknown setting: {params.place}")
    if params.trait not in TRAITS:
        raise StoryError(f"Unknown trait: {params.trait}")

    seed = params.seed
    if seed is None:
        seed = sum(ord(c) for c in f"{params.name}|{params.place}|{params.trait}")
    cursor = seed
    arc = ARCS[cursor % len(ARCS)]
    cursor //= len(ARCS)
    opening = OPENINGS[cursor % len(OPENINGS)]
    cursor //= len(OPENINGS)
    pause = PAUSES[cursor % len(PAUSES)]
    cursor //= len(PAUSES)
    reflection = REFLECTIONS[cursor % len(REFLECTIONS)]

    world = World()
    gazelle = world.add(
        Entity(
            id="luna",
            kind="animal",
            type="gazelle",
            label=params.name,
            memes={"confidence": 1.0, "curiosity": 1.0, "understanding": 0.0},
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="animal",
            type="helper",
            label="the tortoise",
        )
    )
    obstacle = world.add(
        Entity(
            id="obstacle",
            kind="thing",
            type="obstacle",
            label=arc.object_label,
        )
    )
    world.facts.update(
        arc=arc,
        gazelle=gazelle,
        helper=helper,
        obstacle=obstacle,
        place=arc.setting,
        misunderstanding=True,
        repetition_count=2,
        humor=True,
    )

    world.say(f"{opening}, a {params.trait} gazelle named {params.name} bounded across {arc.setting}.")
    world.say(f"Near {arc.object_label}, {arc.warning}")
    world.para()

    gazelle.memes["heard_warning"] = 1.0
    world.say(f"{params.name} {pause}.")
    world.say(f"\"Did you say I must do the same thing twice?\" asked {params.name}.")
    world.say(f"\"No,\" said the tortoise. \"I said, {arc.warning.lower()}\"")
    world.say(f"But {params.name} understood the warning as this: {arc.misunderstanding}.")
    gazelle.meters["misunderstood"] = 1.0

    world.para()
    world.say(f"First, {params.name} {arc.repeated_action}.")
    world.say(f"Then {params.name} did it again, because repetition sounded like excellent evidence.")
    gazelle.meters["repeated"] = 1.0
    world.say(arc.consequence)
    world.say(f"\"Again?\" asked the tortoise. \"That was the joke the first time.\"")
    world.say(f"\"I was not trying to be funny,\" said {params.name}. \"My hooves were following my ears.\"")
    world.say(arc.helper_line)

    world.para()
    world.say(arc.truth)
    world.say(f"{params.name} finally asked, \"What should I do now?\"")
    world.say(f"The tortoise gave a clear answer: \"Listen, check, and then choose.\"")
    gazelle.memes["understanding"] = 1.0
    gazelle.meters["asked_question"] = 1.0
    world.say(f"{params.name} followed the safe way and left {arc.object_label} in peace.")
    world.say(reflection)
    world.say(f"{arc.final_image} {params.name} remembered that {arc.lesson}")

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    arc: FableArc = world.facts["arc"]  # type: ignore[assignment]
    gazelle: Entity = world.facts["gazelle"]  # type: ignore[assignment]
    return [
        f"Write a humorous fable about gazelle {gazelle.label}, who misunderstands this warning: {arc.warning}",
        f"Tell a child-facing story in which {gazelle.label} repeats a mistaken action near {arc.object_label}.",
        f"Write a fable showing that {arc.lesson}",
    ]


def story_qa(world: World) -> list[QAItem]:
    arc: FableArc = world.facts["arc"]  # type: ignore[assignment]
    gazelle: Entity = world.facts["gazelle"]  # type: ignore[assignment]
    return [
        QAItem(
            question="Who was the main character?",
            answer=f"The main character was {gazelle.label}, a gazelle who was quick and curious but misunderstood a warning.",
        ),
        QAItem(
            question=f"What did {gazelle.label} misunderstand?",
            answer=f"{gazelle.label} misunderstood the warning, thinking that {arc.misunderstanding}.",
        ),
        QAItem(
            question=f"How did repetition make the situation funny?",
            answer=f"{gazelle.label} {arc.repeated_action}, and then repeated the same mistake, making the tortoise joke that the second try was already funny.",
        ),
        QAItem(
            question=f"What did {gazelle.label} learn?",
            answer=f"{gazelle.label} learned that {arc.lesson}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a gazelle?",
            answer="A gazelle is a swift, slender antelope that lives in open grasslands and can leap quickly to escape danger.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone hears or sees something but gives it the wrong meaning.",
        ),
        QAItem(
            question="Why can repetition be humorous?",
            answer="Repetition can be humorous when a character keeps doing the same surprising thing while everyone else understands the mistake.",
        ),
        QAItem(
            question="What is a fable?",
            answer="A fable is a short story, often with animal characters, that ends with a lesson about wise behavior.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"- {prompt}" for prompt in sample.prompts)
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: type={entity.type}, meters={entity.meters}, memes={entity.memes}"
        )
    lines.append(f"facts={{misunderstanding: {world.facts['misunderstanding']}, repetition_count: {world.facts['repetition_count']}, humor: {world.facts['humor']}, resolved: {world.facts['resolved']}}}")
    return "\n".join(lines)


CURATED = [
    StoryParams(name="Luna", place="the acacia plain", trait="quick", seed=11),
    StoryParams(name="Zara", place="the silver grassland", trait="curious", seed=23),
    StoryParams(name="Nia", place="the watering hollow", trait="cheerful", seed=37),
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
        print(asp_program("#show misunderstands/1.\n#show repeats/1.\n#show comic_cost/1.\n#show learns/1.\n#show safe_ending/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print("ASP model:")
        for atom in model:
            print(atom)
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n:
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                samples.append(sample)
                seen.add(sample.story)
            index += 1

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
            print("\n" + "=" * 72 + "\n")


if __name__ == "__main__":
    main()
