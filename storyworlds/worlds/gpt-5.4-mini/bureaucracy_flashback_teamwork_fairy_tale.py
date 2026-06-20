#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/bureaucracy_flashback_teamwork_fairy_tale.py
=============================================================================

A tiny fairy-tale story world about a child, a royal permit, a patient clerk,
a flashback to how the rule began, and teamwork that turns a tangled paper maze
into a happy ending.

The story domain is intentionally small:
- a castle office runs on stamps, forms, and polite rules
- a hero needs a permit to do something kind or useful
- a helpful partner remembers an old lesson in a flashback
- together they solve the paperwork instead of breaking the rule

This file is standalone and uses only the stdlib plus storyworlds/results.py.
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
SENSE_MIN = 2


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

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "queen", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "king", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "queen": "queen", "king": "king"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Place:
    id: str
    label: str
    office: str
    wall: str
    mood: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Task:
    id: str
    label: str
    need: str
    hope: str
    flashback: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Paper:
    id: str
    label: str
    phrase: str
    stampable: bool
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class HelpAction:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


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

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_frustration(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["stuck"] < THRESHOLD:
            continue
        sig = ("frustration", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["worry"] += 1
        out.append(f"{e.id} felt the old worry return.")
    return out


CAUSAL_RULES = [Rule("frustration", "social", _r_frustration)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
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


def paperwork_risk(task: Task, paper: Paper) -> bool:
    return paper.stampable and task.need == paper.label


def sensible_actions() -> list[HelpAction]:
    return [a for a in ACTIONS.values() if a.sense >= SENSE_MIN]


def outcome_of(params: "StoryParams") -> str:
    if params.teamwork and params.flashback:
        return "solved"
    return "stuck"


def explain_rejection(task: Task, paper: Paper) -> str:
    if not paperwork_risk(task, paper):
        return f"(No story: {paper.label} does not match the permit needed for {task.label}.)"
    return "(No story: this combination has no real paperwork problem.)"


def explain_action(aid: str) -> str:
    a = ACTIONS[aid]
    better = " / ".join(sorted(x.id for x in sensible_actions()))
    return f"(Refusing action '{aid}': it is too weak in common sense (sense={a.sense} < {SENSE_MIN}). Try: {better}.)"


def predict(world: World, task: Task, paper_id: str) -> dict:
    sim = world.copy()
    _do_task(sim, sim.get("hero"), task, narrate=False)
    return {"stuck": sim.get("hero").meters["stuck"] >= THRESHOLD, "confused": sim.get("hero").memes["worry"] >= THRESHOLD}


def _do_task(world: World, hero: Entity, task: Task, narrate: bool = True) -> None:
    hero.meters["stuck"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, hero: Entity, helper: Entity, task: Task, paper: Paper) -> None:
    world.say(f"Long ago in a castle with {world.place.mood}, {hero.id} and {helper.id} came to {world.place.office}.")
    world.say(f"{hero.id} needed {paper.phrase} for {task.label}, but the office wall was lined with little drawers and stamps.")
    hero.memes["hope"] += 1
    helper.memes["patience"] += 1


def wants(world: World, hero: Entity, task: Task) -> None:
    world.say(f'{hero.id} bowed and said, "I need to {task.hope}."')


def refuses(world: World, clerk: Entity, hero: Entity, task: Task, paper: Paper) -> None:
    world.say(f'{clerk.id} shook {clerk.pronoun("possessive")} head. "Not without {paper.label}," {clerk.pronoun()} said.')
    world.say(f"The rule was plain, but it made {hero.id} feel stuck.")


def flashback(world: World, helper: Entity, task: Task) -> None:
    world.say(f"Then {helper.id} remembered a flashback from an earlier winter: a lost shepherd had once hurried a crowd without counting them, and the village had learned a careful lesson.")
    world.say(f'"That is why the town keeps {task.flashback}," {helper.id} whispered. "The rule protects everyone."')
    helper.memes["memory"] += 1


def teamwork(world: World, hero: Entity, helper: Entity, clerk: Entity, task: Task, paper: Paper) -> None:
    hero.memes["trust"] += 1
    helper.memes["courage"] += 1
    world.say(f"So {hero.id}, {helper.id}, and {clerk.id} worked together like a little fairy-tale team.")
    world.say(f"{helper.id} found the missing line, {hero.id} carried the ink, and {clerk.id} stamped the page.")
    world.say(f"At last, {paper.phrase} was ready, and the gate could open for {task.label}.")


def resolve(world: World, hero: Entity, helper: Entity, task: Task) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(f"{hero.id} smiled as the castle doors opened. {task.label.capitalize()} could finally begin, and the paperwork had turned into a victory.")

def stuck_ending(world: World, hero: Entity, helper: Entity, task: Task) -> None:
    world.say(f"The papers stayed unfinished, and the day remained paused at the desk. Still, {hero.id} and {helper.id} promised to return with the right form.")


def tell(place: Place, task: Task, paper: Paper, action: HelpAction,
         hero_name: str = "Mina", helper_name: str = "Pip", clerk_name: str = "Clara",
         seed_hint: int = 0, teamwork: bool = True, flashback: bool = True) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type="girl", role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type="boy", role="helper"))
    clerk = world.add(Entity(id=clerk_name, kind="character", type="woman", role="clerk", label="the clerk"))
    world.facts["teamwork"] = teamwork
    world.facts["flashback"] = flashback

    setup(world, hero, helper, task, paper)
    world.para()
    wants(world, hero, task)
    refuses(world, clerk, hero, task, paper)
    if flashback:
        flashback(world, helper, task)
    if teamwork:
        teamwork(world, hero, helper, clerk, task, paper)
        world.para()
        world.say(action.text.replace("{paper}", paper.label))
        resolve(world, hero, helper, task)
        outcome = "solved"
    else:
        world.para()
        world.say(action.fail.replace("{paper}", paper.label))
        stuck_ending(world, hero, helper, task)
        outcome = "stuck"

    world.facts.update(hero=hero, helper=helper, clerk=clerk, task=task, paper=paper, action=action, outcome=outcome)
    return world


PLACES = {
    "castle_office": Place("castle_office", "the castle office", "office hall", "wall of drawers", "golden lantern light"),
    "queen_hall": Place("queen_hall", "the queen's hall", "royal desk", "wall of seals", "soft candlelight"),
}

TASKS = {
    "bridge_pass": Task("bridge_pass", "the bridge crossing", "file the bridge pass", "file the bridge pass", "how the mayor taught the villagers to count before crossing", {"permit", "bridge"}),
    "garden_permit": Task("garden_permit", "the moon garden", "ask for the garden permit", "ask for the garden permit", "why the royal garden logbook must be signed in order", {"permit", "garden"}),
    "library_pass": Task("library_pass", "the night library", "request the library pass", "request the library pass", "why the lamp room keeps a list of names", {"permit", "library"}),
}

PAPERS = {
    "permit": Paper("permit", "permit", "the permit papers", True, {"permit"}),
    "form": Paper("form", "form", "the form", True, {"form"}),
    "seal": Paper("seal", "seal", "the seal letter", True, {"seal"}),
}

ACTIONS = {
    "stamp": HelpAction("stamp", 3, 2, "Together they stamped the page until the last box was neat.", "They tried to wave the papers through, but the office would not allow it.", "They stamped the page and finished the permit.", {"teamwork", "paper"}),
    "copy": HelpAction("copy", 2, 2, "Together they copied the missing lines and made the page complete.", "They copied nothing useful, and the papers stayed blank.", "They copied the missing lines.", {"teamwork", "paper"}),
    "sort": HelpAction("sort", 3, 2, "Together they sorted the stack into tidy piles.", "They sorted the wrong pile and lost the important page.", "They sorted the stack into tidy piles.", {"teamwork", "paper"}),
}



@dataclass
class StoryParams:
    place: str
    task: str
    paper: str
    action: str
    teamwork: bool = True
    flashback: bool = True
    hero_name: str = "Mina"
    helper_name: str = "Pip"
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")

CURATED = [
    StoryParams("castle_office", "bridge_pass", "permit", "stamp", True, True, "Mina", "Pip"),
    StoryParams("queen_hall", "garden_permit", "form", "copy", True, True, "Lina", "Jo"),
    StoryParams("castle_office", "library_pass", "seal", "sort", True, True, "Nia", "Bo"),
]



def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for t in TASKS:
            for pa in PAPERS:
                if paperwork_risk(TASKS[t], PAPERS[pa]):
                    combos.append((p, t, pa))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    task = f["task"]
    return [
        f'Write a fairy tale with the word "bureaucracy" where a child must wait for a {task.label} because of the castle office rules.',
        f"Tell a story about teamwork and a flashback in a royal office where {f['hero'].id} and {f['helper'].id} solve a paperwork problem together.",
        f'Write a gentle fairy tale where bureaucracy is annoying at first, but teamwork turns the permit process into a happy ending.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, helper, clerk = f["hero"], f["helper"], f["clerk"]
    task, paper = f["task"], f["paper"]
    qas = [
        ("What problem did the hero have?",
         f"{hero.id} needed {paper.phrase} for {task.label}, but the castle office would not let the request go through without it."),
        ("Why did the helper mention the flashback?",
         f"{helper.id} remembered an older story about a village lesson, and that flashback explained why the bureaucracy existed. It helped everyone see that the rule was there to keep people safe and fair."),
        ("How did teamwork help?",
         f"{hero.id}, {helper.id}, and {clerk.id} worked together to fill the page, stamp it, and finish the papers. Because they shared the work, the permit could be completed instead of getting stuck."),
    ]
    if f["outcome"] == "solved":
        qas.append(("How did the story end?",
                    f"It ended happily, with the permit finished and the castle gate opening. The paperwork was no longer a problem because the team solved it together."))
    else:
        qas.append(("How did the story end?",
                    f"It ended with the papers still unfinished, so the hero had to wait. The rule remained, and the task stayed paused at the desk."))
    return qas


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is bureaucracy?",
         "Bureaucracy is a system of rules and papers that people follow when they need permission or want to keep things organized."),
        ("What is teamwork?",
         "Teamwork is when people help one another and share the work so a hard job becomes easier."),
        ("What is a flashback?",
         "A flashback is a story moment that goes back to something that happened earlier. It helps explain why the present moment matters."),
    ]


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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection_action(aid: str) -> str:
    return explain_action(aid)


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("need", tid, t.need))
    for pid, p in PAPERS.items():
        lines.append(asp.fact("paper", pid))
        if p.stampable:
            lines.append(asp.fact("stampable", pid))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("sense", aid, a.sense))
        lines.append(asp.fact("power", aid, a.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, T, Pa) :- place(P), task(T), paper(Pa), need(T, Pa), stampable(Pa).
sensible(A) :- action(A), sense(A, S), sense_min(M), S >= M.
outcome(solved) :- teamwork, flashback.
outcome(stuck) :- not outcome(solved).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([asp.fact("teamwork"), asp.fact("flashback")]) if params.teamwork and params.flashback else ""
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos().")
    if set(asp_sensible()) == {a.id for a in sensible_actions()}:
        print("OK: sensible actions match.")
    else:
        rc = 1
        print("MISMATCH in sensible actions.")
    smoke = generate(CURATED[0])
    if not smoke.story:
        rc = 1
        print("MISMATCH: smoke generation failed.")
    else:
        print("OK: smoke generation succeeded.")
    if asp_outcome(CURATED[0]) != outcome_of(CURATED[0]):
        rc = 1
        print("MISMATCH in outcome model.")
    else:
        print("OK: outcome model matches.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale bureaucracy, flashback, and teamwork.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--paper", choices=PAPERS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    if args.action and args.action not in ACTIONS:
        raise StoryError(explain_action(args.action))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.task is None or c[1] == args.task)
              and (args.paper is None or c[2] == args.paper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, task, paper = rng.choice(sorted(combos))
    action = args.action or rng.choice(sorted(ACTIONS))
    return StoryParams(place, task, paper, action, True, True, args.name or "Mina", args.helper or "Pip")


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], TASKS[params.task], PAPERS[params.paper], ACTIONS[params.action],
                 params.hero_name, params.helper_name, "Clara", params.seed or 0, params.teamwork, params.flashback)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(f"sensible actions: {', '.join(asp_sensible())}\n")
        for p, t, pa in asp_valid_combos():
            print(f"  {p:12} {t:14} {pa}")
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
                p = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
