#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/combat_pasta_optimistic_suspense_curiosity_conflict_fairy.py
===========================================================================================

A small fairy-tale storyworld about a moonlit kitchen, a curious child, a tiny
bit of combat, and an optimistic ending where pasta helps everyone make peace.

The world is intentionally small and state-driven:
- a fairy-cottage kitchen
- a missing pot of pasta sauce
- a curious child and a guarded helper
- a short suspense beat in the pantry
- a conflict that turns into a playful combat of spoons and spells
- a bright ending where supper is saved and everyone feels hopeful

This script follows the Storyweavers world contract:
- stdlib-only
- typed entities with physical meters and emotional memes
- world state drives prose
- separate prompts, story-grounded QA, and world-knowledge QA
- inline ASP twin plus Python reasonableness gate
- --verify runs parity checks and a smoke test of generation
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
SUSPENSE_MIN = 1


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "fairy"}
        male = {"boy", "father", "dad", "man", "knight"}
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
    detail: str
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
class Hero:
    id: str
    type: str
    gender: str
    role: str = "hero"
    optimistic: bool = True
    curious: bool = True
    brave: bool = True
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Trouble:
    id: str
    label: str
    kind: str
    hideout: str
    clue: str
    dangerous: bool = True
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
class Tool:
    id: str
    label: str
    helps: str
    safe: bool = True
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


def _r_tension(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("missing"):
        for eid in ("hero", "helper"):
            if eid in world.entities:
                world.get(eid).memes["suspense"] += 1
                world.get(eid).memes["curiosity"] += 1
        if ("tension",) not in world.fired:
            world.fired.add(("tension",))
            out.append("__tension__")
    return out


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("squabble") and ("conflict",) not in world.fired:
        world.fired.add(("conflict",))
        world.get("hero").memes["conflict"] += 1
        world.get("helper").memes["conflict"] += 1
        out.append("__conflict__")
    return out


CAUSAL_RULES = [Rule("tension", "social", _r_tension), Rule("conflict", "social", _r_conflict)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def reason_ok(trouble: Trouble, tool: Tool) -> bool:
    return trouble.dangerous and tool.safe


def sensible_tools() -> list[Tool]:
    return [t for t in TOOLS.values() if t.safe]


def _do_mischief(world: World, trouble: Trouble, narrate: bool = True) -> None:
    world.facts["missing"] = True
    world.get("kitchen").meters["unease"] += 1
    propagate(world, narrate=narrate)
    if narrate:
        world.say(f"The kitchen grew quiet, and the {trouble.label} seemed to listen.")


def investigate(world: World, hero: Entity, helper: Entity, trouble: Trouble) -> None:
    world.say(
        f"On a moon-soft evening, {hero.id} and {helper.id} stood in the fairy cottage "
        f"where the air smelled of warm herbs and butter. {world.facts['setting'].detail}"
    )
    world.say(
        f"They had planned a feast of pasta for the lantern celebration, but the {trouble.label} was gone."
    )
    hero.memes["hope"] += 1
    helper.memes["hope"] += 1


def suspense(world: World, hero: Entity, helper: Entity, trouble: Trouble) -> None:
    world.say(
        f"{helper.id} peeked toward {trouble.hideout}. \"I heard a tiny scritch near the pantry,\" {helper.pronoun()} whispered."
    )
    world.say(
        f"{hero.id}'s eyes widened with curiosity. \"Then let's look kindly and carefully,\" {hero.pronoun()} said."
    )
    world.facts["squabble"] = True


def conflict_scene(world: World, hero: Entity, helper: Entity, trouble: Trouble) -> None:
    hero.memes["defiance"] += 1
    helper.memes["worry"] += 1
    world.say(
        f"In the pantry doorway, a grumpy sprite puffed up and guarded the shelf, declaring that the {trouble.label} belonged to him."
    )
    world.say(
        f"{hero.id} and {helper.id} stepped closer, and for a breath it felt like a tiny combat of spoons, sparks, and stubborn hearts."
    )


def resolve(world: World, hero: Entity, helper: Entity, tool: Tool, trouble: Trouble) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    hero.memes["conflict"] = 0
    helper.memes["conflict"] = 0
    world.get("kitchen").meters["unease"] = 0
    world.say(
        f"Then {helper.id} found a safe tool: {tool.label}. It {tool.helps}, and the sprite blinked at the gentle light."
    )
    world.say(
        f"{hero.id} did not attack; {hero.pronoun()} bowed, offered a bowl of pasta, and asked the sprite to share instead."
    )
    world.say(
        f"The sprite's grumpy face softened. The {trouble.label} came back, and the quarrel turned into a supper table."
    )
    world.say(
        f"At last everyone twirled noodles together, and the moon looked bright and optimistic over the cottage roof."
    )


SETTINGS = {
    "cottage": Setting(
        id="cottage",
        place="a fairy cottage kitchen",
        mood="moon-soft",
        detail="A little blue kettle hummed on the hearth, and a silver spoon hung by the door.",
    ),
    "garden": Setting(
        id="garden",
        place="a moonlit garden feast",
        mood="moon-bright",
        detail="The roses leaned over the table, and fireflies blinked like tiny candles.",
    ),
}

TROUBLES = {
    "pasta": Trouble(
        id="pasta",
        label="pasta bowl",
        kind="pasta",
        hideout="the pantry shelf",
        clue="a noodle trail",
        dangerous=False,
        tags={"pasta"},
    ),
    "sauce": Trouble(
        id="sauce",
        label="pasta sauce",
        kind="sauce",
        hideout="behind the flour jar",
        clue="a red drip",
        dangerous=True,
        tags={"pasta"},
    ),
    "key": Trouble(
        id="key",
        label="silver key",
        kind="key",
        hideout="inside the sugar tin",
        clue="a bright clink",
        dangerous=True,
        tags={"curiosity"},
    ),
}

TOOLS = {
    "lantern": Tool(
        id="lantern",
        label="a lantern of kind light",
        helps="made the shadows small enough to search without fear",
        safe=True,
        tags={"suspense"},
    ),
    "spoon": Tool(
        id="spoon",
        label="a wooden spoon",
        helps="helped stir the pot and keep hands busy",
        safe=True,
        tags={"conflict"},
    ),
    "net": Tool(
        id="net",
        label="a ribbon net",
        helps="lifted the missing thing down without a scramble",
        safe=True,
        tags={"curiosity"},
    ),
}

HERO_NAMES = ["Lina", "Milo", "Tess", "Rowan", "Pip", "Nora"]
HELPER_NAMES = ["Bram", "Elsie", "Marin", "Ivo", "Wren", "Poppy"]


@dataclass
class StoryParams:
    setting: str
    trouble: str
    tool: str
    hero_name: str
    helper_name: str
    hero_gender: str
    helper_gender: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for tid, trouble in TROUBLES.items():
            for tool in TOOLS.values():
                if reason_ok(trouble, tool):
                    combos.append((sid, tid, tool.id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld about pasta, suspense, curiosity, conflict, and an optimistic ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--tool", choices=TOOLS)
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
    if args.trouble and not TROUBLES[args.trouble].dangerous and args.tool is None:
        # allow; harmless trouble still makes a tale, but no conflict-heavy arc
        pass
    if args.setting and args.trouble and args.tool:
        if not reason_ok(TROUBLES[args.trouble], TOOLS[args.tool]):
            raise StoryError("That tool cannot reasonably solve that trouble.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.trouble is None or c[1] == args.trouble)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    sid, tid, tool = rng.choice(sorted(combos))
    hero_name = rng.choice(HERO_NAMES)
    helper_name = rng.choice([n for n in HELPER_NAMES if n != hero_name])
    hero_gender = rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["girl", "boy"])
    return StoryParams(
        setting=sid,
        trouble=tid,
        tool=tool,
        hero_name=hero_name,
        helper_name=helper_name,
        hero_gender=hero_gender,
        helper_gender=helper_gender,
    )


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    trouble = TROUBLES[params.trouble]
    tool = TOOLS[params.tool]
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_gender, role="hero"))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_gender, role="helper"))
    kitchen = world.add(Entity(id="kitchen", kind="thing", type="room", label="the kitchen"))
    world.facts.update(setting=setting, trouble=trouble, tool=tool)
    investigate(world, hero, helper, trouble)
    world.para()
    if trouble.dangerous:
        suspense(world, hero, helper, trouble)
        conflict_scene(world, hero, helper, trouble)
        _do_mischief(world, trouble, narrate=False)
        world.para()
        resolve(world, hero, helper, tool, trouble)
    else:
        world.say(
            f"They found the {trouble.label} at once, and the whole kitchen breathed easier."
        )
        world.say(
            f"No combat was needed; the little mystery was solved by curiosity and a smile."
        )
        hero.memes["joy"] += 1
        helper.memes["joy"] += 1
    world.facts.update(hero=hero, helper=helper, kitchen=kitchen, outcome="happy" if trouble.dangerous else "gentle")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy tale for a 3-to-5-year-old that includes the words "combat", "pasta", and "optimistic".',
        f"Tell a moonlit fairy-cottage story where {f['hero'].id} and {f['helper'].id} search for {f['trouble'].label} with curiosity, face a small conflict, and end optimistic.",
        f"Write a gentle story with suspense in a pantry, a tiny combat of spoons, and pasta at the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, helper, trouble = f["hero"], f["helper"], f["trouble"]
    return [
        ("Who is the story about?",
         f"It is about {hero.id} and {helper.id}, two small fairy-tale helpers in a moonlit kitchen. They begin with worry, but they keep going together."),
        ("Why was there suspense in the story?",
         f"There was suspense because something important was missing, and the children had to search the pantry to find it. The quiet hiding place made everyone pause and listen."),
        ("What caused the conflict?",
         f"A grumpy sprite tried to guard the pantry shelf, so the children and the sprite disagreed. That disagreement turned into a little combat of spoons and stubborn hearts before kindness won."),
        ("How did the story end?",
         f"It ended with pasta shared at the table and everyone feeling optimistic. The missing thing came back, and the moon over the cottage looked bright and safe."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["trouble"].tags) | set(f["tool"].tags)
    if f["trouble"].kind == "pasta":
        tags.add("pasta")
    out = []
    if "pasta" in tags:
        out.append(("What is pasta?",
                    "Pasta is a food made from dough, often shaped like noodles or little tubes. It is usually cooked in hot water and eaten warm."))
    if "suspense" in tags:
        out.append(("What is suspense?",
                    "Suspense is the feeling that something important is about to happen, so you want to keep watching or listening."))
    if "curiosity" in tags:
        out.append(("What is curiosity?",
                    "Curiosity is the wish to look, ask, and learn about something you do not yet understand."))
    if "conflict" in tags:
        out.append(("What is conflict?",
                    "Conflict is when two sides want different things and they do not agree at first."))
    return out


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in TROUBLES.items():
        lines.append(asp.fact("trouble", tid))
        if t.dangerous:
            lines.append(asp.fact("dangerous", tid))
    for uid, u in TOOLS.items():
        lines.append(asp.fact("tool", uid))
        if u.safe:
            lines.append(asp.fact("safe", uid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,T,U) :- setting(S), trouble(T), tool(U), dangerous(T), safe(U).
"""


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
        print("MISMATCH in valid combos.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, trouble=None, tool=None), random.Random(7)))
        _ = sample.story
        print("OK: smoke test generated a story.")
    except Exception as e:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.trouble not in TROUBLES or params.tool not in TOOLS:
        raise StoryError("Unknown trouble or tool.")
    if not reason_ok(TROUBLES[params.trouble], TOOLS[params.tool]):
        raise StoryError("That combination is not reasonable for this fairy tale.")
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
        print("--- world model state ---")
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            print(f"  {e.id}: meters={meters} memes={memes}")
    if qa:
        print()
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


CURATED = [
    StoryParams(setting="cottage", trouble="sauce", tool="lantern", hero_name="Lina", helper_name="Bram", hero_gender="girl", helper_gender="boy"),
    StoryParams(setting="garden", trouble="key", tool="net", hero_name="Pip", helper_name="Wren", hero_gender="boy", helper_gender="girl"),
    StoryParams(setting="cottage", trouble="sauce", tool="spoon", hero_name="Nora", helper_name="Milo", hero_gender="girl", helper_gender="boy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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

    for i, s in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(s, trace=args.trace, qa=args.qa)
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
