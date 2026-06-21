#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/jello_teensy_teamwork_rhyme_slice_of_life.py
=============================================================================

A small, slice-of-life storyworld about making jello together, where a teensy
mix-up becomes a teamwork moment and the children use a little rhyme to keep the
work cheerful.

The world is built to satisfy the shared Storyweavers contract:
- typed entities with physical meters and emotional memes
- a Python reasonableness gate and inline ASP twin
- deterministic generation from StoryParams
- three QA sets grounded in world state
- CLI support for default runs, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
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
class Place:
    id: str
    label: str
    cozy: bool
    works: set[str] = field(default_factory=set)
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


@dataclass
class Activity:
    id: str
    action: str
    setup: str
    mess: str
    zone: set[str]
    keyword: str
    rhyme_seed: str
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
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str] = field(default_factory=set)
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
class Rhyme:
    id: str
    lines: tuple[str, str]
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
    def __init__(self, place: Place) -> None:
        self.place = place
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

    def children(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character" and e.role in {"teammate", "helper"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
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


def _r_shared_cleanup(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["spilled"] < THRESHOLD:
            continue
        sig = ("cleanup", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for kid in world.children():
            kid.memes["teamwork"] += 1
        out.append("__cleanup__")
    return out


CAUSAL_RULES = [Rule("shared_cleanup", _r_shared_cleanup)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(x for x in items if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predicted_spill(world: World, bowl_id: str) -> bool:
    sim = world.copy()
    _do_stir(sim, sim.get(bowl_id), narrate=False)
    return sim.get(bowl_id).meters["spilled"] >= THRESHOLD


def _do_stir(world: World, bowl: Entity, narrate: bool = True) -> None:
    bowl.meters["spilled"] += 1
    bowl.meters["jiggly"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, a: Entity, b: Entity, place: Place, activity: Activity) -> None:
    a.memes["anticipation"] += 1
    b.memes["anticipation"] += 1
    world.say(
        f"After school, {a.id} and {b.id} stood in {place.label} with a bowl, a spoon, "
        f"and a box of jello. {activity.setup}"
    )
    world.say(
        f"{a.id} tapped the spoon and grinned. {b.id} lined up the cups, neat as little stars."
    )


def trouble(world: World, a: Entity, b: Entity, activity: Activity, bowl: Entity) -> None:
    a.memes["worry"] += 1
    b.memes["worry"] += 1
    world.say(
        f"But the jello mix was teensy and slippery, and {b.id} nudged the bowl too hard. "
        f"{b.id} whispered, 'Oops, that was a teensy slip.'"
    )
    world.say(
        f"{a.id} saw a shiny spill starting to spread. The counter needed quick hands and a calm plan."
    )
    world.facts["predicted_spill"] = predicted_spill(world, bowl.id)


def rhyme_help(world: World, a: Entity, b: Entity, rhyme: Rhyme) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    a.memes["teamwork"] += 1
    b.memes["teamwork"] += 1
    world.say(f'Then {a.id} said, "{rhyme.lines[0]}"')
    world.say(f'{b.id} laughed and answered, "{rhyme.lines[1]}"')


def fix_it(world: World, a: Entity, b: Entity, tool: Tool, bowl: Entity) -> None:
    bowl.meters["spilled"] = 0.0
    bowl.meters["jiggly"] = 0.0
    world.get("counter").meters["mess"] = 0.0
    world.say(
        f"Together they used {tool.phrase} and wiped the spot clean in a few careful swipes."
    )
    world.say(
        f"{a.id} held the bowl steady while {b.id} tucked the cups into a tidy row."
    )


def finish(world: World, a: Entity, b: Entity, place: Place, activity: Activity, rhyme: Rhyme) -> None:
    a.memes["pride"] += 1
    b.memes["pride"] += 1
    world.say(
        f"At last, the jello cups went into the fridge to set. The kitchen smelled sweet and calm."
    )
    world.say(
        f"Before closing the door, {a.id} and {b.id} whispered one last rhyme together: "
        f'"{rhyme.lines[0]} / {rhyme.lines[1]}"'
    )
    world.say(
        f"By snack time, the jello was wobbly and bright, and the two friends had made it together."
    )


def tell(place: Place, activity: Activity, tool: Tool, rhyme: Rhyme,
         kid1: str = "Maya", kid1_gender: str = "girl",
         kid2: str = "Noah", kid2_gender: str = "boy",
         adult: str = "parent") -> World:
    world = World(place)
    a = world.add(Entity(id=kid1, kind="character", type=kid1_gender, role="teammate"))
    b = world.add(Entity(id=kid2, kind="character", type=kid2_gender, role="helper"))
    grown = world.add(Entity(id="Adult", kind="character", type=adult, role="adult"))
    bowl = world.add(Entity(id="jello_bowl", type="thing", label="jello bowl"))
    counter = world.add(Entity(id="counter", type="thing", label="counter"))
    world.facts["adult"] = grown
    world.facts["bowl"] = bowl
    world.facts["counter"] = counter
    setup(world, a, b, place, activity)
    world.para()
    trouble(world, a, b, activity, bowl)
    world.para()
    rhyme_help(world, a, b, rhyme)
    fix_it(world, a, b, tool, bowl)
    world.para()
    finish(world, a, b, place, activity, rhyme)
    world.facts.update(
        teammate=a, helper=b, place_cfg=place, activity=activity, tool=tool,
        rhyme=rhyme, outcome="clean",
        teamwork=max(a.memes["teamwork"], b.memes["teamwork"]),
    )
    return world


PLACES = {
    "kitchen": Place(id="kitchen", label="the kitchen table", cozy=True, works={"jello"}),
    "picnic_table": Place(id="picnic", label="the picnic table", cozy=True, works={"jello"}),
    "porch": Place(id="porch", label="the porch rail", cozy=True, works={"jello"}),
}

ACTIVITIES = {
    "jello": Activity(
        id="jello",
        action="make jello",
        setup="They were making little cups for an after-school treat.",
        mess="sticky",
        zone={"counter"},
        keyword="jello",
        rhyme_seed="jiggle",
        tags={"jello", "sweets"},
    ),
    "jello_cups": Activity(
        id="jello_cups",
        action="fill jello cups",
        setup="They had measured the mix, the water, and the tiny spoons.",
        mess="sticky",
        zone={"counter"},
        keyword="jello",
        rhyme_seed="wiggle",
        tags={"jello", "cups"},
    ),
}

TOOLS = {
    "towel": Tool(
        id="towel",
        label="a towel",
        phrase="a folded towel",
        helps={"sticky"},
        tags={"cleanup", "jello"},
    ),
    "tray": Tool(
        id="tray",
        label="a tray",
        phrase="a little tray",
        helps={"sticky"},
        tags={"cleanup", "jello"},
    ),
}

RHYMES = {
    "jiggle": Rhyme(
        id="jiggle",
        lines=("Little jello, gentle and slow,", "Hold the bowl and let it go mellow."),
        tags={"rhyme", "jello", "teamwork"},
    ),
    "wiggle": Rhyme(
        id="wiggle",
        lines=("Wiggle, giggle, careful now,", "Two small hands can fix it somehow."),
        tags={"rhyme", "teamwork"},
    ),
}

@dataclass
class StoryParams:
    place: str
    activity: str
    tool: str
    rhyme: str
    kid1: str
    kid1_gender: str
    kid2: str
    kid2_gender: str
    adult: str
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


CURATED = [
    StoryParams(place="kitchen", activity="jello", tool="towel", rhyme="jiggle", kid1="Maya", kid1_gender="girl", kid2="Noah", kid2_gender="boy", adult="mother"),
    StoryParams(place="picnic_table", activity="jello_cups", tool="tray", rhyme="wiggle", kid1="Ava", kid1_gender="girl", kid2="Eli", kid2_gender="boy", adult="father"),
    StoryParams(place="porch", activity="jello", tool="towel", rhyme="wiggle", kid1="Lena", kid1_gender="girl", kid2="Theo", kid2_gender="boy", adult="mother"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for aid, act in ACTIVITIES.items():
            if "jello" not in act.tags or "jello" not in place.works:
                continue
            for tid, tool in TOOLS.items():
                if "sticky" not in tool.helps:
                    continue
                combos.append((pid, aid, tid))
    return combos


def explain_rejection(place: Place, activity: Activity) -> str:
    return f"(No story: {activity.action} doesn't fit this little setting in a sensible way.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A slice-of-life storyworld about jello, teamwork, and a little rhyme.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--rhyme", choices=RHYMES)
    ap.add_argument("--name1")
    ap.add_argument("--name2")
    ap.add_argument("--adult", choices=["mother", "father"])
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
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, tool = rng.choice(sorted(combos))
    rhyme = args.rhyme or rng.choice(sorted(RHYMES))
    adult = args.adult or rng.choice(["mother", "father"])
    names = [args.name1 or rng.choice(["Maya", "Luna", "Ava", "Nia", "Ella"]),
             args.name2 or rng.choice(["Noah", "Leo", "Eli", "Milo", "Theo"])]
    return StoryParams(place=place, activity=activity, tool=tool, rhyme=rhyme,
                       kid1=names[0], kid1_gender="girl", kid2=names[1], kid2_gender="boy",
                       adult=adult)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life story for a small child that includes the word "{f["activity"].keyword}" and a gentle teamwork moment.',
        f'Tell a story where {f["teammate"].id} and {f["helper"].id} make {f["activity"].action} and use a little rhyme to solve a tiny mess.',
        f'Write a cozy story about making {f["activity"].keyword} with teamwork, ending with a sweet snack and a simple rhyme.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b = f["teammate"], f["helper"]
    act, tool, rhyme = f["activity"], f["tool"], f["rhyme"]
    return [
        ("Who worked together in the story?",
         f"{a.id} and {b.id} worked together. They shared the job, watched the bowl, and kept the kitchen calm."),
        ("What small problem happened?",
         f"The jello mix made a teensy spill on the counter. It was small, but it needed quick hands and a careful plan."),
        ("How did they fix it?",
         f"They used {tool.phrase} and cleaned up together. After that, the bowl could go into the fridge without any sticky trouble."),
        ("What was the rhyme like?",
         f"It was a short, cheerful rhyme that helped them stay calm. The rhyme made the work feel like a game they could do together."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is jello?",
         "Jello is a wobbly sweet treat that starts as a mix and then chills until it sets."),
        ("Why is teamwork helpful?",
         "Teamwork is helpful because two people can share the work, stay calmer, and finish faster."),
        ("What is a rhyme?",
         "A rhyme is a pair of lines or words that sound alike at the end, which makes them fun to say."),
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
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,A,T) :- place(P), activity(A), tool(T), jello_place(P), jello_activity(A), sticky_tool(T).
spilled :- bowl_action.
teamwork :- spill, rhyme.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("jello_place", pid))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("jello_activity", aid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("sticky_tool", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH between ASP and Python gates.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, activity=None, tool=None, rhyme=None, name1=None, name2=None, adult=None), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.activity not in ACTIVITIES or params.tool not in TOOLS or params.rhyme not in RHYMES:
        raise StoryError("(Invalid parameters.)")
    world = tell(
        PLACES[params.place],
        ACTIVITIES[params.activity],
        TOOLS[params.tool],
        RHYMES[params.rhyme],
        kid1=params.kid1,
        kid1_gender=params.kid1_gender,
        kid2=params.kid2,
        kid2_gender=params.kid2_gender,
        adult=params.adult,
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
