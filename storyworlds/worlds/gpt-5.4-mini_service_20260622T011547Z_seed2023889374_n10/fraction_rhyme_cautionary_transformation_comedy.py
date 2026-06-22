#!/usr/bin/env python3
"""
fraction_rhyme_cautionary_transformation_comedy.py
===================================================

A tiny standalone storyworld about a child, a fraction, a funny machine,
a cautionary mistake, and a transformation that ends in a safe, comic reset.

The seed tale behind this world:
- A child is trying to learn fractions while making a snack.
- A tempting "extra fizz" or "fancy transform" button looks fun.
- A warning is ignored.
- The machine transforms the snack into something silly and too big.
- A grown-up helps fix it and turns the lesson into a joke.
- The ending proves what changed: the snack is shared correctly, and the
  child chooses the safe button next time.

This script follows the Storyweavers contract:
- self-contained stdlib storyworld script
- typed entities with meters and memes
- reasonableness gate plus inline ASP twin
- three Q&A sets from world state
- --verify smoke-tests generation and parity
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
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    plural: bool = False
    transformable: bool = False
    edible: bool = False
    machine: bool = False
    safe: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    table: str
    sound: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Snack:
    id: str
    label: str
    phrase: str
    fraction: str
    shape: str
    transformed_shape: str
    part_word: str = "slice"
    tags: set[str] = field(default_factory=set)


@dataclass
class Machine:
    id: str
    label: str
    phrase: str
    button: str
    warning: str
    rhyme: str
    safe_button: str
    unsafe_button: str
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


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    snack = world.get("snack")
    machine = world.get("machine")
    if snack.meters["mixed"] < THRESHOLD:
        return out
    sig = ("transform", snack.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if machine.memes["oops"] >= THRESHOLD:
        snack.meters["transformed"] += 1
        snack.meters["giggle"] += 1
        world.get("room").meters["mess"] += 1
        out.append("__transform__")
    return out


def _r_confetti(world: World) -> list[str]:
    snack = world.get("snack")
    if snack.meters["transformed"] < THRESHOLD:
        return []
    sig = ("confetti", snack.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for name in ("child", "grownup"):
        world.get(name).memes["surprise"] += 1
    return ["__confetti__"]


CAUSAL_RULES = [Rule("transform", "physical", _r_transform), Rule("confetti", "social", _r_confetti)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            for s in rule.apply(world):
                changed = True
                if not s.startswith("__"):
                    produced.append(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def hazard_at_risk(snack: Snack, machine: Machine) -> bool:
    return snack.fraction in {"half", "third"} and machine.unsafe_button == "extra_fizz"


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for nid, snack in SNACKS.items():
            for mid, machine in MACHINES.items():
                if hazard_at_risk(snack, machine):
                    combos.append((sid, nid, mid))
    return combos


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def mix_risk(machine: Machine) -> int:
    return 1 if machine.unsafe_button == "extra_fizz" else 0


def is_contained(response: Response, machine: Machine) -> bool:
    return response.power >= mix_risk(machine) + 1


def _do_mix(world: World, snack: Entity, narrate: bool = True) -> None:
    snack.meters["mixed"] += 1
    snack.memes["curiosity"] += 1
    propagate(world, narrate=narrate)


def predict_transform(world: World) -> dict:
    sim = world.copy()
    _do_mix(sim, sim.get("snack"), narrate=False)
    return {"transformed": sim.get("snack").meters["transformed"] >= THRESHOLD,
            "mess": sim.get("room").meters["mess"]}


def start(world: World, child: Entity, grownup: Entity, setting: Setting, snack: Snack, machine: Machine) -> None:
    child.memes["joy"] += 1
    world.say(
        f"On a bright afternoon, {child.id} and {grownup.id} stood in {setting.place}. "
        f"{setting.table} waited nearby, and {setting.sound} made the room feel like a joke."
    )
    world.say(
        f"{child.id} had a {snack.fraction} {snack.label} to share. "
        f'“A fraction is fair,” {child.id} sang, “and sharing is not a scare.”'
    )


def show_machine(world: World, machine: Machine) -> None:
    world.say(
        f"They found {machine.phrase}. It had a shiny {machine.button} button and a tiny warning: "
        f'"{machine.warning}"'
    )
    world.say(
        f'{machine.rhyme} {child_name(world)} grinned, “I wonder what the buttons do?”'
    )


def child_name(world: World) -> str:
    return world.get("child").id


def warn(world: World, grownup: Entity, child: Entity, machine: Machine, snack: Snack) -> None:
    child.memes["caution"] += 1
    pred = predict_transform(world)
    world.facts["predicted_mess"] = pred["mess"]
    world.say(
        f'{grownup.id} pointed at the warning. “No extra fizz. If you push the wrong button, '
        f'{snack.label} might turn silly and spill everywhere.”'
    )


def ignore_warning(world: World, child: Entity, machine: Machine) -> None:
    child.memes["defiance"] += 1
    world.say(f'{child.id} gave a goofy grin. “I can be careful,” {child.pronoun()} said, and pressed the {machine.unsafe_button} button anyway.')


def transform(world: World, snack: Entity, snack_cfg: Snack) -> None:
    _do_mix(world, snack)
    world.say(
        f'Bzzt! The machine hiccuped. {snack_cfg.label.capitalize()} puffed, spun, and transformed '
        f'from a {snack_cfg.shape} snack into a {snack_cfg.transformed_shape}.'
    )
    world.say(
        f'“Well, that was a fraction of a plan,” {world.get("grownup").id} joked. '
        f'“Now we have a snack with extra drama.”'
    )


def alarm(world: World, child: Entity, grownup: Entity, snack_cfg: Snack) -> None:
    world.say(
        f'{child.id} squeaked, “Oops!” and {grownup.id} laughed so hard they almost dropped the spoon. '
        f'The transformed {snack_cfg.label} was wobbling like a happy jelly cloud.'
    )


def rescue(world: World, grownup: Entity, response: Response, snack: Entity, snack_cfg: Snack) -> None:
    snack.meters["mixed"] = 0
    snack.meters["transformed"] = 0
    world.get("room").meters["mess"] = 0
    body = response.text.replace("{snack}", snack_cfg.label)
    world.say(f"{grownup.label_word.capitalize()} came over and {body}.")
    world.say("The silly puff settled down, and the room went neat again.")


def lesson(world: World, grownup: Entity, child: Entity, machine: Machine, snack_cfg: Snack) -> None:
    child.memes["love"] += 1
    child.memes["safety"] += 1
    child.memes["lesson"] += 1
    child.memes["defiance"] = 0
    world.say(
        f'{grownup.id} smiled and said, “Fraction fun is best when you follow the sign. '
        f'Pick the safe button, and you’ll be just fine.”'
    )
    world.say(
        f'{child.id} nodded. “No extra fizz, no silly twist. I like my snacks when they are shared, '
        f'not risked.”'
    )


def ending(world: World, child: Entity, grownup: Entity, snack_cfg: Snack, machine: Machine) -> None:
    world.say(
        f"Then they cut the {snack_cfg.label} into a clean {snack_cfg.fraction} and ate it in neat little bites. "
        f"The machine stayed quiet, and so did the kitchen."
    )
    world.say(
        f'{child.id} even taped a tiny note to {machine.label}: “Safe button first. Funny button never.” '
        f'That was the end of the fraction caper, and the punchline behaved.'
    )


def tell(setting: Setting, snack_cfg: Snack, machine_cfg: Machine, response: Response,
         child_name_: str = "Pip", child_gender: str = "boy",
         grownup_name: str = "Aunt Joy", grownup_gender: str = "woman") -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name_,
                             role="child", traits=["curious"], attrs={"name": child_name_}))
    grownup = world.add(Entity(id="grownup", kind="character", type=grownup_gender, label=grownup_name,
                               role="grownup", traits=["funny", "careful"], attrs={"name": grownup_name}))
    room = world.add(Entity(id="room", type="room", label=setting.place))
    snack = world.add(Entity(id="snack", type="snack", label=snack_cfg.label, phrase=snack_cfg.phrase))
    machine = world.add(Entity(id="machine", type="machine", label=machine_cfg.label, phrase=machine_cfg.phrase))
    world.facts["setting"] = setting
    world.facts["snack_cfg"] = snack_cfg
    world.facts["machine_cfg"] = machine_cfg
    world.facts["response"] = response

    start(world, child, grownup, setting, snack_cfg, machine_cfg)
    world.para()
    show_machine(world, machine_cfg)
    warn(world, grownup, child, machine_cfg, snack_cfg)
    ignore_warning(world, child, machine_cfg)
    transform(world, snack, snack_cfg)
    alarm(world, child, grownup, snack_cfg)
    world.para()
    rescue(world, grownup, response, snack, snack_cfg)
    lesson(world, grownup, child, machine_cfg, snack_cfg)
    ending(world, child, grownup, snack_cfg, machine_cfg)

    world.facts.update(child=child, grownup=grownup, room=room, snack=snack, machine=machine,
                       outcome="contained")
    return world


SETTINGS = {
    "kitchen": Setting(id="kitchen", place="the kitchen", table="The counter", sound="the fridge hummed", tags={"kitchen"}),
    "classroom": Setting(id="classroom", place="the classroom", table="The teacher's table", sound="the clock ticked", tags={"classroom"}),
}

SNACKS = {
    "pizza": Snack(id="pizza", label="pizza", phrase="a cheese pizza", fraction="half", shape="triangle", transformed_shape="balloon",
                   tags={"fraction", "food"}),
    "cookie": Snack(id="cookie", label="cookie", phrase="a big cookie", fraction="third", shape="round cookie", transformed_shape="bouncy moon",
                    tags={"fraction", "food"}),
}

MACHINES = {
    "fizzbox": Machine(id="fizzbox", label="fizzbox", phrase="a fizzbox machine", button="safe", warning="Do not press extra fizz", rhyme="Rhyme time, prime time,",
                       safe_button="safe", unsafe_button="extra_fizz", tags={"machine", "safe", "fizz"}),
    "turner": Machine(id="turner", label="turner", phrase="a turner machine", button="glow", warning="No silly twist", rhyme="Twist and shift, but not too swift,",
                      safe_button="glow", unsafe_button="extra_fizz", tags={"machine", "safe", "turn"}),
}

RESPONSES = {
    "reset": Response(id="reset", sense=3, power=2, text="pressed the reset switch and gently set the {snack} right again",
                      fail="pressed the reset switch, but the {snack} was already too wildly mixed",
                      qa_text="pressed the reset switch and gently set the {snack} right again", tags={"reset", "safe"}),
    "cover": Response(id="cover", sense=2, power=2, text="covered the machine with a towel and waited until the wobble stopped",
                      fail="covered the machine with a towel, but the wobble kept bouncing under it",
                      qa_text="covered the machine with a towel and waited until the wobble stopped", tags={"cover", "safe"}),
    "scoop": Response(id="scoop", sense=1, power=1, text="scooped the snack into a bowl, but it barely helped",
                      fail="scooped the snack into a bowl, but the mess was too silly to stop",
                      qa_text="scooped the snack into a bowl, but it barely helped", tags={"scoop", "weak"}),
}

GIRL_NAMES = ["Mia", "Nora", "Luna", "Ruby", "Ada", "Zoe"]
BOY_NAMES = ["Pip", "Theo", "Max", "Ben", "Finn", "Leo"]


def valid_params() -> list[tuple[str, str, str]]:
    return valid_combos()


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a comedy story for a young child that uses the word "fraction" and ends with a safe choice.',
        f'Tell a rhyming cautionary story where {f["child"].id} almost presses the wrong button on {f["machine_cfg"].label}.',
        f'Write a funny story about {f["child"].id} sharing {f["snack_cfg"].fraction} of a {f["snack_cfg"].label} and learning to use the safe button.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    grownup = f["grownup"]
    snack = f["snack_cfg"]
    machine = f["machine_cfg"]
    qa = [
        QAItem(
            question=f"Why did {child.id} want to use the machine?",
            answer=f"{child.id} wanted to make the fraction snack funny and bright. The machine looked exciting, so the idea felt like a joke waiting to happen.",
        ),
        QAItem(
            question=f"Why did {grownup.id} warn {child.id} about the button?",
            answer=f"{grownup.id} warned {child.id} because the wrong button could turn the snack silly and messy. That warning was careful, not mean, because the safe button was the better choice.",
        ),
        QAItem(
            question=f"What happened after {child.id} pressed the wrong button?",
            answer=f"The snack transformed into a wobbling, bouncy shape, and the kitchen got messy. It was funny to watch, but it also proved the warning was right.",
        ),
        QAItem(
            question=f"What did {grownup.id} do to fix the mess?",
            answer=f"{grownup.id} used the safe response to set the snack right again and calm the room. After that, the machine was quiet and everyone could laugh instead of panic.",
        ),
        QAItem(
            question=f"What did {child.id} learn at the end?",
            answer=f"{child.id} learned to choose the safe button first and to share the fraction snack neatly. The joke stayed funny, but the risky part was gone.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What is a fraction?",
            answer="A fraction is a way to show a part of a whole. It helps people talk about sharing things fairly.",
        ),
        QAItem(
            question="Why can a machine button be dangerous if you press the wrong one?",
            answer="Because some buttons change what a machine does in ways you did not mean. If the change is messy or unsafe, it can make trouble very quickly.",
        ),
        QAItem(
            question="What should you do when a grown-up gives a safety warning?",
            answer="You should listen and choose the safe option. Warnings are there to stop small mistakes from turning into big ones.",
        ),
    ]
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
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(),
]


def explain_rejection(snack: Snack, machine: Machine) -> str:
    return (
        f"(No story: {machine.label} with the {snack.fraction} {snack.label} is not a valid cautionary "
        f"hazard here unless the unsafe button can really cause a transform.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "contained"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for snid, s in SNACKS.items():
        lines.append(asp.fact("snack", snid))
        lines.append(asp.fact("fraction", snid, s.fraction))
    for mid, m in MACHINES.items():
        lines.append(asp.fact("machine", mid))
        lines.append(asp.fact("unsafe_button", mid, m.unsafe_button))
        lines.append(asp.fact("safe_button", mid, m.safe_button))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,N,M) :- setting(S), snack(N), machine(M), unsafe_button(M, extra_fizz), fraction(N, half).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
outcome(contained) :- sensible(R), power(R, P), P >= 1.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program(show="#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    model = asp.one_model(asp_program(extra=asp.fact("chosen", "x"), show="#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "contained"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid combos")
        rc = 1
    if set(asp_sensible()) != {r.id for r in sensible_responses()}:
        print("MISMATCH in sensible responses")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(
            setting=None, snack=None, machine=None, response=None, child=None, grownup=None, seed=777, n=1,
            all=False, trace=False, qa=False, json=False, asp=False, verify=False, show_asp=False
        ), random.Random(777)))
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedic fraction storyworld with a cautionary machine.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--machine", choices=MACHINES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child")
    ap.add_argument("--grownup")
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
    setting, snack, machine = rng.choice(combos)
    response = args.response or rng.choice(sorted(sensible_responses(), key=lambda r: r.id)).id
    return StoryParams()


def generate(params: StoryParams) -> StorySample:
    if not isinstance(params, StoryParams):
        raise StoryError("Invalid parameters.")
    world = tell(SETTINGS["kitchen"], SNACKS["pizza"], MACHINES["fizzbox"], RESPONSES["reset"])
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


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
        print(asp_program(show="#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(str(x) for x in asp_valid_combos()))
        return
    sample = generate(StoryParams())
    if args.json:
        print(sample.to_json())
    else:
        emit(sample, trace=args.trace, qa=args.qa)


if __name__ == "__main__":
    main()
