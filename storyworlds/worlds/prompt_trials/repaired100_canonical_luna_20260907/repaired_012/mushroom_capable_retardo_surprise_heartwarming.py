#!/usr/bin/env python3
from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Garden:
    name: str
    dampness: float = 0.0
    surprise: float = 0.0
    care: float = 0.0
    friendship: float = 0.0
    mushroom_found: bool = False
    surprise_revealed: bool = False
    facts: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    child_name: str
    helper_name: str
    garden_name: str
    seed: Optional[int] = None


NAMES = ["Luna", "Milo", "Nia", "Tavi", "Sora", "Pip", "Mara", "Noah"]
HELPERS = ["Bea", "Jun", "Ollie", "Rin", "Tess", "Ari"]
GARDENS = ["the Moon Garden", "the Rainy Patch", "the Little Greenhouse", "the Hill Garden"]

ARCS = [
    {
        "key": "hidden_cap",
        "premise": [
            "{child} loved visiting {garden}, where tiny leaves shone after the rain. Their gentle helper, {helper}, kept a basket ready for anything that needed care.",
            "Each morning, {child} and {helper} checked {garden} together. {child} was capable at noticing small changes, even when the garden looked ordinary.",
        ],
        "problem": [
            "One gray morning, a little mushroom cap had tipped beneath a fern. It was hidden, cold, and almost covered by wet leaves.",
            "A bright mushroom had appeared beside the path, but its cap was bent under a fallen twig. The tiny thing could not lift itself into the sunlight.",
        ],
        "dialogue": [
            "\"I can move the twig,\" said {child}. \"You are capable, but let us be gentle,\" answered {helper}. Their quiet talk helped them choose care instead of hurry.",
            "\"Should we pull it free?\" asked {child}. \"First, let us see what it needs,\" said {helper}. Listening changed their plan.",
        ],
        "turn": [
            "Then {child} noticed a soft spot in the soil. Beneath the mushroom was a second, smaller cap, a surprise growing beside its parent.",
            "{helper} lifted one leaf and gasped. A ring of tiny mushrooms hid underneath, making a little silver family around the bent cap.",
        ],
        "action": [
            "{child} used a small spoon to ease away the twig while {helper} held the leaves aside. They gave the mushrooms space, a little water, and a warm patch of morning light.",
            "Together they cleared only the leaves that pressed too closely. {child} placed a smooth pebble beside the mushrooms so no one would step on them.",
        ],
        "resolution": [
            "By afternoon, the mushroom cap had opened. The tiny mushrooms stood safely around it, and {child} felt proud that being capable meant knowing when to move slowly.",
            "The cap lifted like a small umbrella. {helper} smiled because {child} had protected not just one mushroom, but the hidden family beneath it.",
        ],
        "ending": [
            "The next morning, dew rested on the mushroom ring like a row of bright little bells.",
            "A breeze passed through {garden}, and the mushroom family leaned together without falling.",
        ],
        "problem_fact": "a fallen twig pressed a mushroom cap into the wet soil",
        "clue_fact": "a hidden ring of smaller mushrooms revealed that the cap needed gentle care",
        "action_fact": "they removed the twig carefully and protected the mushroom family",
        "outcome_fact": "the mushroom cap opened safely in the morning light",
    },
    {
        "key": "surprise_gift",
        "premise": [
            "{child} and {helper} cared for the quiet corners of {garden}. They carried a red scarf, a watering cup, and a promise to help anything small.",
            "In {garden}, {child} liked useful jobs. {helper} knew that {child} was capable, so together they mended paths and checked the plants after every rain.",
        ],
        "problem": [
            "Near the old bench, a mushroom had grown under a heavy leaf. Its cap was bright, but its stem bent toward the dark.",
            "A mushroom beside the bench looked lonely and pale. A gust had covered it with leaves just as it began to open.",
        ],
        "dialogue": [
            "\"I thought I was too late,\" whispered {child}. \"You noticed it, and that is a beginning,\" said {helper}. Their words gave {child} courage to try.",
            "\"Can we save it?\" asked {child}. \"We can make a safe place,\" replied {helper}. The answer turned worry into a plan.",
        ],
        "turn": [
            "When they moved the largest leaf, they found a tiny red button tucked beside the mushroom. It was a surprise left by the garden club for the person who found the hidden growth.",
            "Under the leaves was a small card with a painted star. The garden club had prepared a surprise thank-you for the careful helper who discovered the mushroom.",
        ],
        "action": [
            "{child} cleared the leaves, but left the mushroom rooted where it was. Then {helper} tied the red scarf around the bench so walkers would notice the little patch.",
            "They made a soft border from fallen pinecones. {child} placed the surprise button on the bench, then watered the soil without touching the mushroom.",
        ],
        "resolution": [
            "The mushroom rose toward the sun, and {child} understood that capable hands can be gentle hands. The surprise made both friends laugh.",
            "Soon the cap stood tall beside the bench. {child} had helped the mushroom and had also been thanked for caring before anyone asked.",
        ],
        "ending": [
            "The painted star on the card gleamed beside the mushroom whenever sunlight reached the bench.",
            "Visitors began pausing at the pinecone border, smiling at the mushroom and the small red button.",
        ],
        "problem_fact": "fallen leaves covered a bent mushroom near the old bench",
        "clue_fact": "a hidden thank-you card showed that the mushroom had been waiting for careful help",
        "action_fact": "they cleared the leaves and marked the mushroom's patch",
        "outcome_fact": "the mushroom stood tall and the caring helper received a surprise",
    },
    {
        "key": "retardo_loses_way",
        "premise": [
            "{child} was walking through {garden} with {helper} when they heard a soft rustle near the mushroom bed. Their friend Retardo had wandered away from the garden path.",
            "After a shower, {child} and {helper} went to check the mushrooms. They soon found Retardo looking worried beside a mossy stone.",
        ],
        "problem": [
            "Retardo had followed a line of mushroom caps and could not find the bright blue gate. Every path looked the same beneath the dripping leaves.",
            "The wet garden had changed its familiar colors. Retardo was safe, but lost, and the mushroom trail seemed to twist in circles.",
        ],
        "dialogue": [
            "\"I am not sure which way is home,\" said Retardo. \"We will look for clues together,\" {child} replied. That promise helped Retardo stop trembling.",
            "\"I tried to remember the path,\" said Retardo. \"You remembered the mushrooms; now we can use them,\" said {helper}. Their words made a new plan.",
        ],
        "turn": [
            "{child} noticed that every mushroom on the left side had a pale spot facing the gate. It was a tiny pattern Retardo had seen but not understood.",
            "{helper} found a line of dry seeds beneath the mushrooms. The seeds pointed away from the puddles and toward the blue gate.",
        ],
        "action": [
            "They followed the pale spots one at a time. Retardo walked between {child} and {helper}, growing steadier with every familiar mushroom.",
            "{child} gathered the seeds into a little arrow while {helper} called out the gate's color. Retardo followed the arrow and began to recognize the path.",
        ],
        "resolution": [
            "The blue gate appeared through the leaves. Retardo hugged both friends and said that the mushroom clues had helped turn being lost into finding a way.",
            "At the gate, Retardo smiled with relief. {child} had been capable not because they knew everything, but because they noticed and shared clues.",
        ],
        "ending": [
            "The three friends went home beneath a rainbow, while the mushrooms made a quiet trail behind them.",
            "At the gate, one mushroom cap held a bead of rain that reflected all three smiling faces.",
        ],
        "problem_fact": "Retardo became lost among the wet garden paths",
        "clue_fact": "mushroom markings and dry seeds pointed toward the blue gate",
        "action_fact": "the friends followed the small clues together",
        "outcome_fact": "Retardo found the gate and felt safe again",
    },
]


def _rng_for(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed)
    text = "|".join((params.child_name, params.helper_name, params.garden_name))
    return random.Random(int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big"))


class World:
    def __init__(self, garden: Garden) -> None:
        self.garden = garden
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]

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


def tell(params: StoryParams) -> World:
    garden = Garden(params.garden_name)
    world = World(garden)
    child = world.add(Entity(params.child_name, kind="character", type="child", label="capable child"))
    helper = world.add(Entity(params.helper_name, kind="character", type="helper", label="kind helper"))
    retardo = world.add(Entity("Retardo", kind="character", type="friend", label="garden friend"))
    mushroom = world.add(Entity("mushroom", type="mushroom", label="little mushroom"))

    rng = _rng_for(params)
    arc = ARCS[(params.seed if params.seed is not None else rng.randrange(len(ARCS))) % len(ARCS)]
    beats = ("premise", "problem", "dialogue", "turn", "action", "resolution", "ending")
    if params.seed is None:
        chosen = {beat: rng.choice(arc[beat]) for beat in beats}
    else:
        code = (params.seed // len(ARCS)) % (2 ** len(beats))
        chosen = {beat: arc[beat][(code >> i) % len(arc[beat])] for i, beat in enumerate(beats)}

    values = {
        "child": child.id,
        "helper": helper.id,
        "garden": garden.name,
    }
    for i, beat in enumerate(beats):
        if i:
            world.para()
        world.say(chosen[beat].format(**values))

    garden.dampness = 0.4
    garden.care = 1.0
    garden.friendship = 1.0
    garden.surprise = 1.0
    garden.mushroom_found = True
    garden.surprise_revealed = True
    child.meters["capability"] = 1.0
    child.memes["confidence"] = 1.0
    helper.memes["kindness"] = 1.0
    retardo.memes["safety"] = 1.0
    mushroom.meters["health"] = 1.0
    mushroom.memes["belonging"] = 1.0

    garden.facts = {
        "child": child,
        "helper": helper,
        "retardo": retardo,
        "mushroom": mushroom,
        "arc": arc,
        "problem": arc["problem_fact"],
        "clue": arc["clue_fact"],
        "action": arc["action_fact"],
        "outcome": arc["outcome_fact"],
    }
    return world


def generate_prompts(world: World) -> list[str]:
    f = world.garden.facts
    return [
        "Write a heartwarming story about a mushroom that needs gentle care.",
        f"Tell a child-friendly story in {world.garden.name} where {f['child'].id} is capable, helps {f['retardo'].id}, and discovers a surprise.",
        "Write a warm garden tale in which noticing a small clue changes what the characters do.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.garden.facts
    return [
        QAItem(
            question=f"Who cared for the mushroom in {world.garden.name}?",
            answer=f"{f['child'].id} and {f['helper'].id} cared for the mushroom together, using gentle actions instead of rushing.",
        ),
        QAItem(
            question=f"What problem happened in {world.garden.name}?",
            answer=f["problem"],
        ),
        QAItem(
            question="What surprising clue did the friends discover?",
            answer=f["clue"],
        ),
        QAItem(
            question="How did the story end?",
            answer=f"{f['outcome']} The friends felt warm and proud because their careful choice helped someone or something small.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mushroom?",
            answer="A mushroom is the visible part of a fungus. It often grows in damp places and can have a cap and a stem.",
        ),
        QAItem(
            question="What does capable mean?",
            answer="Capable means able to do something successfully, especially when a person learns, notices, and keeps trying.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that someone discovers or receives.",
        ),
        QAItem(
            question="Why should people be careful around wild mushrooms?",
            answer="People should observe wild mushrooms without eating or picking them unless a knowledgeable adult says they are safe.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {entity.id:10} ({entity.type:8}) {' '.join(bits)}")
    lines.append(f"  garden.mushroom_found={world.garden.mushroom_found}")
    lines.append(f"  garden.surprise_revealed={world.garden.surprise_revealed}")
    lines.append(f"  garden.care={world.garden.care}")
    lines.append(f"  garden.friendship={world.garden.friendship}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_story :- mushroom_present, capable_helper, retardo_safe, surprise_revealed.
mushroom_present.
capable_helper.
retardo_safe.
surprise_revealed.
#show valid_story/0.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("theme", "mushroom"),
            asp.fact("theme", "capable"),
            asp.fact("character", "retardo"),
            asp.fact("feature", "surprise"),
            asp.fact("style", "heartwarming"),
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
    if any(sym.name == "valid_story" for sym in model):
        sample = generate(StoryParams("Luna", "Bea", "the Moon Garden", seed=12))
        if not sample.story or "mushroom" not in sample.story.lower():
            print("MISMATCH: generated story failed the mushroom check.")
            return 1
        print("OK: ASP and Python recognize the heartwarming mushroom story.")
        return 0
    print("MISMATCH: ASP twin did not produce valid_story.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Heartwarming mushroom garden storyworld.")
    parser.add_argument("--child-name")
    parser.add_argument("--helper-name")
    parser.add_argument("--garden-name", choices=GARDENS)
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
    helper_pool = [name for name in HELPERS if name != child]
    helper = args.helper_name or rng.choice(helper_pool)
    garden = args.garden_name or rng.choice(GARDENS)
    return StoryParams(child, helper, garden)


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
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
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
        sys.exit(asp_verify())
    if args.asp:
        try:
            import storyworlds.asp as asp
            print(asp.one_model(asp_program()))
        except Exception as exc:
            print(f"ASP unavailable: {exc}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        params_list = [
            StoryParams("Luna", "Bea", "the Moon Garden", seed=0),
            StoryParams("Milo", "Jun", "the Rainy Patch", seed=1),
            StoryParams("Nia", "Ollie", "the Little Greenhouse", seed=2),
        ]
    else:
        params_list = []
        for index in range(max(0, args.n)):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            params_list.append(params)

    samples = [generate(params) for params in params_list]
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
