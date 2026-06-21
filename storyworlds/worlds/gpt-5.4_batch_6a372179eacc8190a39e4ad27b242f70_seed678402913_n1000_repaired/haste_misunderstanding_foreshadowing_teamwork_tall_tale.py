#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/haste_misunderstanding_foreshadowing_teamwork_tall_tale.py
=====================================================================================

A standalone storyworld for a child-facing tall tale about haste, a
misunderstanding, a warning sign that foreshadows trouble, and a teamwork fix.

In this tiny world, children live in an exaggerated farm country where sheets are
big as sails, pumpkins are round as wagons, and weather gives its warnings loud
enough to sound like gossip. A grown-up gives a simple job. If the hero moves in
haste, the words are misheard, the wrong tool is fetched, and the problem grows
until teamwork puts it right. If the helper is calm enough and the haste is not
too fierce, the misunderstanding is caught before the trouble starts.

Run it
------
    python storyworlds/worlds/gpt-5.4/haste_misunderstanding_foreshadowing_teamwork_tall_tale.py
    python storyworlds/worlds/gpt-5.4/haste_misunderstanding_foreshadowing_teamwork_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4/haste_misunderstanding_foreshadowing_teamwork_tall_tale.py --job sheet --haste haste
    python storyworlds/worlds/gpt-5.4/haste_misunderstanding_foreshadowing_teamwork_tall_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/haste_misunderstanding_foreshadowing_teamwork_tall_tale.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
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
CALM_TRAITS = {"steady", "careful", "patient"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
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
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def title_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    flavor: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Warning:
    id: str
    sign: str
    line: str
    jobs: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Job:
    id: str
    label: str
    phrase: str
    needs: str
    wrong: str
    ask: str
    misheard: str
    result: str
    trouble: str
    severity: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    text: str
    qa_text: str
    jobs: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_trouble_spreads(world: World) -> list[str]:
    obj = world.entities.get("job")
    if obj is None or obj.meters["loose"] < THRESHOLD:
        return []
    sig = ("trouble_spreads", obj.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    obj.meters["risk"] += 1
    for role in ("hero", "helper"):
        if role in world.entities:
            world.get(role).memes["alarm"] += 1
    if "elder" in world.entities:
        world.get("elder").memes["concern"] += 1
    return ["__risk__"]


CAUSAL_RULES = [Rule(name="trouble_spreads", tag="physical", apply=_r_trouble_spreads)]


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


PLACES = {
    "prairie": Place(
        id="prairie",
        label="the prairie farm",
        flavor="where the grass leaned so far in the wind it looked like green water",
        affords={"sheet", "wagon"},
    ),
    "orchard": Place(
        id="orchard",
        label="the hill orchard",
        flavor="where apple trees stood in rows like soldiers and each apple was nearly hat-sized",
        affords={"wagon", "banner"},
    ),
    "riverside": Place(
        id="riverside",
        label="the riverside ranch",
        flavor="where the reeds whispered louder than grown-ups and the barns looked broad as little ships",
        affords={"sheet", "banner"},
    ),
}

WARNINGS = {
    "windmill": Warning(
        id="windmill",
        sign="the windmill squealed like a fiddle with a loose string",
        line="When the windmill sings before supper, something big will try to fly.",
        jobs={"sheet", "banner"},
        tags={"wind", "foreshadowing"},
    ),
    "thunder": Warning(
        id="thunder",
        sign="a long ribbon of thunder rolled beyond the fields",
        line="That kind of grumble means hurry wisely, not wildly.",
        jobs={"sheet", "wagon", "banner"},
        tags={"storm", "foreshadowing"},
    ),
    "dust": Warning(
        id="dust",
        sign="little dust-whirls hopped along the road like brown rabbits",
        line="Dust-whirls are the weather's way of practicing for mischief.",
        jobs={"wagon", "banner"},
        tags={"wind", "foreshadowing"},
    ),
}

JOBS = {
    "sheet": Job(
        id="sheet",
        label="the town wash sheet",
        phrase="a wash sheet so wide it could have shaded three cows and a milk pail",
        needs="rope",
        wrong="soap",
        ask="Fetch the rope for the wash sheet!",
        misheard="Fetch the soap for the wash sheet!",
        result="The soap made the knots slide and the giant sheet bellied out like a sail.",
        trouble="The sheet tugged at the clothesline and tried to climb into the sky.",
        severity=2,
        tags={"sheet", "laundry", "wind"},
    ),
    "wagon": Job(
        id="wagon",
        label="the pumpkin wagon",
        phrase="a pumpkin wagon with wheels taller than a fence rail",
        needs="stakes",
        wrong="cakes",
        ask="Fetch the stakes for the pumpkin wagon!",
        misheard="Fetch the cakes for the pumpkin wagon!",
        result="The sweet cakes drew every goat in shouting distance, and the wagon jolted loose.",
        trouble="The wagon began to roll down the hill with a pumpkin wobbling in it like a second moon.",
        severity=3,
        tags={"wagon", "pumpkin", "hill"},
    ),
    "banner": Job(
        id="banner",
        label="the harvest banner",
        phrase="a harvest banner long enough to wave across half the lane",
        needs="pegs",
        wrong="eggs",
        ask="Fetch the pegs for the harvest banner!",
        misheard="Fetch the eggs for the harvest banner!",
        result="The eggs cracked, the cloth turned slick, and the banner flapped hard enough to slap the fence.",
        trouble="The banner snapped loose at one corner and thrashed like a cloth dragon.",
        severity=2,
        tags={"banner", "festival", "wind"},
    ),
}

FIXES = {
    "team_pull": Fix(
        id="team_pull",
        label="a team pull",
        text="set their heels, took hold together, and pulled until the wild thing remembered it belonged on the ground",
        qa_text="They all pulled together until it was safe again.",
        jobs={"sheet", "wagon", "banner"},
        tags={"teamwork", "pull"},
    ),
    "ladder_loop": Fix(
        id="ladder_loop",
        label="a ladder and looped line",
        text="worked as a team, with one holding the ladder steady while another tossed a looped line over the flapping top and cinched it down",
        qa_text="They used a steady ladder and a looped line together.",
        jobs={"sheet", "banner"},
        tags={"teamwork", "ladder"},
    ),
    "shoulder_chock": Fix(
        id="shoulder_chock",
        label="a shoulder-and-chock stop",
        text="braced their shoulders against the wheel while another person slid stout chocks under it, and the whole rumbling load gave up its run",
        qa_text="They stopped the wheel together and chocked it.",
        jobs={"wagon"},
        tags={"teamwork", "wagon"},
    ),
}

HASTE_LEVELS = {"steady": 0, "quick": 1, "haste": 2}
GIRL_NAMES = ["Lila", "Mara", "Nell", "Ada", "June", "Dora", "Cora", "Molly"]
BOY_NAMES = ["Finn", "Eli", "Toby", "Ned", "Cal", "Jesse", "Beau", "Otis"]
TRAITS = ["steady", "careful", "patient", "bright", "cheerful", "stouthearted"]


@dataclass
class StoryParams:
    place: str
    warning: str
    job: str
    fix: str
    haste: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    elder: str
    helper_trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="prairie",
        warning="windmill",
        job="sheet",
        fix="ladder_loop",
        haste="haste",
        hero="Finn",
        hero_gender="boy",
        helper="Lila",
        helper_gender="girl",
        elder="mother",
        helper_trait="careful",
    ),
    StoryParams(
        place="orchard",
        warning="dust",
        job="wagon",
        fix="shoulder_chock",
        haste="haste",
        hero="Mara",
        hero_gender="girl",
        helper="Otis",
        helper_gender="boy",
        elder="father",
        helper_trait="steady",
    ),
    StoryParams(
        place="riverside",
        warning="thunder",
        job="banner",
        fix="team_pull",
        haste="quick",
        hero="Ada",
        hero_gender="girl",
        helper="Ned",
        helper_gender="boy",
        elder="mother",
        helper_trait="patient",
    ),
    StoryParams(
        place="prairie",
        warning="thunder",
        job="wagon",
        fix="team_pull",
        haste="quick",
        hero="Eli",
        hero_gender="boy",
        helper="June",
        helper_gender="girl",
        elder="father",
        helper_trait="careful",
    ),
]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for warning_id, warning in WARNINGS.items():
            for job_id, job in JOBS.items():
                for fix_id, fix in FIXES.items():
                    if job_id not in place.affords:
                        continue
                    if job_id not in warning.jobs:
                        continue
                    if job_id not in fix.jobs:
                        continue
                    combos.append((place_id, warning_id, job_id, fix_id))
    return combos


def calm_enough(helper_trait: str) -> bool:
    return helper_trait in CALM_TRAITS


def outcome_of(params: StoryParams) -> str:
    haste_value = HASTE_LEVELS[params.haste]
    if calm_enough(params.helper_trait) and haste_value <= 1:
        return "averted"
    return "scramble"


def predict_trouble(job_id: str) -> dict:
    job = JOBS[job_id]
    return {"severity": job.severity, "loose": True}


def introduce(world: World, hero: Entity, helper: Entity, elder: Entity, job: Job) -> None:
    world.say(
        f"In {world.place.label}, {world.place.flavor}. Folks said {job.phrase}, "
        f"and on that day {hero.id}, {helper.id}, and {hero.pronoun('possessive')} "
        f"{elder.title_word} meant to keep {job.label} from turning the afternoon upside down."
    )


def foreshadow(world: World, warning: Warning, elder: Entity) -> None:
    world.say(
        f"Before anybody lifted a hand, {warning.sign}. {elder.title_word.capitalize()} "
        f"heard it first and said, \"{warning.line}\""
    )


def task(world: World, elder: Entity, hero: Entity, job: Job, haste: str) -> None:
    hero.memes["duty"] += 1
    phrase = {
        "steady": "without any rush at all",
        "quick": "pretty quick",
        "haste": "in such haste that even the chickens stepped aside",
    }[haste]
    world.say(
        f"Then {elder.title_word} pointed at {job.label} and called, "
        f"\"{job.ask}\" {hero.id} jumped to obey {phrase}."
    )


def misunderstand(world: World, hero: Entity, helper: Entity, job: Job) -> None:
    hero.memes["haste"] += 1
    hero.memes["confidence"] += 1
    world.say(
        f"But the wind chewed the words and {hero.id} heard, \"{job.misheard}\" "
        f"So {hero.pronoun()} came back hugging {job.wrong} instead of {job.needs}."
    )
    helper.memes["suspicion"] += 1


def catch_before_trouble(world: World, helper: Entity, hero: Entity, elder: Entity, job: Job) -> None:
    helper.memes["care"] += 1
    hero.memes["embarrassment"] += 1
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"{helper.id} blinked once, then laughed softly. \"{job.wrong.capitalize()} won't hold {job.label},\" "
        f"{helper.pronoun()} said. \"{elder.title_word.capitalize()} asked for {job.needs}.\""
    )
    world.say(
        f"{hero.id} stopped short, listened again, and felt the heat rise in "
        f"{hero.pronoun('possessive')} cheeks. Even in haste, {hero.pronoun()} knew a good helper was better than a proud guess."
    )
    world.say(
        f"So the two children fetched the real {job.needs} together and fastened "
        f"{job.label} snug and neat before the weather could make a liar out of the warning."
    )


def use_wrong_tool(world: World, hero: Entity, job_ent: Entity, job: Job) -> None:
    hero.memes["embarrassment"] += 1
    job_ent.meters["loose"] += 1
    job_ent.meters["trouble"] += 1
    propagate(world, narrate=False)
    world.say(job.result)
    world.say(job.trouble)


def teamwork_fix(world: World, hero: Entity, helper: Entity, elder: Entity, job_ent: Entity, fix: Fix, job: Job) -> None:
    hero.memes["trust"] += 1
    helper.memes["trust"] += 1
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    elder.memes["pride"] += 1
    job_ent.meters["loose"] = 0.0
    job_ent.meters["risk"] = 0.0
    world.say(
        f"No one wasted a breath on blaming. {elder.title_word.capitalize()}, {helper.id}, and {hero.id} {fix.text}."
    )
    world.say(
        f"When it was over, {job.label} stayed put at last, and the trouble that had looked enormous shrank back down to ordinary size."
    )


def ending(world: World, hero: Entity, helper: Entity, elder: Entity, outcome: str, job: Job) -> None:
    if outcome == "averted":
        world.say(
            f"That evening the clouds went past with nothing worse than a grumble. "
            f"{hero.id} grinned at {helper.id} and said the day had taught {hero.pronoun('object')} that haste could turn one little word sideways."
        )
        world.say(
            f"After that, whenever work came whistling across the yard, the children listened twice and moved once, and even the wind had less to laugh about."
        )
    else:
        world.say(
            f"{elder.title_word.capitalize()} ruffled both their hair and said, "
            f"\"Big jobs don't care who started the muddle. They care who stands shoulder to shoulder to mend it.\""
        )
        world.say(
            f"From then on, when a warning sign creaked or thunder grumbled, {hero.id} and {helper.id} traded haste for teamwork first, and {job.label} never again got the jump on them."
        )


def tell(
    place: Place,
    warning: Warning,
    job: Job,
    fix: Fix,
    haste: str,
    hero_name: str,
    hero_gender: str,
    helper_name: str,
    helper_gender: str,
    elder_type: str,
    helper_trait: str,
) -> World:
    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero"))
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            type=helper_gender,
            label=helper_name,
            role="helper",
            traits=[helper_trait],
        )
    )
    elder = world.add(Entity(id="elder", kind="character", type=elder_type, label="the elder", role="elder"))
    job_ent = world.add(Entity(id="job", kind="thing", type="job", label=job.label, phrase=job.phrase))

    introduce(world, hero, helper, elder, job)
    foreshadow(world, warning, elder)

    world.para()
    task(world, elder, hero, job, haste)
    misunderstand(world, hero, helper, job)

    outcome = outcome_of(
        StoryParams(
            place=place.id,
            warning=warning.id,
            job=job.id,
            fix=fix.id,
            haste=haste,
            hero=hero_name,
            hero_gender=hero_gender,
            helper=helper_name,
            helper_gender=helper_gender,
            elder=elder_type,
            helper_trait=helper_trait,
        )
    )

    if outcome == "averted":
        catch_before_trouble(world, helper, hero, elder, job)
    else:
        world.para()
        use_wrong_tool(world, hero, job_ent, job)
        world.para()
        teamwork_fix(world, hero, helper, elder, job_ent, fix, job)

    world.para()
    ending(world, hero, helper, elder, outcome, job)

    world.facts.update(
        place=place,
        warning=warning,
        job_cfg=job,
        fix=fix,
        hero=hero,
        helper=helper,
        elder=elder,
        job=job_ent,
        haste=haste,
        outcome=outcome,
        predicted=predict_trouble(job.id),
        misheard=(job.needs, job.wrong),
        teamwork_used=(outcome == "scramble"),
    )
    return world


KNOWLEDGE = {
    "foreshadowing": [
        (
            "What is foreshadowing in a story?",
            "Foreshadowing is when a story gives a little hint early on about something that may matter later. A creaking windmill or a low rumble of thunder can warn readers to watch for trouble.",
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone hears, sees, or explains something the wrong way. Small mistakes can grow into big problems if nobody stops to check.",
        )
    ],
    "teamwork": [
        (
            "Why does teamwork help with big jobs?",
            "Teamwork helps because different people can notice different things and share the hard part. A big problem often feels smaller when everyone works together.",
        )
    ],
    "haste": [
        (
            "What does haste mean?",
            "Haste means rushing too fast. When people move in haste, they can miss important words or details.",
        )
    ],
    "wind": [
        (
            "Why is strong wind hard for loose things?",
            "Strong wind pushes and tugs on loose cloth and light objects. If something is not tied down well, wind can make it flap, slide, or fly away.",
        )
    ],
    "storm": [
        (
            "Why do people watch the sky before a storm?",
            "People watch the sky because storms often give warnings first, like thunder, gusts, or dark clouds. Those signs help them get ready before the trouble starts.",
        )
    ],
    "wagon": [
        (
            "Why can a wagon roll if it is not secured?",
            "A wagon can roll because its wheels are made to turn easily. On a hill, even a small push can start it moving.",
        )
    ],
    "laundry": [
        (
            "Why can a big sheet act like a sail?",
            "A big sheet can catch a lot of air. When wind fills it, the cloth can pull hard just like a sail on a boat.",
        )
    ],
    "festival": [
        (
            "Why does a banner need to be fastened tightly?",
            "A banner is wide and light, so wind can snap at it from many sides. Tight pegs and strong lines keep it from whipping loose.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "haste",
    "misunderstanding",
    "foreshadowing",
    "teamwork",
    "storm",
    "wind",
    "wagon",
    "laundry",
    "festival",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    job = f["job_cfg"]
    warning = f["warning"]
    if f["outcome"] == "averted":
        return [
            f'Write a tall-tale style story for a young child that includes the word "haste" and uses misunderstanding, foreshadowing, and teamwork.',
            f"Tell a farm tall tale where {hero.label} mishears a job about {job.label}, but {helper.label} catches the mistake before trouble starts.",
            f"Write a windy story where {warning.sign} foreshadows trouble, yet the children solve the problem by listening carefully together.",
        ]
    return [
        f'Write a tall-tale style story for a young child that includes the word "haste" and uses misunderstanding, foreshadowing, and teamwork.',
        f"Tell a farm tall tale where {hero.label} mishears a job about {job.label}, and the mistake grows into a big scramble before teamwork saves the day.",
        f"Write a story where {warning.sign} warns of trouble, a wrong word causes a mess, and children and a grown-up fix it together.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    elder = f["elder"]
    job = f["job_cfg"]
    warning = f["warning"]
    needs, wrong = f["misheard"]
    out: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, {helper.label}, and their {elder.title_word} working around {job.label}. They live in a place exaggerated like a tall tale, where ordinary chores can feel enormous.",
        ),
        (
            "What warning sign came before the trouble?",
            f"The warning sign was that {warning.sign}. That moment foreshadowed that the weather and the job might soon get rowdy.",
        ),
        (
            f"What misunderstanding happened to {hero.label}?",
            f"{hero.label} was in haste and heard {wrong} instead of {needs}. The mix-up mattered because {job.label} needed the right thing to stay safe.",
        ),
    ]
    if f["outcome"] == "averted":
        out.append(
            (
                f"How was the problem solved before it became big?",
                f"{helper.label} noticed the mistake and spoke up before the wrong item was used. Because they checked the words together, the misunderstanding stopped early and the warning never grew into real trouble.",
            )
        )
        out.append(
            (
                "What changed by the end of the story?",
                f"By the end, the children had learned to slow their ears even when their feet wanted to run. They still worked quickly, but not in blind haste.",
            )
        )
    else:
        out.append(
            (
                f"What happened when the wrong {wrong} was used?",
                f"{job.result} {job.trouble} The misunderstanding turned into a physical problem because the wrong item could not do the right job.",
            )
        )
        out.append(
            (
                "How did teamwork help?",
                f"{elder.title_word.capitalize()}, {helper.label}, and {hero.label} worked together instead of arguing. Their shared effort solved the problem faster because each person held, pulled, or steadied a different part.",
            )
        )
        out.append(
            (
                "What lesson did the hero learn?",
                f"{hero.label} learned that haste can bend words out of shape. The story shows that listening carefully and working with others is wiser than charging ahead alone.",
            )
        )
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"haste", "misunderstanding", "foreshadowing", "teamwork"}
    tags |= set(world.facts["warning"].tags)
    tags |= set(world.facts["job_cfg"].tags)
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(place_id: str, warning_id: str, job_id: str, fix_id: str) -> str:
    if job_id not in PLACES[place_id].affords:
        return (
            f"(No story: {PLACES[place_id].label} does not host the {JOBS[job_id].label}. "
            f"Pick a place that reasonably fits that chore.)"
        )
    if job_id not in WARNINGS[warning_id].jobs:
        return (
            f"(No story: the warning sign '{warning_id}' does not foreshadow trouble for the {JOBS[job_id].label}. "
            f"Choose a warning that matches that kind of danger.)"
        )
    if job_id not in FIXES[fix_id].jobs:
        return (
            f"(No story: the fix '{fix_id}' is not a sensible way to secure the {JOBS[job_id].label}. "
            f"Choose a fix that fits the job.)"
        )
    return "(No story: this combination does not fit the world.)"


ASP_RULES = r"""
valid(P, W, J, F) :- place(P), warning(W), job(J), fix(F),
                     affords(P, J), warns(W, J), fixes(F, J).

calm(T) :- helper_trait(T), calm_trait(T).
averted :- haste_value(H), H <= 1, calm(T).
scramble :- not averted.

outcome(averted) :- averted.
outcome(scramble) :- scramble.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for job_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, job_id))
    for warning_id, warning in WARNINGS.items():
        lines.append(asp.fact("warning", warning_id))
        for job_id in sorted(warning.jobs):
            lines.append(asp.fact("warns", warning_id, job_id))
    for job_id in JOBS:
        lines.append(asp.fact("job", job_id))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        for job_id in sorted(fix.jobs):
            lines.append(asp.fact("fixes", fix_id, job_id))
    for trait in sorted(TRAITS):
        lines.append(asp.fact("helper_trait", trait))
    for trait in sorted(CALM_TRAITS):
        lines.append(asp.fact("calm_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("haste_value", HASTE_LEVELS[params.haste]),
            asp.fact("helper_trait", params.helper_trait),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
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
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)
    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            emit(sample, trace=False, qa=False, header="")
        finally:
            sys.stdout = old
        if not sample.story.strip():
            raise StoryError("empty story")
        print("OK: smoke-tested generate() and emit().")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale storyworld: haste causes a misunderstanding, a warning foreshadows trouble, and teamwork sets things right."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--warning", choices=sorted(WARNINGS))
    ap.add_argument("--job", choices=sorted(JOBS))
    ap.add_argument("--fix", choices=sorted(FIXES))
    ap.add_argument("--haste", choices=sorted(HASTE_LEVELS))
    ap.add_argument("--elder", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check Python/ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.warning and args.job and args.fix:
        combo = (args.place, args.warning, args.job, args.fix)
        if combo not in set(valid_combos()):
            raise StoryError(explain_rejection(*combo))

    combos = [
        c
        for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.warning is None or c[1] == args.warning)
        and (args.job is None or c[2] == args.job)
        and (args.fix is None or c[3] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, warning, job, fix = rng.choice(sorted(combos))
    haste = args.haste or rng.choice(sorted(HASTE_LEVELS))
    hero_gender = rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["girl", "boy"])
    hero = _pick_name(rng, hero_gender)
    helper = _pick_name(rng, helper_gender, avoid=hero)
    elder = args.elder or rng.choice(["mother", "father"])
    helper_trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        warning=warning,
        job=job,
        fix=fix,
        haste=haste,
        hero=hero,
        hero_gender=hero_gender,
        helper=helper,
        helper_gender=helper_gender,
        elder=elder,
        helper_trait=helper_trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        warning = WARNINGS[params.warning]
        job = JOBS[params.job]
        fix = FIXES[params.fix]
        _ = HASTE_LEVELS[params.haste]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter: {err.args[0]})") from None

    if (params.place, params.warning, params.job, params.fix) not in set(valid_combos()):
        raise StoryError(explain_rejection(params.place, params.warning, params.job, params.fix))

    world = tell(
        place=place,
        warning=warning,
        job=job,
        fix=fix,
        haste=params.haste,
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        elder_type=params.elder,
        helper_trait=params.helper_trait,
    )
    return StorySample(
        params=params,
        story=world.render().replace(" hero", f" {params.hero}").replace(" helper", f" {params.helper}"),
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, warning, job, fix) combos:\n")
        for place, warning, job, fix in combos:
            print(f"  {place:10} {warning:9} {job:7} {fix}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            header = f"### {p.hero} and {p.helper}: {p.job} at {p.place} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
