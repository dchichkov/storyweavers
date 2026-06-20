#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/waive_suspense_misunderstanding_flashback_heartwarming.py
=========================================================================================

A standalone storyworld about a child, a small misunderstanding, a suspenseful
search, a flashback that explains the missing thing, and a heartwarming ending
where a grown-up waives a tiny fee and everyone feels better.

The seed word is "waive"; the world models a library-day story where a child
thinks something bad has happened, but the truth is gentler than it first seems.
A short flashback explains the confusion, the suspense peaks during the search,
and the ending proves what changed.
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

    tags: set[str] = field(default_factory=set)

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
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Setting:
    id: str
    place: str
    atmosphere: str
    desk: str
    quiet_spot: str
    home_return: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    missing_phrase: str
    found_phrase: str
    singular: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Misunderstanding:
    id: str
    suspicion: str
    mistaken_guess: str
    real_reason: str
    flashback_hint: str
    waiver_phrase: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


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
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.memes["worry"] < THRESHOLD:
            continue
        sig = ("suspense", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "child" in world.entities:
            world.get("child").memes["fear"] += 1
        out.append("__suspense__")
    return out


def _r_search(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["searching"] < THRESHOLD:
            continue
        sig = ("search", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["determination"] += 1
        out.append("__search__")
    return out


CAUSAL_RULES = [
    Rule("suspense", "social", _r_suspense),
    Rule("search", "social", _r_search),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_missing(world: World, item_id: str) -> dict:
    sim = world.copy()
    sim.get(item_id).meters["missing"] += 1
    return {
        "worry": sim.get("child").memes["worry"] + 1,
        "searching": 1,
    }


def introduce(world: World, child: Entity, friend: Entity, setting: Setting) -> None:
    child.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"On a soft afternoon, {child.id} and {friend.id} went to {setting.place}. "
        f"{setting.atmosphere}."
    )
    world.say(
        f"{child.id} carried a little notebook, and {friend.id} carried a pencil "
        f"with a chewed-up eraser."
    )


def setup_need(world: World, child: Entity, item: Entity, setting: Setting) -> None:
    world.say(
        f"They stopped by {setting.desk}, where {item.phrase} was supposed to be kept."
    )
    world.say(
        f"{child.id} wanted to show {item.label} to {child.pronoun('possessive')} "
        f"{world.facts['helper'].label_word}, but the shelf looked bare."
    )


def prompt_suspense(world: World, child: Entity, friend: Entity, item: Entity) -> None:
    child.memes["worry"] += 1
    friend.memes["worry"] += 1
    world.say(
        f"Then {friend.id} frowned. '{item.label_word if item.label else item.label} is gone,' "
        f"{friend.pronoun()} whispered, and the room felt suddenly very quiet."
    )
    world.say(
        f"{child.id}'s heart thumped. '{item.label} was here a minute ago,' "
        f"{child.pronoun()} said."
    )


def flashback(world: World, child: Entity, helper: Entity, item: Entity,
              misunderstanding: Misunderstanding) -> None:
    world.say(
        f"For a moment, {child.id} remembered earlier that morning: "
        f"{misunderstanding.flashback_hint}"
    )
    world.say(
        f"In that flashback, {helper.id} had said, '{misunderstanding.real_reason}.'"
    )


def search(world: World, child: Entity, friend: Entity, item: Entity) -> None:
    child.meters["searching"] += 1
    friend.meters["searching"] += 1
    propagate(world, narrate=False)
    world.say(
        f"They searched under the table, behind the picture books, and inside a "
        f"paper basket. The quiet search made the mystery feel bigger."
    )


def reveal(world: World, helper: Entity, item: Entity, misunderstanding: Misunderstanding) -> None:
    item.meters["found"] += 1
    helper.memes["kindness"] += 1
    world.say(
        f"Then {helper.id} came back smiling. '{misunderstanding.suspicion}' "
        f"{helper.pronoun()} said gently, 'but look again.'"
    )
    world.say(
        f"{helper.id} reached into {world.setting.quiet_spot} and found {item.found_phrase}."
    )


def waive(world: World, helper: Entity, item: Entity, misunderstanding: Misunderstanding) -> None:
    helper.meters["waived"] += 1
    helper.memes["warmth"] += 1
    world.say(
        f"{helper.id} chuckled and said, 'No worries at all. I can waive that tiny fee.'"
    )
    world.say(
        f"That made the whole room feel lighter, as if the air had opened up for a hug."
    )


def heartwarming_end(world: World, child: Entity, friend: Entity, helper: Entity,
                     item: Entity) -> None:
    child.memes["relief"] += 1
    friend.memes["relief"] += 1
    helper.memes["love"] += 1
    world.say(
        f"{child.id} smiled, held up {item.label}, and thanked {helper.id} with a big hug."
    )
    world.say(
        f"{friend.id} laughed too, and the three of them headed home feeling safe, "
        f"kind, and glad the misunderstanding had been solved."
    )


SETTINGS = {
    "library": Setting(
        "library",
        "the library",
        "The lamps glowed softly, and the carpet held the hush of turning pages",
        "the front desk",
        "the quiet reading nook",
        "the tiny overdue slip",
    ),
    "bookshop": Setting(
        "bookshop",
        "the bookshop",
        "Shelves rose like towers, and the bell above the door made a gentle ring",
        "the checkout counter",
        "the corner by the picture books",
        "the small receipt packet",
    ),
    "community_center": Setting(
        "community_center",
        "the community center",
        "Kids' art hung on the walls, and the hallway smelled like crayons and paper",
        "the sign-in desk",
        "the chair by the puzzle shelf",
        "the lost sticker card",
    ),
}

ITEMS = {
    "book": Item("book", "a library book", "a library book with a blue ribbon", "the book was missing", "the book on the return shelf", tags={"book", "library"}),
    "pencil_box": Item("pencil_box", "a pencil box", "a bright pencil box", "the pencil box was missing", "the pencil box in the art basket", tags={"pencil", "box"}),
    "glasses": Item("glasses", "glasses", "a pair of glasses", "the glasses were missing", "the glasses on the chair arm", singular=False, tags={"glasses"}),
}

MISUNDERSTANDINGS = {
    "overdue": Misunderstanding(
        "overdue",
        "The tiny slip looked serious.",
        "You must owe a big fine",
        "The due date was already waived for a week because of the holiday",
        "Last week, while the rain tapped the windows, the helper had calmly tucked the slip into a folder.",
        "We can waive that tiny fee",
    ),
    "missing_note": Misunderstanding(
        "missing_note",
        "The empty shelf looked alarming.",
        "Someone took it away on purpose",
        "The item had been moved to the return shelf so the child could find it later",
        "Earlier, the helper had smiled and whispered that it would be safe there until closing time.",
        "I put it somewhere safer",
    ),
    "late_return": Misunderstanding(
        "late_return",
        "The clock looked too loud.",
        "We are in trouble",
        "The helper had already said it was fine and the return could wait until morning",
        "A flashback to the morning showed a calm nod and a kind promise to make things easier.",
        "There is no trouble here",
    ),
}

GROWNUPS = ["mother", "father", "aunt", "uncle"]
KIDS = ["girl", "boy"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for mid in MISUNDERSTANDINGS:
            for iid in ITEMS:
                combos.append((sid, mid, iid))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    misunderstanding: str
    item: str
    child_name: str
    child_gender: str
    friend_name: str
    friend_gender: str
    helper_name: str
    helper_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story that includes the word "waive" and a gentle misunderstanding at {f["setting"].place}.',
        f"Tell a suspenseful but kind story where {f['child'].id} worries about {f['item'].label}, then a flashback explains what really happened.",
        f"Write a short story with a flashback, a misunderstanding, and a warm ending where {f['helper'].id} can waive a tiny fee.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, friend, helper, item = f["child"], f["friend"], f["helper"], f["item"]
    mis = f["misunderstanding"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id}, {friend.id}, and {helper.id} at {world.setting.place}. The story follows a small worry that turns into a kind solution."),
        ("What did the child think at first?",
         f"{child.id} thought {mis.mistaken_guess}. That was the misunderstanding that made the moment feel suspenseful."),
        ("What was the flashback for?",
         f"The flashback explained why {item.label} was not really lost. It showed that {helper.id} had already moved it somewhere safe and had been gentle about it."),
    ]
    if f.get("waived"):
        qa.append((
            "What did the helper do to make things better?",
            f"{helper.id} waived the tiny fee and spoke kindly, so the child could relax. The warm response turned the worry into relief instead of trouble."
        ))
    qa.append((
        "How did the story end?",
        f"Everyone left feeling better, and {child.id} held up {item.label} with a smile. The ending proves the mistake was only a misunderstanding, not a real problem."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["item"].tags)
    tags |= {"library", "waive"}
    out = []
    if "book" in tags:
        out.append(("What is a library book?",
                     "A library book is a book that many people can borrow and return so others can read it too."))
    if "waive" in tags:
        out.append(("What does waive mean?",
                     "To waive something means to say you do not need to pay it or do it this time. A grown-up might waive a small fee to be kind."))
    out.append(("What is a flashback in a story?",
                 "A flashback is a part of the story that shows something from earlier. It helps explain why a character feels confused or worried now."))
    return out


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
    for e in list(world.entities.values()):
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
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
worry(C) :- child(C), worry_word(C).
suspense(C) :- child(C), worry(C).
found(I) :- item(I), moved_safe(I).
waived(H) :- helper(H), kind_help(H).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid in MISUNDERSTANDINGS:
        lines.append(asp.fact("misunderstanding", mid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    lines.append(asp.fact("waive_word", "waive"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("", "#show setting/1."))
    if not model:
        print("MISMATCH: ASP did not produce a model.")
        return 1
    print("OK: ASP program loads and produces a model.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a suspenseful misunderstanding with a flashback and a heartwarming waiver."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=KIDS)
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=KIDS)
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["mother", "father", "aunt", "uncle"])
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
              and (args.misunderstanding is None or c[1] == args.misunderstanding)
              and (args.item is None or c[2] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, misunderstanding, item = rng.choice(combos)
    child_gender = args.child_gender or rng.choice(KIDS)
    friend_gender = args.friend_gender or rng.choice(KIDS)
    helper_gender = args.helper_gender or rng.choice(["mother", "father", "aunt", "uncle"])
    child_name = args.child_name or rng.choice(["Mina", "Nora", "Liam", "Theo", "Ivy", "Ava"])
    friend_name = args.friend_name or rng.choice(["Pip", "Ben", "Maya", "June", "Owen", "Zoe"])
    helper_name = args.helper_name or rng.choice(["Mom", "Dad", "Aunt Ruby", "Uncle Sam"])
    return StoryParams(setting, misunderstanding, item, child_name, child_gender,
                       friend_name, friend_gender, helper_name, helper_gender)


def tell(setting: Setting, mis: Misunderstanding, item_cfg: Item,
         child_name: str, child_gender: str, friend_name: str, friend_gender: str,
         helper_name: str, helper_gender: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper", label="the helper"))
    item = world.add(Entity(id="item", kind="thing", type="thing", label=item_cfg.label, traits=[item_cfg.id]))
    world.facts.update(child=child, friend=friend, helper=helper, item=item, misunderstanding=mis, setting=setting)

    introduce(world, child, friend, setting)
    setup_need(world, child, item, setting)
    world.para()
    prompt_suspense(world, child, friend, item)
    search(world, child, friend, item)
    world.para()
    flashback(world, child, helper, item, mis)
    reveal(world, helper, item, mis)
    waive(world, helper, item, mis)
    heartwarming_end(world, child, friend, helper, item)

    world.facts["waived"] = True
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], MISUNDERSTANDINGS[params.misunderstanding],
                 ITEMS[params.item], params.child_name, params.child_gender,
                 params.friend_name, params.friend_gender, params.helper_name,
                 params.helper_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


CURATED = [
    StoryParams("library", "overdue", "book", "Mina", "girl", "Pip", "boy", "Mom", "mother"),
    StoryParams("bookshop", "missing_note", "pencil_box", "Liam", "boy", "Zoe", "girl", "Aunt Ruby", "aunt"),
    StoryParams("community_center", "late_return", "glasses", "Ivy", "girl", "Ben", "boy", "Dad", "father"),
]


def valid_response() -> str:
    return "waive"


def explain_rejection() -> str:
    return "(No story: this world only supports gentle misunderstanding stories with a waive moment.)"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show setting/1."))
    return sorted(set(asp.atoms(model, "setting")))


def asp_sensible() -> list[str]:
    return [valid_response()]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show setting/1."))
        return
    if args.verify:
        # smoke test
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise SystemExit(1)
        print(sample.story[:120])
        sys.exit(asp_verify())
    if args.asp:
        print("sensible responses: waive")
        for sid in SETTINGS:
            print(sid)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
        if args.all:
            p = sample.params
            header = f"### {p.child_name} at {p.setting} ({p.misunderstanding}, {p.item})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        if header:
            print(header)
        print(sample.story)
        if args.trace and sample.world is not None:
            print(dump_trace(sample.world))
        if args.qa:
            print()
            print(format_qa(sample))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
