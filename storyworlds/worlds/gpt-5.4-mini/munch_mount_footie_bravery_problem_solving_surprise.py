#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/munch_mount_footie_bravery_problem_solving_surprise.py
=======================================================================================

A standalone storyworld for a tiny comedic adventure about a child, a snack,
a small mount, and a footie ball. The world is intentionally compact:
one child gets brave, faces a small problem, and solves it after a surprise
turn. The resulting story should feel playful, concrete, and child-facing.

The core premise:
- A child wants to munch snacks at the top of a little mount.
- A footie ball rolls away or gets stuck.
- Bravery helps the child climb or ask for help.
- Problem solving turns the mishap into a funny, safe ending.
- Surprise provides a distinct twist and final image.

This script follows the Storyweavers world contract:
- typed entities with physical meters and emotional memes
- state-driven prose
- QA from world state, not by parsing rendered English
- Python reasonableness gate plus inline ASP twin
- standard CLI flags including --verify, --asp, --show-asp, --json, --qa, --trace

The word "footie" is used as the name of the toy ball; "mount" is a small hill,
and "munch" is the child's snacky action. Comedy comes from the goofy contrast
between a grand adventure and a very small, very snacky world.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

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
class Setting:
    id: str
    place: str
    mount: str
    detail: str
    indoor: bool = False

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Snack:
    id: str
    label: str
    phrase: str
    crumbs: str
    munchy: bool = True

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Ball:
    id: str
    label: str
    phrase: str
    bouncy: bool = True
    roll: str = "rolled"

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Challenge:
    id: str
    label: str
    problem: str
    fix: str
    surprise: str
    power: int

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
            value = defaultdict(float)
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


def _r_dust(world: World) -> list[str]:
    out: list[str] = []
    if world.get("snack").meters["munched"] >= THRESHOLD and not world.get("trail").meters["crumbed"]:
        sig = ("crumbs",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("trail").meters["crumbed"] = 1
            out.append("__crumbs__")
    return out


def _r_laugh(world: World) -> list[str]:
    out: list[str] = []
    if world.get("ball").meters["stuck"] >= THRESHOLD and world.get("kid").memes["brave"] >= THRESHOLD:
        sig = ("laugh",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("kid").memes["laughing"] += 1
            out.append("__laugh__")
    return out


CAUSAL_RULES = [Rule("dust", "physical", _r_dust), Rule("laugh", "social", _r_laugh)]


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


def reasonableness_ok(setting: Setting, snack: Snack, ball: Ball, challenge: Challenge) -> bool:
    return setting.id in SETTINGS and snack.munchy and ball.bouncy and challenge.power >= 1


def outcome_of(params: "StoryParams") -> str:
    ch = CHALLENGES[params.challenge]
    return "surprised" if ch.power >= 2 else "solved"


def _do_snack(world: World, snack: Entity, narrate: bool = True) -> None:
    snack.meters["munched"] += 1
    world.get("kid").memes["joy"] += 1
    propagate(world, narrate=narrate)


def _ball_problem(world: World, ball: Entity) -> None:
    ball.meters["stuck"] += 1
    world.get("kid").memes["worry"] += 1
    propagate(world, narrate=False)


def introduce(world: World, kid: Entity, setting: Setting, snack: Snack, ball: Ball) -> None:
    world.say(
        f"{kid.id} was a small {kid.type} with big brave ideas. "
        f"One bright day, {kid.pronoun()} went to {setting.place} and looked up at {setting.mount}."
    )
    world.say(
        f"{setting.detail} {kid.id} had {snack.phrase} in a pocket and a {ball.phrase} by {kid.pronoun('possessive')} feet."
    )


def munch_setup(world: World, kid: Entity, snack: Snack) -> None:
    world.say(
        f"{kid.id} wanted to munch {snack.label} at the top, because every tiny climb feels grand when you have a snack."
    )
    _do_snack(world, world.get("snack"))


def problem_turn(world: World, kid: Entity, ball: Ball, challenge: Challenge) -> None:
    world.para()
    world.say(
        f"Then the {ball.label} did a silly thing. It {ball.roll} away and got stuck where it should not have been."
    )
    _ball_problem(world, world.get("ball"))
    world.say(
        f"{kid.id} blinked at the problem. {kid.pronoun().capitalize()} felt brave anyway, because {challenge.problem}."
    )


def solve_turn(world: World, kid: Entity, challenge: Challenge, snack: Snack) -> None:
    world.say(
        f"So {kid.id} used a very serious face and a very small plan: {challenge.fix}."
    )
    world.get("kid").memes["problem_solving"] += 1
    world.get("ball").meters["stuck"] = 0
    world.get("ball").meters["returned"] = 1
    world.say(
        f"It worked. The {world.get('ball').label} popped free, and {kid.id} laughed so hard a {snack.label} almost fell out of {kid.pronoun('possessive')} mouth."
    )


def surprise_end(world: World, kid: Entity, setting: Setting, challenge: Challenge, snack: Snack) -> None:
    world.para()
    world.say(
        f"That was when the surprise arrived: {challenge.surprise}."
    )
    world.say(
        f"At the top of the {setting.mount}, {kid.id} found a silly little sign that said, 'MUNCH ZONE -- BRAVER IF SNACKED.'"
    )
    world.say(
        f"{kid.id} gave the sign a careful nod, munched the last bite, and climbed down with crumbs on {kid.pronoun('possessive')} grin."
    )


def tell(setting: Setting, snack: Snack, ball: Ball, challenge: Challenge,
         kid_name: str = "Milo", kid_type: str = "boy", parent_type: str = "mother") -> World:
    world = World()
    kid = world.add(Entity(id=kid_name, kind="character", type=kid_type, role="hero"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="helper"))
    world.add(Entity(id="mount", type="landform", label=setting.mount))
    world.add(Entity(id="snack", type="thing", label=snack.label))
    world.add(Entity(id="ball", type="thing", label=ball.label))
    world.add(Entity(id="trail", type="thing", label="the trail"))
    kid.memes["brave"] = 1.0
    kid.memes["joy"] = 1.0
    kid.memes["worry"] = 0.0
    world.facts["setting"] = setting
    world.facts["snack"] = snack
    world.facts["ball"] = ball
    world.facts["challenge"] = challenge
    world.facts["parent"] = parent

    introduce(world, kid, setting, snack, ball)
    munch_setup(world, kid, snack)
    problem_turn(world, kid, ball, challenge)
    solve_turn(world, kid, challenge, snack)
    surprise_end(world, kid, setting, challenge, snack)

    world.facts.update(
        kid=kid,
        outcome=outcome_of(StoryParams(setting.id, snack.id, ball.id, challenge.id, kid_name, kid_type, parent_type))
    )
    return world


SETTINGS = {
    "hill": Setting("hill", "the hill", "the little mount", "The little mount looked like a hill made for ants with good manners."),
    "park": Setting("park", "the park", "the grassy mount", "The grassy mount sat beside the slide like a sleepy green pillow."),
    "yard": Setting("yard", "the yard", "the tiny mount", "The tiny mount was really just a bump pretending to be important."),
}

SNACKS = {
    "apple": Snack("apple", "apple slices", "a bag of apple slices", "crumbs"),
    "cracker": Snack("cracker", "crackers", "a paper pouch of crackers", "crumbs"),
    "cookie": Snack("cookie", "cookies", "a napkin full of cookies", "crumbs"),
}

BALLS = {
    "footie": Ball("footie", "footie ball", "a bright footie ball"),
    "softball": Ball("softball", "soft ball", "a round soft ball"),
    "mini": Ball("mini", "mini footie", "a tiny footie"),
}

CHALLENGES = {
    "stuck": Challenge("stuck", "stuck", "the ball got stuck halfway up", "roll it back with a stick", "a squirrel was already pushing it down", 2),
    "lost": Challenge("lost", "lost", "the ball vanished behind a bush", "follow the laugh trail", "a dog had tucked it into a flowerpot", 2),
    "wind": Challenge("wind", "wind", "the wind kept nudging the ball away", "use a towel as a catcher", "a kite swooped down and chased it", 1),
}

GIRL_NAMES = ["Luna", "Maya", "Ivy", "Nora", "Pia", "Zoe"]
BOY_NAMES = ["Milo", "Finn", "Theo", "Jude", "Otis", "Leo"]
TRAITS = ["brave", "curious", "quick-thinking", "cheerful"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    snack: str
    ball: str
    challenge: str
    kid: str
    kid_type: str
    parent_type: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for n in SNACKS:
            for b in BALLS:
                for c in CHALLENGES:
                    if reasonableness_ok(SETTINGS[s], SNACKS[n], BALLS[b], CHALLENGES[c]):
                        combos.append((s, n, b, c))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a comedy story for a small child that includes the words "munch", "mount", and "footie".',
        f"Tell a brave but funny story where {f['kid'].id} tries to munch snack at a mount, then solves a problem with a footie ball.",
        f"Write a playful story with a surprise ending where a child climbs a tiny mount, faces a small problem, and thinks it through.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    kid = f["kid"]
    setting = f["setting"]
    snack = f["snack"]
    ball = f["ball"]
    challenge = f["challenge"]
    return [
        QAItem(
            question="What did the child want to do at the mount?",
            answer=f"{kid.id} wanted to munch {snack.label} at the top of the {setting.mount}. It sounded like a grand adventure even though it was really just snack time."
        ),
        QAItem(
            question="What problem happened with the footie ball?",
            answer=f"The {ball.label} got stuck and made the climb funny instead of smooth. That gave {kid.id} a chance to be brave and solve it."
        ),
        QAItem(
            question="How did the child solve the problem?",
            answer=f"{kid.id} used {challenge.fix} and the {ball.label} came free again. The plan was simple, which made it feel even sillier and better."
        ),
        QAItem(
            question="What was the surprise at the end?",
            answer=f"The surprise was {challenge.surprise}. It turned the tiny mount into a very funny place to finish the story."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="What does it mean to munch something?",
            answer="To munch means to chew a snack in a noisy, eager way. It is a word that sounds a little funny, which makes it good for playful stories."
        ),
        QAItem(
            question="What is a mount?",
            answer="A mount is a small hill or raised place you can climb. It is not a huge mountain, just a little bump that feels important to a kid."
        ),
        QAItem(
            question="What is a footie ball?",
            answer="A footie ball is a ball used for kicking or rolling in play. It is bouncy, friendly, and good at causing harmless trouble."
        ),
        QAItem(
            question="Why is bravery important in the story?",
            answer="Bravery helps the child keep going even when the ball gets stuck. It does not mean being reckless; it means staying calm long enough to try a fix."
        ),
        QAItem(
            question="Why is problem solving helpful?",
            answer="Problem solving turns a stuck moment into a plan. That is how the story stays funny instead of turning into a sad frown."
        ),
        QAItem(
            question="Why does the surprise make the ending funny?",
            answer="Surprise changes what the child expects, so the ending pops a little. In comedy, that unexpected twist often makes the whole scene feel brighter."
        ),
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
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("hill", "apple", "footie", "stuck", "Milo", "boy", "mother"),
    StoryParams("park", "cookie", "mini", "lost", "Luna", "girl", "father"),
    StoryParams("yard", "cracker", "footie", "wind", "Theo", "boy", "mother"),
]


def explain_rejection() -> str:
    return "(No story: that combination would not give the child a real playful problem to solve.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: munch, mount, footie, bravery, problem solving, surprise.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--ball", choices=BALLS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--kid")
    ap.add_argument("--kid-type", choices=["girl", "boy"])
    ap.add_argument("--parent-type", choices=["mother", "father"])
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
              if (args.setting is None or c[0] == args.setting)
              and (args.snack is None or c[1] == args.snack)
              and (args.ball is None or c[2] == args.ball)
              and (args.challenge is None or c[3] == args.challenge)]
    if not combos:
        raise StoryError(explain_rejection())
    setting, snack, ball, challenge = rng.choice(sorted(combos))
    kid_type = args.kid_type or rng.choice(["girl", "boy"])
    kid = args.kid or rng.choice(GIRL_NAMES if kid_type == "girl" else BOY_NAMES)
    parent_type = args.parent_type or rng.choice(["mother", "father"])
    return StoryParams(setting, snack, ball, challenge, kid, kid_type, parent_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], SNACKS[params.snack], BALLS[params.ball], CHALLENGES[params.challenge], params.kid, params.kid_type, params.parent_type)
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


ASP_RULES = r"""
valid(S,N,B,C) :- setting(S), snack(N), ball(B), challenge(C), munchy(N), bouncy(B), power(C,P), P >= 1.
outcome(solved) :- chosen(C), power(C,P), P < 2.
outcome(surprised) :- chosen(C), power(C,P), P >= 2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for nid, n in SNACKS.items():
        lines.append(asp.fact("snack", nid))
        if n.munchy:
            lines.append(asp.fact("munchy", nid))
    for bid, b in BALLS.items():
        lines.append(asp.fact("ball", bid))
        if b.bouncy:
            lines.append(asp.fact("bouncy", bid))
    for cid, c in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        lines.append(asp.fact("power", cid, c.power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = asp.fact("chosen", params.challenge)
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    import random as _random
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP valid combos differ from Python.")
    else:
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    sample = generate(CURATED[0])
    print("OK: generate smoke test succeeded.")
    if not sample.story.strip():
        rc = 1
    cases = [CURATED[0], CURATED[1], CURATED[2]]
    for i in range(20):
        params = resolve_params(build_parser().parse_args([]), _random.Random(i))
        cases.append(params)
    if any(asp_outcome(p) not in {"solved", "surprised"} for p in cases):
        rc = 1
        print("MISMATCH: outcome model failed.")
    else:
        print(f"OK: outcome model checked on {len(cases)} scenarios.")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print(" ", combo)
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
            header = f"### {p.kid}: {p.snack} + {p.ball} on {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
