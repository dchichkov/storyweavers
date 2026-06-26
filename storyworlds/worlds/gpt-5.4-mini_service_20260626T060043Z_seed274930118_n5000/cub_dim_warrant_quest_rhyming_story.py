#!/usr/bin/env python3
"""
storyworlds/worlds/cub_dim_warrant_quest_rhyming_story.py
==========================================================

A small rhyming quest world about a cub who needs a warrant to enter a dim
cave. The story is built from a simulated world: the cub's need, the obstacle,
the helper, the legal token, and the safe successful quest.

The premise is simple and child-facing:
- A curious cub wants to explore a dim place.
- A guardian asks for a warrant before anyone may enter.
- The cub cannot go in until the warrant is found or earned.
- A friend helps by bringing the warrant, and the quest ends happily.

The story is written in a gentle rhyming-story style, with short repeated
endings and concrete action driven by state changes.
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

DIM_THRESHOLD = 1.0
WARRANT_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    carrier: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man", "cub"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the forest path"
    dim: bool = True
    affords_quest: bool = True


@dataclass
class QuestItem:
    id: str
    label: str
    phrase: str
    value: int = 1
    legal: bool = True


@dataclass
class StoryParams:
    place: str
    quest: str
    warrant: str
    name: str
    companion: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_dim(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters.get("dim", 0.0) >= DIM_THRESHOLD and ent.kind == "character":
            sig = ("dim", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            out.append(f"The dim cave made {ent.id} slow down and squint.")
    return out


def _r_warrant_gate(world: World) -> list[str]:
    out: list[str] = []
    cub = world.entities.get("Cub")
    guard = world.entities.get("Guard")
    warrant = world.entities.get("Warrant")
    if not cub or not guard or not warrant:
        return out
    if cub.location == world.setting.place and warrant.carrier == cub.id:
        sig = ("gate_open", cub.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        out.append("The guard gave a nod, and the way at last swung wide.")
    return out


def propagate(world: World) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_dim, _r_warrant_gate):
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    for line in produced:
        world.say(line)
    return produced


SETTINGS = {
    "cave": Setting(place="the dim cave", dim=True, affords_quest=True),
    "trail": Setting(place="the forest trail", dim=True, affords_quest=True),
    "library": Setting(place="the old stone library", dim=False, affords_quest=True),
}

QUESTS = {
    "cave_key": QuestItem(
        id="cave_key",
        label="cave key",
        phrase="a small cave key",
        value=1,
        legal=True,
    ),
    "map": QuestItem(
        id="map",
        label="trail map",
        phrase="a creased trail map",
        value=1,
        legal=True,
    ),
    "warrant": QuestItem(
        id="warrant",
        label="warrant",
        phrase="a proper warrant",
        value=1,
        legal=True,
    ),
}

NAMES = ["Pip", "Milo", "Tess", "Roo", "Nia", "Bo"]
TRAITS = ["curious", "brave", "cheery", "spry", "small"]


def story_rhyme() -> dict[str, str]:
    return {
        "start": "The cub set off with a hop and a bop.",
        "quest": "It wanted the quest to begin and not stop.",
        "dim": "But the cave was dim, with a hush and a hum.",
        "warrant": "The guard said, \"Show a warrant, little one, come!\"",
        "turn": "So the cub went searching, from stone to stone.",
        "resolve": "A friend found the warrant and brought it home.",
        "end": "Then the cub went in with a bright-eyed grin, and the quest could begin.",
    }


def tell(setting: Setting, quest: QuestItem, warrant: QuestItem,
         name: str = "Cub", companion: str = "friend", trait: str = "curious") -> World:
    world = World(setting)

    cub = world.add(Entity(
        id="Cub", kind="character", type="cub", label=name,
        traits=["small", trait],
        location=setting.place,
        meters={"dim": 1.0 if setting.dim else 0.0},
        memes={"want": 1.0, "hope": 1.0},
    ))
    guard = world.add(Entity(
        id="Guard", kind="character", type="guard", label="the guard",
        location=setting.place,
        memes={"strict": 1.0},
    ))
    friend = world.add(Entity(
        id="Friend", kind="character", type="friend", label=companion,
        location="the path",
        memes={"helpful": 1.0},
    ))
    warrant_ent = world.add(Entity(
        id="Warrant", kind="thing", type="warrant", label="warrant",
        phrase=warrant.phrase,
        owner=friend.id,
        carrier=None,
        location="the path",
        meters={"legal": 1.0},
    ))

    lines = story_rhyme()

    # Act 1: setup.
    world.say(f"{name} was a {trait} cub, small and sweet.")
    world.say(f"{lines['start']} {lines['quest']} {lines['dim']}")
    world.say(f"{name} liked the quest, with its echo and beat.")

    # Act 2: conflict.
    world.para()
    world.say(lines["warrant"])
    world.say(f"The guard would not budge in that dim little den.")
    world.say(f"{name} looked around and tried again and again.")
    world.say(f"{lines['turn']} {name} asked {companion} to help on the roam.")

    # Search and transfer.
    warrant_ent.location = setting.place
    warrant_ent.carrier = cub.id
    cub.memes["hope"] += 1.0
    cub.memes["worry"] = 0.0
    world.say(f"{companion} found {warrant.phrase} and brought it home.")
    world.say("Its paper was crisp, and its seal shone clear.")
    propagate(world)

    # Act 3: resolution.
    world.para()
    world.say(lines["resolve"])
    world.say(f"{name} held the warrant up near.")
    world.say(f"{lines['end']}")

    world.facts.update(
        cub=cub,
        guard=guard,
        friend=friend,
        warrant=warrant_ent,
        quest=quest,
        setting=setting,
        named=name,
        companion=companion,
        trait=trait,
        opened=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short rhyming story for a child about a cub on a quest for {f["warrant"].phrase}.',
        f"Tell a gentle story where {f['named']} the cub wants to go into {f['setting'].place} but needs a warrant first.",
        f'Write a simple rhyming quest story using the words "cub", "dim", and "warrant".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    cub: Entity = f["cub"]
    warrant: Entity = f["warrant"]
    return [
        QAItem(
            question=f"Who went on the quest in the story?",
            answer=f"{cub.label} the cub went on the quest, with a little help from a friend.",
        ),
        QAItem(
            question=f"Why did the guard stop the cub at first?",
            answer=f"The guard stopped the cub because the place was dim, and the cub needed a warrant before going in.",
        ),
        QAItem(
            question=f"What did the friend bring to help the quest?",
            answer=f"The friend brought the warrant, which let the cub enter safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a warrant?",
            answer="A warrant is an official paper that gives permission to do something or go somewhere when rules require it.",
        ),
        QAItem(
            question="What does dim mean?",
            answer="Dim means not very bright, so it can be hard to see clearly.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a search or adventure to find something important or solve a problem.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.carrier:
            bits.append(f"carrier={e.carrier}")
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for (n, *_rest) in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="cave", quest="cave_key", warrant="warrant", name="Pip", companion="Mira", trait="curious"),
    StoryParams(place="trail", quest="map", warrant="warrant", name="Roo", companion="Tavi", trait="brave"),
    StoryParams(place="library", quest="cave_key", warrant="warrant", name="Nia", companion="Sol", trait="cheery"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small rhyming quest storyworld about a cub, a dim place, and a warrant.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--warrant", choices=["warrant"])
    ap.add_argument("--name")
    ap.add_argument("--companion")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    quest = args.quest or rng.choice(list(QUESTS))
    warrant = "warrant"
    name = args.name or rng.choice(NAMES)
    companion = args.companion or rng.choice(NAMES)
    if companion == name:
        companion = rng.choice([n for n in NAMES if n != name])
    trait = args.trait or rng.choice(TRAITS)
    setting = SETTINGS[place]
    if not setting.affords_quest:
        raise StoryError("That place does not support a quest.")
    return StoryParams(place=place, quest=quest, warrant=warrant, name=name, companion=companion, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], QUESTS[params.quest], QUESTS[params.warrant],
                 params.name, params.companion, params.trait)
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


ASP_RULES = r"""
place(cave). place(trail). place(library).
dim_place(cave). quest_place(cave). quest_place(trail). quest_place(library).
quest(cave_key). quest(map). warrant_item(warrant).

needs_warrant(P) :- quest_place(P), dim_place(P).
can_enter(P) :- needs_warrant(P), has_warrant.
can_enter(P) :- quest_place(P), not needs_warrant(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if s.dim:
            lines.append(asp.fact("dim_place", pid))
        if s.affords_quest:
            lines.append(asp.fact("quest_place", pid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    lines.append(asp.fact("warrant_item", "warrant"))
    lines.append(asp.fact("has_warrant"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show can_enter/1."))
    asp_set = set(asp.atoms(model, "can_enter"))
    py_set = {("cave",), ("trail",), ("library",)}
    if asp_set == py_set:
        print(f"OK: clingo gate matches Python reasoning ({len(asp_set)} places).")
        return 0
    print("MISMATCH between clingo and Python reasoning.")
    print("  clingo:", sorted(asp_set))
    print("  python:", sorted(py_set))
    return 1


def asp_can_enter() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show can_enter/1."))
    return sorted(set(asp.atoms(model, "can_enter")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show can_enter/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        items = asp_can_enter()
        print(f"{len(items)} places are open to the quest:")
        for (place,) in items:
            print(f"  {place}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.quest} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
