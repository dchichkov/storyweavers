#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/memory_ize_turnip_persuade_misunderstanding_rhyming_story.py
=============================================================================================

A tiny, standalone story world for a rhyming misunderstanding tale:

- A child wants to memory-ize a turnip patch.
- A second child misunderstands the odd word.
- One child persuades the other with a calm, rhyming explanation.
- The ending proves the memory changed: a note, a rhyme, and a ready turnip.

This world is intentionally small and classical: typed entities, physical meters
and emotional memes, a forward-chained rule or two, a reasonableness gate, an
ASP twin, and story-grounded Q&A.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "aunt"}
        male = {"boy", "father", "dad", "man", "grandfather", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "grandmother": "grandma", "grandfather": "grandpa"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    quiet: bool = False
    earthy: bool = False


@dataclass
class ObjectThing:
    id: str
    label: str
    phrase: str
    edible: bool = False
    earthy: bool = False
    memorable: bool = True
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class Helper:
    id: str
    kind: str
    phrase: str
    rhyme: str
    sense: int
    calm: int
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_uneasy(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.memes["confused"] >= THRESHOLD and ("uneasy", e.id) not in world.fired:
            world.fired.add(("uneasy", e.id))
            e.memes["worry"] += 1
            out.append("__quiet__")
    return out


def _r_memory(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["labeled"] >= THRESHOLD and ("memory", e.id) not in world.fired:
            world.fired.add(("memory", e.id))
            e.memes["confidence"] += 1
            out.append("__memory__")
    return out


CAUSAL_RULES = [Rule("uneasy", "social", _r_uneasy), Rule("memory", "social", _r_memory)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonable(place: Place, item: ObjectThing, helper: Helper) -> bool:
    return place.quiet and item.memorable and helper.sense >= 2


def predict_misunderstanding(world: World, child: Entity, helper: Helper, item: ObjectThing) -> dict:
    sim = world.copy()
    _start_confusion(sim, sim.get(child.id), helper, item, narrate=False)
    return {
        "confused": sim.get(child.id).memes["confused"] >= THRESHOLD,
        "memory": sim.get("note").meters["labeled"] >= THRESHOLD,
    }


def _start_confusion(world: World, child: Entity, helper: Helper, item: ObjectThing, narrate: bool = True) -> None:
    child.memes["confused"] += 1
    child.memes["hope"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, child: Entity, friend: Entity, place: Place, item: ObjectThing) -> None:
    world.say(
        f"On a quiet day at {place.label}, {child.id} and {friend.id} went for a walk. "
        f"They found {item.phrase} by the green row."
    )
    world.say(
        f"{child.id} smiled and said, 'I want to memory-ize this turnip so I can keep its tune.'"
    )


def misunderstand(world: World, friend: Entity, child: Entity, item: ObjectThing) -> None:
    friend.memes["confused"] += 1
    world.say(
        f"{friend.id} blinked and frowned. 'Memory-ize? Do you mean hide the turnip in a box?' "
        f"{friend.pronoun().capitalize()} had the wrong idea and looked quite cross."
    )


def persuade(world: World, child: Entity, friend: Entity, helper: Helper, item: ObjectThing) -> None:
    child.memes["kindness"] += 1
    child.memes["determination"] += 1
    world.say(
        f"{child.id} took a breath and tried to persuade {friend.id}. "
        f"'{helper.rhyme}' {child.id} sang. 'It means to keep it in your mind, not to make it disappear behind.'"
    )
    world.say(
        f"{child.id} pointed to {item.label} and tapped a note book with a grin, to make the meaning clear and thin."
    )


def resolve(world: World, child: Entity, friend: Entity, item: ObjectThing, helper: Helper) -> None:
    item.meters["labeled"] += 1
    note = world.get("note")
    note.meters["labeled"] += 1
    child.memes["joy"] += 1
    friend.memes["relief"] += 1
    friend.memes["confidence"] += 1
    world.say(
        f"Then {friend.id} nodded and laughed, because the mistake was only a small old daft. "
        f"They wrote a label on a note for the turnip's shelf, so nobody would wonder by themselves."
    )
    world.say(
        f"Now the turnip had a rhyming tag, and the friends could remember it with a happy wag."
    )


def tell(place: Place, item: ObjectThing, helper: Helper, child_name: str = "Mina", child_type: str = "girl",
         friend_name: str = "Jasper", friend_type: str = "boy") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="persuader"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, role="misreader"))
    world.add(Entity(id="note", kind="thing", type="note", label="note"))
    world.add(Entity(id="basket", kind="thing", type="basket", label="basket"))
    world.facts["place"] = place
    world.facts["item_cfg"] = item
    world.facts["helper"] = helper

    introduce(world, child, friend, place, item)
    world.para()
    misunderstand(world, friend, child, item)
    predict = predict_misunderstanding(world, child, helper, item)
    world.facts["predicted"] = predict
    world.para()
    persuade(world, child, friend, helper, item)
    if predict["confused"]:
        resolve(world, child, friend, item, helper)

    world.facts.update(child=child, friend=friend, item=world.get("basket"), outcome="resolved")
    return world


PLACES = {
    "garden": Place("garden", "the garden", quiet=True, earthy=True),
    "farm": Place("farm", "the little farm", quiet=True, earthy=True),
    "yard": Place("yard", "the yard", quiet=True, earthy=True),
}

ITEMS = {
    "turnip": ObjectThing("turnip", "turnip", "a round white turnip", earthy=True, memorable=True),
    "big_turnip": ObjectThing("big_turnip", "turnip", "a big fat turnip", earthy=True, memorable=True),
}

HELPERS = {
    "rhyme": Helper("rhyme", "rhyme", "memory-ize means keep it in your mind", "Keep it in mind, not out of sight; a word can be a memory-light.", 3, 3, {"rhyme", "memory-ize", "persuade"}),
    "note": Helper("note", "note", "write a note so the turnip stays bright", "Write it down, and you'll remember; keep the idea warm like ember.", 2, 4, {"note", "memory-ize", "persuade"}),
}


@dataclass
class StoryParams:
    place: str
    item: str
    helper: str
    child_name: str
    child_gender: str
    friend_name: str
    friend_gender: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, i, h) for p in PLACES for i in ITEMS for h in HELPERS if reasonable(PLACES[p], ITEMS[i], HELPERS[h])]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story for a young child that uses the words "memory-ize", "turnip", and "persuade".',
        f"Tell a gentle misunderstanding story set at {f['place'].label} where one child says memory-ize and another child takes it the wrong way, then they persuade each other with a rhyme.",
        f"Write a small rhyming tale about a turnip and a label, with a misunderstanding that gets fixed kindly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    place = f["place"]
    item = f["item_cfg"]
    helper = f["helper"]
    return [
        QAItem(
            question="What did the child want to do with the turnip?",
            answer=f"{child.id} wanted to memory-ize the turnip, which meant to keep it in {child.pronoun('possessive')} mind. {child.id} wanted to remember it clearly, not lose it."
        ),
        QAItem(
            question="What was the misunderstanding?",
            answer=f"{friend.id} thought memory-ize meant to hide the turnip in a box. That was the wrong idea, so {friend.id} needed a kinder explanation."
        ),
        QAItem(
            question="How did they fix the confusion?",
            answer=f"{child.id} persuaded {friend.id} with a rhyme and then they wrote a label on a note. That made the meaning clear and helped everyone remember the turnip."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a turnip?",
            answer="A turnip is a round root vegetable that grows under the ground. People can cook it or keep it in a basket after picking it."
        ),
        QAItem(
            question="What does persuade mean?",
            answer="To persuade means to help someone change their mind by giving a good reason or saying something kindly. A calm voice and a clear idea can do it."
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks a word or idea means the wrong thing. Talking it through can fix the mix-up."
        ),
        QAItem(
            question="What does it mean to remember something?",
            answer="Remembering means keeping an idea in your mind so you can think of it again later. Notes, labels, and rhymes can help."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, _ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("garden", "turnip", "rhyme", "Mina", "girl", "Jasper", "boy"),
    StoryParams("farm", "big_turnip", "note", "Lila", "girl", "Owen", "boy"),
]


def explain_rejection(place: Place, item: ObjectThing, helper: Helper) -> str:
    if not reasonable(place, item, helper):
        return "(No story: the setup is not calm or the helper is too weak for a good persuasion tale.)"
    return "(No story: this combination is not available.)"


ASP_RULES = r"""
valid(P, I, H) :- place(P), item(I), helper(H), quiet(P), memorable(I), sense(H, S), S >= min_sense.
misunderstanding(P, I) :- valid(P, I, H).
resolved(P, I, H) :- valid(P, I, H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.quiet:
            lines.append(asp.fact("quiet", pid))
    for iid, i in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if i.memorable:
            lines.append(asp.fact("memorable", iid))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("sense", hid, h.sense))
    lines.append(asp.fact("min_sense", 2))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python valid_combos() differ.")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    if rc == 0:
        print(f"OK: ASP matches Python and generation works ({len(valid_combos())} combos).")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny rhyming misunderstanding storyworld with a turnip and persuasion.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.item is None or c[1] == args.item)
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, item, helper = rng.choice(combos)
    return StoryParams(
        place=place,
        item=item,
        helper=helper,
        child_name=args.child_name or rng.choice(["Mina", "Lila", "Nia", "Pip"]),
        child_gender=args.child_gender or rng.choice(["girl", "boy"]),
        friend_name=args.friend_name or rng.choice(["Jasper", "Owen", "Toby", "Noah"]),
        friend_gender=args.friend_gender or rng.choice(["boy", "girl"]),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], ITEMS[params.item], HELPERS[params.helper],
                 params.child_name, params.child_gender,
                 params.friend_name, params.friend_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q.question, q.answer) for q in story_qa(world)],
        world_qa=[QAItem(q.question, q.answer) for q in world_knowledge_qa(world)],
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
        print("\n".join(f"{a} {b} {c}" for a, b, c in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
