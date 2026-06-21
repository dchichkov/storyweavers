#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/simple_session_duff_humor_fable.py
====================================================================

A small, self-contained storyworld with a fable-like tone and a little humor.

Premise
-------
A careful mouse runs a simple cooking session for the forest animals. A boastful
crow keeps trying to improve the plan, but only makes a sticky duff of things.
The turn is practical: the group swaps cleverness for patience, finishes the
session calmly, and ends with a funny moral about simple steps and full bellies.

The story always includes the seed words:
- simple
- session
- duff

It supports the standard Storyweavers interface:
- build_parser
- resolve_params
- generate
- emit
- main

And it includes:
- a Python reasonableness gate
- an inline ASP twin
- --verify with a smoke test of ordinary generation
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
    quiet: bool = True
    roomy: bool = False
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
class Treat:
    id: str
    label: str
    phrase: str
    simple_name: str
    sticky: bool = False
    sweet: bool = True
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
class Tool:
    id: str
    label: str
    safe: bool = True
    neat: bool = True
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
class Rule:
    name: str
    apply: Callable[["World"], list[str]]
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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


def _r_sticky(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["sticky"] < THRESHOLD:
            continue
        sig = ("sticky", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["embarrassed"] += 1
        out.append("__sticky__")
    return out


def _r_cleanup(world: World) -> list[str]:
    out: list[str] = []
    if world.get("table").meters["sticky"] < THRESHOLD:
        return out
    sig = ("cleanup", "table")
    if sig not in world.fired:
        world.fired.add(sig)
        world.get("mouse").memes["responsible"] += 1
        out.append("__cleanup__")
    return out


CAUSAL_RULES = [Rule("sticky", _r_sticky), Rule("cleanup", _r_cleanup)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(i for i in items if not i.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def simple_reasonable(kind: str, treat: Treat, tool: Tool) -> bool:
    return kind in SIMPLE_COMBOS and treat.sticky and tool.safe


def outcome_of(params: "StoryParams") -> str:
    return "messy" if params.extra_spill else "tidy"


def choose_name(rng: random.Random) -> str:
    return rng.choice(["Milo", "Pip", "Nia", "Tess", "Roo", "Bram"])


def tell(place: Place, treat: Treat, tool: Tool, host_name: str, guest_name: str,
         extra_spill: bool) -> World:
    world = World()
    mouse = world.add(Entity(id=host_name, kind="character", type="mouse", label="the mouse",
                             role="host", traits=["careful", "simple"]))
    crow = world.add(Entity(id=guest_name, kind="character", type="crow", label="the crow",
                            role="guest", traits=["proud", "funny"]))
    world.add(Entity(id="table", kind="thing", type="table", label="the table"))
    world.add(Entity(id="duff", kind="thing", type="treat", label=treat.label))
    world.facts["place"] = place
    world.facts["treat"] = treat
    world.facts["tool"] = tool
    world.facts["mouse"] = mouse
    world.facts["crow"] = crow
    world.facts["extra_spill"] = extra_spill

    mouse.memes["hope"] += 1
    crow.memes["hunger"] += 1

    world.say(
        f"In the little {place.label}, {mouse.id} planned a simple session for supper."
        f" {mouse.id} laid out {treat.phrase} and a clean cloth, while {crow.id} "
        f"arrived with a grin as sharp as a pin."
    )
    world.say(
        f'"This will be a fine session," said {mouse.id}. '
        f'"No fuss, no rush, and no duff in the plan."'
    )

    world.para()
    crow.memes["pride"] += 1
    world.say(
        f'But {crow.id} puffed out {crow.pronoun("possessive")} feathers. '
        f'"A fancier session needs a fancier trick!" {crow.pronoun().capitalize()} '
        f"cried, and {crow.id} tipped {tool.label} into the bowl."
    )
    if extra_spill:
        world.get("table").meters["sticky"] += 1
        world.get("duff").meters["sticky"] += 1
        crow.memes["oops"] += 1
        propagate(world, narrate=False)
        world.say(
            f"The mix went splat, then splish, then suddenly looked like sticky duff."
            f" Even the spoon seemed to be wearing it."
        )
    else:
        world.say(
            f"The tool stayed put, and the bowl kept its dignity."
        )

    world.para()
    if extra_spill:
        mouse.memes["calm"] += 1
        world.say(
            f"{mouse.id} did not scold. {mouse.pronoun().capitalize()} simply laughed "
            f"and said, \"A simple session is safest when the cleverness sits down first.\""
        )
        world.say(
            f"Then {mouse.id} wiped the table, set the bowl straight, and finished the "
            f"duff the old way: slow, kind, and tidy."
        )
    else:
        world.say(
            f"{mouse.id} smiled and said, \"See? Simple steps are strong steps.\""
        )
        world.say(
            f"The bowl was stirred once, then twice, and the treat settled into a neat "
            f"little duff with no drama at all."
        )

    world.para()
    mouse.memes["joy"] += 1
    crow.memes["joy"] += 1
    world.say(
        f"At last, the animals ate together, and {crow.id} bowed so low that "
        f"{crow.pronoun('possessive')} beak nearly tickled {mouse.id}'s nose."
    )
    if extra_spill:
        world.say(
            f'"I tried to improve the session," admitted {crow.id}, "but I only made a '
            f"duff of myself."'
        )
    world.say(
        f"{mouse.id} chuckled. \"That is the tale,\" {mouse.pronoun()} said. "
        f"\"A simple heart, a simple plan, and a full belly make the best ending.\""
    )

    world.facts["outcome"] = "messy" if extra_spill else "tidy"
    return world


@dataclass
class StoryParams:
    place: str
    treat: str
    tool: str
    extra_spill: bool = False
    host_name: str = "Milo"
    guest_name: str = "Quill"
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


PLACES = {
    "kitchen": Place(id="kitchen", label="kitchen"),
    "barn": Place(id="barn", label="barn"),
    "garden_shed": Place(id="shed", label="garden shed"),
}

TREATS = {
    "duff": Treat(
        id="duff",
        label="warm duff",
        phrase="a warm pan of duff",
        simple_name="duff",
        sticky=True,
        sweet=True,
        tags={"duff", "sweet"},
    ),
    "jam": Treat(
        id="jam",
        label="plum jam",
        phrase="a jar of plum jam",
        simple_name="jam",
        sticky=True,
        sweet=True,
        tags={"jam", "sweet"},
    ),
    "porridge": Treat(
        id="porridge",
        label="oat porridge",
        phrase="a pot of oat porridge",
        simple_name="porridge",
        sticky=False,
        sweet=False,
        tags={"porridge"},
    ),
}

TOOLS = {
    "ladle": Tool(id="ladle", label="a ladle", safe=True, neat=True, tags={"simple"}),
    "whisk": Tool(id="whisk", label="a whisk", safe=True, neat=False, tags={"session"}),
    "spoon": Tool(id="spoon", label="a spoon", safe=True, neat=True, tags={"simple"}),
    "trumpet": Tool(id="trumpet", label="a tiny trumpet", safe=False, neat=False, tags={"humor"}),
}

SIMPLE_COMBOS = {
    "duff",
    "jam",
    "simple",
    "session",
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for t in TREATS:
            for tool in TOOLS:
                if TREATS[t].sticky and TOOLS[tool].safe:
                    combos.append((p, t, tool))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable-like story world with humor.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--spill", action="store_true", help="allow the funny mishap branch")
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
    if args.tool and not TOOLS[args.tool].safe:
        raise StoryError("That tool would spoil the simple meal instead of helping it.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.treat is None or c[1] == args.treat)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, treat, tool = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        treat=treat,
        tool=tool,
        extra_spill=bool(args.spill) or rng.choice([False, True]),
        host_name=args.host_name if hasattr(args, "host_name") and args.host_name else choose_name(rng),
        guest_name=args.guest_name if hasattr(args, "guest_name") and args.guest_name else choose_name(rng),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    treat: Treat = f["treat"]
    return [
        f'Write a fable-like story that includes the words "simple", "session", and "{treat.simple_name}".',
        f"Tell a humorous moral tale about {f['mouse'].id} and {f['crow'].id} running a simple session with {treat.simple_name}.",
        "Write a short child-friendly fable where a tidy plan beats a silly boast.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    mouse, crow, treat = f["mouse"], f["crow"], f["treat"]
    ans1 = (
        f"It is about {mouse.id}, a careful mouse, and {crow.id}, a boastful crow. "
        f"They try to share a simple session and learn from a sticky mistake."
    )
    ans2 = (
        f"{crow.id} made a fuss and turned the treat into sticky duff. "
        f"{mouse.id} stayed calm and finished the session the simple way."
    )
    ans3 = (
        f"The ending is funny and kind: the animals eat together, and {crow.id} "
        f"admits that too much cleverness made a duff of the plan."
    )
    return [
        QAItem(question="Who is the story about?", answer=ans1),
        QAItem(question="What went wrong during the session?", answer=ans2),
        QAItem(question="How does the story end?", answer=ans3),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to keep a plan simple?",
            answer="It means using only the steps you truly need. A simple plan is easy to follow and less likely to turn into a mess.",
        ),
        QAItem(
            question="What is duff in this story?",
            answer="Duff is a sweet, soft pudding here. It is also a funny word for a sticky mistake when the crow gets carried away.",
        ),
        QAItem(
            question="What should you do if a shared task starts to go wrong?",
            answer="Stop, laugh if it is safe to laugh, and choose the calmer way. Careful hands usually finish the job better than fancy bragging.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
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
    return "\n".join(lines)


ASP_RULES = r"""
sticky(T) :- treat(T), sticky_treat(T).
messy_outcome(messy) :- sticky(treat_duff), spill(yes).
messy_outcome(tidy) :- not messy_outcome(messy).
valid(Place, Treat, Tool) :- place(Place), treat(Treat), tool(Tool), sticky_treat(Treat), safe_tool(Tool).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for t, obj in TREATS.items():
        lines.append(asp.fact("treat", t))
        if obj.sticky:
            lines.append(asp.fact("sticky_treat", t))
    for tl, obj in TOOLS.items():
        lines.append(asp.fact("tool", tl))
        if obj.safe:
            lines.append(asp.fact("safe_tool", tl))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH between ASP and Python valid_combos()")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, treat=None, tool=None, spill=False), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.treat not in TREATS or params.tool not in TOOLS:
        raise StoryError("Invalid story parameters.")
    treat = TREATS[params.treat]
    tool = TOOLS[params.tool]
    if not simple_reasonable(params.place, treat, tool):
        raise StoryError("That choice does not fit the simple fable logic.")
    world = tell(PLACES[params.place], treat, tool, params.host_name, params.guest_name, params.extra_spill)
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


CURATED = [
    StoryParams(place="kitchen", treat="duff", tool="ladle", extra_spill=True, host_name="Milo", guest_name="Quill"),
    StoryParams(place="barn", treat="jam", tool="spoon", extra_spill=False, host_name="Pip", guest_name="Mara"),
    StoryParams(place="garden_shed", treat="duff", tool="whisk", extra_spill=True, host_name="Nia", guest_name="Gus"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
