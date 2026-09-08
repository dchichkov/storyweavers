#!/usr/bin/env python3
"""
Standalone storyworld: an intrusive mystery, a gentle reconciliation, and a twist
told as a rhyming story.
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

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = ""
    owner: Optional[str] = None


@dataclass
class StoryParams:
    seed: Optional[int] = None
    place: str = "moonlit garden"
    protagonist: str = "Luna"
    protagonist_type: str = "girl"
    friend: str = "Milo"
    friend_type: str = "boy"
    gardener: str = "Tess"
    gardener_type: str = "woman"
    mystery_id: int = 0
    rhyme_id: int = 0


MYSTERIES = [
    {
        "title": "the whispering gate",
        "premise": "A silver gate squeaked each night, though no one touched its latch.",
        "clue": "a blue ribbon caught on a thorn beside the path",
        "twist": "the gate was not opening at all; a wind bell behind the hedge was making its voice",
        "action": "followed the ribbon and listened beside the hedge",
        "resolution": "Milo admitted he had blamed Luna too quickly, and Luna forgave him after he helped untangle the bell",
        "ending": "The gate stood still while the little bell sang to the moon.",
    },
    {
        "title": "the vanished lantern",
        "premise": "The garden lantern disappeared just before the evening visitors arrived.",
        "clue": "warm drops of candle wax beside a wheelbarrow",
        "twist": "the lantern had been moved by Tess to guide a sleepy hedgehog away from the pond",
        "action": "traced the wax marks without stepping into the flower beds",
        "resolution": "Milo apologized for his intrusive questions, and Luna told him that asking kindly was welcome",
        "ending": "The lantern glowed beside the pond, and no shadow looked lonely.",
    },
    {
        "title": "the backwards footprints",
        "premise": "Tiny footprints crossed the wet soil, then seemed to walk backward into the roses.",
        "clue": "a fallen paper crown near the rose arch",
        "twist": "the prints belonged to a toy mouse being pulled by a thread, not to a secret creature",
        "action": "examined the crown and watched the marks from the safe stone path",
        "resolution": "Luna and Milo laughed, then agreed that curiosity should knock before it barged in",
        "ending": "The toy mouse rolled home beneath a crown of dew.",
    },
    {
        "title": "the humming basket",
        "premise": "A covered basket hummed softly beneath the old pear tree.",
        "clue": "a trail of petals leading from the basket to a broken music box",
        "twist": "the hum came from a bee trapped in the music box's open lid",
        "action": "called Tess instead of lifting the cover",
        "resolution": "Milo made peace with Luna by saying he would ask before peeking into her things",
        "ending": "The bee flew free, and the music box played one bright note.",
    },
]


RHYME_OPENINGS = [
    "By moonlit leaves where fireflies flew, / A puzzling thing came into view.",
    "Beneath the stars, beside the gate, / A little mystery stayed up late.",
    "Where silver petals caught the light, / A secret stirred one quiet night.",
    "In gardens washed with midnight blue, / A strange small question waited too.",
]

RHYME_LESSONS = [
    "A question asked with care can mend / The fraying thread between a friend.",
    "Do not push through every door; / Ask first, and friendship blooms once more.",
    "A hasty guess may point blame's way; / Kind listening brings truth to day.",
    "When secrets seem to hide from sight, / Gentle words can make them light.",
]


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def reason_gate(params: StoryParams) -> None:
    names = [params.protagonist.strip(), params.friend.strip(), params.gardener.strip()]
    if not all(names):
        raise StoryError("Character names must not be empty.")
    if len(set(name.lower() for name in names)) != len(names):
        raise StoryError("The protagonist, friend, and gardener need different names.")
    if params.place != "moonlit garden":
        raise StoryError("This storyworld uses the moonlit garden as its setting.")


def build_world(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity(
        "hero", "character", params.protagonist_type, params.protagonist,
        memes={"curiosity": 1.0, "hurt": 0.0, "trust": 0.0},
        location=params.place,
    ))
    friend = world.add(Entity(
        "friend", "character", params.friend_type, params.friend,
        memes={"curiosity": 1.0, "intrusive": 0.0, "trust": 0.0},
        location=params.place,
    ))
    gardener = world.add(Entity(
        "gardener", "character", params.gardener_type, params.gardener,
        memes={"patience": 1.0, "trust": 1.0},
        location=params.place,
    ))
    mystery = world.add(Entity(
        "mystery", "thing", "mystery", "the garden mystery",
        meters={"uncertainty": 1.0, "solved": 0.0},
        location=params.place,
    ))
    world.facts.update(hero=hero, friend=friend, gardener=gardener, mystery=mystery)
    return world


def tell(params: StoryParams) -> World:
    reason_gate(params)
    world = build_world(params)
    hero = world.get("hero")
    friend = world.get("friend")
    gardener = world.get("gardener")
    mystery = world.get("mystery")
    case = MYSTERIES[params.mystery_id % len(MYSTERIES)]
    lesson = RHYME_LESSONS[params.rhyme_id % len(RHYME_LESSONS)]
    opening = RHYME_OPENINGS[params.rhyme_id % len(RHYME_OPENINGS)]

    world.facts.update(case=case, lesson=lesson, solved=True, twist=case["twist"])
    friend.memes["intrusive"] = 1.0
    hero.memes["hurt"] = 1.0

    world.say(
        f"{opening} {hero.label} walked with {friend.label}, whose questions came near, "
        f"then nearer still, with an intrusive cheer."
    )
    world.say(
        f"{case['premise']} {mystery.label.capitalize()} made the moonlight seem strange, "
        f"and {friend.label} pointed at {hero.label}. "
        f"'Did you hide it?' {friend.label} asked. 'That guess feels unkind,' said {hero.label}, "
        "'but we can seek the truth we find.'"
    )

    world.para()
    world.say(
        f"{hero.label} noticed {case['clue']}; it glittered beside the trail, "
        "a tiny sign beneath the moon, a clue upon the veil."
    )
    world.say(
        f"{gardener.label} called, 'Stay on the path and do not lift that lid.' "
        f"{friend.label} answered, 'I am sorry. I should have asked before I did.'"
    )
    world.say(
        f"Together they {case['action']}. Then came the twist: {case['twist']}."
    )
    mystery.meters["uncertainty"] = 0.0
    mystery.meters["solved"] = 1.0
    world.fired.add("twist")

    world.para()
    world.say(
        f"{case['resolution']}. {hero.label} said, 'Your questions may come, but knock first, please.' "
        f"{friend.label} replied, 'I will. I want our friendship to feel at ease.'"
    )
    friend.memes["intrusive"] = 0.0
    friend.memes["trust"] = 1.0
    hero.memes["hurt"] = 0.0
    hero.memes["trust"] = 1.0
    world.say(f"{lesson} {case['ending']}")
    return world


def generation_prompts(world: World) -> list[str]:
    case = world.facts["case"]
    hero = world.get("hero")
    friend = world.get("friend")
    return [
        f"Write a rhyming mystery story about {case['title']} in a moonlit garden.",
        f"Show how {hero.label} and {friend.label} repair their friendship after intrusive questioning.",
        f"Include a twist revealing that {case['twist']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    case = world.facts["case"]
    hero = world.get("hero")
    friend = world.get("friend")
    gardener = world.get("gardener")
    return [
        QAItem(
            f"What mystery did {hero.label} and {friend.label} investigate?",
            f"They investigated {case['title']}: {case['premise']}",
        ),
        QAItem(
            f"What clue did {hero.label} find?",
            f"{hero.label} found {case['clue']}, which gave them a safe detail to follow.",
        ),
        QAItem(
            "What was the twist?",
            f"The twist was that {case['twist']}.",
        ),
        QAItem(
            f"How did {friend.label} make peace with {hero.label}?",
            f"{case['resolution']}. The friends changed their behavior by replacing blame with a respectful question.",
        ),
        QAItem(
            f"How did {gardener.label} help?",
            f"{gardener.label} reminded them to stay on the path and avoid lifting or touching unknown things.",
        ),
        QAItem(
            "What lesson did the rhyming story teach?",
            f"It taught that {world.facts['lesson']}",
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        "What does intrusive mean?",
        "Intrusive means pushing into someone's space, privacy, or conversation without being invited.",
    ),
    QAItem(
        "Why is asking permission helpful?",
        "Asking permission shows respect and gives another person a chance to feel safe and ready.",
    ),
    QAItem(
        "What is reconciliation?",
        "Reconciliation is making peace after hurt or disagreement by listening, apologizing, and changing behavior.",
    ),
]


def world_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        meters = {k: round(v, 3) for k, v in entity.meters.items() if v}
        memes = {k: round(v, 3) for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id:9} ({entity.type:10}) "
            f"meters={meters} memes={memes} location={entity.location}"
        )
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
intrusive(friend) :- character(friend), questions_without_permission(friend).
reconciled(hero,friend) :- apology(friend), changed_behavior(friend).
solved(mystery) :- clue_found, twist_revealed.
coherent :- solved(mystery), reconciled(hero,friend), not unsafe_touch.
#show coherent/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("character", "hero"),
        asp.fact("character", "friend"),
        asp.fact("character", "gardener"),
        asp.fact("questions_without_permission", "friend"),
        asp.fact("apology", "friend"),
        asp.fact("changed_behavior", "friend"),
        asp.fact("clue_found"),
        asp.fact("twist_revealed"),
    ])


def asp_program(show: str = "#show coherent/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    asp_ok = any(symbol.name == "coherent" for symbol in model)
    py_ok = True
    if asp_ok != py_ok:
        print("MISMATCH between ASP and Python reasonableness gate.")
        return 1
    sample = generate(StoryParams())
    if not sample.story or "twist" not in sample.story.lower():
        print("MISMATCH: generated story check failed.")
        return 1
    print("OK: ASP and Python reasonableness gate agree.")
    print("OK: generated story check passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Intrusive reconciliation mystery in rhyming-story style."
    )
    parser.add_argument("--place", choices=["moonlit garden"], default="moonlit garden")
    parser.add_argument("--protagonist")
    parser.add_argument("--protagonist-type", choices=["girl", "boy", "woman", "man"], default="girl")
    parser.add_argument("--friend")
    parser.add_argument("--friend-type", choices=["girl", "boy", "woman", "man"], default="boy")
    parser.add_argument("--gardener")
    parser.add_argument("--gardener-type", choices=["girl", "boy", "woman", "man"], default="woman")
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


def resolve_params(args: argparse.Namespace, rng: random.Random, sample_seed: int) -> StoryParams:
    protagonist = args.protagonist or rng.choice(["Luna", "Iris", "Nell", "Mara"])
    friend = args.friend or rng.choice(["Milo", "Pip", "Theo", "Finn"])
    gardener = args.gardener or rng.choice(["Tess", "Mira", "June", "Asha"])
    if len({protagonist.lower(), friend.lower(), gardener.lower()}) != 3:
        raise StoryError("Names must be distinct.")
    return StoryParams(
        seed=args.seed,
        place=args.place,
        protagonist=protagonist,
        protagonist_type=args.protagonist_type,
        friend=friend,
        friend_type=args.friend_type,
        gardener=gardener,
        gardener_type=args.gardener_type,
        mystery_id=sample_seed % len(MYSTERIES),
        rhyme_id=(sample_seed // len(MYSTERIES)) % len(RHYME_OPENINGS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        presets = [
            ("Luna", "Milo", "Tess"),
            ("Iris", "Pip", "Mira"),
            ("Nell", "Theo", "June"),
            ("Mara", "Finn", "Asha"),
        ]
        for offset, (hero, friend, gardener) in enumerate(presets):
            params = StoryParams(
                seed=base_seed + offset,
                protagonist=hero,
                friend=friend,
                gardener=gardener,
                mystery_id=(base_seed + offset) % len(MYSTERIES),
                rhyme_id=((base_seed + offset) // len(MYSTERIES)) % len(RHYME_OPENINGS),
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        for offset in range(max(args.n * 20, 20)):
            if len(samples) >= args.n:
                break
            seed = base_seed + offset
            try:
                params = resolve_params(args, random.Random(seed), seed)
                params.seed = seed
                sample = generate(params)
            except StoryError:
                continue
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
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
