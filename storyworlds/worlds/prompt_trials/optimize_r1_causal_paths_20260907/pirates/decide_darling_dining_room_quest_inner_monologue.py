#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample

@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

@dataclass
class StoryParams:
    quest: str
    obstacle: str
    solution: str
    companion: str
    companion_type: str
    darling: str
    clue: str
    reward: str
    seed: int | None = None

@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    history: list[str] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)
        self.history.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

QUESTS = {
    "silver_key": {
        "object": "a silver key",
        "location": "beneath the dining-room table",
        "reward": "the little music box",
        "clue": "three crumbs beside a chair leg",
    },
    "blue_ribbon": {
        "object": "a blue ribbon",
        "location": "behind the tall china cabinet",
        "reward": "a birthday parcel",
        "clue": "a shining thread on the rug",
    },
    "painted_spoon": {
        "object": "a painted wooden spoon",
        "location": "inside the old sideboard",
        "reward": "a warm bowl of pudding",
        "clue": "a yellow dot near the teapot",
    },
}

OBSTACLES = {
    "darkness": {
        "problem": "The dining room was dim, and the hiding place looked deep and uncertain.",
        "solutions": ["lantern", "curtain"],
    },
    "high_shelf": {
        "problem": "The clue led to a high shelf that small hands could not safely reach.",
        "solutions": ["chair", "helper"],
    },
    "wrong_clue": {
        "problem": "The first clue seemed to point beneath the table, but nothing was there.",
        "solutions": ["notice", "ask"],
    },
    "sleepy_cat": {
        "problem": "A sleepy cat guarded the path, its tail curled across the rug.",
        "solutions": ["wait", "treat"],
    },
}

SOLUTIONS = {
    "lantern": "They carried a battery lantern, and its gentle glow showed a second clue.",
    "curtain": "They opened the curtains, letting a stripe of afternoon light reach the floor.",
    "chair": "They stopped and fetched a grown-up instead of climbing the chair.",
    "helper": "They called Aunt May, who lifted the object down while they watched.",
    "notice": "They looked again and noticed the clue had been turned upside down.",
    "ask": "They asked Darling what she remembered, and her answer changed the search.",
    "wait": "They waited quietly until the cat stretched and padded away.",
    "treat": "They offered the cat a tiny treat, and it moved aside with a pleased purr.",
}

NAMES = ["Milo", "Nora", "Tessa", "Ben", "Ivy", "Leo"]
COMPANION_TYPES = ["sister", "brother", "friend"]
CLUES = ["a brass button", "a folded napkin", "a fleck of blue paint", "a tiny bell"]
REWARDS = ["a hug from Darling", "a shared slice of cake", "a secret dance", "a bright gold sticker"]

KNOWLEDGE = {
    "quest": QAItem("What is a quest?", "A quest is a careful journey toward a goal, often guided by clues."),
    "suspense": QAItem("What is suspense?", "Suspense is the feeling of waiting to discover what will happen next."),
    "inner_monologue": QAItem("What is an inner monologue?", "An inner monologue is a character's private thought spoken inside their mind."),
    "safety": QAItem("Why should children ask for help with a high shelf?", "A grown-up can reach safely and keep a child from falling."),
}

def build_world(p: StoryParams) -> World:
    world = World()
    child = world.add(Entity("child", "character", "child", "the child"))
    companion = world.add(Entity("companion", "character", p.companion_type, p.companion))
    darling = world.add(Entity("darling", "character", "grandparent", p.darling))
    room = world.add(Entity("dining_room", "place", "dining_room", "the dining room"))
    child.memes["curiosity"] = 1
    companion.memes["hope"] = 1
    world.facts.update(child=child, companion=companion, darling=darling, room=room)
    return world

def tell(p: StoryParams) -> World:
    if p.quest not in QUESTS:
        raise StoryError("Unknown quest.")
    if p.obstacle not in OBSTACLES:
        raise StoryError("Unknown obstacle.")
    if p.solution not in OBSTACLES[p.obstacle]["solutions"]:
        raise StoryError(f"Solution '{p.solution}' does not fit obstacle '{p.obstacle}'.")
    world = build_world(p)
    child, companion, darling = world.facts["child"], world.facts["companion"], world.facts["darling"]
    q = QUESTS[p.quest]
    obstacle = OBSTACLES[p.obstacle]

    world.say(f"After supper, {darling.id} placed a small card beside the flower vase in the dining room.")
    world.say(f'"A quest for my darling helpers," {darling.id} said. "Can you find {q["object"]}?"')
    world.say(f"{child.id.capitalize()} felt a happy flutter. Inside, {child.id} thought, \"I will decide carefully, because Darling is counting on us.\"")
    world.say(f"{companion.id.capitalize()} found the first clue: {q['clue']} led toward {q['location']}.")
    world.para()
    world.say(obstacle["problem"])
    world.say(f'"Should we hurry?" {companion.id} asked.')
    world.say(f'"No," {child.id} replied. "We can think first. Darling said a good quest needs careful eyes."')
    world.say(f"That made the silence feel larger. Somewhere near the dishes, something gave a tiny, secret sound.")
    world.say(SOLUTIONS[p.solution])
    child.memes["courage"] += 1
    companion.memes["trust"] += 1
    world.para()

    if p.obstacle == "wrong_clue":
        world.say(f"{child.id.capitalize()} turned the clue around and saw an arrow pointing toward {q['location']}.")
        world.say(f'"I was looking at it the wrong way," {child.id} whispered.')
    elif p.obstacle == "high_shelf":
        world.say(f"{darling.id.capitalize()} reached safely, while {child.id} kept both feet on the floor.")
    elif p.obstacle == "darkness":
        world.say(f"The new light made the silver edges of the dishes sparkle.")
    else:
        world.say("The quiet room became friendly again, and the quest moved on.")

    world.say(f"At last, they found {q['object']}.")
    world.say(f'"We found it, darling!" {child.id} called.')
    world.say(f"{darling.id.capitalize()} opened her arms. \"I knew you would decide together,\" she said.")
    world.say(f"They shared {p.reward}, while the dining room filled with warm voices and the soft clink of spoons.")
    world.facts.update(quest=q, obstacle=obstacle, solution=p.solution, found=True)
    return world

def prompts(world: World) -> list[str]:
    p = world.facts
    q = p["quest"]
    return [
        f"Write a heartwarming dining-room quest where children find {q['object']} through clues.",
        "Include suspense, a brief inner monologue, and dialogue that changes the children's decision.",
        "End with Darling welcoming the children and showing what their careful choice accomplished.",
    ]

def story_qa(world: World) -> list[QAItem]:
    p = world.facts
    q = p["quest"]
    return [
        QAItem("Where did the quest take place?", "The quest took place in the dining room after supper."),
        QAItem("What were the children trying to find?", f"They were trying to find {q['object']}."),
        QAItem("What helped them solve the difficulty?", f"They used {p['solution']} to handle the obstacle and continue safely."),
        QAItem("What did Darling say at the end?", "Darling said she knew they would decide together."),
        QAItem("How did the quest end?", "They found the hidden object, shared a treat, and celebrated together."),
    ]

def world_qa(world: World) -> list[QAItem]:
    return [KNOWLEDGE["quest"], KNOWLEDGE["suspense"], KNOWLEDGE["inner_monologue"], KNOWLEDGE["safety"]]

def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )

def valid_combos() -> list[tuple[str, str, str]]:
    return [(q, o, s) for q in QUESTS for o, data in OBSTACLES.items() for s in data["solutions"]]

ASP_RULES = r"""
valid(Q,O,S) :- quest(Q), obstacle(O), solution(O,S).
"""

def asp_facts() -> str:
    return "\n".join(
        [f"quest({q})." for q in QUESTS]
        + [f"obstacle({o})." for o in OBSTACLES]
        + [f"solution({o},{s})." for o, data in OBSTACLES.items() for s in data["solutions"]]
    )

def asp_verify() -> int:
    expected = set(valid_combos())
    try:
        import asp
        program = asp_facts() + "\n" + ASP_RULES + "\n#show valid/3."
        atoms = asp.atoms(asp.one_model(program), "valid")
        actual = set(atoms)
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 0
    if actual != expected:
        print("ASP mismatch.")
        return 1
    print(f"OK: ASP matches {len(expected)} valid combinations.")
    for i, combo in enumerate(sorted(expected)[:20]):
        p = random_params(random.Random(i), combo)
        if not generate(p).story:
            return 1
    print("OK: generated stories exercised.")
    return 0

def random_params(rng: random.Random, combo=None) -> StoryParams:
    if combo is None:
        combo = rng.choice(valid_combos())
    quest, obstacle, solution = combo
    companion = rng.choice(NAMES)
    return StoryParams(
        quest=quest,
        obstacle=obstacle,
        solution=solution,
        companion=companion,
        companion_type=rng.choice(COMPANION_TYPES),
        darling=rng.choice(["Darling", "Grandma Rose", "Aunt May"]),
        clue=rng.choice(CLUES),
        reward=rng.choice(REWARDS),
    )

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A heartwarming dining-room quest storyworld.")
    parser.add_argument("--quest", choices=QUESTS)
    parser.add_argument("--obstacle", choices=OBSTACLES)
    parser.add_argument("--solution")
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
    quests = [args.quest] if args.quest else list(QUESTS)
    obstacles = [args.obstacle] if args.obstacle else list(OBSTACLES)
    combos = [(q, o, s) for q, o, s in valid_combos() if q in quests and o in obstacles and (not args.solution or s == args.solution)]
    if not combos:
        raise StoryError("No compatible quest, obstacle, and solution choices.")
    return random_params(rng, rng.choice(combos))

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = dict(entity.meters)
        memes = dict(entity.memes)
        lines.append(f"{entity.id}: meters={meters}, memes={memes}")
    lines.append("features: Quest, Inner Monologue, Suspense, Heartwarming")
    return "\n".join(lines)

def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("\n== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}\nA: {item.answer}")
    lines.append("\n== World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}\nA: {item.answer}")
    return "\n".join(lines)

def emit(sample: StorySample, trace=False, qa=False, header="") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print(format_qa(sample))

def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_facts() + "\n" + ASP_RULES + "\n#show valid/3.")
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print("Valid combinations:")
        for combo in valid_combos():
            print("  " + " / ".join(combo))
        return

    rng = random.Random(args.seed)
    if args.all:
        params_list = [
            random_params(random.Random(i), combo)
            for i, combo in enumerate(valid_combos())
        ]
    else:
        params_list = [resolve_params(args, random.Random(rng.randrange(2**31))) for _ in range(args.n)]

    samples = [generate(p) for p in params_list]
    if args.json:
        payload = [s.to_dict() for s in samples]
        print(json.dumps(payload[0] if len(payload) == 1 else payload, indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### Quest {i + 1}" if len(samples) > 1 else "")

if __name__ == "__main__":
    main()
