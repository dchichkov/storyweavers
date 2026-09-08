#!/usr/bin/env python3
"""A gentle bedtime storyworld about a tenement, a gigolo, magic, and friendship."""

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
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("warmth", "worry", "magic", "friendship", "hope", "sleepiness"):
            self.meters.setdefault(key, 0.0)
            self.memes.setdefault(key, 0.0)


@dataclass
class Setting:
    id: str
    label: str
    detail: str


@dataclass(frozen=True)
class Gig:
    id: str
    title: str
    task: str
    trouble: str
    clue: str
    plan: str
    result: str
    ending: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.trace.append(text)


SETTINGS = {
    "moonlit_tenement": Setting(
        "moonlit_tenement",
        "the moonlit tenement",
        "a tall brick tenement where warm windows glowed above a quiet courtyard",
    ),
    "canal_tenement": Setting(
        "canal_tenement",
        "the canal-side tenement",
        "an old canal-side tenement whose stairwell smelled of soap and rain",
    ),
    "garden_tenement": Setting(
        "garden_tenement",
        "the garden tenement",
        "a friendly tenement wrapped around a tiny rooftop garden",
    ),
}

GIGS = {
    "lantern_lullaby": Gig(
        "lantern_lullaby",
        "the Lantern Lullaby gig",
        "play a soft tune so the youngest tenants can fall asleep",
        "the courtyard lanterns kept blinking out before the first verse",
        "a blue moth landed on the darkest lantern and its wings shone like a tiny map",
        "follow the moths, polish the lantern glass, and place a pinch of moon-salt inside each lamp",
        "the lanterns glowed steadily while the melody floated through every open window",
        "the last light became a silver star reflected in a sleepy child's window",
    ),
    "rainy_roof": Gig(
        "rainy_roof",
        "the Rainy Roof gig",
        "play above the rain so neighbors could share a peaceful bedtime",
        "raindrops drummed on the roof and covered every quiet note",
        "a loose copper gutter sang one clear note whenever the wind turned",
        "tie a ribbon to the gutter, copy its rhythm, and let the rain become part of the song",
        "the roof made a gentle accompaniment instead of a noisy blanket",
        "rain whispered on the tiles long after the friends had packed away the instruments",
    ),
    "stairwell_stars": Gig(
        "stairwell_stars",
        "the Stairwell Stars gig",
        "guide a shy child home with music after the stairwell lights went dark",
        "the unlit stairs made every landing look like a different place",
        "dusty footprints formed a trail toward the top-floor window",
        "hang tiny star charms along the trail and play one warm note at each landing",
        "the child followed the shining path and found the right door",
        "the star charms dimmed to firefly sparks as everyone settled into bed",
    ),
    "courtyard_dream": Gig(
        "courtyard_dream",
        "the Courtyard Dream gig",
        "send a kind dream to a neighbor who had been awake with worry",
        "the dream bell made only a dull clunk when the gig began",
        "a friend noticed a thread of gold caught inside the bell's little clapper",
        "untangle the thread together and ring the bell only after the worried neighbor was ready",
        "a warm dream-song rose gently above the courtyard",
        "the bell rested under the moon while a peaceful smile appeared upstairs",
    ),
}

NAMES = ["Luna", "Mara", "Nia", "Tessa", "Pip", "Theo", "Milo", "Sam"]
FRIEND_NAMES = ["Rafi", "Mina", "Jo", "Nell", "Ari", "Bea"]

OPENINGS = [
    "At bedtime, the tenement seemed to breathe with the slow hush of sleeping rooms.",
    "When the moon climbed above the tenement, one small gig still waited in the courtyard.",
    "The old tenement had many windows, and each window held a different kind of dream.",
    "Just before bedtime, a quiet mystery shimmered beneath the tenement stairs.",
]

REFLECTIONS = [
    "Magic was kindest when friendship gave it a careful purpose.",
    "A soft heart and a patient plan could make even a little gig feel grand.",
    "The friends learned that wonder grows brighter when nobody has to carry it alone.",
    "Their magic did not chase away every worry; it helped the worry find a quieter shape.",
]


@dataclass
class StoryParams:
    setting: str = "moonlit_tenement"
    gig: str = "lantern_lullaby"
    name: str = "Luna"
    friend_name: str = "Rafi"
    opening: int = 0
    reflection: int = 0
    seed: Optional[int] = None
    samples: list = field(default_factory=list)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a gentle bedtime story about a magical tenement gig."
    )
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--gig", choices=GIGS)
    parser.add_argument("--name")
    parser.add_argument("--friend-name")
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
    name = args.name or rng.choice(NAMES)
    possible = [item for item in FRIEND_NAMES if item != name]
    friend_name = args.friend_name or rng.choice(possible)
    return StoryParams(
        setting=args.setting or rng.choice(list(SETTINGS)),
        gig=args.gig or rng.choice(list(GIGS)),
        name=name,
        friend_name=friend_name,
        opening=rng.randrange(len(OPENINGS)),
        reflection=rng.randrange(len(REFLECTIONS)),
    )


def _get_setting(key: str) -> Setting:
    if key not in SETTINGS:
        raise StoryError(f"Unknown tenement setting: {key}")
    return SETTINGS[key]


def _get_gig(key: str) -> Gig:
    if key not in GIGS:
        raise StoryError(f"Unknown gig: {key}")
    return GIGS[key]


def tell(params: StoryParams) -> World:
    setting = _get_setting(params.setting)
    gig = _get_gig(params.gig)
    if not params.name.strip() or not params.friend_name.strip():
        raise StoryError("Both the gigolo's name and the friend's name must be non-empty.")
    if params.name.strip().lower() == params.friend_name.strip().lower():
        raise StoryError("The gigolo and friend need different names.")

    world = World(setting)
    gigolo = world.add(Entity(params.name, "gigolo", params.name))
    friend = world.add(Entity(params.friend_name, "friend", params.friend_name))
    world.facts.update(gigolo=gigolo, friend=friend, gig=gig)

    opening = OPENINGS[params.opening % len(OPENINGS)]
    reflection = REFLECTIONS[params.reflection % len(REFLECTIONS)]

    world.say(
        f"{opening} {setting.detail.capitalize()}. {gigolo.label} was a gentle gigolo "
        f"who played bedtime gigs for the neighbors, and {friend.label} was "
        f"{gigolo.label}'s dearest friend."
    )
    gigolo.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    gigolo.memes["worry"] += 1
    world.say(
        f"Tonight they had promised to perform {gig.title}. The gig had one special task: "
        f"{gig.task}. But {gig.trouble.capitalize()}."
    )
    world.say(
        f'"I do not know how to begin," whispered {gigolo.label}. '
        f'"Then we will begin by noticing," said {friend.label}.'
    )

    gigolo.memes["magic"] += 1
    friend.memes["magic"] += 1
    gigolo.memes["worry"] = max(0.0, gigolo.memes["worry"] - 0.5)
    world.say(f"Together, they looked closely. {gig.clue.capitalize()}.")
    world.say(
        f'"The magic is giving us a hint," said {friend.label}. '
        f'"And friendship can help us use it wisely," replied {gigolo.label}.'
    )
    world.say(f"They followed their clue: {gig.plan.capitalize()}.")

    gigolo.memes["hope"] += 1
    friend.memes["hope"] += 1
    gigolo.memes["worry"] = 0.0
    world.facts["resolved"] = True
    world.facts["magic_used_with_care"] = True
    world.say(
        f"When the gig began, {gigolo.label} played slowly and {friend.label} stayed close. "
        f"{gig.result.capitalize()}."
    )
    world.say(
        f"The neighbors listened from their doors and windows. {gigolo.label} smiled, "
        f"because the gig had not needed loud magic. It had needed a brave question, "
        f"a faithful friend, and time to listen."
    )
    world.say(f"As a final kindness, {gig.ending.capitalize()} {reflection}")
    world.say(
        f"Then the tenement grew quiet again, and {gigolo.label} and {friend.label} "
        "went to sleep knowing that tomorrow might hold another small wonder."
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    gig = world.facts["gig"]
    gigolo = world.facts["gigolo"]
    friend = world.facts["friend"]
    prompts = [
        "Write a child-facing bedtime story in which a gigolo performs a gentle gig in a tenement.",
        f"Show how {gigolo.label} and {friend.label} use Magic and Friendship to solve a bedtime problem.",
        f"Keep the story warm and concrete, using this clue: {gig.clue}",
    ]
    story_questions = [
        QAItem(
            f"What kind of gigolo was {gigolo.label}?",
            f"{gigolo.label} was a gentle gigolo who played bedtime gigs for the neighbors in the tenement.",
        ),
        QAItem(
            f"What problem threatened {gig.title}?",
            f"The problem was that {gig.trouble}.",
        ),
        QAItem(
            f"How did {gigolo.label} and {friend.label} discover what to do?",
            f"They noticed that {gig.clue}, then used that clue to make a careful plan together.",
        ),
        QAItem(
            "How did Friendship change the outcome?",
            f"Friendship helped {gigolo.label} pause, listen, and work beside {friend.label} instead of facing the trouble alone. Their gig then ended safely and peacefully.",
        ),
        QAItem(
            "What happened at the end?",
            gig.ending.capitalize(),
        ),
    ]
    world_questions = [
        QAItem(
            "What is a tenement?",
            "A tenement is a building divided into many homes, often with neighbors living close together.",
        ),
        QAItem(
            "What is a gig?",
            "A gig is a performance or job arranged for a particular time and place.",
        ),
        QAItem(
            "What does friendship mean?",
            "Friendship means caring about someone, listening to them, and helping them through difficult moments.",
        ),
        QAItem(
            "What is magic in a bedtime story?",
            "Magic is a wonder-making force in a story. Good magic is often guided by kindness, care, and wise choices.",
        ),
    ]
    return StorySample(
        params=params,
        story=world_render(world),
        prompts=prompts,
        story_qa=story_questions,
        world_qa=world_questions,
        world=world,
    )


def world_render(world: World) -> str:
    return " ".join(world.trace)


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"  setting: {world.setting.label}")
    for entity in world.entities.values():
        active = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.label} ({entity.kind}): memes={active}")
    lines.append(f"  resolved: {world.facts.get('resolved', False)}")
    lines.append(f"  magic_used_with_care: {world.facts.get('magic_used_with_care', False)}")
    return "\n".join(lines)


ASP_RULES = r"""
friendship_supports(H, F) :- gigolo(H), friend(F), works_with(F, H).
magic_guided(H) :- gigolo(H), magic(H), friendship_supports(H, F).
peaceful_gig(H) :- magic_guided(H), gig(H), listens(H).
bedtime_ready(H) :- peaceful_gig(H), tenement(H).
#show friendship_supports/2.
#show magic_guided/1.
#show peaceful_gig/1.
#show bedtime_ready/1.
"""


def asp_facts() -> str:
    from asp import fact
    return "\n".join(
        [
            fact("gigolo", "luna"),
            fact("friend", "rafi"),
            fact("works_with", "rafi", "luna"),
            fact("magic", "luna"),
            fact("gig", "luna"),
            fact("listens", "luna"),
            fact("tenement", "luna"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(
        asp_program(
            "#show friendship_supports/2. "
            "#show magic_guided/1. "
            "#show peaceful_gig/1. "
            "#show bedtime_ready/1."
        )
    )
    found = {str(atom) for atom in model}
    expected = {
        "friendship_supports(rafi,luna)",
        "magic_guided(luna)",
        "peaceful_gig(luna)",
        "bedtime_ready(luna)",
    }
    if found == expected:
        sample = generate(StoryParams())
        if all(word in sample.story.lower() for word in ("tenement", "gigolo", "gig")):
            print("OK: ASP twin matches the Python story gate.")
            return 0
    print("MISMATCH between ASP and Python.")
    print("  asp:", sorted(found))
    print("  expected:", sorted(expected))
    return 1


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

    if args.verify:
        raise SystemExit(asp_verify())
    if args.show_asp:
        print(asp_program(
            "#show friendship_supports/2. "
            "#show magic_guided/1. "
            "#show peaceful_gig/1. "
            "#show bedtime_ready/1."
        ))
        return
    if args.asp:
        import asp
        model = asp.one_model(
            asp_program(
                "#show friendship_supports/2. "
                "#show magic_guided/1. "
                "#show peaceful_gig/1. "
                "#show bedtime_ready/1."
            )
        )
        print("\n".join(sorted(str(atom) for atom in model)))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        params_list = [
            StoryParams(setting=setting, gig=gig, name="Luna", friend_name="Rafi")
            for setting in SETTINGS
            for gig in GIGS
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
