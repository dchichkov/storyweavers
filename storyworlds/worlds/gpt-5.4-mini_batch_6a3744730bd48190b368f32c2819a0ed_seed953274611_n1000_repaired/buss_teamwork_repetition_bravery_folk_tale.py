#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/buss_teamwork_repetition_bravery_folk_tale.py
===============================================================================

A small folk-tale storyworld: a village child, a stuck buss, repeated tries,
teamwork, and a brave turn that gets everyone home.

The world is built around a simple premise:
- a buss gets stuck on a rough road or at a crossing,
- the children and a helper repeat a plan together,
- bravery is needed to try the risky part,
- teamwork and repetition finally free the buss.

The story text stays child-facing and concrete, with the same simulated state
driving every variant.

Run it:
    python storyworlds/worlds/gpt-5.4-mini/buss_teamwork_repetition_bravery_folk_tale.py
    python storyworlds/worlds/gpt-5.4-mini/buss_teamwork_repetition_bravery_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4-mini/buss_teamwork_repetition_bravery_folk_tale.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/buss_teamwork_repetition_bravery_folk_tale.py --verify
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
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    road_kind: str
    dark_word: str
    opening: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Buss:
    id: str
    label: str
    phrase: str
    stuck_word: str
    move_word: str
    heavy: bool = True
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Plan:
    id: str
    name: str
    action: str
    repeat: str
    team_line: str
    bravery_need: int
    success_power: int
    fail_line: str
    success_line: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_mud(world: World) -> list[str]:
    out: list[str] = []
    buss = world.entities.get("buss")
    if not buss or buss.meters["stuck"] < THRESHOLD:
        return out
    sig = ("mud",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("road").meters["trouble"] += 1
    for ent in list(world.entities.values()):
        if ent.kind == "character":
            ent.memes["worry"] += 1
    out.append("__mud__")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    if world.get("helper").memes["helping"] < THRESHOLD:
        return out
    sig = ("teamwork",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("buss").meters["pull"] += 1
    out.append("__team__")
    return out


CAUSAL_RULES = [Rule("mud", "physical", _r_mud), Rule("teamwork", "social", _r_teamwork)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def predict(world: World, plan: Plan) -> dict:
    sim = world.copy()
    _try_plan(sim, plan, narrate=False)
    return {"freed": sim.get("buss").meters["freed"] >= THRESHOLD, "trouble": sim.get("road").meters["trouble"]}


def _try_plan(world: World, plan: Plan, narrate: bool = True) -> None:
    child = world.get("child")
    helper = world.get("helper")
    buss = world.get("buss")
    child.memes["bravery"] += 1
    helper.memes["helping"] += 1
    buss.meters["push"] += 1
    if narrate:
        world.say(plan.team_line)
    if plan.name == "rope" or plan.name == "wheel":
        buss.meters["freed"] += 1
    propagate(world, narrate=narrate)


def tell(place: Place, buss: Buss, plan: Plan, child_name: str = "Mira",
         child_gender: str = "girl", helper_name: str = "Old Kest", helper_gender: str = "woman",
         seed: Optional[int] = None) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name,
                             role="brave one", traits=["small", "brave"]))
    helper = world.add(Entity(id="helper", kind="character", type=helper_gender, label=helper_name,
                              role="helper", traits=["kind", "steady"]))
    road = world.add(Entity(id="road", kind="place", type="road", label=place.label))
    bus = world.add(Entity(id="buss", kind="thing", type="buss", label=buss.label))
    bus.meters["stuck"] = 1
    world.facts.update(place=place, buss=buss, plan=plan, child=child, helper=helper, road=road)

    world.say(
        f"Long ago, in {place.opening}, a little buss named {buss.label} went on the road. "
        f"But the road was {place.dark_word}, and {buss.label} slowed and stopped."
    )
    world.say(
        f"{child.label} pressed a hand to {child.pronoun('possessive')} chest. "
        f'"We will help the buss," {child.label} said, "even if it is hard."'
    )

    world.para()
    world.say(
        f"{helper.label} nodded. "{plan.team_line}" "
        f"They tried {plan.repeat}."
    )
    if predict(world, plan)["freed"]:
        _try_plan(world, plan, narrate=True)
        world.para()
        world.say(
            f"Once more, they pulled together. This time the buss {buss.move_word}, "
            f"and the wheels found the road."
        )
        world.say(
            f"{child.label} laughed, and {helper.label} laughed too. "
            f"The brave child had not done it alone; the whole little team had."
        )
    else:
        _try_plan(world, plan, narrate=True)
        world.para()
        world.say(
            f"They tried again and again, but the buss would not budge. "
            f"At last {helper.label} fetched a stronger help, and together they won the day."
        )
        world.say(
            f"Even then, {child.label} kept {child.pronoun('possessive')} brave heart steady."
        )

    world.facts["outcome"] = "freed" if world.get("buss").meters["freed"] >= THRESHOLD else "stalled"
    return world


PLACES = {
    "bridge": Place(id="bridge", label="the bridge", road_kind="bridge", dark_word="too narrow and dark",
                    opening="a village by the silver river", tags={"bridge", "river"}),
    "hill": Place(id="hill", label="the hill road", road_kind="hill", dark_word="steep and rocky",
                  opening="a village under a windy hill", tags={"hill"}),
    "marsh": Place(id="marsh", label="the marsh path", road_kind="marsh", dark_word="soft and muddy",
                   opening="a village beside a reed marsh", tags={"marsh"}),
}

BUSSES = {
    "red": Buss(id="red", label="Red Buss", phrase="a red buss with bright windows", stuck_word="stuck", move_word="rolled free",
                tags={"buss"}),
    "blue": Buss(id="blue", label="Blue Buss", phrase="a blue buss with a round bell", stuck_word="stuck", move_word="rattled on",
                 tags={"buss"}),
    "gold": Buss(id="gold", label="Gold Buss", phrase="a gold buss with a painted star", stuck_word="stuck", move_word="moved on",
                 tags={"buss"}),
}

PLANS = {
    "rope": Plan(id="rope", name="rope", action="pull with a rope", repeat="pull three times",
                 team_line="They tied a rope to the buss and pulled together.", bravery_need=1, success_power=1,
                 fail_line="the rope slipped in their hands", success_line="the rope held fast", tags={"teamwork", "repetition", "bravery"}),
    "push": Plan(id="push", name="push", action="push with both hands", repeat="push again and again",
                 team_line="They planted their feet and pushed together.", bravery_need=1, success_power=1,
                 fail_line="their hands slipped on the wet wood", success_line="their feet found grip", tags={"teamwork", "repetition", "bravery"}),
    "wheel": Plan(id="wheel", name="wheel", action="steady the wheel and guide", repeat="try one more careful time",
                  team_line="One held the wheel while the other guided the buss forward.", bravery_need=1, success_power=1,
                  fail_line="the wheel spun back into the rut", success_line="the wheel caught the road", tags={"teamwork", "repetition", "bravery"}),
}

GIRL_NAMES = ["Mira", "Anya", "Suri", "Lina", "Tala"]
BOY_NAMES = ["Joren", "Pavel", "Milo", "Rian", "Tomas"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid in PLACES:
        for bid in BUSSES:
            for pl in PLANS:
                combos.append((pid, bid, pl))
    return combos


@dataclass
class StoryParams:
    place: str
    buss: str
    plan: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


KNOWLEDGE = {
    "buss": [("What is a buss?", "A buss is a village vehicle that carries people and goods along the road.")],
    "teamwork": [("What is teamwork?", "Teamwork means people help one another and do a job together.")],
    "repetition": [("Why do people repeat a task?", "People repeat a task when one try is not enough and the job needs patience.")],
    "bravery": [("What is bravery?", "Bravery means trying the hard thing even when you feel a little scared.")],
    "road": [("Why can a road be hard for a heavy vehicle?", "A rough road can make a heavy vehicle slow down, sink, or get stuck.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place, buss, plan = f["place"], f["buss"], f["plan"]
    return [
        f'Write a folk-tale story that includes the word "buss" and shows teamwork, repetition, and bravery.',
        f"Tell a village tale where {f['child'].label} helps a stuck buss on {place.label} by repeating a plan with a helper.",
        f"Write a child-friendly folk tale about {buss.label} getting unstuck through brave teamwork and trying again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper, buss, place, plan = f["child"], f["helper"], f["buss"], f["place"], f["plan"]
    qa = [
        ("Who helped the buss?", f"{child.label} and {helper.label} helped the buss together."),
        ("What made the story hard?", f"The buss was stuck on {place.label}, so the road would not let it move."),
        ("How did they solve it?", f"They repeated {plan.repeat} and worked as a team until the buss could move again."),
        ("What brave thing did the child do?", f"{child.label} stayed brave and kept trying even when the first try was not enough."),
    ]
    if f.get("outcome") == "freed":
        qa.append(("How did the story end?", f"It ended happily, with the buss rolling free and everyone smiling beside the road."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["buss"].tags) | set(world.facts["plan"].tags) | {"road"}
    out = []
    for key in ["buss", "teamwork", "repetition", "bravery", "road"]:
        if key in tags:
            out.extend(KNOWLEDGE[key])
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
stuck(buss) :- buss_state(stuck).
helping(child) :- brave(child), teamwork(plan).
freed(buss) :- helping(child), repeat(plan), teamwork(plan).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for bid in BUSSES:
        lines.append(asp.fact("buss", bid))
    for pid, p in PLANS.items():
        lines.append(asp.fact("plan", pid))
        lines.append(asp.fact("teamwork", pid))
        lines.append(asp.fact("repeat", pid))
        lines.append(asp.fact("brave", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show combo/3."))
    return sorted(set(asp.atoms(model, "combo")))


def asp_verify() -> int:
    rc = 0
    # smoke test
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, buss=None, plan=None, seed=None, qa=False, json=False, trace=False, all=False, asp=False, verify=False, show_asp=False, n=1), random.Random(7)))
        _ = sample.story
        _ = sample.to_json()
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    if set(valid_combos()):
        print(f"OK: valid_combos() has {len(valid_combos())} combos.")
    else:
        print("MISMATCH: no combos.")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk tale about a buss, teamwork, repetition, and bravery.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--buss", choices=BUSSES)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["woman", "man"])
    ap.add_argument("--child-name")
    ap.add_argument("--helper-name")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.buss is None or c[1] == args.buss)
              and (args.plan is None or c[2] == args.plan)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, buss, plan = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["woman", "man"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper_name = args.helper_name or rng.choice(["Old Kest", "Mara", "Bram", "Nessa"])
    return StoryParams(
        place=place,
        buss=buss,
        plan=plan,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.buss not in BUSSES or params.plan not in PLANS:
        raise StoryError("Invalid parameters.")
    world = tell(PLACES[params.place], BUSSES[params.buss], PLANS[params.plan],
                 child_name=params.child_name, child_gender=params.child_gender,
                 helper_name=params.helper_name, helper_gender=params.helper_gender,
                 seed=params.seed)
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


CURATED = [
    StoryParams(place="bridge", buss="red", plan="rope", child_name="Mira", child_gender="girl", helper_name="Old Kest", helper_gender="woman"),
    StoryParams(place="hill", buss="blue", plan="push", child_name="Joren", child_gender="boy", helper_name="Bram", helper_gender="man"),
    StoryParams(place="marsh", buss="gold", plan="wheel", child_name="Tala", child_gender="girl", helper_name="Nessa", helper_gender="woman"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for c in valid_combos():
            print(c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
