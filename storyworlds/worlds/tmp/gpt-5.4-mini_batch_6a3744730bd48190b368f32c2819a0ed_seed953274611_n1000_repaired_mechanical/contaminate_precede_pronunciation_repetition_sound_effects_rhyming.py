#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/contaminate_precede_pronunciation_repetition_sound_effects_rhyming.py
======================================================================================================

A standalone storyworld for a small rhyming recital domain.

Seed idea:
- The story should include the words contaminate, precede, and pronunciation.
- It should feel like a rhyming story, with repetition and sound effects.
- The world should still be state-driven: a small problem, a turn, and a fix.

Premise:
A child is getting ready for a little rhyme recital. A clean prop must stay clean,
the child practices pronunciation, and a noisy mishap can contaminate the prop.

Resolution:
The helper notices the spill in time, cleans the prop, and the child finishes the
recital with a bright rhyming line.

This file is self-contained and uses the shared Storyweavers result containers.
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
    sound: str
    rhyme_word: str
    affords: set[str] = field(default_factory=set)
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
class Prop:
    id: str
    label: str
    clean: bool = True
    contamination_kind: str = "sticky"
    sound_word: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
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
class Mishap:
    id: str
    label: str
    sound_effect: str
    makes_contaminate: bool = True
    strength: int = 1
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
class Fix:
    id: str
    label: str
    power: int
    text: str
    qa_text: str
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
class StoryParams:
    setting: str
    prop: str
    mishap: str
    fix: str
    child: str
    child_gender: str
    helper: str
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


def _r_contaminate(world: World) -> list[str]:
    out: list[str] = []
    prop = world.get("prop")
    if prop.meters["contaminated"] < THRESHOLD:
        return out
    sig = ("contaminate",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for e in list(world.entities.values()):
        if e.kind == "character":
            e.memes["worry"] += 1
    out.append("__contaminate__")
    return out


CAUSAL_RULES = [Rule("contaminate", _r_contaminate)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(x for x in out if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _do_mishap(world: World, prop: Entity, mishap: Mishap, narrate: bool = True) -> None:
    if mishap.makes_contaminate:
        prop.meters["contaminated"] += mishap.strength
        prop.meters["mess"] += mishap.strength
    propagate(world, narrate=narrate)


def predict_contaminate(world: World, prop_id: str, mishap: Mishap) -> bool:
    sim = world.copy()
    _do_mishap(sim, sim.get(prop_id), mishap, narrate=False)
    return sim.get(prop_id).meters["contaminated"] >= THRESHOLD


def tidy_fix(world: World, helper: Entity, fix: Fix, prop: Entity, prop_cfg: Prop) -> None:
    prop.meters["contaminated"] = 0.0
    prop.meters["mess"] = 0.0
    helper.memes["calm"] += 1
    world.say(
        f"{helper.label_word.capitalize()} came in quick as a wink, {fix.text}."
    )
    world.say(
        f"The spill went away, and the prop stayed ready for the rhyme."
    )


def tell_setting(world: World, child: Entity, helper: Entity, prop: Entity, setting: Setting) -> None:
    world.say(
        f"At {setting.place}, {child.id} and {helper.id} made a tiny stage out of chairs and chalk."
    )
    world.say(
        f"The room hummed with {setting.sound}. It felt like a place for a song that could rhyme."
    )


def practice_pronunciation(world: World, child: Entity, prop_cfg: Prop, setting: Setting) -> None:
    child.memes["confidence"] += 1
    world.say(
        f'{child.id} practiced pronunciation again and again: "Rhyme, chime, time." '
        f'"Rhyme, chime, time." {child.pronoun().capitalize()} smiled at the sound.'
    )
    world.say(
        f'{child.id} liked the word "{setting.rhyme_word}" because it could precede the bell.'
    )


def warn(world: World, helper: Entity, child: Entity, prop: Entity, mishap: Mishap) -> None:
    if predict_contaminate(world, "prop", mishap):
        helper.memes["care"] += 1
        world.say(
            f'{helper.id} heard the little clack-clack and said, "Wait, wait, wait -- '
            f'{mishap.label} could contaminate the {prop.label}."'
        )
        world.say(
            f'"Let\'s keep it clean, and keep the rhyme.'"'
        )


def mishap_scene(world: World, child: Entity, prop_cfg: Prop, mishap: Mishap) -> None:
    child.memes["startle"] += 1
    world.say(
        f"{mishap.sound_effect} went the jar! {mishap.sound_effect} went the lid!"
    )
    world.say(
        f"The {prop_cfg.label} got a sticky spot, and the bright prop was no longer clean."
    )


def finish_rhyme(world: World, child: Entity, helper: Entity, setting: Setting, prop: Entity) -> None:
    child.memes["joy"] += 1
    world.say(
        f"Then {child.id} stood up straight and sang, "
        f'"Clean and keen, bright and green, now the shiny prop can gleam!"'
    )
    world.say(
        f"{helper.id} clapped in time: tap-tap-tap, clap-clap-clap."
    )
    world.say(
        f"At {setting.place}, the rhyme rang out, and the stage looked neat again."
    )


SETTINGS = {
    "schoolroom": Setting(
        id="schoolroom",
        place="the little schoolroom",
        sound="soft shuffles and a pencil tap",
        rhyme_word="chime",
        affords={"recital"},
    ),
    "kitchen": Setting(
        id="kitchen",
        place="the sunny kitchen",
        sound="a spoon against a cup and a happy hum",
        rhyme_word="time",
        affords={"recital"},
    ),
    "porch": Setting(
        id="porch",
        place="the front porch",
        sound="birds going cheep-cheep and the breeze going swoosh",
        rhyme_word="shine",
        affords={"recital"},
    ),
}

PROPS = {
    "bell": Prop(id="bell", label="little bell", clean=True, contamination_kind="dust", sound_word="ding"),
    "card": Prop(id="card", label="picture card", clean=True, contamination_kind="smear", sound_word="flip"),
    "cup": Prop(id="cup", label="paper cup", clean=True, contamination_kind="sticky", sound_word="pop"),
}

MISHAPS = {
    "spill": Mishap(id="spill", label="berry spill", sound_effect="Splish-splash", makes_contaminate=True, strength=1),
    "jam": Mishap(id="jam", label="jam drop", sound_effect="Plip-plop", makes_contaminate=True, strength=1),
    "paint": Mishap(id="paint", label="paint drip", sound_effect="Drip-drop", makes_contaminate=True, strength=1),
}

FIXES = {
    "wipe": Fix(id="wipe", label="wipe", power=1, text="wiped it clean with a soft cloth", qa_text="wiped it clean with a soft cloth"),
    "rinse": Fix(id="rinse", label="rinse", power=1, text="rinsed the sticky spot away", qa_text="rinsed the sticky spot away"),
    "polish": Fix(id="polish", label="polish", power=1, text="polished the prop until it shone", qa_text="polished the prop until it shone"),
}

GIRL_NAMES = ["Mia", "Lina", "Zoe", "Ava", "Nia", "Mina"]
BOY_NAMES = ["Noah", "Leo", "Theo", "Milo", "Finn", "Eli"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for pid, p in PROPS.items():
            for mid, m in MISHAPS.items():
                if not p.clean and m.makes_contaminate:
                    continue
                for fid in FIXES:
                    combos.append((sid, pid, mid, fid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming storyworld with repetition and sound effects.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--mishap", choices=MISHAPS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
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
              and (args.prop is None or c[1] == args.prop)
              and (args.mishap is None or c[2] == args.mishap)
              and (args.fix is None or c[3] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, prop, mishap, fix = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if child_gender == "girl" and rng.random() < 0.5 else "girl")
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper_pool = [n for n in (GIRL_NAMES if helper_gender == "girl" else BOY_NAMES) if n != child]
    helper = args.helper or rng.choice(helper_pool)
    if child == helper:
        raise StoryError("child and helper must be different")
    return StoryParams(
        setting=setting, prop=prop, mishap=mishap, fix=fix,
        child=child, child_gender=child_gender, helper=helper, helper_gender=helper_gender,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        prop_cfg = PROPS[params.prop]
        mishap = MISHAPS[params.mishap]
        fix = FIXES[params.fix]
    except KeyError as exc:
        raise StoryError(f"Invalid parameter: {exc.args[0]}") from exc

    world = World(setting)
    child = world.add(Entity(id=params.child, kind="character", type=params.child_gender, role="child"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper"))
    prop = world.add(Entity(id="prop", kind="thing", type="prop", label=prop_cfg.label))

    tell_setting(world, child, helper, prop, setting)
    world.para()
    practice_pronunciation(world, child, prop_cfg, setting)
    warn(world, helper, child, prop, mishap)
    world.para()
    mishap_scene(world, child, prop_cfg, mishap)
    _do_mishap(world, prop, mishap, narrate=False)
    tidy_fix(world, helper, fix, prop, prop_cfg)
    world.para()
    finish_rhyme(world, child, helper, setting, prop)

    world.facts.update(
        setting=setting, prop=prop_cfg, mishap=mishap, fix=fix,
        child=child, helper=helper, contaminated=prop.meters["contaminated"] >= THRESHOLD,
    )

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story for a 3-to-5-year-old that uses the words "contaminate", "precede", and "pronunciation".',
        f"Tell a short story where {f['child'].id} practices pronunciation, a mishap can contaminate a prop, and a helper fixes it with a gentle sound-effect scene.",
        f'Write a repetition-filled story where a clean prop must stay clean, the word "precede" belongs in the middle, and the ending rhymes.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    setting: Setting = f["setting"]
    prop: Prop = f["prop"]
    mishap: Mishap = f["mishap"]
    fix: Fix = f["fix"]
    contaminated = f["contaminated"]
    answers = [
        QAItem(
            question="What was the child practicing?",
            answer=f"{child.id} was practicing pronunciation. The child kept repeating a little rhyme so the words would come out clear."
        ),
        QAItem(
            question="What could contaminate the prop?",
            answer=f"The {mishap.label} could contaminate the {prop.label}. It was sticky enough to leave a mark on the clean prop."
        ),
        QAItem(
            question=f"How did {helper.id} help when the prop got messy?",
            answer=f"{helper.id} {fix.qa_text}. That cleaned the prop before the ending rhyme, so the recital could go on."
        ),
    ]
    if contaminated:
        answers.append(
            QAItem(
                question="What changed by the end of the story?",
                answer=f"At first the prop was contaminated, but by the end it was clean again. The child finished with a bright rhyme and a tidy stage."
            )
        )
    else:
        answers.append(
            QAItem(
                question="What changed by the end of the story?",
                answer=f"The prop stayed clean, and the child finished with a bright rhyme. The little stage ended neat and ready for another song."
            )
        )
    answers.insert(
        1,
        QAItem(
            question="What did the helper say the mishap would do?",
            answer=f"{helper.id} said the {mishap.label} could contaminate the {prop.label}. That warning came before the messy part, so the child knew to be careful."
        ),
    )
    return answers


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    setting: Setting = f["setting"]
    mishap: Mishap = f["mishap"]
    prop: Prop = f["prop"]
    return [
        QAItem(
            question="What does pronunciation mean?",
            answer="Pronunciation means how you say a word. Good pronunciation helps other people hear the word clearly."
        ),
        QAItem(
            question="What does precede mean?",
            answer="Precede means to come before something else. If one thing precedes another, it happens first."
        ),
        QAItem(
            question="What does contaminate mean?",
            answer="Contaminate means to make something dirty or unsafe by mixing it with something bad. A sticky spill can contaminate a clean object."
        ),
        QAItem(
            question="What is a sound effect?",
            answer="A sound effect is a small noise that helps tell the story, like splash, tap, ding, or drip."
        ),
        QAItem(
            question="Why do repeated words help in a rhyming story?",
            answer="Repeated words make the story feel sing-song and easy to remember. They help the reader hear the beat of the rhyme."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)], ""]
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def valid_combo(params: StoryParams) -> bool:
    return all([
        params.setting in SETTINGS,
        params.prop in PROPS,
        params.mishap in MISHAPS,
        params.fix in FIXES,
    ])


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PROPS:
        lines.append(asp.fact("prop", pid))
    for mid in MISHAPS:
        lines.append(asp.fact("mishap", mid))
    for fid in FIXES:
        lines.append(asp.fact("fix", fid))
    lines.append(asp.fact("can_contaminate", "yes"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,P,M,F) :- setting(S), prop(P), mishap(M), fix(F), can_contaminate(yes).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        print("MISMATCH in valid combos")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        rc = 1

    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, prop=None, mishap=None, fix=None, child=None, child_gender=None, helper=None, helper_gender=None), random.Random(777)))
        _ = sample.story
        print("OK: default generate smoke test succeeded.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


CURATED = [
    StoryParams(setting="schoolroom", prop="bell", mishap="spill", fix="wipe", child="Mia", child_gender="girl", helper="Noah", helper_gender="boy"),
    StoryParams(setting="kitchen", prop="cup", mishap="jam", fix="rinse", child="Leo", child_gender="boy", helper="Ava", helper_gender="girl"),
    StoryParams(setting="porch", prop="card", mishap="paint", fix="polish", child="Nia", child_gender="girl", helper="Finn", helper_gender="boy"),
]


def explain_rejection() -> str:
    return "(No story: this combination does not make a believable contamination-and-cleanup rhyme.)"


def generate_default_params(rng: random.Random) -> StoryParams:
    return resolve_params(argparse.Namespace(setting=None, prop=None, mishap=None, fix=None, child=None, child_gender=None, helper=None, helper_gender=None), rng)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for combo in asp_valid_combos():
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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
        if i:
            print("\n" + "=" * 70 + "\n")
        print(sample.story)
        if args.trace and sample.world is not None:
            print(dump_trace(sample.world))
        if args.qa:
            print()
            print(format_qa(sample))


if __name__ == "__main__":
    main()
