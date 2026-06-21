#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/motel_twist_whodunit.py
=======================================================

A standalone story world for a small motel whodunit with a twist.

Premise:
A child and a grown-up arrive at a quiet roadside motel. Something important
goes missing, the child notices clues, and the mystery turns out to have a
kindly, surprising answer: the "missing" thing was moved for a good reason.

The world keeps the story grounded in simulated state:
- typed entities
- physical meters and emotional memes
- forward-chained causal rules
- a reasonableness gate
- an inline ASP twin
- three Q&A sets generated from world state, not from parsing the story text
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
MYSTERY_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type)


@dataclass
class StoryParams:
    motel: str
    mystery: str
    missing: str
    clue: str
    twist: str
    child: str
    child_gender: str
    grownup: str
    grownup_gender: str
    helper: str
    seed: Optional[int] = None


@dataclass
class Motel:
    id: str
    name: str
    front: str
    room: str
    office: str
    place_detail: str
    mood: str


@dataclass
class Mystery:
    id: str
    item: str
    phrase: str
    value: str
    important: bool = True


@dataclass
class Clue:
    id: str
    text: str
    location: str
    kind: str
    hint: str
    tags: set[str] = field(default_factory=set)


@dataclass
class TwistPlan:
    id: str
    cause: str
    reveal: str
    calm_fix: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    type: str
    label: str
    role: str
    can_move: bool = True
    can_hide: bool = False
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


def _r_clue(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("mystery_seen") and world.facts.get("helper_used"):
        sig = ("clue", "revealed")
        if sig not in world.fired:
            world.fired.add(sig)
            world.facts["clue_strength"] = 1.0
            out.append("__clue__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("twist_revealed"):
        sig = ("relief", "done")
        if sig not in world.fired:
            world.fired.add(sig)
            for eid in ("child", "grownup"):
                if eid in world.entities:
                    world.get(eid).memes["relief"] += 1
            out.append("__relief__")
    return out


CAUSAL_RULES = [Rule("clue", "social", _r_clue), Rule("relief", "social", _r_relief)]


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


def stable_mystery(mystery: Mystery, clue: Clue) -> bool:
    return mystery.important and clue.kind in {"missing", "moved", "quiet"}


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def response_succeeds(response: Response, mystery: Mystery, helper: Helper) -> bool:
    return response.power >= 1 and helper.can_move and mystery.important


def predict_twist(world: World, plan: TwistPlan) -> dict:
    sim = world.copy()
    sim.facts["mystery_seen"] = True
    sim.facts["helper_used"] = True
    sim.facts["twist_revealed"] = True
    propagate(sim, narrate=False)
    return {"relief": sim.get("child").memes["relief"] if "child" in sim.entities else 0}


def discover(world: World, child: Entity, clue: Clue, mystery: Mystery) -> None:
    child.memes["curiosity"] += 1
    world.facts["mystery_seen"] = True
    world.say(
        f"In a quiet roadside motel, {child.id} noticed something odd near "
        f"{clue.location}: {clue.text}."
    )
    world.say(
        f'That made {child.id} look at {mystery.phrase} in a new way, as if the room were asking a question.'
    )


def suspect(world: World, child: Entity, helper: Helper, mystery: Mystery) -> None:
    child.memes["worry"] += 1
    world.say(
        f'{child.id} whispered, "Who moved {mystery.value}? Was it someone sneaky?"'
    )
    if helper.can_hide:
        world.say(f"Even {helper.label} seemed suspicious at first, because it knew how to hide shiny things.")
    else:
        world.say(f"Even {helper.label} looked secretive just by standing still in the corner.")


def search(world: World, grownup: Entity, mystery: Mystery, clue: Clue) -> None:
    grownup.memes["focus"] += 1
    world.say(
        f"{grownup.label_word.capitalize()} checked the room, the front desk, and the little shelf by the ice machine."
    )
    world.say(
        f"Then {grownup.pronoun()} followed the clue at {clue.location}, because the smallest details matter in a whodunit."
    )


def reveal(world: World, grownup: Entity, helper: Helper, mystery: Mystery, plan: TwistPlan) -> None:
    world.facts["twist_revealed"] = True
    helper.memes["helpful"] += 1
    body = plan.reveal.replace("{mystery}", mystery.value).replace("{helper}", helper.label)
    world.say(
        f"In the end, {grownup.label_word.capitalize()} smiled and said the answer aloud: {body}."
    )
    world.say(
        f"{plan.calm_fix} {mystery.phrase} had not been stolen after all; it had been moved for a good reason."
    )
    propagate(world, narrate=True)


def ending(world: World, child: Entity, grownup: Entity) -> None:
    child.memes["relief"] += 1
    child.memes["pride"] += 1
    grownup.memes["relief"] += 1
    world.say(
        f"{child.id} grinned at the tidy room, and {grownup.id} laughed softly. "
        f"The mystery was solved, and the motel felt calm again."
    )


def tell(motel: Motel, mystery: Mystery, clue: Clue, plan: TwistPlan, helper: Helper,
         child_name: str = "Mia", child_gender: str = "girl",
         grownup_name: str = "Aunt June", grownup_gender: str = "aunt") -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, role="detective"))
    grownup = world.add(Entity(id="grownup", kind="character", type=grownup_gender, label=grownup_name, role="guardian"))
    helper_ent = world.add(Entity(id="helper", kind="character", type=helper.type, label=helper.label, role=helper.role))
    world.add(Entity(id="motel", kind="place", type="place", label=motel.name))
    world.add(Entity(id="mystery", kind="thing", type="thing", label=mystery.phrase))
    world.add(Entity(id="clue", kind="thing", type="thing", label=clue.text))
    world.add(Entity(id="plan", kind="thing", type="thing", label=plan.reveal))

    world.say(
        f"{child_name} and {grownup_name} arrived at {motel.name}, a little motel with {motel.place_detail}."
    )
    world.say(
        f"Inside their room, {mystery.phrase} was missing, and the whole place felt like a small puzzle waiting to be solved."
    )

    world.para()
    discover(world, child, clue, mystery)
    suspect(world, child, helper_ent, mystery)
    search(world, grownup, mystery, clue)

    world.para()
    reveal(world, grownup, helper_ent, mystery, plan)
    ending(world, child, grownup)

    world.facts.update(
        child=child,
        grownup=grownup,
        helper=helper_ent,
        motel=motel,
        mystery=mystery,
        clue=clue,
        plan=plan,
        solved=True,
        twist_revealed=True,
        helper_used=True,
    )
    return world


MOTELS = {
    "sunset": Motel(
        id="sunset",
        name="Sunset Motel",
        front="a glowing front sign",
        room="a neat room with striped curtains",
        office="a tiny office with a brass bell",
        place_detail="a humming ice machine and a row of plant pots",
        mood="quiet",
    ),
    "bluebird": Motel(
        id="bluebird",
        name="Bluebird Motel",
        front="a blue sign with a painted bird",
        room="a room with a creaky dresser",
        office="a narrow office with a cookie jar",
        place_detail="a blinking vending machine and a gravel path",
        mood="still",
    ),
}

MYSTERIES = {
    "key": Mystery(id="key", item="key", phrase="the tiny room key", value="the tiny room key", important=True),
    "hat": Mystery(id="hat", item="hat", phrase="the red sun hat", value="the red sun hat", important=True),
    "cookie": Mystery(id="cookie", item="cookie", phrase="the chocolate cookie plate", value="the chocolate cookie plate", important=True),
}

CLUES = {
    "ice": Clue(id="ice", text="a wet ring by the ice machine", location="the ice machine", kind="moved", hint="cold air", tags={"ice", "moved"}),
    "bell": Clue(id="bell", text="the little brass bell on the desk had been rung", location="the desk", kind="missing", hint="office", tags={"bell", "missing"}),
    "laundry": Clue(id="laundry", text="a folded towel with a sticky note", location="the laundry cart", kind="quiet", hint="cleaning", tags={"laundry", "quiet"}),
}

TWISTS = {
    "laundry": TwistPlan(
        id="laundry",
        cause="the cleaner was tidying the room",
        reveal="it was {helper} who moved {mystery} to the laundry shelf",
        calm_fix="The cleaner had set it aside so nobody would lose it.",
        tags={"cleaning", "kind"},
    ),
    "ice": TwistPlan(
        id="ice",
        cause="the ice machine was loud",
        reveal="the answer was simple: {helper} borrowed {mystery} to mark a cooler bag",
        calm_fix="The helper only needed it for a minute.",
        tags={"ice", "borrowed"},
    ),
    "desk": TwistPlan(
        id="desk",
        cause="the front desk was busy",
        reveal="{helper} had taken {mystery} to the office so it would be safe",
        calm_fix="The office had kept it safe behind the bell.",
        tags={"office", "safe"},
    ),
}

HELPERS = {
    "cleaner": Helper(id="cleaner", type="person", label="the cleaner", role="helper", can_move=True, can_hide=False, tags={"cleaning"}),
    "deskclerk": Helper(id="deskclerk", type="person", label="the desk clerk", role="helper", can_move=True, can_hide=True, tags={"office"}),
    "cat": Helper(id="cat", type="animal", label="the motel cat", role="helper", can_move=False, can_hide=True, tags={"quiet"}),
}

RESPONSES = {
    "search": Response("search", 3, 2, "carefully searched the room and asked the front desk for help", "searched, but the clue was too small to follow", "carefully searched the room and asked the front desk for help", tags={"search"}),
    "ask": Response("ask", 3, 2, "asked the cleaner and the desk clerk one calm question at a time", "asked, but nobody had a useful answer yet", "asked the cleaner and the desk clerk one calm question at a time", tags={"ask"}),
    "check": Response("check", 2, 1, "checked the ice machine and the laundry cart", "checked, but looked in the wrong place", "checked the ice machine and the laundry cart", tags={"check"}),
}

CHILD_NAMES = ["Mia", "Nina", "Leo", "Owen", "Eli", "Ruby", "Zoe", "Iris"]
GROWNUP_NAMES = ["Aunt June", "Dad", "Mom", "Uncle Ray", "Aunt May"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for m in MOTELS:
        for mi in MYSTERIES:
            for c in CLUES:
                for t in TWISTS:
                    if stable_mystery(MYSTERIES[mi], CLUES[c]):
                        combos.append((m, mi, c, t))
    return combos


KNOWLEDGE = {
    "motel": [("What is a motel?", "A motel is a place where travelers can stay for a night or two. It often has rooms with doors outside and a parking lot nearby.")],
    "key": [("What is a room key for?", "A room key opens a hotel or motel room. It helps people get into their room and keep it locked when they leave.")],
    "laundry": [("What is laundry?", "Laundry is clothes, towels, and sheets that need to be washed. Cleaners use carts and rooms to sort them.")],
    "office": [("What is a front desk office?", "A front desk office is where a worker helps guests, answers questions, and keeps track of rooms and keys.")],
    "ice": [("What is an ice machine?", "An ice machine makes ice cubes for guests. People use them to keep drinks cold.")],
    "cookie": [("Why would a motel have cookies?", "Some motels give guests a snack to make them feel welcome. A small treat can be a friendly surprise.")],
    "mystery": [("What is a mystery?", "A mystery is something puzzling that people try to figure out. Clues help show what really happened.")],
    "whodunit": [("What does whodunit mean?", "A whodunit is a story about finding out who did something. The clues point to the answer little by little.")],
}

KNOWLEDGE_ORDER = ["motel", "key", "laundry", "office", "ice", "cookie", "mystery", "whodunit"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly whodunit story set in a motel that includes the word "motel" and ends with a twist.',
        f"Tell a short mystery about {f['motel'].name} where {f['child'].label} thinks something was stolen, but the answer is kinder than that.",
        f'Write a gentle detective story with a motel room, one clue, and a surprise ending that shows why the item was moved.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, grownup, helper = f["child"], f["grownup"], f["helper"]
    mystery, clue, plan, motel = f["mystery"], f["clue"], f["plan"], f["motel"]
    qa = [
        ("Where does the story happen?",
         f"It happens at {motel.name}, a motel with a quiet room and a clue waiting near the desk. The whole mystery stays inside that small place, which makes every detail matter."),
        ("What did the child think at first?",
         f"{child.label} thought {mystery.value} had been taken by someone sneaky. That first guess made the story feel like a real whodunit."),
        ("What clue helped solve the mystery?",
         f"The clue was {clue.text}. It mattered because it pointed toward the right place instead of the wrong suspect."),
    ]
    if f.get("twist_revealed"):
        qa.append((
            "What was the twist?",
            f"The twist was that {plan.reveal.replace('{helper}', helper.label).replace('{mystery}', mystery.value)}. "
            f"{plan.calm_fix} So the missing thing was moved to keep it safe, not stolen."
        ))
        qa.append((
            "How did the story end?",
            f"The child and the grown-up felt relieved, and the motel room was calm again. "
            f"{child.label} got to see that the mystery had a kind answer after all."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {world.facts["mystery"].item, "motel", "mystery", "whodunit"}
    tags |= set(world.facts["clue"].tags)
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(motel="sunset", mystery="key", missing="key", clue="ice", twist="laundry", child="Mia", child_gender="girl", grownup="Aunt June", grownup_gender="aunt"),
    StoryParams(motel="bluebird", mystery="hat", missing="hat", clue="bell", twist="desk", child="Leo", child_gender="boy", grownup="Dad", grownup_gender="father"),
    StoryParams(motel="sunset", mystery="cookie", missing="cookie", clue="laundry", twist="ice", child="Zoe", child_gender="girl", grownup="Mom", grownup_gender="mother"),
]


def explain_rejection(mystery: Mystery, clue: Clue) -> str:
    return f"(No story: this clue does not fit a small motel mystery about {mystery.value}. Choose a clue that plausibly points to a real moving place.)"


def outcome_of(params: StoryParams) -> str:
    return "solved"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}). Try: {better}.)"


ASP_RULES = r"""
stable_mystery(M, C) :- mystery(M), important(M), clue(C), clue_kind(C, K), K != broken.
valid(Mo, My, Cl, Tw) :- motel(Mo), mystery(My), clue(Cl), twist(Tw), stable_mystery(My, Cl).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for mid in MOTELS:
        lines.append(asp.fact("motel", mid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        if m.important:
            lines.append(asp.fact("important", mid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("clue_kind", cid, c.kind))
    for tid in TWISTS:
        lines.append(asp.fact("twist", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid combos.")
    try:
        sample = generate(resolve_params(argparse.Namespace(motel=None, mystery=None, missing=None, clue=None, twist=None, child=None, child_gender=None, grownup=None, grownup_gender=None, seed=None), random.Random(1)))
        _ = sample.story
    except Exception as e:
        print(f"Story generation smoke test failed: {e}")
        return 1
    print("OK: ASP parity and generate() smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A child-friendly motel whodunit with a twist.")
    ap.add_argument("--motel", choices=MOTELS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--grownup")
    ap.add_argument("--grownup-gender", choices=["mother", "father", "aunt", "uncle"])
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
    if args.mystery and args.clue:
        if not stable_mystery(MYSTERIES[args.mystery], CLUES[args.clue]):
            raise StoryError(explain_rejection(MYSTERIES[args.mystery], CLUES[args.clue]))
    combos = [c for c in valid_combos()
              if (args.motel is None or c[0] == args.motel)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.clue is None or c[2] == args.clue)
              and (args.twist is None or c[3] == args.twist)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    motel, mystery, clue, twist = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(CHILD_NAMES)
    grownup_gender = args.grownup_gender or rng.choice(["mother", "father", "aunt", "uncle"])
    grownup = args.grownup or rng.choice(GROWNUP_NAMES)
    return StoryParams(motel=motel, mystery=mystery, missing=mystery, clue=clue, twist=twist,
                       child=child, child_gender=child_gender, grownup=grownup, grownup_gender=grownup_gender)


def generate(params: StoryParams) -> StorySample:
    if params.motel not in MOTELS or params.mystery not in MYSTERIES or params.clue not in CLUES or params.twist not in TWISTS:
        raise StoryError("Invalid params for this motel whodunit.")
    world = tell(MOTELS[params.motel], MYSTERIES[params.mystery], CLUES[params.clue], TWISTS[params.twist], HELPERS["cleaner"], params.child, params.child_gender, params.grownup, params.grownup_gender)
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
