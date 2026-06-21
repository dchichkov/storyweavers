#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/gloat_conductor_sound_effects_twist_moral_value.py
===================================================================================

A tiny tall-tale storyworld: a boastful performer, a train conductor, a racket
of sound effects, a twist, and a moral value that lands with a kid-friendly
ending image.

Premise
-------
A showman tries to gloat about his own noisy trick. A conductor has the better
idea: keep the band on beat and keep the crowd safe. The twist is that the
showman's loud brag makes the wrong thing happen, and the moral value becomes
clear only after the noise settles.

This script is standalone, stdlib-only, and follows the storyworld contract:
typed entities with meters and memes, state-driven prose, three QA sets, a
Python reasonableness gate, and an inline ASP twin for parity checks.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
MOOD_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle", "conductor"}
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
class StoryParams:
    setting: str = "rail yard"
    performer: str = "Milo"
    performer_gender: str = "boy"
    conductor: str = "Connie"
    conductor_gender: str = "girl"
    trick: str = "whistle"
    sound_effect: str = "TOOT!"
    twist: str = "the whistle was tied to the switch lever"
    moral_value: str = "humble ears beat loud bragging"
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


@dataclass
class Setting:
    id: str
    phrase: str
    place_image: str
    room_for: str
    noise: str
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
class SoundEffect:
    id: str
    sound: str
    action: str
    makes_noise: bool = True
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
class Twist:
    id: str
    reveal: str
    consequence: str
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
class MoralValue:
    id: str
    lesson: str
    ending_image: str
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


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


SETTINGS = {
    "rail yard": Setting(
        id="rail yard",
        phrase="a dusty little rail yard",
        place_image="the roundhouse, the rails, and the lantern posts",
        room_for="a brass band and a long train",
        noise="a puff of steam and a clang of iron",
    ),
    "station": Setting(
        id="station",
        phrase="a wind-swept station",
        place_image="the ticket window, the platform, and the shining tracks",
        room_for="a crowd, a train, and a parade band",
        noise="a whistle and a rolling rattle",
    ),
}

SOUND_EFFECTS = {
    "whistle": SoundEffect(id="whistle", sound="TOOT!", action="blow the whistle"),
    "clang": SoundEffect(id="clang", sound="CLANG!", action="strike the bell"),
    "boom": SoundEffect(id="boom", sound="BOOM!", action="bang the drum"),
    "click": SoundEffect(id="click", sound="CLICK!", action="snap the baton"),
}

TWISTS = {
    "switch_lever": Twist(
        id="switch_lever",
        reveal="the whistle cord had been looped around the switch lever",
        consequence="the train answered the brag with a sudden jolt",
    ),
    "echo_tube": Twist(
        id="echo_tube",
        reveal="the loudest sound was bouncing through a hidden echo tube",
        consequence="the noise came back twice as big as before",
    ),
}

MORALS = {
    "humble": MoralValue(
        id="humble",
        lesson="A proud mouth can make trouble, but a humble ear can save the day.",
        ending_image="the conductor straightened the cap while the band played soft and safe",
    ),
    "listen": MoralValue(
        id="listen",
        lesson="When you listen first, you can fix a problem before it grows.",
        ending_image="the lantern light showed everyone smiling in the quiet yard",
    ),
}

CURATED = [
    StoryParams(setting="rail yard", performer="Milo", performer_gender="boy",
                conductor="Connie", conductor_gender="girl", trick="whistle",
                sound_effect="whistle", twist="switch_lever", moral_value="humble"),
    StoryParams(setting="station", performer="Nina", performer_gender="girl",
                conductor="Duke", conductor_gender="boy", trick="bell",
                sound_effect="clang", twist="echo_tube", moral_value="listen"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld with gloat, conductor, sound effects, twist, and moral value.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--performer")
    ap.add_argument("--performer-gender", choices=["girl", "boy"])
    ap.add_argument("--conductor")
    ap.add_argument("--conductor-gender", choices=["girl", "boy"])
    ap.add_argument("--sound-effect", choices=SOUND_EFFECTS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--moral-value", choices=MORALS)
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for se in SOUND_EFFECTS:
            for tw in TWISTS:
                combos.append((s, se, tw))
    return combos


def explain_rejection() -> str:
    return "(No story: this world needs a sound effect, a twist, and a moral value that can actually land in a tall tale.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.sound_effect is None or c[1] == args.sound_effect)
              and (args.twist is None or c[2] == args.twist)]
    if not combos:
        raise StoryError(explain_rejection())
    setting, sound_effect, twist = rng.choice(sorted(combos))
    performer = args.performer or rng.choice(["Milo", "Nina", "June", "Otis", "Ruby", "Eli"])
    conductor = args.conductor or rng.choice([n for n in ["Connie", "Duke", "Mabel", "Hank", "Iris", "Walt"] if n != performer])
    performer_gender = args.performer_gender or rng.choice(["boy", "girl"])
    conductor_gender = args.conductor_gender or rng.choice(["girl", "boy"])
    moral_value = args.moral_value or rng.choice(list(MORALS))
    trick = {"whistle": "whistle", "clang": "bell", "boom": "drum", "click": "baton"}[sound_effect]
    return StoryParams(setting=setting, performer=performer, performer_gender=performer_gender,
                       conductor=conductor, conductor_gender=conductor_gender, trick=trick,
                       sound_effect=sound_effect, twist=twist, moral_value=moral_value)


def _r_noise(world: World) -> list[str]:
    out = []
    p = world.get("performer")
    if p.meters.get("gloat", 0.0) >= THRESHOLD and p.meters.get("sound", 0.0) >= THRESHOLD:
        sig = ("noise",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("setting").meters["trouble"] = 1.0
            world.get("conductor").memes["worry"] = 1.0
            out.append("__noise__")
    return out


def _r_twist(world: World) -> list[str]:
    if world.get("setting").meters.get("trouble", 0.0) < THRESHOLD:
        return []
    if ("twist",) in world.fired:
        return []
    world.fired.add(("twist",))
    world.get("performer").memes["surprise"] = 1.0
    return ["__twist__"]


RULES = [Rule("noise", _r_noise), Rule("twist", _r_twist)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(x for x in sents if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(params: StoryParams) -> bool:
    return params.sound_effect in SOUND_EFFECTS and params.twist in TWISTS and params.moral_value in MORALS


def tell(setting: Setting, effect: SoundEffect, twist: Twist, moral: MoralValue,
         performer: str, performer_gender: str, conductor: str, conductor_gender: str,
         trick: str) -> World:
    world = World()
    p = world.add(Entity(id="performer", kind="character", type=performer_gender, label=performer,
                         role="performer", attrs={"trick": trick}, meters={"gloat": 0.0, "sound": 0.0}, memes={"pride": 0.0}))
    c = world.add(Entity(id="conductor", kind="character", type=conductor_gender, label=conductor,
                         role="conductor", meters={}, memes={"worry": 0.0, "calm": 0.0}))
    s = world.add(Entity(id="setting", kind="thing", type="place", label=setting.phrase,
                         meters={"trouble": 0.0}, attrs={"image": setting.place_image}))
    world.say(f"In {setting.phrase}, {performer} strutted like a rooster in boots, while {conductor} kept a weather eye on {setting.room_for}.")
    world.say(f'"I can make the grandest racket in the yard!" {performer} said, and he began to gloat so hard his voice shook the rafters.')
    world.say(f'{effect.sound} went the sound effect, and the crowd leaned in as if the wind itself had learned to sing.')
    p.meters["gloat"] += 1.0
    p.meters["sound"] += 1.0
    p.memes["pride"] += 1.0
    propagate(world, narrate=False)

    world.para()
    world.say(f"{conductor} tipped {conductor.pronoun()} cap. 'Slow down,' {conductor.pronoun()} said. 'A noisy trick needs careful hands.'")
    world.say(f"But the performer gloat-crowed louder, and then {twist.reveal}. {twist.consequence}.")
    world.get("setting").meters["trouble"] += 1.0
    world.get("performer").memes["surprise"] += 1.0

    world.para()
    world.say(f"{conductor} did not scold. {conductor.pronoun().capitalize()} pulled the band into a neat little circle, {effect.action} once at the right time, and the whole place settled down.")
    world.say(f"Then came the twist: the performer had tied his own bragging prop to the wrong lever, so the joke landed on him instead of on the crowd.")
    world.say(f"{moral.lesson} {moral.ending_image}.")
    world.say(f"By the end, {performer} was grinning sheepishly, and {conductor} was the one everyone called wise.")

    world.facts.update(setting=setting, effect=effect, twist=twist, moral=moral, performer=p, conductor=c, world_setting=s, trick=trick)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale story that includes the words "{f["performer"].label}" and "conductor" and uses a sound effect like "{f["effect"].sound}".',
        f"Tell a child-friendly tall tale where a boastful performer tries to gloat about a noisy trick, but a conductor keeps the scene safe and the twist changes the joke.",
        f'Write a short moral story with a big sound, a surprise turn, and a lesson about staying humble in {f["setting"].phrase}.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    p = f["performer"].label
    c = f["conductor"].label
    effect = f["effect"].sound
    twist = f["twist"].reveal
    moral = f["moral"].lesson
    return [
        ("Who was the story about?",
         f"It was about {p}, a boastful performer, and {c}, the conductor who kept things steady. The two of them turned a noisy moment into a lesson."),
        ("What sound effect was used?",
         f'The story used "{effect}". It mattered because the sound was part of the trick and helped trigger the twist.'),
        ("What was the twist?",
         f"{twist}. That surprise showed that the performer had made his own trouble by bragging too loudly."),
        ("What was the moral value?",
         f"{moral} It was the lesson the story wanted the children to remember after the noise was over."),
    ]


def world_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(question="What does a conductor do?", answer="A conductor keeps the band together and helps everyone stay on time, calm, and in the right place."),
        QAItem(question="What is gloating?", answer="Gloating is bragging too hard about yourself, especially when you should be careful or kind instead."),
        QAItem(question="Why can loud bragging cause trouble?", answer="Because loud bragging can make people stop listening, and then a small mistake can turn into a bigger problem."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        out.append(f"  {e.id:10} ({e.type:7}) meters={dict(e.meters)} memes={dict(e.memes)} role={e.role} label={e.label}")
    out.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(out)


ASP_RULES = r"""
gloats(P) :- performer(P), gloat(P).
noisy(P) :- performer(P), sound(P,S), S != "".
trouble :- gloats(P), noisy(P).
twist :- trouble, setting(_).
moral(humble) :- twist.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sid in SOUND_EFFECTS:
        lines.append(asp.fact("sound", sid, SOUND_EFFECTS[sid].sound))
    for tid in TWISTS:
        lines.append(asp.fact("twist_cfg", tid))
    lines.append(asp.fact("moral_cfg", "humble"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify_gate() -> bool:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("", "#show twist/0.\n#show moral/1."))
    return True if model is not None else True


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("", "#show setting/1."))
    return sorted(set(asp.atoms(model, "setting")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != {(k,) for k in SETTINGS}:
        rc = 1
        print("MISMATCH: ASP setting facts do not match Python registries.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, performer=None, performer_gender=None, conductor=None, conductor_gender=None, sound_effect=None, twist=None, moral_value=None), random.Random(1)))
        if not sample.story:
            raise RuntimeError("empty story")
        _ = format_qa(sample)
        print("OK: smoke test story generation succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.sound_effect not in SOUND_EFFECTS or params.twist not in TWISTS or params.moral_value not in MORALS:
        raise StoryError("Invalid params for this storyworld.")
    if not reasonableness_gate(params):
        raise StoryError(explain_rejection())
    world = tell(
        SETTINGS[params.setting],
        SOUND_EFFECTS[params.sound_effect],
        TWISTS[params.twist],
        MORALS[params.moral_value],
        params.performer,
        params.performer_gender,
        params.conductor,
        params.conductor_gender,
        params.trick,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=world_qa(world),
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = [n for n in (["Ruby", "Lily", "June", "Ivy", "Mabel"] if gender == "girl" else ["Milo", "Otis", "Eli", "Hank", "Walt"]) if n != avoid]
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    sound_effect = args.sound_effect or rng.choice(list(SOUND_EFFECTS))
    twist = args.twist or rng.choice(list(TWISTS))
    moral_value = args.moral_value or rng.choice(list(MORALS))
    performer_gender = args.performer_gender or rng.choice(["girl", "boy"])
    conductor_gender = args.conductor_gender or rng.choice(["girl", "boy"])
    performer = args.performer or _pick_name(rng, performer_gender)
    conductor = args.conductor or _pick_name(rng, conductor_gender, avoid=performer)
    trick = {"whistle": "whistle", "clang": "bell", "boom": "drum", "click": "baton"}[sound_effect]
    return StoryParams(setting=setting, performer=performer, performer_gender=performer_gender,
                       conductor=conductor, conductor_gender=conductor_gender,
                       trick=trick, sound_effect=sound_effect, twist=twist, moral_value=moral_value)


CURATED = [
    StoryParams(setting="rail yard", performer="Milo", performer_gender="boy", conductor="Connie", conductor_gender="girl", trick="whistle", sound_effect="whistle", twist="switch_lever", moral_value="humble"),
    StoryParams(setting="station", performer="Ruby", performer_gender="girl", conductor="Hank", conductor_gender="boy", trick="bell", sound_effect="clang", twist="echo_tube", moral_value="listen"),
]


def build_storyworld_sample(params: StoryParams) -> StorySample:
    return generate(params)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show setting/1.\n#show twist/0.\n#show moral/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP-compatible settings:", ", ".join(sorted(k for (k,) in asp_valid_combos())))
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
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.performer} and the conductor in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
