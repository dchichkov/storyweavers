#!/usr/bin/env python3
"""A tall little tale of Luna, a puddle, and a warning she almost missed.

Luna wants to leap across the widest puddle in town. She must rouse her sleepy
friend Pip, strive across a slippery plank, and form an alliance with the
park keeper. Suspense grows as the puddle rises. The tale has a bad ending:
Luna reaches the far bank, but her treasured red boots are swallowed by the
muddy water. Even so, the ending leaves a concrete lesson behind.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass(frozen=True)
class Setting:
    id: str
    label: str
    detail: str
    water_level: int
    affords: set[str]


@dataclass(frozen=True)
class Activity:
    id: str
    verb: str
    gerund: str
    risk: str
    obstacle: str
    object_label: str


@dataclass(frozen=True)
class Companion:
    id: str
    label: str
    sleepy: bool
    skill: str


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Event:
    kind: str
    actor: str
    target: str
    text: str
    cause: str
    result: str


class World:
    def __init__(self, setting: Setting, activity: Activity, companion: Companion):
        self.setting = setting
        self.activity = activity
        self.companion = companion
        self.entities: dict[str, Entity] = {}
        self.history: list[Event] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.turn = 0

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def record(self, kind: str, actor: str, target: str, text: str,
               cause: str, result: str) -> None:
        self.history.append(Event(kind, actor, target, text, cause, result))
        self.say(text)

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "town_park": Setting(
        id="town_park",
        label="the town park",
        detail="The park's puddles shone like little silver lakes beneath the clouds.",
        water_level=3,
        affords={"puddle_jump"},
    ),
    "hill_park": Setting(
        id="hill_park",
        label="the hill park",
        detail="The hill park held a long puddle that curled around the path like a blue ribbon.",
        water_level=2,
        affords={"puddle_jump"},
    ),
    "garden": Setting(
        id="garden",
        label="the old garden",
        detail="The old garden was full of dripping leaves and puddles between the stones.",
        water_level=2,
        affords={"puddle_jump"},
    ),
}

ACTIVITIES = {
    "puddle_jump": Activity(
        id="puddle_jump",
        verb="jump across the biggest puddle",
        gerund="jumping across the biggest puddle",
        risk="slipping into deep mud",
        obstacle="a narrow plank",
        object_label="red boots",
    ),
}

COMPANIONS = {
    "pip": Companion("pip", "Pip the small dog", True, "sniffing out dry ground"),
    "mara": Companion("mara", "Mara the mouse", True, "spotting safe stones"),
    "tobin": Companion("tobin", "Tobin the tortoise", True, "remembering old paths"),
}

NAMES = ["Luna", "Nell", "Tara", "Milo", "Pia", "Owen"]
GENDERS = ["girl", "boy"]
TRAITS = ["bold", "curious", "stubborn", "cheerful"]
PARENTS = ["mother", "father"]

@dataclass
class StoryParams:
    place: str = "town_park"
    activity: str = "puddle_jump"
    companion: str = "pip"
    name: str = "Luna"
    gender: str = "girl"
    trait: str = "bold"
    parent: str = "mother"
    seed: Optional[int] = None


KNOWLEDGE = {
    "puddle": QAItem(
        "What is a puddle?",
        "A puddle is a small pool of water on the ground, often left after rain."
    ),
    "alliance": QAItem(
        "What is an alliance?",
        "An alliance is an agreement between helpers who join together to reach a goal."
    ),
    "suspense": QAItem(
        "Why can a story feel suspenseful?",
        "A story feels suspenseful when something important might happen and the reader must wait to learn what it will be."
    ),
    "boots": QAItem(
        "Why do boots get muddy?",
        "Boots get muddy when they step through wet dirt, because mud sticks to their soles and sides."
    ),
}


def valid_params(params: StoryParams) -> bool:
    return (
        params.place in SETTINGS
        and params.activity in ACTIVITIES
        and params.companion in COMPANIONS
        and params.gender in GENDERS
        and params.trait in TRAITS
        and params.parent in PARENTS
    )


def tell(params: StoryParams) -> World:
    if not valid_params(params):
        raise StoryError("The requested story choices are not valid.")
    setting = SETTINGS[params.place]
    activity = ACTIVITIES[params.activity]
    companion = COMPANIONS[params.companion]
    if activity.id not in setting.affords:
        raise StoryError("That place cannot support the requested activity.")

    world = World(setting, activity, companion)
    luna = world.add(Entity(params.name, "character", params.name))
    friend = world.add(Entity("friend", "animal", companion.label))
    parent = world.add(Entity("parent", "character", f"the {params.parent}"))
    boots = world.add(Entity("boots", "thing", activity.object_label))
    plank = world.add(Entity("plank", "thing", activity.obstacle))
    puddle = world.add(Entity("puddle", "thing", "the biggest puddle"))
    keeper = world.add(Entity("keeper", "character", "the park keeper"))

    luna.memes.update(hope=1, impatience=1 if params.trait == "stubborn" else 0)
    friend.memes["sleepiness"] = 1
    puddle.meters["depth"] = setting.water_level
    boots.meters["dry"] = 1
    world.facts.update(
        hero=luna, friend=friend, parent=parent, boots=boots, plank=plank,
        puddle=puddle, keeper=keeper, resolved=False, bad_ending=False,
        roused=False, alliance=False, strived=False,
    )

    world.record(
        "arrival", luna.id, puddle.id,
        f"{params.name} reached {setting.label} with {luna.memes.get('hope', 0):.0f} "
        f"bright hopes and {activity.object_label} shining on her feet. "
        f"{setting.detail} She wanted to {activity.verb}.",
        f"{params.name} found a tempting puddle and wanted an adventure.",
        f"{params.name} stood at the edge of the puddle.",
    )

    world.para()
    friend_word = "he" if companion.id in {"pip", "tobin"} else "she"
    world.record(
        "rouse", luna.id, friend.id,
        f'"Wake up, {companion.label}!" {params.name} called. The little friend stirred, '
        f'but {friend_word} was still sleepy. {params.name} shook a leaf gently and said, '
        f'"I need your sharp eyes." At last, the friend blinked awake and pointed toward '
        f'a narrow plank beside the water.',
        "The safe route was hard to see, and the sleepy companion had to be roused.",
        f"{companion.label} woke and revealed the plank.",
    )
    world.facts["roused"] = True
    friend.memes["sleepiness"] = 0
    luna.memes["trust"] = 1

    world.para()
    world.record(
        "suspense", friend.id, puddle.id,
        f'The two helpers formed an alliance with the park keeper. "Hold the rope tight," '
        f'said the keeper. "{params.name}, cross slowly." Luna put one foot on the plank. '
        f'The puddle rose against the stones. The plank creaked. One more step might carry '
        f'her over, but one wrong step could send her into {activity.risk}.',
        "The puddle was rising, so Luna needed both helpers and a careful plan.",
        "The alliance made a crossing plan, but the danger remained.",
    )
    world.facts["alliance"] = True
    keeper.memes["helpfulness"] = 1
    friend.memes["courage"] = 1

    world.para()
    world.record(
        "strive", luna.id, plank.id,
        f'"Slow and steady," {companion.label} called. Luna gripped the rope and began to '
        f'strive across the plank. She leaned left, then right. The water lapped higher. '
        f'"You can do it!" cried the keeper. Luna took the last long step and landed on the '
        f'far bank. But the plank rolled behind her, and both {activity.object_label} slid '
        f'back into the brown water.',
        "Luna had to cross the unstable plank before the rising puddle reached it.",
        f"Luna reached the far bank, but her {activity.object_label} fell into the puddle.",
    )
    world.facts["strived"] = True
    world.facts["bad_ending"] = True
    world.facts["resolved"] = True
    world.turn += 1
    boots.meters["dry"] = 0
    boots.meters["lost"] = 1
    luna.memes["disappointment"] = 1

    world.para()
    world.record(
        "ending", keeper.id, boots.id,
        f'The helpers pulled Luna to safety, but the muddy water swallowed the shining '
        f'{activity.object_label}. Luna looked at her wet socks and sighed. "Next time, '
        f'I will listen before I leap," she said. The alliance had saved Luna, even though '
        f'the boots were gone, and the puddle kept its tall brown secret.',
        "The crossing succeeded for Luna but failed for her treasured boots.",
        "Luna was safe, learned to listen, and lost the boots.",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a tall tale about {f['hero'].label} trying to {world.activity.verb} in {world.setting.label}.",
        f"Include a moment when {f['hero'].label} must rouse a sleepy helper, strive across danger, and form an alliance.",
        "Build suspense toward a bad ending in which the child reaches safety but loses a treasured object.",
    ]


def story_qa(world: World) -> list[QAItem]:
    questions = {
        "arrival": "Why did Luna go to the park?",
        "rouse": "How did Luna get her helper ready?",
        "suspense": "Why was the crossing dangerous?",
        "strive": "What happened when Luna crossed the plank?",
        "ending": "What was the bad ending, and what did Luna learn?",
    }
    return [
        QAItem(e.text and questions[e.kind], f"{e.cause} {e.result}")
        for e in world.history if e.kind in questions
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [KNOWLEDGE["puddle"], KNOWLEDGE["alliance"], KNOWLEDGE["suspense"], KNOWLEDGE["boots"]]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id}: meters={meters} memes={memes}")
    lines.append("--- events ---")
    for event in world.history:
        lines.append(f"  {event.kind}: {event.text}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("\n== Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
safe_crossing :- roused, alliance, strived.
bad_ending :- safe_crossing, boots_lost.
resolved :- bad_ending.
#show safe_crossing/0.
#show bad_ending/0.
#show resolved/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("roused"),
        asp.fact("alliance"),
        asp.fact("strived"),
        asp.fact("boots_lost"),
    ])


def asp_program() -> str:
    return asp_facts() + "\n" + ASP_RULES


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    atoms = {str(x) for x in model}
    needed = {"safe_crossing", "bad_ending", "resolved"}
    if not needed.issubset(atoms):
        print("MISMATCH: ASP did not derive the complete ending.")
        return 1
    sample = generate(StoryParams())
    world = sample.world
    assert world.facts["roused"]
    assert world.facts["alliance"]
    assert world.facts["strived"]
    assert world.facts["bad_ending"]
    assert world.facts["resolved"]
    assert "bad" not in sample.story.lower() or "bad ending" not in sample.story.lower()
    assert len(sample.story_qa) == 5
    print("OK: ASP/Python parity and story-state checks passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate Luna's suspenseful puddle tale.")
    parser.add_argument("--place", choices=sorted(SETTINGS))
    parser.add_argument("--activity", choices=sorted(ACTIVITIES))
    parser.add_argument("--companion", choices=sorted(COMPANIONS))
    parser.add_argument("--name")
    parser.add_argument("--gender", choices=GENDERS)
    parser.add_argument("--trait", choices=TRAITS)
    parser.add_argument("--parent", choices=PARENTS)
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
    return StoryParams(
        place=args.place or rng.choice(sorted(SETTINGS)),
        activity=args.activity or "puddle_jump",
        companion=args.companion or rng.choice(sorted(COMPANIONS)),
        name=args.name or rng.choice(NAMES),
        gender=args.gender or rng.choice(GENDERS),
        trait=args.trait or rng.choice(TRAITS),
        parent=args.parent or rng.choice(PARENTS),
        seed=args.seed,
    )


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print("\n" + format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.n < 1:
        raise SystemExit("-n must be at least 1")
    if args.verify:
        raise SystemExit(asp_verify())
    if args.show_asp:
        print(asp_program())
        return
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print("Derived ASP atoms:")
        for atom in model:
            print(f"  {atom}")
        return

    rng = random.Random(args.seed)
    samples: list[StorySample] = []
    if args.all:
        for place in sorted(SETTINGS):
            params = StoryParams(place=place, seed=args.seed)
            samples.append(generate(params))
    else:
        for index in range(args.n):
            params = resolve_params(args, random.Random(rng.randrange(2 ** 31)))
            params.seed = (args.seed + index) if args.seed is not None else None
            samples.append(generate(params))

    if args.json:
        payload = samples[0].to_dict() if len(samples) == 1 else [s.to_dict() for s in samples]
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### tale {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
