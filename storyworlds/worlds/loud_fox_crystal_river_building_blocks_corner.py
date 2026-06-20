#!/usr/bin/env python3
"""Fairy-tale quest in a building blocks corner with a loud fox and a crystal river."""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Iterable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


SOURCE_TALE = (
    "In the building blocks corner, a loud fox had to cross a crystal river of blue "
    "blocks to fetch a treasure for a little block kingdom. His booming voice made "
    "the river banks shake, so every bridge slipped apart. When he remembered a soft "
    "rhyme and matched it with the right kind of bridge, the blocks held still, the "
    "quest was finished, and the corner looked like a tiny fairy kingdom at dusk."
)


@dataclass(frozen=True)
class FoxSpec:
    id: str
    name: str
    phrase: str
    cloak: str
    boast: str
    voice: int
    dream: str
    subject: str
    object: str
    possessive: str
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class RiverSpec:
    id: str
    phrase: str
    width: int
    echo: int
    fragility: int
    shimmer: str
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class QuestSpec:
    id: str
    prize: str
    goal_line: str
    ending_image: str
    fragility: int
    need: str
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class BridgeSpec:
    id: str
    phrase: str
    material: str
    span: int
    stability: int
    gentleness: int
    lay_line: str
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class RhymeSpec:
    id: str
    line1: str
    line2: str
    calm: int
    cadence: str
    effect: str
    tags: tuple[str, ...] = ()


@dataclass
class StoryParams:
    fox: str
    river: str
    quest: str
    bridge: str
    rhyme: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    phrase: str
    location: Optional[str] = None
    owner: Optional[str] = None
    meters: dict[str, int] = field(default_factory=dict)
    memes: dict[str, int] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)


@dataclass
class Event:
    id: str
    text: str
    actor: str
    target: Optional[str] = None
    meters: dict[str, int] = field(default_factory=dict)
    memes: dict[str, int] = field(default_factory=dict)


@dataclass
class StoryWorld:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def entity(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def record(
        self,
        event_id: str,
        text: str,
        actor: str,
        target: Optional[str] = None,
        meter_updates: Optional[dict[str, dict[str, int]]] = None,
        meme_updates: Optional[dict[str, dict[str, int]]] = None,
    ) -> None:
        meter_updates = meter_updates or {}
        meme_updates = meme_updates or {}
        for ent_id, changes in meter_updates.items():
            entity = self.entity(ent_id)
            for key, value in changes.items():
                entity.meters[key] = entity.meters.get(key, 0) + value
        for ent_id, changes in meme_updates.items():
            entity = self.entity(ent_id)
            for key, value in changes.items():
                entity.memes[key] = entity.memes.get(key, 0) + value
        self.history.append(
            Event(
                id=event_id,
                text=text,
                actor=actor,
                target=target,
                meters=copy.deepcopy(meter_updates),
                memes=copy.deepcopy(meme_updates),
            )
        )

    def render(self) -> str:
        return "\n\n".join(self.paragraphs)


FOXES: dict[str, FoxSpec] = {
    "cedar": FoxSpec(
        "cedar",
        "Cedar",
        "a loud fox with a copper tail",
        "a red felt cloak",
        '"Make way for the boldest builder!"',
        3,
        "to make the block kingdom cheer",
        "he",
        "him",
        "his",
        ("fox", "loud"),
    ),
    "juniper": FoxSpec(
        "juniper",
        "Juniper",
        "a loud fox with bright white paws",
        "a green ribbon scarf",
        '"Hear me, river! I will cross you in one jump!"',
        2,
        "to bring wonder back to the block throne",
        "she",
        "her",
        "her",
        ("fox", "loud"),
    ),
    "saffron": FoxSpec(
        "saffron",
        "Saffron",
        "a loud fox with a lantern-colored tail",
        "a gold paper crown",
        '"Stand aside, little blocks! A hero is coming through!"',
        3,
        "to prove that brave hearts could also be careful",
        "they",
        "them",
        "their",
        ("fox", "loud"),
    ),
}

RIVERS: dict[str, RiverSpec] = {
    "ribbon": RiverSpec(
        "ribbon",
        "a crystal river made of blue window blocks",
        3,
        2,
        1,
        "The blue pieces shone like bits of frozen sky.",
        ("river", "crystal"),
    ),
    "moonbend": RiverSpec(
        "moonbend",
        "a moon-bent crystal river of pale cubes",
        4,
        2,
        2,
        "Every pale cube held a moon-shaped gleam inside it.",
        ("river", "crystal", "wide"),
    ),
    "silverstep": RiverSpec(
        "silverstep",
        "a crystal river with silver stepping blocks under the blue shine",
        2,
        3,
        2,
        "Silver flashes skipped under the clear blue surface.",
        ("river", "crystal", "echo"),
    ),
}

QUESTS: dict[str, QuestSpec] = {
    "bell": QuestSpec(
        "bell",
        "the silver wishing bell",
        "so the small paper queen could ring in evening story time",
        "the bell chimed above the block castle like one bright star",
        1,
        "a steady trip home",
        ("bell", "quest"),
    ),
    "crown": QuestSpec(
        "crown",
        "the glass petal crown",
        "so the block kingdom could welcome its shy queen again",
        "the crown glimmered on the queen's head while the crystal river went still",
        2,
        "the gentlest paws in the room",
        ("crown", "fragile", "quest"),
    ),
    "lantern": QuestSpec(
        "lantern",
        "the moon lantern cube",
        "so the dim tower could glow before nap time shadows came",
        "the lantern cube turned the whole corner honey-gold",
        1,
        "a bridge that would not sway",
        ("lantern", "quest"),
    ),
}

BRIDGES: dict[str, BridgeSpec] = {
    "planks": BridgeSpec(
        "planks",
        "a bridge of flat silver planks",
        "flat silver planks",
        3,
        2,
        1,
        "Block by block, the flat silver planks reached from bank to bank.",
        ("bridge", "flat"),
    ),
    "arch": BridgeSpec(
        "arch",
        "a clear arch of long window blocks",
        "long clear window blocks",
        4,
        3,
        2,
        "Piece by piece, the long clear blocks rose into a shining arch.",
        ("bridge", "arch"),
    ),
    "stepping": BridgeSpec(
        "stepping",
        "a path of round stepping blocks",
        "round stepping blocks",
        2,
        1,
        3,
        "One by one, the round stepping blocks settled a careful paw-length apart.",
        ("bridge", "stepping"),
    ),
}

RHYMES: dict[str, RhymeSpec] = {
    "softsong": RhymeSpec(
        "softsong",
        "Soft paw, slow song,",
        "crystal hold strong.",
        2,
        "a hush-and-hold rhyme",
        "The rhyme made the fox breathe before each block touched down.",
        ("rhyme", "calm"),
    ),
    "moonhum": RhymeSpec(
        "moonhum",
        "Moon light, small and bright,",
        "keep my building true tonight.",
        1,
        "a moonlit humming rhyme",
        "The rhyme turned the fox's loud voice into a steady hum.",
        ("rhyme", "calm"),
    ),
    "riverrest": RhymeSpec(
        "riverrest",
        "River, rest under my feet,",
        "little blocks, stay calm and neat.",
        3,
        "a resting-river rhyme",
        "The rhyme quieted even the sharp clicks between the blocks.",
        ("rhyme", "calm", "strong"),
    ),
}


def _bridge_strength(bridge: BridgeSpec, rhyme: RhymeSpec) -> int:
    return bridge.stability + rhyme.calm


def _gentle_strength(bridge: BridgeSpec, rhyme: RhymeSpec) -> int:
    return bridge.gentleness + rhyme.calm


def _count_phrase(value: int, singular: str, plural: str) -> str:
    if value == 1:
        return f"1 {singular}"
    return f"{value} {plural}"


def valid_params(params: StoryParams) -> tuple[bool, str]:
    if params.fox not in FOXES:
        return False, f"unknown fox: {params.fox}"
    if params.river not in RIVERS:
        return False, f"unknown river: {params.river}"
    if params.quest not in QUESTS:
        return False, f"unknown quest: {params.quest}"
    if params.bridge not in BRIDGES:
        return False, f"unknown bridge: {params.bridge}"
    if params.rhyme not in RHYMES:
        return False, f"unknown rhyme: {params.rhyme}"

    river = RIVERS[params.river]
    quest = QUESTS[params.quest]
    bridge = BRIDGES[params.bridge]
    rhyme = RHYMES[params.rhyme]

    if bridge.span < river.width:
        return False, f"{bridge.phrase} is too short to cross {river.phrase}"
    if _bridge_strength(bridge, rhyme) < river.echo + river.fragility:
        return (
            False,
            f"{river.phrase} chatters too hard for {bridge.phrase} unless the fox uses a calmer build",
        )
    if _gentle_strength(bridge, rhyme) < quest.fragility + 1:
        return (
            False,
            f"{quest.prize} needs a gentler crossing than {bridge.phrase} and this rhyme can provide",
        )
    return True, ""


def all_params() -> list[StoryParams]:
    combos: list[StoryParams] = []
    for fox in FOXES:
        for river in RIVERS:
            for quest in QUESTS:
                for bridge in BRIDGES:
                    for rhyme in RHYMES:
                        params = StoryParams(fox=fox, river=river, quest=quest, bridge=bridge, rhyme=rhyme)
                        ok, _ = valid_params(params)
                        if ok:
                            combos.append(params)
    return combos


def make_world(params: StoryParams) -> StoryWorld:
    fox = FOXES[params.fox]
    river = RIVERS[params.river]
    quest = QUESTS[params.quest]
    bridge = BRIDGES[params.bridge]
    rhyme = RHYMES[params.rhyme]

    world = StoryWorld(params=params)
    world.add(
        Entity(
            "corner",
            "place",
            "the building blocks corner",
            "the building blocks corner",
            meters={"order": 3, "sparkle": 2},
            memes={"Wonder": 2},
            tags={"corner", "blocks", "fairy"},
        )
    )
    world.add(
        Entity(
            "hero",
            "character",
            fox.name,
            fox.phrase,
            location="corner",
            meters={"voice": fox.voice, "steps": 0},
            memes={"Bravery": 2, "Patience": 0, "Wonder": 2},
            tags=set(fox.tags),
        )
    )
    world.add(
        Entity(
            "river",
            "physical",
            "crystal river",
            river.phrase,
            location="corner",
            meters={"width": river.width, "echo": river.echo, "fragility": river.fragility, "wobble": 0},
            memes={"Beauty": 3},
            tags=set(river.tags),
        )
    )
    world.add(
        Entity(
            "prize",
            "physical",
            quest.prize,
            quest.prize,
            location="island",
            owner="queen",
            meters={"fragility": quest.fragility},
            memes={"Value": 2},
            tags=set(quest.tags),
        )
    )
    world.add(
        Entity(
            "bridge",
            "physical",
            bridge.phrase,
            bridge.phrase,
            location="corner",
            meters={"span": 0, "stability": 0, "gentleness": 0},
            tags=set(bridge.tags),
        )
    )
    world.add(
        Entity(
            "rhyme",
            "meme",
            rhyme.cadence,
            rhyme.cadence,
            location="hero",
            memes={"Calm": rhyme.calm},
            tags=set(rhyme.tags),
        )
    )
    world.facts["source_tale"] = SOURCE_TALE
    world.facts["setting"] = "building blocks corner"
    world.facts["quest_goal"] = quest.goal_line
    world.facts["ending_image"] = quest.ending_image
    world.facts["shimmer"] = river.shimmer
    world.facts["rhyme_lines"] = [rhyme.line1, rhyme.line2]
    return world


def begin_quest(world: StoryWorld) -> None:
    fox = FOXES[world.params.fox]
    quest = QUESTS[world.params.quest]
    river = RIVERS[world.params.river]
    world.record(
        "begin_quest",
        f"{fox.name} saw {quest.prize} waiting beyond {river.phrase} {quest.goal_line}.",
        "hero",
        "prize",
        meter_updates={"hero": {"steps": 1}},
        meme_updates={"hero": {"Bravery": 1, "Wonder": 1}},
    )


def loud_mistake(world: StoryWorld) -> None:
    fox = FOXES[world.params.fox]
    river = RIVERS[world.params.river]
    wobble = fox.voice + river.echo
    world.record(
        "loud_mistake",
        f"{fox.name} shouted {fox.boast}, and the bright river blocks rattled apart.",
        "hero",
        "river",
        meter_updates={"river": {"wobble": wobble}, "hero": {"voice": 0}},
        meme_updates={"hero": {"Patience": -1}},
    )
    world.entity("hero").meters["voice"] = fox.voice
    world.facts["loud_wobble"] = wobble


def remember_rhyme(world: StoryWorld) -> None:
    fox = FOXES[world.params.fox]
    rhyme = RHYMES[world.params.rhyme]
    river = world.entity("river")
    hero = world.entity("hero")
    quiet_voice = max(1, hero.meters["voice"] - rhyme.calm)
    wobble_drop = min(river.meters["wobble"], rhyme.calm + 1)
    world.record(
        "remember_rhyme",
        f"{fox.name} remembered {rhyme.cadence} and said it softly: \"{rhyme.line1} {rhyme.line2}\"",
        "hero",
        "rhyme",
        meter_updates={"river": {"wobble": -wobble_drop}},
        meme_updates={"hero": {"Patience": rhyme.calm, "Wonder": 1}, "corner": {"Wonder": 1}},
    )
    hero.meters["voice"] = quiet_voice
    world.facts["quiet_voice"] = quiet_voice
    world.facts["calm_wobble"] = river.meters["wobble"]


def build_bridge(world: StoryWorld) -> None:
    fox = FOXES[world.params.fox]
    bridge = BRIDGES[world.params.bridge]
    rhyme = RHYMES[world.params.rhyme]
    span = bridge.span
    stability = _bridge_strength(bridge, rhyme)
    gentleness = _gentle_strength(bridge, rhyme)
    world.record(
        "build_bridge",
        f"{fox.name} used {bridge.material} after the rhyme steadied the room.",
        "hero",
        "bridge",
        meter_updates={"bridge": {"span": span, "stability": stability, "gentleness": gentleness}, "hero": {"steps": 1}},
        meme_updates={"hero": {"Patience": 1}},
    )
    world.facts["bridge_line"] = bridge.lay_line


def cross_and_return(world: StoryWorld) -> None:
    fox = FOXES[world.params.fox]
    river = RIVERS[world.params.river]
    quest = QUESTS[world.params.quest]
    bridge = world.entity("bridge")
    hero = world.entity("hero")
    success = (
        bridge.meters["span"] >= river.width
        and bridge.meters["stability"] >= river.echo + river.fragility
        and bridge.meters["gentleness"] >= quest.fragility + 1
    )
    if not success:
        raise StoryError("the simulated quest did not resolve; the bridge state is not strong enough")

    world.record(
        "cross_and_return",
        f"{fox.name} crossed, lifted {quest.prize}, and carried it back without a crack or splash.",
        "hero",
        "prize",
        meter_updates={"hero": {"steps": 2}, "corner": {"sparkle": 1}},
        meme_updates={"hero": {"Bravery": 1, "Patience": 1}, "corner": {"Wonder": 1}},
    )
    world.entity("river").meters["wobble"] = min(world.entity("river").meters["wobble"], 1)
    hero.memes["Care"] = bridge.meters["gentleness"]
    world.facts["resolved"] = True


def render_story(world: StoryWorld) -> str:
    fox = FOXES[world.params.fox]
    river = RIVERS[world.params.river]
    quest = QUESTS[world.params.quest]
    bridge = BRIDGES[world.params.bridge]
    rhyme = RHYMES[world.params.rhyme]
    loud_wobble = int(world.facts["loud_wobble"])
    calm_wobble = int(world.facts["calm_wobble"])

    opening = (
        f"In the building blocks corner, where towers stood like tiny castle walls, "
        f"there lived {fox.phrase} named {fox.name}. {fox.subject.capitalize()} wore {fox.cloak}, "
        f"and {fox.possessive} heart held one bright wish: {fox.dream}."
    )
    quest_para = (
        f"That afternoon {fox.name} had a quest. "
        f"Across {river.phrase}, {quest.prize} waited on a little island of square gold blocks {quest.goal_line}. "
        f"{river.shimmer}"
    )
    tension = (
        f"But {fox.name} was a loud fox, and loudness was no friend to a crystal river. "
        f"When {fox.subject} cried {fox.boast}, the river answered with sharp bright clicks. "
        f"The banks wobbled {_count_phrase(loud_wobble, 'little shake', 'little shakes')}, and even the nearest path broke away."
    )
    turn = (
        f"For one small moment {fox.name} stood still. Then {fox.subject} remembered {rhyme.cadence}: "
        f"\"{rhyme.line1} {rhyme.line2}\" {rhyme.effect} "
        f"The wobble fell until only {_count_phrase(calm_wobble, 'soft tremor remained', 'soft tremors remained')}, and patience returned to {fox.possessive} paws."
    )
    crossing = (
        f"{world.facts['bridge_line']} Because {bridge.phrase} was long enough for the river and gentle enough for {quest.prize}, "
        f"it held fast under {fox.possessive} careful steps. {fox.name} reached the island, took up {quest.prize}, "
        f"and came home by the same shining way."
    )
    ending = (
        f"When the quest was done, {quest.ending_image}. Even {fox.name}'s voice sounded different then: "
        f"not like a crash, but like a brave drum played softly in a fairy hall."
    )
    world.paragraphs = [opening, quest_para, tension, turn, crossing, ending]
    return world.render()


def generation_prompts(world: StoryWorld) -> list[str]:
    fox = FOXES[world.params.fox]
    quest = QUESTS[world.params.quest]
    bridge = BRIDGES[world.params.bridge]
    rhyme = RHYMES[world.params.rhyme]
    return [
        'Write a Fairy Tale set in a building blocks corner that includes the words "loud fox" and "crystal river".',
        f"Give {fox.name} a quest to fetch {quest.prize}, and make the turning point come from a spoken rhyme instead of force.",
        f"Let the ending prove that {bridge.phrase} and {rhyme.cadence} changed the room as well as the hero.",
    ]


def story_qa(world: StoryWorld) -> list[tuple[str, str]]:
    fox = FOXES[world.params.fox]
    quest = QUESTS[world.params.quest]
    bridge = BRIDGES[world.params.bridge]
    rhyme = RHYMES[world.params.rhyme]
    river = RIVERS[world.params.river]
    wobble = int(world.facts["calm_wobble"])
    return [
        (
            f"Why was {fox.name}'s loud voice a problem at first?",
            f"{fox.name}'s loud voice shook the crystal river until the bright blocks rattled apart. That made the quest harder because no bridge could stay steady while the banks were wobbling.",
        ),
        (
            f"What changed when {fox.name} said the rhyme?",
            f"The rhyme changed the room by quieting the fox and calming the crystal river. After that, only {_count_phrase(wobble, 'soft tremor was left', 'soft tremors were left')}, so careful building finally worked.",
        ),
        (
            "How did the fox cross the river?",
            f"{fox.name} crossed on {bridge.phrase}. It worked because the bridge was strong enough for {river.phrase} and gentle enough to carry {quest.prize} home safely.",
        ),
        (
            f"How did the quest end?",
            f"The quest ended with {fox.name} bringing back {quest.prize}. In the final image, {quest.ending_image}, which shows that the whole building blocks corner changed after the careful crossing.",
        ),
    ]


KNOWLEDGE: dict[str, list[tuple[str, str]]] = {
    "fox": [
        (
            "Why might a loud animal need to speak more softly while building?",
            "Soft sounds cause less shaking and less distraction. That helps careful paws or hands place pieces where they belong.",
        )
    ],
    "crystal": [
        (
            "Why do clear blocks seem magical in a child-sized story?",
            "Clear blocks catch light and send it through the room. That makes ordinary play pieces look like treasure or water in a fairy tale.",
        )
    ],
    "wide": [
        (
            "Why does a wider river need a longer bridge?",
            "A bridge must reach all the way from one side to the other. If it is too short, the traveler still has a gap to cross."
        )
    ],
    "fragile": [
        (
            "Why must someone carry a crown or glass-like toy gently?",
            "Fragile things can chip or fall if they sway too much. Gentle steps protect them on the way home.",
        )
    ],
    "bridge": [
        (
            "What makes a block bridge feel safe?",
            "A safe bridge is long enough to reach, stable enough not to slide, and calm enough for careful steps. When all three are true, a crossing feels trustworthy.",
        )
    ],
    "rhyme": [
        (
            "How can a rhyme help in a story even when it is not magic?",
            "A rhyme gives the hero a steady pattern to follow. That can slow breathing, focus attention, and turn a wild moment into a careful one.",
        )
    ],
}

KNOWLEDGE_ORDER = ["fox", "crystal", "wide", "fragile", "bridge", "rhyme"]


def world_knowledge_qa(world: StoryWorld) -> list[tuple[str, str]]:
    tags: set[str] = {"bridge", "rhyme"}
    tags |= world.entity("hero").tags
    tags |= world.entity("river").tags
    tags |= world.entity("prize").tags
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def dump_trace(world: StoryWorld) -> str:
    lines = ["--- world trace ---"]
    for event in world.history:
        lines.append(f"- {event.id}: {event.text}")
    lines.append("")
    lines.append("--- entity state ---")
    for entity_id in ["hero", "river", "bridge", "prize", "corner", "rhyme"]:
        entity = world.entity(entity_id)
        lines.append(
            f"{entity.id}: kind={entity.kind} meters={entity.meters} memes={entity.memes} location={entity.location}"
        )
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Knowledge QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def tell(params: StoryParams) -> StoryWorld:
    ok, reason = valid_params(params)
    if not ok:
        raise StoryError(reason)
    world = make_world(params)
    begin_quest(world)
    loud_mistake(world)
    remember_rhyme(world)
    build_bridge(world)
    cross_and_return(world)
    render_story(world)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


ASP_RULES = r"""
valid(F, R, Q, B, H) :-
    fox(F), river(R), quest(Q), bridge(B), rhyme(H),
    span(B, S), width(R, W), S >= W,
    stability(B, BS), calm(H, HC), echo(R, E), river_fragility(R, RF), BS + HC >= E + RF,
    gentleness(B, BG), prize_fragility(Q, PF), BG + HC >= PF + 1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for fox in FOXES:
        lines.append(asp.fact("fox", fox))
    for river_id, river in RIVERS.items():
        lines.append(asp.fact("river", river_id))
        lines.append(asp.fact("width", river_id, river.width))
        lines.append(asp.fact("echo", river_id, river.echo))
        lines.append(asp.fact("river_fragility", river_id, river.fragility))
    for quest_id, quest in QUESTS.items():
        lines.append(asp.fact("quest", quest_id))
        lines.append(asp.fact("prize_fragility", quest_id, quest.fragility))
    for bridge_id, bridge in BRIDGES.items():
        lines.append(asp.fact("bridge", bridge_id))
        lines.append(asp.fact("span", bridge_id, bridge.span))
        lines.append(asp.fact("stability", bridge_id, bridge.stability))
        lines.append(asp.fact("gentleness", bridge_id, bridge.gentleness))
    for rhyme_id, rhyme in RHYMES.items():
        lines.append(asp.fact("rhyme", rhyme_id))
        lines.append(asp.fact("calm", rhyme_id, rhyme.calm))
    return "\n".join(lines)


def asp_program(show_clause: str = "#show valid/5.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show_clause}\n"


def asp_valid_combos() -> list[tuple[str, str, str, str, str]]:
    import asp

    model = asp.one_model(asp_program())
    combos = sorted(set(asp.atoms(model, "valid")))
    return [(str(a), str(b), str(c), str(d), str(e)) for a, b, c, d, e in combos]


def verify() -> int:
    rc = 0
    py = {(p.fox, p.river, p.quest, p.bridge, p.rhyme) for p in all_params()}
    asp_set = set(asp_valid_combos())
    if py != asp_set:
        rc = 1
        print("MISMATCH between Python and ASP validity gates.")
        if py - asp_set:
            print("  only in Python:", sorted(py - asp_set)[:10])
        if asp_set - py:
            print("  only in ASP:", sorted(asp_set - py)[:10])
    else:
        print(f"OK: Python and ASP agree on {len(py)} valid loud-fox quest combos.")

    for params in all_params():
        sample = generate(params)
        if "building blocks corner" not in sample.story:
            rc = 1
            print("Missing setting phrase in story:", params)
            break
        if "crystal river" not in sample.story:
            rc = 1
            print("Missing seed phrase in story:", params)
            break
        if len(sample.story_qa) < 3 or len(sample.world_qa) < 2:
            rc = 1
            print("QA generation too thin:", params)
            break
    if rc == 0:
        print("OK: every valid combination generates a complete story and grounded QA.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fox", choices=sorted(FOXES))
    parser.add_argument("--river", choices=sorted(RIVERS))
    parser.add_argument("--quest", choices=sorted(QUESTS))
    parser.add_argument("--bridge", choices=sorted(BRIDGES))
    parser.add_argument("--rhyme", choices=sorted(RHYMES))
    parser.add_argument("-n", type=int, default=1, help="number of stories to generate")
    parser.add_argument("--all", action="store_true", help="render every valid parameter combination")
    parser.add_argument("--seed", type=int, default=19, help="base seed for deterministic sampling")
    parser.add_argument("--trace", action="store_true", help="dump the world-model trace after each story")
    parser.add_argument("--qa", action="store_true", help="include prompts, story QA, and world-knowledge QA")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of plain text")
    parser.add_argument("--asp", action="store_true", help="list valid parameter combinations from the ASP twin")
    parser.add_argument("--verify", action="store_true", help="check ASP/Python parity and exercise generation")
    parser.add_argument("--show-asp", action="store_true", help="print the complete ASP program")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if all(
        value is not None
        for value in (args.fox, args.river, args.quest, args.bridge, args.rhyme)
    ):
        params = StoryParams(
            fox=args.fox,
            river=args.river,
            quest=args.quest,
            bridge=args.bridge,
            rhyme=args.rhyme,
            seed=args.seed,
        )
        ok, reason = valid_params(params)
        if not ok:
            raise StoryError(reason)
        return params

    combos = [
        combo
        for combo in all_params()
        if (args.fox is None or combo.fox == args.fox)
        and (args.river is None or combo.river == args.river)
        and (args.quest is None or combo.quest == args.quest)
        and (args.bridge is None or combo.bridge == args.bridge)
        and (args.rhyme is None or combo.rhyme == args.rhyme)
    ]
    if not combos:
        raise StoryError("no valid loud-fox crystal-river quest matches the requested options")
    params = copy.deepcopy(rng.choice(combos))
    params.seed = rng.randrange(2**31)
    return params


def iter_samples(args: argparse.Namespace) -> Iterable[StorySample]:
    if args.all:
        for params in all_params():
            seeded = copy.deepcopy(params)
            seeded.seed = args.seed
            yield generate(seeded)
        return

    rng = random.Random(args.seed)
    seen: set[tuple[str, str, str, str, str]] = set()
    attempts = 0
    while len(seen) < max(1, args.n) and attempts < max(args.n * 20, 50):
        attempts += 1
        params = resolve_params(args, rng)
        key = (params.fox, params.river, params.quest, params.bridge, params.rhyme)
        if key in seen:
            continue
        seen.add(key)
        yield generate(params)
    if not seen:
        raise StoryError("could not produce any valid story samples")


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (fox, river, quest, bridge, rhyme) combinations:\n")
        for fox, river, quest, bridge, rhyme in combos:
            print(f"  {fox:8} {river:10} {quest:8} {bridge:8} {rhyme}")
        return

    try:
        samples = list(iter_samples(args))
    except StoryError as err:
        print(err)
        return

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
            header = f"### {p.fox} {p.river} {p.quest} {p.bridge} {p.rhyme}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
