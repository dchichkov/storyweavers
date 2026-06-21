#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/intimidate_motion_kindness_conflict_bedtime_story.py
====================================================================================

A small bedtime-story storyworld about a child, a moving toy, a scare, and a
kind resolution. The domain is intentionally tiny: one child is tempted to use a
moving bedtime toy to intimidate someone, conflict rises, kindness intervenes,
and the ending proves the room became calm again.

The required seed words are present in the domain through the motion toy and the
intimidation beat. The story quality aim is a gentle bedtime tale with a clear
premise, a turning point, and a soothing ending image.
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
class MotionToy:
    id: str
    label: str
    phrase: str
    motion: str
    glow: str
    speed: int
    safe: bool = True
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
class IntimidationTool:
    id: str
    label: str
    phrase: str
    effect: str
    strength: int
    safe: bool = False
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
class BedtimeSetting:
    id: str
    place: str
    hush: str
    corners: str
    listener: str
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
class StoryParams:
    setting: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    parent_name: str
    parent_gender: str
    toy: str
    tool: str
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


class World:
    def __init__(self, setting: BedtimeSetting) -> None:
        self.setting = setting
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
        return clone


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.memes["threat"] < THRESHOLD:
            continue
        sig = ("conflict", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["conflict"] += 1
        if "helper" in world.entities:
            world.get("helper").memes["worry"] += 1
        out.append("__conflict__")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    if "child" in world.entities and world.get("child").memes["calmed"] >= THRESHOLD:
        sig = ("kindness",)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append("__kindness__")
    return out


CAUSAL_RULES = [_r_conflict, _r_kindness]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(tool: IntimidationTool, toy: MotionToy) -> bool:
    return tool.strength > 0 and toy.safe and toy.motion


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for tid, toy in TOYS.items():
            for tool_id, tool in TOOLS.items():
                if reasonableness_gate(tool, toy):
                    combos.append((sid, tid, tool_id))
    return combos


def predict_motion(world: World, toy_id: str, tool_id: str) -> dict:
    sim = world.copy()
    toy = sim.get("toy")
    tool = sim.get("tool")
    toy.meters["moving"] += 1
    toy.memes["threat"] += tool.meters.get("threat", 1)
    propagate(sim, narrate=False)
    return {
        "conflict": sim.get("child").memes["conflict"] >= THRESHOLD,
        "calm": sim.get("child").memes["calm"] >= THRESHOLD,
    }


def tell(setting: BedtimeSetting, toy: MotionToy, tool: IntimidationTool,
         child_name: str = "Mila", child_gender: str = "girl",
         helper_name: str = "Pip", helper_gender: str = "boy",
         parent_name: str = "Mara", parent_gender: str = "mother") -> World:
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, role="child"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_gender, label=helper_name, role="helper"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_gender, label=parent_name, role="parent"))
    toy_ent = world.add(Entity(id="toy", type="toy", label=toy.label))
    tool_ent = world.add(Entity(id="tool", type="tool", label=tool.label))
    child.label = child_name
    helper.label = helper_name
    parent.label = parent_name

    world.say(f"In the quiet {setting.place}, {child_name} and {helper_name} listened to the hush of bedtime.")
    world.say(f"Near the pillow, {toy.phrase} gave a little {toy.motion}, soft as a secret moonbeam.")
    world.say(f"{helper_name} smiled, because the room felt cozy and still.")

    world.para()
    child.memes["curious"] += 1
    child.meters["moving"] += 1
    world.say(f"But {child_name} found {tool.phrase} and thought it would intimidate the room.")
    world.say(f'“{tool.effect},” {child_name} said, giving the toy a sharp motion just to look brave.')
    child.memes["threat"] += tool.strength
    helper.memes["worry"] += 1
    propagate(world, narrate=False)

    world.para()
    if child.memes["conflict"] >= THRESHOLD:
        world.say(f"{helper_name} took a small breath and held up a kind hand.")
        world.say(f'“We can use kindness instead,” {helper_name} whispered. “Bedtime is for gentle motion.”')
        child.memes["calmed"] += 1
        child.memes["threat"] = 0.0
        child.memes["kindness"] += 1
        parent.memes["pride"] += 1
        world.say(f"{parent_name} came to the doorway, not angry, only calm and warm.")
        world.say(f'{parent_name} said, “That was a big feeling. Let’s tuck the scary tool away.”')
        world.say(f"{child_name} placed {tool.label} on the shelf and gave the toy one last slow motion.")
        world.say(f"Then the room grew gentle again, and {toy.phrase} spun quietly beside the lamp.")
        world.say(f"{child_name}, {helper_name}, and {parent_name} all breathed more softly than before.")
    else:
        world.say(f"{child_name} stopped on their own and tucked the tool away before any trouble grew.")
        child.memes["kindness"] += 1
        child.memes["calmed"] += 1
        world.say(f"{toy.phrase} kept its peaceful motion, and the room stayed sweet and still.")

    world.facts.update(
        child=child, helper=helper, parent=parent, toy_cfg=toy, tool_cfg=tool,
        setting=setting, outcome="kindness" if child.memes["calmed"] >= THRESHOLD else "conflict"
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    toy: MotionToy = f["toy_cfg"]
    tool: IntimidationTool = f["tool_cfg"]
    setting: BedtimeSetting = f["setting"]
    return [
        f'Write a bedtime story that uses the words "{toy.id}" and "{tool.id}" and ends kindly.',
        f"Tell a calm story set in {setting.place} where a child tries to intimidate with motion, but kindness solves the conflict.",
        f"Write a gentle bedtime story about {toy.label} and {tool.label}, with conflict turning into kindness.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    parent: Entity = f["parent"]
    toy: MotionToy = f["toy_cfg"]
    tool: IntimidationTool = f["tool_cfg"]
    qa = [
        ("Who is the story about?", f"It is about {child.label} and {helper.label}, with {parent.label} nearby at bedtime."),
        ("What made the child try to intimidate the room?", f"{child.label} used {tool.label} and a sharp little motion because they wanted to look brave. That choice caused conflict instead of calm."),
        ("How was the problem solved?", f"{helper.label} answered with kindness and {parent.label} stayed calm. Then {child.label} put the scary tool away and let {toy.label} move gently again."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    toy: MotionToy = world.facts["toy_cfg"]
    tool: IntimidationTool = world.facts["tool_cfg"]
    out = []
    if "motion" in toy.tags:
        out.append(("What is motion?", "Motion means moving from one place to another, or changing position a little at a time. A toy can have motion when it spins, sways, or rolls."))
    if "kindness" in tool.tags or "kindness" in world.facts["setting"].tags:
        out.append(("What is kindness?", "Kindness is being gentle, helpful, and caring with other people. Kindness can make a scary moment feel safe again."))
    out.append(("What is conflict?", "Conflict is when people want different things or feelings clash. A calm voice and a gentle choice can help end it."))
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
        lines.append(f"  {e.id:8} ({e.type:8}) meters={meters} memes={memes}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


SETTINGS = {
    "nursery": BedtimeSetting(id="nursery", place="the nursery", hush="soft", corners="rounded", listener="lamp", tags={"kindness"}),
    "bedroom": BedtimeSetting(id="bedroom", place="the bedroom", hush="gentle", corners="sleepy", listener="nightlight", tags={"kindness"}),
    "attic": BedtimeSetting(id="attic", place="the attic playroom", hush="muffled", corners="quiet", listener="window", tags={"conflict"}),
}

TOYS = {
    "mobile": MotionToy(id="mobile", label="a moon mobile", phrase="a moon mobile", motion="slow sway", glow="silver", speed=1, tags={"motion"}),
    "top": MotionToy(id="top", label="a spinning top", phrase="a spinning top", motion="small spin", glow="bright", speed=2, tags={"motion"}),
    "windup": MotionToy(id="windup", label="a tiny windup mouse", phrase="a tiny windup mouse", motion="quick scuttle", glow="pale", speed=2, tags={"motion"}),
}

TOOLS = {
    "scowl": IntimidationTool(id="scowl", label="a scowl", phrase="a sharp scowl", effect="I can scare you", strength=2, tags={"conflict"}),
    "bang": IntimidationTool(id="bang", label="a loud clap", phrase="a loud clap", effect="Listen to me now", strength=3, tags={"conflict"}),
    "stare": IntimidationTool(id="stare", label="a hard stare", phrase="a hard stare", effect="Don't move", strength=1, tags={"conflict"}),
}

CURATED = [
    StoryParams(setting="nursery", child_name="Mila", child_gender="girl", helper_name="Pip", helper_gender="boy", parent_name="Mara", parent_gender="mother", toy="mobile", tool="scowl"),
    StoryParams(setting="bedroom", child_name="Noah", child_gender="boy", helper_name="Luna", helper_gender="girl", parent_name="Nia", parent_gender="mother", toy="top", tool="bang"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime story world about motion, intimidation, kindness, and conflict.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--toy", choices=TOYS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--child-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--parent-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--parent-gender", choices=["mother", "father", "woman", "man"])
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
    if args.tool and args.toy and not reasonableness_gate(TOOLS[args.tool], TOYS[args.toy]):
        raise StoryError("This tool and toy do not make a reasonable bedtime conflict.")
    setting = args.setting or rng.choice(list(SETTINGS))
    toy = args.toy or rng.choice(list(TOYS))
    tool = args.tool or rng.choice(list(TOOLS))
    if not reasonableness_gate(TOOLS[tool], TOYS[toy]):
        # retry with a valid pair
        valid = [(s, t, u) for (s, t, u) in valid_combos()]
        if not valid:
            raise StoryError("No reasonable bedtime stories are available.")
        setting, toy, tool = rng.choice(valid)
    return StoryParams(
        setting=setting,
        child_name=args.child_name or rng.choice(["Mila", "Noah", "Aria", "Theo", "Luna", "Finn"]),
        child_gender=args.child_gender or rng.choice(["girl", "boy"]),
        helper_name=args.helper_name or rng.choice(["Pip", "Zoe", "Milo", "June"]),
        helper_gender=args.helper_gender or rng.choice(["girl", "boy"]),
        parent_name=args.parent_name or rng.choice(["Mara", "Nia", "Evan", "Asha"]),
        parent_gender=args.parent_gender or rng.choice(["mother", "father", "woman", "man"]),
        toy=toy,
        tool=tool,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.toy not in TOYS or params.tool not in TOOLS:
        raise StoryError("Invalid StoryParams values.")
    if not reasonableness_gate(TOOLS[params.tool], TOYS[params.toy]):
        raise StoryError("This story combination is not reasonable.")
    world = tell(
        SETTINGS[params.setting],
        TOYS[params.toy],
        TOOLS[params.tool],
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        parent_name=params.parent_name,
        parent_gender=params.parent_gender,
    )
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


ASP_RULES = r"""
reasonable(S,T,U) :- setting(S), toy(T), tool(U), toy_safe(T), tool_strength(U,N), N > 0.
"""
def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for t in TOYS:
        lines.append(asp.fact("toy", t))
        lines.append(asp.fact("toy_safe", t))
    for u, tool in TOOLS.items():
        lines.append(asp.fact("tool", u))
        lines.append(asp.fact("tool_strength", u, tool.strength))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("", "#show reasonable/3."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python valid_combos differ.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, toy=None, tool=None, child_name=None, helper_name=None, parent_name=None, child_gender=None, helper_gender=None, parent_gender=None), random.Random(777)))
        _ = sample.story
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generation smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"MISMATCH: generation smoke test failed: {e}")
    return rc


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, t, u) for (s, t, u) in [(s, t, u) for s in SETTINGS for t in TOYS for u in TOOLS] if reasonableness_gate(TOOLS[u], TOYS[t])]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show reasonable/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(" ".join(map(str, row)) for row in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
