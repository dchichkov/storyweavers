#!/usr/bin/env python3
"""
A tiny bedtime-story world about a monk, an epiphany, and reconciliation.

The premise: a gentle monk prepares for sleep after a small hurt has left two
friends apart. During the quiet of bedtime, an inner monologue helps the monk
see the other side clearly, leading to a simple apology, forgiveness, and a
restful ending.

The world model tracks:
- physical meters: candlelight, footsteps, teacups, blankets, distance
- emotional memes: hurt, worry, kindness, regret, understanding, peace

The prose is generated from state changes, not from a frozen template.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"monk", "man", "boy", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"woman", "girl", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the monastery"
    bedtime: str = "late evening"


@dataclass
class StoryParams:
    place: str
    monk_name: str
    friend_name: str
    object_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


THRESHOLD = 1.0


def _add_mem(e: Entity, key: str, value: float = 1.0) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + value


def _add_meter(e: Entity, key: str, value: float = 1.0) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + value


def _monologue(world: World, monk: Entity, friend: Entity, object_ent: Entity) -> None:
    _add_mem(monk, "worry", 1)
    world.say(
        f"As the lamps grew soft, {monk.id} sat very still and listened to his own "
        f"inner monologue. He thought, '{friend.id} looked sad today, and I was not "
        f"gentle enough when I spoke about {object_ent.label}.'"
    )
    world.say(
        f"The quiet made the thought clearer and clearer, like a tiny bell ringing in the dark."
    )
    _add_mem(monk, "understanding", 1)


def _epiphany(world: World, monk: Entity, friend: Entity, object_ent: Entity) -> None:
    if monk.memes.get("understanding", 0.0) < THRESHOLD:
        return
    _add_mem(monk, "regret", 1)
    world.say(
        f"Then {monk.id} had an epiphany: the {object_ent.label} mattered, but kindness mattered more."
    )
    world.say(
        f"He realized {friend.id} had been trying to help all along."
    )


def _reconcile(world: World, monk: Entity, friend: Entity, object_ent: Entity) -> None:
    _add_mem(monk, "peace", 1)
    _add_mem(friend, "peace", 1)
    friend.meters["distance"] = 0
    monk.meters["distance"] = 0
    world.say(
        f"{monk.id} walked over with a bowed head and said sorry. "
        f"{friend.id} listened, and the hurt between them softened."
    )
    world.say(
        f"Together they agreed to share {object_ent.it()} carefully, and the room felt warm again."
    )
    world.say(
        f"At last, {friend.id} smiled, {monk.id} smiled back, and both of them were ready for sleep."
    )


def tell(setting: Setting, params: StoryParams) -> World:
    world = World(setting)
    monk = world.add(Entity(id=params.monk_name, kind="character", type="monk", label="monk"))
    friend = world.add(Entity(id=params.friend_name, kind="character", type="friend", label="friend"))
    obj = world.add(Entity(id=params.object_name, kind="thing", type="lantern", label="little lantern"))

    _add_meter(monk, "candlelight", 1)
    _add_meter(friend, "hurt", 1)
    _add_meter(monk, "distance", 2)
    _add_meter(friend, "distance", 2)

    world.say(
        f"At {setting.place}, in the soft bedtime hour, {monk.id} and {friend.id} stood by a small table."
    )
    world.say(
        f"{monk.id} had been thinking about {obj.label}, and {friend.id} had gone quiet after the little argument."
    )

    world.para()
    _monologue(world, monk, friend, obj)
    _epiphany(world, monk, friend, obj)

    world.para()
    _reconcile(world, monk, friend, obj)

    world.facts.update(monk=monk, friend=friend, object=obj, setting=setting)
    return world


SETTINGS = {
    "monastery": Setting(place="the monastery", bedtime="late evening"),
    "garden": Setting(place="the moonlit garden", bedtime="late evening"),
    "cell": Setting(place="the small candlelit cell", bedtime="bedtime"),
}

NAMES = ["Hugo", "Milo", "Soren", "Theo", "Arin", "Benedict", "Emil", "Niko"]
FRIEND_NAMES = ["Pip", "Rowan", "Tavi", "Lio", "Nell", "Sera", "Mira", "Jules"]
OBJECTS = ["lantern", "blanket", "cup", "book"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story for a young child about an epiphany and reconciliation at {f["setting"].place}.',
        f"Tell a gentle story where {f['monk'].id} has an inner monologue, then realizes a mistake and makes peace with {f['friend'].id}.",
        f"Write a cozy story about a monk, a small hurt, and a kind apology involving {f['object'].label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    monk, friend, obj = f["monk"], f["friend"], f["object"]
    return [
        QAItem(
            question=f"Why did {monk.id} think so hard before bedtime?",
            answer=f"{monk.id} used a quiet inner monologue and realized he had been unkind about {obj.label}.",
        ),
        QAItem(
            question=f"What was the monk's epiphany in the story?",
            answer=f"He saw that {obj.label} was not the most important thing; kindness and friendship were more important.",
        ),
        QAItem(
            question=f"How did {monk.id} and {friend.id} reconcile?",
            answer=f"{monk.id} said sorry, {friend.id} listened, and they decided to share {obj.it()} carefully.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an epiphany?",
            answer="An epiphany is a sudden clear understanding, like when a person suddenly sees the right answer or a better way to act.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet talking people do in their own minds when they are thinking.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people make peace again after a disagreement or hurt feelings.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: type={e.type} meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
% A monk is ready for reconciliation when understanding and regret are present.
ready_for_reconciliation(M) :- monk(M), understanding(M), regret(M).

% Reconciliation happens when the monk and friend both gain peace.
reconciled(M, F) :- ready_for_reconciliation(M), friend(F), peace(M), peace(F).

#show ready_for_reconciliation/1.
#show reconciled/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("monk", "monk"))
    lines.append(asp.fact("friend", "friend"))
    lines.append(asp.fact("object", "lantern"))
    lines.append(asp.fact("understanding", "monk"))
    lines.append(asp.fact("regret", "monk"))
    lines.append(asp.fact("peace", "monk"))
    lines.append(asp.fact("peace", "friend"))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    atoms = set(asp.atoms(model, "reconciled"))
    expected = {("monk", "friend")}
    if atoms == expected:
        print("OK: ASP parity verified.")
        return 0
    print(f"MISMATCH: {atoms} != {expected}")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world about a monk, an epiphany, and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--object")
    ap.add_argument("-n", type=int, default=1)
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
    monk_name = args.name or rng.choice(NAMES)
    friend_name = args.friend or rng.choice(FRIEND_NAMES)
    object_name = args.object or rng.choice(OBJECTS)
    if monk_name == friend_name:
        raise StoryError("The monk and the friend must be different people.")
    return StoryParams(place=place, monk_name=monk_name, friend_name=friend_name, object_name=object_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params)
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


CURATED = [
    StoryParams(place="monastery", monk_name="Hugo", friend_name="Pip", object_name="lantern"),
    StoryParams(place="garden", monk_name="Soren", friend_name="Mira", object_name="book"),
    StoryParams(place="cell", monk_name="Benedict", friend_name="Tavi", object_name="blanket"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print("ASP model:")
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
