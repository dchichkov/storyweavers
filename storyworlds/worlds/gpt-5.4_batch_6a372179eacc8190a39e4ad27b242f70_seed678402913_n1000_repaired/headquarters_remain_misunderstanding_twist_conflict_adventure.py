#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/headquarters_remain_misunderstanding_twist_conflict_adventure.py
============================================================================================

A standalone storyworld for a small adventure tale about a children's club, a
headquarters, and a note that says one scout must remain behind. The conflict is
driven by a misunderstanding of that note; the twist is that the child who
remains at headquarters becomes the one who notices the true clue.

The world model prefers plausible little adventures over broad coverage:
a route is only valid when it can really be seen from the chosen headquarters
and the chosen signal can really mark that route. The Python reasonableness gate
has an inline ASP twin, and --verify checks parity and also runs a smoke test.

Run it
------
    python storyworlds/worlds/gpt-5.4/headquarters_remain_misunderstanding_twist_conflict_adventure.py
    python storyworlds/worlds/gpt-5.4/headquarters_remain_misunderstanding_twist_conflict_adventure.py --headquarters treehouse --route creek_path
    python storyworlds/worlds/gpt-5.4/headquarters_remain_misunderstanding_twist_conflict_adventure.py --signal lantern_flash
    python storyworlds/worlds/gpt-5.4/headquarters_remain_misunderstanding_twist_conflict_adventure.py --all
    python storyworlds/worlds/gpt-5.4/headquarters_remain_misunderstanding_twist_conflict_adventure.py --qa --json
    python storyworlds/worlds/gpt-5.4/headquarters_remain_misunderstanding_twist_conflict_adventure.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from contextlib import redirect_stdout
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
    phrase: str = ""
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
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(
            self.type, self.type
        )


@dataclass
class Headquarters:
    id: str
    label: str
    phrase: str
    view_zone: str
    detail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Route:
    id: str
    label: str
    phrase: str
    zone: str
    landmark: str
    treasure: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Signal:
    id: str
    label: str
    phrase: str
    zones: set[str]
    appearance: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Misread:
    id: str
    wrong_belief: str
    protest: str
    correction: str
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


def _r_notice_signal(world: World) -> list[str]:
    watcher = world.entities.get("watcher")
    hq = world.entities.get("hq")
    route = world.entities.get("route")
    signal = world.entities.get("signal")
    if not watcher or not hq or not route or not signal:
        return []
    if watcher.attrs.get("place") != "hq":
        return []
    if signal.meters["raised"] < THRESHOLD:
        return []
    if hq.attrs.get("view_zone") != route.attrs.get("zone"):
        return []
    if route.attrs.get("zone") not in signal.attrs.get("zones", set()):
        return []
    sig = ("notice_signal", hq.id, route.id, signal.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    watcher.memes["certainty"] += 1
    world.facts["true_route_seen"] = True
    return ["__signal__"]


def _r_ring_recall(world: World) -> list[str]:
    seeker = world.entities.get("seeker")
    if not seeker:
        return []
    if world.facts.get("bell_rung") is not True:
        return []
    if seeker.attrs.get("place") != "wrong_path":
        return []
    sig = ("bell_recall", seeker.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    seeker.attrs["place"] = "hq"
    seeker.memes["relief"] += 1
    seeker.memes["embarrassment"] += 1
    world.facts["recalled"] = True
    return ["__recall__"]


CAUSAL_RULES = [
    Rule(name="notice_signal", tag="physical", apply=_r_notice_signal),
    Rule(name="ring_recall", tag="social", apply=_r_ring_recall),
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
                produced.extend(out)
    if narrate:
        for item in produced:
            if not item.startswith("__"):
                world.say(item)
    return produced


HEADQUARTERS = {
    "treehouse": Headquarters(
        id="treehouse",
        label="treehouse headquarters",
        phrase="a creaky treehouse headquarters with a rope ladder and a tin bell",
        view_zone="creek",
        detail="From the little window they could see the creek shimmer between the reeds.",
        tags={"headquarters", "treehouse", "lookout"},
    ),
    "boathouse_loft": Headquarters(
        id="boathouse_loft",
        label="boathouse headquarters",
        phrase="a boathouse loft headquarters smelling of rope and salt",
        view_zone="dunes",
        detail="The loft door looked over the dune path and the strip of bright sea beyond it.",
        tags={"headquarters", "boathouse", "lookout"},
    ),
    "clocktower_nook": Headquarters(
        id="clocktower_nook",
        label="clocktower headquarters",
        phrase="a tiny clocktower headquarters above the village square",
        view_zone="orchard",
        detail="From up there they could spy the old orchard gate and the field behind it.",
        tags={"headquarters", "tower", "lookout"},
    ),
}

ROUTES = {
    "creek_path": Route(
        id="creek_path",
        label="creek path",
        phrase="the narrow creek path",
        zone="creek",
        landmark="the willow by the creek bend",
        treasure="a biscuit tin full of explorer badges",
        tags={"creek", "path", "adventure"},
    ),
    "dune_trail": Route(
        id="dune_trail",
        label="dune trail",
        phrase="the windy dune trail",
        zone="dunes",
        landmark="the leaning driftwood post",
        treasure="a canvas satchel with a brass compass inside",
        tags={"dunes", "trail", "adventure"},
    ),
    "orchard_gate": Route(
        id="orchard_gate",
        label="orchard gate",
        phrase="the orchard gate trail",
        zone="orchard",
        landmark="the striped gate at the edge of the orchard",
        treasure="a red box with lemon cakes and a note of congratulations",
        tags={"orchard", "gate", "adventure"},
    ),
}

SIGNALS = {
    "blue_flag": Signal(
        id="blue_flag",
        label="blue flag",
        phrase="a blue flag tied low at the true start",
        zones={"creek", "orchard"},
        appearance="a strip of blue cloth snapping in the air",
        tags={"flag", "signal"},
    ),
    "lantern_flash": Signal(
        id="lantern_flash",
        label="lantern flash",
        phrase="a shaded lantern that blinked once from the real trail",
        zones={"dunes"},
        appearance="one brief gold blink against the pale boards",
        tags={"lantern", "signal"},
    ),
    "kite_tail": Signal(
        id="kite_tail",
        label="kite tail",
        phrase="a small kite tail caught on the marker branch",
        zones={"creek", "dunes"},
        appearance="a bright tail fluttering where the wind touched it",
        tags={"kite", "signal"},
    ),
}

MISREADS = {
    "stuck_here": Misread(
        id="stuck_here",
        wrong_belief='that "remain at headquarters" meant the club was supposed to stay there all afternoon',
        protest='"That is not an adventure. That is just sitting still in our clubhouse."',
        correction='The note did not say everybody had to stay forever. It only said one scout should remain and watch.',
        tags={"misunderstanding", "conflict"},
    ),
    "treasure_here": Misread(
        id="treasure_here",
        wrong_belief='that "remain at headquarters" meant the prize itself was hidden inside headquarters',
        protest='"If the prize will remain here, why would we even go outside?"',
        correction='The note was about a scout remaining behind, not the treasure waiting in a corner.',
        tags={"misunderstanding", "conflict"},
    ),
    "stay_behind_unfair": Misread(
        id="stay_behind_unfair",
        wrong_belief='that the note was an unfair trick that would make one child miss the whole expedition',
        protest='"So one of us gets left out? That is not fair at all."',
        correction='The watcher was not being left out. The watcher was part of the plan and would see the clue first.',
        tags={"misunderstanding", "conflict"},
    ),
}


def valid_combo(headquarters_id: str, route_id: str, signal_id: str) -> bool:
    if headquarters_id not in HEADQUARTERS or route_id not in ROUTES or signal_id not in SIGNALS:
        return False
    hq = HEADQUARTERS[headquarters_id]
    route = ROUTES[route_id]
    signal = SIGNALS[signal_id]
    return hq.view_zone == route.zone and route.zone in signal.zones


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for headquarters_id in HEADQUARTERS:
        for route_id in ROUTES:
            for signal_id in SIGNALS:
                if valid_combo(headquarters_id, route_id, signal_id):
                    out.append((headquarters_id, route_id, signal_id))
    return out


def outcome_of(temper: str) -> str:
    if temper not in {"hasty", "steady"}:
        raise StoryError(f"(Unknown temper: {temper})")
    return "rush" if temper == "hasty" else "reread"


@dataclass
class StoryParams:
    headquarters: str
    route: str
    signal: str
    misread: str
    seeker: str
    seeker_gender: str
    watcher: str
    watcher_gender: str
    mentor: str
    temper: str
    keepsake: str = ""
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        headquarters="treehouse",
        route="creek_path",
        signal="blue_flag",
        misread="treasure_here",
        seeker="Tom",
        seeker_gender="boy",
        watcher="Lily",
        watcher_gender="girl",
        mentor="mother",
        temper="steady",
        keepsake="a stubby blue pencil",
    ),
    StoryParams(
        headquarters="boathouse_loft",
        route="dune_trail",
        signal="lantern_flash",
        misread="stay_behind_unfair",
        seeker="Max",
        seeker_gender="boy",
        watcher="Nora",
        watcher_gender="girl",
        mentor="father",
        temper="hasty",
        keepsake="a striped shell",
    ),
    StoryParams(
        headquarters="clocktower_nook",
        route="orchard_gate",
        signal="blue_flag",
        misread="stuck_here",
        seeker="Mia",
        seeker_gender="girl",
        watcher="Ben",
        watcher_gender="boy",
        mentor="aunt",
        temper="steady",
        keepsake="a silver whistle",
    ),
    StoryParams(
        headquarters="treehouse",
        route="creek_path",
        signal="kite_tail",
        misread="stay_behind_unfair",
        seeker="Eli",
        seeker_gender="boy",
        watcher="Zoe",
        watcher_gender="girl",
        mentor="uncle",
        temper="hasty",
        keepsake="a smooth skipping stone",
    ),
]


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    girl_names = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
    boy_names = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (girl_names if gender == "girl" else boy_names) if n != avoid]
    return rng.choice(pool), gender


def describe_note(route: Route, signal: Signal) -> str:
    return (
        f'"One scout must remain at headquarters. '
        f'When you see {signal.label.replace("_", " ") if "_" in signal.label else signal.label}, '
        f'start at {route.landmark}."'
    )


def introduce(world: World, seeker: Entity, watcher: Entity, hq: Headquarters) -> None:
    for child in (seeker, watcher):
        child.memes["eagerness"] += 1
    world.say(
        f"{seeker.id} and {watcher.id} called {hq.phrase} their headquarters. "
        f"They kept a hand-drawn map there, a biscuit tin of string, and one brave-looking bell."
    )
    world.say(hq.detail)


def mission(world: World, seeker: Entity, watcher: Entity, mentor: Entity, route: Route, signal: Signal) -> None:
    world.say(
        f"That afternoon, their {mentor.label_word} left a test for the Explorer Club: "
        f"find the hidden prize by following the right trail and not just the first trail that looked exciting."
    )
    world.say(
        f"On the table was a note that read {describe_note(route, signal)}"
    )
    world.facts["note_text"] = describe_note(route, signal)


def misunderstanding(world: World, seeker: Entity, watcher: Entity, misread: Misread) -> None:
    seeker.memes["confusion"] += 1
    seeker.memes["frustration"] += 1
    watcher.memes["worry"] += 1
    world.say(
        f"{seeker.id} frowned and decided {misread.wrong_belief}."
    )
    world.say(misread.protest)
    world.say(
        f'{watcher.id} shook {watcher.pronoun("possessive")} head. "{misread.correction}"'
    )


def argue(world: World, seeker: Entity, watcher: Entity) -> None:
    seeker.memes["conflict"] += 1
    watcher.memes["conflict"] += 1
    world.say(
        f"For one sharp minute, the two young scouts argued so hard that the bell on the wall trembled."
    )


def reread_note(world: World, seeker: Entity, watcher: Entity) -> None:
    seeker.memes["calm"] += 1
    watcher.memes["trust"] += 1
    seeker.memes["trust"] += 1
    world.say(
        f"At last {watcher.id} traced the words with one finger and read them slowly again."
    )
    world.say(
        f"{seeker.id} listened, cheeks warm, and heard the sentence the right way this time."
    )
    world.say(
        f'"All right," {seeker.id} said. "You remain at headquarters and watch. I will wait for your signal."'
    )


def take_posts(world: World, seeker: Entity, watcher: Entity, keepsake: str) -> None:
    watcher.attrs["place"] = "hq"
    seeker.attrs["place"] = "hq"
    if keepsake:
        world.say(
            f"To make the waiting feel official, {watcher.id} set {watcher.pronoun('possessive')} {keepsake} beside the map like a proper club token."
        )


def watcher_spots_signal(world: World, watcher: Entity, signal: Signal, route: Route) -> None:
    signal_ent = world.get("signal")
    signal_ent.meters["raised"] += 1
    propagate(world, narrate=False)
    watcher.memes["pride"] += 1
    world.say(
        f"Then the twist came. From the window, {watcher.id} saw {signal.appearance} near {route.landmark}."
    )
    world.say(
        f"The clue had never been hiding inside headquarters at all. The note needed a watcher so someone could spot the true start."
    )


def ring_and_send(world: World, watcher: Entity, seeker: Entity, route: Route) -> None:
    world.facts["bell_rung"] = True
    seeker.attrs["place"] = "hq"
    watcher.meters["bell"] += 1
    propagate(world, narrate=False)
    seeker.attrs["place"] = route.id
    watcher.attrs["place"] = route.id
    world.say(
        f'{watcher.id} rang the bell, and {seeker.id} came running to the ladder at once.'
    )
    world.say(
        f"Together they hurried to {route.landmark}, this time knowing exactly where the real trail began."
    )


def rush_wrong_way(world: World, seeker: Entity, watcher: Entity, route: Route) -> None:
    seeker.attrs["place"] = "wrong_path"
    watcher.attrs["place"] = "hq"
    seeker.memes["defiance"] += 1
    watcher.memes["worry"] += 1
    world.say(
        f"But {seeker.id} was too hot with feelings to wait. "
        f'{seeker.pronoun().capitalize()} darted down the first path {seeker.pronoun()} saw, sure that speed would beat careful reading.'
    )
    world.say(
        f"{watcher.id} stayed in headquarters because somebody had to keep faith with the note."
    )


def bell_recalls(world: World, watcher: Entity, seeker: Entity, route: Route) -> None:
    watcher_spots_signal(world, watcher, SIGNALS[world.facts["signal_id"]], route)
    world.facts["bell_rung"] = True
    watcher.meters["bell"] += 1
    world.say(
        f'{watcher.id} snatched the bell rope and rang until the sound skipped across the air.'
    )
    propagate(world, narrate=False)
    if world.facts.get("recalled"):
        world.say(
            f"Hearing the bell, {seeker.id} stopped, turned, and realized the wrong path had no signal at all."
        )
        world.say(
            f"{seeker.id} ran back, breathless and embarrassed, but also relieved that {watcher.id} had stayed sharp."
        )
    seeker.attrs["place"] = route.id
    watcher.attrs["place"] = route.id
    seeker.memes["trust"] += 1
    watcher.memes["trust"] += 1
    world.say(
        f"Then they set off side by side toward {route.landmark}, following the clue the proper way."
    )


def find_treasure(world: World, seeker: Entity, watcher: Entity, route: Route) -> None:
    world.say(
        f"Behind {route.landmark} they found {route.treasure}."
    )
    world.say(
        f"Inside was one more note: \"Best explorers do not race ahead. They watch, think, and help each other.\""
    )
    seeker.memes["lesson"] += 1
    watcher.memes["lesson"] += 1
    seeker.memes["joy"] += 1
    watcher.memes["joy"] += 1


def ending(world: World, seeker: Entity, watcher: Entity, mentor: Entity, hq: Headquarters) -> None:
    world.say(
        f"When they climbed back into {hq.label}, {mentor.label_word.capitalize()} was waiting with a proud smile."
    )
    world.say(
        f"{seeker.id} touched the note again and laughed a little at the old misunderstanding."
    )
    world.say(
        f"After that, whenever the Explorer Club planned a mission, one scout would remain at headquarters on purpose, "
        f"and the other would trust the watcher to help the adventure go right."
    )


def tell(
    headquarters: Headquarters,
    route: Route,
    signal: Signal,
    misread: Misread,
    seeker_name: str,
    seeker_gender: str,
    watcher_name: str,
    watcher_gender: str,
    mentor_type: str,
    temper: str,
    keepsake: str,
) -> World:
    world = World()
    seeker = world.add(
        Entity(
            id="seeker",
            kind="character",
            type=seeker_gender,
            label=seeker_name,
            phrase=seeker_name,
            role="seeker",
            attrs={"place": "hq", "display": seeker_name},
        )
    )
    watcher = world.add(
        Entity(
            id="watcher",
            kind="character",
            type=watcher_gender,
            label=watcher_name,
            phrase=watcher_name,
            role="watcher",
            attrs={"place": "hq", "display": watcher_name},
        )
    )
    mentor = world.add(
        Entity(
            id="mentor",
            kind="character",
            type=mentor_type,
            label="the grown-up",
            phrase="the grown-up",
            role="mentor",
        )
    )
    world.add(
        Entity(
            id="hq",
            kind="thing",
            type="headquarters",
            label=headquarters.label,
            phrase=headquarters.phrase,
            attrs={"view_zone": headquarters.view_zone},
            tags=set(headquarters.tags),
        )
    )
    world.add(
        Entity(
            id="route",
            kind="thing",
            type="route",
            label=route.label,
            phrase=route.phrase,
            attrs={"zone": route.zone, "landmark": route.landmark},
            tags=set(route.tags),
        )
    )
    world.add(
        Entity(
            id="signal",
            kind="thing",
            type="signal",
            label=signal.label,
            phrase=signal.phrase,
            attrs={"zones": set(signal.zones)},
            tags=set(signal.tags),
        )
    )

    introduce(world, seeker, watcher, headquarters)
    mission(world, seeker, watcher, mentor, route, signal)

    world.para()
    misunderstanding(world, seeker, watcher, misread)
    argue(world, seeker, watcher)
    take_posts(world, seeker, watcher, keepsake)

    world.para()
    branch = outcome_of(temper)
    if branch == "reread":
        reread_note(world, seeker, watcher)
        watcher_spots_signal(world, watcher, signal, route)
        ring_and_send(world, watcher, seeker, route)
    else:
        rush_wrong_way(world, seeker, watcher, route)
        bell_recalls(world, watcher, seeker, route)

    world.para()
    find_treasure(world, seeker, watcher, route)
    ending(world, seeker, watcher, mentor, headquarters)

    seeker_display = seeker.attrs.get("display", seeker.label or seeker.id)
    watcher_display = watcher.attrs.get("display", watcher.label or watcher.id)
    world.facts.update(
        seeker=seeker,
        watcher=watcher,
        seeker_name=seeker_display,
        watcher_name=watcher_display,
        mentor=mentor,
        headquarters_cfg=headquarters,
        route_cfg=route,
        signal_cfg=signal,
        misread_cfg=misread,
        temper=temper,
        outcome=branch,
        signal_seen=world.facts.get("true_route_seen", False),
        note_text=world.facts.get("note_text", ""),
        treasure=route.treasure,
        keepsake=keepsake,
        signal_id=signal.id,
    )
    return world


def story_text_name(entity: Entity) -> str:
    return entity.attrs.get("display", entity.label or entity.id)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    seeker = story_text_name(f["seeker"])
    watcher = story_text_name(f["watcher"])
    hq = f["headquarters_cfg"]
    route = f["route_cfg"]
    signal = f["signal_cfg"]
    misread = f["misread_cfg"]
    return [
        'Write a short adventure story for a 3-to-5-year-old that includes the words "headquarters" and "remain".',
        f"Tell a gentle adventure about two children in {hq.label} who argue because of a misunderstanding about a note, then solve the problem when the watcher sees {signal.label} near {route.landmark}.",
        f"Write an adventure with misunderstanding, conflict, and a twist: {seeker} thinks {misread.wrong_belief}, but {watcher} discovers the real clue from headquarters.",
    ]


KNOWLEDGE = {
    "headquarters": [
        (
            "What is a headquarters?",
            "A headquarters is the main place a team uses to plan and meet. It is where people keep maps, tools, and ideas before they set off.",
        )
    ],
    "signal": [
        (
            "What is a signal?",
            "A signal is a sign that tells someone something important, like where to go or when to start. It helps people work together even when they are not standing side by side.",
        )
    ],
    "map": [
        (
            "Why do explorers use maps?",
            "Explorers use maps so they can find the right way instead of guessing. A map helps a team notice where they are and where they should go next.",
        )
    ],
    "bell": [
        (
            "Why would a bell help at a clubhouse or headquarters?",
            "A bell makes a strong sound that can carry farther than an ordinary voice. It helps call people back quickly when there is important news.",
        )
    ],
    "flag": [
        (
            "What is a flag used for in a game or adventure?",
            "A flag can mark a place or send a message from far away. Bright cloth is easy to notice when it moves in the wind.",
        )
    ],
    "lantern": [
        (
            "Why is a lantern flash easy to notice?",
            "A flash of light stands out quickly, especially if someone is watching for it. That makes it useful as a clue or signal.",
        )
    ],
    "kite": [
        (
            "Why can a kite tail make a good clue?",
            "A kite tail flutters when the wind catches it, so it can draw the eye from far away. That movement helps a watcher spot the right place.",
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone hears or reads something the wrong way. People can fix it by slowing down, asking questions, and checking the words again.",
        )
    ],
    "teamwork": [
        (
            "Why is teamwork important on an adventure?",
            "Teamwork helps people share jobs, notice more clues, and help each other when one person misses something. A team often does better than one person racing alone.",
        )
    ],
}

KNOWLEDGE_ORDER = [
    "headquarters",
    "signal",
    "map",
    "bell",
    "flag",
    "lantern",
    "kite",
    "misunderstanding",
    "teamwork",
]


def story_qa_items(world: World) -> list[tuple[str, str]]:
    f = world.facts
    seeker = story_text_name(f["seeker"])
    watcher = story_text_name(f["watcher"])
    mentor = f["mentor"]
    route = f["route_cfg"]
    signal = f["signal_cfg"]
    misread = f["misread_cfg"]
    outcome = f["outcome"]
    hq = f["headquarters_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two young scouts, {seeker} and {watcher}, and their {mentor.label_word}. The children treat {hq.label} like a real explorer base.",
        ),
        (
            "What did the note say?",
            f'The note said, {f["note_text"]} That message is what started the whole adventure and the whole misunderstanding.',
        ),
        (
            f"Why did {seeker} and {watcher} argue?",
            f"They argued because {seeker} thought {misread.wrong_belief}. {watcher} understood that one scout should remain at headquarters so the team would not miss the real clue.",
        ),
    ]
    if outcome == "reread":
        qa.append(
            (
                f"What was the twist in the story?",
                f"The twist was that the child who stayed behind saw the important clue first. From headquarters, {watcher} spotted {signal.appearance} near {route.landmark}, which proved the note had been right all along.",
            )
        )
        qa.append(
            (
                f"How did {seeker} and {watcher} solve the problem?",
                f"They solved it by reading the note again and giving each child a job. When {watcher} saw the signal, {watcher} rang the bell and both scouts followed the true trail together.",
            )
        )
    else:
        qa.append(
            (
                f"What happened when {seeker} rushed off?",
                f"{seeker} ran down the wrong path because strong feelings were pushing harder than careful reading. Then the bell from headquarters called {seeker} back, and that saved the adventure from going the wrong way.",
            )
        )
        qa.append(
            (
                f"What was the twist in the story?",
                f"The twist was that staying behind was the most important job, not the boring one. {watcher} saw {signal.appearance} near {route.landmark}, and that turned the watcher into the hero of the mission.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"The children found {f['treasure']} and learned to trust each other. After that, one scout would remain at headquarters on purpose so the next adventure could begin the right way.",
        )
    )
    return qa


def world_knowledge_qa_items(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"headquarters", "signal", "map", "bell", "misunderstanding", "teamwork"}
    signal = f["signal_cfg"]
    if signal.id == "blue_flag":
        tags.add("flag")
    elif signal.id == "lantern_flash":
        tags.add("lantern")
    elif signal.id == "kite_tail":
        tags.add("kite")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        attrs = {k: v for k, v in ent.attrs.items() if v not in ("", None, set())}
        bits: list[str] = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(headquarters_id: str, route_id: str, signal_id: str) -> str:
    if headquarters_id not in HEADQUARTERS:
        return f"(Unknown headquarters: {headquarters_id})"
    if route_id not in ROUTES:
        return f"(Unknown route: {route_id})"
    if signal_id not in SIGNALS:
        return f"(Unknown signal: {signal_id})"
    hq = HEADQUARTERS[headquarters_id]
    route = ROUTES[route_id]
    signal = SIGNALS[signal_id]
    if hq.view_zone != route.zone:
        return (
            f"(No story: {hq.label} looks toward the {hq.view_zone}, but {route.label} starts in the {route.zone}. "
            f"If the watcher cannot see the true trail from headquarters, the twist does not work.)"
        )
    if route.zone not in signal.zones:
        good = ", ".join(sorted(s.id for s in SIGNALS.values() if route.zone in s.zones))
        return (
            f"(No story: {signal.label} cannot mark the {route.label}. "
            f"Pick a signal that works in the {route.zone}, such as: {good}.)"
        )
    return "(No story: this combination is unreasonable.)"


ASP_RULES = r"""
valid(H, R, S) :- headquarters(H), route(R), signal(S), view_zone(H, Z), route_zone(R, Z), signal_zone(S, Z).

outcome(rush)   :- temper(hasty).
outcome(reread) :- temper(steady).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for hq in HEADQUARTERS.values():
        lines.append(asp.fact("headquarters", hq.id))
        lines.append(asp.fact("view_zone", hq.id, hq.view_zone))
    for route in ROUTES.values():
        lines.append(asp.fact("route", route.id))
        lines.append(asp.fact("route_zone", route.id, route.zone))
    for signal in SIGNALS.values():
        lines.append(asp.fact("signal", signal.id))
        for zone in sorted(signal.zones):
            lines.append(asp.fact("signal_zone", signal.id, zone))
    lines.append(asp.fact("temper", "steady"))
    lines.append("% temper fact is overridden in scenario-specific queries for outcome/1.")
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(temper: str) -> str:
    import asp

    if temper not in {"hasty", "steady"}:
        raise StoryError(f"(Unknown temper: {temper})")
    scenario = f"temper({temper}).\n"
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    if not atoms:
        return "?"
    return atoms[0][0]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Adventure storyworld: a headquarters note, a misunderstanding, a conflict, and a clue-spotted twist."
    )
    ap.add_argument("--headquarters", choices=HEADQUARTERS)
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--signal", choices=SIGNALS)
    ap.add_argument("--misread", choices=MISREADS)
    ap.add_argument("--temper", choices=["hasty", "steady"])
    ap.add_argument("--mentor", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.headquarters and args.route and args.signal:
        if not valid_combo(args.headquarters, args.route, args.signal):
            raise StoryError(explain_rejection(args.headquarters, args.route, args.signal))

    combos = [
        combo
        for combo in valid_combos()
        if (args.headquarters is None or combo[0] == args.headquarters)
        and (args.route is None or combo[1] == args.route)
        and (args.signal is None or combo[2] == args.signal)
    ]
    if not combos:
        if args.headquarters and args.route and args.signal:
            raise StoryError(explain_rejection(args.headquarters, args.route, args.signal))
        raise StoryError("(No valid combination matches the given options.)")

    headquarters_id, route_id, signal_id = rng.choice(sorted(combos))
    seeker_name, seeker_gender = _pick_child(rng)
    watcher_name, watcher_gender = _pick_child(rng, avoid=seeker_name)
    misread_id = args.misread or rng.choice(sorted(MISREADS))
    temper = args.temper or rng.choice(["hasty", "steady"])
    mentor = args.mentor or rng.choice(["mother", "father", "aunt", "uncle"])
    keepsake = rng.choice(
        [
            "a silver whistle",
            "a striped shell",
            "a stubby blue pencil",
            "a smooth skipping stone",
            "",
            "",
        ]
    )
    return StoryParams(
        headquarters=headquarters_id,
        route=route_id,
        signal=signal_id,
        misread=misread_id,
        seeker=seeker_name,
        seeker_gender=seeker_gender,
        watcher=watcher_name,
        watcher_gender=watcher_gender,
        mentor=mentor,
        temper=temper,
        keepsake=keepsake,
    )


def generate(params: StoryParams) -> StorySample:
    if params.headquarters not in HEADQUARTERS:
        raise StoryError(f"(Unknown headquarters: {params.headquarters})")
    if params.route not in ROUTES:
        raise StoryError(f"(Unknown route: {params.route})")
    if params.signal not in SIGNALS:
        raise StoryError(f"(Unknown signal: {params.signal})")
    if params.misread not in MISREADS:
        raise StoryError(f"(Unknown misread: {params.misread})")
    if params.temper not in {"hasty", "steady"}:
        raise StoryError(f"(Unknown temper: {params.temper})")
    if params.seeker == params.watcher:
        raise StoryError("(The two scouts must have different names.)")
    if not valid_combo(params.headquarters, params.route, params.signal):
        raise StoryError(explain_rejection(params.headquarters, params.route, params.signal))

    world = tell(
        headquarters=HEADQUARTERS[params.headquarters],
        route=ROUTES[params.route],
        signal=SIGNALS[params.signal],
        misread=MISREADS[params.misread],
        seeker_name=params.seeker,
        seeker_gender=params.seeker_gender,
        watcher_name=params.watcher,
        watcher_gender=params.watcher_gender,
        mentor_type=params.mentor,
        temper=params.temper,
        keepsake=params.keepsake,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[
            QAItem(question=question, answer=answer)
            for question, answer in story_qa_items(world)
        ],
        world_qa=[
            QAItem(question=question, answer=answer)
            for question, answer in world_knowledge_qa_items(world)
        ],
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


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    for temper in ["hasty", "steady"]:
        a = asp_outcome(temper)
        p = outcome_of(temper)
        if a == p:
            print(f"OK: outcome model matches for temper={temper} ({p}).")
        else:
            rc = 1
            print(f"MISMATCH in outcome model for temper={temper}: clingo={a} python={p}")

    try:
        sample = generate(CURATED[0])
        if not sample.story or "headquarters" not in sample.story or "remain" not in sample.story:
            raise StoryError("(Smoke test failed: generated story missing required seed words.)")
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample, trace=True, qa=True, header="### smoke")
        if not buf.getvalue().strip():
            raise StoryError("(Smoke test failed: emit produced no output.)")
        print("OK: smoke test passed for generate() and emit().")
    except Exception as err:
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
        print(f"{len(combos)} compatible (headquarters, route, signal) combos:\n")
        for headquarters_id, route_id, signal_id in combos:
            print(f"  {headquarters_id:15} {route_id:12} {signal_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.seeker} and {p.watcher}: {p.headquarters}, {p.route}, "
                f"{p.signal} ({outcome_of(p.temper)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
