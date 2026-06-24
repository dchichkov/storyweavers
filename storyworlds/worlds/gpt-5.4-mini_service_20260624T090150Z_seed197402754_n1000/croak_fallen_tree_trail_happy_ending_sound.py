#!/usr/bin/env python3
"""
A mythic story world about a fallen tree trail, a croaking mystery, and a happy ending.

A small child and an elder walk the fallen tree trail. Strange croaks sound from the
roots and hollows of a toppled tree. The child worries there is something spooky
lurking there, but the elder listens, solves the mystery, and the trail ends with a
gentle, happy feeling.

The world model tracks:
- physical meters: rustle, rain, wetness, hiddenness, light, distance
- emotional memes: fear, curiosity, relief, joy, trust
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# ---------------------------------------------------------------------------
# Core domain registries
# ---------------------------------------------------------------------------

PEOPLE = {
    "child": {
        "type": "child",
        "name_pool": ["Mina", "Ivo", "Lena", "Taro", "Nia", "Rumi", "Bela"],
    },
    "elder": {
        "type": "elder",
        "name_pool": ["Ari", "Mara", "Soren", "Tessa", "Oren", "Luma"],
    },
}

SOUNDS = {
    "croak": {
        "word": "croak",
        "description": "a deep, bobbing croak",
        "source_pool": ["frog", "toad", "nest of frogs"],
    },
    "rustle": {
        "word": "rustle",
        "description": "a leaf-soft rustle",
        "source_pool": ["wind", "moss", "small paws"],
    },
    "drip": {
        "word": "drip",
        "description": "a steady drip",
        "source_pool": ["wet bark", "a leaf tip", "the muddy root"],
    },
}

SETTING = {
    "id": "fallen_tree_trail",
    "place": "the fallen tree trail",
    "details": [
        "The trail wound beneath a giant tree that had fallen across the path long ago.",
        "Its roots rose like a broken crown, and the air smelled of moss and rain.",
        "Little hollows hid under the bark, and every sound seemed bigger there.",
    ],
}

MYSTERIES = {
    "croak_tree": {
        "mystery": "why the fallen tree kept croaking",
        "clue": "the croak came from a damp hollow near the roots",
        "solution": "a family of frogs had tucked itself in the hollow to stay safe",
        "turn_sound": "croak",
        "reveal_sound": "plop",
    },
}

# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str = "fallen_tree_trail"
    mystery: str = "croak_tree"
    seed: Optional[int] = None
    child_name: str = "Mina"
    elder_name: str = "Ari"


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    name: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        # neutral, child-facing defaults
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.sound_log: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        w = World(self.params)
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        w.sound_log = list(self.sound_log)
        return w


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def sound_line(sound: str, source: str) -> str:
    if sound == "croak":
        return f"From the hollow came a croak, low and round, as if the tree itself were speaking."
    if sound == "rustle":
        return f"A rustle ran through the leaves like a tiny secret."
    return f"A drip answered the silence, soft as a blink."


def build_world(params: StoryParams) -> World:
    world = World(params)
    child = world.add(Entity(
        id="child", kind="character", type="child", name=params.child_name,
        meters={"distance": 0.0}, memes={"curiosity": 1.0, "fear": 0.0, "joy": 0.0, "relief": 0.0},
    ))
    elder = world.add(Entity(
        id="elder", kind="character", type="elder", name=params.elder_name,
        meters={"distance": 0.0}, memes={"calm": 1.0, "trust": 0.0},
    ))

    mystery = MYSTERIES[params.mystery]
    world.facts.update(child=child, elder=elder, mystery=mystery, setting=SETTING)

    # Act 1: setting and the first strange sound
    world.say(f"{SETTING['details'][0]}")
    world.say(f"{child.name} and {elder.name} walked the {SETTING['place']}, where old roots made arches over the trail.")
    world.say(f"{child.name} heard {mystery['mystery']} and stopped short.")
    world.say(sound_line(mystery["turn_sound"], mystery["clue"]))
    child.memes["fear"] += 1.0
    child.memes["curiosity"] += 1.0

    # Act 2: mystery and worry
    world.para()
    world.say(f"{child.name} whispered, 'Is something lonely in there?'")
    world.say(f"{elder.name} knelt by the roots and listened carefully.")
    world.say(f"They found {mystery['clue']}.")
    world.say(sound_line("rustle", "wind"))
    world.say(f"Then another sound answered: {sound_line('drip', 'water')}")
    child.memes["fear"] += 0.5
    child.memes["trust"] += 1.0

    # Act 3: solve and happy ending
    world.para()
    world.say(f"{elder.name} smiled. 'No monster lives here,' they said. 'The trail is hosting frogs in a safe, damp home.'")
    world.say(f"As if to prove it, the hollow gave one last {mystery['turn_sound']}, and then came a cheerful {mystery['reveal_sound']}.")
    world.say(f"{child.name} peered inside and saw little frogs blinking in the moss, snug and unafraid.")
    child.memes["fear"] = 0.0
    child.memes["joy"] += 2.0
    child.memes["relief"] += 2.0
    elder.memes["trust"] += 1.0

    world.para()
    world.say(f"{child.name} laughed, because the mystery had not been spooky after all.")
    world.say(f"Together they left the fallen tree trail with light steps, and the croaks sounded like a friendly song behind them.")
    world.say(f"The ending felt happy, as if the old tree had been keeping a tiny, secret blessing all along.")

    return world


# ---------------------------------------------------------------------------
# Quality gate / ASP twin
# ---------------------------------------------------------------------------

def reasonableness_gate(params: StoryParams) -> None:
    if params.setting != "fallen_tree_trail":
        raise StoryError("This world only supports the fallen tree trail setting.")
    if params.mystery not in MYSTERIES:
        raise StoryError("Unknown mystery.")
    if not params.child_name or not params.elder_name:
        raise StoryError("Both child and elder names are required.")


ASP_RULES = r"""
setting(fallen_tree_trail).
mystery(croak_tree).

sound(croak).
sound(rustle).
sound(drip).

proves_happy_end(M) :- mystery(M).
solved(M) :- mystery(M).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "fallen_tree_trail"),
        asp.fact("mystery", "croak_tree"),
    ]
    for sid in SOUNDS:
        lines.append(asp.fact("sound", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:  # pragma: no cover
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show setting/1. #show mystery/1. #show sound/1."))
    facts = {
        "setting": set(asp.atoms(model, "setting")),
        "mystery": set(asp.atoms(model, "mystery")),
        "sound": set(asp.atoms(model, "sound")),
    }
    expected = {
        "setting": {("fallen_tree_trail",)},
        "mystery": {("croak_tree",)},
        "sound": {("croak",), ("rustle",), ("drip",)},
    }
    if facts != expected:
        print("MISMATCH between ASP facts and Python registries.")
        print("expected:", expected)
        print("got:", facts)
        return 1
    print("OK: ASP and Python registries match.")
    return 0


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    mystery = f["mystery"]["mystery"]
    return [
        f'Write a myth-like story for a young child about {SETTING["place"]} and a mystery involving the word "croak".',
        f"Tell a gentle tale where {child.name} hears {mystery} and {elder.name} helps solve it on {SETTING['place']}.",
        "Write a short story with sound effects, a mystery to solve, and a happy ending in an old, mossy place.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    mystery = f["mystery"]
    return [
        QAItem(
            question=f"What made {child.name} stop on the trail?",
            answer=f"{child.name} stopped because they heard a strange croak coming from the fallen tree trail.",
        ),
        QAItem(
            question=f"Who helped solve the mystery for {child.name}?",
            answer=f"{elder.name} helped by listening carefully and looking into the damp hollow near the roots.",
        ),
        QAItem(
            question="What was the mystery in the story?",
            answer=f"The mystery was why the fallen tree kept croaking, and the answer was that frogs were hiding safely inside the hollow.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended happily, with the child laughing and the trail feeling friendly instead of spooky.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a croak?",
            answer="A croak is a deep sound that frogs and toads often make.",
        ),
        QAItem(
            question="Why do frogs like damp places?",
            answer="Frogs like damp places because their skin needs moisture, and wet, shady spots help them stay comfortable.",
        ),
        QAItem(
            question="What is a fallen tree trail?",
            answer="A fallen tree trail is a path where a tree has toppled down, making roots, bark, and hollows part of the landscape.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic story world about a croaking mystery on a fallen tree trail.")
    ap.add_argument("--setting", choices=["fallen_tree_trail"], default="fallen_tree_trail")
    ap.add_argument("--mystery", choices=sorted(MYSTERIES), default="croak_tree")
    ap.add_argument("--child-name")
    ap.add_argument("--elder-name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    child_name = args.child_name or rng.choice(PEOPLE["child"]["name_pool"])
    elder_name = args.elder_name or rng.choice(PEOPLE["elder"]["name_pool"])
    params = StoryParams(
        setting=args.setting,
        mystery=args.mystery,
        seed=args.seed,
        child_name=child_name,
        elder_name=elder_name,
    )
    reasonableness_gate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
        print(asp_program("#show setting/1. #show mystery/1. #show sound/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show setting/1. #show mystery/1. #show sound/1."))
        print("ASP model:")
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(setting="fallen_tree_trail", mystery="croak_tree", seed=base_seed)
        samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 10):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
