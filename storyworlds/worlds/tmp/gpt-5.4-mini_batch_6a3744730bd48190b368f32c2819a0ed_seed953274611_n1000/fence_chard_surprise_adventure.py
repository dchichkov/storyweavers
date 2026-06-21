#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/fence_chard_surprise_adventure.py
==================================================================

A small standalone storyworld for an adventure-style surprise tale about a child,
a fence, and chard. The world model keeps track of typed entities, physical
meters, and emotional memes. The adventure begins with a garden errand, turns on
a surprise at the fence, and resolves when the child uses a sensible tool to
help the garden and discovers the hidden gift.

The story is intentionally small and classical:
- a child explores a backyard garden path,
- they notice chard that needs gathering,
- a fence hides a surprise,
- a helpful reveal changes the mood,
- the ending proves what changed in the world.

This file follows the shared Storyweavers contract.
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
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
        return self.label or self.id


@dataclass
class Thing:
    id: str
    label: str
    kind: str = "thing"
    type: str = "thing"
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)


@dataclass
class Setting:
    id: str
    place: str
    scene: str
    gate: str
    path: str
    surprise_hint: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    use: str
    sense: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Reward:
    id: str
    label: str
    phrase: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    tool: str
    reward: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    seed: Optional[int] = None


SETTINGS = {
    "garden": Setting(
        id="garden",
        place="the back garden",
        scene="a little expedition through bean rows and sun-warmed dirt",
        gate="the old fence",
        path="the narrow path by the fence",
        surprise_hint="something waited beyond the fence slats",
        tags={"garden", "fence", "adventure"},
    ),
    "yard": Setting(
        id="yard",
        place="the yard",
        scene="a brave search beside tomato cages and climbing vines",
        gate="the leaning fence",
        path="the path along the fence",
        surprise_hint="something shiny hid near the boards",
        tags={"yard", "fence", "adventure"},
    ),
}

TOOLS = {
    "basket": Tool(
        id="basket",
        label="basket",
        phrase="a small woven basket",
        use="carry the chard without crushing it",
        sense=3,
        tags={"basket", "harvest"},
    ),
    "gloves": Tool(
        id="gloves",
        label="gloves",
        phrase="a pair of soft gloves",
        use="keep sticky leaves clean",
        sense=3,
        tags={"gloves", "harvest"},
    ),
    "ladder": Tool(
        id="ladder",
        label="ladder",
        phrase="a short step ladder",
        use="peek over the fence safely",
        sense=2,
        tags={"ladder", "fence"},
    ),
}

REWARDS = {
    "toy_boat": Reward(
        id="toy_boat",
        label="toy boat",
        phrase="a little blue toy boat",
        reveal="had been tucked into a nook behind the fence",
        tags={"surprise", "gift"},
    ),
    "note": Reward(
        id="note",
        label="note",
        phrase="a folded paper note",
        reveal="had been clipped to a nail on the fence",
        tags={"surprise", "gift"},
    ),
}

CHILD_NAMES = ["Mia", "Leo", "Ava", "Noah", "Zoe", "Eli", "Lily", "Finn"]
HELPER_NAMES = ["Mum", "Dad", "Nina", "Owen", "Tess", "Ben"]
GENDERS = ["girl", "boy"]


class World:
    def __init__(self, setting: Setting) -> None:
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
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    reward = world.entities.get("reward")
    if reward and reward.meters["revealed"] >= THRESHOLD and ("fear", "reward") not in world.fired:
        world.fired.add(("fear", "reward"))
        out.append("The surprise made the child gasp, then grin.")
        for ent in world.entities.values():
            if ent.kind == "character":
                ent.memes["wonder"] += 1
        if reward:
            reward.meters["wonder"] += 1
    return out


def _r_harvest(world: World) -> list[str]:
    out: list[str] = []
    chard = world.entities.get("chard")
    child = world.entities.get("child")
    tool = world.entities.get("tool")
    if not (chard and child and tool):
        return out
    if child.memes["help"] < THRESHOLD:
        return out
    if chard.meters["picked"] >= THRESHOLD:
        return out
    sig = ("harvest", chard.id, tool.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    chard.meters["picked"] += 1
    chard.meters["saved"] += 1
    out.append(f"{child.id} gathered the chard carefully.")
    return out


def _r_happy(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    helper = world.entities.get("helper")
    if not child or not helper:
        return out
    if child.memes["joy"] >= THRESHOLD and helper.memes["joy"] >= THRESHOLD and ("happy",) not in world.fired:
        world.fired.add(("happy",))
        out.append("The garden felt brighter after that.")
    return out


CAUSAL_RULES = [Rule("fear", _r_fear), Rule("harvest", _r_harvest), Rule("happy", _r_happy)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(tool: Tool, setting: Setting) -> bool:
    return "fence" in tool.tags or "harvest" in tool.tags or setting.id in {"garden", "yard"}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for tid in TOOLS:
            for rid in REWARDS:
                combos.append((sid, tid, rid))
    return combos


def create_world(setting: Setting, tool: Tool, reward: Reward, child_name: str, child_gender: str,
                 helper_name: str, helper_gender: str) -> World:
    w = World(setting)
    child = w.add(Entity(id="child", kind="character", type=child_gender, label=child_name, role="child"))
    helper = w.add(Entity(id="helper", kind="character", type=helper_gender, label=helper_name, role="helper"))
    chard = w.add(Entity(id="chard", kind="thing", type="plant", label="chard"))
    fence = w.add(Entity(id="fence", kind="thing", type="thing", label="fence"))
    reward_ent = w.add(Entity(id="reward", kind="thing", type="thing", label=reward.label))
    tool_ent = w.add(Entity(id="tool", kind="thing", type="tool", label=tool.label))

    child.memes["curiosity"] += 1
    helper.memes["care"] += 1

    w.say(f"{child.label} and {helper.label} set out through {setting.place}. {setting.scene.capitalize()}.")
    w.say(f"Near {setting.path}, they spotted the chard and the old fence, and {setting.surprise_hint}.")
    w.say(f'"Let us gather the chard," said {child.label}, "and look for what is hidden by the fence."')

    w.para()
    child.memes["hope"] += 1
    w.say(f"{helper.label} handed over {tool.phrase} so the leaves could be handled the right way.")
    w.say(f"{child.label} used it to {tool.use}, while {helper.label} watched the fence carefully.")

    reward_ent.meters["revealed"] += 1
    reward_ent.attrs["reveal"] = reward.reveal
    child.memes["surprise"] += 1
    helper.memes["surprise"] += 1
    w.para()
    w.say(f"Then, with a small creak from {setting.gate}, the surprise appeared: {reward.phrase} {reward.reveal}.")
    w.say(f"{child.label} laughed in delight, because the adventure had turned into a treasure hunt.")

    propagate(w, narrate=True)
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    w.para()
    w.say(f"In the end, the chard was safe in the basket, the fence kept its secret no longer, and {reward.phrase} rode home like a prize from a real adventure.")

    w.facts.update(
        child=child,
        helper=helper,
        chard=chard,
        fence=fence,
        reward=reward_ent,
        tool=tool_ent,
        setting=setting,
        tool_cfg=tool,
        reward_cfg=reward,
    )
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an adventure story for a young child that includes the words "fence" and "chard".',
        f"Tell a surprise adventure about {f['child'].label} and {f['helper'].label} in {f['setting'].place}, where the fence hides a gift.",
        f"Write a gentle quest story where chard is gathered carefully and a surprise is found behind a fence.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="Who went on the adventure?",
            answer=f"{f['child'].label} went with {f['helper'].label}, and they explored the garden together."
        ),
        QAItem(
            question="What did they do with the chard?",
            answer=f"They gathered the chard carefully with {f['tool_cfg'].phrase}, so the leaves stayed neat."
        ),
        QAItem(
            question="What surprise did they find?",
            answer=f"They found {f['reward_cfg'].phrase}, and it had been hidden near the fence as a cheerful surprise."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is chard?",
            answer="Chard is a leafy green plant people can pick and eat. It has big leaves and grows in a garden."
        ),
        QAItem(
            question="What is a fence for?",
            answer="A fence marks the edge of a place and helps keep a yard or garden in order. It can also hide a little surprise on the other side."
        ),
        QAItem(
            question="Why is a surprise fun in a story?",
            answer="A surprise gives the characters something unexpected to discover. It can turn an ordinary walk into an adventure."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="garden", tool="basket", reward="toy_boat", child_name="Mia", child_gender="girl", helper_name="Nina", helper_gender="girl"),
    StoryParams(setting="yard", tool="gloves", reward="note", child_name="Leo", child_gender="boy", helper_name="Owen", helper_gender="boy"),
    StoryParams(setting="garden", tool="ladder", reward="toy_boat", child_name="Ava", child_gender="girl", helper_name="Tess", helper_gender="girl"),
]


ASP_RULES = r"""
setting(S) :- setting_fact(S).
tool(T) :- tool_fact(T).
reward(R) :- reward_fact(R).
valid(S,T,R) :- setting(S), tool(T), reward(R).

show_surprise(R) :- reward(R).
show_harvest(T) :- tool(T), sense(T, S), S >= 2.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting_fact", sid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool_fact", tid))
        lines.append(asp.fact("sense", tid, t.sense))
    for rid in REWARDS:
        lines.append(asp.fact("reward_fact", rid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import storyworlds.asp as asp
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP parity failed.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE FAIL: {exc}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure surprise storyworld with fence and chard.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--reward", choices=REWARDS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=GENDERS)
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=GENDERS)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    tool = args.tool or rng.choice(list(TOOLS))
    reward = args.reward or rng.choice(list(REWARDS))
    if args.tool and args.tool not in TOOLS:
        raise StoryError("Unknown tool.")
    if not reasonableness_gate(TOOLS[tool], SETTINGS[setting]):
        raise StoryError("This tool does not make sense for the adventure.")
    child_gender = args.child_gender or rng.choice(GENDERS)
    helper_gender = args.helper_gender or rng.choice(GENDERS)
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    helper_name = args.helper_name or rng.choice([n for n in HELPER_NAMES if n != child_name])
    return StoryParams(
        setting=setting,
        tool=tool,
        reward=reward,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.tool not in TOOLS or params.reward not in REWARDS:
        raise StoryError("Invalid parameters.")
    world = create_world(
        SETTINGS[params.setting],
        TOOLS[params.tool],
        REWARDS[params.reward],
        params.child_name,
        params.child_gender,
        params.helper_name,
        params.helper_gender,
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
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
