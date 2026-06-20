#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/pierce_blot_happy_ending_pirate_tale.py
=======================================================================

A small standalone storyworld for a pirate-tale style scene built from the seed
words "pierce" and "blot" with a happy ending.

The domain: two child pirates are decorating a paper map and a sail for pretend
adventure. A sharp point can pierce the paper and leave an ink blot, so one child
wants to use a safer tool, a grown-up warns them, and the story resolves with a
gentle repair and a bright ending image: the map is patched, the blot becomes a
dot of treasure, and the crew sails on happily.

This script follows the Storyweavers storyworld contract:
- self-contained stdlib script
- imports storyworlds/results.py eagerly
- defines StoryParams, registries, build_parser, resolve_params, generate, emit,
  and main
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



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Theme:
    id: str
    scene: str
    rig: str
    captain: str
    mate: str
    goal: str
    dark_spot: str
    treasure_word: str
    send_off: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Tool:
    id: str
    label: str
    phrase: str
    where: str
    action: str
    makes_cut: bool = False
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Target:
    id: str
    label: str
    the: str
    near: str
    fragile: bool = False
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Fix:
    id: str
    label: str
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


def _r_smudge(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["smudged"] < THRESHOLD:
            continue
        sig = ("smudge", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "deck" in world.entities:
            world.get("deck").meters["mess"] += 1
        for cid in ("hero", "mate"):
            if cid in world.entities:
                world.get(cid).memes["worry"] += 1
        out.append("__smudge__")
    return out


CAUSAL_RULES = [Rule("smudge", "physical", _r_smudge)]


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


def hazard(tool: Tool, target: Target) -> bool:
    return tool.makes_cut and target.fragile


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.power >= 2]


def is_reasonable(tool: Tool, target: Target) -> bool:
    return hazard(tool, target)


def story_severity(target: Target, delay: int) -> int:
    return 1 + delay


def would_fix(fix: Fix, target: Target, delay: int) -> bool:
    return fix.power >= story_severity(target, delay)


def predict_blot(world: World, target_id: str) -> dict:
    sim = world.copy()
    _do_pierce(sim, sim.get(target_id), narrate=False)
    return {"smudged": sim.get(target_id).meters["smudged"] >= THRESHOLD,
            "mess": sim.get("deck").meters["mess"] if "deck" in sim.entities else 0}


def _do_pierce(world: World, target: Entity, narrate: bool = True) -> None:
    target.meters["smudged"] += 1
    propagate(world, narrate=narrate)


def set_scene(world: World, a: Entity, b: Entity, theme: Theme) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"On a bright afternoon, {a.id} and {b.id} turned the deck into {theme.scene}. "
        f"{theme.rig}"
    )
    world.say(
        f'"{theme.captain} {a.id} and {theme.mate} {b.id}!" {a.id} shouted. '
        f'"Let\'s reach {theme.goal}!"'
    )


def need_map(world: World, b: Entity, theme: Theme, target: Target) -> None:
    world.say(
        f"But the {theme.dark_spot} was shadowy, and {target.drape if hasattr(target, "drape") else target.near} waited in the dark."
    )


def tempt(world: World, a: Entity, tool: Tool) -> None:
    world.say(
        f'{a.id} pointed at {tool.label}. "{tool.action} would be quicker," {a.id} said.'
    )


def warn(world: World, b: Entity, a: Entity, tool: Tool, target: Target, parent: Entity) -> None:
    pred = predict_blot(world, "target")
    b.memes["caution"] += 1
    world.facts["predicted_mess"] = pred["mess"]
    world.say(
        f'{b.id} frowned. "{parent.label_word.capitalize()} said not to touch {tool.label}, '
        f"and it could {tool.action} the paper near {target.the}."
    )


def defy(world: World, a: Entity, b: Entity, tool: Tool) -> None:
    a.memes["defiance"] += 1
    world.say(f'"{a.id} can handle it," {a.id} said, and reached for {tool.phrase}.')


def pierce(world: World, tool_ent: Entity, target_ent: Entity, tool: Tool, target: Target) -> None:
    _do_pierce(world, target_ent)
    world.say(
        f"{tool.label.capitalize()} slipped. The point pierced {target.near}, and a dark blot spread on the paper."
    )


def alarm(world: World, b: Entity, a: Entity, target: Target, parent: Entity) -> None:
    world.say(f'"{a.id}! The {target.label}!" {b.id} cried.')
    world.say(f'"{parent.label_word.upper()}!"')


def rescue(world: World, parent: Entity, fix: Fix, target_ent: Entity, target: Target) -> None:
    target_ent.meters["smudged"] = 0.0
    world.get("deck").meters["mess"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} came running and {fix.text.replace('{target}', target.label)}."
    )
    world.say("The blot stayed small, and the map was safe again.")


def lesson(world: World, parent: Entity, a: Entity, b: Entity, tool: Tool) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
    world.say("For a moment, nobody spoke.")
    world.say(
        f"Then {parent.label_word.capitalize()} knelt beside them. "
        f'"I am glad you called me," {parent.pronoun()} said. '
        f'"A sharp tool can pierce paper fast, so it is not a game."'
    )
    world.say(f'"We promise," whispered {b.id} and {a.id}.')


def gift(world: World, parent: Entity, a: Entity, b: Entity, theme: Theme, fix: Fix) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"The next day, {parent.label_word.capitalize()} brought a softer piece of cloth, a round stamp, and {fix.label}."
    )
    world.say(
        f'"Now," {parent.pronoun()} smiled, "what should a pirate use to make a safe mark on {theme.treasure_word}?"'
    )
    world.say(f"{a.id} stamped a neat dot. {b.id} tied the map to the mast.")
    world.say(f'“{theme.send_off},” they cheered, and the crew sailed on with a happy heart.')


def fail_rescue(world: World, parent: Entity, fix: Fix, target_ent: Entity, target: Target) -> None:
    world.get("deck").meters["mess"] += 1
    target_ent.meters["smudged"] += 1
    world.say(f"{parent.label_word.capitalize()} came running, but {fix.fail.replace('{target}', target.label)}.")
    world.say("The blot grew across the page, yet the little crew stayed together.")


def happy_end(world: World, parent: Entity, a: Entity, b: Entity, theme: Theme, fix: Fix) -> None:
    a.memes["love"] += 1
    b.memes["love"] += 1
    world.say("Soon the page dried, the repair held, and the map showed the way again.")
    world.say(
        f"{a.id} and {b.id} leaned over the fresh patch, grinning at the new bright dot beside the trail."
    )
    world.say(f"{theme.send_off.capitalize()}, safe and proud.")


def tell(theme: Theme, tool: Tool, target: Target, fix: Fix, delay: int = 0,
         hero_name: str = "Pip", mate_name: str = "Mara",
         hero_gender: str = "boy", mate_gender: str = "girl",
         parent_type: str = "mother") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    mate = world.add(Entity(id=mate_name, kind="character", type=mate_gender, role="mate"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    deck = world.add(Entity(id="deck", type="deck", label="the deck"))
    tool_ent = world.add(Entity(id="tool", type="tool", label=tool.label))
    tgt = world.add(Entity(id="target", type="target", label=target.label))
    set_scene(world, hero, mate, theme)
    world.para()
    need_map(world, mate, theme, target)
    tempt(world, hero, tool)
    warn(world, mate, hero, tool, target, parent)
    world.para()
    defy(world, hero, mate, tool)
    pierce(world, tool_ent, tgt, tool, target)
    alarm(world, mate, hero, target, parent)
    world.para()
    if would_fix(fix, target, delay):
        rescue(world, parent, fix, tgt, target)
        lesson(world, parent, hero, mate, tool)
        world.para()
        gift(world, parent, hero, mate, theme, fix)
        outcome = "happy"
    else:
        fail_rescue(world, parent, fix, tgt, target)
        happy_end(world, parent, hero, mate, theme, fix)
        outcome = "repaired"
    world.facts.update(hero=hero, mate=mate, parent=parent, theme=theme, tool=tool,
                       target_cfg=target, target=tgt, fix=fix, outcome=outcome,
                       delay=delay)
    return world


THEMES = {
    "pirates": Theme("pirates", "a pretend pirate deck",
                     "A chair became the captain's seat, a blanket became a sail, and a toy chest held the treasure.",
                     "Captain", "Mate", "the treasure islet", "the shadowy chart corner", "treasure map",
                     "sailing toward the shining shore"),
    "island": Theme("island", "a sandy island camp",
                    "A crate became a lookout, a towel became a flag, and a shell jar held the treasure.",
                    "Captain", "Scout", "the hidden cove", "the dark sand patch", "secret map",
                    "rowing back to the safe beach"),
}

TOOLS = {
    "pin": Tool("pin", "a sharp pin", "a sharp pin", "in a tin cup", "pierce", makes_cut=True, tags={"sharp", "pierce"}),
    "needle": Tool("needle", "a needle", "a needle", "in a sewing kit", "pierce", makes_cut=True, tags={"sharp", "pierce"}),
    "stick": Tool("stick", "a pointy stick", "a pointy stick", "behind a bucket", "poke", makes_cut=True, tags={"sharp", "pierce"}),
}

TARGETS = {
    "map": Target("map", "paper map", "the paper map", "the thin edge of the map", fragile=True, tags={"paper", "blot"}),
    "sail": Target("sail", "cloth sail", "the cloth sail", "the white cloth of the sail", fragile=True, tags={"cloth", "blot"}),
}

FIXES = {
    "patch": Fix("patch", "a soft patch", 3,
                 "taped a soft patch over {target} and smoothed the paper flat",
                 "pressed a patch on, but the mark spread anyway",
                 "taped a soft patch over {target}",
                 tags={"patch", "repair"}),
    "stamp": Fix("stamp", "a round stamp", 3,
                 "pressed a round stamp over the blot and made it look like treasure",
                 "pressed a stamp, but the blot was too wild to hide",
                 "pressed a round stamp over the blot",
                 tags={"stamp", "repair"}),
    "cloth": Fix("cloth", "a small cloth", 2,
                 "wiped the blot with a small cloth and dried the page carefully",
                 "wiped, but the blot was too deep to clear",
                 "wiped the blot with a small cloth",
                 tags={"cloth", "repair"}),
}

GIRL_NAMES = ["Mara", "Nia", "Lena", "Tia", "Rosa", "Mina"]
BOY_NAMES = ["Pip", "Jace", "Finn", "Toby", "Nico", "Ezra"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for theme in THEMES:
        for tool in TOOLS:
            for target in TARGETS:
                if hazard(TOOLS[tool], TARGETS[target]):
                    combos.append((theme, tool, target))
    return combos


@dataclass
@dataclass
class StoryParams:
    theme: str
    tool: str
    target: str
    fix: str
    hero: str
    hero_gender: str
    mate: str
    mate_gender: str
    parent: str
    delay: int = 0
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with pierce/blot and a happy ending.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["boy", "girl"])
    ap.add_argument("--mate")
    ap.add_argument("--mate-gender", choices=["boy", "girl"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="head start for the blot/problem")
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


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool and args.target:
        if not hazard(TOOLS[args.tool], TARGETS[args.target]):
            raise StoryError("No story: that tool cannot make the kind of blot this tale needs.")
    combos = [c for c in valid_combos()
              if (args.theme is None or c[0] == args.theme)
              and (args.tool is None or c[1] == args.tool)
              and (args.target is None or c[2] == args.target)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, tool, target = rng.choice(sorted(combos))
    fix = args.fix or rng.choice(sorted(FIXES))
    hero_gender = args.hero_gender or rng.choice(["boy", "girl"])
    mate_gender = args.mate_gender or ("girl" if hero_gender == "boy" else "boy")
    hero = args.hero or _pick_name(rng, hero_gender)
    mate = args.mate or _pick_name(rng, mate_gender)
    parent = args.parent or rng.choice(["mother", "father"])
    delay = args.delay if args.delay is not None else rng.randint(0, 1)
    return StoryParams(theme, tool, target, fix, hero, hero_gender, mate, mate_gender, parent, delay)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    theme, tool, target = f["theme"], f["tool"], f["target_cfg"]
    return [
        f'Write a pirate tale for a young child that includes the words "pierce" and "blot".',
        f"Tell a happy-ending story where {f['hero'].id} reaches for {tool.label}, but a parent helps prevent a blot on {target.the}.",
        f"Write a short pirate story about a safe repair after a point can pierce {target.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, mate, parent = f["hero"], f["mate"], f["parent"]
    tool, target, fix = f["tool"], f["target_cfg"], f["fix"]
    out = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {hero.id} and {mate.id}, two little pirates, and {parent.label_word} who helped them stay safe."
        ),
        QAItem(
            question=f"Why did {mate.id} warn {hero.id}?",
            answer=f"{mate.id} warned {hero.id} because {tool.label} could pierce {target.the} and leave a blot on the map. The paper was fragile, so the wrong tool would have ruined the adventure."
        ),
    ]
    if f["outcome"] == "happy":
        out.append(QAItem(
            question="How did they fix the problem?",
            answer=f"They used {fix.label} to repair the mark and keep the map useful. That gentle fix turned the scary blot into a safe part of the story."
        ))
        out.append(QAItem(
            question="How did the story end?",
            answer=f"It ended happily, with the page repaired and the little pirates sailing on. The finished map still worked, so the crew could keep exploring."
        ))
    else:
        out.append(QAItem(
            question="What changed after the repair?",
            answer=f"The blot was cleaned or covered, and the page dried safely. After that, the children could keep their pirate game going."
        ))
    return out


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["tool"].tags) | set(world.facts["target_cfg"].tags) | set(world.facts["fix"].tags)
    qa: list[QAItem] = []
    if "pierce" in tags:
        qa.append(QAItem("What does pierce mean?", "To pierce something is to make a tiny hole or opening in it with a sharp point. Paper and cloth can be pierced easily if the point is sharp."))
    if "blot" in tags:
        qa.append(QAItem("What is a blot?", "A blot is a dark spot or mark, often made by ink or water. On paper, a blot can spread and make the page messy."))
    if "repair" in tags:
        qa.append(QAItem("What does repair mean?", "To repair something means to fix it so it works or looks better again. A patch or careful covering can repair a small problem."))
    return qa


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines += [f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)]
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("pirates", "pin", "map", "patch", "Pip", "boy", "Mara", "girl", "mother", 0),
    StoryParams("pirates", "needle", "sail", "stamp", "Nia", "girl", "Jace", "boy", "father", 0),
    StoryParams("island", "stick", "map", "cloth", "Finn", "boy", "Tia", "girl", "mother", 1),
]


def explain_response(fid: str) -> str:
    f = FIXES[fid]
    better = ", ".join(sorted(s.id for s in sensible_fixes()))
    return f"(Refusing fix '{fid}': it is too weak for the tale's happy ending. Try one of: {better}.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if t.makes_cut:
            lines.append(asp.fact("makes_cut", tid))
    for tid, t in TARGETS.items():
        lines.append(asp.fact("target", tid))
        if t.fragile:
            lines.append(asp.fact("fragile", tid))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("power", fid, f.power))
    lines.append(asp.fact("min_power", 2))
    return "\n".join(lines)


ASP_RULES = r"""
hazard(Tool, Target) :- makes_cut(Tool), fragile(Target).
sensible(Fix) :- fix(Fix), power(Fix, P), min_power(M), P >= M.
valid(T, Tool, Target) :- theme(T), tool(Tool), target(Target), hazard(Tool, Target).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP valid_combos differs from Python.")
    if set(asp_sensible()) != {f.id for f in sensible_fixes()}:
        rc = 1
        print("MISMATCH: ASP sensible fixes differs from Python.")
    try:
        s = generate(CURATED[0])
        assert s.story
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    else:
        print("OK: smoke test generated a story.")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(THEMES[params.theme], TOOLS[params.tool], TARGETS[params.target], FIXES[params.fix], params.delay, params.hero, params.mate, params.hero_gender, params.mate_gender, params.parent)
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible (theme, tool, target) combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            try:
                p = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1
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
