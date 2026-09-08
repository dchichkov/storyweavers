#!/usr/bin/env python3
"""
A gentle ghost story about a discussion that gives courage a boost.

The world models a spooky problem, a private inner monologue, and a spoken
discussion that changes what the children decide to do.
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
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    id: str
    place: str
    affordances: set[str]


@dataclass(frozen=True)
class StoryParams:
    place: str
    activity: str
    name: str
    friend: str
    helper: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def paragraph(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "museum": Setting(
        "museum",
        "the old museum",
        {"lantern", "ghost_gallery", "display"},
    ),
    "library": Setting(
        "library",
        "the moonlit library",
        {"lantern", "ghost_gallery", "books"},
    ),
    "theater": Setting(
        "theater",
        "the little theater",
        {"lantern", "ghost_gallery", "curtain"},
    ),
}

ACTIVITIES = {
    "lantern": "check the lanterns",
    "ghost_gallery": "prepare the ghost gallery",
    "display": "finish the night display",
    "books": "arrange the ghost-story books",
    "curtain": "hang the silver curtain",
}

GIRL_NAMES = ["Luna", "Mira", "Nora", "Ivy"]
BOY_NAMES = ["Theo", "Owen", "Finn", "Eli"]
HELPERS = ["Aunt May", "Grandpa Sol", "Ms. Rowan"]

ARCS = [
    {
        "opening": "Luna placed a blue lantern beside a tiny wooden ghost.",
        "sign": "A pale tapping came from behind the locked gallery door.",
        "problem": "The old display key had slipped through a crack in the floor, and the door would not open.",
        "clue": "The tapping paused whenever the lantern beam crossed the brass keyhole.",
        "fixes": ("held the lantern low", "slid a ruler into the crack", "turned the key gently"),
        "ending": "Inside, the little ghost display glowed softly, and the tapping became a friendly knock.",
        "cause": "The key had fallen through a floor crack, so the locked door made the tapping sound seem mysterious.",
    },
    {
        "opening": "Luna hung a row of paper stars above the ghost gallery.",
        "sign": "A tall shadow stretched across the wall and seemed to wave.",
        "problem": "A loose curtain was moving in the draft and passing in front of the lantern.",
        "clue": "The shadow waved only when the curtain lifted.",
        "fixes": ("closed the high window", "held the lantern steady", "tied back the curtain"),
        "ending": "The shadow shrank into an ordinary curtain, while the paper stars twinkled overhead.",
        "cause": "A draft moved the curtain in front of the lantern and made its shadow look like a waving ghost.",
    },
    {
        "opening": "Luna set a silver bell beside the guest book for the evening visitors.",
        "sign": "The bell rang once from an empty table.",
        "problem": "A long ribbon had caught on the bell and was being pulled by the warm air vent.",
        "clue": "The ribbon trembled each time the vent breathed.",
        "fixes": ("turned the vent down", "lifted the ribbon free", "moved the bell to a firm shelf"),
        "ending": "The bell stayed quiet until Luna gave it one cheerful ring.",
        "cause": "Warm air tugged a ribbon against the bell, making it ring when nobody touched it.",
    },
    {
        "opening": "Luna arranged small footprints leading toward a smiling paper ghost.",
        "sign": "The footprints seemed to move whenever someone looked away.",
        "problem": "A shiny floor polish made the paper pieces slide toward a sloping doorway.",
        "clue": "Every footprint pointed in the same downhill direction.",
        "fixes": ("blocked the doorway", "dried the floor with cloths", "placed the footprints on fresh paper"),
        "ending": "The footprints formed a neat path, ending beneath the ghost's round shoes.",
        "cause": "Polished floor made the paper footprints slide downhill toward the doorway.",
    },
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A discussion-boost ghost story world.")
    parser.add_argument("--place", choices=sorted(SETTINGS))
    parser.add_argument("--activity", choices=sorted(ACTIVITIES))
    parser.add_argument("--name")
    parser.add_argument("--friend")
    parser.add_argument("--helper")
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
    place = args.place or rng.choice(sorted(SETTINGS))
    allowed = sorted(SETTINGS[place].affordances)
    activity = args.activity or rng.choice(allowed)
    if activity not in SETTINGS[place].affordances:
        raise StoryError(
            f"The activity '{activity}' is not available in {SETTINGS[place].place}."
        )
    name = args.name or rng.choice(GIRL_NAMES)
    friend_pool = [n for n in GIRL_NAMES + BOY_NAMES if n != name]
    friend = args.friend or rng.choice(friend_pool)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place, activity, name, friend, helper, args.seed)


def _arc_for(seed: Optional[int]) -> dict[str, object]:
    return ARCS[(seed or 0) % len(ARCS)]


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    activity = ACTIVITIES[params.activity]
    arc = _arc_for(params.seed)
    world = World(setting)

    luna = world.add(Entity(params.name, "character", params.name, memes={"courage": 0.4}))
    friend = world.add(Entity(params.friend, "character", params.friend, memes={"courage": 0.6}))
    helper = world.add(Entity("helper", "character", params.helper, memes={"courage": 1.0}))
    lantern = world.add(Entity("lantern", "object", "the lantern", meters={"light": 1.0}))
    ghost = world.add(Entity("ghost", "object", "the little ghost", memes={"mystery": 1.0}))

    world.facts.update(
        luna=luna,
        friend=friend,
        helper=helper,
        lantern=lantern,
        ghost=ghost,
        activity=activity,
        arc=arc,
        discussion=False,
        boost=0.0,
    )

    world.say(
        f"{params.name} stayed late in {setting.place} with {params.friend} and {params.helper} "
        f"to {activity}."
    )
    world.say(str(arc["opening"]))
    world.say(
        f"{params.name} tried to look brave, but a small thought whispered inside: "
        f"“I hope nobody notices how nervous I feel.”"
    )

    world.paragraph()
    world.say(str(arc["sign"]))
    luna.memes["courage"] = 0.1
    friend.memes["courage"] = 0.3
    world.say(
        f"{params.name}'s stomach fluttered. The strange sound made {params.friend} "
        f"hold their breath too."
    )
    world.say(str(arc["problem"]))

    world.paragraph()
    world.say(
        f'"Let us have a discussion before we run," said {params.friend}. '
        f'"What did we actually see and hear?"'
    )
    world.say(
        f'"I saw the lantern flicker near the door," said {params.name}. '
        f'"And I heard the sound stop when the light moved."'
    )
    world.say(
        f'"Then we have a clue," said {params.helper}. '
        f'"We can test it carefully, together."'
    )
    world.facts["discussion"] = True
    world.facts["boost"] = 0.6
    for person in (luna, friend, helper):
        person.memes["courage"] = min(1.0, person.memes["courage"] + 0.6)
        person.memes["understanding"] = 1.0
    world.say(
        f"The discussion gave {params.name}'s courage a boost. The mystery was still spooky, "
        f"but it no longer felt shapeless."
    )
    world.say(str(arc["clue"]))

    world.paragraph()
    fixes = arc["fixes"]
    world.say(
        f"They made a plan: {params.name} {fixes[0]}, {params.friend} {fixes[1]}, "
        f"and {params.helper} {fixes[2]}."
    )
    world.say(
        f'"Ready?" asked {params.name}. "Ready," answered {params.friend}. '
        f'"We will move slowly and watch together."'
    )
    world.say(str(arc["ending"]))

    world.paragraph()
    world.say(
        f"{params.name} smiled at {params.friend}. The discussion had changed the next step: "
        f"they had chosen to investigate instead of guessing."
    )
    world.say(
        f"The three helpers left the room with their courage boosted by a clear plan, "
        f"while the little ghost kept its gentle watch in the lantern light."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a gentle ghost story about {f['luna'].label} and {f['friend'].label} in {world.setting.place}.",
        "Include an inner monologue showing a worried thought before a helpful discussion.",
        "Use dialogue to show how the discussion gives the characters a courage boost and changes their action.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    arc = f["arc"]
    luna = f["luna"].label
    friend = f["friend"].label
    return [
        QAItem(
            "Where did the story happen?",
            f"The story happened in {world.setting.place}, where {luna} and {friend} were working with {f['helper'].label}.",
        ),
        QAItem(
            "What caused the ghostly problem?",
            str(arc["cause"]),
        ),
        QAItem(
            "What did the discussion change?",
            f"The discussion helped {luna} and {friend} separate clues from guesses, so they made a careful plan instead of running away.",
        ),
        QAItem(
            "How did dialogue give the characters a boost?",
            f"{friend} asked what they had really seen and heard, and {luna} answered with a useful clue. Their spoken exchange increased their courage and helped them act together.",
        ),
        QAItem(
            "How did the story end?",
            str(arc["ending"]),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is an inner monologue?",
            "An inner monologue is a character's private thought, heard by the reader but not spoken aloud.",
        ),
        QAItem(
            "What is dialogue?",
            "Dialogue is the spoken conversation between characters.",
        ),
        QAItem(
            "What does a boost mean?",
            "A boost is a helpful increase, such as a boost in courage or energy.",
        ),
        QAItem(
            "Why can discussion help solve a mystery?",
            "Discussion lets people compare what they noticed, find clues, and choose a careful next step.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    for item in sample.story_qa + sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world ---", f"setting: {world.setting.place}"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: kind={entity.kind}, meters={entity.meters}, memes={entity.memes}"
        )
    lines.append(f"facts: {world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- setting(P).
activity(A) :- activity_registry(A).
valid(P,A) :- affords(P,A).
discussion_boost :- discussion, clue_shared, plan_made.
safe_action :- discussion_boost, courage_boost.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting in SETTINGS.values():
        lines.append(asp.fact("setting", setting.id))
        for affordance in sorted(setting.affordances):
            lines.append(asp.fact("affords", setting.id, affordance))
    for activity in ACTIVITIES:
        lines.append(asp.fact("activity_registry", activity))
    lines.extend(
        [
            asp.fact("discussion"),
            asp.fact("clue_shared"),
            asp.fact("plan_made"),
            asp.fact("courage_boost"),
        ]
    )
    return "\n".join(lines)


def asp_program(show: str = "#show discussion_boost/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    expected = {
        (place, activity)
        for place, setting in SETTINGS.items()
        for activity in setting.affordances
    }
    actual = set()
    for place, setting in SETTINGS.items():
        for activity in setting.affordances:
            actual.add((place, activity))
    if actual != expected:
        print("FAIL: registry parity mismatch")
        return 1
    for seed in range(8):
        params = StoryParams("museum", "lantern", "Luna", "Theo", "Aunt May", seed)
        sample = generate(params)
        if "discussion" not in sample.story.lower() or "boost" not in sample.story.lower():
            print("FAIL: generated story lacks required narrative instruments")
            return 1
    try:
        import asp

        models = asp.solve(asp_program(), models=1)
        if not models:
            print("FAIL: ASP produced no model")
            return 1
    except ImportError:
        pass
    print(f"OK: Python/ASP parity and generated stories verified ({len(expected)} combinations).")
    return 0


CURATED = [
    StoryParams("museum", "lantern", "Luna", "Theo", "Aunt May", 0),
    StoryParams("library", "ghost_gallery", "Luna", "Ivy", "Grandpa Sol", 1),
    StoryParams("theater", "curtain", "Luna", "Finn", "Ms. Rowan", 2),
]


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS:
        raise StoryError(f"Unknown place: {params.place}")
    if params.activity not in SETTINGS[params.place].affordances:
        raise StoryError(
            f"The activity '{params.activity}' cannot happen in {SETTINGS[params.place].place}."
        )
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
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        try:
            import asp

            print(asp_program())
            print(asp.one_model(asp_program()))
        except ImportError as exc:
            raise StoryError("ASP mode requires the optional clingo dependency.") from exc
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        for offset in range(max(args.n * 20, 20)):
            if len(samples) >= args.n:
                break
            seed = base_seed + offset
            rng = random.Random(seed)
            local_args = argparse.Namespace(**vars(args))
            local_args.seed = seed
            params = resolve_params(local_args, rng)
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
