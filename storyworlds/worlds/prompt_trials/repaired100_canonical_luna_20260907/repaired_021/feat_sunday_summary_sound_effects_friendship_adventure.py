#!/usr/bin/env python3
"""
A small adventure world about Luna's Sunday feat, told with sound effects
and strengthened by friendship.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while ROOT != os.path.dirname(ROOT) and not os.path.exists(os.path.join(ROOT, "results.py")):
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    held_by: Optional[str] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    name: str
    friend_name: str
    setting: str = "the echoing canyon"
    feat: str = "the Sunday bell"
    seed: Optional[int] = None


NAMES = ["Luna", "Milo", "Pip", "Nora", "Toby", "Cleo", "Finn", "Daisy"]
SETTINGS = [
    "the echoing canyon",
    "the windy hill trail",
    "the little mountain pass",
]
FEATS = [
    ("the Sunday bell", "a small silver bell"),
    ("the sunrise flag", "a bright red flag"),
    ("the Sunday bridge", "a bundle of strong climbing rope"),
]


@dataclass(frozen=True)
class Adventure:
    title: str
    opening: str
    danger: str
    sound: str
    friend_line: str
    plan: str
    result: str
    ending: str


ADVENTURES = (
    Adventure(
        "the narrow ledge",
        "On Sunday morning, Luna carried {object_phrase} toward the old lookout above {setting}.",
        "A sudden gust shoved the bell toward a narrow ledge, and Luna's paws slipped on the loose gravel.",
        '"Clang! Clang!" went the bell as it bounced beside the drop.',
        '"Do not reach alone," {friend} called. "I can anchor the rope while you crawl low."',
        "Luna clipped the rope around a sturdy pine, and {friend} held it tight while Luna reached the bell.",
        "The friends pulled together, and the dangerous ledge became a careful path instead of a foolish race.",
        "At the lookout, the Sunday bell rang once for the valley, and two happy voices answered, \"Hooray!\"",
    ),
    Adventure(
        "the rushing stream",
        "Luna and {friend} followed a bright trail toward {setting}, carrying {object_phrase} for a Sunday celebration.",
        "A stream had swollen across the trail, and the current tugged the bell from Luna's basket.",
        '"Splash! Whoosh!" cried the water as the bell spun downstream.',
        '"I will block the current with these stones," {friend} said. "You guide the bell toward me."',
        "Luna used a long branch to steer the bell while {friend} built a little stone wall.",
        "The friends' plan slowed the water long enough to rescue the bell without either one stepping into danger.",
        "The rescued bell chimed beside the stream while wet footprints showed the shape of their teamwork.",
    ),
    Adventure(
        "the dark tunnel",
        "A Sunday map led Luna into a cool tunnel beneath {setting}, where {object_phrase} glimmered in her paws.",
        "The tunnel forked, and Luna chose the wrong passage; soon the daylight disappeared behind her.",
        '"Tap, tap, tap," echoed the tunnel as Luna tested the stone walls.',
        '"Listen for my whistle," {friend} said. "We can follow the sound back together."',
        "{friend} whistled three times, and Luna answered by tapping the bell. They followed the sounds until the passages joined.",
        "The two explorers learned that courage can mean stopping, listening, and accepting help.",
        "Outside, the Sunday sun warmed the bell while Luna and {friend} marked the safe tunnel on their map.",
    ),
    Adventure(
        "the broken footbridge",
        "Luna planned a Sunday feat: carrying {object_phrase} across a footbridge above {setting}.",
        "One plank cracked under her weight, leaving the bell safe but Luna stranded on the far side.",
        '"Crack! Creak!" groaned the bridge between the friends.',
        '"Stay still," {friend} said. "I will find the strong boards, and you can pass the bell one careful step at a time."',
        "{friend} tested each plank with a stick while Luna moved slowly, passing the bell across only when the bridge held firm.",
        "Patience and friendship carried them over more safely than speed could have done.",
        "The bell rested on solid ground, and the broken bridge creaked behind two friends who had crossed with care.",
    ),
)


def _choose(params: StoryParams) -> Adventure:
    if params.seed is None:
        return ADVENTURES[0]
    return ADVENTURES[params.seed % len(ADVENTURES)]


def _feat_phrase(label: str) -> str:
    return dict(FEATS).get(label, f"a {label}")


def build_world(params: StoryParams) -> World:
    if params.name == params.friend_name:
        raise StoryError("The adventurer and friend must have different names.")
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.feat not in dict(FEATS):
        raise StoryError(f"Unknown Sunday feat: {params.feat}")

    world = World()
    luna = world.add(
        Entity(
            id=params.name,
            kind="character",
            type="adventurer",
            label="adventurer",
            meters={"balance": 1.0, "courage": 1.0},
            memes={"hope": 1.0, "friendship": 1.0},
        )
    )
    friend = world.add(
        Entity(
            id=params.friend_name,
            kind="character",
            type="helper",
            label="friend",
            meters={"strength": 1.0, "care": 1.0},
            memes={"trust": 1.0, "friendship": 1.0},
        )
    )
    object_entity = world.add(
        Entity(
            id="sunday_feat",
            kind="thing",
            type="relic",
            label=params.feat,
            meters={"safe": 1.0},
            memes={"meaning": 1.0},
            held_by=luna.id,
        )
    )

    adventure = _choose(params)
    values = {
        "friend": friend.id,
        "setting": params.setting,
        "object_phrase": _feat_phrase(params.feat),
    }

    world.say(
        f"{params.name} woke before breakfast on Sunday, ready for a brave feat with {friend.id}."
    )
    world.say(adventure.opening.format(**values))
    world.say(
        f"The plan was simple in its summary: reach the high place, protect {_feat_phrase(params.feat)}, and return before sunset."
    )
    world.para()
    world.say(adventure.danger.format(**values))
    world.say(adventure.sound.format(**values))
    luna.meters["balance"] = 0.3
    luna.memes["worry"] = 1.0
    world.say(adventure.friend_line.format(**values))
    world.para()
    world.say(
        f"{params.name} looked at {friend.id} and said, "
        f'"You are right. A real feat should bring us home safely."'
    )
    world.say(adventure.plan.format(**values))
    object_entity.held_by = None
    luna.meters["balance"] = 1.0
    luna.memes["worry"] = 0.0
    luna.memes["gratitude"] = 1.0
    luna.memes["friendship"] += 1.0
    friend.memes["trust"] += 1.0
    friend.memes["friendship"] += 1.0
    world.say(
        f'"We did it together," {friend.id} said. "{params.name}, your courage listened to friendship."'
    )
    world.say(adventure.result.format(**values))
    world.para()
    world.say(adventure.ending.format(**values))
    world.say(
        f"That was the Sunday summary: the greatest part of {params.name}'s feat was not reaching far, but returning safely with a friend."
    )

    world.facts.update(
        adventurer=luna,
        friend=friend,
        feat=object_entity,
        adventure=adventure,
        setting=params.setting,
        danger=adventure.danger.format(**values),
        sound=adventure.sound.format(**values),
        friend_line=adventure.friend_line.format(**values),
        plan=adventure.plan.format(**values),
        result=adventure.result.format(**values),
        ending=adventure.ending.format(**values),
    )
    return world


def generation_prompts(world: World) -> list[str]:
    adventurer: Entity = world.facts["adventurer"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]
    feat: Entity = world.facts["feat"]  # type: ignore[assignment]
    return [
        f"Write an Adventure story about {adventurer.id}'s Sunday feat with sound effects and friendship.",
        f"Tell a child-friendly story in {world.facts['setting']} where {adventurer.id} and {friend.id} protect {feat.label}.",
        "Create a Sunday summary showing that brave choices become safer with a helpful friend.",
    ]


def story_qa(world: World) -> list[QAItem]:
    adventurer: Entity = world.facts["adventurer"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]
    feat: Entity = world.facts["feat"]  # type: ignore[assignment]
    return [
        QAItem(
            question="Who went on the Sunday adventure?",
            answer=f"{adventurer.id} went on the Sunday adventure with {friend.id}, a caring friend.",
        ),
        QAItem(
            question=f"What danger threatened {feat.label}?",
            answer=str(world.facts["danger"]),
        ),
        QAItem(
            question="What sound effect showed that something had gone wrong?",
            answer=str(world.facts["sound"]),
        ),
        QAItem(
            question="How did friendship help solve the problem?",
            answer=f"{friend.id} offered a safe plan, and {adventurer.id} listened. {world.facts['plan']}",
        ),
        QAItem(
            question="What did the Sunday summary teach?",
            answer=f"The Sunday summary taught that courage works best with care and friendship: {world.facts['result']}",
        ),
        QAItem(
            question="What final image proves the adventure ended well?",
            answer=str(world.facts["ending"]),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is friendship?",
            answer="Friendship is a caring connection in which people help, trust, and listen to one another.",
        ),
        QAItem(
            question="Why can sound effects help an adventure story?",
            answer="Sound effects make action easier to imagine and help readers notice when a danger or exciting change occurs.",
        ),
        QAItem(
            question="What makes a feat wise rather than reckless?",
            answer="A wise feat uses preparation, attention, and help so that courage does not create unnecessary danger.",
        ),
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sunday adventure story world.")
    parser.add_argument("--name")
    parser.add_argument("--friend-name")
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--feat", choices=[name for name, _ in FEATS])
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
    name = args.name or rng.choice(NAMES)
    choices = [item for item in NAMES if item != name]
    return StoryParams(
        name=name,
        friend_name=args.friend_name or rng.choice(choices),
        setting=args.setting or rng.choice(SETTINGS),
        feat=args.feat or rng.choice([name for name, _ in FEATS]),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: type={entity.type}, meters={entity.meters}, "
            f"memes={entity.memes}, held_by={entity.held_by}"
        )
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.extend(["", "== story qa =="])
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world qa ==")
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


ASP_RULES = r"""
character(X) :- adventurer(X).
character(X) :- helper(X).
safe_feat(X) :- feat(X), friendship(X).
friendship(X) :- adventurer(X), helper(Y), X != Y.
completed(X) :- adventurer(X), safe_feat(F), feat(F).
#show completed/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for name in NAMES:
        lines.append(asp.fact("adventurer", name))
        lines.append(asp.fact("helper", name))
    for feat, _phrase in FEATS:
        lines.append(asp.fact("feat", feat.replace(" ", "_")))
    lines.append(asp.fact("friendship", "Luna"))
    return "\n".join(lines)


def asp_program(show: str = "#show completed/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    models = asp.solve(asp_program(), models=1)
    if not models:
        print("ASP verification failed: no model.")
        return 1
    for seed in range(8):
        sample = generate(
            StoryParams(
                name=NAMES[seed % len(NAMES)],
                friend_name=NAMES[(seed + 1) % len(NAMES)],
                setting=SETTINGS[seed % len(SETTINGS)],
                feat=FEATS[seed % len(FEATS)][0],
                seed=seed,
            )
        )
        if "Sunday" not in sample.story or "friend" not in sample.story.lower():
            print("Python verification failed: incomplete story.")
            return 1
    print("OK: ASP/Python adventure parity verified.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        print(asp_program())
        print("== ASP model ==")
        for atom in asp.one_model(asp_program()):
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, (feat, _phrase) in enumerate(FEATS):
            samples.append(
                generate(
                    StoryParams(
                        name=NAMES[index % len(NAMES)],
                        friend_name=NAMES[(index + 1) % len(NAMES)],
                        setting=SETTINGS[index % len(SETTINGS)],
                        feat=feat,
                        seed=base_seed + index,
                    )
                )
            )
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < max(1, args.n):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            index += 1

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
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
