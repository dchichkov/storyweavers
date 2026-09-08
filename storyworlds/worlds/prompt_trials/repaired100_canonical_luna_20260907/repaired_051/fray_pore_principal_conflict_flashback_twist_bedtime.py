#!/usr/bin/env python3
"""
A gentle bedtime storyworld about a frayed curtain, a curious pore, and a
principal who learns that a small opening can let kindness through.
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
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(
        default_factory=lambda: {"distance": 0.0, "strength": 0.0, "warmth": 0.0}
    )
    memes: dict[str, float] = field(
        default_factory=lambda: {
            "worry": 0.0,
            "courage": 0.0,
            "trust": 0.0,
            "relief": 0.0,
            "wonder": 0.0,
        }
    )


@dataclass
class Setting:
    place: str = "Moonbeam School"


@dataclass
class StoryParams:
    child_name: str
    child_type: str
    principal_name: str
    companion_name: str
    companion_type: str
    curtain_color: str
    bedtime_object: str
    scenario_index: int = 0
    detail_variant: int = 0
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    trace_log: list[str] = field(default_factory=list)

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

    def log(self, text: str) -> None:
        self.trace_log.append(text)


SCENARIOS = [
    {
        "room": "the little observatory",
        "problem": "The silver curtain had begun to fray beside a tiny pore, and moonlight spilled through the tear in a crooked stripe.",
        "conflict": "The principal wanted to close the curtain before bedtime, but the child feared that the sleeping stars would disappear.",
        "flashback": "The child remembered how the principal had once said that even a pinprick of sky could help a lonely heart find its way home.",
        "clue": "A soft star-shaped stitch was still hidden in the curtain's hem.",
        "action": "The friends loosened the rough threads, placed a small patch around the pore, and sewed the star stitch over it.",
        "twist": "When they finished, the pore was not gone. It had become a neat little window for one bright star.",
        "resolution": "The curtain was strong again, yet the room kept one peaceful glimpse of the night.",
        "image": "one star shone through the tiny window while every child slept quietly below",
        "lesson": "repair does not always mean hiding every small opening",
    },
    {
        "room": "the quiet music room",
        "problem": "A velvet curtain had started to fray near a round pore, and a cold draft was making the lullaby bells tremble.",
        "conflict": "The principal wished to replace the curtain, while the child hoped to save the old cloth that had sheltered many evening songs.",
        "flashback": "A bedtime memory returned: the principal had once wrapped the same curtain around a shivering kitten during a storm.",
        "clue": "The old cloth still held a warm thread stitched by many careful hands.",
        "action": "They trimmed only the loose threads, tucked the warm thread around the pore, and added a soft lining behind it.",
        "twist": "The curtain's hidden lining had belonged to the school's first music teacher, whose quiet note was sewn inside.",
        "resolution": "The curtain hung safely again, and the bells rang softly without a shiver.",
        "image": "the repaired velvet breathed gently beside the sleeping music bells",
        "lesson": "old kindness can become new strength",
    },
    {
        "room": "the lantern library",
        "problem": "The reading curtain was beginning to fray around a thumb-sized pore, letting dust drift onto the bedtime books.",
        "conflict": "The principal wanted a perfectly smooth curtain, but the child wondered whether the pore had something to teach them.",
        "flashback": "The child recalled a rainy night when the principal had read aloud beside that very opening until everyone felt safe.",
        "clue": "Dust gathered in a ring shaped like a tiny crescent moon.",
        "action": "They brushed the cloth clean, stitched the frayed edge, and placed a clear patch behind the pore.",
        "twist": "The clear patch turned the pore into a small lens that made the lantern light look like a moon.",
        "resolution": "The books stayed clean, and the curtain glowed with a calm silver circle.",
        "image": "a round moon of light rested on the last page of the bedtime book",
        "lesson": "a flaw can sometimes become a gentle gift",
    },
]


CHILD_NAMES = ["Luna", "Mira", "Theo", "Nell", "Pip"]
CHILD_TYPES = ["rabbit", "fox", "mouse", "bear", "cat"]
COMPANION_NAMES = ["Moss", "Tilly", "Bram", "Dove", "Juniper"]
COMPANION_TYPES = ["owl", "mouse", "badger", "kitten", "squirrel"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bedtime Story: fray, pore, and principal.")
    parser.add_argument("--child")
    parser.add_argument("--type")
    parser.add_argument("--principal")
    parser.add_argument("--companion")
    parser.add_argument("--companion-type")
    parser.add_argument("--color")
    parser.add_argument("--object")
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
    return StoryParams(
        child_name=args.child or rng.choice(CHILD_NAMES),
        child_type=args.type or rng.choice(CHILD_TYPES),
        principal_name=args.principal or rng.choice(["Principal Fern", "Principal Rowan", "Principal Willow"]),
        companion_name=args.companion or rng.choice(COMPANION_NAMES),
        companion_type=args.companion_type or rng.choice(COMPANION_TYPES),
        curtain_color=args.color or rng.choice(["blue", "violet", "green", "silver"]),
        bedtime_object=args.object or rng.choice(["a moon book", "a soft blanket", "a tiny music box"]),
        scenario_index=rng.randrange(len(SCENARIOS)),
        detail_variant=rng.randrange(10000),
    )


def tell(params: StoryParams) -> World:
    if not params.child_name.strip():
        raise StoryError("child name must not be empty")
    if params.child_name.lower() == params.principal_name.lower():
        raise StoryError("the child and principal need different names")

    scenario = SCENARIOS[params.scenario_index % len(SCENARIOS)]
    world = World(Setting())
    child = world.add(Entity("child", "animal", params.child_name))
    companion = world.add(Entity("companion", "animal", params.companion_name))
    principal = world.add(Entity("principal", "person", params.principal_name))
    curtain = world.add(Entity("curtain", "thing", f"{params.curtain_color} curtain"))
    pore = world.add(Entity("pore", "opening", "tiny pore"))
    world.facts.update(
        child=child,
        companion=companion,
        principal=principal,
        curtain=curtain,
        pore=pore,
        scenario=scenario,
    )

    child.memes["worry"] = 1.0
    companion.memes["trust"] = 1.0
    principal.memes["worry"] = 1.0
    curtain.meters["strength"] = 0.35
    pore.meters["distance"] = 1.0

    world.say(
        f"At bedtime, {params.child_name} the {params.child_type} carried {params.bedtime_object} "
        f"to {world.setting.place}, where the lamps were dim and kind."
    )
    world.say(
        f"{params.principal_name}, the principal, waited in {scenario['room']} beside a "
        f"{params.curtain_color} curtain."
    )
    world.say(scenario["problem"])
    world.say(f'"Perhaps the curtain is only tired," said {params.child_name}.')
    world.say(
        f'"Perhaps it should be replaced," replied {params.principal_name}. '
        f'"I must keep everyone warm and safe."'
    )
    world.para()

    world.say(scenario["conflict"])
    world.say(
        f'{params.companion_name} the {params.companion_type} touched the cloth and whispered, '
        f'"Let us look closely before we choose."'
    )
    world.say(scenario["flashback"])
    child.memes["courage"] = 1.0
    principal.memes["trust"] = 1.0
    world.para()

    world.say(scenario["clue"])
    world.say(
        f'"The fray is around the pore, not across the whole curtain," '
        f'{params.child_name} said.'
    )
    world.say(
        f'"Then we can mend the weak place carefully," said {params.principal_name}. '
        f'"You noticed what I hurried past."'
    )
    world.say(scenario["action"])
    curtain.meters["strength"] = 1.0
    pore.meters["distance"] = 0.5
    companion.memes["joy"] = 1.0
    world.para()

    world.say(scenario["twist"])
    world.say(scenario["resolution"])
    principal.memes["relief"] = 1.0
    child.memes["wonder"] = 1.0
    child.memes["relief"] = 1.0
    world.say(
        f'"A small opening can still let in something good," said {params.principal_name}.'
    )
    world.say(scenario["lesson"].capitalize() + ".")
    world.say(f"That night, {scenario['image']}.")
    world.log("conflict=curtain safety versus preserving a meaningful old cloth")
    world.log("flashback=the principal remembered an earlier act of shelter")
    world.log("twist=the pore became a useful window rather than a hidden defect")
    return world


def generation_prompts(world: World) -> list[str]:
    scenario = world.facts["scenario"]
    child: Entity = world.facts["child"]
    principal: Entity = world.facts["principal"]
    return [
        f"Write a gentle bedtime story about {child.label} and {principal.label}, a principal.",
        f"Include a fray and a pore in a curtain, then let a conflict become a kind repair.",
        f"Use a flashback and a twist to show how {child.label}'s careful observation changes the ending.",
        f"End with a peaceful nighttime image and the lesson that {scenario['lesson']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    scenario = world.facts["scenario"]
    child: Entity = world.facts["child"]
    principal: Entity = world.facts["principal"]
    companion: Entity = world.facts["companion"]
    return [
        QAItem(
            question=f"What problem did {child.label} discover?",
            answer=f"{child.label} discovered that the curtain was beginning to fray around a tiny pore, allowing an unwanted draft or dust to pass through.",
        ),
        QAItem(
            question=f"What conflict did {principal.label} and {child.label} face?",
            answer=f"{principal.label} wanted to replace or close the curtain for safety, while {child.label} hoped to preserve the old cloth and understand the small opening first.",
        ),
        QAItem(
            question="What did the flashback reveal?",
            answer=f"The flashback revealed that {principal.label} had once used the same curtain to shelter someone during a difficult night, so the old cloth carried a memory of kindness.",
        ),
        QAItem(
            question=f"How did {companion.label} help?",
            answer=f"{companion.label} encouraged everyone to look closely before choosing, which helped them notice that the fray was limited to the area around the pore.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=f"The twist was that the pore did not need to be erased completely; after careful mending, it became a small useful window for moonlight or starlight.",
        ),
        QAItem(
            question="What changed by the ending?",
            answer=f"The curtain became strong and safe again, while its little opening let in a peaceful point of night light.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean for cloth to fray?",
            answer="When cloth frays, its woven threads begin to loosen or come apart along an edge or worn spot.",
        ),
        QAItem(
            question="What is a pore?",
            answer="A pore is a very small opening or passage in a surface, such as cloth, skin, or another material.",
        ),
        QAItem(
            question="What does a principal do at a school?",
            answer="A principal helps lead a school, cares about its students and staff, and makes decisions that support safety and learning.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a passage that briefly shows an earlier event so the reader can understand the present more deeply.",
        ),
        QAItem(
            question="What is a twist?",
            answer="A twist is an unexpected change or discovery that makes the events of a story look different from what the reader first expected.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        meters = {k: round(v, 2) for k, v in entity.meters.items() if v}
        memes = {k: round(v, 2) for k, v in entity.memes.items() if v}
        lines.append(
            f"{entity.id}: kind={entity.kind}, meters={meters}, memes={memes}"
        )
    lines.extend(world.trace_log)
    return "\n".join(lines)


ASP_RULES = r"""
entity(child).
entity(companion).
entity(principal).
entity(curtain).
entity(pore).

mended(curtain) :- careful_look(child), safe_plan(principal), repaired(pore).
peaceful_end :- mended(curtain), useful(pore).
#show mended/1.
#show peaceful_end/0.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("careful_look", "child"),
            asp.fact("safe_plan", "principal"),
            asp.fact("repaired", "pore"),
            asp.fact("useful", "pore"),
        ]
    )


def asp_program(show: str = "#show mended/1. #show peaceful_end/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    found = {f"{symbol.name}/{len(symbol.arguments)}" for symbol in model}
    expected = {"mended/1", "peaceful_end/0"}
    if found == expected:
        print("OK: ASP parity check passed.")
        return 0
    print(f"MISMATCH: {sorted(found)} != {sorted(expected)}")
    return 1


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
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(
        child_name="Luna",
        child_type="rabbit",
        principal_name="Principal Fern",
        companion_name="Moss",
        companion_type="owl",
        curtain_color="silver",
        bedtime_object="a moon book",
        scenario_index=0,
    ),
    StoryParams(
        child_name="Mira",
        child_type="mouse",
        principal_name="Principal Rowan",
        companion_name="Tilly",
        companion_type="squirrel",
        curtain_color="violet",
        bedtime_object="a soft blanket",
        scenario_index=1,
    ),
    StoryParams(
        child_name="Theo",
        child_type="fox",
        principal_name="Principal Willow",
        companion_name="Dove",
        companion_type="kitten",
        curtain_color="green",
        bedtime_object="a tiny music box",
        scenario_index=2,
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
        print("ASP model:", " ".join(str(atom) for atom in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < max(0, args.n) and attempt < max(20, args.n * 20):
            rng = random.Random(base_seed + attempt)
            params = resolve_params(args, rng)
            params.seed = base_seed + attempt
            attempt += 1
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
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
