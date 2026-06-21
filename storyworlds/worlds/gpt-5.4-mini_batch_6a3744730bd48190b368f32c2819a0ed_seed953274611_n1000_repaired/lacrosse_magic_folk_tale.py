#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/lacrosse_magic_folk_tale.py
===========================================================

A standalone storyworld for a small folk-tale shaped lacrosse-and-magic domain.

Premise: a child wants to play lacrosse in an old village clearing.
Tension: the field is enchanted, and a greedy snag or spell makes the game go wrong.
Turn: a wise helper uses gentle magic and a sensible action to restore the game.
Resolution: the game ends with a bright, shared image that proves what changed.

The world is intentionally small and constraint-checked: each story is built from
a simulated world state, not from a frozen paragraph with swapped names.
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)
    magic: bool = False
    tool: bool = False
    enchanted: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
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
    mood: str
    field: str
    sky: str
    home: str
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
class ChildCfg:
    id: str
    type: str
    age: int
    trait: str
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
class MagicCfg:
    id: str
    label: str
    phrase: str
    effect: str
    safe: bool = True
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class TroubleCfg:
    id: str
    label: str
    phrase: str
    snag: str
    power: int
    magic: bool = True
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class FixCfg:
    id: str
    label: str
    phrase: str
    action: str
    power: int
    glow: str
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]
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


def _r_spell_spreads(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["spell"] < THRESHOLD:
            continue
        sig = ("spell", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "field" in world.entities:
            world.get("field").meters["glow"] += 1
        for c in world.characters():
            c.memes["wonder"] += 1
        out.append("__spell__")
    return out


def _r_snag_bites(world: World) -> list[str]:
    out: list[str] = []
    field = world.entities.get("field")
    if not field or field.meters["glow"] < THRESHOLD:
        return out
    sig = ("snag", "field")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    field.meters["snagged"] += 1
    for c in world.characters():
        c.memes["worry"] += 1
    out.append("The old field answered with a twisting snag.")
    return out


CAUSAL_RULES = [Rule("spell_spreads", _r_spell_spreads), Rule("snag_bites", _r_snag_bites)]


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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for tid, t in TROUBLES.items():
            if not t.magic:
                continue
            for fid, f in FIXES.items():
                if f.power >= t.power:
                    combos.append((sid, tid, fid))
    return combos


@dataclass
class StoryParams:
    setting: str = "village_green"
    child: str = "Mara"
    child_type: str = "girl"
    helper: str = "Bram"
    helper_type: str = "boy"
    trouble: str = "snarl"
    fix: str = "song"
    magic: str = "spark_stick"
    seed: Optional[int] = None
    delay: int = 0
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
    "village_green": Setting(
        id="village_green",
        place="the village green",
        mood="bright and breezy",
        field="a wide playing field",
        sky="high blue sky",
        home="by the old oak",
    ),
    "moon_field": Setting(
        id="moon_field",
        place="the moonlit field",
        mood="quiet and silver",
        field="a field of white grass",
        sky="pale moon sky",
        home="beside the well",
    ),
    "river_elm": Setting(
        id="river_elm",
        place="the green by the river",
        mood="soft and singing",
        field="a damp meadow",
        sky="river mist",
        home="near the baker's door",
    ),
}

CHILDREN = {
    "Mara": ChildCfg("Mara", "girl", 7, "curious"),
    "Ivo": ChildCfg("Ivo", "boy", 8, "brave"),
    "Nell": ChildCfg("Nell", "girl", 6, "gentle"),
    "Tobin": ChildCfg("Tobin", "boy", 7, "thoughtful"),
}

MAGICS = {
    "spark_stick": MagicCfg("spark_stick", "a spark stick", "with a flick of the wrist", "a small harmless glow"),
    "silver_whistle": MagicCfg("silver_whistle", "a silver whistle", "with one clear note", "a ring of bright calm"),
    "oak_bell": MagicCfg("oak_bell", "an oak bell", "with a soft ding", "a settling hush"),
}

TROUBLES = {
    "snarl": TroubleCfg("snarl", "a snarl of vines", "the vines twining around the goal", "snag", 1),
    "fog_knot": TroubleCfg("fog_knot", "a fog knot", "the fog curling over the grass", "mist", 1),
    "riddle_wind": TroubleCfg("riddle_wind", "a riddle wind", "the wind spinning the ball away", "wind", 2),
}

FIXES = {
    "song": FixCfg("song", "a quiet song", "to sing the old field calm", "sing", 1, "warm as lantern light"),
    "lace_tie": FixCfg("lace_tie", "a lace tie", "to lace the stick and steady the ball", "tie", 1, "neat and sure"),
    "lantern_walk": FixCfg("lantern_walk", "a lantern walk", "to walk the field and mark the safe path", "walk", 2, "soft gold"),
}


def hazard_ok(trouble: TroubleCfg, fix: FixCfg) -> bool:
    return trouble.magic and fix.power >= trouble.power


def _do_magic(world: World, mage: Entity, magic: MagicCfg, narrate: bool = True) -> None:
    mage.meters["spell"] += 1
    mage.memes["hope"] += 1
    world.say(f"{mage.id} lifted {magic.phrase} and worked it {magic.effect}.")
    propagate(world, narrate=narrate)


def tell(setting: Setting, child: ChildCfg, helper: ChildCfg, trouble: TroubleCfg, fix: FixCfg, magic: MagicCfg, delay: int = 0) -> World:
    world = World()
    c = world.add(Entity(id=child.id, kind="character", type=child.type, role="child", traits=[child.trait], attrs={"age": child.age}))
    h = world.add(Entity(id=helper.id, kind="character", type=helper.type, role="helper", traits=["wise"], attrs={"age": helper.age}))
    field = world.add(Entity(id="field", type="thing", label="the field"))
    goal = world.add(Entity(id="goal", type="thing", label="the goal", enchanted=True))
    staff = world.add(Entity(id="staff", kind="thing", label=magic.label, tool=True, magic=True))
    snag = world.add(Entity(id="snag", kind="thing", label=trouble.label, magic=trouble.magic))
    world.facts["delay"] = delay

    world.say(f"On {setting.place}, under a {setting.sky}, {c.id} and {h.id} came to play lacrosse.")
    world.say(f"The day was {setting.mood}, and the old tale of the green said the game should be fair and kind.")
    world.say(f"They carried {magic.phrase}, because that was the village's magic for hard moments.")
    world.para()
    world.say(f"{c.id} wanted to chase the ball, but {trouble.phrase} made the goal hard to reach.")
    c.memes["want"] += 1
    h.memes["worry"] += 1
    if delay == 0:
        world.say(f"{h.id} frowned, for {h.id} knew the trouble could grow teeth if nobody minded it.")
    else:
        world.say(f"{h.id} saw the trouble had already been left alone for a while.")
    world.para()
    _do_magic(world, h, magic, narrate=False)
    world.say(f"Then {h.id} chose {fix.phrase}, {fix.action}ing the field with care and a steady heart.")
    if fix.power >= trouble.power:
        field.meters["snagged"] = 0
        goal.meters["open"] += 1
        c.memes["joy"] += 1
        h.memes["joy"] += 1
        world.say(f"The spell answered at once. {trouble.label.capitalize()} loosened, and the way to the goal opened wide.")
        world.say(f"{c.id} ran a clean line, sent the ball true, and the whole green shone {magic.effect}.")
        world.para()
        world.say(f"At the end, {c.id} and {h.id} laughed beside the goal, and even the grass looked glad to be part of the tale.")
    else:
        world.say(f"But the fix was too small, and the old trouble stayed knotted.")
        world.say(f"{c.id} and {h.id} had to stop and call for the village keeper instead.")
        world.para()
        world.say(f"They still kept safe, yet the game ended before the field could be mended.")
    world.facts.update(
        setting=setting,
        child=c,
        helper=h,
        trouble=trouble,
        fix=fix,
        magic=magic,
        field=field,
        goal=goal,
        staff=staff,
        outcome="open" if field.meters["snagged"] < THRESHOLD else "stopped",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a folk-tale style story about {f['child'].id} and {f['helper'].id} playing lacrosse on {f['setting'].place}, with a touch of magic.",
        f"Tell a child-friendly magic tale where a lacrosse game meets {f['trouble'].label} and is set right by {f['fix'].label}.",
        f"Create a short folk tale that includes the word lacrosse and ends with the field feeling bright again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(question=f"What game were {f['child'].id} and {f['helper'].id} playing?", answer="They were playing lacrosse on the village green, turning an ordinary day into a folk-tale game. The game matters because it gives the magic a reason to be used."),
        QAItem(question=f"What problem got in the way?", answer=f"{f['trouble'].label.capitalize()} got in the way and made the goal hard to reach. That trouble was exactly why the helper had to use magic with care."),
        QAItem(question=f"How did they fix it?", answer=f"{f['helper'].id} used {f['magic'].label} and chose {f['fix'].label}, which made the field open again. The fix worked because it was strong enough for the trouble."),
        QAItem(question="How did the story end?", answer=f"It ended with the field shining again and the children laughing beside the goal. That ending shows the game was safe and the trouble was gone."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is lacrosse?", answer="Lacrosse is a fast ball game played with sticks that have nets or heads for catching and moving the ball. In a folk tale, it can feel like a brave village contest."),
        QAItem(question="What is magic in a story?", answer="Magic is something wonderful that can make impossible things happen in a story. In folk tales, magic often helps when kindness and courage are not quite enough."),
        QAItem(question="Why do folk tales often feel simple and old?", answer="Folk tales usually sound simple, memorable, and a little timeless because they come from old ways of telling stories aloud. They often repeat important lessons in a gentle way."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.magic:
            bits.append("magic")
        if e.tool:
            bits.append("tool")
        if e.enchanted:
            bits.append("enchanted")
        out.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    out.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(out)


CURATED = [
    StoryParams(setting="village_green", child="Mara", child_type="girl", helper="Bram", helper_type="boy", trouble="snarl", fix="song", magic="spark_stick", delay=0),
    StoryParams(setting="moon_field", child="Ivo", child_type="boy", helper="Nell", helper_type="girl", trouble="fog_knot", fix="lace_tie", magic="silver_whistle", delay=0),
    StoryParams(setting="river_elm", child="Tobin", child_type="boy", helper="Mara", helper_type="girl", trouble="riddle_wind", fix="lantern_walk", magic="oak_bell", delay=1),
]


def explain_rejection(trouble: TroubleCfg, fix: FixCfg) -> str:
    return f"(No story: {fix.label} is not strong enough for {trouble.label}. Pick a fix whose power can match the trouble.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.trouble and args.fix:
        if not hazard_ok(TROUBLES[args.trouble], FIXES[args.fix]):
            raise StoryError(explain_rejection(TROUBLES[args.trouble], FIXES[args.fix]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.trouble is None or c[1] == args.trouble)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, trouble, fix = rng.choice(sorted(combos))
    child = CHILDREN[rng.choice(sorted(CHILDREN))]
    helper_choices = [c for c in CHILDREN.values() if c.id != child.id]
    helper = rng.choice(helper_choices)
    magic = MAGICS[rng.choice(sorted(MAGICS))]
    return StoryParams(setting=setting, child=child.id, child_type=child.type, helper=helper.id, helper_type=helper.type, trouble=trouble, fix=fix, magic=magic.id, delay=args.delay if args.delay is not None else rng.randint(0, 1))


def generate(params: StoryParams) -> StorySample:
    try:
        world = tell(SETTINGS[params.setting], CHILDREN[params.child], CHILDREN[params.helper], TROUBLES[params.trouble], FIXES[params.fix], MAGICS[params.magic], params.delay)
    except KeyError as e:
        raise StoryError(f"Invalid story parameter: {e.args[0]}") from e
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale lacrosse storyworld with a little magic.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--delay", type=int, choices=[0, 1], default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


ASP_RULES = r"""
valid(S,T,F) :- setting(S), trouble(T), fix(F), trouble_power(T,P), fix_power(F,Q), Q >= P.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in TROUBLES.items():
        lines.append(asp.fact("trouble", tid))
        lines.append(asp.fact("trouble_power", tid, t.power))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("fix_power", fid, f.power))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = True
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        ok = False
        print("MISMATCH: ASP and Python valid_combos differ.")
        print("  python:", sorted(set(valid_combos()) - set(asp_valid_combos())))
        print("  asp:", sorted(set(asp_valid_combos()) - set(valid_combos())))
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as e:
        ok = False
        print(f"MISMATCH: smoke test failed: {e}")
    return 0 if ok else 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for t in asp_valid_combos():
            print(t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
