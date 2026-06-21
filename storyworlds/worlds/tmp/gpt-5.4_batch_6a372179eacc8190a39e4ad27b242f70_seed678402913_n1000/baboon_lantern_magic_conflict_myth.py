#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/baboon_lantern_magic_conflict_myth.py
================================================================

A standalone storyworld for a small mythic domain: a child must carry a gift to a
sacred baboon so a magic lantern can shine again. The conflict is social rather
than violent: the baboon is angry, hungry, lonely, or proud because people have
forgotten old courtesies. The resolution must be *reasonable* for that mood.

The world model tracks physical meters (light, darkness, safety) and emotional
memes (fear, trust, respect, relief). The rendered story follows those changes.

Run it
------
    python storyworlds/worlds/gpt-5.4/baboon_lantern_magic_conflict_myth.py
    python storyworlds/worlds/gpt-5.4/baboon_lantern_magic_conflict_myth.py --place hill_shrine --mood hungry --gift figs
    python storyworlds/worlds/gpt-5.4/baboon_lantern_magic_conflict_myth.py --mood proud --gift figs
    python storyworlds/worlds/gpt-5.4/baboon_lantern_magic_conflict_myth.py --all
    python storyworlds/worlds/gpt-5.4/baboon_lantern_magic_conflict_myth.py --qa
    python storyworlds/worlds/gpt-5.4/baboon_lantern_magic_conflict_myth.py --verify
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

# Make the shared result containers importable when this script is run directly.
# This file lives under storyworlds/worlds/gpt-5.4/, so we add storyworlds/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"            # character | thing
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
        female = {"girl", "woman", "mother", "grandmother", "priestess"}
        male = {"boy", "man", "father", "grandfather", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    path: str
    sky_effect: str
    lantern: str
    tags: set[str] = field(default_factory=set)


@dataclass
class LanternKind:
    id: str
    label: str
    flame_color: str
    glow_effect: str
    belongs_at: str
    tags: set[str] = field(default_factory=set)


@dataclass
class BaboonMood:
    id: str
    label: str
    complaint: str
    accepts: set[str]
    softens_with: str
    first_action: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    reply: str
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
        out = World()
        out.entities = copy.deepcopy(self.entities)
        out.fired = set(self.fired)
        out.paragraphs = [[]]
        out.facts = copy.deepcopy(self.facts)
        return out


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_darkness(world: World) -> list[str]:
    out: list[str] = []
    lantern = world.get("lantern")
    sky = world.get("sky")
    if lantern.meters["lit"] < THRESHOLD:
        sig = ("darkness",)
        if sig not in world.fired:
            world.fired.add(sig)
            sky.meters["dark"] += 1
            sky.meters["safe"] = 0.0
            out.append("__darkness__")
    return out


def _r_trust(world: World) -> list[str]:
    out: list[str] = []
    baboon = world.get("baboon")
    hero = world.get("hero")
    if baboon.memes["soothed"] >= THRESHOLD and baboon.memes["trust"] < THRESHOLD:
        sig = ("trust",)
        if sig not in world.fired:
            world.fired.add(sig)
            baboon.memes["trust"] += 1
            hero.memes["hope"] += 1
            out.append("__trust__")
    return out


def _r_light(world: World) -> list[str]:
    out: list[str] = []
    lantern = world.get("lantern")
    sky = world.get("sky")
    hero = world.get("hero")
    baboon = world.get("baboon")
    if lantern.meters["lit"] >= THRESHOLD:
        sig = ("light",)
        if sig not in world.fired:
            world.fired.add(sig)
            sky.meters["dark"] = 0.0
            sky.meters["glow"] += 1
            sky.meters["safe"] += 1
            hero.memes["relief"] += 1
            hero.memes["wonder"] += 1
            baboon.memes["peace"] += 1
            out.append("__light__")
    return out


CAUSAL_RULES = [
    Rule(name="darkness", tag="physical", apply=_r_darkness),
    Rule(name="trust", tag="social", apply=_r_trust),
    Rule(name="light", tag="physical", apply=_r_light),
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


PLACES = {
    "hill_shrine": Place(
        id="hill_shrine",
        label="the Hill Shrine",
        path="a stair of white stones above the sleeping village",
        sky_effect="the fields below looked like a dark sea",
        lantern="moon_lantern",
        tags={"shrine", "hill"},
    ),
    "reed_gate": Place(
        id="reed_gate",
        label="the Reed Gate",
        path="a narrow causeway through whispering reeds",
        sky_effect="the marsh pools held the stars like broken silver",
        lantern="mist_lantern",
        tags={"marsh", "reed"},
    ),
    "sun_cave": Place(
        id="sun_cave",
        label="the Sun Cave",
        path="a path of warm rock under a cliff of gold stone",
        sky_effect="the sea beyond the cliff had already turned purple",
        lantern="dawn_lantern",
        tags={"cave", "sea"},
    ),
}

LANTERNS = {
    "moon_lantern": LanternKind(
        id="moon_lantern",
        label="moon lantern",
        flame_color="silver",
        glow_effect="laid a pale road across the roofs and fields",
        belongs_at="hill_shrine",
        tags={"lantern", "moon", "magic"},
    ),
    "mist_lantern": LanternKind(
        id="mist_lantern",
        label="mist lantern",
        flame_color="blue",
        glow_effect="turned the marsh paths clear and gentle",
        belongs_at="reed_gate",
        tags={"lantern", "mist", "magic"},
    ),
    "dawn_lantern": LanternKind(
        id="dawn_lantern",
        label="dawn lantern",
        flame_color="gold",
        glow_effect="painted the cliff mouth with warm morning color even at dusk",
        belongs_at="sun_cave",
        tags={"lantern", "dawn", "magic"},
    ),
}

MOODS = {
    "hungry": BaboonMood(
        id="hungry",
        label="hungry",
        complaint="No one remembers that a watchful belly must be fed.",
        accepts={"figs", "dates", "lotus_cake"},
        softens_with="food shared with open hands",
        first_action="bared his teeth over a pile of empty husks",
        tags={"food", "baboon"},
    ),
    "proud": BaboonMood(
        id="proud",
        label="proud",
        complaint="No one bows to the old hill-keeper now.",
        accepts={"beads", "ribbon", "bronze_bell"},
        softens_with="a bright gift given with respect",
        first_action="sat high on the altar wall as if it were a king's throne",
        tags={"respect", "baboon"},
    ),
    "lonely": BaboonMood(
        id="lonely",
        label="lonely",
        complaint="The songs have gone, and the night has forgotten my name.",
        accepts={"story_shell", "song_reed", "bronze_bell"},
        softens_with="a gift that carries voice or music",
        first_action="rocked beside the cold lantern and called into the echoing dusk",
        tags={"music", "baboon"},
    ),
}

GIFTS = {
    "figs": Gift(
        id="figs",
        label="figs",
        phrase="a leaf bowl of purple figs",
        reply="The sweet smell reached the baboon before the child did.",
        tags={"food"},
    ),
    "dates": Gift(
        id="dates",
        label="dates",
        phrase="a string of honey dates",
        reply="The dates shone like little drops of sunset.",
        tags={"food"},
    ),
    "lotus_cake": Gift(
        id="lotus_cake",
        label="lotus cake",
        phrase="a round lotus cake wrapped in cool leaves",
        reply="The cake smelled soft and warm, like festival mornings.",
        tags={"food"},
    ),
    "beads": Gift(
        id="beads",
        label="beads",
        phrase="a loop of sky-blue beads",
        reply="Each bead caught the last light and answered it with a tiny star.",
        tags={"treasure"},
    ),
    "ribbon": Gift(
        id="ribbon",
        label="ribbon",
        phrase="a crimson ribbon from the festival pole",
        reply="The ribbon fluttered like a little banner in the wind.",
        tags={"treasure"},
    ),
    "bronze_bell": Gift(
        id="bronze_bell",
        label="bronze bell",
        phrase="a bronze bell no bigger than a plum",
        reply="Even before it rang, the small bell seemed full of waiting music.",
        tags={"music", "treasure"},
    ),
    "story_shell": Gift(
        id="story_shell",
        label="story shell",
        phrase="a white story shell that held the sea's hush",
        reply="When the shell touched the air, it seemed to remember old voices.",
        tags={"music", "story"},
    ),
    "song_reed": Gift(
        id="song_reed",
        label="song reed",
        phrase="a green song reed cut from the riverbank",
        reply="The reed was plain to look at, but the wind already wanted to sing through it.",
        tags={"music"},
    ),
}

GIRL_NAMES = ["Asha", "Mina", "Tala", "Nira", "Suri", "Luma"]
BOY_NAMES = ["Kian", "Ravi", "Tarin", "Jori", "Sami", "Nilo"]
TRAITS = ["brave", "gentle", "patient", "quick-footed", "bright-eyed", "steady"]


def lantern_belongs(place_id: str, lantern_id: str) -> bool:
    return place_id in PLACES and lantern_id in LANTERNS and LANTERNS[lantern_id].belongs_at == place_id


def gift_fits(mood_id: str, gift_id: str) -> bool:
    return mood_id in MOODS and gift_id in GIFTS and gift_id in MOODS[mood_id].accepts


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for lantern_id, lantern in LANTERNS.items():
            if not lantern_belongs(place_id, lantern_id):
                continue
            for mood_id in MOODS:
                for gift_id in GIFTS:
                    if gift_fits(mood_id, gift_id):
                        combos.append((place_id, lantern_id, mood_id, gift_id))
    return combos


def explain_place_lantern(place_id: str, lantern_id: str) -> str:
    place = PLACES[place_id]
    lantern = LANTERNS[lantern_id]
    return (
        f"(No story: the {lantern.label} does not belong at {place.label}. "
        f"In this world, each sacred lantern has one true home.)"
    )


def explain_gift(mood_id: str, gift_id: str) -> str:
    mood = MOODS[mood_id]
    gift = GIFTS[gift_id]
    good = ", ".join(sorted(mood.accepts))
    return (
        f"(No story: {gift.label} would not calm a {mood.label} baboon. "
        f"That mood softens with {mood.softens_with}. Try one of: {good}.)"
    )


def predict_reconciliation(world: World, gift_id: str) -> dict:
    sim = world.copy()
    baboon = sim.get("baboon")
    if gift_fits(sim.facts["mood"].id, gift_id):
        baboon.memes["soothed"] += 1
        propagate(sim, narrate=False)
    return {
        "trust": baboon.memes["trust"] >= THRESHOLD,
        "safe": sim.get("sky").meters["safe"] >= THRESHOLD,
    }


def introduction(world: World, place: Place, hero: Entity, lantern: LanternKind) -> None:
    world.say(
        f"In the old days, people said every village was watched by one sacred {lantern.label}. "
        f"When it shone, no traveler lost the path and no child feared the dark."
    )
    world.say(
        f"One dusk at {place.label}, the magic flame sank to a coal. From {place.path}, "
        f"{place.sky_effect}, and the shadows below began to gather their long sleeves."
    )


def charge(world: World, keeper: Entity, hero: Entity, place: Place, lantern: LanternKind) -> None:
    hero.memes["duty"] += 1
    world.say(
        f'The old {keeper.label} touched {hero.id} on the shoulder and said, '
        f'"Take this gift to the baboon who keeps the high fire. Ask with respect, '
        f'and the {lantern.label} may wake again."'
    )
    world.say(
        f"So {hero.id} climbed toward {place.label}, carrying more courage than size."
    )


def meet_baboon(world: World, hero: Entity, baboon: Entity, mood: BaboonMood, gift: Gift) -> None:
    hero.memes["fear"] += 1
    baboon.memes["anger"] += 1
    world.say(
        f"At the top, a great baboon {mood.first_action}. One brown hand rested on the dark lantern, "
        f"and his eyes flashed like wet stones."
    )
    world.say(
        f'"Go softly, little one," the baboon said. "{mood.complaint}"'
    )
    world.say(gift.reply)
    world.facts["conflict_started"] = True


def answer_with_respect(world: World, hero: Entity, baboon: Entity, gift: Gift, mood: BaboonMood) -> None:
    hero.memes["respect"] += 1
    hero.memes["courage"] += 1
    world.say(
        f'{hero.id} wanted to snatch the lantern and run, but {hero.pronoun()} remembered the old warning: '
        f'magic closes its hand against rude fingers.'
    )
    world.say(
        f'{hero.pronoun().capitalize()} knelt instead and lifted {gift.phrase}. '
        f'"I did not come to fight you," {hero.pronoun()} said. "I came to remember you."'
    )
    if gift_fits(mood.id, gift.id):
        baboon.memes["soothed"] += 1
        propagate(world, narrate=False)


def peace_and_flame(world: World, hero: Entity, baboon: Entity, lantern_ent: Entity, lantern: LanternKind, gift: Gift) -> None:
    baboon.memes["anger"] = 0.0
    baboon.memes["trust"] += 1
    hero.memes["fear"] = 0.0
    hero.memes["trust"] += 1
    lantern_ent.meters["lit"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The baboon took {gift.phrase} with surprising care. Then his fierce face changed, "
        f"as if a hard door had opened behind it."
    )
    world.say(
        f'He bowed his shaggy head. "Then let the old friendship stand again," he said.'
    )
    world.say(
        f"He touched the lantern glass, and a {lantern.flame_color} fire blossomed inside without smoke or wick. "
        f"The new light {lantern.glow_effect}."
    )


def ending(world: World, hero: Entity, baboon: Entity, place: Place, lantern: LanternKind) -> None:
    world.say(
        f"The wind that had felt sharp a moment before now moved like a blessing through the stones. "
        f"{hero.id} and the baboon stood side by side while night settled gently around {place.label}."
    )
    world.say(
        f"After that, the people below left gifts at the stair again, and whenever the {lantern.label} gleamed, "
        f"children said the village was being watched by light, memory, and one solemn baboon."
    )


def tell(
    *,
    place: Place,
    lantern: LanternKind,
    mood: BaboonMood,
    gift: Gift,
    hero_name: str,
    hero_gender: str,
    hero_trait: str,
    keeper_type: str,
) -> World:
    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_gender,
        label=hero_name,
        phrase=hero_name,
        role="hero",
        traits=[hero_trait],
        tags={"child"},
    ))
    keeper = world.add(Entity(
        id="keeper",
        kind="character",
        type=keeper_type,
        label="keeper",
        phrase="the old keeper of the shrine",
        role="keeper",
        tags={"elder"},
    ))
    baboon = world.add(Entity(
        id="baboon",
        kind="character",
        type="baboon",
        label="baboon",
        phrase="the great baboon",
        role="guardian",
        tags={"baboon", "guardian"},
    ))
    lantern_ent = world.add(Entity(
        id="lantern",
        kind="thing",
        type="lantern",
        label=lantern.label,
        phrase=f"the {lantern.label}",
        role="lantern",
        tags=set(lantern.tags),
    ))
    sky = world.add(Entity(
        id="sky",
        kind="thing",
        type="sky",
        label="sky",
        phrase="the evening sky",
        role="sky",
    ))
    lantern_ent.meters["lit"] = 0.0
    propagate(world, narrate=False)

    world.facts.update(
        place=place,
        lantern_kind=lantern,
        mood=mood,
        gift=gift,
        hero=hero,
        keeper=keeper,
        baboon=baboon,
        lantern=lantern_ent,
        conflict_started=False,
    )

    introduction(world, place, hero, lantern)
    charge(world, keeper, hero, place, lantern)
    world.para()
    meet_baboon(world, hero, baboon, mood, gift)
    answer_with_respect(world, hero, baboon, gift, mood)
    world.para()
    peace_and_flame(world, hero, baboon, lantern_ent, lantern, gift)
    ending(world, hero, baboon, place, lantern)

    world.facts.update(
        reconciled=baboon.memes["trust"] >= THRESHOLD,
        relit=lantern_ent.meters["lit"] >= THRESHOLD,
        sky_safe=sky.meters["safe"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    place: str
    lantern: str
    mood: str
    gift: str
    hero_name: str
    hero_gender: str
    hero_trait: str
    keeper_type: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"]
    lantern = f["lantern_kind"]
    mood = f["mood"]
    hero = f["hero"]
    return [
        f'Write a short myth for a young child that includes the words "baboon" and "{lantern.label}".',
        f"Tell a mythic story where a {hero.type} climbs to {place.label} with a gift, faces a {mood.label} baboon, and restores a magic light.",
        f"Write a gentle conflict-and-magic tale in myth style where respect heals an old quarrel and a sacred lantern shines again.",
    ]


KNOWLEDGE = {
    "baboon": [
        (
            "What is a baboon?",
            "A baboon is a kind of monkey with a long face, strong hands, and a clever social life. In stories, people often imagine baboons as watchful guardians because they are bold and quick."
        )
    ],
    "lantern": [
        (
            "What is a lantern?",
            "A lantern is a lamp that holds light inside a case, often with glass around it. People use lanterns to carry light through dark places."
        )
    ],
    "gift": [
        (
            "Why can a gift help end a quarrel?",
            "A thoughtful gift can show respect, care, or apology. It helps the other person feel seen instead of ignored."
        )
    ],
    "respect": [
        (
            "Why does respect matter in old myths?",
            "Many myths teach that power listens to courtesy better than to shouting. Respect shows that someone understands the rules of the world they are entering."
        )
    ],
    "magic": [
        (
            "What makes a light feel magical in a story?",
            "A magical light changes more than what people can see. It can also change fear into safety or turn a hard heart gentle."
        )
    ],
}
KNOWLEDGE_ORDER = ["baboon", "lantern", "gift", "respect", "magic"]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    place = f["place"]
    lantern = f["lantern_kind"]
    mood = f["mood"]
    gift = f["gift"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a child who climbed to {place.label}, and a baboon who guarded the darkened {lantern.label}. The story turns on whether they will stay enemies or remember the old bond."
        ),
        (
            f"Why did {hero.label} climb to {place.label}?",
            f"{hero.label} climbed there because the sacred {lantern.label} had gone dim and the village below was slipping into darkness. The child hoped to ask the baboon guardian to wake the magic flame again."
        ),
        (
            "What was the conflict with the baboon?",
            f"The baboon was angry because people had forgotten the old courtesies and offerings. That made him guard the lantern instead of sharing its fire."
        ),
        (
            f"How did {hero.label} solve the problem?",
            f"{hero.label} did not grab the lantern or fight. {hero.pronoun('subject').capitalize()} knelt, offered {gift.phrase}, and spoke with respect, which soothed the {mood.label} baboon and opened the way to peace."
        ),
    ]
    if f.get("relit"):
        qa.append(
            (
                "What happened when the lantern shone again?",
                f"A magical {lantern.flame_color} light filled the {lantern.label} and made the night safe again. The change mattered because the new glow turned fear and quarrel into calm."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"baboon", "lantern", "gift", "respect", "magic"}
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
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="hill_shrine",
        lantern="moon_lantern",
        mood="hungry",
        gift="figs",
        hero_name="Asha",
        hero_gender="girl",
        hero_trait="brave",
        keeper_type="grandmother",
    ),
    StoryParams(
        place="reed_gate",
        lantern="mist_lantern",
        mood="proud",
        gift="beads",
        hero_name="Kian",
        hero_gender="boy",
        hero_trait="patient",
        keeper_type="grandfather",
    ),
    StoryParams(
        place="sun_cave",
        lantern="dawn_lantern",
        mood="lonely",
        gift="song_reed",
        hero_name="Mina",
        hero_gender="girl",
        hero_trait="gentle",
        keeper_type="priestess",
    ),
    StoryParams(
        place="hill_shrine",
        lantern="moon_lantern",
        mood="proud",
        gift="bronze_bell",
        hero_name="Ravi",
        hero_gender="boy",
        hero_trait="steady",
        keeper_type="priest",
    ),
]


ASP_RULES = r"""
valid_place_lantern(P, L) :- place(P), lantern(L), belongs_at(L, P).
fit_gift(M, G) :- mood(M), gift(G), accepts(M, G).
valid(P, L, M, G) :- valid_place_lantern(P, L), fit_gift(M, G).

scenario_ok :- chosen_place(P), chosen_lantern(L), chosen_mood(M), chosen_gift(G), valid(P, L, M, G).
outcome(reconciled) :- scenario_ok.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for lantern_id, lantern in LANTERNS.items():
        lines.append(asp.fact("lantern", lantern_id))
        lines.append(asp.fact("belongs_at", lantern_id, lantern.belongs_at))
    for mood_id, mood in MOODS.items():
        lines.append(asp.fact("mood", mood_id))
        for gift_id in sorted(mood.accepts):
            lines.append(asp.fact("accepts", mood_id, gift_id))
    for gift_id in GIFTS:
        lines.append(asp.fact("gift", gift_id))
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
        asp.fact("chosen_lantern", params.lantern),
        asp.fact("chosen_mood", params.mood),
        asp.fact("chosen_gift", params.gift),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "invalid"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    for params in CURATED:
        outcome = asp_outcome(params)
        if outcome != "reconciled":
            rc = 1
            print(f"MISMATCH in outcome for curated params: {params} -> {outcome}")

    try:
        sample = generate(CURATED[0])
        if not sample.story or "baboon" not in sample.story.lower() or "lantern" not in sample.story.lower():
            raise StoryError("Smoke test failed: generated story is missing required story content.")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke-test generation and emit succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mythic storyworld: a child, a baboon guardian, and a sacred lantern."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--lantern", choices=LANTERNS)
    ap.add_argument("--mood", choices=MOODS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--keeper", choices=["grandmother", "grandfather", "priestess", "priest"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.lantern and not lantern_belongs(args.place, args.lantern):
        raise StoryError(explain_place_lantern(args.place, args.lantern))
    if args.mood and args.gift and not gift_fits(args.mood, args.gift):
        raise StoryError(explain_gift(args.mood, args.gift))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.lantern is None or combo[1] == args.lantern)
        and (args.mood is None or combo[2] == args.mood)
        and (args.gift is None or combo[3] == args.gift)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, lantern_id, mood_id, gift_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    keeper_type = args.keeper or rng.choice(["grandmother", "grandfather", "priestess", "priest"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        lantern=lantern_id,
        mood=mood_id,
        gift=gift_id,
        hero_name=name,
        hero_gender=gender,
        hero_trait=trait,
        keeper_type=keeper_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.lantern not in LANTERNS:
        raise StoryError(f"(Unknown lantern: {params.lantern})")
    if params.mood not in MOODS:
        raise StoryError(f"(Unknown mood: {params.mood})")
    if params.gift not in GIFTS:
        raise StoryError(f"(Unknown gift: {params.gift})")
    if not lantern_belongs(params.place, params.lantern):
        raise StoryError(explain_place_lantern(params.place, params.lantern))
    if not gift_fits(params.mood, params.gift):
        raise StoryError(explain_gift(params.mood, params.gift))

    world = tell(
        place=PLACES[params.place],
        lantern=LANTERNS[params.lantern],
        mood=MOODS[params.mood],
        gift=GIFTS[params.gift],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        hero_trait=params.hero_trait,
        keeper_type=params.keeper_type,
    )
    rendered = world.render().replace("hero", params.hero_name)
    rendered = rendered.replace(" keeper ", " old keeper ")
    rendered = rendered.replace("hero.id", params.hero_name)
    hero = world.facts["hero"]
    story = rendered.replace("hero.label", hero.label)
    story = story.replace(" hero ", f" {hero.label} ")
    story = story.replace("hero", hero.label)
    story = story.replace("keeper", world.facts["keeper"].label)

    # Clean direct entity-id labels in narration.
    story = story.replace("the old old keeper", "the old keeper")
    story = story.replace("  ", " ")

    return StorySample(
        params=params,
        story=story,
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
        print(f"{len(combos)} compatible (place, lantern, mood, gift) combos:\n")
        for place_id, lantern_id, mood_id, gift_id in combos:
            print(f"  {place_id:11} {lantern_id:13} {mood_id:7} {gift_id}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.lantern} at {p.place} ({p.mood}, {p.gift})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
