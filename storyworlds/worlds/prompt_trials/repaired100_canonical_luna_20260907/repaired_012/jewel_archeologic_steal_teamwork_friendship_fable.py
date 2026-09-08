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
    kind: str
    type: str
    label: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Vault:
    name: str
    jewel_name: str
    jewel_value: float = 10.0
    danger: float = 0.0
    recovered: bool = False
    facts: dict[str, object] = field(default_factory=dict)


@dataclass
class StoryParams:
    fox_name: str
    magpie_name: str
    jewel_name: str
    temple_name: str
    seed: Optional[int] = None


NAMES = ["Luna", "Milo", "Nia", "Pip", "Tara", "Oren", "Faye", "Bram"]
JEWELS = ["the Moon Jewel", "the Star Ruby", "the Green Opal", "the Sunstone"]
TEMPLES = ["the Old Hill Temple", "the Fern-Covered Shrine", "the Valley Ruins", "the Whispering Arch"]


class World:
    def __init__(self, vault: Vault) -> None:
        self.vault = vault
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


ARCS = [
    {
        "key": "false_floor",
        "premise": "At sunrise, {fox} the fox and {magpie} the magpie explored {temple}, an old archeologic ruin where a lost jewel was said to rest.",
        "problem": "They found the jewel beneath a stone floor, but a greedy jackal tried to steal it before the friends could lift it safely.",
        "conflict": "\"I can carry it alone,\" said {fox}. \"Then you may drop it alone,\" replied {magpie}, and their quarrel made the loose floor tremble.",
        "turn": "A tiny lizard showed them that the floor stones had different dust marks. The friends realized the ruin's safe path could be read instead of guessed.",
        "action": "{magpie} watched the dust while {fox} moved the stones one at a time. Together they opened a path and placed the jewel in a clay basket.",
        "resolution": "The jackal lunged, but the friends pulled the basket through the safe path and blocked the passage with the marked stones. They chose teamwork over pride.",
        "ending": "They returned the jewel to the village museum, where the Moon Jewel shone beside a small lizard-shaped carving.",
        "problem_fact": "a jackal tried to steal the jewel from the ruin",
        "clue_fact": "dust marks revealed the safe path across the loose floor",
        "action_fact": "the friends moved the marked stones together and carried the jewel safely",
        "outcome_fact": "the jewel reached the village museum instead of the thief",
    },
    {
        "key": "echo_chamber",
        "premise": "{fox} and {magpie} entered {temple} to study an archeologic chamber painted with animals and stars.",
        "problem": "Inside, they discovered a jewel in a nest of reeds, while a sly monkey crept behind them to steal it.",
        "conflict": "\"Hide the jewel,\" whispered {fox}. \"Tell the truth and guard it together,\" said {magpie}. Their friendship felt thin as the monkey's shadow stretched across the wall.",
        "turn": "When {magpie} tapped a clay drum, the chamber answered with an echo from the far wall. The echo revealed a second doorway and a way out for both friends.",
        "action": "{fox} carried the jewel while {magpie} beat a steady rhythm. The echoes confused the monkey, and the friends slipped through the doorway side by side.",
        "resolution": "Outside, they agreed that neither friend should face danger alone. They gave the jewel to the careful village keeper.",
        "ending": "The old chamber echoed with their laughter, and the jewel glimmered safely beneath the keeper's kind hands.",
        "problem_fact": "a monkey followed them into the chamber to steal the jewel",
        "clue_fact": "a clay drum echo revealed a hidden doorway",
        "action_fact": "one friend carried the jewel while the other used the echo to confuse the thief",
        "outcome_fact": "the friends escaped together and protected the jewel",
    },
    {
        "key": "river_guardian",
        "premise": "Beside {temple}, {fox} and {magpie} studied an archeologic bridge built by people long ago.",
        "problem": "The bridge led to a jewel shrine, but a crow swooped down to steal the jewel and dropped it toward the river.",
        "conflict": "\"Chase the crow!\" cried {fox}. \"Save the jewel's landing place first,\" said {magpie}. Their disagreement cost precious time.",
        "turn": "They noticed old rope grooves carved into the bridge stones. The grooves showed where ancient helpers had once lowered a catching net.",
        "action": "{fox} held the rope while {magpie} tied a net from the bridge rail. Working together, they caught the jewel before it touched the water.",
        "resolution": "The crow flew away empty-clawed. The friends placed the jewel in the shrine and thanked one another for listening.",
        "ending": "The river carried their smiles downstream while the jewel flashed like a small sunrise in its ancient home.",
        "problem_fact": "a crow tried to steal the jewel and dropped it toward the river",
        "clue_fact": "old rope grooves showed where a catching net belonged",
        "action_fact": "the friends lowered a net together and caught the falling jewel",
        "outcome_fact": "the jewel was returned to its shrine",
    },
]


def _rng(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed)
    raw = "|".join([params.fox_name, params.magpie_name, params.jewel_name, params.temple_name])
    return random.Random(int.from_bytes(hashlib.sha256(raw.encode()).digest()[:8], "big"))


def tell(params: StoryParams) -> World:
    rng = _rng(params)
    arc = ARCS[(params.seed if params.seed is not None else rng.randrange(len(ARCS))) % len(ARCS)]
    fox = Entity(params.fox_name, "character", "fox", "a fox", meters={"care": 2.0}, memes={"friendship": 1.0})
    magpie = Entity(params.magpie_name, "character", "magpie", "a magpie", meters={"care": 2.0}, memes={"friendship": 1.0})
    jewel = Entity("jewel", "thing", "jewel", params.jewel_name, meters={"safety": 0.0}, memes={"trust": 0.0})
    vault = Vault(params.temple_name, params.jewel_name)
    world = World(vault)
    world.add(fox)
    world.add(magpie)
    world.add(jewel)

    fields = {
        "fox": params.fox_name,
        "magpie": params.magpie_name,
        "jewel": params.jewel_name,
        "temple": params.temple_name,
    }
    beats = {}
    for key in ("premise", "problem", "conflict", "turn", "action", "resolution", "ending"):
        beats[key] = arc[key].format(**fields)
        if key != "premise":
            world.para()
        world.say(beats[key])

    jewel.meters["safety"] = 1.0
    jewel.memes["trust"] = 1.0
    fox.memes["friendship"] = 2.0
    magpie.memes["friendship"] = 2.0
    vault.recovered = True
    vault.facts = {
        "arc": arc["key"],
        "problem": arc["problem_fact"],
        "clue": arc["clue_fact"],
        "action": arc["action_fact"],
        "outcome": arc["outcome_fact"],
        "problem_event": beats["problem"],
        "turn_event": beats["turn"],
        "action_event": beats["action"],
        "resolution_event": beats["resolution"],
        "fox": fox,
        "magpie": magpie,
        "jewel": jewel,
    }
    return world


def generate_prompts(world: World) -> list[str]:
    f = world.vault.facts
    return [
        "Write a child-friendly fable about an archeologic jewel that someone tries to steal.",
        f"Tell a fable in which {f['fox'].id} and {f['magpie'].id} use teamwork and friendship to protect {f['jewel'].label}.",
        "Write a short fable whose lesson is that trusted friends solve dangers better together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.vault.facts
    fox = f["fox"].id
    magpie = f["magpie"].id
    return [
        QAItem("Who explored the old archeologic place?", f"{fox} the fox and {magpie} the magpie explored it together."),
        QAItem("What danger threatened the jewel?", f["problem_event"]),
        QAItem("What clue helped the friends?", f["turn_event"]),
        QAItem("How did teamwork protect the jewel?", f"{f['action_event']} {f['resolution_event']}"),
        QAItem("What is the fable's lesson?", "Friendship grows when friends listen, share work, and protect one another instead of acting alone."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is archeology?", "Archeology is the study of objects and places left by people long ago."),
        QAItem("What is a jewel?", "A jewel is a beautiful, valuable stone that may be polished and kept safe."),
        QAItem("What does teamwork mean?", "Teamwork means people or animals sharing jobs and helping one another reach a goal."),
        QAItem("Why is stealing harmful?", "Stealing takes something that belongs to someone else and can break trust between friends."),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(f"  {entity.id}: type={entity.type} meters={entity.meters} memes={entity.memes}")
    lines.append(f"  vault={world.vault.name}")
    lines.append(f"  jewel_recovered={world.vault.recovered}")
    lines.append(f"  jewel_value={world.vault.jewel_value}")
    return "\n".join(lines)


ASP_RULES = r"""
has_feature(teamwork).
has_feature(friendship).
has_theme(jewel).
has_theme(archeologic).
has_theme(steal).
valid_story :- has_feature(teamwork), has_feature(friendship),
               has_theme(jewel), has_theme(archeologic), has_theme(steal).
#show valid_story/0.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("has_feature", "teamwork"),
            asp.fact("has_feature", "friendship"),
            asp.fact("has_theme", "jewel"),
            asp.fact("has_theme", "archeologic"),
            asp.fact("has_theme", "steal"),
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
        sample = generate(StoryParams("Luna", "Milo", JEWELS[0], TEMPLES[0], seed=7))
        required = ("jewel", "archeologic", "steal")
        if all(word in sample.story.lower() for word in required):
            print("OK: ASP and Python recognize the jewel teamwork fable.")
            return 0
    print("MISMATCH: ASP/Python parity failed.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fable world about an archeologic jewel, theft, teamwork, and friendship.")
    parser.add_argument("--fox-name")
    parser.add_argument("--magpie-name")
    parser.add_argument("--jewel-name", choices=JEWELS)
    parser.add_argument("--temple-name", choices=TEMPLES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    fox = args.fox_name or rng.choice(NAMES)
    magpie = args.magpie_name or rng.choice([name for name in NAMES if name != fox])
    return StoryParams(
        fox_name=fox,
        magpie_name=magpie,
        jewel_name=args.jewel_name or rng.choice(JEWELS),
        temple_name=args.temple_name or rng.choice(TEMPLES),
    )


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


def emit(sample: StorySample, *, trace: bool, qa: bool, header: str = "") -> None:
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
        print("1 compatible fable pattern: jewel + archeologic + steal + teamwork + friendship")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params_list = [
            StoryParams("Luna", "Milo", JEWELS[0], TEMPLES[0], seed=0),
            StoryParams("Nia", "Pip", JEWELS[1], TEMPLES[1], seed=1),
            StoryParams("Tara", "Oren", JEWELS[2], TEMPLES[2], seed=2),
        ]
        samples = [generate(params) for params in params_list]
    else:
        seen: set[str] = set()
        for index in range(max(args.n, 0)):
            seed = base_seed + index
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

    if args.json:
        payload = samples[0].to_dict() if len(samples) == 1 else [sample.to_dict() for sample in samples]
        print(json.dumps(payload, indent=2, ensure_ascii=False))
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
