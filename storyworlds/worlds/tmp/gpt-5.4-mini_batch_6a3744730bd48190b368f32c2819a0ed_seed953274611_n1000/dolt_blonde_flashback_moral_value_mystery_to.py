#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/dolt_blonde_flashback_moral_value_mystery_to.py
=================================================================================

A small mystery storyworld with a gentle flashback, a moral turn, and a concrete
solution. The seed asks for the words "dolt" and "blonde" and for a mystery
style, so the world centers on a kid detective story in a library: something
goes missing, clues are tested against the world model, a flashback reveals an
earlier detail, and the ending proves what changed.

The domain is deliberately tiny:
- one mystery item goes missing
- one clue is noticed in the present
- one flashback corrects a mistaken assumption
- one moral value is learned
- one culprit/object is revealed

The prose is state-driven, not a frozen paragraph with swapped nouns.
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    atmosphere: str
    hidden_spot: str


@dataclass
class MysteryItem:
    id: str
    label: str
    phrase: str
    usual_place: str
    clue_word: str
    value: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    kind: str
    truth: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Flashback:
    id: str
    opening: str
    detail: str
    truth: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Moral:
    id: str
    lesson: str
    action: str
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_suspect(world: World) -> list[str]:
    out = []
    box = world.get("bookbox")
    if box.meters["opened"] < THRESHOLD:
        return out
    if box.meters["messy"] >= THRESHOLD and ("suspect",) not in world.fired:
        world.fired.add(("suspect",))
        world.get("detective").memes["curiosity"] += 1
        out.append("__suspect__")
    return out


def _r_truth(world: World) -> list[str]:
    out = []
    if world.get("flashback").meters["seen"] < THRESHOLD:
        return out
    if ("truth",) not in world.fired:
        world.fired.add(("truth",))
        world.get("detective").memes["certainty"] += 1
        out.append("__truth__")
    return out


CAUSAL_RULES = [Rule("suspect", "mystery", _r_suspect), Rule("truth", "memory", _r_truth)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


def predict_missing(world: World, item: MysteryItem) -> dict:
    sim = world.copy()
    sim.get("object").meters["hidden"] += 1
    if item.id == "scarf" and "closet" in item.usual_place:
        sim.get("bookbox").meters["opened"] += 1
    return {"found": item.id == "scarf", "messy": sim.get("bookbox").meters["messy"]}


def search(world: World, detective: Entity, item: MysteryItem) -> None:
    detective.memes["curiosity"] += 1
    world.say(
        f"On a rainy afternoon, {detective.id} looked around the quiet library and "
        f"noticed that {item.phrase} was gone from {item.usual_place}."
    )
    world.say(
        f"{detective.id} frowned. \"This is a mystery,\" {detective.pronoun()} said, "
        f"\"and even a dolt would see something is wrong.\""
    )


def clue_scene(world: World, clue: Clue) -> None:
    world.get("bookbox").meters["opened"] += 1
    world.get("bookbox").meters["messy"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Near the shelf, {clue.phrase} sat by the bookbox. It looked like a small, "
        f"blonde thread on the floor, but it did not fit the missing {world.facts['item'].label}."
    )


def flashback_scene(world: World, fb: Flashback, helper: Entity) -> None:
    helper.memes["memory"] += 1
    world.get("flashback").meters["seen"] += 1
    world.say(
        f"Then {fb.opening} {helper.id} remembered {fb.detail}. The memory pointed to "
        f"the real hiding place."
    )


def reveal(world: World, detective: Entity, item: MysteryItem, helper: Entity) -> None:
    item_ent = world.get("object")
    item_ent.meters["found"] += 1
    detective.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"In the back room, behind the tall atlas, there it was: {item.phrase}. "
        f"The missing piece had been tucked into the wrong bin by mistake."
    )
    world.say(
        f"{detective.id} laughed. \"So the culprit wasn't a thief after all -- just a dolt "
        f"who put things away badly.\""
    )


def moral_scene(world: World, moral: Moral, helper: Entity, detective: Entity) -> None:
    detective.memes["moral"] += 1
    helper.memes["moral"] += 1
    world.say(
        f"{helper.id} apologized and put the {world.facts['item'].label} back where it belonged."
    )
    world.say(
        f"{moral.lesson} {moral.action}."
    )
    world.say(
        f"The library felt calm again, and the blonde thread on the floor was swept away at last."
    )


def tell(setting: Setting, item: MysteryItem, clue: Clue, fb: Flashback, moral: Moral,
         detective_name: str = "Nina", detective_gender: str = "girl",
         helper_name: str = "Milo", helper_gender: str = "boy") -> World:
    world = World()
    detective = world.add(Entity(id=detective_name, kind="character", type=detective_gender,
                                 role="detective", traits=["observant"]))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender,
                              role="helper", traits=["nervous"]))
    bookbox = world.add(Entity(id="bookbox", type="thing", label="bookbox"))
    flash = world.add(Entity(id="flashback", type="thing", label="flashback"))
    obj = world.add(Entity(id="object", type="thing", label=item.label))
    world.facts.update(setting=setting, item=item, clue=clue, flashback=fb, moral=moral,
                       detective=detective, helper=helper, bookbox=bookbox,
                       flashback_ent=flash, object=obj)

    world.say(
        f"In {setting.place}, where {setting.atmosphere}, {detective.id} and {helper.id} "
        f"began a small mystery."
    )
    world.say(
        f"The missing thing was {item.phrase}, and everyone knew it usually stayed {item.usual_place}."
    )

    world.para()
    search(world, detective, item)
    clue_scene(world, clue)

    world.para()
    flashback_scene(world, fb, helper)
    reveal(world, detective, item, helper)

    world.para()
    moral_scene(world, moral, helper, detective)

    return world


SETTINGS = {
    "library": Setting(id="library", place="the old library", atmosphere="the lamps were warm and the shelves were tall", hidden_spot="back room"),
    "museum": Setting(id="museum", place="the little museum", atmosphere="the halls were quiet and cool", hidden_spot="side archive"),
}

ITEMS = {
    "scarf": MysteryItem(id="scarf", label="scarf", phrase="a soft blue scarf", usual_place="the coat rack", clue_word="thread", value="warmth", tags={"blue", "cloth", "lost"}),
    "badge": MysteryItem(id="badge", label="badge", phrase="a tiny brass badge", usual_place="the front desk", clue_word="shine", value="pride", tags={"brass", "lost"}),
}

CLUES = {
    "thread": Clue(id="thread", label="thread", phrase="a blonde thread", kind="thread", truth="it came from a sweater, not the missing thing", tags={"blonde", "thread"}),
    "smudge": Clue(id="smudge", label="smudge", phrase="a chalk smudge", kind="smudge", truth="it came from the map table, not the hidden item", tags={"chalk", "smudge"}),
}

FLASHBACKS = {
    "wrong_bin": Flashback(id="wrong_bin", opening="With a flash of memory, ", detail="seeing Milo carry the scarf toward the wrong bin earlier", truth="the item was misplaced"),
    "shelf_note": Flashback(id="shelf_note", opening="Then suddenly, ", detail="a note that said 'back room' under the shelf card", truth="the item was moved to the back room"),
}

MORALS = {
    "kindness": Moral(id="kindness", lesson="The best mystery solvers tell the truth kindly and fix mistakes", action="because a mistake is easier to mend when nobody hides it"),
    "careful": Moral(id="careful", lesson="A careful detective checks clues before blaming anyone", action="because true answers come from thinking, not from being rude"),
}

GIRL_NAMES = ["Nina", "Maya", "Lila", "Zoe", "Ava"]
BOY_NAMES = ["Milo", "Finn", "Theo", "Owen", "Leo"]


@dataclass
class StoryParams:
    setting: str
    item: str
    clue: str
    flashback: str
    moral: str
    detective_name: str
    detective_gender: str
    helper_name: str
    helper_gender: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(setting="library", item="scarf", clue="thread", flashback="wrong_bin", moral="kindness",
                detective_name="Nina", detective_gender="girl", helper_name="Milo", helper_gender="boy"),
    StoryParams(setting="museum", item="badge", clue="smudge", flashback="shelf_note", moral="careful",
                detective_name="Lila", detective_gender="girl", helper_name="Theo", helper_gender="boy"),
]


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for i in ITEMS:
            for c in CLUES:
                for fb in FLASHBACKS:
                    for m in MORALS:
                        combos.append((s, i, c, fb, m))
    return combos


def explain_rejection() -> str:
    return "(No story: the requested choices do not fit this mystery world.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny mystery storyworld with flashback and moral value.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--flashback", choices=FLASHBACKS)
    ap.add_argument("--moral", choices=MORALS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    combos = valid_combos()
    if not combos:
        raise StoryError("(No valid mystery combinations.)")
    setting = args.setting or rng.choice(sorted(SETTINGS))
    item = args.item or rng.choice(sorted(ITEMS))
    clue = args.clue or rng.choice(sorted(CLUES))
    flashback = args.flashback or rng.choice(sorted(FLASHBACKS))
    moral = args.moral or rng.choice(sorted(MORALS))
    if args.item and args.clue and CLUES[args.clue].kind != ITEMS[args.item].clue_word and args.clue != ITEMS[args.item].clue_word:
        raise StoryError(explain_rejection())
    gender = "girl" if not args.name else "girl"
    detective_name = args.name or rng.choice(GIRL_NAMES)
    helper_name = args.helper or rng.choice(BOY_NAMES)
    return StoryParams(setting=setting, item=item, clue=clue, flashback=flashback, moral=moral,
                       detective_name=detective_name, detective_gender=gender,
                       helper_name=helper_name, helper_gender="boy")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mystery story for a young child that includes the words "dolt" and "blonde".',
        f"Tell a gentle detective story where {f['detective'].id} finds {f['item'].phrase} after a flashback, and the story ends with a moral.",
        f"Write a mystery in an old library where a clue seems to point one way, then a memory shows the real answer.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    det, helper, item, clue, fb, moral = f["detective"], f["helper"], f["item"], f["clue"], f["flashback"], f["moral"]
    return [
        ("What kind of story is this?",
         f"It is a mystery story set in {f['setting'].place}. It uses clues, a flashback, and a moral to solve the problem."),
        (f"What was missing?",
         f"{item.phrase} was missing from {item.usual_place}. That is why the children started looking around so carefully."),
        (f"Why did the blonde thread not solve the mystery by itself?",
         f"The blonde thread was only a clue, not the answer. It showed that someone had been near the bookbox, but it did not prove where the missing thing went."),
        (f"What did the flashback help them remember?",
         f"The flashback helped {helper.id} remember {fb.truth}. That memory pointed to the real hiding place and cleared up the mistake."),
        (f"What did {det.id} learn?",
         f"{moral.lesson}. The story shows that a good detective stays kind and checks the facts before blaming anyone."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a clue?",
         "A clue is a small piece of information that helps solve a mystery. It can be a mark, a note, a sound, or something unusual."),
        ("What is a flashback?",
         "A flashback is a memory that takes the story back to something that happened earlier. It helps explain what is true now."),
        ("What does moral value mean in a story?",
         "A moral value is the good lesson the story teaches, like kindness, honesty, or careful thinking."),
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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
missing_item(I) :- item(I).
suspect_clue(C) :- clue(C).
flashback_used :- flashback(F), seen(F).
lesson_learned :- moral(M).
mystery_solved :- missing_item(I), suspect_clue(C), flashback_used, lesson_learned.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for i, item in ITEMS.items():
        lines.append(asp.fact("item", i))
        lines.append(asp.fact("usual_place", i, item.usual_place))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    for fb in FLASHBACKS:
        lines.append(asp.fact("flashback", fb))
    for m in MORALS:
        lines.append(asp.fact("moral", m))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show mystery_solved/0.")
    model = asp.one_model(program)
    ok = any(sym.name == "mystery_solved" for sym in model)
    py_ok = len(valid_combos()) > 0
    if ok and py_ok:
        print("OK: ASP twin is live and the mystery world has valid combinations.")
    else:
        print("MISMATCH in ASP verification.")
        return 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, item=None, clue=None, flashback=None, moral=None, name=None, helper=None), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test completed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return 0


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.item not in ITEMS or params.clue not in CLUES or params.flashback not in FLASHBACKS or params.moral not in MORALS:
        raise StoryError("(Invalid story parameters.)")
    world = tell(
        SETTINGS[params.setting], ITEMS[params.item], CLUES[params.clue],
        FLASHBACKS[params.flashback], MORALS[params.moral],
        detective_name=params.detective_name, detective_gender=params.detective_gender,
        helper_name=params.helper_name, helper_gender=params.helper_gender,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program(show="#show mystery_solved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show mystery_solved/0."))
        print("ASP says mystery_solved:", bool(model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
            i += 1
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
            header = f"### {p.detective_name}: {p.setting}, {p.item}, {p.flashback}, {p.moral}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
