#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/material_diabetic_rhyme_reconciliation_magic_superhero_story.py
=================================================================================================

A tiny superhero storyworld about a hero who uses rhyme and magic to solve a
material problem without fighting. The seed words are "material" and
"diabetic"; the world makes them matter by giving the hero a careful body need
and a costume-material dilemma that only cooperation can solve.

The story shape:
- A hero wants to help on a rainy city mission.
- A magical rhyme reveals that the wrong costume material will make a helper sick
  and tired, so the team must pause.
- There is a small conflict between a flashy hero and a careful teammate.
- The heroes reconcile, choose the right material, and use a magic rhyme to
  finish the rescue.

This file is standalone, stdlib-only, and follows the shared Storyweavers
result/ASP contract.
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
BRAVE_INIT = 6.0
CAREFUL_TRAITS = {"careful", "gentle", "thoughtful", "wise", "patient"}


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
    wearable: bool = False
    material: str = ""
    magical: bool = False
    healing: bool = False

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
    weather: str
    color: str
    crowd: str
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
class Material:
    id: str
    label: str
    feels: str
    protects: bool
    comfort: int
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
class Trouble:
    id: str
    label: str
    severity: int
    need: str
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
class MagicLine:
    id: str
    rhyme: str
    effect: str
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


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


def _r_unease(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    sidekick = world.get("sidekick")
    if hero.meters["wrong_material"] >= THRESHOLD and ("unease",) not in world.fired:
        world.fired.add(("unease",))
        sidekick.memes["worry"] += 1
        hero.memes["pressure"] += 1
        out.append("__unease__")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    sidekick = world.get("sidekick")
    if hero.memes["apology"] < THRESHOLD or sidekick.memes["forgiveness"] >= THRESHOLD:
        return out
    if ("reconcile",) in world.fired:
        return out
    world.fired.add(("reconcile",))
    hero.memes["calm"] += 1
    sidekick.memes["trust"] += 1
    out.append("__reconcile__")
    return out


CAUSAL_RULES = [Rule("unease", _r_unease), Rule("reconcile", _r_reconcile)]


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


def safe_materials() -> list[Material]:
    return [m for m in MATERIALS.values() if m.comfort >= 2]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for tid, trouble in TROUBLES.items():
            for mid, mat in MATERIALS.items():
                if trouble.need == "costume" and mat.protects:
                    combos.append((sid, tid, mid))
    return combos


def reason_gate(tid: str, mid: str) -> bool:
    return TROUBLES[tid].need == "costume" and MATERIALS[mid].protects


def choose_line(rng: random.Random) -> MagicLine:
    return rng.choice(list(MAGIC_LINES.values()))


def _do_material_choice(world: World, material: Material) -> None:
    hero = world.get("hero")
    if material.protects:
        hero.meters["right_material"] += 1
    else:
        hero.meters["wrong_material"] += 1


def tell(setting: Setting, trouble: Trouble, material: Material, magic: MagicLine,
         hero_name: str, hero_type: str, sidekick_name: str, sidekick_type: str,
         parent_name: str = "Aunt Nova") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type,
                            role="hero", traits=["bold"], attrs={"diabetic": True}))
    sidekick = world.add(Entity(id=sidekick_name, kind="character", type=sidekick_type,
                                role="sidekick", traits=["careful"],
                                attrs={"diabetic": False}))
    parent = world.add(Entity(id=parent_name, kind="character", type="woman",
                              role="adult", label="the grown-up"))
    suit = world.add(Entity(id="suit", type="thing", label=material.label,
                            wearable=True, material=material.id))
    helper = world.add(Entity(id="helper", type="thing", label=trouble.label))
    hero.memes["bravery"] = BRAVE_INIT
    sidekick.memes["worry"] = 0.0

    world.say(
        f"In {setting.place}, {hero.id} wore a bright cape and raced through the "
        f"rainy night like a comic-book comet. {hero.id} was a diabetic hero, so "
        f"{hero.pronoun()} always kept a snack in {hero.pronoun('possessive')} belt."
    )
    world.say(
        f"{sidekick.id} pointed at the mission table. A sign said the next rescue "
        f"needed the right material for the suit, because the wrong one would rub "
        f"and leave the hero shaky."
    )
    world.para()

    world.say(
        f'"{magic.rhyme}," whispered {sidekick.id}. "{magic.effect}."'
    )
    _do_material_choice(world, material)
    propagate(world, narrate=False)

    if material.protects:
        hero.memes["joy"] += 1
        sidekick.memes["hope"] += 1
        world.say(
            f"{hero.id} smiled and picked the soft {material.label}. It felt "
            f"smooth, not scratchy, and it was the perfect material for a hero "
            f"who needed steady energy."
        )
        world.say(
            f"{hero.id} and {sidekick.id} lifted {helper.label} together and "
            f"used the rhyme again, turning the lights on in a blink."
        )
        world.para()
        world.say(
            f"Then came the hard part: a windy gap between two towers, and a "
            f"crowd below waiting for help. {hero.id} and {sidekick.id} argued "
            f"for one quick moment about who should lead."
        )
        sidekick.memes["forgiveness"] += 1
        hero.memes["apology"] += 1
        propagate(world, narrate=False)
        world.say(
            f"{hero.id} took a breath and said sorry. {sidekick.id} forgave "
            f"{hero.id} at once, because saving the city mattered more than being right."
        )
        world.say(
            f"Together they spoke the rhyme in a clear chorus. The magic answered, "
            f"the bridge of wind settled, and the people below cheered as the two "
            f"heroes landed side by side."
        )
        world.say(
            f"By sunset, the cape still fluttered, the suit still fit, and {hero.id} "
            f"stood tall beside {sidekick.id}, calm and ready for another day."
        )
    else:
        hero.memes["worry"] += 1
        world.say(
            f"The {material.label} turned out wrong. It looked flashy, but it was "
            f"too rough and would have made the diabetic hero feel awful during the rescue."
        )
        world.say(
            f"{sidekick.id} shook {sidekick.pronoun('possessive')} head and called for "
            f"{parent.label_word}. {parent.id} brought the soft spare cloth, and the team "
            f"changed plans before any harm could start."
        )
        world.say(
            f"That was the first real victory: not the loudest one, but the wise one. "
            f"They chose safety, shared the rhyme, and the city waited a little longer."
        )

    world.facts.update(
        setting=setting,
        trouble=trouble,
        material=material,
        magic=magic,
        hero=hero,
        sidekick=sidekick,
        parent=parent,
        suit=suit,
        helper=helper,
        outcome="good" if material.protects else "replaced",
    )
    return world


SETTINGS = {
    "downtown": Setting(id="downtown", place="Downtown Starway", weather="rainy", color="blue", crowd="busy"),
    "harbor": Setting(id="harbor", place="Harbor Lights", weather="windy", color="silver", crowd="sailors"),
    "museum": Setting(id="museum", place="the Museum of Bright Days", weather="quiet", color="gold", crowd="families"),
}

MATERIALS = {
    "silk": Material(id="silk", label="silk material", feels="smooth", protects=True, comfort=3, tags={"material"}),
    "wool": Material(id="wool", label="wool material", feels="soft", protects=True, comfort=3, tags={"material"}),
    "paper": Material(id="paper", label="paper material", feels="crinkly", protects=False, comfort=0, tags={"material"}),
    "plastic": Material(id="plastic", label="plastic material", feels="slick", protects=False, comfort=1, tags={"material"}),
}

TROUBLES = {
    "scratchy_suit": Trouble(id="scratchy_suit", label="scratchy suit", severity=2, need="costume", tags={"costume"}),
    "wrong_wrap": Trouble(id="wrong_wrap", label="wrong wrap", severity=1, need="costume", tags={"costume"}),
}

MAGIC_LINES = {
    "spark_rhyme": MagicLine(id="spark_rhyme", rhyme="bright light, kind light, help arrives tonight", effect="the lock will sing and open", tags={"magic", "rhyme"}),
    "calm_rhyme": MagicLine(id="calm_rhyme", rhyme="soft and slow, steady glow, let the good ideas flow", effect="the team will breathe and choose again", tags={"magic", "rhyme"}),
}

@dataclass
class StoryParams:
    setting: str
    trouble: str
    material: str
    magic: str
    hero_name: str
    hero_type: str
    sidekick_name: str
    sidekick_type: str
    parent_name: str
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


CURATED = [
    StoryParams(
        setting="downtown", trouble="scratchy_suit", material="silk",
        magic="spark_rhyme", hero_name="Nova", hero_type="girl",
        sidekick_name="Pip", sidekick_type="boy", parent_name="Dr. Halo", seed=None
    ),
    StoryParams(
        setting="harbor", trouble="wrong_wrap", material="wool",
        magic="calm_rhyme", hero_name="Rae", hero_type="girl",
        sidekick_name="June", sidekick_type="girl", parent_name="Aunt Nova", seed=None
    ),
    StoryParams(
        setting="museum", trouble="scratchy_suit", material="paper",
        magic="spark_rhyme", hero_name="Miles", hero_type="boy",
        sidekick_name="Tess", sidekick_type="girl", parent_name="Captain Kind", seed=None
    ),
]


KNOWLEDGE = {
    "diabetic": [("What does diabetic mean?", "Diabetic means a person needs to watch their blood sugar and may need snacks or medicine to stay well.")],
    "material": [("What is a material?", "A material is what something is made from, like cloth, paper, or wood.")],
    "rhyme": [("What is a rhyme?", "A rhyme is when words sound alike at the end, like light and night.")],
    "magic": [("What is magic in a story?", "Magic in a story is a special power that makes surprising things happen.")],
    "reconciliation": [("What is reconciliation?", "Reconciliation is when people stop arguing, forgive each other, and work together again.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a superhero story about {f['hero'].id}, a diabetic hero, who needs the right material for a suit.",
        f"Tell a kid-friendly story with rhyme and magic where {f['sidekick'].id} helps {f['hero'].id} choose a safer material.",
        f"Make a reconciliation story where two heroes argue, apologize, and save the city together.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, sidekick, parent = f["hero"], f["sidekick"], f["parent"]
    material, trouble, magic = f["material"], f["trouble"], f["magic"]
    qa = [
        ("Who is the story about?",
         f"It is about {hero.id}, a diabetic superhero, and {sidekick.id}, who helps with the mission. {parent.id} is the grown-up who steps in when the team needs a calm hand."),
        ("Why did the heroes pause before the rescue?",
         f"They paused because the wrong suit material could make {hero.id} feel shaky and uncomfortable. The team wanted a material that would keep the hero steady during the rescue."),
        ("How did they fix the problem?",
         f"They chose {material.label} and then used the rhyme {magic.rhyme}. That let them finish the mission with a safer plan and no more arguing."),
    ]
    if f["outcome"] == "good":
        qa.append((
            "How did the argument end?",
            f"{hero.id} apologized first, and {sidekick.id} forgave {hero.id}. That reconciliation let them work as a team again, and the rescue went smoothly."
        ))
    else:
        qa.append((
            "What happened with the wrong material?",
            f"The team noticed it would not work, so they replaced it before the mission could begin. That kept {hero.id} safe and gave everyone time to choose better."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"diabetic", "material", "rhyme", "magic", "reconciliation"}
    out = []
    for tag in ["diabetic", "material", "rhyme", "magic", "reconciliation"]:
        out.extend(KNOWLEDGE[tag])
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
        if e.material:
            bits.append(f"material={e.material}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
material_ok(M) :- material(M), protects(M).
valid(S,T,M) :- setting(S), trouble(T), material(M), material_ok(M).
good_outcome :- chosen_material(M), protects(M).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in TROUBLES:
        lines.append(asp.fact("trouble", tid))
    for mid, m in MATERIALS.items():
        lines.append(asp.fact("material", mid))
        if m.protects:
            lines.append(asp.fact("protects", mid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid combos")
        rc = 1
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        emit(sample)
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld with rhyme, magic, and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--material", choices=MATERIALS)
    ap.add_argument("--hero-name")
    ap.add_argument("--sidekick-name")
    ap.add_argument("--parent-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--sidekick-type", choices=["girl", "boy"])
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
    if args.material and not MATERIALS[args.material].protects:
        raise StoryError("That material would not keep the hero comfortable enough for the mission.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.trouble is None or c[1] == args.trouble)
              and (args.material is None or c[2] == args.material)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, trouble, material = rng.choice(sorted(combos))
    hero_name = args.hero_name or rng.choice(["Nova", "Rae", "Luna", "Sky", "Pax"])
    sidekick_name = args.sidekick_name or rng.choice(["Pip", "June", "Tess", "Jules", "Bo"])
    parent_name = args.parent_name or rng.choice(["Aunt Nova", "Dr. Halo", "Captain Kind"])
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    sidekick_type = args.sidekick_type or ("boy" if hero_type == "girl" else "girl")
    return StoryParams(setting=setting, trouble=trouble, material=material, magic=rng.choice(list(MAGIC_LINES)),
                       hero_name=hero_name, hero_type=hero_type,
                       sidekick_name=sidekick_name, sidekick_type=sidekick_type,
                       parent_name=parent_name)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.trouble not in TROUBLES or params.material not in MATERIALS or params.magic not in MAGIC_LINES:
        raise StoryError("Invalid params for this storyworld.")
    world = tell(
        SETTINGS[params.setting], TROUBLES[params.trouble], MATERIALS[params.material],
        MAGIC_LINES[params.magic], params.hero_name, params.hero_type,
        params.sidekick_name, params.sidekick_type, params.parent_name
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for sid, tid, mid in combos:
            print(f"  {sid:10} {tid:14} {mid}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
