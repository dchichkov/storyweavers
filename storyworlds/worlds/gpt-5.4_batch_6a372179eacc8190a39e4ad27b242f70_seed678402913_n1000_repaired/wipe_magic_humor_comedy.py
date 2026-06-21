#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/wipe_magic_humor_comedy.py
====================================================

A standalone story world about a child, a silly magic spell, and the one good
way to wipe a comic mess away.

This world rebuilds a tiny comedy domain rather than a single fixed paragraph:
a child tries a joke spell on a washable surface, a friend or sibling predicts
the mess, the spell either gets stopped or bursts into the room, and a grown-up
helps everyone wipe it away with the right cleaner.

Run it
------
    python storyworlds/worlds/gpt-5.4/wipe_magic_humor_comedy.py
    python storyworlds/worlds/gpt-5.4/wipe_magic_humor_comedy.py --room kitchen --spell pudding_pop
    python storyworlds/worlds/gpt-5.4/wipe_magic_humor_comedy.py --surface rug
    python storyworlds/worlds/gpt-5.4/wipe_magic_humor_comedy.py --cleaner sleeve
    python storyworlds/worlds/gpt-5.4/wipe_magic_humor_comedy.py --all
    python storyworlds/worlds/gpt-5.4/wipe_magic_humor_comedy.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/wipe_magic_humor_comedy.py --verify
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
MISCHIEF_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "cautious", "sensible", "thoughtful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    wipeable: bool = False
    smooth: bool = False
    on_floor: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
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
class RoomCfg:
    id: str
    label: str
    scene: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class SpellCfg:
    id: str
    title: str
    mess_kind: str
    effect: str
    burst: str
    residue: str
    lesson: str
    severity: int
    surfaces: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class SurfaceCfg:
    id: str
    label: str
    the: str
    phrase: str
    room_text: str
    smooth: bool = False
    on_floor: bool = False
    wipeable: bool = True
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]


@dataclass
class CleanerCfg:
    id: str
    label: str
    phrase: str
    guards: set[str] = field(default_factory=set)
    surfaces: set[str] = field(default_factory=set)
    sense: int = 0
    power: int = 0
    success_text: str = ""
    fail_text: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, room: RoomCfg) -> None:
        self.room = room
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
        return [e for e in self.entities.values() if e.role in {"instigator", "helper"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.room)
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


def _r_magic_spread(world: World) -> list[str]:
    out: list[str] = []
    surface = world.entities.get("surface")
    if surface is None or surface.meters["messy"] < THRESHOLD:
        return out
    sig = ("spread", surface.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("room").meters["disorder"] += 1
    for kid in world.kids():
        kid.memes["surprise"] += 1
    if surface.on_floor:
        world.get("room").meters["slip_risk"] += 1
    out.append("__spread__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="magic_spread", tag="physical", apply=_r_magic_spread),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(s for s in lines if not s.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def spell_fits_surface(spell: SpellCfg, surface: SurfaceCfg) -> bool:
    return surface.id in spell.surfaces and surface.wipeable


def cleaner_fits(cleaner: CleanerCfg, spell: SpellCfg, surface: SurfaceCfg) -> bool:
    return (
        spell.mess_kind in cleaner.guards
        and surface.id in cleaner.surfaces
        and surface.wipeable
    )


def sensible_cleaners() -> list[CleanerCfg]:
    return [cfg for cfg in CLEANERS.values() if cfg.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_cleaners():
        return combos
    for room_id, room in ROOMS.items():
        for surface_id in sorted(room.affords):
            surface = SURFACES[surface_id]
            for spell_id, spell in SPELLS.items():
                if not spell_fits_surface(spell, surface):
                    continue
                if any(cleaner_fits(c, spell, surface) for c in sensible_cleaners()):
                    combos.append((room_id, spell_id, surface_id))
    return combos


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, helper_age: int, trait: str) -> bool:
    helper_older = relation == "siblings" and helper_age > instigator_age
    authority = initial_caution(trait) + 1.0 + (4.0 if helper_older else 0.0)
    return helper_older and authority > MISCHIEF_INIT


def mess_severity(spell: SpellCfg, delay: int, surface: SurfaceCfg) -> int:
    return spell.severity + delay + (1 if surface.on_floor else 0)


def is_contained(cleaner: CleanerCfg, spell: SpellCfg, delay: int, surface: SurfaceCfg) -> bool:
    return cleaner.power >= mess_severity(spell, delay, surface)


def predict_mess(world: World, spell_id: str, surface_id: str) -> dict:
    sim = world.copy()
    _cast_spell(sim, spell_id=spell_id, surface_id=surface_id, narrate=False)
    return {
        "messy": sim.get("surface").meters["messy"] >= THRESHOLD,
        "slip_risk": sim.get("room").meters["slip_risk"],
        "disorder": sim.get("room").meters["disorder"],
    }


def introduce(world: World, instigator: Entity, helper: Entity, room_cfg: RoomCfg) -> None:
    for kid in (instigator, helper):
        kid.memes["joy"] += 1
    world.say(
        f"One bright afternoon, {instigator.id} and {helper.id} were in {room_cfg.label}. "
        f"{room_cfg.scene}"
    )
    world.say(
        f"They had turned an ordinary cleanup rag into a pretend magician's cape, "
        f"which was already a silly idea and therefore very interesting."
    )


def set_surface(world: World, surface: SurfaceCfg) -> None:
    world.say(
        f"Right in the middle stood {surface.phrase}, {surface.room_text}."
    )


def tempt(world: World, instigator: Entity, spell: SpellCfg, surface: SurfaceCfg) -> None:
    instigator.memes["mischief"] += 1
    world.say(
        f'"Want to see my newest trick?" {instigator.id} whispered. '
        f'"I call it {spell.title}."'
    )
    world.say(
        f"{instigator.id} pointed the toy wand at {surface.the} and grinned as if a laugh "
        f"were already waiting to jump out."
    )


def warn(world: World, helper: Entity, instigator: Entity, spell: SpellCfg,
         surface: SurfaceCfg, adult: Entity) -> None:
    pred = predict_mess(world, spell.id, surface.id)
    helper.memes["caution"] += 1
    world.facts["predicted_disorder"] = pred["disorder"]
    world.facts["predicted_slip_risk"] = pred["slip_risk"]
    extra = ""
    if pred["slip_risk"] >= THRESHOLD:
        extra = " It could make the floor slippery too."
    world.say(
        f'{helper.id} pulled a face. "{instigator.id}, {adult.label_word} said joke spells are '
        f'only funny if someone can wipe them away. {surface.The} would end up {spell.residue}.{extra}"'
    )


def back_down(world: World, instigator: Entity, helper: Entity, spell: SpellCfg,
              adult: Entity, surface: SurfaceCfg) -> None:
    instigator.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f'{instigator.id} opened {instigator.pronoun("possessive")} mouth for one brave little '
        f'"Poof!" and then stopped. {helper.id} was {instigator.pronoun("possessive")} older '
        f"sibling, and suddenly the trick did not seem half as clever."
    )
    world.say(
        f"Instead of casting {spell.title}, they asked {adult.label_word} for a plain drawing cloth "
        f"and made a silly face on {surface.the} with washable soap foam."
    )


def defy(world: World, instigator: Entity, helper: Entity, spell: SpellCfg) -> None:
    instigator.memes["defiance"] += 1
    world.say(
        f'"Just one tiny spell," {instigator.id} said. That was how comic trouble always introduced itself.'
    )
    if helper.attrs.get("relation") == "siblings" and instigator.age > helper.age:
        world.say(
            f"{helper.id} still looked doubtful, but {instigator.id} was the older one, so "
            f"{helper.id} only scooted back and hoped for the best."
        )


def _cast_spell(world: World, spell_id: str, surface_id: str, narrate: bool = True) -> None:
    surface = world.get(surface_id)
    surface.meters["messy"] += 1
    surface.meters[world.facts.get("mess_kind", "mess")] += 1
    propagate(world, narrate=narrate)


def cast(world: World, instigator: Entity, spell: SpellCfg, surface: SurfaceCfg) -> None:
    world.facts["mess_kind"] = spell.mess_kind
    _cast_spell(world, spell_id="surface", surface_id="surface", narrate=False)
    instigator.memes["delight"] += 1
    world.say(
        f"{spell.burst} In a blink, {surface.the} was covered in {spell.effect}."
    )
    if surface.on_floor:
        world.say("The mess skated across the floor in little magic loops, which was funny for exactly one second.")
    else:
        world.say("For one second it looked magnificent. For the next second it looked like a joke that had forgotten when to stop.")


def alarm(world: World, helper: Entity, surface: SurfaceCfg, adult: Entity) -> None:
    if surface.on_floor:
        world.say(f'"It is sliding everywhere!" {helper.id} yelped. "{adult.label_word.capitalize()}!"')
    else:
        world.say(f'"It is spreading!" {helper.id} cried. "{adult.label_word.capitalize()}!"')


def rescue(world: World, adult: Entity, cleaner: CleanerCfg, surface: Entity,
           surface_cfg: SurfaceCfg, spell: SpellCfg) -> None:
    surface.meters["messy"] = 0.0
    world.get("room").meters["disorder"] = 0.0
    world.get("room").meters["slip_risk"] = 0.0
    world.say(
        f"{adult.label_word.capitalize()} came in at a brisk walk, took one look, and did not even gasp. "
        f"{adult.pronoun().capitalize()} grabbed {cleaner.phrase} and {cleaner.success_text.replace('{surface}', surface_cfg.label)}."
    )
    world.say(
        f"With one long wipe, the spell broke apart into ordinary sparkles and a ridiculous smell of lemons."
    )
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1


def rescue_fail(world: World, adult: Entity, cleaner: CleanerCfg,
                surface_cfg: SurfaceCfg, spell: SpellCfg) -> None:
    world.get("room").meters["disorder"] += 1
    if surface_cfg.on_floor:
        world.get("room").meters["slip_risk"] += 1
    world.say(
        f"{adult.label_word.capitalize()} hurried in and {cleaner.fail_text.replace('{surface}', surface_cfg.label)}."
    )
    world.say(
        f"But the magic only wriggled faster. Soon there were {spell.effect} on the chair legs, on the door, and somehow on one lonely banana."
    )
    for kid in world.kids():
        kid.memes["worry"] += 1


def lesson(world: World, adult: Entity, instigator: Entity, helper: Entity,
           spell: SpellCfg, cleaner: CleanerCfg) -> None:
    instigator.memes["love"] += 1
    helper.memes["love"] += 1
    world.say(
        f'{adult.label_word.capitalize()} knelt down and tapped the cloth. "Magic jokes need a cleanup plan," '
        f'{adult.pronoun()} said. "If you cannot wipe the trick, do not flick the trick."'
    )
    world.say(
        f'{instigator.id} laughed in spite of {instigator.pronoun("possessive")} red cheeks. '
        f'"That rhymes," {instigator.pronoun()} said.'
    )
    world.say(
        f'"Good," said {adult.label_word}. "Maybe you will remember it next time."'
    )


def long_cleanup(world: World, adult: Entity, instigator: Entity, helper: Entity,
                 cleaner: CleanerCfg, spell: SpellCfg) -> None:
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
    world.say(
        f"So they fetched more proper cloths, a little bucket, and a lot more patience. "
        f"By supper time, the room was finally clean."
    )
    world.say(
        f'{adult.label_word.capitalize()} held up the soggy pile and said, "Next time we start with a real wipe, not a hopeful poke."'
    )
    world.say(
        f"{instigator.id} and {helper.id} nodded so hard they nearly bumped foreheads, and then they both laughed."
    )


def safe_finish(world: World, adult: Entity, instigator: Entity, helper: Entity,
                surface_cfg: SurfaceCfg) -> None:
    for kid in world.kids():
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    world.say(
        f"The next day, {adult.label_word} set out a bowl of plain soap foam and a big clean rag."
    )
    world.say(
        f"Together they drew enormous smiling eyebrows on {surface_cfg.the}, then wiped them away before the eyebrows could think any funny thoughts of their own."
    )
    world.say(
        f"{instigator.id} bowed, {helper.id} clapped, and the room looked neat enough to prove the lesson had really stuck."
    )


def tell(room_cfg: RoomCfg, spell: SpellCfg, surface_cfg: SurfaceCfg, cleaner_cfg: CleanerCfg,
         instigator_name: str = "Milo", instigator_gender: str = "boy",
         helper_name: str = "Lena", helper_gender: str = "girl",
         trait: str = "careful", adult_type: str = "mother",
         delay: int = 0, instigator_age: int = 6, helper_age: int = 4,
         relation: str = "siblings") -> World:
    world = World(room_cfg)
    instigator = world.add(Entity(
        id=instigator_name,
        kind="character",
        type=instigator_gender,
        role="instigator",
        age=instigator_age,
        traits=["bold"],
        attrs={"relation": relation},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        role="helper",
        age=helper_age,
        traits=[trait],
        attrs={"relation": relation},
    ))
    adult = world.add(Entity(
        id="Adult",
        kind="character",
        type=adult_type,
        role="adult",
        label="the grown-up",
    ))
    room = world.add(Entity(
        id="room",
        type="room",
        label=room_cfg.label,
        tags=set(room_cfg.tags),
    ))
    surface = world.add(Entity(
        id="surface",
        type="surface",
        label=surface_cfg.label,
        phrase=surface_cfg.phrase,
        tags=set(surface_cfg.tags),
        wipeable=surface_cfg.wipeable,
        smooth=surface_cfg.smooth,
        on_floor=surface_cfg.on_floor,
    ))
    cleaner = world.add(Entity(
        id="cleaner",
        type="cleaner",
        label=cleaner_cfg.label,
        phrase=cleaner_cfg.phrase,
        tags=set(cleaner_cfg.tags),
    ))

    instigator.memes["mischief"] = MISCHIEF_INIT
    helper.memes["caution"] = initial_caution(trait)

    introduce(world, instigator, helper, room_cfg)
    set_surface(world, surface_cfg)

    world.para()
    tempt(world, instigator, spell, surface_cfg)
    warn(world, helper, instigator, spell, surface_cfg, adult)

    averted = would_avert(relation, instigator_age, helper_age, trait)
    if averted:
        back_down(world, instigator, helper, spell, adult, surface_cfg)
        world.para()
        safe_finish(world, adult, instigator, helper, surface_cfg)
        severity = 0
        contained = True
    else:
        defy(world, instigator, helper, spell)
        world.para()
        cast(world, instigator, spell, surface_cfg)
        alarm(world, helper, surface_cfg, adult)
        severity = mess_severity(spell, delay, surface_cfg)
        surface.meters["severity"] = float(severity)
        contained = is_contained(cleaner_cfg, spell, delay, surface_cfg)
        world.para()
        if contained:
            rescue(world, adult, cleaner_cfg, surface, surface_cfg, spell)
            lesson(world, adult, instigator, helper, spell, cleaner_cfg)
            world.para()
            safe_finish(world, adult, instigator, helper, surface_cfg)
        else:
            rescue_fail(world, adult, cleaner_cfg, surface_cfg, spell)
            long_cleanup(world, adult, instigator, helper, cleaner_cfg, spell)

    outcome = "averted" if averted else ("contained" if contained else "soggy")
    world.facts.update(
        room_cfg=room_cfg,
        spell=spell,
        surface_cfg=surface_cfg,
        cleaner=cleaner_cfg,
        instigator=instigator,
        helper=helper,
        adult=adult,
        room=room,
        surface=surface,
        relation=relation,
        outcome=outcome,
        severity=severity,
        delay=delay,
        mess_happened=surface.meters["severity"] >= THRESHOLD or surface.meters["messy"] >= THRESHOLD or outcome in {"contained", "soggy"},
    )
    return world


ROOMS = {
    "bathroom": RoomCfg(
        id="bathroom",
        label="the bathroom",
        scene="The tiles shone, the towels hung straight, and the room looked much too tidy to know what was coming.",
        affords={"mirror", "floor"},
        tags={"bathroom"},
    ),
    "kitchen": RoomCfg(
        id="kitchen",
        label="the kitchen",
        scene="Sunlight sat on the table, and even the fruit bowl looked as if it were minding its own business.",
        affords={"table", "floor", "fridge"},
        tags={"kitchen"},
    ),
    "classroom": RoomCfg(
        id="classroom",
        label="the classroom art corner",
        scene="Paper scraps waited in a box, and a row of cups held brushes like sleepy flowers.",
        affords={"desk", "window"},
        tags={"classroom"},
    ),
}

SPELLS = {
    "mustache_mizzle": SpellCfg(
        id="mustache_mizzle",
        title="the Moustache Mizzle",
        mess_kind="ink",
        effect="twirly purple moustaches that wiggled at the ends",
        burst='Piff! Three purple curls popped out of the wand',
        residue="smudgy with purple ink moustaches",
        lesson="magic jokes need wiping plans",
        severity=1,
        surfaces={"mirror", "window", "fridge"},
        tags={"magic", "ink", "mustache"},
    ),
    "pudding_pop": SpellCfg(
        id="pudding_pop",
        title="the Pudding Pop Surprise",
        mess_kind="sticky",
        effect="plops of singing lemon pudding",
        burst='Plop-pop-poof! A wobbling blob jumped from the wand',
        residue="sticky with pudding",
        lesson="sticky spells spread",
        severity=2,
        surfaces={"table", "floor", "desk", "fridge"},
        tags={"magic", "sticky", "pudding"},
    ),
    "bubble_banjo": SpellCfg(
        id="bubble_banjo",
        title="the Bubble Banjo",
        mess_kind="bubbly",
        effect="bouncing bubbles that squeaked tiny notes",
        burst='Boing-boing! A row of bubbles bounced out in tune',
        residue="foamy with bouncing bubbles",
        lesson="bubbles still need wiping",
        severity=1,
        surfaces={"mirror", "window", "table", "floor"},
        tags={"magic", "bubbles"},
    ),
}

SURFACES = {
    "mirror": SurfaceCfg(
        id="mirror",
        label="mirror",
        the="the mirror",
        phrase="a wide mirror",
        room_text="so shiny it looked ready to copy every silly face twice",
        smooth=True,
        on_floor=False,
        wipeable=True,
        tags={"mirror"},
    ),
    "window": SurfaceCfg(
        id="window",
        label="window",
        the="the window",
        phrase="a tall window",
        room_text="bright enough to show every fingerprint if anybody made one",
        smooth=True,
        on_floor=False,
        wipeable=True,
        tags={"window"},
    ),
    "table": SurfaceCfg(
        id="table",
        label="table",
        the="the table",
        phrase="a sturdy table",
        room_text="broad and flat and therefore tempting to every inventor in the family",
        smooth=True,
        on_floor=False,
        wipeable=True,
        tags={"table"},
    ),
    "floor": SurfaceCfg(
        id="floor",
        label="floor",
        the="the floor",
        phrase="the smooth floor",
        room_text="wide open, like a stage waiting for terrible ideas in socks",
        smooth=True,
        on_floor=True,
        wipeable=True,
        tags={"floor"},
    ),
    "desk": SurfaceCfg(
        id="desk",
        label="desk",
        the="the desk",
        phrase="a little desk",
        room_text="with a clear top that made every crumb look guilty",
        smooth=True,
        on_floor=False,
        wipeable=True,
        tags={"desk"},
    ),
    "fridge": SurfaceCfg(
        id="fridge",
        label="fridge door",
        the="the fridge door",
        phrase="the white fridge door",
        room_text="which already wore one crooked magnet shaped like a carrot",
        smooth=True,
        on_floor=False,
        wipeable=True,
        tags={"fridge"},
    ),
    "rug": SurfaceCfg(
        id="rug",
        label="rug",
        the="the rug",
        phrase="a fluffy rug",
        room_text="that would drink up mess like a thirsty sponge",
        smooth=False,
        on_floor=True,
        wipeable=False,
        tags={"rug"},
    ),
}

CLEANERS = {
    "damp_cloth": CleanerCfg(
        id="damp_cloth",
        label="damp cloth",
        phrase="a damp cloth",
        guards={"ink", "bubbly"},
        surfaces={"mirror", "window", "table", "desk", "fridge"},
        sense=3,
        power=2,
        success_text="wiped every last bit of magic off the {surface}",
        fail_text="tried to wipe the {surface}, but the cloth was too small and the magic slipped around it",
        qa_text="wiped the magic away with a damp cloth",
        tags={"cloth", "wipe"},
    ),
    "lemon_sponge": CleanerCfg(
        id="lemon_sponge",
        label="lemon sponge",
        phrase="the lemon sponge",
        guards={"sticky", "bubbly"},
        surfaces={"table", "desk", "fridge", "mirror", "window"},
        sense=3,
        power=3,
        success_text="gave the {surface} three brisk wipes until the sticky spell gave up",
        fail_text="scrubbed at the {surface}, but the spell kept sticking itself somewhere new",
        qa_text="scrubbed the mess away with a lemon sponge",
        tags={"sponge", "wipe"},
    ),
    "mop": CleanerCfg(
        id="mop",
        label="mop",
        phrase="the long mop",
        guards={"sticky", "bubbly"},
        surfaces={"floor"},
        sense=3,
        power=4,
        success_text="swished the mop across the {surface} in a great shining arc",
        fail_text="swished at the {surface}, but the magic slid around the mop head and squeaked with triumph",
        qa_text="mopped the magic off the floor",
        tags={"mop", "wipe"},
    ),
    "paper_towel": CleanerCfg(
        id="paper_towel",
        label="paper towel",
        phrase="a paper towel",
        guards={"ink"},
        surfaces={"mirror", "window", "fridge"},
        sense=2,
        power=1,
        success_text="pressed a paper towel to the {surface} and wiped the little ink curls away",
        fail_text="dabbed at the {surface}, but the paper tore and the spell spread into extra smudges",
        qa_text="used a paper towel to wipe off the ink",
        tags={"paper_towel", "wipe"},
    ),
    "sleeve": CleanerCfg(
        id="sleeve",
        label="shirt sleeve",
        phrase="a shirt sleeve",
        guards={"ink"},
        surfaces={"mirror", "window", "fridge"},
        sense=1,
        power=0,
        success_text="rubbed the {surface} with a sleeve",
        fail_text="rubbed the {surface} with a sleeve, which only smeared everything worse",
        qa_text="rubbed at it with a sleeve",
        tags={"bad_idea"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Milo", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["careful", "curious", "clever", "cautious", "sensible", "thoughtful", "giggly"]


@dataclass
class StoryParams:
    room: str
    spell: str
    surface: str
    cleaner: str
    instigator: str
    instigator_gender: str
    helper: str
    helper_gender: str
    adult: str
    trait: str
    delay: int = 0
    instigator_age: int = 6
    helper_age: int = 4
    relation: str = "siblings"
    seed: Optional[int] = None


KNOWLEDGE = {
    "magic": [(
        "What is a magic trick?",
        "A magic trick is something that looks surprising or impossible, even though somebody made it happen on purpose. Good tricks should be safe and planned."
    )],
    "wipe": [(
        "What does wipe mean?",
        "To wipe means to rub a surface with a cloth, sponge, or mop so a mess comes off. A good wipe can clean water, crumbs, or sticky goo."
    )],
    "mirror": [(
        "Why is a mirror easy to wipe?",
        "A mirror has a smooth hard surface, so a damp cloth can slide over it and lift the mess away. That is why fingerprints show up on mirrors so easily."
    )],
    "window": [(
        "Why do windows show smudges?",
        "Windows are smooth glass, so dirt and fingerprints sit right on top where you can see them. A wipe with the right cloth can clear them away."
    )],
    "table": [(
        "Why should a sticky table be cleaned quickly?",
        "Sticky spills grab dust and crumbs and make the table unpleasant to touch. Cleaning them fast keeps the mess from spreading."
    )],
    "floor": [(
        "Why is a messy floor dangerous?",
        "A wet or slippery floor can make people slide or fall. That is why grown-ups like spills to be wiped up right away."
    )],
    "sticky": [(
        "What does sticky mean?",
        "Sticky means something clings and does not want to let go. Syrup, jam, and pudding can all feel sticky."
    )],
    "bubbles": [(
        "Why can bubbles make a mess?",
        "Bubbles may look light and funny, but when they pop they leave little wet spots behind. Many bubbles together can make a surface slippery or streaky."
    )],
    "cloth": [(
        "What is a damp cloth good for?",
        "A damp cloth is good for wiping smooth surfaces because it can pick up dust, marks, and little spills. The water helps the mess loosen."
    )],
    "sponge": [(
        "Why does a sponge help with sticky messes?",
        "A sponge can hold water and soap, so it helps lift sticky goo off a surface. It is good when a dry cloth would only smear things around."
    )],
    "mop": [(
        "What is a mop for?",
        "A mop is for wiping large floor messes. Its long handle helps a grown-up clean a wide area without kneeling on the floor."
    )],
}

KNOWLEDGE_ORDER = [
    "magic", "wipe", "mirror", "window", "table", "floor",
    "sticky", "bubbles", "cloth", "sponge", "mop",
]


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
    instigator = f["instigator"]
    helper = f["helper"]
    spell = f["spell"]
    surface = f["surface_cfg"]
    cleaner = f["cleaner"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            f'Write a funny magic story for a 3-to-5-year-old that includes the word "wipe" and ends before the spell goes wrong.',
            f"Tell a comedy story where {instigator.id} wants to use {spell.title} on {surface.the}, but {helper.id} talks {instigator.pronoun('object')} out of it and they choose a safe joke instead.",
            f'Write a gentle magical near-miss where a child learns that if you cannot wipe a trick away, you should not do it at all.',
        ]
    if outcome == "soggy":
        return [
            f'Write a funny cleanup story for a 3-to-5-year-old that includes the word "wipe" and a magic mess that gets bigger before it gets better.',
            f"Tell a comedy story where {instigator.id} uses {spell.title}, the first cleanup tool is not enough, and the whole room has to help wipe the mess away.",
            f'Write a magical humor story where a joke spell turns into a sticky problem, but the ending still feels warm and playful.',
        ]
    return [
        f'Write a funny magic story for a 3-to-5-year-old that includes the word "wipe" and ends with a room becoming neat again.',
        f"Tell a comedy story where {instigator.id} casts {spell.title} on {surface.the}, and a calm grown-up fixes the problem with {cleaner.phrase}.",
        f'Write a playful story about a child learning that a clever trick is only good if it can be wiped away safely.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    instigator = f["instigator"]
    helper = f["helper"]
    adult = f["adult"]
    room_cfg = f["room_cfg"]
    spell = f["spell"]
    surface = f["surface_cfg"]
    cleaner = f["cleaner"]
    pair = pair_noun(instigator, helper, f["relation"])
    adult_word = adult.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {instigator.id} and {helper.id}, in {room_cfg.label}. A calm {adult_word} helps when the magic gets risky."
        ),
        (
            f"What trick did {instigator.id} want to try?",
            f"{instigator.id} wanted to cast {spell.title} on {surface.the}. The trick was meant to be funny, but it could leave {surface.the} {spell.residue}."
        ),
        (
            f"Why did {helper.id} warn {instigator.id}?",
            f"{helper.id} knew the spell could leave a mess that needed a real wipe to remove. The warning came before the trouble, because {helper.id} could already imagine the room getting harder to clean."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append((
            f"What happened after the warning?",
            f"{instigator.id} stopped before casting the spell, so no magic mess spread at all. Instead, the children made a safe silly picture and wiped it away normally."
        ))
        qa.append((
            "How did the story end?",
            f"It ended neatly and happily. The room stayed tidy, and the children learned that some jokes are funniest when they stay easy to clean."
        ))
    elif f["outcome"] == "contained":
        qa.append((
            f"How did the {adult_word} fix the problem?",
            f"The {adult_word} used {cleaner.phrase} and {cleaner.qa_text}. That worked because it was the right cleanup tool for that kind of magical mess."
        ))
        qa.append((
            "What did the children learn?",
            f"They learned that a trick needs a cleanup plan. If they cannot wipe the mess safely, the trick is not ready to use."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with the room neat again and the children laughing more carefully. The final clean wipe showed that the trouble was truly over."
        ))
    else:
        qa.append((
            f"Why did the first cleanup go badly?",
            f"The first tool was not strong enough for how big the mess had become. So instead of stopping the spell at once, everyone had to spend much longer wiping the room."
        ))
        qa.append((
            "Was the ending scary or safe?",
            f"It stayed safe, but it became soggy and tiring before it got better. By supper time the room was clean again, and the children understood why the right wipe matters."
        ))
        qa.append((
            "What was funny about the magical mess?",
            f"The spell was silly because it spread onto odd things and acted as if it had its own joke ideas. The humor made the story playful even while the cleanup lesson stayed real."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"magic", "wipe"}
    surface = f["surface_cfg"]
    if surface.id in {"mirror", "window", "table", "floor"}:
        tags.add(surface.id)
    if f["spell"].mess_kind == "sticky":
        tags.add("sticky")
    if f["spell"].mess_kind == "bubbly":
        tags.add("bubbles")
    if f["cleaner"].id == "damp_cloth":
        tags.add("cloth")
    if f["cleaner"].id == "lemon_sponge":
        tags.add("sponge")
    if f["cleaner"].id == "mop":
        tags.add("mop")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = []
        if ent.wipeable:
            flags.append("wipeable")
        if ent.smooth:
            flags.append("smooth")
        if ent.on_floor:
            flags.append("on_floor")
        if flags:
            bits.append(f"flags={flags}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        room="bathroom",
        spell="mustache_mizzle",
        surface="mirror",
        cleaner="damp_cloth",
        instigator="Milo",
        instigator_gender="boy",
        helper="Lily",
        helper_gender="girl",
        adult="mother",
        trait="careful",
        delay=0,
        instigator_age=6,
        helper_age=4,
        relation="siblings",
    ),
    StoryParams(
        room="kitchen",
        spell="pudding_pop",
        surface="table",
        cleaner="lemon_sponge",
        instigator="Ava",
        instigator_gender="girl",
        helper="Ben",
        helper_gender="boy",
        adult="father",
        trait="clever",
        delay=0,
        instigator_age=5,
        helper_age=5,
        relation="friends",
    ),
    StoryParams(
        room="kitchen",
        spell="pudding_pop",
        surface="floor",
        cleaner="paper_towel",
        instigator="Sam",
        instigator_gender="boy",
        helper="Maya",
        helper_gender="girl",
        adult="mother",
        trait="cautious",
        delay=1,
        instigator_age=6,
        helper_age=4,
        relation="siblings",
    ),
    StoryParams(
        room="classroom",
        spell="bubble_banjo",
        surface="window",
        cleaner="damp_cloth",
        instigator="Zoe",
        instigator_gender="girl",
        helper="Anna",
        helper_gender="girl",
        adult="aunt",
        trait="careful",
        delay=0,
        instigator_age=5,
        helper_age=7,
        relation="siblings",
    ),
    StoryParams(
        room="kitchen",
        spell="mustache_mizzle",
        surface="fridge",
        cleaner="paper_towel",
        instigator="Noah",
        instigator_gender="boy",
        helper="Ella",
        helper_gender="girl",
        adult="father",
        trait="thoughtful",
        delay=1,
        instigator_age=6,
        helper_age=4,
        relation="friends",
    ),
]


def explain_surface_rejection(surface: SurfaceCfg, spell: Optional[SpellCfg] = None) -> str:
    if not surface.wipeable:
        if spell is None:
            return (
                f"(No story: {surface.the} is not a good wipe-away surface. "
                f"This world needs a mess that can honestly be cleaned with a wipe.)"
            )
        return (
            f"(No story: {spell.title} on {surface.the} would sink into the material instead of wiping clean. "
            f"Pick a smooth washable surface like a mirror, table, or window.)"
        )
    return "(No story: that surface does not fit this domain.)"


def explain_combo_rejection(room: RoomCfg, spell: SpellCfg, surface: SurfaceCfg) -> str:
    if surface.id not in room.affords:
        return (
            f"(No story: {surface.the} is not the featured washable surface in {room.label}. "
            f"Pick one of: {', '.join(sorted(room.affords))}.)"
        )
    if not spell_fits_surface(spell, surface):
        return (
            f"(No story: {spell.title} does not belong on {surface.the} here. "
            f"The comic mess needs a surface that can reasonably show that kind of magic and be wiped away.)"
        )
    if not any(cleaner_fits(c, spell, surface) for c in sensible_cleaners()):
        return (
            f"(No story: no sensible cleaner in this world can wipe {spell.title} off {surface.the}. "
            f"A valid story needs an honest cleanup method.)"
        )
    return "(No story: this combination is unreasonable.)"


def explain_cleaner(cleaner_id: str) -> str:
    cleaner = CLEANERS[cleaner_id]
    return (
        f"(Refusing cleaner '{cleaner_id}': it scores too low on common sense "
        f"(sense={cleaner.sense} < {SENSE_MIN}). A comedy story can be silly, but the cleanup still has to be sensible.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.helper_age, params.trait):
        return "averted"
    cleaner = CLEANERS[params.cleaner]
    spell = SPELLS[params.spell]
    surface = SURFACES[params.surface]
    return "contained" if is_contained(cleaner, spell, params.delay, surface) else "soggy"


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
valid(Room, Spell, Surface) :-
    room(Room), spell(Spell), surface(Surface),
    affords(Room, Surface), wipeable(Surface), works_on(Spell, Surface),
    sensible_cleaner_for(Spell, Surface).

sensible(Cleaner) :-
    cleaner(Cleaner), sense(Cleaner, S), sense_min(M), S >= M.

sensible_cleaner_for(Spell, Surface) :-
    sensible(Cleaner), guards(Cleaner, Kind), mess_kind(Spell, Kind),
    reaches(Cleaner, Surface).

% --- outcome model ---------------------------------------------------------
cautious_now(Trait) :- trait(Trait), is_cautious(Trait).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
helper_older :- relation(siblings), instigator_age(IA), helper_age(HA), HA > IA.
bonus(4) :- helper_older.
bonus(0) :- not helper_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- helper_older, authority(A), mischief_init(M), A > M.

severity(Base + Delay + Floor) :-
    chosen_spell(Spell), spell_severity(Spell, Base),
    chosen_surface(Surface), floor_bonus(Surface, Floor),
    delay(Delay).

contained :-
    chosen_cleaner(Cleaner), power(Cleaner, P),
    severity(V), P >= V.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(soggy) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for room_id, room in ROOMS.items():
        lines.append(asp.fact("room", room_id))
        for surface_id in sorted(room.affords):
            lines.append(asp.fact("affords", room_id, surface_id))
    for spell_id, spell in SPELLS.items():
        lines.append(asp.fact("spell", spell_id))
        lines.append(asp.fact("mess_kind", spell_id, spell.mess_kind))
        lines.append(asp.fact("spell_severity", spell_id, spell.severity))
        for surface_id in sorted(spell.surfaces):
            lines.append(asp.fact("works_on", spell_id, surface_id))
    for surface_id, surface in SURFACES.items():
        lines.append(asp.fact("surface", surface_id))
        if surface.wipeable:
            lines.append(asp.fact("wipeable", surface_id))
        lines.append(asp.fact("floor_bonus", surface_id, 1 if surface.on_floor else 0))
    for cleaner_id, cleaner in CLEANERS.items():
        lines.append(asp.fact("cleaner", cleaner_id))
        lines.append(asp.fact("sense", cleaner_id, cleaner.sense))
        lines.append(asp.fact("power", cleaner_id, cleaner.power))
        for kind in sorted(cleaner.guards):
            lines.append(asp.fact("guards", cleaner_id, kind))
        for surface_id in sorted(cleaner.surfaces):
            lines.append(asp.fact("reaches", cleaner_id, surface_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("mischief_init", int(MISCHIEF_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
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
    return sorted(c for (c,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_spell", params.spell),
        asp.fact("chosen_surface", params.surface),
        asp.fact("chosen_cleaner", params.cleaner),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("instigator_age", params.instigator_age),
        asp.fact("helper_age", params.helper_age),
        asp.fact("trait", params.trait),
    ])
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

    clingo_cleaners = set(asp_sensible())
    python_cleaners = {c.id for c in sensible_cleaners()}
    if clingo_cleaners == python_cleaners:
        print(f"OK: sensible cleaners match ({sorted(clingo_cleaners)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible cleaners: clingo={sorted(clingo_cleaners)} python={sorted(python_cleaners)}")

    cases = list(CURATED)
    for s in range(150):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test story generation succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a silly magic mess and the right wipe for it."
    )
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--spell", choices=SPELLS)
    ap.add_argument("--surface", choices=SURFACES)
    ap.add_argument("--cleaner", choices=CLEANERS)
    ap.add_argument("--adult", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.surface and not SURFACES[args.surface].wipeable:
        spell = SPELLS[args.spell] if args.spell else None
        raise StoryError(explain_surface_rejection(SURFACES[args.surface], spell))
    if args.cleaner and CLEANERS[args.cleaner].sense < SENSE_MIN:
        raise StoryError(explain_cleaner(args.cleaner))
    if args.room and args.spell and args.surface:
        room = ROOMS[args.room]
        spell = SPELLS[args.spell]
        surface = SURFACES[args.surface]
        if (args.surface not in room.affords) or (not spell_fits_surface(spell, surface)) or (
            not any(cleaner_fits(c, spell, surface) for c in sensible_cleaners())
        ):
            raise StoryError(explain_combo_rejection(room, spell, surface))

    combos = [
        combo for combo in valid_combos()
        if (args.room is None or combo[0] == args.room)
        and (args.spell is None or combo[1] == args.spell)
        and (args.surface is None or combo[2] == args.surface)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    room_id, spell_id, surface_id = rng.choice(sorted(combos))
    spell = SPELLS[spell_id]
    surface = SURFACES[surface_id]

    cleaner_options = [
        cid for cid, cleaner in CLEANERS.items()
        if cleaner.sense >= SENSE_MIN and cleaner_fits(cleaner, spell, surface)
    ]
    if args.cleaner is not None:
        if args.cleaner not in cleaner_options:
            raise StoryError(
                f"(No story: {CLEANERS[args.cleaner].label} is not a sensible way to wipe {spell.title} from {surface.the}.)"
            )
        cleaner_id = args.cleaner
    else:
        cleaner_id = rng.choice(sorted(cleaner_options))

    instigator_name, instigator_gender = _pick_child(rng)
    helper_name, helper_gender = _pick_child(rng, avoid=instigator_name)
    adult = args.adult or rng.choice(["mother", "father", "aunt", "uncle"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, helper_age = rng.sample([3, 4, 5, 6, 7], 2)

    return StoryParams(
        room=room_id,
        spell=spell_id,
        surface=surface_id,
        cleaner=cleaner_id,
        instigator=instigator_name,
        instigator_gender=instigator_gender,
        helper=helper_name,
        helper_gender=helper_gender,
        adult=adult,
        trait=trait,
        delay=delay,
        instigator_age=instigator_age,
        helper_age=helper_age,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        room_cfg = ROOMS[params.room]
        spell = SPELLS[params.spell]
        surface_cfg = SURFACES[params.surface]
        cleaner_cfg = CLEANERS[params.cleaner]
    except KeyError as exc:
        raise StoryError(f"(Invalid parameter value: {exc.args[0]}.)") from exc

    if not surface_cfg.wipeable:
        raise StoryError(explain_surface_rejection(surface_cfg, spell))
    if params.surface not in room_cfg.affords or not spell_fits_surface(spell, surface_cfg):
        raise StoryError(explain_combo_rejection(room_cfg, spell, surface_cfg))
    if cleaner_cfg.sense < SENSE_MIN:
        raise StoryError(explain_cleaner(params.cleaner))
    if not cleaner_fits(cleaner_cfg, spell, surface_cfg):
        raise StoryError(
            f"(No story: {cleaner_cfg.label} cannot honestly wipe {spell.title} from {surface_cfg.the}.)"
        )

    world = tell(
        room_cfg=room_cfg,
        spell=spell,
        surface_cfg=surface_cfg,
        cleaner_cfg=cleaner_cfg,
        instigator_name=params.instigator,
        instigator_gender=params.instigator_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        trait=params.trait,
        adult_type=params.adult,
        delay=params.delay,
        instigator_age=params.instigator_age,
        helper_age=params.helper_age,
        relation=params.relation,
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
        print(f"sensible cleaners: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (room, spell, surface) combos:\n")
        for room, spell, surface in combos:
            print(f"  {room:10} {spell:16} {surface}")
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
            params = sample.params
            header = (
                f"### {params.instigator} & {params.helper}: {params.spell} on "
                f"{params.surface} in {params.room} ({outcome_of(params)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
