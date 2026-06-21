#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/reward_filter_transformation_suspense_whodunit.py
==================================================================================

A tiny whodunit storyworld with a reward, a filter, a transformation, and a
suspenseful reveal.

Premise:
- A small crew is in a sealed observatory after a prize goes missing.
- A filter device and a transforming lens alter what each witness can see.
- Clues are gathered under suspense.
- The ending reveals who moved the reward and why.

The world is intentionally classical and small: a few typed entities, physical
meters, emotional memes, a forward causal simulation, QA grounded in the world
state, and an ASP twin for a simple reasonableness gate.
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
from typing import Optional

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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Room:
    id: str
    label: str
    sealed: bool = True
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class Witness:
    id: str
    type: str
    label: str
    cautious: bool
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "girl" or self.type == "woman":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type == "boy" or self.type == "man":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class SuspenseDevice:
    id: str
    label: str
    reveal: str
    can_transform: bool
    can_filter: bool
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class Reward:
    id: str
    label: str
    hidden_place: str
    moved_place: str
    is_movable: bool = True
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class StoryParams:
    setting: str
    culprit: str
    witness1: str
    witness2: str
    device: str
    reward: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
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
        clone.facts = dict(self.facts)
        return clone


def _rule_suspense(world: World) -> list[str]:
    out: list[str] = []
    clue = world.get("clue")
    if clue.meters["uncertain"] < THRESHOLD:
        return out
    sig = ("suspense",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for wid in ("witness1", "witness2"):
        world.get(wid).memes["unease"] += 1
    world.get("room").meters["tense"] += 1
    out.append("__suspense__")
    return out


def _rule_transform(world: World) -> list[str]:
    out: list[str] = []
    device = world.get("device")
    if device.meters["switched"] < THRESHOLD or device.meters["focused"] < THRESHOLD:
        return out
    sig = ("transform",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("clue").meters["seen"] += 1
    world.get("clue").meters["shifted"] += 1
    out.append("__transform__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_rule_suspense, _rule_transform):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "observatory": {
        "label": "the old observatory",
        "detail": "The dome was shut tight, and moonlight lay in a pale stripe across the floor.",
        "shadow": "the dark corner behind the telescope",
    },
    "museum": {
        "label": "the small museum archive",
        "detail": "The glass cases stood still, and every footstep seemed to echo too long.",
        "shadow": "the shelf behind the curtain",
    },
}

WITNESSES = {
    "girl": ["Mina", "Nell", "Tia"],
    "boy": ["Jory", "Pip", "Ren"],
}

DEVICES = {
    "filter": SuspenseDevice(id="filter", label="a glass filter", reveal="changed the light and showed a hidden mark", can_transform=True, can_filter=True),
    "lens": SuspenseDevice(id="lens", label="a turning lens", reveal="shifted the view and made the clue appear", can_transform=True, can_filter=False),
    "screen": SuspenseDevice(id="screen", label="a paper filter screen", reveal="softened the glare and revealed a faint trail", can_transform=False, can_filter=True),
}

REWARDS = {
    "medal": Reward(id="medal", label="the silver reward medal", hidden_place="under the table", moved_place="inside a velvet box"),
    "key": Reward(id="key", label="the brass reward key", hidden_place="behind a book", moved_place="inside a map case"),
    "star": Reward(id="star", label="the prize star pin", hidden_place="in the drawer", moved_place="under a cloth"),
}

CURSED = {"broken", "too_heavy", "already_found"}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for device in DEVICES:
            for reward in REWARDS:
                combos.append((setting, device, reward))
    return combos


def clue_at_risk(setting: str, reward: str) -> bool:
    return setting in SETTINGS and reward in REWARDS


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld: reward, filter, transformation, suspense.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--device", choices=DEVICES)
    ap.add_argument("--reward", choices=REWARDS)
    ap.add_argument("--culprit")
    ap.add_argument("--witness1")
    ap.add_argument("--witness2")
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
    if args.setting or args.device or args.reward:
        combos = [c for c in combos
                  if (args.setting is None or c[0] == args.setting)
                  and (args.device is None or c[1] == args.device)
                  and (args.reward is None or c[2] == args.reward)]
    if not combos:
        raise StoryError("No valid story matches those options.")
    setting, device, reward = rng.choice(sorted(combos))
    witnesses = rng.sample(WITNESSES["girl"] + WITNESSES["boy"], 2)
    culprit = args.culprit or rng.choice(["Iris", "Noel", "Ada", "Bram"])
    w1 = args.witness1 or witnesses[0]
    w2 = args.witness2 or witnesses[1]
    return StoryParams(setting=setting, culprit=culprit, witness1=w1, witness2=w2, device=device, reward=reward)


def _setup_world(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    device = DEVICES[params.device]
    reward = REWARDS[params.reward]
    room = world.add(Room(id="room", label=setting["label"]))
    clue = world.add(Entity(id="clue", kind="thing", type="clue", label=reward.label))
    culprit = world.add(Entity(id="culprit", kind="character", type="person", label=params.culprit, role="suspect"))
    w1 = world.add(Witness(id="witness1", type="girl" if params.witness1 in WITNESSES["girl"] else "boy", label=params.witness1, cautious=True))
    w2 = world.add(Witness(id="witness2", type="girl" if params.witness2 in WITNESSES["girl"] else "boy", label=params.witness2, cautious=True))
    dev = world.add(device)
    rew = world.add(reward)
    world.facts.update(setting=params.setting, device=params.device, reward=params.reward, culprit=culprit.label, witness1=w1.label, witness2=w2.label)
    world.facts["room_detail"] = setting["detail"]
    world.facts["shadow"] = setting["shadow"]
    world.facts["device_label"] = device.label
    world.facts["reward_label"] = reward.label
    return world


def tell(world: World, params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    device: SuspenseDevice = world.get("device")
    reward: Reward = world.get("reward")
    culprit: Entity = world.get("culprit")
    w1: Witness = world.get("witness1")
    w2: Witness = world.get("witness2")
    clue: Entity = world.get("clue")

    culprit.memes["nervous"] += 1
    w1.memes["suspense"] += 1
    w2.memes["suspense"] += 1
    clue.meters["uncertain"] += 1

    world.say(f"It was a quiet night in {setting['label']}. {setting['detail']}")
    world.say(f"{w1.label} and {w2.label} were there when the reward went missing: {reward.label} had vanished from {reward.hidden_place}.")
    world.say(f"{w1.label} held up {device.label}, but the light only deepened the shadows near {setting['shadow']}.")
    world.para()
    world.say(f"Then {params.culprit} tried to act innocent. \"I only wanted to help,\" {culprit.pronoun()} said.")
    world.say(f"But {w2.label} noticed something small: the filter could change what the eye could trust.")
    clue.meters["uncertain"] += 1
    if device.can_filter:
        device.meters["switched"] += 1
    if device.can_transform:
        device.meters["focused"] += 1
    propagate(world, narrate=False)
    world.para()
    if device.can_transform and device.can_filter:
        world.say(f"{w1.label} turned the filter slowly until the beam changed. Suddenly the mark on the clue shifted into view.")
    elif device.can_filter:
        world.say(f"{w1.label} slid the filter screen over the lamp. The glare softened, and a faint trail appeared at last.")
    else:
        world.say(f"{w1.label} tilted the lens, and the line of light moved just enough to expose a hidden smudge.")
    world.say(f"The truth came out in pieces: {params.culprit} had moved the reward into {reward.moved_place} so nobody would notice the joke.")
    world.para()
    culprit.meters["caught"] += 1
    culprit.memes["shame"] += 1
    w1.memes["relief"] += 1
    w2.memes["relief"] += 1
    clue.meters["seen"] += 1
    world.say(f"In the end, the room was still and clear again. The reward returned, and the case was solved before dawn.")
    world.facts["solved"] = True
    world.facts["device_can_filter"] = device.can_filter
    world.facts["device_can_transform"] = device.can_transform
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a suspenseful whodunit for a young child that includes the words "reward" and "filter" and ends with the mystery solved in {f["setting"]}.',
        f"Tell a small detective story where a filter helps two witnesses see what happened to the reward, and the culprit is revealed.",
        "Write a calm whodunit with a transformation in the clue-finding tool, a tense middle, and a clear ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    return [
        ("What was missing?",
         f"The reward was missing, and everyone noticed because the room felt wrong without it. That missing place is what made the mystery begin."),
        ("How did the witnesses solve the mystery?",
         f"They used a filter and changed the way the light reached the clue. That transformation made a hidden mark and trail show up clearly."),
        ("Who moved the reward?",
         f"{f['culprit']} moved it into {world.get('reward').moved_place} to hide it. The witnesses pieced together the clues and caught the trick."),
        ("How did the story end?",
         "The reward came back, the room calmed down, and the mystery was solved before dawn. Nothing stayed hidden once the filter helped them see better."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does a filter do?",
         "A filter changes what passes through it, like light or liquid. That can make something easier to see or cleaner to use."),
        ("What is suspense in a story?",
         "Suspense is the feeling that something important is about to be revealed. It keeps you wondering until the truth appears."),
        ("What is a whodunit?",
         "A whodunit is a mystery story where the reader tries to figure out who caused the problem. The answer is revealed at the end."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts ==", *[f"- {p}" for p in sample.prompts], "", "== story QA =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
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
        if getattr(e, "role", ""):
            bits.append(f"role={e.role}")
        if getattr(e, "label", ""):
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,D,R) :- setting(S), device(D), reward(R).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for d in DEVICES:
        lines.append(asp.fact("device", d))
    for r in REWARDS:
        lines.append(asp.fact("reward", r))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3.", ""))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: ASP gate matches valid_combos() ({len(a)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def explain_rejection() -> str:
    return "(No story: the requested pieces don't fit this mystery world.)"


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.device not in DEVICES or params.reward not in REWARDS:
        raise StoryError(explain_rejection())
    world = tell(_setup_world(params), params)
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


CURATED = [
    StoryParams(setting="observatory", culprit="Iris", witness1="Mina", witness2="Jory", device="filter", reward="medal"),
    StoryParams(setting="museum", culprit="Noel", witness1="Tia", witness2="Ren", device="lens", reward="key"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.setting or args.device or args.reward:
        combos = [c for c in combos if (args.setting is None or c[0] == args.setting)
                  and (args.device is None or c[1] == args.device)
                  and (args.reward is None or c[2] == args.reward)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    setting, device, reward = rng.choice(sorted(combos))
    names = rng.sample(["Mina", "Jory", "Tia", "Ren", "Iris", "Noel", "Ada", "Bram"], 2)
    return StoryParams(
        setting=setting,
        culprit=args.culprit or rng.choice(["Iris", "Noel", "Ada", "Bram"]),
        witness1=args.witness1 or names[0],
        witness2=args.witness2 or names[1],
        device=device,
        reward=reward,
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for s, d, r in asp_valid_combos():
            print(f"{s} {d} {r}")
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
