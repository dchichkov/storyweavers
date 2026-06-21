#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/snivel_dialogue_fairy_tale.py
==============================================================

A small fairy-tale storyworld about a child who snivels over a problem, speaks
with a helper in dialogue, and learns a gentler way to solve it.

The world is intentionally tiny: a child, a place, a troublesome object out of
reach, a helper, and a safe tool or method.  The story turns on a state change:
the child starts sad and sniveling, the helper notices the real problem, they
talk, the helper fixes the problem, and the ending proves the change with a
calmer, brighter image.

Seed words: snivel
Feature: dialogue
Style: fairy tale
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
GENTLE_MIN = 2


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
        if self.type in {"girl", "queen", "princess", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "king", "prince", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father", "queen": "queen", "king": "king"}.get(self.type, self.type)
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
    shadow: str
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
class Trouble:
    id: str
    label: str
    phrase: str
    risk: str
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
class HelperTool:
    id: str
    label: str
    phrase: str
    method: str
    power: int
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
class StoryParams:
    setting: str = "rose_garden"
    trouble: str = "stuck_kite"
    helper: str = "fairy"
    tool: str = "ladder"
    child_name: str = "Elin"
    child_type: str = "girl"
    helper_name: str = "Moss"
    helper_type: str = "fairy"
    parent_name: str = "Queen"
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
    "rose_garden": Setting(
        id="rose_garden",
        place="the rose garden",
        mood="under a pale pink sky",
        shadow="behind the briar hedge",
    ),
    "castle_yard": Setting(
        id="castle_yard",
        place="the castle yard",
        mood="beside the old stone tower",
        shadow="under the high window",
    ),
    "moon_lane": Setting(
        id="moon_lane",
        place="the moonlit lane",
        mood="where silver dew lay on the grass",
        shadow="in the pear tree",
    ),
}

TROUBLES = {
    "stuck_kite": Trouble(
        id="stuck_kite",
        label="kite",
        phrase="a bright kite",
        risk="caught in the thorny branches",
        tags={"kite", "high"},
    ),
    "lost_ring": Trouble(
        id="lost_ring",
        label="ring",
        phrase="a little gold ring",
        risk="fallen into the well",
        tags={"ring", "deep"},
    ),
    "stuck_basket": Trouble(
        id="stuck_basket",
        label="basket",
        phrase="a picnic basket",
        risk="hung from a tall branch",
        tags={"basket", "high"},
    ),
}

TOOLS = {
    "ladder": HelperTool(
        id="ladder",
        label="ladder",
        phrase="a leaning ladder",
        method="set up the ladder and reach",
        power=3,
        tags={"high"},
    ),
    "hook_pole": HelperTool(
        id="hook_pole",
        label="hook pole",
        phrase="a long hook pole",
        method="hook it down carefully",
        power=2,
        tags={"high"},
    ),
    "bucket_rope": HelperTool(
        id="bucket_rope",
        label="bucket and rope",
        phrase="a bucket tied to a rope",
        method="lower the bucket and lift it back",
        power=3,
        tags={"deep"},
    ),
    "applecrate_steps": HelperTool(
        id="applecrate_steps",
        label="apple crates",
        phrase="three sturdy apple crates",
        method="stack the crates and climb",
        power=2,
        tags={"high"},
    ),
}

HELPERS = {
    "fairy": ("fairy", "fairy"),
    "owl": ("wise owl", "owl"),
    "grandmother": ("grandmother", "woman"),
}

GIRL_NAMES = ["Elin", "Mira", "Luna", "Tilda", "Nessa", "Sophie", "Ada"]
BOY_NAMES = ["Robin", "Jon", "Pip", "Milo", "Theo", "Hugo", "Otis"]


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


def hazard(trouble: Trouble, tool: HelperTool) -> bool:
    return trouble.id == "lost_ring" and tool.id == "bucket_rope" or trouble.tags & tool.tags == trouble.tags & tool.tags and bool(trouble.tags & tool.tags)


def compatible(trouble: Trouble, tool: HelperTool) -> bool:
    if "high" in trouble.tags:
        return "high" in tool.tags
    if "deep" in trouble.tags:
        return "deep" in tool.tags
    return False


def sensible_tools() -> list[HelperTool]:
    return [t for t in TOOLS.values() if t.id != "applecrate_steps" or t.power >= GENTLE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid in SETTINGS:
        for tid, tr in TROUBLES.items():
            for tool in TOOLS.values():
                if compatible(tr, tool):
                    out.append((sid, tid, tool.id))
    return out


def ask_child(name: str, trouble: Trouble) -> str:
    if trouble.id == "lost_ring":
        return f'"Oh dear," {name} sniveled, "where did my ring go?"'
    return f'"Oh dear," {name} sniveled, "how will I ever reach my {trouble.label}?"'


def tell_setup(world: World, child: Entity, helper: Entity, setting: Setting, trouble: Trouble) -> None:
    world.say(
        f"Once in {setting.place}, {child.id} wandered {setting.mood}. "
        f"The air was sweet, but one small trouble sat {trouble.risk}."
    )
    world.say(ask_child(child.id, trouble))


def tell_dialogue(world: World, child: Entity, helper: Entity, trouble: Trouble, tool: HelperTool) -> None:
    child.memes["worry"] += 1
    world.say(
        f'"Do not fret," said {helper.id}. "I see the problem at once, and I know '
        f'a kinder way."'
    )
    world.say(f'"What way?" asked {child.id}, wiping a snivel from {child.pronoun("possessive")} nose.')
    world.say(
        f'"We shall use {tool.phrase}," said {helper.id}, "and {tool.method}."'
    )


def repair(world: World, trouble: Entity, helper: Entity, tool: HelperTool) -> None:
    trouble.meters["stuck"] = 0.0
    trouble.memes["hope"] += 1
    helper.memes["calm"] += 1
    world.say(
        f"At once {helper.id} used {tool.phrase}. With a careful tug and a soft "
        f"\"There!\" the {trouble.label} came free."
    )


def close_story(world: World, child: Entity, helper: Entity, setting: Setting, trouble: Trouble) -> None:
    child.memes["joy"] += 1
    child.memes["worry"] = 0.0
    world.say(
        f'{child.id} laughed, no longer sniveling. "You were right!" '
        f'{child.id} cried. "The {trouble.label} is ours again!"'
    )
    world.say(
        f"And so they went back through {setting.place}, the {trouble.label} "
        f"held high, while the moon or the roses shone upon them."
    )


ASP_RULES = r"""
compatible(S, T, U) :- setting(S), trouble(T), tool(U), need(T, N), covers(U, N).
valid(S, T, U) :- compatible(S, T, U).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in TROUBLES.items():
        lines.append(asp.fact("trouble", tid))
        if "high" in t.tags:
            lines.append(asp.fact("need", tid, "high"))
        if "deep" in t.tags:
            lines.append(asp.fact("need", tid, "deep"))
    for uid, u in TOOLS.items():
        lines.append(asp.fact("tool", uid))
        for tag in sorted(u.tags):
            lines.append(asp.fact("covers", uid, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        print(" python-only:", sorted(py - cl))
        print(" asp-only:", sorted(cl - py))
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, trouble=None, helper=None, tool=None, child_name=None, child_type=None, helper_name=None, helper_type=None, parent_name=None, seed=None), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld with snivels and dialogue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["fairy", "owl", "woman"])
    ap.add_argument("--parent-name")
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
    if args.setting and args.trouble and args.tool and (args.setting, args.trouble, args.tool) not in combos:
        raise StoryError("(No valid fairy-tale combination matches the given options.)")
    valid = [c for c in combos
             if (args.setting is None or c[0] == args.setting)
             and (args.trouble is None or c[1] == args.trouble)
             and (args.tool is None or c[2] == args.tool)]
    if not valid:
        raise StoryError("(No valid combination matches the given options.)")
    setting, trouble, tool = rng.choice(sorted(valid))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    helper_kind = args.helper_type or rng.choice(list(HELPERS))
    helper_name = args.helper_name or rng.choice(["Moss", "Bracken", "Thistle", "Wren"])
    parent_name = args.parent_name or rng.choice(["Queen", "King", "Mother", "Father"])
    return StoryParams(
        setting=setting,
        trouble=trouble,
        helper=helper_kind,
        tool=tool,
        child_name=child_name,
        child_type=child_type,
        helper_name=helper_name,
        helper_type=helper_kind,
        parent_name=parent_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.trouble not in TROUBLES or params.tool not in TOOLS:
        raise StoryError("Invalid story parameters.")
    setting = SETTINGS[params.setting]
    trouble_cfg = TROUBLES[params.trouble]
    tool = TOOLS[params.tool]
    if not compatible(trouble_cfg, tool):
        raise StoryError("That tool does not fit the trouble.")
    world = World()
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_type, role="child"))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type, role="helper"))
    parent = world.add(Entity(id=params.parent_name, kind="character", type="queen", role="parent"))
    trouble = world.add(Entity(id=trouble_cfg.label, kind="thing", type="thing", label=trouble_cfg.label))
    child.memes["snivel"] += 1
    child.memes["worry"] += 1
    tell_setup(world, child, helper, setting, trouble_cfg)
    world.para()
    tell_dialogue(world, child, helper, trouble_cfg, tool)
    world.para()
    repair(world, trouble, helper, tool)
    close_story(world, child, helper, setting, trouble_cfg)
    world.facts.update(setting=setting, trouble=trouble_cfg, tool=tool, child=child, helper=helper, parent=parent)
    prompts = [
        f'Write a fairy tale that includes the word "snivel" and a dialogue scene where a child asks for help.',
        f'Tell a gentle story about {child.id} in {setting.place} who snivels over {trouble_cfg.label} and speaks with a kind helper.',
        f'Write a child-friendly fairy tale where a helper uses {tool.label} to solve a problem after some dialogue.',
    ]
    story_qa = [
        QAItem(
            question=f"Why was {child.id} sniveling?",
            answer=f"{child.id} was sniveling because {child.pronoun('possessive')} {trouble_cfg.label} was stuck {trouble_cfg.risk}. That made the problem feel big and upsetting until help arrived."
        ),
        QAItem(
            question=f"What did {helper.id} say they would do?",
            answer=f"{helper.id} said they would use {tool.phrase} and {tool.method}. That matched the trouble, so the child had a real reason to hope."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended happily, with the {trouble_cfg.label} free again and the child no longer sniveling. The ending shows that the helper's calm idea worked."
        ),
    ]
    world_qa = [
        QAItem(
            question="What does snivel mean?",
            answer="To snivel means to cry in a small, watery way, often with a runny nose. Children may snivel when they are upset or worried."
        ),
        QAItem(
            question="Why is a ladder useful in a fairy tale garden?",
            answer="A ladder helps someone reach a high place that is out of arm's reach. It is useful for branches, windows, or anything perched up high."
        ),
        QAItem(
            question="Why is a bucket and rope useful for a well?",
            answer="A bucket and rope help lower something into a deep place and bring it back up. That makes it a good tool for a well or another deep spot."
        ),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world model state ---")
        for e in sample.world.entities.values():
            print(f"  {e.id}: kind={e.kind} type={e.type} memes={dict(e.memes)} meters={dict(e.meters)}")
    if qa:
        print()
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print("\n== story qa ==")
        for q in sample.story_qa:
            print(f"Q: {q.question}\nA: {q.answer}")
        print("\n== world qa ==")
        for q in sample.world_qa:
            print(f"Q: {q.question}\nA: {q.answer}")


CURATED = [
    StoryParams(setting="rose_garden", trouble="stuck_kite", helper="fairy", tool="ladder", child_name="Elin", child_type="girl", helper_name="Moss", helper_type="fairy", parent_name="Queen"),
    StoryParams(setting="castle_yard", trouble="lost_ring", helper="owl", tool="bucket_rope", child_name="Robin", child_type="boy", helper_name="Wren", helper_type="owl", parent_name="King"),
    StoryParams(setting="moon_lane", trouble="stuck_basket", helper="grandmother", tool="applecrate_steps", child_name="Mira", child_type="girl", helper_name="Thistle", helper_type="woman", parent_name="Mother"),
]


def generation_prompts(sample: StorySample) -> list[str]:
    return sample.prompts


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for s, t, u in combos:
            print(f"  {s:12} {t:12} {u}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
