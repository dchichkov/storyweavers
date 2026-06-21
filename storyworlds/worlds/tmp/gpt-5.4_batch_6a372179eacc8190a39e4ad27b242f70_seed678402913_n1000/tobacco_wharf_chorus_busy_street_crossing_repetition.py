#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/tobacco_wharf_chorus_busy_street_crossing_repetition.py
==================================================================================

A standalone storyworld for a tiny detective-story domain set at a busy street
crossing by the wharf.

Seed ingredients rebuilt as a small simulation:
- words: tobacco, wharf, chorus
- setting: busy street crossing
- features: repetition, bad ending
- style: detective story

Premise
-------
A child detective and a partner are asked to help someone from the wharf chorus.
A missing object must be found before the chorus begins. The main clue always
includes a tobacco smell, but some tobacco clues are vague and lead to repeated
false starts around the crossing. The crossing plan is always safety-first, yet
different safe plans cost different amounts of time. If the pair loses too much
time, the case is missed for the night: the chorus begins without the item, or
the suspect slips away along the wharf.

Run it
------
python storyworlds/worlds/gpt-5.4/tobacco_wharf_chorus_busy_street_crossing_repetition.py
python storyworlds/worlds/gpt-5.4/tobacco_wharf_chorus_busy_street_crossing_repetition.py --all
python storyworlds/worlds/gpt-5.4/tobacco_wharf_chorus_busy_street_crossing_repetition.py -n 5 --seed 7
python storyworlds/worlds/gpt-5.4/tobacco_wharf_chorus_busy_street_crossing_repetition.py --qa --json
python storyworlds/worlds/gpt-5.4/tobacco_wharf_chorus_busy_street_crossing_repetition.py --verify
"""

from __future__ import annotations

import argparse
import io
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

# Make the shared result containers importable when this script is run directly
# from its nested directory under storyworlds/worlds/<model>/.
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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Crowd:
    id: str
    label: str = ""
    detail: str = ""
    risk: int = 1
    wait: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class CaseFile:
    id: str
    item: str = ""
    item_phrase: str = ""
    owner_role: str = ""
    deadline: int = 3
    opening: str = ""
    ending_bad: str = ""
    ending_good: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str = ""
    smell_line: str = ""
    confusion: int = 0
    wrong_people: list[str] = field(default_factory=list)
    true_holder: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str = ""
    method: str = ""
    capacity: int = 1
    delay: int = 0
    sense: int = 2
    arrival: str = ""
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
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


CROWDS = {
    "tram_bells": Crowd(
        id="tram_bells",
        label="tram bells",
        detail="Tram bells rang, carts rattled, and grown-ups hurried across the painted lines.",
        risk=2,
        wait=1,
        tags={"street", "traffic"},
    ),
    "market_rush": Crowd(
        id="market_rush",
        label="market rush",
        detail="Barrows squeaked, bus tires hissed, and the crossing filled and emptied like a tide.",
        risk=2,
        wait=2,
        tags={"street", "traffic"},
    ),
    "ferry_crush": Crowd(
        id="ferry_crush",
        label="ferry crush",
        detail="The ferry crowd poured toward the wharf, shoulder to shoulder, while horns and brakes argued at the curb.",
        risk=3,
        wait=2,
        tags={"street", "traffic", "wharf"},
    ),
}

CASES = {
    "songbook": CaseFile(
        id="songbook",
        item="songbook",
        item_phrase="the blue chorus songbook",
        owner_role="choir leader",
        deadline=3,
        opening="Without it, the wharf chorus would have to begin by memory and guesswork.",
        ending_bad="By the time the children reached the wharf gate, the chorus had already begun without the blue songbook, and the thin first notes sounded lost in the wind.",
        ending_good="They reached the wharf in time, and when the songbook was opened, the whole chorus lifted one bright song together.",
        tags={"chorus", "book"},
    ),
    "baton": CaseFile(
        id="baton",
        item="baton",
        item_phrase="the little walnut conductor's baton",
        owner_role="chorus conductor",
        deadline=2,
        opening="Without it, the wharf chorus kept peeking at one another, unsure when the first note should begin.",
        ending_bad="They were too late. On the wharf, the chorus started in a ragged clump, with no baton to guide their hands or breaths.",
        ending_good="The baton came back just as the conductor raised a hand, and the chorus entered together as neat as one long ribbon.",
        tags={"chorus", "music"},
    ),
    "lantern": CaseFile(
        id="lantern",
        item="lantern",
        item_phrase="the brass lantern for the front singer",
        owner_role="lead singer",
        deadline=4,
        opening="Without it, the singers at the wharf would stand in a dim patch where nobody could see the first face.",
        ending_bad="When they finally got to the wharf, the lantern was still gone and the chorus stood in the evening gloom like shapes cut from paper.",
        ending_good="The lantern was returned before dusk settled, and its warm circle made the chorus look brave and ready.",
        tags={"chorus", "light"},
    ),
}

CLUES = {
    "tobacco_coat": Clue(
        id="tobacco_coat",
        label="a tobacco-smelling coat",
        smell_line="A stale tobacco smell clung to the bit of cloth left on the curb.",
        confusion=2,
        wrong_people=["a sailor with a brown cap", "a porter rolling crates"],
        true_holder="a ticket clerk in a neat gray coat",
        tags={"tobacco", "smell"},
    ),
    "tobacco_crate": Clue(
        id="tobacco_crate",
        label="a tobacco-marked crate slip",
        smell_line="The paper slip smelled of tobacco and river damp.",
        confusion=1,
        wrong_people=["a deckhand carrying rope"],
        true_holder="a cart driver with the chorus parcel under the seat",
        tags={"tobacco", "smell"},
    ),
    "tobacco_scarf": Clue(
        id="tobacco_scarf",
        label="a tobacco-tainted scarf thread",
        smell_line="One loose thread smelled faintly of tobacco, but the smell was old and thin.",
        confusion=0,
        wrong_people=[],
        true_holder="the wharf watchman who had picked the item up for safekeeping",
        tags={"tobacco", "smell"},
    ),
}

HELPERS = {
    "crossing_guard": Helper(
        id="crossing_guard",
        label="a crossing guard",
        method="held up a gloved hand and stopped the stream of wheels for them",
        capacity=3,
        delay=0,
        sense=3,
        arrival="A crossing guard noticed the children's worried faces and stepped to the curb with a bright red flag.",
        tags={"crossing_guard", "safety"},
    ),
    "green_light": Helper(
        id="green_light",
        label="the walk signal",
        method="waited for the green walking light and crossed when the cars had to stay put",
        capacity=2,
        delay=1,
        sense=3,
        arrival="They stood shoulder to shoulder at the curb and watched for the green walking light.",
        tags={"signal", "safety"},
    ),
    "footbridge": Helper(
        id="footbridge",
        label="the iron footbridge",
        method="climbed the iron footbridge over the road instead of hurrying through the crush below",
        capacity=3,
        delay=2,
        sense=3,
        arrival="The old iron footbridge arched above the crossing, safe and slow.",
        tags={"bridge", "safety"},
    ),
    "painted_lines": Helper(
        id="painted_lines",
        label="just the painted lines",
        method="tried to trust the painted lines alone in the middle of all that noise",
        capacity=1,
        delay=1,
        sense=1,
        arrival="They looked at the painted lines and the racing wheels beyond them.",
        tags={"unsafe_choice"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Tess", "Ruby", "Clara"]
BOY_NAMES = ["Owen", "Jude", "Finn", "Leo", "Max", "Theo"]
TRAITS = ["sharp-eyed", "careful", "quiet", "steady", "curious", "patient"]


@dataclass
class StoryParams:
    case_id: str
    clue_id: str
    helper_id: str
    crowd_id: str
    detective_name: str
    detective_gender: str
    partner_name: str
    partner_gender: str
    detective_trait: str
    partner_trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        case_id="songbook",
        clue_id="tobacco_coat",
        helper_id="green_light",
        crowd_id="market_rush",
        detective_name="Mina",
        detective_gender="girl",
        partner_name="Jude",
        partner_gender="boy",
        detective_trait="sharp-eyed",
        partner_trait="careful",
        seed=101,
    ),
    StoryParams(
        case_id="baton",
        clue_id="tobacco_scarf",
        helper_id="crossing_guard",
        crowd_id="tram_bells",
        detective_name="Owen",
        detective_gender="boy",
        partner_name="Ruby",
        partner_gender="girl",
        detective_trait="steady",
        partner_trait="quiet",
        seed=102,
    ),
    StoryParams(
        case_id="lantern",
        clue_id="tobacco_crate",
        helper_id="footbridge",
        crowd_id="ferry_crush",
        detective_name="Clara",
        detective_gender="girl",
        partner_name="Finn",
        partner_gender="boy",
        detective_trait="patient",
        partner_trait="careful",
        seed=103,
    ),
    StoryParams(
        case_id="baton",
        clue_id="tobacco_coat",
        helper_id="crossing_guard",
        crowd_id="ferry_crush",
        detective_name="Leo",
        detective_gender="boy",
        partner_name="Nora",
        partner_gender="girl",
        detective_trait="sharp-eyed",
        partner_trait="steady",
        seed=104,
    ),
]


def safe_helpers() -> list[Helper]:
    return [h for h in HELPERS.values() if h.sense >= SENSE_MIN]


def valid_combo(case_id: str, clue_id: str, helper_id: str, crowd_id: str) -> bool:
    helper = HELPERS[helper_id]
    crowd = CROWDS[crowd_id]
    return helper.sense >= SENSE_MIN and helper.capacity >= crowd.risk


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for case_id in CASES:
        for clue_id in CLUES:
            for helper_id in HELPERS:
                for crowd_id in CROWDS:
                    if valid_combo(case_id, clue_id, helper_id, crowd_id):
                        combos.append((case_id, clue_id, helper_id, crowd_id))
    return combos


def total_delay(case_id: str, clue_id: str, helper_id: str, crowd_id: str) -> int:
    _ = CASES[case_id]
    clue = CLUES[clue_id]
    helper = HELPERS[helper_id]
    crowd = CROWDS[crowd_id]
    return clue.confusion + helper.delay + crowd.wait


def outcome_of(params: StoryParams) -> str:
    if not valid_combo(params.case_id, params.clue_id, params.helper_id, params.crowd_id):
        raise StoryError("(No story: the chosen crossing plan is not reasonable for this crowd.)")
    case = CASES[params.case_id]
    return "solved" if total_delay(params.case_id, params.clue_id, params.helper_id, params.crowd_id) <= case.deadline else "missed"


def explain_rejection(helper_id: str, crowd_id: str) -> str:
    helper = HELPERS[helper_id]
    crowd = CROWDS[crowd_id]
    if helper.sense < SENSE_MIN:
        better = ", ".join(sorted(h.id for h in safe_helpers()))
        return (
            f"(Refusing helper '{helper_id}': it is too weak on common sense for a child detective story "
            f"(sense={helper.sense} < {SENSE_MIN}). Try a safer crossing plan like {better}.)"
        )
    return (
        f"(No story: {helper.label} cannot safely handle {crowd.label}. "
        f"Pick a stronger crossing plan for this busy street crossing.)"
    )


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def phrase_repeat(world: World, detective: Entity, partner: Entity, times: int) -> None:
    if times <= 0:
        return
    for _ in range(times):
        world.say(
            f'"Clue first, curb first," {detective.id} whispered. '
            f'"Clue first, curb first," {partner.id} answered back.'
        )
        detective.memes["discipline"] += 1
        partner.memes["discipline"] += 1


def tell(case: CaseFile, clue: Clue, helper: Helper, crowd: Crowd,
         detective_name: str, detective_gender: str,
         partner_name: str, partner_gender: str,
         detective_trait: str, partner_trait: str) -> World:
    world = World()
    detective = world.add(Entity(
        id=detective_name,
        kind="character",
        type=detective_gender,
        role="detective",
        label=detective_name,
        traits=[detective_trait],
    ))
    partner = world.add(Entity(
        id=partner_name,
        kind="character",
        type=partner_gender,
        role="partner",
        label=partner_name,
        traits=[partner_trait],
    ))
    owner = world.add(Entity(
        id="Owner",
        kind="character",
        type="woman",
        role="client",
        label="the chorus leader",
        phrase=f"the {case.owner_role} from the wharf chorus",
    ))
    crossing = world.add(Entity(
        id="Crossing",
        type="place",
        label="the busy street crossing",
        phrase="the busy street crossing by the wharf",
        tags={"street", "wharf"},
    ))
    missing = world.add(Entity(
        id="Missing",
        type="object",
        label=case.item,
        phrase=case.item_phrase,
        tags=set(case.tags),
    ))

    detective.memes["focus"] = 2.0
    partner.memes["trust"] = 2.0
    crossing.meters["traffic"] = float(crowd.risk)
    crossing.meters["wait"] = float(crowd.wait)
    missing.meters["urgency"] = float(case.deadline)

    world.say(
        f"By late afternoon, {detective.id} and {partner.id} had promoted themselves to street detectives and were watching "
        f"{crossing.phrase} as if it might confess a secret."
    )
    world.say(
        f"{crowd.detail} Beyond the crossing, the wharf smelled of rope, salt, and old paint, and a few singers were already testing their notes."
    )

    world.para()
    world.say(
        f"Then {owner.phrase} hurried up with worried eyes. "
        f'"Our {missing.phrase} is gone," {owner.pronoun()} said. '
        f'"Please help us before the chorus begins."'
    )
    world.say(case.opening)
    world.say(clue.smell_line)
    world.say(
        f"{detective.id} knelt, touched the clue lightly, and narrowed {detective.pronoun('possessive')} eyes. "
        f'"Tobacco," {detective.pronoun()} said. "That smell came through here."'
    )
    detective.memes["mystery"] += 1
    partner.memes["mystery"] += 1

    world.para()
    world.say(
        f"This was a detective case, but it was also a street case. "
        f"The road between the children and the wharf never stopped moving."
    )
    world.say(helper.arrival)
    phrase_repeat(world, detective, partner, clue.confusion + 1)
    world.say(
        f"Together they {helper.method}. Nobody ran. Nobody guessed with their feet."
    )
    detective.memes["care"] += 1
    partner.memes["care"] += 1

    wrong_turns: list[str] = []
    for wrong in clue.wrong_people:
        world.para()
        world.say(
            f"On the far curb, the tobacco smell brushed past again, and the children hurried after {wrong}. "
            f"For one hopeful minute, the case seemed solved."
        )
        world.say(
            f"But it was the wrong person. {detective.id} stopped, frowned, and looked back toward the crossing."
        )
        detective.memes["frustration"] += 1
        partner.memes["frustration"] += 1
        crossing.meters["delay"] += 1
        wrong_turns.append(wrong)
        phrase_repeat(world, detective, partner, 1)

    solved = total_delay(case.id, clue.id, helper.id, crowd.id) <= case.deadline
    world.para()
    if solved:
        world.say(
            f"At last, {partner.id} noticed {clue.true_holder} near the wharf gate. "
            f"The missing {case.item} had not been stolen after all; it had been picked up and carried aside in the confusion."
        )
        world.say(
            f"{detective.id} explained the case in a low detective voice, and the {case.item} was handed back at once."
        )
        world.say(case.ending_good)
        owner.memes["relief"] += 1
        detective.memes["pride"] += 1
        partner.memes["joy"] += 1
    else:
        world.say(
            f"When they finally saw {clue.true_holder}, precious minutes had already run ahead of them."
        )
        world.say(
            f"The children reached the wharf too late to put the case right before the singing began."
        )
        world.say(case.ending_bad)
        world.say(
            f"{detective.id} still remembered every clue, but that night the little detectives had to stand and listen to a case they had not solved."
        )
        detective.memes["sadness"] += 1
        partner.memes["sadness"] += 1
        owner.memes["disappointment"] += 1

    outcome = "solved" if solved else "missed"
    world.facts.update(
        detective=detective,
        partner=partner,
        owner=owner,
        crossing=crossing,
        missing=missing,
        case=case,
        clue=clue,
        helper=helper,
        crowd=crowd,
        wrong_turns=wrong_turns,
        repetitions=clue.confusion + 1 + len(wrong_turns),
        total_delay=total_delay(case.id, clue.id, helper.id, crowd.id),
        deadline=case.deadline,
        outcome=outcome,
        solved=solved,
    )
    return world


KNOWLEDGE = {
    "tobacco": [
        (
            "What is tobacco?",
            "Tobacco is a plant that people dry and use in cigarettes, cigars, or pipes. It has a strong smell, and breathing its smoke is unhealthy."
        )
    ],
    "wharf": [
        (
            "What is a wharf?",
            "A wharf is a place by the water where boats stop and people load or unload things. It is often busy with ropes, crates, and workers."
        )
    ],
    "chorus": [
        (
            "What is a chorus?",
            "A chorus is a group of people singing together. They try to start and stop at the same time so the song sounds like one big voice."
        )
    ],
    "crossing_guard": [
        (
            "What does a crossing guard do?",
            "A crossing guard helps people cross the street safely. They watch the traffic and stop it when it is safe to let walkers go."
        )
    ],
    "signal": [
        (
            "Why should you wait for the walk signal?",
            "The walk signal tells you when it is your turn to cross. Waiting helps you cross when cars are supposed to stay stopped."
        )
    ],
    "bridge": [
        (
            "Why can a footbridge be safer than running through traffic?",
            "A footbridge takes people above the road, away from moving cars and buses. It may be slower, but it keeps the crossing safer."
        )
    ],
    "traffic": [
        (
            "Why is a busy street crossing dangerous?",
            "A busy street crossing has many moving vehicles and many people trying to get through at once. That makes it easy to make a mistake if you rush."
        )
    ],
}
KNOWLEDGE_ORDER = ["tobacco", "wharf", "chorus", "traffic", "crossing_guard", "signal", "bridge"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    case = f["case"]
    clue = f["clue"]
    helper = f["helper"]
    crowd = f["crowd"]
    detective = f["detective"]
    partner = f["partner"]
    outcome = f["outcome"]
    ending = "bad ending" if outcome == "missed" else "detective success ending"
    return [
        f'Write a child-facing detective story set at a busy street crossing by a wharf. Include the words "tobacco", "wharf", and "chorus".',
        f"Tell a small mystery where {detective.id} and {partner.id} try to recover {case.item_phrase} by following {clue.label} through {crowd.label}, using repetition and ending with a {ending}.",
        f"Write a detective tale in which children solve a case without running into traffic, using {helper.label} while the wharf chorus waits.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    partner = f["partner"]
    case = f["case"]
    clue = f["clue"]
    helper = f["helper"]
    crowd = f["crowd"]
    wrong_turns = f["wrong_turns"]
    qa: list[tuple[str, str]] = [
        (
            "Who are the detectives in the story?",
            f"The detectives are {detective.id} and {partner.id}. They treat the busy street crossing like a real case scene and try to help the wharf chorus."
        ),
        (
            "What was missing?",
            f"The missing thing was {case.item_phrase}. The chorus needed it before the singing began, which is why the case felt urgent."
        ),
        (
            "What clue did the children follow?",
            f"They followed a tobacco clue: {clue.smell_line[0].lower() + clue.smell_line[1:]} The smell pointed them toward the wharf side of the crossing."
        ),
        (
            "Why did the story repeat the line about the curb first?",
            f'The children kept saying "Clue first, curb first" to remind themselves not to rush into the road. The repeated line shows that safety stayed part of the detective work every time they had to cross or wait.'
        ),
        (
            "How did they cross the street?",
            f"They used {helper.label}. That mattered because the crossing was full of {crowd.label}, so they needed a safe way to get across."
        ),
    ]
    if wrong_turns:
        qa.append(
            (
                "Why did the detectives lose time?",
                f"They lost time because the tobacco clue was hard to read and led them after {', '.join(wrong_turns)} before they found the real lead. Each wrong turn cost minutes while the chorus deadline kept getting closer."
            )
        )
    if f["outcome"] == "solved":
        qa.append(
            (
                "How did the case end?",
                f"The case ended well: the children found the missing {case.item} in time and returned it before the chorus began properly. Their careful crossing plan let them investigate without getting hurt."
            )
        )
    else:
        qa.append(
            (
                "How did the case end?",
                f"The case ended badly for that evening because the children reached the wharf too late to fix the problem before the singing began. Nobody was hurt, but the chorus had to begin without {case.item_phrase}, so the detectives felt sad and disappointed."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"tobacco", "wharf", "chorus", "traffic"}
    helper = f["helper"]
    if "crossing_guard" in helper.tags:
        tags.add("crossing_guard")
    if "signal" in helper.tags:
        tags.add("signal")
    if "bridge" in helper.tags:
        tags.add("bridge")
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} delay={world.facts.get('total_delay')} deadline={world.facts.get('deadline')}")
    return "\n".join(lines)


ASP_RULES = r"""
sensible(H) :- helper(H), sense(H, S), sense_min(M), S >= M.
valid(Case, Clue, Helper, Crowd) :-
    case(Case), clue(Clue), helper(Helper), crowd(Crowd),
    sensible(Helper), capacity(Helper, Cap), risk(Crowd, R), Cap >= R.

total_delay(Case, Clue, Helper, Crowd, D) :-
    valid(Case, Clue, Helper, Crowd),
    confusion(Clue, C), helper_delay(Helper, H), crowd_wait(Crowd, W),
    D = C + H + W.

outcome(Case, Clue, Helper, Crowd, solved) :-
    valid(Case, Clue, Helper, Crowd),
    total_delay(Case, Clue, Helper, Crowd, D),
    deadline(Case, Lim), D <= Lim.

outcome(Case, Clue, Helper, Crowd, missed) :-
    valid(Case, Clue, Helper, Crowd),
    total_delay(Case, Clue, Helper, Crowd, D),
    deadline(Case, Lim), D > Lim.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for case_id, case in CASES.items():
        lines.append(asp.fact("case", case_id))
        lines.append(asp.fact("deadline", case_id, case.deadline))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        lines.append(asp.fact("confusion", clue_id, clue.confusion))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("capacity", helper_id, helper.capacity))
        lines.append(asp.fact("helper_delay", helper_id, helper.delay))
        lines.append(asp.fact("sense", helper_id, helper.sense))
    for crowd_id, crowd in CROWDS.items():
        lines.append(asp.fact("crowd", crowd_id))
        lines.append(asp.fact("risk", crowd_id, crowd.risk))
        lines.append(asp.fact("crowd_wait", crowd_id, crowd.wait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_safe_helpers() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(h for (h,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_case", params.case_id),
        asp.fact("chosen_clue", params.clue_id),
        asp.fact("chosen_helper", params.helper_id),
        asp.fact("chosen_crowd", params.crowd_id),
        "picked(Outcome) :- chosen_case(C), chosen_clue(L), chosen_helper(H), chosen_crowd(R), outcome(C, L, H, R, Outcome).",
    ])
    model = asp.one_model(asp_program(extra, "#show picked/1."))
    atoms = asp.atoms(model, "picked")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        if asp_valid - py_valid:
            print("  only in ASP:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in Python:", sorted(py_valid - asp_valid))

    py_helpers = {h.id for h in safe_helpers()}
    asp_helpers = set(asp_safe_helpers())
    if py_helpers == asp_helpers:
        print(f"OK: sensible helpers match ({sorted(py_helpers)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible helpers: asp={sorted(asp_helpers)} python={sorted(py_helpers)}")

    checked = 0
    for params in CURATED:
        if asp_outcome(params) != outcome_of(params):
            rc = 1
            print(f"MISMATCH in curated outcome: {params}")
        checked += 1

    for seed in range(40):
        rng = random.Random(seed)
        args = build_parser().parse_args([])
        try:
            params = resolve_params(args, rng)
        except StoryError:
            continue
        if asp_outcome(params) != outcome_of(params):
            rc = 1
            print(f"MISMATCH in sampled outcome: {params}")
        checked += 1

    if rc == 0:
        print(f"OK: outcome model matches Python on {checked} scenarios.")

    try:
        sample = generate(CURATED[0])
        if not sample.story or "wharf" not in sample.story or "tobacco" not in sample.story or "chorus" not in sample.story:
            raise StoryError("smoke test story missing required seed words or text")
        buf = io.StringIO()
        stdout = sys.stdout
        try:
            sys.stdout = buf
            emit(sample, trace=True, qa=True, header="### smoke test")
        finally:
            sys.stdout = stdout
        if not buf.getvalue().strip():
            raise StoryError("emit() produced no output in smoke test")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        rc = 1

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Detective storyworld at a busy street crossing by the wharf. "
                    "Unspecified choices are randomized in a reasonableness-checked way."
    )
    ap.add_argument("--case", dest="case_id", choices=CASES)
    ap.add_argument("--clue", dest="clue_id", choices=CLUES)
    ap.add_argument("--helper", dest="helper_id", choices=HELPERS)
    ap.add_argument("--crowd", dest="crowd_id", choices=CROWDS)
    ap.add_argument("--detective-name")
    ap.add_argument("--partner-name")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--partner-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.helper_id and args.crowd_id and not valid_combo(
        args.case_id or next(iter(CASES)),
        args.clue_id or next(iter(CLUES)),
        args.helper_id,
        args.crowd_id,
    ):
        raise StoryError(explain_rejection(args.helper_id, args.crowd_id))
    if args.helper_id and HELPERS[args.helper_id].sense < SENSE_MIN:
        raise StoryError(explain_rejection(args.helper_id, args.crowd_id or next(iter(CROWDS))))

    combos = [
        combo for combo in valid_combos()
        if (args.case_id is None or combo[0] == args.case_id)
        and (args.clue_id is None or combo[1] == args.clue_id)
        and (args.helper_id is None or combo[2] == args.helper_id)
        and (args.crowd_id is None or combo[3] == args.crowd_id)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    case_id, clue_id, helper_id, crowd_id = rng.choice(sorted(combos))

    detective_gender = args.detective_gender or rng.choice(["girl", "boy"])
    partner_gender = args.partner_gender or rng.choice(["girl", "boy"])
    detective_name = args.detective_name or _pick_name(rng, detective_gender)
    partner_name = args.partner_name or _pick_name(rng, partner_gender, avoid=detective_name)
    detective_trait = rng.choice(TRAITS)
    partner_trait = rng.choice([t for t in TRAITS if t != detective_trait] or TRAITS)

    return StoryParams(
        case_id=case_id,
        clue_id=clue_id,
        helper_id=helper_id,
        crowd_id=crowd_id,
        detective_name=detective_name,
        detective_gender=detective_gender,
        partner_name=partner_name,
        partner_gender=partner_gender,
        detective_trait=detective_trait,
        partner_trait=partner_trait,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.case_id not in CASES:
        raise StoryError(f"(Unknown case: {params.case_id})")
    if params.clue_id not in CLUES:
        raise StoryError(f"(Unknown clue: {params.clue_id})")
    if params.helper_id not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper_id})")
    if params.crowd_id not in CROWDS:
        raise StoryError(f"(Unknown crowd: {params.crowd_id})")
    if not valid_combo(params.case_id, params.clue_id, params.helper_id, params.crowd_id):
        raise StoryError(explain_rejection(params.helper_id, params.crowd_id))

    world = tell(
        case=CASES[params.case_id],
        clue=CLUES[params.clue_id],
        helper=HELPERS[params.helper_id],
        crowd=CROWDS[params.crowd_id],
        detective_name=params.detective_name,
        detective_gender=params.detective_gender,
        partner_name=params.partner_name,
        partner_gender=params.partner_gender,
        detective_trait=params.detective_trait,
        partner_trait=params.partner_trait,
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
        print(asp_program("", "#show sensible/1.\n#show valid/4."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        helpers = ", ".join(asp_safe_helpers())
        print(f"sensible helpers: {helpers}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (case, clue, helper, crowd) combos:\n")
        for case_id, clue_id, helper_id, crowd_id in combos:
            print(f"  {case_id:8} {clue_id:14} {helper_id:14} {crowd_id}")
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
            header = f"### {p.detective_name} & {p.partner_name}: {p.case_id}, {p.clue_id}, {p.helper_id}, {outcome_of(p)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
