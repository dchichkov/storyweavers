#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/dismantle_tornado_uterus_humor_mystery_to_solve.py
====================================================================================

A tiny, self-contained storyworld about a child detective, a noisy tornado display,
and a puzzling clue hidden in a science project. The tone is mystery-first, but the
world keeps things child-friendly with a little humor and a simple problem-solving
turn.

Seed prompt
-----------
Write a story that includes the following words and narrative instruments.
Words: dismantle, tornado, uterus
Features: Humor, Mystery to Solve, Problem Solving
Style: Mystery
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
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    clue_spot: str
    has_display: bool = True


@dataclass
class MysteryObject:
    id: str
    label: str
    thing: str
    hides_clue: bool = False
    noisy: bool = False
    breakable: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class EventTool:
    id: str
    label: str
    verb: str
    power: int
    sense: int
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.objects: dict[str, MysteryObject] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add_entity(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_object(self, obj: MysteryObject) -> MysteryObject:
        self.objects[obj.id] = obj
        return obj

    def get_entity(self, eid: str) -> Entity:
        return self.entities[eid]

    def get_object(self, oid: str) -> MysteryObject:
        return self.objects[oid]

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
        clone.objects = copy.deepcopy(self.objects)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class StoryParams:
    setting: str
    detective: str
    detective_type: str
    helper: str
    helper_type: str
    parent: str
    object: str
    tool: str
    seed: Optional[int] = None


SETTINGS = {
    "science_fair": Setting(
        id="science_fair",
        place="the school science fair",
        mood="bright and busy",
        clue_spot="behind the tornado display",
        has_display=True,
    ),
    "library": Setting(
        id="library",
        place="the library corner",
        mood="quiet and echoey",
        clue_spot="under the display shelf",
        has_display=True,
    ),
    "classroom": Setting(
        id="classroom",
        place="the classroom",
        mood="tidy but curious",
        clue_spot="inside the project box",
        has_display=True,
    ),
}

OBJECTS = {
    "tornado_model": MysteryObject(
        id="tornado_model",
        label="cardboard tornado",
        thing="a tall cardboard tornado",
        hides_clue=True,
        noisy=True,
        breakable=True,
    ),
    "mystery_box": MysteryObject(
        id="mystery_box",
        label="mystery box",
        thing="a little mystery box",
        hides_clue=True,
        noisy=False,
        breakable=True,
    ),
    "spinning_top": MysteryObject(
        id="spinning_top",
        label="spinning top",
        thing="a shiny spinning top",
        hides_clue=False,
        noisy=True,
        breakable=False,
    ),
}

TOOLS = {
    "careful_scissors": EventTool(
        id="careful_scissors",
        label="careful scissors",
        verb="dismantle",
        power=3,
        sense=3,
        tags={"dismantle", "problem_solving"},
    ),
    "small_screwdriver": EventTool(
        id="small_screwdriver",
        label="a small screwdriver",
        verb="dismantle",
        power=4,
        sense=3,
        tags={"dismantle", "problem_solving"},
    ),
    "ruler_wedge": EventTool(
        id="ruler_wedge",
        label="a ruler",
        verb="pry apart",
        power=2,
        sense=2,
        tags={"problem_solving"},
    ),
}

GIRL_NAMES = ["Mina", "Luna", "Iris", "Nora", "Zoe", "Maya"]
BOY_NAMES = ["Theo", "Finn", "Eli", "Noah", "Max", "Owen"]
TRAITS = ["curious", "clever", "patient", "sensible", "funny"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for oid, obj in OBJECTS.items():
            if not obj.hides_clue:
                continue
            for tid, tool in TOOLS.items():
                if tool.sense >= 2:
                    combos.append((sid, oid, tid))
    return combos


def clue_for(obj: MysteryObject) -> str:
    return "the word uterus" if obj.id == "tornado_model" else "a folded note with the word uterus"


def mystery_risk(obj: MysteryObject) -> bool:
    return obj.hides_clue and obj.breakable


def use_tool(world: World, obj: MysteryObject, tool: EventTool) -> None:
    obj.meters["opened"] += 1
    if tool.power >= 3:
        obj.meters["opened_cleanly"] += 1
    world.say(
        f"{tool.label.capitalize()} helped {tool.verb} the {obj.label} enough to peek inside."
    )


def reveal_clue(world: World, obj: MysteryObject) -> None:
    obj.memes["solved"] += 1
    world.say(
        f"Inside, they found {clue_for(obj)} tucked behind a paper clip, which made the whole mystery feel suddenly very silly."
    )


def explain_setting(world: World, detective: Entity, helper: Entity) -> None:
    world.say(
        f"At {world.setting.place}, everything looked {world.setting.mood}. "
        f"{detective.id} and {helper.id} noticed {world.setting.clue_spot} right away."
    )


def introduce(world: World, detective: Entity, helper: Entity, obj: MysteryObject) -> None:
    detective.memes["curiosity"] += 1
    helper.memes["curiosity"] += 1
    world.say(
        f"{detective.id} was a {next((t for t in detective.traits if t), 'curious')} little {detective.type} who liked strange clues."
    )
    world.say(
        f"{helper.id} stayed close and said, \"That {obj.label} looks like it is trying very hard to be mysterious.\""
    )


def ask_question(world: World, detective: Entity, obj: MysteryObject) -> None:
    detective.memes["mystery"] += 1
    world.say(
        f"{detective.id} leaned in. \"Why does the {obj.label} keep humming like a tiny storm?\" {detective.pronoun()} asked."
    )


def predict(world: World, obj: MysteryObject, tool: EventTool) -> dict:
    sim = world.copy()
    use_tool(sim, sim.get_object(obj.id), tool)
    if sim.get_object(obj.id).hides_clue:
        reveal_clue(sim, sim.get_object(obj.id))
    return {"opened": sim.get_object(obj.id).meters["opened"] >= THRESHOLD, "solved": sim.get_object(obj.id).memes["solved"] >= THRESHOLD}


def solve_mystery(world: World, detective: Entity, helper: Entity, obj: MysteryObject, tool: EventTool) -> None:
    pred = predict(world, obj, tool)
    if pred["opened"]:
        world.say(
            f"{helper.id} guessed the trick: the storm sound came from loose cardboard, not real weather."
        )
    use_tool(world, obj, tool)
    world.say(
        f"Together they {tool.verb} the {obj.label} carefully, so the pieces would fit back together later."
    )
    reveal_clue(world, obj)
    detective.memes["joy"] += 1
    helper.memes["joy"] += 1


def ending(world: World, detective: Entity, helper: Entity, parent: Entity, obj: MysteryObject) -> None:
    world.say(
        f"{parent.label_word.capitalize()} laughed when they heard the answer. "
        f"\"So that was the mystery? A cardboard tornado and a clue about {clue_for(obj)}?\""
    )
    world.say(
        f"{detective.id} grinned, and the little team put the {obj.label} back together. "
        f"Then they marched off, still giggling, as if they had solved a very important case."
    )


def tell(setting: Setting, obj: MysteryObject, tool: EventTool,
         detective_name: str, detective_type: str,
         helper_name: str, helper_type: str,
         parent_type: str) -> World:
    world = World(setting)
    detective = world.add_entity(Entity(id=detective_name, kind="character", type=detective_type, role="detective", traits=["curious", "funny"]))
    helper = world.add_entity(Entity(id=helper_name, kind="character", type=helper_type, role="helper", traits=["patient"]))
    parent = world.add_entity(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    thing = world.add_object(copy.deepcopy(obj))

    introduce(world, detective, helper, thing)
    explain_setting(world, detective, helper)
    world.para()
    ask_question(world, detective, thing)
    world.say(f"{helper.id} pointed at the {thing.label}. \"We should {tool.verb} it and see what is hiding inside.\"")
    world.para()
    solve_mystery(world, detective, helper, thing, tool)
    world.para()
    ending(world, detective, helper, parent, thing)

    world.facts.update(
        detective=detective,
        helper=helper,
        parent=parent,
        object_cfg=thing,
        tool=tool,
        setting=setting,
        solved=thing.memes["solved"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    det = f["detective"]
    obj = f["object_cfg"]
    tool = f["tool"]
    return [
        f'Write a mystery story for a 3-to-5-year-old that includes the words "dismantle", "tornado", and "uterus".',
        f"Tell a funny mystery where {det.id} and a helper {tool.verb} a {obj.label} and find a clue hidden inside.",
        f"Write a problem-solving story set at {world.setting.place} with a strange tornado noise and a child detective who solves it."
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    det = f["detective"]
    helper = f["helper"]
    obj = f["object_cfg"]
    tool = f["tool"]
    qa = [
        QAItem(
            question="What was the mystery in the story?",
            answer=f"The mystery was why the {obj.label} sounded like a tornado and what was hidden inside it. They solved it by working carefully instead of guessing."
        ),
        QAItem(
            question="What did they do to solve the problem?",
            answer=f"They used {tool.label} to {tool.verb} the {obj.label} and opened it without breaking the important parts. That let them find the clue and keep going."
        ),
        QAItem(
            question="Why was the ending funny?",
            answer=f"The ending was funny because the big mystery turned out to be a tiny clue with the word uterus inside a cardboard project. It sounded dramatic at first, but it was really just a sneaky paper clue."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does dismantle mean?",
            answer="Dismantle means to take something apart carefully so you can see how it works or fix it."
        ),
        QAItem(
            question="What is a tornado?",
            answer="A tornado is a spinning column of air that can roar very loudly and move very fast."
        ),
        QAItem(
            question="What is a uterus?",
            answer="A uterus is a part inside the body. It is a real anatomy word, and the story uses it as part of a clue."
        ),
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
    for o in world.objects.values():
        bits = []
        meters = {k: v for k, v in o.meters.items() if v}
        memes = {k: v for k, v in o.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {o.id:8} (object ) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="science_fair", detective="Mina", detective_type="girl", helper="Theo", helper_type="boy", parent="mother", object="tornado_model", tool="careful_scissors"),
    StoryParams(setting="library", detective="Finn", detective_type="boy", helper="Luna", helper_type="girl", parent="father", object="mystery_box", tool="small_screwdriver"),
    StoryParams(setting="classroom", detective="Nora", detective_type="girl", helper="Max", helper_type="boy", parent="mother", object="tornado_model", tool="ruler_wedge"),
]


def explain_rejection(obj: MysteryObject, tool: EventTool) -> str:
    if not obj.hides_clue:
        return "(No story: that object does not hide a clue, so there is no mystery to solve.)"
    if tool.sense < 2:
        return "(No story: that tool is too clumsy for a careful mystery solution.)"
    return "(No story: this combination is not reasonable.)"


def valid_story(params: StoryParams) -> bool:
    return params.setting in SETTINGS and params.object in OBJECTS and params.tool in TOOLS


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.object and args.tool:
        obj = OBJECTS[args.object]
        tool = TOOLS[args.tool]
        if not (mystery_risk(obj) and tool.sense >= 2):
            raise StoryError(explain_rejection(obj, tool))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.object is None or c[1] == args.object)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, obj_id, tool_id = rng.choice(sorted(combos))
    gender = rng.choice(["girl", "boy"])
    detective = args.detective or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice([n for n in (BOY_NAMES + GIRL_NAMES) if n != detective])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        setting=setting,
        detective=detective,
        detective_type=gender,
        helper=helper,
        helper_type="boy" if gender == "girl" else "girl",
        parent=parent,
        object=obj_id,
        tool=tool_id,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.object not in OBJECTS:
        raise StoryError(f"Unknown object: {params.object}")
    if params.tool not in TOOLS:
        raise StoryError(f"Unknown tool: {params.tool}")
    world = tell(
        SETTINGS[params.setting],
        OBJECTS[params.object],
        TOOLS[params.tool],
        params.detective,
        params.detective_type,
        params.helper,
        params.helper_type,
        params.parent,
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A child-friendly mystery storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--detective")
    ap.add_argument("--helper")
    ap.add_argument("--parent", choices=["mother", "father"])
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


ASP_RULES = r"""
hides_clue(tornado_model).
hides_clue(mystery_box).
tool(careful_scissors).
tool(small_screwdriver).
tool(ruler_wedge).
sensible(T) :- tool(T), T != ruler_wedge.
valid(S,O,T) :- setting(S), hides_clue(O), sensible(T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if tool.sense >= 2:
            lines.append(asp.fact("sensible", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set != clingo_set:
        print("MISMATCH in valid_combos")
        return 1
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            print("MISMATCH: empty story")
            return 1
    except Exception as e:
        print(f"MISMATCH: generate() failed: {e}")
        return 1
    print(f"OK: verified {len(python_set)} combos and a story generation smoke test.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for c in combos:
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
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
            if sample.story not in seen:
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
