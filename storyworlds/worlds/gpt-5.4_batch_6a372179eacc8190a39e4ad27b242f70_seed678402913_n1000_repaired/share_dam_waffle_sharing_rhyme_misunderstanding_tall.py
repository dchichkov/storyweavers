#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/share_dam_waffle_sharing_rhyme_misunderstanding_tall.py
===================================================================================

A standalone storyworld for a tall-tale misunderstanding about sharing a giant
waffle near a dam. The child-facing shape is:

    huge waffle + breezy rhyme + noisy dam -> misunderstanding
    misunderstanding changes the world      -> little trouble
    calm helper explains the rhyme          -> sharing fix
    ending image proves what changed        -> everyone shares

This world keeps the domain deliberately small and concrete. Every generated
story includes the words "share", "dam", and "waffle", and every story uses:
Sharing, Rhyme, and Misunderstanding in a Tall Tale style.

Run it
------
    python storyworlds/worlds/gpt-5.4/share_dam_waffle_sharing_rhyme_misunderstanding_tall.py
    python storyworlds/worlds/gpt-5.4/share_dam_waffle_sharing_rhyme_misunderstanding_tall.py --place beaver_dam
    python storyworlds/worlds/gpt-5.4/share_dam_waffle_sharing_rhyme_misunderstanding_tall.py --noise quiet
    python storyworlds/worlds/gpt-5.4/share_dam_waffle_sharing_rhyme_misunderstanding_tall.py --all
    python storyworlds/worlds/gpt-5.4/share_dam_waffle_sharing_rhyme_misunderstanding_tall.py --qa
    python storyworlds/worlds/gpt-5.4/share_dam_waffle_sharing_rhyme_misunderstanding_tall.py --verify
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
    traits: list[str] = field(default_factory=list)
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
        return {
            "mother": "mom",
            "father": "dad",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    water: str
    structure: str
    sound: str
    animal: str
    huge_detail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Noise:
    id: str
    label: str
    allows_mishear: bool
    line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class RhymeCue:
    id: str
    heard: str
    meant: str
    action: str
    repair: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    success: str
    ending: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_wet_feelings(world: World) -> list[str]:
    out: list[str] = []
    if "dam" not in world.entities or "waffle" not in world.entities:
        return out
    dam = world.get("dam")
    waffle = world.get("waffle")
    if dam.meters["blocked"] >= THRESHOLD:
        sig = ("blocked",)
        if sig not in world.fired:
            world.fired.add(sig)
            dam.meters["overflow"] += 1
            world.get("hero").memes["surprise"] += 1
            world.get("friend").memes["worry"] += 1
            out.append("__blocked__")
    if waffle.meters["wet"] >= THRESHOLD:
        sig = ("wet",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("hero").memes["embarrassment"] += 1
            world.get("friend").memes["hunger"] += 1
            out.append("__wet__")
    return out


CAUSAL_RULES = [
    Rule(name="wet_feelings", tag="physical", apply=_r_wet_feelings),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(bits)
    if narrate:
        for bit in produced:
            if bit == "__blocked__":
                world.say("At once the water huffed and puffed against the little dam.")
            elif bit == "__wet__":
                world.say("A few waffle crumbs got splashed, and breakfast looked less grand than before.")
    return produced


PLACES = {
    "beaver_dam": Place(
        id="beaver_dam",
        label="the beaver dam",
        water="the creek",
        structure="a neat little wall of sticks",
        sound="the creek chattering over sticks",
        animal="beavers",
        huge_detail="The giant waffle on the picnic cloth looked almost as wide as the moon and nearly as round.",
        tags={"dam", "beaver"},
    ),
    "mill_dam": Place(
        id="mill_dam",
        label="the old mill dam",
        water="the river",
        structure="a broad stone wall holding back the river",
        sound="the river drumming against stone",
        animal="ducks",
        huge_detail="The giant waffle on the picnic cloth was so big it could have worn a scarecrow for a hat.",
        tags={"dam", "river"},
    ),
    "sand_dam": Place(
        id="sand_dam",
        label="the sandy play dam",
        water="the stream",
        structure="a child-sized ridge of packed sand and pebbles",
        sound="the stream whispering through pebbles",
        animal="frogs",
        huge_detail="The giant waffle on the picnic cloth looked like a golden wagon wheel fresh from the sunrise bakery.",
        tags={"dam", "stream"},
    ),
}

NOISES = {
    "breezy": Noise(
        id="breezy",
        label="breezy",
        allows_mishear=True,
        line="The wind kept tugging words into rhymes and tossing them about like leaves.",
        tags={"rhyme", "wind"},
    ),
    "rushing": Noise(
        id="rushing",
        label="rushing",
        allows_mishear=True,
        line="The rushing water made every sentence wobble and bounce before it reached another ear.",
        tags={"rhyme", "water"},
    ),
    "quiet": Noise(
        id="quiet",
        label="quiet",
        allows_mishear=False,
        line="The air was so still that even the crumbs seemed to listen.",
        tags={"quiet"},
    ),
}

RHYMES = {
    "share_spare": RhymeCue(
        id="share_spare",
        heard='"Spare the dam waffle!"',
        meant='"Share the waffle by the dam!"',
        action="tries to tuck the waffle behind the dam so nobody will nibble it first",
        repair="The friend laughed and explained that share and spare sound alike in noisy air, but they mean different things.",
        tags={"share", "rhyme", "misunderstanding"},
    ),
    "share_shore": RhymeCue(
        id="share_shore",
        heard='"Shore the dam with waffle!"',
        meant='"Share the waffle by the dam!"',
        action="starts patching the edge of the dam with waffle squares as if breakfast were a brick wall",
        repair="The helper pointed to the picnic cloth and said that share means give some to others, not build a shore out of breakfast.",
        tags={"share", "rhyme", "misunderstanding"},
    ),
    "share_chair": RhymeCue(
        id="share_chair",
        heard='"Chair the dam waffle!"',
        meant='"Share the waffle by the dam!"',
        action="leans the waffle against a stump like a crunchy golden throne beside the dam",
        repair="The friend grinned and said the rhyme had tickled the ears the wrong way; nobody needed a waffle chair, only a fair share.",
        tags={"share", "rhyme", "misunderstanding"},
    ),
}

FIXES = {
    "blanket_circle": Fix(
        id="blanket_circle",
        label="blanket circle",
        success="They carried the giant waffle back to the picnic blanket, cut it into neat sunny squares, and passed them around in a circle.",
        ending="Soon everyone sat knee to knee on the blanket, and even the air seemed full of happy chewing and easy laughter.",
        tags={"share", "picnic"},
    ),
    "flat_stone": Fix(
        id="flat_stone",
        label="flat stone table",
        success="They set the waffle on a flat stone, snapped off crisp corners, and made sure each waiting hand got one first.",
        ending="In the end the stone looked like a tiny feast table, and every face around it wore syrupy smiles.",
        tags={"share", "stone"},
    ),
    "basket_boat": Fix(
        id="basket_boat",
        label="basket boat",
        success="They put the waffle pieces in a picnic basket and ferried them across the grass from child to child like a slow, careful boat.",
        ending="By the last crumb, the basket had made a full round and the morning felt roomy enough for everybody.",
        tags={"share", "basket"},
    ),
}


def misunderstanding_possible(place: Place, noise: Noise, rhyme: RhymeCue) -> bool:
    return noise.allows_mishear and "dam" in place.tags and "share" in rhyme.tags


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for noise_id, noise in NOISES.items():
            for rhyme_id, rhyme in RHYMES.items():
                for fix_id in FIXES:
                    if misunderstanding_possible(place, noise, rhyme):
                        combos.append((place_id, noise_id, rhyme_id, fix_id))
    return combos


@dataclass
class StoryParams:
    place: str
    noise: str
    rhyme: str
    fix: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    helper_type: str
    hero_trait: str
    friend_trait: str
    seed: Optional[int] = None


GIRL_NAMES = ["Mabel", "Clara", "Nell", "Ada", "Ruby", "June", "Tess", "Maisie"]
BOY_NAMES = ["Hank", "Jasper", "Eli", "Finn", "Otis", "Milo", "Beau", "Cal"]
TRAITS = ["long-legged", "big-hearted", "lanky", "cheerful", "barn-strong", "sunny"]

CURATED = [
    StoryParams(
        place="beaver_dam",
        noise="breezy",
        rhyme="share_spare",
        fix="blanket_circle",
        hero_name="Mabel",
        hero_gender="girl",
        friend_name="Hank",
        friend_gender="boy",
        helper_type="aunt",
        hero_trait="long-legged",
        friend_trait="cheerful",
        seed=1,
    ),
    StoryParams(
        place="mill_dam",
        noise="rushing",
        rhyme="share_shore",
        fix="flat_stone",
        hero_name="Jasper",
        hero_gender="boy",
        friend_name="Ruby",
        friend_gender="girl",
        helper_type="uncle",
        hero_trait="barn-strong",
        friend_trait="big-hearted",
        seed=2,
    ),
    StoryParams(
        place="sand_dam",
        noise="breezy",
        rhyme="share_chair",
        fix="basket_boat",
        hero_name="Clara",
        hero_gender="girl",
        friend_name="Otis",
        friend_gender="boy",
        helper_type="mother",
        hero_trait="lanky",
        friend_trait="sunny",
        seed=3,
    ),
]


def predict_misunderstanding(world: World, rhyme: RhymeCue) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    dam = sim.get("dam")
    waffle = sim.get("waffle")
    hero.memes["misheard"] += 1
    dam.meters["blocked"] += 1
    waffle.meters["moved"] += 1
    waffle.meters["wet"] += 1
    propagate(sim, narrate=False)
    return {
        "blocked": dam.meters["blocked"] >= THRESHOLD,
        "wet": waffle.meters["wet"] >= THRESHOLD,
        "action": rhyme.action,
    }


def introduce(world: World, hero: Entity, friend: Entity, place: Place, helper: Entity) -> None:
    world.say(
        f"In a valley so roomy that thunder had to take two trips to cross it, "
        f"{hero.id} was a {next(iter([t for t in hero.traits if t]))} {hero.type} "
        f"whose legs could step over rain barrels when {hero.pronoun()} felt polite."
    )
    world.say(
        f"{friend.id}, {hero.pronoun('possessive')} friend, could laugh a fence post loose, "
        f"and {helper.label_word} said the two of them made more commotion than a brass band of geese."
    )
    world.say(
        f"One bright morning they spread a cloth beside {place.label}, where {place.sound} "
        f"never stopped talking. {place.huge_detail}"
    )


def setup_waffle(world: World, hero: Entity, friend: Entity, place: Place) -> None:
    hero.memes["generosity"] += 1
    friend.memes["hunger"] += 1
    world.say(
        f"{hero.id} had brought a waffle so grand that the butter slid across it like a sled on a golden hill."
    )
    world.say(
        f'"We should share this waffle by the dam," {friend.id} said, patting the cloth beside {place.structure}.'
    )


def noise_beat(world: World, noise: Noise) -> None:
    world.say(noise.line)


def mishear(world: World, hero: Entity, friend: Entity, place: Place, rhyme: RhymeCue) -> None:
    pred = predict_misunderstanding(world, rhyme)
    world.facts["predicted_blocked"] = pred["blocked"]
    world.facts["predicted_wet"] = pred["wet"]
    world.facts["heard_line"] = rhyme.heard
    hero.memes["misheard"] += 1
    world.say(
        f"But the words bumped into the wind and water, came back crooked, and {hero.id} heard {rhyme.heard}"
    )
    world.say(
        f"So {hero.pronoun()} {rhyme.action}. {friend.id} blinked so hard you could almost hear the eyelashes clap."
    )
    dam = world.get("dam")
    waffle = world.get("waffle")
    dam.meters["blocked"] += 1
    waffle.meters["moved"] += 1
    waffle.meters["wet"] += 1
    propagate(world, narrate=True)


def trouble(world: World, hero: Entity, friend: Entity, place: Place) -> None:
    overflow = world.get("dam").meters["overflow"] >= THRESHOLD
    if overflow:
        world.say(
            f"A puddly ribbon of {place.water} curled around the waffle, and a pair of {place.animal} stared as if breakfast had become a very foolish kind of bridge."
        )
    world.say(
        f'"No, no," cried {friend.id}. "I said share, not hide or stack or throne it!"'
    )


def explain_and_repair(world: World, hero: Entity, friend: Entity, helper: Entity, rhyme: RhymeCue) -> None:
    hero.memes["embarrassment"] += 1
    friend.memes["care"] += 1
    helper.memes["calm"] += 1
    world.say(
        f"{helper.label_word.capitalize()} came over with a syrup jar in one hand and patience in the other."
    )
    world.say(
        f"{rhyme.repair} Then {helper.pronoun()} brushed a damp crumb from the waffle and added, "
        f'"A rhyme can bounce, but kindness must land straight."'
    )
    world.say(
        f"{hero.id}'s ears turned as warm as toast. {hero.pronoun().capitalize()} looked at {friend.id} and nodded."
    )


def share_fix(world: World, hero: Entity, friend: Entity, helper: Entity, fix: Fix) -> None:
    waffle = world.get("waffle")
    dam = world.get("dam")
    waffle.meters["wet"] = 0.0
    waffle.meters["shared"] += 1
    waffle.meters["pieces"] += 1
    dam.meters["blocked"] = 0.0
    dam.meters["overflow"] = 0.0
    hero.memes["generosity"] += 1
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    helper.memes["pride"] += 1
    world.say(fix.success)
    world.say(
        f'{hero.id} made sure {friend.id} got the first piece. "{friend.id} heard the right words first," {hero.pronoun()} said, and that made everybody smile.'
    )
    world.say(fix.ending)


def ending_image(world: World, place: Place) -> None:
    world.say(
        f"After that, {place.label} kept humming its watery tune, the waffle crumbs vanished by honest bites instead of foolish confusion, and the morning stood tall and sweet."
    )


def tell(
    place: Place,
    noise: Noise,
    rhyme: RhymeCue,
    fix: Fix,
    hero_name: str,
    hero_gender: str,
    friend_name: str,
    friend_gender: str,
    helper_type: str,
    hero_trait: str,
    friend_trait: str,
) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        role="hero",
        traits=[hero_trait],
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_gender,
        role="friend",
        traits=[friend_trait],
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        label="the helper",
        role="helper",
    ))
    world.add(Entity(
        id="dam",
        type="dam",
        label=place.label,
        phrase=place.structure,
        tags=set(place.tags),
    ))
    world.add(Entity(
        id="waffle",
        type="waffle",
        label="waffle",
        phrase="the giant waffle",
        tags={"waffle", "share"},
    ))

    introduce(world, hero, friend, place, helper)
    setup_waffle(world, hero, friend, place)

    world.para()
    noise_beat(world, noise)
    mishear(world, hero, friend, place, rhyme)
    trouble(world, hero, friend, place)

    world.para()
    explain_and_repair(world, hero, friend, helper, rhyme)
    share_fix(world, hero, friend, helper, fix)
    ending_image(world, place)

    world.facts.update(
        hero=hero,
        friend=friend,
        helper=helper,
        place=place,
        noise=noise,
        rhyme=rhyme,
        fix=fix,
        waffle=world.get("waffle"),
        dam=world.get("dam"),
        misunderstood=hero.memes["misheard"] >= THRESHOLD,
        shared=world.get("waffle").meters["shared"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "waffle": [(
        "What is a waffle?",
        "A waffle is a round or square breakfast cake cooked between hot plates, so it gets little pockets that can hold butter or syrup."
    )],
    "dam": [(
        "What is a dam?",
        "A dam is something that holds back or slows water. Some dams are built by people, and some little ones are built by beavers."
    )],
    "share": [(
        "What does share mean?",
        "To share means to let other people have some too. It is a kind way to enjoy one thing together."
    )],
    "rhyme": [(
        "What is a rhyme?",
        "A rhyme is when words sound alike, like share and spare. Rhymes can be fun, but they do not always mean the same thing."
    )],
    "misunderstanding": [(
        "What is a misunderstanding?",
        "A misunderstanding happens when someone hears or understands something the wrong way. Talking calmly can straighten it out."
    )],
    "beaver": [(
        "Why do beavers build dams?",
        "Beavers build dams to slow water and make safer ponds near their homes. They use sticks, mud, and hard work."
    )],
}
KNOWLEDGE_ORDER = ["waffle", "dam", "share", "rhyme", "misunderstanding", "beaver"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    place = f["place"]
    rhyme = f["rhyme"]
    return [
        'Write a short Tall Tale for a 3-to-5-year-old that includes the words "share", "dam", and "waffle".',
        f"Tell a tall, child-friendly story where {hero.id} and {friend.id} bring a giant waffle to {place.label}, but a rhyming misunderstanding makes trouble before they learn to share properly.",
        f"Write a playful story where the line {rhyme.meant} is misheard near noisy water, and the ending shows kindness winning over confusion.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    helper = f["helper"]
    place = f["place"]
    rhyme = f["rhyme"]
    fix = f["fix"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} and {friend.id}, who brought a giant waffle to {place.label}, and {helper.label_word} who helped them sort out the trouble."
        ),
        (
            "What made the story feel like a tall tale?",
            f"The waffle was described as enormous, and the children were described in big, funny, impossible ways. Those grand exaggerations make the story feel playful and larger than life."
        ),
        (
            f"What misunderstanding happened near {place.label}?",
            f"{friend.id} meant to say {rhyme.meant}, but the wind and water bent the words. {hero.id} heard {rhyme.heard}, so {hero.pronoun()} used the waffle the wrong way instead of sharing it."
        ),
        (
            "Why was that a problem?",
            f"The misunderstanding put the waffle too close to the dam and the water, so breakfast started turning soggy and silly. It also meant nobody was sharing yet, even though sharing was the whole idea."
        ),
        (
            "How was the problem solved?",
            f"{helper.label_word.capitalize()} explained that rhyming words can sound alike without meaning the same thing. Then {fix.success.lower()} That turned the mixed-up moment into a fair, happy meal."
        ),
        (
            "How did the story end?",
            f"It ended with everyone calmly sharing the waffle while the dam stayed just as it should. The final image shows that the confusion was gone and kindness was bigger than the mistake."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"waffle", "dam", "share", "rhyme", "misunderstanding"}
    place = world.facts["place"]
    if "beaver" in place.tags:
        tags.add("beaver")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(x[0] if isinstance(x, tuple) else x for x in world.fired))}")
    return "\n".join(lines)


def explain_rejection(place: Place, noise: Noise, rhyme: RhymeCue) -> str:
    if not noise.allows_mishear:
        return (
            f"(No story: {place.label} with {noise.label} air does not support a believable misunderstanding. "
            f"This world needs noisy water or wind so the rhyme can be misheard.)"
        )
    if "share" not in rhyme.tags:
        return "(No story: this rhyme does not support the sharing misunderstanding the world is built around.)"
    return "(No story: the chosen options do not make a believable misunderstanding.)"


ASP_RULES = r"""
misunderstanding_possible(P, N, R) :- place(P), noise(N), rhyme(R),
                                      allows_mishear(N), place_has_dam(P), rhyme_has_share(R).

valid(P, N, R, F) :- misunderstanding_possible(P, N, R), fix(F).

outcome(shared_end) :- chosen_place(P), chosen_noise(N), chosen_rhyme(R), chosen_fix(F),
                       valid(P, N, R, F).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        if "dam" in place.tags:
            lines.append(asp.fact("place_has_dam", place_id))
    for noise_id, noise in NOISES.items():
        lines.append(asp.fact("noise", noise_id))
        if noise.allows_mishear:
            lines.append(asp.fact("allows_mishear", noise_id))
    for rhyme_id, rhyme in RHYMES.items():
        lines.append(asp.fact("rhyme", rhyme_id))
        if "share" in rhyme.tags:
            lines.append(asp.fact("rhyme_has_share", rhyme_id))
    for fix_id in FIXES:
        lines.append(asp.fact("fix", fix_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_place", params.place),
        asp.fact("chosen_noise", params.noise),
        asp.fact("chosen_rhyme", params.rhyme),
        asp.fact("chosen_fix", params.fix),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale storyworld: a giant waffle, a dam, a rhyme, and a sharing misunderstanding."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--noise", choices=NOISES)
    ap.add_argument("--rhyme", choices=RHYMES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--helper", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.noise and args.rhyme:
        place = PLACES[args.place]
        noise = NOISES[args.noise]
        rhyme = RHYMES[args.rhyme]
        if not misunderstanding_possible(place, noise, rhyme):
            raise StoryError(explain_rejection(place, noise, rhyme))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.noise is None or combo[1] == args.noise)
        and (args.rhyme is None or combo[2] == args.rhyme)
        and (args.fix is None or combo[3] == args.fix)
    ]
    if not combos:
        place = PLACES[args.place] if args.place else next(iter(PLACES.values()))
        noise = NOISES[args.noise] if args.noise else next(iter(NOISES.values()))
        rhyme = RHYMES[args.rhyme] if args.rhyme else next(iter(RHYMES.values()))
        raise StoryError(explain_rejection(place, noise, rhyme))

    place_id, noise_id, rhyme_id, fix_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    friend_name = args.friend_name or _pick_name(rng, friend_gender, avoid=hero_name)
    helper_type = args.helper or rng.choice(["mother", "father", "aunt", "uncle"])
    hero_trait = rng.choice(TRAITS)
    friend_trait = rng.choice([t for t in TRAITS if t != hero_trait] or TRAITS)
    return StoryParams(
        place=place_id,
        noise=noise_id,
        rhyme=rhyme_id,
        fix=fix_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        helper_type=helper_type,
        hero_trait=hero_trait,
        friend_trait=friend_trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        noise = NOISES[params.noise]
        rhyme = RHYMES[params.rhyme]
        fix = FIXES[params.fix]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter: {err.args[0]!r} is not a known registry key.)") from err

    if not misunderstanding_possible(place, noise, rhyme):
        raise StoryError(explain_rejection(place, noise, rhyme))

    world = tell(
        place=place,
        noise=noise,
        rhyme=rhyme,
        fix=fix,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        helper_type=params.helper_type,
        hero_trait=params.hero_trait,
        friend_trait=params.friend_trait,
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


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    for params in CURATED:
        outcome = asp_outcome(params)
        if outcome != "shared_end":
            rc = 1
            print(f"MISMATCH in outcome for curated params: {params} -> {outcome}")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, noise, rhyme, fix) combos:\n")
        for place, noise, rhyme, fix in combos:
            print(f"  {place:10} {noise:8} {rhyme:12} {fix}")
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
            header = f"### {p.hero_name} and {p.friend_name}: {p.rhyme} at {p.place} ({p.fix})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
