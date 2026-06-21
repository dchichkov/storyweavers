#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/surgical_organ_quest_moral_value_fairy_tale.py
=========================================================================

A small fairy-tale story world about a child healer sent on a quest for the
right herb before a careful surgical repair can begin. The child must carry a
moral value into the woods, cross one real obstacle with the proper tool, and
return in time to help a sick creature whose heart, lung, or stomach needs care.

The world is intentionally narrow. A story is only valid when the chosen aid
can truly solve the chosen obstacle. The ending is then driven by urgency,
travel difficulty, and the extra help earned by the hero's virtue.

Run it
------
    python storyworlds/worlds/gpt-5.4/surgical_organ_quest_moral_value_fairy_tale.py
    python storyworlds/worlds/gpt-5.4/surgical_organ_quest_moral_value_fairy_tale.py --case heart --obstacle brook --aid boat
    python storyworlds/worlds/gpt-5.4/surgical_organ_quest_moral_value_fairy_tale.py --obstacle dark_cave --aid gloves
    python storyworlds/worlds/gpt-5.4/surgical_organ_quest_moral_value_fairy_tale.py --all
    python storyworlds/worlds/gpt-5.4/surgical_organ_quest_moral_value_fairy_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/surgical_organ_quest_moral_value_fairy_tale.py --trace
    python storyworlds/worlds/gpt-5.4/surgical_organ_quest_moral_value_fairy_tale.py --verify
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
        female = {"girl", "mother", "woman", "queen"}
        male = {"boy", "father", "man", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father"}.get(self.type, self.type)


@dataclass
class PatientCase:
    id: str
    patient_label: str
    patient_kind: str
    organ: str
    symptom: str
    herb: str
    herb_place: str
    treatment: str
    urgency: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    need: str
    difficulty: int
    sight: str
    crossing: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    handles: set[str] = field(default_factory=set)
    power: int = 0
    use_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Virtue:
    id: str
    label: str
    bonus: int
    scene: str
    reward: str
    lesson: str
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


def obstacle_solved(obstacle: Obstacle, aid: Aid) -> bool:
    return obstacle.need in aid.handles


def travel_score(case: PatientCase, obstacle: Obstacle, aid: Aid, virtue: Virtue) -> int:
    return 1 + aid.power + virtue.bonus - obstacle.difficulty - case.urgency


def outcome_of(params: "StoryParams") -> str:
    if params.case not in CASES or params.obstacle not in OBSTACLES or params.aid not in AIDS or params.virtue not in VIRTUES:
        raise StoryError("(Invalid parameters: one or more ids are not known to this story world.)")
    case = CASES[params.case]
    obstacle = OBSTACLES[params.obstacle]
    aid = AIDS[params.aid]
    virtue = VIRTUES[params.virtue]
    if not obstacle_solved(obstacle, aid):
        raise StoryError(explain_rejection(obstacle, aid))
    return "swift" if travel_score(case, obstacle, aid, virtue) >= 0 else "slow"


def introduce(world: World, hero: Entity, mentor: Entity, case: PatientCase, patient: Entity) -> None:
    patient.meters["pain"] = float(case.urgency + 1)
    patient.memes["fear"] = 1.0
    hero.memes["care"] = 1.0
    hero.memes["fear"] = 1.0
    world.say(
        f"Once, in a valley where bells of blue flowers rang softly in the wind, "
        f"there lived {hero.id}, a young healer with a brave satchel and kind hands."
    )
    world.say(
        f"One dawn, {mentor.id}, the village surgeon, knelt beside {case.patient_label}. "
        f'"This little one\'s {case.organ} is hurting," {mentor.pronoun()} said. '
        f'"An {case.organ} is a body organ, and I must do careful surgical work to help."'
    )
    world.say(
        f"{case.patient_label.capitalize()} {case.symptom}, and even the kettle seemed to hush."
    )
    world.say(
        f'"To begin {case.treatment}, I need {case.herb} from {case.herb_place}," '
        f"{mentor.id} said. \"Will you go on this quest for me?\""
    )
    world.say(
        f'"I will," said {hero.id}, though {hero.pronoun("possessive")} heart gave one small thump of fear.'
    )


def set_out(world: World, hero: Entity, case: PatientCase, obstacle: Obstacle, aid: Aid) -> None:
    hero.meters["distance"] += 1
    world.para()
    world.say(
        f"So {hero.id} set out toward {case.herb_place} with {aid.label} and a promise to hurry."
    )
    world.say(
        f"Soon {hero.pronoun()} came to {obstacle.label}, where {obstacle.sight}."
    )


def virtue_scene(world: World, hero: Entity, virtue: Virtue) -> None:
    world.say(virtue.scene.replace("{hero}", hero.id))
    hero.memes["virtue"] += 1
    hero.memes["hope"] += 1
    hero.attrs["virtue_reward"] = virtue.reward
    world.say(virtue.reward.replace("{hero}", hero.id))


def cross_obstacle(world: World, hero: Entity, obstacle: Obstacle, aid: Aid) -> None:
    hero.meters["distance"] += 1
    hero.meters["effort"] += float(max(1, obstacle.difficulty))
    world.para()
    world.say(
        f"Then {hero.id} remembered {aid.label}. {aid.use_text}"
    )
    world.say(
        obstacle.crossing.replace("{hero}", hero.id)
    )


def gather_herb(world: World, hero: Entity, case: PatientCase) -> None:
    hero.attrs["has_herb"] = case.herb
    hero.meters["distance"] += 1
    world.para()
    world.say(
        f"Beyond the trouble lay {case.herb_place}, silvered with dew. There {hero.id} found {case.herb}, "
        f"glowing as if a star had hidden in the leaves."
    )
    world.say(
        f"{hero.pronoun().capitalize()} wrapped the herb gently in a clean cloth and ran home as fast as the path allowed."
    )


def heal_swift(world: World, hero: Entity, mentor: Entity, case: PatientCase, patient: Entity) -> None:
    patient.meters["pain"] = 0.0
    patient.memes["fear"] = 0.0
    patient.memes["relief"] = 1.0
    hero.memes["relief"] = 1.0
    hero.memes["joy"] = 1.0
    world.para()
    world.say(
        f"{hero.id} reached the cottage while the sun was still pale gold. "
        f"{mentor.id} smiled at once and used {case.herb} to begin {case.treatment}."
    )
    world.say(
        f"The careful surgical work was quiet and sure. Before long, {case.patient_label} lifted {patient.pronoun('possessive')} head, "
        f"breathed easier, and looked at {hero.id} with bright, thankful eyes."
    )


def heal_slow(world: World, hero: Entity, mentor: Entity, case: PatientCase, patient: Entity) -> None:
    patient.meters["pain"] = 1.0
    patient.memes["fear"] = 0.0
    patient.memes["relief"] = 1.0
    hero.memes["relief"] = 1.0
    hero.memes["joy"] = 1.0
    world.para()
    world.say(
        f"When {hero.id} returned, the cottage lamps were already glowing. "
        f"{mentor.id} still used {case.herb} to begin {case.treatment}, but {case.patient_label} had grown very tired while waiting."
    )
    world.say(
        f"The careful surgical work still helped, and by bedtime the little patient was safe. "
        f"Yet {patient.pronoun()} would need extra rest, warm broth, and many soft blankets before feeling strong again."
    )


def moral_close(world: World, hero: Entity, virtue: Virtue, patient: Entity) -> None:
    hero.memes["lesson"] = 1.0
    patient.memes["trust"] = 1.0
    world.say(
        f"That night, the village spoke of more than herbs and skill. They spoke of {virtue.label}, "
        f"for {virtue.lesson}"
    )
    world.say(
        f"And from then on, whenever {patient.label} heard {hero.id}'s footsteps by the gate, "
        f"{patient.pronoun()} no longer trembled, but waited with a peaceful face."
    )


def tell(
    *,
    case: PatientCase,
    obstacle: Obstacle,
    aid: Aid,
    virtue: Virtue,
    hero_name: str,
    hero_gender: str,
    mentor_type: str,
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero", label=hero_name))
    mentor_name = "Mira" if mentor_type == "mother" else "Rowan"
    mentor = world.add(Entity(id=mentor_name, kind="character", type=mentor_type, role="mentor", label="the surgeon"))
    patient = world.add(Entity(id="patient", kind="character", type=case.patient_kind, role="patient", label=case.patient_label))
    herb = world.add(Entity(id="herb", kind="thing", type="herb", label=case.herb))
    tool = world.add(Entity(id="aid", kind="thing", type="aid", label=aid.label))

    introduce(world, hero, mentor, case, patient)
    set_out(world, hero, case, obstacle, aid)
    virtue_scene(world, hero, virtue)
    cross_obstacle(world, hero, obstacle, aid)
    gather_herb(world, hero, case)

    outcome = "swift" if travel_score(case, obstacle, aid, virtue) >= 0 else "slow"
    if outcome == "swift":
        heal_swift(world, hero, mentor, case, patient)
    else:
        heal_slow(world, hero, mentor, case, patient)
    moral_close(world, hero, virtue, patient)

    world.facts.update(
        hero=hero,
        mentor=mentor,
        patient=patient,
        case=case,
        obstacle=obstacle,
        aid=aid,
        virtue=virtue,
        herb=herb,
        tool=tool,
        outcome=outcome,
        has_herb=hero.attrs.get("has_herb") == case.herb,
        travel_score=travel_score(case, obstacle, aid, virtue),
    )
    return world


CASES = {
    "heart": PatientCase(
        id="heart",
        patient_label="a fox cub",
        patient_kind="creature",
        organ="heart",
        symptom="lay still while its heart fluttered like a frightened moth",
        herb="starleaf",
        herb_place="the Moonwell Hill",
        treatment="a tiny stitch beside the trembling heart",
        urgency=2,
        tags={"heart", "organ", "surgical", "herb"},
    ),
    "lung": PatientCase(
        id="lung",
        patient_label="a swan child",
        patient_kind="creature",
        organ="lung",
        symptom="gave a small wheeze between each breath",
        herb="mistmint",
        herb_place="the Reedglass Mere",
        treatment="a careful draining around the sore lung",
        urgency=1,
        tags={"lung", "organ", "surgical", "herb"},
    ),
    "stomach": PatientCase(
        id="stomach",
        patient_label="a bear cub",
        patient_kind="creature",
        organ="stomach",
        symptom="curled up with a stomach knotted hard as rope",
        herb="gold fennel",
        herb_place="the Sunny Hollow",
        treatment="a gentle opening and mending near the cramped stomach",
        urgency=1,
        tags={"stomach", "organ", "surgical", "herb"},
    ),
}

OBSTACLES = {
    "brook": Obstacle(
        id="brook",
        label="a bright brook",
        need="float",
        difficulty=1,
        sight="the stepping stones had sunk under the fast water",
        crossing="{hero} crossed without losing a single leaf of the precious bundle.",
        tags={"water", "brook"},
    ),
    "thorn_gate": Obstacle(
        id="thorn_gate",
        label="the Thorn Gate",
        need="grip",
        difficulty=2,
        sight="black briars braided together, each hook sharp as a kitten's claw",
        crossing="{hero} parted the briars, found the old hidden path, and slipped through with only a scratch on one sleeve.",
        tags={"thorns"},
    ),
    "dark_cave": Obstacle(
        id="dark_cave",
        label="the Hollow Cave",
        need="light",
        difficulty=2,
        sight="the cave mouth yawned open, and the path inside could not be trusted in the dark",
        crossing="{hero} walked carefully through the cave until a round patch of daylight appeared at the far end.",
        tags={"cave", "dark"},
    ),
}

AIDS = {
    "boat": Aid(
        id="boat",
        label="a little reed boat",
        handles={"float"},
        power=1,
        use_text="It bobbed gently on the water, and soon the child was paddling over the shining current.",
        tags={"boat", "water"},
    ),
    "gloves": Aid(
        id="gloves",
        label="a pair of moon-silk gloves",
        handles={"grip"},
        power=2,
        use_text="The soft gloves turned the hooks of the thorns aside and kept small fingers safe.",
        tags={"gloves", "thorns"},
    ),
    "lantern": Aid(
        id="lantern",
        label="a firefly lantern",
        handles={"light"},
        power=2,
        use_text="Warm green light spread in a little circle and showed every bend of the stony floor.",
        tags={"lantern", "dark"},
    ),
}

VIRTUES = {
    "honesty": Virtue(
        id="honesty",
        label="honesty",
        bonus=1,
        scene="{hero} met a gate-sprite searching the grass for a lost silver key. Though in a hurry, the child admitted, \"I saw it glint near the roots,\" and told the truth at once.",
        reward="The grateful sprite bowed and said, \"Because you spoke plainly, {hero}, take my quick-path blessing.\"",
        lesson="truth spoken quickly can carry help faster than clever pretending",
        tags={"honesty", "moral"},
    ),
    "kindness": Virtue(
        id="kindness",
        label="kindness",
        bonus=1,
        scene="{hero} found a beetle upside down on the path, kicking at the air. The child set it gently back on its feet instead of hurrying past.",
        reward="The beetle clicked its thanks and showed {hero} a smooth side path hidden under fern fronds.",
        lesson="a kind pause can save time in a deeper way, because help often comes back with small shining feet",
        tags={"kindness", "moral"},
    ),
    "patience": Virtue(
        id="patience",
        label="patience",
        bonus=1,
        scene="{hero} reached a place where the path seemed to split in three. Instead of dashing blindly ahead, the child stood still and waited for the wind to settle the hanging moss.",
        reward="When the leaves stopped rustling, the true trail showed itself, clear as a ribbon. \"Slow eyes can be wise eyes,\" {hero} whispered.",
        lesson="patient hearts do not always move slow; sometimes they keep a quest from going wrong",
        tags={"patience", "moral"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Elsie", "Nora", "Wren", "Ivy", "Tessa", "May"]
BOY_NAMES = ["Finn", "Alder", "Rowan", "Leo", "Tobin", "Milo", "Jory", "Bram"]


@dataclass
class StoryParams:
    case: str
    obstacle: str
    aid: str
    virtue: str
    hero_name: str
    hero_gender: str
    mentor_type: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        case="heart",
        obstacle="brook",
        aid="boat",
        virtue="honesty",
        hero_name="Lina",
        hero_gender="girl",
        mentor_type="mother",
    ),
    StoryParams(
        case="lung",
        obstacle="dark_cave",
        aid="lantern",
        virtue="kindness",
        hero_name="Finn",
        hero_gender="boy",
        mentor_type="father",
    ),
    StoryParams(
        case="stomach",
        obstacle="thorn_gate",
        aid="gloves",
        virtue="patience",
        hero_name="Ivy",
        hero_gender="girl",
        mentor_type="mother",
    ),
    StoryParams(
        case="heart",
        obstacle="thorn_gate",
        aid="gloves",
        virtue="kindness",
        hero_name="Bram",
        hero_gender="boy",
        mentor_type="father",
    ),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for case_id in CASES:
        for obstacle_id, obstacle in OBSTACLES.items():
            for aid_id, aid in AIDS.items():
                if obstacle_solved(obstacle, aid):
                    combos.append((case_id, obstacle_id, aid_id))
    return combos


def explain_rejection(obstacle: Obstacle, aid: Aid) -> str:
    return (
        f"(No story: {aid.label} cannot solve {obstacle.label}. "
        f"This obstacle needs something that can {obstacle.need}, so pick a matching aid.)"
    )


def generation_prompts(world: World) -> list[str]:
    case = world.facts["case"]
    obstacle = world.facts["obstacle"]
    virtue = world.facts["virtue"]
    hero = world.facts["hero"]
    outcome = world.facts["outcome"]
    ending = "returns in time for a bright recovery" if outcome == "swift" else "returns late, so recovery is slower but still hopeful"
    return [
        f'Write a fairy-tale quest for ages 3 to 5 that includes the words "surgical" and "organ".',
        f"Tell a gentle fairy tale about a young healer named {hero.id} who must fetch {case.herb} for a patient whose {case.organ} needs help, while crossing {obstacle.label} with {world.facts['aid'].label}.",
        f"Write a moral story where {virtue.label} matters during a quest, and the child {ending}.",
    ]


def pair_case_answer(case: PatientCase) -> str:
    return (
        f"The patient was {case.patient_label}, and the hurting organ was the {case.organ}. "
        f"The quest mattered because the surgeon needed {case.herb} before beginning {case.treatment}."
    )


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    mentor = world.facts["mentor"]
    patient = world.facts["patient"]
    case = world.facts["case"]
    obstacle = world.facts["obstacle"]
    aid = world.facts["aid"]
    virtue = world.facts["virtue"]
    outcome = world.facts["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a young healer, {mentor.id} the village surgeon, and {case.patient_label} who needed help. "
            f"The whole story begins because someone small is sick and the grown-up healer cannot finish the cure alone."
        ),
        (
            "Why did the quest begin?",
            pair_case_answer(case),
        ),
        (
            f"What stood in {hero.id}'s way, and how was it crossed?",
            f"{obstacle.label.capitalize()} blocked the path. {hero.id} used {aid.label}, because that tool could truly solve the problem, and that is how the child reached {case.herb_place}."
        ),
        (
            f"How did {virtue.label} help on the journey?",
            f"{virtue.label.capitalize()} helped because {hero.id} earned extra help instead of rushing in a foolish way. "
            f"{virtue.lesson[0].upper()}{virtue.lesson[1:]}."
        ),
    ]
    if outcome == "swift":
        qa.append(
            (
                "How did the story end?",
                f"{hero.id} came back in time, and the surgeon used {case.herb} for careful surgical work. "
                f"By the end, {patient.label} felt better and looked peaceful instead of frightened."
            )
        )
    else:
        qa.append(
            (
                "How did the story end?",
                f"{hero.id} returned a little late, so the cure took longer and the patient still needed rest. "
                f"But the herb arrived, the surgical mending began, and the ending stayed hopeful because the little one was safe."
            )
        )
    return qa


KNOWLEDGE = {
    "organ": [
        (
            "What is an organ?",
            "An organ is a body part inside you that has a special job, like a heart that beats or lungs that help you breathe."
        )
    ],
    "surgical": [
        (
            "What does surgical mean?",
            "Surgical means using careful doctor tools and very steady hands to fix a hurt part of a body."
        )
    ],
    "heart": [
        (
            "What does a heart do?",
            "A heart pumps blood around the body. That is why a hurt heart needs quick and careful help."
        )
    ],
    "lung": [
        (
            "What do lungs do?",
            "Lungs help you breathe air in and out. When they hurt, breathing can feel hard or noisy."
        )
    ],
    "stomach": [
        (
            "What does a stomach do?",
            "A stomach helps your body break down food after you eat. If it hurts, a tummy can feel tight or sore."
        )
    ],
    "boat": [
        (
            "What is a boat for?",
            "A boat helps someone float across water instead of getting swept in."
        )
    ],
    "lantern": [
        (
            "Why is a lantern useful in the dark?",
            "A lantern makes light, so you can see where to put your feet and where the safe path goes."
        )
    ],
    "gloves": [
        (
            "Why do gloves help with thorns?",
            "Gloves cover your hands and give you safer grip, so sharp thorns do not scratch your skin as easily."
        )
    ],
    "honesty": [
        (
            "Why is honesty a good value?",
            "Honesty helps other people trust you. Telling the truth can bring the right help at the right time."
        )
    ],
    "kindness": [
        (
            "Why is kindness a good value?",
            "Kindness helps small hurts grow smaller. When you help others, they often help make the world gentler too."
        )
    ],
    "patience": [
        (
            "Why is patience a good value?",
            "Patience helps you slow down long enough to notice what is true. That can keep you from making a bigger mistake."
        )
    ],
}
KNOWLEDGE_ORDER = ["organ", "surgical", "heart", "lung", "stomach", "boat", "lantern", "gloves", "honesty", "kindness", "patience"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    case = world.facts["case"]
    aid = world.facts["aid"]
    virtue = world.facts["virtue"]
    tags = {"organ", "surgical", case.id, aid.id, virtue.id}
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
        attrs = {k: v for k, v in ent.attrs.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  outcome={world.facts.get('outcome')} travel_score={world.facts.get('travel_score')}")
    return "\n".join(lines)


ASP_RULES = r"""
% valid story ingredients
solves(O, A) :- obstacle(O), aid(A), needs(O, N), handles(A, N).
valid(C, O, A) :- pcase(C), obstacle(O), aid(A), solves(O, A).

% outcome model
score(C, O, A, V, 1 + P + B - D - U) :-
    valid(C, O, A),
    power(A, P),
    bonus(V, B),
    difficulty(O, D),
    urgency(C, U).

outcome(C, O, A, V, swift) :- score(C, O, A, V, S), S >= 0.
outcome(C, O, A, V, slow) :- score(C, O, A, V, S), S < 0.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for case_id, case in CASES.items():
        lines.append(asp.fact("pcase", case_id))
        lines.append(asp.fact("urgency", case_id, case.urgency))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("needs", obstacle_id, obstacle.need))
        lines.append(asp.fact("difficulty", obstacle_id, obstacle.difficulty))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        lines.append(asp.fact("power", aid_id, aid.power))
        for handle in sorted(aid.handles):
            lines.append(asp.fact("handles", aid_id, handle))
    for virtue_id, virtue in VIRTUES.items():
        lines.append(asp.fact("virtue", virtue_id))
        lines.append(asp.fact("bonus", virtue_id, virtue.bonus))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join(
        [
            asp.fact("chosen_case", params.case),
            asp.fact("chosen_obstacle", params.obstacle),
            asp.fact("chosen_aid", params.aid),
            asp.fact("chosen_virtue", params.virtue),
            "selected_outcome(X) :- chosen_case(C), chosen_obstacle(O), chosen_aid(A), chosen_virtue(V), outcome(C,O,A,V,X).",
        ]
    )
    model = asp.one_model(asp_program(extra, "#show selected_outcome/1."))
    atoms = asp.atoms(model, "selected_outcome")
    return atoms[0][0] if atoms else "?"


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

    cases = list(CURATED)
    for idx in range(20):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(idx))
        except StoryError:
            continue
        p.seed = idx
        cases.append(p)

    mismatches = 0
    for params in cases:
        py_out = outcome_of(params)
        asp_out = asp_outcome(params)
        if py_out != asp_out:
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test produced an empty story")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale healer quest: fetch the right herb for careful surgical care of a hurting organ."
    )
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--virtue", choices=VIRTUES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--mentor", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible case/obstacle/aid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.aid:
        obstacle = OBSTACLES[args.obstacle]
        aid = AIDS[args.aid]
        if not obstacle_solved(obstacle, aid):
            raise StoryError(explain_rejection(obstacle, aid))

    combos = [
        combo
        for combo in valid_combos()
        if (args.case is None or combo[0] == args.case)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.aid is None or combo[2] == args.aid)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    case_id, obstacle_id, aid_id = rng.choice(sorted(combos))
    virtue_id = args.virtue or rng.choice(sorted(VIRTUES))
    hero_gender = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    mentor_type = args.mentor or rng.choice(["mother", "father"])
    return StoryParams(
        case=case_id,
        obstacle=obstacle_id,
        aid=aid_id,
        virtue=virtue_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        mentor_type=mentor_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.case not in CASES:
        raise StoryError(f"(Invalid case '{params.case}'.)")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Invalid obstacle '{params.obstacle}'.)")
    if params.aid not in AIDS:
        raise StoryError(f"(Invalid aid '{params.aid}'.)")
    if params.virtue not in VIRTUES:
        raise StoryError(f"(Invalid virtue '{params.virtue}'.)")
    if params.hero_gender not in {"girl", "boy"}:
        raise StoryError(f"(Invalid gender '{params.hero_gender}'.)")
    if params.mentor_type not in {"mother", "father"}:
        raise StoryError(f"(Invalid mentor '{params.mentor_type}'.)")

    case = CASES[params.case]
    obstacle = OBSTACLES[params.obstacle]
    aid = AIDS[params.aid]
    virtue = VIRTUES[params.virtue]
    if not obstacle_solved(obstacle, aid):
        raise StoryError(explain_rejection(obstacle, aid))

    world = tell(
        case=case,
        obstacle=obstacle,
        aid=aid,
        virtue=virtue,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        mentor_type=params.mentor_type,
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
        print(asp_program("", "#show valid/3.\n#show outcome/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (case, obstacle, aid) combos:\n")
        for case_id, obstacle_id, aid_id in combos:
            print(f"  {case_id:8} {obstacle_id:11} {aid_id}")
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
            header = f"### {p.hero_name}: {p.case} via {p.obstacle} with {p.aid} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
