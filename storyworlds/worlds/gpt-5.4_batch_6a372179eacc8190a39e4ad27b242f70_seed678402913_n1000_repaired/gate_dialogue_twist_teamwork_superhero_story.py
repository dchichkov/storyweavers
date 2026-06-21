#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/gate_dialogue_twist_teamwork_superhero_story.py
===========================================================================

A standalone story world for small superhero stories built around a gate, a
misread mystery, and a teamwork rescue.

Premise
-------
Two children are playing superheroes when they hear a clatter behind a gate.
At first the shape and sounds seem spooky, almost like a villain. Then the
twist lands: the "monster" is only a frightened little creature caught behind
the gate. One child has the right way to open the gate, the other has the right
way to calm the creature, and together they solve the problem.

This world is intentionally narrow and constraint-checked:

* Every gate has a specific opening problem: a high latch, a rusty slide, or a
  looped rope.
* Every creature has a specific calming need: a soft voice, a crunchy snack, or
  slow quiet humming.
* A reasonable story needs both halves of the rescue. The opener must truly fit
  the gate, and the calmer must truly fit the frightened creature.
* The inline ASP twin matches the Python gate and the rescue logic.

Run it
------
    python storyworlds/worlds/gpt-5.4/gate_dialogue_twist_teamwork_superhero_story.py
    python storyworlds/worlds/gpt-5.4/gate_dialogue_twist_teamwork_superhero_story.py --gate school
    python storyworlds/worlds/gpt-5.4/gate_dialogue_twist_teamwork_superhero_story.py --open-skill strength --gate school
    python storyworlds/worlds/gpt-5.4/gate_dialogue_twist_teamwork_superhero_story.py --all
    python storyworlds/worlds/gpt-5.4/gate_dialogue_twist_teamwork_superhero_story.py --qa --json
    python storyworlds/worlds/gpt-5.4/gate_dialogue_twist_teamwork_superhero_story.py --verify
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

# Make the shared result containers importable when this script is run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "lady"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class GateConfig:
    id: str
    place: str
    gate_label: str
    needs_open: str
    problem_line: str
    opening_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class CreatureConfig:
    id: str
    label: str
    article: str
    cry: str
    sound: str
    shadow: str
    twist_line: str
    needs_calm: str
    calm_result: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class OpenSkill:
    id: str
    label: str
    boast: str
    action_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class CalmSkill:
    id: str
    label: str
    boast: str
    action_line: str
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


GATES = {
    "school": GateConfig(
        id="school",
        place="the little school garden",
        gate_label="the tall blue gate",
        needs_open="reach",
        problem_line="The latch sat high above their heads, clicking where small hands could not quite reach.",
        opening_line="reached up to the high latch and flicked it free",
        tags={"gate", "garden", "latch"},
    ),
    "dog_park": GateConfig(
        id="dog_park",
        place="the dog park",
        gate_label="the red park gate",
        needs_open="strength",
        problem_line="The slide bolt had gone stiff and rusty after the wet weather.",
        opening_line="braced both sneakers, pushed hard, and dragged the rusty bolt back",
        tags={"gate", "park", "rust"},
    ),
    "orchard": GateConfig(
        id="orchard",
        place="the tiny orchard",
        gate_label="the wooden orchard gate",
        needs_open="untie",
        problem_line="A rope had been looped around the handle in two tight knots.",
        opening_line="worked quick fingers through the loops and untied the rope",
        tags={"gate", "rope", "orchard"},
    ),
}

CREATURES = {
    "goat": CreatureConfig(
        id="goat",
        label="baby goat",
        article="a baby goat",
        cry="Maa-aah!",
        sound="a wobbling bleat",
        shadow="two pointy shadows that looked like horns on a villain helmet",
        twist_line="Then the shape bounced forward, and they saw the truth: it was only a baby goat with leaves stuck on its little horns.",
        needs_calm="soft_voice",
        calm_result="The baby goat stopped butting the gate and leaned toward the gentle words instead.",
        ending_image="The goat skipped back to its patch of clover, tail twitching like a tiny flag.",
        tags={"animal", "goat", "soft_voice"},
    ),
    "puppy": CreatureConfig(
        id="puppy",
        label="puppy",
        article="a puppy",
        cry="Yip! Yip!",
        sound="a scrappy little bark",
        shadow="a flapping shape that looked like a cape in the wind",
        twist_line="Then the cape-shape tripped over its own paws, and they saw the truth: it was only a puppy tangled in a loose ribbon.",
        needs_calm="snack",
        calm_result="The puppy sniffed the treat, forgot to bark, and wagged so hard its whole back half wriggled.",
        ending_image="The puppy trotted after them with the ribbon gone, carrying a fallen leaf like a medal.",
        tags={"animal", "puppy", "snack"},
    ),
    "duck": CreatureConfig(
        id="duck",
        label="duckling",
        article="a duckling",
        cry="Peep-peep!",
        sound="a frightened peeping sound",
        shadow="a round shadow bobbing so fast it looked like a buzzing gadget",
        twist_line="Then the buzzing shape waddled into a stripe of light, and they saw the truth: it was only a duckling with a burdock burr stuck to its fluff.",
        needs_calm="hum",
        calm_result="The duckling heard the low humming, stopped skittering in circles, and stood still long enough to be helped.",
        ending_image="The duckling paddled after its mother through the puddle by the fence, leaving silver rings behind it.",
        tags={"animal", "duck", "hum"},
    ),
}

OPEN_SKILLS = {
    "reach": OpenSkill(
        id="reach",
        label="Sky-Stretch",
        boast='"I can reach anything way up high,"',
        action_line="stretched up like a tower",
        tags={"reach", "teamwork"},
    ),
    "strength": OpenSkill(
        id="strength",
        label="Thunder-Hands",
        boast='"I can shove the toughest things open,"',
        action_line="set sturdy hands on the gate and pushed with a superhero grunt",
        tags={"strength", "teamwork"},
    ),
    "untie": OpenSkill(
        id="untie",
        label="Knot-Ninja",
        boast='"I can beat even the trickiest loops,"',
        action_line="pinched and teased at the knot with speedy fingers",
        tags={"untie", "teamwork"},
    ),
}

CALM_SKILLS = {
    "soft_voice": CalmSkill(
        id="soft_voice",
        label="Moon-Whisper",
        boast='"I can talk in the calm voice that scared animals trust,"',
        action_line='knelt by the bars and said, "Easy now. We are here to help."',
        tags={"soft_voice", "kindness"},
    ),
    "snack": CalmSkill(
        id="snack",
        label="Pocket-Treat",
        boast='"I packed a crunchy cracker just in case a hero needed one,"',
        action_line="broke a cracker into tiny bits and held one out on a flat palm",
        tags={"snack", "kindness"},
    ),
    "hum": CalmSkill(
        id="hum",
        label="Star-Hum",
        boast='"I know a slow hero hum that makes the world feel less jumpy,"',
        action_line="made a quiet humming sound, soft and steady as a bicycle wheel",
        tags={"hum", "kindness"},
    ),
}

GIRL_NAMES = ["Maya", "Luna", "Ava", "Zoe", "Nora", "Ella", "Ivy", "Ruby"]
BOY_NAMES = ["Leo", "Max", "Sam", "Ben", "Theo", "Eli", "Finn", "Jack"]
TRAITS = ["brave", "quick", "kind", "steady", "clever", "hopeful"]


def can_open(gate_id: str, open_skill_id: str) -> bool:
    return GATES[gate_id].needs_open == open_skill_id


def can_calm(creature_id: str, calm_skill_id: str) -> bool:
    return CREATURES[creature_id].needs_calm == calm_skill_id


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for gate_id, gate in GATES.items():
        for creature_id, creature in CREATURES.items():
            for open_skill_id in OPEN_SKILLS:
                for calm_skill_id in CALM_SKILLS:
                    if gate.needs_open == open_skill_id and creature.needs_calm == calm_skill_id:
                        combos.append((gate_id, creature_id, open_skill_id))
    return sorted(set(combos))


def valid_quads() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for gate_id, gate in GATES.items():
        for creature_id, creature in CREATURES.items():
            for open_skill_id in OPEN_SKILLS:
                for calm_skill_id in CALM_SKILLS:
                    if gate.needs_open == open_skill_id and creature.needs_calm == calm_skill_id:
                        out.append((gate_id, creature_id, open_skill_id, calm_skill_id))
    return sorted(set(out))


@dataclass
class StoryParams:
    gate: str
    creature: str
    open_skill: str
    calm_skill: str
    hero1_name: str
    hero1_gender: str
    hero2_name: str
    hero2_gender: str
    parent: str
    hero1_trait: str
    hero2_trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        gate="school",
        creature="goat",
        open_skill="reach",
        calm_skill="soft_voice",
        hero1_name="Maya",
        hero1_gender="girl",
        hero2_name="Leo",
        hero2_gender="boy",
        parent="mother",
        hero1_trait="quick",
        hero2_trait="kind",
    ),
    StoryParams(
        gate="dog_park",
        creature="puppy",
        open_skill="strength",
        calm_skill="snack",
        hero1_name="Ben",
        hero1_gender="boy",
        hero2_name="Ruby",
        hero2_gender="girl",
        parent="father",
        hero1_trait="brave",
        hero2_trait="steady",
    ),
    StoryParams(
        gate="orchard",
        creature="duck",
        open_skill="untie",
        calm_skill="hum",
        hero1_name="Nora",
        hero1_gender="girl",
        hero2_name="Finn",
        hero2_gender="boy",
        parent="mother",
        hero1_trait="clever",
        hero2_trait="hopeful",
    ),
]


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def explain_gate_rejection(gate_id: str, open_skill_id: str) -> str:
    gate = GATES[gate_id]
    skill = OPEN_SKILLS[open_skill_id]
    return (
        f"(No story: {gate.gate_label} needs a hero who can handle {gate.needs_open}, "
        f"but {skill.label} does not fit that gate problem. The gate has to open in a believable way.)"
    )


def explain_creature_rejection(creature_id: str, calm_skill_id: str) -> str:
    creature = CREATURES[creature_id]
    skill = CALM_SKILLS[calm_skill_id]
    return (
        f"(No story: {creature.article} needs {creature.needs_calm}, "
        f"but {skill.label} would not calm it in this world. The rescue needs a believable second half.)"
    )


def tell(params: StoryParams) -> World:
    gate_cfg = GATES[params.gate]
    creature_cfg = CREATURES[params.creature]
    opener_cfg = OPEN_SKILLS[params.open_skill]
    calmer_cfg = CALM_SKILLS[params.calm_skill]

    world = World()
    hero1 = world.add(Entity(
        id=params.hero1_name,
        kind="character",
        type=params.hero1_gender,
        role="opener",
        attrs={"trait": params.hero1_trait, "alias": opener_cfg.label},
    ))
    hero2 = world.add(Entity(
        id=params.hero2_name,
        kind="character",
        type=params.hero2_gender,
        role="calmer",
        attrs={"trait": params.hero2_trait, "alias": calmer_cfg.label},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent,
        role="adult",
        label="the parent",
    ))
    gate = world.add(Entity(
        id="gate",
        kind="thing",
        type="gate",
        label=gate_cfg.gate_label,
        role="gate",
        attrs={"place": gate_cfg.place, "need": gate_cfg.needs_open},
        tags=set(gate_cfg.tags),
    ))
    creature = world.add(Entity(
        id="creature",
        kind="thing",
        type="animal",
        label=creature_cfg.label,
        role="creature",
        attrs={"need": creature_cfg.needs_calm},
        tags=set(creature_cfg.tags),
    ))

    gate.meters["closed"] = 1.0
    creature.meters["behind_gate"] = 1.0
    creature.memes["fear"] = 1.0
    hero1.memes["joy"] = 1.0
    hero2.memes["joy"] = 1.0

    world.say(
        f"After supper, {hero1.id} and {hero2.id} raced along the path beside {gate_cfg.place} "
        f"with towels tied around their shoulders like superhero capes."
    )
    world.say(
        f"{hero1.id} was {params.hero1_trait}, {hero2.id} was {params.hero2_trait}, "
        f"and tonight they called themselves {opener_cfg.label} and {calmer_cfg.label}."
    )
    world.say(
        f"When they reached {gate_cfg.gate_label}, they heard {creature_cfg.sound} from the other side. "
        f"The slats threw {creature_cfg.shadow} onto the ground."
    )

    world.para()
    hero1.memes["alarm"] += 1.0
    hero2.memes["alarm"] += 1.0
    world.say(
        f'"Did you see that?" whispered {hero1.id}. "Something spooky is hiding behind the gate."'
    )
    world.say(
        f'"Maybe it is a gate villain," {hero2.id} whispered back, though {hero2.pronoun("possessive")} voice shook a tiny bit.'
    )
    world.say(creature_cfg.cry)
    world.say(gate_cfg.problem_line)

    world.para()
    hero1.memes["bravery"] += 1.0
    hero2.memes["bravery"] += 1.0
    world.say(
        f'{hero1.id} puffed up {hero1.pronoun("possessive")} cape. {opener_cfg.boast} {hero1.id} said.'
    )
    world.say(
        f'{hero2.id} nodded. {calmer_cfg.boast} {hero2.id} said.'
    )
    world.say(
        f'"Then we do it together," said {hero1.id}. "{hero1.attrs["alias"]} opens. '
        f'{hero2.attrs["alias"]} calms. Nobody scares the city while we are on watch."'
    )

    world.para()
    world.say(creature_cfg.twist_line)
    hero1.memes["surprise"] += 1.0
    hero2.memes["surprise"] += 1.0
    world.say(
        f'"It is not a villain at all," said {hero2.id}. "It is just {creature_cfg.article}, and it is scared."'
    )

    world.para()
    world.say(
        f"{hero1.id} {opener_cfg.action_line}, and {gate_cfg.opening_line}."
    )
    gate.meters["closed"] = 0.0
    gate.meters["open"] = 1.0
    hero1.meters["helped_open"] = 1.0
    world.say(
        f"At the very same moment, {hero2.id} {calmer_cfg.action_line}"
    )
    creature.memes["fear"] = 0.0
    creature.memes["trust"] += 1.0
    hero2.meters["helped_calm"] = 1.0
    world.say(creature_cfg.calm_result)

    world.para()
    creature.meters["behind_gate"] = 0.0
    creature.meters["safe"] = 1.0
    hero1.memes["relief"] += 1.0
    hero2.memes["relief"] += 1.0
    hero1.memes["teamwork"] += 1.0
    hero2.memes["teamwork"] += 1.0
    world.say(
        f"The gate swung open at last. {creature_cfg.article.capitalize()} hurried out, brushed past their capes, and was safe."
    )
    world.say(
        f"{parent.label_word.capitalize()} had been coming down the path with a flashlight and stopped to smile. "
        f'"Real heroes look first, think next, and help together," {parent.pronoun()} said.'
    )
    world.say(
        f"{hero1.id} and {hero2.id} grinned at each other. The mystery at the gate had turned into a rescue, "
        f"and the rescue had worked because neither hero tried to do every part alone."
    )
    world.say(creature_cfg.ending_image)

    world.facts.update(
        gate_cfg=gate_cfg,
        creature_cfg=creature_cfg,
        opener_cfg=opener_cfg,
        calmer_cfg=calmer_cfg,
        hero1=hero1,
        hero2=hero2,
        parent=parent,
        gate=gate,
        creature=creature,
        twist=True,
        teamwork=gate.meters["open"] >= THRESHOLD and creature.meters["safe"] >= THRESHOLD,
        misread="villain",
    )
    return world


KNOWLEDGE = {
    "gate": [
        (
            "What does a gate do?",
            "A gate is a movable part of a fence. It lets you go in and out while still helping keep a place closed when it needs to be."
        )
    ],
    "latch": [
        (
            "What is a latch on a gate?",
            "A latch is the small part that catches and holds a gate shut. You move it to open the gate."
        )
    ],
    "rust": [
        (
            "Why can rust make a gate hard to open?",
            "Rust makes metal rough and stiff. That can make a bolt scrape and stick instead of sliding smoothly."
        )
    ],
    "rope": [
        (
            "Why does a knot keep a gate closed?",
            "A knot holds a rope in loops that grip tight. Until the loops are loosened, the gate handle cannot move freely."
        )
    ],
    "goat": [
        (
            "Why might a goat bump a gate?",
            "A goat may bump a gate because it is scared or wants to get through. Frightened animals often push before they understand what is happening."
        )
    ],
    "puppy": [
        (
            "Why do puppies bark when they are scared?",
            "Puppies bark to call out and let their feelings burst out. A scared bark can sound fierce even when the puppy is very small."
        )
    ],
    "duck": [
        (
            "Why does a duckling peep?",
            "A duckling peeps to call for help or stay close to its family. The sound is small, but it can mean a lot."
        )
    ],
    "soft_voice": [
        (
            "Why can a soft voice help a scared animal?",
            "A soft voice is gentle and steady. That can help an animal feel that nobody is about to chase or hurt it."
        )
    ],
    "snack": [
        (
            "Why can a treat help calm a puppy?",
            "A small treat gives the puppy something friendly to notice. It can shift the puppy from barking and jumping to sniffing and trusting."
        )
    ],
    "hum": [
        (
            "Why can humming help when someone is scared?",
            "A slow hum is smooth and steady. Gentle repeating sounds can make a frightened body feel calmer."
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means people help with different parts of the same job. The team can do more together than one person can do alone."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "gate", "latch", "rust", "rope", "goat", "puppy", "duck",
    "soft_voice", "snack", "hum", "teamwork",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero1 = f["hero1"]
    hero2 = f["hero2"]
    gate_cfg = f["gate_cfg"]
    creature_cfg = f["creature_cfg"]
    return [
        (
            f'Write a short superhero story for a 3-to-5-year-old that includes the word "gate". '
            f'Two child heroes hear something behind {gate_cfg.gate_label}, speak in dialogue, '
            f'and discover a gentle twist.'
        ),
        (
            f"Tell a teamwork story where {hero1.id} and {hero2.id} first think a villain is behind a gate, "
            f"but the twist is that it is {creature_cfg.article} that needs help."
        ),
        (
            f"Write a child-facing rescue story with capes, a gate, dialogue, and a happy ending where one hero opens "
            f"the way and the other hero calms the frightened animal."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero1 = f["hero1"]
    hero2 = f["hero2"]
    parent = f["parent"]
    gate_cfg = f["gate_cfg"]
    creature_cfg = f["creature_cfg"]
    opener_cfg = f["opener_cfg"]
    calmer_cfg = f["calmer_cfg"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two children, {hero1.id} and {hero2.id}, who were pretending to be superheroes. "
            f"They found a problem at {gate_cfg.gate_label} and solved it together."
        ),
        (
            "Why did the gate seem scary at first?",
            f"The children heard {creature_cfg.sound} and saw {creature_cfg.shadow}, so they guessed something spooky was there. "
            f"The gate hid the truth until they looked more carefully."
        ),
        (
            "What was the twist?",
            f"The twist was that there was no gate villain at all. "
            f"It was really {creature_cfg.article} that had been frightened behind the gate."
        ),
        (
            f"How did {hero1.id} and {hero2.id} use teamwork?",
            f"{hero1.id} handled the part about opening the gate, and {hero2.id} handled the part about calming the animal. "
            f"The rescue worked because they shared the job instead of both trying the same thing."
        ),
        (
            f"What did the grown-up say at the end?",
            f"{parent.label_word.capitalize()} said that real heroes look first, think next, and help together. "
            f"That line fits the story because the children stopped guessing and worked as a team."
        ),
    ]

    if f["gate"].meters["open"] >= THRESHOLD:
        qa.append(
            (
                f"How did {hero1.id} open the gate?",
                f"{hero1.id} used the {opener_cfg.label} part of the plan and {gate_cfg.opening_line}. "
                f"That matched the gate's real problem instead of using a random trick."
            )
        )
    if f["creature"].meters["safe"] >= THRESHOLD:
        qa.append(
            (
                f"How did {hero2.id} calm the {creature_cfg.label}?",
                f"{hero2.id} used the {calmer_cfg.label} part of the plan. "
                f"{creature_cfg.calm_result}"
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"gate", "teamwork"}
    tags |= set(f["gate_cfg"].tags)
    tags |= set(f["creature_cfg"].tags)
    tags |= set(f["opener_cfg"].tags)
    tags |= set(f["calmer_cfg"].tags)
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
        bits = [f"({ent.type})"]
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:9} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
good_open(G, O) :- gate(G), open_skill(O), needs_open(G, O).
good_calm(C, K) :- creature(C), calm_skill(K), needs_calm(C, K).

valid_quad(G, C, O, K) :- gate(G), creature(C), open_skill(O), calm_skill(K),
                          good_open(G, O), good_calm(C, K).
valid(G, C, O) :- valid_quad(G, C, O, _).

opened :- chosen_gate(G), chosen_open(O), good_open(G, O).
calmed :- chosen_creature(C), chosen_calm(K), good_calm(C, K).
rescued :- opened, calmed.

outcome(success) :- rescued.
outcome(failed_open) :- not opened.
outcome(failed_calm) :- opened, not calmed.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for gate_id, gate in GATES.items():
        lines.append(asp.fact("gate", gate_id))
        lines.append(asp.fact("needs_open", gate_id, gate.needs_open))
    for creature_id, creature in CREATURES.items():
        lines.append(asp.fact("creature", creature_id))
        lines.append(asp.fact("needs_calm", creature_id, creature.needs_calm))
    for open_skill_id in OPEN_SKILLS:
        lines.append(asp.fact("open_skill", open_skill_id))
    for calm_skill_id in CALM_SKILLS:
        lines.append(asp.fact("calm_skill", calm_skill_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid_quad/4."))
    return sorted(set(asp.atoms(model, "valid_quad")))


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_gate", params.gate),
            asp.fact("chosen_creature", params.creature),
            asp.fact("chosen_open", params.open_skill),
            asp.fact("chosen_calm", params.calm_skill),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    opened = can_open(params.gate, params.open_skill)
    calmed = can_calm(params.creature, params.calm_skill)
    if opened and calmed:
        return "success"
    if not opened:
        return "failed_open"
    return "failed_calm"


def asp_verify() -> int:
    rc = 0

    py3 = set(valid_combos())
    asp3 = set(asp_valid_combos())
    if py3 == asp3:
        print(f"OK: gate triple set matches ({len(py3)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid triple set:")
        if py3 - asp3:
            print("  only in python:", sorted(py3 - asp3))
        if asp3 - py3:
            print("  only in clingo:", sorted(asp3 - py3))

    py4 = set(valid_quads())
    asp4 = set(asp_valid())
    if py4 == asp4:
        print(f"OK: full rescue quad set matches ({len(py4)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid quad set:")
        if py4 - asp4:
            print("  only in python:", sorted(py4 - asp4))
        if asp4 - py4:
            print("  only in clingo:", sorted(asp4 - py4))

    cases: list[StoryParams] = list(CURATED)
    for seed in range(30):
        try:
            args = build_parser().parse_args([])
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError during seeded resolve at seed {seed}.")
            break

    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} scenario outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during verify smoke test.")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Superhero gate story world: a spooky misunderstanding, a twist, and teamwork."
    )
    ap.add_argument("--gate", choices=GATES)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--open-skill", choices=OPEN_SKILLS)
    ap.add_argument("--calm-skill", choices=CALM_SKILLS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible rescue set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.gate and args.open_skill and not can_open(args.gate, args.open_skill):
        raise StoryError(explain_gate_rejection(args.gate, args.open_skill))
    if args.creature and args.calm_skill and not can_calm(args.creature, args.calm_skill):
        raise StoryError(explain_creature_rejection(args.creature, args.calm_skill))

    candidates = [
        quad for quad in valid_quads()
        if (args.gate is None or quad[0] == args.gate)
        and (args.creature is None or quad[1] == args.creature)
        and (args.open_skill is None or quad[2] == args.open_skill)
        and (args.calm_skill is None or quad[3] == args.calm_skill)
    ]
    if not candidates:
        raise StoryError("(No valid combination matches the given options.)")

    gate_id, creature_id, open_skill_id, calm_skill_id = rng.choice(candidates)
    hero1_gender = rng.choice(["girl", "boy"])
    hero2_gender = rng.choice(["girl", "boy"])
    hero1_name = _pick_name(rng, hero1_gender)
    hero2_name = _pick_name(rng, hero2_gender, avoid=hero1_name)
    parent = args.parent or rng.choice(["mother", "father"])
    hero1_trait = rng.choice(TRAITS)
    hero2_trait = rng.choice([t for t in TRAITS if t != hero1_trait] or TRAITS)

    return StoryParams(
        gate=gate_id,
        creature=creature_id,
        open_skill=open_skill_id,
        calm_skill=calm_skill_id,
        hero1_name=hero1_name,
        hero1_gender=hero1_gender,
        hero2_name=hero2_name,
        hero2_gender=hero2_gender,
        parent=parent,
        hero1_trait=hero1_trait,
        hero2_trait=hero2_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.gate not in GATES:
        raise StoryError(f"(Invalid gate: {params.gate})")
    if params.creature not in CREATURES:
        raise StoryError(f"(Invalid creature: {params.creature})")
    if params.open_skill not in OPEN_SKILLS:
        raise StoryError(f"(Invalid open skill: {params.open_skill})")
    if params.calm_skill not in CALM_SKILLS:
        raise StoryError(f"(Invalid calm skill: {params.calm_skill})")
    if not can_open(params.gate, params.open_skill):
        raise StoryError(explain_gate_rejection(params.gate, params.open_skill))
    if not can_calm(params.creature, params.calm_skill):
        raise StoryError(explain_creature_rejection(params.creature, params.calm_skill))

    world = tell(params)
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
        print(asp_program("", "#show valid_quad/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        quads = asp_valid()
        print(f"{len(quads)} compatible (gate, creature, open_skill, calm_skill) combinations:\n")
        for gate_id, creature_id, open_skill_id, calm_skill_id in quads:
            print(f"  {gate_id:8} {creature_id:7} {open_skill_id:8} {calm_skill_id}")
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
            header = f"### {p.hero1_name} & {p.hero2_name}: {p.creature} at {p.gate} gate"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
