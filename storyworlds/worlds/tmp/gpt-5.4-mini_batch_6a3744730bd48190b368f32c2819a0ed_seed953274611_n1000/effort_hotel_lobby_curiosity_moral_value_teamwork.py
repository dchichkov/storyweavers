#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/effort_hotel_lobby_curiosity_moral_value_teamwork.py
====================================================================================

A small, heartwarming storyworld set in a hotel lobby.

Premise
-------
A curious child notices something out of place in the hotel lobby, wants to know
what it is, and discovers that helping kindly takes effort. With teamwork and a
moral choice to do the right thing, the lobby becomes warm and welcoming again.

The world is intentionally tiny and classical:
- typed entities with meters and memes
- forward-chained causal state changes
- a reasonableness gate
- Q&A generated from world state, not from rendered prose
- an inline ASP twin for parity checks

This world includes the seed words/features:
- effort
- Curiosity
- Moral Value
- Teamwork
- hotel lobby
- heartwarming style
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
        return self.label or self.type


@dataclass
class LobbySetting:
    id: str
    place: str
    detail: str
    calm: str


@dataclass
class TidyItem:
    id: str
    label: str
    mess: str
    weight: int
    moral_task: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperTool:
    id: str
    label: str
    phrase: str
    helps_with: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class OutcomePlan:
    id: str
    effort: int
    teamwork: int
    text: str
    after: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: LobbySetting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_clean(world: World) -> list[str]:
    out: list[str] = []
    area = world.get("lobby")
    if area.meters["mess"] < THRESHOLD:
        return out
    sig = ("clean",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    area.meters["mess"] = 0.0
    area.meters["shine"] += 1
    for kid in world.characters():
        kid.memes["pride"] += 1
    out.append("__shine__")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    if world.get("child").memes["helping"] < THRESHOLD:
        return out
    if world.get("adult").memes["helping"] < THRESHOLD:
        return out
    sig = ("teamwork",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("child").memes["teamwork"] += 1
    world.get("adult").memes["teamwork"] += 1
    out.append("__teamwork__")
    return out


CAUSAL_RULES = [Rule("clean", _r_clean), Rule("teamwork", _r_teamwork)]


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


def predict_mess(world: World, item: TidyItem) -> dict:
    sim = world.copy()
    sim.get("lobby").meters["mess"] += item.weight
    return {
        "messy": sim.get("lobby").meters["mess"] >= THRESHOLD,
    }


def is_reasonable(item: TidyItem, tool: HelperTool, plan: OutcomePlan) -> bool:
    return item.moral_task in tool.helps_with and plan.effort >= 1 and plan.teamwork >= 1


def _make_mess(world: World, child: Entity, item: TidyItem) -> None:
    child.memes["curiosity"] += 1
    world.get("lobby").meters["mess"] += item.weight
    world.get("child").meters["effort"] += 1
    world.say(
        f"In the hotel lobby, {child.id} spotted {item.label} and leaned closer to see what it was."
    )
    world.say(
        f"That curious choice made the floor a little messy, and {child.id} felt the effort of helping."
    )


def notice(world: World, child: Entity, adult: Entity, item: TidyItem) -> None:
    world.say(
        f"{child.id} paused by the lobby bench and noticed {item.label}. "
        f'"I wonder why someone left that there," {child.pronoun()} said.'
    )
    child.memes["curiosity"] += 1


def moral_turn(world: World, child: Entity, adult: Entity, item: TidyItem) -> None:
    world.say(
        f"{adult.id} smiled gently and said, \"We can help because it is the kind thing to do.\""
    )
    adult.memes["moral_value"] += 1
    child.memes["moral_value"] += 1


def team_up(world: World, child: Entity, adult: Entity, tool: HelperTool) -> None:
    child.memes["helping"] += 1
    adult.memes["helping"] += 1
    world.say(
        f"They worked together with {tool.phrase}, taking turns and sharing the effort."
    )


def finish(world: World, child: Entity, adult: Entity, item: TidyItem, plan: OutcomePlan) -> None:
    world.say(plan.text)
    world.say(plan.after)
    child.memes["joy"] += 1
    adult.memes["joy"] += 1


SETTING = LobbySetting(
    id="hotel_lobby",
    place="hotel lobby",
    detail="A tall vase, a soft rug, polished tiles, and a front desk made the lobby feel bright and busy.",
    calm="The place felt calmer when everyone helped.",
)

ITEMS = {
    "sand": TidyItem(
        id="sand",
        label="a little trail of sand by the door",
        mess="mess",
        weight=1,
        moral_task="help",
        tags={"curiosity", "moral_value"},
    ),
    "spills": TidyItem(
        id="spills",
        label="a small spill near the chair",
        mess="mess",
        weight=1,
        moral_task="help",
        tags={"curiosity", "moral_value"},
    ),
}

TOOLS = {
    "towel": HelperTool(
        id="towel",
        label="towel",
        phrase="a soft towel",
        helps_with={"help"},
        tags={"teamwork"},
    ),
    "bucket": HelperTool(
        id="bucket",
        label="bucket",
        phrase="a small bucket and a mop",
        helps_with={"help"},
        tags={"teamwork"},
    ),
}

PLANS = {
    "warm": OutcomePlan(
        id="warm",
        effort=1,
        teamwork=1,
        text="Soon the lobby was tidy again, and the polished tiles shone like a friendly smile.",
        after="The child looked proud, and the adult looked grateful.",
        tags={"heartwarming"},
    ),
    "brighter": OutcomePlan(
        id="brighter",
        effort=2,
        teamwork=1,
        text="After a little extra effort, the lobby looked even brighter than before.",
        after="They stood side by side, happy to have made things right together.",
        tags={"heartwarming"},
    ),
}

GIRL_NAMES = ["Maya", "Lina", "Tessa", "Nora", "Ivy"]
BOY_NAMES = ["Owen", "Noah", "Eli", "Theo", "Finn"]
TRAITS = ["curious", "gentle", "thoughtful", "kind"]


@dataclass
class StoryParams:
    item: str
    tool: str
    plan: str
    name: str
    gender: str
    adult: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for item_id, item in ITEMS.items():
        for tool_id, tool in TOOLS.items():
            for plan_id, plan in PLANS.items():
                if is_reasonable(item, tool, plan):
                    combos.append((item_id, tool_id, plan_id))
    return combos


def explain_rejection(item: TidyItem, tool: HelperTool, plan: OutcomePlan) -> str:
    if item.moral_task not in tool.helps_with:
        return f"(No story: {tool.label} does not fit the kind of help this lobby problem needs.)"
    if plan.effort < 1:
        return "(No story: the ending needs a visible effort beat.)"
    return "(No story: this combination is not reasonable.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A heartwarming hotel-lobby story world about curiosity, moral value, teamwork, and effort."
    )
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["receptionist", "parent", "uncle", "aunt"])
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
    if args.item and args.tool and args.plan:
        if not is_reasonable(ITEMS[args.item], TOOLS[args.tool], PLANS[args.plan]):
            raise StoryError(explain_rejection(ITEMS[args.item], TOOLS[args.tool], PLANS[args.plan]))
    combos = [c for c in valid_combos()
              if (args.item is None or c[0] == args.item)
              and (args.tool is None or c[1] == args.tool)
              and (args.plan is None or c[2] == args.plan)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    item, tool, plan = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    adult = args.adult or rng.choice(["receptionist", "parent", "uncle", "aunt"])
    trait = rng.choice(TRAITS)
    return StoryParams(item=item, tool=tool, plan=plan, name=name, gender=gender, adult=adult, trait=trait)


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    child = world.add(Entity(id=params.name, kind="character", type=params.gender, role="child", traits=[params.trait]))
    adult = world.add(Entity(id="Adult", kind="character", type=params.adult, role="helper"))
    lobby = world.add(Entity(id="lobby", kind="thing", type="place", label="the lobby"))
    item = ITEMS[params.item]
    tool = TOOLS[params.tool]
    plan = PLANS[params.plan]

    notice(world, child, adult, item)
    world.para()
    _make_mess(world, child, item)
    moral_turn(world, child, adult, item)
    team_up(world, child, adult, tool)
    propagate(world, narrate=False)
    world.para()
    finish(world, child, adult, item, plan)

    world.facts.update(
        child=child,
        adult=adult,
        lobby=lobby,
        item=item,
        tool=tool,
        plan=plan,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, item, tool = f["child"], f["item"], f["tool"]
    return [
        f'Write a heartwarming story set in a hotel lobby where {child.id} notices {item.label} and chooses to help. Include the word "effort".',
        f"Tell a short story about curiosity, moral value, and teamwork in a hotel lobby, where {child.id} and a grown-up work together with {tool.phrase}.",
        f"Write a gentle story in a hotel lobby where a curious child makes a good choice, and the ending shows their effort paid off.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, adult, item, tool, plan = f["child"], f["adult"], f["item"], f["tool"], f["plan"]
    qa = [
        (
            "Who is the story about?",
            f"It is about {child.id} in the hotel lobby and {adult.id}, who helped {child.id} after noticing something out of place.",
        ),
        (
            "Why did {0} stop and look around?".format(child.id),
            f"{child.id} was curious, so {child.pronoun()} wanted to know what {item.label} was doing there. That curiosity led {child.pronoun('object')} to help instead of walking away.",
        ),
        (
            "What did they do together?",
            f"They used {tool.phrase} and shared the effort to tidy the lobby. They took turns, which showed teamwork and a kind moral choice.",
        ),
    ]
    qa.append(
        (
            "How did the story end?",
            f"It ended with the lobby tidy and bright again. The child felt proud because effort and teamwork made the right thing happen.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a hotel lobby?", "A hotel lobby is the open area near the front desk where guests arrive, wait, and get help."),
        ("What does curiosity mean?", "Curiosity means wanting to know more about something. It often makes children ask questions and look closely."),
        ("What is teamwork?", "Teamwork means people help each other and work together toward the same goal."),
        ("What does effort mean?", "Effort is the work and energy you put into doing something well, especially when it is not easy."),
        ("What is a moral value?", "A moral value is a kind choice or belief that helps people decide to do what is right."),
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
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(item="sand", tool="towel", plan="warm", name="Maya", gender="girl", adult="receptionist", trait="curious"),
    StoryParams(item="spills", tool="bucket", plan="brighter", name="Owen", gender="boy", adult="parent", trait="thoughtful"),
]


def generate(params: StoryParams) -> StorySample:
    if params.item not in ITEMS or params.tool not in TOOLS or params.plan not in PLANS:
        raise StoryError("(Invalid params: unknown item, tool, or plan.)")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
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


ASP_RULES = r"""
helpful(C) :- child(C), curiosity(C), moral(C).
teamwork(C, A) :- child(C), adult(A), helping(C), helping(A).
tidy :- effort(E), E >= 1, teamwork_score(T), T >= 1.
outcome(warm) :- tidy.
outcome(brighter) :- tidy, extra_effort.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("setting", SETTING.id))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("task", iid, item.moral_task))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for h in sorted(tool.helps_with):
            lines.append(asp.fact("helps_with", tid, h))
    for pid, plan in PLANS.items():
        lines.append(asp.fact("plan", pid))
        lines.append(asp.fact("effort", pid, plan.effort))
        lines.append(asp.fact("teamwork_score", pid, plan.teamwork))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    from contextlib import redirect_stdout

    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH between ASP and Python valid_combos()")
    try:
        sample = generate(CURATED[0])
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample)
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    if rc == 0:
        print("OK: ASP parity and generate/emit smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming hotel-lobby story world.")
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["receptionist", "parent", "uncle", "aunt"])
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
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
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
