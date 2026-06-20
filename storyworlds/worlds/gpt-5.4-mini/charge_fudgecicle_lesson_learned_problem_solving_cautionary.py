#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/charge_fudgecicle_lesson_learned_problem_solving_cautionary.py
================================================================================================

A standalone story world for a fairy-tale style cautionary lesson about a child,
a fragile frozen treat, and a wiser problem-solving turn.

The seed words are woven into the simulated world:
- charge
- fudgecicle

The story shape is:
premise -> caution -> problem solving -> lesson learned

The simulation tracks physical meters and emotional memes so the prose is driven
by state rather than by a frozen template.
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
    light: str
    coolness: str

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
class Treat:
    id: str
    label: str
    phrase: str
    melt_rate: int
    delicious: str
    fragile: bool = True

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
    power: int
    text: str
    fail: str
    qa_text: str

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


def _r_melt(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.type != "treat":
            continue
        if ent.meters["warmth"] < THRESHOLD:
            continue
        sig = ("melt", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["melting"] += 1
        out.append("__melt__")
    return out


def _r_sticky(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.type != "treat":
            continue
        if ent.meters["melting"] < THRESHOLD:
            continue
        sig = ("sticky", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "hands" in world.entities:
            world.get("hands").meters["sticky"] += 1
        out.append(f"The {ent.label} began to soften and slouch.")
    return out


CAUSAL_RULES = [Rule("melt", "physical", _r_melt), Rule("sticky", "physical", _r_sticky)]


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


def reasonableness_gate(activity: str, treat: Treat, setting: Setting) -> bool:
    return activity in {"charge", "carry", "dash"} and treat.fragile and setting.id in {"castle", "garden", "hall"}


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def treat_risk(setting: Setting, treat: Treat) -> bool:
    return setting.id in {"castle", "garden", "hall"} and treat.fragile


def predict_melt(world: World, treat_id: str) -> dict:
    sim = world.copy()
    _do_action(sim, sim.get("child"), sim.facts["action"], sim.facts["treat"], narrate=False)
    tr = sim.get(treat_id)
    return {"melted": tr.meters["melting"] >= THRESHOLD, "sticky": sim.get("hands").meters["sticky"]}


def _do_action(world: World, child: Entity, action: str, treat: Treat, narrate: bool = True) -> None:
    child.memes["impulse"] += 1
    world.get("hands").meters["warmth"] += 1
    world.get("treat").meters["warmth"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, child: Entity, helper: Entity, setting: Setting, treat: Treat) -> None:
    child.memes["joy"] += 1
    world.say(
        f"Once upon a time, in {setting.place}, {child.id} was lively and bright, and "
        f"{helper.id} kept a calm eye on the day."
    )
    world.say(
        f"{child.id} held a {treat.label} that was {treat.delicious}, and everyone called it "
        f"{treat.phrase}."
    )


def want_charge(world: World, child: Entity, setting: Setting, treat: Treat) -> None:
    world.say(
        f"But {child.id} wished to charge ahead into the {setting.light}, eager to show the little "
        f"{treat.label} to the whole wide {setting.place}."
    )


def warn(world: World, helper: Entity, child: Entity, setting: Setting, treat: Treat) -> None:
    pred = predict_melt(world, "treat")
    helper.memes["care"] += 1
    if pred["melted"]:
        world.say(
            f'"Wait," said {helper.id}. "If you charge out there, the {treat.label} will melt in the '
            f"{setting.light}. {setting.coolness} is better for a {treat.label}."
        )


def solve(world: World, helper: Entity, child: Entity, setting: Setting, treat: Treat, response: Response) -> None:
    world.say(
        f"{helper.id} did not scold. Instead, {helper.pronoun()} solved the problem by {response.text}."
    )
    world.say(
        f"{child.id} listened, and the plan turned from a rushing charge into a careful little walk."
    )


def lesson(world: World, child: Entity, helper: Entity, treat: Treat) -> None:
    child.memes["lesson"] += 1
    child.memes["calm"] += 1
    world.say(
        f"In the end, {child.id} learned that a sweet thing lasts longer when one pauses to think, "
        f"and the {treat.label} stayed safe."
    )
    world.say(
        f"{child.id} smiled at {helper.id}, proud that clever thinking saved the treat and the day."
    )


def fail(world: World, helper: Entity, treat: Treat, response: Response) -> None:
    body = response.fail.replace("{target}", treat.label)
    world.say(f"{helper.id} tried to help, but {body}.")
    world.say(f"The {treat.label} turned soft and sad before anyone could enjoy it.")


SETTINGS = {
    "castle": Setting("castle", "the castle kitchen", "sunny courtyard", "cool shade"),
    "garden": Setting("garden", "the garden gate", "golden sunlight", "cool shade"),
    "hall": Setting("hall", "the great hall", "bright window light", "cool stone"),
}

TASTES = {
    "chocolate": Treat("chocolate", "fudgecicle", "fudgecicle", 1, "sweet and chilly"),
    "berry": Treat("berry", "fudgecicle", "fudgecicle", 1, "sweet and chilly"),
}

RESPONSES = {
    "ice_box": Response(
        "ice_box", 3, 4,
        "carried the fudgecicle to the cold pantry and nestled it in a bowl of ice",
        "carried the fudgecicle to the cold pantry, but it had already melted too much",
        "carried the fudgecicle to the cold pantry and kept it cold",
    ),
    "shade_cloth": Response(
        "shade_cloth", 3, 3,
        "wrapped it in a shade cloth and walked by the cool wall",
        "wrapped it in a cloth, but the sun still warmed it too fast",
        "wrapped it in a shade cloth and kept it cool",
    ),
    "slow_walk": Response(
        "slow_walk", 2, 2,
        "walked slowly through the shade instead of charging ahead",
        "walked slowly, but the fudgecicle was too far gone",
        "walked slowly through the shade and kept it from melting",
    ),
    "water_bucket": Response(
        "water_bucket", 1, 1,
        "splashed water nearby",
        "splashed water nearby, but that did not help the fudgecicle",
        "splashed water nearby",
    ),
}

GIRL_NAMES = ["Mira", "Ella", "Nora", "Luna", "Pippa", "Tessa"]
BOY_NAMES = ["Theo", "Finn", "Leo", "Owen", "Bram", "Jules"]
HELPERS = ["fairy godmother", "old baker", "wise aunt", "garden sprite"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    treat: str
    response: str
    child: str
    child_gender: str
    helper: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for tid, treat in TASTES.items():
            if treat_risk(setting, treat):
                for rid, resp in RESPONSES.items():
                    if resp.sense >= SENSE_MIN:
                        combos.append((sid, tid, rid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale cautionary problem-solving story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--treat", choices=TASTES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError("That response is too weak for a proper cautionary tale.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.treat is None or c[1] == args.treat)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, treat, response = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(setting, treat, response, child, gender, helper)


def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(id=params.child, kind="character", type=params.child_gender, role="child"))
    helper = world.add(Entity(id=params.helper, kind="character", type="woman", role="helper"))
    world.add(Entity(id="hands", type="thing", label="little hands"))
    treat = world.add(Entity(id="treat", type="treat", label="fudgecicle"))
    setting = SETTINGS[params.setting]
    action = "charge"
    world.facts.update(action=action, treat=treat)
    setup(world, child, helper, setting, TASTES[params.treat])
    world.para()
    want_charge(world, child, setting, TASTES[params.treat])
    warn(world, helper, child, setting, TASTES[params.treat])
    world.para()
    solve(world, helper, child, setting, TASTES[params.treat], RESPONSES[params.response])
    _do_action(world, child, action, treat)
    lesson(world, child, helper, TASTES[params.treat])
    world.facts.update(child=child, helper=helper, setting=setting, treat=treat, response=RESPONSES[params.response])
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a fairy-tale cautionary story for a young child that includes the word "charge" and the word "fudgecicle".',
        'Tell a story where a child wants to charge ahead, but a wise helper offers a problem-solving solution for a fudgecicle in the sun.',
        'Write a gentle lesson-learned story with a magical feel, a fragile fudgecicle, and a safe ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    treat = f["treat"]
    setting = f["setting"]
    resp = f["response"]
    return [
        QAItem(
            question="Why did the helper warn the child?",
            answer=f"The helper warned {child.id} because the fudgecicle was in danger of melting in {setting.light}. The sun and heat would have softened it before the child could enjoy it."
        ),
        QAItem(
            question="How did they solve the problem?",
            answer=f"They solved it by {resp.qa_text}. That kept the fudgecicle cool instead of letting the day spoil it."
        ),
        QAItem(
            question="What did the child learn at the end?",
            answer="The child learned to slow down, listen, and choose the cooler path. Careful thinking helped save the sweet treat."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a fudgecicle?", "A fudgecicle is a frozen sweet treat on a stick. It can melt if it stays in the heat too long."),
        QAItem("What should you do if something delicate might melt?", "Move it to a cooler place and think before acting. Careful problem solving can protect it."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world Q&A ==")
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, T, R) :- setting(S), treat(T), response(R), fragile(T), sense_ok(R).
sense_ok(R) :- response(R), sense(R,S), sense_min(M), S >= M.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("sense_min", SENSE_MIN)]
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for t in TASTES:
        lines.append(asp.fact("treat", t))
        lines.append(asp.fact("fragile", t))
    for r, resp in RESPONSES.items():
        lines.append(asp.fact("response", r))
        lines.append(asp.fact("sense", r, resp.sense))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos disagree.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, treat=None, response=None, child=None, gender=None, helper=None), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        _ = format_qa(sample)
        print("OK: story generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams("castle", "chocolate", "ice_box", "Mira", "girl", "fairy godmother"),
    StoryParams("garden", "berry", "shade_cloth", "Theo", "boy", "old baker"),
    StoryParams("hall", "chocolate", "slow_walk", "Nora", "girl", "wise aunt"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
        for c in asp_valid_combos():
            print(c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
