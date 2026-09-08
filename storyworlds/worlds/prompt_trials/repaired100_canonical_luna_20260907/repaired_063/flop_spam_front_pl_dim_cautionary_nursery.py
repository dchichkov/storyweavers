#!/usr/bin/env python3
"""
A standalone cautionary nursery-rhyme storyworld about a floppy spam sign
that dims the front porch lamp until careful friends repair it.
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
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

STORYWORLDS_ROOT = Path(__file__).resolve().parents[2]
if str(STORYWORLDS_ROOT) not in sys.path:
    sys.path.insert(0, str(STORYWORLDS_ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    type: str
    label: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str = "the front porch"


@dataclass
class StoryParams:
    name: str
    helper_name: str
    warning_mode: int = 0
    discovery_mode: int = 0
    repair_mode: int = 0
    ending_mode: int = 0
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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


SETTING = Setting()
NAMES = ["Luna", "Milo", "Tansy", "Pip", "Nell", "Bram"]
HELPERS = ["Aunt Bea", "Grandpa Jo", "Mina", "Uncle Sol"]

WARNING_LINES = [
    "Do not poke the box, do not tug at the wire; a dark little spark can leap higher and higher.",
    "Do not chase the dimness or kick at the frame; ask for a grown helper and name what you name.",
    "Do not plug in a stranger or pull at a cord; safe hands and calm questions are better than hoard.",
    "When a lamp starts to falter and flicker and flop, step back from the doorway and carefully stop.",
]

DISCOVERY_LINES = [
    "Luna looked from the porch to the flag and saw spam: a heap of silly paper messages stuffed against the vent.",
    "Milo noticed that the spam was not food at all, but unwanted paper cards packed where cool air should pass.",
    "The friends read the front-pl-dim label on their little safety chart: front porch lamp dimming, not a game to fix alone.",
    "A feather, a bent card, and a warm dusty smell told them that the spam had gathered beneath the loose shade.",
]

REPAIR_LINES = [
    "Aunt Bea switched off the lamp at the safe indoor control, then used a dry brush to clear the cards.",
    "The helper fetched a new shade and tightened the porch sign while Luna held the basket far away.",
    "Together they kept the porch empty while the grown helper checked the cord, cleaned the vent, and replaced the bent label.",
    "No child reached into the fixture; the helper made the repair, and the friends sorted the harmless paper for recycling.",
]

ENDINGS = [
    "The lamp shone bright, the porch grew warm, and Luna learned that a quick flop is no reason to make a risky hop.",
    "The spam went away, the sign stood straight, and every child waited for help before touching a strange thing.",
    "The front porch glowed like a moonlit rhyme, because careful words had saved the evening in time.",
    "At bedtime the repaired lamp winked once, and the safety chart rested neatly beside the broom.",
]

LESSONS = [
    "If a thing is strange, step back and explain; safe help can turn a worry plain.",
    "Never poke, pull, or plug in haste; ask a trusted grown-up and leave danger its space.",
    "A cautionary rhyme may sound small, but careful choices protect us all.",
]

ASP_RULES = r"""
lamp_dim :- front_pl_dim, spam_near_vent.
needs_helper :- lamp_dim, strange_wire.
safe_plan :- needs_helper, power_off, adult_checks.
good_story :- safe_plan, repaired.
#show good_story/0.
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Cautionary nursery rhyme about a floppy spam sign and a dim porch lamp."
    )
    parser.add_argument("--name")
    parser.add_argument("--helper-name")
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
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        helper_name=args.helper_name or rng.choice(HELPERS),
        warning_mode=rng.randrange(len(WARNING_LINES)),
        discovery_mode=rng.randrange(len(DISCOVERY_LINES)),
        repair_mode=rng.randrange(len(REPAIR_LINES)),
        ending_mode=rng.randrange(len(ENDINGS)),
    )


def _build_world(params: StoryParams) -> World:
    world = World(SETTING)
    child = world.add(Entity("child", "child", params.name, memes={"curiosity": 1}))
    helper = world.add(Entity("helper", "adult", params.helper_name, memes={"calm": 1}))
    lamp = world.add(
        Entity(
            "lamp",
            "lamp",
            "the front porch lamp",
            meters={"brightness": 0.35, "safe": 0},
        )
    )
    spam = world.add(
        Entity(
            "spam",
            "paper",
            "the spam",
            meters={"amount": 1, "near_vent": 1},
        )
    )
    sign = world.add(
        Entity(
            "sign",
            "sign",
            "the floppy front-pl-dim sign",
            meters={"upright": 0},
        )
    )
    wire = world.add(
        Entity(
            "wire",
            "wire",
            "a strange loose wire",
            meters={"exposed": 1},
        )
    )
    world.facts.update(
        child=child,
        helper=helper,
        lamp=lamp,
        spam=spam,
        sign=sign,
        wire=wire,
        params=params,
        repaired=False,
        helper_called=False,
    )
    return world


def tell(world: World) -> None:
    facts = world.facts
    params: StoryParams = facts["params"]  # type: ignore[assignment]
    child: Entity = facts["child"]  # type: ignore[assignment]
    helper: Entity = facts["helper"]  # type: ignore[assignment]
    lamp: Entity = facts["lamp"]  # type: ignore[assignment]
    sign: Entity = facts["sign"]  # type: ignore[assignment]
    wire: Entity = facts["wire"]  # type: ignore[assignment]
    spam: Entity = facts["spam"]  # type: ignore[assignment]

    world.say(
        f"{child.label} went flop-flop-flop to {world.setting.place}, "
        f"where {sign.label} wobbled in the breeze."
    )
    world.say(
        f"The lamp was dim, and a loose wire peeked out below it. "
        f"Then {child.label} saw a pile of spam pressed against the lamp's vent."
    )

    world.para()
    world.say(WARNING_LINES[params.warning_mode % len(WARNING_LINES)])
    world.say(
        f'"I will not touch it," said {child.label}. '
        f'"{helper.label}, please come and look."'
    )
    world.say(
        f'"Good choice," said {helper.label}. '
        f'"A dim lamp and a loose wire need an adult, not a curious tug."'
    )
    facts["helper_called"] = True

    world.para()
    world.say(DISCOVERY_LINES[params.discovery_mode % len(DISCOVERY_LINES)])
    world.say(
        f"The word front-pl-dim meant that the front porch lamp was dimming; "
        f"it was a reminder, not a command to fiddle."
    )
    world.say(
        f"{child.label} stayed behind the step while {helper.label} "
        f"switched off the power from inside the house."
    )

    world.para()
    world.say(REPAIR_LINES[params.repair_mode % len(REPAIR_LINES)])
    world.say(
        f"The spam was removed, the floppy sign was secured, and the loose wire "
        f"was covered safely."
    )
    lamp.meters["brightness"] = 1
    lamp.meters["safe"] = 1
    spam.meters["amount"] = 0
    sign.meters["upright"] = 1
    wire.meters["exposed"] = 0
    facts["repaired"] = True

    world.para()
    world.say(ENDINGS[params.ending_mode % len(ENDINGS)])
    world.say(LESSONS[params.ending_mode % len(LESSONS)])


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a cautionary nursery rhyme using the words flop, spam, and front-pl-dim.",
        f"Tell a safe child-facing story in which {world.facts['child'].label} notices a dim front porch lamp.",
        "Include a brief dialogue exchange, an adult helper, a practical repair, and a clear safety lesson.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    params: StoryParams = facts["params"]  # type: ignore[assignment]
    child: Entity = facts["child"]  # type: ignore[assignment]
    helper: Entity = facts["helper"]  # type: ignore[assignment]
    return [
        QAItem(
            "What was floppy on the front porch?",
            "The floppy front-pl-dim sign wobbled in the breeze.",
        ),
        QAItem(
            "What was spam doing?",
            "The spam was packed against the lamp's vent.",
        ),
        QAItem(
            f"Why did {child.label} call {helper.label}?",
            "The porch lamp was dim and a loose wire was visible, so an adult needed to inspect it.",
        ),
        QAItem(
            "What did the helper do first?",
            "The helper switched off the power from inside the house before making the repair.",
        ),
        QAItem(
            "What changed at the end?",
            "The spam was removed, the sign was secured, the wire was covered, and the lamp shone brightly again.",
        ),
        QAItem(
            "What was the cautionary lesson?",
            "Children should not poke, pull, or plug in strange electrical things; they should step back and ask a trusted adult.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is spam?",
            "Spam is unwanted material or messages; in this story it is unwanted paper gathered near the lamp.",
        ),
        QAItem(
            "What should a child do near a loose wire?",
            "A child should stay away, avoid touching it, and tell a trusted adult.",
        ),
        QAItem(
            "What does dim mean?",
            "Dim means giving off only a small amount of light.",
        ),
        QAItem(
            "Why can nursery rhymes teach caution?",
            "Their rhythm and repeated words can make a safety reminder easy to remember.",
        ),
    ]


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        lines.append(
            f"  {entity.id:7} ({entity.type:7}) meters={meters} memes={memes}"
        )
    lines.append(f"  repaired={world.facts['repaired']}")
    lines.append(f"  helper_called={world.facts['helper_called']}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("front_pl_dim"),
            asp.fact("spam_near_vent"),
            asp.fact("strange_wire"),
            asp.fact("power_off"),
            asp.fact("adult_checks"),
            asp.fact("repaired"),
        ]
    )


def asp_program(show: str = "#show good_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    good = any(symbol.name == "good_story" for symbol in model)
    if good:
        print("OK: ASP twin agrees that the cautious repair is complete.")
        return 0
    print("MISMATCH: ASP twin did not derive good_story.")
    return 1


def _validate(params: StoryParams) -> None:
    if not params.name.strip():
        raise StoryError("name must not be empty")
    if not params.helper_name.strip():
        raise StoryError("helper_name must not be empty")
    for field_name in ("warning_mode", "discovery_mode", "repair_mode", "ending_mode"):
        if getattr(params, field_name) < 0:
            raise StoryError(f"{field_name} cannot be negative")


def generate(params: StoryParams) -> StorySample:
    _validate(params)
    world = _build_world(params)
    tell(world)
    if not world.facts["helper_called"] or not world.facts["repaired"]:
        raise StoryError("the story must include adult help and a completed safe repair")
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
    StoryParams("Luna", "Aunt Bea", 0, 0, 0, 0),
    StoryParams("Milo", "Grandpa Jo", 1, 1, 1, 1),
    StoryParams("Tansy", "Mina", 2, 2, 2, 2),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        code = asp_verify()
        if code:
            sys.exit(code)
        for params in CURATED:
            sample = generate(params)
            if not sample.story or "front-pl-dim" not in sample.story:
                print("MISMATCH: generated story lost required vocabulary.")
                sys.exit(1)
        print("OK: generated stories pass the Python checks.")
        return

    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        print("good_story" if any(symbol.name == "good_story" for symbol in model) else "(none)")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempts = max(args.n * 20, 20)
        for offset in range(attempts):
            if len(samples) >= args.n:
                break
            seed = base_seed + offset
            rng = random.Random(seed)
            params = resolve_params(args, rng)
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
        if args.all:
            header = f"### {sample.params.name} and the floppy porch sign"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
