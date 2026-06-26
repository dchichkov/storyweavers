#!/usr/bin/env python3
"""
storyworlds/worlds/turban_touch_petting_zoo_problem_solving_twist.py
====================================================================

A small storyworld about a petting zoo, a turban, a touch, a problem, and a
twist. The tone is ghost-story-like: a gentle eerie feeling, a mystery, then a
careful solution that reveals the truth.

The world model keeps track of physical meters and emotional memes, and the
story is built from state changes rather than a fixed paragraph.
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    gentle: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the petting zoo"
    feels: str = "quiet and a little spooky"


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    animal: str
    turban_color: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    location: str = "gate"

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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.location = self.location
        return w


@dataclass
class Rule:
    name: str
    apply: callable


def _r_spook(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes.get("unease", 0.0) >= THRESHOLD and ("spook",) not in world.fired:
        world.fired.add(("spook",))
        child.memes["spookiness"] = child.memes.get("spookiness", 0.0) + 1
        out.append("A cold shiver seemed to hang in the air.")
    return out


def _r_touch_reveal(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    turban = world.get("turban")
    animal = world.get("animal")
    if child.memes.get("touched", 0.0) >= THRESHOLD and ("reveal",) not in world.fired:
        world.fired.add(("reveal",))
        child.memes["curiosity"] = child.memes.get("curiosity", 0.0) + 1
        child.memes["fear"] = max(0.0, child.memes.get("fear", 0.0) - 1)
        turban.meters["straightened"] = turban.meters.get("straightened", 0.0) + 1
        out.append(
            f"When {child.id} touched the soft edge of the {animal.label}, the mystery changed shape."
        )
    return out


def _r_problem_solve(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    parent = world.get("parent")
    turban = world.get("turban")
    animal = world.get("animal")
    if child.memes.get("startled", 0.0) >= THRESHOLD and ("solve",) not in world.fired:
        world.fired.add(("solve",))
        child.memes["brave"] = child.memes.get("brave", 0.0) + 1
        child.memes["calm"] = child.memes.get("calm", 0.0) + 1
        turban.meters["settled"] = turban.meters.get("settled", 0.0) + 1
        out.append(
            f"{parent.label.capitalize()} pointed out that the shadow was only the {animal.label}'s shape, "
            f"and the answer was simple once everyone looked closely."
        )
    return out


CAUSAL_RULES = [
    Rule("spook", _r_spook),
    Rule("touch_reveal", _r_touch_reveal),
    Rule("problem_solve", _r_problem_solve),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_touch(world: World) -> bool:
    sim = world.copy()
    child = sim.get("child")
    child.memes["touched"] = child.memes.get("touched", 0.0) + 1
    child.memes["startled"] = child.memes.get("startled", 0.0) + 1
    propagate(sim, narrate=False)
    return sim.get("child").memes.get("fear", 0.0) > 0


def tell(params: StoryParams) -> World:
    world = World(Setting())
    child = world.add(Entity(id="child", kind="character", type=params.gender, label=params.name))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=params.parent))
    animal = world.add(Entity(id="animal", kind="animal", type="goat", label=params.animal))
    turban = world.add(Entity(
        id="turban",
        type="turban",
        label="turban",
        phrase=f"a {params.turban_color} turban",
        owner=child.id,
    ))
    child.worn_turban = turban.id  # not serialized; just a story hint
    child.memes["unease"] = 1.0
    child.memes["fear"] = 1.0

    world.say(
        f"At the petting zoo, {child.id} wore {turban.phrase} and listened to the animals breathe softly."
    )
    world.say(
        f"The {world.setting.feels} air made the pens look like they held secrets."
    )

    world.para()
    world.say(
        f"{child.id} wanted to touch {animal.label}, but the hoof shadows looked strange in the straw."
    )
    if predict_touch(world):
        child.memes["startled"] = 1.0
        world.say(
            f"For a moment, {child.id} thought the {animal.label} might be a ghost in disguise."
        )
    child.memes["touched"] = child.memes.get("touched", 0.0) + 1
    child.memes["startled"] = child.memes.get("startled", 0.0) + 1
    world.say(f"{child.id} reached out carefully and touched the warm, fuzzy side of the {animal.label}.")
    propagate(world)

    world.para()
    world.say(
        f"Then the twist appeared: the eerie shape was only the {animal.label}'s shadow, wobbling on the fence."
    )
    world.say(
        f"{parent.label.capitalize()} laughed softly, and {child.id} laughed too."
    )
    world.say(
        f"With the mystery solved, the {turban.label} stayed neat, the zoo felt friendly again, and the night seemed less spooky."
    )

    world.facts.update(child=child, parent=parent, animal=animal, turban=turban)
    return world


SETTINGS = {"petting_zoo": Setting()}

ANIMALS = {
    "goat": "goat",
    "sheep": "sheep",
    "pony": "pony",
    "rabbit": "rabbit",
}

NAMES = {
    "girl": ["Mina", "Lena", "Nora", "Ivy", "Clara"],
    "boy": ["Owen", "Eli", "Noah", "Milo", "Finn"],
}

TURBAN_COLORS = ["blue", "red", "gold", "green", "white"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A ghost-story-like petting zoo tale with a twist.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--animal", choices=sorted(ANIMALS))
    ap.add_argument("--turban-color", choices=TURBAN_COLORS)
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
    gender = args.gender or rng.choice(["girl", "boy"])
    parent = args.parent or rng.choice(["mother", "father"])
    name = args.name or rng.choice(NAMES[gender])
    animal = args.animal or rng.choice(list(ANIMALS))
    turban_color = args.turban_color or rng.choice(TURBAN_COLORS)
    return StoryParams(name=name, gender=gender, parent=parent, animal=ANIMALS[animal], turban_color=turban_color)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short ghost-story-like tale set in a petting zoo that includes a turban and the word "touch".',
        f"Tell a child-friendly story where {f['child'].id} feels uneasy, reaches for the {f['animal'].label}, and discovers the scary thing was not real.",
        f"Write a simple story about a {f['child'].type} wearing a turban who solves a spooky problem at the petting zoo.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    animal = f["animal"]
    turban = f["turban"]
    return [
        QAItem(
            question=f"Where does {child.id}'s spooky little problem happen?",
            answer=f"It happens at the petting zoo, where the pens, straw, and shadows all make the place feel mysterious.",
        ),
        QAItem(
            question=f"What did {child.id} want to do with the {animal.label}?",
            answer=f"{child.id} wanted to touch the {animal.label}, even though it seemed a little eerie at first.",
        ),
        QAItem(
            question=f"What was {child.id} wearing?",
            answer=f"{child.id} was wearing {turban.phrase}, which stayed neat during the story.",
        ),
        QAItem(
            question=f"How was the problem solved?",
            answer=f"{parent.label.capitalize()} explained that the scary shape was only the {animal.label}'s shadow, so the mystery was solved by looking closely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a petting zoo?",
            answer="A petting zoo is a place where children can see gentle animals up close and sometimes touch them carefully.",
        ),
        QAItem(
            question="What is a turban?",
            answer="A turban is a cloth head covering that is wrapped around the head.",
        ),
        QAItem(
            question="What is a shadow?",
            answer="A shadow is a dark shape made when something blocks light.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story QA ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== world QA ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    lines.append(f"location={world.location}")
    return "\n".join(lines)


ASP_RULES = r"""
touched_reveal :- touched.
solved :- touched_reveal, shadow_only.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("setting", "petting_zoo"),
        asp.fact("shadow_only"),
        asp.fact("touchable", "animal"),
        asp.fact("wearable", "turban"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show solved/0. #show touched_reveal/0."))
    atoms = {a.name for a in model}
    expected = {"solved"}
    if atoms == expected:
        print("OK: ASP twin is consistent.")
        return 0
    print(f"Mismatch: {sorted(atoms)} != {sorted(expected)}")
    return 1


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
        print(asp_program("#show solved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(name="Mina", gender="girl", parent="mother", animal="goat", turban_color="blue"),
            StoryParams(name="Owen", gender="boy", parent="father", animal="sheep", turban_color="gold"),
            StoryParams(name="Lena", gender="girl", parent="mother", animal="pony", turban_color="green"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
