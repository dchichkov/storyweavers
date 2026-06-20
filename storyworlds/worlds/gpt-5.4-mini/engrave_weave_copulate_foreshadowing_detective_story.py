#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/engrave_weave_copulate_foreshadowing_detective_story.py
======================================================================================

A standalone storyworld for a tiny detective tale with foreshadowing, built from
the seed words "engrave", "weave", and "copulate" in a child-safe, mystery
domain.

Premise
-------
A child detective visits a little workshop-museum where a family heirloom went
missing. The clue trail includes an engraved nameplate, a woven ribbon, and a
pair of tiny puzzle charms that copulate in the old sense of "join together."
The story leans detective-like: clue, suspicion, reveal, and a tidy ending image
that proves what changed.

This world is intentionally small and constraint-driven:
- typed entities with physical meters and emotional memes
- state-driven prose, not a fixed paragraph template
- a Python reasonableness gate plus an inline ASP twin
- three Q&A sets grounded in world state
- foreshadowing via a visible clue that becomes meaningful later
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    atmosphere: str
    has_display_case: bool = False
    has_attic: bool = False

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Clue:
    id: str
    label: str
    line: str
    importance: int
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Suspect:
    id: str
    label: str
    motive: str
    honest: bool
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Solution:
    id: str
    label: str
    reveal: str
    fix: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.clues_seen: list[str] = []

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
        clone.clues_seen = list(self.clues_seen)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_nervousness(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["mystery"] < THRESHOLD:
            continue
        sig = ("nervous", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["curiosity"] += 1
        out.append("__narrate__")
    return out


def _r_relieved(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("case_solved") and not world.facts.get("relief_done"):
        world.facts["relief_done"] = True
        for e in list(world.entities.values()):
            if e.kind == "character":
                e.memes["relief"] += 1
        out.append("__narrate__")
    return out


CAUSAL_RULES = [
    Rule("nervousness", "social", _r_nervousness),
    Rule("relieved", "social", _r_relieved),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                produced.extend(g for g in got if g != "__narrate__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def clue_fires(world: World, clue: Clue) -> None:
    world.facts.setdefault("clues", []).append(clue.id)
    world.clues_seen.append(clue.id)
    world.get("case").meters["mystery"] += 1
    if clue.importance >= 2:
        world.get("detective").memes["curiosity"] += 1


def predict_case(world: World, clue: Clue) -> dict:
    sim = world.copy()
    clue_fires(sim, clue)
    return {
        "mystery": sim.get("case").meters["mystery"],
        "curiosity": sim.get("detective").memes["curiosity"],
    }


def setup(world: World, detective: Entity, partner: Entity, setting: Setting) -> None:
    world.say(
        f"On a gray afternoon, {detective.id} and {partner.id} stepped into "
        f"{setting.place}. {setting.atmosphere}"
    )
    detective.memes["confidence"] += 1
    partner.memes["confidence"] += 1


def mention_missing(world: World, item: Entity, detective: Entity) -> None:
    world.say(
        f"The museum guide pointed to an empty hook. {item.label} was missing, "
        f"and {detective.id} narrowed {detective.pronoun('possessive')} eyes."
    )


def foreshadow(world: World, clue: Clue) -> None:
    clue_fires(world, clue)
    if clue.id == "engraved_plate":
        world.say(
            f"Near the display, {clue.line}. {world.get('detective').id} noticed "
            f"it, but did not yet know why it mattered."
        )
    else:
        world.say(clue.line)


def question(world: World, detective: Entity, partner: Entity, suspect: Suspect) -> None:
    detective.memes["doubt"] += 1
    world.say(
        f'"Maybe {suspect.label} knows more than {they := partner.pronoun("subject")},'
        f'" {partner.id} whispered.'
    )
    world.say(
        f"{detective.id} looked again. The first clue had felt ordinary, but now it "
        f"seemed like a whisper from before the theft."
    )


def reveal(world: World, suspect: Suspect, solution: Solution) -> None:
    world.facts["case_solved"] = True
    world.say(
        f"At last, {suspect.label} smiled and showed the hidden spot. "
        f"{solution.reveal}"
    )
    world.say(
        f"It turned out the missing piece had never been stolen. {solution.fix}"
    )


def ending(world: World, detective: Entity, partner: Entity, item: Entity) -> None:
    detective.memes["joy"] += 1
    partner.memes["joy"] += 1
    world.say(
        f"By evening, {item.label} was back where it belonged, and the empty hook "
        f"was filled again. {detective.id} tucked the woven ribbon beside it, "
        f"and the engraved nameplate gleamed under the lamp."
    )
    world.say(
        f"{detective.id} smiled, because the clue that seemed small at first had "
        f"led them to the truth."
    )


def tell(setting: Setting, clue: Clue, suspect: Suspect, solution: Solution,
         detective_name: str = "Mina", partner_name: str = "Noah") -> World:
    world = World(setting)
    detective = world.add(Entity(id=detective_name, kind="character", type="girl", role="detective"))
    partner = world.add(Entity(id=partner_name, kind="character", type="boy", role="helper"))
    guide = world.add(Entity(id="Guide", kind="character", type="adult", role="guide"))
    item = world.add(Entity(id="Medal", kind="thing", type="thing", label="the medal"))
    case = world.add(Entity(id="case", kind="thing", type="thing", label="the case"))
    world.add(Entity(id="clueboard", kind="thing", type="thing", label="the clue board"))
    detective.memes["curiosity"] = 2.0
    partner.memes["curiosity"] = 1.0
    world.facts.update(detective=detective, partner=partner, guide=guide,
                       item=item, clue=clue, suspect=suspect, solution=solution,
                       setting=setting, case=case)

    setup(world, detective, partner, setting)
    mention_missing(world, item, detective)
    world.para()
    foreshadow(world, clue)
    world.say(
        f"{partner.id} pointed at the clue board. The tiny scratch on the brass "
        f"frame looked unimportant, but {detective.id} kept it in mind."
    )
    world.para()
    question(world, detective, partner, suspect)
    world.say(
        f"{detective.id} followed the ribbon trail, then checked the old chest. "
        f"The pieces there did not match by chance; they copulated, fitting together "
        f"like two parts of one old charm."
    )
    reveal(world, suspect, solution)
    world.para()
    ending(world, detective, partner, item)
    return world


SETTINGS = {
    "museum": Setting("museum", "The little museum smelled like dust, polish, and old paper.", has_display_case=True),
    "workshop": Setting("workshop", "The workshop had a warm lamp, a wooden bench, and neat drawers.", has_attic=True),
    "attic_room": Setting("attic_room", "The attic room creaked softly, and a rain ticked at the window.", has_attic=True),
}

CLUES = {
    "engraved_plate": Clue("engraved_plate", "an engraved brass plate", "The plate was engraved with a single initial", 3, {"engrave", "foreshadow"}),
    "woven_ribbon": Clue("woven_ribbon", "a woven ribbon", "A woven ribbon hung from the drawer handle", 2, {"weave", "foreshadow"}),
    "matched_marks": Clue("matched_marks", "matching marks", "Two little marks lined up like they belonged together", 2, {"copulate", "foreshadow"}),
}

SUSPECTS = {
    "cat": Suspect("cat", "the cat", "wanted a shiny place to nap", True, {"comedy"}),
    "assistant": Suspect("assistant", "the assistant", "was tidying the display", True, {"mystery"}),
    "wind": Suspect("wind", "the wind", "nudged things out of place", True, {"mystery"}),
}

SOLUTIONS = {
    "chest": Solution("chest", "the old chest", "Inside the chest sat the medal in a soft cloth wrap.", "the guide had tucked the medal away during cleanup, and the ribbon kept it from scratching.", {"solve"}),
    "drawer": Solution("drawer", "the drawer", "Behind the drawer runner was the medal, safe and sound.", "the piece had slid behind the drawer during a bump, and the ribbon made the drawer stick less.", {"solve"}),
    "case": Solution("case", "the display case", "Under the case rim, the medal was waiting with a tiny dust bunny.", "the medal had slipped under the case edge when the latch was opened.", {"solve"}),
}

NAMES_GIRL = ["Mina", "Luna", "Ivy", "Rosa", "Nora"]
NAMES_BOY = ["Noah", "Eli", "Jasper", "Theo", "Finn"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    clue: str
    suspect: str
    solution: str
    detective: str
    partner: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for c in CLUES:
            for sol in SOLUTIONS:
                combos.append((s, c, sol))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world with foreshadowing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("--detective")
    ap.add_argument("--partner")
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.clue is None or c[1] == args.clue)
              and (args.solution is None or c[2] == args.solution)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, solution = rng.choice(sorted(combos))
    detective = args.detective or rng.choice(NAMES_GIRL)
    partner = args.partner or rng.choice(NAMES_BOY)
    return StoryParams(setting, clue, args.suspect or "assistant", solution, detective, partner)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], CLUES[params.clue],
                 SUSPECTS[params.suspect], SOLUTIONS[params.solution],
                 params.detective, params.partner)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a detective story for a child that includes the word "engrave" and a clue about {f["clue"].label}.',
        f'Write a foreshadowing mystery where a small detail like {f["clue"].line.lower()} matters later.',
        f'Tell a short detective story using the words engrave, weave, and copulate, with a neat reveal at the end.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    clue = f["clue"]
    solution = f["solution"]
    item = f["item"]
    detective = f["detective"]
    partner = f["partner"]
    return [
        ("Who solved the mystery?",
         f"{detective.id} and {partner.id} solved it together by following the clues carefully."),
        ("What clue was foreshadowed early in the story?",
         f"The engraved plate was shown early, and later it became clear why it mattered. That was the clue that helped point the detectives in the right direction."),
        ("Where was the missing item found?",
         f"{solution.reveal} The final answer was found in {solution.label}, after the early clues had led the way."),
        ("What did the detectives do with the item at the end?",
         f"They put {item.label} back where it belonged, and the case was calm again. The ending showed the mystery was truly solved."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does it mean to engrave something?",
         "To engrave something means to cut or mark words or a design into a hard surface so they last a long time."),
        ("What does weave mean?",
         "To weave means to make cloth or a pattern by crossing pieces over and under each other."),
        ("What does copulate mean in this storyworld?",
         "Here it means to join together snugly, like two puzzle pieces or two parts of a charm fitting as one."),
        ("What is foreshadowing in a story?",
         "Foreshadowing is when a story gives a small clue early that helps the reader understand what will matter later."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("museum", "engraved_plate", "assistant", "chest", "Mina", "Noah"),
    StoryParams("workshop", "woven_ribbon", "wind", "drawer", "Luna", "Eli"),
    StoryParams("attic_room", "matched_marks", "cat", "case", "Ivy", "Theo"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("importance", cid, c.importance))
    for sid in SUSPECTS:
        lines.append(asp.fact("suspect", sid))
    for soid in SOLUTIONS:
        lines.append(asp.fact("solution", soid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, C, So) :- setting(S), clue(C), solution(So).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in gate.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        assert sample.story
        print("OK: smoke test generate() produced a story.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


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
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for row in combos:
            print(" ", row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
            i += 1
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def story_knowledge_placeholder() -> None:
    return


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does engrave mean?",
         "To engrave means to carve words or pictures into a hard surface."),
        ("What does weave mean?",
         "To weave means to cross threads or strips over and under each other to make something strong or patterned."),
        ("What does copulate mean here?",
         "Here it means to fit or join together snugly, like matching parts of a clue box."),
        ("What is foreshadowing?",
         "Foreshadowing is a clue placed early in a story that hints at something important later."),
    ]


if __name__ == "__main__":
    main()
