#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/luck_dim_sound_effects_kindness_heartwarming.py
================================================================================

A standalone storyworld about a small, heartwarming scene in which a child
notices that a little lucky charm light has gone dim, hears gentle sound effects,
and receives kindness from family and a neighbor. The world is built around a
simple causal model: a dim object can be restored by patient help, a worried
child can be comforted, and a shared act of kindness changes the ending image.

The required seed word "luck-dim" is included in the prose and in the generated
world facts. Sound effects appear as authored narration beats, not as raw logs.

Run it:
    python storyworlds/worlds/gpt-5.4-mini/luck_dim_sound_effects_kindness_heartwarming.py
    python storyworlds/worlds/gpt-5.4-mini/luck_dim_sound_effects_kindness_heartwarming.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/luck_dim_sound_effects_kindness_heartwarming.py --verify
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
BRIGHT_MIN = 2.0


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
        female = {"girl", "mother", "mom", "woman", "grandmother", "aunt"}
        male = {"boy", "father", "dad", "man", "grandfather", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
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
    cozy_detail: str
    sound: str
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
class DimItem:
    id: str
    label: str
    glow_word: str
    restore_word: str
    source: str
    is_luck_dim: bool = False
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
class HelpAction:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


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


def _r_comfort(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    helper = world.entities.get("helper")
    if not child or not helper:
        return out
    if child.memes["worry"] < THRESHOLD or helper.memes["kindness"] < THRESHOLD:
        return out
    sig = ("comfort",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["hope"] += 1
    out.append("__comfort__")
    return out


def _r_brighten(world: World) -> list[str]:
    out: list[str] = []
    item = world.entities.get("dim")
    if not item:
        return out
    if item.meters["brightness"] < THRESHOLD:
        return out
    sig = ("brighten",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.facts["restored"] = True
    out.append("__bright__")
    return out


CAUSAL_RULES = [Rule("comfort", "social", _r_comfort), Rule("brighten", "physical", _r_brighten)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for did, d in DIM_ITEMS.items():
            for aid, a in HELP_ACTIONS.items():
                if a.sense >= SENSE_MIN and d.is_luck_dim:
                    combos.append((sid, did, aid))
    return combos


def dim_at_risk(item: DimItem) -> bool:
    return item.is_luck_dim


def best_help() -> HelpAction:
    return max(HELP_ACTIONS.values(), key=lambda a: a.sense)


def is_enough(action: HelpAction, item: DimItem, delay: int) -> bool:
    return action.power >= (1 + delay) and item.is_luck_dim


def explain_rejection(item: DimItem, action: HelpAction) -> str:
    return f"(No story: {item.label} must be the luck-dim kind, and '{action.id}' must be a kind enough help.)"


def tell(setting: Setting, item: DimItem, action: HelpAction,
         child_name: str = "Milo", child_gender: str = "boy",
         helper_name: str = "Nia", helper_gender: str = "girl",
         helper_role: str = "neighbor", delay: int = 0) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name,
                             role="child", traits=["gentle", "curious"]))
    helper = world.add(Entity(id="helper", kind="character", type=helper_gender, label=helper_name,
                              role=helper_role, traits=["kind", "patient"]))
    dim = world.add(Entity(id="dim", kind="thing", type="thing", label=item.label,
                           attrs={"source": item.source}, tags=set(item.tags)))
    child.memes["worry"] = 1.0
    helper.memes["kindness"] = 2.0
    world.facts["setting"] = setting
    world.facts["item_cfg"] = item
    world.facts["action"] = action
    world.say(f"In {setting.place}, {child_name} noticed {item.label_word} had gone luck-dim.")
    world.say(f"{setting.cozy_detail} {setting.sound} drifted through the room, soft as a hush.")
    world.say(f'"It looks so dim," {child_name} whispered.')
    world.para()
    world.say(f'{helper_name} knelt beside {child_name} and said, "Kindness can make a dark moment feel smaller."')
    world.say(f'"Let us help it together," {helper_name} said, and made a gentle plan.')
    if not is_enough(action, item, delay):
        world.say(f"{helper_name} tried, but the help was too small.")
        world.facts["restored"] = False
    else:
        dim.meters["brightness"] += 1.0
        child.memes["worry"] = 0.0
        propagate(world, narrate=False)
        world.say(f"{action.text.replace('{item}', item.label)}.")
        world.say(f"With a soft {setting.sound}, the little light glowed back to life.")
        world.say(f"{child_name} smiled, and the room felt warm again.")
    world.facts.update(child=child, helper=helper, dim=dim, delay=delay, outcome="restored" if world.facts.get("restored") else "failed")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    item = f["item_cfg"]
    return [
        f'Write a heartwarming story that includes the word "luck-dim" and the idea of kindness helping a dim little light.',
        f"Tell a cozy story where {f['child'].label_word} sees {item.label} go luck-dim and a kind helper makes things better.",
        f'Write a gentle child story with a soft sound effect and a kind helper who restores "luck-dim" hope.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    item = f["item_cfg"]
    setting = f["setting"]
    if f["outcome"] == "restored":
        return [
            ("What did the child notice?",
             f"{child.label_word} noticed that {item.label} had gone luck-dim. It looked weak at first, but the child did not give up."),
            ("How did the helper respond?",
             f"{helper.label_word} used kindness and worked with the child instead of rushing. That gentle help made the dim light brighten again."),
            ("How did the story end?",
             f"It ended warmly, with {item.label} glowing again and the room feeling cozy. The child smiled because kindness changed the mood and the light.")
        ]
    return [
        ("What happened to the light?",
         f"{item.label} stayed dim because the help was too small. The child still felt cared for, even though the glow did not come back right away."),
        ("What did the helper do?",
         f"{helper.label_word} tried to help kindly and stayed with the child. That mattered, because kindness can still comfort someone even before a problem is solved."),
        ("How did the story end?",
         f"It ended softly, with two people sitting together in the dim room. The light was still low, but the child no longer felt alone.")
    ]


WORLD_KNOWLEDGE = {
    "luck-dim": [("What does luck-dim mean here?",
                  "It means something lucky or special has become dim and weak. The word sounds a little sad, but it can be turned around with care.")],
    "kindness": [("What is kindness?",
                  "Kindness is when someone helps, shares, or speaks gently so another person feels safer and happier.")],
    "sound": [("Why do stories use sound effects?",
               "Sound effects help readers imagine what is happening. They can make a moment feel soft, exciting, or magical.")],
    "glow": [("What does it mean when something glows?",
              "When something glows, it gives off a soft light. It can help a room feel cozy and calm.")],
}
WORLD_ORDER = ["luck-dim", "kindness", "sound", "glow"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["item_cfg"].tags) | {"kindness", "sound", "glow", "luck-dim"}
    out: list[tuple[str, str]] = []
    for tag in WORLD_ORDER:
        if tag in tags:
            out.extend(WORLD_KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


SETTINGS = {
    "cozy_room": Setting(id="cozy_room", place="the cozy room", cozy_detail="A small lamp on the shelf",
                         sound="tick-tick", tags={"cozy"}),
    "porch": Setting(id="porch", place="the porch", cozy_detail="The railing was warm from the sun",
                     sound="tap-tap", tags={"cozy"}),
    "kitchen": Setting(id="kitchen", place="the kitchen", cozy_detail="A kettle rested on the stove",
                       sound="plink-plink", tags={"cozy"}),
}

DIM_ITEMS = {
    "lantern": DimItem(id="lantern", label="the little lantern", glow_word="glow", restore_word="brighten",
                       source="battery", is_luck_dim=True, tags={"luck-dim", "glow"}),
    "nightlight": DimItem(id="nightlight", label="the night-light", glow_word="glow", restore_word="shine",
                          source="plug", is_luck_dim=True, tags={"luck-dim", "glow"}),
    "starjar": DimItem(id="starjar", label="the star jar", glow_word="twinkle", restore_word="sparkle",
                       source="glass", is_luck_dim=True, tags={"luck-dim", "glow"}),
}

HELP_ACTIONS = {
    "replace_battery": HelpAction(id="replace_battery", sense=3, power=2,
                                  text="Together they swapped in a fresh battery, and the little lantern hummed brighter",
                                  fail="They tried a new battery, but the light stayed sleepy",
                                  qa_text="replaced the battery and made the light brighter",
                                  tags={"kindness", "sound"}),
    "warm_hands": HelpAction(id="warm_hands", sense=2, power=1,
                             text="They cupped their hands around the lantern and waited patiently",
                             fail="They cupped their hands around it, but it needed more help",
                             qa_text="cupped their hands around it and waited kindly",
                             tags={"kindness"}),
    "clean_glass": HelpAction(id="clean_glass", sense=3, power=2,
                              text="They wiped the glass clean, and the glow returned with a soft shimmer",
                              fail="They wiped the glass, but the dimness stayed",
                              qa_text="wiped the glass clean so the glow could return",
                              tags={"kindness", "sound"}),
}

SENSE_MIN = 2

GIRL_NAMES = ["Nia", "Maya", "Lena", "Ivy", "Rose", "Ava"]
BOY_NAMES = ["Milo", "Ben", "Theo", "Owen", "Finn", "Kai"]


@dataclass
class StoryParams:
    setting: str
    item: str
    action: str
    child_name: str = "Milo"
    child_gender: str = "boy"
    helper_name: str = "Nia"
    helper_gender: str = "girl"
    helper_role: str = "neighbor"
    delay: int = 0
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


def valid_lookup(params: StoryParams) -> bool:
    return params.setting in SETTINGS and params.item in DIM_ITEMS and params.action in HELP_ACTIONS


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for did, d in DIM_ITEMS.items():
        lines.append(asp.fact("item", did))
        if d.is_luck_dim:
            lines.append(asp.fact("luck_dim", did))
    for aid, a in HELP_ACTIONS.items():
        lines.append(asp.fact("help", aid))
        lines.append(asp.fact("sense", aid, a.sense))
        lines.append(asp.fact("power", aid, a.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, I, A) :- setting(S), item(I), luck_dim(I), help(A), sense(A, N), sense_min(M), N >= M.
restores(I, A) :- luck_dim(I), help(A), power(A, P), P >= 1.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos")
        print("only in python:", sorted(py - cl))
        print("only in asp:", sorted(cl - py))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: smoke-tested generate() with default-resolved params.")
    except Exception as e:
        print(f"FAIL: smoke test crashed: {e}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming luck-dim story world with soft sound effects and kindness.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=DIM_ITEMS)
    ap.add_argument("--action", choices=HELP_ACTIONS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["boy", "girl"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["boy", "girl"])
    ap.add_argument("--helper-role", choices=["neighbor", "sister", "brother", "parent"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if args.item and args.item not in DIM_ITEMS:
        raise StoryError("Unknown item.")
    if args.action and args.action not in HELP_ACTIONS:
        raise StoryError("Unknown action.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.item is None or c[1] == args.item)
              and (args.action is None or c[2] == args.action)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, item, action = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["boy", "girl"])
    child_name = args.child_name or rng.choice(BOY_NAMES if child_gender == "boy" else GIRL_NAMES)
    helper_gender = args.helper_gender or ("girl" if child_gender == "boy" else "boy")
    helper_name = args.helper_name or rng.choice(GIRL_NAMES if helper_gender == "girl" else BOY_NAMES)
    helper_role = args.helper_role or rng.choice(["neighbor", "sister", "brother", "parent"])
    delay = args.delay if args.delay is not None else rng.randint(0, 1)
    return StoryParams(setting=setting, item=item, action=action, child_name=child_name,
                       child_gender=child_gender, helper_name=helper_name, helper_gender=helper_gender,
                       helper_role=helper_role, delay=delay)


def generate(params: StoryParams) -> StorySample:
    if not valid_lookup(params):
        raise StoryError("(Invalid parameters.)")
    world = tell(SETTINGS[params.setting], DIM_ITEMS[params.item], HELP_ACTIONS[params.action],
                 child_name=params.child_name, child_gender=params.child_gender,
                 helper_name=params.helper_name, helper_gender=params.helper_gender,
                 helper_role=params.helper_role, delay=params.delay)
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
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a} {b} {c}" for a, b, c in asp_valid_combos()))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(setting="cozy_room", item="lantern", action="replace_battery", child_name="Milo", child_gender="boy", helper_name="Nia", helper_gender="girl", helper_role="neighbor", delay=0),
            StoryParams(setting="porch", item="nightlight", action="clean_glass", child_name="Lena", child_gender="girl", helper_name="Owen", helper_gender="boy", helper_role="brother", delay=0),
            StoryParams(setting="kitchen", item="starjar", action="warm_hands", child_name="Kai", child_gender="boy", helper_name="Rose", helper_gender="girl", helper_role="sister", delay=1),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 25):
            i += 1
            try:
                p = resolve_params(args, random.Random(base_seed + i))
            except StoryError as e:
                print(e)
                return
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for idx, s in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(s, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
