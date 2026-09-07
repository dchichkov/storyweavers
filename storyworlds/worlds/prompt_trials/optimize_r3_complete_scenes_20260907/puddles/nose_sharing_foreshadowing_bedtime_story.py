#!/usr/bin/env python3
"""A gentle bedtime story about a nose, sharing, and a small surprise."""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field

HERE = os.path.abspath(__file__)
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE)))))
sys.path.insert(0, ROOT)
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    path: str
    child: str
    friend: str
    seed: int | None = None


@dataclass
class Event:
    kind: str
    text: str
    cause: str
    result: str


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    events: list[Event] = field(default_factory=list)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def record(self, kind: str, text: str, cause: str, result: str) -> None:
        self.events.append(Event(kind, text, cause, result))

    def render(self) -> str:
        return "\n\n".join(event.text for event in self.events)


PATHS = ("sneeze", "secret", "cold")

CHILD_NAMES = ("Milo", "Nora", "Ivy", "Theo")
FRIEND_NAMES = ("Pip", "Luna", "Ben", "Maya")

OPENINGS = (
    "The moon shone softly through the curtains.",
    "Silver moonlight rested on the quiet floor.",
    "The house grew still while the stars blinked outside.",
)

SNEEZE_REACTIONS = (
    "Milo's nose gave one tiny twitch.",
    "A tickle danced at the end of Milo's nose.",
    "Milo felt a little feather of a tickle in his nose.",
)

SECRET_REACTIONS = (
    "Nora noticed that Pip kept touching his nose.",
    "Pip sniffed twice and looked toward the window.",
    "A small sound came from Pip's nose, though he tried to hide it.",
)

COLD_REACTIONS = (
    "Pip's nose looked pink in the lamplight.",
    "Pip rubbed his nose with the back of his hand.",
    "Pip sniffed and pulled the blanket close.",
)


def build_world(params: StoryParams) -> World:
    if params.path not in PATHS:
        raise StoryError("The story path must be sneeze, secret, or cold.")
    if params.child == params.friend:
        raise StoryError("The two characters must have different names.")

    world = World(params)
    child = world.add(Entity(params.child, "character", params.child))
    friend = world.add(Entity(params.friend, "character", params.friend))
    blanket = world.add(Entity("blanket", "thing", "the blue blanket"))
    child.memes["kindness"] = 1
    friend.memes["trust"] = 1
    world.facts.update(child=child, friend=friend, blanket=blanket, shared=False)

    rng = random.Random(params.seed)
    opening = rng.choice(OPENINGS)
    child_name = params.child
    friend_name = params.friend

    world.record(
        "arrival",
        f"{opening} {child_name} and {friend_name} snuggled together for a bedtime story. "
        f"Their noses peeked above the blue blanket.",
        "The children were settling down for the night.",
        f"{child_name} and {friend_name} were ready to listen together.",
    )

    if params.path == "sneeze":
        _sneeze_path(world, rng)
    elif params.path == "secret":
        _secret_path(world, rng)
    else:
        _cold_path(world, rng)

    world.facts["resolved"] = True
    return world


def _sneeze_path(world: World, rng: random.Random) -> None:
    child = world.facts["child"]
    friend = world.facts["friend"]
    blanket = world.facts["blanket"]
    child_name, friend_name = child.label, friend.label

    tickle = rng.choice(SNEEZE_REACTIONS).replace("Milo", child_name)
    world.record(
        "trouble",
        f"{tickle} \"I think a sneeze is coming,\" {child_name} whispered. "
        f"\"Should I move away?\" {friend_name} asked. "
        f"\"No. Just help me find a tissue,\" {child_name} said.",
        "A tickle in the nose warned that a sneeze might spread germs.",
        f"{friend_name} learned that {child_name} needed a tissue, not distance.",
    )

    blanket.meters["shared"] = 1
    child.memes["relief"] = 1
    world.record(
        "sharing",
        f"{friend_name} shared a tissue from the bedside table and held the blanket "
        f"open while {child_name} used it. \"Thank you,\" {child_name} said. "
        f"\"We can share the cozy part and keep the tissue to ourselves,\" "
        f"{friend_name} replied.",
        "The children wanted to stay close while keeping the sneeze contained.",
        f"They shared the blanket but used one tissue for the sneeze.",
    )

    child.meters["sneeze_caught"] = 1
    world.record(
        "resolution",
        f"The sneeze arrived with a tiny \"Achoo!\" and landed in the tissue. "
        f"{child_name} folded it shut and placed it in the bin. "
        f"{friend_name} pulled the blue blanket up to their chins, and both noses "
        f"soon pointed toward the same sleepy moon.",
        "The tissue caught the sneeze and was put away.",
        "The children stayed warm and safe beneath the shared blanket.",
    )


def _secret_path(world: World, rng: random.Random) -> None:
    child = world.facts["child"]
    friend = world.facts["friend"]
    blanket = world.facts["blanket"]
    child_name, friend_name = child.label, friend.label

    reaction = rng.choice(SECRET_REACTIONS).replace("Pip", friend_name).replace("Nora", child_name)
    world.record(
        "trouble",
        f"{reaction} \"Are you hiding something?\" {child_name} asked. "
        f"\"I heard a sniffly sound, but I do not want to spoil bedtime,\" "
        f"{friend_name} said.",
        "A strange nose sound made the children unsure what was wrong.",
        f"{friend_name} learned that {child_name} had noticed the sniffle.",
    )

    friend.memes["trust"] = 2
    world.record(
        "sharing",
        f"{child_name} shared the truth instead of guessing. \"My nose feels stuffy, "
        f"and I was afraid you would laugh,\" {friend_name} admitted. "
        f"\"I will not laugh. You can tell me things,\" {child_name} promised.",
        "Speaking honestly gave the children the information they needed.",
        f"{child_name} learned that {friend_name} felt worried, not playful.",
    )

    blanket.meters["shared"] = 1
    world.record(
        "resolution",
        f"{child_name} shared the softest corner of the blue blanket and fetched a "
        f"glass of water. After one small sip, {friend_name}'s nose felt calmer. "
        f"They left the door open a crack for the grown-up to check, then whispered "
        f"good night under the same warm fold.",
        "Water, comfort, and a nearby grown-up helped with the stuffy nose.",
        f"{friend_name} felt safe enough to rest, and the children shared the blanket.",
    )


def _cold_path(world: World, rng: random.Random) -> None:
    child = world.facts["child"]
    friend = world.facts["friend"]
    blanket = world.facts["blanket"]
    child_name, friend_name = child.label, friend.label

    reaction = rng.choice(COLD_REACTIONS).replace("Pip", friend_name)
    world.record(
        "trouble",
        f"{reaction} \"Your nose looks cold,\" {child_name} said. "
        f"\"I am trying not to shiver,\" {friend_name} answered. "
        f"{child_name} touched the edge of the blue blanket and made a plan.",
        "The pink nose and shiver showed that the blanket was not covering both children well.",
        f"{child_name} learned that {friend_name} needed warmth.",
    )

    blanket.meters["shared"] = 1
    child.memes["care"] = 1
    world.record(
        "decision",
        f"\"Move closer, and we can share the blanket fairly,\" {child_name} said. "
        f"{friend_name} moved beside {child_name}, but left one corner tucked around "
        f"the other child's shoulders. \"Now you are warm too,\" {friend_name} said.",
        "The children chose to share the blanket instead of letting one child keep all of it.",
        f"Each child received a warm part of the blanket.",
    )

    world.record(
        "resolution",
        f"The shiver stopped. {friend_name}'s nose no longer looked pink, and "
        f"{child_name} smiled at the quiet proof. Together they listened to the "
        f"last line of the bedtime story, then fell asleep with their hands resting "
        f"on the same blue blanket.",
        "Sharing the blanket made both children warm.",
        "Both children slept peacefully beneath their shared blanket.",
    )


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a bedtime story about {p.child} and {p.friend} sharing comfort after a nose-related worry.",
        f"Tell a gentle story where a child learns something important about {p.friend}'s nose and chooses kindness.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    questions = {
        "sneeze": (
            f"Why did {p.friend} look for a tissue for {p.child}?",
            f"{p.friend} looked for a tissue because {p.child}'s nose had a tickle and a sneeze was coming.",
        ),
        "secret": (
            f"What did {p.child} learn about {p.friend}?",
            f"{p.child} learned that {p.friend}'s nose felt stuffy and that {p.friend} was afraid of being laughed at.",
        ),
        "cold": (
            f"Why did {p.child} move closer to {p.friend}?",
            f"{p.child} moved closer because {p.friend}'s nose looked cold and {p.friend} was trying not to shiver.",
        ),
    }
    q, a = questions[p.path]
    return [QAItem(q, a), QAItem(
        "How did sharing help at the end?",
        f"{p.child} and {p.friend} shared comfort beneath the blue blanket, so they could rest peacefully together.",
    )]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a nose for?",
            "A nose helps us breathe and notice smells, and it can also tickle when a sneeze is coming.",
        ),
        QAItem(
            "Why can sharing be kind?",
            "Sharing can help another person feel cared for because both people get a fair part of something useful or comforting.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("\n== Story questions ==")
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.append("\n== World knowledge ==")
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


ASP_RULES = r"""
trouble(sneeze). trouble(secret). trouble(cold).
valid_path(P) :- trouble(P).
"""


def asp_facts() -> str:
    import importlib
    asp = importlib.import_module("asp")
    return "\n".join(asp.fact("trouble", path) for path in PATHS)


def asp_program(show: str = "#show valid_path/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id}: meters={meters}, memes={memes}")
    lines.append("--- events ---")
    lines.extend(f"  {event.kind}: {event.text}" for event in world.events)
    return "\n".join(lines)


def check_sample(sample: StorySample) -> None:
    world = sample.world
    assert world.facts["resolved"]
    assert len(world.events) == 4
    assert all(event.text in sample.story for event in world.events)
    assert "nose" in sample.story.lower()
    assert world.facts["blanket"].meters["shared"] == 1
    assert "share" in sample.story.lower() or "sharing" in sample.story.lower()
    assert all(item.answer.endswith(".") for item in sample.story_qa)


def asp_verify() -> int:
    import importlib
    asp = importlib.import_module("asp")
    atoms = asp.atoms(asp.one_model(asp_program()), "valid_path")
    found = tuple(sorted(a[0] for a in atoms))
    if set(found) != set(PATHS):
        print("MISMATCH: ASP and Python paths differ.")
        return 1
    for path in PATHS:
        sample = generate(StoryParams(path, "Milo", "Pip", 7))
        check_sample(sample)
    print(f"OK: {len(PATHS)} causal paths and story checks.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A bedtime nose-sharing storyworld.")
    parser.add_argument("--path", choices=PATHS)
    parser.add_argument("--child")
    parser.add_argument("--friend")
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
    path = args.path or rng.choice(PATHS)
    child = args.child or rng.choice(CHILD_NAMES)
    friend = args.friend or rng.choice(tuple(n for n in FRIEND_NAMES if n != child))
    if child == friend:
        raise StoryError("The two characters must have different names.")
    return StoryParams(path, child, friend, args.seed)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    sample = StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )
    check_sample(sample)
    return sample


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace:
        print(dump_trace(sample.world))
    if qa:
        print("\n" + format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.n < 1:
        raise SystemExit("-n must be at least 1")
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import importlib
        asp = importlib.import_module("asp")
        model = asp.one_model(asp_program())
        for path in sorted(a[0] for a in asp.atoms(model, "valid_path")):
            print(path)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        params_list = [StoryParams(path, "Milo", "Pip", base_seed + i) for i, path in enumerate(PATHS)]
    else:
        params_list = []
        for i in range(args.n):
            seed = base_seed + i
            params_list.append(resolve_params(args, random.Random(seed)))
            params_list[-1].seed = seed

    samples = [generate(params) for params in params_list]
    if args.json:
        payload = [sample.to_dict() for sample in samples]
        print(json.dumps(payload[0] if len(payload) == 1 else payload, indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if args.all:
            emit(sample, trace=args.trace, qa=args.qa, header=f"### {sample.params.path}")
        else:
            emit(sample, trace=args.trace, qa=args.qa)
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
