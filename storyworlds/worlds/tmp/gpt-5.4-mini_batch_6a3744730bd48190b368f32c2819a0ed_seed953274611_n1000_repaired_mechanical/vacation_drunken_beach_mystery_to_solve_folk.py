#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/vacation_drunken_beach_mystery_to_solve_folk.py
================================================================================

A small standalone story world for a folk-tale style beach mystery.

Premise:
- A family or small party arrives on vacation at the beach.
- A strange problem appears: something important is missing, swapped, or washed up.
- A drunken, kindly local or visitor creates confusion, but the mystery is solved
  by careful noticing, practical help, and a gentle folk-tale turn.
- The ending should feel warm, complete, and concrete: the missing thing is found,
  the misunderstanding is cleared, and the beach scene changes because of it.

The world is intentionally small. It models physical meters and emotional memes,
drives prose from world state, and includes a Python reasonableness gate plus an
inline ASP twin for parity checks.
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
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
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
class Setting:
    id: str
    label: str
    mood: str
    tide: str
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
class Mystery:
    id: str
    clue: str
    missing: str
    found_as: str
    location_hint: str
    folk_reason: str
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
class DrunkState:
    id: str
    label: str
    stumble: str
    muddle: str
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
    purpose: str
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def _r_confusion(world: World) -> list[str]:
    out: list[str] = []
    mist = world.entities.get("mist")
    if mist and mist.meters["confusion"] >= THRESHOLD:
        sig = ("confusion",)
        if sig not in world.fired:
            world.fired.add(sig)
            for eid in ("child", "helper"):
                if eid in world.entities:
                    world.get(eid).memes["unease"] += 1
            out.append("__confusion__")
    return out


def _r_clue(world: World) -> list[str]:
    out: list[str] = []
    clue = world.entities.get("clue")
    if clue and clue.meters["noticed"] >= THRESHOLD:
        sig = ("noticed",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("child").memes["hope"] += 1
            out.append("__noticed__")
    return out


CAUSAL_RULES = [_r_confusion, _r_clue]


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


def reasonableness_gate(mystery: Mystery, drunk: DrunkState) -> bool:
    return mystery.id in MYSTERIES and drunk.id in DRUNKS


def solveable(mystery: Mystery) -> bool:
    return mystery.id in SOLUTIONS


def predict(world: World, mystery: Mystery) -> dict:
    sim = world.copy()
    sim.get("clue").meters["noticed"] += 1
    propagate(sim, narrate=False)
    return {
        "noticed": sim.get("clue").meters["noticed"] >= THRESHOLD,
        "hope": sim.get("child").memes["hope"],
    }


def opening(world: World, setting: Setting, child: Entity, helper: Entity, mystery: Mystery) -> None:
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"On a bright vacation by the {setting.label}, {child.id} and {helper.id} "
        f"came with a small cart and a song in their steps. The {setting.mood} air "
        f"moved over the sand, and the {setting.tide} kept whispering at the shore."
    )
    world.say(
        f"They meant to rest like folk in an old tale, with fish for supper and "
        f"shells for keepsakes, but soon a little mystery came walking out of the sea."
    )
    world.say(
        f"A child had lost {mystery.missing}, and the only clue was {mystery.clue}."
    )


def drunken_mislead(world: World, helper: Entity, drunk: Entity, mystery: Mystery) -> None:
    helper.memes["worry"] += 1
    drunk.memes["confusion"] += 1
    world.say(
        f"Then along came {drunk.id}, a drunken {drunk.label_word} with a wobble in "
        f"{drunk.pronoun('possessive')} knees and a muddle in {drunk.pronoun('possessive')} tongue."
    )
    world.say(
        f'"{mystery.missing}?" {drunk.id} laughed. "{mystery.found_as} can be found '
        f"where the gulls go to sleep!"'
    )
    world.say(
        f"{helper.id} did not trust those words, for {mystery.folk_reason}."
    )


def notice_clue(world: World, child: Entity, clue: Entity, mystery: Mystery) -> None:
    clue.meters["noticed"] += 1
    child.memes["care"] += 1
    world.say(
        f"{child.id} bent down and saw {mystery.clue} where the tide had left it."
    )
    world.say(
        f"It was not a lie and not a trick, only a small thing that told a true tale."
    )


def solve(world: World, child: Entity, helper: Entity, mystery: Mystery, tool: Tool) -> None:
    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"With {tool.phrase}, {helper.id} brushed the sand aside and followed the clue "
        f"to the little place it pointed."
    )
    world.say(
        f"There, tucked behind a driftwood post, lay {mystery.found_as} all along."
    )
    world.say(
        f"{child.id} took it back with both hands, and the beach seemed to breathe easier."
    )


def ending(world: World, setting: Setting, child: Entity, helper: Entity, mystery: Mystery) -> None:
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"By sunset, the mystery was finished. The {setting.label} still shone, but now "
        f"{child.id} and {helper.id} had a story to carry home: {mystery.missing} was found, "
        f"the drunken chatter was harmless, and the sea kept its own secrets once more."
    )


def tell(setting: Setting, mystery: Mystery, drunk: DrunkState, tool: Tool,
         child_name: str = "Anya", child_gender: str = "girl",
         helper_name: str = "Mara", helper_gender: str = "woman") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    drunk_ent = world.add(Entity(id="Rook", kind="character", type="man", role="drunk"))
    clue = world.add(Entity(id="clue", type="thing", label=mystery.clue))
    mist = world.add(Entity(id="mist", type="thing", label="mist"))
    opening(world, setting, child, helper, mystery)
    world.para()
    drunken_mislead(world, helper, drunk_ent, mystery)
    world.para()
    notice_clue(world, child, clue, mystery)
    propagate(world, narrate=False)
    world.say(f"The clue led them to {mystery.location_hint}.")
    world.para()
    solve(world, child, helper, mystery, tool)
    world.para()
    ending(world, setting, child, helper, mystery)
    world.facts.update(
        setting=setting, mystery=mystery, drunk=drunk, tool=tool,
        child=child, helper=helper, clue=clue, mist=mist,
        solved=True, clue_noticed=True, drunk_present=True,
    )
    return world


SETTINGS = {
    "beach": Setting(id="beach", label="beach", mood="salt", tide="tidal water"),
    "cove": Setting(id="cove", label="cove", mood="briny", tide="small tide"),
    "harbor": Setting(id="harbor", label="harbor", mood="windy", tide="slow tide"),
}

MYSTERIES = {
    "lost_hat": Mystery(
        id="lost_hat",
        clue="a wet ribbon caught on a shell",
        missing="the fisher-child's red hat",
        found_as="the red hat",
        location_hint="a driftwood post near the gull tracks",
        folk_reason="the sea never hides a thing without leaving a sign",
        tags={"hat", "shell", "search"},
    ),
    "missing_key": Mystery(
        id="missing_key",
        clue="a brass glint in the sand",
        missing="the inn key",
        found_as="the inn key",
        location_hint="under a net beside the pier stones",
        folk_reason="metal sings to anyone who kneels and looks close",
        tags={"key", "sand", "search"},
    ),
    "borrowed_basket": Mystery(
        id="borrowed_basket",
        clue="a trail of apple peels",
        missing="the picnic basket",
        found_as="the picnic basket",
        location_hint="behind a bench by the beach path",
        folk_reason="where crumbs go, there a basket must soon follow",
        tags={"basket", "path", "search"},
    ),
}

DRUNKS = {
    "rook": DrunkState(
        id="Rook",
        label="old sailor",
        stumble="a stagger",
        muddle="a muddle",
        tags={"drunk", "sailor"},
    ),
    "miller": DrunkState(
        id="Miller",
        label="harbor miller",
        stumble="a wobble",
        muddle="a blur",
        tags={"drunk", "miller"},
    ),
}

TOOLS = {
    "lantern": Tool(
        id="lantern",
        label="lantern",
        phrase="a little brass lantern",
        purpose="light",
        tags={"light", "brass"},
    ),
    "net": Tool(
        id="net",
        label="net",
        phrase="a fishing net",
        purpose="lift",
        tags={"net", "lift"},
    ),
    "stick": Tool(
        id="stick",
        label="stick",
        phrase="a smooth stick",
        purpose="point",
        tags={"stick", "point"},
    ),
}

@dataclass
class StoryParams:
    setting: str
    mystery: str
    drunk: str
    tool: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
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
    StoryParams(setting="beach", mystery="lost_hat", drunk="rook", tool="lantern",
                child_name="Anya", child_gender="girl", helper_name="Mara", helper_gender="woman"),
    StoryParams(setting="cove", mystery="missing_key", drunk="miller", tool="net",
                child_name="Niko", child_gender="boy", helper_name="Edda", helper_gender="woman"),
    StoryParams(setting="harbor", mystery="borrowed_basket", drunk="rook", tool="stick",
                child_name="Lina", child_gender="girl", helper_name="Hollis", helper_gender="man"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for m in MYSTERIES:
            for d in DRUNKS:
                if reasonableness_gate(MYSTERIES[m], DRUNKS[d]) and solveable(MYSTERIES[m]):
                    combos.append((s, m, d))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk-tale beach mystery for a young child that uses the words "vacation", "drunken", and "beach".',
        f"Tell a warm seaside story where {f['child'].id} solves a small mystery while a drunken old sailor makes a muddled guess.",
        f"Write a gentle story about a vacation at the beach, a mistaken clue, and a careful child who finds the answer.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    m: Mystery = f["mystery"]
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    drunk: DrunkState = f["drunk"]
    answers = [
        QAItem(
            question="What was the story about?",
            answer=f"It was about a vacation at the beach and a small mystery that needed solving. {child.id} and {helper.id} worked carefully until the missing thing was found.",
        ),
        QAItem(
            question="Why did the drunken person not solve the mystery?",
            answer=f"{drunk.id} made a noisy guess, but it was only a muddle and not a true clue. {child.id} trusted the little sign left by the tide instead, and that led to the answer.",
        ),
        QAItem(
            question="How was the mystery solved?",
            answer=f"{child.id} noticed {m.clue} and {helper.id} used a lantern to follow it. That careful looking led them to {m.found_as} hidden where the clue had pointed.",
        ),
    ]
    return answers


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a lantern do?",
            answer="A lantern gives off a soft light so people can see in the dark without needing a fire.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a small sign that helps you figure something out. In a mystery, clues lead you toward the answer.",
        ),
        QAItem(
            question="Why do people go to the beach on vacation?",
            answer="People go on vacation to rest, play, and see new places. The beach is a sunny place where families can walk, look for shells, and enjoy the sea.",
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(x[0] for x in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
noticed_clue :- clue_notice.
solved :- noticed_clue, lantern.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("missing", mid, m.missing))
    for did in DRUNKS:
        lines.append(asp.fact("drunk", did))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    rc = 0
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
    try:
        sample = generate(resolve_params(argparse.Namespace(
            setting=None, mystery=None, drunk=None, tool=None,
            child_name=None, child_gender=None, helper_name=None, helper_gender=None
        ), random.Random(1)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: smoke test generated a non-empty story.")
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        rc = 1
    return rc


def explain_rejection(mystery: Mystery, drunk: DrunkState) -> str:
    return (
        f"(No story: this mystery/drunk pairing does not make a solid folk-tale puzzle. "
        f"Try a real missing object with a clear clue, and a drunken character who adds confusion "
        f"but not the answer.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale beach mystery world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--drunk", choices=DRUNKS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["woman", "man", "girl", "boy"])
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
    combos = valid_combos()
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    filtered = []
    for s, m, d in combos:
        if args.setting is not None and s != args.setting:
            continue
        if args.mystery is not None and m != args.mystery:
            continue
        if args.drunk is not None and d != args.drunk:
            continue
        filtered.append((s, m, d))
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    s, m, d = rng.choice(sorted(filtered))
    tool = args.tool or rng.choice(sorted(TOOLS))
    return StoryParams(
        setting=s,
        mystery=m,
        drunk=d,
        tool=tool,
        child_name=args.child_name or rng.choice(["Anya", "Niko", "Lina", "Ivo", "Mira"]),
        child_gender=args.child_gender or rng.choice(["girl", "boy"]),
        helper_name=args.helper_name or rng.choice(["Mara", "Hollis", "Edda", "Rin"]),
        helper_gender=args.helper_gender or rng.choice(["woman", "man", "girl", "boy"]),
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        mystery = MYSTERIES[params.mystery]
        drunk = DRUNKS[params.drunk]
        tool = TOOLS[params.tool]
    except KeyError as exc:
        raise StoryError(f"Unknown parameter: {exc.args[0]}") from exc
    if not reasonableness_gate(mystery, drunk):
        raise StoryError(explain_rejection(mystery, drunk))
    world = tell(setting, mystery, drunk, tool, params.child_name, params.child_gender,
                 params.helper_name, params.helper_gender)
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
        print(asp_program("", "#show valid/3."))
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
        i = 0
        seen: set[str] = set()
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
