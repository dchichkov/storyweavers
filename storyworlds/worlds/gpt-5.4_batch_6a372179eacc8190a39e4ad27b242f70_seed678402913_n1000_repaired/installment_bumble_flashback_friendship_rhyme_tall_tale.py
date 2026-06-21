#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/installment_bumble_flashback_friendship_rhyme_tall_tale.py
======================================================================================

A standalone storyworld for a tall-tale friendship story built around the seed
words "installment" and "bumble", with a flashback and a rhyme at its heart.

Premise
-------
In a windy prairie town, two friends build something absurdly large for the
market hill: a kite, a drum, or a banner. One friend tries to hurry the giant
thing up the hill, bumbles the job, and the object is put at risk. The other
friend remembers a flashback from the day their friendship began, when the two
of them learned a little rhyme about doing big jobs little by little. Using
that lesson, they carry the load in installments and save the day together.

World-model notes
-----------------
This script keeps the domain small and constrained:

* A giant object has a size and a weakness.
* A terrain creates a transport risk.
* A strategy is only valid when it actually matches the size and risk.
* The "installments" plan is the sensible fix for oversized loads.
* A flashback is state-driven: it appears when the friendship memory is needed.
* The ending image proves the change: the friends succeed together because they
  stop rushing and work in smaller steps.

Run it
------
    python storyworlds/worlds/gpt-5.4/installment_bumble_flashback_friendship_rhyme_tall_tale.py
    python storyworlds/worlds/gpt-5.4/installment_bumble_flashback_friendship_rhyme_tall_tale.py --project kite --terrain hill
    python storyworlds/worlds/gpt-5.4/installment_bumble_flashback_friendship_rhyme_tall_tale.py --strategy drag
    python storyworlds/worlds/gpt-5.4/installment_bumble_flashback_friendship_rhyme_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4/installment_bumble_flashback_friendship_rhyme_tall_tale.py --qa --json
    python storyworlds/worlds/gpt-5.4/installment_bumble_flashback_friendship_rhyme_tall_tale.py --verify
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
# from the repo root or from this nested subdirectory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


# ---------------------------------------------------------------------------
# Shared entity representation.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain registries.
# ---------------------------------------------------------------------------
@dataclass
class Project:
    id: str
    label: str
    phrase: str
    boast: str
    weak_spot: str
    haul_word: str
    ending_image: str
    size: int
    risky_on: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Terrain:
    id: str
    place: str
    footing: str
    trouble: str
    risk: str
    risk_score: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Strategy:
    id: str
    label: str
    mode: str
    sense: int
    power: int
    success_text: str
    fail_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


PROJECTS = {
    "kite": Project(
        id="kite",
        label="kite",
        phrase="a kite so wide it could have shaded three barns",
        boast="said the kite would pull the whole hill a little closer to the sky",
        weak_spot="its long ribbon tail",
        haul_word="spool and tail",
        ending_image="the giant kite rose over the market like a bright new sail",
        size=3,
        risky_on={"hill", "bridge"},
        tags={"kite", "wind", "craft"},
    ),
    "drum": Project(
        id="drum",
        label="drum",
        phrase="a parade drum as round as a cider barrel and twice as loud in promise",
        boast="said one boom from that drum would make fence posts stand up straighter",
        weak_spot="its stretched skin",
        haul_word="hoops and sticks",
        ending_image="the giant drum rolled into place and boomed warm as thunder",
        size=2,
        risky_on={"bridge", "mud"},
        tags={"drum", "parade", "craft"},
    ),
    "banner": Project(
        id="banner",
        label="banner",
        phrase="a banner so long it could have tied one elm tree to another",
        boast="said the banner would flap hard enough to wave at the moon",
        weak_spot="its painted edge",
        haul_word="poles and cloth",
        ending_image="the giant banner streamed above the stalls like a strip of sunset",
        size=2,
        risky_on={"hill", "mud"},
        tags={"banner", "parade", "craft"},
    ),
}

TERRAINS = {
    "hill": Terrain(
        id="hill",
        place="the market hill",
        footing="the path climbed steep and stony",
        trouble="the wind shoved at anything broad",
        risk="gusts",
        risk_score=2,
        tags={"hill", "wind"},
    ),
    "bridge": Terrain(
        id="bridge",
        place="the creek bridge",
        footing="the boards were narrow and springy",
        trouble="the planks bounced under long awkward loads",
        risk="bouncing boards",
        risk_score=2,
        tags={"bridge", "balance"},
    ),
    "mud": Terrain(
        id="mud",
        place="the fairground lane",
        footing="the lane had turned to pudding-thick mud",
        trouble="the ground tugged at boots and dragged at anything heavy",
        risk="sucking mud",
        risk_score=1,
        tags={"mud", "boots"},
    ),
}

STRATEGIES = {
    "installments": Strategy(
        id="installments",
        label="installments",
        mode="split",
        sense=3,
        power=3,
        success_text="they broke the giant load into small parts and carried it uphill in installment after installment, laughing the whole way",
        fail_text="they tried to split the load, but the day had already gone too wild and pieces kept slipping from their arms",
        qa_text="They saved the project by carrying it in small installments instead of all at once.",
        tags={"installment", "teamwork", "planning"},
    ),
    "wagon": Strategy(
        id="wagon",
        label="wagon",
        mode="wheel",
        sense=3,
        power=2,
        success_text="they fetched a red wagon and trundled the big load along with both friends steadying each side",
        fail_text="they fetched a wagon, but the wheels jolted so hard that the giant load lurched and bent anyway",
        qa_text="They used a wagon and kept both sides steady as they moved it.",
        tags={"wagon", "teamwork", "planning"},
    ),
    "drag": Strategy(
        id="drag",
        label="drag",
        mode="rush",
        sense=1,
        power=1,
        success_text="they somehow dragged the whole thing in one scrape and reached the top in a shower of dust",
        fail_text="they dragged the whole thing at once, and that only made the trouble worse",
        qa_text="They dragged the whole thing at once.",
        tags={"rush"},
    ),
}

RHYMES = {
    "step": "Bit by bit, not in a scramble; friends don't rush and bumble.",
    "steady": "Small by small, and strong by strong; two good friends can haul along.",
    "share": "Piece by piece and hand by hand; friends can move what none had planned.",
}

GIRL_NAMES = ["Mabel", "June", "Elsie", "Tess", "Nell", "Ruby", "Ada", "Clara"]
BOY_NAMES = ["Cal", "Otis", "Wes", "Jude", "Eli", "Silas", "Bo", "Ned"]
TRAITS = ["bold", "cheerful", "steady", "stubborn", "clever", "kindly"]


# ---------------------------------------------------------------------------
# Per-world parameters.
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    project: str
    terrain: str
    strategy: str
    lead_name: str
    lead_gender: str
    friend_name: str
    friend_gender: str
    helper_name: str
    helper_gender: str
    rhyme: str
    lead_trait: str
    friend_trait: str
    delay: int = 0
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Curated examples.
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        project="kite",
        terrain="hill",
        strategy="installments",
        lead_name="Cal",
        lead_gender="boy",
        friend_name="Mabel",
        friend_gender="girl",
        helper_name="Gran",
        helper_gender="girl",
        rhyme="step",
        lead_trait="bold",
        friend_trait="steady",
        delay=0,
    ),
    StoryParams(
        project="drum",
        terrain="bridge",
        strategy="wagon",
        lead_name="June",
        lead_gender="girl",
        friend_name="Otis",
        friend_gender="boy",
        helper_name="Gran",
        helper_gender="girl",
        rhyme="share",
        lead_trait="cheerful",
        friend_trait="clever",
        delay=0,
    ),
    StoryParams(
        project="banner",
        terrain="mud",
        strategy="installments",
        lead_name="Elsie",
        lead_gender="girl",
        friend_name="Wes",
        friend_gender="boy",
        helper_name="Gran",
        helper_gender="girl",
        rhyme="steady",
        lead_trait="stubborn",
        friend_trait="kindly",
        delay=1,
    ),
    StoryParams(
        project="kite",
        terrain="bridge",
        strategy="wagon",
        lead_name="Bo",
        lead_gender="boy",
        friend_name="Ruby",
        friend_gender="girl",
        helper_name="Gran",
        helper_gender="girl",
        rhyme="share",
        lead_trait="bold",
        friend_trait="steady",
        delay=1,
    ),
]


# ---------------------------------------------------------------------------
# World model.
# ---------------------------------------------------------------------------
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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


# ---------------------------------------------------------------------------
# Causal rules.
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_bumble_damage(world: World) -> list[str]:
    out: list[str] = []
    project = world.get("project")
    terrain = world.get("terrain")
    if project.meters["stressed"] < THRESHOLD:
        return out
    sig = ("damage", project.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    project.meters["at_risk"] += 1
    for kid in [world.get("lead"), world.get("friend")]:
        kid.memes["worry"] += 1
    out.append("__risk__")
    if terrain.meters["risk"] >= THRESHOLD:
        project.meters["danger"] += 1
    return out


def _r_teamwork_relief(world: World) -> list[str]:
    out: list[str] = []
    project = world.get("project")
    if project.meters["moved_parts"] < THRESHOLD:
        return out
    sig = ("relief", project.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in [world.get("lead"), world.get("friend")]:
        kid.memes["trust"] += 1
        kid.memes["joy"] += 1
        kid.memes["worry"] = max(0.0, kid.memes["worry"] - 1.0)
    out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule(name="bumble_damage", tag="physical", apply=_r_bumble_damage),
    Rule(name="teamwork_relief", tag="social", apply=_r_teamwork_relief),
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


# ---------------------------------------------------------------------------
# Reasonableness helpers.
# ---------------------------------------------------------------------------
def strategy_fits(project: Project, terrain: Terrain, strategy: Strategy) -> bool:
    if strategy.sense < SENSE_MIN:
        return False
    need = project.size + terrain.risk_score
    if strategy.id == "installments":
        return True
    return strategy.power >= need - 2


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for pid, project in PROJECTS.items():
        for tid, terrain in TERRAINS.items():
            if tid not in project.risky_on:
                continue
            for sid, strategy in STRATEGIES.items():
                if strategy_fits(project, terrain, strategy):
                    combos.append((pid, tid, sid))
    return combos


def project_severity(project: Project, terrain: Terrain, delay: int) -> int:
    return project.size + terrain.risk_score + delay


def is_saved(project: Project, terrain: Terrain, strategy: Strategy, delay: int) -> bool:
    if strategy.id == "installments":
        return True
    return strategy.power >= project_severity(project, terrain, delay) - 1


def explain_rejection(project: Project, terrain: Terrain, strategy: Strategy) -> str:
    if terrain.id not in project.risky_on:
        return (
            f"(No story: {project.phrase} is not the kind of load this world models on "
            f"{terrain.place}. Pick a terrain that truly makes that giant {project.label} awkward.)"
        )
    if strategy.sense < SENSE_MIN:
        return (
            f"(Refusing strategy '{strategy.id}': dragging one huge load at once is poor common "
            f"sense for a child-facing story. Try installments or wagon.)"
        )
    return (
        f"(No story: {strategy.label} is too weak for moving {project.phrase} across "
        f"{terrain.place}. Pick a steadier plan.)"
    )


# ---------------------------------------------------------------------------
# Prediction.
# ---------------------------------------------------------------------------
def predict_trouble(world: World, project_id: str, terrain_id: str) -> dict:
    sim = world.copy()
    project = sim.get(project_id)
    terrain = sim.get(terrain_id)
    project.meters["stressed"] += 1
    terrain.meters["risk"] += 1
    propagate(sim, narrate=False)
    return {
        "at_risk": project.meters["at_risk"] >= THRESHOLD,
        "danger": project.meters["danger"],
    }


# ---------------------------------------------------------------------------
# Story verbs.
# ---------------------------------------------------------------------------
def introduce(world: World, lead: Entity, friend: Entity, project: Project, terrain: Terrain) -> None:
    world.say(
        f"In the prairie town of Larkspur, {lead.id} and {friend.id} were such good friends "
        f"that folks said one of them could laugh on Tuesday and the other would finish the chuckle on Wednesday."
    )
    world.say(
        f"That spring they built {project.phrase} for the fair at {terrain.place}, and {lead.id} "
        f"{project.boast}."
    )
    for kid in (lead, friend):
        kid.memes["joy"] += 1
        kid.memes["friendship"] += 1


def set_out(world: World, lead: Entity, friend: Entity, project: Project, terrain: Terrain) -> None:
    world.say(
        f"On fair morning, {terrain.footing}, and {terrain.trouble}. Still, the two friends set off with "
        f"{project.weak_spot} fluttering and the whole enormous {project.label} tugging at their arms."
    )


def rush_and_bumble(world: World, lead: Entity, friend: Entity, project: Project, terrain: Terrain) -> None:
    lead.memes["pride"] += 1
    lead.memes["has_bumbled"] += 1
    project.meters["stressed"] += 1
    terrain.meters["risk"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"If we hurry, we can be on top before the band tunes a fiddle," {lead.id} cried.'
    )
    world.say(
        f"But {lead.id} tried to haul the whole thing in one grand yank, bumble-footed on the way, and "
        f"{project.weak_spot} gave a worried flap."
    )
    if project.meters["at_risk"] >= THRESHOLD:
        world.say(
            f"{friend.id} grabbed the nearest corner just in time, because {terrain.risk} had started making mischief with the giant {project.label}."
        )


def flashback(world: World, lead: Entity, friend: Entity, helper: Entity, rhyme_text: str) -> None:
    lead.memes["memory"] += 1
    friend.memes["memory"] += 1
    world.say(
        f"For one hush of a second, {friend.id} remembered the day their friendship began."
    )
    world.say(
        f"Back then, a barrel of windfall apples had split beside {helper.id}'s porch, and the fruit went rolling every which way."
    )
    world.say(
        f"{lead.id} had tried to scoop them all at once and nearly sat down in the grass with apples in both elbows. "
        f"{helper.id} laughed kindly and taught them a rhyme: \"{rhyme_text}\""
    )
    world.say(
        f"The two children had carried those apples in little trips until every last one was safe in the cellar, and that was the first day they knew they worked better together than alone."
    )


def choose_strategy(world: World, lead: Entity, friend: Entity, strategy: Strategy, project: Project, rhyme_text: str) -> None:
    friend.memes["care"] += 1
    if strategy.id == "installments":
        world.say(
            f'"We do not need one mighty trip," {friend.id} said. "We need an installment, then another installment, then another until the hill gives up."'
        )
        world.say(
            f"Together they chanted, \"{rhyme_text}\" and began sorting the {project.haul_word} into neat little loads."
        )
    else:
        world.say(
            f'"Let us work the sensible way," {friend.id} said, and together they chose the {strategy.label}.'
        )


def carry_in_parts(world: World, lead: Entity, friend: Entity, strategy: Strategy, project: Project, terrain: Terrain, delay: int) -> None:
    project.meters["moved_parts"] += 1
    propagate(world, narrate=False)
    if strategy.id == "installments":
        world.say(
            f"Up they went, little trip by little trip: one armful of {project.haul_word}, one laugh, one puff of breath, and then another."
        )
        if delay > 0:
            world.say(
                f"The day still fussed at them, but steady work beat the fuss. Even {terrain.risk} had to wait its turn while the friends kept coming back for the next piece."
            )
    else:
        world.say(
            f"They moved in one careful roll and one careful tug, each friend watching the other side so the giant load stayed true."
        )


def triumph(world: World, lead: Entity, friend: Entity, project: Project, terrain: Terrain) -> None:
    project.meters["safe"] += 1
    lead.memes["pride"] = 0.0
    for kid in (lead, friend):
        kid.memes["joy"] += 1
        kid.memes["friendship"] += 1
    world.say(
        f"By the time they reached {terrain.place}, not a stitch was lost and not a corner had gone astray."
    )
    world.say(
        f"Soon {project.ending_image}, and people below tipped hats, dropped pies, and forgot mid-bite what they had been about to say."
    )
    world.say(
        f"{lead.id} bowed to {friend.id} and admitted the plain truth: the giant job had only become possible once two friends stopped hurrying and started helping."
    )


def setback(world: World, lead: Entity, friend: Entity, project: Project, terrain: Terrain, strategy: Strategy) -> None:
    project.meters["torn"] += 1
    lead.memes["regret"] += 1
    friend.memes["worry"] += 1
    world.say(
        f"But {strategy.fail_text}, and {project.weak_spot} finally gave way under {terrain.risk}."
    )
    world.say(
        f"The fair folk still helped gather the pieces, yet {lead.id} stood very still and knew rushing had made the giant trouble bigger."
    )
    world.say(
        f"Even then, {friend.id} did not leave. The two friends sat on the grass beside the bent {project.label}, and promised that the next big job would be done together and in smaller steps."
    )


# ---------------------------------------------------------------------------
# Screenplay.
# ---------------------------------------------------------------------------
def tell(
    project: Project,
    terrain: Terrain,
    strategy: Strategy,
    rhyme_text: str,
    lead_name: str = "Cal",
    lead_gender: str = "boy",
    friend_name: str = "Mabel",
    friend_gender: str = "girl",
    helper_name: str = "Gran",
    helper_gender: str = "girl",
    lead_trait: str = "bold",
    friend_trait: str = "steady",
    delay: int = 0,
) -> World:
    world = World()
    lead = world.add(Entity(
        id="lead",
        kind="character",
        type=lead_gender,
        label=lead_name,
        phrase=lead_name,
        role="lead",
        traits=[lead_trait],
        attrs={"name": lead_name},
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type=friend_gender,
        label=friend_name,
        phrase=friend_name,
        role="friend",
        traits=[friend_trait],
        attrs={"name": friend_name},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type="mother" if helper_gender == "girl" else "father",
        label=helper_name,
        phrase=helper_name,
        role="helper",
        attrs={"name": helper_name},
    ))
    project_ent = world.add(Entity(
        id="project",
        type="project",
        label=project.label,
        phrase=project.phrase,
        role="project",
        tags=set(project.tags),
    ))
    terrain_ent = world.add(Entity(
        id="terrain",
        type="terrain",
        label=terrain.place,
        phrase=terrain.place,
        role="terrain",
        tags=set(terrain.tags),
    ))

    world.facts["lead_name"] = lead_name
    world.facts["friend_name"] = friend_name
    world.facts["helper_name"] = helper_name

    introduce(world, lead, friend, project, terrain)
    set_out(world, lead, friend, project, terrain)

    world.para()
    rush_and_bumble(world, lead, friend, project_ent, terrain_ent)
    flashback(world, lead, friend, helper, rhyme_text)

    world.para()
    choose_strategy(world, lead, friend, strategy, project, rhyme_text)

    saved = is_saved(project, terrain, strategy, delay)
    if saved:
        carry_in_parts(world, lead, friend, strategy, project, terrain, delay)
        triumph(world, lead, friend, project, terrain)
        outcome = "saved"
    else:
        setback(world, lead, friend, project, terrain, strategy)
        outcome = "failed"

    world.facts.update(
        project_cfg=project,
        terrain_cfg=terrain,
        strategy_cfg=strategy,
        rhyme_text=rhyme_text,
        lead=lead,
        friend=friend,
        helper=helper,
        project=project_ent,
        terrain=terrain_ent,
        outcome=outcome,
        bumbled=lead.memes["has_bumbled"] >= THRESHOLD,
        recalled=lead.memes["memory"] >= THRESHOLD or friend.memes["memory"] >= THRESHOLD,
        delay=delay,
        saved=saved,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A.
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "installment": [
        (
            "What is an installment?",
            "An installment is one small part of a bigger job or payment. You do one part, and then another, instead of trying to finish everything at once.",
        )
    ],
    "teamwork": [
        (
            "Why can teamwork help with a big job?",
            "Two people can share the weight, watch for trouble, and take turns. That often makes a hard job safer and easier.",
        )
    ],
    "wind": [
        (
            "Why is wind a problem for big light things?",
            "Wind can push and twist big light things because they catch lots of air. That makes them harder to carry safely.",
        )
    ],
    "wagon": [
        (
            "Why does a wagon help move something heavy?",
            "A wagon lets wheels carry the weight along the ground. That means people do not have to hold all the weight in their arms.",
        )
    ],
    "bridge": [
        (
            "Why must people be careful on a narrow bridge?",
            "A narrow bridge gives less room to balance and turn. A long awkward load can bump and wobble there.",
        )
    ],
    "mud": [
        (
            "Why is mud hard to walk through?",
            "Mud can grab at your boots and make your steps slow and slippery. That makes carrying things harder.",
        )
    ],
    "kite": [
        (
            "What does a kite need to fly well?",
            "A kite needs wind, a good shape, and a tail or line that stays balanced. If part of it twists, it may not fly right.",
        )
    ],
    "drum": [
        (
            "How does a drum make sound?",
            "A drum makes sound when its tight skin is struck and begins to shake. Those shakes move the air and make a noise you can hear.",
        )
    ],
    "banner": [
        (
            "What is a banner?",
            "A banner is a long piece of cloth with words, colors, or pictures on it. People hang it up so others can see it from far away.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "installment",
    "teamwork",
    "wind",
    "wagon",
    "bridge",
    "mud",
    "kite",
    "drum",
    "banner",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    project = f["project_cfg"]
    terrain = f["terrain_cfg"]
    lead = f["lead"]
    friend = f["friend"]
    rhyme_text = f["rhyme_text"]
    return [
        f'Write a Tall Tale for a young child that uses the words "installment" and "bumble" and includes a flashback, a friendship, and a rhyme.',
        f"Tell a big-hearted story where {f['lead_name']} and {f['friend_name']} try to move {project.phrase} across {terrain.place}, bumble the first try, remember an old rhyme, and succeed together.",
        f'Write a playful tall tale in which two friends solve a giant problem little by little, using this rhyme: "{rhyme_text}"',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    lead = f["lead"]
    friend = f["friend"]
    project = f["project_cfg"]
    terrain = f["terrain_cfg"]
    strategy = f["strategy_cfg"]
    rhyme_text = f["rhyme_text"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two friends, {f['lead_name']} and {f['friend_name']}, who made a giant {project.label} for the fair. Their friendship matters because they only solve the big problem once they work together.",
        ),
        (
            f"What big thing were they trying to move?",
            f"They were trying to move {project.phrase} to {terrain.place}. It was so oversized that carrying it like an ordinary object was asking for trouble.",
        ),
        (
            f"What happened when {f['lead_name']} tried to hurry?",
            f"{f['lead_name']} tried to move the whole giant load in one grand rush and began to bumble. That put {project.weak_spot} at risk because {terrain.risk} was already making the path harder.",
        ),
        (
            "What was the flashback about?",
            f"The flashback went back to the day the friends first worked well together, when rolling apples had to be saved in many small trips. That memory reminded them that big jobs can be finished safely a little at a time.",
        ),
        (
            "What rhyme helped them?",
            f'The rhyme was "{rhyme_text}" It gave them a simple way to remember not to rush when the load was too big.',
        ),
    ]
    if outcome == "saved":
        qa.append(
            (
                "How did they solve the problem?",
                f"{strategy.qa_text} They changed from one wild rush to a steadier method, and that is what let the giant {project.label} reach the fair safely.",
            )
        )
        qa.append(
            (
                "Why is the word installment important in this story?",
                f"In this story, installment means one small part of a big job. The friends win by doing the hauling in installment after installment instead of trying to do everything at once.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the giant {project.label} safely in place at {terrain.place}. The final image shows that friendship and patience were stronger than hurry.",
            )
        )
    else:
        qa.append(
            (
                "Did the first plan work?",
                f"No, it did not. The plan stayed too rough for the size of the load, so the giant {project.label} was damaged instead of saved.",
            )
        )
        qa.append(
            (
                "What did the friends learn even though the day went badly?",
                f"They learned that rushing makes a giant problem worse. They also learned that their friendship held firm, because they stayed together and promised to choose smaller, steadier steps next time.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"installment", "teamwork"} | set(f["project_cfg"].tags) | set(f["terrain_cfg"].tags)
    tags |= set(f["strategy_cfg"].tags)
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


# ---------------------------------------------------------------------------
# Trace.
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
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
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Compatibility gate.
risky_combo(P, T) :- project(P), terrain(T), risky_on(P, T).
sensible(S)       :- strategy(S), sense(S, V), sense_min(M), V >= M.
need(P, T, N)     :- size(P, A), risk_score(T, B), N = A + B.
fit(P, T, installments) :- risky_combo(P, T).
fit(P, T, S)      :- strategy(S), S != installments, risky_combo(P, T),
                     need(P, T, N), power(S, Pwr), Pwr >= N - 2, sensible(S).
valid(P, T, S)    :- fit(P, T, S).

% Outcome model.
severity(N)       :- chosen_project(P), chosen_terrain(T), delay(D),
                     size(P, A), risk_score(T, B), N = A + B + D.
saved             :- chosen_strategy(installments).
saved             :- chosen_strategy(S), S != installments, power(S, Pwr),
                     severity(N), Pwr >= N - 1.
outcome(saved)    :- saved.
outcome(failed)   :- not saved.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, project in PROJECTS.items():
        lines.append(asp.fact("project", pid))
        lines.append(asp.fact("size", pid, project.size))
        for terrain_id in sorted(project.risky_on):
            lines.append(asp.fact("risky_on", pid, terrain_id))
    for tid, terrain in TERRAINS.items():
        lines.append(asp.fact("terrain", tid))
        lines.append(asp.fact("risk_score", tid, terrain.risk_score))
    for sid, strategy in STRATEGIES.items():
        lines.append(asp.fact("strategy", sid))
        lines.append(asp.fact("sense", sid, strategy.sense))
        lines.append(asp.fact("power", sid, strategy.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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
    return sorted(item[0] for item in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_project", params.project),
            asp.fact("chosen_terrain", params.terrain),
            asp.fact("chosen_strategy", params.strategy),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos():")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_sensible = {sid for sid, strategy in STRATEGIES.items() if strategy.sense >= SENSE_MIN}
    asp_sens = set(asp_sensible())
    if py_sensible == asp_sens:
        print(f"OK: sensible strategies match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible strategies: clingo={sorted(asp_sens)} python={sorted(py_sensible)}")

    cases = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)
    bad = 0
    for params in cases:
        py = "saved" if is_saved(PROJECTS[params.project], TERRAINS[params.terrain], STRATEGIES[params.strategy], params.delay) else "failed"
        asp = asp_outcome(params)
        if py != asp:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Smoke test produced an empty story.")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


# ---------------------------------------------------------------------------
# CLI.
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale friendship storyworld with a flashback, a rhyme, and a giant job done in installments."
    )
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--terrain", choices=TERRAINS)
    ap.add_argument("--strategy", choices=STRATEGIES)
    ap.add_argument("--rhyme", choices=RHYMES)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="extra trouble before the friends settle on a plan")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [name for name in pool if name != avoid]
    return rng.choice(names), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.project and args.terrain and args.strategy:
        project = PROJECTS[args.project]
        terrain = TERRAINS[args.terrain]
        strategy = STRATEGIES[args.strategy]
        if not (args.terrain in project.risky_on and strategy_fits(project, terrain, strategy)):
            raise StoryError(explain_rejection(project, terrain, strategy))
    if args.strategy and STRATEGIES[args.strategy].sense < SENSE_MIN:
        strategy = STRATEGIES[args.strategy]
        raise StoryError(
            f"(Refusing strategy '{strategy.id}': it scores too low on common sense for this world. Try installments or wagon.)"
        )

    combos = [
        combo for combo in valid_combos()
        if (args.project is None or combo[0] == args.project)
        and (args.terrain is None or combo[1] == args.terrain)
        and (args.strategy is None or combo[2] == args.strategy)
    ]
    if not combos:
        if args.project and args.terrain and args.strategy:
            raise StoryError(explain_rejection(PROJECTS[args.project], TERRAINS[args.terrain], STRATEGIES[args.strategy]))
        raise StoryError("(No valid combination matches the given options.)")

    project_id, terrain_id, strategy_id = rng.choice(sorted(combos))
    lead_name, lead_gender = _pick_name(rng)
    friend_name, friend_gender = _pick_name(rng, avoid=lead_name)
    helper_name = "Gran"
    helper_gender = "girl"
    rhyme = args.rhyme or rng.choice(sorted(RHYMES))
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        project=project_id,
        terrain=terrain_id,
        strategy=strategy_id,
        lead_name=lead_name,
        lead_gender=lead_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        rhyme=rhyme,
        lead_trait=rng.choice(TRAITS),
        friend_trait=rng.choice(TRAITS),
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.project not in PROJECTS:
        raise StoryError(f"(Unknown project '{params.project}'.)")
    if params.terrain not in TERRAINS:
        raise StoryError(f"(Unknown terrain '{params.terrain}'.)")
    if params.strategy not in STRATEGIES:
        raise StoryError(f"(Unknown strategy '{params.strategy}'.)")
    if params.rhyme not in RHYMES:
        raise StoryError(f"(Unknown rhyme '{params.rhyme}'.)")

    project = PROJECTS[params.project]
    terrain = TERRAINS[params.terrain]
    strategy = STRATEGIES[params.strategy]
    if params.terrain not in project.risky_on or not strategy_fits(project, terrain, strategy):
        raise StoryError(explain_rejection(project, terrain, strategy))

    world = tell(
        project=project,
        terrain=terrain,
        strategy=strategy,
        rhyme_text=RHYMES[params.rhyme],
        lead_name=params.lead_name,
        lead_gender=params.lead_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        lead_trait=params.lead_trait,
        friend_trait=params.friend_trait,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible strategies: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (project, terrain, strategy) combos:\n")
        for project_id, terrain_id, strategy_id in combos:
            print(f"  {project_id:8} {terrain_id:8} {strategy_id}")
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
            outcome = "saved" if is_saved(PROJECTS[p.project], TERRAINS[p.terrain], STRATEGIES[p.strategy], p.delay) else "failed"
            header = f"### {p.project} on {p.terrain} with {p.strategy} ({outcome})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
