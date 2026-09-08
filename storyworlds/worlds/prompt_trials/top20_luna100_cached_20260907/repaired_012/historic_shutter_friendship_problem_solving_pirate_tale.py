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
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
)
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Harbor:
    name: str
    location: str = "a historic island harbor"
    shutter_open: bool = False
    tide_safe: bool = False
    friendship_strength: float = 0.0
    facts: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    captain_name: str
    mate_name: str
    ship_name: str
    harbor_name: str
    seed: Optional[int] = None


NAMES = ["Mara", "Nell", "Finn", "Pip", "Rory", "Tess", "Jory", "Bram"]
SHIP_NAMES = ["The Moon Finch", "The Brass Parrot", "The Kind Compass", "The Old Star"]
HARBOR_NAMES = ["Lantern Harbor", "Cannon Cove", "Sailor's Rest", "Blue Door Bay"]


ARCS = [
    {
        "key": "museum_shutter",
        "premise": [
            "{captain} sailed {ship} to {harbor}, where an old fort held a historic wooden shutter carved with a moon and a gull.",
            "At sunrise, pirate friends {captain} and {mate} reached {harbor} aboard {ship}. They had promised to open its historic lighthouse shutter before the harbor festival.",
        ],
        "problem": [
            "The heavy shutter was swollen with salt and would not move. Without it, the lighthouse could not show ships the safe channel.",
            "A storm had jammed the historic shutter shut. The harbor boats waited in dark water, and every hard pull only made the old wood creak.",
        ],
        "conflict": [
            "\"We should force it with a crowbar,\" said {captain}. \"That could break the historic shutter,\" warned {mate}. Their disagreement left the lighthouse dark.",
            "{captain} wanted to sail for help, but {mate} wanted to study the hinges. \"We are wasting time,\" said {captain}. \"We need the right idea,\" answered {mate}.",
        ],
        "turn": [
            "The friends paused beside the wall. {mate} noticed tiny shells packed around the lower hinge, while {captain} saw that the tide would soon lift the dock beside it.",
            "{captain} listened instead of pulling. {mate} found a narrow drain under the sill, and a trickle of warm rainwater softened the salt around one hinge.",
        ],
        "action": [
            "\"You found the trouble; I will bring the water,\" said {captain}. Together they poured warm kettle water over the hinge, brushed away the shells, and lifted with the tide.",
            "{mate} held the shutter steady while {captain} cleaned each hinge with a sail needle. Then they pushed together only when the rising tide buoyed the wood.",
        ],
        "resolution": [
            "The shutter swung open without a crack. Sunlight poured through the lighthouse, and the friends' careful plan guided the waiting boats into the safe channel.",
            "The old wood opened with a soft groan. {captain} thanked {mate} for noticing the hinge, and their friendship felt stronger than the heavy shutter.",
        ],
        "ending": [
            "That evening, the historic moon-and-gull carving glowed above the harbor while the two pirates shared tea on the lighthouse steps.",
            "The lighthouse beam swept across calm water, and the rescued shutter rested open like a wooden wing.",
        ],
        "problem_fact": "salt and shells had jammed the historic lighthouse shutter",
        "clue_fact": "careful observation revealed trapped shells and a rising tide that could help",
        "action_fact": "the friends cleaned the hinge and lifted the shutter with warm water and the tide",
        "outcome_fact": "the lighthouse opened its safe beam and the boats reached harbor",
    },
    {
        "key": "fort_window",
        "premise": [
            "{captain} and {mate} brought {ship} to {harbor} to visit a historic sea fort whose blue shutter protected an old signal room.",
            "Pirate friends {captain} and {mate} were carrying a festival flag to {harbor}. The flag belonged in a historic fort behind a tall blue shutter.",
        ],
        "problem": [
            "The shutter's rope had slipped behind a stone ledge. The signal room stayed closed, so the harbor could not raise its warning flag before the storm.",
            "A gull had tangled the shutter cord around a rusted bell. Pulling from below only tightened the knot, and dark clouds gathered over the fort.",
        ],
        "conflict": [
            "\"Climb the wall now,\" said {captain}. \"We need a safer plan,\" replied {mate}. Their friendship wobbled as the storm clouds thickened.",
            "{captain} wanted to cut the cord. {mate} feared damaging the historic bell beside it. Neither pirate moved until they stopped to hear one another.",
        ],
        "turn": [
            "{mate} pointed out that the bell rope moved whenever a wave struck the dock. {captain} realized the tide could loosen the knot if they timed their pull.",
            "They shared a quiet biscuit and examined the wall together. A loose tile showed a small passage leading behind the shutter cord.",
        ],
        "action": [
            "{captain} held the tile while {mate} guided the cord through the passage. On the third wave, they pulled together and freed the knot.",
            "\"You watch the bell; I will guide the rope,\" said {captain}. {mate} counted the waves, and the cord slid loose without harming the historic room.",
        ],
        "resolution": [
            "The blue shutter opened, and the festival flag rose before the storm arrived. The pirates solved the problem by trusting both courage and care.",
            "The signal room brightened, and the warning flag flew safely. {captain} and {mate} laughed because their friendship had made room for two good ideas.",
        ],
        "ending": [
            "Rain began after the flag was high, pattering on the blue shutter while the fort bell rang a grateful note.",
            "The historic fort stood bright against the clouds, its open window showing the harbor boats safe below.",
        ],
        "problem_fact": "a slipped cord had tangled behind the historic fort shutter",
        "clue_fact": "the tide and a loose tile revealed a safe way to reach the cord",
        "action_fact": "the friends guided and pulled the cord together at the right wave",
        "outcome_fact": "the shutter opened and the warning flag rose before the storm",
    },
    {
        "key": "captains_gallery",
        "premise": [
            "At {harbor}, {captain} and {mate} sailed {ship} to deliver a painted map to a historic captain's gallery.",
            "The crew of {ship} carried a precious map through {harbor}. Friends {captain} and {mate} hoped to place it behind the gallery's carved shutter.",
        ],
        "problem": [
            "The shutter would not close around the map's frame. If rain entered, the historic painting would be ruined.",
            "One side of the carved shutter sat lower than the other. The gallery keeper worried that wind would slam it into the precious map.",
        ],
        "conflict": [
            "\"Push the frame harder,\" said {captain}. \"The frame is not the problem,\" said {mate}. Their sharp words made the keeper step back.",
            "{captain} blamed the heavy map, while {mate} blamed the bent hinge. Their friendship felt strained because each pirate wanted to protect the painting.",
        ],
        "turn": [
            "Instead of pushing, {mate} traced the shutter's shadow. {captain} saw that one corner touched the floor before the other, revealing a pebble beneath the sill.",
            "They opened the shutter wide and looked beneath it. A tiny brass button had fallen into the hinge, stopping the wood from lining up.",
        ],
        "action": [
            "{captain} lifted the shutter while {mate} swept out the pebble. Then they lowered it gently, and the frame settled around the map.",
            "{mate} held a lantern, and {captain} used a thin knife to nudge out the brass button. Together they tested the shutter in the wind.",
        ],
        "resolution": [
            "The shutter closed snugly, protecting the historic map. {captain} apologized, and {mate} smiled as the keeper thanked them both.",
            "The wind pressed against the repaired shutter, but it stayed firm. The pirates solved the problem without harming the gallery or their friendship.",
        ],
        "ending": [
            "Through the shutter's small moon-shaped cutout, the map's blue sea shone safely in the evening light.",
            "The gallery keeper hung a friendship ribbon beside the historic map, while {ship} rocked quietly at the dock.",
        ],
        "problem_fact": "a pebble or brass button kept the historic gallery shutter from closing safely",
        "clue_fact": "looking at the shutter's alignment exposed the small object beneath its hinge",
        "action_fact": "the friends lifted the shutter and removed the object carefully",
        "outcome_fact": "the shutter closed securely and protected the historic map",
    },
]


class World:
    def __init__(self, harbor: Harbor) -> None:
        self.harbor = harbor
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


def _rng_for(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed)
    raw = "|".join(
        [params.captain_name, params.mate_name, params.ship_name, params.harbor_name]
    )
    seed = int.from_bytes(hashlib.sha256(raw.encode("utf-8")).digest()[:8], "big")
    return random.Random(seed)


def tell(params: StoryParams) -> World:
    if params.captain_name == params.mate_name:
        raise StoryError("The captain and mate must have different names.")
    if params.harbor_name not in HARBOR_NAMES:
        raise StoryError("Choose a harbor from the historic harbor registry.")

    harbor = Harbor(name=params.harbor_name)
    world = World(harbor)
    captain = world.add(
        Entity(
            id=params.captain_name,
            kind="character",
            type="captain",
            label="captain",
            meters={"energy": 4.0},
            memes={"trust": 0.5},
        )
    )
    mate = world.add(
        Entity(
            id=params.mate_name,
            kind="character",
            type="mate",
            label="first mate",
            meters={"energy": 4.0},
            memes={"trust": 0.5},
        )
    )
    shutter = world.add(
        Entity(
            id="historic_shutter",
            type="shutter",
            label="historic shutter",
            phrase="the historic shutter",
            meters={"stuck": 1.0, "opened": 0.0},
            memes={"memory": 1.0},
        )
    )
    ship = world.add(
        Entity(
            id=params.ship_name,
            type="ship",
            label="pirate ship",
            phrase=params.ship_name,
            meters={"distance": 0.0},
        )
    )

    rng = _rng_for(params)
    arc = ARCS[(params.seed if params.seed is not None else rng.randrange(len(ARCS))) % len(ARCS)]
    beats = ("premise", "problem", "conflict", "turn", "action", "resolution", "ending")
    if params.seed is None:
        chosen = {beat: rng.choice(arc[beat]) for beat in beats}
    else:
        code = (params.seed // len(ARCS)) % (2 ** len(beats))
        chosen = {
            beat: arc[beat][(code >> index) % len(arc[beat])]
            for index, beat in enumerate(beats)
        }

    values = {
        "captain": params.captain_name,
        "mate": params.mate_name,
        "ship": params.ship_name,
        "harbor": params.harbor_name,
    }
    rendered = {}
    for index, beat in enumerate(beats):
        if index:
            world.para()
        rendered[beat] = chosen[beat].format(**values)
        world.say(rendered[beat])

    shutter.meters["stuck"] = 0.0
    shutter.meters["opened"] = 1.0
    harbor.shutter_open = True
    harbor.tide_safe = True
    harbor.friendship_strength = 1.0
    captain.memes["trust"] = 1.0
    mate.memes["trust"] = 1.0

    harbor.facts = {
        "captain": captain,
        "mate": mate,
        "ship": ship,
        "shutter": shutter,
        "arc": arc,
        "rendered": rendered,
        "problem": arc["problem_fact"],
        "clue": arc["clue_fact"],
        "action": arc["action_fact"],
        "outcome": arc["outcome_fact"],
    }
    return world


def generate_prompts(world: World) -> list[str]:
    f = world.harbor.facts
    return [
        "Write a child-friendly pirate tale about a historic shutter that causes a problem.",
        f"Tell a Pirate Tale where {f['captain'].id} and {f['mate'].id} use friendship and problem solving to repair a shutter in {world.harbor.name}.",
        "Write a short adventure whose ending shows that two friends solved a practical problem together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.harbor.facts
    return [
        QAItem(
            question=f"Who worked together in {world.harbor.name}?",
            answer=f"{f['captain'].id}, the captain, and {f['mate'].id}, the mate, worked together as pirate friends.",
        ),
        QAItem(
            question="What problem did the historic shutter cause?",
            answer=f["rendered"]["problem"],
        ),
        QAItem(
            question="What clue helped the pirates solve the problem?",
            answer=f["rendered"]["turn"],
        ),
        QAItem(
            question="How did the friends solve the shutter problem?",
            answer=f"{f['rendered']['action']} {f['rendered']['resolution']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shutter?",
            answer="A shutter is a hinged cover that can close over a window or opening to protect it from light, wind, or rain.",
        ),
        QAItem(
            question="What does historic mean?",
            answer="Historic means important or connected to the past, often because people remember what happened there.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means noticing what is wrong, finding useful clues, and choosing careful actions that make things better.",
        ),
        QAItem(
            question="Why is friendship useful during a hard task?",
            answer="Friendship helps people listen to one another, share ideas, and keep helping when a task is difficult.",
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
        lines.append(f"  {entity.id:18} ({entity.type:10}) {' '.join(bits)}")
    lines.append(f"  harbor.shutter_open={world.harbor.shutter_open}")
    lines.append(f"  harbor.tide_safe={world.harbor.tide_safe}")
    lines.append(f"  harbor.friendship_strength={world.harbor.friendship_strength}")
    return "\n".join(lines)


ASP_RULES = r"""
has_theme(historic).
has_theme(shutter).
has_feature(friendship).
has_feature(problem_solving).
has_style(pirate_tale).
valid_story :- has_theme(historic), has_theme(shutter),
               has_feature(friendship), has_feature(problem_solving),
               has_style(pirate_tale).
#show valid_story/0.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("theme", "historic"),
            asp.fact("theme", "shutter"),
            asp.fact("feature", "friendship"),
            asp.fact("feature", "problem_solving"),
            asp.fact("style", "pirate_tale"),
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
        params = StoryParams("Mara", "Finn", "The Moon Finch", "Lantern Harbor", seed=17)
        sample = generate(params)
        if (
            "historic" in sample.story.lower()
            and "shutter" in sample.story.lower()
            and "friendship" in sample.story.lower()
        ):
            print("OK: ASP and Python agree on the historic shutter friendship story.")
            return 0
        print("MISMATCH: generated story omitted required narrative features.")
        return 1
    print("MISMATCH: ASP twin rejected the required story pattern.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Pirate tale world: a historic shutter, friendship, and problem solving."
    )
    parser.add_argument("--captain-name")
    parser.add_argument("--mate-name")
    parser.add_argument("--ship-name", choices=SHIP_NAMES)
    parser.add_argument("--harbor-name", choices=HARBOR_NAMES)
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
    captain = args.captain_name or rng.choice(NAMES)
    mate_choices = [name for name in NAMES if name != captain]
    mate = args.mate_name or rng.choice(mate_choices)
    ship = args.ship_name or rng.choice(SHIP_NAMES)
    harbor = args.harbor_name or rng.choice(HARBOR_NAMES)
    return StoryParams(
        captain_name=captain,
        mate_name=mate,
        ship_name=ship,
        harbor_name=harbor,
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
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
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
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        try:
            import storyworlds.asp as asp
            models = asp.solve(asp_program(), models=1)
            print("1 compatible pirate story pattern found." if models else "No compatible pattern found.")
        except Exception as exc:
            print(f"ASP unavailable: {exc}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Mara", "Finn", "The Moon Finch", "Lantern Harbor", seed=11),
            StoryParams("Nell", "Pip", "The Brass Parrot", "Cannon Cove", seed=29),
            StoryParams("Tess", "Bram", "The Kind Compass", "Blue Door Bay", seed=47),
        ]
        samples = [generate(params) for params in curated]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(args.n * 50, 50):
            seed = base_seed + index
            index += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if not samples:
        raise StoryError("No story variants could be generated.")

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
