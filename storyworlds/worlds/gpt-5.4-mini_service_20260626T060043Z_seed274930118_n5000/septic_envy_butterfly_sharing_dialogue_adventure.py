#!/usr/bin/env python3
"""
storyworlds/worlds/septic_envy_butterfly_sharing_dialogue_adventure.py
=======================================================================

A standalone story world for a small adventure about a butterfly, a bit of envy,
and a sharing-and-dialogue resolution near a septic tank cover.

Premise:
- Two young adventurers visit a garden trail beside a farmhouse yard.
- A bright butterfly becomes the day's treasure.
- One child feels envy when the other gets the net first.
- A careful parent points out the septic lid and keeps the children on the safe
  path.
- The children talk it out, share the net, and follow the butterfly together.

The world model tracks physical meters and emotional memes:
- meters: "danger", "delight", "butterfly_interest", "dust"
- memes: "envy", "joy", "frustration", "trust", "connection"

The prose is authored from the simulated state. It should read as a complete
TinyStories-style adventure with a clear turn and a satisfying ending image.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    wear: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ["danger", "delight", "butterfly_interest", "dust", "care"]:
            self.meters.setdefault(key, 0.0)
        for key in ["envy", "joy", "frustration", "trust", "connection"]:
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    hazardous: bool = False
    safe_path: str = "the stone path"


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    delight: str
    risk_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ObjectCfg:
    label: str
    phrase: str
    type: str
    plural: bool = False


@dataclass
class ToolCfg:
    id: str
    label: str
    phrase: str
    shareable: bool = True
    helps: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        return clone


@dataclass
class StoryParams:
    place: str
    activity: str
    object: str
    tool: str
    name_a: str
    name_b: str
    gender_a: str
    gender_b: str
    parent: str
    trait_a: str
    trait_b: str
    seed: Optional[int] = None


SETTINGS = {
    "backyard": Setting(place="the backyard", hazardous=True, safe_path="the stone path"),
    "garden": Setting(place="the garden", hazardous=False, safe_path="the gravel path"),
    "orchard": Setting(place="the orchard", hazardous=False, safe_path="the lane"),
}

ACTIVITIES = {
    "butterfly": Activity(
        id="butterfly",
        verb="follow the butterfly",
        gerund="following the butterfly",
        rush="dash after the butterfly",
        delight="the yellow wings flashing in the sun",
        risk_word="danger",
        tags={"butterfly", "adventure"},
    ),
    "explore": Activity(
        id="explore",
        verb="explore the trail",
        gerund="exploring the trail",
        rush="run toward the trail",
        delight="the path turning through the trees",
        risk_word="dust",
        tags={"adventure"},
    ),
}

OBJECTS = {
    "net": ObjectCfg(label="butterfly net", phrase="a light butterfly net", type="net"),
    "jar": ObjectCfg(label="flower jar", phrase="a small flower jar", type="jar"),
}

TOOLS = {
    "guide": ToolCfg(id="guide", label="field guide", phrase="a tiny field guide", helps={"butterfly", "adventure"}),
    "snack": ToolCfg(id="snack", label="trail snack", phrase="a shared trail snack", helps={"adventure"}),
}

GIRL_NAMES = ["Lena", "Maya", "Iris", "Nora", "Zoe", "Ava"]
BOY_NAMES = ["Theo", "Finn", "Eli", "Noah", "Milo", "Jack"]
TRAITS = ["curious", "brave", "lively", "gentle", "spirited", "playful"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id, act in ACTIVITIES.items():
            for obj_id in OBJECTS:
                if act_id == "butterfly" and obj_id != "net":
                    continue
                for tool_id in TOOLS:
                    combos.append((place, act_id, obj_id, tool_id))
    return combos


def prize_at_risk(activity: Activity, setting: Setting, obj: ObjectCfg) -> bool:
    return activity.id == "butterfly" and obj.label == "butterfly net" and setting.hazardous


def select_share_fix(activity: Activity, obj: ObjectCfg, tool: ToolCfg) -> bool:
    return obj.label == "butterfly net" and "butterfly" in tool.helps


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: septic caution, envy, butterfly chase, sharing, and dialogue."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--object", dest="object_", choices=OBJECTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender-a", choices=["girl", "boy"])
    ap.add_argument("--gender-b", choices=["girl", "boy"])
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait-a", choices=TRAITS)
    ap.add_argument("--trait-b", choices=TRAITS)
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


def explain_rejection() -> str:
    return "(No story: this adventure needs the butterfly net and a sharing tool that can honestly resolve envy.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.object_:
        act = ACTIVITIES[args.activity]
        obj = OBJECTS[args.object_]
        if not prize_at_risk(act, SETTINGS[args.place] if args.place else SETTINGS["backyard"], obj):
            raise StoryError(explain_rejection())
        if not select_share_fix(act, obj, TOOLS[args.tool] if args.tool else TOOLS["guide"]):
            raise StoryError(explain_rejection())

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.object_ is None or c[2] == args.object_)
              and (args.tool is None or c[3] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, obj, tool = rng.choice(sorted(combos))
    gender_a = args.gender_a or rng.choice(["girl", "boy"])
    gender_b = args.gender_b or ("boy" if gender_a == "girl" else "girl")
    name_a = args.name_a or rng.choice(GIRL_NAMES if gender_a == "girl" else BOY_NAMES)
    name_b = args.name_b or rng.choice([n for n in (GIRL_NAMES if gender_b == "girl" else BOY_NAMES) if n != name_a])
    return StoryParams(
        place=place,
        activity=activity,
        object=obj,
        tool=tool,
        name_a=name_a,
        name_b=name_b,
        gender_a=gender_a,
        gender_b=gender_b,
        parent=args.parent or rng.choice(["mother", "father"]),
        trait_a=args.trait_a or rng.choice(TRAITS),
        trait_b=args.trait_b or rng.choice([t for t in TRAITS if t != (args.trait_a or "")]),
    )


def _story_start(world: World, a: Entity, b: Entity, parent: Entity, obj: Entity, tool: Entity, act: Activity) -> None:
    world.say(f"{a.id} and {b.id} were little adventurers at {world.setting.place}, where the {act.id} trail curled beside a quiet septic lid.")
    world.say(f"{a.id} had a {tool.label}, and {b.id} had the best eyes for spotting bright wings.")
    obj.held_by = a.id
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(f"They loved {act.gerund}, because {act.delight} made the whole day feel like a treasure hunt.")


def _warn_about_septic(world: World, parent: Entity, a: Entity, b: Entity) -> None:
    parent.memes["trust"] += 1
    world.say(f"Before they started, {parent.id} pointed to the septic cover and said, \"Stay on {world.setting.safe_path}; we never go near that lid.\"")
    a.meters["danger"] += 1
    b.meters["danger"] += 1


def _envy_turn(world: World, a: Entity, b: Entity, obj: Entity, tool: Entity) -> None:
    a.memes["envy"] += 1
    a.memes["frustration"] += 1
    world.say(f"When {b.id} reached for the {obj.label}, {a.id} felt a prickly envy.")
    world.say(f"\"I want the {tool.label} first,\" {a.id} muttered, hugging {tool.label if False else 'the net'} closer.")
    if obj.held_by == a.id:
        obj.held_by = None


def _dialogue_and_share(world: World, a: Entity, b: Entity, parent: Entity, obj: Entity, tool: Entity, act: Activity) -> None:
    a.memes["frustration"] += 0.5
    b.memes["connection"] += 1
    a.memes["connection"] += 1
    world.say(f"{b.id} looked at {a.id} and said, \"We can share it. You can hold one side, and I can hold the other.\"")
    world.say(f"{parent.id} smiled and added, \"That is how adventures work best: two voices, one plan.\"")
    world.say(f"{a.id} took a breath, nodded, and said, \"Okay. I was jealous, but I do want to do this together.\"")
    a.memes["envy"] = 0
    a.memes["trust"] += 1
    b.memes["trust"] += 1
    obj.held_by = a.id
    tool.held_by = b.id
    world.say(f"So they shared the {obj.label} and the {tool.label}, walking side by side on {world.setting.safe_path}.")


def _butterfly_finish(world: World, a: Entity, b: Entity, obj: Entity, tool: Entity, act: Activity) -> None:
    a.meters["butterfly_interest"] += 1
    b.meters["butterfly_interest"] += 1
    a.meters["delight"] += 1
    b.meters["delight"] += 1
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(f"A gold butterfly floated up from the clover, paused on a leaf, and flicked its wings like a tiny fan.")
    world.say(f"This time {a.id} and {b.id} did not rush. They leaned close, shared the {tool.label}, and watched the butterfly drift away safely.")
    world.say(f"At the end, the septic lid stayed untouched, the net stayed whole, and both children were laughing as if the garden had handed them a secret.")


def tell(setting: Setting, activity: Activity, obj_cfg: ObjectCfg, tool_cfg: ToolCfg,
         name_a: str, gender_a: str, name_b: str, gender_b: str, parent_type: str,
         trait_a: str, trait_b: str) -> World:
    world = World(setting)
    a = world.add(Entity(id=name_a, kind="character", type=gender_a, label=name_a))
    b = world.add(Entity(id=name_b, kind="character", type=gender_b, label=name_b))
    parent = world.add(Entity(id=parent_type, kind="character", type=parent_type, label=parent_type))
    obj = world.add(Entity(id="object", type=obj_cfg.type, label=obj_cfg.label, phrase=obj_cfg.phrase, owner=a.id))
    tool = world.add(Entity(id="tool", type="tool", label=tool_cfg.label, phrase=tool_cfg.phrase, owner=a.id, plural=False))

    a.meters["care"] += 1
    b.meters["care"] += 1
    a.memes["joy"] += 1
    b.memes["joy"] += 1

    _story_start(world, a, b, parent, obj, tool, activity)
    world.para()
    _warn_about_septic(world, parent, a, b)
    world.say(f"{a.id} wanted to {activity.verb}, but the shiny butterfly kept circling just beyond the safe stones.")
    world.say(f"{b.id} started to reach for the {tool.label}, and that was when envy pinched {a.id}'s chest.")
    _envy_turn(world, a, b, obj, tool)
    world.para()
    _dialogue_and_share(world, a, b, parent, obj, tool, activity)
    _butterfly_finish(world, a, b, obj, tool, activity)

    world.facts.update(
        a=a, b=b, parent=parent, obj=obj, tool=tool, activity=activity, setting=setting,
        shared=True, envy_fixed=True, septic=True
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        OBJECTS[params.object],
        TOOLS[params.tool],
        params.name_a,
        params.gender_a,
        params.name_b,
        params.gender_b,
        params.parent,
        params.trait_a,
        params.trait_b,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a, b, act, obj, tool = f["a"], f["b"], f["activity"], f["obj"], f["tool"]
    return [
        f"Write a short adventure story for a child named {a.id} who feels envy during a butterfly hunt.",
        f"Tell a gentle dialogue-driven story where {a.id} and {b.id} share the {obj.label} and the {tool.label}.",
        f"Write a story that includes a septic cover, a butterfly, sharing, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b, parent, act, obj, tool = f["a"], f["b"], f["parent"], f["activity"], f["obj"], f["tool"]
    return [
        QAItem(
            question=f"Why did {a.id} feel bad when {b.id} reached for the {tool.label}?",
            answer=f"{a.id} felt envy because {b.id} was about to take the {tool.label}, and {a.id} wanted to be the first one ready for the butterfly adventure.",
        ),
        QAItem(
            question=f"What did {parent.id} warn the children about near {world.setting.place}?",
            answer=f"{parent.id} warned them to stay on {world.setting.safe_path} and keep away from the septic lid.",
        ),
        QAItem(
            question=f"How did {a.id} and {b.id} solve the problem?",
            answer=f"They talked it out, shared the {obj.label} and the {tool.label}, and chose to watch the butterfly together instead of arguing.",
        ),
        QAItem(
            question=f"What showed that the adventure ended well?",
            answer=f"The butterfly flew safely away, the septic lid was never touched, and both children were laughing together at the end.",
        ),
    ]


KNOWLEDGE = {
    "butterfly": QAItem(
        question="What is a butterfly?",
        answer="A butterfly is an insect with soft wings that starts life as a caterpillar and later changes into a winged adult.",
    ),
    "septic": QAItem(
        question="What is a septic lid?",
        answer="A septic lid covers an underground tank, so people keep it closed and stay away from it.",
    ),
    "share": QAItem(
        question="What does it mean to share?",
        answer="To share means to let other people use part of something or enjoy it with you.",
    ),
    "dialogue": QAItem(
        question="What is dialogue in a story?",
        answer="Dialogue is when characters speak to each other, so we can hear their words directly.",
    ),
    "envy": QAItem(
        question="What is envy?",
        answer="Envy is a feeling you get when you really want something that someone else has.",
    ),
    "adventure": QAItem(
        question="What makes a story feel like an adventure?",
        answer="An adventure story usually has a journey, a goal, a little danger or surprise, and a brave choice at the end.",
    ),
}


def world_qa(world: World) -> list[QAItem]:
    return [
        KNOWLEDGE["butterfly"],
        KNOWLEDGE["septic"],
        KNOWLEDGE["share"],
        KNOWLEDGE["dialogue"],
        KNOWLEDGE["envy"],
        KNOWLEDGE["adventure"],
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
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="backyard",
        activity="butterfly",
        object="net",
        tool="guide",
        name_a="Lena",
        name_b="Theo",
        gender_a="girl",
        gender_b="boy",
        parent="mother",
        trait_a="curious",
        trait_b="brave",
    ),
    StoryParams(
        place="garden",
        activity="butterfly",
        object="net",
        tool="guide",
        name_a="Maya",
        name_b="Finn",
        gender_a="girl",
        gender_b="boy",
        parent="father",
        trait_a="playful",
        trait_b="gentle",
    ),
]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.hazardous:
            lines.append(asp.fact("hazardous", pid))
        lines.append(asp.fact("safe_path", pid, s.safe_path))
        for a in ACTIVITIES:
            lines.append(asp.fact("affords", pid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("object_type", oid, o.type))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for help_word in sorted(t.helps):
            lines.append(asp.fact("helps", tid, help_word))
    return "\n".join(lines)


ASP_RULES = r"""
% A butterfly story is reasonable when the setting is adventurous and the
% chosen tool can honestly support sharing.
needs_share(A, O) :- activity(A), object(O), A = butterfly, O = net.
can_fix(A, O, T) :- needs_share(A, O), tool(T), helps(T, butterfly).

valid_story(P, A, O, T) :- setting(P), activity(A), object(O), tool(T), affords(P, A), can_fix(A, O, T).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for combo in combos:
            print("  ", combo)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name_a} and {p.name_b}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
