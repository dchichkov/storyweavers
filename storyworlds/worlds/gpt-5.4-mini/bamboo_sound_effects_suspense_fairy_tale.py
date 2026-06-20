#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/bamboo_sound_effects_suspense_fairy_tale.py
============================================================================

A standalone storyworld for a small fairy-tale domain built from the seed words
"bamboo", with Sound Effects and Suspense.

Premise
-------
A young child in a fairy-tale village hears strange bamboo sounds in the dusk,
follows them with caution, discovers a hidden helper in trouble, and saves the
night with a brave, gentle choice. The world model tracks who is present, what
the bamboo grove is doing physically, and how fear, courage, and relief change
as the story unfolds.

This script follows the Storyweavers contract:
- stdlib only
- imports storyworlds/results.py eagerly
- exposes StoryParams, build_parser, resolve_params, generate, emit, main
- supports --all, -n, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- includes Python reasonableness gates and an inline ASP twin
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
SUSPENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "princess", "queen"}
        male = {"boy", "father", "dad", "man", "prince", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "queen": "queen", "king": "king"}.get(self.type, self.type)



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
    dusk: str
    dark_spot: str
    sound_source: str
    atmosphere: str

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
class SoundSource:
    id: str
    label: str
    sound: str
    clue: str
    plural: bool = False
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
class HiddenThing:
    id: str
    label: str
    phrase: str
    risk: str
    rescued_by: str
    fragile: bool = False
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
class Helper:
    id: str
    label: str
    action: str
    effect: str
    power: int
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


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["suspense"] < THRESHOLD or e.id == "Grove":
            continue
        sig = ("fear", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["fear"] += 1
        out.append("")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    if world.get("Hidden").meters["saved"] < THRESHOLD:
        return out
    for eid in ("Hero", "Parent"):
        e = world.get(eid)
        sig = ("relief", eid)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["relief"] += 1
        out.append("")
    return out


CAUSAL_RULES = [Rule("fear", "social", _r_fear), Rule("relief", "social", _r_relief)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            if s:
                world.say(s)
    return produced


@dataclass
@dataclass
class StoryParams:
    setting: str
    sound: str
    hidden: str
    helper: str
    hero: str
    hero_gender: str
    parent: str
    parent_gender: str
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


SETTINGS = {
    "grove": Setting("grove", "a moonlit bamboo grove", "At dusk", "the deepest shadow", "the bamboo", "The grove hummed softly."),
    "bridge": Setting("bridge", "a bamboo bridge over a river", "At twilight", "the water below", "the bridge planks", "The river sang under the bridge."),
}

SOUNDS = {
    "whistle": SoundSource("whistle", "a bamboo whistle", "fiuu-fiuu", "a thin tune",
                           tags={"bamboo", "sound"}),
    "rattle": SoundSource("rattle", "a bamboo rattle", "rat-a-tat-tat", "a jittery clatter",
                          tags={"bamboo", "sound"}),
    "wind": SoundSource("wind", "the bamboo stems", "swish-swish", "a soft, slippery whisper",
                        plural=True, tags={"bamboo", "sound"}),
}

HIDDEN = {
    "kit": HiddenThing("kit", "a little lantern kit", "a lantern kit",
                       "it might get lost in the dark", "lamp",
                       fragile=True, tags={"lantern", "light"}),
    "goose": HiddenThing("goose", "a tiny goose", "a tiny goose",
                         "it was stuck by the river reeds", "home",
                         fragile=False, tags={"help", "bird"}),
}

HELPERS = {
    "lamp": Helper("lamp", "a lamp", "shone steady and gold", "the dark path bright", 2, tags={"light"}),
    "song": Helper("song", "a lullaby song", "calmed the shivering heart", 1, tags={"song"}),
    "staff": Helper("staff", "a bamboo staff", "parted the reeds gently", 3, tags={"bamboo", "help"}),
}

GIRL_NAMES = ["Lina", "Mira", "Nora", "Elia", "Sera", "Iris"]
BOY_NAMES = ["Finn", "Joren", "Pavel", "Milo", "Tarin", "Oren"]
PARENT_NAMES = ["Queen", "King", "Mother", "Father"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for snd in SOUNDS:
            for hid in HIDDEN:
                if sid == "bridge" and hid == "goose":
                    combos.append((sid, snd, hid))
                if sid == "grove" and hid == "kit":
                    combos.append((sid, snd, hid))
    return combos


def reasonableness_gate(setting: str, sound: str, hidden: str, helper: str) -> bool:
    if setting == "bridge" and hidden == "kit":
        return False
    if hidden == "goose" and helper == "song":
        return False
    return True


def explain_rejection(setting: str, sound: str, hidden: str, helper: str) -> str:
    if setting == "bridge" and hidden == "kit":
        return "(No story: the lantern kit does not fit the river-bridge danger well enough for a convincing rescue.)"
    if hidden == "goose" and helper == "song":
        return "(No story: a lullaby can comfort, but it cannot free a goose trapped in the reeds.)"
    return "(No story: this combination is not a reasonable fairy-tale suspense setup.)"


def _sound_line(source: SoundSource) -> str:
    return f"{source.sound}! {source.clue} whispered through the bamboo."


def tell(setting: Setting, sound: SoundSource, hidden: HiddenThing, helper: Helper,
         hero_name: str, hero_gender: str, parent_name: str, parent_gender: str) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero", traits=["brave"]))
    parent = world.add(Entity(id=parent_name, kind="character", type=parent_gender, role="parent"))
    grove = world.add(Entity(id="Grove", type="setting", label=setting.place))
    hidden_ent = world.add(Entity(id="Hidden", type="thing", label=hidden.label, attrs={"kind": hidden.id}))
    helper_ent = world.add(Entity(id="Helper", type="thing", label=helper.label, attrs={"kind": helper.id}))
    sound_ent = world.add(Entity(id="Sound", type="thing", label=sound.label, attrs={"kind": sound.id}))

    hero.memes["curiosity"] += 1
    world.say(f"Long ago, in {setting.place}, {hero_name} lived where {setting.atmosphere.lower()}")
    world.say(f"{setting.dusk}, {hero_name} heard {_sound_line(sound)}")
    world.say(f"{hero_name} stood still. The {setting.dark_spot} seemed to hold its breath.")

    world.para()
    hero.meters["suspense"] += 1
    world.say(f'"Did you hear that?" {hero_name} whispered. "Fiuu-fiuu... swish-swish..."')
    world.say(f"{hero_name} followed the sound, one careful step at a time, until the bamboo shadows thinned.")

    world.para()
    hero.meters["suspense"] += 1
    hidden_ent.meters["trapped"] += 1
    world.say(f"Behind the stems, {hidden.phrase} was caught fast. It trembled and made a tiny {hidden.risk}.")
    if hidden.id == "kit":
        world.say("A small lantern case had slipped between the roots and could not find the path home.")
    else:
        world.say("A tiny goose was stuck in the reeds, too nervous to waddle free.")

    world.say(f'"Oh no," said {hero_name}, and the bamboo answered with a soft, nervous {sound.sound}.')

    if helper.id == "lamp":
        world.para()
        helper_ent.meters["power"] += 1
        world.say(f"{parent_name} arrived with {helper.label}. {helper.effect.capitalize()}, and the shadows shrank back.")
        world.say(f"{hero_name} used the light to guide {hidden.label} out, little by little, until it was safe.")
        hidden_ent.meters["saved"] += 1
    elif helper.id == "staff":
        world.para()
        helper_ent.meters["power"] += 1
        world.say(f"{parent_name} brought {helper.label}, and with a gentle push {helper.action}.")
        world.say(f"{hero_name} slipped through the reeds and led {hidden.label} free.")
        hidden_ent.meters["saved"] += 1
    else:
        world.para()
        helper_ent.meters["power"] += 1
        world.say(f"{parent_name} sang a low song. {helper.effect.capitalize()}, but the brave child still had to reach the hidden one.")
        world.say(f"{hero_name} did, and together they brought {hidden.label} home.")
        hidden_ent.meters["saved"] += 1

    propagate(world, narrate=False)
    world.say(f"In the end, the bamboo stood quiet again, and the night felt safe instead of strange.")
    world.say(f"{hero_name} looked back at the grove and smiled at the soft {sound.sound} still lingering in the leaves.")

    world.facts.update(
        setting=setting,
        sound=sound,
        hidden=hidden,
        helper=helper,
        hero=hero,
        parent=parent,
        grove=grove,
        sound_ent=sound_ent,
        hidden_ent=hidden_ent,
        helper_ent=helper_ent,
        rescued=hidden_ent.meters["saved"] >= THRESHOLD,
        suspense=hero.meters["suspense"],
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy-tale story for a 3-to-5-year-old that includes the word "bamboo" and a suspenseful sound like {f["sound"].sound}.',
        f"Tell a gentle suspense story where {f['hero'].id} follows a mysterious bamboo sound and helps {f['hidden'].label}.",
        f'Write a fairy tale with sound effects and a brave ending where the bamboo grove turns from scary to safe.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    hidden = f["hidden"]
    parent = f["parent"]
    sound = f["sound"]
    qa = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {hero.id}, a brave child in a bamboo fairy tale, and {parent.id}, who helps at the end."
        ),
        QAItem(
            question="What mysterious sound did the child hear?",
            answer=f"{hero.id} heard {sound.sound}. It drifted through the bamboo and led the child toward the hidden place."
        ),
        QAItem(
            question=f"What was {hero.id} trying to save?",
            answer=f"{hero.id} was trying to save {hidden.label}. It was trapped in the shadows and needed a gentle helper."
        ),
    ]
    if f["rescued"]:
        qa.append(QAItem(
            question="How did the story end?",
            answer=f"It ended safely, with {hidden.label} rescued and the bamboo grove quiet again. The scary feeling faded once the helper did its job."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    sound = f["sound"]
    hidden = f["hidden"]
    helper = f["helper"]
    items = []
    if "bamboo" in sound.tags or "bamboo" in helper.tags:
        items.append(QAItem(
            question="What is bamboo?",
            answer="Bamboo is a tall plant with hollow stems. It can make light, hollow sounds when the wind moves through it."
        ))
    items.append(QAItem(
        question="What does suspense mean in a story?",
        answer="Suspense is the waiting feeling when something is about to happen, but you do not know exactly what it is yet."
    ))
    items.append(QAItem(
        question="Why do sound effects matter in a fairy tale?",
        answer="Sound effects help you imagine the scene more clearly. They can make a quiet moment feel spooky, lively, or magical."
    ))
    if helper.id == "lamp":
        items.append(QAItem(
            question="What does a lamp do?",
            answer="A lamp gives steady light. It helps people see in the dark without making a scary flame."
        ))
    if hidden.id == "goose":
        items.append(QAItem(
            question="Why might a goose need help?",
            answer="A goose might need help if it gets stuck or frightened. A calm helper can guide it back to safety."
        ))
    return items


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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
suspensey(H) :- hero(H), suspense(H, S), S >= suspense_min(M), S >= M.
rescued(X) :- hidden(X), saved(X).
ending(safe) :- rescued(X).
ending(quiet) :- not rescued(_).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sid, s in SOUNDS.items():
        lines.append(asp.fact("sound", sid))
        if "bamboo" in s.tags:
            lines.append(asp.fact("bamboo_sound", sid))
    for hid in HIDDEN:
        lines.append(asp.fact("hidden", hid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    lines.append(asp.fact("suspense_min", SUSPENSE_MIN))
    return "\n".join(lines)

def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))

def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_setting", params.setting),
        asp.fact("chosen_sound", params.sound),
        asp.fact("chosen_hidden", params.hidden),
        asp.fact("chosen_helper", params.helper),
    ])
    model = asp.one_model(asp_program(scenario, "#show ending/1."))
    out = asp.atoms(model, "ending")
    return out[0][0] if out else "?"

def reasonableness_gate(setting: str, sound: str, hidden: str, helper: str) -> bool:
    return setting == "bridge" and hidden == "goose" or setting == "grove" and hidden == "kit"

def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for snd in SOUNDS:
            for hid in HIDDEN:
                for h in HELPERS:
                    if reasonableness_gate(sid, snd, hid, h):
                        combos.append((sid, snd, hid, h))
    return combos

def explain_response(helper: str) -> str:
    return f"(Refusing helper '{helper}': it does not fit the suspense setup well enough.)"

def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in the gate:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: default generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld with bamboo sounds and suspense.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--hidden", choices=HIDDEN)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy", "princess", "prince"])
    ap.add_argument("--parent")
    ap.add_argument("--parent-gender", choices=["mother", "father", "queen", "king"])
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
    if args.setting or args.hidden or args.helper:
        combos = [c for c in combos
                  if (args.setting is None or c[0] == args.setting)
                  and (args.hidden is None or c[2] == args.hidden)
                  and (args.helper is None or c[3] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, sound, hidden, helper = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    parent_gender = args.parent_gender or rng.choice(["mother", "father", "queen", "king"])
    parent = args.parent or rng.choice(PARENT_NAMES)
    return StoryParams(setting, sound, hidden, helper, hero, hero_gender, parent, parent_gender)

def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], SOUNDS[params.sound], HIDDEN[params.hidden],
                 HELPERS[params.helper], params.hero, params.hero_gender,
                 params.parent, params.parent_gender)
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

CURATED = [
    StoryParams("grove", "whistle", "kit", "lamp", "Lina", "girl", "Queen", "queen"),
    StoryParams("bridge", "wind", "goose", "staff", "Finn", "boy", "Mother", "mother"),
    StoryParams("grove", "rattle", "goose", "song", "Mira", "girl", "Father", "father"),
]

def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
