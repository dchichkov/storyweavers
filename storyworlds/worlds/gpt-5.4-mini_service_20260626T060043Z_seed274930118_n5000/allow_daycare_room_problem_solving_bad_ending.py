#!/usr/bin/env python3
"""
A small mythic story world set in a daycare room.

Premise:
- A child wants to use or carry something in the daycare room.
- A guardian must decide whether to allow it.

Tension:
- The child's wish may break a rule, cause a mess, or disturb the room.
- A problem-solving attempt can repair the situation.

Outcomes:
- Happy ending: the guardian allows the child after a sensible fix.
- Bad ending: the guardian refuses, the child cannot make the desired change,
  and the room remains unsettled.

This world is intentionally small and constraint-checked. It models one concrete
daycare-room problem-solving tale in a mythic, child-facing tone.
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

ROOMS = {
    "daycare_room": {
        "name": "the daycare room",
        "features": {"blocks", "paint", "snack_table", "blankets"},
    }
}

ACTIONS = {
    "tower": {
        "verb": "build a tower",
        "gerund": "building towers",
        "risk": "topple",
        "problem": "the blocks could crash into the snack table",
        "fix": "move the blocks to the soft rug",
        "mess": "scattered",
        "zone": {"floor"},
        "keyword": "blocks",
        "tag": "blocks",
    },
    "paint": {
        "verb": "paint a picture",
        "gerund": "painting bright pictures",
        "risk": "smear",
        "problem": "the paint could splatter onto the blankets",
        "fix": "spread a big cloth over the table",
        "mess": "painted",
        "zone": {"table", "hands"},
        "keyword": "paint",
        "tag": "paint",
    },
    "snack": {
        "verb": "share a snack",
        "gerund": "sharing snacks",
        "risk": "spill",
        "problem": "the crumbs could fall onto the clean rug",
        "fix": "use a tray and sit at the snack table",
        "mess": "crumbed",
        "zone": {"table"},
        "keyword": "snack",
        "tag": "snack",
    },
    "blanket_fort": {
        "verb": "make a blanket fort",
        "gerund": "making blanket forts",
        "risk": "tangle",
        "problem": "the blankets could block the doorway",
        "fix": "tie the corners to the low chairs",
        "mess": "tangled",
        "zone": {"floor", "chairs"},
        "keyword": "blankets",
        "tag": "blankets",
    },
}

GUARDS = {
    "mat": {
        "label": "a soft mat",
        "covers": {"floor"},
        "guards": {"scattered"},
        "prep": "lay down a soft mat first",
        "tail": "laid down a soft mat",
        "plural": False,
    },
    "cloth": {
        "label": "a big cloth",
        "covers": {"table"},
        "guards": {"painted"},
        "prep": "spread a big cloth over the table",
        "tail": "spread a big cloth over the table",
        "plural": False,
    },
    "tray": {
        "label": "a bright tray",
        "covers": {"table"},
        "guards": {"crumbed"},
        "prep": "set out a bright tray first",
        "tail": "set out a bright tray",
        "plural": False,
    },
    "chair_ties": {
        "label": "low chair ties",
        "covers": {"floor", "chairs"},
        "guards": {"tangled"},
        "prep": "tie the corners to the low chairs",
        "tail": "tied the corners to the low chairs",
        "plural": True,
    },
}

CHILD_NAMES = ["Mina", "Tobi", "Lio", "Ari", "Nia", "Sora", "Zuri", "Pip"]
GUARDIAN_NAMES = ["the teacher", "the grown-up", "the caregiver"]

TRAITS = ["curious", "bold", "gentle", "bright", "restless", "patient"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


def legal_action(action: str) -> bool:
    return action in ACTIONS


def valid_combo(action: str, ending: str) -> bool:
    if ending not in {"happy", "bad"}:
        return False
    return legal_action(action)


def valid_combos() -> list[tuple[str, str]]:
    return [(a, e) for a in ACTIONS for e in ("happy", "bad")]


def choose_guard(action: str) -> Optional[dict]:
    risk = ACTIONS[action]["risk"]
    for g in GUARDS.values():
        if risk in g["guards"]:
            return g
    return None


def predict_problem(world: World, child: Entity, action: str) -> bool:
    return action in ACTIONS and choose_guard(action) is not None


def tell(world: World, child_name: str, guardian_label: str, action: str, ending: str) -> World:
    if not valid_combo(action, ending):
        raise StoryError("The requested daycare-room story cannot be told for that combination.")

    child = world.add(Entity(
        id=child_name,
        kind="character",
        type="girl" if child_name in {"Mina", "Nia", "Zuri"} else "boy",
        traits=["little", random.choice(TRAITS)],
    ))
    guardian = world.add(Entity(
        id="guardian",
        kind="character",
        type="adult",
        label=guardian_label,
    ))
    room = ROOMS["daycare_room"]["name"]
    act = ACTIONS[action]

    child.memes["want"] = 1
    world.say(
        f"In {room}, {child.id} was a little {child.traits[1]} child who loved {act['gerund']}."
    )
    world.say(
        f"The room held blocks, paint, snacks, and blankets, like treasures in a small temple."
    )

    world.para()
    world.say(
        f"One day, {child.id} wanted to {act['verb']} right away."
    )
    world.say(
        f"But {guardian.label} looked at the room and said, \"I cannot allow that yet.\""
    )
    world.say(
        f"{guardian.label.capitalize()} feared that {act['problem']}."
    )

    world.para()
    if ending == "happy":
        guard = choose_guard(action)
        if guard is None:
            raise StoryError("No sensible guard exists for this action.")
        child.memes["hope"] = 1
        world.say(
            f"{child.id} thought hard and helped solve the problem."
        )
        world.say(
            f"Together they chose to {guard['prep']}, and that made the room safe."
        )
        world.say(
            f"Then {guardian.label} smiled and said, \"Now I can allow it.\""
        )
        world.say(
            f"So {child.id} got to {act['verb']}, and the daycare room stayed calm and bright."
        )
        world.facts["resolved"] = True
        world.facts["guard"] = guard["label"]
    else:
        child.memes["frustration"] = 1
        world.say(
            f"{child.id} tried to fix it in a hurry, but the problem stayed larger than little hands."
        )
        world.say(
            f"At last {guardian.label} stayed firm and did not allow it."
        )
        world.say(
            f"So {child.id} could not {act['verb']}, and the room kept its worry like a cloud at the ceiling."
        )
        world.facts["resolved"] = False

    world.facts.update(
        child=child,
        guardian=guardian,
        action=act,
        ending=ending,
        room=room,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    act = f["action"]
    return [
        f'Write a short mythic story set in a daycare room about a child who wants to {act["verb"]} and must ask to be allowed.',
        f'Tell a gentle myth where a grown-up in the daycare room says "allow" only after the child solves the problem.',
        f'Write a child-facing story about {act["keyword"]} in the daycare room with a clear problem-solving ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    guardian = f["guardian"]
    act = f["action"]
    room = f["room"]
    qas = [
        QAItem(
            question=f"Where does the story happen?",
            answer=f"It happens in {room}, where the child and guardian are trying to keep things safe.",
        ),
        QAItem(
            question=f"What did {child.id} want to do?",
            answer=f"{child.id} wanted to {act['verb']}.",
        ),
        QAItem(
            question=f"Why did {guardian.label} hesitate to allow it?",
            answer=f"{guardian.label} worried that {act['problem']}.",
        ),
    ]
    if f["ending"] == "happy":
        qas.append(QAItem(
            question="How did the child solve the problem?",
            answer=f"The child helped with a simple fix: {f['guard']}. That made the daycare room safe enough to allow the plan.",
        ))
    else:
        qas.append(QAItem(
            question="How did the story end?",
            answer=f"It ended with a bad ending. The guardian did not allow the action, so the child could not finish the wish.",
        ))
    return qas


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    act = f["action"]
    return [
        QAItem(
            question="What is a daycare room?",
            answer="A daycare room is a place where young children play, rest, and learn with help from a caregiver.",
        ),
        QAItem(
            question="Why do grown-ups sometimes say no in a daycare room?",
            answer="Grown-ups may say no to keep children safe, keep the room tidy, and help everyone share the space fairly.",
        ),
        QAItem(
            question=f"What is a {act['keyword']}?",
            answer=f"A {act['keyword']} is one of the things that belongs in the daycare room story world, used for play or care.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Story prompts =="]
    for p in sample.prompts:
        parts.append(f"- {p}")
    parts.append("")
    parts.append("== Story Q&A ==")
    for qa in sample.story_qa:
        parts.append(f"Q: {qa.question}")
        parts.append(f"A: {qa.answer}")
    parts.append("")
    parts.append("== World Q&A ==")
    for qa in sample.world_qa:
        parts.append(f"Q: {qa.question}")
        parts.append(f"A: {qa.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: type={e.type} traits={e.traits} meters={e.meters} memes={e.memes}"
        )
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


@dataclass
class StoryParams:
    action: str
    ending: str
    child: str
    guardian: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(action="tower", ending="happy", child="Mina", guardian="the teacher"),
    StoryParams(action="paint", ending="happy", child="Lio", guardian="the caregiver"),
    StoryParams(action="snack", ending="bad", child="Ari", guardian="the grown-up"),
    StoryParams(action="blanket_fort", ending="happy", child="Nia", guardian="the teacher"),
    StoryParams(action="tower", ending="bad", child="Tobi", guardian="the caregiver"),
]


ASP_RULES = r"""
valid_action(A) :- action(A).
valid_ending(E) :- ending(E).
valid_combo(A,E) :- valid_action(A), valid_ending(E).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for a in ACTIONS:
        lines.append(asp.fact("action", a))
    for e in ("happy", "bad"):
        lines.append(asp.fact("ending", e))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/2."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("Mismatch between ASP and Python.")
    if py - cl:
        print("Only in Python:", sorted(py - cl))
    if cl - py:
        print("Only in ASP:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic daycare-room story world.")
    ap.add_argument("--action", choices=sorted(ACTIONS))
    ap.add_argument("--ending", choices=["happy", "bad"])
    ap.add_argument("--child", choices=CHILD_NAMES)
    ap.add_argument("--guardian", choices=GUARDIAN_NAMES)
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
    action = args.action or rng.choice(sorted(ACTIONS))
    ending = args.ending or rng.choice(["happy", "bad"])
    if not valid_combo(action, ending):
        raise StoryError("Invalid daycare-room story combination.")
    child = args.child or rng.choice(CHILD_NAMES)
    guardian = args.guardian or rng.choice(GUARDIAN_NAMES)
    return StoryParams(action=action, ending=ending, child=child, guardian=guardian)


def generate(params: StoryParams) -> StorySample:
    world = World("daycare_room")
    tell(world, params.child, params.guardian, params.action, params.ending)
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
        print(asp_program("#show valid_combo/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for combo in combos:
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, p in enumerate(CURATED):
            p.seed = base_seed + i
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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
            header = f"### {p.child}: {p.action} ({p.ending})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
