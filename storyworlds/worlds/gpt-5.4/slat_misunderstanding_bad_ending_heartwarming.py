#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/slat_misunderstanding_bad_ending_heartwarming.py
============================================================================

A standalone story world for a heartwarming-but-sad misunderstanding tale built
around a wooden slat.

Premise
-------
A kind child hears a sound near a slatted little animal house and misunderstands
it. Thinking something is trapped inside, the child pulls away one loose slat to
help. The sound was coming from somewhere else, and the opening lets the small
animals escape into the evening. A grown-up helps search, but the ending stays
sad: at least one animal is still missing by bedtime. The warmth comes from the
adult's response and from the child's kind motive, not from a full recovery.

Reasonableness gate
-------------------
Not every sound is plausible, and not every structure is vulnerable in the same
way. This world only generates combinations where:

* the real sound can plausibly be mistaken for the hoped-for trapped animal, and
* the enclosure is made of slats and holds small animals that could slip out
  through a gap if a slat were removed.

Run it
------
    python storyworlds/worlds/gpt-5.4/slat_misunderstanding_bad_ending_heartwarming.py
    python storyworlds/worlds/gpt-5.4/slat_misunderstanding_bad_ending_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/slat_misunderstanding_bad_ending_heartwarming.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/slat_misunderstanding_bad_ending_heartwarming.py --qa
    python storyworlds/worlds/gpt-5.4/slat_misunderstanding_bad_ending_heartwarming.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/slat_misunderstanding_bad_ending_heartwarming.py --verify
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


@dataclass
class Enclosure:
    id: str
    label: str
    the: str
    residents: str
    count: int
    resident_word: str
    slat_text: str
    escape_verb: str
    food: str
    track: str
    escape_risk: int
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]


@dataclass
class Mistake:
    id: str
    animal: str
    cry: str
    article: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Source:
    id: str
    label: str
    location: str
    sounds_like: set[str]
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SearchPlan:
    id: str
    tool: str
    action: str
    comfort_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Weather:
    id: str
    sky: str
    air: str
    difficulty: int
    hiding: str
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


def entity_by_role(world: World, role: str, fallback_id: str) -> Entity:
    for ent in world.entities.values():
        if ent.role == role:
            return ent
    return world.get(fallback_id)


def _r_gap_means_escape(world: World) -> list[str]:
    out: list[str] = []
    coop = world.get("enclosure")
    flock = world.get("residents")
    if coop.meters["gap"] < THRESHOLD:
        return out
    sig = ("escape", world.facts["enclosure_cfg"].id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    escaped = world.facts["escaped_count"]
    flock.meters["escaped"] += escaped
    flock.memes["fear"] += 1
    world.get("child").memes["alarm"] += 1
    parent = entity_by_role(world, "parent", "parent")
    parent.memes["worry"] += 1
    out.append("__escaped__")
    return out


def _r_missing_after_search(world: World) -> list[str]:
    flock = world.get("residents")
    parent = entity_by_role(world, "parent", "parent")
    if flock.meters["escaped"] < THRESHOLD or parent.meters["searched"] < THRESHOLD:
        return []
    sig = ("missing", int(flock.meters["escaped"]))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    missing = world.facts["missing_count"]
    found = world.facts["escaped_count"] - missing
    if found > 0:
        flock.meters["found"] += found
    flock.meters["missing"] += missing
    world.get("child").memes["guilt"] += 1
    parent.memes["care"] += 1
    return ["__missing__"]


CAUSAL_RULES = [
    Rule("escape", "physical", _r_gap_means_escape),
    Rule("missing", "physical", _r_missing_after_search),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
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


ENCLOSURES = {
    "rabbit_hutch": Enclosure(
        "rabbit_hutch", "rabbit hutch", "the rabbit hutch",
        "two rabbits", 2, "rabbit",
        "One side was made from thin wooden slats, and one slat had worked loose at the bottom.",
        "bounded",
        "carrot tops",
        "small paw prints in the damp dirt",
        2,
        tags={"rabbits", "hutch", "slat"},
    ),
    "chick_pen": Enclosure(
        "chick_pen", "chick pen", "the chick pen",
        "four chicks", 4, "chick",
        "Its little wall was built from narrow slats, and one slat wiggled when touched.",
        "scattered",
        "crumbs and grain",
        "tiny scratch marks in the mud",
        3,
        tags={"chicks", "pen", "slat"},
    ),
    "dove_loft": Enclosure(
        "dove_loft", "dove loft", "the dove loft",
        "three white doves", 3, "dove",
        "A weathered slat near the latch had a soft split in it and sat a little crooked.",
        "fluttered",
        "seed",
        "white feathers by the fence",
        3,
        tags={"doves", "loft", "slat"},
    ),
}

MISTAKES = {
    "kitten": Mistake("kitten", "kitten", "a tiny mew", "a", tags={"kitten"}),
    "puppy": Mistake("puppy", "puppy", "a soft yip", "a", tags={"puppy"}),
    "duckling": Mistake("duckling", "duckling", "a peeping cry", "a", tags={"duckling"}),
}

SOURCES = {
    "hedge_kitten": Source(
        "hedge_kitten", "a stray kitten", "under the hedge behind the animal house",
        {"kitten", "puppy"},
        "A real kitten was crouched under the hedge, shivering and calling there instead.",
        tags={"kitten", "hedge"},
    ),
    "nestlings": Source(
        "nestlings", "a nest of hungry baby birds", "in the ivy above the roof",
        {"duckling", "kitten"},
        "The sound had been coming from hungry nestlings tucked in the ivy above the roof.",
        tags={"birds", "ivy"},
    ),
    "pump_squeak": Source(
        "pump_squeak", "the old hand pump", "beside the rain barrel",
        {"puppy", "duckling"},
        "The cry was only the old hand pump by the barrel, squeaking each time the wind nudged it.",
        tags={"wind", "pump"},
    ),
}

SEARCH_PLANS = {
    "lantern": SearchPlan(
        "lantern", "a lantern",
        "lifted a lantern and called softly while looking under leaves and buckets",
        "Then the grown-up wrapped the child in a warm arm and said kind hearts can still make mistakes.",
        tags={"lantern", "search"},
    ),
    "basket": SearchPlan(
        "basket", "a basket of feed",
        "carried a basket of feed and shook it gently while searching the yard",
        "Then the grown-up rubbed the child's back and said trying to help had come from love, not from meanness.",
        tags={"feed", "search"},
    ),
    "blanket": SearchPlan(
        "blanket", "a wool blanket",
        "tucked a wool blanket over one arm and searched slowly by the fence and the shed",
        "Then the grown-up pulled the child close under the blanket and said being sorry was part of learning to be gentle.",
        tags={"blanket", "search"},
    ),
}

WEATHERS = {
    "calm_dusk": Weather(
        "calm_dusk",
        "The evening sky had turned peach and gray.",
        "The yard was growing dim.",
        1,
        "the quiet shadows under the bushes",
        tags={"dusk"},
    ),
    "windy_dusk": Weather(
        "windy_dusk",
        "The sky was turning dark, and the wind kept worrying the leaves.",
        "Every rustle sounded bigger than it was.",
        2,
        "the rattling hedge and the dark space under the porch",
        tags={"wind", "dusk"},
    ),
    "drizzly_evening": Weather(
        "drizzly_evening",
        "A thin evening rain made everything shine.",
        "Drops tapped on wood and made the garden smell cold and wet.",
        2,
        "the wet grass and the places where the rain blurred small tracks",
        tags={"rain", "dusk"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Leo", "Ben", "Max", "Sam", "Finn", "Theo", "Noah", "Eli", "Jack", "Owen"]
TRAITS = ["gentle", "helpful", "soft-hearted", "curious", "eager", "tender"]


def compatible(mistake: Mistake, source: Source, enclosure: Enclosure) -> bool:
    return mistake.id in source.sounds_like and enclosure.escape_risk >= 2


def escaped_count(enclosure: Enclosure) -> int:
    return max(1, enclosure.count - 1)


def missing_count(enclosure: Enclosure, weather: Weather) -> int:
    escaped = escaped_count(enclosure)
    if enclosure.escape_risk + weather.difficulty >= 5:
        return escaped
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for e_id, enclosure in ENCLOSURES.items():
        for m_id, mistake in MISTAKES.items():
            for s_id, source in SOURCES.items():
                if compatible(mistake, source, enclosure):
                    combos.append((e_id, m_id, s_id))
    return combos


def predict_gap(enclosure: Enclosure, weather: Weather) -> dict:
    return {
        "escaped": escaped_count(enclosure),
        "missing": missing_count(enclosure, weather),
    }


def introduce(world: World, child: Entity, parent: Entity, weather: Weather, enclosure: Enclosure) -> None:
    trait = child.traits[0] if child.traits else "gentle"
    world.say(
        f"{child.id} was a {trait} little {child.type} who always hurried toward small sad sounds."
    )
    world.say(
        f"One evening, {child.id} was in the yard with {child.pronoun('possessive')} {parent.label_word}. "
        f"{weather.sky} {weather.air}"
    )
    world.say(
        f"Near the shed stood {enclosure.the}. {enclosure.slat_text}"
    )


def hear_sound(world: World, child: Entity, mistake: Mistake, source: Source) -> None:
    child.memes["concern"] += 1
    world.say(
        f"From somewhere close by came {mistake.cry}. "
        f"{child.id} stopped and listened hard."
    )
    world.say(
        f'"There is a {mistake.animal} in there," {child.pronoun()} whispered, staring at {world.facts["enclosure_cfg"].the}. '
        f"{child.pronoun().capitalize()} thought the sound must be coming from behind the slats."
    )


def choose_help(world: World, child: Entity, mistake: Mistake) -> None:
    child.memes["resolve"] += 1
    world.say(
        f"{child.id} did not want {mistake.article} {mistake.animal} to stay trapped for even one more minute."
    )
    world.say(
        f"So {child.pronoun()} knelt by the loose slat and tugged it, trying to make a little door."
    )


def remove_slat(world: World, child: Entity, enclosure: Enclosure) -> None:
    coop = world.get("enclosure")
    coop.meters["gap"] += 1
    world.facts["slat_removed"] = True
    propagate(world, narrate=False)
    world.say(
        f"The slat came free with a dry little crack. At once a gap opened near the bottom of {enclosure.the}."
    )


def reveal_mistake(world: World, child: Entity, enclosure: Enclosure, source: Source) -> None:
    flock = world.get("residents")
    child.memes["shock"] += 1
    escaped = int(flock.meters["escaped"])
    world.say(
        f"But no trapped creature was inside. Instead, {enclosure.residents} startled and {enclosure.escape_verb} through the gap."
    )
    if escaped == 1:
        world.say(
            f"{child.id} saw one {enclosure.resident_word} vanish into the yard and felt {child.pronoun('possessive')} stomach drop."
        )
    else:
        world.say(
            f"In a blink, {escaped} of them were out in the yard, and {child.id} felt {child.pronoun('possessive')} stomach drop."
        )
    world.say(source.reveal)


def call_parent(world: World, child: Entity, parent: Entity) -> None:
    world.say(f'"{parent.label_word.capitalize()}!" {child.id} cried. "I was trying to help!"')


def search(world: World, child: Entity, parent: Entity, plan: SearchPlan, enclosure: Enclosure, weather: Weather) -> None:
    parent.meters["searched"] += 1
    propagate(world, narrate=False)
    found = int(world.get("residents").meters["found"])
    missing = int(world.get("residents").meters["missing"])
    world.say(
        f"{parent.label_word.capitalize()} came quickly, saw the empty gap, and understood what had happened."
    )
    world.say(
        f"{parent.pronoun().capitalize()} did not scold first. {parent.pronoun().capitalize()} {plan.action}."
    )
    if found > 0:
        world.say(
            f"They found {found} {enclosure.resident_word if found == 1 else enclosure.resident_word + 's'} by following {enclosure.track}."
        )
    if missing == 1:
        world.say(
            f"But one {enclosure.resident_word} stayed hidden in {weather.hiding}, and the light kept fading."
        )
    else:
        world.say(
            f"But {missing} {enclosure.resident_word + 's'} stayed hidden in {weather.hiding}, and the light kept fading."
        )


def comfort(world: World, child: Entity, parent: Entity, enclosure: Enclosure, plan: SearchPlan) -> None:
    child.memes["sorrow"] += 1
    child.memes["love"] += 1
    parent.memes["love"] += 1
    world.say(
        f"{child.id}'s eyes filled with tears. {child.pronoun().capitalize()} kept saying {child.pronoun('possessive')} heart had meant to rescue someone."
    )
    world.say(plan.comfort_line)
    world.say(
        f'Together they set a little dish of {enclosure.food} by the hutch and left the broken place covered for the night.'
    )


def ending(world: World, child: Entity, enclosure: Enclosure) -> None:
    missing = int(world.get("residents").meters["missing"])
    if missing == 1:
        world.say(
            f"The missing {enclosure.resident_word} was still gone at bedtime."
        )
    else:
        world.say(
            f"{missing} {enclosure.resident_word}s were still gone at bedtime."
        )
    world.say(
        f"From the window, {child.id} looked out at the place where the slat had been and wished kindness alone could mend every mistake."
    )


def tell(
    enclosure: Enclosure,
    mistake: Mistake,
    source: Source,
    plan: SearchPlan,
    weather: Weather,
    child_name: str = "Lily",
    child_gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "gentle",
) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child", traits=[trait]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    world.add(Entity(id="enclosure", type="enclosure", label=enclosure.label))
    world.add(Entity(id="residents", type="animals", label=enclosure.residents))
    world.facts.update(
        enclosure_cfg=enclosure,
        mistake=mistake,
        source=source,
        plan=plan,
        weather=weather,
        child=child,
        parent=parent,
        escaped_count=escaped_count(enclosure),
        missing_count=missing_count(enclosure, weather),
    )

    introduce(world, child, parent, weather, enclosure)
    world.para()
    hear_sound(world, child, mistake, source)
    choose_help(world, child, mistake)
    remove_slat(world, child, enclosure)
    reveal_mistake(world, child, enclosure, source)
    call_parent(world, child, parent)
    world.para()
    search(world, child, parent, plan, enclosure, weather)
    comfort(world, child, parent, enclosure, plan)
    ending(world, child, enclosure)

    world.facts.update(
        slat_removed=True,
        escaped=int(world.get("residents").meters["escaped"]),
        found=int(world.get("residents").meters["found"]),
        missing=int(world.get("residents").meters["missing"]),
        outcome="bad",
    )
    return world


KNOWLEDGE = {
    "slat": [(
        "What is a slat?",
        "A slat is a thin strip of wood used as part of a fence, crate, or little wall. If one comes loose, it can leave a gap."
    )],
    "kitten": [(
        "Why might a kitten sound scared?",
        "A kitten may cry when it is cold, hungry, or alone. Small animals often make bigger-sounding worries than they really are."
    )],
    "puppy": [(
        "Why should you tell a grown-up before pulling wood off something?",
        "A grown-up can check what the wood is holding in or holding up. Pulling it away can make a new problem even when you are trying to help."
    )],
    "duckling": [(
        "Why do baby birds or ducklings make peeping sounds?",
        "Tiny birds peep to call for food, warmth, or their family. Their voices can be easy to mix up with other little cries."
    )],
    "rabbits": [(
        "Why do rabbits hide when they are frightened?",
        "Rabbits are small prey animals, so when they feel scared they often run and hide very quickly. That can make them hard to find."
    )],
    "chicks": [(
        "Why are chicks easy to lose in tall grass?",
        "Chicks are tiny and quick, and their colors can blend into dirt or straw. Once they scatter, they are hard to spot."
    )],
    "doves": [(
        "Why can doves be hard to catch once they fly out?",
        "Doves can flutter up to roofs and fences in a moment. After that, people may have to wait and coax them back gently."
    )],
    "search": [(
        "What is a good first step when an animal gets loose?",
        "Tell a grown-up right away and search calmly together. Moving gently helps more than panicking."
    )],
    "mistake": [(
        "Can a kind mistake still hurt something?",
        "Yes. A person can mean to help and still cause trouble because they did not understand the whole situation."
    )],
}

KNOWLEDGE_ORDER = ["slat", "kitten", "puppy", "duckling", "rabbits", "chicks", "doves", "search", "mistake"]


@dataclass
class StoryParams:
    enclosure: str
    mistaken_for: str
    source: str
    search: str
    weather: str
    child_name: str
    child_gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    enclosure = f["enclosure_cfg"]
    mistake = f["mistake"]
    return [
        f'Write a heartwarming but sad story for a 3-to-5-year-old that includes the word "slat".',
        f"Tell a gentle misunderstanding story where {child.id} hears what sounds like a {mistake.animal}, pulls a loose slat from {enclosure.the}, and accidentally lets {enclosure.residents} escape.",
        f"Write a soft, emotional story where a kind child makes a mistake while trying to rescue someone, and bedtime comes before everything can be fixed.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    enclosure = f["enclosure_cfg"]
    mistake = f["mistake"]
    source = f["source"]
    plan = f["plan"]
    missing = f["missing"]
    escaped = f["escaped"]
    found = f["found"]
    source_reveal = source.reveal.rstrip(".")
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a kind little {child.type}, and {child.pronoun('possessive')} {parent.label_word}. The story turns on {child.id}'s wish to help a creature that seemed trapped."
        ),
        (
            f"Why did {child.id} pull the slat away?",
            f"{child.id} thought a {mistake.animal} was trapped behind the wooden slats. {child.pronoun().capitalize()} was trying to make a little door, so the mistake began with kindness."
        ),
        (
            "What was the misunderstanding?",
            f"The sound was not coming from inside {enclosure.the} at all. {source_reveal}."
        ),
        (
            f"What happened when the slat came off?",
            f"A gap opened at the bottom of {enclosure.the}, and {escaped} of the animals got out. The opening changed the world right away because the home was no longer closed."
        ),
        (
            f"How did {child.id}'s {parent.label_word} react?",
            f"{parent.label_word.capitalize()} came quickly and started searching instead of scolding first. {parent.pronoun().capitalize()} {plan.action}, because helping calmly mattered more than blaming in that moment."
        ),
    ]
    if found > 0:
        qa.append((
            "Did they find all the animals?",
            f"No. They found {found}, but {missing} were still missing by bedtime. That is why the ending stays sad even though the grown-up is gentle."
        ))
    else:
        qa.append((
            "Did they find any of the animals that night?",
            f"No. By the time they searched in the fading light, all the escaped animals were still hidden. The weather and the darkness made the loss feel even bigger."
        ))
    qa.append((
        "How did the story end?",
        f"It ended with love but not with a full fix: {missing} {enclosure.resident_word if missing == 1 else enclosure.resident_word + 's'} were still gone at bedtime. From the window, {child.id} looked toward the place where the slat had been and understood that good hearts still need careful choices."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"slat", "search", "mistake"}
    tags |= set(f["mistake"].tags)
    tags |= set(f["enclosure_cfg"].tags)
    out: list[tuple[str, str]] = []
    mapping = {
        "slat": "slat",
        "kitten": "kitten",
        "puppy": "puppy",
        "duckling": "duckling",
        "rabbits": "rabbits",
        "chicks": "chicks",
        "doves": "doves",
        "search": "search",
        "mistake": "mistake",
    }
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and mapping[tag] in KNOWLEDGE:
            out.extend(KNOWLEDGE[mapping[tag]])
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    lines.append(f"  facts: escaped={world.facts.get('escaped')} missing={world.facts.get('missing')}")
    return "\n".join(lines)


CURATED = [
    StoryParams("rabbit_hutch", "kitten", "hedge_kitten", "lantern", "calm_dusk", "Lily", "girl", "mother", "gentle"),
    StoryParams("chick_pen", "duckling", "nestlings", "basket", "windy_dusk", "Ben", "boy", "father", "helpful"),
    StoryParams("dove_loft", "puppy", "pump_squeak", "blanket", "drizzly_evening", "Mia", "girl", "mother", "soft-hearted"),
    StoryParams("rabbit_hutch", "puppy", "pump_squeak", "basket", "windy_dusk", "Leo", "boy", "father", "eager"),
    StoryParams("chick_pen", "kitten", "nestlings", "lantern", "drizzly_evening", "Nora", "girl", "mother", "tender"),
]


def explain_rejection(mistake: Mistake, source: Source, enclosure: Enclosure) -> str:
    if mistake.id not in source.sounds_like:
        return (
            f"(No story: {source.label} at {source.location} would not reasonably sound like a {mistake.animal}. "
            f"The misunderstanding needs a believable sound alike.)"
        )
    if enclosure.escape_risk < 2:
        return (
            f"(No story: {enclosure.the} is not vulnerable enough for one loose slat to create a real escape problem.)"
        )
    return "(No story: this combination does not fit the world rules.)"


ASP_RULES = r"""
plausible(M, S) :- source(S), mistake(M), sounds_like(S, M).
breachable(E)   :- enclosure(E), escape_risk(E, R), R >= 2.
valid(E, M, S)  :- enclosure(E), mistake(M), source(S), plausible(M, S), breachable(E).

escaped(E, N) :- escape_count(E, N).
all_missing(E, W) :- escape_risk(E, R), weather_diff(W, D), R + D >= 5.
missing(E, W, N) :- all_missing(E, W), escaped(E, N).
missing(E, W, 1) :- weather(W), escaped(E, N), not all_missing(E, W), N >= 1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for e_id, e in ENCLOSURES.items():
        lines.append(asp.fact("enclosure", e_id))
        lines.append(asp.fact("escape_risk", e_id, e.escape_risk))
        lines.append(asp.fact("escape_count", e_id, escaped_count(e)))
    for m_id in MISTAKES:
        lines.append(asp.fact("mistake", m_id))
    for s_id, s in SOURCES.items():
        lines.append(asp.fact("source", s_id))
        for m_id in sorted(s.sounds_like):
            lines.append(asp.fact("sounds_like", s_id, m_id))
    for w_id, w in WEATHERS.items():
        lines.append(asp.fact("weather", w_id))
        lines.append(asp.fact("weather_diff", w_id, w.difficulty))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_missing(enclosure: str, weather: str) -> int:
    import asp

    extra = "\n".join([asp.fact("chosen_enclosure", enclosure), asp.fact("chosen_weather", weather)])
    rules = """
escaped_now(N) :- chosen_enclosure(E), escaped(E, N).
missing_now(N) :- chosen_enclosure(E), chosen_weather(W), missing(E, W, N).
"""
    model = asp.one_model(f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{rules}\n#show missing_now/1.\n")
    atoms = asp.atoms(model, "missing_now")
    return atoms[0][0] if atoms else -1


def asp_verify() -> int:
    rc = 0
    a_set, p_set = set(asp_valid_combos()), set(valid_combos())
    if a_set == p_set:
        print(f"OK: gate matches valid_combos() ({len(a_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if a_set - p_set:
            print("  only in asp:", sorted(a_set - p_set))
        if p_set - a_set:
            print("  only in python:", sorted(p_set - a_set))

    mismatches = []
    for e_id in ENCLOSURES:
        for w_id in WEATHERS:
            p = missing_count(ENCLOSURES[e_id], WEATHERS[w_id])
            a = asp_missing(e_id, w_id)
            if p != a:
                mismatches.append((e_id, w_id, p, a))
    if not mismatches:
        print("OK: missing-count model matches Python for all enclosure/weather pairs.")
    else:
        rc = 1
        print("MISMATCH in missing counts:")
        for row in mismatches:
            print(" ", row)

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during verify smoke test.")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a kind misunderstanding, a loose slat, and a heartwarming bad ending."
    )
    ap.add_argument("--enclosure", choices=ENCLOSURES)
    ap.add_argument("--mistaken-for", dest="mistaken_for", choices=MISTAKES)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--search", choices=SEARCH_PLANS)
    ap.add_argument("--weather", choices=WEATHERS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.mistaken_for and args.source and args.enclosure:
        m = MISTAKES[args.mistaken_for]
        s = SOURCES[args.source]
        e = ENCLOSURES[args.enclosure]
        if not compatible(m, s, e):
            raise StoryError(explain_rejection(m, s, e))

    combos = [
        c for c in valid_combos()
        if (args.enclosure is None or c[0] == args.enclosure)
        and (args.mistaken_for is None or c[1] == args.mistaken_for)
        and (args.source is None or c[2] == args.source)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    enclosure, mistaken_for, source = rng.choice(sorted(combos))
    search = args.search or rng.choice(sorted(SEARCH_PLANS))
    weather = args.weather or rng.choice(sorted(WEATHERS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(enclosure, mistaken_for, source, search, weather, name, gender, parent, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        ENCLOSURES[params.enclosure],
        MISTAKES[params.mistaken_for],
        SOURCES[params.source],
        SEARCH_PLANS[params.search],
        WEATHERS[params.weather],
        params.child_name,
        params.child_gender,
        params.parent,
        params.trait,
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
        print(asp_program("", "#show valid/3.\n#show missing/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (enclosure, mistaken_for, source) combos:\n")
        for enclosure, mistake, source in combos:
            print(f"  {enclosure:12} {mistake:10} {source}")
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
            header = (
                f"### {p.child_name}: {p.mistaken_for} near {p.enclosure} "
                f"({p.source}, {p.weather})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
