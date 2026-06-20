#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/continue_edge_dim_employee_reconciliation_rhyming_story.py
=========================================================================================

A standalone story world for a tiny rhyming reconciliation tale.

Seed words / features:
- continue
- edge-dim
- employee
- Reconciliation
- Rhyming Story

Domain:
A tired employee and a small disagreement at closing time. The lights grow
edge-dim, a customer wants to continue browsing, and a gentle reconciliation
turns the closing moment into a kind ending. The world model tracks physical
state (meters) and emotional state (memes), so the prose changes because the
world changes.

This script follows the Storyweavers contract:
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- QAItem / StoryError / StorySample imported eagerly from storyworlds/results.py
- lazy storyworlds.asp import in ASP helpers
- --verify compares Python/ASP parity and exercises story generation
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"tired": 0.0, "closed": 0.0}
        if not self.memes:
            self.memes = {"frustration": 0.0, "kindness": 0.0, "relief": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



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
    edge_dim: bool = False
    open_late: bool = False
    closing_chime: str = ""

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
class Action:
    id: str
    need: str
    effect: str
    risk: str
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
class Response:
    id: str
    sense: int
    calm: int
    text: str
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
        return clone


PLACES = {
    "bakery": Place("bakery", "a little bakery", edge_dim=True, open_late=False, closing_chime="The bell gave a tinny note."),
    "bookshop": Place("bookshop", "a cozy bookshop", edge_dim=True, open_late=False, closing_chime="The lamp-glow turned soft and low."),
    "cafe": Place("cafe", "a warm cafe", edge_dim=False, open_late=True, closing_chime="The last cup clinked with a merry chime."),
}

ACTIONS = {
    "browse": Action("browse", need="time to continue browsing", effect="kept the shelves lively", risk="held the employee past closing", tags={"continue"}),
    "shelf": Action("shelf", need="a careful shelf check", effect="found one more crumbly loaf", risk="left the edge dim and neat", tags={"edge-dim"}),
    "change": Action("change", need="a quick change to the order", effect="turned a mistake into a smile", risk="hurt feelings if handled poorly", tags={"employee"}),
}

RESPONSES = {
    "apology": Response("apology", 3, 3, "smiled, apologized, and asked what would help", tags={"reconciliation"}),
    "invite": Response("invite", 2, 2, "invited the customer to pick one last thing and then come back tomorrow", tags={"reconciliation"}),
    "note": Response("note", 3, 3, "wrote a gentle note and offered to make it right", tags={"reconciliation"}),
}

NAMES = {
    "employee": ["Mina", "Theo", "Ivy", "Owen", "June", "Noah", "Rosa", "Eli"],
    "customer": ["Luna", "Pip", "Bree", "Milo", "Nina", "Zack", "Faye", "Otto"],
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place in PLACES.values():
        if not place.edge_dim:
            continue
        for action in ACTIONS.values():
            for response in sensible_responses():
                combos.append((place.id, action.id, response.id))
    return combos


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def predict_tension(world: World) -> dict:
    sim = world.copy()
    _apply_mood(sim, narrate=False)
    return {
        "friction": sim.get("employee").memes["frustration"],
        "repair": sim.get("employee").memes["relief"],
    }


def _apply_mood(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    emp = world.get("employee")
    cust = world.get("customer")
    if emp.memes["frustration"] >= THRESHOLD and ("frustration", "peak") not in world.fired:
        world.fired.add(("frustration", "peak"))
        emp.meters["closed"] += 1
        out.append("__edge__")
    if emp.memes["kindness"] >= THRESHOLD and cust.memes["kindness"] < THRESHOLD:
        cust.memes["hope"] += 1
    if emp.memes["relief"] >= THRESHOLD:
        emp.meters["tired"] = max(emp.meters["tired"] - 1.0, 0.0)
    if narrate:
        for line in out:
            if not line.startswith("__"):
                world.say(line)
    return out


def opening(world: World, place: Place, employee: Entity, customer: Entity) -> None:
    world.say(
        f"In {place.label}, {employee.id} swept the floor in the glow. "
        f"{place.closing_chime}"
    )
    world.say(
        f"{employee.id} was a busy employee with a smile that tried to stay neat, "
        f"and {customer.id} was still browsing the sweet little street."
    )


def edge_dim(world: World, place: Place, employee: Entity) -> None:
    if place.edge_dim:
        employee.meters["tired"] += 1
        employee.memes["frustration"] += 1
        world.say(
            "The last light went edge-dim and the counter grew small; "
            f"{employee.id} felt sleepy and ready to close for the hall."
        )


def request_continue(world: World, customer: Entity, action: Action) -> None:
    customer.memes["want"] += 1
    world.say(
        f'"Could I {action.need}?" {customer.id} asked with a tugging thin grin, '
        f"wanting to continue before the night could begin."
    )


def warning(world: World, employee: Entity, action: Action) -> None:
    pred = predict_tension(world)
    employee.memes["care"] = employee.memes.get("care", 0.0) + 1
    world.facts["predicted_friction"] = pred["friction"]
    world.say(
        f'{employee.id} breathed in and said, "{action.effect} is lovely indeed, '
        f"but we close soon, and the room needs some speed."
    )


def conflict(world: World, customer: Entity, employee: Entity, action: Action) -> None:
    customer.memes["frustration"] += 1
    employee.memes["frustration"] += 1
    world.say(
        f'"I want to continue," {customer.id} sighed, "just a little more time." '
        f"{employee.id} felt the same push, yet had closing to mind."
    )


def reconciliation(world: World, employee: Entity, customer: Entity, response: Response) -> None:
    employee.memes["kindness"] += 1
    customer.memes["kindness"] += 1
    employee.memes["relief"] += 1
    customer.memes["relief"] += 1
    employee.memes["frustration"] = max(employee.memes["frustration"] - 1, 0.0)
    customer.memes["frustration"] = max(customer.memes["frustration"] - 1, 0.0)
    world.say(
        f"Then {employee.id} remembered a softer tune: {response.text}. "
        f"{customer.id} nodded, and both faces went moon-bright and kind."
    )


def ending(world: World, place: Place, employee: Entity, customer: Entity) -> None:
    world.say(
        f"They put the stools back straight and the receipt book was signed. "
        f"{customer.id} promised to return tomorrow, and {employee.id} could unwind."
    )
    world.say(
        f"So the shop stayed calm under the edge-dim glow, "
        f"and the two left as friends with a warm afterglow."
    )


def tell(place: Place, action: Action, response: Response,
         employee_name: str = "Mina", employee_gender: str = "girl",
         customer_name: str = "Pip", customer_gender: str = "boy") -> World:
    world = World()
    employee = world.add(Entity(id=employee_name, kind="character", type=employee_gender, role="employee"))
    customer = world.add(Entity(id=customer_name, kind="character", type=customer_gender, role="customer"))

    opening(world, place, employee, customer)
    world.para()
    edge_dim(world, place, employee)
    request_continue(world, customer, action)
    warning(world, employee, action)
    conflict(world, customer, employee, action)
    world.para()
    reconciliation(world, employee, customer, response)
    ending(world, place, employee, customer)

    world.facts.update(
        place=place,
        action=action,
        response=response,
        employee=employee,
        customer=customer,
        outcome="reconciled",
        used_continue=True,
        used_edge_dim=place.edge_dim,
        used_employee=True,
    )
    return world


@dataclass
@dataclass
class StoryParams:
    place: str
    action: str
    response: str
    employee_name: str
    employee_gender: str
    customer_name: str
    customer_gender: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny rhyming story world about an employee, a continuing customer, and reconciliation."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--employee-name")
    ap.add_argument("--employee-gender", choices=["girl", "boy"])
    ap.add_argument("--customer-name")
    ap.add_argument("--customer-gender", choices=["girl", "boy"])
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
    if args.action and args.response and args.response not in RESPONSES:
        raise StoryError("Unknown response.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.action is None or c[1] == args.action)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, action, response = rng.choice(sorted(combos))
    emp_gender = args.employee_gender or rng.choice(["girl", "boy"])
    cust_gender = args.customer_gender or ("boy" if emp_gender == "girl" else "girl")
    emp_pool = NAMES["employee"]
    cust_pool = [n for n in NAMES["customer"] if n not in emp_pool]
    employee_name = args.employee_name or rng.choice(emp_pool)
    customer_name = args.customer_name or rng.choice(cust_pool)
    return StoryParams(place, action, response, employee_name, emp_gender, customer_name, cust_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story that includes the words "continue", "edge-dim", and "employee".',
        f"Tell a child-friendly reconciliation story where {f['customer'].id} wants to continue shopping, "
        f"{f['employee'].id} is an employee near closing, and the two make up kindly.",
        f"Write a short rhyming tale about a shop that goes edge-dim, a gentle disagreement, and a warm apology.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    employee = f["employee"]
    customer = f["customer"]
    place = f["place"]
    response = f["response"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {customer.id} and {employee.id} in {place.label}. The employee has to close the shop, and the customer wants to continue browsing.",
        ),
        QAItem(
            question="Why did things feel tense?",
            answer=f"The light went edge-dim and {employee.id} felt pressure to finish closing. At the same time, {customer.id} wanted to continue, so their wishes bumped together for a moment.",
        ),
        QAItem(
            question="How did they reconcile?",
            answer=f"{employee.id} answered with a kind response and {response.text}. That gave both of them relief, so the ending could be friendly instead of sharp.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does an employee do?",
            answer="An employee is a person who works for a place or a business. They help customers, keep things tidy, and do the jobs that keep the place running.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making up after a disagreement. People talk kindly, understand each other better, and feel calm again.",
        ),
        QAItem(
            question="What does edge-dim suggest about the light?",
            answer="Edge-dim suggests the light is fading near the edges. It makes a place feel like evening or closing time.",
        ),
    ]


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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} ({e.type:8}) meters={meters} memes={memes} role={e.role}")
    return "\n".join(lines)


CURATED = [
    StoryParams("bookshop", "browse", "apology", "Mina", "girl", "Pip", "boy"),
    StoryParams("bakery", "shelf", "invite", "Theo", "boy", "Luna", "girl"),
    StoryParams("cafe", "change", "note", "Ivy", "girl", "Otto", "boy"),
]


def explain_rejection() -> str:
    return "(No story: the chosen options do not make a plausible edge-dim closing-time reconciliation scene.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for aid in ACTIONS:
        lines.append(asp.fact("action", aid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,A,R) :- place(P), action(A), response(R), sense(R,S), sense_min(M), S >= M.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos():")
        print(" only python:", sorted(py - cl))
        print(" only clingo:", sorted(cl - py))
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, action=None, response=None, employee_name=None, employee_gender=None, customer_name=None, customer_gender=None), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        ACTIONS[params.action],
        RESPONSES[params.response],
        params.employee_name,
        params.employee_gender,
        params.customer_name,
        params.customer_gender,
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
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for i in range(max(args.n * 50, 50)):
            if len(samples) >= args.n:
                break
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.employee_name} & {p.customer_name}: {p.place} ({p.action}, {p.response})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
