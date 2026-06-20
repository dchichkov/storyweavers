#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/joint_sharing_bravery_myth.py
==============================================================

A standalone storyworld about a small mythic act of sharing and bravery.

Premise:
- Two children hear a little river-god trapped in a cave temple.
- A hidden stone door can only open if the children work together at the joint in the gate.
- One child wants to keep the bright charm, but chooses to share it.
- Their brave sharing lets them face the dark, open the gate, and free the light.

This world is tuned for a mythic tone, child-facing prose, and a clear state-
driven turn: a shared object, a fearful threshold, a brave choice, and a final
image showing what changed.
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
    age: int = 0
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
    dark_name: str
    light_name: str
    myth_name: str
    threshold: str


@dataclass
class SharedThing:
    id: str
    label: str
    phrase: str
    glow: str
    plural: bool = False


@dataclass
class Risk:
    id: str
    label: str
    danger: str
    severity: int


@dataclass
class Aid:
    id: str
    label: str
    action: str
    power: int
    success: str
    fail: str


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
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_dread(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.memes["fear"] < THRESHOLD:
            continue
        sig = ("dread", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append("__dread__")
    return out


def _r_bond(world: World) -> list[str]:
    out: list[str] = []
    a = world.entities.get("child_a")
    b = world.entities.get("child_b")
    if not a or not b:
        return out
    if a.meters["sharing"] >= THRESHOLD and b.meters["sharing"] >= THRESHOLD:
        sig = ("bond",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        a.memes["courage"] += 1
        b.memes["courage"] += 1
        out.append("__bond__")
    return out


CAUSAL_RULES = [Rule("dread", "social", _r_dread), Rule("bond", "social", _r_bond)]


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


def predict_open(world: World, setting: Setting, risk: Risk) -> dict:
    sim = world.copy()
    sim.get("gate").meters["stuck"] += risk.severity
    return {
        "dark": sim.get("gate").meters["stuck"] >= THRESHOLD,
        "fear": sim.get("child_a").memes["fear"] + sim.get("child_b").memes["fear"],
    }


def valid_combo(setting: Setting, shared: SharedThing, risk: Risk) -> bool:
    return shared.label in {"lamp", "cloak", "bread"} and risk.severity >= 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for shid, sh in SHARED.items():
            for rid, rk in RISKS.items():
                if valid_combo(SETTINGS[sid], sh, rk):
                    combos.append((sid, shid, rid))
    return combos


def tell(setting: Setting, shared: SharedThing, risk: Risk, aid: Aid,
         child_a: str, child_b: str, parent: str = "mother", delay: int = 0) -> World:
    world = World()
    a = world.add(Entity("child_a", kind="character", type="girl", role="first", attrs={"name": child_a}))
    b = world.add(Entity("child_b", kind="character", type="boy", role="second", attrs={"name": child_b}))
    p = world.add(Entity("parent", kind="character", type=parent, role="parent", label="the elder"))
    gate = world.add(Entity("gate", label="the stone gate"))
    light = world.add(Entity("light", label=shared.label))
    spirit = world.add(Entity("spirit", label=setting.myth_name))

    a.memes["curiosity"] += 1
    b.memes["joy"] += 1

    world.say(
        f"Long ago, in {setting.place}, {child_a} and {child_b} came to {setting.myth_name}. "
        f"{child_a} held {shared.phrase}, and its {shared.glow} made the {setting.dark_name} shine."
    )
    world.say(
        f"They had heard a tale of {setting.threshold} hidden in the rocks, where a small {setting.myth_name} slept by a gate."
    )

    world.para()
    a.memes["greed"] += 1
    world.say(
        f"But the {shared.label} felt precious in {child_a}'s hands. {child_a} wanted to keep it close, "
        f"because the dark at the {setting.dark_name} looked deep and cold."
    )
    world.say(
        f"{child_b} bit {child_b if False else 'their'} lip and said, "
        f'"We can share it. The path is too dark for one pair of hands."'
    )
    a.memes["fear"] += 1
    b.memes["fear"] += 1
    predict_open(world, setting, risk)

    if delay:
        world.get("gate").meters["stuck"] += delay

    if a.memes["fear"] >= THRESHOLD or b.memes["fear"] >= THRESHOLD:
        world.say(
            f"The {setting.dark_name} was so black that even the stones seemed to listen."
        )

    a.meters["sharing"] += 1
    b.meters["sharing"] += 1
    propagate(world, narrate=False)

    world.para()
    world.say(
        f"At last, {child_a} opened {shared.phrase} and set it between them. "
        f"{child_b} took the other side, and together they walked to the {setting.threshold}, "
        f"where the {risk.label} waited."
    )
    world.say(
        f"Braver now, they used {aid.action}. {aid.success}."
    )

    world.get("gate").meters["stuck"] = max(0.0, world.get("gate").meters["stuck"] - aid.power)
    if world.get("gate").meters["stuck"] < THRESHOLD:
        world.get("spirit").meters["free"] += 1
        world.get("light").meters["glow"] += 1
        world.say(
            f"The stone gate gave a deep sigh and swung open. {setting.myth_name} rose up bright as dawn, "
            f"and the little {setting.myth_name} bowed to the brave children."
        )
        world.say(
            f"They left side by side, still sharing the {shared.label}, while the path behind them stayed full of gold light."
        )
        outcome = "open"
    else:
        world.say(
            f"But the gate stayed shut, and the dark held its breath. {aid.fail}."
        )
        outcome = "stuck"

    world.facts.update(
        setting=setting, shared=shared, risk=risk, aid=aid,
        child_a=a, child_b=b, parent=p, spirit=spirit, light=light, gate=gate,
        outcome=outcome, delay=delay
    )
    return world


SETTINGS = {
    "temple": Setting("temple", "the hill temple", "hall", "light", "river-saint", "joint"),
    "cave": Setting("cave", "the sea cave", "gloom", "light", "tide-guest", "joint"),
    "grove": Setting("grove", "the moon grove", "shadow", "glow", "leaf-queen", "joint"),
}

SHARED = {
    "lamp": SharedThing("lamp", "lamp", "a little lamp", "warm gold"),
    "cloak": SharedThing("cloak", "cloak", "a wool cloak", "soft fire"),
    "bread": SharedThing("bread", "bread", "a round loaf of bread", "fresh light"),
}

RISKS = {
    "door": Risk("door", "stone door", "a stone door with a stuck joint", 1),
    "gate": Risk("gate", "gate", "a gate with a stiff joint", 2),
    "arch": Risk("arch", "archway", "an archway with a cracked joint", 2),
}

AIDS = {
    "push": Aid("push", "shoulders together", "their shoulders together", 1,
                "Together they pressed at the stone until it shivered", "Their push was too small"),
    "pull": Aid("pull", "pulling rope", "the rope from the shrine", 2,
                "They pulled in rhythm, and the stone moved at once", "The rope slipped and the stone stayed"),
    "song": Aid("song", "a brave song", "a brave song", 1,
                "They sang to steady their hands, and the gate listened", "The song trembled and did not help"),
}

GIRL_NAMES = ["Mira", "Nia", "Sana", "Lena", "Iris", "Tala"]
BOY_NAMES = ["Oren", "Jai", "Kito", "Bram", "Niko", "Taro"]


@dataclass
class StoryParams:
    setting: str
    shared: str
    risk: str
    aid: str
    child_a: str
    child_b: str
    parent: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic storyworld of sharing and bravery.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--shared", choices=SHARED)
    ap.add_argument("--risk", choices=RISKS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--child-a")
    ap.add_argument("--child-b")
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
              and (args.shared is None or c[1] == args.shared)
              and (args.risk is None or c[2] == args.risk)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, shared, risk = rng.choice(sorted(combos))
    aid = args.aid or rng.choice(sorted(AIDS))
    child_a = args.child_a or rng.choice(GIRL_NAMES)
    child_b = args.child_b or rng.choice([n for n in BOY_NAMES if n != child_a])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, shared, risk, aid, child_a, child_b, parent)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a myth-like story for a small child that includes the word "joint" and shows sharing and bravery.',
        f"Tell a gentle myth about {f['child_a'].id} and {f['child_b'].id}, who share a {f['shared'].label} to face a stone gate with a joint.",
        f"Write a child-facing legend where a shared light helps two children open a dark gate and free a trapped spirit.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b, shared, risk, aid, setting = f["child_a"], f["child_b"], f["shared"], f["risk"], f["aid"], f["setting"]
    return [
        ("Who is the story about?",
         f"It is about {a.id} and {b.id}, two children who went to {setting.place}. They faced a stone {risk.label} and found a brave way to help."),
        ("What did they share?",
         f"They shared {shared.phrase}. Sharing let them hold the light together instead of keeping it for only one child."),
        ("Why did they need bravery?",
         f"The path was dark, and the stone {risk.label} had a stubborn joint. They had to be brave enough to go closer and work together."),
        ("How did they fix the problem?",
         f"They used {aid.action} and pushed at the gate until it moved. Their sharing and bravery made the door give way."),
        ("How did the story end?",
         f"The gate opened, the trapped spirit was free, and the children walked home side by side. The ending shows that sharing and bravery can turn fear into light."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a joint?",
         "A joint is a place where two parts meet and bend or move. A door can have a joint too, where the stone pieces join together."),
        ("What does it mean to share?",
         "To share means to let someone else use or hold something too. Sharing can help people work together and feel brave."),
        ("What is bravery?",
         "Bravery means doing something scary when it matters, even if your heart is trembling a little. Brave people keep going to help someone."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.label:
            bits.append(f"label={e.label}")
        out.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(out)


CURATED = [
    StoryParams("temple", "lamp", "door", "push", "Mira", "Oren", "mother"),
    StoryParams("cave", "cloak", "gate", "pull", "Nia", "Bram", "father"),
    StoryParams("grove", "bread", "arch", "song", "Tala", "Taro", "mother"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, sh, r) for s in SETTINGS for sh in SHARED for r in RISKS]


ASP_RULES = r"""
valid(S, H, R) :- setting(S), shared(H), risk(R).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for h in SHARED:
        lines.append(asp.fact("shared", h))
    for r in RISKS:
        lines.append(asp.fact("risk", r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
    else:
        print("MISMATCH in valid combos.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], SHARED[params.shared], RISKS[params.risk],
                 AIDS[params.aid], params.child_a, params.child_b, params.parent)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
