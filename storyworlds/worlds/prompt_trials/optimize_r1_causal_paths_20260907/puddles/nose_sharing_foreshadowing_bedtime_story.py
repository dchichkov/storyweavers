#!/usr/bin/env python3
"""A gentle bedtime story about a nose, sharing, and a clue that comes true."""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    child: str = "Mira"
    companion: str = "Ollie"
    object_name: str = "moonberry muffin"
    setting: str = "the little blue bedroom"
    problem: str = "sharing"
    solution: str = "split"
    voice: str = "soft"
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    label: str
    kind: str
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
    def __init__(self, params: StoryParams, rng: random.Random) -> None:
        self.params = params
        self.rng = rng
        self.entities: dict[str, Entity] = {}
        self.history: list[Event] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
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


PROBLEMS = {
    "sharing": ("split", "offer"),
    "sneeze": ("wait", "comfort"),
    "bedtime": ("whisper", "promise"),
    "secret": ("tell", "invite"),
}

OPENINGS = [
    "{child} was almost asleep when the moonlight made a silver path across {setting}.",
    "At bedtime, {child} tucked the blanket beneath {companion}'s chin and listened to the quiet room.",
    "The house had grown hushed, but one small adventure was still awake in {setting}.",
]

WARNINGS = [
    "Just then, {child}'s nose gave a tiny twitch.",
    "A feather from the pillow floated past, and {child}'s nose wiggled again.",
    "From the window came a cool breeze, carrying the clean smell of rain.",
]

CLOSINGS = [
    "Soon the room was quiet again, with two happy breaths rising and falling together.",
    "The moon moved across the wall, and the shared treat left a warm little memory behind.",
    "By the time the stars blinked twice, both friends were dreaming of tomorrow.",
]

NAMES = ["Mira", "Nia", "Leo", "Tess", "Ari", "Sam", "Luca", "Pia"]
COMPANIONS = ["Ollie", "Pip", "Bram", "Nell", "Toby", "Wren"]
TREATS = ["moonberry muffin", "star-shaped biscuit", "honey bun", "warm cinnamon roll"]
VOICES = ["soft", "cozy", "playful", "dreamy"]


def build_world(params: StoryParams) -> World:
    if params.problem not in PROBLEMS:
        raise StoryError("That bedtime problem is not part of this story world.")
    if params.solution not in PROBLEMS[params.problem]:
        raise StoryError("That solution does not fit the chosen bedtime problem.")
    if params.child == params.companion:
        raise StoryError("The child and companion need different names.")
    world = World(params, random.Random(params.seed))
    child = world.add(Entity("child", params.child, "character",
                             memes={"kindness": 0, "worry": 0, "sleepiness": 1}))
    companion = world.add(Entity("companion", params.companion, "companion",
                                 memes={"trust": 1, "hunger": 0}))
    treat = world.add(Entity("treat", params.object_name, "treat",
                             meters={"pieces": 1, "shared": 0}))
    blanket = world.add(Entity("blanket", "the quilt", "blanket",
                               meters={"warmth": 1}))
    nose = world.add(Entity("nose", "a small nose", "body",
                            meters={"twitches": 0, "sneezes": 0}))
    world.facts.update(child=child, companion=companion, treat=treat,
                       blanket=blanket, nose=nose)
    return world


def opening(world: World) -> None:
    p = world.params
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    companion: Entity = world.facts["companion"]  # type: ignore[assignment]
    text = world.rng.choice(OPENINGS).format(
        child=child.label, companion=companion.label, setting=p.setting
    )
    text += f" Beside the bed lay one {p.object_name}, saved for a last sleepy bite."
    world.record("arrive", "child", "treat", text,
                 f"{child.label} had one special {p.object_name} at bedtime.",
                 "The treat became part of a quiet choice.")


def foreshadow(world: World) -> None:
    nose: Entity = world.facts["nose"]  # type: ignore[assignment]
    nose.meters["twitches"] += 1
    world.facts["clue"] = "nose_twitch"
    warning = world.rng.choice(WARNINGS).format(
        child=world.params.child, companion=world.params.companion
    )
    text = (f"{warning} {world.params.child} noticed the clue and tucked the "
            f"{world.params.object_name} a little farther from the pillow.")
    world.record("clue", "child", "nose", text,
                 "The nose twitched before the hidden feather could cause trouble.",
                 "The child learned that a small warning can be worth noticing.")


def create_problem(world: World) -> None:
    p = world.params
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    companion: Entity = world.facts["companion"]  # type: ignore[assignment]
    treat: Entity = world.facts["treat"]  # type: ignore[assignment]
    nose: Entity = world.facts["nose"]  # type: ignore[assignment]
    world.para()

    if p.problem == "sharing":
        companion.memes["hunger"] = 1
        child.memes["worry"] = 1
        text = (f'{companion.label} looked at the {p.object_name}. '
                f'"It smells lovely," {companion.label} whispered. '
                f'"But there is only one." {child.label} held it close, then '
                f'looked at the two sleepy faces.')
        cause = f"There was one {p.object_name}, but both friends wanted a taste."
        result = "The child had to choose between keeping it and sharing it."
    elif p.problem == "sneeze":
        nose.meters["sneezes"] = 1
        child.memes["worry"] = 1
        text = (f'The feather slipped from the pillow. "{child.label}—achoo!" '
                f'{companion.label} sat up. "Your nose warned you," '
                f'{companion.label} said, reaching for a tissue.')
        cause = "The pillow feather tickled the nose after the first warning."
        result = "The child needed to pause and care for the irritated nose."
    elif p.problem == "bedtime":
        child.memes["worry"] = 1
        text = (f'{companion.label} yawned, but the moonberry smell kept the room '
                f'bright in their minds. "My eyes are sleepy," {companion.label} '
                f'said. "{child.label}, what shall we do?"')
        cause = "A pleasant treat and an exciting thought were keeping everyone awake."
        result = "The friends needed a gentle plan for settling down."
    else:
        child.memes["worry"] = 1
        text = (f'{child.label} heard a tiny rustle beneath the bed. '
                f'"Should we keep it secret?" {child.label} asked. '
                f'"No secret feels smaller when we tell a friend," '
                f'{companion.label} replied.')
        cause = "A strange rustle made the child uncertain and afraid."
        result = "The child had to decide whether to hide the worry or invite help."
    world.record(p.problem, "child", "companion", text, cause, result)


def solve_problem(world: World) -> None:
    p = world.params
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    companion: Entity = world.facts["companion"]  # type: ignore[assignment]
    treat: Entity = world.facts["treat"]  # type: ignore[assignment]
    nose: Entity = world.facts["nose"]  # type: ignore[assignment]
    world.para()

    if p.problem == "sharing" and p.solution == "split":
        treat.meters["pieces"] = 2
        treat.meters["shared"] = 1
        child.memes["kindness"] += 1
        text = (f'"Let us share it exactly," {child.label} said. {child.label} '
                f'carefully broke the {p.object_name} in two. {companion.label} '
                f'smiled. "The first bite tastes better with a friend."')
        cause = "The child chose to divide the single treat fairly."
        result = f"Both friends received a piece of the {p.object_name}."
        kind = "share"
    elif p.problem == "sharing" and p.solution == "offer":
        treat.meters["shared"] = 1
        child.memes["kindness"] += 1
        text = (f'"You may have the first bite," {child.label} offered. '
                f'{companion.label} took a tiny piece, then pushed the rest back. '
                f'"Now you have some too." They passed it between them until only '
                f'a few crumbs remained.')
        cause = "The child offered first, and the companion returned the kindness."
        result = "The treat became a turn-taking game instead of a lonely bite."
        kind = "take_turns"
    elif p.problem == "sneeze" and p.solution == "wait":
        nose.meters["sneezes"] = 0
        text = (f'"Let us move the feather and wait," {child.label} said. '
                f'Together they placed it in a basket. After three calm breaths, '
                f'{child.label} whispered, "My nose feels better now."')
        cause = "They removed the feather and waited for the nose to settle."
        result = "The sneeze passed, and the room became comfortable again."
        kind = "wait"
    elif p.problem == "sneeze" and p.solution == "comfort":
        nose.meters["sneezes"] = 0
        text = (f'{companion.label} brought a soft tissue and held the cup of water. '
                f'"A little sip," {companion.label} said. "{child.label}, your nose '
                f'can rest." {child.label} nodded and breathed slowly.')
        cause = "The companion offered water and a soft tissue."
        result = "The child felt cared for and the nose stopped tickling."
        kind = "comfort"
    elif p.problem == "bedtime" and p.solution == "whisper":
        child.memes["sleepiness"] += 1
        text = (f'"We can tell the story in whispers," {child.label} decided. '
                f'They whispered about a boat crossing a silver puddle until even '
                f'the words became soft as feathers.')
        cause = "Whispering kept the story gentle instead of exciting."
        result = "The friends grew sleepy while sharing a quiet tale."
        kind = "whisper"
    elif p.problem == "bedtime" and p.solution == "promise":
        child.memes["sleepiness"] += 1
        text = (f'"We will save the rest for tomorrow," {child.label} promised. '
                f'{companion.label} nodded. "Tomorrow can hold the next bite and '
                f'the next adventure." They tucked the treat beside the lamp.')
        cause = "They promised that tomorrow would bring another chance."
        result = "The promise made it easier to put the treat away and rest."
        kind = "promise"
    elif p.problem == "secret" and p.solution == "tell":
        child.memes["worry"] = 0
        text = (f'"I heard a rustle under the bed," {child.label} admitted. '
                f'{companion.label} looked with a night-light. It was only a '
                f'loose slipper. "Thank you for telling me," {companion.label} said.')
        cause = "The child told the companion about the frightening sound."
        result = "The night-light showed that the secret rustle was only a slipper."
        kind = "tell"
    else:
        child.memes["worry"] = 0
        companion.memes["trust"] += 1
        text = (f'"Come look with me," {child.label} invited. They checked beneath '
                f'the bed together and found the loose slipper. {companion.label} '
                f'laughed softly. "A worry is easier to carry with two people."')
        cause = "The child invited the companion to investigate together."
        result = "Their shared courage turned the strange sound into a harmless discovery."
        kind = "invite"
    world.record(kind, "child", "companion", text, cause, result)


def resolve(world: World) -> None:
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    companion: Entity = world.facts["companion"]  # type: ignore[assignment]
    nose: Entity = world.facts["nose"]  # type: ignore[assignment]
    world.para()
    nose.meters["twitches"] += 1
    clue_result = (
        "The earlier nose twitch had warned them before the feather could spoil the night."
        if world.params.problem == "sneeze"
        else "The little nose gave one last twitch, then rested, as if it approved."
    )
    text = (f'{clue_result} {child.label} pulled the quilt over {companion.label}, '
            f'and {companion.label} pulled it back over {child.label}. '
            f'{random.Random(world.params.seed or 0).choice(CLOSINGS)}')
    world.record("sleep", "child", "blanket", text,
                 "Sharing attention and kindness made the bedtime worry smaller.",
                 "Both friends settled safely beneath the quilt.")


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    opening(world)
    foreshadow(world)
    create_problem(world)
    solve_problem(world)
    resolve(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a {p.voice} bedtime story about {p.child} noticing a nose clue and sharing {p.object_name} with {p.companion}.",
        f"Tell a gentle story in {p.setting} where a small warning foreshadows a later choice: {p.problem} solved by {p.solution}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    questions = {
        "clue": "What warning did the child notice?",
        "sharing": "What problem did the friends face?",
        "sneeze": "Why did the child need to pause?",
        "bedtime": "Why were the friends still awake?",
        "secret": "What worried the child?",
        "share": "How did the child share the treat?",
        "take_turns": "How did the friends share the treat?",
        "wait": "What did the friends do about the feather?",
        "comfort": "How did the companion help?",
        "whisper": "How did the friends make their story calm?",
        "promise": "What did the friends promise?",
        "tell": "What did the child tell the companion?",
        "invite": "How did the friends investigate?",
        "sleep": "How did the story end?",
    }
    out = []
    for event in world.history:
        if event.kind in questions:
            out.append(QAItem(questions[event.kind], f"{event.cause} {event.result}"))
    return out


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a nose for?",
               "A nose helps us smell things and breathe air."),
        QAItem("Why can sharing feel good?",
               "Sharing lets people enjoy something together and shows care for a friend."),
        QAItem("What does foreshadowing mean in a story?",
               "Foreshadowing is a small clue early in a story that hints at something later."),
        QAItem("Why is bedtime quieter than playtime?",
               "Quiet bedtime activities help bodies slow down so sleep can come."),
    ]


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


ASP_RULES = r"""
warning(nose, sneeze).
shared(split).
shared(offer).
compatible(sharing, split).
compatible(sharing, offer).
compatible(sneeze, wait).
compatible(sneeze, comfort).
compatible(bedtime, whisper).
compatible(bedtime, promise).
compatible(secret, tell).
compatible(secret, invite).
valid(P, S) :- compatible(P, S).
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("warning", "nose", "sneeze"),
        *[asp.fact("compatible", problem, solution)
          for problem, solutions in PROBLEMS.items()
          for solution in solutions],
    ])


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}"


def verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    found = set(asp.atoms(model, "valid"))
    expected = {(p, s) for p, solutions in PROBLEMS.items() for s in solutions}
    if found != expected:
        print("ASP/Python mismatch.")
        return 1
    for problem, solution in sorted(expected):
        sample = generate(StoryParams(problem=problem, solution=solution, seed=17))
        assert sample.story and sample.story_qa
        assert "nose" in sample.story.lower()
    print(f"OK: {len(expected)} causal paths and generated story checks passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--child")
    parser.add_argument("--companion")
    parser.add_argument("--object", dest="object_name")
    parser.add_argument("--problem", choices=sorted(PROBLEMS))
    parser.add_argument("--solution", choices=sorted({s for v in PROBLEMS.values() for s in v}))
    parser.add_argument("--voice", choices=VOICES)
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
    problem = args.problem or rng.choice(sorted(PROBLEMS))
    solution = args.solution or rng.choice(PROBLEMS[problem])
    if solution not in PROBLEMS[problem]:
        raise StoryError("That solution does not fit the selected problem.")
    return StoryParams(
        child=args.child or rng.choice(NAMES),
        companion=args.companion or rng.choice(COMPANIONS),
        object_name=args.object_name or rng.choice(TREATS),
        setting="the little blue bedroom",
        problem=problem,
        solution=solution,
        voice=args.voice or rng.choice(VOICES),
    )


CURATED = [
    StoryParams(child="Mira", companion="Ollie", object_name="moonberry muffin",
                problem="sharing", solution="split", voice="soft", seed=1),
    StoryParams(child="Leo", companion="Pip", object_name="honey bun",
                problem="sharing", solution="offer", voice="cozy", seed=2),
    StoryParams(child="Nia", companion="Wren", object_name="star-shaped biscuit",
                problem="sneeze", solution="wait", voice="dreamy", seed=3),
    StoryParams(child="Tess", companion="Bram", object_name="warm cinnamon roll",
                problem="sneeze", solution="comfort", voice="soft", seed=4),
    StoryParams(child="Ari", companion="Nell", object_name="moonberry muffin",
                problem="bedtime", solution="whisper", voice="cozy", seed=5),
    StoryParams(child="Sam", companion="Toby", object_name="honey bun",
                problem="secret", solution="invite", voice="dreamy", seed=6),
]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print("\n== Generation prompts ==")
        for prompt in sample.prompts:
            print(f"- {prompt}")
        print("\n== Story questions ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== World knowledge ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.n < 1:
        raise SystemExit("-n must be at least 1")
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        for problem, solution in sorted(asp.atoms(model, "valid")):
            print(f"{problem:10} -> {solution}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for index in range(args.n):
            seed = base_seed + index
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            samples.append(generate(params))

    if args.json:
        payload = [sample.to_dict() for sample in samples]
        print(json.dumps(payload[0] if len(payload) == 1 else payload,
                         indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa,
             header=f"### bedtime story {index + 1}" if len(samples) > 1 else "")
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
