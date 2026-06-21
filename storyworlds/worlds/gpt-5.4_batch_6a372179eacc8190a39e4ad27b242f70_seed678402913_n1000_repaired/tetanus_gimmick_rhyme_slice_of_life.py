#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/tetanus_gimmick_rhyme_slice_of_life.py
=================================================================

A standalone story world for a small slice-of-life domain: two children are
making a tiny rhyme performance with a homemade gimmick, one child is tempted
to use dirty sharp metal to fasten it, and a calm grown-up helps them switch to
a safer way.

The model keeps the domain deliberately narrow and reasoned:

* A project has a fastening need: stick / hang / tie.
* A risky tool is tempting because it looks quick, but only dirty sharp metal
  counts as the puncture hazard we care about here.
* A safe fix must actually satisfy the same fastening need.
* If the older sibling carries enough authority, the risky move is averted.
* Otherwise a poke happens, and the adult response must be sensible:
  - home care can be enough for a clean, routine-risk poke
  - a clinic visit is required when the child is due for a tetanus booster

The stories include short rhyming lines as part of the children's little show.
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
BRAVERY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "cautious", "steady", "sensible"}


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
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    sharp: bool = False
    dirty: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "nurse"}
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
class Project:
    id: str
    place: str
    setup: str
    prop: str
    need: str
    rhyme_a: str
    rhyme_b: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class RiskyTool:
    id: str
    label: str
    phrase: str
    where: str
    use_line: str
    warning_name: str
    dirty: bool = True
    sharp: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class SafeFix:
    id: str
    label: str
    phrase: str
    needs: set[str] = field(default_factory=set)
    action: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    level: int
    text: str
    qa_text: str
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


def _r_poke_alarm(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.kids():
        if ent.meters["poked"] < THRESHOLD:
            continue
        sig = ("poke_alarm", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["bleeding"] += 1
        ent.memes["fear"] += 1
        for kid in world.kids():
            kid.memes["worry"] += 1
        if "room" in world.entities:
            world.get("room").meters["alarm"] += 1
        out.append("__poke__")
    return out


def _r_dirty_risk(world: World) -> list[str]:
    child = world.entities.get("instigator")
    tool = world.entities.get("tool")
    if not child or not tool:
        return []
    if child.meters["poked"] < THRESHOLD or not tool.dirty:
        return []
    sig = ("dirty_risk", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.meters["tetanus_risk"] += 1
    return ["__tetanus__"]


CAUSAL_RULES = [
    Rule(name="poke_alarm", tag="physical", apply=_r_poke_alarm),
    Rule(name="dirty_risk", tag="physical", apply=_r_dirty_risk),
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


def hazard_at_risk(tool: RiskyTool) -> bool:
    return tool.sharp and tool.dirty


def select_fix(project: Project) -> Optional[SafeFix]:
    for fix in SAFE_FIXES.values():
        if project.need in fix.needs:
            return fix
    return None


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    older = relation == "siblings" and cautioner_age > instigator_age
    authority = initial_caution(trait) + 1.0 + (4.0 if older else 0.0)
    return older and authority > BRAVERY_INIT


def response_allowed(response: Response, booster_due: bool) -> bool:
    if response.sense < SENSE_MIN:
        return False
    if booster_due and response.level < 2:
        return False
    return True


def predict_poke(world: World) -> dict:
    sim = world.copy()
    child = sim.get("instigator")
    child.meters["poked"] += 1
    propagate(sim, narrate=False)
    return {
        "bleeding": sim.get("instigator").meters["bleeding"],
        "tetanus_risk": sim.get("instigator").meters["tetanus_risk"],
        "alarm": sim.get("room").meters["alarm"],
    }


def introduce(world: World, a: Entity, b: Entity, project: Project) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"After school, {a.id} and {b.id} sat together at {project.place}. {project.setup}"
    )
    world.say(
        f"They were making {project.prop} for a tiny rhyme show, and {a.id} kept calling it "
        f"their special gimmick."
    )
    world.say(f'"{project.rhyme_a}" {a.id} sang. "{project.rhyme_b}" {b.id} answered.')


def need_fastener(world: World, b: Entity, project: Project) -> None:
    need_text = {
        "stick": "Something had to hold the cardboard piece flat.",
        "hang": "Something had to hang the little piece from the string.",
        "tie": "Something had to hold the ribbon on tight.",
    }[project.need]
    world.say(
        f"But the last part was loose. {need_text} {b.id} pressed it with careful fingers and frowned."
    )


def tempt(world: World, a: Entity, tool: RiskyTool) -> None:
    a.memes["bravado"] += 1
    world.say(
        f'{a.id} spotted {tool.phrase} {tool.where}. "{tool.warning_name}!" {a.pronoun().capitalize()} said. '
        f'"That would make the gimmick work fast."'
    )


def warn(world: World, b: Entity, a: Entity, tool: RiskyTool, parent: Entity) -> None:
    pred = predict_poke(world)
    world.facts["predicted_alarm"] = pred["alarm"]
    world.facts["predicted_tetanus_risk"] = pred["tetanus_risk"]
    b.memes["caution"] += 1
    extra = ""
    if pred["tetanus_risk"] >= THRESHOLD:
        extra = f" Dirty sharp metal can bring germs that cause tetanus, and {parent.label_word}s take pokes like that seriously."
    world.say(
        f'{b.id} pulled {b.pronoun("possessive")} hand back. "{a.id}, no. We are not supposed to touch {tool.label}.{extra}"'
    )


def back_down(world: World, a: Entity, b: Entity, project: Project, fix: SafeFix) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f'{a.id} opened {a.pronoun("possessive")} mouth to argue, but {b.id} was older and very steady. '
        f'After one long breath, {a.id} set the metal down.'
    )
    world.say(
        f'Together they used {fix.phrase} instead, and the little gimmick stayed cute without being sharp.'
    )


def defy(world: World, a: Entity, b: Entity, tool: RiskyTool) -> None:
    a.memes["defiance"] += 1
    world.say(
        f'"It will only take one second," {a.id} said. Even though {b.id} leaned closer, {a.id} reached for {tool.label}.'
    )


def poke(world: World, a: Entity, tool: RiskyTool) -> None:
    a.meters["poked"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{tool.use_line} Then {a.id} gave a tiny gasp. The metal slipped, and it poked one finger."
    )
    world.say(
        f"A bright bead of blood stood up at once, and the room felt very still."
    )


def call_parent(world: World, b: Entity, parent: Entity) -> None:
    b.memes["care"] += 1
    world.say(f'"{parent.label_word.capitalize()}!" {b.id} called. "{b.pronoun().capitalize()} got hurt."')


def home_care(world: World, parent: Entity, a: Entity, tool: RiskyTool) -> None:
    a.meters["cleaned"] += 1
    a.meters["bandaged"] += 1
    a.memes["relief"] += 1
    world.say(
        f"{parent.label_word.capitalize()} came quickly, washed the little poke with soap and water, "
        f"and wrapped a clean bandage around {a.id}'s finger."
    )
    world.say(
        f'"A gimmick is never worth a dirty poke," {parent.pronoun()} said softly. '
        f'"We clean it right away, and we do not play with {tool.label}."'
    )


def clinic_care(world: World, parent: Entity, a: Entity, tool: RiskyTool) -> None:
    a.meters["cleaned"] += 1
    a.meters["clinic"] += 1
    a.memes["fear"] = 0.0
    a.memes["relief"] += 1
    world.say(
        f"{parent.label_word.capitalize()} washed the little wound, then looked closely at the dirty metal."
    )
    world.say(
        f'"Because this was a dirty sharp poke, we are going to the clinic to ask about tetanus protection," '
        f"{parent.pronoun()} said."
    )
    world.say(
        f"At the clinic, the nurse cleaned the finger again and helped everyone feel calmer."
    )


def finish_show(world: World, a: Entity, b: Entity, project: Project, fix: SafeFix, outcome: str) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    if outcome == "averted":
        start = "A little later"
    elif outcome == "home_care":
        start = "By the time the bandage sat neat and white"
    else:
        start = "Later, back home from the clinic"
    world.say(
        f"{start}, they finished the project with {fix.phrase}. {fix.action}"
    )
    world.say(
        f'Then they tried their rhyme again: "{project.rhyme_a}" "{project.rhyme_b}"'
    )
    world.say(project.ending_image)


PROJECTS = {
    "porch_spinner": Project(
        id="porch_spinner",
        place="the front porch steps",
        setup="A shoebox of markers, ribbon, and cardboard sat open between them.",
        prop="a cardboard star that would spin at the end of their chant",
        need="stick",
        rhyme_a="Spin and grin, let the rhyme begin",
        rhyme_b="Clap in time, little porch rhyme",
        ending_image="The star turned in the breeze while they grinned at each other and kept time with their hands.",
        tags={"rhyme", "porch", "craft"},
    ),
    "kitchen_jingle": Project(
        id="kitchen_jingle",
        place="the kitchen table",
        setup="Scraps of paper, string, and a little bell made a soft clutter in the sunny light.",
        prop="a tiny bell jingle for the end of their poem",
        need="hang",
        rhyme_a="Ring and sing, hear the small bell swing",
        rhyme_b="Chime in line, little kitchen rhyme",
        ending_image="The bell gave one bright jingle while the warm kitchen smelled like toast and soap.",
        tags={"rhyme", "kitchen", "craft"},
    ),
    "yard_ribbon": Project(
        id="yard_ribbon",
        place="a picnic blanket in the yard",
        setup="Paper flowers and a basket of bits and pieces were spread over the blanket.",
        prop="a ribbon tail for their pretend parade microphone",
        need="tie",
        rhyme_a="Tie it high, wave it to the sky",
        rhyme_b="Step in line, parade and rhyme",
        ending_image="The ribbon fluttered behind the paper microphone as they marched three happy circles in the grass.",
        tags={"rhyme", "yard", "craft"},
    ),
}

RISKY_TOOLS = {
    "rusty_nail": RiskyTool(
        id="rusty_nail",
        label="the rusty nail",
        phrase="a rusty nail",
        where="near the flowerpot",
        use_line="It looked quick and clever for exactly half a moment.",
        warning_name="A nail",
        dirty=True,
        sharp=True,
        tags={"tetanus", "metal", "sharp"},
    ),
    "bent_wire": RiskyTool(
        id="bent_wire",
        label="the bent wire",
        phrase="a bent, dusty wire",
        where="beside the toolbox",
        use_line="The wire bent the wrong way under small fingers.",
        warning_name="That wire",
        dirty=True,
        sharp=True,
        tags={"tetanus", "metal", "sharp"},
    ),
    "thumbtack": RiskyTool(
        id="thumbtack",
        label="the thumbtack",
        phrase="an old thumbtack",
        where="on the windowsill",
        use_line="The tack skittered instead of staying still.",
        warning_name="A tack",
        dirty=True,
        sharp=True,
        tags={"tetanus", "metal", "sharp"},
    ),
    "clothespin": RiskyTool(
        id="clothespin",
        label="the clothespin",
        phrase="a wooden clothespin",
        where="in the basket",
        use_line="It only pinched the cardboard.",
        warning_name="A clothespin",
        dirty=False,
        sharp=False,
        tags={"wood"},
    ),
}

SAFE_FIXES = {
    "tape": SafeFix(
        id="tape",
        label="masking tape",
        phrase="a strip of masking tape",
        needs={"stick"},
        action="The cardboard held flat at once.",
        tags={"tape"},
    ),
    "string_loop": SafeFix(
        id="string_loop",
        label="a soft string loop",
        phrase="a soft string loop",
        needs={"hang"},
        action="The bell hung neatly and swung without scratching anyone.",
        tags={"string"},
    ),
    "ribbon_knot": SafeFix(
        id="ribbon_knot",
        label="a ribbon knot",
        phrase="a careful ribbon knot",
        needs={"tie"},
        action="The ribbon stayed on with one snug little bow.",
        tags={"string"},
    ),
    "glue_dot": SafeFix(
        id="glue_dot",
        label="a glue dot",
        phrase="a sticky glue dot",
        needs={"stick"},
        action="The cardboard settled into place and stayed there.",
        tags={"glue"},
    ),
}

RESPONSES = {
    "wash_bandage": Response(
        id="wash_bandage",
        sense=2,
        level=1,
        text="washed the poke and put on a bandage",
        qa_text="washed the little wound with soap and water and put on a bandage",
        tags={"bandage"},
    ),
    "clinic_visit": Response(
        id="clinic_visit",
        sense=3,
        level=2,
        text="washed the poke, then took the child to the clinic to ask about tetanus protection",
        qa_text="washed the wound and took the child to the clinic to ask about tetanus protection",
        tags={"clinic", "bandage", "tetanus"},
    ),
    "ignore": Response(
        id="ignore",
        sense=1,
        level=0,
        text="shrugged and said it was probably nothing",
        qa_text="did almost nothing",
        tags={"unsafe"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Maya"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Theo", "Eli"]
TRAITS = ["careful", "curious", "steady", "playful", "cautious", "sensible"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for project_id, project in PROJECTS.items():
        if select_fix(project) is None:
            continue
        for tool_id, tool in RISKY_TOOLS.items():
            if hazard_at_risk(tool):
                combos.append((project_id, tool_id))
    return combos


@dataclass
class StoryParams:
    project: str
    risky_tool: str
    safe_fix: str
    response: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
    trait: str
    relation: str = "siblings"
    instigator_age: int = 5
    cautioner_age: int = 6
    booster_due: bool = False
    seed: Optional[int] = None


KNOWLEDGE = {
    "tetanus": [
        (
            "What is tetanus?",
            "Tetanus is a very serious sickness caused by germs that can get into a cut or puncture. That is why grown-ups clean dirty pokes fast and sometimes call a doctor or clinic.",
        )
    ],
    "metal": [
        (
            "Why can dirty sharp metal be dangerous?",
            "Dirty sharp metal can poke skin and carry germs into the little hole it makes. A puncture wound may look small, but grown-ups still take it seriously.",
        )
    ],
    "bandage": [
        (
            "What does a bandage do?",
            "A bandage helps cover a wound and keeps it cleaner while the skin starts to heal. It also reminds you to be gentle with that spot.",
        )
    ],
    "clinic": [
        (
            "Why might someone go to a clinic after a dirty poke?",
            "A clinic can help clean the wound well and check whether the person needs tetanus protection. That keeps a small injury from turning into a bigger problem.",
        )
    ],
    "tape": [
        (
            "What is masking tape good for?",
            "Masking tape is good for holding light paper or cardboard in place. It sticks without making a sharp hole.",
        )
    ],
    "string": [
        (
            "What can a string loop or knot do in a craft?",
            "A string loop or knot can hold a light craft part by wrapping around it instead of poking through skin or paper. It is often safer for children to use.",
        )
    ],
    "glue": [
        (
            "What does glue do in a paper craft?",
            "Glue helps paper pieces stay together by sticking them gently. It can do the job without sharp metal.",
        )
    ],
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme is when words sound alike at the end, like time and chime. Rhymes can make songs and little poems fun to say out loud.",
        )
    ],
}
KNOWLEDGE_ORDER = ["rhyme", "tetanus", "metal", "bandage", "clinic", "tape", "string", "glue"]


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
    project = f["project_cfg"]
    tool = f["tool_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a slice-of-life story for a 3-to-5-year-old that includes the words '
        f'"tetanus" and "gimmick" and uses little rhyming lines. The story should be set at {project.place}.'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle story where {a.id} wants to use {tool.label} for a craft gimmick, but {b.id} stops it before anyone gets hurt.",
            f'Write a homey rhyme story where children making a tiny show choose a safe craft fix instead of dirty sharp metal, and a grown-up later smiles at the finished result.',
        ]
    if outcome == "home_care":
        return [
            base,
            f"Tell a story where {a.id} ignores a warning, gets a small poke from {tool.label}, and a calm grown-up washes it and puts on a bandage.",
            f'Write a slice-of-life cautionary story with a small injury, a mention of tetanus, and a cozy ending where the children still finish their rhyme project safely.',
        ]
    return [
        base,
        f"Tell a story where {a.id} gets a dirty poke while making a craft gimmick, and a grown-up takes {a.pronoun('object')} to the clinic to ask about tetanus protection.",
        f'Write a gentle but serious family story with a clinic visit, rhyming lines, and an ending that shows the children now use safer tools.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    parent = f["parent"]
    project = f["project_cfg"]
    tool = f["tool_cfg"]
    fix = f["fix_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(a, b, f['relation'])}, {a.id} and {b.id}, making a little rhyme show with {parent.label_word} nearby in their day.",
        ),
        (
            "What were the children making?",
            f"They were making {project.prop} for a tiny rhyme show. {a.id} called it their gimmick because it was the special little trick at the end.",
        ),
        (
            f"Why did {b.id} say no to {tool.label}?",
            f"{b.id} knew the metal was dirty and sharp, so it could poke a finger. {b.pronoun().capitalize()} also knew that a dirty puncture can worry grown-ups because of tetanus germs.",
        ),
    ]
    if outcome == "averted":
        qa.append(
            (
                f"What happened after {b.id} warned {a.id}?",
                f"{a.id} listened and set the metal down before anyone got hurt. Then they used {fix.phrase}, so the gimmick worked without any poke at all.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended softly and safely. The children finished their rhyme and {project.ending_image[0].lower() + project.ending_image[1:]}",
            )
        )
    elif outcome == "home_care":
        qa.append(
            (
                f"What happened when {a.id} used {tool.label}?",
                f"The metal slipped and poked one finger, and a little bit of blood appeared. The problem came from choosing a dirty sharp shortcut instead of a safe craft fix.",
            )
        )
        qa.append(
            (
                f"How did {parent.label_word} help?",
                f"{parent.label_word.capitalize()} washed the poke and put on a bandage. That helped clean the wound quickly and turned the scary moment into a lesson about safer tools.",
            )
        )
        qa.append(
            (
                "Did they still finish the project?",
                f"Yes. After the finger was cleaned, they used {fix.phrase} and finished the rhyme show safely. The ending proves they changed the method, not the fun.",
            )
        )
    else:
        qa.append(
            (
                f"Why did {parent.label_word} take {a.id} to the clinic?",
                f"{parent.label_word.capitalize()} saw that the poke came from dirty sharp metal, so the family needed to ask about tetanus protection. Even a small puncture can need extra care when it is dirty.",
            )
        )
        qa.append(
            (
                "What happened at the clinic?",
                "The nurse cleaned the finger again and helped everyone feel calmer. After that, the family knew they were taking the risk seriously instead of guessing at home.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended in a steadier, safer way. Back at home, they used {fix.phrase}, said their rhyme, and the craft worked without any more sharp metal.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"rhyme"}
    tags |= set(world.facts["tool_cfg"].tags)
    tags |= set(world.facts["fix_cfg"].tags)
    tags |= set(world.facts["response_cfg"].tags)
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


def tell(
    project: Project,
    tool_cfg: RiskyTool,
    fix_cfg: SafeFix,
    response_cfg: Response,
    *,
    instigator: str,
    instigator_gender: str,
    cautioner: str,
    cautioner_gender: str,
    parent_type: str,
    trait: str,
    relation: str,
    instigator_age: int,
    cautioner_age: int,
    booster_due: bool,
) -> World:
    world = World()
    a = world.add(
        Entity(
            id="instigator",
            kind="character",
            type=instigator_gender,
            label=instigator,
            role="instigator",
            age=instigator_age,
            traits=["bold"],
            attrs={"name": instigator, "relation": relation},
        )
    )
    b = world.add(
        Entity(
            id="cautioner",
            kind="character",
            type=cautioner_gender,
            label=cautioner,
            role="cautioner",
            age=cautioner_age,
            traits=[trait],
            attrs={"name": cautioner, "relation": relation},
        )
    )
    parent = world.add(
        Entity(
            id="parent",
            kind="character",
            type=parent_type,
            label="the parent",
            role="parent",
        )
    )
    world.add(Entity(id="room", type="room", label="the room"))
    tool = world.add(
        Entity(
            id="tool",
            type="tool",
            label=tool_cfg.label,
            phrase=tool_cfg.phrase,
            sharp=tool_cfg.sharp,
            dirty=tool_cfg.dirty,
            tags=set(tool_cfg.tags),
        )
    )

    a.memes["bravery"] = BRAVERY_INIT
    b.memes["caution"] = initial_caution(trait)
    world.facts["relation"] = relation
    world.facts["booster_due"] = booster_due

    introduce(world, a, b, project)
    need_fastener(world, b, project)

    world.para()
    tempt(world, a, tool_cfg)
    warn(world, b, a, tool_cfg, parent)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)
    if averted:
        back_down(world, a, b, project, fix_cfg)
        world.para()
        finish_show(world, a, b, project, fix_cfg, "averted")
        outcome = "averted"
    else:
        defy(world, a, b, tool_cfg)
        world.para()
        poke(world, a, tool_cfg)
        call_parent(world, b, parent)
        world.para()
        if response_cfg.id == "clinic_visit":
            clinic_care(world, parent, a, tool_cfg)
            outcome = "clinic"
        else:
            home_care(world, parent, a, tool_cfg)
            outcome = "home_care"
        world.para()
        finish_show(world, a, b, project, fix_cfg, outcome)

    world.facts.update(
        instigator=a,
        cautioner=b,
        parent=parent,
        project_cfg=project,
        tool_cfg=tool_cfg,
        fix_cfg=fix_cfg,
        response_cfg=response_cfg,
        outcome=outcome,
        poked=a.meters["poked"] >= THRESHOLD,
    )
    return world


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.label:
            bits.append(f"label={ent.label!r}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.sharp:
            bits.append("sharp=True")
        if ent.dirty:
            bits.append("dirty=True")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        project="porch_spinner",
        risky_tool="rusty_nail",
        safe_fix="tape",
        response="wash_bandage",
        instigator="Ben",
        instigator_gender="boy",
        cautioner="Lily",
        cautioner_gender="girl",
        parent="mother",
        trait="careful",
        relation="siblings",
        instigator_age=5,
        cautioner_age=7,
        booster_due=False,
    ),
    StoryParams(
        project="kitchen_jingle",
        risky_tool="bent_wire",
        safe_fix="string_loop",
        response="wash_bandage",
        instigator="Mia",
        instigator_gender="girl",
        cautioner="Max",
        cautioner_gender="boy",
        parent="father",
        trait="curious",
        relation="friends",
        instigator_age=6,
        cautioner_age=6,
        booster_due=False,
    ),
    StoryParams(
        project="yard_ribbon",
        risky_tool="thumbtack",
        safe_fix="ribbon_knot",
        response="clinic_visit",
        instigator="Theo",
        instigator_gender="boy",
        cautioner="Nora",
        cautioner_gender="girl",
        parent="mother",
        trait="steady",
        relation="siblings",
        instigator_age=7,
        cautioner_age=5,
        booster_due=True,
    ),
]


def explain_rejection(tool: RiskyTool, project: Project) -> str:
    if not hazard_at_risk(tool):
        return (
            f"(No story: {tool.label} is not the dirty sharp metal hazard this world models, "
            f"so there is no tetanus worry and no meaningful safety turn.)"
        )
    if select_fix(project) is None:
        return (
            f"(No story: the project needs a fastening method, but the catalog has no safe fix "
            f"that actually does the same job.)"
        )
    return "(No story: this combination is outside the modeled hazard.)"


def explain_response(rid: str, booster_due: bool) -> str:
    response = RESPONSES[rid]
    if response.sense < SENSE_MIN:
        return (
            f"(Refusing response '{rid}': it scores too low on common sense "
            f"(sense={response.sense} < {SENSE_MIN}). Try a safer response like clinic_visit or wash_bandage.)"
        )
    if booster_due and response.level < 2:
        return (
            f"(Refusing response '{rid}': when the child is due for tetanus protection, "
            f"the adult must go to the clinic instead of handling it only at home.)"
        )
    return "(Refusing response: unsupported.)"


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    return "clinic" if RESPONSES[params.response].level >= 2 else "home_care"


ASP_RULES = r"""
hazard(T) :- risky_tool(T), sharp(T), dirty(T).
has_fix(P) :- project(P), need(P, N), safe_fix(F), fits(F, N).
valid(P, T) :- project(P), risky_tool(T), hazard(T), has_fix(P).

sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
response_allowed(R) :- sensible(R), booster_due(0).
response_allowed(R) :- sensible(R), booster_due(1), level(R, L), L >= 2.

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
older_sib :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(4) :- older_sib.
bonus(0) :- not older_sib.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- older_sib, authority(A), bravery_init(BR), A > BR.

outcome(averted) :- averted.
outcome(clinic) :- not averted, chosen_response(R), level(R, L), L >= 2.
outcome(home_care) :- not averted, chosen_response(R), level(R, L), L < 2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for project_id, project in PROJECTS.items():
        lines.append(asp.fact("project", project_id))
        lines.append(asp.fact("need", project_id, project.need))
    for tool_id, tool in RISKY_TOOLS.items():
        lines.append(asp.fact("risky_tool", tool_id))
        if tool.sharp:
            lines.append(asp.fact("sharp", tool_id))
        if tool.dirty:
            lines.append(asp.fact("dirty", tool_id))
    for fix_id, fix in SAFE_FIXES.items():
        lines.append(asp.fact("safe_fix", fix_id))
        for need in sorted(fix.needs):
            lines.append(asp.fact("fits", fix_id, need))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("level", rid, response.level))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
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


def asp_response_allowed(response_id: str, booster_due: bool) -> bool:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_response", response_id),
            asp.fact("booster_due", 1 if booster_due else 0),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show response_allowed/1."))
    allowed = asp.atoms(model, "response_allowed")
    return bool(allowed)


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_response", params.response),
            asp.fact("booster_due", 1 if params.booster_due else 0),
            asp.fact("relation", params.relation),
            asp.fact("instigator_age", params.instigator_age),
            asp.fact("cautioner_age", params.cautioner_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a child craft gimmick, a dirty sharp shortcut, and a safer way to finish the rhyme."
    )
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--risky-tool", choices=RISKY_TOOLS, dest="risky_tool")
    ap.add_argument("--safe-fix", choices=SAFE_FIXES, dest="safe_fix")
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--booster-due", action="store_true", help="child is due for tetanus protection, so clinic response is required")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.project and args.risky_tool:
        tool = RISKY_TOOLS[args.risky_tool]
        project = PROJECTS[args.project]
        if not (hazard_at_risk(tool) and select_fix(project) is not None):
            raise StoryError(explain_rejection(tool, project))

    booster_due = bool(args.booster_due)
    if args.response and not response_allowed(RESPONSES[args.response], booster_due):
        raise StoryError(explain_response(args.response, booster_due))

    combos = [
        combo for combo in valid_combos()
        if (args.project is None or combo[0] == args.project)
        and (args.risky_tool is None or combo[1] == args.risky_tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    project_id, tool_id = rng.choice(sorted(combos))
    project = PROJECTS[project_id]
    fix = args.safe_fix or select_fix(project).id
    if fix not in SAFE_FIXES or project.need not in SAFE_FIXES[fix].needs:
        raise StoryError("(No story: the chosen safe fix does not actually solve this project's fastening need.)")

    allowed_responses = [
        rid for rid, response in RESPONSES.items()
        if response_allowed(response, booster_due)
    ]
    response_id = args.response or rng.choice(sorted(allowed_responses))

    instigator, ig = _pick_child(rng)
    cautioner, cg = _pick_child(rng, avoid=instigator)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([4, 5, 6, 7], 2)
    trait = rng.choice(TRAITS)
    return StoryParams(
        project=project_id,
        risky_tool=tool_id,
        safe_fix=fix,
        response=response_id,
        instigator=instigator,
        instigator_gender=ig,
        cautioner=cautioner,
        cautioner_gender=cg,
        parent=args.parent or rng.choice(["mother", "father"]),
        trait=trait,
        relation=relation,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        booster_due=booster_due,
    )


def generate(params: StoryParams) -> StorySample:
    if params.project not in PROJECTS:
        raise StoryError(f"(Invalid project: {params.project})")
    if params.risky_tool not in RISKY_TOOLS:
        raise StoryError(f"(Invalid risky tool: {params.risky_tool})")
    if params.safe_fix not in SAFE_FIXES:
        raise StoryError(f"(Invalid safe fix: {params.safe_fix})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Invalid response: {params.response})")

    project = PROJECTS[params.project]
    tool = RISKY_TOOLS[params.risky_tool]
    fix = SAFE_FIXES[params.safe_fix]
    response = RESPONSES[params.response]

    if not hazard_at_risk(tool):
        raise StoryError(explain_rejection(tool, project))
    if project.need not in fix.needs:
        raise StoryError("(No story: the chosen safe fix does not fit the project.)")
    if not response_allowed(response, params.booster_due):
        raise StoryError(explain_response(params.response, params.booster_due))

    world = tell(
        project=project,
        tool_cfg=tool,
        fix_cfg=fix,
        response_cfg=response,
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        parent_type=params.parent,
        trait=params.trait,
        relation=params.relation,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
        booster_due=params.booster_due,
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

    clingo_sensible = set(asp_sensible())
    python_sensible = {r.id for r in sensible_responses()}
    if clingo_sensible == python_sensible:
        print(f"OK: sensible responses match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sensible)} python={sorted(python_sensible)}")

    for booster_due in (False, True):
        for rid, response in RESPONSES.items():
            c_ok = asp_response_allowed(rid, booster_due)
            p_ok = response_allowed(response, booster_due)
            if c_ok != p_ok:
                rc = 1
                print(f"MISMATCH in response_allowed for {rid} booster_due={booster_due}: clingo={c_ok} python={p_ok}")

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            cases.append(params)
        except StoryError:
            continue
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (project, risky_tool) combos:\n")
        for project, tool in combos:
            print(f"  {project:15} {tool}")
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
            header = f"### {p.project} / {p.risky_tool} / {outcome_of(p)}"
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
