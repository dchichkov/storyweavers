#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/scrumptious_sound_effects_whodunit.py
================================================================

A standalone storyworld for a tiny child-facing whodunit built around a missing
snack, clue-tracing, and sound effects.

Premise
-------
A child helps make a scrumptious treat and leaves it to cool. When the plate is
suddenly missing a piece, two young detectives inspect the room. The world model
tracks who could reach the treat, what crumbs and smells they leave behind, what
sound they make in hiding, and whether the chosen hiding place fits the culprit.
The turn is not a random reveal: the detectives follow physical traces and then
hear the culprit's tell-tale sound from the correct place.

Coverage is deliberately narrow. Not every animal can hide everywhere; not every
treat suits every culprit. Invalid combinations are rejected with legible
StoryError messages.

Run it
------
    python storyworlds/worlds/gpt-5.4/scrumptious_sound_effects_whodunit.py
    python storyworlds/worlds/gpt-5.4/scrumptious_sound_effects_whodunit.py --all
    python storyworlds/worlds/gpt-5.4/scrumptious_sound_effects_whodunit.py --qa
    python storyworlds/worlds/gpt-5.4/scrumptious_sound_effects_whodunit.py --json
    python storyworlds/worlds/gpt-5.4/scrumptious_sound_effects_whodunit.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        animal = {"dog", "cat", "goat"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in animal:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    room_phrase: str
    cooling_spot: str
    detective_open: str
    hideouts: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Treat:
    id: str
    label: str
    phrase: str
    tray: str
    crumbs: str
    smell: str
    cooling_line: str
    tasty_to: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Culprit:
    id: str
    label: str
    type: str
    appetite: set[str] = field(default_factory=set)
    sound: str = ""
    verb: str = ""
    crumb_mark: str = ""
    innocent_mask: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Hideout:
    id: str
    label: str
    phrase: str
    sound_style: str
    fits: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    treat: str
    culprit: str
    hideout: str
    detective: str
    detective_gender: str
    partner: str
    partner_gender: str
    baker: str
    baker_type: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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


PLACES = {
    "bakery": Place(
        id="bakery",
        label="the little bakery kitchen",
        room_phrase="The little bakery kitchen smelled warm and sweet.",
        cooling_spot="the sunny window ledge",
        detective_open="Every spoon, bowl, and napkin looked as if it might know a secret.",
        hideouts={"tablecloth", "pantry", "bench"},
        tags={"kitchen", "bakery"},
    ),
    "school": Place(
        id="school",
        label="the school cooking room",
        room_phrase="The school cooking room buzzed softly after snack time.",
        cooling_spot="the long counter by the sink",
        detective_open="Even the big mixing bowl seemed to be waiting for questions.",
        hideouts={"tablecloth", "cubby", "bench"},
        tags={"school", "kitchen"},
    ),
    "garden": Place(
        id="garden",
        label="the garden picnic table",
        room_phrase="The garden picnic table sat under a shady pear tree.",
        cooling_spot="the middle of the picnic table",
        detective_open="Leaves flickered overhead as if they had seen everything.",
        hideouts={"basket", "bench", "bush"},
        tags={"garden", "picnic"},
    ),
}

TREATS = {
    "tarts": Treat(
        id="tarts",
        label="berry tarts",
        phrase="a plate of scrumptious berry tarts",
        tray="the blue plate",
        crumbs="flaky crumbs with purple jam dots",
        smell="sweet berry smell",
        cooling_line="They had to cool before anyone could nibble them.",
        tasty_to={"dog", "goat", "cat"},
        tags={"berries", "pastry", "scrumptious"},
    ),
    "buns": Treat(
        id="buns",
        label="cinnamon buns",
        phrase="a pan of scrumptious cinnamon buns",
        tray="the silver pan",
        crumbs="sticky crumbs dusted with cinnamon",
        smell="warm cinnamon smell",
        cooling_line="The icing gleamed while the buns rested.",
        tasty_to={"dog", "goat"},
        tags={"cinnamon", "bun", "scrumptious"},
    ),
    "sandwiches": Treat(
        id="sandwiches",
        label="jam sandwiches",
        phrase="a tray of scrumptious jam sandwiches",
        tray="the checkered tray",
        crumbs="soft crumbs with bright red jam smears",
        smell="sunny jam smell",
        cooling_line="They were lined up neatly for a picnic plate.",
        tasty_to={"dog", "goat", "cat"},
        tags={"jam", "bread", "scrumptious"},
    ),
}

CULPRITS = {
    "dog": Culprit(
        id="dog",
        label="the puppy",
        type="dog",
        appetite={"tarts", "buns", "sandwiches"},
        sound="sniff, sniff... woof!",
        verb="licked the crumbs from its nose",
        crumb_mark="a muddy paw print beside the plate",
        innocent_mask="had tried to look very small and very innocent",
        tags={"dog", "pet", "sound"},
    ),
    "cat": Culprit(
        id="cat",
        label="the cat",
        type="cat",
        appetite={"tarts", "sandwiches"},
        sound="scritch-scratch... mew!",
        verb="curled its tail around its paws",
        crumb_mark="a neat trail of tiny paw prints on the chair",
        innocent_mask="sat as still as a statue with jam on its whiskers",
        tags={"cat", "pet", "sound"},
    ),
    "goat": Culprit(
        id="goat",
        label="the little goat",
        type="goat",
        appetite={"tarts", "buns", "sandwiches"},
        sound="clop-clop... maa!",
        verb="blinked with a crooked mouthful of crumbs",
        crumb_mark="a few round hoof marks near the plate",
        innocent_mask="pretended a napkin was a very normal snack",
        tags={"goat", "animal", "sound"},
    ),
}

HIDEOUTS = {
    "tablecloth": Hideout(
        id="tablecloth",
        label="under the tablecloth",
        phrase="under the droopy tablecloth",
        sound_style="muffled",
        fits={"dog", "cat"},
        tags={"under_table", "sound"},
    ),
    "pantry": Hideout(
        id="pantry",
        label="inside the pantry",
        phrase="inside the half-open pantry",
        sound_style="echoey",
        fits={"dog", "goat"},
        tags={"pantry", "sound"},
    ),
    "bench": Hideout(
        id="bench",
        label="behind the wooden bench",
        phrase="behind the wooden bench",
        sound_style="hollow",
        fits={"dog", "cat", "goat"},
        tags={"bench", "sound"},
    ),
    "cubby": Hideout(
        id="cubby",
        label="inside the apron cubby",
        phrase="inside the apron cubby",
        sound_style="boxed",
        fits={"cat"},
        tags={"cubby", "sound"},
    ),
    "basket": Hideout(
        id="basket",
        label="inside the picnic basket",
        phrase="inside the big picnic basket",
        sound_style="rustly",
        fits={"cat", "dog"},
        tags={"basket", "sound"},
    ),
    "bush": Hideout(
        id="bush",
        label="behind the berry bush",
        phrase="behind the berry bush",
        sound_style="leafy",
        fits={"cat", "goat"},
        tags={"bush", "sound"},
    ),
}

GIRL_NAMES = ["Lila", "Nora", "Mia", "Tess", "Ruby", "Anna", "Zoe"]
BOY_NAMES = ["Ben", "Leo", "Max", "Finn", "Owen", "Sam", "Eli"]


def valid_combo(place_id: str, treat_id: str, culprit_id: str, hideout_id: str) -> bool:
    if place_id not in PLACES or treat_id not in TREATS or culprit_id not in CULPRITS or hideout_id not in HIDEOUTS:
        return False
    place = PLACES[place_id]
    treat = TREATS[treat_id]
    culprit = CULPRITS[culprit_id]
    hideout = HIDEOUTS[hideout_id]
    return (
        hideout_id in place.hideouts
        and culprit.type in hideout.fits
        and treat_id in culprit.appetite
        and culprit.type in treat.tasty_to
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in sorted(PLACES):
        for treat_id in sorted(TREATS):
            for culprit_id in sorted(CULPRITS):
                for hideout_id in sorted(HIDEOUTS):
                    if valid_combo(place_id, treat_id, culprit_id, hideout_id):
                        combos.append((place_id, treat_id, culprit_id, hideout_id))
    return combos


def explain_rejection(place_id: str, treat_id: str, culprit_id: str, hideout_id: str) -> str:
    if place_id not in PLACES:
        return f"(No story: unknown place '{place_id}'.)"
    if treat_id not in TREATS:
        return f"(No story: unknown treat '{treat_id}'.)"
    if culprit_id not in CULPRITS:
        return f"(No story: unknown culprit '{culprit_id}'.)"
    if hideout_id not in HIDEOUTS:
        return f"(No story: unknown hideout '{hideout_id}'.)"
    place = PLACES[place_id]
    treat = TREATS[treat_id]
    culprit = CULPRITS[culprit_id]
    hideout = HIDEOUTS[hideout_id]
    if hideout_id not in place.hideouts:
        return (
            f"(No story: {place.label} does not have {hideout.label}, so the mystery would "
            f"point to a place that is not really there.)"
        )
    if culprit.type not in hideout.fits:
        return (
            f"(No story: {culprit.label} would not sensibly fit {hideout.label}. "
            f"Pick a different hiding place.)"
        )
    return (
        f"(No story: {culprit.label} is not a sensible thief for {treat.phrase}. "
        f"Pick a treat the culprit would really try to eat.)"
    )


def culprit_kind(params: StoryParams) -> str:
    return CULPRITS[params.culprit].type


ASP_RULES = r"""
likes(C, T) :- culprit(C), treat(T), appetite(C, T), tasty_to(T, C).
can_hide(C, H) :- culprit(C), hideout(H), fits(H, C).
present_hideout(P, H) :- place(P), hideout(H), place_has(P, H).
valid(P, T, C, H) :- place(P), treat(T), culprit(C), hideout(H),
                     likes(C, T), can_hide(C, H), present_hideout(P, H).
chosen_kind(K) :- chosen_culprit(C), culprit_kind(C, K).
python_outcome(guilty) :- chosen_place(P), chosen_treat(T), chosen_culprit(C), chosen_hideout(H),
                          valid(P, T, C, H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for hideout_id in sorted(place.hideouts):
            lines.append(asp.fact("place_has", place_id, hideout_id))
    for treat_id, treat in TREATS.items():
        lines.append(asp.fact("treat", treat_id))
        for kind in sorted(treat.tasty_to):
            lines.append(asp.fact("tasty_to", treat_id, kind))
    for culprit_id, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", culprit_id))
        lines.append(asp.fact("culprit_kind", culprit_id, culprit.type))
        for treat_id in sorted(culprit.appetite):
            lines.append(asp.fact("appetite", culprit_id, treat_id))
    for hideout_id, hideout in HIDEOUTS.items():
        lines.append(asp.fact("hideout", hideout_id))
        for kind in sorted(hideout.fits):
            lines.append(asp.fact("fits", hideout_id, kind))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_culprit_kind(params: StoryParams) -> str:
    import asp
    extra = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_treat", params.treat),
            asp.fact("chosen_culprit", params.culprit),
            asp.fact("chosen_hideout", params.hideout),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show chosen_kind/1.\n#show python_outcome/1."))
    kinds = asp.atoms(model, "chosen_kind")
    outcome = asp.atoms(model, "python_outcome")
    if not outcome:
        return "?"
    return kinds[0][0] if kinds else "?"


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
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
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def intro(world: World, detective: Entity, partner: Entity, baker: Entity, place: Place, treat: Treat) -> None:
    detective.memes["pride"] += 1
    baker.memes["care"] += 1
    world.say(
        f"{detective.id} helped {baker.label_word} set out {treat.phrase} in {place.label}. "
        f"{place.room_phrase}"
    )
    world.say(
        f"The plate rested on {place.cooling_spot}, and {treat.cooling_line}"
    )
    world.say(
        f"{partner.id} leaned close and whispered, \"They look scrumptious.\""
    )


def discover_missing(world: World, detective: Entity, partner: Entity, treat: Treat, culprit_cfg: Culprit) -> None:
    plate = world.get("plate")
    plate.meters["missing_piece"] += 1
    detective.memes["surprise"] += 1
    partner.memes["curiosity"] += 1
    world.say(
        f"But when {detective.id} came back with napkins, one piece was gone from {treat.tray}."
    )
    world.say(
        f"Only {treat.crumbs} and {culprit_cfg.crumb_mark} were left behind."
    )
    world.say(
        f"\"A snack thief!\" gasped {partner.id}. \"This is a whodunit.\""
    )


def inspect_clues(world: World, detective: Entity, partner: Entity, place: Place, treat: Treat, culprit: Entity, hideout: Hideout) -> None:
    detective.memes["focus"] += 1
    partner.memes["focus"] += 1
    culprit.meters["crumbs_on_face"] += 1
    culprit.memes["guilty"] += 1
    world.say(
        f"{detective.id} crouched beside the plate. \"The clues say our thief loved the {treat.smell},\" "
        f"{detective.pronoun()} said."
    )
    world.say(
        f"{partner.id} followed the trail across the floor. {place.detective_open}"
    )
    world.say(
        f"The tiny trail led toward {hideout.phrase}, where the room turned very quiet."
    )


def listen(world: World, detective: Entity, partner: Entity, culprit_cfg: Culprit, hideout: Hideout) -> None:
    world.say(
        f"Then they stopped and listened. {hideout.sound_style.capitalize()} from the shadows came "
        f"\"{culprit_cfg.sound}\""
    )
    detective.memes["certainty"] += 1
    partner.memes["certainty"] += 1
    world.say(
        f"{partner.id}'s eyes grew round. \"That sound belongs to {culprit_cfg.label}!\""
    )


def reveal(world: World, detective: Entity, partner: Entity, baker: Entity, culprit: Entity, culprit_cfg: Culprit, hideout: Hideout, treat: Treat) -> None:
    culprit.meters["found"] += 1
    culprit.memes["shame"] += 1
    baker.memes["calm"] += 1
    world.say(
        f"{detective.id} lifted the cloth and peeked {hideout.phrase}. There was {culprit_cfg.label}. "
        f"It {culprit_cfg.verb} and {culprit_cfg.innocent_mask}."
    )
    world.say(
        f"{baker.label_word.capitalize()} could not help smiling. \"So that is our crumbly culprit,\" "
        f"{baker.pronoun()} said."
    )
    world.say(
        f"{detective.id} pointed to the crumbs. \"The missing piece came from {treat.tray}, and the sound gave the thief away.\""
    )


def resolve(world: World, detective: Entity, partner: Entity, baker: Entity, culprit_cfg: Culprit, treat: Treat) -> None:
    detective.memes["relief"] += 1
    partner.memes["relief"] += 1
    baker.memes["wisdom"] += 1
    world.say(
        f"{baker.label_word.capitalize()} broke off a tiny proper nibble for {culprit_cfg.label} and moved the rest of {treat.phrase} higher up."
    )
    world.say(
        f"\"Mysteries are easier to solve when we look, listen, and keep calm,\" {baker.pronoun()} said."
    )
    world.say(
        f"Soon the room felt bright again, and when snack time finally came, the friends ate the remaining treats slowly, declaring them every bit as scrumptious as before."
    )


def tell(params: StoryParams) -> World:
    if not valid_combo(params.place, params.treat, params.culprit, params.hideout):
        raise StoryError(explain_rejection(params.place, params.treat, params.culprit, params.hideout))

    place = PLACES[params.place]
    treat = TREATS[params.treat]
    culprit_cfg = CULPRITS[params.culprit]
    hideout = HIDEOUTS[params.hideout]

    world = World()
    detective = world.add(Entity(id=params.detective, kind="character", type=params.detective_gender, role="detective"))
    partner = world.add(Entity(id=params.partner, kind="character", type=params.partner_gender, role="partner"))
    baker = world.add(Entity(id=params.baker, kind="character", type=params.baker_type, role="baker", label="the baker"))
    culprit = world.add(Entity(id="culprit", kind="character", type=culprit_cfg.type, role="culprit", label=culprit_cfg.label))
    plate = world.add(Entity(id="plate", type="plate", label=treat.tray))
    scene = world.add(Entity(id="scene", type="place", label=place.label))

    intro(world, detective, partner, baker, place, treat)
    world.para()
    discover_missing(world, detective, partner, treat, culprit_cfg)
    inspect_clues(world, detective, partner, place, treat, culprit, hideout)
    world.para()
    listen(world, detective, partner, culprit_cfg, hideout)
    reveal(world, detective, partner, baker, culprit, culprit_cfg, hideout, treat)
    world.para()
    resolve(world, detective, partner, baker, culprit_cfg, treat)

    world.facts.update(
        detective=detective,
        partner=partner,
        baker=baker,
        culprit=culprit,
        culprit_cfg=culprit_cfg,
        place=place,
        treat=treat,
        hideout=hideout,
        solved=culprit.meters["found"] >= THRESHOLD,
        sound=culprit_cfg.sound,
        clue=treat.crumbs,
        mark=culprit_cfg.crumb_mark,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    d = f["detective"]
    p = f["partner"]
    t = f["treat"]
    c = f["culprit_cfg"]
    return [
        f'Write a short whodunit for a 3-to-5-year-old that includes the word "scrumptious" and uses sound effects.',
        f"Tell a gentle mystery where {d.id} and {p.id} follow crumbs from {t.phrase} and solve the case by listening for \"{c.sound}\".",
        f"Write a child-facing snack mystery with a missing treat, clue-tracing, and a soft funny reveal of {c.label}.",
    ]


def story_qa_items(world: World) -> list[tuple[str, str]]:
    f = world.facts
    d = f["detective"]
    p = f["partner"]
    b = f["baker"]
    c = f["culprit_cfg"]
    t = f["treat"]
    h = f["hideout"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {d.id} and {p.id}, two little detectives, plus {d.id}'s {b.label_word} and {c.label}. "
            f"They are all in the same small snack mystery."
        ),
        (
            "What went missing?",
            f"One piece went missing from {t.phrase}. The empty spot on {t.tray} is what started the whodunit."
        ),
        (
            "What clues did the children find?",
            f"They found {t.crumbs} and {f['mark']}. Those physical clues showed that someone had sneaked close enough to steal a bite."
        ),
        (
            "How did they solve the mystery?",
            f"They followed the crumb trail toward {h.label} and then stopped to listen. "
            f"When they heard \"{f['sound']}\", they knew the hidden thief had given itself away."
        ),
        (
            "Who took the treat, and why did the children know?",
            f"{c.label.capitalize()} took it. The detectives matched the crumbs, the track marks, and the sound from the hiding place, so the answer came from the clues instead of a guess."
        ),
        (
            "How did the story end?",
            f"The baker stayed calm, gave the culprit a tiny proper nibble, and moved the rest of the treats up high. "
            f"At the end the room felt peaceful again, and everyone remembered how scrumptious the snack smelled."
        ),
    ]
    return qa


KNOWLEDGE = {
    "whodunit": [
        (
            "What is a whodunit?",
            "A whodunit is a mystery story where people look for clues to find out who did something. The fun is in noticing signs and solving the puzzle."
        )
    ],
    "sound": [
        (
            "Why can sounds be clues?",
            "Sounds can tell you where someone is or what they are doing, even if you cannot see them yet. A bark, a mew, or a clatter can point to the answer."
        )
    ],
    "dog": [
        (
            "What sound does a puppy make?",
            "A puppy can sniff, snuffle, and bark. Those sounds are often clues that a dog is nearby."
        )
    ],
    "cat": [
        (
            "What sound does a cat make?",
            "A cat can mew, purr, and make little scratchy sounds with its paws. Those sounds can help you notice it hiding."
        )
    ],
    "goat": [
        (
            "What sound does a goat make?",
            "A goat often says 'maa' and makes cloppy hoof sounds. Those noises can be easy to hear on a floor or path."
        )
    ],
    "crumbs": [
        (
            "What are crumbs?",
            "Crumbs are tiny little bits that break off bread, cake, or pastry. They can show where food has been carried or eaten."
        )
    ],
    "scrumptious": [
        (
            "What does scrumptious mean?",
            "Scrumptious means something smells or tastes very, very good. It is a happy word for delicious food."
        )
    ],
}
KNOWLEDGE_ORDER = ["whodunit", "sound", "crumbs", "scrumptious", "dog", "cat", "goat"]


def world_knowledge_items(world: World) -> list[tuple[str, str]]:
    culprit_type = world.facts["culprit_cfg"].type
    tags = ["whodunit", "sound", "crumbs", "scrumptious", culprit_type]
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


CURATED = [
    StoryParams(
        place="bakery",
        treat="tarts",
        culprit="dog",
        hideout="tablecloth",
        detective="Lila",
        detective_gender="girl",
        partner="Ben",
        partner_gender="boy",
        baker="Mama",
        baker_type="mother",
    ),
    StoryParams(
        place="school",
        treat="sandwiches",
        culprit="cat",
        hideout="cubby",
        detective="Max",
        detective_gender="boy",
        partner="Nora",
        partner_gender="girl",
        baker="Dad",
        baker_type="father",
    ),
    StoryParams(
        place="garden",
        treat="buns",
        culprit="goat",
        hideout="bush",
        detective="Ruby",
        detective_gender="girl",
        partner="Finn",
        partner_gender="boy",
        baker="Mama",
        baker_type="mother",
    ),
    StoryParams(
        place="bakery",
        treat="buns",
        culprit="goat",
        hideout="pantry",
        detective="Eli",
        detective_gender="boy",
        partner="Mia",
        partner_gender="girl",
        baker="Dad",
        baker_type="father",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny sound-effects whodunit about a scrumptious missing snack."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--treat", choices=sorted(TREATS))
    ap.add_argument("--culprit", choices=sorted(CULPRITS))
    ap.add_argument("--hideout", choices=sorted(HIDEOUTS))
    ap.add_argument("--detective")
    ap.add_argument("--partner")
    ap.add_argument("--gender", choices=["girl", "boy"], help="detective gender if name is randomized")
    ap.add_argument("--partner-gender", choices=["girl", "boy"])
    ap.add_argument("--baker", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.treat and args.culprit and args.hideout:
        if not valid_combo(args.place, args.treat, args.culprit, args.hideout):
            raise StoryError(explain_rejection(args.place, args.treat, args.culprit, args.hideout))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.treat is None or combo[1] == args.treat)
        and (args.culprit is None or combo[2] == args.culprit)
        and (args.hideout is None or combo[3] == args.hideout)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, treat, culprit, hideout = rng.choice(combos)
    detective_gender = args.gender or rng.choice(["girl", "boy"])
    partner_gender = args.partner_gender or rng.choice(["girl", "boy"])
    detective = args.detective or pick_name(rng, detective_gender)
    partner = args.partner or pick_name(rng, partner_gender, avoid=detective)
    baker_type = args.baker or rng.choice(["mother", "father"])
    baker_name = "Mama" if baker_type == "mother" else "Dad"
    return StoryParams(
        place=place,
        treat=treat,
        culprit=culprit,
        hideout=hideout,
        detective=detective,
        detective_gender=detective_gender,
        partner=partner,
        partner_gender=partner_gender,
        baker=baker_name,
        baker_type=baker_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.treat not in TREATS or params.culprit not in CULPRITS or params.hideout not in HIDEOUTS:
        raise StoryError("(No story: one or more parameters are unknown to this world.)")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_items(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_items(world)],
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

    for params in CURATED[:3]:
        asp_kind = asp_culprit_kind(params)
        py_kind = culprit_kind(params)
        if asp_kind != py_kind:
            rc = 1
            print(f"MISMATCH for {params.culprit}: clingo={asp_kind} python={py_kind}")
            break
    else:
        print("OK: culprit kind matches on curated scenarios.")

    try:
        sample = generate(CURATED[0])
        if not sample.story or "scrumptious" not in sample.story.lower():
            raise StoryError("Generated story is empty or missing required seed word.")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show chosen_kind/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (place, treat, culprit, hideout) combos:\n")
        for place, treat, culprit, hideout in combos:
            print(f"  {place:8} {treat:11} {culprit:7} {hideout}")
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
            header = f"### {p.detective} and {p.partner}: {p.treat} at {p.place} ({p.culprit} in {p.hideout})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
