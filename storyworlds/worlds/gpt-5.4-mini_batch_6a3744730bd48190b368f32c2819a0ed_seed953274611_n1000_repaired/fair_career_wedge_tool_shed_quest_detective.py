#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/fair_career_wedge_tool_shed_quest_detective.py
===============================================================================

A standalone tiny storyworld in a tool shed, told in a detective-story style.

Premise:
- A child detective runs a small quest in a tool shed.
- A missing wedge blocks a fair repair for a grown-up's career project.
- The detective gathers clues, solves the puzzle, and restores order.
- The ending proves what changed: the right wedge is found, the repair works,
  and the workday can continue fairly.

The world is intentionally small, concrete, and state-driven.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    afford: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    kind: str
    useful_for: str
    missing: bool = False
    plural: bool = False
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class QuestPlan:
    id: str
    title: str
    clue: str
    suspect: str
    find_text: str
    resolve_text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Wedge:
    id: str
    label: str
    phrase: str
    fit: str
    role: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


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
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_missing_alert(world: World) -> list[str]:
    out: list[str] = []
    shelf = world.get("shelf")
    for item in list(world.entities.values()):
        if item.kind == "item" and item.meters["missing"] >= THRESHOLD:
            sig = ("missing", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            shelf.meters["clutter"] += 1
            for char in world.characters():
                if char.role == "detective":
                    char.memes["curiosity"] += 1
            out.append("__clue__")
    return out


def _r_fairness(world: World) -> list[str]:
    out: list[str] = []
    if world.get("wedge").meters["found"] < THRESHOLD:
        return out
    sig = ("fair",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("project").meters["stable"] += 1
    for char in world.characters():
        char.memes["relief"] += 1
    out.append("__resolve__")
    return out


CAUSAL_RULES = [Rule("missing_alert", _r_missing_alert), Rule("fairness", _r_fairness)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            vals = rule.apply(world)
            if vals:
                changed = True
                produced.extend(v for v in vals if not v.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_ok(setting: Setting, plan: QuestPlan, item: Item, wedge: Wedge) -> bool:
    return (
        setting.id == "tool_shed"
        and "quest" in plan.tags
        and item.kind == plan.suspect
        and wedge.fit == item.kind
        and item.missing
        and not wedge.role == ""
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for pid, plan in QUESTS.items():
            for iid, item in ITEMS.items():
                for wid, wedge in WEDGES.items():
                    if reasonableness_ok(setting, plan, item, wedge):
                        combos.append((sid, pid, iid, wid))
    return combos


@dataclass
class StoryParams:
    setting: str
    quest: str
    item: str
    wedge: str
    detective_name: str
    detective_gender: str
    foreman_name: str
    foreman_gender: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


SETTINGS = {
    "tool_shed": Setting(
        id="tool_shed",
        place="the tool shed",
        mood="dusty and bright with little sunbeams",
        afford={"quest"},
    ),
    "back_room": Setting(
        id="back_room",
        place="the back room",
        mood="quiet and tidy",
        afford={"quest"},
    ),
}

QUESTS = {
    "fair_fix": QuestPlan(
        id="fair_fix",
        title="the fair fix",
        clue="a crooked latch and a missing shim",
        suspect="item",
        find_text="followed the clue trail between the hooks",
        resolve_text="made the latch fit straight again",
        tags={"quest"},
    ),
    "career_case": QuestPlan(
        id="career_case",
        title="the career case",
        clue="a workbench that would not stay level",
        suspect="item",
        find_text="searched under the paint cans and the broom",
        resolve_text="helped the grown-up's work move along fairly",
        tags={"quest"},
    ),
}

ITEMS = {
    "latch": Item(
        id="latch",
        label="latch",
        phrase="the little latch",
        kind="item",
        useful_for="door",
        missing=True,
        tags={"fair"},
    ),
    "drawer": Item(
        id="drawer",
        label="drawer",
        phrase="the small drawer",
        kind="item",
        useful_for="bench",
        missing=True,
        tags={"career"},
    ),
}

WEDGES = {
    "wood_wedge": Wedge(
        id="wood_wedge",
        label="wood wedge",
        phrase="a smooth wood wedge",
        fit="item",
        role="helper",
        tags={"wedge"},
    ),
    "metal_wedge": Wedge(
        id="metal_wedge",
        label="metal wedge",
        phrase="a shiny metal wedge",
        fit="item",
        role="helper",
        tags={"wedge"},
    ),
}

GIRL_NAMES = ["Mia", "Zoe", "Lily", "Nora", "Ava", "Ruby"]
BOY_NAMES = ["Theo", "Finn", "Max", "Eli", "Noah", "Jack"]
TRAITS = ["careful", "brave", "sharp-eyed", "patient", "curious"]


def tell(setting: Setting, quest: QuestPlan, item: Item, wedge: Wedge,
         detective_name: str, detective_gender: str,
         foreman_name: str, foreman_gender: str) -> World:
    world = World()
    d = world.add(Entity(
        id=detective_name, kind="character", type=detective_gender,
        role="detective", traits=["sharp-eyed"],
    ))
    f = world.add(Entity(
        id=foreman_name, kind="character", type=foreman_gender,
        role="foreman", traits=["tired", "fair"],
    ))
    shed = world.add(Entity(id="shed", kind="thing", type="room", label="tool shed"))
    shelf = world.add(Entity(id="shelf", kind="thing", type="shelf", label="shelf"))
    project = world.add(Entity(id="project", kind="thing", type="project", label="workbench project"))
    clue = world.add(Entity(id="clue", kind="thing", type="clue", label=quest.clue))
    lost = world.add(Entity(id="lost_item", kind="item", type="item", label=item.label))
    chosen = world.add(Entity(id="wedge", kind="item", type="wedge", label=wedge.label))

    world.facts.update(setting=setting, quest=quest, item=item, wedge=wedge, detective=d, foreman=f)

    d.memes["curiosity"] = 1
    f.memes["worry"] = 1

    world.say(
        f"In {setting.place}, the air was {setting.mood}. "
        f"{d.id} was a little detective, and {f.id} was trying to finish a big "
        f"career project at the workbench."
    )
    world.say(
        f"Then {d.id} noticed a mystery: {quest.clue}. "
        f"The job could not stay fair until the missing wedge was found."
    )

    world.para()
    lost.meters["missing"] += 1
    d.memes["determination"] += 1
    world.say(
        f'"This is a quest," said {d.id}. "{quest.find_text.capitalize()}." '
        f'{d.id} looked under jars, hooks, and a nail box.'
    )

    world.para()
    world.say(
        f"{f.id} frowned at the tilted bench. "
        f'"{quest.resolve_text.capitalize()}, but I cannot do it without the right wedge," '
        f'{f.id} said.'
    )
    world.say(
        f"{d.id} found {item.phrase}, then spotted {wedge.phrase} tucked beside the shelf.'
    )

    item.meters["missing"] = 0
    wedge.meters["found"] += 1
    project.meters["needs_wedge"] += 1
    propagate(world, narrate=False)

    world.para()
    world.say(
        f'{d.id} held up {wedge.phrase}. "{quest.title.capitalize()} solved!" '
        f"{f.id} fit the wedge into place, and the workbench stood straight."
    )
    world.say(
        f"The shed felt fair again. {f.id}'s career project could go on, and "
        f"{d.id} left like a detective who had cracked the case."
    )

    world.facts.update(outcome="solved", shed=shed, shelf=shelf, project=project, clue=clue, lost=lost, chosen=chosen)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a detective story for a young child set in a tool shed. Include the words "fair", "career", and "wedge".',
        f"Tell a quest story where {f['detective'].id} solves a tool-shed mystery for {f['foreman'].id} and keeps the fix fair.",
        f"Write a short detective tale about a missing wedge, a career project, and a clue hiding in the shed.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    d = f["detective"]
    fore = f["foreman"]
    quest = f["quest"]
    item = f["item"]
    wedge = f["wedge"]
    return [
        ("Where does the story happen?",
         f"It happens in the tool shed. The shed is dusty and full of little hiding places, which makes it a good place for a mystery."),
        ("What kind of story is this?",
         f"It is a detective story with a quest. {d.id} follows clues, finds the missing wedge, and helps finish the job fairly."),
        ("Why was the foreman worried?",
         f"{fore.id} needed the workbench to stay level for a career project, but the right wedge was missing. Without it, the repair would not hold."),
        ("What solved the case?",
         f"{d.id} found {item.phrase} and then the right {wedge.label}. That let {fore.id} set the wedge in place and make the bench steady again."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a detective?",
         "A detective is someone who looks for clues and solves mysteries. Detectives ask careful questions and notice small details."),
        ("What is a quest?",
         "A quest is a search for something important. The seeker follows clues and keeps going until the goal is found."),
        ("What is a wedge?",
         "A wedge is a piece with a thin end and a thicker end. People use wedges to help hold things steady or to fit things in place."),
        ("What does fair mean?",
         "Fair means everyone gets a kind and honest turn. A fair choice does not cheat anybody or leave someone out."),
        ("What is a career?",
         "A career is the kind of work a grown-up does over time. It is how someone earns a living and helps others with their skills."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:12} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="tool_shed", quest="fair_fix", item="latch", wedge="wood_wedge",
                detective_name="Mia", detective_gender="girl",
                foreman_name="Ben", foreman_gender="boy"),
    StoryParams(setting="tool_shed", quest="career_case", item="drawer", wedge="metal_wedge",
                detective_name="Theo", detective_gender="boy",
                foreman_name="Lily", foreman_gender="girl"),
]


def explain_rejection() -> str:
    return "(No story: this world only works in the tool shed with a quest, a missing item, and a fitting wedge.)"


def valid_params(params: StoryParams) -> bool:
    if params.setting not in SETTINGS or params.quest not in QUESTS or params.item not in ITEMS or params.wedge not in WEDGES:
        return False
    return reasonableness_ok(SETTINGS[params.setting], QUESTS[params.quest], ITEMS[params.item], WEDGES[params.wedge])


ASP_RULES = r"""
quest(quest).
setting(tool_shed).
item(latch).
item(drawer).
wedge(wood_wedge).
wedge(metal_wedge).

missing(Item) :- item(Item).
fits(Wedge, Item) :- wedge(Wedge), item(Item).
valid(Setting, Quest, Item, Wedge) :- setting(Setting), quest(Quest), item(Item), wedge(Wedge), missing(Item), fits(Wedge, Item).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "tool_shed"), asp.fact("quest", "quest")]
    for i in ITEMS:
        lines.append(asp.fact("item", i))
    for w in WEDGES:
        lines.append(asp.fact("wedge", w))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    ok = True
    if set(asp_valid_combos()) != set(valid_combos()):
        ok = False
        print("MISMATCH: ASP and Python valid-combo logic differ.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as exc:  # pragma: no cover
        ok = False
        print(f"SMOKE TEST FAILED: {exc}")
    if ok:
        print("OK: ASP parity and smoke test passed.")
        return 0
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective-style tool-shed quest storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--wedge", choices=WEDGES)
    ap.add_argument("--detective-name")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--foreman-name")
    ap.add_argument("--foreman-gender", choices=["girl", "boy"])
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
    setting = args.setting or "tool_shed"
    quest = args.quest or rng.choice(list(QUESTS))
    item = args.item or rng.choice(list(ITEMS))
    wedge = args.wedge or rng.choice(list(WEDGES))
    params = StoryParams(
        setting=setting,
        quest=quest,
        item=item,
        wedge=wedge,
        detective_name=args.detective_name or rng.choice(GIRL_NAMES + BOY_NAMES),
        detective_gender=args.detective_gender or rng.choice(["girl", "boy"]),
        foreman_name=args.foreman_name or rng.choice(GIRL_NAMES + BOY_NAMES),
        foreman_gender=args.foreman_gender or rng.choice(["girl", "boy"]),
    )
    if not valid_params(params):
        raise StoryError(explain_rejection())
    return params


def generate(params: StoryParams) -> StorySample:
    if not valid_params(params):
        raise StoryError(explain_rejection())
    world = tell(
        SETTINGS[params.setting], QUESTS[params.quest], ITEMS[params.item], WEDGES[params.wedge],
        params.detective_name, params.detective_gender, params.foreman_name, params.foreman_gender,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for combo in asp_valid_combos():
            print("  ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
            header = f"### {p.detective_name} in the {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
