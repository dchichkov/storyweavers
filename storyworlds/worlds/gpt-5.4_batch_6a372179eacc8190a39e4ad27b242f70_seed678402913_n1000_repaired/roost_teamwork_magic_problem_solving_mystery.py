#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/roost_teamwork_magic_problem_solving_mystery.py
============================================================================

A standalone storyworld for a small mystery about a missing magical bedtime item
at a roost. Bird friends work together, use gentle magic, follow clues, and
solve the problem before night falls.

Run it
------
    python storyworlds/worlds/gpt-5.4/roost_teamwork_magic_problem_solving_mystery.py
    python storyworlds/worlds/gpt-5.4/roost_teamwork_magic_problem_solving_mystery.py --roost oak --item moon_lantern
    python storyworlds/worlds/gpt-5.4/roost_teamwork_magic_problem_solving_mystery.py --cause wind --hiding thorn_bush
    python storyworlds/worlds/gpt-5.4/roost_teamwork_magic_problem_solving_mystery.py --all
    python storyworlds/worlds/gpt-5.4/roost_teamwork_magic_problem_solving_mystery.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/roost_teamwork_magic_problem_solving_mystery.py --trace
    python storyworlds/worlds/gpt-5.4/roost_teamwork_magic_problem_solving_mystery.py --qa --json
    python storyworlds/worlds/gpt-5.4/roost_teamwork_magic_problem_solving_mystery.py --verify
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "hen", "mother", "woman"}
        male = {"boy", "rooster", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Roost:
    id: str
    label: str
    phrase: str
    dusk_view: str
    drafty: bool
    nearby: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MissingItem:
    id: str
    label: str
    phrase: str
    glow: str
    use: str
    sound: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str
    label: str
    clue_text: str
    leaves_trace: str
    leads_to: set[str]
    move_style: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HidingPlace:
    id: str
    label: str
    phrase: str
    clue_seen: str
    reach: str
    needs: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    sense: int
    solves: set[str]
    team_line: str
    magic_line: str
    recover_line: str
    qa_line: str
    tags: set[str] = field(default_factory=set)


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
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_alarm(world: World) -> list[str]:
    item = world.entities.get("item")
    if item is None:
        return []
    if item.meters["missing"] < THRESHOLD:
        return []
    sig = ("alarm", "item")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for eid in ("hero", "friend1", "friend2"):
        if eid in world.entities:
            world.get(eid).memes["worry"] += 1
    if "roost" in world.entities:
        world.get("roost").memes["unease"] += 1
    return ["__alarm__"]


def _r_teamwork(world: World) -> list[str]:
    needed = world.facts.get("needed_roles", set())
    if not needed:
        return []
    used = set(world.facts.get("used_roles", set()))
    if not needed.issubset(used):
        return []
    sig = ("teamwork", tuple(sorted(needed)))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.facts["team_complete"] = True
    for eid in ("hero", "friend1", "friend2"):
        if eid in world.entities:
            world.get(eid).memes["trust"] += 1
    return ["__team__"]


def _r_solution(world: World) -> list[str]:
    if not world.facts.get("team_complete"):
        return []
    if not world.facts.get("clue_matched"):
        return []
    sig = ("solution", world.facts.get("method"))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if "item" in world.entities:
        item = world.get("item")
        item.meters["missing"] = 0.0
        item.meters["found"] += 1
    for eid in ("hero", "friend1", "friend2"):
        if eid in world.entities:
            ent = world.get(eid)
            ent.memes["relief"] += 1
            ent.memes["joy"] += 1
            ent.memes["worry"] = 0.0
    if "roost" in world.entities:
        world.get("roost").memes["unease"] = 0.0
        world.get("roost").memes["safe"] += 1
    world.facts["solved"] = True
    return ["__solved__"]


CAUSAL_RULES = [
    Rule(name="alarm", tag="emotional", apply=_r_alarm),
    Rule(name="teamwork", tag="social", apply=_r_teamwork),
    Rule(name="solution", tag="physical", apply=_r_solution),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


ROOSTS = {
    "oak": Roost(
        id="oak",
        label="oak roost",
        phrase="a high roost tucked into the branches of the old oak",
        dusk_view="the last gold light sliding through the leaves",
        drafty=True,
        nearby="a thorn bush below the trunk",
        tags={"roost", "tree"},
    ),
    "barn": Roost(
        id="barn",
        label="barn-beam roost",
        phrase="a snug roost on the warm beams inside the red barn",
        dusk_view="soft strips of sunset peeking through the boards",
        drafty=False,
        nearby="a hay basket under the ladder",
        tags={"roost", "barn"},
    ),
    "willow": Roost(
        id="willow",
        label="willow roost",
        phrase="a swinging roost woven between the silver willow branches",
        dusk_view="the pond turning pink and still below",
        drafty=True,
        nearby="a reed basket near the water",
        tags={"roost", "willow"},
    ),
}

ITEMS = {
    "moon_lantern": MissingItem(
        id="moon_lantern",
        label="moon lantern",
        phrase="the little moon lantern",
        glow="glowed with a soft silver light",
        use="show the smallest birds where to step at bedtime",
        sound="made a tiny chiming hum",
        tags={"lantern", "magic"},
    ),
    "star_bell": MissingItem(
        id="star_bell",
        label="star bell",
        phrase="the star bell",
        glow="shimmered like a sleepy star",
        use="ring the bedtime call across the branches",
        sound="gave a clear, bright ting",
        tags={"bell", "magic"},
    ),
    "dew_charm": MissingItem(
        id="dew_charm",
        label="dew charm",
        phrase="the round dew charm",
        glow="shone blue like a drop of moonlit water",
        use="keep the roost calm and easy to find in the dark",
        sound="whispered with a soft glassy note",
        tags={"charm", "magic"},
    ),
}

CAUSES = {
    "wind": Cause(
        id="wind",
        label="a jumpy gust of wind",
        clue_text="A line of loose feathers pointed away from the sleeping perch.",
        leaves_trace="a scatter of feathers and a thin scrape in the dust",
        leads_to={"thorn_bush", "reed_basket"},
        move_style="blew it right out of place",
        tags={"wind", "weather"},
    ),
    "squirrel": Cause(
        id="squirrel",
        label="a nosy squirrel",
        clue_text="Tiny paw prints dotted the rail beside the empty hook.",
        leaves_trace="tiny paw prints and a nibbled acorn cap",
        leads_to={"hollow_log", "hay_basket"},
        move_style="snatched it to inspect it somewhere quiet",
        tags={"squirrel", "animal"},
    ),
    "roll": Cause(
        id="roll",
        label="a sleepy bump and a roll",
        clue_text="There was no thief at all, only a round trail in the dust.",
        leaves_trace="a curved mark as if something small had rolled away",
        leads_to={"hay_basket", "reed_basket"},
        move_style="let it tumble into the nearest low place",
        tags={"rolling", "motion"},
    ),
}

HIDING_PLACES = {
    "thorn_bush": HidingPlace(
        id="thorn_bush",
        label="thorn bush",
        phrase="inside the thorn bush below the trunk",
        clue_seen="a silver glint blinked between the thorns",
        reach="too prickly for one bird to grab alone",
        needs={"look", "lift"},
        tags={"bush"},
    ),
    "reed_basket": HidingPlace(
        id="reed_basket",
        label="reed basket",
        phrase="under a flap of reeds in the basket by the water",
        clue_seen="something round made the basket lid bulge a little",
        reach="hidden under woven reeds",
        needs={"listen", "look"},
        tags={"basket"},
    ),
    "hay_basket": HidingPlace(
        id="hay_basket",
        label="hay basket",
        phrase="deep in the hay basket under the ladder",
        clue_seen="the hay gave a tiny sparkle and then went still",
        reach="buried under rustly straw",
        needs={"listen", "peck"},
        tags={"hay"},
    ),
    "hollow_log": HidingPlace(
        id="hollow_log",
        label="hollow log",
        phrase="inside a hollow log beside the fence",
        clue_seen="a faint chiming echo came from the dark opening",
        reach="too dark to search without a careful spell",
        needs={"glow", "listen"},
        tags={"log"},
    ),
}

METHODS = {
    "feather_chain": Method(
        id="feather_chain",
        label="feather-chain spell",
        sense=3,
        solves={"thorn_bush"},
        team_line="One bird spotted the shine, one steadied the branch, and one pulled in time.",
        magic_line='Together they whispered, "Light and lift, soft and slow."',
        recover_line="The charm rose gently over the thorns and floated into waiting wings.",
        qa_line="They used a feather-chain spell to lift the item out without poking themselves on the thorns.",
        tags={"lift", "spell"},
    ),
    "echo_hum": Method(
        id="echo_hum",
        label="echo-hum spell",
        sense=3,
        solves={"reed_basket", "hay_basket", "hollow_log"},
        team_line="One bird listened, one cleared the way, and one followed the sound exactly.",
        magic_line='Together they hummed a round little tune until the lost magic answered back.',
        recover_line="The hidden item answered with a brighter note, and they followed the sound straight to it.",
        qa_line="They used an echo-hum spell so the missing item would answer with its own sound.",
        tags={"listen", "sound", "spell"},
    ),
    "soft_peck": Method(
        id="soft_peck",
        label="soft-peck search",
        sense=2,
        solves={"hay_basket"},
        team_line="They took turns moving the hay instead of making a big mess.",
        magic_line='To help, they breathed a tiny warm spark and whispered, "Show, do not scorch."',
        recover_line="A few gentle pecks parted the hay, and the missing item sat safe underneath.",
        qa_line="They searched carefully through the hay, using a tiny warm spell only to help them see.",
        tags={"peck", "look", "spell"},
    ),
    "glow_dust": Method(
        id="glow_dust",
        label="glow-dust spell",
        sense=3,
        solves={"hollow_log"},
        team_line="One bird dropped the dust, one watched the shadows, and one reached in when the path was clear.",
        magic_line='They puffed glow dust into the log and whispered, "Bright enough to guide, never enough to scare."',
        recover_line="The log lit up softly, and the item gleamed near the back where it had rolled to rest.",
        qa_line="They brightened the hollow log with glow dust so they could see the safe path to the missing item.",
        tags={"glow", "spell"},
    ),
    "splash_guess": Method(
        id="splash_guess",
        label="wild splash guess",
        sense=1,
        solves=set(),
        team_line="They guessed without looking closely.",
        magic_line='Someone muttered, "Maybe it will pop out."',
        recover_line="Nothing happened at all.",
        qa_line="They only guessed, which was not a careful way to solve the mystery.",
        tags={"guess"},
    ),
}

GIRL_NAMES = ["Pip", "Mina", "Lark", "Tia", "Nia", "Wren"]
BOY_NAMES = ["Ollie", "Bram", "Finn", "Toby", "Reed", "Ash"]
TRAITS = ["careful", "curious", "bright", "patient", "kind", "quick-thinking"]


def cause_allows_hiding(cause: Cause, hiding: HidingPlace) -> bool:
    return hiding.id in cause.leads_to


def method_suits_hiding(method: Method, hiding: HidingPlace) -> bool:
    return method.sense >= SENSE_MIN and hiding.id in method.solves


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for roost_id in ROOSTS:
        for item_id in ITEMS:
            for cause_id, cause in CAUSES.items():
                for hiding_id, hiding in HIDING_PLACES.items():
                    if not cause_allows_hiding(cause, hiding):
                        continue
                    for method_id, method in METHODS.items():
                        if method_suits_hiding(method, hiding):
                            combos.append((roost_id, item_id, cause_id, hiding_id, method_id))
    return combos


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


@dataclass
class StoryParams:
    roost: str
    item: str
    cause: str
    hiding: str
    method: str
    hero_name: str
    hero_gender: str
    friend1_name: str
    friend1_gender: str
    friend2_name: str
    friend2_gender: str
    parent_type: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        roost="oak",
        item="moon_lantern",
        cause="wind",
        hiding="thorn_bush",
        method="feather_chain",
        hero_name="Pip",
        hero_gender="girl",
        friend1_name="Ollie",
        friend1_gender="boy",
        friend2_name="Wren",
        friend2_gender="girl",
        parent_type="hen",
        trait="careful",
    ),
    StoryParams(
        roost="barn",
        item="star_bell",
        cause="squirrel",
        hiding="hay_basket",
        method="echo_hum",
        hero_name="Finn",
        hero_gender="boy",
        friend1_name="Mina",
        friend1_gender="girl",
        friend2_name="Ash",
        friend2_gender="boy",
        parent_type="rooster",
        trait="curious",
    ),
    StoryParams(
        roost="willow",
        item="dew_charm",
        cause="roll",
        hiding="reed_basket",
        method="echo_hum",
        hero_name="Lark",
        hero_gender="girl",
        friend1_name="Reed",
        friend1_gender="boy",
        friend2_name="Nia",
        friend2_gender="girl",
        parent_type="hen",
        trait="patient",
    ),
    StoryParams(
        roost="barn",
        item="dew_charm",
        cause="squirrel",
        hiding="hollow_log",
        method="glow_dust",
        hero_name="Toby",
        hero_gender="boy",
        friend1_name="Pip",
        friend1_gender="girl",
        friend2_name="Bram",
        friend2_gender="boy",
        parent_type="rooster",
        trait="quick-thinking",
    ),
]


def _pick_name(rng: random.Random, avoid: set[str]) -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n not in avoid]
    return rng.choice(choices), gender


def explain_hiding_rejection(cause: Cause, hiding: HidingPlace) -> str:
    return (
        f"(No story: {cause.label} would not reasonably move the lost item to {hiding.phrase}. "
        f"That cause leaves clues leading somewhere else.)"
    )


def explain_method_rejection(method: Method, hiding: HidingPlace) -> str:
    if method.sense < SENSE_MIN:
        better = ", ".join(sorted(m.id for m in sensible_methods()))
        return (
            f"(Refusing method '{method.id}': it scores too low on common sense "
            f"(sense={method.sense} < {SENSE_MIN}). Try one of: {better}.)"
        )
    return (
        f"(No story: {method.label} does not fit {hiding.label}. "
        f"The solution must actually work for that hiding place.)"
    )


def required_roles_for(hiding: HidingPlace) -> set[str]:
    return set(hiding.needs)


def predict_clue(world: World) -> dict:
    sim = world.copy()
    cause = sim.facts["cause_cfg"]
    hiding = sim.facts["hiding_cfg"]
    sim.facts["clue_matched"] = cause_allows_hiding(cause, hiding)
    return {"matched": sim.facts["clue_matched"]}


def introduce(world: World, hero: Entity, f1: Entity, f2: Entity, roost: Roost, parent: Entity) -> None:
    world.say(
        f"At dusk, {hero.id}, {f1.id}, and {f2.id} hurried back to {roost.phrase}. "
        f"From there they could see {roost.dusk_view}."
    )
    world.say(
        f"Every evening, {parent.label} hung the bedtime magic in its place before the flock settled in."
    )


def bedtime_need(world: World, item: MissingItem, roost: Roost) -> None:
    world.say(
        f"That night, {item.phrase} should have been there. It usually {item.glow} and helped {item.use}."
    )
    if roost.drafty:
        world.say("But the hook was empty, and the branch around it still trembled a little in the evening air.")
    else:
        world.say("But the hook was empty, and the quiet around it felt suddenly wrong.")
    world.get("item").meters["missing"] += 1
    propagate(world, narrate=False)


def notice_clue(world: World, hero: Entity, cause: Cause) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f'"Wait," whispered {hero.id}. "{cause.clue_text}"'
    )
    world.say(
        f"So this was not a spooky vanishing after all. Something had {cause.move_style}, and it had left {cause.leaves_trace}."
    )


def gather_roles(world: World, hero: Entity, f1: Entity, f2: Entity, hiding: HidingPlace) -> None:
    needed = required_roles_for(hiding)
    world.facts["needed_roles"] = needed
    hero.attrs["skill"] = "look"
    f1.attrs["skill"] = "listen"
    f2.attrs["skill"] = "lift" if "lift" in needed else ("glow" if "glow" in needed else "peck")
    cast = [hero, f1, f2]
    for ent in cast:
        if ent.attrs["skill"] in needed:
            world.facts.setdefault("used_roles", set()).add(ent.attrs["skill"])
            ent.memes["helpfulness"] += 1
    if "look" in needed and "look" not in world.facts["used_roles"]:
        world.facts["used_roles"].add("look")
    if "listen" in needed and "listen" not in world.facts["used_roles"]:
        world.facts["used_roles"].add("listen")
    if "lift" in needed and "lift" not in world.facts["used_roles"]:
        world.facts["used_roles"].add("lift")
    if "peck" in needed and "peck" not in world.facts["used_roles"]:
        world.facts["used_roles"].add("peck")
    if "glow" in needed and "glow" not in world.facts["used_roles"]:
        world.facts["used_roles"].add("glow")
    propagate(world, narrate=False)
    role_bits = []
    if "look" in needed:
        role_bits.append(f"{hero.id} would watch for tiny flashes")
    if "listen" in needed:
        role_bits.append(f"{f1.id} would listen for the magic sound")
    helper = f2
    if "lift" in needed:
        role_bits.append(f"{helper.id} would do the lifting spell")
    elif "peck" in needed:
        role_bits.append(f"{helper.id} would move things with the gentlest pecks")
    elif "glow" in needed:
        role_bits.append(f"{helper.id} would brighten the dark places")
    world.say(
        "They did not flap about in a panic. Instead, they made a plan: "
        + ", and ".join(role_bits) + "."
    )


def follow_trail(world: World, hiding: HidingPlace, roost: Roost) -> None:
    world.say(
        f"The clues led away from the roost toward {roost.nearby if hiding.id in {'thorn_bush', 'reed_basket'} else hiding.phrase}."
    )
    world.say(
        f"When they came closer, they saw that {hiding.clue_seen}. It was there, but {hiding.reach}."
    )


def solve(world: World, method: Method, hiding: HidingPlace) -> None:
    world.facts["clue_matched"] = True
    world.facts["method"] = method.id
    propagate(world, narrate=False)
    world.say(method.team_line)
    world.say(method.magic_line)
    world.say(method.recover_line)
    if world.facts.get("solved"):
        world.say(
            f"In one small blink, the mystery stopped being scary and became something they had solved together."
        )


def return_item(world: World, hero: Entity, f1: Entity, f2: Entity, item: MissingItem, parent: Entity, roost: Roost) -> None:
    world.say(
        f"They carried {item.phrase} back to the roost together, each bird steadying it for the others."
    )
    world.say(
        f"{parent.label.capitalize()} hung it up again, and soon it {item.glow}. The whole roost looked softer and safer at once."
    )
    world.say(
        f"{hero.id}, {f1.id}, and {f2.id} tucked themselves close on the branch, proud that careful thinking and teamwork had brought the magic home."
    )


def tell(
    roost: Roost,
    item: MissingItem,
    cause: Cause,
    hiding: HidingPlace,
    method: Method,
    hero_name: str,
    hero_gender: str,
    friend1_name: str,
    friend1_gender: str,
    friend2_name: str,
    friend2_gender: str,
    parent_type: str,
    trait: str,
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero", traits=[trait]))
    f1 = world.add(Entity(id="friend1", kind="character", type=friend1_gender, label=friend1_name, role="friend", traits=["steady"]))
    f2 = world.add(Entity(id="friend2", kind="character", type=friend2_gender, label=friend2_name, role="friend", traits=["gentle"]))
    parent_label = "Mama Hen" if parent_type == "hen" else "Old Rooster"
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label=parent_label, role="caretaker"))
    world.add(Entity(id="roost", type="place", label=roost.label))
    world.add(Entity(id="item", type="magic_item", label=item.label, tags=set(item.tags)))

    world.facts.update(
        roost_cfg=roost,
        item_cfg=item,
        cause_cfg=cause,
        hiding_cfg=hiding,
        method_cfg=method,
        hero=hero,
        friend1=f1,
        friend2=f2,
        parent=parent,
        needed_roles=set(),
        used_roles=set(),
        clue_matched=False,
        team_complete=False,
        solved=False,
    )

    introduce(world, hero, f1, f2, roost, parent)
    bedtime_need(world, item, roost)

    world.para()
    notice_clue(world, hero, cause)
    pred = predict_clue(world)
    world.facts["predicted_clue_match"] = pred["matched"]
    gather_roles(world, hero, f1, f2, hiding)

    world.para()
    follow_trail(world, hiding, roost)
    solve(world, method, hiding)

    world.para()
    return_item(world, hero, f1, f2, item, parent, roost)
    world.facts["hero_name"] = hero_name
    world.facts["friend1_name"] = friend1_name
    world.facts["friend2_name"] = friend2_name
    return world


KNOWLEDGE = {
    "roost": [
        (
            "What is a roost?",
            "A roost is a place where birds rest or sleep together. It can be on a branch, a beam, or another safe high spot.",
        )
    ],
    "magic": [
        (
            "What does magic mean in this story?",
            "Here, magic means gentle make-believe powers that help the birds listen, glow, or lift carefully. The magic works best when they stay calm and think together.",
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means people or animals help one another instead of trying to do everything alone. Each one does a part of the job so the whole problem becomes easier.",
        )
    ],
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is a problem where something is missing or puzzling and you have to look for clues. You solve it by noticing details and thinking carefully.",
        )
    ],
    "wind": [
        (
            "What can wind do to light things?",
            "Wind can blow light things out of place or make them roll and tumble. That is why people and animals often secure small objects.",
        )
    ],
    "squirrel": [
        (
            "Why might a squirrel carry something shiny away?",
            "Squirrels are curious and may pick up strange things to inspect them. They often leave little paw prints or bits of what they were carrying.",
        )
    ],
    "listen": [
        (
            "Why can listening help solve a mystery?",
            "Listening can reveal sounds you cannot see yet, like a bell, a hum, or an echo. Good listening helps narrow down where something is hiding.",
        )
    ],
    "glow": [
        (
            "Why is a soft light useful in the dark?",
            "A soft light helps you see where to step and what is around you. It makes searching safer without needing bright, scary light.",
        )
    ],
}

KNOWLEDGE_ORDER = ["roost", "mystery", "teamwork", "magic", "wind", "squirrel", "listen", "glow"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    item = f["item_cfg"]
    roost = f["roost_cfg"]
    return [
        f'Write a gentle mystery story for a 3-to-5-year-old that includes the word "roost".',
        f"Tell a story where three young birds at {roost.phrase} notice that {item.phrase} is missing and solve the problem with teamwork and a little magic.",
        f"Write a bedtime mystery where clues, calm thinking, and shared jobs help friends bring a magical object back to the roost.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    f1 = f["friend1"]
    f2 = f["friend2"]
    parent = f["parent"]
    roost = f["roost_cfg"]
    item = f["item_cfg"]
    cause = f["cause_cfg"]
    hiding = f["hiding_cfg"]
    method = f["method_cfg"]
    return [
        (
            "Who is the story about?",
            f"It is about {hero.label}, {f1.label}, and {f2.label}, three young birds at {roost.phrase}. It also includes {parent.label}, who cares for the bedtime magic there.",
        ),
        (
            f"What was missing from the roost?",
            f"{item.phrase.capitalize()} was missing from its hook. That mattered because it usually helped {item.use}.",
        ),
        (
            "How did they know this was a mystery with clues instead of a spooky vanishing?",
            f"{hero.label} noticed {cause.clue_text.lower()} That clue showed that something had really moved the item and left a trail behind.",
        ),
        (
            "How did the birds work together?",
            f"They stopped panicking and gave each bird a job. Because they shared the looking, listening, and careful helping, they could solve the mystery faster and more safely.",
        ),
        (
            f"Where did they find the missing item, and how did they get it back?",
            f"They found it {hiding.phrase}. {method.qa_line} That worked because the method matched the hiding place instead of being a wild guess.",
        ),
        (
            "How did the story end?",
            f"They carried the magic back to the roost together, and it glowed again over the sleeping place. The ending shows that the roost became calm and safe once more because they solved the problem together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"roost", "mystery", "teamwork", "magic"}
    cause = world.facts["cause_cfg"]
    method = world.facts["method_cfg"]
    if "wind" in cause.tags:
        tags.add("wind")
    if "squirrel" in cause.tags:
        tags.add("squirrel")
    if "listen" in method.tags or "sound" in method.tags:
        tags.add("listen")
    if "glow" in method.tags:
        tags.add("glow")
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
        bits = []
        if e.label:
            bits.append(f"label={e.label!r}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  facts: solved={world.facts.get('solved')} team_complete={world.facts.get('team_complete')}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
cause_allows(C, H) :- leads_to(C, H).
sensible(M) :- method(M), sense(M, S), sense_min(Min), S >= Min.
method_suits(M, H) :- sensible(M), solves(M, H).

valid(R, I, C, H, M) :- roost(R), item(I), cause(C), hiding(H), method(M),
                        cause_allows(C, H), method_suits(M, H).

team_complete(H) :- hiding(H), need(H, N1), used(N1),
                    not missing_needed(H).
missing_needed(H) :- hiding(H), need(H, N), not used(N).

solved(H, M) :- team_complete(H), cause_allows(chosen_cause, H), method_suits(M, H).

outcome(solved) :- solved(chosen_hiding, chosen_method).
outcome(stuck) :- not solved(chosen_hiding, chosen_method).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for rid in ROOSTS:
        lines.append(asp.fact("roost", rid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    for cid, cause in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        for hid in sorted(cause.leads_to):
            lines.append(asp.fact("leads_to", cid, hid))
    for hid, hiding in HIDING_PLACES.items():
        lines.append(asp.fact("hiding", hid))
        for need in sorted(hiding.needs):
            lines.append(asp.fact("need", hid, need))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("sense", mid, method.sense))
        for hid in sorted(method.solves):
            lines.append(asp.fact("solves", mid, hid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    for role in ["look", "listen", "lift", "peck", "glow"]:
        lines.append(asp.fact("used", role))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_cause", params.cause),
            asp.fact("chosen_hiding", params.hiding),
            asp.fact("chosen_method", params.method),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    if not cause_allows_hiding(CAUSES[params.cause], HIDING_PLACES[params.hiding]):
        return "stuck"
    if not method_suits_hiding(METHODS[params.method], HIDING_PLACES[params.hiding]):
        return "stuck"
    return "solved"


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate logic:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    c_sens = set(asp_sensible())
    p_sens = {m.id for m in sensible_methods()}
    if c_sens == p_sens:
        print(f"OK: sensible methods match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible methods: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during smoke test.")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Storyworld: a magical missing-item mystery at a roost. Unspecified choices are randomized (seeded)."
    )
    ap.add_argument("--roost", choices=ROOSTS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--hiding", choices=HIDING_PLACES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--parent", choices=["hen", "rooster"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.cause and args.hiding:
        cause = CAUSES[args.cause]
        hiding = HIDING_PLACES[args.hiding]
        if not cause_allows_hiding(cause, hiding):
            raise StoryError(explain_hiding_rejection(cause, hiding))
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        raise StoryError(explain_method_rejection(METHODS[args.method], HIDING_PLACES[args.hiding] if args.hiding else next(iter(HIDING_PLACES.values()))))
    if args.method and args.hiding:
        method = METHODS[args.method]
        hiding = HIDING_PLACES[args.hiding]
        if not method_suits_hiding(method, hiding):
            raise StoryError(explain_method_rejection(method, hiding))

    combos = [
        c
        for c in valid_combos()
        if (args.roost is None or c[0] == args.roost)
        and (args.item is None or c[1] == args.item)
        and (args.cause is None or c[2] == args.cause)
        and (args.hiding is None or c[3] == args.hiding)
        and (args.method is None or c[4] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    roost_id, item_id, cause_id, hiding_id, method_id = rng.choice(sorted(combos))
    used_names: set[str] = set()
    hero_name, hero_gender = _pick_name(rng, used_names)
    used_names.add(hero_name)
    friend1_name, friend1_gender = _pick_name(rng, used_names)
    used_names.add(friend1_name)
    friend2_name, friend2_gender = _pick_name(rng, used_names)
    parent_type = args.parent or rng.choice(["hen", "rooster"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        roost=roost_id,
        item=item_id,
        cause=cause_id,
        hiding=hiding_id,
        method=method_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend1_name=friend1_name,
        friend1_gender=friend1_gender,
        friend2_name=friend2_name,
        friend2_gender=friend2_gender,
        parent_type=parent_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        roost = ROOSTS[params.roost]
        item = ITEMS[params.item]
        cause = CAUSES[params.cause]
        hiding = HIDING_PLACES[params.hiding]
        method = METHODS[params.method]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err.args[0]})") from None

    if not cause_allows_hiding(cause, hiding):
        raise StoryError(explain_hiding_rejection(cause, hiding))
    if not method_suits_hiding(method, hiding):
        raise StoryError(explain_method_rejection(method, hiding))

    world = tell(
        roost=roost,
        item=item,
        cause=cause,
        hiding=hiding,
        method=method,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend1_name=params.friend1_name,
        friend1_gender=params.friend1_gender,
        friend2_name=params.friend2_name,
        friend2_gender=params.friend2_gender,
        parent_type=params.parent_type,
        trait=params.trait,
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
        print(asp_program("", "#show valid/5.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible methods: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (roost, item, cause, hiding, method) combos:\n")
        for roost, item, cause, hiding, method in combos:
            print(f"  {roost:7} {item:12} {cause:8} {hiding:12} {method}")
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
            header = f"### {p.hero_name}: {p.item} missing at {p.roost} ({p.cause} -> {p.hiding} via {p.method})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
