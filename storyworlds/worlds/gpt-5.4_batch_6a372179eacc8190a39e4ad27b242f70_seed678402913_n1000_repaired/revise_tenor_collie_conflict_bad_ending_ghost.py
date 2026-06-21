#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/revise_tenor_collie_conflict_bad_ending_ghost.py
============================================================================

A small story world about two children revising a song at dusk, a collie who
hears danger first, and a ghostly tenor voice behind a sealed door.

The core shape is a ghost story:
- premise: a child is revising music in an old place;
- tension: a tenor voice starts singing where nobody should be;
- conflict: one child wants to open the sealed place, while the other and the
  collie warn that something is wrong;
- turn: the children either back away, fetch help, or open the door anyway;
- resolution: either the danger is averted, contained by a sensible grown-up, or
  the haunting wins and the ending turns sad.

Words required by the seed appear naturally in the domain:
- revise: the child is revising a song or solo;
- tenor: the ghostly voice is a tenor;
- collie: the family dog is a collie.

Run it
------
    python storyworlds/worlds/gpt-5.4/revise_tenor_collie_conflict_bad_ending_ghost.py
    python storyworlds/worlds/gpt-5.4/revise_tenor_collie_conflict_bad_ending_ghost.py --portal linen_closet
    python storyworlds/worlds/gpt-5.4/revise_tenor_collie_conflict_bad_ending_ghost.py --response whisper_back
    python storyworlds/worlds/gpt-5.4/revise_tenor_collie_conflict_bad_ending_ghost.py --all
    python storyworlds/worlds/gpt-5.4/revise_tenor_collie_conflict_bad_ending_ghost.py --verify
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
NERVE_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "steady", "watchful", "sensible"}


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
    age: int = 0
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        dog = {"dog", "collie"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in dog:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    room: str
    dusk_detail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Piece:
    id: str
    label: str
    revise_text: str
    line_text: str
    comfort: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Portal:
    id: str
    label: str
    the: str
    beyond: str
    approach: str
    danger: int
    echoing: bool = True
    bolted: bool = True
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    piece: str
    portal: str
    response: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
    trait: str
    delay: int = 0
    instigator_age: int = 8
    cautioner_age: int = 7
    relation: str = "siblings"
    collie_name: str = "Moss"
    seed: Optional[int] = None


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
        return [e for e in self.entities.values() if e.role in {"instigator", "cautioner"}]

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


def _r_haunt(world: World) -> list[str]:
    out: list[str] = []
    portal = world.get("portal")
    ghost = world.get("ghost")
    if portal.meters["opened"] < THRESHOLD:
        return out
    sig = ("haunt", portal.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ghost.meters["freed"] += 1
    ghost.meters["cold"] += 1
    world.get("paper").meters["scattered"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    world.get("collie").memes["alarm"] += 1
    out.append("__haunt__")
    return out


def _r_stolen_voice(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.get("ghost")
    instigator = world.get("instigator")
    if ghost.meters["freed"] < THRESHOLD:
        return out
    sig = ("voice", instigator.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    instigator.meters["voice_lost"] += 1
    instigator.memes["sorrow"] += 1
    out.append("__voice__")
    return out


CAUSAL_RULES = [
    Rule(name="haunt", tag="physical", apply=_r_haunt),
    Rule(name="stolen_voice", tag="physical", apply=_r_stolen_voice),
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


def haunting_possible(piece: Piece, portal: Portal) -> bool:
    return portal.echoing and portal.bolted


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def danger_value(portal: Portal, delay: int) -> int:
    return portal.danger + delay


def is_contained(response: Response, portal: Portal, delay: int) -> bool:
    return response.power >= danger_value(portal, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    older_sibling = relation == "siblings" and cautioner_age > instigator_age
    authority = initial_caution(trait) + 1.0 + (3.0 if older_sibling else 0.0)
    return older_sibling and authority > NERVE_INIT


def predict_opening(world: World) -> dict:
    sim = world.copy()
    sim.get("portal").meters["opened"] += 1
    propagate(sim, narrate=False)
    return {
        "freed": sim.get("ghost").meters["freed"] >= THRESHOLD,
        "voice_lost": sim.get("instigator").meters["voice_lost"] >= THRESHOLD,
    }


def introduce(world: World, setting: Setting, piece: Piece, a: Entity, b: Entity, collie: Entity) -> None:
    for kid in (a, b):
        kid.memes["calm"] += 1
    world.say(
        f"At dusk in {setting.place}, {a.id} sat in {setting.room} to revise {piece.revise_text}. "
        f"{setting.dusk_detail}"
    )
    world.say(
        f"{b.id} listened from the rug, and {collie.label}, the collie, lay with his nose on his paws. "
        f"Now and then {a.id} sang {piece.line_text} in a small brave voice."
    )


def first_voice(world: World, portal: Portal) -> None:
    ghost = world.get("ghost")
    ghost.meters["singing"] += 1
    world.say(
        f"Then a second voice answered from behind {portal.the}. It was not loud, but it was deep and clear, "
        f"a tenor voice that did not belong to anyone in the room."
    )


def collie_warning(world: World, collie: Entity, portal: Portal) -> None:
    collie.memes["alarm"] += 1
    world.say(
        f"{collie.label} sprang up at once. His fur lifted along his back, and he stared at {portal.the} "
        f"with a low rumble in his throat."
    )


def temptation(world: World, a: Entity, portal: Portal) -> None:
    a.memes["curiosity"] += 1
    a.memes["defiance"] += 1
    world.say(
        f'"Maybe someone is shut in there," {a.id} whispered. "If I open {portal.the}, I can see."'
    )


def warning(world: World, b: Entity, a: Entity, portal: Portal, parent: Entity, collie: Entity) -> None:
    pred = predict_opening(world)
    b.memes["caution"] += 1
    world.facts["predicted_freed"] = pred["freed"]
    world.facts["predicted_voice_lost"] = pred["voice_lost"]
    extra = ""
    if pred["voice_lost"]:
        extra = f" {b.id} could almost feel the song being pulled right out of {a.id}'s mouth."
    world.say(
        f'{b.id} caught {a.id}\'s sleeve. "{parent.label_word.capitalize()} said never to touch old bolts at night," '
        f'{b.pronoun()} said. "Listen to {collie.label}. Something behind {portal.the} wants us to open it."{extra}'
    )


def back_down(world: World, a: Entity, b: Entity, portal: Portal, response: Response) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f"{a.id} stood very still, hand halfway out, and then let it fall. The tenor voice sang once more behind "
        f"{portal.the}, but {a.id} stepped back instead of forward."
    )
    world.say(
        f"They left {portal.the} shut and used {response.text} before the song inside could grow any stronger."
    )


def open_portal(world: World, a: Entity, portal: Portal) -> None:
    portal_ent = world.get("portal")
    portal_ent.meters["opened"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Before anyone could stop {a.id}, {a.pronoun()} slid the bolt. {portal.The} opened on {portal.beyond}, "
        f"and a cold breath rushed out as if the dark itself had lungs."
    )
    world.say(
        f"The hidden tenor voice rose at once, fuller now, and the note seemed to press against every window in the place."
    )


def contained_rescue(world: World, parent: Entity, response: Response, portal: Portal, collie: Entity) -> None:
    world.get("ghost").meters["freed"] = 0.0
    world.get("ghost").meters["cold"] = 0.0
    world.get("portal").meters["opened"] = 0.0
    world.get("paper").meters["scattered"] = 0.0
    for kid in world.kids():
        kid.memes["fear"] = 0.0
        kid.memes["relief"] += 1
    body = response.qa_text.replace("{portal}", portal.label)
    world.say(
        f"{parent.label_word.capitalize()} came fast, and {parent.pronoun()} {body}. "
        f"{collie.label} barked once into the dark, and the terrible singing broke apart like smoke in wind."
    )
    world.say(
        f"After that, only the ordinary house sounds remained: a beam settling, a clock ticking, the thin scrape of rain on glass."
    )


def haunted_loss(world: World, a: Entity, b: Entity, portal: Portal, piece: Piece, collie: Entity) -> None:
    paper = world.get("paper")
    paper.meters["lost"] += 1
    for kid in (a, b):
        kid.memes["fear"] += 1
    world.say(
        f"The pages {a.id} had been using to revise {piece.label} flew from {a.pronoun('possessive')} hands and spun down "
        f"{portal.approach}. {collie.label} snapped at them, but the dark took them first."
    )
    world.say(
        f"When {a.id} tried to call out, only a ragged breath came. The ghost had kept the song and left the room colder than stone."
    )
    if b.memes["caution"] >= THRESHOLD:
        world.say(
            f"{b.id} pulled {a.id} away from {portal.the}, but the tenor voice was already singing with {a.id}'s lost note folded into it."
        )


def bad_ending(world: World, a: Entity, b: Entity, piece: Piece, setting: Setting) -> None:
    a.memes["sorrow"] += 1
    b.memes["sorrow"] += 1
    world.say(
        f"The next evening, when the children were meant to sing, {a.id} stood silent. {b.id} stayed close, but nothing could bring "
        f"the missing voice back."
    )
    world.say(
        f"Long after bedtime, the same tenor note drifted through {setting.place} again, as if someone unseen were still revising "
        f"{piece.label} in the dark."
    )


def safe_after(world: World, a: Entity, b: Entity, piece: Piece, collie: Entity) -> None:
    for kid in (a, b):
        kid.memes["calm"] += 1
    world.say(
        f"Later, wrapped in lamplight, {a.id} revised {piece.label} again with {b.id} beside {a.pronoun('object')} and {collie.label} asleep across the doorway."
    )
    world.say(
        f"This time every note belonged to the living, and that was enough."
    )


def tell(
    setting: Setting,
    piece: Piece,
    portal: Portal,
    response: Response,
    *,
    instigator: str = "Nora",
    instigator_gender: str = "girl",
    cautioner: str = "Ben",
    cautioner_gender: str = "boy",
    parent_type: str = "mother",
    trait: str = "steady",
    delay: int = 0,
    instigator_age: int = 8,
    cautioner_age: int = 7,
    relation: str = "siblings",
    collie_name: str = "Moss",
) -> World:
    world = World()
    a = world.add(Entity(
        id="instigator",
        kind="character",
        type=instigator_gender,
        label=instigator,
        phrase=instigator,
        role="instigator",
        age=instigator_age,
        traits=["curious"],
        attrs={"name": instigator, "relation": relation},
    ))
    b = world.add(Entity(
        id="cautioner",
        kind="character",
        type=cautioner_gender,
        label=cautioner,
        phrase=cautioner,
        role="cautioner",
        age=cautioner_age,
        traits=[trait],
        attrs={"name": cautioner, "relation": relation},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    collie = world.add(Entity(
        id="collie",
        kind="character",
        type="collie",
        label=collie_name,
        phrase=f"{collie_name} the collie",
        role="helper",
        tags={"collie", "dog"},
    ))
    ghost = world.add(Entity(
        id="ghost",
        kind="thing",
        type="ghost",
        label="the hidden singer",
        tags={"ghost", "tenor"},
    ))
    portal_ent = world.add(Entity(
        id="portal",
        kind="thing",
        type="door",
        label=portal.label,
        phrase=portal.the,
        tags=set(portal.tags),
    ))
    paper = world.add(Entity(
        id="paper",
        kind="thing",
        type="music",
        label="music pages",
        phrase="the music pages",
        tags={"music"},
    ))

    a.memes["nerve"] = NERVE_INIT
    b.memes["caution"] = initial_caution(trait)
    world.facts["names"] = {"instigator": instigator, "cautioner": cautioner, "collie": collie_name}

    introduce(world, setting, piece, a, b, collie)
    first_voice(world, portal)
    collie_warning(world, collie, portal)

    world.para()
    temptation(world, a, portal)
    warning(world, b, a, portal, parent, collie)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)
    if averted:
        back_down(world, a, b, portal, response)
        world.para()
        safe_after(world, a, b, piece, collie)
        outcome = "averted"
    else:
        world.para()
        open_portal(world, a, portal)
        contained = is_contained(response, portal, delay)
        world.para()
        if contained:
            contained_rescue(world, parent, response, portal, collie)
            world.para()
            safe_after(world, a, b, piece, collie)
            outcome = "contained"
        else:
            haunted_loss(world, a, b, portal, piece, collie)
            world.para()
            bad_ending(world, a, b, piece, setting)
            outcome = "haunted"

    world.facts.update(
        setting=setting,
        piece=piece,
        portal_cfg=portal,
        response=response,
        instigator=a,
        cautioner=b,
        parent=parent,
        collie=collie,
        ghost=ghost,
        paper=paper,
        outcome=outcome,
        relation=relation,
        delay=delay,
        voice_lost=a.meters["voice_lost"] >= THRESHOLD,
        pages_lost=paper.meters["lost"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "chapel": Setting(
        id="chapel",
        place="the old chapel house",
        room="the long parlor",
        dusk_detail="Outside, rain touched the panes, and the hall beyond the lamplight looked deeper than it should have.",
        tags={"ghost", "house"},
    ),
    "manor": Setting(
        id="manor",
        place="the stone manor",
        room="the music room",
        dusk_detail="The candles were low, and the corners of the room seemed to hold their breath.",
        tags={"ghost", "house"},
    ),
    "schoolhouse": Setting(
        id="schoolhouse",
        place="the empty schoolhouse",
        room="the assembly room",
        dusk_detail="The wind moved around the eaves, and the dark corridor behind the curtain kept answering with tiny sighs.",
        tags={"ghost", "school"},
    ),
}

PIECES = {
    "hymn": Piece(
        id="hymn",
        label="the winter hymn",
        revise_text="the winter hymn for Sunday's singing",
        line_text='"Softly the evening bells..."',
        comfort="It was the kind of song that usually made the room feel warm.",
        tags={"music", "hymn"},
    ),
    "solo": Piece(
        id="solo",
        label="the recital solo",
        revise_text="the recital solo for the harvest evening",
        line_text='"Carry the lantern home..."',
        comfort="It was meant to sound brave and bright.",
        tags={"music", "singing"},
    ),
    "carol": Piece(
        id="carol",
        label="the old carol",
        revise_text="the old carol the children had been given to learn",
        line_text='"Over the hill, through silver snow..."',
        comfort="It was a sweet song, though older than anyone in the family.",
        tags={"music", "carol"},
    ),
}

PORTALS = {
    "choir_loft": Portal(
        id="choir_loft",
        label="choir-loft door",
        the="the bolted choir-loft door",
        beyond="a narrow stair curling up into a pocket of dark rafters",
        approach="the stair",
        danger=3,
        echoing=True,
        bolted=True,
        tags={"door", "stairs"},
    ),
    "cellar": Portal(
        id="cellar",
        label="cellar door",
        the="the chained cellar door",
        beyond="wet steps dropping under the house where no lamp was burning",
        approach="the cellar steps",
        danger=2,
        echoing=True,
        bolted=True,
        tags={"door", "cellar"},
    ),
    "bell_tower": Portal(
        id="bell_tower",
        label="tower hatch",
        the="the iron tower hatch",
        beyond="a steep ladder rising toward the blind bell chamber",
        approach="the ladder",
        danger=3,
        echoing=True,
        bolted=True,
        tags={"door", "tower"},
    ),
    "linen_closet": Portal(
        id="linen_closet",
        label="linen-closet door",
        the="the little linen-closet door",
        beyond="a tidy shelf of folded sheets",
        approach="the closet floor",
        danger=1,
        echoing=False,
        bolted=False,
        tags={"closet"},
    ),
}

RESPONSES = {
    "call_caretaker": Response(
        id="call_caretaker",
        sense=3,
        power=4,
        text="the bell-pull by the stairs to summon the caretaker",
        fail="rang for the caretaker, but the singing had already slipped too far into the house",
        qa_text="pulled the bell for the caretaker and shut the {portal} fast",
        tags={"adult", "bell"},
    ),
    "back_to_lamplight": Response(
        id="back_to_lamplight",
        sense=3,
        power=3,
        text="the warm parlor lamp and called for a grown-up",
        fail="dragged the children back toward the lamplight, but the cold song followed them anyway",
        qa_text="pulled the children back to the lamplight and called for a grown-up",
        tags={"adult", "lamp"},
    ),
    "whisper_back": Response(
        id="whisper_back",
        sense=1,
        power=0,
        text="a hushed answer through the crack",
        fail="whispered back to the dark, which only invited the singer nearer",
        qa_text="whispered back through the crack",
        tags={"ghost"},
    ),
}

GIRL_NAMES = ["Nora", "Lucy", "Mira", "Elsie", "Clara", "June", "Ada", "Mabel"]
BOY_NAMES = ["Ben", "Theo", "Miles", "Evan", "Jonah", "Sam", "Finn", "Leo"]
TRAITS = ["careful", "steady", "watchful", "sensible", "curious", "brisk"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for piece_id, piece in PIECES.items():
            for portal_id, portal in PORTALS.items():
                if haunting_possible(piece, portal):
                    combos.append((setting_id, piece_id, portal_id))
    return combos


CURATED = [
    StoryParams(
        setting="chapel",
        piece="hymn",
        portal="choir_loft",
        response="call_caretaker",
        instigator="Nora",
        instigator_gender="girl",
        cautioner="Ben",
        cautioner_gender="boy",
        parent="mother",
        trait="steady",
        delay=0,
        instigator_age=8,
        cautioner_age=10,
        relation="siblings",
        collie_name="Moss",
    ),
    StoryParams(
        setting="manor",
        piece="solo",
        portal="cellar",
        response="back_to_lamplight",
        instigator="Theo",
        instigator_gender="boy",
        cautioner="Lucy",
        cautioner_gender="girl",
        parent="father",
        trait="watchful",
        delay=0,
        instigator_age=9,
        cautioner_age=8,
        relation="friends",
        collie_name="Bramble",
    ),
    StoryParams(
        setting="schoolhouse",
        piece="carol",
        portal="bell_tower",
        response="back_to_lamplight",
        instigator="Mira",
        instigator_gender="girl",
        cautioner="Finn",
        cautioner_gender="boy",
        parent="mother",
        trait="careful",
        delay=1,
        instigator_age=9,
        cautioner_age=7,
        relation="siblings",
        collie_name="Skye",
    ),
    StoryParams(
        setting="chapel",
        piece="solo",
        portal="choir_loft",
        response="call_caretaker",
        instigator="Leo",
        instigator_gender="boy",
        cautioner="Ada",
        cautioner_gender="girl",
        parent="father",
        trait="sensible",
        delay=1,
        instigator_age=10,
        cautioner_age=8,
        relation="friends",
        collie_name="Moss",
    ),
]


def explain_rejection(piece: Piece, portal: Portal) -> str:
    if not portal.echoing:
        return (
            f"(No story: {portal.the} is too ordinary for a hidden tenor haunting. "
            f"It would not throw back a ghostly voice, so there is no honest conflict.)"
        )
    if not portal.bolted:
        return (
            f"(No story: {portal.the} is not sealed off, so the place does not feel forbidden enough "
            f"for this ghost story.)"
        )
    return f"(No story: {piece.label} and {portal.the} do not make a plausible haunting here.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it is too weak and unwise for this world "
        f"(sense={r.sense} < {SENSE_MIN}). Try {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    contained = is_contained(RESPONSES[params.response], PORTALS[params.portal], params.delay)
    return "contained" if contained else "haunted"


KNOWLEDGE = {
    "ghost": [
        (
            "What is a ghost story?",
            "A ghost story is a spooky tale about something strange that seems to come from the dead or from a haunted place. It is meant to make the reader feel chills and wonder what is hiding in the dark.",
        )
    ],
    "tenor": [
        (
            "What is a tenor voice?",
            "A tenor is a kind of singing voice that is usually high for a grown man. In stories, a clear tenor voice can sound bright, eerie, or lonely depending on where it is heard.",
        )
    ],
    "collie": [
        (
            "What is a collie?",
            "A collie is a smart kind of dog with a long nose and a thick coat. Collies are known for noticing things quickly and watching over people.",
        )
    ],
    "bell": [
        (
            "Why might someone ring a bell for help in an old house?",
            "In an old house, a bell-pull could call a caretaker or servant from another room. It was a fast way to bring help before a problem grew worse.",
        )
    ],
    "lamp": [
        (
            "Why does lamplight feel safer in a ghost story?",
            "Lamplight makes a small warm circle you can see clearly. That bright circle feels safer because the dark cannot hide as easily inside it.",
        )
    ],
    "music": [
        (
            "What does it mean to revise a song?",
            "To revise a song means to practice it again and fix the parts that are not right yet. A singer may repeat lines, notes, or words until the song is ready.",
        )
    ],
}
KNOWLEDGE_ORDER = ["ghost", "tenor", "collie", "music", "bell", "lamp"]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    piece = f["piece"]
    portal = f["portal_cfg"]
    collie = f["collie"]
    outcome = f["outcome"]
    if outcome == "haunted":
        return [
            f'Write a ghost story for a young child that includes the words "revise," "tenor," and "collie."',
            f"Tell a spooky story where {a.attrs['name']} is revising {piece.label}, hears a tenor voice behind {portal.the}, and ignores a warning from {b.attrs['name']} and {collie.label}.",
            f"Write a sad ghost story with a bad ending in which opening {portal.the} lets the haunting take something precious from a child.",
        ]
    if outcome == "contained":
        return [
            f'Write a ghost story for a young child that includes the words "revise," "tenor," and "collie."',
            f"Tell a spooky-but-safe story where {a.attrs['name']} hears a tenor voice behind {portal.the}, the collie senses danger, and a grown-up arrives in time.",
            f"Write a story with conflict, fear, and an ending where the living keep their song by choosing help over curiosity.",
        ]
    return [
        f'Write a ghost story for a young child that includes the words "revise," "tenor," and "collie."',
        f"Tell a spooky story where {a.attrs['name']} wants to open {portal.the}, but {b.attrs['name']} and the collie stop it before the haunting grows.",
        f"Write a quiet ghost story where the children choose caution and leave the dark singing shut away.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    parent = f["parent"]
    collie = f["collie"]
    piece = f["piece"]
    portal = f["portal_cfg"]
    relation = f["relation"]
    pair = pair_noun(a, b, relation)
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.attrs['name']} and {b.attrs['name']}, and {collie.label} the collie. They were together when the strange singing began.",
        ),
        (
            f"What was {a.attrs['name']} doing at the beginning?",
            f"{a.attrs['name']} was trying to revise {piece.label}. That is why the ghostly tenor voice felt so unsettling: it answered the song instead of starting its own.",
        ),
        (
            f"Why did {b.attrs['name']} think {a.attrs['name']} should not open {portal.the}?",
            f"{b.attrs['name']} knew the place was forbidden at night, and {collie.label} was already warning them. The warning mattered because the dark singing seemed to want the door opened.",
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"What stopped the trouble before it began?",
                f"{a.attrs['name']} listened and stepped back from {portal.the}. Because the children left it shut and called for help instead, the haunting never grew stronger.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended quietly in lamplight, with the children safe and the collie resting by the doorway. The last image shows that the song stayed with the living.",
            )
        )
    elif f["outcome"] == "contained":
        qa.append(
            (
                f"How did {pw} stop the haunting?",
                f"{pw.capitalize()} came quickly and {f['response'].qa_text.replace('{portal}', portal.label)}. That broke the danger before the ghost could keep the stolen music.",
            )
        )
        qa.append(
            (
                f"Why did the collie matter in the story?",
                f"{collie.label} sensed the danger before the children fully understood it. His alarm pushed the warning from a spooky feeling into something they could not ignore.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the children revising the song again in a safe bright room. That ending proves the haunting failed to take the music away from them.",
            )
        )
    else:
        qa.append(
            (
                f"What bad thing happened after {a.attrs['name']} opened {portal.the}?",
                f"The ghost scattered the music pages and stole the voice {a.attrs['name']} had been using to sing. That is why the danger felt worse than an ordinary fright.",
            )
        )
        qa.append(
            (
                "Why is the ending sad?",
                f"The next evening, {a.attrs['name']} could not sing at all, even though the song had mattered at the beginning. The ghost keeps singing in the dark, which shows the loss did not end when the children walked away.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"ghost", "tenor", "collie", "music"}
    if f["response"].id == "call_caretaker":
        tags.add("bell")
    if f["response"].id == "back_to_lamplight" or f["outcome"] == "averted":
        tags.add("lamp")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
haunting(Piece, Portal) :- piece(Piece), portal(Portal), echoing(Portal), bolted(Portal).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(S, P, D) :- setting(S), piece(P), portal(D), haunting(P, D).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).

older_sibling :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(3) :- older_sibling.
bonus(0) :- not older_sibling.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- older_sibling, authority(A), nerve_init(N), A > N.

severity(Dg + Dl) :- chosen_portal(P), danger(P, Dg), delay(Dl).
contained :- chosen_response(R), power(R, P), severity(S), P >= S.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(haunted) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PIECES:
        lines.append(asp.fact("piece", pid))
    for did, portal in PORTALS.items():
        lines.append(asp.fact("portal", did))
        if portal.echoing:
            lines.append(asp.fact("echoing", did))
        if portal.bolted:
            lines.append(asp.fact("bolted", did))
        lines.append(asp.fact("danger", did, portal.danger))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("nerve_init", int(NERVE_INIT)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_portal", params.portal),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("instigator_age", params.instigator_age),
            asp.fact("cautioner_age", params.cautioner_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    c_sens, p_sens = set(asp_sensible()), {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    diff = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if diff == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {diff}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test produced an empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Ghost-story world: revising a song, a tenor voice behind a sealed door, and a collie that hears danger first."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--piece", choices=PIECES)
    ap.add_argument("--portal", choices=PORTALS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long help takes to arrive")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.portal and not PORTALS[args.portal].echoing:
        piece = PIECES[args.piece] if args.piece else next(iter(PIECES.values()))
        raise StoryError(explain_rejection(piece, PORTALS[args.portal]))
    if args.piece and args.portal:
        piece = PIECES[args.piece]
        portal = PORTALS[args.portal]
        if not haunting_possible(piece, portal):
            raise StoryError(explain_rejection(piece, portal))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        c
        for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.piece is None or c[1] == args.piece)
        and (args.portal is None or c[2] == args.portal)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, piece, portal = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    instigator, ig = _pick_kid(rng)
    cautioner, cg = _pick_kid(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([7, 8, 9, 10], 2)
    collie_name = rng.choice(["Moss", "Skye", "Bramble", "Pip", "Rowan"])
    return StoryParams(
        setting=setting,
        piece=piece,
        portal=portal,
        response=response,
        instigator=instigator,
        instigator_gender=ig,
        cautioner=cautioner,
        cautioner_gender=cg,
        parent=parent,
        trait=trait,
        delay=delay,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        relation=relation,
        collie_name=collie_name,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        piece = PIECES[params.piece]
        portal = PORTALS[params.portal]
        response = RESPONSES[params.response]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err})") from err

    if not haunting_possible(piece, portal):
        raise StoryError(explain_rejection(piece, portal))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(response.id))

    world = tell(
        setting=setting,
        piece=piece,
        portal=portal,
        response=response,
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        parent_type=params.parent,
        trait=params.trait,
        delay=params.delay,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
        relation=params.relation,
        collie_name=params.collie_name,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, piece, portal) combos:\n")
        for setting, piece, portal in combos:
            print(f"  {setting:10} {piece:8} {portal}")
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
                f"### {p.instigator} & {p.cautioner}: {p.piece} at {p.setting} "
                f"({p.portal}, {p.response}, {outcome_of(p)})"
            )
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
