#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/quarter_gaga_sharing_mystery.py
==============================================================

A standalone storyworld for a small mystery about sharing a missing quarter,
with a playful "gaga" clue and a gentle reveal.

Premise
-------
A child sets aside a quarter for a shared treat, but the quarter goes missing.
The children search for clues, notice a gaga bird-shaped token, and follow the
trail through a small, concrete world of pockets, jars, and hiding places.
The ending resolves through sharing: the lost quarter is found, the friends
split the treat, and the mystery becomes a warm little celebration.

This script follows the Storyweavers contract:
- self-contained stdlib script
- shared results imported eagerly
- shared asp imported lazily
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
- includes a Python reasonableness gate and inline ASP twin
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
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
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    scene: str
    hiding_places: list[str]
    nouns: set[str] = field(default_factory=set)
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
    container: str
    clue: str
    can_hide: bool = True
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
class MysteryAct:
    id: str
    verb: str
    search_place: str
    reveal: str
    clue_text: str
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
class SharingPlan:
    id: str
    treat: str
    split_text: str
    share_sentence: str
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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    jar = world.get("jar")
    if jar.meters["empty"] < THRESHOLD:
        return out
    for child in ("mara", "jun"):
        ent = world.get(child)
        sig = ("worry", child)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["worry"] += 1
        out.append("")
    return out


def _r_hidden_clue(world: World) -> list[str]:
    out: list[str] = []
    if world.get("quarter").attrs.get("found"):
        return out
    if world.get("gaga").attrs.get("seen") and world.get("shoe").attrs.get("noticed"):
        sig = ("clue",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("quarter").attrs["hinted"] = True
            out.append("")
    return out


CAUSAL_RULES = [Rule("worry", "social", _r_worry), Rule("clue", "mystery", _r_hidden_clue)]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s)
    if narrate:
        for s in produced:
            world.say(s)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for act_id, act in ACTS.items():
            for plan_id, plan in PLANS.items():
                if act.id == "find" and "share" in plan.tags and "quarter" in setting.nouns:
                    combos.append((setting_id, act_id, plan_id))
    return combos


def sensible_plans() -> list[SharingPlan]:
    return [p for p in PLANS.values() if p.id != "stingy"]


def best_plan() -> SharingPlan:
    return max(PLANS.values(), key=lambda p: p.id != "stingy")


def is_reasonable(act: MysteryAct, plan: SharingPlan, setting: Setting) -> bool:
    return "share" in plan.tags and "quarter" in setting.nouns and act.id == "find"


def look_for_clue(world: World, hero: Entity, friend: Entity, act: MysteryAct, item: Item) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"On a quiet evening, {hero.id} and {friend.id} stood by {world.facts['setting'].place}. "
        f"{hero.id} had set a quarter on the table for a shared treat, but now it was gone."
    )
    world.say(
        f'"Where did the quarter go?" {friend.id} whispered. "{act.clue_text}"'
    )


def inspect_clue(world: World, hero: Entity, friend: Entity, item: Item) -> None:
    world.say(
        f"They looked under the chair, behind the jar, and beside the shoes. "
        f"Then {friend.id} spotted something tiny: {item.phrase}."
    )
    world.say(
        f'"That is odd," {hero.id} said. "{item.clue}"'
    )
    item.attrs["seen"] = True


def find_quarter(world: World, hero: Entity, friend: Entity) -> None:
    quarter = world.get("quarter")
    gaga = world.get("gaga")
    quarter.attrs["found"] = True
    gaga.attrs["seen"] = True
    world.say(
        f"At last, they heard a soft clink from {world.facts['setting'].hiding_places[0]}. "
        f"The quarter had slipped inside a little jar and rolled under {gaga.label_word}."
    )
    world.say(
        f"{friend.id} lifted {gaga.label_word} gently, and there was the quarter, bright and safe."
    )


def share_treat(world: World, hero: Entity, friend: Entity, plan: SharingPlan) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f'{hero.id} grinned. "{plan.split_text}"'
    )
    world.say(
        f"They used the quarter for {plan.treat}, then split it in half and shared the last sweet bite."
    )
    world.say(plan.share_sentence)


SETTINGS = {
    "kitchen": Setting(
        id="kitchen",
        place="the kitchen",
        scene="a quiet place with a shiny table and a jar of buttons",
        hiding_places=["the bread box"],
        nouns={"quarter", "jar", "table", "shoe"},
    ),
    "porch": Setting(
        id="porch",
        place="the porch",
        scene="a small porch with a mat, a step, and a wind-chime",
        hiding_places=["the doormat"],
        nouns={"quarter", "step", "mat", "shoe"},
    ),
    "laundry": Setting(
        id="laundry",
        place="the laundry room",
        scene="a busy room with a basket and a humming dryer",
        hiding_places=["the sock basket"],
        nouns={"quarter", "basket", "sock", "shoe"},
    ),
}

ACTS = {
    "find": MysteryAct(
        id="find",
        verb="find",
        search_place="look for the missing quarter",
        reveal="the quarter was hiding in a place they almost missed",
        clue_text="We should follow the tiny clues.",
        tags={"mystery"},
    ),
    "search": MysteryAct(
        id="search",
        verb="search",
        search_place="search carefully",
        reveal="the search led them from one clue to the next",
        clue_text="Let's look where little things like to hide.",
        tags={"mystery"},
    ),
}

PLANS = {
    "cookies": SharingPlan(
        id="cookies",
        treat="a cookie from the bakery",
        split_text="Let's share it!",
        share_sentence="The mystery ended with happy faces and a fair share for both.",
        tags={"share"},
    ),
    "juice": SharingPlan(
        id="juice",
        treat="a cup of apple juice",
        split_text="We can share the juice.",
        share_sentence="They clinked their cups together like little detectives at a victory parade.",
        tags={"share"},
    ),
    "stingy": SharingPlan(
        id="stingy",
        treat="a treat",
        split_text="Maybe I should keep it all.",
        share_sentence="That would not fit this little sharing mystery.",
        tags={"not_share"},
    ),
}

ITEMS = {
    "gaga": Item(
        id="gaga",
        label="gaga",
        phrase="a tiny gaga bird token",
        container="jar",
        clue="Gaga likes shiny things and sits near the jar.",
        tags={"gaga", "clue"},
    ),
    "shoe": Item(
        id="shoe",
        label="shoe",
        phrase="one shoe tipped sideways",
        container="floor",
        clue="The shoe was knocked just enough to point at the jar.",
        tags={"shoe", "clue"},
    ),
}

GIRL_NAMES = ["Mara", "Nina", "Tess", "Ivy", "Lina"]
BOY_NAMES = ["Jun", "Owen", "Pax", "Nico", "Leo"]


@dataclass
class StoryParams:
    setting: str
    act: str
    plan: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery storyworld about sharing a missing quarter.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--act", choices=ACTS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
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
              if (args.setting is None or c[0] == args.setting)
              and (args.act is None or c[1] == args.act)
              and (args.plan is None or c[2] == args.plan)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, act, plan = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    friend = args.friend or rng.choice([n for n in (BOY_NAMES if friend_gender == "boy" else GIRL_NAMES) if n != hero])
    return StoryParams(setting=setting, act=act, plan=plan, hero=hero, hero_gender=hero_gender, friend=friend, friend_gender=friend_gender)


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    act = ACTS[params.act]
    plan = PLANS[params.plan]
    if not is_reasonable(act, plan, setting):
        raise StoryError("This setup does not support a real mystery with sharing.")
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_gender, role="hero"))
    friend = world.add(Entity(id=params.friend, kind="character", type=params.friend_gender, role="friend"))
    quarter = world.add(Entity(id="quarter", label="quarter", role="token"))
    gaga = world.add(Entity(id="gaga", label="gaga", role="clue"))
    shoe = world.add(Entity(id="shoe", label="shoe", role="clue"))
    world.facts["setting"] = setting
    world.facts["act"] = act
    world.facts["plan"] = plan
    world.facts["quarter"] = quarter
    world.facts["gaga"] = gaga
    world.facts["shoe"] = shoe

    world.say(
        f"{hero.id} and {friend.id} were in {setting.place}, where the evening was quiet and a little mysterious."
    )
    world.say(
        f"{hero.id} had saved a quarter for a shared treat, but when the friends looked down, the quarter was gone."
    )
    world.para()
    look_for_clue(world, hero, friend, act, shoe)
    inspect_clue(world, hero, friend, gaga)
    world.para()
    find_quarter(world, hero, friend)
    world.para()
    share_treat(world, hero, friend, plan)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mystery story for a child that includes the words "quarter" and "gaga" and ends with sharing.',
        f"Tell a gentle mystery about {f['setting'].place} where {f['quarter'].label} goes missing, a clue from gaga is noticed, and the friends share a treat.",
        f'Write a story with a quiet clue, a found quarter, and a happy sharing ending.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = world.get(f["hero"].id) if "hero" in f else None
    if hero is None:
        # locate by params-like reference
        hero = next(e for e in world.entities.values() if e.role == "hero")
    friend = next(e for e in world.entities.values() if e.role == "friend")
    setting = f["setting"]
    plan = f["plan"]
    qa = [
        ("What was missing at the start?",
         f"The quarter was missing. It had been set aside for a shared treat, so losing it made the little mystery begin."),
        ("What clue did they notice?",
         f"They noticed gaga near the jar. That clue mattered because it pointed them toward a hiding place instead of making them guess wildly."),
        ("How did the story end?",
         f"They found the quarter and shared {plan.treat}. The ending proves the missing thing was recovered and the friends chose sharing."),
    ]
    if world.get("quarter").attrs.get("found"):
        qa.append((
            "Why did the friends feel better after searching?",
            f"They felt better because the quarter was found and the mystery made sense at last. Once they understood the clue, the worry turned into a small celebration."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    out = [
        ("What is a quarter?",
         "A quarter is a small coin. People can save it, spend it, or keep it in a jar."),
        ("What does a mystery story do?",
         "A mystery story asks a question at the start and then uses clues to help solve it."),
        ("What does sharing mean?",
         "Sharing means more than one person gets part of something. It is a kind way to enjoy a treat together."),
        ("What can a clue do?",
         "A clue helps you figure something out. It can point to the right place or the right answer."),
    ]
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"- {p}" for p in sample.prompts], "", "== (2) Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="kitchen", act="find", plan="cookies", hero="Mara", hero_gender="girl", friend="Jun", friend_gender="boy"),
    StoryParams(setting="porch", act="search", plan="juice", hero="Nina", hero_gender="girl", friend="Pax", friend_gender="boy"),
]


def explain_rejection() -> str:
    return "(No story: this setup needs a real sharing mystery, with a quarter to find and a clue to follow.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid in ACTS:
        lines.append(asp.fact("act", aid))
    for pid, plan in PLANS.items():
        lines.append(asp.fact("plan", pid))
        if "share" in plan.tags:
            lines.append(asp.fact("sharing_plan", pid))
    for sid, s in SETTINGS.items():
        if "quarter" in s.nouns:
            lines.append(asp.fact("has_quarter", sid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,A,P) :- setting(S), act(A), plan(P), has_quarter(S), sharing_plan(P), A = find.
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos().")
    try:
        params = CURATED[0]
        sample = generate(params)
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    try:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(generate(CURATED[0]), trace=False, qa=False)
        print("OK: emit() smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"EMIT TEST FAILED: {e}")
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.act not in ACTS or params.plan not in PLANS:
        raise StoryError("Invalid params.")
    world = tell(params)
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
