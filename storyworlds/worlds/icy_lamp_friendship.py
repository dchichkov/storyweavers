#!/usr/bin/env python3
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
MESS_KINDS = {"chilled", "frosted"}
GENDERS = ("girl", "boy")


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    gender: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    region: Optional[str] = None
    covers: set[str] = field(default_factory=set)
    guards: set[str] = field(default_factory=set)
    worn_by: Optional[str] = None
    owner: Optional[str] = None
    protective: bool = False
    plural: bool = False

    def pronoun(self, case: str) -> str:
        table = {
            "girl": {"subject": "she", "object": "her", "possessive": "her"},
            "boy": {"subject": "he", "object": "him", "possessive": "his"},
            "mother": {"subject": "she", "object": "her", "possessive": "her"},
            "father": {"subject": "he", "object": "him", "possessive": "his"},
            "grandmother": {"subject": "she", "object": "her", "possessive": "her"},
            "grandfather": {"subject": "he", "object": "him", "possessive": "his"},
        }
        return table.get(self.gender or self.kind, table["girl"])[case]


@dataclass(frozen=True)
class Setting:
    id: str
    label: str
    landmark: str
    affords: set[str]
    tall_claim: str


@dataclass(frozen=True)
class Activity:
    id: str
    label: str
    gerund: str
    urge: str
    mess: str
    zones: set[str]
    warning: str
    tags: set[str]


@dataclass(frozen=True)
class Token:
    id: str
    label: str
    full_label: str
    region: str
    vulnerable: set[str]
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: set(GENDERS))


@dataclass(frozen=True)
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    instruction: str
    action: str
    tags: set[str]
    plural: bool = False


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.fired_names: list[str] = []
        self.facts: dict[str, object] = {}
        self.active_activity: Optional[str] = None

    def copy(self) -> "World":
        return copy.deepcopy(self)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, text: str) -> None:
        if not self.paragraphs:
            self.paragraphs.append([])
        self.paragraphs[-1].append(text)

    def break_para(self) -> None:
        if self.paragraphs and self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str, mess: str) -> bool:
        for item in self.worn_items(actor):
            if item.protective and region in item.covers and mess in item.guards:
                return True
        return False


@dataclass(frozen=True)
class Rule:
    name: str
    apply: Callable[[World, bool], bool]


def _mark(world: World, name: str, *parts: object) -> bool:
    sig = (name, *parts)
    if sig in world.fired:
        return False
    world.fired.add(sig)
    world.fired_names.append(name)
    return True


def _r_freeze_token(world: World, narrate: bool) -> bool:
    activity_id = world.active_activity
    if not activity_id:
        return False
    activity = ACTIVITIES[activity_id]
    changed = False
    for actor in [e for e in world.entities.values() if e.kind == "character"]:
        if actor.meters[activity.mess] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective:
                continue
            if item.region not in activity.zones:
                continue
            if activity.mess not in item.guards and item.guards:
                continue
            if world.covered(actor, item.region, activity.mess):
                continue
            if not _mark(world, "token_freeze", actor.id, item.id, activity.mess):
                continue
            item.meters[activity.mess] += 1
            item.meters["needs_help"] += 1
            changed = True
            if narrate:
                verb = "were" if item.plural else "was"
                world.say(f"The {item.label} {verb} {activity.warning}.")
    return changed


def _r_friend_worry(world: World, narrate: bool) -> bool:
    changed = False
    for item in world.entities.values():
        if item.meters["needs_help"] < THRESHOLD or not item.owner:
            continue
        friend = world.get(item.owner)
        if not _mark(world, "friend_worry", item.id, friend.id):
            continue
        friend.memes["worry"] += 1
        changed = True
        if narrate:
            world.say(f"{friend.label} worried because the friendship token needed help.")
    return changed


def _r_grab_conflict(world: World, narrate: bool) -> bool:
    hero_id = world.facts.get("hero")
    elder_id = world.facts.get("elder")
    if not isinstance(hero_id, str) or not isinstance(elder_id, str):
        return False
    hero = world.get(hero_id)
    elder = world.get(elder_id)
    if hero.memes["defiance"] < THRESHOLD or hero.meters["stopped"] < THRESHOLD:
        return False
    if not _mark(world, "conflict", hero.id, elder.id):
        return False
    hero.memes["conflict"] += 1
    elder.memes["worry"] += 1
    if narrate:
        world.say(f"For a moment, {hero.label} and {elder.label} were both upset.")
    return True


CAUSAL_RULES = [
    Rule("token_freeze", _r_freeze_token),
    Rule("friend_worry", _r_friend_worry),
    Rule("conflict", _r_grab_conflict),
]


def propagate(world: World, *, narrate: bool = True) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            if rule.apply(world, narrate):
                changed = True


SETTINGS = {
    "snow_hill": Setting(
        "snow_hill",
        "Blueberry Snow Hill",
        "a hill so tall that clouds stopped to catch their breath",
        {"carry_lamp", "swing_lamp"},
        "The hill was so high that the moon looked like a silver button on a coat.",
    ),
    "frozen_dock": Setting(
        "frozen_dock",
        "the frozen ferry dock",
        "a dock glazed with ice beside the dark river",
        {"carry_lamp", "raise_lamp"},
        "The river was said to freeze so hard that whispers bounced across it.",
    ),
    "barn_roof": Setting(
        "barn_roof",
        "the red barn roof",
        "a roof that looked over every snowy field",
        {"swing_lamp", "raise_lamp"},
        "The barn roof was so high that a sneeze from there could shake frost off a star.",
    ),
}


ACTIVITIES = {
    "carry_lamp": Activity(
        "carry_lamp",
        "carry the icy lamp by its handle",
        "carrying the icy lamp by its handle",
        "wanted to carry the icy lamp straight to the signal post",
        "chilled",
        {"hands"},
        "cold enough to make fingers stiff",
        {"icy_lamp", "cold", "hands", "friendship"},
    ),
    "swing_lamp": Activity(
        "swing_lamp",
        "swing the icy lamp as a signal",
        "swinging the icy lamp as a signal",
        "wanted to swing the icy lamp in a huge shining circle",
        "frosted",
        {"hands", "cord"},
        "frosted white and hard to move",
        {"icy_lamp", "cold", "cord", "friendship"},
    ),
    "raise_lamp": Activity(
        "raise_lamp",
        "raise the icy lamp on the lookout rope",
        "raising the icy lamp on the lookout rope",
        "wanted to pull the icy lamp up to the lookout hook",
        "frosted",
        {"cord"},
        "frosted white and stuck fast",
        {"icy_lamp", "cold", "cord", "friendship"},
    ),
}


TOKENS = {
    "mittens": Token(
        "mittens",
        "mittens",
        "blue friendship mittens",
        "hands",
        {"chilled", "frosted"},
        plural=True,
    ),
    "bracelet": Token(
        "bracelet",
        "bracelet",
        "braided friendship bracelet",
        "hands",
        {"chilled", "frosted"},
    ),
    "signal_ribbon": Token(
        "signal_ribbon",
        "signal ribbon",
        "red signal ribbon",
        "cord",
        {"frosted"},
    ),
}


GEAR = {
    "wool_wrap": Gear(
        "wool_wrap",
        "thick wool wrap",
        {"hands"},
        {"chilled", "frosted"},
        "wrap your hands first",
        "wrapped the thick wool around the lamp handle",
        {"wool", "hands"},
    ),
    "rope_sleeve": Gear(
        "rope_sleeve",
        "warm rope sleeve",
        {"cord"},
        {"frosted"},
        "slide the warm sleeve over the rope first",
        "slid the warm sleeve over the lookout rope",
        {"rope", "cord"},
    ),
    "lamp_cradle": Gear(
        "lamp_cradle",
        "padded lamp cradle",
        {"hands", "cord"},
        {"chilled", "frosted"},
        "carry the lamp in the padded cradle",
        "set the icy lamp in the padded cradle",
        {"lamp", "cold"},
    ),
}


NAMES = {
    "girl": ["Mira", "Nell", "Ava", "Lena"],
    "boy": ["Otis", "Finn", "Theo", "Ben"],
}
FRIENDS = ["Pip", "Rae", "Jo", "Max"]
ELDERS = {
    "mother": "mother",
    "father": "father",
    "grandmother": "grandmother",
    "grandfather": "grandfather",
}
TRAITS = ["bold", "kind", "quick", "curious"]


def prize_at_risk(activity: Activity, token: Token) -> bool:
    return token.region in activity.zones and activity.mess in token.vulnerable


def select_gear(activity: Activity, token: Token) -> Optional[Gear]:
    for gear in GEAR.values():
        if token.region in gear.covers and activity.mess in gear.guards:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for place, setting in SETTINGS.items():
        for activity_id in setting.affords:
            activity = ACTIVITIES[activity_id]
            for token_id, token in TOKENS.items():
                if not prize_at_risk(activity, token):
                    continue
                if select_gear(activity, token) is None:
                    continue
                for gender in sorted(token.genders):
                    out.append((place, activity_id, token_id, gender))
    return sorted(out)


def explain_rejection(place: str, activity_id: str, token_id: str, gender: str) -> str:
    setting = SETTINGS.get(place)
    activity = ACTIVITIES.get(activity_id)
    token = TOKENS.get(token_id)
    if setting is None:
        return f"Unknown place: {place}."
    if activity is None:
        return f"Unknown activity: {activity_id}."
    if token is None:
        return f"Unknown friendship token: {token_id}."
    if activity_id not in setting.affords:
        return f"{setting.label} does not support {activity.label}."
    if gender not in token.genders:
        return f"A {gender} is not a plausible wearer for the {token.label} in this catalog."
    if not prize_at_risk(activity, token):
        return f"The {activity.label} would not honestly threaten the {token.label}."
    if select_gear(activity, token) is None:
        return f"No available safety gear fixes the risk to the {token.label}."
    return "The requested options are reasonable."


def article(text: str) -> str:
    return "an" if text[:1].lower() in {"a", "e", "i", "o", "u"} else "a"


def gift_phrase(token: Token) -> str:
    if token.plural:
        return f"a pair of {token.full_label}"
    return f"{article(token.full_label)} {token.full_label}"


def token_prompt_phrase(token: Token) -> str:
    return f"{article(token.label)} {token.label}" if not token.plural else f"a pair of {token.label}"


def sentence_start(text: str) -> str:
    return text[:1].upper() + text[1:]


def _do_activity(world: World, hero: Entity, activity: Activity, *, narrate: bool) -> None:
    world.active_activity = activity.id
    hero.meters[activity.mess] += 1
    if narrate:
        world.say(f"{hero.label} started {activity.gerund}.")
    propagate(world, narrate=narrate)


def predict_freeze(world: World, hero: Entity, activity: Activity, token: Entity) -> dict[str, object]:
    sim = world.copy()
    sim.paragraphs = [[]]
    _do_activity(sim, sim.get(hero.id), activity, narrate=False)
    sim_token = sim.get(token.id)
    friend_id = sim.facts.get("friend")
    friend_worry = 0.0
    if isinstance(friend_id, str):
        friend_worry = sim.get(friend_id).memes["worry"]
    return {
        "at_risk": sim_token.meters[activity.mess] >= THRESHOLD,
        "mess": activity.mess,
        "warning": activity.warning,
        "friend_worry": friend_worry >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, friend: Entity, elder: Entity, trait: str) -> None:
    world.say(
        f"Once upon a time, there was a little {trait} {hero.gender} named {hero.label} "
        f"who lived near {world.setting.landmark}."
    )
    world.say(
        f"{world.setting.tall_claim} At the center of it all stood an icy lamp, "
        f"bright enough to shine through a snowstorm."
    )
    world.say(f"{hero.label}'s best friend was {friend.label}, and the two shared every brave idea.")
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    elder.memes["care"] += 1


def give_token(world: World, hero: Entity, friend: Entity, token_cfg: Token) -> Entity:
    token = world.add(
        Entity(
            token_cfg.id,
            "token",
            token_cfg.label,
            region=token_cfg.region,
            guards=set(token_cfg.vulnerable),
            worn_by=hero.id,
            owner=friend.id,
            plural=token_cfg.plural,
        )
    )
    verb = "were" if token.plural else "was"
    world.say(
        f"{friend.label} had given {hero.label} {gift_phrase(token_cfg)}, "
        f"and the {token.label} {verb} their promise to help each other."
    )
    hero.memes["love"] += 1
    friend.memes["love"] += 1
    world.facts["token"] = token.id
    return token


def want_activity(world: World, hero: Entity, activity: Activity) -> None:
    world.break_para()
    world.say(f"One glittering evening, {hero.label} {activity.urge}.")
    hero.memes["want"] += 1


def warn(world: World, hero: Entity, elder: Entity, activity: Activity, token: Entity) -> None:
    prediction = predict_freeze(world, hero, activity, token)
    world.facts["prediction"] = prediction
    world.say(
        f'"Wait," said {elder.label}. "If you {activity.label}, your {token.label} '
        f'may become {prediction["warning"]}. Then {world.get(str(world.facts["friend"])).label} '
        f'will worry that the signal failed."'
    )
    elder.memes["caution"] += 1


def object_to_warning(world: World, hero: Entity, elder: Entity) -> None:
    hero.memes["defiance"] += 1
    world.say(f'"But I can do it," said {hero.label}. "I am almost as tall as tomorrow."')
    hero.meters["stopped"] += 1
    world.say(f"{elder.label} gently caught {hero.pronoun('possessive')} sleeve before the icy lamp moved.")
    propagate(world, narrate=True)


def offer_compromise(world: World, hero: Entity, friend: Entity, activity: Activity, token_cfg: Token) -> Gear:
    gear = select_gear(activity, token_cfg)
    if gear is None:
        raise StoryError("No gear can make this icy-lamp story reasonable.")
    world.break_para()
    world.add(
        Entity(
            gear.id,
            "gear",
            gear.label,
            covers=set(gear.covers),
            guards=set(gear.guards),
            worn_by=hero.id,
            protective=True,
            plural=gear.plural,
        )
    )
    world.say(f"Just then, {friend.label} came running up with a better idea.")
    world.say(f'"{sentence_start(gear.instruction)}," {friend.label} said. "Friends can be brave and careful."')
    world.say(f"So {hero.label} {gear.action}.")
    hero.memes["trust"] += 1
    friend.memes["helpfulness"] += 1
    world.facts["gear"] = gear.id
    return gear


def accept(world: World, hero: Entity, friend: Entity, elder: Entity, activity: Activity, token: Entity) -> None:
    _do_activity(world, hero, activity, narrate=False)
    if token.meters[activity.mess] < THRESHOLD:
        world.say(
            f"This time the {token.label} stayed safe, and the icy lamp shone across "
            f"{world.setting.label} like a tiny winter sun."
        )
    hero.memes["conflict"] = 0
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    elder.memes["relief"] += 1
    world.say(
        f"{hero.label} smiled at {friend.label}, and the two friends kept their promise "
        f"without freezing it."
    )
    world.facts["resolved"] = True


def tell(params: "StoryParams") -> World:
    setting = SETTINGS[params.place]
    activity = ACTIVITIES[params.activity]
    token_cfg = TOKENS[params.token]
    world = World(setting)
    hero = world.add(Entity("hero", "character", params.name, gender=params.gender))
    friend = world.add(Entity("friend", "character", params.friend, gender="girl"))
    elder = world.add(Entity("elder", "character", params.elder.title(), gender=params.elder))
    world.facts.update(
        {
            "hero": hero.id,
            "friend": friend.id,
            "elder": elder.id,
            "activity": activity.id,
            "place": setting.id,
            "resolved": False,
        }
    )
    introduce(world, hero, friend, elder, params.trait)
    token = give_token(world, hero, friend, token_cfg)
    want_activity(world, hero, activity)
    warn(world, hero, elder, activity, token)
    object_to_warning(world, hero, elder)
    offer_compromise(world, hero, friend, activity, token_cfg)
    accept(world, hero, friend, elder, activity, token)
    return world


@dataclass
class StoryParams:
    place: str
    activity: str
    token: str
    name: str
    gender: str
    friend: str
    elder: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams("snow_hill", "carry_lamp", "mittens", "Mira", "girl", "Pip", "grandmother", "bold", 11),
    StoryParams("frozen_dock", "raise_lamp", "signal_ribbon", "Finn", "boy", "Rae", "father", "kind", 12),
    StoryParams("barn_roof", "swing_lamp", "bracelet", "Nell", "girl", "Jo", "mother", "curious", 13),
    StoryParams("barn_roof", "raise_lamp", "signal_ribbon", "Otis", "boy", "Max", "grandfather", "quick", 14),
]


def generation_prompts(world: World) -> list[str]:
    activity = ACTIVITIES[str(world.facts["activity"])]
    token = TOKENS[str(world.facts["token"])]
    hero = world.get(str(world.facts["hero"]))
    return [
        'Write a tall tale for children that includes the words "icy lamp" and centers on friendship.',
        f"Write a story about {hero.label}, a friend, and {activity.gerund} without harming {token_prompt_phrase(token)}.",
        "Write a story where an elder predicts a cold problem and a friend helps solve it safely.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.get(str(world.facts["hero"]))
    friend = world.get(str(world.facts["friend"]))
    elder = world.get(str(world.facts["elder"]))
    activity = ACTIVITIES[str(world.facts["activity"])]
    token = world.get(str(world.facts["token"]))
    gear = GEAR[str(world.facts["gear"])]
    prediction = dict(world.facts["prediction"])
    return [
        (
            f"Why did {elder.label} stop {hero.label}?",
            f"{elder.label} stopped {hero.label} because {activity.gerund} could make the {token.label} {prediction['warning']}. "
            f"The warning came from a predicted consequence, not from damage that had already happened.",
        ),
        (
            f"How did {friend.label} help?",
            f"{friend.label} brought the {gear.label} and gave a safer plan. "
            f"That let {hero.label} use the icy lamp while keeping the friendship token safe.",
        ),
        (
            "What changed by the end of the story?",
            f"{hero.label} stopped arguing and accepted help from {friend.label}. "
            f"The conflict faded, the icy lamp still shone, and their friendship promise stayed intact.",
        ),
    ]


KNOWLEDGE = {
    "icy_lamp": (
        "What could an icy lamp mean in a story?",
        "An icy lamp can be an imaginary lamp that is very cold and very bright. In this storyworld, it creates a cold risk that characters must handle carefully.",
    ),
    "cold": (
        "Why can very cold things be hard to hold?",
        "Very cold things can make fingers stiff or uncomfortable. A cover, wrap, or handle keeps skin away from the cold surface.",
    ),
    "hands": (
        "Why do mittens help in winter?",
        "Mittens trap warm air around the fingers. They also make it safer to touch cold objects for a short time.",
    ),
    "cord": (
        "Why can frost be a problem for a rope or cord?",
        "Frost can make a cord stiff and harder to move. If the cord must slide or bend, a warm sleeve can keep it working.",
    ),
    "friendship": (
        "What does friendship mean in a child-level story?",
        "Friendship means caring about another person and helping them make good choices. It can turn a risky plan into a shared, safer plan.",
    ),
    "wool": (
        "Why is wool useful in cold weather?",
        "Wool holds warmth even when the air is cold. It is often used for wraps, hats, and mittens.",
    ),
    "rope": (
        "What is a rope sleeve for?",
        "A rope sleeve covers part of a rope so it is easier and safer to handle. In this story, it keeps frost away from the working part of the rope.",
    ),
    "lamp": (
        "Why would a lamp need a cradle?",
        "A cradle can hold a lamp steady and keep hands away from hot or cold parts. It makes carrying the lamp safer.",
    ),
}


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    activity = ACTIVITIES[str(world.facts["activity"])]
    gear = GEAR[str(world.facts["gear"])]
    tags = set(activity.tags) | set(gear.tags)
    pairs = [KNOWLEDGE[tag] for tag in sorted(tags) if tag in KNOWLEDGE]
    return pairs[:4]


ASP_RULES = r"""
at_risk(A,T) :- zone(A,R), worn_on(T,R), mess_of(A,M), vulnerable(T,M).
effective(A,T,G) :- at_risk(A,T), worn_on(T,R), covers(G,R), mess_of(A,M), guards(G,M).
valid(P,A,T,Gender) :- setting(P), affords(P,A), token(T), gender(Gender), can_wear(Gender,T), effective(A,T,_).
#show valid/4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for gender in GENDERS:
        lines.append(asp.fact("gender", gender))
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for activity in setting.affords:
            lines.append(asp.fact("affords", place, activity))
    for activity_id, activity in ACTIVITIES.items():
        lines.append(asp.fact("activity", activity_id))
        lines.append(asp.fact("mess_of", activity_id, activity.mess))
        for zone in activity.zones:
            lines.append(asp.fact("zone", activity_id, zone))
    for token_id, token in TOKENS.items():
        lines.append(asp.fact("token", token_id))
        lines.append(asp.fact("worn_on", token_id, token.region))
        for mess in token.vulnerable:
            lines.append(asp.fact("vulnerable", token_id, mess))
        for gender in token.genders:
            lines.append(asp.fact("can_wear", gender, token_id))
    for gear_id, gear in GEAR.items():
        lines.append(asp.fact("gear", gear_id))
        for region in gear.covers:
            lines.append(asp.fact("covers", gear_id, region))
        for mess in gear.guards:
            lines.append(asp.fact("guards", gear_id, mess))
    return "\n".join(lines) + "\n"


def asp_valid_combos() -> list[tuple[str, str, str, str]]:
    import asp

    model = asp.one_model(asp_facts() + ASP_RULES)
    return sorted(asp.atoms(model, "valid"))


def asp_verify() -> int:
    py = set(valid_combos())
    lp = set(asp_valid_combos())
    if py == lp:
        print(f"OK: Python and ASP agree on {len(py)} valid icy-lamp stories.")
        return 0
    print("Mismatch between Python and ASP valid story sets.")
    print("Only Python:", sorted(py - lp))
    print("Only ASP:", sorted(lp - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate the icy-lamp friendship storyworld.")
    parser.add_argument("--place", choices=sorted(SETTINGS))
    parser.add_argument("--activity", choices=sorted(ACTIVITIES))
    parser.add_argument("--token", choices=sorted(TOKENS))
    parser.add_argument("--gender", choices=list(GENDERS))
    parser.add_argument("--name")
    parser.add_argument("--friend", choices=FRIENDS)
    parser.add_argument("--elder", choices=sorted(ELDERS))
    parser.add_argument("--trait", choices=TRAITS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.activity:
        combos = [c for c in combos if c[1] == args.activity]
    if args.token:
        combos = [c for c in combos if c[2] == args.token]
    if args.gender:
        combos = [c for c in combos if c[3] == args.gender]
    if not combos:
        place = args.place or next(iter(SETTINGS))
        activity = args.activity or next(iter(ACTIVITIES))
        token = args.token or next(iter(TOKENS))
        gender = args.gender or GENDERS[0]
        raise StoryError(explain_rejection(place, activity, token, gender))
    place, activity, token, gender = rng.choice(combos)
    name = args.name or rng.choice(NAMES[gender])
    friend = args.friend or rng.choice([f for f in FRIENDS if f != name])
    elder = args.elder or rng.choice(list(ELDERS))
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place, activity, token, name, gender, friend, elder, trait, args.seed)


def generate(params: StoryParams) -> StorySample:
    if (params.place, params.activity, params.token, params.gender) not in valid_combos():
        raise StoryError(explain_rejection(params.place, params.activity, params.token, params.gender))
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def dump_trace(world: World) -> None:
    print("\nTRACE")
    print(f"setting: {world.setting.id}")
    print("fired rules:", ", ".join(world.fired_names) or "(none)")
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        parts = [entity.id, entity.kind, entity.label]
        if entity.region:
            parts.append(f"region={entity.region}")
        if entity.covers:
            parts.append(f"covers={sorted(entity.covers)}")
        if entity.guards:
            parts.append(f"guards={sorted(entity.guards)}")
        if entity.worn_by:
            parts.append(f"worn_by={entity.worn_by}")
        print("  " + " | ".join(parts))
        if meters:
            print(f"    meters={meters}")
        if memes:
            print(f"    memes={memes}")


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if qa:
        print("\nPROMPTS")
        for prompt in sample.prompts:
            print(f"- {prompt}")
        print("\nSTORY QA")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\nWORLD KNOWLEDGE QA")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
    if trace and sample.world is not None:
        dump_trace(sample.world)


def _samples_from_args(args) -> list[StorySample]:
    if args.all:
        return [generate(params) for params in CURATED]
    base_seed = args.seed if args.seed is not None else random.randrange(1, 10_000_000)
    samples: list[StorySample] = []
    seen: set[str] = set()
    attempts = 0
    while len(samples) < args.n and attempts < max(20, args.n * 20):
        seed = base_seed + attempts
        rng = random.Random(seed)
        local_args = copy.copy(args)
        local_args.seed = seed
        params = resolve_params(local_args, rng)
        params.seed = seed
        sample = generate(params)
        if sample.story not in seen:
            samples.append(sample)
            seen.add(sample.story)
        attempts += 1
    if len(samples) < args.n:
        raise StoryError(f"Only generated {len(samples)} distinct stories after {attempts} attempts.")
    return samples


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.show_asp:
        print(asp_facts() + ASP_RULES)
        return 0
    if args.verify:
        return asp_verify()
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
        return 0
    try:
        samples = _samples_from_args(args)
    except StoryError as exc:
        parser.error(str(exc))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return 0
    for i, sample in enumerate(samples, 1):
        header = f"=== icy_lamp_friendship #{i} seed={sample.params.seed} ===" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i != len(samples):
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
