#!/usr/bin/env python3
"""
Tall-tale storyworld for:
  Words: murmur, wobbly window, wondrous bush
  Setting: neighborhood park
  Features: Magic, Kindness

Internal source tale:
    In a neighborhood park, a loose window on a shed carries the tiny murmur of
    a wondrous bush so loudly that two children think the whole park is trying
    to speak. Instead of running from the strange sound, they answer it with
    kindness. They discover that the bush needs help, and when they help it, the
    bush answers with impossible-looking magic that turns the rumor into a warm,
    visible ending image.
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
from typing import Iterable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    role: str = ""
    traits: list[str] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass(frozen=True)
class Park:
    id: str
    place: str
    opening: str
    closing_view: str
    supports: frozenset[str]


@dataclass(frozen=True)
class Window:
    id: str
    phrase: str
    location: str
    wobble_sound: str
    hears: frozenset[str]
    image_line: str


@dataclass(frozen=True)
class Bush:
    id: str
    phrase: str
    location: str
    need: str
    murmur_words: str
    need_line: str
    magic_type: str
    magic_line: str
    final_image: str
    lesson_line: str
    tags: frozenset[str]


@dataclass(frozen=True)
class KindAct:
    id: str
    label: str
    supports: frozenset[str]
    gear: str
    method_line: str
    proof_line: str
    kindness_line: str
    tags: frozenset[str]


class World:
    def __init__(self, park: Park) -> None:
        self.park = park
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.history: list[dict[str, str]] = []
        self.fired: set[tuple[str, ...]] = set()
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, ent_id: str) -> Entity:
        return self.entities[ent_id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def note(self, event: str, **fields: str) -> None:
        item = {"event": event}
        item.update(fields)
        self.history.append(item)

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)

    def copy(self) -> "World":
        clone = World(self.park)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.history = copy.deepcopy(self.history)
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


def role(world: World, name: str) -> Optional[Entity]:
    return next((ent for ent in world.entities.values() if ent.role == name), None)


PARKS = {
    "maple_patch": Park(
        id="maple_patch",
        place="Maple Patch Park",
        opening="the swings squeaked like fiddles and the pebble path shone as if it had borrowed nickels from the moon",
        closing_view="The penny fountain blinked at the last light",
        supports=frozenset({"shed_window", "greenhouse_window", "garden_bed", "kite_corner", "robin_fence"}),
    ),
    "chestnut_loop": Park(
        id="chestnut_loop",
        place="Chestnut Loop Park",
        opening="the merry-go-round stood so proud it looked ready to spin the clouds into buttons",
        closing_view="The sandbox looked smooth as cake frosting",
        supports=frozenset({"shed_window", "kiosk_window", "garden_bed", "kite_corner", "robin_fence"}),
    ),
    "poppy_lane": Park(
        id="poppy_lane",
        place="Poppy Lane Park",
        opening="the jump ropes slapped the path like tiny drumlines and the benches warmed their wooden knees in the sun",
        closing_view="The bandstand rails gleamed like polished honey",
        supports=frozenset({"greenhouse_window", "kiosk_window", "garden_bed", "kite_corner", "robin_fence"}),
    ),
}

WINDOWS = {
    "shed_window": Window(
        id="shed_window",
        phrase="the wobbly window on the tool shed",
        location="shed_window",
        wobble_sound="rattled like a pocketful of teaspoons",
        hears=frozenset({"thirst", "snag"}),
        image_line="Its pane flashed a crooked stripe of light across the gravel.",
    ),
    "greenhouse_window": Window(
        id="greenhouse_window",
        phrase="the wobbly window on the tiny greenhouse",
        location="greenhouse_window",
        wobble_sound="hummed and clicked like a polite tambourine",
        hears=frozenset({"thirst", "brace"}),
        image_line="Its glass trembled with a green shine that made even the weeds look important.",
    ),
    "kiosk_window": Window(
        id="kiosk_window",
        phrase="the wobbly window on the park notice kiosk",
        location="kiosk_window",
        wobble_sound="clacked like two seashells trying to gossip",
        hears=frozenset({"snag", "brace"}),
        image_line="Its loose corner winked every time the breeze poked it.",
    ),
}

BUSHES = {
    "bellberry": Bush(
        id="bellberry",
        phrase="a wondrous bush hung with bell-blue berries",
        location="garden_bed",
        need="thirst",
        murmur_words="Water my thirsty toes",
        need_line="The soil around its roots had gone crumbly and pale.",
        magic_type="dew_bells",
        magic_line="Each berry filled with silver dew and chimed so sweetly that even the pigeons stood still to listen.",
        final_image="The berries glittered like a necklace big enough for the evening sky.",
        lesson_line="Kind hands had noticed a small thirst before it turned into a big sorrow.",
        tags=frozenset({"bush", "water", "berries", "magic"}),
    ),
    "ribbonthorn": Bush(
        id="ribbonthorn",
        phrase="a wondrous bush stitched with silver-thorn ribbons",
        location="kite_corner",
        need="snag",
        murmur_words="Please free my sleeves",
        need_line="A tangled kite tail had wrapped itself around its springy branches.",
        magic_type="ribbon_lanterns",
        magic_line="When the last knot slipped free, the ribbons rose and glowed like a parade of tiny lanterns.",
        final_image="The freed streamers floated above the path like comets learning their table manners.",
        lesson_line="Gentle patience had untied a problem that rough hands would only tighten.",
        tags=frozenset({"bush", "kite", "ribbons", "magic"}),
    ),
    "lanternlaurel": Bush(
        id="lanternlaurel",
        phrase="a wondrous bush with lantern-shaped leaves",
        location="robin_fence",
        need="brace",
        murmur_words="Please hold me up",
        need_line="One heavy branch leaned over a robin nest and shook every time the wind teased it.",
        magic_type="leaf_lamps",
        magic_line="The leaves brightened one by one until the whole bush glowed like a row of friendly porch lamps.",
        final_image="Its green lantern leaves shone so warmly that dusk seemed to sit down beside them and smile.",
        lesson_line="A soft brace and a soft voice can steady more than one thing at a time.",
        tags=frozenset({"bush", "nest", "leaves", "magic"}),
    ),
}

ACTS = {
    "water_roots": KindAct(
        id="water_roots",
        label="water the roots",
        supports=frozenset({"thirst"}),
        gear="a green watering can",
        method_line="They carried water cup by cup and tipped it slowly so the thirsty ground could drink without spilling a drop.",
        proof_line="As the dark soil drank, the murmur softened into a humming thank-you.",
        kindness_line="They treated the roots the way they would help a friend after a long, hot walk.",
        tags=frozenset({"kindness", "water"}),
    ),
    "untangle_kite": KindAct(
        id="untangle_kite",
        label="untangle the snag",
        supports=frozenset({"snag"}),
        gear="gentle fingers and a low park stool",
        method_line="They lifted each ribbon loop slowly, as careful as bakers carrying frosting, until the snag loosened.",
        proof_line="The branches stopped tugging, and the murmur turned into a bright little sigh of relief.",
        kindness_line="They were careful not to snap a twig or scold the trapped kite tail.",
        tags=frozenset({"kindness", "patience"}),
    ),
    "brace_branch": KindAct(
        id="brace_branch",
        label="brace the branch",
        supports=frozenset({"brace"}),
        gear="a smooth stick and a scarf folded into a soft tie",
        method_line="They propped the leaning branch with the stick and wrapped the scarf so the bark would not pinch.",
        proof_line="The branch held steady at once, and the murmur dropped from a worry into a calm, grateful whisper.",
        kindness_line="They cared for the nest and the branch at the same time.",
        tags=frozenset({"kindness", "care"}),
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Josie", "Ruth", "Nora", "Pia"]
BOY_NAMES = ["Owen", "Theo", "Jules", "Milo", "Benji", "Eli"]
TRAITS = ["kind", "careful", "bright-eyed", "steady", "curious"]


@dataclass
class StoryParams:
    park: str
    window: str
    bush: str
    act: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    trait: str
    seed: Optional[int] = None


def park_supports(park: Park, item_location: str) -> bool:
    return item_location in park.supports


def window_hears(window: Window, bush: Bush) -> bool:
    return bush.need in window.hears


def act_solves(act: KindAct, bush: Bush) -> bool:
    return bush.need in act.supports


def valid_combo(park: Park, window: Window, bush: Bush, act: KindAct) -> bool:
    return (
        park_supports(park, window.location)
        and park_supports(park, bush.location)
        and window_hears(window, bush)
        and act_solves(act, bush)
    )


def explain_rejection(park: Park, window: Window, bush: Bush, act: KindAct) -> str:
    if not park_supports(park, window.location):
        return f"(No story: {park.place} does not have room for {window.phrase}.)"
    if not park_supports(park, bush.location):
        return f"(No story: {park.place} has no place for {bush.phrase} to grow in this setup.)"
    if not window_hears(window, bush):
        return f"(No story: {window.phrase} cannot carry a murmur about {bush.need} trouble.)"
    return f"(No story: the plan to {act.label} does not solve the bush's real need.)"


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for park_id, park in PARKS.items():
        for window_id, window in WINDOWS.items():
            for bush_id, bush in BUSHES.items():
                for act_id, act in ACTS.items():
                    if valid_combo(park, window, bush, act):
                        combos.append((park_id, window_id, bush_id, act_id))
    return sorted(combos)


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.park and args.window and args.bush and args.act:
        park = PARKS[args.park]
        window = WINDOWS[args.window]
        bush = BUSHES[args.bush]
        act = ACTS[args.act]
        if not valid_combo(park, window, bush, act):
            raise StoryError(explain_rejection(park, window, bush, act))

    combos = [
        combo
        for combo in valid_combos()
        if (args.park is None or combo[0] == args.park)
        and (args.window is None or combo[1] == args.window)
        and (args.bush is None or combo[2] == args.bush)
        and (args.act is None or combo[3] == args.act)
    ]
    if not combos:
        raise StoryError("(No valid neighborhood-park tall tale matches the given options.)")

    park_id, window_id, bush_id, act_id = rng.choice(combos)
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    hero = args.hero or _pick_name(rng, hero_gender)
    friend = args.friend or _pick_name(rng, friend_gender, avoid=hero)
    return StoryParams(
        park=park_id,
        window=window_id,
        bush=bush_id,
        act=act_id,
        hero=hero,
        hero_gender=hero_gender,
        friend=friend,
        friend_gender=friend_gender,
        trait=rng.choice(TRAITS),
    )


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in (_r_catch_murmur, _r_read_need, _r_help_bush, _r_magic_thanks):
            before = len(world.fired)
            rule(world)
            if len(world.fired) > before:
                changed = True


def _r_catch_murmur(world: World) -> None:
    window = world.get("window")
    bush = world.get("bush")
    if window.meters["wobbling"] < THRESHOLD or bush.meters["needs_help"] < THRESHOLD:
        return
    sig = ("catch_murmur",)
    if sig in world.fired:
        return
    world.fired.add(sig)
    hero = role(world, "hero")
    friend = role(world, "friend")
    window.meters["carrying_murmur"] += 1
    bush.meters["heard"] += 1
    if hero is not None:
        hero.memes["wonder"] += 1
    if friend is not None:
        friend.memes["wonder"] += 1
    world.note("murmur_carried", source="window", target="children")


def _r_read_need(world: World) -> None:
    window = world.get("window")
    bush = world.get("bush")
    hero = role(world, "hero")
    friend = role(world, "friend")
    if window.meters["carrying_murmur"] < THRESHOLD or hero is None or friend is None:
        return
    sig = ("read_need",)
    if sig in world.fired:
        return
    world.fired.add(sig)
    hero.memes["kindness"] += 1
    friend.memes["kindness"] += 1
    hero.memes["concern"] += 1
    friend.memes["concern"] += 1
    bush.memes["hope"] += 1
    world.note("need_understood", need=world.facts["bush_cfg"].need, method="kind_attention")


def _r_help_bush(world: World) -> None:
    hero = role(world, "hero")
    friend = role(world, "friend")
    bush = world.get("bush")
    act = world.get("act")
    if hero is None or friend is None:
        return
    if hero.memes["kindness"] < THRESHOLD or friend.memes["kindness"] < THRESHOLD:
        return
    if act.meters["attempted"] < THRESHOLD:
        return
    sig = ("help_bush",)
    if sig in world.fired:
        return
    world.fired.add(sig)
    bush.meters["needs_help"] = 0.0
    bush.meters["helped"] += 1
    bush.memes["relief"] += 1
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    act.meters["worked"] += 1
    world.note("kindness_worked", act=world.facts["act_cfg"].id, need=world.facts["bush_cfg"].need)


def _r_magic_thanks(world: World) -> None:
    bush = world.get("bush")
    window = world.get("window")
    if bush.meters["helped"] < THRESHOLD:
        return
    sig = ("magic_thanks",)
    if sig in world.fired:
        return
    world.fired.add(sig)
    bush.meters["glowing"] += 1
    bush.memes["magic"] += 1
    window.meters["gleaming"] += 1
    world.note("magic_answered", magic=world.facts["bush_cfg"].magic_type, witness="window")


def introduce(world: World, hero: Entity, friend: Entity, window_cfg: Window, bush_cfg: Bush) -> None:
    world.say(
        f"At {world.park.place}, {world.park.opening}. "
        f"{hero.id}, a {hero.traits[0]} child, and {friend.id} came skipping along the path."
    )
    world.say(
        f"Beside them stood {window_cfg.phrase}, and beyond it grew {bush_cfg.phrase}."
    )
    world.say(
        f"In that neighborhood park, even ordinary breezes liked to tell tall tales bigger than a parade float."
    )


def stir_window(world: World, window_ent: Entity, window_cfg: Window) -> None:
    window_ent.meters["wobbling"] += 1
    world.note("window_wobbled", sound=window_cfg.wobble_sound)
    propagate(world)
    world.say(
        f"The breeze touched the frame, and {window_cfg.phrase} {window_cfg.wobble_sound}."
    )
    world.say(window_cfg.image_line)


def hear_murmur(world: World, hero: Entity, friend: Entity, bush_cfg: Bush) -> None:
    bush_ent = world.get("bush")
    if bush_ent.meters["heard"] < THRESHOLD:
        return
    world.say(
        f"Out rolled a murmur so clear that {hero.id} stopped short. "
        f'"{bush_cfg.murmur_words}," it seemed to say.'
    )
    world.say(
        f"{friend.id} looked past the glass and saw the wondrous bush moving in the wind as if it were trying to wave them over."
    )
    world.say(
        f"They could have called it a ghost story, but kindness tugged harder than fear."
    )


def inspect_need(world: World, hero: Entity, friend: Entity, bush_cfg: Bush, act_cfg: KindAct) -> None:
    world.say(
        f"They ran to the bush and found the truth beneath the tall-tale sound. {bush_cfg.need_line}"
    )
    world.say(
        f'{hero.id} said, "If something in the park is asking nicely, we can answer nicely."'
    )
    world.say(
        f"So the two friends chose to {act_cfg.label} with {act_cfg.gear}."
    )


def do_kindness(world: World, hero: Entity, friend: Entity, act_ent: Entity, act_cfg: KindAct) -> None:
    act_ent.meters["attempted"] += 1
    world.note("kindness_attempted", act=act_cfg.id)
    propagate(world)
    world.say(act_cfg.method_line)
    world.say(act_cfg.kindness_line)
    world.say(
        f"{hero.id} worked first, and {friend.id} watched closely, then they traded jobs so neither kindness nor magic missed a turn."
    )


def reveal_magic(world: World, bush_cfg: Bush, act_cfg: KindAct) -> None:
    bush_ent = world.get("bush")
    window_ent = world.get("window")
    if bush_ent.meters["helped"] < THRESHOLD:
        return
    world.say(act_cfg.proof_line)
    if bush_ent.memes["magic"] >= THRESHOLD:
        world.say(bush_cfg.magic_line)
    if window_ent.meters["gleaming"] >= THRESHOLD:
        world.say(
            f"The glow splashed back across the wobbly window, and for one grand second the pane looked polished enough to hold a second sunset."
        )


def close_story(world: World, hero: Entity, friend: Entity, bush_cfg: Bush) -> None:
    world.say(
        f"{bush_cfg.final_image} {world.park.closing_view}."
    )
    world.say(
        f"{hero.id} and {friend.id} walked home knowing that a small kind deed can sound tiny at first and still grow as huge as legend."
    )
    world.say(bush_cfg.lesson_line)
    world.facts["resolved"] = world.get("bush").meters["helped"] >= THRESHOLD


def tell(
    park: Park,
    window_cfg: Window,
    bush_cfg: Bush,
    act_cfg: KindAct,
    hero_name: str,
    hero_gender: str,
    friend_name: str,
    friend_gender: str,
    trait: str,
) -> World:
    world = World(park)
    hero = world.add(Entity(hero_name, "character", hero_gender, hero_name, role="hero", traits=[trait]))
    friend = world.add(Entity(friend_name, "character", friend_gender, friend_name, role="friend"))
    window_ent = world.add(
        Entity("window", "thing", "window", "wobbly window", tags={"window", "sound", "park"})
    )
    bush_ent = world.add(
        Entity("bush", "thing", "bush", "wondrous bush", tags=set(bush_cfg.tags))
    )
    act_ent = world.add(
        Entity("act", "plan", "kind_act", act_cfg.label, tags=set(act_cfg.tags))
    )
    bush_ent.meters["needs_help"] = 1

    world.facts.update(
        park=park,
        window_cfg=window_cfg,
        bush_cfg=bush_cfg,
        act_cfg=act_cfg,
        hero=hero,
        friend=friend,
    )

    introduce(world, hero, friend, window_cfg, bush_cfg)
    stir_window(world, window_ent, window_cfg)

    world.para()
    hear_murmur(world, hero, friend, bush_cfg)
    inspect_need(world, hero, friend, bush_cfg, act_cfg)

    world.para()
    do_kindness(world, hero, friend, act_ent, act_cfg)
    reveal_magic(world, bush_cfg, act_cfg)
    close_story(world, hero, friend, bush_cfg)
    return world


def generation_prompts(world: World) -> list[str]:
    bush_cfg: Bush = world.facts["bush_cfg"]  # type: ignore[assignment]
    act_cfg: KindAct = world.facts["act_cfg"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]
    return [
        'Write a tall tale for young children set in a neighborhood park that includes the words "murmur," "wobbly window," and "wondrous bush."',
        f"Tell a magical kindness story where {hero.id} and {friend.id} hear a murmur through a wobbly window and discover that {bush_cfg.phrase} needs help.",
        f"Write a funny, warm tall tale where children choose to {act_cfg.label} and the park answers with impossible-looking magic.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]
    bush_cfg: Bush = world.facts["bush_cfg"]  # type: ignore[assignment]
    act_cfg: KindAct = world.facts["act_cfg"]  # type: ignore[assignment]
    window_cfg: Window = world.facts["window_cfg"]  # type: ignore[assignment]
    park: Park = world.facts["park"]  # type: ignore[assignment]
    items = [
        (
            "What did the children hear first?",
            f"They first heard a murmur carried by {window_cfg.phrase}. The loose glass made the bush's small plea sound big enough to stop them in the path.",
        ),
        (
            "What trouble was the wondrous bush in?",
            f"The wondrous bush needed help because {bush_cfg.need_line.rstrip('.').lower()}. That was the real cause of the strange voice.",
        ),
        (
            "How did kindness change the story?",
            f"{hero.id} and {friend.id} chose to {act_cfg.label} instead of turning the murmur into a scary rumor. Their kind action fixed the bush's problem and let the magic answer appear.",
        ),
        (
            "Why is the wobbly window important?",
            f"The wobbly window carried the sound from the bush to the children. Without that shaky pane, they might never have noticed the quiet need waiting in {park.place}.",
        ),
    ]
    if world.facts.get("resolved"):
        items.append(
            (
                "What happened after the children helped?",
                f"After they helped, {bush_cfg.magic_line[0].lower() + bush_cfg.magic_line[1:]} That shining change proved the murmur had been real and friendly.",
            )
        )
    return items


KNOWLEDGE = {
    "window": [
        (
            "Why can a loose window change a sound?",
            "A loose window can rattle, echo, or point a sound in a new direction. That can make a tiny noise seem larger or clearer than it first was.",
        )
    ],
    "kindness": [
        (
            "Why is kindness a good first answer to a mystery?",
            "Kindness slows people down and helps them look closely. When someone stays gentle, they often notice the real problem instead of inventing a frightening one.",
        )
    ],
    "magic": [
        (
            "What makes magic feel believable in a story?",
            "Story magic feels believable when it grows out of what just happened. A kind action can lead to a marvelous result that also shows the change clearly.",
        )
    ],
    "water": [
        (
            "Why do plant roots need water?",
            "Roots drink water from the soil to help a plant stay alive and upright. Dry roots make leaves and fruit droop or weaken.",
        )
    ],
    "patience": [
        (
            "Why does patience help with tangles?",
            "Patience helps because quick pulling usually makes a knot tighter. Slow hands can find where the snag begins and loosen it safely.",
        )
    ],
    "care": [
        (
            "Why should a branch be tied softly?",
            "A soft tie holds the branch up without scraping its bark. Good care supports a plant while protecting the living part of it.",
        )
    ],
    "nest": [
        (
            "Why should people be careful near a bird nest?",
            "Bird nests hold eggs or young birds that can be startled easily. Careful movement keeps the nest steady and the birds safe.",
        )
    ],
}

KNOWLEDGE_ORDER = ["window", "kindness", "magic", "water", "patience", "care", "nest"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    bush_cfg: Bush = world.facts["bush_cfg"]  # type: ignore[assignment]
    act_cfg: KindAct = world.facts["act_cfg"]  # type: ignore[assignment]
    tags = {"window", "kindness", "magic"} | set(bush_cfg.tags) | set(act_cfg.tags)
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(KNOWLEDGE[key])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    lines.extend(f"{idx}. {prompt}" for idx, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story world ==")
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        parts = [f"{ent.id:8} ({ent.type:10})"]
        if ent.role:
            parts.append(f"role={ent.role}")
        if ent.traits:
            parts.append(f"traits={ent.traits}")
        if ent.tags:
            parts.append(f"tags={sorted(ent.tags)}")
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        lines.append("  " + " ".join(parts))
    lines.append(f"  fired rules: {sorted(name for name, *_ in world.fired)}")
    lines.append("  history:")
    for item in world.history:
        bits = ", ".join(f"{k}={v}" for k, v in item.items())
        lines.append(f"    - {bits}")
    return "\n".join(lines)


CURATED = [
    StoryParams("maple_patch", "shed_window", "bellberry", "water_roots", "Mina", "girl", "Theo", "boy", "kind"),
    StoryParams("chestnut_loop", "kiosk_window", "ribbonthorn", "untangle_kite", "Owen", "boy", "Lila", "girl", "careful"),
    StoryParams("poppy_lane", "greenhouse_window", "lanternlaurel", "brace_branch", "Nora", "girl", "Eli", "boy", "steady"),
    StoryParams("maple_patch", "greenhouse_window", "bellberry", "water_roots", "Jules", "boy", "Pia", "girl", "bright-eyed"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PARKS[params.park],
        WINDOWS[params.window],
        BUSHES[params.bush],
        ACTS[params.act],
        params.hero,
        params.hero_gender,
        params.friend,
        params.friend_gender,
        params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


ASP_RULES = r"""
host(P,L)            :- supports(P,L).
window_working(W,B)  :- hears_need(W,N), bush_need(B,N).
act_working(A,B)     :- supports_need(A,N), bush_need(B,N).
valid(P,W,B,A)       :- park(P), window(W), bush(B), act(A),
                        window_loc(W,WL), bush_loc(B,BL),
                        host(P,WL), host(P,BL),
                        window_working(W,B),
                        act_working(A,B).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for park_id, park in PARKS.items():
        lines.append(asp.fact("park", park_id))
        for location in sorted(park.supports):
            lines.append(asp.fact("supports", park_id, location))
    for window_id, window in WINDOWS.items():
        lines.append(asp.fact("window", window_id))
        lines.append(asp.fact("window_loc", window_id, window.location))
        for need in sorted(window.hears):
            lines.append(asp.fact("hears_need", window_id, need))
    for bush_id, bush in BUSHES.items():
        lines.append(asp.fact("bush", bush_id))
        lines.append(asp.fact("bush_loc", bush_id, bush.location))
        lines.append(asp.fact("bush_need", bush_id, bush.need))
    for act_id, act in ACTS.items():
        lines.append(asp.fact("act", act_id))
        for need in sorted(act.supports):
            lines.append(asp.fact("supports_need", act_id, need))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str, str]]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def _verify_story_sample(sample: StorySample) -> list[str]:
    problems: list[str] = []
    story = sample.story
    if "murmur" not in story.lower():
        problems.append("story is missing 'murmur'")
    if "wobbly window" not in story.lower():
        problems.append("story is missing 'wobbly window'")
    if "wondrous bush" not in story.lower():
        problems.append("story is missing 'wondrous bush'")
    if "park" not in story.lower():
        problems.append("story is missing neighborhood park grounding")
    if story.count("\n\n") < 2:
        problems.append("story should have at least three paragraphs")
    if not sample.story_qa or not sample.world_qa or not sample.prompts:
        problems.append("qa/prompt sections are incomplete")
    world = sample.world
    if world is None:
        problems.append("sample is missing world trace")
    else:
        bush = world.get("bush")
        if bush.meters["helped"] < THRESHOLD:
            problems.append("bush was not actually helped")
        if bush.memes["magic"] < THRESHOLD:
            problems.append("magic resolution did not fire")
        if not world.facts.get("resolved"):
            problems.append("world did not mark itself resolved")
    return problems


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    status = 0
    if python_set != clingo_set:
        print("MISMATCH between Python gate and ASP gate:")
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        status = 1
    else:
        print(f"OK: ASP gate matches Python gate ({len(python_set)} combos).")

    exercise = CURATED + [
        StoryParams(park, window, bush, act, "Mina", "girl", "Owen", "boy", "kind")
        for park, window, bush, act in valid_combos()[:4]
    ]
    for params in exercise:
        sample = generate(params)
        problems = _verify_story_sample(sample)
        if problems:
            print(
                f"VERIFY FAILED for {(params.park, params.window, params.bush, params.act)}:"
            )
            for item in problems:
                print(f"  - {item}")
            status = 1
    if status == 0:
        print(f"OK: exercised {len(exercise)} generated stories.")
    return status


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Story world: murmur, wobbly window, wondrous bush, neighborhood park."
    )
    parser.add_argument("--park", choices=sorted(PARKS))
    parser.add_argument("--window", choices=sorted(WINDOWS))
    parser.add_argument("--bush", choices=sorted(BUSHES))
    parser.add_argument("--act", choices=sorted(ACTS))
    parser.add_argument("--hero")
    parser.add_argument("--hero-gender", choices=["girl", "boy"])
    parser.add_argument("--friend")
    parser.add_argument("--friend-gender", choices=["girl", "boy"])
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)

    if args.show_asp:
        print(asp_program())
        return 0
    if args.verify:
        return asp_verify()
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (park, window, bush, act) combos:\n")
        for combo in combos:
            print("  " + " ".join(f"{part:18}" for part in combo))
        return 0

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 60):
            seed = base_seed + attempts
            attempts += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return 1
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
        if len(samples) < args.n:
            print(f"(Only found {len(samples)} unique stories for the requested constraints.)")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return 0

    for idx, sample in enumerate(samples):
        params = sample.params
        header = ""
        if args.all:
            header = f"### {params.hero} & {params.friend}: {params.window}, {params.bush}, {params.act}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
