#!/usr/bin/env python3
"""
A gentle ghost story about a lost piece of loot, a moth's molt, and a brave
inner voice that turns a spooky room into a place of care.
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
class StoryParams:
    setting: str
    seed: Optional[int] = None
    child_name: str = "Luna"
    helper_name: str = "Nana"
    ghost_name: str = "Moss"
    loot_kind: str = "silver button"
    molt_kind: str = "moth shell"
    style: str = "ghost story"


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def inc_meter(self, key: str, amount: float = 1.0) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def inc_meme(self, key: str, amount: float = 1.0) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass
class World:
    setting: str
    child: Entity
    helper: Entity
    ghost: Entity
    loot: Entity
    molt: Entity
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        for entity in [self.child, self.helper, self.ghost, self.loot, self.molt]:
            meters = {k: v for k, v in entity.meters.items() if v}
            memes = {k: v for k, v in entity.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={meters}")
            if memes:
                bits.append(f"memes={memes}")
            lines.append(f"  {entity.id:10} ({entity.kind:8}) {' '.join(bits)}")
        lines.append(f"  setting: {self.setting}")
        return "\n".join(lines)


SETTINGS = {
    "attic": "the old attic",
    "boathouse": "the moonlit boathouse",
    "lighthouse": "the quiet lighthouse",
    "garden": "the sleeping garden",
}

NAMES = ["Luna", "Milo", "Iris", "Theo", "Nell"]
HELPERS = ["Nana", "Grandpa", "Aunt Bea", "Uncle Sol"]
GHOSTS = ["Moss", "Wisp", "Pip", "Elder Shade"]
LOOT = ["silver button", "brass key", "blue marble", "tiny crown"]
MOLTS = ["moth shell", "beetle shell", "empty cicada skin", "dragonfly husk"]

OPENINGS = {
    "attic": [
        "{child} climbed into the old attic while rain tapped the roof.",
        "On a windy evening, {child} searched the old attic for a missing storybook.",
    ],
    "boathouse": [
        "{child} stepped into the moonlit boathouse after a rope knocked against the wall.",
        "The moon shone through the boathouse window when {child} heard a soft little sob.",
    ],
    "lighthouse": [
        "{child} visited the quiet lighthouse as fog curled around its door.",
        "At dusk, {child} climbed the quiet lighthouse stairs with a small lantern.",
    ],
    "garden": [
        "{child} crossed the sleeping garden when the roses began to whisper.",
        "After twilight, {child} carried a basket through the sleeping garden.",
    ],
}

CLUES = {
    "silver button": (
        "A pale gleam slid beneath an old trunk, followed by three tiny taps.",
        "The ghost had lost a silver button from its moon-blue coat.",
    ),
    "brass key": (
        "Something bright chimed beside the dusty floorboards.",
        "The ghost had dropped a brass key that opened its little memory box.",
    ),
    "blue marble": (
        "A round blue light rolled in a slow circle and stopped at {child}'s shoe.",
        "The ghost had treasured the blue marble since it was a living child.",
    ),
    "tiny crown": (
        "A small golden shape trembled on a shelf beneath the cobwebs.",
        "The ghost had misplaced a tiny crown from an old paper play.",
    ),
}

MOLT_LINES = {
    "moth shell": "A moth had slipped out of its old shell and left the light skin behind.",
    "beetle shell": "A beetle had grown and left its empty shell beside the wall.",
    "empty cicada skin": "A cicada had changed and left its papery old skin among the leaves.",
    "dragonfly husk": "A dragonfly had flown away from the husk of its younger self.",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A gentle ghost story about loot, molt, and a brave inner voice."
    )
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--ghost", choices=GHOSTS)
    parser.add_argument("--loot", choices=LOOT)
    parser.add_argument("--molt", choices=MOLTS)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def _validate_params(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError("Choose a setting such as the attic, boathouse, lighthouse, or garden.")
    if params.loot_kind not in LOOT:
        raise StoryError("The loot must be one of the small story treasures.")
    if params.molt_kind not in MOLTS:
        raise StoryError("The molt must be a harmless empty insect shell.")
    if params.child_name == params.ghost_name:
        raise StoryError("The child and ghost need different names.")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    params = StoryParams(
        setting=args.setting or rng.choice(list(SETTINGS)),
        seed=args.seed,
        child_name=args.name or rng.choice(NAMES),
        helper_name=args.helper or rng.choice(HELPERS),
        ghost_name=args.ghost or rng.choice(GHOSTS),
        loot_kind=args.loot or rng.choice(LOOT),
        molt_kind=args.molt or rng.choice(MOLTS),
    )
    _validate_params(params)
    return params


def make_world(params: StoryParams) -> World:
    child = Entity(params.child_name, "character", params.child_name, "child")
    helper = Entity(params.helper_name, "character", params.helper_name, "helper")
    ghost = Entity(params.ghost_name, "spirit", params.ghost_name, "friendly ghost")
    loot = Entity("loot", "treasure", params.loot_kind, "lost keepsake")
    molt = Entity("molt", "nature", params.molt_kind, "empty insect skin")
    return World(SETTINGS[params.setting], child, helper, ghost, loot, molt)


def _build_story(world: World, params: StoryParams) -> None:
    rng = random.Random((params.seed or 0) + 9176)
    child = world.child
    helper = world.helper
    ghost = world.ghost
    loot = world.loot
    molt = world.molt

    opening = rng.choice(OPENINGS[params.setting]).format(child=child.label)
    clue, reveal = CLUES[loot.label]
    clue = clue.format(child=child.label)

    child.memes["worry"] = 1.0
    child.memes["courage"] = 0.0
    ghost.memes["loneliness"] = 1.0
    loot.meters["lost"] = 1.0
    molt.meters["empty"] = 1.0

    world.say(opening)
    world.say(
        f"On a cushion lay a strange little {molt.label}, and beside it floated a faint blue glow. "
        f"Then a voice sighed, “Have you seen my {loot.label}?”"
    )
    world.say(
        f'{child.label} froze. “Are you a ghost?” {child.label} asked. '
        f'{ghost.label} answered, “Only a lost one.”'
    )
    world.say(clue)

    world.para()
    world.say(
        f"Inside {child.label}'s thoughts, a small frightened voice whispered, "
        f"“Run to {helper.label}. This place is full of shadows.”"
    )
    world.say(
        f"Another thought answered, “A lost ghost may need help. I can be careful and still be kind.”"
    )
    child.inc_meme("courage", 1.0)
    child.inc_meter("careful_steps", 1.0)
    ghost.inc_meme("trust", 1.0)
    world.say(
        f'{child.label} lifted the lantern. “I will help you look,” {child.label} said. '
        f'{ghost.label} brightened. “Thank you. I remember the moon on it.”'
    )

    world.para()
    world.say(
        f"Together they searched under a trunk, behind a flowerpot, and near the old window. "
        f"The {molt.label} fluttered when the night breeze passed."
    )
    world.say(MOLT_LINES[molt.label])
    world.say(
        f"{child.label} noticed a thin silver trail leading toward a cracked wooden chest."
    )
    loot.meters["lost"] = 0.0
    loot.meters["found"] = 1.0
    world.say(
        f"Inside the chest was the {loot.label}. {reveal} "
        f"{child.label} placed it gently in {ghost.label}'s misty hand."
    )

    world.para()
    ghost.memes["loneliness"] = 0.0
    ghost.memes["peace"] = 1.0
    child.memes["worry"] = 0.25
    world.say(
        f'"It is warm again," said {ghost.label}. "{helper.label} will be glad you found it," '
        f'{child.label} replied.'
    )
    world.say(
        f"{ghost.label} smiled and faded into a soft patch of moonlight. "
        f"The {molt.label} remained on the sill, proof that leaving an old shape behind can be part of growing."
    )
    world.say(
        f"When {helper.label} found {child.label}, the lantern was steady, the {loot.label} was safe, "
        f"and the shadows looked ordinary. {child.label} still felt a flutter of fear, "
        f"but the brave thought now knew what to say: “Kindness can light a haunted room.”"
    )

    world.facts.update(
        opening=opening,
        clue=clue,
        reveal=reveal,
        molt_explanation=MOLT_LINES[molt.label],
        found=True,
        brave=True,
    )


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a gentle ghost story in {world.setting} where {world.child.label} searches for lost loot.",
        f"Include a {world.molt.label}, a friendly ghost, and a child's inner monologue that changes fear into courage.",
        f"Tell how {world.child.label} returns a {world.loot.label} and leaves the haunted place peaceful.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question=f"What did {world.child.label} find?",
            answer=f"{world.child.label} found the lost {world.loot.label} inside a cracked wooden chest.",
        ),
        QAItem(
            question=f"How did {world.child.label}'s inner thoughts change?",
            answer=(
                f"At first {world.child.label}'s thoughts urged a retreat, but then a brave inner voice "
                "decided to help the lonely ghost carefully."
            ),
        ),
        QAItem(
            question="What was the molt?",
            answer=f"The {world.molt.label} was an empty insect skin left behind after the insect changed and grew.",
        ),
        QAItem(
            question=f"Why did the ghost become peaceful?",
            answer=f"The ghost became peaceful because {world.child.label} returned the lost {world.loot.label} and listened kindly.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is loot?",
            answer="Loot is a found or gathered treasure, such as a small keepsake or prize.",
        ),
        QAItem(
            question="What is a molt?",
            answer="A molt is the old outer covering an animal leaves behind as it grows.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the stream of thoughts a character has inside their mind.",
        ),
        QAItem(
            question="Can a ghost story be gentle?",
            answer="Yes. A ghost story can use mystery while ending with kindness, understanding, and peace.",
        ),
    ]


ASP_RULES = r"""
lost_loot(L) :- loot(L), not found(L).
brave_child(C) :- child(C), hears(C, G), returns_loot(C, G).
peaceful_ghost(G) :- ghost(G), returned(G), not lonely(G).
good_story(C, G, L) :- brave_child(C), peaceful_ghost(G), loot(L).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines = []
    for setting in SETTINGS:
        lines.append(asp.fact("setting", setting))
    for name in NAMES:
        lines.append(asp.fact("child", name))
    for name in GHOSTS:
        lines.append(asp.fact("ghost", name))
    for item in LOOT:
        lines.append(asp.fact("loot", item.replace(" ", "_")))
    for item in MOLTS:
        lines.append(asp.fact("molt", item.replace(" ", "_")))
    return "\n".join(lines)


def asp_program(show: str = "#show good_story/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def _python_reasonable(params: StoryParams) -> bool:
    return (
        params.setting in SETTINGS
        and params.loot_kind in LOOT
        and params.molt_kind in MOLTS
        and params.child_name != params.ghost_name
    )


def asp_verify() -> int:
    params = StoryParams(setting="attic")
    if not _python_reasonable(params):
        print("MISMATCH: Python reasonableness gate failed.")
        return 1
    try:
        import storyworlds.asp as asp

        program = asp_program()
        models = asp.solve(program, models=1)
        if not models:
            print("MISMATCH: ASP produced no model.")
            return 1
    except ImportError:
        print("OK: Python reasonableness gate passed; clingo is unavailable.")
        return 0
    sample = generate(params)
    if not sample.story or not sample.story_qa:
        print("MISMATCH: generated story check failed.")
        return 1
    print("OK: Python and ASP checks passed.")
    return 0


def generate(params: StoryParams) -> StorySample:
    _validate_params(params)
    world = make_world(params)
    _build_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(sample.world.trace())
    if qa:
        print("\n== Generation prompts ==")
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"{index}. {prompt}")
        print("\n== Story questions ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== World questions ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


CURATED = [
    StoryParams(setting="attic", child_name="Luna", helper_name="Nana", ghost_name="Moss", loot_kind="silver button", molt_kind="moth shell"),
    StoryParams(setting="boathouse", child_name="Milo", helper_name="Grandpa", ghost_name="Wisp", loot_kind="brass key", molt_kind="beetle shell"),
    StoryParams(setting="lighthouse", child_name="Iris", helper_name="Aunt Bea", ghost_name="Pip", loot_kind="blue marble", molt_kind="empty cicada skin"),
    StoryParams(setting="garden", child_name="Theo", helper_name="Uncle Sol", ghost_name="Elder Shade", loot_kind="tiny crown", molt_kind="dragonfly husk"),
]


def build_all_samples() -> list[StorySample]:
    return [generate(params) for params in CURATED]


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

            models = asp.solve(asp_program(), models=1)
            print(f"ASP models found: {len(models)}")
        except ImportError:
            print("ASP mode requires the optional clingo package.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = build_all_samples()
    else:
        samples = []
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

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
