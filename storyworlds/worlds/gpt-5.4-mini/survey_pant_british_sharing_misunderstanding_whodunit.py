#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/survey_pant_british_sharing_misunderstanding_whodunit.py
=========================================================================================

A standalone storyworld for a small whodunit-style domestic mystery about a
missing shared item, a misunderstanding, and a careful survey that reveals the
truth. The seed words are woven into the premise:
- survey: the children inspect the room and ask questions like a detective
- pant: an anxious breath or a clothing item in the mystery
- british: a British guest, clue, or expression that shapes the misunderstanding

The world is built to produce short, complete, child-facing mystery stories with
a beginning, clue-gathering middle, and a reveal that resolves the confusion.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"missing": 0.0, "clue": 0.0, "worry": 0.0, "relief": 0.0, "embarrassment": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "curiosity": 0.0, "relief": 0.0, "trust": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mum", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    survey_target: str
    clue_style: str
    ending_image: str


@dataclass
class Person:
    id: str
    type: str
    label: str
    role: str
    voice: str
    relation: str = ""


@dataclass
class SharedItem:
    id: str
    label: str
    phrase: str
    owner: str
    shared_with: list[str]
    place: str
    found_by_survey: bool = True
    prone_to_misunderstanding: bool = True


@dataclass
class ClueObject:
    id: str
    label: str
    phrase: str
    clue_text: str
    british_tinge: bool = False
    meters: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"noticed": 0.0}


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_clue(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["clue"] < THRESHOLD:
            continue
        sig = ("clue", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append("__clue__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("revealed") and ("relief", "family") not in world.fired:
        world.fired.add(("relief", "family"))
        for e in world.entities.values():
            if e.kind == "character":
                e.memes["relief"] += 1
        out.append("__relief__")
    return out


CAUSAL_RULES = [Rule("clue", "social", _r_clue), Rule("relief", "social", _r_relief)]


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


def survey_scene(world: World, detective: Entity, setting: Setting) -> None:
    detective.memes["curiosity"] += 1
    world.say(
        f"On a bright morning, {detective.id} decided to survey the room like a "
        f"proper detective. The {setting.place} looked ordinary at first, but the air "
        f"felt a little too quiet."
    )


def missing_item(world: World, keeper: Entity, item: SharedItem) -> None:
    keeper.meters["missing"] += 1
    keeper.memes["worry"] += 1
    world.say(
        f'"Where is {item.phrase}?" {keeper.id} asked, starting to pant with worry. '
        f'"It was right here before breakfast."'
    )


def misunderstood_comment(world: World, speaker: Entity, listener: Entity, item: SharedItem) -> None:
    speaker.meters["clue"] += 1
    listener.memes["worry"] += 1
    world.say(
        f"{speaker.id} pointed at a small note and said, "
        f'"That is a British clue."'
    )
    world.say(
        f"{listener.id} heard only part of it and frowned. "
        f'"British? Then someone from far away took {item.phrase}?"'
    )
    world.say(
        "That was not the right meaning at all, but the misunderstanding made the "
        "mystery feel bigger."
    )


def gather_clues(world: World, detective: Entity, clue: ClueObject, item: SharedItem) -> None:
    clue.meters["noticed"] += 1
    world.say(
        f"{detective.id} walked slowly around the desk, checked under the chair, and "
        f"surveyed the little marks on the floor. One clue was a tiny teacup picture; "
        f"another was a note that said {clue.phrase}."
    )
    if clue.british_tinge:
        world.say(
            f"The note sounded British, which explained the odd wording without making "
            f"the story strange."
        )
    world.say(
        f"Then {detective.id} noticed that {item.phrase} was not stolen at all."
    )


def reveal(world: World, detective: Entity, owner: Entity, sharer: Entity, item: SharedItem) -> None:
    world.facts["revealed"] = True
    item_mis = "shared by mistake" if item.prone_to_misunderstanding else "moved for a good reason"
    world.say(
        f"{detective.id} smiled and solved the puzzle. {item.phrase} had been {item_mis}: "
        f"{sharer.id} had borrowed it to share with {owner.id}, then set it in a new place "
        f"so it would be ready for later."
    )
    world.say(
        f"{owner.id} blinked, then laughed. " 
        f'"Oh! I thought it was gone."'
    )
    world.say(
        f"{sharer.id} patted the pocket and held up the missing thing. "
        f'"I only moved it because I was sharing it."'
    )
    propagate(world, narrate=False)


def ending(world: World, detective: Entity, owner: Entity, item: SharedItem, setting: Setting) -> None:
    world.say(
        f"In the end, everyone stood together in {setting.place}, and the mystery was "
        f"small again. The shared {item.label} was back where all of them could see it, "
        f"and the day felt calm and clever."
    )
    world.say(setting.ending_image)


def tell(setting: Setting, detective_name: str, detective_type: str,
         owner_name: str, owner_type: str, sharer_name: str, sharer_type: str,
         item: SharedItem, clue: ClueObject) -> World:
    world = World(setting)
    detective = world.add(Entity(detective_name, "character", detective_type, label="the detective", role="detective"))
    owner = world.add(Entity(owner_name, "character", owner_type, label="the owner", role="owner"))
    sharer = world.add(Entity(sharer_name, "character", sharer_type, label="the sharer", role="sharer"))
    world.add(Entity("room", "room", "room", label=setting.place))
    world.facts.update(detective=detective, owner=owner, sharer=sharer, item=item, clue=clue, setting=setting)

    survey_scene(world, detective, setting)
    world.para()
    missing_item(world, owner, item)
    misunderstood_comment(world, sharer, owner, item)
    world.para()
    gather_clues(world, detective, clue, item)
    reveal(world, detective, owner, sharer, item)
    world.para()
    ending(world, detective, owner, item, setting)
    return world


SETTINGS = {
    "kitchen": Setting("kitchen", "the kitchen", "counter", "a tea-note clue", "The kettle gave a soft little sigh beside the window."),
    "hall": Setting("hall", "the hallway", "hooks", "a label clue", "The front mat sat straight again like nothing had happened."),
    "study": Setting("study", "the study", "desk", "a paper clue", "The lamp glowed warmly over the tidy desk."),
    "parlour": Setting("parlour", "the parlour", "sideboard", "a postcard clue", "The curtains swayed gently, and everything felt solved."),
}

ITEMS = {
    "pants": SharedItem("pants", "trousers", "the trousers", owner="owner", shared_with=["sharer"], place="chair"),
    "coat": SharedItem("coat", "coat", "the coat", owner="owner", shared_with=["sharer"], place="hook"),
    "book": SharedItem("book", "book", "the library book", owner="owner", shared_with=["sharer"], place="table"),
}

CLUES = {
    "british_note": ClueObject("british_note", "note", "the tiny note", "the British note said 'lifted for sharing, not missing'", True),
    "crumbs": ClueObject("crumbs", "crumbs", "the little crumbs", "a neat trail of crumbs led to the pantry", False),
    "ticket": ClueObject("ticket", "ticket", "the ticket stub", "a ticket stub was tucked under a mug", True),
}

NAMES = ["Mia", "Ava", "Lily", "Noah", "Ben", "Theo", "Penny", "Rose"]


@dataclass
class StoryParams:
    setting: str
    item: str
    clue: str
    detective: str
    detective_type: str
    owner: str
    owner_type: str
    sharer: str
    sharer_type: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, i, c) for s in SETTINGS for i in ITEMS for c in CLUES]


def explain_rejection(_: str, __: str, ___: str) -> str:
    return "(No story: this setup does not support a clear shared-item misunderstanding mystery.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit story world: survey, sharing, misunderstanding.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--detective")
    ap.add_argument("--owner")
    ap.add_argument("--sharer")
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
              if (args.setting is None or c[0] == args.setting)
              and (args.item is None or c[1] == args.item)
              and (args.clue is None or c[2] == args.clue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, item, clue = rng.choice(sorted(combos))
    return StoryParams(
        setting, item, clue,
        args.detective or rng.choice(NAMES),
        rng.choice(["girl", "boy"]),
        args.owner or rng.choice([n for n in NAMES if n != args.detective]),
        rng.choice(["girl", "boy"]),
        args.sharer or rng.choice([n for n in NAMES if n not in {args.detective, args.owner}]),
        rng.choice(["girl", "boy"]),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short whodunit story for a child that includes the words "survey", "pant", and "british".',
        f"Tell a gentle mystery where {f['detective'].id} surveys {f['setting'].place} and discovers that {f['item'].phrase} only seems missing because of a misunderstanding.",
        f"Write a story about sharing something, a mistaken clue, and a careful reveal in {f['setting'].place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective, owner, sharer, item = f["detective"], f["owner"], f["sharer"], f["item"]
    return [
        QAItem(
            question="What kind of story is this?",
            answer="It is a little whodunit, so it begins with something missing and ends with a careful reveal. The detective uses clues instead of guessing too fast."
        ),
        QAItem(
            question=f"Why did {owner.id} pant with worry?",
            answer=f"{owner.id} thought {item.phrase} had disappeared, so {owner.id} started to pant with worry. The worry came from a misunderstanding, not from anyone doing something bad."
        ),
        QAItem(
            question="What solved the mystery?",
            answer=f"{detective.id} surveyed the room, followed the clues, and noticed that {item.phrase} had only been moved for sharing. That is what turned the confusion into relief."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does survey mean in a detective story?",
            answer="To survey means to look over a place carefully and notice small details. A detective surveys a room to find clues."
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone gets the wrong idea about what is happening. It can make a normal thing seem mysterious."
        ),
        QAItem(
            question="Why can sharing cause confusion sometimes?",
            answer="If one person moves an item to share it, another person might think it is missing. A quick explanation can clear that up."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        out.append(f"  {e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    out.append(f"  fired={sorted(n for n, *_ in world.fired)}")
    return "\n".join(out)


CURATED = [
    StoryParams("kitchen", "pants", "british_note", "Mia", "girl", "Ben", "boy", "Ava", "girl"),
    StoryParams("hall", "coat", "ticket", "Noah", "boy", "Penny", "girl", "Rose", "girl"),
    StoryParams("study", "book", "crumbs", "Lily", "girl", "Theo", "boy", "Ben", "boy"),
]


ASP_RULES = r"""
valid(S, I, C) :- setting(S), item(I), clue(C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, item=None, clue=None, detective=None, owner=None, sharer=None), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        return 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], params.detective, params.detective_type,
                 params.owner, params.owner_type, params.sharer, params.sharer_type,
                 ITEMS[params.item], CLUES[params.clue])
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return
    base = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        for i in range(max(args.n * 50, 50)):
            if len(samples) >= args.n:
                break
            p = resolve_params(args, random.Random(base + i))
            p.seed = base + i
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
