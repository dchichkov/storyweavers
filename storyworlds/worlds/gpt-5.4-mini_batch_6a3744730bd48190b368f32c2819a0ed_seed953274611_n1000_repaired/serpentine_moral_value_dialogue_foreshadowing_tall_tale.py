#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/serpentine_moral_value_dialogue_foreshadowing_tall_tale.py
===========================================================================================

A tiny tall-tale storyworld about a winding serpentine trail, a boastful plan,
a warning tucked in a foreshadowing clue, and a moral value learned at the end.

Domain sketch
-------------
A child and a small helper are hauling something valuable along a long,
serpentine route. The child wants a flashy shortcut or a boastful trick.
A wiser voice notices a warning sign, predicts trouble, and speaks up.
The ending is either:
  * averted: they choose the slower safe route, or
  * contained: they make the risky move, but a quick remedy saves the day.

The story style leans tall-tale: vivid, playful, exaggerated, but still driven
by a simulated world state rather than frozen template prose.
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

METER_THRESHOLD = 1.0
BRAVERY_INIT = 6.0
MORAL_INIT = 5.0
CAUTIOUS_TRAITS = {"careful", "wise", "patient", "steady"}


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
    serpentine: bool = False
    fragile: bool = False
    helpful: bool = False

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
class Route:
    id: str
    place: str
    image: str
    winding: str
    shortcut: str
    danger_hint: str
    long_name: str
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
class ObjectThing:
    id: str
    label: str
    phrase: str
    fragile: bool = False
    helpful: bool = False
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
class Remedy:
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["spill"] < METER_THRESHOLD:
            continue
        sig = ("spill", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("road").meters["slick"] += 1
        for c in world.characters():
            c.memes["worry"] += 1
        out.append("__spill__")
    return out


def _r_shame(world: World) -> list[str]:
    out: list[str] = []
    for c in world.characters():
        if c.memes["defiance"] < METER_THRESHOLD:
            continue
        sig = ("shame", c.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        c.memes["pride"] += 1
        out.append("")
    return out


CAUSAL_RULES = [Rule("spill", "physical", _r_spill), Rule("shame", "social", _r_shame)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def serpentine_risk(route: Route) -> bool:
    return route.serpentine


def sensible_remedies() -> list[Remedy]:
    return [r for r in REMEDIES.values() if r.sense >= 2]


def best_remedy() -> Remedy:
    return max(REMEDIES.values(), key=lambda r: r.sense)


def travel_choice_would_warn(route: Route, helper_trait: str, elder: bool) -> bool:
    caution = 5.0 if helper_trait in CAUTIOUS_TRAITS else 3.0
    authority = caution + (2.0 if elder else 0.0)
    return serpentine_risk(route) and authority + 1.0 > BRAVERY_INIT


def path_delay(route: Route, delay: int) -> int:
    return delay + (2 if route.serpentine else 0)


def is_repaired(remedy: Remedy, route: Route, delay: int) -> bool:
    return remedy.power >= path_delay(route, delay)


def predict_route(world: World, route_id: str, delay: int) -> dict:
    sim = world.copy()
    _take_risky_path(sim, sim.get("cargo"), ROUTES[route_id], delay=delay, narrate=False)
    return {
        "spilled": sim.get("cargo").meters["spill"] >= METER_THRESHOLD,
        "slick": sim.get("road").meters["slick"],
    }


def _take_risky_path(world: World, cargo: Entity, route: Route, delay: int, narrate: bool = True) -> None:
    cargo.meters["spill"] += 1
    cargo.meters["jolt"] += 1
    world.get("road").meters["speed"] += 1
    if delay > 0:
        world.get("road").meters["delay"] += delay
    propagate(world, narrate=narrate)


def _safe_route(world: World, hero: Entity, helper: Entity, route: Route) -> None:
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f'{hero.id} blinked at the winding trail and said, "Maybe the long road is '
        f"the brave road after all."'
    )
    world.say(
        f"{helper.id} nodded. They kept to the serpentine path, and the day rolled "
        f"along as smooth as a marbles-in-a-sack song."
    )


def _tempt(world: World, hero: Entity, route: Route) -> None:
    hero.memes["bravado"] += 1
    world.say(
        f'{hero.id} grinned wide enough to shake a fence post. "I can whip us '
        f"around that serpentine bend faster than a blue jay on a biscuit!""
    )
    world.say(f"But the route itself seemed to whisper a warning from the ditch.")


def _foreshadow(world: World, helper: Entity, route: Route) -> None:
    pred = predict_route(world, "cargo", 0)
    helper.memes["caution"] += 1
    world.facts["predicted_slick"] = pred["slick"]
    world.say(
        f'{helper.id} pointed at the {route.danger_hint} and said, '
        f'"That bend has a memory, and memory is a fine thing to respect."'
    )
    world.say(
        f'"If we rush, this load could spill," {helper.id} added. '
        f'"A crooked road often keeps a crooked surprise."'
    )


def _defy(world: World, hero: Entity, helper: Entity, route: Route) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f'"Bah," {hero.id} said, tipping the sack onto {hero.pronoun("possessive")} '
        f"shoulder. \"A little zig and zag never frightened a hero.\""
    )


def _warned_off(world: World, hero: Entity, helper: Entity, route: Route) -> None:
    hero.memes["moral"] += 1
    helper.memes["moral"] += 1
    world.say(
        f"At last {hero.id} looked at {helper.id}, then at the serpentine road, "
        f"and gave the wise nod that grows a person faster than bragging ever can."
    )


def _spill(world: World, cargo: Entity, route: Route) -> None:
    _take_risky_path(world, cargo, route, delay=0)
    world.say(
        f"The load tipped. Out came a glittering spill that skipped over the stones "
        f"like a hundred tiny moons."
    )


def _alarm(world: World, helper: Entity, hero: Entity, route: Route) -> None:
    world.say(f'"{hero.id}! Watch the bend!" {helper.id} shouted.')
    world.say(f'"The road is serpentine, and serpentine roads like to test a boast!"')


def _remedy(world: World, elder: Entity, remedy: Remedy, cargo: Entity, route: Route, delay: int) -> None:
    if is_repaired(remedy, route, delay):
        cargo.meters["spill"] = 0.0
        world.get("road").meters["slick"] = 0.0
        body = remedy.text.replace("{route}", route.place)
        world.say(
            f"{elder.label_word.capitalize()} came striding in and {body}."
        )
    else:
        body = remedy.fail.replace("{route}", route.place)
        world.say(
            f"{elder.label_word.capitalize()} came striding in and {body}."
        )
        world.get("road").meters["slick"] += 1


def _moral(world: World, hero: Entity, helper: Entity, route: Route, remedy: Remedy, averted: bool, contained: bool) -> None:
    hero.memes["moral"] += 2
    helper.memes["moral"] += 2
    if averted:
        world.say(
            "And so they learned that a careful heart can outrun a foolish dash, "
            "especially when the road itself has already raised a warning finger."
        )
    elif contained:
        world.say(
            "They learned that a person may brag with their mouth, but the truth "
            "walks behind with a broom, sweeping up the mess."
        )
    else:
        world.say(
            "They learned that even a tall tale has a short moment to tell the truth: "
            "the wise voice should be listened to before trouble grows legs."
        )


def tell(route: Route, helper_trait: str, remedy: Remedy, hero_name: str = "Lark", hero_gender: str = "girl",
         helper_name: str = "Moss", helper_gender: str = "boy", elder_type: str = "mother",
         delay: int = 0, elder: bool = True) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper", traits=[helper_trait]))
    elder_ent = world.add(Entity(id="Elder", kind="character", type=elder_type, role="elder"))
    world.add(Entity(id="road", type="road", label="the road", serpentine=True))
    cargo = world.add(Entity(id="cargo", type="cargo", label="the crate", fragile=True))

    hero.memes["bravery"] = BRAVERY_INIT
    helper.memes["caution"] = MORAL_INIT
    world.facts["route"] = route
    world.facts["remedy"] = remedy
    world.facts["delay"] = delay

    world.say(
        f"Now, that was a day with a hat full of wind and a horse-shaped cloud, "
        f"and {hero.id} and {helper.id} were hauling a crate along {route.long_name}."
    )
    world.say(
        f"{route.image} {route.winding} It looked harmless enough, but the ditch wore "
        f"a grin like it knew a secret."
    )

    world.para()
    _tempt(world, hero, route)
    _foreshadow(world, helper, route)

    averted = travel_choice_would_warn(route, helper_trait, elder)
    contained = False
    if averted:
        _warned_off(world, hero, helper, route)
        world.para()
        _safe_route(world, hero, helper, route)
    else:
        _defy(world, hero, helper, route)
        world.para()
        _spill(world, cargo, route)
        _alarm(world, helper, hero, route)
        contained = is_repaired(remedy, route, delay)
        world.para()
        elder = world.get("Elder")
        _remedy(world, elder, remedy, cargo, route, delay)
        _moral(world, hero, helper, route, remedy, averted, contained)
        if not contained:
            world.say(
                "By sundown the crate was mended only in the telling, which is how a "
                "tall tale keeps its hat on."
            )
    world.facts.update(hero=hero, helper=helper, elder=elder_ent, cargo=cargo,
                       averted=averted, contained=contained, remedy=remedy)
    return world


@dataclass
class StoryParams:
    route: str
    remedy: str
    helper_trait: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
    elder_type: str
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


ROUTES = {
    "riverbend": Route(
        id="riverbend", place="the riverbend", image="The river made a silver hook through the grass.",
        winding="The trail went serpentine as a ribbon in a windstorm.", shortcut="cut across the reeds",
        danger_hint="crooked bend by the cattails", long_name="the riverbend road", tags={"serpentine"}
    ),
    "canyon": Route(
        id="canyon", place="the canyon road", image="The cliffs leaned in like old spectators.",
        winding="The road curled serpentine between the red walls.", shortcut="climb the loose ledge",
        danger_hint="echoing turn under the ledge", long_name="the canyon road", tags={"serpentine"}
    ),
    "orchard": Route(
        id="orchard", place="the orchard lane", image="The apple trees stood in rows like polite giants.",
        winding="The lane ran serpentine between the trees.", shortcut="dash between the wagons",
        danger_hint="a bend shadowed by a wagon wheel", long_name="the orchard lane", tags={"serpentine"}
    ),
}

REMEDIES = {
    "broom_brush": Remedy(
        id="broom_brush", sense=3, power=3,
        text="brushed the spill back into the crate with a broom and a grin",
        fail="swung a broom at the spill, but the wind and the bend laughed it away",
        qa_text="brushed the spill back into the crate with a broom",
        tags={"cleaning"},
    ),
    "tarp_wrap": Remedy(
        id="tarp_wrap", sense=3, power=2,
        text="wrapped the crate in a tarp and tied it down with knots fit for a sea captain",
        fail="wrapped the crate in a tarp, but the load had already slipped too far",
        qa_text="wrapped the crate in a tarp and tied it down",
        tags={"cover"},
    ),
    "slow_down": Remedy(
        id="slow_down", sense=2, power=2,
        text="made everyone slow down until even the dust had time to mind its manners",
        fail="called for a slowdown, but the spill had already galloped ahead",
        qa_text="made everyone slow down and steady the load",
        tags={"slow"},
    ),
    "water_bucket": Remedy(
        id="water_bucket", sense=1, power=1,
        text="threw a bucket of water at the mess",
        fail="threw a bucket of water at the mess, but it only spread the trouble",
        qa_text="threw a bucket of water at the mess",
        tags={"weak"},
    ),
}

HERO_NAMES = ["Lark", "Nell", "Pip", "June", "Bodhi", "Wren", "Milo", "Ivy"]
HELPER_NAMES = ["Moss", "Sage", "Fern", "Toby", "Luna", "Otis", "Kit", "Reed"]
TRAITS = ["careful", "wise", "patient", "steady", "bold", "quiet"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for rid, route in ROUTES.items():
        if not serpentine_risk(route):
            continue
        for rem in REMEDIES.values():
            if rem.sense >= 2:
                combos.append((rid, rem.id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale serpentine moral dialogue story world.")
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--helper-trait", choices=TRAITS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--elder-type", choices=["mother", "father"])
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
    if args.remedy and REMEDIES[args.remedy].sense < 2:
        raise StoryError(f"(Refusing remedy '{args.remedy}': too weak for a sensible story.)")
    combos = [c for c in valid_combos()
              if (args.route is None or c[0] == args.route)
              and (args.remedy is None or c[1] == args.remedy)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    route, remedy = rng.choice(sorted(combos))
    helper_trait = args.helper_trait or rng.choice(TRAITS)
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    helper_name = args.helper_name or rng.choice([n for n in HELPER_NAMES if n != hero_name])
    elder_type = args.elder_type or rng.choice(["mother", "father"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    hero_gender = rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["girl", "boy"])
    return StoryParams(
        route=route, remedy=remedy, helper_trait=helper_trait,
        hero_name=hero_name, hero_gender=hero_gender,
        helper_name=helper_name, helper_gender=helper_gender,
        elder_type=elder_type, delay=delay,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    route, remedy, hero, helper = f["route"], f["remedy"], f["hero"], f["helper"]
    return [
        f'Write a tall-tale story that includes the word "serpentine" and a moral lesson about listening to wise warnings.',
        f"Tell a dialogue-heavy story where {hero.id} boasts about a {route.place}, {helper.id} notices a warning sign, and they either choose the safe path or fix the spill.",
        f"Write a funny, child-facing adventure on {route.place} with foreshadowing, a risky boast, and a final lesson about carefulness.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, route, remedy = f["hero"], f["helper"], f["route"], f["remedy"]
    qa = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {hero.id} and {helper.id}, who were carrying a crate along {route.place}. The road was serpentine, so the trip itself already felt like a dare."
        ),
        QAItem(
            question="What warning showed up before the trouble?",
            answer=f"{helper.id} pointed out the {route.danger_hint} and warned that a rush could make the load spill. That was the foreshadowing, because the road had already been acting like a trickster."
        ),
    ]
    if f["averted"]:
        qa.append(QAItem(
            question="How did they avoid the problem?",
            answer=f"They listened to the warning and stayed on the long route instead of making a bragging shortcut. The safe choice kept the crate steady, which proved that patience can be the boldest move of all."
        ))
    else:
        qa.append(QAItem(
            question="How did they fix the problem?",
            answer=f"{f['elder'].label_word.capitalize()} {remedy.qa_text} after the spill. It worked well enough to save the day, and the ending proved that quick hands and a calm head can mend a mistake."
        ))
    qa.append(QAItem(
        question="What moral did they learn?",
        answer="They learned that a brave person listens before they boast. A big voice is easy to hear, but a wise warning can keep everybody safe."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What does serpentine mean?", "Serpentine means winding and curving like a snake. A serpentine road twists instead of going straight."),
        QAItem("What is foreshadowing?", "Foreshadowing is a clue that hints something important may happen later. It helps a story feel like it has a shadow before the surprise arrives."),
        QAItem("What is a moral?", "A moral is the lesson a story leaves in your mind. It tells you what the characters learned about how to act."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


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
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for rid, r in ROUTES.items():
        lines.append(asp.fact("route", rid))
        lines.append(asp.fact("serpentine", rid))
    for mid, m in REMEDIES.items():
        lines.append(asp.fact("remedy", mid))
        lines.append(asp.fact("sense", mid, m.sense))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
sensible(R) :- remedy(R), sense(R,S), sense_min(M), S >= M.
valid(R, M) :- route(R), remedy(M), serpentine(R), sensible(M).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP valid combos differ from Python.")
        rc = 1
    else:
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: default generation smoke test passed.")
    except Exception as err:
        print(f"FAILED: generation smoke test crashed: {err}")
        return 1
    return rc


def generate(params: StoryParams) -> StorySample:
    for key, lookup in [("route", ROUTES), ("remedy", REMEDIES)]:
        if getattr(params, key) not in lookup:
            raise StoryError(f"Invalid {key}: {getattr(params, key)!r}")
    world = tell(
        ROUTES[params.route],
        params.helper_trait,
        REMEDIES[params.remedy],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        elder_type=params.elder_type,
        delay=params.delay,
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


CURATED = [
    StoryParams(route="riverbend", remedy="slow_down", helper_trait="careful", hero_name="Lark", hero_gender="girl", helper_name="Moss", helper_gender="boy", elder_type="mother", delay=0),
    StoryParams(route="canyon", remedy="broom_brush", helper_trait="wise", hero_name="Nell", hero_gender="girl", helper_name="Sage", helper_gender="boy", elder_type="father", delay=1),
    StoryParams(route="orchard", remedy="tarp_wrap", helper_trait="patient", hero_name="Pip", hero_gender="boy", helper_name="Fern", helper_gender="girl", elder_type="mother", delay=0),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible remedies: {', '.join(asp_sensible())}\n")
        for route, remedy in asp_valid_combos():
            print(f"{route:10} {remedy}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
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
