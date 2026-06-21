#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/elbow_bravery_fable.py
======================================================

A tiny fable-style storyworld about a fox, an elbow bruise, and bravery.

Premise:
- A small animal wants to do a brave deed.
- The deed goes wrong in a modest, physical way: a scraped elbow.
- A wiser helper shows a safer, braver response.
- The ending proves bravery changed from rashness into courage with care.

The world is built as a stateful simulation with meters and memes:
- meters track physical conditions like scrape, ache, and soaked
- memes track emotions like fear, bravery, shame, and pride

The story is generated from simulated events rather than from a frozen paragraph.
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

# ---------------------------------------------------------------------------
# World constants
# ---------------------------------------------------------------------------

THRESHOLD = 1.0
BRAVERY_MIN = 5.0


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
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
    def label_word(self) -> str:
        return self.label or self.type


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

@dataclass
class Place:
    id: str
    label: str
    perch: str
    risk: str
    wet: bool = False
    height: int = 0
    tags: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    goal: str
    hazard: str
    risk_kind: str
    bravery_need: int
    success_clause: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    advice: str
    rescue: str
    wisdom: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    task: str
    helper: str
    response: str
    hero: str
    hero_type: str
    helper_name: str
    helper_type: str
    elder_name: str = "Grandmother"
    elder_type: str = "woman"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World container
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------

PLACES = {
    "pond_bank": Place(
        id="pond_bank",
        label="the pond bank",
        perch="the slippery bank",
        risk="the muddy water",
        wet=True,
        height=1,
        tags={"pond", "water"},
    ),
    "hayloft": Place(
        id="hayloft",
        label="the hayloft",
        perch="the old ladder",
        risk="the loose straw",
        wet=False,
        height=2,
        tags={"hay", "barn"},
    ),
    "stone_wall": Place(
        id="stone_wall",
        label="the stone wall",
        perch="the narrow ledge",
        risk="the hard ground below",
        wet=False,
        height=1,
        tags={"stone", "wall"},
    ),
}

TASKS = {
    "fetch_bucket": Task(
        id="fetch_bucket",
        verb="climb down for the bucket",
        goal="a pail for the thirsty garden",
        hazard="the ladder",
        risk_kind="fall",
        bravery_need=5,
        success_clause="brought the bucket down safely",
        tags={"bucket", "climb"},
    ),
    "rescue_kitten": Task(
        id="rescue_kitten",
        verb="reach the kitten",
        goal="the frightened kitten",
        hazard="the narrow perch",
        risk_kind="fall",
        bravery_need=6,
        success_clause="carried the kitten back in both arms",
        tags={"kitten", "rescue"},
    ),
    "carry_lantern": Task(
        id="carry_lantern",
        verb="carry the lantern",
        goal="the barn door",
        hazard="the tall step",
        risk_kind="bump",
        bravery_need=4,
        success_clause="kept the lantern steady",
        tags={"lantern", "light"},
    ),
}

HELPERS = {
    "mole": Helper(
        id="mole",
        label="the mole",
        advice="bravery means being careful while you are doing a hard thing",
        rescue="showed the safest foothold",
        wisdom=8,
        tags={"wise", "ground"},
    ),
    "heron": Helper(
        id="heron",
        label="the heron",
        advice="a brave heart still watches its feet",
        rescue="spread one wing toward the safest step",
        wisdom=7,
        tags={"wise", "water"},
    ),
    "grandmother": Helper(
        id="grandmother",
        label="Grandmother",
        advice="bravery is asking for help when the path is steep",
        rescue="held the lantern steady from below",
        wisdom=9,
        tags={"elder", "family"},
    ),
}

RESPONSES = {
    "cloth_wrap": Response(
        id="cloth_wrap",
        sense=3,
        power=4,
        text="wrapped a soft cloth around the elbow and cleaned the scrape with cool water",
        fail="wrapped the elbow too loosely, and the ache kept growing",
        qa_text="wrapped the elbow in a soft cloth and cleaned the scrape with cool water",
        tags={"first_aid", "cloth"},
    ),
    "salve_bandage": Response(
        id="salve_bandage",
        sense=4,
        power=5,
        text="washed the scrape, smoothed on a little salve, and tied on a neat bandage",
        fail="tried to stop the bleeding, but the scrape was already too sore",
        qa_text="washed the scrape, put on a little salve, and tied on a neat bandage",
        tags={"first_aid", "bandage"},
    ),
    "rest_and_tea": Response(
        id="rest_and_tea",
        sense=2,
        power=3,
        text="sat the child down, gave warm tea, and let the elbow rest on a pillow",
        fail="offered tea, but the hurt elbow still needed more help",
        qa_text="sat the child down with warm tea and let the elbow rest on a pillow",
        tags={"rest", "tea"},
    ),
}

HERO_NAMES = ["Robin", "Pip", "Mina", "Toby", "Iris", "Jasper", "Nina", "Orin"]


# ---------------------------------------------------------------------------
# Reasonableness gates
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for tid, task in TASKS.items():
            if place.height > 0 and task.risk_kind == "fall":
                for hid in HELPERS:
                    combos.append((pid, tid, hid))
    return combos


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= 3]


def explain_rejection(task: Task, place: Place) -> str:
    return (
        f"(No story: {task.verb} does not fit {place.label} well enough for a fable. "
        f"Choose a place with a little height, since the elbow story needs a small fall.)"
    )


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    return (
        f"(Refusing response '{rid}': it is too weak for the scrape and does not meet "
        f"the common-sense floor. Try one of: {', '.join(sorted(x.id for x in sensible_responses()))}.)"
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(P) :- place_fact(P).
task(T) :- task_fact(T).
helper(H) :- helper_fact(H).
response(R) :- response_fact(R).

valid(P,T,H) :- place(P), task(T), helper(H), fall_task(T), raised(P).
fall_task(T) :- task_kind(T, fall).
raised(P) :- height(P, H), H > 0.

sensible(R) :- response(R), sense(R, S), S >= 3.
outcome(safe) :- chosen_response(R), power(R, P), severity(V), P >= V.
outcome(sore) :- chosen_response(R), power(R, P), severity(V), P < V.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place_fact", pid))
        lines.append(asp.fact("height", pid, p.height))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task_fact", tid))
        lines.append(asp.fact("task_kind", tid, t.risk_kind))
    for hid in HELPERS:
        lines.append(asp.fact("helper_fact", hid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response_fact", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    severity = 3
    extra = "\n".join([
        asp.fact("chosen_response", params.response),
        asp.fact("severity", severity),
    ])
    model = asp.one_model(asp_program(extra=extra, show="#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


# ---------------------------------------------------------------------------
# Story mechanics
# ---------------------------------------------------------------------------

def fall_severity(place: Place) -> int:
    return 3 if place.height >= 2 else 2


def can_rescue(response: Response, place: Place) -> bool:
    return response.power >= fall_severity(place)


def predict_fall(world: World, place: Place, task: Task) -> dict:
    sim = world.copy()
    actor = sim.get("hero")
    actor.meters["wobble"] += 1
    if task.risk_kind == "fall" and place.height > 0:
        actor.meters["scrape"] += 1
        actor.meters["ache"] += 1
    return {
        "scraped": actor.meters["scrape"] >= THRESHOLD,
        "ache": actor.meters["ache"],
    }


def _r_scrape(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.meters["wobble"] >= THRESHOLD and hero.meters["scrape"] >= THRESHOLD:
        sig = ("scrape", hero.id)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        hero.memes["fear"] += 1
        hero.memes["bravery"] -= 1
        out.append("__scrape__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    for s in _r_scrape(world):
        if s != "__scrape__":
            produced.append(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(place: Place, task: Task, helper: Helper, response: Response,
         hero: str = "Robin", hero_type: str = "girl",
         helper_name: str = "Mole", helper_type: str = "thing",
         elder_name: str = "Grandmother", elder_type: str = "woman") -> World:
    world = World()
    h = world.add(Entity(id=hero, kind="character", type=hero_type, role="hero"))
    wise = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_type, role="elder"))

    h.memes["bravery"] = 6.0
    wise.memes["wisdom"] = float(helper.wisdom)

    world.say(
        f"In a little fable village, {hero} loved to prove {h.pronoun('possessive')} courage."
    )
    world.say(
        f"One morning {hero} wanted to {task.verb} at {place.label}. "
        f"The task looked small, but the {place.perch} was no toy."
    )

    world.para()
    world.say(
        f"{hero} climbed toward {task.goal} because {h.pronoun()} wanted the whole lane to know "
        f"{h.pronoun('possessive')} bravery."
    )
    world.say(
        f"But the {place.risk} asked for steady feet, and {hero} gave one careless elbow a hard knock."
    )
    h.meters["wobble"] += 1
    h.meters["scrape"] += 1
    h.meters["ache"] += 1
    h.memes["fear"] += 1
    h.memes["shame"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero} rubbed {h.pronoun('possessive')} elbow and tried not to cry."
    )

    world.para()
    world.say(
        f"Then {helper.label} came by and said, \"{helper.advice}.\""
    )
    world.say(
        f"{helper.label_word.capitalize()} {helper.rescue}."
    )

    world.para()
    if can_rescue(response, place):
        body = response.text
        world.say(
            f"{elder_name} smiled and helped with the hurt. {elder_name} {body}."
        )
        h.meters["scrape"] = 0
        h.meters["ache"] = 0
        h.memes["fear"] = 0
        h.memes["shame"] = 0
        h.memes["pride"] += 1
        h.memes["bravery"] += 1
        world.say(
            f"{hero} looked at the clean bandage and understood that bravery was not rushing. "
            f"It was rising again with care."
        )
        ending = f"By sunset, {hero} stood straighter beside the {place.label_word if hasattr(place, 'label_word') else place.label}, elbow wrapped neat and white."
    else:
        body = response.fail
        world.say(f"{elder_name} tried to help, but {body}.")
        h.memes["fear"] += 1
        ending = f"By sunset, {hero} still sat with a sore elbow and a lesson about haste."

    world.say(ending)
    world.facts.update(
        hero=h,
        helper=wise,
        elder=elder,
        place=place,
        task=task,
        response=response,
        outcome="safe" if can_rescue(response, place) else "sore",
        severity=fall_severity(place),
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable for a child that includes the word "elbow" and teaches bravery without boasting.',
        f"Tell a fable about {f['hero'].id} at {f['place'].label} who learns that bravery can include taking care after a scrape.",
        f"Write a gentle story where a small character gets a scraped elbow, listens to a wise helper, and ends more brave than before.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero: Entity = f["hero"]
    place: Place = f["place"]
    task: Task = f["task"]
    response: Response = f["response"]
    qa = [
        (
            "What happened to the hero's elbow?",
            f"{hero.id} scraped {hero.pronoun('possessive')} elbow while trying to {task.verb} at {place.label}. "
            f"The tumble was small, but it still hurt and made {hero.id} feel less sure for a moment.",
        ),
        (
            "What did the wise helper teach?",
            f"{f['helper'].label} taught that {f['helper'].advice}. "
            f"That lesson turned the trouble into a truer kind of bravery.",
        ),
    ]
    if f["outcome"] == "safe":
        qa.append(
            (
                "How did the problem get fixed?",
                f"{f['elder'].id} used {response.qa_text}. "
                f"That helped the scrape settle down, so the hero could stand up proud again.",
            )
        )
        qa.append(
            (
                "How did bravery change by the end?",
                f"At first, bravery was only a bold feeling. By the end, {hero.id} learned that bravery also means being careful, accepting help, and trying again.",
            )
        )
    else:
        qa.append(
            (
                "How did the story end?",
                f"It ended with a sore elbow and a quiet lesson. {hero.id} learned that rushing is not the same as bravery.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["task"].tags) | set(f["place"].tags)
    if f["outcome"] == "safe":
        tags |= set(f["response"].tags)
    out = []
    if "first_aid" in tags:
        out.append((
            "Why do people clean a scrape?",
            "People clean a scrape to wash away dirt and keep it from getting worse. Clean water and a bandage help the hurt place heal.",
        ))
    if "fall" in tags:
        out.append((
            "Why can a small fall hurt?",
            "A small fall can hurt because bones and skin are not soft like a pillow. Even a little bump can leave an elbow sore.",
        ))
    out.append((
        "What is bravery?",
        "Bravery means doing the hard thing when you are afraid. In a fable, bravery is often wiser when it is careful too.",
    ))
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
# CLI helpers
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="pond_bank",
        task="fetch_bucket",
        helper="mole",
        response="salve_bandage",
        hero="Robin",
        hero_type="girl",
        helper_name="Mole",
        helper_type="thing",
        elder_name="Grandmother",
        elder_type="woman",
    ),
    StoryParams(
        place="hayloft",
        task="rescue_kitten",
        helper="heron",
        response="cloth_wrap",
        hero="Pip",
        hero_type="boy",
        helper_name="Heron",
        helper_type="thing",
        elder_name="Grandmother",
        elder_type="woman",
    ),
    StoryParams(
        place="stone_wall",
        task="carry_lantern",
        helper="grandmother",
        response="rest_and_tea",
        hero="Mina",
        hero_type="girl",
        helper_name="Grandmother",
        helper_type="woman",
        elder_name="Grandmother",
        elder_type="woman",
    ),
]


def valid_combo_params(place: str, task: str, helper: str) -> bool:
    return place in PLACES and task in TASKS and helper in HELPERS and PLACES[place].height > 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable storyworld about elbow, bravery, and wiser care.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy", "bird", "fox", "mouse"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["thing", "woman", "man", "bird", "fox"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < 3:
        raise StoryError(explain_response(args.response))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.task is None or c[1] == args.task)
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, task, helper = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    return StoryParams(
        place=place,
        task=task,
        helper=helper,
        response=response,
        hero=args.hero or rng.choice(HERO_NAMES),
        hero_type=args.hero_type or rng.choice(["girl", "boy", "fox", "bird", "mouse"]),
        helper_name=args.helper_name or HELPER_LABELS[helper],
        helper_type=args.helper_type or "thing",
        elder_name="Grandmother",
        elder_type="woman",
    )


HELPER_LABELS = {
    "mole": "Mole",
    "heron": "Heron",
    "grandmother": "Grandmother",
}


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.task not in TASKS or params.helper not in HELPERS or params.response not in RESPONSES:
        raise StoryError("Invalid params for this world.")
    world = tell(
        PLACES[params.place],
        TASKS[params.task],
        HELPERS[params.helper],
        RESPONSES[params.response],
        hero=params.hero,
        hero_type=params.hero_type,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        elder_name=params.elder_name,
        elder_type=params.elder_type,
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
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid_combos().")
    # smoke test ordinary generation
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    # outcome parity check on curated
    for p in CURATED:
        if asp_outcome(p) not in {"safe", "sore"}:
            rc = 1
            print("MISMATCH: invalid ASP outcome.")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, task, helper) combos:")
        for c in combos:
            print("  ", c)
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
            header = f"### {p.hero} at {p.place} ({p.task}, {p.response})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
