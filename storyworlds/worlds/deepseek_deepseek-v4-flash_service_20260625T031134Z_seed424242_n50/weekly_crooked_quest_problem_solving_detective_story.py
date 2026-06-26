#!/usr/bin/env python3
"""
storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260625T031134Z_seed424242_n50/weekly_crooked_quest_problem_solving_detective_story.py
=================================================================================================================================

A standalone *story world* sketch based on a weekly crooked quest, using problem-solving
in the style of a detective story. Each week in Sunnyville, something goes crooked, and
young detective Kit helps solve the mystery through careful observation and reasoning.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "character"
    type: str = "person"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    # Two numeric dimensions
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandma", "teacher", "librarian"}
        male = {"boy", "father", "grandpa", "postman", "shopkeeper"}
        neutral = {"detective", "kid"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in neutral:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    name: str
    place: str = ""
    season: str = "spring"
    weekly_event: str = ""


@dataclass
class Mystery:
    """A crooked thing that happens -- the problem to solve."""
    id: str
    name: str
    problem: str
    solution: str
    clue_phrase: str
    reason_phrase: str
    crookedness: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Evidence:
    """A piece of evidence the detective gathers."""
    id: str
    label: str
    phrase: str
    reveals: str
    location: str = ""
    tag: str = ""


custom_week_events: dict[str, str] = {}


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.mystery: Optional[Mystery] = None
        self.evidence_found: list[str] = []
        self.solved: bool = False

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
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
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.mystery = self.mystery
        clone.evidence_found = list(self.evidence_found)
        clone.solved = self.solved
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_curiosity(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["curious"] < THRESHOLD:
            continue
        sig = ("curious", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append(f"Little detective {actor.id} felt their curiosity grow.")
    return out


def _r_solve(world: World) -> list[str]:
    if world.solved:
        return []
    sig = ("solve_check")
    if sig in world.fired:
        return []
    mystery = world.mystery
    if not mystery:
        return []
    if len(world.evidence_found) >= 3:
        world.fired.add(sig)
        world.solved = True
        return [f"Now {world.get('detective').id} understood. The answer was clear."]
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="curiosity", tag="mental", apply=_r_curiosity),
    Rule(name="solve", tag="mental", apply=_r_solve),
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
                produced.extend(s for s in sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Verbs / screenplay
# ---------------------------------------------------------------------------
def introduce_detective(world: World, name: str) -> None:
    det = world.add(Entity(
        id="detective",
        kind="character",
        type="detective",
        label=name,
        phrase=f"a young detective named {name}",
        traits=["curious", "clever", "observant"],
    ))
    world.say(f"In Sunnyville lived a young detective named {name}, who noticed "
              f"everything -- even things that seemed small.")
    world.say(f"Every week, {name} helped solve the crooked little mysteries that happened "
              f"around town.")
    det.memes["curious"] = 1.0


def weekly_intro(world: World, mystery: Mystery) -> None:
    world.mystery = mystery
    season = world.setting.season
    event = world.setting.weekly_event
    world.say(f"One {season} day, during the {event}, something went crooked in Sunnyville.")
    world.say(f"{mystery.problem}")
    world.facts["problem"] = mystery.problem
    world.facts["crookedness"] = mystery.crookedness


def hero_arrives(world: World, hero_name: str, mystery: Mystery) -> None:
    hero = world.get("detective")
    hero.memes["curious"] += 1
    world.say(f'"{mystery.problem}" said the townsfolk.')
    world.say(f"{hero.label} put on {hero.pronoun('possessive')} thinking cap "
              f"and began to look closely.")
    world.say(f"This was a weekly mystery, and {hero.label} loved solving problems.")


def find_evidence(world: World, evidence: Evidence) -> None:
    hero = world.get("detective")
    world.say(f"{hero.label} looked at {evidence.phrase}.")
    world.say(f"{evidence.reveals}")
    world.evidence_found.append(evidence.id)
    hero.memes["curious"] += 1
    propagate(world)


def solve_mystery(world: World, mystery: Mystery) -> None:
    hero = world.get("detective")
    world.say(f"{hero.label} thought hard about the clues.")
    propagate(world)  # triggers solve rule
    if world.solved:
        world.say(f'"I know what happened!" {hero.label} said.')
        world.say(f"{mystery.solution}")
        world.say(f"{mystery.reason_phrase}")
        world.say(f"And just like that, the weekly crooked mystery was solved again.")


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "springtown": Setting(name="springtown", place="Sunnyville square",
                          season="spring", weekly_event="Spring Flower Fair"),
    "summerpark": Setting(name="summerpark", place="Sunnyville park",
                          season="summer", weekly_event="Summer Picnic"),
    "fallmarket": Setting(name="fallmarket", place="Sunnyville market",
                          season="autumn", weekly_event="Fall Harvest Market"),
    "winterfest": Setting(name="winterfest", place="Sunnyville hall",
                          season="winter", weekly_event="Winter Festival"),
}

MYSTERIES = {
    "missing_banner": Mystery(
        id="missing_banner",
        name="the missing welcome banner",
        problem="The big welcome banner for the fair was gone. Who took it?",
        solution="A stray dog named Wally had pulled it down to use as a blanket.",
        clue_phrase="found some paw prints and a torn piece of cloth near the old oak tree",
        reason_phrase="Every week, something goes crooked -- but with curiosity and care, the truth comes out.",
        crookedness="banner theft",
        tags={"dog", "missing"},
    ),
    "crooked_sign": Mystery(
        id="crooked_sign",
        name="the crooked signpost",
        problem="The signpost at the park entrance was pointing the wrong way. All visitors were getting lost!",
        solution="A playful squirrel had been scratching its back on the post and loosened it.",
        clue_phrase="discovered a pile of acorn shells and scratch marks on the post",
        reason_phrase="The squirrel was just having fun with its weekly scratching ritual.",
        crookedness="sign direction",
        tags={"squirrel", "sign"},
    ),
    "upset_pies": Mystery(
        id="upset_pies",
        name="the upset pie stand",
        problem="Someone had mixed up all the pies at the market stand. Blueberry labels on apple pies!",
        solution="The baker's little helper had swapped the labels while playing a matching game.",
        clue_phrase="noticed tiny handprint smudges and a set of colorful label stickers",
        reason_phrase="The helper was just trying to be helpful, but the labels got completely crooked.",
        crookedness="pie mislabeling",
        tags={"pies", "labels"},
    ),
    "silent_bell": Mystery(
        id="silent_bell",
        name="the silent festival bell",
        problem="The big bell at the Winter Festival wouldn't ring. It was completely silent.",
        solution="A thick layer of snow and ice had frozen the clapper inside the bell.",
        clue_phrase="found icicles hanging from the bell and some frost on the rope",
        reason_phrase="The cold winter had made the bell crooked in its own icy way.",
        crookedness="frozen bell",
        tags={"bell", "winter"},
    ),
    "lost_ribbon": Mystery(
        id="lost_ribbon",
        name="the lost prize ribbon",
        problem="The first-prize ribbon for the flower contest had vanished just before the award ceremony.",
        solution="A magpie bird had taken the shiny ribbon to line its nest on the rooftop.",
        clue_phrase="spotted a bit of blue ribbon poking out of a nest on the library roof",
        reason_phrase="The magpie thought it was the perfect decoration for a weekly nest upgrade.",
        crookedness="ribbon theft",
        tags={"ribbon", "bird"},
    ),
}

# Evidence sets for each mystery
EVIDENCE = {
    "missing_banner": [
        Evidence(id="eb1", label="paw prints", phrase="some muddy paw prints near the banner pole",
                 reveals="The prints were small and led toward the old oak tree",
                 location="near pole", tag="paw"),
        Evidence(id="eb2", label="cloth scrap", phrase="a torn piece of cloth caught on a branch",
                 reveals="The cloth matched the missing banner exactly",
                 location="oak tree", tag="cloth"),
        Evidence(id="eb3", label="tracks", phrase="a trail of paw prints heading toward the doghouse",
                 reveals="The tracks belonged to Wally the stray dog, who loves soft things",
                 location="doghouse", tag="track"),
    ],
    "crooked_sign": [
        Evidence(id="es1", label="acorn shells", phrase="a pile of acorn shells at the base of the signpost",
                 reveals="Squirrels had been busy here recently",
                 location="signpost base", tag="acorn"),
        Evidence(id="es2", label="scratch marks", phrase="fresh scratch marks on the wooden post",
                 reveals="Something had been rubbing against the post repeatedly",
                 location="signpost", tag="scratch"),
        Evidence(id="es3", label="squirrel tracks", phrase="tiny squirrel footprints leading away",
                 reveals="A squirrel had been the cause of the weekly crooked sign",
                 location="near fence", tag="track"),
    ],
    "upset_pies": [
        Evidence(id="ep1", label="handprints", phrase="tiny handprint smudges on the pie boxes",
                 reveals="A small child had been handling the boxes",
                 location="pie stand", tag="handprint"),
        Evidence(id="ep2", label="stickers", phrase="a colorful sheet of leftover label stickers",
                 reveals="Someone was playing with labels and got them mixed up",
                 location="under counter", tag="sticker"),
        Evidence(id="ep3", label="helper", phrase="the baker's helper playing with labels behind the stand",
                 reveals="The little helper had swapped the labels as a game",
                 location="behind stand", tag="helper"),
    ],
    "silent_bell": [
        Evidence(id="ebel1", label="icicles", phrase="long icicles hanging from the bell rim",
                 reveals="The bell had been frozen solid by winter weather",
                 location="bell tower", tag="ice"),
        Evidence(id="ebel2", label="frost", phrase="frost covering the bell rope all the way up",
                 reveals="The cold had reached inside the bell mechanism",
                 location="rope", tag="frost"),
        Evidence(id="ebel3", label="snow", phrase="a thick snowdrift piled around the bell tower base",
                 reveals="The extreme cold had made the bell crooked and quiet",
                 location="tower base", tag="snow"),
    ],
    "lost_ribbon": [
        Evidence(id="er1", label="magpie", phrase="a magpie flying toward the library roof with something shiny",
                 reveals="Magpies love collecting shiny objects for their nests",
                 location="market square", tag="bird"),
        Evidence(id="er2", label="nest", phrase="a nest on the library roof with blue fabric poking out",
                 reveals="The ribbon was being used as nest decoration",
                 location="library roof", tag="nest"),
        Evidence(id="er3", label="color", phrase="a scrap of blue ribbon caught on the gutter",
                 reveals="The ribbon had traveled from the contest table all the way to the roof",
                 location="gutter", tag="ribbon"),
    ],
}

DETECTIVE_NAMES = ["Kit", "Riley", "Sam", "Avery", "Jules", "Casey", "Morgan", "Ellis"]
DETECTIVE_TYPES = ["detective"]
HELPER_NAMES = ["Mom", "Dad", "Grandma", "Grandpa"]

EVIDENCE_ORDER = {
    "missing_banner": ["eb1", "eb2", "eb3"],
    "crooked_sign": ["es1", "es2", "es3"],
    "upset_pies": ["ep1", "ep2", "ep3"],
    "silent_bell": ["ebel1", "ebel2", "ebel3"],
    "lost_ribbon": ["er1", "er2", "er3"],
}


# ---------------------------------------------------------------------------
# Storytelling
# ---------------------------------------------------------------------------
def tell(setting: Setting, mystery: Mystery,
         detective_name: str = "Kit",
         helper_type: str = "Mom") -> World:
    world = World(setting)

    # Introduce detective
    introduce_detective(world, detective_name)
    world.para()

    # Setup the weekly event and the crooked problem
    weekly_intro(world, mystery)
    world.para()

    # Hero arrives and investigates
    hero_arrives(world, detective_name, mystery)
    world.para()

    # Gather evidence
    ev_order = EVIDENCE_ORDER[mystery.id]
    ev_set = {e.id: e for e in EVIDENCE[mystery.id]}
    for ev_id in ev_order[:2]:
        find_evidence(world, ev_set[ev_id])
    world.para()

    # Find final evidence and solve
    find_evidence(world, ev_set[ev_order[2]])
    solve_mystery(world, mystery)

    # Record facts
    world.facts["detective"] = world.get("detective")
    world.facts["mystery"] = mystery
    world.facts["setting"] = setting
    world.facts["solved"] = world.solved

    return world


# ---------------------------------------------------------------------------
# Per-world parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    mystery: str
    detective_name: str
    helper: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "detective": [("What does a detective do?",
                   "A detective is someone who looks closely at clues and solves "
                   "mysteries by thinking carefully about what they see.")],
    "clue": [("What is a clue?",
              "A clue is a small piece of information that helps you figure out "
              "what happened, like a footprint or a torn piece of cloth.")],
    "question": [("Why is asking questions important for solving problems?",
                  "Asking questions helps you learn more about the problem so you "
                  "can find the right answer. It is a key part of problem solving.")],
    "mystery": [("What is a mystery?",
                 "A mystery is something that is strange or unknown and needs to "
                 "be figured out. It is like a puzzle waiting to be solved.")],
    "observation": [("What does it mean to observe?",
                     "To observe means to look very carefully at things around you, "
                     "like a detective does. Good observation helps you find clues.")],
    "curiosity": [("Why is curiosity helpful for learning?",
                   "Curiosity makes you want to ask questions and explore, which "
                   "helps you discover new things and solve problems.")],
    "crooked": [("What does 'crooked' mean?",
                 "Crooked means something is bent, twisted, or not straight. "
                 "In a story, something going crooked means it is not as it should be.")],
    "weekly": [("What does 'weekly' mean?",
                "Weekly means happening every week. A weekly event is something "
                "that takes place once each week, like a market or a festival.")],
    "solution": [("What is a solution?",
                  "A solution is an answer to a problem. When you solve a mystery, "
                  "you find the solution and understand what really happened.")],
}
KNOWLEDGE_ORDER = ["detective", "clue", "question", "mystery", "observation",
                   "curiosity", "crooked", "weekly", "solution"]


def generation_prompts(world: World) -> list[str]:
    mystery = world.facts["mystery"]
    det = world.facts["detective"]
    return [
        f"Write a short detective story for a 3-to-5-year-old about a weekly "
        f"mystery in Sunnyville where {mystery.crookedness} happens.",
        f"Tell a gentle problem-solving story where {det.label} the detective "
        f"looks for clues about {mystery.problem}.",
        f"Write a simple story about solving a crooked weekly mystery using "
        f"observation, clues, and careful thinking.",
    ]


def story_qa(world: World) -> list[QAItem]:
    det = world.facts["detective"]
    mystery = world.facts["mystery"]
    setting = world.facts["setting"]
    sub = det.pronoun("subject")
    pos = det.pronoun("possessive")
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who is the young detective in Sunnyville who loves solving "
                f"weekly mysteries?"
            ),
            answer=(
                f"The detective is named {det.label}, a curious and observant "
                f"person who notices everything. Every week, {sub} helps solve "
                f"the crooked little mysteries of Sunnyville."
            ),
        ),
        QAItem(
            question=(
                f"What was the problem during the {setting.weekly_event} in "
                f"{setting.season}?"
            ),
            answer=(
                f"The problem was: {mystery.problem} Something had gone crooked, "
                f"and the townsfolk did not know how to fix it."
            ),
        ),
        QAItem(
            question=(
                f"What did {det.label} find that helped solve the weekly mystery?"
            ),
            answer=(
                f"{det.label} looked carefully and found many clues. By observing "
                f"every detail, {sub} discovered what really happened and "
                f"explained it to everyone."
            ),
        ),
    ]
    if world.solved:
        qa.append(QAItem(
            question=(
                f"How did {det.label} solve the problem of {mystery.crookedness}?"
            ),
            answer=(
                f"{det.label} followed the clues carefully, thought about each "
                f"one, and realized that {mystery.solution} "
                f"{mystery.reason_phrase}"
            ),
        ))
        qa.append(QAItem(
            question=(
                f"What did {det.label} learn from solving this weekly mystery?"
            ),
            answer=(
                f"{det.label} learned that every problem has a solution if you "
                f"look closely and think hard. Even when things go crooked, "
                f"curiosity and care can make things right again."
            ),
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    mystery = world.facts.get("mystery")
    tags = set()
    if mystery:
        tags = mystery.tags.copy()
        tags.add("detective")
        tags.add("clue")
        tags.add("observation")
        tags.add("curiosity")
        tags.add("crooked")
        tags.add("weekly")
        tags.add("solution")
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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


# ---------------------------------------------------------------------------
# CLI / trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    if world.mystery:
        lines.append(f"  mystery: {world.mystery.name}")
        lines.append(f"  solved: {world.solved}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Each mystery has a problem to solve. A detective can solve it if they 
% gather enough clues.
has_clue(D, M) :- detective(D), mystery(M), clue_for(M, C), found(C).
solved(D, M) :- detective(D), mystery(M), has_clue(D, M), clue_count(M, N), 
                count{ C : clue_for(M, C), found(C) } >= N.
valid_story(S, M) :- setting(S), mystery(M), afford(S, M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for mid in MYSTERIES:
            lines.append(asp.fact("afford", sid, mid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("crookedness", mid, m.crookedness))
        evs = EVIDENCE.get(mid, [])
        lines.append(asp.fact("clue_count", mid, len(evs)))
        for ev in evs:
            lines.append(asp.fact("clue_for", mid, ev.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    stories = asp_valid_stories()
    print(f"OK: clingo found {len(stories)} valid (setting, mystery) pairs.")
    return 0


# ---------------------------------------------------------------------------
# Standard storyworld interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Weekly crooked quest: a detective story for problem solving.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(sorted(SETTINGS.keys()))
    mystery = args.mystery or rng.choice(sorted(MYSTERIES.keys()))
    name = args.name or rng.choice(DETECTIVE_NAMES)
    helper = rng.choice(HELPER_NAMES)
    return StoryParams(
        setting=setting,
        mystery=mystery,
        detective_name=name,
        helper=helper,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        MYSTERIES[params.mystery],
        params.detective_name,
        params.helper,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} valid (setting, mystery) pairs:\n")
        for s, m in stories:
            print(f"  {s:12} {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        cur = [StoryParams(setting=s, mystery=m, detective_name=rng.choice(DETECTIVE_NAMES), helper=rng.choice(HELPER_NAMES))
               for s in sorted(SETTINGS)
               for m in sorted(MYSTERIES)
               for rng in [random.Random(base_seed + hash(s + m))]]
        samples = [generate(p) for p in cur]
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
            header = f"### {p.detective_name}: {p.mystery} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
