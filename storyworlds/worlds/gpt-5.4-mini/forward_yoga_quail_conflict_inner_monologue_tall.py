#!/usr/bin/env python3
"""
storyworlds/worlds/forward_yoga_quail_conflict_inner_monologue_tall.py
======================================================================

A small standalone story world about a tall-tale yoga mishap: a child or adult
tries to move *forward* through a yoga pose, a mischievous *quail* interrupts,
and an inner monologue plus a visible conflict lead to a calmer ending.

The world is deliberately tiny and state-driven:
- physical meters track balance, distance, and spill/tilt style consequences
- emotional memes track worry, pride, irritation, courage, and relief
- a forward-chained rule engine makes tension and resolution emerge from state
- a reasonableness gate ensures the generated conflict is plausible
- an inline ASP twin mirrors the Python validation and outcome logic

Run it
------
    python storyworlds/worlds/forward_yoga_quail_conflict_inner_monologue_tall.py
    python storyworlds/worlds/forward_yoga_quail_conflict_inner_monologue_tall.py --all
    python storyworlds/worlds/forward_yoga_quail_conflict_inner_monologue_tall.py --qa
    python storyworlds/worlds/forward_yoga_quail_conflict_inner_monologue_tall.py --verify
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
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
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
    label: str
    mat: str
    echo: str
    breeze: str


@dataclass
class Pose:
    id: str
    name: str
    motion: str
    balance: int
    forward_need: int
    inner_voice: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Quail:
    id: str
    label: str
    cry: str
    skitter: str
    peck: str
    startle: int
    tags: set[str] = field(default_factory=set)


@dataclass
class CalmAction:
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.meters["wobble"] < THRESHOLD:
            continue
        sig = ("wobble", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["worry"] += 1
        ent.meters["balance"] -= 1
        out.append("__wobble__")
    return out


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("Child")
    if child.memes["resist"] >= THRESHOLD and child.memes["worry"] >= THRESHOLD:
        sig = ("conflict",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        child.memes["conflict"] += 1
        out.append("__conflict__")
    return out


CAUSAL_RULES = [Rule("wobble", "physical", _r_wobble), Rule("conflict", "social", _r_conflict)]


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


def reasonable_combo(setting: Setting, pose: Pose, quail: Quail) -> bool:
    return pose.forward_need >= 1 and quail.startle >= 1 and "open" in setting.tags


def can_calm(action: CalmAction, pose: Pose, quail: Quail) -> bool:
    return action.sense >= 2 and action.power >= pose.balance + quail.startle - 1


def predict(world: World, pose: Pose, quail: Quail) -> dict:
    sim = world.copy()
    sim.get("Child").meters["wobble"] += 1
    sim.get("Child").meters["distance"] += pose.forward_need
    propagate(sim, narrate=False)
    return {
        "wobbly": sim.get("Child").meters["balance"] < 0,
        "conflict": sim.get("Child").memes["conflict"] >= THRESHOLD,
    }


def tell(setting: Setting, pose: Pose, quail: Quail, action: CalmAction,
         child_name: str = "Mina", child_gender: str = "girl",
         parent_name: str = "Grandma", parent_gender: str = "woman") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id=parent_name, kind="character", type=parent_gender, role="helper"))
    qu = world.add(Entity(id="Quail", kind="thing", type="bird", label=quail.label, attrs={"setting": setting.id}))
    mat = world.add(Entity(id="Mat", kind="thing", type="thing", label="the yoga mat"))
    child.memes["resolve"] = 1
    child.meters["balance"] = float(pose.balance)
    child.meters["forward"] = float(pose.forward_need)
    world.facts["setting"] = setting
    world.facts["pose"] = pose
    world.facts["quail"] = quail
    world.facts["action"] = action

    world.say(
        f"On a windy morning, {child.id} rolled out {setting.label} and tried a tall yoga pose on {mat.label}."
    )
    world.say(
        f"{child.id} whispered inside {child.pronoun('possessive')} own head, '{pose.inner_voice}'."
    )
    world.say(
        f"{child.id} wanted to move forward into the pose just so, while the air smelled of dust and sunshine."
    )
    world.para()
    child.memes["desire"] += 1
    child.memes["resist"] += 1
    if predict(world, pose, quail)["conflict"]:
        child.meters["wobble"] += 1
        propagate(world, narrate=True)
    world.say(
        f"Then {quail.label} came skittering in, {quail.cry.lower()} and {quail.skitter} across the edge of the mat."
    )
    child.memes["irritation"] += 1
    world.say(
        f'"Stay back," {child.id} muttered, but {child.pronoun("possessive")} knees went loose as reeds in a storm.'
    )
    world.para()
    child.meters["wobble"] += 1
    propagate(world, narrate=True)
    if can_calm(action, pose, quail):
        child.memes["courage"] += 1
        child.meters["wobble"] = 0
        world.say(
            f"{parent.label_word.capitalize()} laughed like thunder and said, 'How about {action.text}?'"
        )
        world.say(
            f"{action.qa_text.capitalize()}. The quail hopped aside, and the pose settled as steady as a fence post."
        )
        child.memes["relief"] += 1
        child.memes["joy"] += 1
    else:
        world.say(
            f"{parent.label_word.capitalize()} tried to help, but the moment was too stormy and the pose kept toppling."
        )
        world.say(
            f"{action.fail.capitalize()}, and the quail puffed off with a proud little bob."
        )
    world.facts.update(
        child=child, parent=parent, quail_entity=qu, mat=mat,
        outcome="calm" if can_calm(action, pose, quail) else "stormy",
        conflicted=child.memes["conflict"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "studio": Setting("studio", "a little yoga studio", {"open", "bright"}, "soft floorboards", "sunlight"),
    "porch": Setting("porch", "a wide porch", {"open", "bright"}, "creaky boards", "wind"),
    "field": Setting("field", "a grassy field", {"open", "bright"}, "tall grass", "breeze"),
}

POSES = {
    "forward_fold": Pose("forward_fold", "forward fold", "bend forward like a willow in a gale", 2, 1,
                         "keep going forward, but kindly", {"forward", "yoga"}),
    "warrior": Pose("warrior", "warrior pose", "step forward and stand tall", 3, 2,
                    "stand strong and do not tip", {"forward", "yoga"}),
    "tree": Pose("tree", "tree pose", "reach forward without falling", 1, 1,
                 "be still even if the world wobbles", {"yoga"}),
}

QUAILS = {
    "quail": Quail("quail", "a quail", "Quail!", "dashing in circles", "pecking at a seed", 2, {"quail"}),
    "pair": Quail("pair", "two quail", "Quail!", "skittering like spilled pepper", "pecking at crumbs", 3, {"quail"}),
}

ACTIONS = {
    "breath": CalmAction("breath", 3, 3, "take three slow breaths and count to four", "tried to breathe, but the wind and the quail won",
                         "after three slow breaths, the wobble eased", {"calm"}),
    "step_back": CalmAction("step_back", 2, 2, "step back and reset the feet", "stepped back, but the pose still toppled",
                            "after stepping back, the body found its balance again", {"calm"}),
    "kneel": CalmAction("kneel", 2, 2, "kneel down and begin again from the mat", "knelt down, but the confusion still twirled",
                        "after kneeling down, the pose could start fresh", {"calm"}),
}

GIVERS = ["Mina", "Ruby", "Jasper", "Nora", "Milo", "Etta", "Pip", "Ada"]


@dataclass
class StoryParams:
    setting: str
    pose: str
    quail: str
    action: str
    child_name: str
    child_gender: str
    parent_name: str
    parent_gender: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s_id, s in SETTINGS.items():
        for p_id, p in POSES.items():
            for q_id, q in QUAILS.items():
                if reasonable_combo(s, p, q):
                    combos.append((s_id, p_id, q_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    pose = f["pose"]
    q = f["quail"]
    return [
        f'Write a tall-tale story for a small child that includes the words "forward", "yoga", and "quail".',
        f"Tell a story where {f['child'].id} tries to do {pose.name}, but a quail interrupts and the child has a big inner monologue.",
        f"Write a funny, windy story about a yoga pose, a quail, and a helper who calms the conflict down.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    pose = f["pose"]
    action = f["action"]
    q = f["quail"]
    return [
        ("Who is the story about?",
         f"It is about {child.id}, who was trying a yoga pose on a windy day. {parent.id} helped when the quarrel with the quail got bigger."),
        ("Why did the child feel bothered?",
         f"{child.id} wanted to go forward in the pose, but the quail skittered in and broke the child's focus. That made the child wobble and feel a bit cross."),
        ("What did the child think to themself?",
         f"{child.id} thought, '{pose.inner_voice}'. That quiet thought helped {child.pronoun('object')} keep going until help arrived."),
    ]
    if f["outcome"] == "calm":
        return [
            *[],
            ("How did the helper calm things down?",
             f"{parent.id} suggested {action.text}, and that gave the child a fresh way to settle the body. The quail wandered off, and the pose became steady again."),
            ("How did the story end?",
             f"It ended with the child balanced again and the quail no longer causing a fuss. The forward pose was finished safely on the mat."),
        ] + story_qa(world)[:1]
    return [
        ("How did the helper calm things down?",
         f"{parent.id} tried to help, but the gusty little moment stayed bumpy. The child had to reset and try again."),
        ("How did the story end?",
         f"It ended with the quail puffing away and the pose still a little wobbly. Even so, the child kept trying and did not give up."),
        *story_qa(world)[:1],
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["pose"].tags) | set(f["quail"].tags) | {"yoga", "forward"}
    out = []
    if "yoga" in tags:
        out.append(("What is yoga?",
                    "Yoga is a kind of exercise where you stretch, breathe, and hold poses. It can help a body feel steady and calm."))
    if "quail" in tags:
        out.append(("What is a quail?",
                    "A quail is a small bird that can move fast over the ground. It can skitter, peep, and surprise people in a snap."))
    if "forward" in tags:
        out.append(("What does forward mean?",
                    "Forward means toward the front or ahead. In a pose, it can mean bending or moving your body toward the front."))
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("studio", "forward_fold", "quail", "breath", "Mina", "girl", "Grandma", "woman"),
    StoryParams("porch", "warrior", "pair", "step_back", "Jasper", "boy", "Dad", "man"),
    StoryParams("field", "tree", "quail", "kneel", "Nora", "girl", "Mom", "woman"),
]


def explain_rejection(setting: Setting, pose: Pose, quail: Quail) -> str:
    if not reasonable_combo(setting, pose, quail):
        return "(No story: this setting, pose, and quail combination is not plausible enough for a tall-tale conflict.)"
    return "(No story: invalid combination.)"


def outcome_of(params: StoryParams) -> str:
    return "calm" if can_calm(ACTIONS[params.action], POSES[params.pose], QUAILS[params.quail]) else "stormy"


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in POSES.items():
        lines.append(asp.fact("pose", pid))
        lines.append(asp.fact("forward_need", pid, p.forward_need))
        lines.append(asp.fact("balance", pid, p.balance))
    for qid, q in QUAILS.items():
        lines.append(asp.fact("quail", qid))
        lines.append(asp.fact("startle", qid, q.startle))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("sense", aid, a.sense))
        lines.append(asp.fact("power", aid, a.power))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,P,Q) :- setting(S), pose(P), quail(Q), open(S), forward_need(P, N), N >= 1, startle(Q, K), K >= 1.
calm(A,P,Q) :- action(A), sense(A,S), S >= 2, power(A,Pw), balance(P,B), startle(Q,K), Pw >= B + K - 1.
outcome(calm) :- calm(A,P,Q).
outcome(stormy) :- not calm(A,P,Q), action(A), pose(P), quail(Q).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([asp.fact("action", params.action), asp.fact("pose", params.pose), asp.fact("quail", params.quail)])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate:")
        print("python only:", sorted(py - cl))
        print("clingo only:", sorted(cl - py))
    samples = [CURATED[0], CURATED[1], CURATED[2]]
    bad = sum(1 for p in samples if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print("OK: outcome model matches Python on curated scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad} outcomes differ.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale yoga, quail, conflict, and inner monologue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--pose", choices=POSES)
    ap.add_argument("--quail", choices=QUAILS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--parent-name")
    ap.add_argument("--parent-gender", choices=["woman", "man"])
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
              and (args.pose is None or c[1] == args.pose)
              and (args.quail is None or c[2] == args.quail)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, pose, quail = rng.choice(sorted(combos))
    action = args.action or rng.choice(sorted(ACTIONS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIVERS)
    parent_gender = args.parent_gender or rng.choice(["woman", "man"])
    parent_name = args.parent_name or ("Grandma" if parent_gender == "woman" else "Grandpa")
    return StoryParams(setting, pose, quail, action, child_name, child_gender, parent_name, parent_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], POSES[params.pose], QUAILS[params.quail], ACTIONS[params.action],
                 params.child_name, params.child_gender, params.parent_name, params.parent_gender)
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
        for item in asp_valid_combos():
            print("  ", item)
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
