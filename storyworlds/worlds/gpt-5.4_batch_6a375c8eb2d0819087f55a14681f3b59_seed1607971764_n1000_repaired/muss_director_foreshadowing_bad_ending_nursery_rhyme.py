#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/muss_director_foreshadowing_bad_ending_nursery_rhyme.py
==================================================================================

A standalone storyworld for a nursery-rhyme-like tale about a little stage show,
a growing muss, a careful director, and a bad ending that was foreshadowed early.

The world models a child nursery performance:
- A little performer wants extra pretty things for a pretend show.
- Those things create a muss on or near the tiny stage steps.
- The director notices the warning sign first and says so.
- The performer ignores the warning.
- At show time, the clutter causes a tumble or snarl.
- The show ends sadly, with a final image that proves what changed.

Run it
------
    python storyworlds/worlds/gpt-5.4/muss_director_foreshadowing_bad_ending_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/muss_director_foreshadowing_bad_ending_nursery_rhyme.py --prop ribbon --risk steps
    python storyworlds/worlds/gpt-5.4/muss_director_foreshadowing_bad_ending_nursery_rhyme.py --risk rug
    python storyworlds/worlds/gpt-5.4/muss_director_foreshadowing_bad_ending_nursery_rhyme.py --all --qa
    python storyworlds/worlds/gpt-5.4/muss_director_foreshadowing_bad_ending_nursery_rhyme.py --verify
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    dangerous: bool = False
    tangle_risk: bool = False
    trip_risk: bool = False
    fragile: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "hen", "goose"}
        male = {"boy", "father", "man", "gander"}
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
class StageTheme:
    id: str
    troupe: str
    opening: str
    chant: str
    final_image: str
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
class Prop:
    id: str
    label: str
    phrase: str
    scatter: str
    snag: str
    mess_kind: str
    trip_risk: bool = False
    tangle_risk: bool = False
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
class RiskSpot:
    id: str
    label: str
    the: str
    issue: str
    trip_works: bool = False
    tangle_works: bool = False
    spread: int = 1
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]
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
class Finale:
    id: str
    sense: int
    power: int
    text: str
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
        clone.facts = copy.deepcopy(self.facts)
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


def _r_clutter_grows(world: World) -> list[str]:
    out: list[str] = []
    prop = world.get("prop")
    risk = world.get("risk")
    room = world.get("room")
    if prop.meters["spilled"] >= THRESHOLD and risk.meters["ready_for_accident"] < THRESHOLD:
        sig = ("ready", prop.id, risk.id)
        if sig not in world.fired:
            world.fired.add(sig)
            risk.meters["ready_for_accident"] += 1
            room.meters["danger"] += float(world.facts.get("hazard_power", 1))
            out.append("__foreshadowed__")
    return out


def _r_fallout(world: World) -> list[str]:
    out: list[str] = []
    risk = world.get("risk")
    performer = world.get("performer")
    room = world.get("room")
    if risk.meters["accident"] >= THRESHOLD:
        sig = ("sadness", performer.id)
        if sig not in world.fired:
            world.fired.add(sig)
            performer.memes["shock"] += 1
            performer.memes["sadness"] += 1
            room.meters["show_stopped"] += 1
            out.append("__ending__")
    return out


CAUSAL_RULES = [
    Rule(name="clutter_grows", tag="physical", apply=_r_clutter_grows),
    Rule(name="fallout", tag="social", apply=_r_fallout),
]


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


def hazard_at_risk(prop: Prop, risk: RiskSpot) -> bool:
    if prop.trip_risk and risk.trip_works:
        return True
    if prop.tangle_risk and risk.tangle_works:
        return True
    return False


def sensible_finales() -> list[Finale]:
    return [f for f in FINALES.values() if f.sense >= SENSE_MIN]


def hazard_power(prop: Prop, risk: RiskSpot) -> int:
    base = risk.spread
    if prop.trip_risk and risk.trip_works:
        base += 1
    if prop.tangle_risk and risk.tangle_works:
        base += 1
    return base


def is_ruin(finale: Finale, prop: Prop, risk: RiskSpot) -> bool:
    return finale.power < hazard_power(prop, risk)


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    sim.get("prop").meters["spilled"] += 1
    propagate(sim, narrate=False)
    return {
        "danger": sim.get("room").meters["danger"],
        "foreshadowed": sim.get("risk").meters["ready_for_accident"] >= THRESHOLD,
    }


def open_stage(world: World, performer: Entity, director: Entity, theme: StageTheme) -> None:
    performer.memes["joy"] += 1
    director.memes["care"] += 1
    world.say(
        f"In the nursery room, where lamplight lay, "
        f"{performer.id} and the {director.role} planned a play."
    )
    world.say(
        f"{theme.opening} {theme.chant}"
    )


def costume_pride(world: World, performer: Entity, prop: Prop) -> None:
    performer.memes["pride"] += 1
    world.say(
        f'"Just one more {prop.label}, bright and fine, '
        f'and I shall be the star that shines," said {performer.id}.'
    )


def foreshadow(world: World, director: Entity, performer: Entity, prop: Prop, risk: RiskSpot) -> None:
    pred = predict_trouble(world)
    world.facts["predicted_danger"] = pred["danger"]
    director.memes["worry"] += 1
    world.say(
        f"But the {director.role} saw, before the song, "
        f"that {prop.scatter} might not lie long."
    )
    world.say(
        f'"Mind the muss by {risk.the}," said {director.id}. '
        f'"If we leave it there, the march may slide or snag and not go right."'
    )


def defy(world: World, performer: Entity, prop: Prop) -> None:
    performer.memes["defiance"] += 1
    performer.memes["haste"] += 1
    world.get("prop").meters["spilled"] += 1
    propagate(world, narrate=False)
    world.say(
        f'But {performer.id} laughed a hurried tune. '
        f'"There is time to tidy up soon!"'
    )
    world.say(
        f"So {prop.scatter}, light and loose, "
        f"and made a merry-looking muss."
    )


def curtain_rise(world: World, theme: StageTheme) -> None:
    world.say(
        f"Soon the little drum went tap-tap-tap, "
        f"and all the nursery held its lap."
    )
    world.say(
        f"The show began for {theme.troupe}, "
        f"with bow and bounce and skipping loop."
    )


def accident(world: World, performer: Entity, prop: Prop, risk: RiskSpot) -> None:
    risk_ent = world.get("risk")
    risk_ent.meters["accident"] += 1
    performer.meters["fallen"] += 1
    performer.meters["costume_torn"] += 1
    world.get("prop").meters["ruined"] += 1
    propagate(world, narrate=False)

    if prop.trip_risk and risk.trip_works and not (prop.tangle_risk and risk.tangle_works):
        line = (
            f"But on {risk.the}, in the middle of the beat, "
            f"{performer.id} came down with a thump from dancing feet."
        )
    elif prop.tangle_risk and risk.tangle_works and not (prop.trip_risk and risk.trip_works):
        line = (
            f"But by {risk.the}, in the middle of the rhyme, "
            f"{prop.snag} at just the worst small time."
        )
    else:
        line = (
            f"But by {risk.the}, with a tug and stumble-sound, "
            f"{performer.id} lurched and tumbled to the ground."
        )

    world.say(line)
    world.say(
        f"The chorus broke, the lantern shook, "
        f"and every watching face lost its look."
    )


def bad_ending(world: World, performer: Entity, director: Entity, theme: StageTheme, finale: Finale) -> None:
    performer.memes["joy"] = 0.0
    performer.memes["sadness"] += 1
    director.memes["sadness"] += 1
    world.say(
        finale.text
    )
    world.say(
        f'{director.id}, the {director.role}, did not scold or shout. '
        f'{director.pronoun().capitalize()} only gathered the songbooks when the lights went out.'
    )
    world.say(
        f"{theme.final_image} "
        f"{performer.id} looked at the muss and knew too late that warnings can come before woe."
    )


def tell(
    theme: StageTheme,
    prop: Prop,
    risk: RiskSpot,
    finale: Finale,
    performer_name: str = "Molly",
    performer_type: str = "girl",
    director_name: str = "Wren",
    director_type: str = "goose",
) -> World:
    world = World()
    performer = world.add(Entity(
        id=performer_name,
        kind="character",
        type=performer_type,
        label=performer_name,
        role="performer",
        traits=["eager", "little"],
        attrs={},
    ))
    director = world.add(Entity(
        id=director_name,
        kind="character",
        type=director_type,
        label=director_name,
        role="director",
        traits=["careful"],
        attrs={},
    ))
    world.add(Entity(id="room", type="room", label="nursery room"))
    world.add(Entity(
        id="prop",
        type="prop",
        label=prop.label,
        trip_risk=prop.trip_risk,
        tangle_risk=prop.tangle_risk,
    ))
    world.add(Entity(
        id="risk",
        type="risk",
        label=risk.label,
        trip_risk=risk.trip_works,
        tangle_risk=risk.tangle_works,
    ))

    world.facts["hazard_power"] = hazard_power(prop, risk)
    world.facts["theme"] = theme
    world.facts["prop_cfg"] = prop
    world.facts["risk_cfg"] = risk
    world.facts["finale"] = finale
    world.facts["performer"] = performer
    world.facts["director"] = director

    open_stage(world, performer, director, theme)
    costume_pride(world, performer, prop)

    world.para()
    foreshadow(world, director, performer, prop, risk)
    defy(world, performer, prop)

    world.para()
    curtain_rise(world, theme)
    accident(world, performer, prop, risk)

    world.para()
    bad_ending(world, performer, director, theme, finale)

    ruined = is_ruin(finale, prop, risk)
    outcome = "ruined" if ruined else "saved"
    world.facts.update(
        outcome=outcome,
        hazard=hazard_at_risk(prop, risk),
        ruined=ruined,
        prop=world.get("prop"),
        risk=world.get("risk"),
        foreshadowed=world.get("risk").meters["ready_for_accident"] >= THRESHOLD,
    )
    return world


THEMES = {
    "moon_march": StageTheme(
        id="moon_march",
        troupe="the moon march",
        opening="They trimmed a tiny silver stage with paper stars and spray,",
        chant='They sang, "Trip-trap, tap-tap, twirl away!"',
        final_image="The paper moon drooped over the window, and one bent shoe lay by the footstool.",
        tags={"nursery", "show"},
    ),
    "lamb_lilt": StageTheme(
        id="lamb_lilt",
        troupe="the lamb lilt",
        opening="They chalked a ring upon the floor where woolly steps would sway,",
        chant='They sang, "Lilt-lamb, tilt-lamb, dance away!"',
        final_image="The chalk ring smudged into a pale cloud, and one torn bow slept by the stool.",
        tags={"nursery", "show"},
    ),
    "thimble_reel": StageTheme(
        id="thimble_reel",
        troupe="the thimble reel",
        opening="They built a little toy-box stage where nimble toes could play,",
        chant='They sang, "Reel-thimble, heel-thimble, skip away!"',
        final_image="The toy-box lid stood half ajar, and a crumpled cap lay by the stool.",
        tags={"nursery", "show"},
    ),
}

PROPS = {
    "ribbon": Prop(
        id="ribbon",
        label="ribbon",
        phrase="a long satin ribbon",
        scatter="the ribbon trailed in curls across the floor",
        snag="the ribbon caught round an ankle",
        mess_kind="trail",
        trip_risk=False,
        tangle_risk=True,
        tags={"ribbon", "clutter"},
    ),
    "confetti": Prop(
        id="confetti",
        label="confetti",
        phrase="a fistful of paper confetti",
        scatter="the confetti spread in bright slips over the floorboards",
        snag="the paper slips slid under a shoe",
        mess_kind="scatter",
        trip_risk=True,
        tangle_risk=False,
        tags={"confetti", "clutter"},
    ),
    "garland": Prop(
        id="garland",
        label="garland",
        phrase="a loop of paper garland",
        scatter="the garland sagged from the costume and puddled by the edge",
        snag="the garland twisted round a foot and the banister peg",
        mess_kind="loop",
        trip_risk=True,
        tangle_risk=True,
        tags={"garland", "clutter"},
    ),
}

RISKS = {
    "steps": RiskSpot(
        id="steps",
        label="stage steps",
        the="the stage steps",
        issue="little feet must climb there in time with the song",
        trip_works=True,
        tangle_works=True,
        spread=2,
        tags={"steps", "stage"},
    ),
    "rug": RiskSpot(
        id="rug",
        label="braided rug",
        the="the braided rug",
        issue="the rug can wrinkle under hurried toes",
        trip_works=True,
        tangle_works=False,
        spread=1,
        tags={"rug", "stage"},
    ),
    "stool": RiskSpot(
        id="stool",
        label="painted stool",
        the="the painted stool",
        issue="the stool has legs that catch loose things",
        trip_works=False,
        tangle_works=True,
        spread=1,
        tags={"stool", "stage"},
    ),
    "window": RiskSpot(
        id="window",
        label="window ledge",
        the="the window ledge",
        issue="the ledge is high and still, not a place where dancing feet pass",
        trip_works=False,
        tangle_works=False,
        spread=0,
        tags={"window"},
    ),
}

FINALES = {
    "stopped_song": Finale(
        id="stopped_song",
        sense=2,
        power=0,
        text="The tune fell flat, the children froze, and the night-time show was done before its close.",
        qa_text="the song stopped and the nursery show ended sadly",
        tags={"sad", "show"},
    ),
    "torn_costume": Finale(
        id="torn_costume",
        sense=2,
        power=0,
        text="A tear ran down the costume hem, and no one wished to dance again with them.",
        qa_text="the costume tore and the dance could not go on",
        tags={"sad", "costume"},
    ),
    "quiet_room": Finale(
        id="quiet_room",
        sense=2,
        power=0,
        text="Soon even the drum was still and dumb, and the nursery room went quiet as a thumb.",
        qa_text="the room went quiet and the little performance ended",
        tags={"sad", "show"},
    ),
}

GIRL_NAMES = ["Molly", "Tess", "Nell", "May", "Dora", "Poppy", "Bess", "Elsie"]
BOY_NAMES = ["Toby", "Ned", "Pip", "Robin", "Kit", "Milo", "Bram", "Hugh"]
DIRECTOR_NAMES = ["Wren", "Goody", "Mavis", "Dot", "Pru"]

KNOWLEDGE = {
    "ribbon": [("What can happen if a long ribbon is left on the floor?",
                "A long ribbon can wrap around feet or furniture and make someone stumble. Loose things on the floor are easier to catch than children expect.")],
    "confetti": [("Why can confetti be slippery?",
                  "Tiny paper bits can slide under shoes or make a floor feel less steady. That is why people sweep it up after a party.")],
    "garland": [("Why can a garland make a mess?",
                 "A garland can droop, drag, or twist when it is too long for the place. If it hangs near feet, it can tangle instead of decorate.")],
    "steps": [("Why are stage steps tricky during a show?",
               "Stage steps are small places where feet have to land neatly and in order. When children hurry on them, clutter makes a tumble more likely.")],
    "rug": [("Why can a rug be dangerous for running feet?",
             "A rug can bunch or slide if people rush across it. Even a little wrinkle can catch a toe.")],
    "director": [("What does a director do in a play?",
                  "A director helps everyone know where to stand, when to move, and how to keep the show together. A careful director notices trouble before the curtain rises.")],
    "foreshadow": [("What is foreshadowing in a story?",
                    "Foreshadowing is a clue that hints at trouble before it happens. It helps a reader feel that the ending grew out of earlier warning signs.")],
}
KNOWLEDGE_ORDER = ["director", "foreshadow", "ribbon", "confetti", "garland", "steps", "rug"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for theme_id in THEMES:
        for prop_id, prop in PROPS.items():
            for risk_id, risk in RISKS.items():
                if hazard_at_risk(prop, risk):
                    combos.append((theme_id, prop_id, risk_id))
    return combos


@dataclass
class StoryParams:
    theme: str
    prop: str
    risk: str
    finale: str
    performer_name: str
    performer_type: str
    director_name: str
    director_type: str
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


def pair_kind(performer: Entity) -> str:
    return "girl" if performer.type == "girl" else "boy"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    performer = f["performer"]
    director = f["director"]
    prop = f["prop_cfg"]
    risk = f["risk_cfg"]
    theme = f["theme"]
    return [
        f'Write a nursery-rhyme-style story that includes the words "muss" and "director" and ends badly.',
        f"Tell a rhyming nursery tale about a little {pair_kind(performer)} named {performer.id} in {theme.troupe}, where the director warns about a muss near {risk.the}, but the warning is ignored.",
        f"Write a short foreshadowing story where {prop.phrase} causes trouble during a tiny stage performance and the ending turns sad instead of neat.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    performer = f["performer"]
    director = f["director"]
    prop = f["prop_cfg"]
    risk = f["risk_cfg"]
    finale = f["finale"]
    theme = f["theme"]
    qa: list[tuple[str, str]] = [
        ("Who is the story about?",
         f"It is about {performer.id}, a little performer in {theme.troupe}, and {director.id}, the careful director. They were getting ready for a nursery show together."),
        (f"What was the warning before the bad ending?",
         f"The director noticed that {prop.scatter} near {risk.the}. That was foreshadowing, because the warning came before the tumble and hinted that the stage would not stay safe."),
        (f"Why did the stage turn into a muss?",
         f"{performer.id} wanted one more pretty thing and left {prop.label} lying loose instead of tidying it away. The pretty prop became a muss because it was in the very place where the marching feet had to go."),
        (f"What happened during the show?",
         f"When the music started, the clutter caused trouble by {risk.issue}. Then {finale.qa_text}, so the happy performance could not continue."),
        (f"How did {performer.id} feel at the end?",
         f"{performer.id} felt shocked and sad. The bad ending mattered because {performer.pronoun()} understood too late that the director had been right to warn about the mess."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"director", "foreshadow"} | set(f["prop_cfg"].tags) | set(f["risk_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        flags = [n for n, on in (
            ("trip_risk", e.trip_risk),
            ("tangle_risk", e.tangle_risk),
            ("dangerous", e.dangerous),
            ("fragile", e.fragile),
        ) if on]
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="moon_march",
        prop="ribbon",
        risk="steps",
        finale="stopped_song",
        performer_name="Molly",
        performer_type="girl",
        director_name="Wren",
        director_type="goose",
    ),
    StoryParams(
        theme="lamb_lilt",
        prop="confetti",
        risk="rug",
        finale="quiet_room",
        performer_name="Pip",
        performer_type="boy",
        director_name="Goody",
        director_type="goose",
    ),
    StoryParams(
        theme="thimble_reel",
        prop="garland",
        risk="stool",
        finale="torn_costume",
        performer_name="Nell",
        performer_type="girl",
        director_name="Mavis",
        director_type="goose",
    ),
    StoryParams(
        theme="moon_march",
        prop="garland",
        risk="steps",
        finale="stopped_song",
        performer_name="Robin",
        performer_type="boy",
        director_name="Dot",
        director_type="goose",
    ),
]


def explain_rejection(prop: Prop, risk: RiskSpot) -> str:
    return (
        f"(No story: {prop.label} does not create a plausible stage hazard at {risk.the}. "
        f"The world only tells stories where the clutter could honestly catch or trip a performer.)"
    )


ASP_RULES = r"""
hazard(P, R) :- trip_prop(P), trip_spot(R).
hazard(P, R) :- tangle_prop(P), tangle_spot(R).
valid(T, P, R) :- theme(T), prop(P), risk(R), hazard(P, R).

ruined :- chosen_prop(P), chosen_risk(R), chosen_finale(F), hazard(P, R), power(F, FP), hazard_power(P, R, HP), FP < HP.
saved  :- chosen_prop(P), chosen_risk(R), chosen_finale(F), hazard(P, R), power(F, FP), hazard_power(P, R, HP), FP >= HP.

outcome(ruined) :- ruined.
outcome(saved)  :- saved.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for pid, prop in PROPS.items():
        lines.append(asp.fact("prop", pid))
        if prop.trip_risk:
            lines.append(asp.fact("trip_prop", pid))
        if prop.tangle_risk:
            lines.append(asp.fact("tangle_prop", pid))
    for rid, risk in RISKS.items():
        lines.append(asp.fact("risk", rid))
        if risk.trip_works:
            lines.append(asp.fact("trip_spot", rid))
        if risk.tangle_works:
            lines.append(asp.fact("tangle_spot", rid))
    for pid, prop in PROPS.items():
        for rid, risk in RISKS.items():
            lines.append(asp.fact("hazard_power", pid, rid, hazard_power(prop, risk)))
    for fid, finale in FINALES.items():
        lines.append(asp.fact("finale", fid))
        lines.append(asp.fact("power", fid, finale.power))
        lines.append(asp.fact("sense", fid, finale.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_prop", params.prop),
        asp.fact("chosen_risk", params.risk),
        asp.fact("chosen_finale", params.finale),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme storyworld: a little stage show, a muss, a careful director, and a bad ending."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--risk", choices=RISKS)
    ap.add_argument("--finale", choices=FINALES)
    ap.add_argument("--performer-name")
    ap.add_argument("--performer-type", choices=["girl", "boy"])
    ap.add_argument("--director-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.prop and args.risk:
        prop = PROPS[args.prop]
        risk = RISKS[args.risk]
        if not hazard_at_risk(prop, risk):
            raise StoryError(explain_rejection(prop, risk))

    combos = [
        c for c in valid_combos()
        if (args.theme is None or c[0] == args.theme)
        and (args.prop is None or c[1] == args.prop)
        and (args.risk is None or c[2] == args.risk)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme_id, prop_id, risk_id = rng.choice(sorted(combos))
    finale_id = args.finale or rng.choice(sorted(sensible_finales(), key=lambda f: f.id)).id
    performer_type = args.performer_type or rng.choice(["girl", "boy"])
    performer_name = args.performer_name or rng.choice(GIRL_NAMES if performer_type == "girl" else BOY_NAMES)
    director_name = args.director_name or rng.choice(DIRECTOR_NAMES)
    return StoryParams(
        theme=theme_id,
        prop=prop_id,
        risk=risk_id,
        finale=finale_id,
        performer_name=performer_name,
        performer_type=performer_type,
        director_name=director_name,
        director_type="goose",
    )


def _validate_params(params: StoryParams) -> None:
    if params.theme not in THEMES:
        raise StoryError(f"(Unknown theme: {params.theme})")
    if params.prop not in PROPS:
        raise StoryError(f"(Unknown prop: {params.prop})")
    if params.risk not in RISKS:
        raise StoryError(f"(Unknown risk: {params.risk})")
    if params.finale not in FINALES:
        raise StoryError(f"(Unknown finale: {params.finale})")
    if not hazard_at_risk(PROPS[params.prop], RISKS[params.risk]):
        raise StoryError(explain_rejection(PROPS[params.prop], RISKS[params.risk]))


def generate(params: StoryParams) -> StorySample:
    _validate_params(params)
    world = tell(
        theme=THEMES[params.theme],
        prop=PROPS[params.prop],
        risk=RISKS[params.risk],
        finale=FINALES[params.finale],
        performer_name=params.performer_name,
        performer_type=params.performer_type,
        director_name=params.director_name,
        director_type=params.director_type,
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


def outcome_of(params: StoryParams) -> str:
    return "ruined" if is_ruin(FINALES[params.finale], PROPS[params.prop], RISKS[params.risk]) else "saved"


def asp_verify() -> int:
    rc = 0
    cset, pset = set(asp_valid_combos()), set(valid_combos())
    if cset == pset:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    cases = list(CURATED)
    for s in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
            params.seed = s
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure for seed {s}.")
            break

    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if mismatches:
        rc = 1
        print(f"MISMATCH in outcomes: {len(mismatches)}/{len(cases)} cases differ.")
    else:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")

    try:
        smoke = generate(cases[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated empty story")
        print("OK: generate() smoke test passed.")
    except Exception as err:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, prop, risk) combos:\n")
        for theme, prop, risk in combos:
            print(f"  {theme:12} {prop:10} {risk}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.performer_name}: {p.prop} by {p.risk} ({p.theme}, {p.finale}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
