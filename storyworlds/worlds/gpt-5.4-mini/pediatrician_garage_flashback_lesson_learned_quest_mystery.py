#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/pediatrician_garage_flashback_lesson_learned_quest_mystery.py
============================================================================================

A standalone storyworld for a small mystery set in a garage with a pediatrician,
a quest, a flashback, and a lesson learned.

The domain is intentionally tiny:
- a child notices a puzzling clue in the garage,
- remembers a helpful flashback from a pediatrician visit,
- follows a quest through the garage to solve the mystery,
- learns a safe, practical lesson by the end.

The simulated world uses typed entities with physical meters and emotional memes.
Stories are state-driven, not frozen text swaps.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/pediatrician_garage_flashback_lesson_learned_quest_mystery.py
    python storyworlds/worlds/gpt-5.4-mini/pediatrician_garage_flashback_lesson_learned_quest_mystery.py --all
    python storyworlds/worlds/gpt-5.4-mini/pediatrician_garage_flashback_lesson_learned_quest_mystery.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4-mini/pediatrician_garage_flashback_lesson_learned_quest_mystery.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/pediatrician_garage_flashback_lesson_learned_quest_mystery.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class GarageSetting:
    id: str
    place: str
    clues: list[str]
    hiding_places: list[str]


@dataclass
class MysteryItem:
    id: str
    label: str
    clue: str
    hidden_in: str
    type: str
    suspicious: bool = True
    found: bool = False
    returned: bool = False


@dataclass
class Hint:
    id: str
    clue: str
    meaning: str


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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for kid in world.characters():
        if kid.role != "child" or kid.memes["curiosity"] < THRESHOLD:
            continue
        sig = ("worry", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kid.memes["worry"] += 1
        out.append("__worry__")
    return out


def _r_find(world: World) -> list[str]:
    out: list[str] = []
    child = next((e for e in world.characters() if e.role == "child"), None)
    if not child:
        return out
    for item in world.facts.get("items", []):
        if item.found:
            continue
        if item.hidden_in == "garage shelf" and world.facts.get("quest_started"):
            sig = ("find", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.found = True
            child.meters["discovery"] += 1
            out.append("__find__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    child = next((e for e in world.characters() if e.role == "child"), None)
    ped = next((e for e in world.characters() if e.role == "pediatrician"), None)
    if not child or not ped:
        return out
    if world.facts.get("lesson_learned") and child.memes["relief"] < 1:
        sig = ("relief", child.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        child.memes["relief"] += 1
        ped.memes["calm"] += 1
        out.append("__relief__")
    return out


CAUSAL_RULES = [Rule("worry", "social", _r_worry), Rule("find", "physical", _r_find), Rule("relief", "social", _r_relief)]


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


def setting_line(setting: GarageSetting) -> str:
    return f"The garage was full of boxes, a rickety shelf, and a little square of dusty light."


def do_flashback(world: World, child: Entity, ped: Entity) -> None:
    child.memes["remembering"] += 1
    world.say(
        f"Then {child.id} had a sudden flashback. At the pediatrician's office, "
        f"{ped.id} had pointed to a picture and said, \"If something looks strange, "
        f"look for the simple clue first.\""
    )


def start_quest(world: World, child: Entity, item: MysteryItem, setting: GarageSetting) -> None:
    world.facts["quest_started"] = True
    child.memes["quest"] += 1
    world.say(
        f"{child.id} stared at the mystery and decided to begin a quest through the garage. "
        f"A thin trail of {item.clue} led toward {setting.hiding_places[0]}."
    )


def search(world: World, child: Entity, item: MysteryItem) -> None:
    child.meters["searching"] += 1
    world.say(
        f"{child.id} checked behind a tire, under a tarp, and beside the shelf. "
        f"{child.pronoun().capitalize()} followed the tiny clue step by step."
    )
    propagate(world, narrate=False)


def reveal(world: World, child: Entity, item: MysteryItem) -> None:
    world.say(
        f"At last, {child.id} found the missing {item.label} hidden in the garage shelf. "
        f"It was not a monster or a thief after all, just one small thing that had rolled away."
    )
    item.returned = True
    child.meters["solved"] += 1
    world.facts["lesson_learned"] = True


def lesson(world: World, child: Entity, ped: Entity, item: MysteryItem) -> None:
    world.say(
        f"{child.id} called the pediatrician right away, and {ped.id} smiled. "
        f"\"Good detectives use clues, ask for help, and stay calm,\" "
        f"{ped.pronoun()} said. \"That is the best way to solve a mystery.\""
    )
    child.memes["confidence"] += 1
    child.memes["lesson"] += 1
    world.say(
        f"{child.id} nodded. The garage felt less spooky now, and the little mystery had become a lesson learned."
    )


def tell(setting: GarageSetting, item: MysteryItem, hint: Hint,
         child_name: str = "Mia", child_gender: str = "girl",
         ped_name: str = "Dr. Lee", ped_gender: str = "woman") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child", traits=["curious"]))
    ped = world.add(Entity(id=ped_name, kind="character", type=ped_gender, role="pediatrician", label="the pediatrician"))
    world.add(Entity(id="garage", type="place", label="the garage"))
    world.facts["setting"] = setting
    world.facts["item"] = item
    world.facts["hint"] = hint
    world.facts["child"] = child
    world.facts["pediatrician"] = ped
    world.facts["items"] = [item]

    child.memes["curiosity"] = 1.0

    world.say(
        f"One afternoon, {child.id} went into the garage and noticed something odd. "
        f"{setting_line(setting)}"
    )
    world.say(
        f"Near the shelf, {child.id} saw {item.clue}. It looked like a clue, and that made the whole garage feel like a mystery."
    )
    world.para()
    do_flashback(world, child, ped)
    start_quest(world, child, item, setting)
    world.para()
    search(world, child, item)
    reveal(world, child, item)
    world.para()
    lesson(world, child, ped, item)
    return world


GARAGE = GarageSetting(
    id="garage",
    place="the garage",
    clues=["dust on the floor", "a tiny squeak", "a bent tag"],
    hiding_places=["garage shelf", "tool box", "old crate"],
)

ITEMS = {
    "bike_key": MysteryItem("bike_key", "bike key", "dusty metal", "garage shelf", "key"),
    "toy_car": MysteryItem("toy_car", "toy car", "a faint red trail", "garage shelf", "toy"),
    "glove": MysteryItem("glove", "single glove", "one lonely blue thread", "garage shelf", "glove"),
}

HINTS = {
    "clue": Hint("clue", "look for the simple clue first", "start with the easiest sign"),
}

CURATED = [
    ("Mia", "girl", "Dr. Lee", "woman", "bike_key"),
    ("Noah", "boy", "Dr. Patel", "man", "toy_car"),
    ("Ava", "girl", "Dr. Kim", "woman", "glove"),
]


@dataclass
class StoryParams:
    setting: str
    item: str
    child_name: str
    child_gender: str
    pediatrician_name: str
    pediatrician_gender: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    return [(GARAGE.id, item_id) for item_id in ITEMS]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    item = f["item"]
    return [
        f'Write a mystery story for a 3-to-5-year-old set in a garage that includes the word "pediatrician" and a flashback from a clinic visit.',
        f"Tell a gentle quest story where {child.id} follows clues in the garage to find a missing {item.label}, remembers advice from the pediatrician, and learns a lesson.",
        f'Write a short mystery with a garage, a clue, and a lesson learned where the child asks the pediatrician for help and solves the puzzle.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    ped = f["pediatrician"]
    item = f["item"]
    return [
        ("Who is the story about?",
         f"It is about {child.id}, who noticed a mystery in the garage and decided to solve it."),
        ("What helped {0} solve the mystery?".format(child.id),
         f"A flashback to advice from the pediatrician helped {child.id} remember to look for the simple clue first. That made the quest calmer and easier to follow."),
        ("What was the mystery?",
         f"The mystery was where the missing {item.label} had gone. {child.id} found it hidden in the garage shelf."),
        ("How did the story end?",
         f"It ended with a lesson learned. {child.id} asked the pediatrician for help, solved the quest, and felt proud and safe."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a pediatrician?",
         "A pediatrician is a doctor who helps children stay healthy and gives advice about their care."),
        ("What is a flashback?",
         "A flashback is when a story remembers something that happened earlier."),
        ("What is a quest?",
         "A quest is a search for something important or missing."),
        ("What is a mystery?",
         "A mystery is a puzzle that makes you wonder what happened."),
        ("Why can a garage feel spooky?",
         "A garage can feel spooky because it is full of shadows, boxes, and hidden corners."),
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
quest_started :- child(C), curiosity(C, Cur), Cur >= 1.
find_item(I) :- quest_started, item(I), hidden_in(I, garage_shelf).
lesson_learned :- find_item(I), pediatrician(P), clue(I, _).
story_ok :- quest_started, find_item(_), lesson_learned.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("child", "child"))
    lines.append(asp.fact("pediatrician", "ped"))
    lines.append(asp.fact("curiosity", "child", 1))
    lines.append(asp.fact("item", "bike_key"))
    lines.append(asp.fact("item", "toy_car"))
    lines.append(asp.fact("item", "glove"))
    lines.append(asp.fact("hidden_in", "bike_key", "garage_shelf"))
    lines.append(asp.fact("hidden_in", "toy_car", "garage_shelf"))
    lines.append(asp.fact("hidden_in", "glove", "garage_shelf"))
    lines.append(asp.fact("clue", "bike_key", "dusty_metal"))
    lines.append(asp.fact("clue", "toy_car", "red_trail"))
    lines.append(asp.fact("clue", "glove", "blue_thread"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("", "#show story_ok/0."))
    ok = bool(asp.atoms(model, "story_ok"))
    py_ok = True
    try:
        sample = generate(CURATED_PARAMS[0])
        py_ok = bool(sample.story)
    except Exception:
        py_ok = False
    print("OK: ASP story flag and Python generation smoke test passed." if ok and py_ok else "MISMATCH: verify failed.")
    return 0 if ok and py_ok else 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery in a garage with a pediatrician, flashback, quest, and lesson learned.")
    ap.add_argument("--setting", choices=["garage"])
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy", "woman", "man"])
    ap.add_argument("--pediatrician", dest="pediatrician_name")
    ap.add_argument("--pediatrician-gender", choices=["woman", "man"])
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
    if args.setting and args.setting != "garage":
        raise StoryError("This world only supports a garage setting.")
    item_id = args.item or rng.choice(list(ITEMS))
    child_name = args.name or rng.choice(["Mia", "Noah", "Ava", "Leo", "Zoe", "Sam"])
    child_gender = args.gender or ("girl" if child_name in {"Mia", "Ava", "Zoe"} else "boy")
    ped_name = args.pediatrician_name or rng.choice(["Dr. Lee", "Dr. Patel", "Dr. Kim"])
    ped_gender = args.pediatrician_gender or ("woman" if ped_name in {"Dr. Lee", "Dr. Kim"} else "man")
    return StoryParams("garage", item_id, child_name, child_gender, ped_name, ped_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(GARAGE, ITEMS[params.item], HINTS["clue"], params.child_name, params.child_gender, params.pediatrician_name, params.pediatrician_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


CURATED_PARAMS = [
    StoryParams("garage", "bike_key", "Mia", "girl", "Dr. Lee", "woman"),
    StoryParams("garage", "toy_car", "Noah", "boy", "Dr. Patel", "man"),
    StoryParams("garage", "glove", "Ava", "girl", "Dr. Kim", "woman"),
]


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
        print(asp_program("", "#show story_ok/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("Story flag: story_ok")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED_PARAMS]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
