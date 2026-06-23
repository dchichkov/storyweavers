#!/usr/bin/env python3
"""
storyworlds/worlds/doozy_conflict_flashback_kindness_slice_of_life.py
====================================================================

A small slice-of-life storyworld about a little everyday doozy:
a child and a friend clash over a shared job, remember a helpful moment,
and solve the problem with kindness.

The world keeps typed entities with physical meters and emotional memes,
runs a tiny forward causal model, exposes three Q&A sets, and mirrors the
reasonableness gate in inline ASP rules.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
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
    role: str = ""
    owner: str = ""
    helper: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    details: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    conflict_word: str
    flashback_word: str
    kindness_word: str
    at_risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SharedItem:
    id: str
    label: str
    phrase: str
    type: str
    cautious: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.items: dict[str, SharedItem] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add_entity(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_item(self, item: SharedItem) -> SharedItem:
        self.items[item.id] = item
        return item

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


def story_doze() -> str:
    return "the whole thing had turned into a doozy"


def valid_task_item(task: Task, item: SharedItem) -> bool:
    return item.label in task.at_risk or item.type in task.tags


def _r_tension(world: World) -> list[str]:
    out: list[str] = []
    a = world.get("child")
    b = world.get("friend")
    if a.memes.get("argument", 0) < THRESHOLD or b.memes.get("argument", 0) < THRESHOLD:
        return out
    sig = ("tension",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    a.memes["conflict"] = a.memes.get("conflict", 0) + 1
    b.memes["conflict"] = b.memes.get("conflict", 0) + 1
    out.append("The room felt tight and quiet for a moment.")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    a = world.get("child")
    b = world.get("friend")
    if a.memes.get("kindness", 0) < THRESHOLD:
        return out
    sig = ("kindness",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    a.memes["conflict"] = 0
    b.memes["conflict"] = 0
    a.memes["joy"] = a.memes.get("joy", 0) + 1
    b.memes["joy"] = b.memes.get("joy", 0) + 1
    out.append("Kindness made the argument smaller.")
    return out


CAUSAL_RULES = [_r_tension, _r_kindness]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_hurt(world: World, task: Task, item: SharedItem) -> dict:
    sim = World(world.place)
    sim.entities = {k: Entity(**asdict(v)) for k, v in world.entities.items()}
    sim.items = {k: SharedItem(**asdict(v)) for k, v in world.items.items()}
    sim.fired = set(world.fired)
    sim.get("child").memes["argument"] = 1
    sim.get("friend").memes["argument"] = 1
    if valid_task_item(task, item):
        sim.items[item.id].meters["used"] = sim.items[item.id].meters.get("used", 0) + 1
    return {
        "conflict": True,
        "item_used": bool(valid_task_item(task, item)),
    }


def tell(place: Place, task: Task, item: SharedItem,
         child_name: str = "Mina", child_gender: str = "girl",
         friend_name: str = "Jules", friend_gender: str = "boy") -> World:
    world = World(place)
    child = world.add_entity(Entity(
        id="child", kind="character", type=child_gender, label=child_name,
        role="main", meters={"busy": 0.0}, memes={"joy": 1.0, "conflict": 0.0},
        attrs={"name": child_name},
    ))
    friend = world.add_entity(Entity(
        id="friend", kind="character", type=friend_gender, label=friend_name,
        role="helper", meters={"busy": 0.0}, memes={"joy": 1.0, "conflict": 0.0},
        attrs={"name": friend_name},
    ))
    shared = world.add_item(item)

    child.memes["kindness"] = 0.0
    child.memes["argument"] = 0.0
    friend.memes["argument"] = 0.0
    child.memes["memory"] = 0.0
    friend.memes["memory"] = 0.0

    world.say(f"{child_name} and {friend_name} met at {place.label}.")
    world.say(f"{place.details} It was a small day, but {story_doze()}.")

    world.para()
    world.say(
        f"They were supposed to {task.verb} together with {shared.phrase}, "
        f"but they both wanted to hold it first."
    )
    child.memes["argument"] += 1
    friend.memes["argument"] += 1
    child.meters["stubborn"] = child.meters.get("stubborn", 0) + 1
    friend.meters["stubborn"] = friend.meters.get("stubborn", 0) + 1
    propagate(world)

    world.para()
    flash = predict_hurt(world, task, shared)
    if flash["conflict"]:
        world.say(
            f"{child_name} paused and remembered a flashback: last week, "
            f"{friend_name} had let {child_name} borrow the same {shared.label} "
            f"when {child_name} felt left out."
        )
        child.memes["memory"] += 1
        child.memes["kindness"] += 1
        world.say(
            f"That memory changed {child_name}'s face. {child_name} said, "
            f"\"You can use it first.\""
        )
        world.say(
            f"{child_name} handed over {shared.phrase} and helped {friend_name} "
            f"{task.gerund} by the table."
        )
        shared.meters["used"] = shared.meters.get("used", 0) + 1
        shared.memes["shared"] = shared.memes.get("shared", 0) + 1
        propagate(world)
        world.para()
        world.say(
            f"In the end, they finished the little job together, "
            f"and the doozy turned into an easy laugh."
        )
        world.say(
            f"{child_name} and {friend_name} left with clean hands, calm hearts, "
            f"and the nice feeling that kindness had helped."
        )

    world.facts.update(
        child=child, friend=friend, item=shared, task=task, place=place,
        resolved=True, flashback=True, kind=True
    )
    return world


SETTINGS = {
    "kitchen": Place(
        id="kitchen",
        label="the kitchen table",
        details="Sunlight was on the floor, and a bowl of fruit sat near the window.",
        affords={"task"},
    ),
    "laundry": Place(
        id="laundry",
        label="the laundry room",
        details="The soft hum of the washer filled the room, and folded towels waited in a neat stack.",
        affords={"task"},
    ),
    "porch": Place(
        id="porch",
        label="the front porch",
        details="A warm breeze moved the leaves, and two shoes sat by the door.",
        affords={"task"},
    ),
}

TASKS = {
    "sort": Task(
        id="sort",
        verb="sort",
        gerund="sorting the crayons",
        conflict_word="argument",
        flashback_word="flashback",
        kindness_word="kindness",
        at_risk="crayons",
        tags={"crayons"},
    ),
    "fold": Task(
        id="fold",
        verb="fold",
        gerund="folding the towels",
        conflict_word="argument",
        flashback_word="flashback",
        kindness_word="kindness",
        at_risk="towels",
        tags={"towels"},
    ),
    "paint": Task(
        id="paint",
        verb="paint",
        gerund="painting the sign",
        conflict_word="argument",
        flashback_word="flashback",
        kindness_word="kindness",
        at_risk="sign",
        tags={"sign"},
    ),
}

ITEMS = {
    "crayons": SharedItem(id="crayons", label="crayons", phrase="a box of crayons", type="crayons"),
    "towels": SharedItem(id="towels", label="towels", phrase="a stack of towels", type="towels"),
    "sign": SharedItem(id="sign", label="sign", phrase="a cardboard sign", type="sign"),
}

NAMES = ["Mina", "Lila", "Nora", "Jules", "Owen", "Pip", "Tess", "Kai"]
TRAITS = ["careful", "kind", "quiet", "gentle"]


@dataclass
class StoryParams:
    place: str
    task: str
    item: str
    child_name: str
    child_gender: str
    friend_name: str
    friend_gender: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(place="kitchen", task="sort", item="crayons", child_name="Mina", child_gender="girl",
                friend_name="Jules", friend_gender="boy", trait="kind"),
    StoryParams(place="laundry", task="fold", item="towels", child_name="Lila", child_gender="girl",
                friend_name="Owen", friend_gender="boy", trait="gentle"),
    StoryParams(place="porch", task="paint", item="sign", child_name="Kai", child_gender="boy",
                friend_name="Tess", friend_gender="girl", trait="quiet"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pid, place in SETTINGS.items():
        for tid, task in TASKS.items():
            for iid, item in ITEMS.items():
                if valid_task_item(task, item):
                    out.append((pid, tid, iid))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    c, fr, task, item, place = f["child"], f["friend"], f["task"], f["item"], f["place"]
    return [
        f'Write a small slice-of-life story about {c.label} and {fr.label} at {place.label} where a shared chore turns into a doozy.',
        f"Tell a story where {c.label} and {fr.label} both want to use {item.phrase}, then remember a past kindness and solve the conflict gently.",
        f'Write a child-friendly story that includes a flashback and ends with kindness at {place.label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c, fr, task, item, place = f["child"], f["friend"], f["task"], f["item"], f["place"]
    return [
        QAItem(
            question=f"Where did {c.label} and {fr.label} meet?",
            answer=f"They met at {place.label}. It was an ordinary place, which fits the slice-of-life feeling of the story.",
        ),
        QAItem(
            question=f"What made the job a doozy?",
            answer=f"They both wanted to hold {item.phrase} first, so the shared chore turned into a little conflict. That made the moment feel like a doozy before kindness fixed it.",
        ),
        QAItem(
            question=f"What did {c.label} remember before acting kindly?",
            answer=f"{c.label} remembered that {fr.label} had once let {c.label} borrow the same thing. That flashback helped {c.label} choose kindness instead of keeping the argument going.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {c.label} and {fr.label} finishing the job together and feeling calm. The kindness changed the mood and made the ending warm and peaceful.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a short memory of something that happened earlier. It helps explain why a character feels a certain way now.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness is when someone chooses to help, share, or be gentle with another person. It can calm a conflict and make a hard moment better.",
        ),
        QAItem(
            question="What does doozy mean here?",
            answer="Here, doozy means a tricky or surprising situation. It is still a small everyday moment, just one that feels extra hard for a little while.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    parts.extend(f"- {p}" for p in sample.prompts)
    parts.append("")
    parts.append("== story qa ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== world qa ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: meters={e.meters} memes={e.memes} attrs={e.attrs}")
    for i in world.items.values():
        lines.append(f"  {i.id}: meters={i.meters} memes={i.memes}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
conflict :- argument(child), argument(friend).
kindness :- kind(child).
valid(P,T,I) :- place(P), task(T), item(I), valid_task(T,I).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("valid_task", tid, t.at_risk))
    for iid, i in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("label", iid, i.label))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = True
    if set(asp_valid_combos()) != set(valid_combos()):
        ok = False
        print("MISMATCH: ASP and Python valid_combos differ.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as exc:
        ok = False
        print(f"MISMATCH: generate smoke test failed: {exc}")
    if ok:
        print("OK: ASP parity and generate smoke test passed.")
        return 0
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld with conflict, flashback, and kindness.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.task is None or c[1] == args.task)
              and (args.item is None or c[2] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, task, item = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if child_gender == "girl" else "girl")
    child_name = args.child_name or rng.choice(NAMES)
    friend_name = args.friend_name or rng.choice([n for n in NAMES if n != child_name])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, task=task, item=item, child_name=child_name,
                       child_gender=child_gender, friend_name=friend_name,
                       friend_gender=friend_gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    place = SETTINGS[params.place]
    task = TASKS[params.task]
    item = ITEMS[params.item]
    world = tell(place, task, item, params.child_name, params.child_gender, params.friend_name, params.friend_gender)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
