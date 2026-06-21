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
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle", "detective"}
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


@dataclass
class Place:
    id: str
    label: str
    clues: list[str] = field(default_factory=list)
    hidden: str = ""
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
class Suspect:
    id: str
    label: str
    alibi: str
    nervous: str
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
    use: str
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
class Case:
    id: str
    mystery: str
    conflict: str
    resolution: str
    setting: str
    clue_word: str
    sweeper_name: str
    inspector_name: str
    helper_name: str
    culprit_name: str
    note_word: str
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
class StoryParams:
    case: str
    place: str
    suspect: str
    tool: str
    sweeper: str
    inspector: str
    helper: str
    culprit: str
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
    def __init__(self) -> None:
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
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


def _r_conflict(world: World) -> list[str]:
    out = []
    if world.get("alley").meters["tension"] >= THRESHOLD and ("conflict",) not in world.fired:
        world.fired.add(("conflict",))
        world.get("sweeper").memes["conflict"] += 1
        world.get("inspector").memes["conflict"] += 1
        out.append("__conflict__")
    return out


CAUSAL_RULES = [Rule("conflict", _r_conflict)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def predict(world: World) -> dict:
    sim = world.copy()
    sim.get("alley").meters["tension"] += 1
    propagate(sim, narrate=False)
    return {"conflict": sim.get("sweeper").memes["conflict"] >= THRESHOLD}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for cid, case in CASES.items():
        for pid, place in PLACES.items():
            for sid, suspect in SUSPECTS.items():
                if case.clue_word in place.clues and suspect.tags & place.tags:
                    combos.append((cid, pid, sid))
    return combos


def choose_name(rng: random.Random, pool: list[str], avoid: str = "") -> str:
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def tell(case: Case, place: Place, suspect: Suspect, tool: Tool, sweeper_name: str,
         inspector_name: str, helper_name: str, culprit_name: str) -> World:
    w = World()
    sweeper = w.add(Entity(id="sweeper", kind="character", type="detective", label=sweeper_name, role="hero"))
    inspector = w.add(Entity(id="inspector", kind="character", type="detective", label=inspector_name, role="ally"))
    helper = w.add(Entity(id="helper", kind="character", type="woman", label=helper_name, role="helper"))
    culprit = w.add(Entity(id="culprit", kind="character", type="man", label=culprit_name, role="culprit"))
    alley = w.add(Entity(id="alley", type="place", label=place.label, tags=set(place.tags)))
    clue = w.add(Entity(id="clue", type="thing", label=case.clue_word))
    toolent = w.add(Entity(id="tool", type="thing", label=tool.label))
    w.facts["case"] = case
    w.facts["place"] = place
    w.facts["suspect"] = suspect
    w.facts["tool"] = tool
    w.facts["sweeper"] = sweeper
    w.facts["inspector"] = inspector
    w.facts["helper"] = helper
    w.facts["culprit"] = culprit
    w.facts["alley"] = alley
    w.facts["clue"] = clue
    w.facts["toolent"] = toolent

    sweeper.memes["curiosity"] += 1
    inspector.memes["curiosity"] += 1
    w.say(f"{sweeper.label} was a careful sweeper in a detective story, and {inspector.label} was always watching for a clue.")
    w.say(f"That afternoon they reached {place.label}. {place.hidden} They found {case.clue_word} near the doorway, and the tiny mark made {sweeper.label} curious at once.")
    w.para()
    w.say(f'"This smells like trouble," {inspector.label} said. "{case.conflict}"')
    w.say(f'{sweeper.label} knelt by the floor and used a {tool.label} to study the dust. {suspect.alibi} But the answer did not feel right.')
    pred = predict(w)
    if pred["conflict"]:
        w.get("alley").meters["tension"] += 1
        propagate(w, narrate=False)
        w.para()
        w.say(f"At the old alley behind the shop, the mystery turned sharp. {helper.label} pointed at the thin trail, and {culprit.label} tried to slip away.")
        w.say(f'"Wait," {sweeper.label} said. "{case.clue_word.capitalize()} comes from the sweeper cart, and that means someone moved it on purpose."')
        w.say(f"The culprit froze, and {inspector.label} stepped in beside the sweeper.")
        w.para()
        w.say(f"In the end, {culprit.label} admitted it. {case.resolution} The sweeper rolled home through the quiet street, and the clue sat safely in place again.")
    else:
        w.para()
        w.say(f"The trail stayed calm, so {sweeper.label} asked one more question instead of making a scene. {case.resolution} The sweeper rolled on, and the little clue made sense at last.")
    w.facts["outcome"] = "conflict" if pred["conflict"] else "calm"
    return w


CASES = {
    "missing_key": Case("missing_key", "a missing key", "a thief had moved the clue cart", "the key was found under the mat", "the side street", "dust", "Ari", "June", "Mina", "Mr. Black", "note"),
    "muddy_boot": Case("muddy_boot", "muddy boots", "someone had crossed the hall in secret", "the boots matched the cellar tracks", "the back alley", "mud", "Nico", "Iris", "Tess", "Old Pike", "sign"),
    "broken_lamp": Case("broken_lamp", "a broken lamp", "the room had gone dark after a quiet bump", "the lamp was fixed with a new bulb", "the narrow lane", "ash", "Lena", "Owen", "Faye", "Captain Reed", "mark"),
}

PLACES = {
    "alley": Place("alley", "the back alley", clues=["dust", "mud"], hidden="The bricks were damp and the bins stood like watchful shadows.", tags={"street", "dust"}),
    "lane": Place("lane", "the narrow lane", clues=["ash", "dust"], hidden="A bent sign hung over the lane, and the windows were nearly dark.", tags={"street", "ash"}),
    "street": Place("street", "the side street", clues=["dust", "mud"], hidden="A row of quiet shops lined the street, and one door had fresh scuffs.", tags={"street", "dust"}),
}

SUSPECTS = {
    "vendor": Suspect("vendor", "the vendor", "I was counting boxes all morning.", "the vendor kept looking at the floor.", tags={"street"}),
    "guard": Suspect("guard", "the guard", "I never left my post.", "the guard's voice sounded too quick.", tags={"street"}),
    "neighbor": Suspect("neighbor", "the neighbor", "I only heard footsteps.", "the neighbor watched the sweeper too closely.", tags={"street"}),
}

TOOLS = {
    "lamp": Tool("lamp", "lamp glass", "shine light on the clue", tags={"light"}),
    "brush": Tool("brush", "little brush", "sweep dust aside", tags={"dust"}),
    "magnifier": Tool("magnifier", "magnifying glass", "look at the tiny mark", tags={"look"}),
}

GIRL_NAMES = ["Ari", "June", "Mina", "Tess", "Lena", "Iris", "Faye"]
BOY_NAMES = ["Nico", "Owen", "Eli", "Miles", "Theo", "Noah", "Jude"]
HELPERS = ["Mina", "Tess", "Faye", "Iris"]
CULPRITS = ["Mr. Black", "Old Pike", "Captain Reed", "the vendor"]

CURATED = [
    StoryParams(case="missing_key", place="street", suspect="vendor", tool="brush", sweeper="Ari", inspector="June", helper="Mina", culprit="Mr. Black"),
    StoryParams(case="muddy_boot", place="alley", suspect="guard", tool="magnifier", sweeper="Nico", inspector="Owen", helper="Tess", culprit="Old Pike"),
    StoryParams(case="broken_lamp", place="lane", suspect="neighbor", tool="lamp", sweeper="Lena", inspector="Iris", helper="Faye", culprit="Captain Reed"),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly detective story that includes the word "sweeper" and the feeling of curiosity.',
        f"Tell a detective story where {f['sweeper'].label} follows a clue in {f['place'].label} and a conflict grows before the truth comes out.",
        f"Write a short mystery where a sweeper notices a clue, gets curious, and solves the problem without losing the gentle tone.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    case: Case = f["case"]
    sweeper: Entity = f["sweeper"]
    inspector: Entity = f["inspector"]
    suspect: Suspect = f["suspect"]
    qa = [
        QAItem(question="Who is the story about?", answer=f"It is about {sweeper.label} and {inspector.label}, who work together to solve a small mystery. The sweeper is the one who keeps noticing clues first."),
        QAItem(question="Why did the sweeper get curious?", answer=f"{case.clue_word.capitalize()} appeared in the wrong place, so {sweeper.label} wanted to know where it came from. That curiosity pushed the story forward and led to the truth."),
    ]
    if f["outcome"] == "conflict":
        qa.append(QAItem(question="What caused the conflict?", answer=f"The conflict grew when {suspect.label} tried to hide what happened and leave before the questions were finished. The sweeper kept going, so the truth had to come out."))

    qa.append(QAItem(question="How did the mystery end?", answer=f"It ended with {case.resolution}. {sweeper.label} stayed calm, and the clue made sense when everyone finally looked closely."))
    return qa


KNOWLEDGE = {
    "sweeper": [("What is a sweeper?", "A sweeper is someone or something that clears dust and dirt away. In a detective story, a sweeper can also be a careful helper who notices small things on the floor.")],
    "curiosity": [("What is curiosity?", "Curiosity is the feeling that makes you want to ask questions and look closer. It helps a detective notice clues.")],
    "conflict": [("What is conflict in a story?", "Conflict is the problem or disagreement that makes the story tense. It gives the detective something to solve.")],
    "clue": [("What is a clue?", "A clue is a small piece of information that helps solve a mystery. A detective looks at clues to find out what happened.")],
    "detective": [("What does a detective do?", "A detective looks carefully, asks questions, and follows clues. A good detective tries to find the truth.")],
}


def world_qa(world: World) -> list[QAItem]:
    return [QAItem(*pair) for key, pair in KNOWLEDGE.items() if key in {"sweeper", "curiosity", "conflict", "clue", "detective"}]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)], "", "== (2) Story questions ==",]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines += ["", "== (3) World knowledge ==",]
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        m = {k: v for k, v in e.meters.items() if v}
        mm = {k: v for k, v in e.memes.items() if v}
        if m:
            bits.append(f"meters={dict(m)}")
        if mm:
            bits.append(f"memes={dict(mm)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        out.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(out)


ASP_RULES = r"""
curiosity(hero) :- role(hero).
conflict :- tension(alley), sweeper(hero).
valid(C,P,S) :- case(C), place(P), suspect(S), clue(C,Cl), clue_in(P,Cl), suspect_tag(S,T), place_tag(P,T).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for cid, c in CASES.items():
        lines.append(asp.fact("case", cid))
        lines.append(asp.fact("clue", cid, c.clue_word))
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("clue_in", pid, p.clues[0]))
        for t in sorted(p.tags):
            lines.append(asp.fact("place_tag", pid, t))
    for sid, s in SUSPECTS.items():
        lines.append(asp.fact("suspect", sid))
        for t in sorted(s.tags):
            lines.append(asp.fact("suspect_tag", sid, t))
    lines.append(asp.fact("role", "hero"))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3.", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python.")
        if cl - py:
            print(" only in ASP:", sorted(cl - py))
        if py - cl:
            print(" only in Python:", sorted(py - cl))
    try:
        sample = generate(resolve_params(argparse.Namespace(case=None, place=None, suspect=None, tool=None, sweeper=None, inspector=None, helper=None, culprit=None), random.Random(0)))
        assert sample.story
        print("OK: smoke test generation succeeded.")
    except Exception as e:
        rc = 1
        print("SMOKE TEST FAILED:", e)
    return rc


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="A tiny detective story world with a sweeper, curiosity, and conflict.")
    p.add_argument("--case", choices=CASES)
    p.add_argument("--place", choices=PLACES)
    p.add_argument("--suspect", choices=SUSPECTS)
    p.add_argument("--tool", choices=TOOLS)
    p.add_argument("--sweeper")
    p.add_argument("--inspector")
    p.add_argument("--helper")
    p.add_argument("--culprit")
    p.add_argument("-n", type=int, default=1)
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--all", action="store_true")
    p.add_argument("--trace", action="store_true")
    p.add_argument("--qa", action="store_true")
    p.add_argument("--json", action="store_true")
    p.add_argument("--asp", action="store_true")
    p.add_argument("--verify", action="store_true")
    p.add_argument("--show-asp", action="store_true")
    return p


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.case and args.place and args.suspect:
        if (args.case, args.place, args.suspect) not in combos:
            raise StoryError("No valid detective setup matches those choices.")
    if not combos:
        raise StoryError("No valid combos available.")
    case, place, suspect = rng.choice([c for c in combos if (args.case is None or c[0] == args.case) and (args.place is None or c[1] == args.place) and (args.suspect is None or c[2] == args.suspect)])
    sweeper = args.sweeper or rng.choice(GIRL_NAMES + BOY_NAMES)
    inspector = args.inspector or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != sweeper])
    helper = args.helper or rng.choice(HELPERS)
    culprit = args.culprit or rng.choice(CULPRITS)
    tool = args.tool or rng.choice(list(TOOLS))
    return StoryParams(case=case, place=place, suspect=suspect, tool=tool, sweeper=sweeper, inspector=inspector, helper=helper, culprit=culprit)


def generate(params: StoryParams) -> StorySample:
    if params.case not in CASES or params.place not in PLACES or params.suspect not in SUSPECTS or params.tool not in TOOLS:
        raise StoryError("Invalid story params.")
    case = CASES[params.case]
    place = PLACES[params.place]
    suspect = SUSPECTS[params.suspect]
    tool = TOOLS[params.tool]
    world = tell(case, place, suspect, tool, params.sweeper, params.inspector, params.helper, params.culprit)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_qa(world), world=world)


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
        print(asp_program("#show valid/3.", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3.", "#show valid/3."))
        for t in asp.atoms(model, "valid"):
            print(t)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
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
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
