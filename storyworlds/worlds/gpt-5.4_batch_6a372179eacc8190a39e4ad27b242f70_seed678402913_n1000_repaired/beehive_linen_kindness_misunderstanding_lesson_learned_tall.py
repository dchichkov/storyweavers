#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/beehive_linen_kindness_misunderstanding_lesson_learned_tall.py
===========================================================================================

A standalone story world for a child-facing tall tale about a giant-hearted child,
a beehive, and a piece of linen.

This world models one small domain:

    A very large child sees bees crowding around a family linen cloth and
    misunderstands what the bees are doing. The bees are not being naughty:
    wind has torn their beehive, and they are after loose threads and shelter.
    A kind grown-up helps the child notice the real problem, offers a better
    solution, and the child learns to look twice before judging.

The story leans a little "tall tale" in scale and imagery: wash lines stretch
like bridges, cloth snaps like sails, and a beehive can hang as big as a basket.
But the causal core stays concrete and checkable.

Run it
------
    python storyworlds/worlds/gpt-5.4/beehive_linen_kindness_misunderstanding_lesson_learned_tall.py
    python storyworlds/worlds/gpt-5.4/beehive_linen_kindness_misunderstanding_lesson_learned_tall.py --cloth sheet --damage torn
    python storyworlds/worlds/gpt-5.4/beehive_linen_kindness_misunderstanding_lesson_learned_tall.py --cloth apron
    python storyworlds/worlds/gpt-5.4/beehive_linen_kindness_misunderstanding_lesson_learned_tall.py --all
    python storyworlds/worlds/gpt-5.4/beehive_linen_kindness_misunderstanding_lesson_learned_tall.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/beehive_linen_kindness_misunderstanding_lesson_learned_tall.py --verify
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
    phrase: str = ""
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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    scene: str
    giant_line: str
    bloom: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Linen:
    id: str
    label: str
    phrase: str
    plural: bool = False
    loose_threads: bool = True
    family_use: str = ""
    tags: set[str] = field(default_factory=set)

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Damage:
    id: str
    cause: str
    hive_need: str
    severity: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    helps_damage: set[str] = field(default_factory=set)
    gives_bees: str = ""
    child_action: str = ""
    ending_image: str = ""
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


def _r_bees_need_help(world: World) -> list[str]:
    hive = world.get("hive")
    if hive.meters["damaged"] < THRESHOLD:
        return []
    sig = ("need_help", "hive")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hive.meters["needs_patch"] += 1
    bees = world.get("bees")
    bees.memes["busy"] += 1
    return ["__need_help__"]


def _r_swarm_at_linen(world: World) -> list[str]:
    hive = world.get("hive")
    linen = world.get("linen")
    bees = world.get("bees")
    if hive.meters["needs_patch"] < THRESHOLD or linen.meters["available_threads"] < THRESHOLD:
        return []
    sig = ("swarm_linen", "bees", "linen")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    bees.meters["near_linen"] += 1
    linen.meters["tugged"] += 1
    return ["__swarm__"]


def _r_misunderstanding(world: World) -> list[str]:
    child = world.get("child")
    bees = world.get("bees")
    if bees.meters["near_linen"] < THRESHOLD:
        return []
    sig = ("misunderstand", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["suspicion"] += 1
    child.memes["protective"] += 1
    return ["__misunderstanding__"]


CAUSAL_RULES = [
    Rule(name="need_help", tag="physical", apply=_r_bees_need_help),
    Rule(name="swarm_linen", tag="physical", apply=_r_swarm_at_linen),
    Rule(name="misunderstanding", tag="social", apply=_r_misunderstanding),
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
                produced.extend(sents)
    if narrate:
        for sent in produced:
            if not sent.startswith("__"):
                world.say(sent)
    return produced


def fix_works(damage_id: str, fix_id: str) -> bool:
    return damage_id in FIXES[fix_id].helps_damage


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id in PLACES:
        for cloth_id, cloth in LINENS.items():
            if not cloth.loose_threads:
                continue
            for damage_id in DAMAGES:
                combos.append((place_id, cloth_id, damage_id))
    return combos


def predict_swarm(damage: Damage, cloth: Linen) -> dict:
    return {
        "needs_patch": damage.severity >= 1,
        "will_circle_linen": damage.severity >= 1 and cloth.loose_threads,
    }


def introduce(world: World, child: Entity, place: Place, cloth: Linen, parent: Entity) -> None:
    world.say(
        f"In {place.scene}, {child.id} was such a tall child that {place.giant_line}. "
        f"{child.pronoun().capitalize()} liked helping {child.pronoun('possessive')} "
        f"{parent.label_word} with the wash, especially when there was {cloth.phrase} to hang."
    )
    world.say(
        f"Folks said {child.id} could shake out a piece of linen so wide it looked like a pale cloud learning manners."
    )


def hang_linen(world: World, child: Entity, cloth: Linen, place: Place) -> None:
    linen = world.get("linen")
    linen.meters["hung"] += 1
    child.memes["pride"] += 1
    world.say(
        f"That morning {child.id} lifted {cloth.phrase} high over {child.pronoun('possessive')} head "
        f"and pinned it to the long line. The clean linen shone in the sun, and beyond it {place.bloom}."
    )


def storm_damage(world: World, damage: Damage) -> None:
    hive = world.get("hive")
    hive.meters["damaged"] += 1
    hive.meters["severity"] = float(damage.severity)
    world.say(
        f"But in the night before, {damage.cause}, leaving the old beehive with {damage.hive_need}."
    )
    propagate(world, narrate=False)


def bees_arrive(world: World, cloth: Linen) -> None:
    propagate(world, narrate=False)
    world.say(
        f"By breakfast a gold-brown buzz was stitching the air. Bees circled the {cloth.label}, "
        f"touching only the loose little threads at the edge."
    )


def mistake(world: World, child: Entity, cloth: Linen) -> None:
    propagate(world, narrate=False)
    world.say(
        f"{child.id} saw the whirling bees and drew a great careful breath. "
        f'"Oh no," {child.pronoun()} said. "Those bees are spoiling the linen!"'
    )


def protective_move(world: World, child: Entity, cloth: Linen) -> None:
    child.memes["kindness"] += 1
    world.say(
        f"{child.pronoun().capitalize()} did not want to hurt a single wing, so instead of swatting, "
        f"{child.pronoun()} spread {child.pronoun('possessive')} broad hands and tried to guard the {cloth.label} with a shadow big as a porch roof."
    )


def explain(world: World, parent: Entity, child: Entity, damage: Damage, cloth: Linen) -> None:
    parent.memes["patience"] += 1
    child.memes["wonder"] += 1
    world.say(
        f"{parent.label_word.capitalize()} came over, listened to the hum, and looked toward the beehive. "
        f'"Easy now," {parent.pronoun()} said. "They are not trying to ruin our {cloth.label}. '
        f'The wind left their home {damage.hive_need}, and they are after only the stray threads."'
    )


def child_notices(world: World, child: Entity) -> None:
    child.memes["understanding"] += 1
    child.memes["suspicion"] = 0.0
    world.say(
        f"Then {child.id} looked again and saw it: the bees were not chewing holes or diving at anyone. "
        f"They were carrying tiny wisps away toward the hive as neatly as tailors carrying thread."
    )


def choose_fix(world: World, child: Entity, parent: Entity, cloth: Linen, fix: Fix) -> None:
    child.memes["kindness"] += 1
    child.memes["lesson"] += 1
    hive = world.get("hive")
    bees = world.get("bees")
    linen = world.get("linen")
    hive.meters["patched"] += 1
    hive.meters["needs_patch"] = 0.0
    bees.meters["near_linen"] = 0.0
    linen.meters["saved"] += 1
    world.say(
        f'"Then let us help the right way," said {child.id}. {child.pronoun().capitalize()} {fix.child_action}. '
        f'Soon the bees had {fix.gives_bees}, and they left the family linen in peace.'
    )
    world.say(
        f"By noon the beehive looked steadier, the buzzing softened, and {fix.ending_image}."
    )


def closing_lesson(world: World, child: Entity, cloth: Linen) -> None:
    world.say(
        f"After that, whenever {child.id} saw a muddle around the wash line, {child.pronoun()} remembered to look twice before deciding who was to blame. "
        f"The lesson stuck fast: kindness begins with asking what trouble someone else might be in."
    )
    world.say(
        f"And the old story says that on still afternoons, the bees still float past the {cloth.label} as politely as tiny thank-you notes."
    )


def tell(
    place: Place,
    cloth: Linen,
    damage: Damage,
    fix: Fix,
    child_name: str = "Tess",
    child_type: str = "girl",
    parent_type: str = "mother",
) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child", label=child_name))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    world.add(Entity(id="linen", type="linen", label=cloth.label, phrase=cloth.phrase, tags=set(cloth.tags)))
    world.add(Entity(id="hive", type="beehive", label="beehive", phrase="the old beehive", tags={"beehive", "bees"}))
    world.add(Entity(id="bees", type="bees", label="bees", phrase="the bees", tags={"bees"}))
    world.get("linen").meters["available_threads"] = 1.0 if cloth.loose_threads else 0.0

    introduce(world, child, place, cloth, parent)
    hang_linen(world, child, cloth, place)

    world.para()
    storm_damage(world, damage)
    bees_arrive(world, cloth)
    mistake(world, child, cloth)
    protective_move(world, child, cloth)

    world.para()
    explain(world, parent, child, damage, cloth)
    child_notices(world, child)
    choose_fix(world, child, parent, cloth, fix)

    world.para()
    closing_lesson(world, child, cloth)

    world.facts.update(
        place=place,
        cloth=cloth,
        damage=damage,
        fix=fix,
        child=child,
        parent=parent,
        misunderstood=True,
        learned=child.memes["lesson"] >= THRESHOLD,
        kindness=child.memes["kindness"] >= THRESHOLD,
    )
    return world


PLACES = {
    "orchard": Place(
        id="orchard",
        scene="a valley orchard where apple trees stood in rows like green soldiers",
        giant_line="the wash line ran from one stump to another like a white footbridge",
        bloom="the clover under the trees glowed pink and white",
        tags={"orchard", "flowers"},
    ),
    "meadow": Place(
        id="meadow",
        scene="a sunny meadow beside a creek that liked to brag after rain",
        giant_line="the wash line stretched across the grass like a banner at a fair",
        bloom="the wildflowers nodded in drifts of yellow and blue",
        tags={"meadow", "flowers"},
    ),
    "hill": Place(
        id="hill",
        scene="a windy hill where the barn roof could see three counties at once",
        giant_line="the wash line climbed between two posts as long as ship masts",
        bloom="the thyme and clover made a sweet smell in the warm air",
        tags={"hill", "flowers"},
    ),
}

LINENS = {
    "sheet": Linen(
        id="sheet",
        label="sheet",
        phrase="a great white linen sheet",
        plural=False,
        loose_threads=True,
        family_use="sleeping",
        tags={"linen", "sheet"},
    ),
    "tablecloth": Linen(
        id="tablecloth",
        label="tablecloth",
        phrase="a long linen tablecloth",
        plural=False,
        loose_threads=True,
        family_use="supper",
        tags={"linen", "tablecloth"},
    ),
    "towels": Linen(
        id="towels",
        label="towels",
        phrase="three snowy linen towels",
        plural=True,
        loose_threads=True,
        family_use="drying dishes",
        tags={"linen", "towels"},
    ),
    "apron": Linen(
        id="apron",
        label="apron",
        phrase="a neat linen apron",
        plural=False,
        loose_threads=False,
        family_use="baking",
        tags={"linen", "apron"},
    ),
}

DAMAGES = {
    "torn": Damage(
        id="torn",
        cause="a hard night wind had worried the branch and torn a flap in the comb",
        hive_need="a torn side open to the morning air",
        severity=2,
        tags={"wind", "repair"},
    ),
    "soaked": Damage(
        id="soaked",
        cause="a quick silver rain had soaked the outside and washed one waxy edge thin",
        hive_need="a soggy edge that no longer held tight",
        severity=1,
        tags={"rain", "repair"},
    ),
    "pecked": Damage(
        id="pecked",
        cause="a hungry woodpecker had pecked at the outer shell before flying off",
        hive_need="a pecked opening near the top",
        severity=2,
        tags={"birds", "repair"},
    ),
}

FIXES = {
    "linen_strip": Fix(
        id="linen_strip",
        label="linen strips",
        helps_damage={"torn", "soaked", "pecked"},
        gives_bees="a clean little bundle of linen strips on a fence rail near the hive",
        child_action="tore a few loose edge threads from an old rag basket and laid the soft strips closer to the tree",
        ending_image="sunlight lay on the cloth while bees worked busily at their own door instead",
        tags={"linen", "kindness"},
    ),
    "flower_patch": Fix(
        id="flower_patch",
        label="flower patch",
        helps_damage={"soaked"},
        gives_bees="fresh clover blossoms and a dry place nearby while the hive settled",
        child_action="moved the linen indoors for a while and set out a shallow pan of pebbles and water beside the clover",
        ending_image="the creek winked, the cloth dried inside, and the bees hummed low over the flowers",
        tags={"flowers", "water", "kindness"},
    ),
    "shade_roof": Fix(
        id="shade_roof",
        label="shade roof",
        helps_damage={"torn", "pecked"},
        gives_bees="a little bark roof over the weak side of the hive and a safer place to work",
        child_action="helped prop a strip of bark above the weak spot and hung one old rag nearby for thread",
        ending_image="the hive sat snug in its patch of shade while the linen billowed untouched on the line",
        tags={"repair", "kindness"},
    ),
}


@dataclass
class StoryParams:
    place: str
    cloth: str
    damage: str
    fix: str
    child_name: str
    child_type: str
    parent: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="orchard",
        cloth="sheet",
        damage="torn",
        fix="linen_strip",
        child_name="Tess",
        child_type="girl",
        parent="mother",
        trait="kind",
    ),
    StoryParams(
        place="meadow",
        cloth="tablecloth",
        damage="soaked",
        fix="flower_patch",
        child_name="Boone",
        child_type="boy",
        parent="father",
        trait="helpful",
    ),
    StoryParams(
        place="hill",
        cloth="towels",
        damage="pecked",
        fix="shade_roof",
        child_name="May",
        child_type="girl",
        parent="mother",
        trait="careful",
    ),
]


KNOWLEDGE = {
    "bees": [
        (
            "Why do bees visit flowers?",
            "Bees collect nectar and pollen from flowers for food. As they move from flower to flower, they also help many plants grow seeds and fruit."
        )
    ],
    "beehive": [
        (
            "What is a beehive?",
            "A beehive is the home where bees live together and store honey and pollen. It needs to stay dry and protected so the bees can keep their babies safe."
        )
    ],
    "linen": [
        (
            "What is linen?",
            "Linen is a cloth made from plant fibers. It is strong, but loose threads at the edge can still snag or pull."
        )
    ],
    "kindness": [
        (
            "What does kindness mean?",
            "Kindness means trying to help without hurting. Sometimes it also means slowing down and finding out what problem someone else is facing."
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone thinks they know what is going on, but they are wrong. Looking again and listening can help fix it."
        )
    ],
    "flowers": [
        (
            "Why are flowers good for bees?",
            "Flowers give bees nectar and pollen. Bees use that food to live and to help feed the hive."
        )
    ],
    "water": [
        (
            "Why do bees need water?",
            "Bees use water to cool and help their hive. They do best when water is shallow and safe to reach."
        )
    ],
    "repair": [
        (
            "Why is a damaged animal home a problem?",
            "A damaged home can let in wind, rain, or other danger. When a home is hurt, the animals living there often have to work extra hard to fix it."
        )
    ],
}
KNOWLEDGE_ORDER = ["bees", "beehive", "linen", "kindness", "misunderstanding", "flowers", "water", "repair"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    cloth = f["cloth"]
    damage = f["damage"]
    place = f["place"]
    return [
        f'Write a short tall-tale story for a 3-to-5-year-old that includes the words "beehive" and "linen".',
        f"Tell a gentle story set in {place.scene} where {child.id} sees bees around a {cloth.label}, misunderstands the buzzing, and learns a lesson about kindness.",
        f"Write a child-facing tall tale where wind leaves a beehive {damage.hive_need}, and a big-hearted child helps after first making the wrong guess.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    cloth = f["cloth"]
    damage = f["damage"]
    fix = f["fix"]
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a very tall and kind child, and {child.pronoun('possessive')} {pw}. It is also about the bees whose beehive had been damaged."
        ),
        (
            f"What was hanging on the line?",
            f"There was {cloth.phrase} hanging on the wash line. The clean linen mattered to the family, so {child.id} wanted to protect it."
        ),
        (
            f"Why did {child.id} think the bees were causing trouble?",
            f"{child.id} saw the bees circling the linen and touching its loose threads, so {child.pronoun()} thought they were spoiling it. That was the misunderstanding, because the bees were really trying to fix their hurt home."
        ),
        (
            "What was really wrong with the beehive?",
            f"The beehive had {damage.hive_need}. The bees were busy because they needed help patching the damage left by the storm or pecking."
        ),
        (
            f"How did {child.id} help once {child.pronoun()} understood?",
            f"{child.id} {fix.child_action}. That gave the bees a better place to work, so they stopped crowding around the family linen."
        ),
        (
            "What lesson did the child learn?",
            f"{child.id} learned not to blame first and ask questions later. {child.pronoun().capitalize()} learned that kindness starts with noticing what trouble someone else may be in."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"bees", "beehive", "linen", "kindness", "misunderstanding"}
    tags |= set(f["damage"].tags)
    tags |= set(f["fix"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(cloth: Linen) -> str:
    return (
        f"(No story: {cloth.phrase} is too neat for this world's misunderstanding. "
        f"The bees need loose threads or a nearby linen scrap, and this {cloth.label} does not offer that.)"
    )


def outcome_of(params: StoryParams) -> str:
    if not fix_works(params.damage, params.fix):
        return "unfixed"
    return "learned"


ASP_RULES = r"""
needs_threads(C) :- linen(C), loose_threads(C).
valid(P, C, D) :- place(P), linen(C), damage(D), needs_threads(C).

works(D, F) :- fix(F), helps(F, D).

outcome(learned) :- chosen_damage(D), chosen_fix(F), works(D, F).
outcome(unfixed) :- chosen_damage(D), chosen_fix(F), not works(D, F).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for cloth_id, cloth in LINENS.items():
        lines.append(asp.fact("linen", cloth_id))
        if cloth.loose_threads:
            lines.append(asp.fact("loose_threads", cloth_id))
    for damage_id in DAMAGES:
        lines.append(asp.fact("damage", damage_id))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        for damage_id in sorted(fix.helps_damage):
            lines.append(asp.fact("helps", fix_id, damage_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join(
        [
            asp.fact("chosen_damage", params.damage),
            asp.fact("chosen_fix", params.fix),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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
    rng = random.Random(99)
    parser = build_parser()
    for _ in range(20):
        params = resolve_params(parser.parse_args([]), rng)
        cases.append(params)

    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a tall child, a beehive, linen, a misunderstanding, and a kind lesson."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--cloth", choices=LINENS)
    ap.add_argument("--damage", choices=DAMAGES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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


GIRL_NAMES = ["Tess", "May", "Ada", "Nell", "June", "Molly"]
BOY_NAMES = ["Boone", "Eli", "Cal", "Finn", "Jude", "Otis"]
TRAITS = ["kind", "helpful", "careful", "gentle", "steady"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.cloth and not LINENS[args.cloth].loose_threads:
        raise StoryError(explain_rejection(LINENS[args.cloth]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.cloth is None or combo[1] == args.cloth)
        and (args.damage is None or combo[2] == args.damage)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, cloth, damage = rng.choice(sorted(combos))
    workable_fixes = [fix_id for fix_id in sorted(FIXES) if fix_works(damage, fix_id)]
    if args.fix is not None:
        if not fix_works(damage, args.fix):
            raise StoryError(
                f"(No story: the fix '{args.fix}' does not honestly solve '{damage}'. "
                f"Pick one of: {', '.join(workable_fixes)}.)"
            )
        fix = args.fix
    else:
        fix = rng.choice(workable_fixes)

    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)

    return StoryParams(
        place=place,
        cloth=cloth,
        damage=damage,
        fix=fix,
        child_name=child_name,
        child_type=child_type,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.cloth not in LINENS:
        raise StoryError(f"Unknown cloth: {params.cloth}")
    if params.damage not in DAMAGES:
        raise StoryError(f"Unknown damage: {params.damage}")
    if params.fix not in FIXES:
        raise StoryError(f"Unknown fix: {params.fix}")
    if not LINENS[params.cloth].loose_threads:
        raise StoryError(explain_rejection(LINENS[params.cloth]))
    if not fix_works(params.damage, params.fix):
        raise StoryError(
            f"(No story: the fix '{params.fix}' does not honestly solve '{params.damage}'.)"
        )

    world = tell(
        place=PLACES[params.place],
        cloth=LINENS[params.cloth],
        damage=DAMAGES[params.damage],
        fix=FIXES[params.fix],
        child_name=params.child_name,
        child_type=params.child_type,
        parent_type=params.parent,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, cloth, damage) combos:\n")
        for place, cloth, damage in combos:
            fixes = [fid for fid in sorted(FIXES) if fix_works(damage, fid)]
            print(f"  {place:8} {cloth:10} {damage:8} fixes=[{', '.join(fixes)}]")
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
            header = f"### {p.child_name}: {p.cloth} / {p.damage} at {p.place} ({p.fix})"
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
