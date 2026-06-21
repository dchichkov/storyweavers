#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/succulent_burnous_anthem_lesson_learned_reconciliation_tall.py
================================================================================================

A standalone story world sketch for a tall-tale style lesson about a prized
succulent, a borrowed burnous, and an anthem sung too boldly.

Premise
-------
A child wants to show off a rare succulent at a windy street fair while wearing
a grand burnous. A boastful anthem attracts attention, the plant is threatened
by the weather, and a quarrel grows between the child and a helper. The world
then turns on a practical rescue, a lesson learned, and a reconciliation.

This script follows the Storyweavers contract:
- typed entities with physical meters and emotional memes
- a world model that drives prose
- a reasonableness gate with inline ASP twin
- three Q&A sets grounded in world state, not rendered text
- support for default, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
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
BRAVERY_INIT = 5.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type)
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
    breeze: str
    stage: str
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
class Prize:
    id: str
    label: str
    phrase: str
    fragrance: str
    fragile: bool = True
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
class Garment:
    id: str
    label: str
    phrase: str
    warmth: str
    status: str
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
class Anthem:
    id: str
    title: str
    loudness: int
    causes_attention: bool
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
class Response:
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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["at_risk"] < THRESHOLD:
            continue
        sig = ("worry", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "helper" in world.entities:
            world.get("helper").memes["worry"] += 1
        out.append("__worry__")
    return out


def _r_scatter(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("anthem_sung") and world.facts.get("attention") >= 1:
        sig = ("scatter", "crowd")
        if sig not in world.fired:
            world.fired.add(sig)
            if "helper" in world.entities:
                world.get("helper").memes["frustration"] += 1
            out.append("The crowd leaned in close, and the problem grew as large as a windmill.")
    return out


CAUSAL_RULES = [Rule("worry", "social", _r_worry), Rule("scatter", "social", _r_scatter)]


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


def reasonable_anthem(anthem: Anthem) -> bool:
    return anthem.causes_attention and anthem.loudness >= 2


def reasonable_response(response: Response) -> bool:
    return response.sense >= SENSE_MIN


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for prize_id, prize in PRIZES.items():
            for anthem_id, anthem in ANTHEMS.items():
                if prize.fragile and anthem.causes_attention:
                    combos.append((setting, prize_id, anthem_id))
    return combos


def _calm(world: World, helper: Entity, child: Entity) -> None:
    helper.memes["calm"] += 1
    world.say(
        f"{helper.id} drew a long breath and said, "
        f'"The wind is wild, but we can still keep the little thing safe."'
    )
    child.memes["shame"] += 1


def predict_loss(world: World, prize_id: str, anthem_id: str) -> dict:
    sim = world.copy()
    sim.facts["anthem_sung"] = True
    sim.facts["attention"] = ANTHEMS[anthem_id].loudness
    sim.get(prize_id).meters["at_risk"] += 1
    propagate(sim, narrate=False)
    return {
        "damage": sim.get(prize_id).meters["damage"],
        "worry": sim.get("helper").memes["worry"] if "helper" in sim.entities else 0,
    }


def blow_wind(world: World, setting: Setting) -> None:
    world.say(
        f"At {setting.place}, the breeze came sweeping by like a herd of white horses, "
        f"and every ribbon and hat tried to lean with it."
    )


def show_prize(world: World, child: Entity, prize: Entity, garment: Entity) -> None:
    world.say(
        f"{child.id} brought out {prize.phrase}, tucked beside {child.pronoun('possessive')} "
        f"{garment.label}, and swore it looked finer than a king's jewel."
    )
    child.memes["pride"] += 1


def sing_anthem(world: World, child: Entity, anthem: Anthem) -> None:
    world.facts["anthem_sung"] = True
    world.facts["attention"] = anthem.loudness
    child.memes["boldness"] += 1
    world.say(
        f'{child.id} sang "{anthem.title}" so loudly that even the sparrows turned their heads.'
    )
    world.say("For one shining minute, the whole fair seemed to stand still and listen.")


def warn(world: World, helper: Entity, child: Entity, prize: Entity, garment: Entity) -> None:
    pred = predict_loss(world, prize.id, world.facts["anthem"].id)
    helper.memes["worry"] += 1
    world.say(
        f'{helper.id} pointed at the {prize.label} and said, '
        f'"That song is louder than a thunder drum. The wind can worry a {prize.label} '
        f'right out of your hands if we do not tuck it down inside the {garment.label}."'
    )
    world.facts["predicted_damage"] = pred["damage"]


def defy(world: World, child: Entity) -> None:
    child.memes["defiance"] += 1
    world.say(
        f'"Oh, I can manage!" {child.id} called, puffing up like a proud peacock.'
    )


def mishap(world: World, prize: Entity) -> None:
    prize.meters["at_risk"] += 1
    prize.meters["damage"] += 1
    propagate(world, narrate=True)
    world.say(
        f"Then a gust came tearing through the fair and worried the succulent's leaves "
        f"until they trembled like green pennies in a tin cup."
    )


def rescue(world: World, helper: Entity, response: Response, prize: Entity, garment: Garment) -> None:
    body = response.text.replace("{prize}", prize.label)
    world.say(
        f"{helper.id} hurried in and {body}."
    )
    prize.meters["at_risk"] = 0
    world.say(
        f"{garment.label.capitalize()} wrapped around the little plant like a snug barn wall."
    )


def lesson(world: World, helper: Entity, child: Entity) -> None:
    helper.memes["affection"] += 1
    child.memes["lesson"] += 1
    child.memes["softness"] += 1
    world.say(
        f'For a moment, the two of them stood quiet. Then {helper.id} knelt and said, '
        f'"A loud song is a fine thing, but a wise song knows when to make room for the wind."'
    )
    world.say(
        f'{child.id} nodded and answered, "I learned it now. I will keep the succulent safer next time."'
    )


def reconcile(world: World, child: Entity, helper: Entity) -> None:
    child.memes["reconciliation"] += 1
    helper.memes["reconciliation"] += 1
    world.say(
        f"After that, {child.id} held out a hand, and {helper.id} took it at once. "
        f"They laughed, not because the wind was gone, but because the trouble was past."
    )


def ending(world: World, child: Entity, prize: Entity, garment: Garment, setting: Setting) -> None:
    world.say(
        f"By sundown, the succulent sat safe beside the stage, tucked out of the gusts, "
        f"and the burnous hung over it like a heroic tent. The fair kept on singing, "
        f"but now the song was gentle enough for the leaves to sleep beneath."
    )


def tell(setting: Setting, prize_cfg: Prize, garment_cfg: Garment, anthem_cfg: Anthem,
         child_name: str = "Mira", child_gender: str = "girl",
         helper_name: str = "Uncle", helper_gender: str = "man",
         response: Response = None) -> World:
    if response is None:
        response = RESPONSES["wrap"]
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    world.add(Entity(id="setting", type="place", label=setting.place))
    prize = world.add(Entity(id="succulent", type="plant", label=prize_cfg.label))
    garment = world.add(Entity(id="burnous", type="garment", label=garment_cfg.label))
    anthem = world.add(Entity(id="anthem", type="anthem", label=anthem_cfg.title))

    child.memes["joy"] += 1
    world.facts.update(setting=setting, prize=prize_cfg, garment=garment_cfg, anthem=anthem_cfg,
                       response=response, child=child, helper=helper)

    blow_wind(world, setting)
    show_prize(world, child, prize, garment)

    world.para()
    sing_anthem(world, child, anthem_cfg)
    warn(world, helper, child, prize, garment)
    defy(world, child)

    world.para()
    mishap(world, prize)
    rescue(world, helper, response, prize, garment)
    lesson(world, helper, child)
    reconcile(world, child, helper)
    ending(world, child, prize, garment, setting)

    world.facts["outcome"] = "reconciled"
    world.facts["lesson"] = True
    return world


SETTINGS = {
    "fairground": Setting(id="fairground", place="the big fairground", breeze="windy", stage="wagon stage", crowd="crowd"),
    "mesa": Setting(id="mesa", place="the red mesa market", breeze="gusty", stage="wooden platform", crowd="neighbors"),
    "riverbank": Setting(id="riverbank", place="the riverbank festival", breeze="breezy", stage="barge stage", crowd="townsfolk"),
}

PRIZES = {
    "succulent": Prize(id="succulent", label="succulent", phrase="a tiny round succulent in a clay cup", fragrance="sweet"),
    "cactus": Prize(id="cactus", label="succulent", phrase="a stubborn little succulent with thick leaves", fragrance="fresh"),
}

GARMENTS = {
    "burnous": Garment(id="burnous", label="burnous", phrase="a white burnous with a broad hood", warmth="warm", status="borrowed"),
    "mantle": Garment(id="mantle", label="burnous", phrase="a long burnous that fluttered like a sail", warmth="warm", status="loaned"),
}

ANTHEMS = {
    "anthem": Anthem(id="anthem", title="The Windy Little Anthem", loudness=4, causes_attention=True),
    "march": Anthem(id="march", title="The Proud Road Anthem", loudness=3, causes_attention=True),
}

RESPONSES = {
    "wrap": Response(id="wrap", sense=3, power=3,
                     text="wrapped the succulent in the burnous and carried it under one arm like a royal lantern",
                     fail="tried to wrap the succulent, but the wind had already done its worst",
                     qa_text="wrapped the succulent in the burnous and carried it to safety"),
    "shield": Response(id="shield", sense=2, power=2,
                       text="held the burnous high like a shield and walked the succulent behind it",
                       fail="held the burnous up, but the gust was stronger than the plan",
                       qa_text="held the burnous high and shielded the succulent"),
    "crate": Response(id="crate", sense=3, power=4,
                      text="set the succulent inside a crate lined with cloth and tied the burnous around it",
                      fail="lined up the crate, but the wind still rattled it apart",
                      qa_text="set the succulent inside a crate and tied the burnous around it"),
    "bucket": Response(id="bucket", sense=1, power=1,
                       text="filled a bucket with water and splashed it near the succulent",
                       fail="splashed water around, but that did little against the wind",
                       qa_text="filled a bucket with water and splashed it nearby"),
}


@dataclass
class StoryParams:
    setting: str
    prize: str
    garment: str
    anthem: str
    response: str
    child_name: str = "Mira"
    child_gender: str = "girl"
    helper_name: str = "Uncle"
    helper_gender: str = "man"
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world with a succulent, a burnous, and an anthem.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--garment", choices=GARMENTS)
    ap.add_argument("--anthem", choices=ANTHEMS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["woman", "man"])
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


def _pick(rng: random.Random, choices: list[str]) -> str:
    return rng.choice(sorted(choices))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and not reasonable_response(RESPONSES[args.response]):
        raise StoryError(f"(Refusing response '{args.response}': too weak for a tall-tale rescue.)")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.prize is None or c[1] == args.prize)
              and (args.anthem is None or c[2] == args.anthem)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, prize, anthem = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting,
        prize=prize,
        garment=args.garment or _pick(rng, list(GARMENTS)),
        anthem=anthem,
        response=args.response or _pick(rng, [r.id for r in RESPONSES.values() if reasonable_response(r)]),
        child_name=args.name or _pick(rng, ["Mira", "June", "Lena", "Tessa", "Bess"]),
        child_gender=args.gender or "girl",
        helper_name=args.helper or _pick(rng, ["Uncle", "Aunt", "Father", "Mother"]),
        helper_gender=args.helper_gender or _pick(rng, ["woman", "man"]),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall tale for a child about a {f["prize"].label}, a {f["garment"].label}, and a loud anthem.',
        f"Tell a story where {f['child'].id} gets too proud, then learns a better way and makes peace with {f['helper'].id}.",
        'Write a story that includes the words "succulent", "burnous", and "anthem", and ends with a lesson learned and reconciliation.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper = f["child"], f["helper"]
    setting, prize, garment, anthem = f["setting"], f["prize"], f["garment"], f["anthem"]
    response = f["response"]
    return [
        ("Who is the story about?",
         f"It is about {child.id} and {helper.id} at {setting.place}. The tall-tale trouble grows around the succulent and the burnous."), 
        ("Why did the helper worry?",
         f"{helper.id} worried because the anthem was loud and the wind was already rough. A fragile succulent can be shaken badly when attention and gusts arrive together."),
        ("What fixed the trouble?",
         f"{helper.id} used the {response.id} plan and wrapped the succulent in the burnous. That made the plant safe, and it gave everyone a calmer way forward."),
        ("What was learned?",
         f"{child.id} learned that being proud is not the same as being wise. A gentler song and a safer plan kept the succulent safe."),
        ("How did the story end?",
         f"{child.id} and {helper.id} reconciled and stood together again. The succulent stayed safe, and the burnous became a shelter instead of a boast."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a succulent?",
         "A succulent is a plant with thick leaves that stores water. Many succulents can handle dry weather, but they still need gentle care."),
        ("What is a burnous?",
         "A burnous is a long cloak with a hood. People wear it to stay warm and covered."),
        ("What is an anthem?",
         "An anthem is a song meant to be proud or important. It is often sung loudly so many people can hear it."),
    ]


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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,P,A) :- setting(S), prize(P), anthem(A).
sensible_response(R) :- response(R), sense(R, N), sense_min(M), N >= M.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        if p.fragile:
            lines.append(asp.fact("fragile", pid))
    for aid in ANTHEMS:
        lines.append(asp.fact("anthem", aid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_responses() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible_response/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible_response"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos().")
    if set(asp_sensible_responses()) == {r.id for r in RESPONSES.values() if reasonable_response(r)}:
        print("OK: sensible responses match.")
    else:
        rc = 1
        print("MISMATCH in sensible responses.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        assert sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


CURATED = [
    StoryParams(setting="fairground", prize="succulent", garment="burnous", anthem="anthem", response="wrap",
                child_name="Mira", child_gender="girl", helper_name="Uncle", helper_gender="man"),
    StoryParams(setting="mesa", prize="cactus", garment="mantle", anthem="march", response="crate",
                child_name="Bess", child_gender="girl", helper_name="Aunt", helper_gender="woman"),
    StoryParams(setting="riverbank", prize="succulent", garment="burnous", anthem="anthem", response="shield",
                child_name="June", child_gender="girl", helper_name="Father", helper_gender="man"),
]

def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.prize not in PRIZES or params.garment not in GARMENTS or params.anthem not in ANTHEMS or params.response not in RESPONSES:
        raise StoryError("Invalid story parameters.")
    response = RESPONSES[params.response]
    if not reasonable_response(response):
        raise StoryError("Response is too weak for this world.")
    world = tell(SETTINGS[params.setting], PRIZES[params.prize], GARMENTS[params.garment], ANTHEMS[params.anthem],
                 child_name=params.child_name, child_gender=params.child_gender,
                 helper_name=params.helper_name, helper_gender=params.helper_gender,
                 response=response)
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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible_response/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for s, p, a in asp_valid_combos():
            print(f"  {s:12} {p:10} {a}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
