#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/final_foreshadowing_humor_reconciliation_tall_tale.py
=================================================================================

A standalone story world for a child-facing tall tale about an enormous kite, a
hurt friendship, a comic near-disaster, and a happy reconciliation before the
final cheer of the fair.

The world model is intentionally small and classical:

- typed entities with physical meters and emotional memes
- a simple reasonableness gate over wind, place, kite size, and line strength
- a state-driven screenplay with foreshadowing, humor, and reconciliation
- a matching inline ASP twin for the compatibility gate and the outcome model

Run it
------
    python storyworlds/worlds/gpt-5.4/final_foreshadowing_humor_reconciliation_tall_tale.py
    python storyworlds/worlds/gpt-5.4/final_foreshadowing_humor_reconciliation_tall_tale.py --place fairground --kite rooster --wind blustery --line porch_rope
    python storyworlds/worlds/gpt-5.4/final_foreshadowing_humor_reconciliation_tall_tale.py --line clothesline --kite moon --wind blustery
    python storyworlds/worlds/gpt-5.4/final_foreshadowing_humor_reconciliation_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4/final_foreshadowing_humor_reconciliation_tall_tale.py --verify
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
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
class Place:
    id: str
    label: str
    gusts: set[str] = field(default_factory=set)
    event: str = ""
    ground: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class KiteCfg:
    id: str
    label: str
    phrase: str
    shape_line: str
    tail_line: str
    weight: int
    tags: set[str] = field(default_factory=set)


@dataclass
class WindCfg:
    id: str
    label: str
    force: int
    opening: str
    omen: str
    tags: set[str] = field(default_factory=set)


@dataclass
class LineCfg:
    id: str
    label: str
    phrase: str
    strength: int
    boast: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    kite: str
    wind: str
    line: str
    hero_name: str
    hero_gender: str
    rival_name: str
    rival_gender: str
    elder_type: str
    hero_trait: str
    seed: Optional[int] = None


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


def required_strength(kite: KiteCfg, wind: WindCfg) -> int:
    return kite.weight + wind.force


def margin_of(line: LineCfg, kite: KiteCfg, wind: WindCfg) -> int:
    return line.strength - required_strength(kite, wind)


def place_supports(place: Place, wind: WindCfg) -> bool:
    return wind.id in place.gusts


def combo_is_valid(place: Place, kite: KiteCfg, wind: WindCfg, line: LineCfg) -> bool:
    return place_supports(place, wind) and line.strength >= required_strength(kite, wind)


def outcome_of(params: StoryParams) -> str:
    kite = KITES.get(params.kite)
    wind = WINDS.get(params.wind)
    line = LINES.get(params.line)
    place = PLACES.get(params.place)
    if not all([kite, wind, line, place]):
        raise StoryError("(Invalid params: unknown place, kite, wind, or line.)")
    if not combo_is_valid(place, kite, wind, line):
        raise StoryError(explain_rejection(place, kite, wind, line))
    return "smooth" if margin_of(line, kite, wind) >= 1 else "scramble"


def _r_pull(world: World) -> list[str]:
    kite = world.facts["kite_cfg"]
    wind = world.facts["wind_cfg"]
    line = world.facts["line_cfg"]
    hero = world.get("hero")
    rival = world.get("rival")
    sig = ("pull", kite.id, wind.id, line.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    need = required_strength(kite, wind)
    hero.meters["pull"] += float(need)
    hero.memes["alarm"] += 1
    if line.strength == need:
        hero.meters["dragged"] += 1
        hero.memes["embarrassment"] += 1
        rival.memes["concern"] += 1
        return ["__scramble__"]
    hero.meters["steady"] += 1
    rival.memes["concern"] += 1
    return ["__steady__"]


CAUSAL_RULES = [
    Rule(name="pull", tag="physical", apply=_r_pull),
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


PLACES = {
    "fairground": Place(
        id="fairground",
        label="the Windberry fairground",
        gusts={"breezy", "blustery"},
        event="the final cheer of the fair",
        ground="between the pie tent and the music wagon",
        tags={"fair"},
    ),
    "hill": Place(
        id="hill",
        label="the high hill above town",
        gusts={"breezy", "blustery"},
        event="the final sunset clap",
        ground="where the grass leaned in one long green wave",
        tags={"hill"},
    ),
    "orchard": Place(
        id="orchard",
        label="the orchard edge",
        gusts={"breezy"},
        event="the final lantern lighting",
        ground="beside the rows of apple trees",
        tags={"orchard"},
    ),
}

KITES = {
    "rooster": KiteCfg(
        id="rooster",
        label="rooster kite",
        phrase="a rooster kite so big it could have crowed at the moon",
        shape_line="Its painted beak stuck out proud as a weather vane.",
        tail_line="Its tail streamed behind it in ribbons as long as laundry day.",
        weight=2,
        tags={"kite", "rooster"},
    ),
    "catfish": KiteCfg(
        id="catfish",
        label="catfish kite",
        phrase="a catfish kite broad enough to throw shade on a goat cart",
        shape_line="Its whiskers curled like two fishing poles that had learned to grin.",
        tail_line="Its tail fluttered like a river of blue neckties.",
        weight=2,
        tags={"kite", "catfish"},
    ),
    "moon": KiteCfg(
        id="moon",
        label="moon kite",
        phrase="a moon kite round enough to look like somebody had ironed the sky",
        shape_line="Its silver face shone with one wink painted in the corner.",
        tail_line="Its tail was stitched from yellow bows that flipped like tiny stars.",
        weight=3,
        tags={"kite", "moon"},
    ),
}

WINDS = {
    "breezy": WindCfg(
        id="breezy",
        label="a breezy afternoon",
        force=1,
        opening="The breeze was skipping along just fast enough to lift hats and spirits.",
        omen="Even the weathercock kept nodding as if it knew a joke ahead of time.",
        tags={"wind"},
    ),
    "blustery": WindCfg(
        id="blustery",
        label="a blustery afternoon",
        force=2,
        opening="The wind came bowling over the fields with both sleeves rolled up.",
        omen="Fence posts hummed, and every loose ribbon practiced running away.",
        tags={"wind"},
    ),
}

LINES = {
    "clothesline": LineCfg(
        id="clothesline",
        label="clothesline",
        phrase="an old clothesline from the backyard",
        strength=3,
        boast="claimed it was stout enough to tow a sleepy mule",
        tags={"line", "clothesline"},
    ),
    "porch_rope": LineCfg(
        id="porch_rope",
        label="porch rope",
        phrase="the thick porch rope from the swing",
        strength=4,
        boast="said it was strong enough to lasso a cloud and ask it to dance",
        tags={"line", "rope"},
    ),
    "boat_rope": LineCfg(
        id="boat_rope",
        label="boat rope",
        phrase="the braided boat rope from the creek dock",
        strength=5,
        boast="swore it could hold the whole county if the county tried to blow away",
        tags={"line", "rope"},
    ),
}

GIRL_NAMES = ["Ada", "Nell", "Molly", "June", "Tessa", "Ruth", "Ivy", "Mabel"]
BOY_NAMES = ["Eli", "Hank", "Jasper", "Otis", "Beau", "Cal", "Ned", "Wes"]
TRAITS = ["bold", "cheerful", "stubborn", "clever", "lively", "showy"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for kite_id, kite in KITES.items():
            for wind_id, wind in WINDS.items():
                for line_id, line in LINES.items():
                    if combo_is_valid(place, kite, wind, line):
                        out.append((place_id, kite_id, wind_id, line_id))
    return sorted(out)


def explain_rejection(place: Place, kite: KiteCfg, wind: WindCfg, line: LineCfg) -> str:
    if not place_supports(place, wind):
        allowed = ", ".join(sorted(place.gusts))
        return (
            f"(No story: {place.label} does not get a {wind.label} in this little world. "
            f"Try one of these winds there: {allowed}.)"
        )
    need = required_strength(kite, wind)
    return (
        f"(No story: {line.phrase} is too weak for the {kite.label} in {wind.label}. "
        f"It holds strength {line.strength}, but the kite needs {need}. "
        f"Choose a stronger line or a lighter kite.)"
    )


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def foreshadow(world: World, hero: Entity, rival: Entity, elder: Entity, kite: KiteCfg, wind: WindCfg, line: LineCfg) -> None:
    need = required_strength(kite, wind)
    world.facts["need"] = need
    world.say(
        f"{wind.opening} {wind.omen}"
    )
    world.say(
        f'{elder.label_word.capitalize()} squinted at {line.phrase} and said, '
        f'"A kite that grand likes two good hands and a line that means what it says."'
    )
    if margin_of(line, kite, wind) == 0:
        world.say(
            f"The rope gave one long hum. It sounded almost like it was clearing its throat before trouble."
        )
    else:
        world.say(
            f"The line stayed solid, but it twitched in the gusts as if reminding everybody that bragging and holding on were not the same chore."
        )
    hero.memes["warning"] += 1
    rival.memes["hurt"] += 1


def build_kite(world: World, hero: Entity, rival: Entity, place: Place, kite: KiteCfg, line: LineCfg) -> None:
    hero.memes["pride"] += 1
    rival.memes["hurt"] += 1
    world.say(
        f"On {place.ground} stood {hero.id} with {kite.phrase}. {kite.shape_line} {kite.tail_line}"
    )
    world.say(
        f"{hero.id} had tied it to {line.phrase} and {line.boast}."
    )
    world.say(
        f'Last year {rival.id} had helped with every knot, but this year {hero.id} had puffed up and said, '
        f'"I can launch this sky-whopper myself." That left {rival.id} standing off to one side with crossed arms and a sore heart.'
    )


def launch(world: World, hero: Entity, rival: Entity, elder: Entity) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f'When {elder.label_word} suggested asking for help, {hero.id} grinned too wide and dug in {hero.pronoun("possessive")} heels. '
        f'"I only need one pair of hands," {hero.pronoun()} said.'
    )
    world.say(
        f"{rival.id} snorted, though not very meanly. Nobody who cared enough to be hurt could snort completely mean."
    )


def steady_comedy(world: World, hero: Entity, kite: KiteCfg, place: Place) -> None:
    hero.memes["relief"] += 1
    world.say(
        f"The kite leaped upward so hard that {hero.id}'s hat spun off, circled once like a puzzled pigeon, and landed in the lemon-cake icing."
    )
    world.say(
        f"But the line held. The great {kite.label} sailed above {place.label}, broad and bright, and its shadow rolled over the booths like a passing story."
    )


def scramble_comedy(world: World, hero: Entity, rival: Entity, kite: KiteCfg, place: Place) -> None:
    hero.memes["fear"] += 1
    rival.memes["concern"] += 1
    world.say(
        f"Up jumped the kite -- and off skidded {hero.id}. For three bouncing steps {hero.pronoun()} looked less like a flyer and more like a carrot being pulled from the ground."
    )
    world.say(
        f"The line sang, the tail slapped a pickle barrel, and the giant {kite.label} swooped low enough to comb the mayor's hair without asking."
    )
    world.say(
        f"It was funny to everybody except {hero.id}, who sat down in the dust at last with both hands smoking from effort and pride."
    )


def reconcile(world: World, hero: Entity, rival: Entity, kite: KiteCfg, outcome: str) -> None:
    hero.memes["remorse"] += 1
    rival.memes["softening"] += 1
    world.say(
        f"{hero.id} looked at {rival.id} and finally said the honest thing. "
        f'"A kite this big was never meant for one pair of hands. I was showing off, and I was wrong."'
    )
    if outcome == "scramble":
        world.say(
            f"{rival.id} let out one short laugh, because the sight of {hero.id} being tugged like a loose wagon still tickled {rival.pronoun("object")}, but then {rival.pronoun()} held out both hands."
        )
    else:
        world.say(
            f"{rival.id}'s mouth twitched at the cake on the runaway hat, but the hurt in {rival.pronoun("possessive")} chest eased when the apology came."
        )
    world.say(
        f'"Well," {rival.id} said, "the sky is big enough for both of us."'
    )
    hero.memes["friendship"] += 1
    rival.memes["friendship"] += 1


def final_launch(world: World, hero: Entity, rival: Entity, elder: Entity, kite: KiteCfg, place: Place) -> None:
    hero.memes["joy"] += 1
    rival.memes["joy"] += 1
    elder.memes["pride"] += 1
    world.say(
        f"So they braced shoulder to shoulder, counted together, and sent the kite up again."
    )
    world.say(
        f"This time the pull spread across four hands instead of two, and the big {kite.label} climbed high enough to make chickens hush and fiddlers miss half a note."
    )
    world.say(
        f"From below, it seemed to wink down at them, as if even the kite liked a made-up friendship better than a lonely brag."
    )
    world.say(
        f"When {place.event} came at last, {hero.id} and {rival.id} took the bow together, while the kite floated overhead like the happiest lie in town."
    )


def tell(
    place: Place,
    kite: KiteCfg,
    wind: WindCfg,
    line: LineCfg,
    hero_name: str = "Ada",
    hero_gender: str = "girl",
    rival_name: str = "Ned",
    rival_gender: str = "boy",
    elder_type: str = "father",
    hero_trait: str = "bold",
) -> World:
    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero"))
    rival = world.add(Entity(id="rival", kind="character", type=rival_gender, label=rival_name, role="rival"))
    elder = world.add(Entity(id="elder", kind="character", type=elder_type, label="the elder", role="elder"))
    hero.attrs["name"] = hero_name
    rival.attrs["name"] = rival_name
    elder.attrs["name"] = elder.label_word
    hero.attrs["trait"] = hero_trait
    world.facts.update(
        place_cfg=place,
        kite_cfg=kite,
        wind_cfg=wind,
        line_cfg=line,
        hero_name=hero_name,
        rival_name=rival_name,
        hero_trait=hero_trait,
    )

    build_kite(world, hero, rival, place, kite, line)
    foreshadow(world, hero, rival, elder, kite, wind, line)

    world.para()
    launch(world, hero, rival, elder)
    world.facts["outcome"] = outcome = "smooth" if margin_of(line, kite, wind) >= 1 else "scramble"
    propagate(world, narrate=False)

    if outcome == "smooth":
        steady_comedy(world, hero, kite, place)
    else:
        scramble_comedy(world, hero, rival, kite, place)

    world.para()
    reconcile(world, hero, rival, kite, outcome)
    final_launch(world, hero, rival, elder, kite, place)

    world.facts.update(
        hero=hero,
        rival=rival,
        elder=elder,
        apologized=hero.memes["remorse"] >= THRESHOLD,
        reconciled=hero.memes["friendship"] >= THRESHOLD and rival.memes["friendship"] >= THRESHOLD,
        comic_scramble=hero.meters["dragged"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    rival = f["rival"]
    kite = f["kite_cfg"]
    place = f["place_cfg"]
    wind = f["wind_cfg"]
    return [
        f'Write a tall tale for a young child that includes the word "final" and features foreshadowing, humor, and reconciliation.',
        f"Tell a playful tall tale where {hero.label} builds a giant {kite.label} for an event at {place.label}, boasts too much, and must make up with {rival.label}.",
        f"Write a story set on {wind.label} where a comic kite mishap hints at trouble early, then ends with two children sharing the final cheer together.",
    ]


KNOWLEDGE = {
    "kite": [
        ("What does a kite need to fly?",
         "A kite needs wind and a line to hold it. The wind lifts it, and the line helps the flyer guide it."),
    ],
    "wind": [
        ("Why can strong wind be hard to handle?",
         "Strong wind pushes hard on light things and pulls on whatever is holding them. That is why a big kite can tug a person around."),
    ],
    "rope": [
        ("Why does a big kite need a strong rope?",
         "A big kite catches lots of wind, so the pull can be strong. A thicker rope is safer because it can hold more strain."),
    ],
    "fair": [
        ("What is a fair?",
         "A fair is a happy public event with games, food, music, and things to see together. People often gather there for parades, contests, and cheers."),
    ],
    "apology": [
        ("What does an apology do?",
         "An apology tells someone you know you hurt them and want to make things better. A sincere apology can help friendship start mending."),
    ],
    "teamwork": [
        ("Why is teamwork useful?",
         "Teamwork lets people share a hard job. When two people help each other, the job can feel lighter and go better."),
    ],
}
KNOWLEDGE_ORDER = ["kite", "wind", "rope", "fair", "apology", "teamwork"]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    rival = f["rival"]
    elder = f["elder"]
    kite = f["kite_cfg"]
    line = f["line_cfg"]
    place = f["place_cfg"]
    wind = f["wind_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, {rival.label}, and their {elder.label_word} while they try to fly a giant {kite.label}. The story follows a boast, a scare, and then a friendship being repaired."
        ),
        (
            f"Why was {rival.label} upset at the beginning?",
            f"{hero.label} had bragged that {hero.pronoun('subject')} could launch the kite alone, even though {rival.label} had helped before. That brag left {rival.label} feeling pushed aside and hurt."
        ),
        (
            "What was the foreshadowing?",
            f"The wind and rope were described like they were warning everyone ahead of time, and {elder.label_word} said a kite that grand liked two good hands. Those details hinted that flying it alone might go badly."
        ),
        (
            f"What made the story funny?",
            f"The giant kite behaved in silly, exaggerated ways, like stealing a hat or nearly combing the mayor's hair. The humor comes from tall-tale exaggeration during the launch trouble."
        ),
    ]
    if outcome == "scramble":
        qa.append(
            (
                f"What happened when {hero.label} tried to launch the kite alone?",
                f"The line held, but the kite pulled so hard that {hero.label} skidded and made a comic scramble across the ground. That happened because the rope was only just strong enough for such a big kite in that wind."
            )
        )
    else:
        qa.append(
            (
                f"What happened when {hero.label} launched the kite alone?",
                f"The launch worked, but it still turned comic when the kite whipped off {hero.label}'s hat and sent it into cake icing. Even with a strong enough rope, the giant kite was far too lively for a neat little launch."
            )
        )
    qa.append(
        (
            f"How did {hero.label} and {rival.label} make up?",
            f"{hero.label} admitted that showing off had been wrong and apologized out loud. Then {rival.label} accepted the apology and chose to help instead of staying mad."
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the two children launching the kite together and sharing {place.event}. The final image proves what changed: the kite is still huge, but the brag is gone and the friendship is back."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"kite", "wind", "apology", "teamwork"}
    place = world.facts["place_cfg"]
    line = world.facts["line_cfg"]
    if "fair" in place.tags:
        tags.add("fair")
    if "rope" in line.tags:
        tags.add("rope")
    elif "clothesline" in line.tags:
        tags.add("rope")
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
    for ent in world.entities.values():
        bits = [f"name={ent.label}"]
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="fairground",
        kite="rooster",
        wind="breezy",
        line="porch_rope",
        hero_name="Ada",
        hero_gender="girl",
        rival_name="Ned",
        rival_gender="boy",
        elder_type="father",
        hero_trait="showy",
    ),
    StoryParams(
        place="hill",
        kite="moon",
        wind="breezy",
        line="porch_rope",
        hero_name="Eli",
        hero_gender="boy",
        rival_name="June",
        rival_gender="girl",
        elder_type="mother",
        hero_trait="bold",
    ),
    StoryParams(
        place="fairground",
        kite="catfish",
        wind="blustery",
        line="porch_rope",
        hero_name="Molly",
        hero_gender="girl",
        rival_name="Wes",
        rival_gender="boy",
        elder_type="mother",
        hero_trait="lively",
    ),
    StoryParams(
        place="hill",
        kite="moon",
        wind="blustery",
        line="boat_rope",
        hero_name="Hank",
        hero_gender="boy",
        rival_name="Ivy",
        rival_gender="girl",
        elder_type="father",
        hero_trait="stubborn",
    ),
    StoryParams(
        place="orchard",
        kite="rooster",
        wind="breezy",
        line="clothesline",
        hero_name="Tessa",
        hero_gender="girl",
        rival_name="Cal",
        rival_gender="boy",
        elder_type="mother",
        hero_trait="cheerful",
    ),
]


ASP_RULES = r"""
compatible_place(P, W) :- place(P), wind(W), allows(P, W).
need(K, W, N) :- kite(K), weight(K, KW), wind(W), force(W, WF), N = KW + WF.
valid(P, K, W, L) :- compatible_place(P, W), line(L), need(K, W, N), strength(L, S), S >= N.

margin(M) :- chosen_kite(K), chosen_wind(W), chosen_line(L),
             weight(K, KW), force(W, WF), strength(L, S), M = S - (KW + WF).

outcome(smooth) :- margin(M), M >= 1.
outcome(scramble) :- margin(0).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for wind in sorted(place.gusts):
            lines.append(asp.fact("allows", pid, wind))
    for kid, kite in KITES.items():
        lines.append(asp.fact("kite", kid))
        lines.append(asp.fact("weight", kid, kite.weight))
    for wid, wind in WINDS.items():
        lines.append(asp.fact("wind", wid))
        lines.append(asp.fact("force", wid, wind.force))
    for lid, line in LINES.items():
        lines.append(asp.fact("line", lid))
        lines.append(asp.fact("strength", lid, line.strength))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_kite", params.kite),
            asp.fact("chosen_wind", params.wind),
            asp.fact("chosen_line", params.line),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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

    cases: list[StoryParams] = list(CURATED)
    for seed in range(25):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving random case at seed {seed}.")
            break

    mismatches = 0
    for params in cases:
        try:
            py = outcome_of(params)
            asp_val = asp_outcome(params)
            if py != asp_val:
                mismatches += 1
        except StoryError as err:
            mismatches += 1
            print(f"Outcome check failed for {params}: {err}")
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        emit(sample, trace=False, qa=False)
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover - defensive verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale story world: a giant kite, a boast, foreshadowing, humor, and reconciliation."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--kite", choices=KITES)
    ap.add_argument("--wind", choices=WINDS)
    ap.add_argument("--line", choices=LINES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--rival-name")
    ap.add_argument("--rival-gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (place, kite, wind, line) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place is not None and args.place not in PLACES:
        raise StoryError("(Invalid place.)")
    if args.kite is not None and args.kite not in KITES:
        raise StoryError("(Invalid kite.)")
    if args.wind is not None and args.wind not in WINDS:
        raise StoryError("(Invalid wind.)")
    if args.line is not None and args.line not in LINES:
        raise StoryError("(Invalid line.)")

    if args.place and args.kite and args.wind and args.line:
        place = PLACES[args.place]
        kite = KITES[args.kite]
        wind = WINDS[args.wind]
        line = LINES[args.line]
        if not combo_is_valid(place, kite, wind, line):
            raise StoryError(explain_rejection(place, kite, wind, line))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.kite is None or combo[1] == args.kite)
        and (args.wind is None or combo[2] == args.wind)
        and (args.line is None or combo[3] == args.line)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, kite_id, wind_id, line_id = rng.choice(combos)
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    rival_gender = args.rival_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    rival_name = args.rival_name or _pick_name(rng, rival_gender, avoid=hero_name)
    elder_type = args.elder or rng.choice(["mother", "father"])
    hero_trait = rng.choice(TRAITS)

    return StoryParams(
        place=place_id,
        kite=kite_id,
        wind=wind_id,
        line=line_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        rival_name=rival_name,
        rival_gender=rival_gender,
        elder_type=elder_type,
        hero_trait=hero_trait,
    )


def generate(params: StoryParams) -> StorySample:
    place = PLACES.get(params.place)
    kite = KITES.get(params.kite)
    wind = WINDS.get(params.wind)
    line = LINES.get(params.line)
    if place is None or kite is None or wind is None or line is None:
        raise StoryError("(Invalid params: unknown place, kite, wind, or line.)")
    if not combo_is_valid(place, kite, wind, line):
        raise StoryError(explain_rejection(place, kite, wind, line))

    world = tell(
        place=place,
        kite=kite,
        wind=wind,
        line=line,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        rival_name=params.rival_name,
        rival_gender=params.rival_gender,
        elder_type=params.elder_type,
        hero_trait=params.hero_trait,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, kite, wind, line) combos:\n")
        for place, kite, wind, line in combos:
            print(f"  {place:10} {kite:8} {wind:9} {line}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} and {p.rival_name}: {p.kite} at {p.place} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
