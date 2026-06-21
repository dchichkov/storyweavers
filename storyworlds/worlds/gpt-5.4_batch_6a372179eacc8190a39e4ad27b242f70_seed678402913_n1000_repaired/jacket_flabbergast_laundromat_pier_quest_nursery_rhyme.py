#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/jacket_flabbergast_laundromat_pier_quest_nursery_rhyme.py
=====================================================================================

A small storyworld about a child on a pier, a favorite jacket, and a bouncy
little quest that bumps into sea spray and ends at a laundromat.

The domain is deliberately tiny and child-facing:
- a child starts a quest on the pier
- a splashy mishap threatens the jacket and the quest token tucked inside it
- the child hurries to the pier laundromat
- a sensible remedy either saves the day or proves too small for the mess

The prose aims for a nursery-rhyme lilt while still being driven by simulated
state rather than by one frozen paragraph.
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

# Make the shared result containers importable when this script is run directly
# from the repo root. This file lives under storyworlds/worlds/gpt-5.4/, so the
# package dir is three levels up.
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
    traits: list[str] = field(default_factory=list)
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
class Quest:
    id: str
    goal: str
    token: str
    token_phrase: str
    rhyme_line: str
    finish_place: str
    finish_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    label: str
    start_line: str
    hit_line: str
    mess: str
    severity: int
    tags: set[str] = field(default_factory=set)
    causes_mess: bool = True


@dataclass
class Remedy:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    quest: str
    hazard: str
    remedy: str
    hero: str
    gender: str
    parent: str
    jacket_color: str
    trait: str
    delay: int = 0
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


def _r_jacket_to_token(world: World) -> list[str]:
    out: list[str] = []
    jacket = world.entities.get("jacket")
    token = world.entities.get("token")
    hero = world.entities.get("hero")
    if jacket is None or token is None or hero is None:
        return out
    if jacket.meters["mess"] < THRESHOLD:
        return out
    sig = ("dampen_token",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    token.meters["damp"] += 1
    hero.memes["worry"] += 1
    out.append("__mess__")
    return out


CAUSAL_RULES = [
    Rule(name="jacket_to_token", tag="physical", apply=_r_jacket_to_token),
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
        for s in produced:
            world.say(s)
    return produced


QUESTS = {
    "bell": Quest(
        id="bell",
        goal="ring the silver bell at the end of the pier",
        token="bell ticket",
        token_phrase="a small bell ticket",
        rhyme_line="Tip-tap toes on timber bright, ring the bell before the night.",
        finish_place="the bell-post",
        finish_image="the silver bell sang over the water",
        tags={"bell", "quest"},
    ),
    "lantern": Quest(
        id="lantern",
        goal="bring a shell note to the lantern keeper",
        token="shell note",
        token_phrase="a shell note tied with blue string",
        rhyme_line="Clip-clap feet and do not veer, carry the shell note to the pier.",
        finish_place="the lantern hut",
        finish_image="the lantern winked on like a golden eye",
        tags={"lantern", "quest"},
    ),
    "song": Quest(
        id="song",
        goal="deliver a rhyme card to the fiddler by the boats",
        token="rhyme card",
        token_phrase="a rhyme card with curly letters",
        rhyme_line="Skip and sing and do not stop, take the rhyme where fiddles hop.",
        finish_place="the fiddler's stool",
        finish_image="the fiddle skipped out a happy tune",
        tags={"song", "quest"},
    ),
}

HAZARDS = {
    "wave": Hazard(
        id="wave",
        label="a jumping wave",
        start_line="A wave went slap at the pilings below.",
        hit_line="Up sprang the splash and kissed the jacket hem with cold salt water.",
        mess="wet",
        severity=1,
        tags={"wave", "wet"},
        causes_mess=True,
    ),
    "bucket": Hazard(
        id="bucket",
        label="a tippy bait bucket",
        start_line="A bait bucket wobbled with a wobble and a clack.",
        hit_line="Over it tipped, and fishy water splashed the jacket pocket and sleeve.",
        mess="fishy",
        severity=2,
        tags={"bucket", "fishy"},
        causes_mess=True,
    ),
    "dry_wind": Hazard(
        id="dry_wind",
        label="a gusty wind",
        start_line="The wind went whoo through rope and rail.",
        hit_line="It ruffled the jacket but left it dry as a shell.",
        mess="none",
        severity=0,
        tags={"wind"},
        causes_mess=False,
    ),
}

REMEDIES = {
    "dryer": Remedy(
        id="dryer",
        sense=3,
        power=1,
        text="opened a round dryer, tucked the jacket in with two warm towels, and turned the drum until the cloth came out toasty",
        fail="gave the jacket a quick spin in the dryer, but the fishy smell still clung to the pocket",
        qa_text="warmed the jacket dry in the laundromat dryer",
        tags={"dryer", "laundromat"},
    ),
    "wash_and_dry": Remedy(
        id="wash_and_dry",
        sense=3,
        power=2,
        text="washed the jacket with lemon soap, then dried it in the round humming dryer until it smelled fresh and warm",
        fail="washed and dried the jacket, but the parade clock had already run ahead of them",
        qa_text="washed the jacket clean and dried it warm at the laundromat",
        tags={"washer", "dryer", "laundromat"},
    ),
    "pat_with_napkin": Remedy(
        id="pat_with_napkin",
        sense=1,
        power=0,
        text="dabbed at the jacket with a napkin",
        fail="dabbed at the jacket with a napkin, which hardly helped at all",
        qa_text="dabbed at the jacket with a napkin",
        tags={"napkin"},
    ),
}

JACKET_COLORS = ["red", "yellow", "blue", "green", "striped"]
TRAITS = ["brisk", "careful", "bouncy", "bright", "patient"]
GIRL_NAMES = ["Mina", "Lulu", "Poppy", "Nell", "Tess", "Dora"]
BOY_NAMES = ["Pip", "Ned", "Milo", "Owen", "Toby", "Rory"]


def hazard_at_risk(hazard: Hazard) -> bool:
    return hazard.causes_mess


def sensible_remedies() -> list[Remedy]:
    return [r for r in REMEDIES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for quest_id in QUESTS:
        for hazard_id, hazard in HAZARDS.items():
            if hazard_at_risk(hazard):
                combos.append((quest_id, hazard_id))
    return combos


def mess_value(hazard: Hazard) -> int:
    return hazard.severity


def can_fix(remedy: Remedy, hazard: Hazard, delay: int) -> bool:
    return remedy.power >= (mess_value(hazard) + delay)


def predict_mess(world: World, hazard_id: str) -> dict:
    sim = world.copy()
    jacket = sim.get("jacket")
    token = sim.get("token")
    hazard = HAZARDS[hazard_id]
    if hazard.causes_mess:
        jacket.meters["mess"] += 1
        jacket.attrs["mess_kind"] = hazard.mess
        propagate(sim, narrate=False)
    return {
        "jacket_mess": jacket.meters["mess"],
        "token_damp": token.meters["damp"],
    }


def setup(world: World, hero: Entity, parent: Entity, jacket: Entity, quest: Quest, token: Entity) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"{hero.id} skipped down the pier in a {jacket.attrs['color']} jacket, "
        f"light as a kite and neat as a pin."
    )
    world.say(
        f"{hero.pronoun().capitalize()} had a quest for the morning: {quest.goal}. "
        f"In the pocket rested {token.phrase}."
    )
    world.say(quest.rhyme_line)
    world.say(
        f'"Mind the boards," said {hero.pronoun("possessive")} {parent.label_word}, '
        f'"and mind that jacket too."'
    )


def tempt(world: World, hero: Entity, hazard: Hazard) -> None:
    hero.memes["eager"] += 1
    world.say(hazard.start_line)
    world.say(
        f"But the quest tugged ahead, and {hero.id} hurried on with {hero.pronoun("possessive")} "
        f"nose toward the end of the pier."
    )


def warn(world: World, hero: Entity, parent: Entity, hazard: Hazard) -> None:
    pred = predict_mess(world, hazard.id)
    world.facts["predicted_token_damp"] = pred["token_damp"]
    if pred["token_damp"] >= THRESHOLD:
        world.say(
            f'"Slow feet save small things," said {hero.pronoun("possessive")} {parent.label_word}. '
            f'"If the jacket gets messy, the quest token in the pocket may get damp too."'
        )


def mishap(world: World, hero: Entity, hazard: Hazard) -> None:
    jacket = world.get("jacket")
    jacket.meters["mess"] += 1
    jacket.attrs["mess_kind"] = hazard.mess
    propagate(world, narrate=False)
    hero.memes["alarm"] += 1
    world.say(hazard.hit_line)
    if hazard.mess == "fishy":
        world.say(f'"Flabbergast!" cried {hero.id}. "My jacket smells like a whole little harbor."')
    else:
        world.say(f'"Flabbergast!" cried {hero.id}. "Now my jacket is all drippy."')


def run_to_laundromat(world: World, hero: Entity, parent: Entity) -> None:
    world.say(
        f"So off they went to the pier laundromat, where the windows glowed round and warm "
        f"like coins in the fog."
    )
    world.say(
        f"The washer hummed. The dryer thumped. Even {hero.id}'s worried feet began to slow."
    )
    hero.memes["hope"] += 1
    parent.memes["care"] += 1


def clean_success(world: World, hero: Entity, parent: Entity, remedy: Remedy) -> None:
    jacket = world.get("jacket")
    token = world.get("token")
    jacket.meters["mess"] = 0.0
    token.meters["damp"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    hero.memes["worry"] = 0.0
    world.say(
        f"The laundromat keeper smiled and {remedy.text}."
    )
    world.say(
        f"Soon the jacket puffed out soft and brave again, and the pocket kept the {token.label} dry."
    )


def clean_fail(world: World, hero: Entity, parent: Entity, remedy: Remedy, hazard: Hazard) -> None:
    hero.memes["sadness"] += 1
    world.say(
        f"The laundromat keeper {remedy.fail}."
    )
    if hazard.mess == "fishy":
        world.say("The jacket was less drippy, but the fishy whiff still wiggled in the cloth.")
    else:
        world.say("The jacket was better than before, but not ready for a proud little quest finish.")


def finish_quest(world: World, hero: Entity, quest: Quest) -> None:
    hero.memes["pride"] += 1
    world.say(
        f"Back to the boards they went, patter and peep, all the way to {quest.finish_place}."
    )
    world.say(
        f"{hero.id} held the pocket flat, delivered the {quest.token}, and {quest.finish_image}."
    )
    world.say(
        f"So the {hero.attrs['trait']} child and the tidy jacket finished the quest at last."
    )


def postpone_quest(world: World, hero: Entity, quest: Quest) -> None:
    hero.memes["lesson"] += 1
    world.say(
        f"They sat on a bench by the laundromat door and watched the gulls bob by the pier."
    )
    world.say(
        f'"The quest can wait till the jacket is truly right," said {hero.id}. '
        f'That was brave in a smaller, steadier way.'
    )
    world.say(
        f"The bell, or lantern, or fiddle would still be there tomorrow, and the child had learned to keep "
        f"small things safe before rushing on."
    )


def tell(
    quest: Quest,
    hazard: Hazard,
    remedy: Remedy,
    hero_name: str,
    hero_type: str,
    parent_type: str,
    jacket_color: str,
    trait: str,
    delay: int,
) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        role="hero",
        traits=[trait],
        attrs={"trait": trait},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    jacket = world.add(Entity(
        id="jacket",
        type="jacket",
        label="jacket",
        phrase=f"a {jacket_color} jacket",
        attrs={"color": jacket_color},
    ))
    token = world.add(Entity(
        id="token",
        type="token",
        label=quest.token,
        phrase=quest.token_phrase,
    ))

    setup(world, hero, parent, jacket, quest, token)

    world.para()
    tempt(world, hero, hazard)
    warn(world, hero, parent, hazard)
    mishap(world, hero, hazard)

    world.para()
    run_to_laundromat(world, hero, parent)
    contained = can_fix(remedy, hazard, delay)
    if contained:
        clean_success(world, hero, parent, remedy)
        world.para()
        finish_quest(world, hero, quest)
    else:
        clean_fail(world, hero, parent, remedy, hazard)
        world.para()
        postpone_quest(world, hero, quest)

    world.facts.update(
        hero=hero,
        parent=parent,
        jacket=jacket,
        token=token,
        quest=quest,
        hazard=hazard,
        remedy=remedy,
        delay=delay,
        contained=contained,
        outcome="finished" if contained else "postponed",
        laundromat_used=True,
    )
    return world


KNOWLEDGE = {
    "pier": [
        (
            "What is a pier?",
            "A pier is a long walkway built out over the water. Boats can stop beside it, and people can walk along it."
        )
    ],
    "laundromat": [
        (
            "What is a laundromat?",
            "A laundromat is a place with washers and dryers for cleaning clothes. People go there when something needs washing or drying."
        )
    ],
    "dryer": [
        (
            "What does a dryer do?",
            "A dryer spins warm air around wet clothes so they become dry. It helps soggy cloth feel warm and fluffy again."
        )
    ],
    "washer": [
        (
            "What does a washing machine do?",
            "A washing machine swishes clothes in soapy water to clean dirt and smells away. After washing, clothes are cleaner and fresher."
        )
    ],
    "wave": [
        (
            "Why does sea spray make clothes wet?",
            "Sea spray is made of tiny drops of water thrown up by waves. When it lands on cloth, the cloth gets wet."
        )
    ],
    "fishy": [
        (
            "Why can fishy water leave a smell?",
            "Fishy water can carry strong smells from bait and boats. Cloth can hold those smells until it is washed."
        )
    ],
    "quest": [
        (
            "What is a quest?",
            "A quest is a special job or journey with a goal. You set out to do one important thing and keep going until you finish or wisely pause."
        )
    ],
}
KNOWLEDGE_ORDER = ["pier", "quest", "wave", "fishy", "laundromat", "washer", "dryer"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    hazard = f["hazard"]
    if f["outcome"] == "finished":
        return [
            f'Write a nursery-rhyme-style story set on a pier where a child in a jacket goes on a quest, cries "flabbergast" after a {hazard.label}, and hurries to a laundromat before finishing the job.',
            f"Tell a gentle quest story about {hero.id} on the pier, a favorite jacket, a splashy mishap, and a warm laundromat rescue that lets the child finish the task.",
            f'Write a small rhyming story for a young child that includes the words "jacket", "flabbergast", and "laundromat", and ends with the quest completed.'
        ]
    return [
        f'Write a nursery-rhyme-style story set on a pier where a child in a jacket goes on a quest, cries "flabbergast" after a {hazard.label}, and visits a laundromat, but learns to pause the quest wisely.',
        f"Tell a gentle cautionary quest about {hero.id} hurrying too fast on the pier and needing help at the laundromat, with a calm ending instead of a triumphant one.",
        f'Write a child-facing story that includes the words "jacket", "flabbergast", and "laundromat", and shows that sometimes finishing later is the wiser ending.'
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    quest = f["quest"]
    hazard = f["hazard"]
    remedy = f["remedy"]
    outcome = f["outcome"]
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child in a {world.get('jacket').attrs['color']} jacket, and {hero.pronoun('possessive')} {pw} on the pier. {hero.id} began the day with a small quest and a token tucked safely in a pocket."
        ),
        (
            "What was the quest?",
            f"The quest was to {quest.goal}. The little token in the jacket pocket mattered because {hero.id} needed it to finish that job."
        ),
        (
            f"Why did {hero.id} shout 'Flabbergast'?",
            f"{hero.id} shouted it when {hazard.label} messed up the jacket on the pier. The splash or spill also threatened the quest token in the pocket, so the problem was bigger than a wet sleeve."
        ),
        (
            "Why did they go to the laundromat?",
            f"They went to the laundromat because the jacket needed help before the quest could go on. A messy jacket could make the token damp or smelly, so cleaning it was part of saving the quest."
        ),
    ]
    if outcome == "finished":
        qa.append(
            (
                "How was the problem solved?",
                f"The laundromat keeper {remedy.qa_text}. That fixed the jacket well enough for {hero.id} to go back and finish the quest."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended happily, with {hero.id} returning to {quest.finish_place} and completing the quest. The final image proves what changed: the jacket was tidy again, and the goal was reached."
            )
        )
    else:
        qa.append(
            (
                "Could they finish the quest that day?",
                f"No. They tried to fix the jacket, but it was not truly ready in time, so {hero.id} chose to wait. That choice showed a calmer kind of bravery, because keeping things safe mattered more than rushing."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended quietly outside the laundromat, with the quest postponed instead of finished. The ending shows that {hero.id} had changed from hurrying ahead to thinking carefully about the jacket and the token."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"pier", "quest", "laundromat"}
    tags |= set(world.facts["hazard"].tags)
    tags |= set(world.facts["remedy"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        quest="bell",
        hazard="wave",
        remedy="dryer",
        hero="Pip",
        gender="boy",
        parent="mother",
        jacket_color="yellow",
        trait="brisk",
        delay=0,
    ),
    StoryParams(
        quest="lantern",
        hazard="bucket",
        remedy="wash_and_dry",
        hero="Mina",
        gender="girl",
        parent="father",
        jacket_color="red",
        trait="careful",
        delay=0,
    ),
    StoryParams(
        quest="song",
        hazard="bucket",
        remedy="dryer",
        hero="Ned",
        gender="boy",
        parent="mother",
        jacket_color="blue",
        trait="patient",
        delay=0,
    ),
    StoryParams(
        quest="bell",
        hazard="wave",
        remedy="wash_and_dry",
        hero="Lulu",
        gender="girl",
        parent="father",
        jacket_color="striped",
        trait="bouncy",
        delay=1,
    ),
]


def explain_rejection(hazard: Hazard) -> str:
    return (
        f"(No story: {hazard.label} does not really make the jacket messy, so there is no honest reason to run to the laundromat. "
        f"Pick a splash or spill that actually threatens the quest.)"
    )


def explain_response(remedy_id: str) -> str:
    remedy = REMEDIES[remedy_id]
    better = ", ".join(sorted(r.id for r in sensible_remedies()))
    return (
        f"(Refusing remedy '{remedy_id}': it scores too low on common sense "
        f"(sense={remedy.sense} < {SENSE_MIN}). Try one of the sensible remedies: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    hazard = HAZARDS[params.hazard]
    remedy = REMEDIES[params.remedy]
    return "finished" if can_fix(remedy, hazard, params.delay) else "postponed"


ASP_RULES = r"""
hazard_risk(H) :- hazard(H), causes_mess(H).
sensible(R)    :- remedy(R), sense(R, S), sense_min(M), S >= M.
valid(Q, H)    :- quest(Q), hazard(H), hazard_risk(H).

need(H, V)     :- chosen_hazard(H), severity(H, S), delay(D), V = S + D.
fixed          :- chosen_remedy(R), power(R, P), chosen_hazard(H), need(H, V), P >= V.

outcome(finished)  :- fixed.
outcome(postponed) :- not fixed.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for hid, hazard in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        lines.append(asp.fact("severity", hid, hazard.severity))
        if hazard.causes_mess:
            lines.append(asp.fact("causes_mess", hid))
    for rid, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        lines.append(asp.fact("sense", rid, remedy.sense))
        lines.append(asp.fact("power", rid, remedy.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_hazard", params.hazard),
        asp.fact("chosen_remedy", params.remedy),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


def asp_verify() -> int:
    rc = 0

    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    c_sens = set(asp_sensible())
    p_sens = {r.id for r in sensible_remedies()}
    if c_sens == p_sens:
        print(f"OK: sensible remedies match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible remedies: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    for s in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story or "laundromat" not in sample.story or "jacket" not in sample.story:
            raise StoryError("smoke test story was empty or missed required seed words")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a jacket quest on a pier with a laundromat turn."
    )
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--hero")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--jacket-color", choices=JACKET_COLORS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--delay", type=int, choices=[0, 1], help="extra time lost before the laundromat fix")
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
    if args.hazard:
        hazard = HAZARDS[args.hazard]
        if not hazard_at_risk(hazard):
            raise StoryError(explain_rejection(hazard))
    if args.remedy and REMEDIES[args.remedy].sense < SENSE_MIN:
        raise StoryError(explain_response(args.remedy))

    combos = [
        c for c in valid_combos()
        if (args.quest is None or c[0] == args.quest)
        and (args.hazard is None or c[1] == args.hazard)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    quest_id, hazard_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    jacket_color = args.jacket_color or rng.choice(JACKET_COLORS)
    trait = args.trait or rng.choice(TRAITS)
    remedy = args.remedy or rng.choice(sorted(r.id for r in sensible_remedies()))
    delay = args.delay if args.delay is not None else rng.choice([0, 0, 1])
    return StoryParams(
        quest=quest_id,
        hazard=hazard_id,
        remedy=remedy,
        hero=hero,
        gender=gender,
        parent=parent,
        jacket_color=jacket_color,
        trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        quest = QUESTS[params.quest]
        hazard = HAZARDS[params.hazard]
        remedy = REMEDIES[params.remedy]
    except KeyError as err:
        raise StoryError(f"(Invalid params: unknown key {err!s}.)") from None

    if not hazard_at_risk(hazard):
        raise StoryError(explain_rejection(hazard))
    if remedy.sense < SENSE_MIN:
        raise StoryError(explain_response(params.remedy))

    world = tell(
        quest=quest,
        hazard=hazard,
        remedy=remedy,
        hero_name=params.hero,
        hero_type=params.gender,
        parent_type=params.parent,
        jacket_color=params.jacket_color,
        trait=params.trait,
        delay=params.delay,
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
        print(asp_program("", "#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible remedies: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (quest, hazard) combos:\n")
        for quest_id, hazard_id in combos:
            print(f"  {quest_id:8} {hazard_id}")
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
            header = f"### {p.hero}: {p.quest} with {p.hazard} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
