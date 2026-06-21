#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/archeologic_union_sharing_transformation_myth.py
============================================================================

A standalone story world about two children at an ancient dig site who uncover a
mythic relic. The relic only answers when the children *share* the right thing
with the place in need, and then the old ruin transforms.

The domain is intentionally small and constrained. A place has a lack
(thirst / darkness / silence), and a relic carries a matching gift
(water / light / song). Only compatible pairings become stories, because the
world model insists on a believable problem and fix: a dry basin needs water,
a dark stair needs light, and a silent gate needs song.

Run it
------
    python storyworlds/worlds/gpt-5.4/archeologic_union_sharing_transformation_myth.py
    python storyworlds/worlds/gpt-5.4/archeologic_union_sharing_transformation_myth.py --site sun_court --relic shell_cup
    python storyworlds/worlds/gpt-5.4/archeologic_union_sharing_transformation_myth.py --site moon_stair --relic shell_cup
    python storyworlds/worlds/gpt-5.4/archeologic_union_sharing_transformation_myth.py --all
    python storyworlds/worlds/gpt-5.4/archeologic_union_sharing_transformation_myth.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/archeologic_union_sharing_transformation_myth.py --verify
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
    kind: str = "thing"            # character | thing | place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
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
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Site:
    id: str
    place: str
    title: str
    lack: str
    need: str
    image: str
    waking_line: str
    transformed_line: str
    closing_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    gift: str
    reveal: str
    share_text: str
    transform_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Guide:
    id: str
    title: str
    warning: str
    blessing: str


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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"finder", "friend"}]

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


def _r_join(world: World) -> list[str]:
    relic = world.get("relic")
    site = world.get("site")
    if relic.meters["shared"] < THRESHOLD or site.meters["answering"] < THRESHOLD:
        return []
    sig = ("join", site.id, relic.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    relic.meters["awake"] += 1
    site.meters["hope"] += 1
    for kid in world.kids():
        kid.memes["wonder"] += 1
    return ["__union__"]


def _r_transform(world: World) -> list[str]:
    relic = world.get("relic")
    site = world.get("site")
    if relic.meters["awake"] < THRESHOLD:
        return []
    sig = ("transform", site.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    site.meters["changed"] += 1
    site.meters["lack"] = 0.0
    for kid in world.kids():
        kid.memes["joy"] += 1
        kid.memes["generosity"] += 1
    return ["__transformation__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="join", tag="social", apply=_r_join),
    Rule(name="transform", tag="physical", apply=_r_transform),
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


def compatible(site: Site, relic: Relic) -> bool:
    return site.need == relic.gift


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for site_id, site in SITES.items():
        for relic_id, relic in RELICS.items():
            if compatible(site, relic):
                combos.append((site_id, relic_id))
    return combos


def explain_rejection(site: Site, relic: Relic) -> str:
    return (
        f"(No story: {site.title} suffers from {site.lack}, so it needs {site.need}, "
        f"but {relic.label} offers {relic.gift}. In this world, the shared gift must "
        f"match the place's need before any transformation can happen.)"
    )


def predict_union(world: World, share: bool) -> dict:
    sim = world.copy()
    site_ent = sim.get("site")
    relic_ent = sim.get("relic")
    if share:
        relic_ent.meters["shared"] += 1
        if sim.facts["site_cfg"].need == sim.facts["relic_cfg"].gift:
            site_ent.meters["answering"] += 1
    propagate(sim, narrate=False)
    return {
        "awake": relic_ent.meters["awake"] >= THRESHOLD,
        "changed": site_ent.meters["changed"] >= THRESHOLD,
    }


def introduce(world: World, a: Entity, b: Entity, site: Site, guide: Entity) -> None:
    for kid in (a, b):
        kid.memes["curiosity"] += 1
    place_ent = world.get("site")
    place_ent.meters["lack"] += 1
    world.say(
        f"In the age when hills still remembered old songs, {a.id} and {b.id} climbed "
        f"to {site.place} with {guide.label}. The guide called it an archeologic wonder, "
        f"for broken stones and buried steps slept there under the dust."
    )
    world.say(
        f"{site.image} Above the highest stone, a faded carving showed two hands meeting "
        f"inside a circle. Under it, the old letters named the place the House of Union."
    )


def uncover(world: World, a: Entity, b: Entity, relic: Relic) -> None:
    world.say(
        f"While {a.id} brushed sand from a cracked floor and {b.id} lifted pebbles from a seam, "
        f"their fingers found {relic.phrase}. {relic.reveal}"
    )
    world.say(
        f"The relic gave a soft answer in their palms, as if it had been waiting a very long time "
        f"to be held by children."
    )


def explain_need(world: World, guide: Entity, site: Site, relic: Relic) -> None:
    world.say(
        f'{guide.label.capitalize()} knelt beside them. "{guide.attrs["warning"]}," {guide.pronoun()} said. '
        f'"This old place is thirsty for {site.need}. If you keep the gift closed in one pair of hands, '
        f'the stones will stay asleep."'
    )
    world.facts["predicted_if_shared"] = predict_union(world, share=True)
    world.facts["predicted_if_kept"] = predict_union(world, share=False)


def clutch(world: World, a: Entity, relic: Relic) -> None:
    a.memes["greed"] += 1
    world.say(
        f"{a.id} curled both hands around the {relic.label}. For one little moment, "
        f"{a.pronoun()} wanted the marvel all for {a.pronoun('object')}self."
    )


def invite_share(world: World, b: Entity, a: Entity, guide: Entity, relic: Relic) -> None:
    b.memes["generosity"] += 1
    world.say(
        f'{b.id} touched {a.pronoun("possessive")} sleeve. "Let us share it," {b.pronoun()} whispered. '
        f'"Then the gift will belong to the place, and to both of us too."'
    )
    world.say(
        f'{guide.label.capitalize()} smiled and added, "{guide.attrs["blessing"]}."'
    )


def decide(world: World, a: Entity, b: Entity, choose_share: bool, site: Site, relic: Relic) -> None:
    if choose_share:
        a.memes["greed"] = 0.0
        a.memes["generosity"] += 1
        b.memes["trust"] += 1
        world.say(
            f"{a.id} looked from the glowing edges of the {relic.label} to the sleeping court around them. "
            f"Then {a.pronoun()} opened {a.pronoun('possessive')} hands."
        )
        world.say(
            f"{a.id} and {b.id} held the relic together and {relic.share_text}."
        )
        world.get("relic").meters["shared"] += 1
        if compatible(site, relic):
            world.get("site").meters["answering"] += 1
        propagate(world, narrate=False)
    else:
        world.say(
            f"But {a.id} hid the {relic.label} against {a.pronoun('possessive')} chest. "
            f"The court stayed still. Even the wind seemed to wait."
        )


def transform_scene(world: World, site: Site, relic: Relic) -> None:
    site_ent = world.get("site")
    if site_ent.meters["changed"] < THRESHOLD:
        return
    world.say(
        f"At once, the sign of union on the stone ring shone clear. {site.waking_line} "
        f"{relic.transform_text} {site.transformed_line}"
    )


def closing(world: World, a: Entity, b: Entity, guide: Entity, site: Site) -> None:
    changed = world.get("site").meters["changed"] >= THRESHOLD
    if changed:
        world.say(
            f'{guide.label.capitalize()} bowed {guide.pronoun("possessive")} head. '
            f'"You have remembered the oldest law," {guide.pronoun()} said. '
            f'"When good things are shared, the world grows larger."'
        )
        world.say(
            f"{site.closing_image} Side by side, {a.id} and {b.id} walked home with dusty knees, "
            f"light hearts, and one story to tell together."
        )
    else:
        world.say(
            f'{guide.label.capitalize()} laid a hand on {a.id}\'s shoulder. '
            f'"A shut hand makes a shut world," {guide.pronoun()} said gently. '
            f'"Another day, you may choose differently."'
        )
        world.say(
            f"The relic dimmed to a quiet pebble again. {a.id} loosened {a.pronoun('possessive')} fingers, "
            f"and {b.id} stood close beside {a.pronoun('object')}, because even a sad lesson was easier to carry together."
        )


def tell(
    site: Site,
    relic: Relic,
    guide_cfg: Guide,
    *,
    finder: str = "Nila",
    finder_gender: str = "girl",
    friend: str = "Ivo",
    friend_gender: str = "boy",
    trait: str = "careful",
    parent_type: str = "mother",
    choose_share: bool = True,
) -> World:
    world = World()
    a = world.add(Entity(id=finder, kind="character", type=finder_gender, role="finder",
                         label=finder, traits=["eager"], attrs={"trait": trait}))
    b = world.add(Entity(id=friend, kind="character", type=friend_gender, role="friend",
                         label=friend, traits=[trait]))
    guide = world.add(Entity(id="Guide", kind="character", type=parent_type, role="guide",
                             label="the guide", attrs={"warning": guide_cfg.warning, "blessing": guide_cfg.blessing}))
    site_ent = world.add(Entity(id="site", kind="place", type="ruin", label=site.title,
                                phrase=site.place, tags=set(site.tags)))
    relic_ent = world.add(Entity(id="relic", kind="thing", type="relic", label=relic.label,
                                 phrase=relic.phrase, tags=set(relic.tags)))

    introduce(world, a, b, site, guide)
    world.para()
    uncover(world, a, b, relic)
    explain_need(world, guide, site, relic)
    clutch(world, a, relic)
    invite_share(world, b, a, guide, relic)
    world.para()
    decide(world, a, b, choose_share, site, relic)
    transform_scene(world, site, relic)
    world.para()
    closing(world, a, b, guide, site)

    world.facts.update(
        finder=a,
        friend=b,
        guide=guide,
        site_cfg=site,
        relic_cfg=relic,
        shared=world.get("relic").meters["shared"] >= THRESHOLD,
        transformed=world.get("site").meters["changed"] >= THRESHOLD,
        outcome="transformed" if world.get("site").meters["changed"] >= THRESHOLD else "dim",
    )
    return world


@dataclass
class StoryParams:
    site: str
    relic: str
    guide: str
    finder: str
    finder_gender: str
    friend: str
    friend_gender: str
    parent: str
    trait: str
    share: bool = True
    seed: Optional[int] = None


SITES = {
    "sun_court": Site(
        id="sun_court",
        place="the Sun Court",
        title="the Sun Court",
        lack="a dry and empty basin",
        need="water",
        image="At the center stood a stone basin, white with dust and dry as old bone.",
        waking_line="A silver thread ran down the carved channels of the floor.",
        transformed_line="The empty basin brimmed, and golden reeds and blue lilies leaned over the bright water.",
        closing_image="Behind them, the Sun Court shimmered with a new pool where dragonflies circled like bits of sky.",
        tags={"water", "dig", "myth"},
    ),
    "moon_stair": Site(
        id="moon_stair",
        place="the Moon Stair",
        title="the Moon Stair",
        lack="a stair lost in darkness",
        need="light",
        image="A stair of black stone climbed upward, but its steps vanished into shadow after only a few turns.",
        waking_line="One by one, the pale carvings on the stair kindled.",
        transformed_line="The whole stair shone pearl-bright, and stars blossomed in the ceiling above it.",
        closing_image="Behind them, the Moon Stair rose like a ladder made of moonmilk and song.",
        tags={"light", "dig", "myth"},
    ),
    "wind_gate": Site(
        id="wind_gate",
        place="the Wind Gate",
        title="the Wind Gate",
        lack="a gate sunk in silence",
        need="song",
        image="Two tall pillars held a gate with no doors, and every hanging ribbon there had forgotten how to move.",
        waking_line="A warm breeze swept the dust from the threshold.",
        transformed_line="The ribbons danced, bronze bells answered, and the empty gate became a doorway of music.",
        closing_image="Behind them, the Wind Gate kept singing, and the ribbons laughed in the afternoon air.",
        tags={"song", "dig", "myth"},
    ),
}

RELICS = {
    "shell_cup": Relic(
        id="shell_cup",
        label="shell cup",
        phrase="a little shell cup set into the stones",
        gift="water",
        reveal="When they lifted it free, a drop of clear water trembled inside and did not spill.",
        share_text="tilted the shell cup over the ancient basin together",
        transform_text="The clear drop fell, but it struck like rain remembered by a desert.",
        tags={"water", "relic"},
    ),
    "sun_mirror": Relic(
        id="sun_mirror",
        label="sun mirror",
        phrase="a round mirror no bigger than a biscuit, buried face-down in the grit",
        gift="light",
        reveal="When they turned it over, it held a piece of sunlight even though a cloud had crossed the sky.",
        share_text="raised the sun mirror with both hands toward the dark stair",
        transform_text="A bright beam leapt from the mirror's heart.",
        tags={"light", "relic"},
    ),
    "reed_whistle": Relic(
        id="reed_whistle",
        label="reed whistle",
        phrase="a green reed whistle hidden in a crack between two old paving stones",
        gift="song",
        reveal="It looked plain until their thumbs touched it, and then a humming note curled out like a sleeping bird waking.",
        share_text="blew the reed whistle together, sharing one long steady breath",
        transform_text="The note widened into the air like a golden ribbon.",
        tags={"song", "relic"},
    ),
}

GUIDES = {
    "keeper": Guide(
        id="keeper",
        title="keeper",
        warning="The old gifts wake only for children who open their hands",
        blessing="Shared hands make strong magic",
    ),
    "scribe": Guide(
        id="scribe",
        title="scribe",
        warning="The buried houses listen for kindness before they listen for power",
        blessing="What is shared becomes bright enough for all",
    ),
}

GIRL_NAMES = ["Nila", "Tali", "Mira", "Sena", "Luma", "Ari", "Yara", "Eni"]
BOY_NAMES = ["Ivo", "Tarin", "Sami", "Oren", "Lio", "Pavel", "Nero", "Darin"]
TRAITS = ["careful", "kind", "steady", "thoughtful", "gentle"]


def outcome_of(params: StoryParams) -> str:
    return "transformed" if params.share else "dim"


CURATED = [
    StoryParams(
        site="sun_court",
        relic="shell_cup",
        guide="keeper",
        finder="Nila",
        finder_gender="girl",
        friend="Ivo",
        friend_gender="boy",
        parent="mother",
        trait="careful",
        share=True,
    ),
    StoryParams(
        site="moon_stair",
        relic="sun_mirror",
        guide="scribe",
        finder="Tarin",
        finder_gender="boy",
        friend="Mira",
        friend_gender="girl",
        parent="father",
        trait="thoughtful",
        share=True,
    ),
    StoryParams(
        site="wind_gate",
        relic="reed_whistle",
        guide="keeper",
        finder="Luma",
        finder_gender="girl",
        friend="Sami",
        friend_gender="boy",
        parent="mother",
        trait="gentle",
        share=True,
    ),
    StoryParams(
        site="sun_court",
        relic="shell_cup",
        guide="scribe",
        finder="Oren",
        finder_gender="boy",
        friend="Yara",
        friend_gender="girl",
        parent="father",
        trait="kind",
        share=False,
    ),
]


KNOWLEDGE = {
    "archeologic": [
        (
            "What does archeologic mean?",
            "Archeologic means connected to very old things people left behind long ago, like buried pots, stones, and buildings. It is about learning from the past by carefully uncovering it.",
        )
    ],
    "union": [
        (
            "What is a union?",
            "A union is a joining together. In stories, it can mean people, hands, or hearts working as one.",
        )
    ],
    "water": [
        (
            "Why does water help dry plants and basins?",
            "Water feeds living things and fills empty places. A dry garden or basin can wake up again when water returns.",
        )
    ],
    "light": [
        (
            "Why do people need light?",
            "Light helps people see where to go. In stories, light can also mean hope and waking up what was hidden.",
        )
    ],
    "song": [
        (
            "Why can song matter in a story?",
            "Songs can help people move together and remember things. In myths, a song often wakes sleeping magic.",
        )
    ],
    "relic": [
        (
            "What is a relic?",
            "A relic is an old object kept from long ago. People treat it carefully because it can tell a story about the past.",
        )
    ],
    "sharing": [
        (
            "Why is sharing important?",
            "Sharing lets more than one person enjoy or use a good thing. It can also turn a lonely moment into a joined one.",
        )
    ],
    "myth": [
        (
            "What is a myth?",
            "A myth is a story told in a grand, old-fashioned way about wonders, lessons, or the beginnings of things. Myths often use symbols like light, water, and song.",
        )
    ],
}
KNOWLEDGE_ORDER = ["archeologic", "union", "relic", "sharing", "water", "light", "song", "myth"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    site = f["site_cfg"]
    relic = f["relic_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a short myth for a 3-to-5-year-old that includes the words "archeologic" '
        f'and "union". Two children uncover {relic.phrase} at {site.place}.'
    )
    if outcome == "transformed":
        return [
            base,
            f"Tell a gentle myth where two children find a buried relic, choose sharing over keeping, "
            f"and the old ruin transforms because the shared gift matches the place's need for {site.need}.",
            f"Write a child-facing mythic story in which an archeologic discovery teaches that union and sharing "
            f"can wake old magic and make the world bloom again.",
        ]
    return [
        base,
        f"Tell a quiet myth where one child almost keeps a relic alone, and the sleeping ruin stays unchanged, "
        f"teaching that magic waits for sharing and union.",
        f"Write a mythic cautionary story where a buried gift remains dim because a child closes a hand instead of sharing.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["finder"]
    b = f["friend"]
    guide = f["guide"]
    site = f["site_cfg"]
    relic = f["relic_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {a.id} and {b.id}, two children exploring an old ruin with {guide.label}. "
            f"They uncover a buried relic and must decide whether to share it.",
        ),
        (
            f"What did the children find at {site.place}?",
            f"They found {relic.phrase}. The relic seemed sleepy at first, but it answered softly when they held it.",
        ),
        (
            "Why did the guide talk about sharing?",
            f"The guide knew the old place needed {site.need}, and the relic carried that very gift. "
            f"In this world, the magic wakes only when the children open their hands together.",
        ),
    ]
    if f["shared"]:
        qa.append(
            (
                "How did sharing change the story?",
                f"{a.id} and {b.id} held the relic together and gave its gift to the ruin. "
                f"Because the gift matched the place's need, the sign of union woke and the whole place transformed.",
            )
        )
        qa.append(
            (
                f"What changed at {site.place} in the end?",
                f"The place stopped being full of {site.lack} and became bright and alive instead. "
                f"The ending image proves the magic answered their shared kindness.",
            )
        )
    else:
        qa.append(
            (
                "What happened when the relic was not shared?",
                f"The court stayed still and the relic dimmed again. "
                f"Nothing transformed because one closed hand kept the gift from reaching the place that needed it.",
            )
        )
        qa.append(
            (
                "What lesson did the children learn?",
                f"They learned that a wonder kept for one person can become smaller, not bigger. "
                f"The old ruin waited for union, so sharing was the true key.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"archeologic", "union", "sharing", "relic", "myth"}
    site = world.facts["site_cfg"]
    relic = world.facts["relic_cfg"]
    if site.need == "water" or relic.gift == "water":
        tags.add("water")
    if site.need == "light" or relic.gift == "light":
        tags.add("light")
    if site.need == "song" or relic.gift == "song":
        tags.add("song")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
gift_matches(S, R) :- need(S, G), gift(R, G).
valid(S, R) :- site(S), relic(R), gift_matches(S, R).

outcome(transformed) :- choose_share(yes), chosen_site(S), chosen_relic(R), gift_matches(S, R).
outcome(dim) :- not outcome(transformed).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for site_id, site in SITES.items():
        lines.append(asp.fact("site", site_id))
        lines.append(asp.fact("need", site_id, site.need))
    for relic_id, relic in RELICS.items():
        lines.append(asp.fact("relic", relic_id))
        lines.append(asp.fact("gift", relic_id, relic.gift))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_site", params.site),
        asp.fact("chosen_relic", params.relic),
        asp.fact("choose_share", "yes" if params.share else "no"),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    cset = set(asp_valid_combos())
    pset = set(valid_combos())
    if cset == pset:
        print(f"OK: ASP gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    cases = list(CURATED)
    for seed in range(20):
        rng = random.Random(seed)
        try:
            params = resolve_params(build_parser().parse_args([]), rng)
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: ASP outcome matches Python outcome on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} ASP outcomes differ.")

    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("empty story during smoke test")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a mythic archeologic relic, sharing, and transformation."
    )
    ap.add_argument("--site", choices=sorted(SITES))
    ap.add_argument("--relic", choices=sorted(RELICS))
    ap.add_argument("--guide", choices=sorted(GUIDES))
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--share", choices=["yes", "no"],
                    help="whether the finder opens the relic gift with the other child")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (site, relic) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.site and args.relic:
        site = SITES[args.site]
        relic = RELICS[args.relic]
        if not compatible(site, relic):
            raise StoryError(explain_rejection(site, relic))

    combos = [
        combo for combo in valid_combos()
        if (args.site is None or combo[0] == args.site)
        and (args.relic is None or combo[1] == args.relic)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    site_id, relic_id = rng.choice(sorted(combos))
    guide_id = args.guide or rng.choice(sorted(GUIDES))
    finder, fg = _pick_name(rng)
    friend, bg = _pick_name(rng, avoid=finder)
    share = {"yes": True, "no": False}.get(args.share, rng.choice([True, True, True, False]))
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)

    return StoryParams(
        site=site_id,
        relic=relic_id,
        guide=guide_id,
        finder=finder,
        finder_gender=fg,
        friend=friend,
        friend_gender=bg,
        parent=parent,
        trait=trait,
        share=share,
    )


def generate(params: StoryParams) -> StorySample:
    if params.site not in SITES:
        raise StoryError(f"(Invalid site: {params.site})")
    if params.relic not in RELICS:
        raise StoryError(f"(Invalid relic: {params.relic})")
    if params.guide not in GUIDES:
        raise StoryError(f"(Invalid guide: {params.guide})")
    site = SITES[params.site]
    relic = RELICS[params.relic]
    if not compatible(site, relic):
        raise StoryError(explain_rejection(site, relic))

    world = tell(
        site=site,
        relic=relic,
        guide_cfg=GUIDES[params.guide],
        finder=params.finder,
        finder_gender=params.finder_gender,
        friend=params.friend,
        friend_gender=params.friend_gender,
        trait=params.trait,
        parent_type=params.parent,
        choose_share=params.share,
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
        print(asp_program("", "#show valid/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (site, relic) combos:\n")
        for site_id, relic_id in combos:
            print(f"  {site_id:12} {relic_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.finder} & {p.friend}: {p.relic} at {p.site} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
