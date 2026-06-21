#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/translate_pebble_flashback_bad_ending_adventure.py
===================================================================================

A small adventure storyworld about a child explorer, a pebble clue, a translator
device, a flashback to an earlier warning, and a bad ending when the wrong
message is trusted too far.

The world is intentionally tiny and classical:
- one child explorer
- one helper adult
- one clue object: a pebble with a carved sign
- one translating tool
- one danger path
- one ending image that proves whether the choice was wise

The story can end in a bad ending if the translated clue is wrong or the child
goes too far into the cave. The flashback instrument is used to recall the
earlier warning, but in the bad ending it comes too late to change the result.

The required seed words are included in story text: translate, pebble.
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
TRANSLATION_MIN = 2
DANGER_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
    mood: str
    danger_name: str
    details: str
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
class Clue:
    id: str
    label: str
    carved_text: str
    meaning: str
    risky_if_misread: str
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
class Translator:
    id: str
    label: str
    device_phrase: str
    success_phrase: str
    fail_phrase: str
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
class Route:
    id: str
    label: str
    warning: str
    ending_image: str
    bad_ending: bool = True
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


def _r_danger(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    route = world.entities.get("route")
    if not child or not route:
        return out
    if child.meters["lost"] >= THRESHOLD and ("danger", "lost") not in world.fired:
        world.fired.add(("danger", "lost"))
        route.meters["danger"] += 1
        child.memes["fear"] += 1
        out.append("__danger__")
    return out


CAUSAL_RULES = [Rule("danger", _r_danger)]


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


def setting_detail(setting: Setting) -> str:
    return f"{setting.place.capitalize()} was {setting.mood}, and {setting.details}"


def predict_translation(world: World, clue: Clue, translator: Translator) -> dict:
    sim = world.copy()
    _translate_clue(sim, clue, translator, narrate=False)
    return {
        "understood": sim.get("child").meters["understood"] >= THRESHOLD,
        "fear": sim.get("child").memes["fear"],
    }


def _translate_clue(world: World, clue: Clue, translator: Translator, narrate: bool = True) -> None:
    child = world.get("child")
    child.meters["understood"] += 1
    child.meters["translated"] += 1
    child.meters["pebble_seen"] += 1
    if narrate:
        if child.meters["understood"] >= TRANSLATION_MIN:
            world.say(
                f"{child.id} used the {translator.label} to translate the pebble's carved mark."
            )
        else:
            world.say(
                f"{child.id} tried to translate the pebble, but the meaning still felt fuzzy."
            )


def setup(world: World, child: Entity, guide: Entity, setting: Setting) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"At {setting.place}, {child.id} and {guide.id} set out like little explorers."
    )
    world.say(setting_detail(setting))
    world.say(
        f"They were searching for a hidden route, and a small pebble near the path caught {child.pronoun('possessive')} eye."
    )


def clue_find(world: World, child: Entity, clue: Clue) -> None:
    child.meters["pebble_seen"] += 1
    world.say(
        f"The pebble was smooth and round, but one side had {clue.carved_text} on it."
    )
    world.say(f'"It might translate to a warning," {child.id} whispered.')


def flashback(world: World, child: Entity, guide: Entity, setting: Setting, route: Route) -> None:
    child.memes["memory"] += 1
    world.say(
        f"Flashback: {child.id} remembered {guide.id}'s voice from earlier in the day."
    )
    world.say(
        f'"If the path turns black and narrow," {guide.id} had said, "stop and come back."'
    )
    world.say(
        f"But the memory floated behind {child.pronoun('object')} like a little cloud, easy to forget."
    )
    world.facts["flashback_used"] = True


def read_choice(world: World, child: Entity, translator: Translator, clue: Clue, route: Route) -> None:
    pred = predict_translation(world, clue, translator)
    world.facts["predicted_understood"] = pred["understood"]
    world.say(
        f"{child.id} pressed the {translator.label} against the pebble and tried to translate it."
    )
    if pred["understood"]:
        world.say(translator.success_phrase)
    else:
        world.say(translator.fail_phrase)


def go_on(world: World, child: Entity, route: Route) -> None:
    child.memes["bravery"] += 1
    child.meters["lost"] += 1
    world.say(
        f"Still, {child.id} stepped onto {route.label} and walked deeper into the cave."
    )
    propagate(world, narrate=True)


def bad_end(world: World, child: Entity, guide: Entity, route: Route) -> None:
    child.memes["fear"] += 1
    child.memes["regret"] += 1
    world.say(
        f"By the time {guide.id} called again, the tunnel had turned too tight to hurry back."
    )
    world.say(
        f"{route.ending_image}"
    )
    world.say(
        f"{child.id} held the pebble in one hand and wished {child.pronoun('subject')} had listened sooner."
    )


def tell(setting: Setting, clue: Clue, translator: Translator, route: Route,
         child_name: str = "Milo", child_gender: str = "boy",
         guide_name: str = "Nia", guide_gender: str = "girl") -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, role="explorer"))
    guide = world.add(Entity(id="guide", kind="character", type=guide_gender, label=guide_name, role="guide"))
    world.add(Entity(id="pebble", kind="thing", type="pebble", label="the pebble", role="clue"))
    world.add(Entity(id="route", kind="thing", type="route", label=route.label, role="path"))

    setup(world, child, guide, setting)
    world.para()
    clue_find(world, child, clue)
    flashback(world, child, guide, setting, route)
    world.para()
    read_choice(world, child, translator, clue, route)
    go_on(world, child, route)
    world.para()
    bad_end(world, child, guide, route)

    world.facts.update(
        child=child,
        guide=guide,
        setting=setting,
        clue=clue,
        translator=translator,
        route=route,
        outcome="bad",
        flashback=True,
        translated=child.meters["translated"] >= THRESHOLD,
        lost=child.meters["lost"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "cave": Setting(
        id="cave",
        place="the cave mouth",
        mood="windy and dim",
        danger_name="the black tunnel",
        details="the walls shimmered with damp stone",
    ),
    "ruins": Setting(
        id="ruins",
        place="the old ruins",
        mood="quiet and echoing",
        danger_name="the broken hall",
        details="crumbled arches leaned over mossy steps",
    ),
}

CLUES = {
    "pebble": Clue(
        id="pebble",
        label="pebble",
        carved_text="tiny spiral scratches",
        meaning="turn back before the narrow path",
        risky_if_misread="go deeper to find treasure",
        tags={"pebble", "translate"},
    ),
}

TRANSLATORS = {
    "lens": Translator(
        id="lens",
        label="pocket lens",
        device_phrase="a pocket lens",
        success_phrase="The marks came clear at once, like a small sign drawn in light.",
        fail_phrase="The marks blurred and wobbled, almost like they were warning him to stop.",
        tags={"translate"},
    ),
    "chip": Translator(
        id="chip",
        label="tiny translation chip",
        device_phrase="a tiny translation chip",
        success_phrase="The chip chimed and turned the pebble's scratches into words.",
        fail_phrase="The chip only buzzed softly, and the message still stayed mixed up.",
        tags={"translate"},
    ),
}

ROUTES = {
    "tunnel": Route(
        id="tunnel",
        label="the black tunnel",
        warning="it narrowed until the ceiling felt low",
        ending_image="Far ahead, the last lantern dot winked out, and the cave kept the rest of the path.",
        bad_ending=True,
        tags={"adventure", "bad"},
    ),
    "stairs": Route(
        id="stairs",
        label="the broken stairway",
        warning="the steps were cracked and slick",
        ending_image="Below the broken stairway, dust drifted over a gap too wide to jump back across.",
        bad_ending=True,
        tags={"adventure", "bad"},
    ),
}

NAMES_BOY = ["Milo", "Arlo", "Theo", "Finn", "Eli"]
NAMES_GIRL = ["Nia", "Luna", "Mina", "Ivy", "Zia"]


@dataclass
class StoryParams:
    setting: str
    clue: str
    translator: str
    route: str
    child_name: str
    child_gender: str
    guide_name: str
    guide_gender: str
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [(s, c, t, r) for s in SETTINGS for c in CLUES for t in TRANSLATORS for r in ROUTES]


def explain_rejection() -> str:
    return "(No story: this world needs a pebble clue, a translate device, and a bad-ending route.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Adventure storyworld: translate a pebble clue, remember a warning, and risk a bad ending."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--translator", choices=TRANSLATORS)
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["boy", "girl"])
    ap.add_argument("--guide")
    ap.add_argument("--guide-gender", choices=["boy", "girl"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    clue = args.clue or rng.choice(list(CLUES))
    translator = args.translator or rng.choice(list(TRANSLATORS))
    route = args.route or rng.choice(list(ROUTES))
    if args.gender:
        gender = args.gender
    else:
        gender = rng.choice(["boy", "girl"])
    name = args.name or rng.choice(NAMES_BOY if gender == "boy" else NAMES_GIRL)
    guide_gender = args.guide_gender or ("girl" if gender == "boy" else "boy")
    guide = args.guide or rng.choice(NAMES_GIRL if guide_gender == "girl" else NAMES_BOY)
    return StoryParams(
        setting=setting,
        clue=clue,
        translator=translator,
        route=route,
        child_name=name,
        child_gender=gender,
        guide_name=guide,
        guide_gender=guide_gender,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an adventure story for a young child that includes the words "translate" and "pebble".',
        f"Tell a cave adventure where {f['child'].label} tries to translate a pebble clue, remembers an earlier warning in a flashback, and still makes a bad choice.",
        f"Write a small suspense story with a flashback, a pebble clue, and a bad ending in {f['setting'].place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    guide = f["guide"]
    clue = f["clue"]
    route = f["route"]
    qa = [
        QAItem(
            question="What did the child try to do with the pebble?",
            answer=(
                f"{child.label} tried to translate the pebble's carved scratches. "
                f"The child hoped the mark would tell where the path went."
            ),
        ),
        QAItem(
            question="What was the flashback for?",
            answer=(
                f"The flashback reminded {child.label} of {guide.label}'s warning from earlier. "
                f"It was meant to stop the child from going deeper into {route.label}."
            ),
        ),
        QAItem(
            question="Why was the ending bad?",
            answer=(
                f"The pebble was not enough to save the day, and {child.label} kept walking into danger. "
                f"By the end, the route closed in and the child could not turn back in time."
            ),
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to translate something?",
            answer="To translate something means to change its meaning into words you can understand. A child can translate a sign, a note, or marks on a pebble if they have a good tool or enough help.",
        ),
        QAItem(
            question="What is a pebble?",
            answer="A pebble is a small smooth stone. People sometimes pick up pebbles because they are easy to hold and can carry tiny marks or clues.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly remembers something that happened earlier. It helps explain why a character feels worried or why a choice matters.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="cave", clue="pebble", translator="lens", route="tunnel", child_name="Milo", child_gender="boy", guide_name="Nia", guide_gender="girl"),
    StoryParams(setting="ruins", clue="pebble", translator="chip", route="stairs", child_name="Ivy", child_gender="girl", guide_name="Theo", guide_gender="boy"),
]


ASP_RULES = r"""
setting(S) :- setting_fact(S).
clue(C) :- clue_fact(C).
translator(T) :- translator_fact(T).
route(R) :- route_fact(R).
valid(S,C,T,R) :- setting(S), clue(C), translator(T), route(R).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting_fact", s))
    for c in CLUES:
        lines.append(asp.fact("clue_fact", c))
    for t in TRANSLATORS:
        lines.append(asp.fact("translator_fact", t))
    for r in ROUTES:
        lines.append(asp.fact("route_fact", r))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program(show="#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import storyworlds.asp as asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.clue not in CLUES or params.translator not in TRANSLATORS or params.route not in ROUTES:
        raise StoryError("(Invalid parameters for this storyworld.)")
    world = tell(
        SETTINGS[params.setting],
        CLUES[params.clue],
        TRANSLATORS[params.translator],
        ROUTES[params.route],
        child_name=params.child_name,
        child_gender=params.child_gender,
        guide_name=params.guide_name,
        guide_gender=params.guide_gender,
    )
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
        print(asp_program(show="#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
