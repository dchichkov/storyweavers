#!/usr/bin/env python3
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    label: str
    dark_spot: str
    rhyme: str
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
class ExtractTool:
    id: str
    label: str
    phrase: str
    use_text: str
    suspense: int = 0
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
class GroomAction:
    id: str
    label: str
    phrase: str
    effect: str
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
class Bug:
    id: str
    label: str
    phrase: str
    hiding: str
    makes_rustle: bool = True
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
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    bugs: dict[str, Bug] = field(default_factory=dict)
    extracted: bool = False
    groomed: bool = False
    bug_seen: bool = False
    bug_gone: bool = False
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        c = World(place=self.place)
        c.entities = copy.deepcopy(self.entities)
        c.bugs = copy.deepcopy(self.bugs)
        c.extracted = self.extracted
        c.groomed = self.groomed
        c.bug_seen = self.bug_seen
        c.bug_gone = self.bug_gone
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c
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


PACES = {
    "slow": 1,
    "wary": 2,
    "sudden": 3,
}

PLACES = {
    "nursery": Place(id="nursery", label="the nursery", dark_spot="the cradle's shadow", rhyme="soft and low", tags={"nursery"}),
    "workroom": Place(id="workroom", label="the workroom", dark_spot="the shelf behind the toys", rhyme="tidy and small", tags={"workroom"}),
}

TOOLS = {
    "tweezers": ExtractTool(id="tweezers", label="tweezers", phrase="a little pair of tweezers", use_text="pinched and pulled the bug free", suspense=2, tags={"extract"}),
    "brush": ExtractTool(id="brush", label="soft brush", phrase="a soft brush", use_text="brushed away the bug's hiding place", suspense=1, tags={"groom"}),
}

GROOMS = {
    "comb": GroomAction(id="comb", label="comb", phrase="a tiny comb", effect="smoothed the wool back into place", tags={"groom"}),
    "ribbon": GroomAction(id="ribbon", label="ribbon", phrase="a bright ribbon", effect="tied the strands neat and neat", tags={"groom"}),
}

BUGS = {
    "beetle": Bug(id="beetle", label="bug", phrase="a little bug", hiding="under the woolly cap", tags={"bug"}),
    "moth": Bug(id="moth", label="bug", phrase="a tiny bug", hiding="in the velvet hem", tags={"bug"}),
}

GIRL_NAMES = ["Milly", "Nell", "Rose", "Luna", "Maisie"]
BOY_NAMES = ["Jack", "Tom", "Finn", "Ned", "Ollie"]


@dataclass
class StoryParams:
    place: str
    tool: str
    groom: str
    bug: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    pace: str = "wary"
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
    StoryParams(place="nursery", tool="tweezers", groom="comb", bug="beetle", child="Milly", child_gender="girl", helper="Mom", helper_gender="mother", pace="wary", seed=1),
    StoryParams(place="workroom", tool="brush", groom="ribbon", bug="moth", child="Jack", child_gender="boy", helper="Dad", helper_gender="father", pace="sudden", seed=2),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for t in TOOLS:
            for g in GROOMS:
                combos.append((p, t, g))
    return combos


def hazard_ok(tool: ExtractTool, bug: Bug) -> bool:
    return tool.id in {"tweezers", "brush"} and bug.label == "bug"


def reasonableness_gate(tool: ExtractTool, bug: Bug) -> bool:
    return hazard_ok(tool, bug)


def _narrate_setup(world: World, child: Entity, helper: Entity, bug: Bug, tool: ExtractTool) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"Down in {world.place.label}, {child.id} and {helper.id} worked in a hush, "
        f"as soft as a nursery rhyme. They meant to groom the little things neat, "
        f"but {bug.phrase} was hiding {bug.hiding}."
    )
    world.say(
        f'"Shh," whispered {child.id}. "We can {tool.label} the trouble out if we are quick."'
    )
    world.bug_seen = True


def _predict(world: World, tool: ExtractTool) -> dict:
    sim = world.copy()
    sim.extracted = True
    sim.bug_gone = True
    return {"noisy": tool.suspense >= 2, "safe": True}


def _tension(world: World, child: Entity, helper: Entity, tool: ExtractTool, bug: Bug) -> None:
    child.memes["fear"] += 1
    helper.memes["care"] += 1
    pred = _predict(world, tool)
    if pred["noisy"]:
        world.say(
            f"But the shadow seemed to twitch, and the tiny bug gave one soft bug-buzz. "
            f"{helper.id} held still and listened, because a loud move could send it skittering away."
        )
    else:
        world.say(
            f"The room went quiet. Even the clock seemed to slow, as if it knew a careful hand was coming."
        )


def _extract(world: World, child: Entity, helper: Entity, tool: ExtractTool, bug: Bug) -> None:
    world.extracted = True
    child.meters["care"] += 1
    world.say(
        f"Then {child.id} took a breath and {tool.use_text}. "
        f"The {tool.label} did its work, and the little bug was out at last."
    )
    world.bug_gone = True


def _groom(world: World, helper: Entity, groom: GroomAction, child: Entity) -> None:
    world.groomed = True
    helper.memes["relief"] += 1
    world.say(
        f"{helper.id} smiled and used {groom.phrase}; {groom.effect}. "
        f"Together they made the place look sweet again, tidy as can be."
    )
    world.say(
        f"{child.id} gave a tiny grin, for the scary bit was over and the little world was neat."
    )


def _ending(world: World, child: Entity, helper: Entity) -> None:
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"So {child.id} and {helper.id} went on with a gentle hum, "
        f"and the nursery stayed calm, safe, and bright."
    )


def tell(place: Place, tool: ExtractTool, groom: GroomAction, bug: Bug,
         child_name: str, child_gender: str, helper_name: str, helper_gender: str) -> World:
    world = World(place=place)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    world.bugs[bug.id] = bug
    _narrate_setup(world, child, helper, bug, tool)
    world.para()
    _tension(world, child, helper, tool, bug)
    world.para()
    _extract(world, child, helper, tool, bug)
    _groom(world, helper, groom, child)
    world.para()
    _ending(world, child, helper)
    world.facts.update(child=child, helper=helper, tool=tool, groom=groom, bug=bug, place=place)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme-style suspense story that includes the words "{f["tool"].label}", "{f["groom"].label}", and "{f["bug"].label}".',
        f"Tell a soft, suspenseful story in a nursery where {f['child'].id} and {f['helper'].id} carefully {f['tool'].label} out a bug, then groom everything neat again.",
        f"Write a child-friendly rhyme with a tiny scare, a careful extract, and a tidy ending in {f['place'].label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    tool = f["tool"]
    groom = f["groom"]
    bug = f["bug"]
    return [
        QAItem(question="Who is the story about?", answer=f"It is about {child.id} and {helper.id} in {f['place'].label}. They were dealing with {bug.phrase} and trying to keep everything calm."),
        QAItem(question=f"What did {child.id} use to extract the bug?", answer=f"{child.id} used {tool.phrase} to extract the bug. The careful tool helped pull the bug free without turning the room into a jumble."),
        QAItem(question=f"How did they groom the scene afterward?", answer=f"{helper.id} used {groom.phrase} to groom things neat again. That made the place look tidy after the little suspenseful moment."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does extract mean?", answer="To extract something means to pull it out or take it free from where it is stuck. It is a careful kind of removing."),
        QAItem(question="What does groom mean?", answer="To groom means to make something neat, smooth, or tidy. People groom hair, fur, or wool to make it look nice."),
        QAItem(question="What is a bug?", answer="A bug is a tiny creature like a beetle or moth. Bugs are small, and they can hide in little places."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)], "", "== story QA =="]
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
    lines = [f"place={world.place.label}"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: memes={dict(e.memes)} meters={dict(e.meters)} role={e.role}")
    lines.append(f"bug_seen={world.bug_seen} extracted={world.extracted} groomed={world.groomed} bug_gone={world.bug_gone}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("place", "nursery"),
        asp.fact("place", "workroom"),
        asp.fact("extract_tool", "tweezers"),
        asp.fact("extract_tool", "brush"),
        asp.fact("groom", "comb"),
        asp.fact("groom", "ribbon"),
        asp.fact("bug", "beetle"),
        asp.fact("bug", "moth"),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
compatible(P, T, G) :- place(P), extract_tool(T), groom(G).
#show compatible/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    import io
    import contextlib

    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python combo gates differ.")
        rc = 1
    try:
        s = generate(CURATED[0])
        _ = s.story
        _ = format_qa(s)
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny nursery-rhyme story world with suspense, extract, groom, and bug.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--groom", choices=GROOMS)
    ap.add_argument("--bug", choices=BUGS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["mother", "father"])
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
    if args.tool and args.bug and not reasonableness_gate(TOOLS[args.tool], BUGS[args.bug]):
        raise StoryError("That tool and bug do not make a sensible suspense story.")
    place = args.place or rng.choice(list(PLACES))
    tool = args.tool or rng.choice(list(TOOLS))
    groom = args.groom or rng.choice(list(GROOMS))
    bug = args.bug or rng.choice(list(BUGS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["mother", "father"])
    child_pool = GIRL_NAMES if child_gender == "girl" else BOY_NAMES
    helper = args.helper or ("Mom" if helper_gender == "mother" else "Dad")
    child = args.child or rng.choice(child_pool)
    return StoryParams(place=place, tool=tool, groom=groom, bug=bug, child=child, child_gender=child_gender, helper=helper, helper_gender=helper_gender)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.tool not in TOOLS or params.groom not in GROOMS or params.bug not in BUGS:
        raise StoryError("Invalid params for this world.")
    world = tell(PLACES[params.place], TOOLS[params.tool], GROOMS[params.groom], BUGS[params.bug], params.child, params.child_gender, params.helper, params.helper_gender)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


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
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{p} {t} {g}" for p, t, g in asp_valid_combos()))
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
            params.seed = base_seed + i
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

    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


CURATED = [
    StoryParams(place="nursery", tool="tweezers", groom="comb", bug="beetle", child="Milly", child_gender="girl", helper="Mom", helper_gender="mother", pace="wary", seed=1),
    StoryParams(place="workroom", tool="brush", groom="ribbon", bug="moth", child="Jack", child_gender="boy", helper="Dad", helper_gender="father", pace="sudden", seed=2),
]


if __name__ == "__main__":
    main()
