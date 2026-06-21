#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/courteous_cautionary_myth.py
=======================================================

A standalone story world for a small cautionary myth about courtesy.

In these tales, a child and an elder go to an old enchanted place to ask for
something simple: water, fruit, or safe crossing. The elder knows the old rule:
one must be courteous there. If the child acts rudely first, the guardian of the
place sends trouble into the world. The only hopeful repair is a true apology
plus a fitting little gift. Some gifts are worthy enough to mend the trouble;
some are too slight, and the lesson ends sadly.

Run it
------
    python storyworlds/worlds/gpt-5.4/courteous_cautionary_myth.py
    python storyworlds/worlds/gpt-5.4/courteous_cautionary_myth.py --place spring --wish water
    python storyworlds/worlds/gpt-5.4/courteous_cautionary_myth.py --gift polished_shell
    python storyworlds/worlds/gpt-5.4/courteous_cautionary_myth.py --gift dry_leaf
    python storyworlds/worlds/gpt-5.4/courteous_cautionary_myth.py --all
    python storyworlds/worlds/gpt-5.4/courteous_cautionary_myth.py --qa --json
    python storyworlds/worlds/gpt-5.4/courteous_cautionary_myth.py --verify
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
SENSE_MIN = 2


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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    domain: str
    guardian_name: str
    guardian_type: str
    resource: str
    opening: str
    trouble_text: str
    ending_text: str
    loss_text: str
    sternness: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class Wish:
    id: str
    domain: str
    want: str
    need: str
    gain: str
    tags: set[str] = field(default_factory=set)


@dataclass
class RudeAct:
    id: str
    domain: str
    text: str
    offense_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    grace: int
    sense: int
    domains: set[str] = field(default_factory=set)
    prayer: str = ""
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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_guardian_wrath(world: World) -> list[str]:
    child = world.get("child")
    guardian = world.get("guardian")
    place = world.get("place")
    if child.meters["offense"] < THRESHOLD:
        return []
    sig = ("wrath", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    guardian.memes["anger"] += 1
    place.meters["trouble"] += 1
    child.memes["fear"] += 1
    return ["__wrath__"]


CAUSAL_RULES = [
    Rule(name="guardian_wrath", tag="social", apply=_r_guardian_wrath),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                out.extend(s for s in lines if not s.startswith("__"))
    if narrate:
        for line in out:
            world.say(line)
    return out


def wish_fits(place: Place, wish: Wish) -> bool:
    return place.domain == wish.domain and place.resource == wish.id


def gift_fits(place: Place, gift: Gift) -> bool:
    return place.domain in gift.domains


def sensible_gifts() -> list[Gift]:
    return [g for g in GIFTS.values() if g.sense >= SENSE_MIN]


def severity(place: Place, delay: int) -> int:
    return place.sternness + delay


def is_mended(place: Place, gift: Gift, delay: int) -> bool:
    return gift.grace >= severity(place, delay)


def explain_rejection(place: Place, wish: Wish, gift: Gift) -> str:
    if not wish_fits(place, wish):
        return (
            f"(No story: {place.label} is a {place.domain} place, so it does not answer "
            f"a request for {wish.id}. Pick a wish that belongs there.)"
        )
    if not gift_fits(place, gift):
        return (
            f"(No story: {gift.phrase} is not a fitting gift for {place.label}. "
            f"The guardian there accepts gifts from the {place.domain} tradition.)"
        )
    if gift.sense < SENSE_MIN:
        better = ", ".join(sorted(g.id for g in sensible_gifts() if place.domain in g.domains))
        return (
            f"(Refusing gift '{gift.id}': it is too slight for a repair offering "
            f"(sense={gift.sense} < {SENSE_MIN}). Try: {better}.)"
        )
    return "(No story: that combination does not make a reasonable myth.)"


def predict_trouble(world: World) -> bool:
    sim = world.copy()
    sim.get("child").meters["offense"] += 1
    propagate(sim, narrate=False)
    return sim.get("place").meters["trouble"] >= THRESHOLD


def introduce(world: World, child: Entity, elder: Entity, place: Place, wish: Wish) -> None:
    world.say(
        f"In the days when hills still listened, {child.id} walked with {child.pronoun('possessive')} "
        f"{elder.label_word} to {place.phrase}. They had come because {wish.need}."
    )
    world.say(place.opening)
    child.memes["hope"] += 1


def old_rule(world: World, child: Entity, elder: Entity, place: Place) -> None:
    world.say(
        f'"Remember," said {child.pronoun("possessive")} {elder.label_word}, '
        f'"the old ones called this place holy. Be courteous here, and speak as if '
        f'{place.guardian_name} can hear."'
    )
    child.memes["warning"] += 1
    world.facts["predicted_trouble"] = predict_trouble(world)


def desire(world: World, child: Entity, wish: Wish) -> None:
    child.memes["desire"] += 1
    world.say(
        f"But {child.id} wanted {wish.want} at once. Hurry climbed into "
        f"{child.pronoun('possessive')} chest like a little drum."
    )


def offend(world: World, child: Entity, rude: RudeAct) -> None:
    child.meters["offense"] += 1
    child.memes["defiance"] += 1
    propagate(world, narrate=False)
    world.say(rude.text)
    world.say(rude.offense_text)


def trouble(world: World, place: Place) -> None:
    world.say(place.trouble_text)


def remorse(world: World, child: Entity, elder: Entity, gift: Gift, place: Place) -> None:
    child.memes["shame"] += 1
    child.memes["courtesy"] += 1
    world.say(
        f"{child.id} shrank close to {child.pronoun('possessive')} {elder.label_word}. "
        f'"I was not courteous," {child.pronoun()} whispered.'
    )
    world.say(
        f'"Then mend what you bent," said the {elder.label_word}. '
        f'"Set down {gift.phrase}, bow your head, and say, {gift.prayer}"'
    )


def repair_success(world: World, child: Entity, gift: Gift, place: Place, wish: Wish) -> None:
    child.memes["relief"] += 1
    child.memes["lesson"] += 1
    world.get("place").meters["trouble"] = 0.0
    world.get("guardian").memes["anger"] = 0.0
    world.say(
        f"{child.id} laid down {gift.phrase} with both hands, as gently as a bird setting a feather. "
        f"For a breath nothing moved."
    )
    world.say(
        f"Then {place.guardian_name} softened. {place.ending_text} {wish.gain}"
    )


def repair_fail(world: World, child: Entity, gift: Gift, place: Place, wish: Wish) -> None:
    child.memes["sorrow"] += 1
    child.memes["lesson"] += 1
    world.say(
        f"{child.id} laid down {gift.phrase} and spoke the apology, but the hurt was deeper than that small peace could mend."
    )
    world.say(
        f"{place.loss_text} {wish.id.capitalize()} did not come to them that day."
    )


def closing_good(world: World, child: Entity, elder: Entity) -> None:
    world.say(
        f"On the road home, {child.id} walked more slowly. Even the dust under "
        f"{child.pronoun('possessive')} feet seemed worth a kind word now."
    )


def closing_sad(world: World, child: Entity, elder: Entity) -> None:
    world.say(
        f"All the way home, {child.id} kept quiet beside {child.pronoun('possessive')} "
        f"{elder.label_word}. Since then, whenever {child.pronoun()} came to an old place, "
        f"{child.pronoun()} remembered that rudeness can close a hand that courtesy might have opened."
    )


def tell(
    place: Place,
    wish: Wish,
    rude: RudeAct,
    gift: Gift,
    child_name: str = "Nila",
    child_gender: str = "girl",
    elder_type: str = "mother",
    delay: int = 0,
) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, phrase=child_name, role="child"))
    elder = world.add(Entity(id="elder", kind="character", type=elder_type, label=elder_type, phrase=f"the {elder_type}", role="elder"))
    guardian = world.add(
        Entity(
            id="guardian",
            kind="character",
            type=place.guardian_type,
            label=place.guardian_name,
            phrase=place.guardian_name,
            role="guardian",
            tags=set(place.tags),
        )
    )
    world.add(Entity(id="place", type="place", label=place.label, phrase=place.phrase, tags=set(place.tags)))

    world.facts["child_name"] = child_name

    introduce(world, child, elder, place, wish)
    old_rule(world, child, elder, place)
    world.para()
    desire(world, child, wish)
    offend(world, child, rude)
    trouble(world, place)
    world.para()
    remorse(world, child, elder, gift, place)

    mended = is_mended(place, gift, delay)
    if mended:
        repair_success(world, child, gift, place, wish)
        world.para()
        closing_good(world, child, elder)
        outcome = "mended"
    else:
        repair_fail(world, child, gift, place, wish)
        world.para()
        closing_sad(world, child, elder)
        outcome = "lost"

    world.facts.update(
        child=child,
        elder=elder,
        guardian=guardian,
        place_cfg=place,
        wish_cfg=wish,
        rude_cfg=rude,
        gift_cfg=gift,
        outcome=outcome,
        delay=delay,
        severity=severity(place, delay),
        repaired=mended,
        offended=child.meters["offense"] >= THRESHOLD,
    )
    return world


PLACES = {
    "spring": Place(
        id="spring",
        label="the moon spring",
        phrase="the Moon Spring under the reeds",
        domain="water",
        guardian_name="the Silver Fish Queen",
        guardian_type="spirit",
        resource="water",
        opening="Its pool was clear enough to hold the sky like a blue bowl.",
        trouble_text="At once the bright water clouded. Cold mist climbed from the pool and wrapped the path, so that stones and roots vanished under white breath.",
        ending_text="The mist uncurled, and the spring shone clear again.",
        loss_text="The mist stayed upon the spring, and the path home remained slow and blind.",
        sternness=1,
        tags={"water", "courtesy"},
    ),
    "tree": Place(
        id="tree",
        label="the fig tree of noon",
        phrase="the Fig Tree of Noon on the hill",
        domain="tree",
        guardian_name="Old Leaf-Mother",
        guardian_type="spirit",
        resource="fruit",
        opening="Golden figs hung there like little lamps among the leaves.",
        trouble_text="The branches shivered though there was no wind. Bitter leaves spun down, and every fig drew itself high among the boughs, out of reach.",
        ending_text="The leaves settled, and three ripe figs dropped softly into the grass.",
        loss_text="The leaves stayed bitter and the figs hid high, too far for any hand.",
        sternness=2,
        tags={"tree", "fruit", "courtesy"},
    ),
    "bridge": Place(
        id="bridge",
        label="the echo bridge",
        phrase="the Echo Bridge over the ravine",
        domain="bridge",
        guardian_name="the Listener Beneath the Arch",
        guardian_type="spirit",
        resource="crossing",
        opening="Its stones were old and pale, and every footstep came back twice.",
        trouble_text="A hollow ringing rose from the stones. The bridge blurred as if made of smoke, and the ravine below seemed deeper than before.",
        ending_text="The ringing faded, and the bridge stood firm as a patient back under the sky.",
        loss_text="The stones kept their smoke-like shimmer, and no safe crossing showed itself.",
        sternness=2,
        tags={"bridge", "travel", "courtesy"},
    ),
}

WISHES = {
    "water": Wish(
        id="water",
        domain="water",
        want="to fill the clay jar and hurry home",
        need="their house jar had gone dry by noon",
        gain="The child filled the jar, and the water tasted cool as morning.",
        tags={"water"},
    ),
    "fruit": Wish(
        id="fruit",
        domain="tree",
        want="to pluck the brightest figs before the sun moved",
        need="their supper basket was still light",
        gain="They carried the figs home in a fold of cloth, sweet enough to perfume the whole path.",
        tags={"fruit"},
    ),
    "crossing": Wish(
        id="crossing",
        domain="bridge",
        want="to run across before the light left the valley",
        need="they still had far to go before dusk",
        gain="They crossed the ravine safely, and the evening star found them already on the warm side of the hill.",
        tags={"travel"},
    ),
}

RUDE_ACTS = {
    "splash": RudeAct(
        id="splash",
        domain="water",
        text='Instead of asking, the child stamped the bank and slapped the pool with a branch. "Give it to me now," the child said.',
        offense_text="That sharp little greed broke the stillness like a thrown pebble.",
        tags={"rude", "water"},
    ),
    "snatch": RudeAct(
        id="snatch",
        domain="tree",
        text='Instead of asking, the child jumped and clawed at the low branch. "The figs are for whoever can grab them," the child said.',
        offense_text="The leaves heard the boast and curled at its edge.",
        tags={"rude", "tree"},
    ),
    "kick": RudeAct(
        id="kick",
        domain="bridge",
        text='Instead of bowing, the child kicked one pale stone and shouted, "Move aside. We need to cross."',
        offense_text="The sound went under the arch and came back colder than before.",
        tags={"rude", "bridge"},
    ),
}

GIFTS = {
    "little_song": Gift(
        id="little_song",
        label="little song",
        phrase="a little song",
        grace=2,
        sense=3,
        domains={"water", "tree", "bridge"},
        prayer='"Guardian, forgive my rough hands. I ask in peace."',
        tags={"song", "courtesy"},
    ),
    "flower_wreath": Gift(
        id="flower_wreath",
        label="flower wreath",
        phrase="a wreath of river flowers",
        grace=2,
        sense=3,
        domains={"water", "tree"},
        prayer='"Bright keeper, forgive me. I have come back with gentle hands."',
        tags={"flowers", "courtesy"},
    ),
    "honey_cake": Gift(
        id="honey_cake",
        label="honey cake",
        phrase="a small honey cake",
        grace=3,
        sense=3,
        domains={"tree", "bridge"},
        prayer='"Kind watcher, forgive my haste. Let sweetness answer my sharpness."',
        tags={"food", "courtesy"},
    ),
    "polished_shell": Gift(
        id="polished_shell",
        label="polished shell",
        phrase="a polished shell from the river road",
        grace=1,
        sense=2,
        domains={"water"},
        prayer='"Silver queen, forgive me. I speak softly now."',
        tags={"shell", "courtesy"},
    ),
    "dry_leaf": Gift(
        id="dry_leaf",
        label="dry leaf",
        phrase="one dry leaf",
        grace=1,
        sense=1,
        domains={"tree", "bridge", "water"},
        prayer='"Please forgive me."',
        tags={"leaf"},
    ),
}

GIRL_NAMES = ["Nila", "Ira", "Tavi", "Mira", "Luma", "Sena", "Rina", "Aya"]
BOY_NAMES = ["Ivo", "Tarin", "Milo", "Soren", "Daro", "Pelin", "Rami", "Niko"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for wish_id, wish in WISHES.items():
            if not wish_fits(place, wish):
                continue
            for rude_id, rude in RUDE_ACTS.items():
                if rude.domain != place.domain:
                    continue
                for gift_id, gift in GIFTS.items():
                    if gift_fits(place, gift):
                        combos.append((place_id, wish_id, rude_id, gift_id))
    return combos


@dataclass
class StoryParams:
    place: str
    wish: str
    rude_act: str
    gift: str
    child_name: str
    child_gender: str
    elder: str
    delay: int = 0
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="spring",
        wish="water",
        rude_act="splash",
        gift="flower_wreath",
        child_name="Nila",
        child_gender="girl",
        elder="mother",
        delay=0,
    ),
    StoryParams(
        place="tree",
        wish="fruit",
        rude_act="snatch",
        gift="honey_cake",
        child_name="Tarin",
        child_gender="boy",
        elder="father",
        delay=0,
    ),
    StoryParams(
        place="bridge",
        wish="crossing",
        rude_act="kick",
        gift="little_song",
        child_name="Mira",
        child_gender="girl",
        elder="mother",
        delay=1,
    ),
    StoryParams(
        place="tree",
        wish="fruit",
        rude_act="snatch",
        gift="dry_leaf",
        child_name="Ivo",
        child_gender="boy",
        elder="father",
        delay=1,
    ),
    StoryParams(
        place="bridge",
        wish="crossing",
        rude_act="kick",
        gift="dry_leaf",
        child_name="Aya",
        child_gender="girl",
        elder="mother",
        delay=1,
    ),
]

KNOWLEDGE = {
    "courtesy": [
        (
            "What does courteous mean?",
            "Courteous means polite and respectful. A courteous person uses gentle words and remembers that other people and places matter."
        )
    ],
    "myth": [
        (
            "What is a myth?",
            "A myth is an old kind of story that explains the world with wonder. Myths often have magical beings, rules, and lessons."
        )
    ],
    "water": [
        (
            "Why do people bring water home in a jar?",
            "A jar can carry water from a spring or a well back to the house. Before pipes, that was how many families got water."
        )
    ],
    "fruit": [
        (
            "Why shouldn't you snatch fruit from a tree?",
            "Snatching is rough and careless, and it can break branches or bruise fruit. Asking, reaching gently, or waiting for help is kinder."
        )
    ],
    "bridge": [
        (
            "Why should you walk carefully on a bridge?",
            "Bridges are for safe crossing, so you should walk carefully and not kick or shake them. Careful feet help everyone stay safe."
        )
    ],
    "song": [
        (
            "Why can a song feel like a gift?",
            "A song takes time, breath, and attention. When sung kindly, it can show thanks and respect."
        )
    ],
    "flowers": [
        (
            "Why do people make flower wreaths?",
            "A flower wreath is a circle woven from flowers and stems. People make them as decorations or as gentle offerings."
        )
    ],
    "food": [
        (
            "Why is sharing food a respectful thing to do?",
            "Food is precious because it takes work to make. Sharing it can show welcome, thanks, or apology."
        )
    ],
}
KNOWLEDGE_ORDER = ["courtesy", "myth", "water", "fruit", "bridge", "song", "flowers", "food"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place_cfg"]
    wish = f["wish_cfg"]
    gift = f["gift_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a short cautionary myth for a 3-to-5-year-old that includes the word "courteous" '
        f"and takes place at {place.phrase}."
    )
    if outcome == "mended":
        return [
            base,
            f"Tell a myth where a child is rude at an enchanted {place.domain} place, causes trouble, then learns to be courteous and repairs the harm with {gift.phrase}.",
            f"Write a gentle old-fashioned tale where an elder teaches that courtesy opens what hurry tries to seize, and the child receives {wish.id} only after apologizing.",
        ]
    return [
        base,
        f"Tell a cautionary myth where a child behaves rudely at {place.phrase}, offers only {gift.phrase} afterward, and learns too late that courtesy matters.",
        f"Write an old moral tale in which haste and disrespect close a magical place, leaving the child sad but wiser.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    place = f["place_cfg"]
    wish = f["wish_cfg"]
    rude = f["rude_cfg"]
    gift = f["gift_cfg"]
    outcome = f["outcome"]
    qa = [
        (
            "Who is the story about?",
            f"It is about {child.label}, a child traveling with {child.pronoun('possessive')} {elder.label_word}, and the old guardian of {place.label}. They went there because {wish.need}."
        ),
        (
            f"Why did they go to {place.label}?",
            f"They went because {wish.need}. The child hoped to get {wish.id} there and hurry home."
        ),
        (
            "What warning did the elder give?",
            f"The elder said the place was holy and that the child should be courteous there. That warning mattered because the old guardian could be offended by rough, greedy behavior."
        ),
        (
            f"What rude thing did the child do?",
            f"The child did not ask politely. Instead, {rude.text.split('. ')[0].lower()}."
        ),
        (
            "What happened after the rude act?",
            f"{place.trouble_text} The trouble came because the child's offense woke the guardian's anger."
        ),
        (
            "How did the child try to mend the harm?",
            f"The child admitted, \"I was not courteous,\" and offered {gift.phrase} with an apology. The repair mattered because the myth treats courtesy as something shown in both words and actions."
        ),
    ]
    if outcome == "mended":
        qa.append(
            (
                "How did the story end?",
                f"The guardian forgave the child, and the place opened again. {wish.gain} The ending proves that a true apology and a fitting gift can mend a wrong."
            )
        )
    else:
        qa.append(
            (
                "How did the story end?",
                f"The gift was too small to mend the hurt, so the place stayed closed. {wish.id.capitalize()} did not come to them that day, and the child walked home wiser and sadder."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"courtesy", "myth"} | set(f["place_cfg"].tags) | set(f["gift_cfg"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
wish_fits(P, W) :- place(P), wish(W), place_domain(P, D), wish_domain(W, D), place_resource(P, W).
gift_fits(P, G) :- place(P), gift(G), place_domain(P, D), gift_domain(G, D).
valid(P, W, R, G) :- place(P), rude(R), wish_fits(P, W), rude_domain(R, D), place_domain(P, D), gift_fits(P, G).

sensible(G) :- gift(G), sense(G, S), sense_min(M), S >= M.

severity(V) :- chosen_place(P), sternness(P, S), delay(D), V = S + D.
mended :- chosen_place(P), chosen_gift(G), gift_fits(P, G), severity(V), grace(G, Gr), Gr >= V.
outcome(mended) :- mended.
outcome(lost) :- not mended.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("place_domain", pid, place.domain))
        lines.append(asp.fact("place_resource", pid, place.resource))
        lines.append(asp.fact("sternness", pid, place.sternness))
    for wid, wish in WISHES.items():
        lines.append(asp.fact("wish", wid))
        lines.append(asp.fact("wish_domain", wid, wish.domain))
    for rid, rude in RUDE_ACTS.items():
        lines.append(asp.fact("rude", rid))
        lines.append(asp.fact("rude_domain", rid, rude.domain))
    for gid, gift in GIFTS.items():
        lines.append(asp.fact("gift", gid))
        lines.append(asp.fact("grace", gid, gift.grace))
        lines.append(asp.fact("sense", gid, gift.sense))
        for domain in sorted(gift.domains):
            lines.append(asp.fact("gift_domain", gid, domain))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(g for (g,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_gift", params.gift),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    place = PLACES[params.place]
    gift = GIFTS[params.gift]
    return "mended" if is_mended(place, gift, params.delay) else "lost"


def asp_verify() -> int:
    rc = 0

    c_valid = set(asp_valid_combos())
    p_valid = set(valid_combos())
    if c_valid == p_valid:
        print(f"OK: gate matches valid_combos() ({len(c_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_valid - p_valid:
            print("  only in clingo:", sorted(c_valid - p_valid))
        if p_valid - c_valid:
            print("  only in python:", sorted(p_valid - c_valid))

    c_sens = set(asp_sensible())
    p_sens = {g.id for g in sensible_gifts()}
    if c_sens == p_sens:
        print(f"OK: sensible gifts match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible gifts: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    for seed in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a courteous cautionary myth. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--wish", choices=WISHES)
    ap.add_argument("--rude-act", dest="rude_act", choices=RUDE_ACTS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--elder", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--delay", type=int, choices=[0, 1], help="extra time before the apology takes hold")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.wish:
        place = PLACES[args.place]
        wish = WISHES[args.wish]
        gift = GIFTS[args.gift] if args.gift else next(iter(GIFTS.values()))
        if not wish_fits(place, wish):
            raise StoryError(explain_rejection(place, wish, gift))
    if args.place and args.gift:
        place = PLACES[args.place]
        gift = GIFTS[args.gift]
        wish = WISHES[args.wish] if args.wish else WISHES[place.resource]
        if not gift_fits(place, gift) or gift.sense < SENSE_MIN:
            raise StoryError(explain_rejection(place, wish, gift))
    if args.gift and not args.place and GIFTS[args.gift].sense < SENSE_MIN:
        raise StoryError(
            f"(Refusing gift '{args.gift}': it scores too low on common sense "
            f"(sense={GIFTS[args.gift].sense} < {SENSE_MIN}). Pick a sturdier offering.)"
        )

    combos = [
        c
        for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.wish is None or c[1] == args.wish)
        and (args.rude_act is None or c[2] == args.rude_act)
        and (args.gift is None or c[3] == args.gift)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    if args.gift and GIFTS[args.gift].sense < SENSE_MIN:
        raise StoryError(
            f"(Refusing gift '{args.gift}': it scores too low on common sense "
            f"(sense={GIFTS[args.gift].sense} < {SENSE_MIN}).)"
        )

    place_id, wish_id, rude_id, gift_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(["mother", "father"])
    delay = args.delay if args.delay is not None else rng.choice([0, 1])
    return StoryParams(
        place=place_id,
        wish=wish_id,
        rude_act=rude_id,
        gift=gift_id,
        child_name=name,
        child_gender=gender,
        elder=elder,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.wish not in WISHES:
        raise StoryError(f"(Unknown wish: {params.wish})")
    if params.rude_act not in RUDE_ACTS:
        raise StoryError(f"(Unknown rude act: {params.rude_act})")
    if params.gift not in GIFTS:
        raise StoryError(f"(Unknown gift: {params.gift})")

    place = PLACES[params.place]
    wish = WISHES[params.wish]
    rude = RUDE_ACTS[params.rude_act]
    gift = GIFTS[params.gift]

    if not wish_fits(place, wish) or rude.domain != place.domain or not gift_fits(place, gift):
        raise StoryError(explain_rejection(place, wish, gift))
    if gift.sense < SENSE_MIN:
        raise StoryError(explain_rejection(place, wish, gift))

    world = tell(
        place=place,
        wish=wish,
        rude=rude,
        gift=gift,
        child_name=params.child_name,
        child_gender=params.child_gender,
        elder_type=params.elder,
        delay=params.delay,
    )
    return StorySample(
        params=params,
        story=world.render().replace("child", params.child_name),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a.replace("child", params.child_name)) for q, a in story_qa(world)],
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
        print(asp_program("", "#show valid/4.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible gifts: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, wish, rude_act, gift) combos:\n")
        for place, wish, rude, gift in combos:
            print(f"  {place:7} {wish:8} {rude:7} {gift}")
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
            header = f"### {p.child_name}: {p.place}, {p.wish}, {p.gift} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
