#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/propose_repetition_fable.py
===========================================================

A tiny fable-style story world about a repeated proposal: a proud character
keeps proposing a shortcut, a steady friend keeps refusing, and repetition
turns the lesson into a simple moral.

The world is intentionally small and classical: characters have meters and
memes, the scene advances through a few causal beats, and the ending proves
what changed.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/propose_repetition_fable.py
    python storyworlds/worlds/gpt-5.4-mini/propose_repetition_fable.py --all
    python storyworlds/worlds/gpt-5.4-mini/propose_repetition_fable.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/propose_repetition_fable.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
REPETITION_TARGET = 3
BRAVERY_START = 2.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "king"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Choice:
    id: str
    scene: str
    place: str
    repeated: str
    lesson: str
    result_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Plan:
    id: str
    text: str
    risk: str
    repeats: int
    safe: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    text: str
    moral: str
    power: int
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
        clone.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label,
            "role": v.role, "traits": list(v.traits),
            "meters": defaultdict(float, dict(v.meters)),
            "memes": defaultdict(float, dict(v.memes)),
            "attrs": dict(v.attrs),
        }) for k, v in self.entities.items()}
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _r_repetition(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["proposal_count"] >= REPETITION_TARGET and ("repeat", e.id) not in world.fired:
            world.fired.add(("repeat", e.id))
            e.memes["stubbornness"] += 1
            out.append("__repeat__")
    return out


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("proposal_count", 0) >= REPETITION_TARGET and ("fear",) not in world.fired:
        world.fired.add(("fear",))
        for e in world.entities.values():
            if e.role == "listener":
                e.memes["worry"] += 1
        out.append("__worry__")
    return out


def _r_moral(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("accepted_safe", False) and ("moral",) not in world.fired:
        world.fired.add(("moral",))
        out.append("__moral__")
    return out


CAUSAL_RULES = [_r_repetition, _r_fear, _r_moral]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for c in CHOICES:
        for p in PLANS:
            for r in RESPONSES:
                if p.safe or r.power >= 1:
                    combos.append((c.id, p.id, r.id))
    return combos


def choose_name(rng: random.Random, pool: list[str]) -> str:
    return rng.choice(pool)


def tell(choice: Choice, plan: Plan, response: Response,
         proposer_name: str, proposer_gender: str,
         listener_name: str, listener_gender: str) -> World:
    world = World()
    proposer = world.add(Entity(id=proposer_name, kind="character", type=proposer_gender,
                                role="proposer", traits=["proud"]))
    listener = world.add(Entity(id=listener_name, kind="character", type=listener_gender,
                                role="listener", traits=["patient", "wise"]))
    elder = world.add(Entity(id="Elder", kind="character", type="adult", label="the elder"))

    proposer.memes["pride"] = 1.0
    proposer.meters["proposal_count"] = 0
    listener.memes["patience"] = 1.0

    world.say(
        f"Once in a small village, {proposer.id} and {listener.id} met by {choice.place}. "
        f"The day was as simple as a clear bell, and {choice.scene}."
    )
    world.say(
        f'"Let us {plan.text}," said {proposer.id}. '
        f'"{listener.id}," replied {listener.id}, "that path is not wise."'
    )

    world.para()
    repeated = 0
    accepted_safe = False
    while repeated < plan.repeats:
        repeated += 1
        proposer.meters["proposal_count"] += 1
        world.facts["proposal_count"] = int(proposer.meters["proposal_count"])
        if repeated == 1:
            world.say(f'{proposer.id} proposed it once.')
        elif repeated == 2:
            world.say(f'{proposer.id} proposed it again.')
        else:
            world.say(f'{proposer.id} proposed it yet again, and the words came back like a drumbeat.')
        if not plan.safe:
            proposer.memes["restlessness"] += 1
        if repeated < plan.repeats:
            world.say(f'{listener.id} listened, and said, "No, that would not end well."')

    world.para()
    if plan.safe:
        accepted_safe = True
        world.say(
            f'At last {listener.id} suggested a kinder way: {response.text}. '
            f'{proposer.id} heard the idea, and the third turn became the good turn.'
        )
        world.say(
            f'The two went on together, and the village path stayed bright and whole.'
        )
    else:
        world.say(
            f'At last {listener.id} would not agree, because {plan.risk}. '
            f'{elder.label_word.capitalize()} arrived and said, "{response.text}."'
        )
        if response.power >= 1:
            world.say(
                f'That steadied the moment, and {proposer.id} finally let the proposal go.'
            )
            accepted_safe = True

    world.facts.update(
        choice=choice,
        plan=plan,
        response=response,
        proposer=proposer,
        listener=listener,
        elder=elder,
        accepted_safe=accepted_safe,
    )
    propagate(world, narrate=False)

    world.para()
    if accepted_safe:
        world.say(
            f'By sunset, {proposer.id} no longer pushed the same idea again and again. '
            f'{listener.id} walked beside {proposer.id}, and the moral was plain: '
            f'{choice.lesson}.'
        )
    else:
        world.say(
            f'By sunset, the repeated proposal had faded, and everyone remembered: '
            f'{choice.lesson}.'
        )

    return world


CHOICES = [
    Choice(
        id="meadow",
        scene="the meadow smelled of clover",
        place="the meadow",
        repeated="shortcut",
        lesson="a wise friend does not praise a bad path just because it is short",
        result_word="steadier",
        tags={"fable", "repetition"},
    ),
    Choice(
        id="bridge",
        scene="the old bridge creaked softly over the stream",
        place="the bridge",
        repeated="riddle",
        lesson="the same wrong idea becomes no better when it is repeated",
        result_word="clearer",
        tags={"fable", "repetition"},
    ),
    Choice(
        id="orchard",
        scene="the orchard trees stood in neat rows of gold",
        place="the orchard",
        repeated="scheme",
        lesson="kindness is stronger than a boast repeated three times",
        result_word="gentler",
        tags={"fable", "repetition"},
    ),
]

PLANS = [
    Plan(
        id="shortcut",
        text="take the shortcut through the thorn gate",
        risk="the thorns would scratch their legs and tear their cloaks",
        repeats=3,
        safe=False,
        tags={"shortcut", "risk"},
    ),
    Plan(
        id="sing",
        text="sing the same tune three times and walk slowly home",
        risk="it is merely slow, not dangerous",
        repeats=3,
        safe=True,
        tags={"music", "safe"},
    ),
    Plan(
        id="hide",
        text="hide the bread beneath the cart and hope no one notices",
        risk="it would be a poor trick and a mean one",
        repeats=3,
        safe=False,
        tags={"trick", "risk"},
    ),
]

RESPONSES = [
    Response(
        id="pause",
        text="let us pause and choose the clean road instead",
        moral="A good path is worth more than a quick one",
        power=2,
        tags={"kindness"},
    ),
    Response(
        id="count",
        text="count to three before speaking again",
        moral="Repetition is useful only when it leads to wisdom",
        power=1,
        tags={"patience"},
    ),
    Response(
        id="loom",
        text="let us come back to this after a little thinking",
        moral="Thinking once is better than repeating a fool's plan",
        power=1,
        tags={"wisdom"},
    ),
]

NAMES_GIRL = ["Mara", "Lina", "Tess", "Nia", "Rosa"]
NAMES_BOY = ["Otto", "Niko", "Bram", "Silas", "Jory"]


@dataclass
class StoryParams:
    choice: str
    plan: str
    response: str
    proposer: str
    proposer_gender: str
    listener: str
    listener_gender: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small repetition fable story world.")
    ap.add_argument("--choice", choices=[c.id for c in CHOICES])
    ap.add_argument("--plan", choices=[p.id for p in PLANS])
    ap.add_argument("--response", choices=[r.id for r in RESPONSES])
    ap.add_argument("--proposer")
    ap.add_argument("--proposer-gender", choices=["girl", "boy"])
    ap.add_argument("--listener")
    ap.add_argument("--listener-gender", choices=["girl", "boy"])
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
    combos = valid_combos()
    if not combos:
        raise StoryError("No valid story combinations.")
    choice = args.choice or rng.choice([c.id for c in CHOICES])
    plan = args.plan or rng.choice([p.id for p in PLANS])
    response = args.response or rng.choice([r.id for r in RESPONSES])
    if choice and plan and response and (choice, plan, response) not in combos:
        raise StoryError("That combination does not fit this fable.")
    pg = args.proposer_gender or rng.choice(["girl", "boy"])
    lg = args.listener_gender or ("boy" if pg == "girl" else "girl")
    proposer = args.proposer or choose_name(rng, NAMES_GIRL if pg == "girl" else NAMES_BOY)
    listener = args.listener or choose_name(rng, NAMES_BOY if lg == "boy" else NAMES_GIRL)
    if listener == proposer:
        listener = choose_name(rng, [n for n in (NAMES_GIRL + NAMES_BOY) if n != proposer])
    return StoryParams(choice=choice, plan=plan, response=response,
                       proposer=proposer, proposer_gender=pg,
                       listener=listener, listener_gender=lg)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fable that includes the word "propose" and repeats the same proposal several times before the lesson lands.',
        f"Tell a short story where {f['proposer'].id} keeps trying to propose {f['plan'].text}, but {f['listener'].id} stays wise.",
        f"Write a repetition fable about a stubborn proposal and a calmer answer that finally ends the argument.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    proposer = f["proposer"]
    listener = f["listener"]
    choice = f["choice"]
    plan = f["plan"]
    response = f["response"]
    return [
        QAItem(
            question="What word did the story use for the stubborn suggestion?",
            answer=f"It used the word propose, because {proposer.id} kept trying to propose the same idea again and again.",
        ),
        QAItem(
            question=f"Why did {listener.id} keep saying no?",
            answer=f"{listener.id} said no because {plan.risk}. Repeating a bad idea did not make it safe, so the wiser answer was to wait and choose a better path.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with a calmer choice and a plain lesson: {choice.lesson}. By then, the repeated proposal had lost its power and the friends could walk on peacefully.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does propose mean?",
            answer="To propose means to suggest an idea or plan. In a fable, a character might propose a path, a game, or a solution.",
        ),
        QAItem(
            question="What is repetition in a story?",
            answer="Repetition means something happens or is said more than once. It can make a fable feel rhythmic and help the lesson stand out.",
        ),
        QAItem(
            question="What is a fable?",
            answer="A fable is a short story that teaches a lesson. It often uses animals or simple characters and ends with a clear moral.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        m = {k: v for k, v in e.meters.items() if v}
        mm = {k: v for k, v in e.memes.items() if v}
        if m:
            bits.append(f"meters={dict(m)}")
        if mm:
            bits.append(f"memes={dict(mm)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
repeated(P) :- proposal(P, N), repetitions(N), N >= 3.
wise_end(R) :- response(R), power(R, P), P >= 1.
valid(C, P, R) :- choice(C), plan(P), response(R).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for c in CHOICES:
        lines.append(asp.fact("choice", c.id))
    for p in PLANS:
        lines.append(asp.fact("plan", p.id))
        lines.append(asp.fact("proposal", p.id, p.repeats))
        lines.append(asp.fact("repetitions", p.repeats))
    for r in RESPONSES:
        lines.append(asp.fact("response", r.id))
        lines.append(asp.fact("power", r.id, r.power))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python valid combos differ.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP parity and generation smoke test passed.")
    return rc


def generate(params: StoryParams) -> StorySample:
    choice = next((c for c in CHOICES if c.id == params.choice), None)
    plan = next((p for p in PLANS if p.id == params.plan), None)
    response = next((r for r in RESPONSES if r.id == params.response), None)
    if not choice or not plan or not response:
        raise StoryError("Invalid story parameters.")
    world = tell(choice, plan, response, params.proposer, params.proposer_gender,
                 params.listener, params.listener_gender)
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


CURATED = [
    StoryParams(choice="meadow", plan="shortcut", response="pause",
                proposer="Mara", proposer_gender="girl", listener="Otto", listener_gender="boy"),
    StoryParams(choice="bridge", plan="hide", response="loom",
                proposer="Bram", proposer_gender="boy", listener="Lina", listener_gender="girl"),
    StoryParams(choice="orchard", plan="sing", response="count",
                proposer="Tess", proposer_gender="girl", listener="Silas", listener_gender="boy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/3."))
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            try:
                p = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(s, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
