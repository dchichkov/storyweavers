#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))),
)
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


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
    facts: dict[str, str] = field(default_factory=dict)
    paragraphs: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def render(self) -> str:
        return "\n\n".join(self.paragraphs)


@dataclass
class StoryParams:
    child_name: str
    elder_name: str
    village_name: str
    seed: Optional[int] = None


NAMES = ["Luna", "Mira", "Tavi", "Niko", "Suri", "Oren", "Pia", "Kito"]
ELDERS = ["Grandmother Asha", "Old Rowan", "Keeper Imani", "Grandfather Sol"]
VILLAGES = ["Willow Hollow", "Red Clay Village", "Moonfield", "the Valley of Bells"]


ARCS = [
    {
        "key": "lantern",
        "premise": "{child} lived in {village}, where people left broken things beside the village fire. One evening, {elder} asked {child} to gather the scrap before the wind scattered it.",
        "problem": "{child} saw bent wire, cracked pots, and a torn blue cloth. Everyone called it useless, but a storm was coming, and the village had no bright marker for travelers on the dark mountain path.",
        "dialogue": "\"Why save this old scrap?\" asked {child}. \"Because even a small piece may remember a purpose,\" said {elder}. Their words made {child} look again instead of turning away.",
        "turn": "{child} noticed that the blue cloth still caught moonlight, the wire could hold a frame, and the cracked pots could become little shades. The forgotten pile held the parts of a lantern.",
        "action": "Together, {child} and {elder} bent the wire, tied the cloth, and placed a warm coal inside a cleaned pot. {child} worked patiently, while {elder} showed how careful hands could transform discarded things.",
        "resolution": "By nightfall, the scrap had become a tall lantern. Its blue light marked the safe path, and three lost shepherds followed it home through the rain.",
        "ending": "At dawn, the villagers placed the lantern beside the fire. It shone above the remaining scrap, reminding everyone that worth can hide beneath a broken appearance.",
        "problem_fact": "the village needed a safe light for a storm-dark mountain path",
        "turn_fact": "the child discovered that different scraps could become parts of a lantern",
        "action_fact": "the child and elder patiently joined the scrap into a lantern",
        "outcome_fact": "the lantern guided lost shepherds safely home",
        "value": "careful reuse can reveal hidden worth",
    },
    {
        "key": "seed_bowl",
        "premise": "In {village}, {child} found a pile of scrap near the dry garden wall. {elder} carried a small pouch of seeds and asked {child} to help prepare the earth before the moon rose.",
        "problem": "The garden's water bowl had cracked, and the thirsty seeds could not be planted. The villagers wanted to throw away the old metal pieces, though the next harvest would feed many families.",
        "dialogue": "\"Scrap cannot hold water,\" said {child}. \"Not by itself,\" answered {elder}, \"but a patient mind can join what is scattered.\" {child} decided to test the idea.",
        "turn": "A curved sheet could form a basin, soft wire could stitch its split, and a flat shard could become a lid. The scrap was not one answer; it was a collection of beginnings.",
        "action": "{child} and {elder} shaped the pieces around a smooth stone, sealed the seams with clay, and filled the new bowl drop by drop. They shared the work instead of arguing over whose hands were stronger.",
        "resolution": "The bowl held enough water for the seeds. Weeks later, green vines climbed the wall, and the village gathered a generous harvest beneath their silver blossoms.",
        "ending": "The first ripe fruit was placed in the repaired bowl. No one called the scrap worthless again, because patient kindness had turned leftovers into food for everyone.",
        "problem_fact": "a cracked garden bowl could not hold water for the village seeds",
        "turn_fact": "the child saw several scraps that could join into a water basin",
        "action_fact": "the child and elder shaped and sealed the pieces with clay",
        "outcome_fact": "the repaired bowl watered seeds that fed the village",
        "value": "patience and shared work can nourish a whole community",
    },
    {
        "key": "bridge_bells",
        "premise": "A narrow river divided {village}, and {child} often watched travelers wait beside it. One morning, {elder} led {child} to a heap of scrap left by an old bridge.",
        "problem": "The river had risen, and the village bridge was broken. People blamed one another, while children on the far bank could not reach the school drum.",
        "dialogue": "\"The bridge is gone,\" said {child}. \"Its pieces are still here,\" replied {elder}. \"Will pieces remember how to stand?\" asked {child}. \"They will, if we give them a wise shape,\" said {elder}.",
        "turn": "The scrap included strong boards, bent nails, and bronze rings from the old bridge. {child} realized the rings could become warning bells and the boards could make a smaller, safer crossing.",
        "action": "{child}, {elder}, and the villagers laid the boards across the shallowest stones. They hammered the nails slowly and hung the bronze rings where a loose board would ring.",
        "resolution": "The new footbridge held firm. When the river rose again, its bells chimed a warning, and everyone crossed safely to hear the school drum.",
        "ending": "The bridge bells sang in the evening wind. The villagers remembered that cooperation could transform broken pieces into a promise of safety.",
        "problem_fact": "a flood had broken the bridge and separated the village",
        "turn_fact": "the child discovered useful boards and bronze rings in the bridge scrap",
        "action_fact": "the villagers built a small bridge with warning bells",
        "outcome_fact": "the new bridge let people cross safely and warned them of danger",
        "value": "cooperation turns shared difficulty into shared safety",
    },
]


def stable_rng(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed)
    text = "|".join((params.child_name, params.elder_name, params.village_name))
    digest = hashlib.sha256(text.encode()).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def tell(params: StoryParams) -> World:
    if params.child_name == params.elder_name:
        raise StoryError("The child and elder must have different names.")
    if params.village_name not in VILLAGES:
        raise StoryError("Unknown village choice.")
    rng = stable_rng(params)
    arc = ARCS[(params.seed if params.seed is not None else rng.randrange(len(ARCS))) % len(ARCS)]

    child = Entity(
        params.child_name,
        "character",
        "a thoughtful child",
        meters={"patience": 1.0, "confidence": 0.5},
        memes={"respect_for_scrap": 0.2, "generosity": 0.4},
    )
    elder = Entity(
        params.elder_name,
        "character",
        "a wise elder",
        meters={"patience": 1.0, "skill": 1.0},
        memes={"wisdom": 1.0, "care_for_others": 1.0},
    )
    scrap = Entity(
        "scrap",
        "material",
        "a heap of discarded pieces",
        meters={"usefulness": 0.2, "transformed": 0.0},
        memes={"neglected": 1.0, "hidden_worth": 0.8},
    )
    world = World()
    world.add(child)
    world.add(elder)
    world.add(scrap)

    beats = ["premise", "problem", "dialogue", "turn", "action", "resolution", "ending"]
    rendered = {}
    for beat in beats:
        rendered[beat] = arc[beat].format(
            child=params.child_name,
            elder=params.elder_name,
            village=params.village_name,
        )
        world.paragraphs.append(rendered[beat])

    scrap.meters["usefulness"] = 1.0
    scrap.meters["transformed"] = 1.0
    scrap.memes["neglected"] = 0.0
    scrap.memes["hidden_worth"] = 1.0
    child.meters["patience"] = 2.0
    child.meters["confidence"] = 1.0
    child.memes["respect_for_scrap"] = 1.0
    world.facts = {
        "arc": arc["key"],
        "child": params.child_name,
        "elder": params.elder_name,
        "village": params.village_name,
        "problem": arc["problem_fact"],
        "turn": arc["turn_fact"],
        "action": arc["action_fact"],
        "outcome": arc["outcome_fact"],
        "value": arc["value"],
        "problem_event": rendered["problem"],
        "turn_event": rendered["turn"],
        "action_event": rendered["action"],
        "resolution_event": rendered["resolution"],
    }
    return world


def generate_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a child-friendly myth about scrap that is transformed into something useful.",
        f"Tell a myth in which {f['child']} learns a moral value from {f['elder']} while helping {f['village']}.",
        "Create a short myth where patient cooperation reveals hidden worth in an ordinary object.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            f"What problem did {f['child']} and {f['elder']} face?",
            f["problem_event"],
        ),
        QAItem(
            "What transformation happened to the scrap?",
            f["turn_event"] + " " + f["action_event"],
        ),
        QAItem(
            "How did the characters help others?",
            f["resolution_event"],
        ),
        QAItem(
            "What moral value did the myth teach?",
            f"The myth taught that {f['value']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is scrap?",
            "Scrap is leftover or discarded material that may still be useful when it is repaired, reused, or reshaped.",
        ),
        QAItem(
            "What is transformation?",
            "Transformation is a change from one form or condition into another.",
        ),
        QAItem(
            "What is a moral value?",
            "A moral value is a principle that helps people choose caring, honest, brave, or responsible actions.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id:10} ({entity.kind:9}) meters={meters} memes={memes}")
    lines.append(f"  arc={world.facts.get('arc')}")
    lines.append(f"  moral_value={world.facts.get('value')}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_story :- has_scrap, has_transformation, has_moral_value, has_myth_style.
has_scrap.
has_transformation.
has_moral_value.
has_myth_style.
#show valid_story/0.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("theme", "scrap"),
            asp.fact("feature", "transformation"),
            asp.fact("feature", "moral_value"),
            asp.fact("style", "myth"),
        ]
    )


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program())
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    if any(symbol.name == "valid_story" for symbol in model):
        sample = generate(StoryParams("Luna", "Grandmother Asha", "Moonfield", seed=0))
        if "scrap" in sample.story.lower() and "transformed" in sample.story.lower():
            print("OK: ASP and Python recognize the scrap transformation myth.")
            return 0
    print("MISMATCH: ASP/Python parity check failed.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A mythic scrap-transformation storyworld.")
    parser.add_argument("--child-name")
    parser.add_argument("--elder-name")
    parser.add_argument("--village-name", choices=VILLAGES)
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
    child = args.child_name or rng.choice(NAMES)
    elder_pool = [name for name in ELDERS if name != child]
    elder = args.elder_name or rng.choice(elder_pool)
    village = args.village_name or rng.choice(VILLAGES)
    return StoryParams(child, elder, village)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generate_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
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
        raise SystemExit(asp_verify())
    if args.asp:
        try:
            import storyworlds.asp as asp
            models = asp.solve(asp_program(), models=1)
            print("1 valid myth pattern found." if models else "No valid myth pattern found.")
        except Exception as exc:
            print(f"ASP unavailable: {exc}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params_list = [
            StoryParams("Luna", "Grandmother Asha", "Moonfield", seed=0),
            StoryParams("Tavi", "Old Rowan", "Willow Hollow", seed=1),
            StoryParams("Mira", "Keeper Imani", "Red Clay Village", seed=2),
        ]
        samples = [generate(params) for params in params_list]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < max(0, args.n):
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
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
