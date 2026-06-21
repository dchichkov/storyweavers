#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/slink_jabber_desperation_cautionary_moral_value_tall.py
======================================================================================

A standalone storyworld for a tall-tale, cautionary moral-value story.

Premise:
- A boastful traveler is tempted to take a risky shortcut.
- The world model tracks a slinking night path, a jabbering crowd, and growing
  desperation.
- A cautious helper predicts trouble, warns in time, and steers the traveler to
  a safer route.
- The ending proves the change in state: danger is avoided, fear drops, and a
  moral is learned.

This script follows the shared Storyweavers contract:
- self-contained stdlib storyworld script
- eager import of results.py for QAItem, StoryError, StorySample
- lazy import of asp.py only inside ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- support for default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
BRAVERY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "cautious", "thoughtful", "sensible"}


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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
    high_path: str
    danger_spot: str
    opening_image: str
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
class RiskyAct:
    id: str
    verb: str
    gerund: str
    keyword: str
    mess: str
    zone: set[str]
    caution_word: str
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
class Goal:
    id: str
    label: str
    phrase: str
    region: str
    vulnerable: bool = True
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
class Fix:
    id: str
    label: str
    sense: int
    power: int
    text: str
    fail: str
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
    act: str
    goal: str
    fix: str
    hero: str
    hero_gender: str
    guide: str
    guide_gender: str
    parent: str
    trait: str
    delay: int = 0
    hero_age: int = 7
    guide_age: int = 9
    relation: str = "friends"
    trust: int = 5
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
        clone.facts = copy.deepcopy(self.facts)
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
    for ent in world.characters():
        if ent.meters["risk"] < THRESHOLD:
            continue
        sig = ("danger", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["fear"] += 1
        if "road" in world.entities:
            world.get("road").meters["danger"] += 1
        out.append("__silent__")
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


def caution_level(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, hero_age: int, guide_age: int, trait: str) -> bool:
    if relation != "siblings":
        return False
    older = guide_age > hero_age
    authority = caution_level(trait) + (4.0 if older else 0.0)
    return older and authority > BRAVERY_INIT


def risk_level(goal: Goal, delay: int) -> int:
    return 2 + delay if goal.vulnerable else delay


def contained(fix: Fix, goal: Goal, delay: int) -> bool:
    return fix.power >= risk_level(goal, delay)


def describe_shift(world: World, hero: Entity, guide: Entity, setting: Setting) -> None:
    hero.memes["wonder"] += 1
    world.say(
        f"Across the wide country road, {hero.id} and {guide.id} set off "
        f"through {setting.place}, where the evening wind could make even a brave "
        f"heart {setting.opening_image}."
    )


def see_risk(world: World, hero: Entity, goal: Goal, act: RiskyAct) -> None:
    hero.memes["desire"] += 1
    world.say(
        f"{hero.id} wanted to {act.verb} near {goal.phrase}, because the dark "
        f"way looked quicker than the long road around."
    )
    world.say(
        f"But the shortcut had a {act.caution_word} feel to it, like a trail "
        f"that could slip into trouble before the moon finished climbing."
    )


def jabber(world: World, guide: Entity, hero: Entity, act: RiskyAct, parent: Entity) -> None:
    guide.memes["caution"] += 1
    world.say(
        f"{guide.id} began to jabber plain and fast: \"{parent.label_word.capitalize()} "
        f"said not to wander off the safe road. A slinking path can hide a ditch, "
        f"and a ditch has no mercy.\""
    )


def slip_away(world: World, hero: Entity, act: RiskyAct) -> None:
    hero.memes["defiance"] += 1
    hero.meters["risk"] += 1
    world.say(
        f'"Bah!" said {hero.id}, and {hero.pronoun()} tried to {act.verb} anyway, '
        f"{act.keyword} under {hero.pronoun('possessive')} boots like a little dare."
    )


def desperation(world: World, hero: Entity, guide: Entity) -> None:
    hero.memes["desperation"] += 1
    world.say(
        f"The farther they went, the more the night seemed to slink around them, "
        f"and the louder the old worry jabbered in {hero.id}'s chest."
    )
    world.say(
        f"At last {hero.id}'s bravado ran thin, and desperation made {hero.id} "
        f"look back at {guide.id} with bigger eyes than before."
    )


def warn(world: World, guide: Entity, hero: Entity, act: RiskyAct, goal: Goal, parent: Entity) -> None:
    world.say(
        f"{guide.id} pointed at the ground. \"See that? {act.keyword} can lead you "
        f"straight into a spill, and then {parent.label_word} would have to fetch "
        f"you home with a sore heart.\""
    )


def save(world: World, parent: Entity, fix: Fix, goal: Goal, act: RiskyAct) -> None:
    body = fix.text.replace("{goal}", goal.label)
    world.say(
        f"{parent.label_word.capitalize()} came calling from the porch, calm as a "
        f"bell, and {body}."
    )
    world.say(
        f"The danger quieted down at once, and the slinking shortcut lost its "
        f"teeth."
    )


def fix_fail(world: World, parent: Entity, fix: Fix, goal: Goal) -> None:
    body = fix.fail.replace("{goal}", goal.label)
    world.say(f"{parent.label_word.capitalize()} tried, but {body}.")
    world.say(
        f"The trouble kept growing until the road looked like a giant worry with "
        f"boots on."
    )


def ending_good(world: World, hero: Entity, guide: Entity, parent: Entity, setting: Setting) -> None:
    hero.memes["relief"] += 1
    guide.memes["relief"] += 1
    hero.memes["lesson"] += 1
    world.say(
        f"By sunset they were back on the broad road, with {parent.label_word} "
        f"walking beside them and the whole valley feeling safe again."
    )
    world.say(
        f"{hero.id} learned that a bold heart is best when it listens, and "
        f"{guide.id} learned that a warning can be as mighty as a horn blast."
    )
    world.say(
        f"So the tall country held its peace, and the night could jabber all it "
        f"wanted while the little company stayed wise."
    )


def ending_bad(world: World, hero: Entity, guide: Entity, parent: Entity) -> None:
    hero.memes["fear"] += 1
    guide.memes["fear"] += 1
    world.say(
        f"They made it home shaken, but with a lesson the size of a barn: the "
        f"quick way is not always the right way, and pride can be a poor lantern."
    )


SETTINGS = {
    "valley": Setting(
        id="valley",
        place="the wide valley road",
        high_path="a slinking shortcut along the ridge",
        danger_spot="the ditch",
        opening_image="jabber like a loose barn door",
    ),
    "marsh": Setting(
        id="marsh",
        place="the marsh edge",
        high_path="a slinking boardwalk over black water",
        danger_spot="the mud",
        opening_image="sway like a whispering fence",
    ),
    "canyon": Setting(
        id="canyon",
        place="the canyon trail",
        high_path="a slinking ledge path above the rocks",
        danger_spot="the drop",
        opening_image="slink and sigh under the stars",
    ),
}

ACTS = {
    "slink": RiskyAct(
        id="slink",
        verb="slink past",
        gerund="slinking past",
        keyword="slink",
        mess="risk",
        zone={"road"},
        caution_word="slinking",
    ),
    "jabber": RiskyAct(
        id="jabber",
        verb="jabber about",
        gerund="jabbering about",
        keyword="jabber",
        mess="risk",
        zone={"road"},
        caution_word="jabbering",
    ),
    "desperation": RiskyAct(
        id="desperation",
        verb="race toward",
        gerund="racing toward",
        keyword="desperation",
        mess="risk",
        zone={"road"},
        caution_word="desperate",
    ),
}

GOALS = {
    "bridge": Goal(id="bridge", label="the old bridge", phrase="the old bridge", region="road"),
    "market": Goal(id="market", label="the bright market", phrase="the bright market", region="road"),
    "barn": Goal(id="barn", label="the lantern barn", phrase="the lantern barn", region="road"),
}

FIXES = {
    "lantern": Fix(
        id="lantern",
        label="a lantern",
        sense=3,
        power=2,
        text="lit a lantern and showed them the safe road to {goal}",
        fail="the lantern flickered weakly and could not guide them from {goal}",
        qa_text="lit a lantern and guided them back to the safe road",
    ),
    "horn": Fix(
        id="horn",
        label="a call horn",
        sense=3,
        power=3,
        text="blew a call horn and drew a straight line home from {goal}",
        fail="the horn echoed, but the trouble was already too large at {goal}",
        qa_text="blew a call horn and drew them home safely",
    ),
    "rope": Fix(
        id="rope",
        label="a guide rope",
        sense=4,
        power=4,
        text="threw down a guide rope and hauled them clear of {goal}",
        fail="the rope slipped, and {goal} stayed out of reach",
        qa_text="used a guide rope and hauled them clear",
    ),
}

HEROES = ["Ruby", "Milo", "June", "Hank", "Nell", "Otis"]
GUIDES = ["Sage", "Annie", "Beck", "Ivy", "Bram", "Pearl"]
TRAITS = ["careful", "cautious", "thoughtful", "sensible", "brave"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for aid in ACTS:
            for gid in GOALS:
                combos.append((sid, aid, gid))
    return combos


def explain_rejection(_: Setting, __: RiskyAct, ___: Goal) -> str:
    return "(No story: this seed world keeps all listed combinations, because the cautionary turn comes from state, not a narrow compatibility filter.)"


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.hero_age, params.guide_age, params.trait):
        return "averted"
    return "contained" if contained(FIXES[params.fix], GOALS[params.goal], params.delay) else "failed"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale cautionary storyworld with slink, jabber, and desperation."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--act", choices=ACTS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--guide")
    ap.add_argument("--guide-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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


def _pick_name(rng: random.Random, pool: list[str], avoid: str = "") -> str:
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.act is None or c[1] == args.act)
              and (args.goal is None or c[2] == args.goal)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, act, goal = rng.choice(sorted(combos))
    fix = args.fix or rng.choice(sorted(FIXES))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    guide_gender = args.guide_gender or rng.choice(["girl", "boy"])
    hero = args.hero or _pick_name(rng, HEROES)
    guide = args.guide or _pick_name(rng, GUIDES, avoid=hero)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        setting=setting,
        act=act,
        goal=goal,
        fix=fix,
        hero=hero,
        hero_gender=hero_gender,
        guide=guide,
        guide_gender=guide_gender,
        parent=parent,
        trait=trait,
        delay=delay,
        hero_age=rng.randint(5, 8),
        guide_age=rng.randint(6, 10),
        relation=rng.choice(["friends", "siblings"]),
        trust=rng.randint(0, 10),
    )


def story_setup(world: World, hero: Entity, guide: Entity, parent: Entity, setting: Setting, act: RiskyAct) -> None:
    hero.memes["wonder"] += 1
    world.say(
        f"Once upon a moon-scraped evening, {hero.id} and {guide.id} went "
        f"{setting.place} where the road was so long it looked like it could wrap "
        f"around three counties and a cloud."
    )
    world.say(
        f"{guide.id} loved to {act.gerund}, and {hero.id} loved anything that "
        f"seemed a little larger than life."
    )


def warning_beat(world: World, hero: Entity, guide: Entity, parent: Entity, act: RiskyAct, goal: Goal, setting: Setting) -> None:
    world.say(
        f"But {setting.high_path} was famous for trouble, and everybody in the "
        f"country knew it. Even the crows would hush there."
    )
    world.say(
        f"{hero.id} wanted to take it anyway, because the shortcut looked quick "
        f"and grand."
    )
    world.say(
        f"{guide.id} started to jabber a warning: \"That path is no friend of a "
        f"traveler. A slinking road can send a fellow to {goal.label} the wrong "
        f"way, and then {parent.label_word} would have to come fetch you.\""
    )


def generate_world(params: StoryParams) -> World:
    if params.fix not in FIXES or params.goal not in GOALS or params.act not in ACTS or params.setting not in SETTINGS:
        raise StoryError("Invalid parameters.")
    world = World()
    setting = SETTINGS[params.setting]
    act = ACTS[params.act]
    goal = GOALS[params.goal]
    fix = FIXES[params.fix]
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_gender, role="hero"))
    guide = world.add(Entity(id=params.guide, kind="character", type=params.guide_gender, role="guide"))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label="the parent", role="parent"))
    world.add(Entity(id="road", type="road", label="the road"))
    story_setup(world, hero, guide, parent, setting, act)
    world.para()
    warning_beat(world, hero, guide, parent, act, goal, setting)
    if would_avert(params.relation, params.hero_age, params.guide_age, params.trait):
        hero.memes["relief"] += 1
        guide.memes["relief"] += 1
        world.say(
            f"{hero.id} listened, and the two of them turned back before the dark "
            f"could make a meal of their courage."
        )
        world.para()
        world.say(
            f"By morning they were on the safe road, and {parent.label_word} had "
            f"a fine story about how a wise warning can save a foolish pride."
        )
        outcome = "averted"
    else:
        slip_away(world, hero, act)
        world.para()
        desperation(world, hero, guide)
        hero.meters["risk"] += 1
        world.get("road").meters["risk"] += 1
        if contained(fix, goal, params.delay):
            save(world, parent, fix, goal, act)
            world.say(
                f"{hero.id} and {guide.id} followed {parent.label_word}'s steady "
                f"light home."
            )
            world.para()
            ending_good(world, hero, guide, parent, setting)
            outcome = "contained"
        else:
            fix_fail(world, parent, fix, goal)
            world.para()
            ending_bad(world, hero, guide, parent)
            outcome = "failed"
    world.facts.update(
        hero=hero,
        guide=guide,
        parent=parent,
        setting=setting,
        act=act,
        goal=goal,
        fix=fix,
        outcome=outcome,
        relation=params.relation,
        hero_age=params.hero_age,
        guide_age=params.guide_age,
        trait=params.trait,
        delay=params.delay,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale cautionary story that includes the words "slink", '
        f'"jabber", and "desperation".',
        f"Tell a moral-value story where {f['hero'].id} almost follows a slinking "
        f"shortcut, but {f['guide'].id} jabbers a warning and saves the day.",
        f"Write a child-friendly tall tale about a risky shortcut, a loud warning, "
        f"and a lesson that bravery should listen to wisdom.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    guide = f["guide"]
    parent = f["parent"]
    act = f["act"]
    goal = f["goal"]
    fix = f["fix"]
    outcome = f["outcome"]
    qa: list[QAItem] = [
        QAItem(
            question="What was the risky choice in the story?",
            answer=f"{hero.id} wanted to {act.verb} instead of staying on the safe road. "
                   f"The shortcut looked quicker, but it was the kind of path that could hide trouble."
        ),
        QAItem(
            question=f"Why did {guide.id} keep warning {hero.id}?",
            answer=f"{guide.id} could tell the slinking path was dangerous, so {guide.id} jabbered a warning before anyone got hurt. "
                   f"{guide.id} wanted {hero.id} to reach {goal.label} safely, not by stumbling into a mishap."
        ),
    ]
    if outcome == "averted":
        qa.append(
            QAItem(
                question="How did the story end?",
                answer=f"{hero.id} listened, turned back, and nobody got trapped in danger. "
                       f"The lesson was that a wise warning can be worth more than a proud hurry."
            )
        )
    elif outcome == "contained":
        qa.append(
            QAItem(
                question="How was the trouble fixed?",
                answer=f"{parent.label_word.capitalize()} came with {fix.label} and used it to guide everyone home. "
                       f"The danger settled down, and the crooked shortcut lost its power."
            )
        )
    else:
        qa.append(
            QAItem(
                question="What happened when the fix was too weak?",
                answer=f"{parent.label_word.capitalize()} tried to help, but {fix.fail.replace('{goal}', goal.label)}. "
                       f"That left the travelers shaken, though they still learned a proper lesson about caution."
            )
        )
    qa.append(
        QAItem(
            question="What did the tall tale teach?",
            answer="It taught that brave feet should listen when wisdom speaks. "
                   "A story can be grand and funny, but a good moral is worth more than a reckless shortcut."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = {f["act"].id, "caution", "moral"}
    if f["outcome"] != "averted":
        tags.add("danger")
    out: list[QAItem] = []
    if "caution" in tags:
        out.append(QAItem(
            question="What does it mean to be cautious?",
            answer="Being cautious means watching out for danger and choosing the safer path. "
                   "It is a way of using good sense before trouble starts."
        ))
    if "moral" in tags:
        out.append(QAItem(
            question="What is a moral in a story?",
            answer="A moral is the lesson a story leaves behind after the adventure ends. "
                   "It helps readers remember how to act wisely in real life."
        ))
    out.append(QAItem(
        question="What is a tall tale?",
        answer="A tall tale is a story that sounds huge, bold, and a little bigger than life. "
               "It often uses lively pictures and grand language to make the adventure sparkle."
    ))
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
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


ASP_RULES = r"""
valid(S,A,G) :- setting(S), act(A), goal(G).
cautious(T) :- trait(T), is_cautious(T).
older_bonus(4) :- relation(siblings), guide_older.
authority(X) :- cautious(T), base_caution(T, B), older_bonus(O), X = B + O.
averted :- guide_older, authority(A), bravery_init(B), A > B.
contained :- chosen_fix(F), chosen_goal(G), fix_power(F, P), goal_risk(G, R), P >= R.
outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(failed) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid in ACTS:
        lines.append(asp.fact("act", aid))
    for gid in GOALS:
        lines.append(asp.fact("goal", gid))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("fix_power", fid, fix.power))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    for tr in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", tr))
    lines.append(asp.fact("base_caution", "careful", 5))
    lines.append(asp.fact("base_caution", "cautious", 5))
    lines.append(asp.fact("base_caution", "thoughtful", 5))
    lines.append(asp.fact("base_caution", "sensible", 5))
    lines.append(asp.fact("guide_older"))
    lines.append(asp.fact("goal_risk", "bridge", 2))
    lines.append(asp.fact("goal_risk", "market", 3))
    lines.append(asp.fact("goal_risk", "barn", 4))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3.", "#show outcome/1."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_fix", params.fix),
        asp.fact("chosen_goal", params.goal),
        asp.fact("relation", params.relation),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    clingo = set(asp_valid_combos())
    if py == clingo:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate:")
        print("  only in python:", sorted(py - clingo))
        print("  only in clingo:", sorted(clingo - py))

    sample = CURATED[0]
    try:
        sample_world = generate(sample)
        if not sample_world.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test produced a story.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    cases = list(CURATED)
    rng = random.Random(777)
    for _ in range(10):
        cases.append(resolve_params(build_parser().parse_args([]), rng))
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: ASP outcome matches Python on {len(cases)} cases.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")
    return rc


CURATED = [
    StoryParams(setting="valley", act="slink", goal="bridge", fix="horn", hero="Ruby", hero_gender="girl", guide="Sage", guide_gender="boy", parent="mother", trait="careful", delay=0, hero_age=6, guide_age=9, relation="siblings", trust=7),
    StoryParams(setting="marsh", act="jabber", goal="market", fix="lantern", hero="Milo", hero_gender="boy", guide="Ivy", guide_gender="girl", parent="father", trait="thoughtful", delay=1, hero_age=7, guide_age=10, relation="siblings", trust=6),
    StoryParams(setting="canyon", act="desperation", goal="barn", fix="rope", hero="June", hero_gender="girl", guide="Pearl", guide_gender="girl", parent="mother", trait="brave", delay=2, hero_age=8, guide_age=8, relation="friends", trust=4),
]


def explain_response(fid: str) -> str:
    fix = FIXES[fid]
    return f"(Refusing fix '{fid}': it is not sensible enough for a cautious tale.)"


def build_story(params: StoryParams) -> World:
    if any(x not in SETTINGS for x in [params.setting]) or any(x not in ACTS for x in [params.act]) or any(x not in GOALS for x in [params.goal]) or any(x not in FIXES for x in [params.fix]):
        raise StoryError("Invalid parameters.")
    world = World()
    setting = SETTINGS[params.setting]
    act = ACTS[params.act]
    goal = GOALS[params.goal]
    fix = FIXES[params.fix]
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_gender, role="hero"))
    guide = world.add(Entity(id=params.guide, kind="character", type=params.guide_gender, role="guide"))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label="the parent", role="parent"))
    world.add(Entity(id="road", type="road", label="the road"))

    describe_shift(world, hero, guide, setting)
    world.para()
    see_risk(world, hero, goal, act)
    jabber(world, guide, hero, act, parent)
    if would_avert(params.relation, params.hero_age, params.guide_age, params.trait):
        world.say(f"{hero.id} stopped short, and the two of them turned back before the dark could bite.")
        world.para()
        world.say(f"By morning, {parent.label_word} praised the wise choice and the safe road looked brighter than gold.")
        outcome = "averted"
    else:
        slip_away(world, hero, act)
        world.para()
        desperation(world, hero, guide)
        if contained(fix, goal, params.delay):
            save(world, parent, fix, goal, act)
            world.para()
            ending_good(world, hero, guide, parent, setting)
            outcome = "contained"
        else:
            fix_fail(world, parent, fix, goal)
            world.para()
            ending_bad(world, hero, guide, parent)
            outcome = "failed"
    world.facts.update(hero=hero, guide=guide, parent=parent, setting=setting, act=act, goal=goal, fix=fix, outcome=outcome, params=params)
    return world


def generate(params: StoryParams) -> StorySample:
    world = build_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def explain_rejection_for_args(args: argparse.Namespace) -> Optional[str]:
    return None


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(sorted(SETTINGS))
    act = args.act or rng.choice(sorted(ACTS))
    goal = args.goal or rng.choice(sorted(GOALS))
    fix = args.fix or rng.choice(sorted(FIXES))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    guide_gender = args.guide_gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(HEROES)
    guide = args.guide or rng.choice([n for n in GUIDES if n != hero])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        setting=setting,
        act=act,
        goal=goal,
        fix=fix,
        hero=hero,
        hero_gender=hero_gender,
        guide=guide,
        guide_gender=guide_gender,
        parent=parent,
        trait=trait,
        delay=delay,
        hero_age=rng.randint(5, 8),
        guide_age=rng.randint(6, 10),
        relation=rng.choice(["friends", "siblings"]),
        trust=rng.randint(0, 10),
    )


def format_story(sample: StorySample) -> str:
    return sample.story


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.hero} & {p.guide}: {p.act} / {outcome_of(p)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
