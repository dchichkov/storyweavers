#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/collector_twist_bad_ending_transformation_heartwarming.py
====================================================================================

A standalone story world about a child who loves collecting little treasures.
One day the child picks up a beautiful object that looks like a perfect prize
for the collection, but the object actually belongs to someone and matters to
them. The middle turn goes badly: someone is upset because the missing thing is
needed. The twist is that the "best treasure" is not keeping pretty things, but
understanding what they mean to other people. The collector transforms into a
careful helper who returns things instead of pocketing them.

The world model keeps typed entities with physical meters and emotional memes,
uses a small forward-chaining rule engine, includes a Python reasonableness gate
plus an inline ASP twin, and renders complete TinyStories-style stories from
state.

Run it
------
    python storyworlds/worlds/gpt-5.4/collector_twist_bad_ending_transformation_heartwarming.py
    python storyworlds/worlds/gpt-5.4/collector_twist_bad_ending_transformation_heartwarming.py --place park --item collar_tag
    python storyworlds/worlds/gpt-5.4/collector_twist_bad_ending_transformation_heartwarming.py --place pond --item bike_bell
    python storyworlds/worlds/gpt-5.4/collector_twist_bad_ending_transformation_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/collector_twist_bad_ending_transformation_heartwarming.py --verify
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    owner: Optional[str] = None
    needed_for: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "grandmother", "sister"}
        male = {"boy", "father", "man", "brother", "grandfather"}
        animal = {"dog", "puppy", "cat", "kitten"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in animal:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.label or self.type)


@dataclass
class Place:
    id: str
    label: str
    detail: str
    allows: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class FoundItem:
    id: str
    label: str
    phrase: str
    shine: str
    owner_type: str
    owner_label: str
    owner_name_pool: list[str]
    lost_line: str
    need_line: str
    return_line: str
    consequence: str
    new_habit: str
    places: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class CollectorStyle:
    id: str
    container: str
    boast: str
    ending_object: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
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


def _r_missing_causes_distress(world: World) -> list[str]:
    out: list[str] = []
    item = world.entities.get("found_item")
    owner = world.entities.get("owner")
    collector = world.entities.get("collector")
    if not item or not owner or not collector:
        return out
    if item.meters["missing"] < THRESHOLD:
        return out
    sig = ("missing", item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    owner.memes["worry"] += 1
    owner.memes["sadness"] += 1
    collector.memes["guilt"] += 1
    out.append("__missing__")
    return out


def _r_return_heals(world: World) -> list[str]:
    out: list[str] = []
    item = world.entities.get("found_item")
    owner = world.entities.get("owner")
    collector = world.entities.get("collector")
    if not item or not owner or not collector:
        return out
    if item.meters["returned"] < THRESHOLD:
        return out
    sig = ("returned", item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    item.meters["missing"] = 0.0
    owner.memes["worry"] = 0.0
    owner.memes["sadness"] = 0.0
    owner.memes["relief"] += 1
    collector.memes["guilt"] = 0.0
    collector.memes["care"] += 1
    collector.memes["pride"] += 1
    out.append("__returned__")
    return out


CAUSAL_RULES = [
    Rule(name="missing_causes_distress", tag="social", apply=_r_missing_causes_distress),
    Rule(name="return_heals", tag="social", apply=_r_return_heals),
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
        for sent in produced:
            world.say(sent)
    return produced


def item_belongs_in_place(place_id: str, item_id: str) -> bool:
    return place_id in ITEMS[item_id].places


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for item_id, item in ITEMS.items():
            if not item_belongs_in_place(place_id, item_id):
                continue
            for style_id in STYLES:
                combos.append((place_id, item_id, style_id))
    return combos


def predict_sadness(world: World) -> dict:
    sim = world.copy()
    item = sim.get("found_item")
    item.meters["missing"] += 1
    propagate(sim, narrate=False)
    owner = sim.get("owner")
    collector = sim.get("collector")
    return {
        "owner_worry": owner.memes["worry"],
        "owner_sadness": owner.memes["sadness"],
        "collector_guilt": collector.memes["guilt"],
    }


def intro(world: World, collector: Entity, style: CollectorStyle) -> None:
    collector.memes["joy"] += 1
    world.say(
        f"{collector.id} was a little collector who loved bringing home tiny treasures. "
        f"{collector.pronoun('subject').capitalize()} kept them in {style.container} and "
        f"liked to {style.boast}."
    )
    world.say(
        f"On bright afternoons, {collector.pronoun('subject')} walked through {world.place.label}, "
        f"looking carefully at pebbles, petals, and other small wonders."
    )


def arrive(world: World) -> None:
    world.say(world.place.detail)


def notice_item(world: World, collector: Entity, item: FoundItem) -> None:
    collector.memes["desire"] += 1
    world.say(
        f"Near the path, {collector.pronoun('subject')} spotted {item.phrase}. "
        f"It {item.shine}, and to a collector it looked like the best find of all."
    )


def pocket_item(world: World, collector: Entity, item_ent: Entity, style: CollectorStyle) -> None:
    item_ent.owner = "collector"
    item_ent.meters["missing"] += 1
    collector.memes["greed"] += 1
    collector.meters["collected"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{collector.id} glanced around, slipped it into {style.container}, and hurried on. "
        f"For one moment, keeping it felt clever."
    )


def twist_scene(world: World, collector: Entity, owner: Entity, item: FoundItem) -> None:
    pred = predict_sadness(world)
    world.facts["predicted_owner_worry"] = pred["owner_worry"]
    world.facts["predicted_owner_sadness"] = pred["owner_sadness"]
    world.say(
        f"But around the next corner, {collector.id} heard a worried voice. "
        f'{owner.id} was looking around and saying, "{item.lost_line}"'
    )
    world.say(
        f"That was the twist: the shiny thing was not lost in the way {collector.id} had imagined. "
        f"{item.need_line}"
    )


def bad_turn(world: World, collector: Entity, owner: Entity, item: FoundItem) -> None:
    collector.memes["guilt"] += 1
    owner.memes["sadness"] += 1
    world.say(
        f"{collector.id}'s happy collecting feeling fell away. "
        f"Because the {item.label} was missing, {item.consequence}"
    )
    world.say(
        f"For a breath, the day felt spoiled, and {collector.pronoun('subject')} wished "
        f"{collector.pronoun('subject')} had not taken it."
    )


def confess_and_return(world: World, collector: Entity, owner: Entity, item_ent: Entity, item: FoundItem) -> None:
    item_ent.owner = "owner"
    item_ent.meters["returned"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{collector.id} walked back slowly, opened {collector.attrs.get('container', 'the container')}, "
        f"and held out the {item.label}. "
        f'"I am sorry," {collector.pronoun("subject")} said. "I thought it was a treasure for me, but it belongs to you."'
    )
    world.say(item.return_line.format(owner=owner.id, collector=collector.id))


def transform(world: World, collector: Entity, owner: Entity, style: CollectorStyle, item: FoundItem) -> None:
    collector.memes["care"] += 1
    collector.memes["joy"] += 1
    world.say(
        f"{owner.id} smiled then, and the warm smile changed something inside {collector.id}. "
        f"{collector.pronoun('subject').capitalize()} still loved noticing beautiful things, "
        f"but now {collector.pronoun('subject')} wanted to care for them, not just keep them."
    )
    world.say(
        f"From that day on, {collector.id} {item.new_habit}. "
        f"{collector.pronoun('subject').capitalize()} called that new collection {style.ending_object}."
    )


def ending_image(world: World, collector: Entity, owner: Entity, item: FoundItem) -> None:
    world.say(
        f"By sunset, {collector.id} was walking home with empty hands and a full heart. "
        f"The {item.label} was back where it was needed, {owner.id} was peaceful again, "
        f"and the little collector had turned into a careful helper."
    )


def tell(
    place: Place,
    item_cfg: FoundItem,
    style: CollectorStyle,
    collector_name: str = "Mila",
    collector_type: str = "girl",
    owner_name: str = "Mrs. Lane",
    seed_note: str = "",
) -> World:
    world = World(place)
    collector = world.add(
        Entity(
            id=collector_name,
            kind="character",
            type=collector_type,
            role="collector",
            label=collector_name,
            traits=["careful", "curious"],
            attrs={"container": style.container},
            tags={"collector"},
        )
    )
    owner = world.add(
        Entity(
            id=owner_name,
            kind="character",
            type=item_cfg.owner_type,
            role="owner",
            label=item_cfg.owner_label,
            tags=set(item_cfg.tags),
        )
    )
    item_ent = world.add(
        Entity(
            id="found_item",
            kind="thing",
            type="object",
            label=item_cfg.label,
            phrase=item_cfg.phrase,
            role="item",
            owner="owner",
            needed_for=item_cfg.consequence,
            tags=set(item_cfg.tags),
        )
    )

    world.facts["seed_note"] = seed_note

    intro(world, collector, style)
    arrive(world)
    notice_item(world, collector, item_cfg)

    world.para()
    pocket_item(world, collector, item_ent, style)
    twist_scene(world, collector, owner, item_cfg)
    bad_turn(world, collector, owner, item_cfg)

    world.para()
    confess_and_return(world, collector, owner, item_ent, item_cfg)
    transform(world, collector, owner, style, item_cfg)
    ending_image(world, collector, owner, item_cfg)

    world.facts.update(
        collector=collector,
        owner=owner,
        item_cfg=item_cfg,
        item=item_ent,
        place=place,
        style=style,
        transformed=collector.memes["care"] >= THRESHOLD,
        returned=item_ent.meters["returned"] >= THRESHOLD,
        middle_bad=True,
    )
    return world


@dataclass
class StoryParams:
    place: str
    item: str
    style: str
    collector_name: str
    collector_type: str
    owner_name: str
    seed: Optional[int] = None


PLACES = {
    "park": Place(
        id="park",
        label="the park",
        detail="The breeze moved the grass in soft waves, and the path curved past benches and a little gate.",
        allows={"collar_tag", "coat_button"},
        tags={"park"},
    ),
    "street": Place(
        id="street",
        label="the sidewalk by the little street",
        detail="Flower boxes sat under the windows, and bicycles clicked by with bright spokes in the sun.",
        allows={"bike_bell", "collar_tag", "coat_button"},
        tags={"street"},
    ),
    "garden": Place(
        id="garden",
        label="the community garden",
        detail="Tomato vines climbed their strings, and ladybugs moved through the leaves like red dots of paint.",
        allows={"coat_button"},
        tags={"garden"},
    ),
}

ITEMS = {
    "collar_tag": FoundItem(
        id="collar_tag",
        label="collar tag",
        phrase="a small silver collar tag shaped like a star",
        shine="winked in the sun",
        owner_type="woman",
        owner_label="the dog's owner",
        owner_name_pool=["Mrs. Lane", "Ms. Ivy", "Mrs. Bloom"],
        lost_line="Has anyone seen Pip's tag? If he runs too far, people will not know where he belongs.",
        need_line="Without the tag, a lost puppy could not be quickly brought back home.",
        return_line="{owner} took a breath of relief. \"Thank you for telling the truth,\" she said. \"Now Pip can wear his tag again and be safe.\"",
        consequence="the puppy could not wear the little name tag that helped strangers bring him home",
        new_habit="stopped putting other people's things into a jar and started making drawings of treasures that should stay where they belong",
        places={"park", "street"},
        tags={"dog", "tag", "truth"},
    ),
    "bike_bell": FoundItem(
        id="bike_bell",
        label="bike bell",
        phrase="a tiny brass bike bell with a painted blue stripe",
        shine="gleamed like a button of sunshine",
        owner_type="boy",
        owner_label="the bike rider",
        owner_name_pool=["Owen", "Ben", "Theo"],
        lost_line="My bell was right here. Without it, I cannot ring when I come around the corner.",
        need_line="It was part of a bicycle, and the rider needed it to warn people on the path.",
        return_line="{owner} fastened the bell back onto his handlebars and gave a grateful laugh. \"You helped my ride be safe again,\" he said.",
        consequence="the small bicycle had to stand still because riding without the bell felt unsafe",
        new_habit="began collecting kind acts instead, keeping count of every returned thing and every honest word",
        places={"street"},
        tags={"bike", "bell", "safety"},
    ),
    "coat_button": FoundItem(
        id="coat_button",
        label="coat button",
        phrase="a round amber coat button smooth as honey",
        shine="glowed warmly in the light",
        owner_type="grandmother",
        owner_label="the coat's owner",
        owner_name_pool=["Grandma May", "Grandma June", "Mrs. Fern"],
        lost_line="Oh dear, my coat button is gone. The wind keeps slipping right inside my coat.",
        need_line="It was not a loose trinket at all. It helped keep a coat closed and warm.",
        return_line="{owner} sewed the button back on with quick careful hands. \"You brought my warmth back,\" she said, giving {collector} a hug.",
        consequence="the coat hung open, and the chilly breeze kept getting in",
        new_habit="started a little notebook called 'Seen and Left Safe,' where beautiful things were remembered instead of taken",
        places={"park", "street", "garden"},
        tags={"coat", "button", "warmth"},
    ),
}

STYLES = {
    "jar": CollectorStyle(
        id="jar",
        container="a glass jam jar",
        boast="shake the jar softly and watch her treasures click together",
        ending_object='"the keep-with-your-eyes collection"',
        tags={"jar"},
    ),
    "box": CollectorStyle(
        id="box",
        container="a small painted box",
        boast="open the lid and line the treasures up in proud little rows",
        ending_object='"the kindness collection"',
        tags={"box"},
    ),
    "pocket": CollectorStyle(
        id="pocket",
        container="the deep pocket of a red cardigan",
        boast="pat the pocket and feel rich with small beautiful finds",
        ending_object='"the return-and-remember collection"',
        tags={"pocket"},
    ),
}

GIRL_NAMES = ["Mila", "Lily", "Nora", "Ella", "Zoe", "Anna"]
BOY_NAMES = ["Noah", "Ben", "Theo", "Eli", "Max", "Finn"]


KNOWLEDGE = {
    "collector": [
        (
            "What is a collector?",
            "A collector is someone who likes gathering special things and keeping them together. Good collectors still make sure the things they keep really belong to them.",
        )
    ],
    "truth": [
        (
            "Why is telling the truth important after a mistake?",
            "Telling the truth helps people fix the problem instead of staying confused or hurt. It can feel hard, but honesty is the first step toward making things right.",
        )
    ],
    "dog": [
        (
            "Why does a dog wear a name tag?",
            "A dog wears a name tag so people can tell who it belongs to if it gets lost. That helps the dog get home safely.",
        )
    ],
    "bike": [
        (
            "Why does a bike bell matter?",
            "A bike bell lets a rider warn other people nearby. That helps everyone share the path more safely.",
        )
    ],
    "coat": [
        (
            "What does a coat button do?",
            "A coat button helps hold the coat closed. That keeps warm air in and cold wind out.",
        )
    ],
}
KNOWLEDGE_ORDER = ["collector", "truth", "dog", "bike", "coat"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    collector = f["collector"]
    item = f["item_cfg"]
    place = f["place"]
    return [
        f'Write a heartwarming story for a 3-to-5-year-old about a little collector in {place.label} who finds a pretty {item.label}. Include the word "collector".',
        f"Tell a story where {collector.id} thinks {item.phrase} is a treasure to keep, but there is a twist: it belongs to someone and is needed.",
        f"Write a gentle transformation story with a sad middle turn, an apology, and an ending where the child changes from keeping pretty things to caring for people.",
    ]


def story_qa_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    collector = f["collector"]
    owner = f["owner"]
    item = f["item_cfg"]
    place = f["place"]
    style = f["style"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {collector.id}, a little collector, and {owner.id}, who needed a missing {item.label}. The story follows how {collector.id} changed after understanding that.",
        ),
        (
            f"What did {collector.id} find in {place.label}?",
            f"{collector.id} found {item.phrase}. It looked bright and special, so at first it seemed like the perfect thing for {style.container}.",
        ),
        (
            f"What was the twist in the story?",
            f"The twist was that the shiny {item.label} was not a free treasure at all. It belonged to {owner.id} and had an important job to do.",
        ),
        (
            f"Why did the story feel sad in the middle?",
            f"It felt sad because the {item.label} was missing and that caused a real problem. {item.need_line} That is why {collector.id} started to feel guilty instead of proud.",
        ),
        (
            f"How did {collector.id} fix the mistake?",
            f"{collector.id} told the truth and gave the {item.label} back. Returning it stopped the worry and showed that {collector.pronoun('subject')} cared more about helping than keeping.",
        ),
        (
            f"How did {collector.id} change by the end?",
            f"By the end, {collector.id} was still a collector, but a different kind. Instead of taking every pretty thing, {collector.pronoun('subject')} learned to notice beauty, leave needed things in place, and help return what belongs to others.",
        ),
    ]
    return qa


def world_knowledge_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"collector"} | set(f["item_cfg"].tags)
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="park",
        item="collar_tag",
        style="jar",
        collector_name="Mila",
        collector_type="girl",
        owner_name="Mrs. Lane",
    ),
    StoryParams(
        place="street",
        item="bike_bell",
        style="box",
        collector_name="Noah",
        collector_type="boy",
        owner_name="Theo",
    ),
    StoryParams(
        place="garden",
        item="coat_button",
        style="pocket",
        collector_name="Ella",
        collector_type="girl",
        owner_name="Grandma May",
    ),
]


def explain_rejection(place_id: str, item_id: str) -> str:
    place = PLACES[place_id]
    item = ITEMS[item_id]
    return (
        f"(No story: {item.phrase} does not fit {place.label} in this little world. "
        f"That object belongs in {sorted(item.places)}, so the missing-owner problem would not feel grounded there.)"
    )


ASP_RULES = r"""
valid(P, I, S) :- place(P), item(I), style(S), allowed(I, P).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        for place_id in sorted(item.places):
            lines.append(asp.fact("allowed", item_id, place_id))
    for style_id in STYLES:
        lines.append(asp.fact("style", style_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "collector" not in sample.story.lower():
            raise StoryError("Generated story missing expected content.")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a collector finds the wrong treasure, learns the truth, and changes."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--style", choices=STYLES)
    ap.add_argument("--collector-name")
    ap.add_argument("--collector-type", choices=["girl", "boy"])
    ap.add_argument("--owner-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.item and not item_belongs_in_place(args.place, args.item):
        raise StoryError(explain_rejection(args.place, args.item))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.item is None or combo[1] == args.item)
        and (args.style is None or combo[2] == args.style)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, item_id, style_id = rng.choice(sorted(combos))
    collector_type = args.collector_type or rng.choice(["girl", "boy"])
    collector_name = args.collector_name or rng.choice(GIRL_NAMES if collector_type == "girl" else BOY_NAMES)
    owner_name = args.owner_name or rng.choice(ITEMS[item_id].owner_name_pool)
    return StoryParams(
        place=place_id,
        item=item_id,
        style=style_id,
        collector_name=collector_name,
        collector_type=collector_type,
        owner_name=owner_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.style not in STYLES:
        raise StoryError(f"(Unknown style: {params.style})")
    if not item_belongs_in_place(params.place, params.item):
        raise StoryError(explain_rejection(params.place, params.item))

    world = tell(
        place=PLACES[params.place],
        item_cfg=ITEMS[params.item],
        style=STYLES[params.style],
        collector_name=params.collector_name,
        collector_type=params.collector_type,
        owner_name=params.owner_name,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_pairs(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_pairs(world)],
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, item, style) combos:\n")
        for place_id, item_id, style_id in combos:
            print(f"  {place_id:8} {item_id:12} {style_id}")
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
            header = f"### {p.collector_name}: {p.item} at {p.place} ({p.style})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
