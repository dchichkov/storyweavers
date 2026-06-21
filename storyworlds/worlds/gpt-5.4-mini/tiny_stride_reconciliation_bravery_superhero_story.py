#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/tiny_stride_reconciliation_bravery_superhero_story.py
====================================================================================

A standalone storyworld for a tiny superhero reconciliation tale.

Premise:
- Two child heroes disagree during a rescue mission.
- One must show bravery, make a tiny stride toward apology, and repair trust.
- The ending proves the team is stronger together.

This world keeps a small simulated model with physical meters and emotional memes,
a reasonableness gate, an inline ASP twin, and the standard Storyweavers CLI.
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
BRAVERY_INIT = 5.0
RECONCILE_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Venue:
    id: str
    place: str
    scene: str
    threat: str
    rescue_tool: str
    safety_tool: str

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
class Problem:
    id: str
    label: str
    cause: str
    danger: str
    requires_stride: bool = True

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
class Response:
    id: str
    label: str
    power: int
    text: str
    fail: str
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
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


def _r_scuffle(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["impact"] < THRESHOLD:
            continue
        sig = ("scuffle", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["hurt"] += 1
        for other in world.characters():
            if other.id != e.id:
                other.memes["worry"] += 1
        out.append("__scuffle__")
    return out


CAUSAL_RULES = [Rule("scuffle", "social", _r_scuffle)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(x for x in items if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness(problem: Problem, venue: Venue) -> bool:
    return problem.requires_stride and "team" in venue.id


def response_ok(response: Response) -> bool:
    return response.power >= 2


def predict_repair(world: World, problem_id: str, response_id: str) -> dict:
    sim = world.copy()
    _cause_conflict(sim, narrate=False)
    _do_repair(sim, sim.get("hero1"), sim.get("hero2"), RESPONSES[response_id], PROBLEMS[problem_id], narrate=False)
    return {
        "repaired": sim.get("hero1").memes["trust"] >= RECONCILE_MIN,
        "worry": sum(e.memes["worry"] for e in sim.characters()),
    }


def _cause_conflict(world: World, narrate: bool = True) -> None:
    h1, h2 = world.get("hero1"), world.get("hero2")
    h1.meters["impact"] += 1
    h2.meters["impact"] += 1
    h1.memes["pride"] += 1
    h2.memes["hurt"] += 1
    propagate(world, narrate=narrate)


def meet(world: World, venue: Venue, a: Entity, b: Entity, problem: Problem) -> None:
    world.say(
        f"On a bright afternoon at {venue.place}, {a.id} and {b.id} leapt into action like tiny superheroes. "
        f"{venue.scene}"
    )
    world.say(
        f"They were chasing {problem.label}, a {problem.cause} that could send trouble through the block."
    )


def split(world: World, a: Entity, b: Entity) -> None:
    a.memes["pride"] += 1
    b.memes["hurt"] += 1
    world.say(
        f"But when the plan got tricky, {a.id} snapped, and {b.id} crossed {b.pronoun('possessive')} arms."
    )
    world.say(
        f'For a moment, the team felt broken, and the air between them was cold and still.'
    )


def tiny_stride(world: World, a: Entity, b: Entity) -> None:
    a.memes["bravery"] += 1
    a.meters["stride"] += 1
    world.say(
        f"{a.id} took a tiny stride forward, even though {a.pronoun()} still felt embarrassed."
    )
    world.say(
        f'"I was wrong," {a.id} said quietly. "I should have listened to you."'
    )
    b.memes["softened"] += 1


def reconcile(world: World, a: Entity, b: Entity, venue: Venue) -> None:
    a.memes["trust"] += 1
    b.memes["trust"] += 1
    a.memes["hurt"] = 0.0
    b.memes["hurt"] = 0.0
    world.say(
        f"{b.id} looked up, then smiled a little. " f'"Thank you for saying that," {b.id} replied.'
    )
    world.say(
        f"They bumped fists, checked {venue.safety_tool}, and stood shoulder to shoulder again."
    )


def _do_repair(world: World, a: Entity, b: Entity, response: Response, problem: Problem, narrate: bool = True) -> None:
    a.meters["repair"] += 1
    b.meters["repair"] += 1
    a.memes["trust"] += 1
    b.memes["trust"] += 1
    if narrate:
        body = response.text.replace("{problem}", problem.label)
        world.say(body)


def rescue(world: World, venue: Venue, response: Response, problem: Problem) -> None:
    body = response.text.replace("{problem}", problem.label)
    world.say(
        f"Together they used {venue.rescue_tool}, and {body}."
    )


def lesson(world: World, a: Entity, b: Entity) -> None:
    world.say(
        f"Afterward, both heroes knew that bravery was not shouting the loudest; it was making a tiny stride toward the truth."
    )
    world.say(
        f"They left the block calmer than before, with their capes fluttering side by side."
    )


def fail_end(world: World, venue: Venue, response: Response, problem: Problem) -> None:
    world.say(
        f"Even so, the fix was too weak, and {response.fail.replace('{problem}', problem.label)}"
    )
    world.say(
        f"The heroes had to call for help and start again with a steadier plan."
    )


def tell(venue: Venue, problem: Problem, response: Response, hero1: str = "Nova",
         hero2: str = "Bolt", gender1: str = "girl", gender2: str = "boy",
         age1: int = 8, age2: int = 8) -> World:
    world = World()
    a = world.add(Entity(id="hero1", kind="character", type=gender1, label=hero1, role="leader"))
    b = world.add(Entity(id="hero2", kind="character", type=gender2, label=hero2, role="partner"))
    world.add(Entity(id="team", kind="character", type="team", label="their team"))

    a.memes["bravery"] = BRAVERY_INIT
    b.memes["bravery"] = BRAVERY_INIT - 1
    world.facts["venue"] = venue
    world.facts["problem"] = problem
    world.facts["response"] = response
    world.facts["hero1"] = a
    world.facts["hero2"] = b

    meet(world, venue, a, b, problem)
    world.para()
    split(world, a, b)
    tiny_stride(world, a, b)

    repaired = response_ok(response) and problem.requires_stride
    if repaired:
        reconcile(world, a, b, venue)
        rescue(world, venue, response, problem)
        lesson(world, a, b)
    else:
        fail_end(world, venue, response, problem)

    world.facts["outcome"] = "repaired" if repaired else "failed"
    world.facts["reconciled"] = repaired
    world.facts["brave_stride"] = a.meters["stride"] >= THRESHOLD
    return world


VENUES = {
    "team_hq": Venue("team_hq", "Team HQ", "The control room blinked with tiny lights and a city map on the wall.", "the signal glitch", "a silver net", "the repair console"),
    "rooftop": Venue("rooftop", "the rooftop", "Above the street, the moon made the chimneys glow like silver towers.", "the runaway kite", "a grappling line", "the rescue beacon"),
    "museum": Venue("museum", "the museum hall", "Between tall statues and shiny glass, the echoes felt as big as thunder.", "the missing medal", "a clue card", "the display case"),
}

PROBLEMS = {
    "glitch": Problem("glitch", "a signal glitch", "a tiny mistake in the rescue plan", "confusing the whole team", True),
    "kite": Problem("kite", "a runaway kite", "a wind tug that pulled the blue kite higher and higher", "sending it into the wires", True),
    "medal": Problem("medal", "a missing medal", "a proud prize dropped during the rush", "making the whole ceremony stall", True),
}

RESPONSES = {
    "net": Response("net", "silver net", 3, "carefully caught the {problem} before it could spread", "could not catch the {problem} in time", {"rescue"}),
    "beacon": Response("beacon", "rescue beacon", 2, "turned on the rescue beacon and guided everyone safely home", "was too dim to guide anyone", {"rescue"}),
    "card": Response("card", "clue card", 2, "used a clue card to sort the {problem} out", "did not give enough help", {"rescue"}),
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for v in VENUES:
        for p in PROBLEMS:
            for r in RESPONSES:
                if reasonableness(PROBLEMS[p], VENUES[v]) and response_ok(RESPONSES[r]):
                    combos.append((v, p, r))
    return combos


@dataclass
@dataclass
class StoryParams:
    venue: str
    problem: str
    response: str
    hero1: str
    hero2: str
    gender1: str
    gender2: str
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


NAMES_GIRL = ["Nova", "Spark", "Skye", "Iris"]
NAMES_BOY = ["Bolt", "Dash", "Leo", "Finn"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero story for a young child that uses the words "tiny" and "stride" and shows reconciliation between {f["hero1"].label} and {f["hero2"].label}.',
        f"Tell a brave superhero story where {f['hero1'].label} makes a tiny stride and apologizes after a disagreement at {f['venue'].place}.",
        f'Write a story about courage and reconciliation where two heroes repair their teamwork and the ending proves they are stronger together.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b = f["hero1"], f["hero2"]
    venue, problem = f["venue"], f["problem"]
    qa = [
        ("Who is the story about?", f"It is about two superhero kids, {a.label} and {b.label}, who tried to solve a problem together."),
        ("What problem did they face?", f"They faced {problem.label}, which was a {problem.cause}. That trouble made their teamwork wobble for a moment."),
        ("What did {0} do to fix the argument?".format(a.label), f"{a.label} took a tiny stride forward and apologized. That brave choice helped {b.label} feel ready to listen again."),
    ]
    if f["reconciled"]:
        qa.append((
            "How did the story end?",
            f"It ended with reconciliation. {a.label} and {b.label} worked side by side again, and the block felt safe and calm."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is bravery?", "Bravery means doing the right thing even when you feel nervous or afraid."),
        ("What is reconciliation?", "Reconciliation is when people who argued make peace and start trusting each other again."),
        ("What does a tiny stride mean?", "A tiny stride is a small step forward. In a story, it can mean making a small but brave move to fix a problem."),
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
        if e.label:
            bits.append(f"label={e.label}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("team_hq", "glitch", "net", "Nova", "Bolt", "girl", "boy"),
    StoryParams("rooftop", "kite", "beacon", "Skye", "Finn", "girl", "boy"),
    StoryParams("museum", "medal", "card", "Iris", "Leo", "girl", "boy"),
]


def explain_rejection(problem: Problem) -> str:
    return f"(No story: this problem does not need a tiny brave stride, so it is not a good reconciliation tale.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    return f"(Refusing response '{rid}': it is too weak for a real superhero reconciliation scene.)"


ASP_RULES = r"""
valid(V, P, R) :- venue(V), problem(P), response(R), needs_stride(P), strong(R).
outcome(repaired) :- chosen_problem(P), chosen_response(R), needs_stride(P), strong(R).
outcome(failed) :- chosen_problem(P), chosen_response(R), needs_stride(P), not strong(R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for v in VENUES:
        lines.append(asp.fact("venue", v))
    for p in PROBLEMS:
        lines.append(asp.fact("problem", p))
        lines.append(asp.fact("needs_stride", p))
    for r in RESPONSES.values():
        lines.append(asp.fact("response", r.id))
        if r.power >= 2:
            lines.append(asp.fact("strong", r.id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([asp.fact("chosen_problem", params.problem), asp.fact("chosen_response", params.response)])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    smoke = generate(CURATED[0])
    if not smoke.story.strip():
        rc = 1
        print("MISMATCH: smoke test produced empty story.")
    else:
        print("OK: smoke test generate() succeeded.")
    mismatches = sum(1 for p in CURATED if asp_outcome(p) != outcome_of(p))
    if mismatches == 0:
        print("OK: ASP outcome matches Python outcome model on curated cases.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches} curated cases differ.")
    return rc


def outcome_of(params: StoryParams) -> str:
    return "repaired" if response_ok(RESPONSES[params.response]) else "failed"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny superhero reconciliation storyworld.")
    ap.add_argument("--venue", choices=VENUES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero1")
    ap.add_argument("--hero2")
    ap.add_argument("--gender1", choices=["girl", "boy"])
    ap.add_argument("--gender2", choices=["girl", "boy"])
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
    if args.problem and args.response and not response_ok(RESPONSES[args.response]):
        raise StoryError(explain_response(args.response))
    combos = [c for c in valid_combos()
              if (args.venue is None or c[0] == args.venue)
              and (args.problem is None or c[1] == args.problem)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    venue, problem, response = rng.choice(sorted(combos))
    gender1 = args.gender1 or "girl"
    gender2 = args.gender2 or "boy"
    hero1 = args.hero1 or rng.choice(NAMES_GIRL if gender1 == "girl" else NAMES_BOY)
    hero2 = args.hero2 or rng.choice(NAMES_BOY if gender2 == "boy" else NAMES_GIRL)
    if hero1 == hero2:
        hero2 = (NAMES_BOY + NAMES_GIRL)[0]
    return StoryParams(venue, problem, response, hero1, hero2, gender1, gender2)


def generate(params: StoryParams) -> StorySample:
    world = tell(VENUES[params.venue], PROBLEMS[params.problem], RESPONSES[params.response],
                 params.hero1, params.hero2, params.gender1, params.gender2)
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for t in asp_valid_combos():
            print(" ", t)
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
