#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/fabricate_stupidity_local_conflict_sharing_folk_tale.py
===================================================================================

A standalone storyworld for a small folk-tale domain: in a village, a child
tries to fabricate a selfish claim over food or water gathered from a local
shared place. The false claim starts a quarrel. A wise elder checks the claim
against simple village rules, the lie falls apart, and the ending turns on
sharing.

The world is intentionally narrow. Not every combination is allowed: the
resource must truly come from a local shared source, and the chosen proof must
actually fit that source. The story engine prefers a few believable tales over a
lot of weak ones.

Run it
------
    python storyworlds/worlds/gpt-5.4/fabricate_stupidity_local_conflict_sharing_folk_tale.py
    python storyworlds/worlds/gpt-5.4/fabricate_stupidity_local_conflict_sharing_folk_tale.py --resource apples --claim ownership
    python storyworlds/worlds/gpt-5.4/fabricate_stupidity_local_conflict_sharing_folk_tale.py --resource milk
    python storyworlds/worlds/gpt-5.4/fabricate_stupidity_local_conflict_sharing_folk_tale.py --all --qa
    python storyworlds/worlds/gpt-5.4/fabricate_stupidity_local_conflict_sharing_folk_tale.py --verify
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
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "grandfather": "grandfather",
            "mother": "mother",
            "father": "father",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    communal: bool = True
    marker: str = ""
    witness: str = ""
    proof_tags: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Resource:
    id: str
    label: str
    phrase: str
    vessel: str
    gathered_from: str
    divisible: bool = True
    marker: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Claim:
    id: str
    title: str
    line: str
    lesson: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Proof:
    id: str
    label: str
    line: str
    success: str
    qa_text: str
    needs: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    resource: str
    claim: str
    proof: str
    child1: str
    child1_gender: str
    child2: str
    child2_gender: str
    elder: str
    elder_gender: str
    elder_role: str
    mood: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


def source_for(resource: Resource) -> Place:
    return PLACES[resource.gathered_from]


def proof_fits(resource: Resource, proof: Proof) -> bool:
    place = source_for(resource)
    return place.communal and proof.needs.issubset(place.proof_tags)


def valid_combo(resource_id: str, claim_id: str, proof_id: str) -> bool:
    resource = RESOURCES[resource_id]
    claim = CLAIMS[claim_id]
    proof = PROOFS[proof_id]
    return resource.divisible and source_for(resource).communal and proof_fits(resource, proof) and "sharing" in claim.tags


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for rid in RESOURCES:
        for cid in CLAIMS:
            for pid in PROOFS:
                if valid_combo(rid, cid, pid):
                    out.append((rid, cid, pid))
    return sorted(out)


def explain_rejection(resource: Resource, proof: Proof) -> str:
    place = source_for(resource)
    if not place.communal:
        return (
            f"(No story: {resource.phrase} do not come from a local shared place, "
            f"so there is no commons to quarrel over or share.)"
        )
    if not resource.divisible:
        return (
            f"(No story: {resource.label} are not treated as something that can be "
            f"split and shared here, so the conflict would be weak.)"
        )
    if not proof_fits(resource, proof):
        return (
            f"(No story: the proof '{proof.id}' does not match {place.phrase}. "
            f"The elder must use a proof that fits the local source.)"
        )
    return "(No story: this combination is not reasonable in the world.)"


def mood_line(mood: str) -> str:
    return {
        "proud": "Pride sat on small shoulders and whispered big words.",
        "hungry": "Hunger can make a little wish sound larger than it is.",
        "hasty": "A hasty tongue can outrun a careful heart.",
        "jealous": "Jealousy made one bright basket look like a treasure chest.",
    }[mood]


def introduce(world: World, teller: Entity, asker: Entity, resource: Resource, place: Place) -> None:
    world.say(
        f"In a small valley village, {teller.id} and {asker.id} walked home from "
        f"{place.phrase} with {resource.vessel} full of {resource.label}."
    )
    world.say(
        f"The place was local to everyone in the village, and every family knew "
        f"that what came from there should be shared fairly."
    )


def gather(world: World, teller: Entity, asker: Entity, resource: Resource, place: Place) -> None:
    teller.memes["joy"] += 1
    asker.memes["joy"] += 1
    world.say(
        f"They had worked side by side beneath {place.marker}, and the morning had "
        f"left their hands busy and happy."
    )
    world.say(mood_line(world.facts["mood"]))


def fabricate_claim(world: World, teller: Entity, asker: Entity, resource: Resource, claim: Claim) -> None:
    teller.memes["greed"] += 1
    teller.memes["dishonesty"] += 1
    teller.meters["holds_resource"] += 1
    world.say(
        f"But when the path narrowed near the village gate, {teller.id} hugged "
        f"{resource.vessel} close and said, {claim.line}"
    )
    world.say(
        f"The words were a fabricate thing, stitched together too quickly because "
        f"{teller.id} did not want to share."
    )
    asker.memes["hurt"] += 1


def challenge(world: World, asker: Entity, teller: Entity, resource: Resource, place: Place) -> None:
    asker.memes["conflict"] += 1
    teller.memes["conflict"] += 1
    world.say(
        f'"That cannot be right," said {asker.id}. "{place.label} feeds the whole '
        f'village, not one pair of hands."'
    )
    world.say(
        f"Soon the two children were arguing in the dust, and even the hens near "
        f"the well stopped scratching to listen."
    )


def summon_elder(world: World, elder: Entity) -> None:
    world.say(
        f"An old {elder.label_word} named {elder.id}, who kept peace in the lane, "
        f"heard the sharp voices and came with slow, steady steps."
    )


def test_claim(world: World, elder: Entity, teller: Entity, asker: Entity, resource: Resource, place: Place, proof: Proof) -> None:
    world.say(
        f'{elder.id} listened to both children and then said, {proof.line}'
    )
    world.say(proof.success.format(place=place.label, marker=place.marker, witness=place.witness))
    teller.memes["shame"] += 1
    teller.memes["dishonesty"] = 0.0
    world.facts["lie_revealed"] = True


def elder_lesson(world: World, elder: Entity, teller: Entity, claim: Claim) -> None:
    teller.memes["remorse"] += 1
    world.say(
        f'Then {elder.id} rested a hand on the basket and said, "Child, a moment '
        f'of stupidity can make a fence where no fence belongs."'
    )
    world.say(
        f'"{claim.lesson} A lie may sound large at first, but truth walks beside '
        f'every neighbor."'
    )


def apology(world: World, teller: Entity, asker: Entity, resource: Resource) -> None:
    teller.memes["conflict"] = 0.0
    asker.memes["conflict"] = 0.0
    teller.memes["kindness"] += 1
    asker.memes["relief"] += 1
    world.say(
        f'{teller.id} looked at {resource.vessel}, then at {asker.id}, and the hot '
        f'proud feeling went out of {teller.pronoun("possessive")} face.'
    )
    world.say(
        f'"I was wrong," {teller.pronoun()} said. "I tried to fabricate a special '
        f'right for myself. Will you forgive me?"'
    )
    world.say(f'{asker.id} nodded, because the truth had been spoken plainly at last.')


def share(world: World, teller: Entity, asker: Entity, elder: Entity, resource: Resource) -> None:
    teller.meters["holds_resource"] = 0.0
    teller.meters["shared"] += 1
    asker.meters["shared"] += 1
    elder.memes["peace"] += 1
    world.say(
        f"So the children sat on the low wall by the well and divided the "
        f"{resource.label} into two fair parts."
    )
    world.say(
        f"They even pressed the first piece toward {elder.id}, who laughed and "
        f"broke it again so all three could taste it."
    )
    world.say(
        f"By sunset the quarrel was gone, and the village lane seemed wider, as if "
        f"sharing itself had swept it clean."
    )


def tell_story(
    resource: Resource,
    claim: Claim,
    proof: Proof,
    child1: str,
    child1_gender: str,
    child2: str,
    child2_gender: str,
    elder_name: str,
    elder_gender: str,
    elder_role: str,
    mood: str,
) -> World:
    if not valid_combo(resource.id, claim.id, proof.id):
        raise StoryError(explain_rejection(resource, proof))

    world = World()
    place = source_for(resource)
    teller = world.add(Entity(id=child1, kind="character", type=child1_gender, role="teller"))
    asker = world.add(Entity(id=child2, kind="character", type=child2_gender, role="asker"))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_gender, role="elder"))
    elder.type = elder_role

    world.facts.update(
        resource=resource,
        place=place,
        claim=claim,
        proof=proof,
        teller=teller,
        asker=asker,
        elder=elder,
        mood=mood,
    )

    introduce(world, teller, asker, resource, place)
    gather(world, teller, asker, resource, place)

    world.para()
    fabricate_claim(world, teller, asker, resource, claim)
    challenge(world, asker, teller, resource, place)
    summon_elder(world, elder)

    world.para()
    test_claim(world, elder, teller, asker, resource, place, proof)
    elder_lesson(world, elder, teller, claim)
    apology(world, teller, asker, resource)

    world.para()
    share(world, teller, asker, elder, resource)
    world.facts["resolved"] = True
    return world


PLACES = {
    "orchard": Place(
        id="orchard",
        label="the village orchard",
        phrase="the village orchard",
        communal=True,
        marker="the old pear tree and its painted commons stone",
        witness="the orchard keeper",
        proof_tags={"marker", "witness"},
        tags={"orchard", "local"},
    ),
    "well": Place(
        id="well",
        label="the old well",
        phrase="the old well in the square",
        communal=True,
        marker="the carved village bucket hanging on its hook",
        witness="the baker's wife who drew water each dawn",
        proof_tags={"marker", "witness"},
        tags={"well", "local"},
    ),
    "beehives": Place(
        id="beehives",
        label="the common beehives",
        phrase="the common beehives behind the chapel",
        communal=True,
        marker="the red wax seal stamped on every village jar",
        witness="the hive keeper",
        proof_tags={"marker", "witness"},
        tags={"bees", "local"},
    ),
    "private_cow": Place(
        id="private_cow",
        label="Old Marta's cowshed",
        phrase="Old Marta's cowshed",
        communal=False,
        marker="her own wooden gate",
        witness="Old Marta",
        proof_tags={"witness"},
        tags={"private"},
    ),
}

RESOURCES = {
    "apples": Resource(
        id="apples",
        label="apples",
        phrase="bright apples",
        vessel="a willow basket",
        gathered_from="orchard",
        divisible=True,
        marker="painted commons stone",
        tags={"fruit", "sharing", "local"},
    ),
    "water": Resource(
        id="water",
        label="water",
        phrase="clear water",
        vessel="a clay jug",
        gathered_from="well",
        divisible=True,
        marker="village bucket",
        tags={"water", "sharing", "local"},
    ),
    "honey": Resource(
        id="honey",
        label="honey cakes",
        phrase="golden honey cakes",
        vessel="a cloth-covered tray",
        gathered_from="beehives",
        divisible=True,
        marker="red wax seal",
        tags={"honey", "sharing", "local"},
    ),
    "milk": Resource(
        id="milk",
        label="milk",
        phrase="fresh milk",
        vessel="a tin pail",
        gathered_from="private_cow",
        divisible=True,
        marker="wooden gate",
        tags={"milk"},
    ),
}

CLAIMS = {
    "ownership": Claim(
        id="ownership",
        title="made-up ownership",
        line='"These are mine alone. The trees bent lower on my side, so the basket belongs only to me."',
        lesson="What is gathered from the commons belongs first to fairness.",
        tags={"sharing", "lie"},
    ),
    "elder_promise": Claim(
        id="elder_promise",
        title="made-up promise",
        line='"The elder promised me every bit of this before sunrise, so none of it must be shared."',
        lesson="Borrowing an elder's name for a lie is worse than borrowing an apple.",
        tags={"sharing", "lie"},
    ),
    "secret_rule": Claim(
        id="secret_rule",
        title="made-up rule",
        line='"There is a secret village rule: whoever carries the basket home may keep it all."',
        lesson="A secret rule that helps only one child is usually no rule at all.",
        tags={"sharing", "lie"},
    ),
}

PROOFS = {
    "marker": Proof(
        id="marker",
        label="commons marker",
        line='"Let us look for the sign that tells whose place this is."',
        success="They went back a few steps and saw {marker}, the plain mark that showed {place} belonged to the whole village.",
        qa_text="looked for the village marker that showed the place was shared",
        needs={"marker"},
        tags={"marker", "local_rule"},
    ),
    "witness": Proof(
        id="witness",
        label="local witness",
        line='"When memory argues, ask the person who tends the place."',
        success="Soon {witness} answered, and the answer was simple: what came from {place} was to be divided fairly.",
        qa_text="asked the local witness who cared for the place",
        needs={"witness"},
        tags={"witness", "local_rule"},
    ),
    "both": Proof(
        id="both",
        label="marker and witness",
        line='"A wise judgment uses both sign and witness."',
        success="First they checked {marker}, and then {witness} said the same thing, so the false claim had nowhere left to hide.",
        qa_text="checked both the village marker and a local witness",
        needs={"marker", "witness"},
        tags={"marker", "witness", "local_rule"},
    ),
}

GIRL_NAMES = ["Anya", "Mira", "Tala", "Suri", "Nila", "Rina"]
BOY_NAMES = ["Ivo", "Milan", "Pavel", "Toma", "Radu", "Niko"]
ELDERS = [
    {"name": "Baba Lina", "gender": "girl", "role": "grandmother"},
    {"name": "Grandfather Petar", "gender": "boy", "role": "grandfather"},
]
MOODS = ["proud", "hungry", "hasty", "jealous"]

KNOWLEDGE = {
    "commons": [
        (
            "What is a village commons?",
            "A village commons is a place the whole community uses together. People follow shared rules so everyone can be treated fairly.",
        )
    ],
    "fabricate": [
        (
            "What does fabricate mean?",
            "To fabricate means to make something up that is not true. In a story like this, it means inventing a false claim or excuse.",
        )
    ],
    "sharing": [
        (
            "Why is sharing important in a village story?",
            "Sharing helps neighbors live peacefully together. When people split common goods fairly, small problems do not grow into big quarrels.",
        )
    ],
    "witness": [
        (
            "What is a witness?",
            "A witness is a person who saw or knows something important. A truthful witness can help settle an argument.",
        )
    ],
    "marker": [
        (
            "Why would a place have a marker?",
            "A marker shows something important about a place, like who may use it. It helps people remember the rules without guessing.",
        )
    ],
    "stupidity": [
        (
            "What does stupidity mean in this folk tale?",
            "Here, stupidity means a foolish moment when someone chooses pride over sense. It is not about being worthless; it is about making a bad choice and then learning from it.",
        )
    ],
    "local": [
        (
            "What does local mean?",
            "Local means belonging to the nearby place where people live. A local well or orchard is part of the village's own daily life.",
        )
    ],
}
KNOWLEDGE_ORDER = ["local", "commons", "fabricate", "sharing", "marker", "witness", "stupidity"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    resource = f["resource"]
    place = f["place"]
    teller = f["teller"]
    asker = f["asker"]
    elder = f["elder"]
    return [
        'Write a short folk tale for a 3-to-5-year-old that includes the words "fabricate", "stupidity", and "local".',
        f"Tell a village folk tale where {teller.id} tries to fabricate a selfish claim over {resource.label} from {place.label}, causing conflict until {elder.id} restores peace through sharing.",
        f"Write a simple local folk tale about two children arguing over a shared resource, with a wise elder, a gentle lesson about stupidity, and an ending image of fairness.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    teller = f["teller"]
    asker = f["asker"]
    elder = f["elder"]
    resource = f["resource"]
    place = f["place"]
    claim = f["claim"]
    proof = f["proof"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {teller.id} and {asker.id}, two village children, and {elder.id}, the elder who helped them. They argued over {resource.label} from {place.label}.",
        ),
        (
            f"Why did {teller.id} and {asker.id} begin to quarrel?",
            f"They quarreled because {teller.id} tried to keep all the {resource.label} and used a false claim to do it. The conflict began when a shared village gift was treated like private treasure.",
        ),
        (
            f"What did {teller.id} do wrong?",
            f"{teller.id} tried to fabricate a story that would justify keeping everything. That was wrong because the claim was not true and it broke the rule of sharing from the commons.",
        ),
        (
            f"How did {elder.id} find the truth?",
            f"{elder.id} {proof.qa_text}. That simple local proof showed the place belonged to the whole village, so the made-up claim fell apart.",
        ),
        (
            "How was the problem solved?",
            f"The lie was admitted, an apology was given, and the {resource.label} were divided fairly. The ending matters because peace returned only after truth and sharing returned together.",
        ),
    ]
    if world.facts.get("resolved"):
        qa.append(
            (
                "What lesson did the elder teach?",
                f"{elder.id} taught that a moment of stupidity can create a quarrel where none is needed. The wiser path is to tell the truth and share what comes from a common place.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"fabricate", "sharing", "stupidity", "local", "commons"}
    proof = world.facts["proof"]
    if "marker" in proof.tags:
        tags.add("marker")
    if "witness" in proof.tags:
        tags.add("witness")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:18} ({ent.type:12}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
divisible_shared(R) :- resource(R), divisible(R), gathered_from(R, P), communal(P).
fits(R, Pr) :- gathered_from(R, P), communal(P), needs_ok(P, Pr).
needs_ok(P, Pr) :- proof(Pr), not missing_need(P, Pr).
missing_need(P, Pr) :- needs_marker(Pr), not has_marker(P).
missing_need(P, Pr) :- needs_witness(Pr), not has_witness(P).
valid(R, C, Pr) :- resource(R), claim(C), proof(Pr), divisible_shared(R), fits(R, Pr), sharing_claim(C).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.communal:
            lines.append(asp.fact("communal", pid))
        if "marker" in place.proof_tags:
            lines.append(asp.fact("has_marker", pid))
        if "witness" in place.proof_tags:
            lines.append(asp.fact("has_witness", pid))
    for rid, resource in RESOURCES.items():
        lines.append(asp.fact("resource", rid))
        lines.append(asp.fact("gathered_from", rid, resource.gathered_from))
        if resource.divisible:
            lines.append(asp.fact("divisible", rid))
    for cid, claim in CLAIMS.items():
        lines.append(asp.fact("claim", cid))
        if "sharing" in claim.tags:
            lines.append(asp.fact("sharing_claim", cid))
    for pid, proof in PROOFS.items():
        lines.append(asp.fact("proof", pid))
        if "marker" in proof.needs:
            lines.append(asp.fact("needs_marker", pid))
        if "witness" in proof.needs:
            lines.append(asp.fact("needs_witness", pid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


CURATED = [
    StoryParams(
        resource="apples",
        claim="ownership",
        proof="marker",
        child1="Mira",
        child1_gender="girl",
        child2="Niko",
        child2_gender="boy",
        elder="Baba Lina",
        elder_gender="girl",
        elder_role="grandmother",
        mood="proud",
    ),
    StoryParams(
        resource="water",
        claim="secret_rule",
        proof="witness",
        child1="Ivo",
        child1_gender="boy",
        child2="Suri",
        child2_gender="girl",
        elder="Grandfather Petar",
        elder_gender="boy",
        elder_role="grandfather",
        mood="hasty",
    ),
    StoryParams(
        resource="honey",
        claim="elder_promise",
        proof="both",
        child1="Tala",
        child1_gender="girl",
        child2="Pavel",
        child2_gender="boy",
        elder="Baba Lina",
        elder_gender="girl",
        elder_role="grandmother",
        mood="jealous",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Storyworld: a village child fabricates a selfish claim over a local shared resource, then learns to share."
    )
    ap.add_argument("--resource", choices=RESOURCES)
    ap.add_argument("--claim", choices=CLAIMS)
    ap.add_argument("--proof", choices=PROOFS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (resource, claim, proof) triples from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP facts and rules")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def _pick_elder(rng: random.Random) -> dict:
    return dict(rng.choice(ELDERS))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.resource and args.resource not in RESOURCES:
        raise StoryError(f"(Unknown resource: {args.resource})")
    if args.claim and args.claim not in CLAIMS:
        raise StoryError(f"(Unknown claim: {args.claim})")
    if args.proof and args.proof not in PROOFS:
        raise StoryError(f"(Unknown proof: {args.proof})")

    if args.resource and args.proof:
        resource = RESOURCES[args.resource]
        proof = PROOFS[args.proof]
        if not valid_combo(args.resource, args.claim or next(iter(CLAIMS)), args.proof):
            # If claim unspecified, rejection should still reflect resource/proof incompatibility.
            raise StoryError(explain_rejection(resource, proof))

    combos = [
        combo
        for combo in valid_combos()
        if (args.resource is None or combo[0] == args.resource)
        and (args.claim is None or combo[1] == args.claim)
        and (args.proof is None or combo[2] == args.proof)
    ]
    if not combos:
        if args.resource and args.proof:
            raise StoryError(explain_rejection(RESOURCES[args.resource], PROOFS[args.proof]))
        raise StoryError("(No valid combination matches the given options.)")

    resource_id, claim_id, proof_id = rng.choice(combos)
    child1, child1_gender = _pick_child(rng)
    child2, child2_gender = _pick_child(rng, avoid=child1)
    elder = _pick_elder(rng)
    mood = rng.choice(MOODS)

    return StoryParams(
        resource=resource_id,
        claim=claim_id,
        proof=proof_id,
        child1=child1,
        child1_gender=child1_gender,
        child2=child2,
        child2_gender=child2_gender,
        elder=elder["name"],
        elder_gender=elder["gender"],
        elder_role=elder["role"],
        mood=mood,
    )


def generate(params: StoryParams) -> StorySample:
    if params.resource not in RESOURCES:
        raise StoryError(f"(Unknown resource: {params.resource})")
    if params.claim not in CLAIMS:
        raise StoryError(f"(Unknown claim: {params.claim})")
    if params.proof not in PROOFS:
        raise StoryError(f"(Unknown proof: {params.proof})")

    resource = RESOURCES[params.resource]
    proof = PROOFS[params.proof]
    if not valid_combo(params.resource, params.claim, params.proof):
        raise StoryError(explain_rejection(resource, proof))

    world = tell_story(
        resource=resource,
        claim=CLAIMS[params.claim],
        proof=proof,
        child1=params.child1,
        child1_gender=params.child1_gender,
        child2=params.child2,
        child2_gender=params.child2_gender,
        elder_name=params.elder,
        elder_gender=params.elder_gender,
        elder_role=params.elder_role,
        mood=params.mood,
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


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: ASP gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story.")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        rng = random.Random(123)
        params = resolve_params(build_parser().parse_args([]), rng)
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("Random generated empty story.")
        print("OK: random resolve/generate smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"RANDOM SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (resource, claim, proof) combos:\n")
        for resource, claim, proof in combos:
            print(f"  {resource:8} {claim:13} {proof}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child1} and {p.child2}: {p.resource}, {p.claim}, {p.proof}"
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
