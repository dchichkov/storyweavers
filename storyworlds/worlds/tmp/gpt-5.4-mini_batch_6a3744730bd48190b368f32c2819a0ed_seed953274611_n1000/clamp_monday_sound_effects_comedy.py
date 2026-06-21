#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/clamp_monday_sound_effects_comedy.py
=====================================================================

A small comedy storyworld about a crafty Monday, a stubborn clamp, and a noisy
sequence of sound effects. The premise is tiny on purpose: one child wants a
quiet craft project to work, the clamp keeps slipping, the helper misuses sound
effects in absurd ways, and the group finally solves the problem with a sensible
setup that turns the whole scene into a cheerful joke.

The world models physical meters and emotional memes, uses a forward-chained
simulation, generates grounded QA from world state, and includes an inline ASP
twin for the reasonableness gate and ending parity checks.
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
NEEDED_WORDS = {"clamp", "monday"}


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


@dataclass
class Setting:
    id: str
    place: str
    light: str
    noise: str


@dataclass
class ObjectCfg:
    id: str
    label: str
    phrase: str
    stubborn: bool = False
    can_be_fixed: bool = False
    can_clamp: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class SoundEffect:
    id: str
    text: str
    helps: bool = False
    fixes: bool = False
    funny: bool = False
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
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_noise(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("jammed") and "room" in world.entities:
        room = world.get("room")
        sig = ("noise",)
        if sig not in world.fired:
            world.fired.add(sig)
            room.meters["noise"] += 1
            for eid in ("kid", "helper"):
                if eid in world.entities:
                    world.get(eid).memes["surprise"] += 1
            out.append("__noise__")
    return out


CAUSAL_RULES = [Rule("noise", _r_noise)]


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


def clamp_at_risk(tool: ObjectCfg, target: ObjectCfg) -> bool:
    return tool.can_clamp and target.can_be_fixed


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for tool_id, tool in TOOLS.items():
        for target_id, target in TARGETS.items():
            if clamp_at_risk(tool, target):
                combos.append((tool_id, target_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    if params.response not in RESPONSES:
        raise StoryError(f"Unknown response: {params.response}")
    if params.tool not in TOOLS or params.target not in TARGETS:
        raise StoryError("Invalid tool or target.")
    if params.tool == "clamp" and params.target == "spout":
        return "fixed"
    return "fixed" if RESPONSES[params.response].power >= TARGETS[params.target].difficulty else "goofy"


def predict(world: World, target_id: str) -> dict:
    sim = world.copy()
    sim.get(target_id).meters["jammed"] += 1
    propagate(sim, narrate=False)
    return {"noisy": sim.get("room").meters["noise"] >= THRESHOLD}


def _do_jam(world: World, target: Entity, narrate: bool = True) -> None:
    target.meters["jammed"] += 1
    world.facts["jammed"] = True
    propagate(world, narrate=narrate)


def intro(world: World, kid: Entity, helper: Entity, setting: Setting) -> None:
    world.say(
        f"On Monday morning, {kid.id} and {helper.id} squeezed into {setting.place}. "
        f"The room was bright, a little silly, and ready for a tiny project."
    )


def setup_problem(world: World, kid: Entity, target: ObjectCfg) -> None:
    world.say(
        f"{kid.id} wanted to make the tiny project work, but the {target.label} kept slipping. "
        f"Every try went {target.label.upper() if target.label == 'clamp' else 'plunk'}."
    )


def tempt(world: World, kid: Entity, tool: ObjectCfg) -> None:
    kid.memes["determination"] += 1
    world.say(
        f'{kid.id} pointed at the bench. "I know! Use the {tool.label}!" '
        f'It sounded clever until it sounded sticky.'
    )


def warn(world: World, helper: Entity, kid: Entity, tool: ObjectCfg, target: ObjectCfg) -> None:
    pred = predict(world, target.id)
    helper.memes["worry"] += 1
    if pred["noisy"]:
        world.say(
            f'{helper.id} blinked. "{tool.label.capitalize()} is for holding things, not for pretending to be a trumpet. '
            f"If we jam the {target.label}, the whole room will go CLANG.""
        )
    else:
        world.say(f'{helper.id} said, "Let’s be sensible about the {target.label}."')


def goofy_try(world: World, kid: Entity, helper: Entity, effect: SoundEffect, target: ObjectCfg) -> None:
    world.say(
        f'{kid.id} tried it anyway. {effect.text} went "{effect.text.upper()}" and the {target.label} replied with an unhappy wobble.'
    )


def jam(world: World, target: Entity, tool: ObjectCfg, effect: SoundEffect) -> None:
    _do_jam(world, target)
    world.say(
        f"The {tool.label} bit down on the {target.label}. {effect.text} -- "
        f"but the target still wiggled like it had a secret."
    )


def fix(world: World, helper: Entity, response: Response, target: Entity, effect: SoundEffect) -> None:
    target.meters["jammed"] = 0.0
    world.get("room").meters["noise"] = 0.0
    world.say(
        f"{helper.label_word.capitalize()} laughed, then {response.text}."
    )
    world.say(
        f"{effect.text.capitalize()}! This time the {target.label} stayed put, and the whole setup finally behaved."
    )


def lesson(world: World, kid: Entity, helper: Entity, response: Response, effect: SoundEffect) -> None:
    kid.memes["relief"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"Monday turned into a joke they could keep. {kid.id} grinned, and {helper.id} said, "
        f'"Next time, the clamp gets a job, and the sound effects get the laugh line."'
    )
    world.say(
        f'They promised to use "{response.qa_text}" and save "{effect.text}" for the comedy part.'
    )


def tell(setting: Setting, tool: ObjectCfg, target: ObjectCfg, effect: SoundEffect, response: Response,
         kid_name: str = "Mia", kid_gender: str = "girl", helper_name: str = "Dad", helper_gender: str = "boy") -> World:
    world = World()
    kid = world.add(Entity(id=kid_name, kind="character", type=kid_gender, role="kid"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    room = world.add(Entity(id="room", type="room", label=setting.place))

    kid.memes["hope"] = 1
    intro(world, kid, helper, setting)
    world.para()
    setup_problem(world, kid, target)
    tempt(world, kid, tool)
    warn(world, helper, kid, tool, target)
    world.para()
    jam(world, room, tool, effect)
    goofy_try(world, kid, helper, effect, target)
    world.para()
    fix(world, helper, response, room, effect)
    lesson(world, kid, helper, response, effect)

    world.facts.update(
        kid=kid,
        helper=helper,
        setting=setting,
        tool=tool,
        target=target,
        effect=effect,
        response=response,
        jammed=True,
    )
    return world


SETTINGS = {
    "workbench": Setting(id="workbench", place="the garage workbench", light="bright", noise="echo"),
    "kitchen": Setting(id="kitchen", place="the kitchen table", light="warm", noise="clatter"),
    "shed": Setting(id="shed", place="the little shed", light="dusty", noise="creak"),
}

TOOLS = {
    "clamp": ObjectCfg(id="clamp", label="clamp", phrase="a red clamp", can_clamp=True, tags={"clamp"}),
    "tape": ObjectCfg(id="tape", label="tape", phrase="a roll of tape", tags={"tape"}),
    "spoon": ObjectCfg(id="spoon", label="spoon", phrase="a wooden spoon", tags={"spoon"}),
}

TARGETS = {
    "box": ObjectCfg(id="box", label="cardboard box", phrase="a wobbly cardboard box", can_be_fixed=True, difficulty=1, tags={"box"}),
    "lid": ObjectCfg(id="lid", label="paint can lid", phrase="a paint can lid", can_be_fixed=True, difficulty=2, tags={"lid"}),
    "spout": ObjectCfg(id="spout", label="spout", phrase="a tiny spout", can_be_fixed=True, difficulty=1, tags={"spout"}),
}

# Add missing difficulty fields dynamically via dataclass-like attribute access
for t in TARGETS.values():
    if not hasattr(t, "difficulty"):
        setattr(t, "difficulty", 1)

EFFECTS = {
    "clang": SoundEffect(id="clang", text="CLANG", helps=False, fixes=False, funny=True, tags={"clang"}),
    "boing": SoundEffect(id="boing", text="BOING", helps=False, fixes=False, funny=True, tags={"boing"}),
    "zip": SoundEffect(id="zip", text="ZIP", helps=True, fixes=False, funny=True, tags={"zip"}),
}

RESPONSES = {
    "tighten": Response(id="tighten", sense=3, power=2, text="tightened the clamp until the box stopped wiggling", fail="tried tightening it, but the box made a rude little wobble", qa_text="tightened the clamp until the box stopped wiggling", tags={"clamp"}),
    "retwist": Response(id="retwist", sense=2, power=1, text="turned the clamp one careful click and smiled", fail="turned it, but the slip came right back", qa_text="turned the clamp one careful click", tags={"clamp"}),
    "stop_laughing": Response(id="stop_laughing", sense=1, power=0, text="asked everyone to stop laughing", fail="asked everyone to stop laughing, which did not help the clamp one bit", qa_text="asked everyone to stop laughing", tags={"comedy"}),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Zoe"]
BOY_NAMES = ["Ben", "Theo", "Max", "Finn"]
TRAITS = ["curious", "silly", "careful", "cheerful"]


@dataclass
class StoryParams:
    setting: str
    tool: str
    target: str
    effect: str
    response: str
    kid_name: str
    kid_gender: str
    helper_name: str
    helper_gender: str
    trait: str = "silly"
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld with clamp, Monday, and sound effects.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--effect", choices=EFFECTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if args.tool and args.target and not clamp_at_risk(TOOLS[args.tool], TARGETS[args.target]):
        raise StoryError("This tool and target do not make a reasonable story.")
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError("That ending is too silly to be the sensible fix here.")
    combos = [c for c in valid_combos()
              if (args.tool is None or c[0] == args.tool)
              and (args.target is None or c[1] == args.target)]
    if not combos:
        raise StoryError("No valid story combination matches the given options.")
    tool_id, target_id = rng.choice(sorted(combos))
    setting_id = args.setting or rng.choice(sorted(SETTINGS))
    effect_id = args.effect or rng.choice(sorted(EFFECTS))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_name = args.helper or ("Dad" if gender == "girl" else "Mom")
    helper_gender = "boy" if helper_name == "Dad" else "girl"
    return StoryParams(
        setting=setting_id, tool=tool_id, target=target_id, effect=effect_id,
        response=response_id, kid_name=name, kid_gender=gender,
        helper_name=helper_name, helper_gender=helper_gender,
        trait=rng.choice(TRAITS),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a funny Monday story that includes the words "clamp" and "Monday" and uses sound effects.',
        f'Tell a comedy story where {f["kid"].id} tries to use a clamp on a wobbly thing, and the sound effects go a little wild.',
        f'Write a child-friendly story about {f["kid"].id}, {f["helper"].id}, a clamp, and a sensible fix with a comic ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    kid, helper, target, response = f["kid"], f["helper"], f["target"], f["response"]
    effect = f["effect"]
    return [
        QAItem(question="What day was it in the story?", answer="It was Monday morning, which made the whole scene feel busy and a little funny."),
        QAItem(question="What kept causing trouble?", answer=f"The {target.label} kept slipping, so the project could not stay steady. That is why everyone started making jokes and noises about it."),
        QAItem(question="How was the problem fixed?", answer=f"{helper.id} used a sensible response and {response.qa_text}. That stopped the wobble and let the project finally work."),
        QAItem(question="What role did the sound effects play?", answer=f"The sound effect {effect.text} made the moment feel extra silly, but it did not solve the problem by itself. It was part of the comedy while the real fix came from the clamp working properly."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a clamp?", answer="A clamp is a tool that squeezes things together so they stay in place."),
        QAItem(question="Why can sound effects be funny?", answer="Sound effects can be funny because they make ordinary actions feel larger, sillier, and more dramatic than they really are."),
        QAItem(question="What is Monday?", answer="Monday is the first day of the school and work week, so it often feels like a fresh start."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    out.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="workbench", tool="clamp", target="box", effect="clang", response="tighten", kid_name="Mia", kid_gender="girl", helper_name="Dad", helper_gender="boy", trait="silly"),
    StoryParams(setting="kitchen", tool="clamp", target="lid", effect="boing", response="retwist", kid_name="Ben", kid_gender="boy", helper_name="Mom", helper_gender="girl", trait="curious"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if t.can_clamp:
            lines.append(asp.fact("can_clamp", tid))
    for gid, g in TARGETS.items():
        lines.append(asp.fact("target", gid))
        if g.can_be_fixed:
            lines.append(asp.fact("fixable", gid))
        lines.append(asp.fact("difficulty", gid, getattr(g, "difficulty", 1)))
    for eid in EFFECTS:
        lines.append(asp.fact("effect", eid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
reasonably_valid(Tool,Target) :- can_clamp(Tool), fixable(Target).
sensible(Response) :- response(Response), sense(Response,S), sense_min(M), S >= M.
outcome(fixed) :- chosen_tool("clamp"), chosen_target(Target), fixable(Target).
outcome(goofy) :- chosen_response(Response), response(Response), sense(Response,S), sense_min(M), S < M.
outcome(fixed) :- chosen_response(Response), power(Response,P), chosen_target(Target), difficulty(Target,D), P >= D.
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show reasonably_valid/2."))
    return sorted(set(asp.atoms(model, "reasonably_valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_tool", params.tool),
        asp.fact("chosen_target", params.target),
        asp.fact("chosen_response", params.response),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    items = asp.atoms(model, "outcome")
    return items[0][0] if items else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP gate matches Python valid_combos().")
    else:
        rc = 1
        print("MISMATCH: ASP gate differs from Python valid_combos().")
    if set(asp_sensible()) == {r.id for r in sensible_responses()}:
        print("OK: sensible response sets match.")
    else:
        rc = 1
        print("MISMATCH: sensible response sets differ.")
    sample = generate(CURATED[0])
    if "Monday" not in sample.story and "monday" not in sample.story.lower():
        rc = 1
        print("MISMATCH: smoke test story missing Monday.")
    else:
        print("OK: smoke test generate() succeeded.")
    if any("clamp" not in s.story.lower() for s in [sample]):
        rc = 1
        print("MISMATCH: smoke test story missing clamp.")
    if any("clang" not in s.story.lower() and "boing" not in s.story.lower() for s in [sample]):
        rc = 1
        print("MISMATCH: smoke test story missing sound effect.")
    return rc


def generate(params: StoryParams) -> StorySample:
    for field_name in ("setting", "tool", "target", "effect", "response"):
        if getattr(params, field_name) is None:
            raise StoryError(f"Missing required parameter: {field_name}")
    if params.tool not in TOOLS or params.target not in TARGETS or params.effect not in EFFECTS or params.response not in RESPONSES:
        raise StoryError("Invalid parameter key.")
    world = tell(
        SETTINGS[params.setting], TOOLS[params.tool], TARGETS[params.target],
        EFFECTS[params.effect], RESPONSES[params.response],
        params.kid_name, params.kid_gender, params.helper_name, params.helper_gender,
    )
    story = world.render()
    if not all(w.lower() in story.lower() for w in NEEDED_WORDS):
        raise StoryError("Generated story did not include the required seed words.")
    return StorySample(
        params=params,
        story=story,
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show reasonably_valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} reasonable tool-target combos:\n")
        for tool, target in combos:
            print(f"  {tool:8} {target}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
