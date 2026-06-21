#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/secretary_foreshadowing_myth.py
================================================================

A small, classical storyworld in a mythic register: a village secretary notices
omens in the temple records, warns the household before a storm, and helps the
people prepare a safe offering and a dry shelter.

The domain is intentionally tiny and state-driven:
- typed entities with physical meters and emotional memes,
- a premise, a foreshadowed turn, and a resolution,
- a reasonableness gate plus an inline ASP twin,
- three Q&A sets grounded in the simulated world.

This world's seed idea is "secretary" with foreshadowing in a myth style.
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

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"danger": 0.0, "rain": 0.0, "dryness": 0.0, "prepared": 0.0}
        if not self.memes:
            self.memes = {"calm": 0.0, "worry": 0.0, "hope": 0.0, "awe": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "queen", "priestess"}
        male = {"boy", "man", "father", "king", "priest"}
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
class Shrine:
    id: str
    name: str
    location: str
    omen: str
    shelter: str
    offering: str
    storm_signs: list[str] = field(default_factory=list)
    danger_need: str = "storm"
    safe_need: str = "shelter"
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
class Sign:
    id: str
    label: str
    detail: str
    warning: str
    certainty: int
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


@dataclass
class StoryParams:
    shrine: str
    sign: str
    response: str
    secretary_name: str
    secretary_type: str
    elder_name: str
    elder_type: str
    ruler_name: str
    ruler_type: str
    delay: int = 0
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


def _r_rain(world: World) -> list[str]:
    out = []
    storm = world.get("sky")
    if storm.meters["rain"] < THRESHOLD:
        return out
    sig = ("rain",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for ent in list(world.entities.values()):
        if ent.role == "secretary":
            ent.memes["worry"] += 1
        if ent.role == "elder":
            ent.memes["awe"] += 1
    world.get("path").meters["danger"] += 1
    out.append("__foreshadow__")
    return out


def _r_prepare(world: World) -> list[str]:
    out = []
    if world.get("store").meters["prepared"] < THRESHOLD:
        return out
    sig = ("prepare",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("hall").meters["dryness"] += 1
    out.append("__safe__")
    return out


CAUSAL_RULES = [Rule("rain", _r_rain), Rule("prepare", _r_prepare)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(b for b in bits if not b.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def storm_rises(world: World, shrine: Shrine) -> None:
    world.get("sky").meters["rain"] += 1
    world.get("sky").memes["worry"] += 1
    world.say(
        f"Over {shrine.location}, the sky gathered its dark cloak. "
        f"The first drops struck the stones like knuckles on a gate."
    )
    propagate(world, narrate=False)


def foreshadow(world: World, secretary: Entity, sign: Sign, shrine: Shrine) -> None:
    secretary.memes["awe"] += 1
    world.say(
        f"{secretary.id}, the secretary of the shrine, unrolled the old tablet of records. "
        f"{sign.detail} The ink seemed to tremble beside the line that named the coming storm."
    )
    world.say(
        f'{secretary.id} touched the margin. "{sign.warning}"'
    )
    world.facts["foreshadowed"] = True


def warn_elder(world: World, secretary: Entity, elder: Entity, shrine: Shrine) -> None:
    elder.memes["worry"] += 1
    world.say(
        f"{secretary.id} carried the sign to {elder.id}, the elder of the hall. "
        f"{elder.id} listened, because the records had never lied when the rain rose early."
    )


def choose_response(world: World, elder: Entity, resp: Response, shrine: Shrine) -> None:
    world.say(
        f"{elder.id} answered at once: {resp.text.replace('{shrine}', shrine.name)}."
    )
    world.get("store").meters["prepared"] += 1
    world.get("hall").meters["dryness"] += 1
    world.get("path").meters["danger"] = max(0.0, world.get("path").meters["danger"] - 1)


def fail_response(world: World, elder: Entity, resp: Response, shrine: Shrine) -> None:
    world.say(
        f"{elder.id} tried to help, but {resp.fail.replace('{shrine}', shrine.name)}."
    )
    world.get("path").meters["danger"] += 1


def shelter_scene(world: World, secretary: Entity, elder: Entity, ruler: Entity, shrine: Shrine) -> None:
    for ent in (secretary, elder, ruler):
        ent.memes["calm"] += 1
        ent.memes["hope"] += 1
    world.say(
        f"They lifted the shrine curtains, set the dry mats by the threshold, and moved the offerings to the inner room."
    )
    world.say(
        f"When the storm broke, {shrine.shelter} held the family together, and the rain drummed harmlessly on the roof."
    )
    world.say(
        f"By dawn, the {shrine.omen} had become only a memory, and {secretary.id} smiled over the fresh ink of the safe record."
    )


def doom_scene(world: World, secretary: Entity, elder: Entity, ruler: Entity, shrine: Shrine) -> None:
    for ent in (secretary, elder, ruler):
        ent.memes["worry"] += 1
    world.say(
        f"The wind came with a roar. The path flooded, the lanterns flickered, and the hall grew wet and cold."
    )
    world.say(
        f"Still, the people remembered {secretary.id}'s warning, and they led {ruler.id} into the stone shelter before the worst of the storm."
    )
    world.say(
        f"Even so, the offering room was soaked, and the old scrolls curled at the edges like leaves after rain."
    )


def tell(shrine: Shrine, sign: Sign, response: Response,
         secretary_name: str = "Nira", secretary_type: str = "woman",
         elder_name: str = "Bram", elder_type: str = "man",
         ruler_name: str = "Queen Ilya", ruler_type: str = "queen",
         delay: int = 0) -> World:
    world = World()
    secretary = world.add(Entity(id=secretary_name, kind="character", type=secretary_type, role="secretary"))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_type, role="elder"))
    ruler = world.add(Entity(id=ruler_name, kind="character", type=ruler_type, role="ruler"))
    sky = world.add(Entity(id="sky", type="sky", label="the sky"))
    store = world.add(Entity(id="store", type="store", label="the storehouse"))
    hall = world.add(Entity(id="hall", type="hall", label="the hall"))
    path = world.add(Entity(id="path", type="path", label="the path"))
    world.facts["delay"] = delay
    world.facts["shrine"] = shrine
    world.facts["sign"] = sign
    world.facts["response"] = response

    world.say(
        f"In the age when rivers spoke and mountains kept their promises, there stood {shrine.name}."
    )
    world.say(
        f"{secretary.id} kept the records there, and nothing escaped {secretary.pronoun('possessive')} careful hands."
    )

    world.para()
    foreshadow(world, secretary, sign, shrine)
    warn_elder(world, secretary, elder, shrine)
    storm_rises(world, shrine)

    world.para()
    if response.sense >= 2 and response.power >= (1 + delay):
        choose_response(world, elder, response, shrine)
        shelter_scene(world, secretary, elder, ruler, shrine)
        outcome = "safe"
    else:
        fail_response(world, elder, response, shrine)
        doom_scene(world, secretary, elder, ruler, shrine)
        outcome = "worn"

    world.facts["outcome"] = outcome
    world.facts["secretary"] = secretary
    world.facts["elder"] = elder
    world.facts["ruler"] = ruler
    world.facts["sky"] = sky
    world.facts["store"] = store
    world.facts["hall"] = hall
    world.facts["path"] = path
    return world


SHRINES = {
    "river": Shrine(
        id="river", name="the Shrine of the River",
        location="the riverside stair", omen="river omen", shelter="the stone hall",
        offering="a bowl of millet", storm_signs=["clouds", "wind"], danger_need="storm",
        safe_need="shelter", tags={"river", "storm"},
    ),
    "mountain": Shrine(
        id="mountain", name="the Shrine of the Mountain",
        location="the high pass", omen="mountain omen", shelter="the inner cave",
        offering="a lamp of oil", storm_signs=["wind", "rain"], danger_need="storm",
        safe_need="shelter", tags={"mountain", "storm"},
    ),
    "orchard": Shrine(
        id="orchard", name="the Orchard Shrine",
        location="the blossom road", omen="petal omen", shelter="the root chamber",
        offering="sweet pears", storm_signs=["rain"], danger_need="storm",
        safe_need="shelter", tags={"orchard", "storm"},
    ),
}

SIGNS = {
    "cloudmark": Sign(
        id="cloudmark", label="cloudmark",
        detail="A thin cloud mark had crossed the first tablet, just where the storm seasons were counted.",
        warning="The storm will arrive before the second bell. Send the lanterns in early.",
        certainty=3, tags={"cloud", "foreshadow"},
    ),
    "crackedseal": Sign(
        id="crackedseal", label="cracked seal",
        detail="The wax seal on the night ledger had cracked in a little white line.",
        warning="The roof will answer the rain if we leave the grain uncovered.",
        certainty=2, tags={"seal", "foreshadow"},
    ),
    "blackink": Sign(
        id="blackink", label="black ink stain",
        detail="A black ink stain had bloomed beside the drought column, dark as a crow's wing.",
        warning="The water will rise; move the offerings to the inner room.",
        certainty=3, tags={"ink", "foreshadow"},
    ),
}

RESPONSES = {
    "lanterns": Response(
        id="lanterns", sense=3, power=3,
        text="ordered the lanterns lit and moved the offerings under cover in {shrine}",
        fail="sent for lanterns too late",
        qa_text="lit the lanterns and moved the offerings under cover in {shrine}",
        tags={"light", "safe"},
    ),
    "shelter": Response(
        id="shelter", sense=3, power=4,
        text="opened the stone shelter and brought everyone inside {shrine}",
        fail="opened the shelter, but the flood had already cut off the door",
        qa_text="opened the stone shelter and brought everyone inside {shrine}",
        tags={"safe", "stone"},
    ),
    "cover_grain": Response(
        id="cover_grain", sense=2, power=2,
        text="covered the grain with thick cloths and kept it dry in {shrine}",
        fail="covered the grain, but the cloths were too thin for the rain",
        qa_text="covered the grain with thick cloths and kept it dry in {shrine}",
        tags={"cloth", "safe"},
    ),
    "run_away": Response(
        id="run_away", sense=1, power=1,
        text="ran away and hoped the storm would forget them",
        fail="ran away and hoped the storm would forget them",
        qa_text="ran away and hoped the storm would forget them",
        tags={"unsafe"},
    ),
}

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, shrine in SHRINES.items():
        for sig in SIGNS:
            for rid, resp in RESPONSES.items():
                if resp.sense >= 2 and resp.power >= 1:
                    combos.append((sid, sig, rid))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    shrine, sign, response = f["shrine"], f["sign"], f["response"]
    return [
        f'Write a mythic story for a child that includes the word "secretary" and a warning sign called {sign.label}.',
        f"Tell a short myth about {world.get('sky').label_word if 'sky' in world.entities else 'the sky'} and {shrine.name}, where a secretary sees a sign and helps the elders prepare.",
        f"Write a foreshadowing story in a myth style where the secretary notices {sign.detail.lower()} and the household chooses a safer response.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    secretary = f["secretary"]
    elder = f["elder"]
    ruler = f["ruler"]
    sign = f["sign"]
    shrine = f["shrine"]
    response = f["response"]
    items = [
        QAItem(
            question="Who noticed the warning first?",
            answer=f"{secretary.id} the secretary noticed it first. {secretary.id} was the one who read the sign in the records and carried the news to the elder."
        ),
        QAItem(
            question="Why did the story feel like a warning before the storm?",
            answer=f"The story foreshadowed the storm through {sign.label}. The old records and the strange mark made the danger clear before the rain arrived."
        ),
        QAItem(
            question="What did the elder do after hearing the secretary?",
            answer=f"{elder.id} listened and chose {response.qa_text.replace('{shrine}', shrine.name)}. That meant the people could prepare before the storm grew strong."
        ),
    ]
    if f["outcome"] == "safe":
        items.append(QAItem(
            question="How did the story end?",
            answer=f"It ended safely. {ruler.id} and the people stayed dry in {shrine.shelter}, and the secretary's warning had helped them prepare in time."
        ))
    else:
        items.append(QAItem(
            question="How did the story end?",
            answer=f"It ended with wet floors and soaked scrolls, though the people still got to safety. The warning still mattered because it helped them move before the worst of the storm."
        ))
    return items


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a secretary?",
            answer="A secretary is a person who keeps records, writes things down, and helps important messages reach the right people."
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a clue that hints something will happen later. It can make a story feel like the world is speaking in advance."
        ),
        QAItem(
            question="What should people do when a storm is coming?",
            answer="They should gather their things, stay under shelter, and move anything fragile or important to a dry place."
        ),
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
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.role:
            parts.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        shrine="river", sign="cloudmark", response="lanterns",
        secretary_name="Nira", secretary_type="woman",
        elder_name="Bram", elder_type="man",
        ruler_name="Queen Ilya", ruler_type="queen", delay=0,
    ),
    StoryParams(
        shrine="mountain", sign="blackink", response="shelter",
        secretary_name="Tala", secretary_type="woman",
        elder_name="Oren", elder_type="man",
        ruler_name="King Miro", ruler_type="king", delay=0,
    ),
    StoryParams(
        shrine="orchard", sign="crackedseal", response="cover_grain",
        secretary_name="Sera", secretary_type="woman",
        elder_name="Pavo", elder_type="man",
        ruler_name="Lady Ren", ruler_type="queen", delay=1,
    ),
]


def explain_rejection(response: Response) -> str:
    return f"(No story: the response '{response.id}' is too weak or too unsafe for this mythic warning.)"


def valid_response(rid: str) -> bool:
    return RESPONSES[rid].sense >= 2 and RESPONSES[rid].power >= 2


ASP_RULES = r"""
valid(SH, SG, R) :- shrine(SH), sign(SG), response(R), sense(R, S), S >= 2, power(R, P), P >= 2.
safe(R) :- response(R), sense(R, S), S >= 2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SHRINES:
        lines.append(asp.fact("shrine", sid))
    for gid in SIGNS:
        lines.append(asp.fact("sign", gid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show safe/1."))
    return sorted(r for (r,) in asp.atoms(model, "safe"))


def asp_verify() -> int:
    import random as _r
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH: ASP and Python combo gates differ.")
    if set(asp_sensible()) == {rid for rid, r in RESPONSES.items() if r.sense >= 2}:
        print("OK: sensible responses match.")
    else:
        rc = 1
        print("MISMATCH: sensible responses differ.")
    # smoke test ordinary generation
    try:
        sample = generate(resolve_params(argparse.Namespace(
            shrine=None, sign=None, response=None, secretary_name=None,
            secretary_type=None, elder_name=None, elder_type=None,
            ruler_name=None, ruler_type=None, delay=None
        ), _r.Random(777)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic secretary storyworld with foreshadowing.")
    ap.add_argument("--shrine", choices=SHRINES)
    ap.add_argument("--sign", choices=SIGNS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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
    if args.response and not valid_response(args.response):
        raise StoryError(explain_rejection(RESPONSES[args.response]))
    combos = [c for c in valid_combos()
              if (args.shrine is None or c[0] == args.shrine)
              and (args.sign is None or c[1] == args.sign)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    shrine, sign, response = rng.choice(sorted(combos))
    return StoryParams(
        shrine=shrine, sign=sign, response=response,
        secretary_name=rng.choice(["Nira", "Tala", "Sera", "Aru"]),
        secretary_type="woman",
        elder_name=rng.choice(["Bram", "Oren", "Pavo"]),
        elder_type="man",
        ruler_name=rng.choice(["Queen Ilya", "King Miro", "Lady Ren"]),
        ruler_type=rng.choice(["queen", "king", "queen"]),
        delay=args.delay if args.delay is not None else rng.randint(0, 2),
    )


def generate(params: StoryParams) -> StorySample:
    if params.shrine not in SHRINES or params.sign not in SIGNS or params.response not in RESPONSES:
        raise StoryError("Invalid story parameters.")
    world = tell(SHRINES[params.shrine], SIGNS[params.sign], RESPONSES[params.response],
                 params.secretary_name, params.secretary_type,
                 params.elder_name, params.elder_type,
                 params.ruler_name, params.ruler_type, params.delay)
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
        print(asp_program("", "#show valid/3.\n#show safe/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        for t in asp_valid_combos():
            print(t)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            p = resolve_params(args, random.Random(base_seed + i))
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
