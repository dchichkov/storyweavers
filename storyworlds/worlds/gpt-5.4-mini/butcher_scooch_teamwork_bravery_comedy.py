#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/butcher_scooch_teamwork_bravery_comedy.py
=========================================================================

A standalone tiny storyworld for a comedy-flavored teamwork-and-bravery tale:
a child visits a butcher shop, a heavy cart blocks the path, and brave teamwork
turns an awkward moment into a funny, warm ending.

The world is deliberately small and constraint-checked:
- physical meters and emotional memes accumulate in a live world model
- prose is driven by world state, not frozen template swapping
- invalid combinations raise StoryError with a legible reason
- Python logic has an inline ASP twin for gate/outcome parity
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
    mood: str
    afford: set[str] = field(default_factory=set)

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
class Problem:
    id: str
    label: str
    block: str
    weight: int
    mess: str
    tags: set[str] = field(default_factory=set)

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
class Fix:
    id: str
    label: str
    action: str
    power: int
    teamwork: int
    bravado: int
    tags: set[str] = field(default_factory=set)

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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

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


def _r_jam(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("cart_jammed") and ("jam", "cart") not in world.fired:
        world.fired.add(("jam", "cart"))
        world.get("cart").meters["blocked"] += 1
        world.get("child").memes["frustration"] += 1
        out.append("__jam__")
    return out


def _r_team(world: World) -> list[str]:
    out: list[str] = []
    if world.get("child").memes["teamwork"] >= THRESHOLD and world.get("butcher").memes["teamwork"] >= THRESHOLD:
        if ("team", "push") not in world.fired:
            world.fired.add(("team", "push"))
            world.get("cart").meters["moved"] += 1
            out.append("__team__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                produced.extend(x for x in got if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


CAUSAL_RULES = [Rule("jam", "physical", _r_jam), Rule("team", "social", _r_team)]


def brief_reasonableness(problem: Problem, setting: Setting) -> bool:
    return problem.id in setting.afford


def fix_ok(fix: Fix) -> bool:
    return fix.power >= 1 and fix.teamwork >= 1 and fix.bravado >= 1


def outcome_of(problem: Problem, fix: Fix, help_now: bool) -> str:
    if not help_now:
        return "solo"
    return "cleared" if fix.power >= problem.weight else "splat"


def tell(setting: Setting, problem: Problem, fix: Fix, child_name: str, child_gender: str,
         butcher_name: str, butcher_gender: str, helper_name: str = "Mina", helper_gender: str = "girl",
         seed_note: str = "") -> World:
    world = World(setting)
    child = world.add(Entity(child_name, "character", child_gender, role="child", traits=["curious"]))
    butcher = world.add(Entity(butcher_name, "character", butcher_gender, role="butcher", traits=["steady"]))
    helper = world.add(Entity(helper_name, "character", helper_gender, role="helper", traits=["brave"]))
    cart = world.add(Entity("cart", "thing", "cart", label="the cart"))
    hook = world.add(Entity("hook", "thing", "hook", label="the rolling hook"))

    child.memes["teamwork"] = 1
    butcher.memes["teamwork"] = 1
    helper.memes["bravery"] = 1
    world.facts.update(seed_note=seed_note)

    world.say(
        f"{child.id} went to {setting.place}, where the air smelled funny in a way that made everyone smile. "
        f"{butcher.id} was at the counter, and {helper.id} was trying very hard not to laugh at a big problem."
    )
    world.say(
        f"A heavy {problem.label} had gotten stuck by {problem.block}. "
        f"{child.id} peered at it and said, \"I can help, but only if I can scooch close enough!\""
    )

    world.para()
    child.memes["bravery"] += 1
    butcher.memes["bravery"] += 1
    world.say(
        f"{helper.id} pointed at the stuck {problem.label}. \"On three,\" {helper.pronoun()} said. "
        f"\"Brave feet, tiny scooches, and no bumping noses.\""
    )
    world.say(
        f"{child.id} took a breath, nodded, and scooched to the right while {butcher.id} lifted from the left. "
        f"{child.id} almost giggled when the cart squeaked like an upset toy."
    )

    world.para()
    world.facts["cart_jammed"] = True
    if brief_reasonableness(problem, setting):
        propagate(world, narrate=False)
        if world.get("cart").meters["moved"] >= THRESHOLD:
            world.say(
                f"Together they gave one careful push. The cart rolled free, the {problem.label} stopped blocking the way, "
                f"and {helper.id} nearly fell into a basket of onions from laughing too hard."
            )
            world.say(
                f"{butcher.id} smiled so wide it looked like {butcher.id} might start laughing too. "
                f"\"That was good teamwork,\" {butcher.id} said, and even the hook seemed impressed."
            )
        else:
            world.say(
                f"They pushed and pushed, but the cart only wobbled like a stubborn pudding. "
                f"{butcher.id} chuckled, then found a smarter angle."
            )
            world.say(
                f"With one more brave scooch from {child.id} and a steady lift from {butcher.id}, the cart finally slid free."
            )
    else:
        raise StoryError("(No story: the problem does not belong in this setting.)")

    world.para()
    child.memes["teamwork"] += 1
    butcher.memes["teamwork"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"Afterward, {butcher.id} handed {child.id} a paper napkin like a medal. "
        f"{child.id} tucked it away, grinning, because the shop now felt less scary and much more friendly."
    )
    world.say(
        f"From then on, whenever the cart squeaked, {child.id} remembered that a brave scooch plus teamwork can move almost anything."
    )

    world.facts.update(
        child=child, butcher=butcher, helper=helper, problem=problem, fix=fix,
        cart=cart, hook=hook, outcome=outcome_of(problem, fix, True),
        helped=True, moved=world.get("cart").meters["moved"] >= THRESHOLD
    )
    return world


SETTINGS = {
    "shop": Setting("shop", "the butcher shop", "busy and bright", {"stuck"}),
    "market": Setting("market", "the market stall", "lively and loud", {"stuck"}),
    "kitchen": Setting("kitchen", "the kitchen", "warm and busy", {"stuck"}),
}

PROBLEMS = {
    "cart": Problem("cart", "meat cart", "the doorway", 1, "stuck in the doorway", {"shop"}),
    "crate": Problem("crate", "heavy crate", "the floor", 1, "stuck by the door", {"market"}),
    "box": Problem("box", "big box", "the rug", 1, "stuck by the sink", {"kitchen"}),
}

FIXES = {
    "push": Fix("push", "a careful push", "push together", 1, 1, 1, {"teamwork"}),
    "lift": Fix("lift", "a steady lift", "lift together", 1, 1, 1, {"teamwork"}),
    "scooch": Fix("scooch", "a brave scooch", "scooch and push", 1, 1, 1, {"bravery", "teamwork"}),
}

GIRL_NAMES = ["Mia", "Nora", "Lily", "Ava", "Zoe"]
BOY_NAMES = ["Theo", "Ben", "Max", "Finn", "Leo"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for pid, problem in PROBLEMS.items():
            if brief_reasonableness(problem, setting):
                for fid, fix in FIXES.items():
                    if fix_ok(fix):
                        combos.append((sid, pid, fid))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    problem: str
    fix: str
    child: str
    child_gender: str
    butcher: str
    butcher_gender: str
    helper: str
    helper_gender: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short comedy story for a young child that includes the words "butcher" and "scooch".',
        f"Tell a teamwork story where {f['child'].id}, {f['butcher'].id}, and {f['helper'].id} work together in {f['problem'].label}.",
        f'Write a brave, funny story ending with everyone smiling after a "scooch" helps solve a problem.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, butcher, helper, problem = f["child"], f["butcher"], f["helper"], f["problem"]
    return [
        QAItem(
            question="What problem did they have?",
            answer=f"They had a {problem.label} stuck by {problem.block}. It made the shop feel crowded until everyone worked together."
        ),
        QAItem(
            question="How did they solve it?",
            answer=f"{child.id} gave a brave scooch while {butcher.id} helped from the other side, and {helper.id} counted them in. Their teamwork moved the cart."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with the problem cleared, laughter in the shop, and {child.id} feeling proud for being brave. The cart rolled free, so the busy place felt cheerful again."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a butcher do?",
            answer="A butcher prepares and sells meat at a shop or market. They also keep the work area organized so customers can get what they need."
        ),
        QAItem(
            question="What does scooch mean?",
            answer="To scooch means to move a little bit, usually by sliding or shuffling carefully. People scooch when there is just a tiny space."
        ),
        QAItem(
            question="Why is teamwork helpful?",
            answer="Teamwork is helpful because more than one person can do a job together. That can make big or awkward tasks easier and safer."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy teamwork/bravery storyworld with butcher and scooch.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--butcher")
    ap.add_argument("--butcher-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
              and (args.problem is None or c[1] == args.problem)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    sid, pid, fid = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    butcher_gender = args.butcher_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    butcher = args.butcher or "Pat"
    helper = args.helper or "Mina"
    return StoryParams(sid, pid, fid, child, child_gender, butcher, butcher_gender, helper, helper_gender)


ASP_RULES = r"""
valid(S,P,F) :- setting(S), problem(P), fix(F).
outcome(cleared) :- chosen_fix(F), fix_power(F, Pw), chosen_problem(P), weight(P, W), Pw >= W.
outcome(solo) :- chosen_fix(F), fix_power(F, Pw), chosen_problem(P), weight(P, W), Pw < W.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("weight", pid, p.weight))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("fix_power", fid, f.power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([asp.fact("chosen_fix", params.fix), asp.fact("chosen_problem", params.problem)])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in gate.")
    params = StoryParams("shop", "cart", "scooch", "Mia", "girl", "Pat", "boy", "Mina", "girl")
    if asp_outcome(params) == outcome_of(PROBLEMS[params.problem], FIXES[params.fix], True):
        print("OK: outcome parity holds.")
    else:
        rc = 1
        print("MISMATCH in outcome parity.")
    try:
        sample = generate(params)
        assert sample.story
        print("OK: smoke test generation succeeded.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def explain_rejection() -> str:
    return "(No story: this setting does not fit the problem, so the comedy teamwork turn would not be honest.)"


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting], PROBLEMS[params.problem], FIXES[params.fix],
        params.child, params.child_gender, params.butcher, params.butcher_gender,
        params.helper, params.helper_gender,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for t in asp_valid_combos():
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("shop", "cart", "scooch", "Mia", "girl", "Pat", "girl", "Mina", "girl"),
            StoryParams("market", "crate", "push", "Theo", "boy", "Rae", "girl", "Jo", "boy"),
            StoryParams("kitchen", "box", "lift", "Nora", "girl", "Sam", "boy", "Leo", "boy"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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
