#!/usr/bin/env python3
"""A tiny team learns that some jobs need everyone's hands.

Build the physics first: a buried object needs digging, but digging leaves
tiredness. Predict on a copy before choosing a strategy; execute on the real
world afterward. Different problems permit different actions: try alone, ask
for help, share the work, or rest and plan. Record each turn after changing
state, then derive QA from those events. Names and wording are not the source
of plot variation.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclassss import dataclass, field, replace
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
DIG_KINDS = {"tired", "dirty"}
REGIONS = {"hands", "arms"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "creature"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    working: bool = False
    helpful: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"mouse", "mouse_girl"}
        male = {"mouse", "mouse_boy", "rabbit"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.type.replace("_", " ")


@dataclass
class Setting:
    place: str = "the meadow"
    affords: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    depth: int
    effort: float
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class ObjectToDig:
    id: str
    label: str
    phrase: str
    value: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Teammate:
    id: str
    label: str
    phrase: str
    type: str
    tool: str
    strengths: set[str] = field(default_factory=set)


@dataclass
class Strategy:
    id: str
    label: str
    description: str
    helps: bool = False


@dataclass
class Event:
    kind: str
    actor: str
    target: str
    text: str
    cause: str = ""
    result: str = ""


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.history: list[Event] = []
        self.facts: dict = {}
        self.turn = 0

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def helpers(self) -> list[Entity]:
        return [e for e in self.characters() if e.helpful and e.id != self.facts["hero"].id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def record(self, kind: str, text: str, *, cause: str = "", result: str = "",
               actor: str = "", target: str = "object") -> None:
        self.history.append(Event(
            kind=kind, actor=actor or self.facts["hero"].id, target=target, text=text,
            cause=cause, result=result,
        ))
        self.say(text)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.turn = self.turn
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_exhaustion(world: World) -> list[str]:
    out = []
    for char in world.characters():
        if not char.working:
            continue
        effort = world.facts["task"].effort
        chars_working = sum(1 for c in world.characters() if c.working)
        share = effort / max(chars_working, 1)
        char.meters["tired"] += share
        if char.meters["tired"] >= THRESHOLD and ("tired", char.id) not in world.fired:
            world.fired.add(("tired", char.id))
            char.memes["grumpiness"] += 1
            out.append(f"{char.id}'s paws felt heavy after all that digging.")
    return out


def _r_progress(world: World) -> list[str]:
    out = []
    task = world.facts["task"]
    obj = world.facts["object"]
    if obj.meters["exposed"] >= task.depth:
        if ("unburied", obj.id) not in world.fired:
            world.fired.add(("unburied", obj.id))
            obj.meters["exposed"] = 0
            obj.meters["found"] = 1
            out.append(f"The dirt fell away, and the {obj.label} sat free and bright in the soil.")
        return out
    workers = [c for c in world.characters() if c.working]
    if not workers:
        return out
    obj.meters["exposed"] += 1
    verb = "shifted" if len(workers) == 1 else "shifted together"
    who = " ".join(w.id for w in workers)
    out.append(f"The {obj.label} {verb} as {who} dug deeper.")
    return out


CAUSAL_RULES = [
    Rule(name="exhaustion", tag="physical", apply=_r_exhaustion),
    Rule(name="progress", tag="physical", apply=_r_progress),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_outcome(world: World, strategy: Strategy) -> dict:
    sim = world.copy()
    f = sim.facts
    hero = f["hero"]
    task = f["task"]
    obj = f["object"]
    
    sim.paragraphs = [[]]
    if strategy.helps:
        for mate in world.entities.values():
            if isinstance(mate, Teammate) or (mate.kind == "character" and mate.id != hero.id):
                if mate.id in world.entities:
                    sim_ent = sim.get(mate.id)
                    sim_ent.working = True
    else:
        hero.working = True
    
    max_steps = task.depth + 5
    for _ in range(max_steps):
        propagate(sim, narrate=False)
        if obj.meters["found"] >= 1:
            break
        if any(c.meters["tired"] >= THRESHOLD * 2 for c in sim.characters()):
            break
    
    total_tired = sum(c.meters["tired"] for c in sim.characters())
    return {
        "found": obj.meters["found"] >= 1,
        "total_tired": total_tired,
        "steps": sim.turn
    }


def dig_setup(world: World) -> None:
    f = world.facts
    hero = f["hero"]
    task = f["task"]
    obj = f["object"]
    
    name = hero.id
    opening = {
        "stubborn": f"{name} had already made up {hero.pronoun('possessive')} mind. No help needed.",
        "shy": f"{name} stood at the edge of the hole, paws trembling slightly.",
        "busy": f"{name} looked around, hoping someone else would start first.",
    }.get(f["trait"], f"{name} looked at the mound of dirt with a small frown.")
    
    detail = f"The {f['setting'].place} was quiet, and the sun warmed the small patch of earth."
    world.record("arrive", f'{opening} {detail} {name} needed to unbury {obj.phrase}, a valuable {obj.label}. '
                 f'{task.verb} looked like a big job for one small {hero.label_word}.')


def choose_action(world: World) -> None:
    f = world.facts
    hero = f["hero"]
    strategy = f["strategy"]
    task = f["task"]
    obj = f["object"]
    
    name = hero.id
    world.para()
    
    if strategy.id == "alone":
        hero.working = True
        cause = f"{name} thought {hero.pronoun('possessive')} paws were strong enough."
        result = f"{name} began to dig by {hero.pronoun('self')}."
        text = f'{cause} {result} The first few scoops felt easy, but the dirt seemed endless.'
        world.record("start_alone", text, cause=cause, result=result)
        
    elif strategy.id == "ask_help":
        mate_id = next((m.id for m in world.entities.values() if m.kind == "character" and m.id != hero.id), None)
        if not mate_id:
            raise StoryError("Need a potential helper to ask for help.")
        mate = world.get(mate_id)
        hero.memes["hope"] += 1
        cause = f"{name} realized the hole was too deep for one pair of paws."
        result = f'{name} asked {mate.id} to dig with {hero.pronoun("object")}. {mate.id} agreed with a cheerful nod.'
        text = f'{cause} {result}'
        world.record("ask_help", text, cause=cause, result=result)
        hero.working = True
        mate.working = True
        mate.helpful = True
        
    elif strategy.id == "share_work":
        mates = [m for m in world.entities.values() if m.kind == "character" and m.id != hero.id]
        if not mates:
            raise StoryError("Need helpers to share work.")
        first_mate = mates[0]
        hero.memes["care"] += 1
        cause = f"{name} noticed everyone was getting tired and wanted to make the work fair."
        result = f'{name} suggested taking turns digging, so {first_mate.id} and {name} could rest while others worked.'
        text = f'{cause} {result} They arranged a little system: one digs, one rests, then they swap.'
        world.record("share_work", text, cause=cause, result=result)
        hero.working = True
        for m in mates:
            m.working = True
            m.helpful = True
            
    else:  # rest
        hero.memes["patience"] += 1
        cause = f"{name} felt too tired to keep digging right away."
        result = f'{name} sat down for a minute to catch {hero.pronoun("possessive")} breath and think.'
        text = f'{cause} {result} The cool air felt nice on {hero.pronoun("possessive")} face.'
        world.record("rest", text, cause=cause, result=result)
        hero.working = False
        return

    # Propagate the digging until finished or stuck
    propagate(world, narrate=True)


def finish(world: World) -> None:
    f = world.facts
    hero = f["hero"]
    obj = f["object"]
    task = f["task"]
    strategy = f["strategy"]
    
    world.para()
    name = hero.id
    
    if f.get("resolved"):
        cause = f"The teamwork made the heavy job feel lighter." if strategy.helps else f"The effort was hard, but {name} did not give up."
        result = f"The {obj.label} was finally out of the ground, clean and safe."
        image = f"{name} held the {obj.label} up, and a bright smile spread across {hero.pronoun('possessive')} face. The meadow felt happy again."
        world.record("success", f'{cause} {result} {image}', cause=cause, result=result)
        hero.memes["joy"] += 1
        hero.memes["conflict"] = 0
        hero.memes["grumpiness"] = 0
    else:
        cause = f"The dirt was too deep and {name} was too tired to continue alone."
        result = f'{name} decided the {obj.label} could wait until morning when {hero.pronoun("possessive")} paws were fresh.'
        image = f"{name} covered the hole with a leaf and promised to try again later with a plan."
        world.record("pause", f'{cause} {result} {image}', cause=cause, result=result)
        hero.memes["hope"] += 1
        hero.memes["conflict"] = 0
        hero.memes["grumpiness"] = 0
    
    f["resolved"] = True


def tell(setting: Setting, task: Task, obj_cfg: ObjectToDig, hero_name: str, hero_type: str, hero_traits: list[str], *, problem: str, strategy: str) -> World:
    if strategy not in STRATEGIES:
        raise StoryError(f"Unknown strategy: {strategy}")
    
    world = World(setting)
    
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=hero_traits, label=hero_type.replace("_", " ")))
    
    # Add a potential helper (always a rabbit in this domain for simplicity)
    helper = world.add(Entity(id="Rex", kind="character", type="rabbit", traits=["strong", "kind"], label="rabbit"))
    
    obj = world.add(Entity(id="object", type="object", label=obj_cfg.label, phrase=obj_cfg.phrase, owner=hero.id))
    
    world.facts.update(
        hero=hero,
        object=obj,
        task=task,
        setting=setting,
        trait=hero_traits[0] if hero_traits else "busy",
        problem=problem,
        strategy=STRATEGIES[strategy],
        resolved=False,
    )
    
    hero.memes["desire"] = 1
    hero.memes["curiosity"] = float("curious" in hero_traits)
    hero.memes["impatience"] = float("stubborn" in hero_traits)
    
    dig_setup(world)
    choose_action(world)
    
    # Check if resolved
    if obj.meters["found"] >= 1:
        finish(world)
    else:
        # If not found, check if it was a rest/pause strategy or exhaustion
        if strategy == "rest":
            finish(world)
        else:
            # If they exhausted themselves, they pause
            if any(c.meters["tired"] >= THRESHOLD * 2 for c in world.characters()):
                finish(world)
            else:
                # Should have found it if working and not exhausted
                finish(world)
                
    return world


SETTINGS = {
    "meadow": Setting(place="the meadow", affords={"dig"}),
    "garden": Setting(place="the vegetable garden", affords={"dig"}),
}

TASKS = {
    "dig_shovel": Task(
        id="dig_shovel",
        verb="dig with a small shovel",
        gerund="digging with a small shovel",
        depth=3,
        effort=2.5,
        keyword="digging",
        tags={"dirt", "shovel"},
    ),
    "dig_paws": Task(
        id="dig_paws",
        verb="dig with tiny paws",
        gerund="digging with tiny paws",
        depth=4,
        effort=3.0,
        keyword="digging",
        tags={"dirt", "paws"},
    ),
}

OBJECTS = {
    "key": ObjectToDig(
        id="key",
        label="golden key",
        phrase="a shiny golden key",
        value="access",
        tags={"key", "treasure"},
    ),
    "ball": ObjectToDig(
        id="ball",
        label="red ball",
        phrase="a bright red ball",
        value="play",
        tags={"ball", "play"},
    ),
}

STRATEGIES = {
    "alone": Strategy(id="alone", label="alone", description="try to do it by oneself", helps=False),
    "ask_help": Strategy(id="ask_help", label="ask_help", description="ask a friend for help", helps=True),
    "share_work": Strategy(id="share_work", label="share_work", description="share the work fairly", helps=True),
    "rest": Strategy(id="rest", label="rest", description="rest and plan", helps=False),
}

NAME_LISTS = {
    "mouse_boy": ["Benny", "Max", "Leo", "Sam"],
    "mouse_girl": ["Mia", "Lily", "Zoe", "Anna"],
    "rabbit": ["Rex", "Bunny", "Hopper"],
}

TRAITS = ["stubborn", "shy", "busy", "curious"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for task_id, task in TASKS.items():
            if task_id not in setting.affords:
                continue
            for obj_id, obj in OBJECTS.items():
                for strategy_id in STRATEGIES:
                    combos.append((place, task_id, obj_id, strategy_id))
    return combos


@dataclass
class StoryParams:
    place: str
    task: str
    object: str
    name: str
    gender: str
    trait: str
    strategy: str
    seed: Optional[int] = None
    problem: str = "buried"


KNOWLEDGE = {
    "dirt": [("What is dirt?", "Dirt is soft earth. It can hide things under it.")],
    "shovel": [("What is a shovel for?", "A shovel helps you move heavy dirt.")],
    "paws": [("Why do paws get tired?", "Paws get tired when they work too hard without rest.")],
    "key": [("What is a key for?", "A key opens locks and helps you find things.")],
    "ball": [("What is a ball for?", "A ball is fun to play with and throw.")],
    "teamwork": [("What is teamwork?", "Teamwork is when friends work together to make a job easier.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, task, obj = f["hero"], f["task"], f["object"]
    strat = f["strategy"].label
    return [
        f"Write a fable about {hero.id} who needs to {task.verb}. {hero.id} decides to {strat}.",
        f"Tell a story where a small {hero.label_word} unburies {obj.phrase} by learning the value of {strat.replace('_', ' ')}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    questions = {
        "arrive": "Why did the character need to dig?",
        "start_alone": "How did the character start the job?",
        "ask_help": "Who helped the character?",
        "share_work": "How did they share the work?",
        "rest": "What did the character do instead of digging?",
        "success": "How did they finish the job?",
        "pause": "Why did they stop digging?",
    }
    return [QAItem(question=questions[e.kind], answer=f"{e.cause} {e.result}")
            for e in world.history if e.kind in questions]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["task"].tags)
    tags.update(f["object"].tags)
    if f["strategy"].helps:
        tags.add("teamwork")
    out = []
    for tag in ["dirt", "shovel", "paws", "key", "ball", "teamwork"]:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.working:
            bits.append(f"working=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append("--- events ---")
    for event in world.history:
        lines.append(f"  {event.kind}: {event.actor} -> {event.target}: {event.text}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="meadow",
        task="dig_shovel",
        object="key",
        name="Benny",
        gender="boy",
        trait="stubborn",
        strategy="alone",
    ),
    StoryParams(
        place="garden",
        task="dig_paws",
        object="ball",
        name="Mia",
        gender="girl",
        trait="shy",
        strategy="ask_help",
    ),
    StoryParams(
        place="meadow",
        task="dig_shovel",
        object="key",
        name="Lily",
        gender="girl",
        trait="busy",
        strategy="share_work",
    ),
    StoryParams(
        place="garden",
        task="dig_paws",
        object="ball",
        name="Max",
        gender="boy",
        trait="curious",
        strategy="rest",
    ),
]


ASP_RULES = r"""
valid(Place, Task, Object, Strategy) :- setting(Place), task(Task), object(Object), strategy(Strategy).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
    for sid in STRATEGIES:
        lines.append(asp.fact("strategy", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def check_sample(sample: StorySample) -> None:
    world = sample.world
    f = world.facts
    hero, obj = f["hero"], f["object"]
    resolved = f["resolved"]
    assert resolved
    assert len(world.paragraphs) >= 3
    assert 2 <= len(sample.story_qa) <= 4
    for event in world.history:
        assert event.text in sample.story
    assert not any(marker in sample.story for marker in ("{", "}", "__", "meters=", "memes="))


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    asp_set = set(asp.atoms(model, "valid"))
    py_set = set(valid_combos())
    if asp_set != py_set:
        print("MISMATCH: ASP and Python choices differ.")
        return 1
    checked = 0
    for place, task, obj, strat in sorted(py_set):
        params = StoryParams(place=place, task=task, object=obj,
                             name="Robin", gender="boy", trait="curious",
                             strategy=strat, problem="buried")
        sample = generate(params)
        check_sample(sample)
        checked += 1
    print(f"OK: {len(py_set)} ASP/Python combinations; {checked} story/state/QA checks.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: bury teamwork fable.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--gender", choices=["boy", "girl"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--strategy", choices=STRATEGIES)
    ap.add_argument("-n", type=int, default=1)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.task is None or c[1] == args.task)
              and (args.object is None or c[2] == args.object)
              and (args.strategy is None or c[3] == args.strategy)]
    if not combos:
        raise StoryError("No valid combination matches the options.")
    
    place, task, obj, strat = rng.choice(combos)
    
    if args.gender:
        gender = args.gender
    else:
        gender = rng.choice(["boy", "girl"])
        
    name_pool = NAME_LISTS.get(f"mouse_{gender}", ["Robin"])
    name = args.name or rng.choice(name_pool)
    trait = args.trait or rng.choice(TRAITS)
    
    return StoryParams(
        place=place,
        task=task,
        object=obj,
        name=name,
        gender=gender,
        trait=trait,
        strategy=strat,
    )


def generate(params: StoryParams) -> StorySample:
    if (params.place, params.task, params.object, params.strategy) not in valid_combos():
        raise StoryError("Invalid combination.")
    
    world = tell(
        SETTINGS[params.place],
        TASKS[params.task],
        OBJECTS[params.object],
        params.name,
        f"mouse_{params.gender}",
        [params.trait],
        problem=params.problem,
        strategy=params.strategy,
    )
    
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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
    if args.n < 1:
        raise SystemExit("-n must be at least 1")

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode not fully implemented for listing, use --verify.")
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
                params.seed = seed
                sample = generate(params)
            except StoryError as err:
                raise SystemExit(str(err)) from err
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
            header = f"### {p.name}: {p.task} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
