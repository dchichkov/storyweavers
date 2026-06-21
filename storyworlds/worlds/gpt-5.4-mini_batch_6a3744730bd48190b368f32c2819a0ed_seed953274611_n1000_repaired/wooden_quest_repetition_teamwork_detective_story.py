#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/wooden_quest_repetition_teamwork_detective_story.py
===================================================================================

A tiny storyworld for a detective-style quest with repetition and teamwork.

Premise
-------
A child detective team follows repeated clues through a small neighborhood to
recover a missing wooden keybox. They search, compare notes, work together, and
find the box in the end.

The world is intentionally small and state-driven:
- typed entities with physical meters and emotional memes
- clue repetition that raises certainty
- teamwork that helps solve the case
- a clear ending image proving what changed

The story stays child-facing and concrete, but keeps the feel of a simple
detective mystery: noticing clues, checking them again, and solving the case
together.

Run
---
    python storyworlds/worlds/gpt-5.4-mini/wooden_quest_repetition_teamwork_detective_story.py
    python storyworlds/worlds/gpt-5.4-mini/wooden_quest_repetition_teamwork_detective_story.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/wooden_quest_repetition_teamwork_detective_story.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
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
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    clue_places: list[str]
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
class Case:
    id: str
    title: str
    object_name: str
    object_phrase: str
    object_material: str
    missing_note: str
    location_hint: str
    repeated_clues: tuple[str, str, str]
    ending_image: str
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
    helpful: bool = True
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


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


def _r_repeat(world: World) -> list[str]:
    out: list[str] = []
    case = world.facts.get("case")
    if not case:
        return out
    for detective in world.characters():
        if detective.role != "detective":
            continue
        if detective.meters["clues"] < THRESHOLD:
            continue
        sig = ("repeat", detective.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        detective.memes["certainty"] += 1
        out.append("The clue made the answer feel closer.")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    team = [e for e in world.characters() if e.role in {"detective", "helper"}]
    if not team:
        return out
    if all(e.memes["shared_plan"] >= THRESHOLD for e in team):
        sig = ("teamwork",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        for e in team:
            e.memes["hope"] += 1
        out.append("Together, they felt ready to solve it.")
    return out


CAUSAL_RULES = [Rule("repeat", _r_repeat), Rule("teamwork", _r_teamwork)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting_id in SETTINGS:
        for case_id, case in CASES.items():
            for tool_id, tool in TOOLS.items():
                if tool.helpful and case.object_material == "wooden":
                    combos.append((setting_id, case_id, tool_id))
    return combos


def clue_strength(case: Case, repeats: int) -> int:
    return repeats + (1 if "wooden" in case.tags else 0)


def solved(case: Case, repeats: int, teamwork: bool) -> bool:
    return clue_strength(case, repeats) >= 3 and teamwork


def tell(setting: Setting, case: Case, tool: Tool, detective_name: str,
         helper_name: str, parent_name: str) -> World:
    world = World()
    d = world.add(Entity(id=detective_name, kind="character", type="boy", role="detective",
                         attrs={"home": setting.place}, tags={"detective"}))
    h = world.add(Entity(id=helper_name, kind="character", type="girl", role="helper",
                         attrs={"home": setting.place}, tags={"helper"}))
    p = world.add(Entity(id=parent_name, kind="character", type="mother", role="parent",
                         label="the parent", attrs={"home": setting.place}))
    clue = world.add(Entity(id="clue", type="thing", label=case.object_name,
                            attrs={"material": case.object_material}, tags=set(case.tags)))
    box = world.add(Entity(id="box", type="thing", label=case.object_phrase,
                           attrs={"material": case.object_material}, tags={"wooden"}))
    world.facts["case"] = case

    d.memes["curiosity"] += 1
    h.memes["curiosity"] += 1
    d.memes["shared_plan"] += 1
    h.memes["shared_plan"] += 1

    world.say(
        f"In the quiet little town, {d.id} and {h.id} were playing detective. "
        f"They had a quest: find the missing {case.object_name}."
    )
    world.say(
        f"{case.missing_note} {setting.mood.capitalize()} fit the case, and a "
        f"{case.object_material} clue had been spotted nearby."
    )
    world.say(
        f'{d.id} tapped the notebook. "{case.repeated_clues[0]}"'
    )
    world.say(
        f'{h.id} checked the note again. "{case.repeated_clues[1]}"'
    )
    world.say(
        f'They compared the clues one more time. "{case.repeated_clues[2]}"'
    )
    d.meters["clues"] += 1
    h.meters["clues"] += 1
    propagate(world)

    world.para()
    world.say(
        f'{p.id} listened, smiled, and pointed toward {case.location_hint}. '
        f'"That sounds like a job for teamwork," {p.pronoun()} said.'
    )
    world.say(
        f'{d.id} and {h.id} followed the hint together, holding the notebook and '
        f'the little tool {tool.phrase} close.'
    )

    if solved(case, 3, True):
        d.memes["joy"] += 1
        h.memes["joy"] += 1
        box.meters["found"] += 1
        clue.meters["used"] += 1
        world.para()
        world.say(
            f'At last, behind the old bench, they found the {case.object_phrase}. '
            f'It was right where the clues had promised.'
        )
        world.say(
            f'The {case.object_phrase} was safely back in place, and {d.id} and {h.id} '
            f'beamed at each other like real detectives.'
        )
    else:
        world.para()
        world.say(
            f'They searched hard, but the case stayed confusing. Still, they kept '
            f'working together, because a good quest is easier with two brave minds.'
        )

    world.facts.update(
        detective=d, helper=h, parent=p, clue=clue, box=box, setting=setting,
        tool=tool, repeats=3, teamwork=True, solved=solved(case, 3, True),
        ending=case.ending_image,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    case = f["case"]
    return [
        f'Write a detective story for a child that includes the word "{case.object_material}" and shows a small quest, repetition, and teamwork.',
        f"Tell a story where two child detectives repeat clues, work together, and recover a missing {case.object_material} object.",
        f"Write a simple mystery with a wooden clue, repeated checking, and a happy teamwork ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    case = f["case"]
    d = f["detective"]
    h = f["helper"]
    p = f["parent"]
    return [
        QAItem(
            question="What was the quest in the story?",
            answer=f"The quest was to find the missing {case.object_name}. They followed clues, checked them again, and kept going until the answer became clear."
        ),
        QAItem(
            question="Why did they repeat the clues?",
            answer="They repeated the clues to make sure they were not guessing. Each repetition made the answer feel more certain, and that helped them stay on the right track."
        ),
        QAItem(
            question="How did teamwork help?",
            answer=f"{d.id} and {h.id} both looked, listened, and compared notes. Their teamwork let them follow the hint together and finish the quest."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with the {case.object_phrase} found and put safely back. The detectives stood together, proud and smiling, with the case solved."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a detective?",
            answer="A detective is someone who looks carefully for clues and tries to solve a mystery."
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and work together toward the same goal."
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a search for something important. It usually has a goal, clues, and a journey to finish."
        ),
        QAItem(
            question="Why do people check clues more than once?",
            answer="They check clues more than once so they can be sure they understood them correctly. Repeating a clue can make a pattern easier to notice."
        ),
        QAItem(
            question="What can wooden objects be like?",
            answer="Wooden objects are made from wood. Wood is sturdy, warm-looking, and can be carved into boxes, toys, and tools."
        ),
    ]


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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(x[0] for x in world.fired if x)}")
    return "\n".join(lines)


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CASES:
        lines.append(asp.fact("case", cid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if t.helpful:
            lines.append(asp.fact("helpful", tid))
    lines.append(asp.fact("required_repeats", 3))
    lines.append(asp.fact("teamwork_needed"))
    lines.append(asp.fact("material", "wooden"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,C,T) :- setting(S), case(C), tool(T), helpful(T).
solved(C) :- case(C), material(wooden), required_repeats(3), teamwork_needed.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = True
    if set(asp_valid_combos()) != set(valid_combos()):
        ok = False
        print("MISMATCH: ASP gate differs from Python gate")
    try:
        sample = generate(resolve_params(argparse.Namespace(
            setting=None, case=None, tool=None, seed=None, all=False, trace=False,
            qa=False, json=False, asp=False, verify=False, show_asp=False, n=1
        ), random.Random(7)))
        _ = sample.story
    except Exception as exc:
        ok = False
        print(f"MISMATCH: smoke test failed: {exc}")
    if ok:
        print("OK: ASP parity and story smoke test passed.")
        return 0
    return 1


@dataclass
class StoryParams:
    setting: str
    case: str
    tool: str
    detective_name: str = "Nia"
    helper_name: str = "Jules"
    parent_name: str = "Parent"
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


SETTINGS = {
    "square": Setting(id="square", place="the little square", mood="the square felt calm", clue_places=["bench", "fountain", "lamp post"]),
    "alley": Setting(id="alley", place="the narrow alley", mood="the alley felt hush-quiet", clue_places=["gate", "wall", "crate"]),
    "library": Setting(id="library", place="the old library", mood="the library felt whisper-soft", clue_places=["desk", "shelf", "window"]),
}

CASES = {
    "box": Case(
        id="box",
        title="The Missing Wooden Box",
        object_name="wooden keybox",
        object_phrase="wooden keybox",
        object_material="wooden",
        missing_note="A small note on the wall said the box was missing.",
        location_hint="the bench by the fountain",
        repeated_clues=("The box was wooden.", "The box was wooden.", "The box was wooden, so it might be nearby."),
        ending_image="the wooden keybox sitting safely on the bench",
        tags={"wooden", "quest"},
    ),
    "toy": Case(
        id="toy",
        title="The Wooden Toy Case",
        object_name="wooden toy",
        object_phrase="wooden toy",
        object_material="wooden",
        missing_note="A tag on the shelf said the toy had gone missing.",
        location_hint="the crate beside the gate",
        repeated_clues=("It was wooden.", "It was wooden.", "It was wooden, so it should be easy to spot."),
        ending_image="the wooden toy resting back in the basket",
        tags={"wooden", "quest"},
    ),
}

TOOLS = {
    "notebook": Tool(id="notebook", label="notebook", phrase="a small notebook", helpful=True, tags={"teamwork"}),
    "lamp": Tool(id="lamp", label="lamp", phrase="a bright lamp", helpful=True, tags={"wooden"}),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective quest world with repetition and teamwork.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--tool", choices=TOOLS)
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
              and (args.case is None or c[1] == args.case)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, case, tool = rng.choice(sorted(combos))
    return StoryParams(setting=setting, case=case, tool=tool)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.case not in CASES or params.tool not in TOOLS:
        raise StoryError("Invalid story parameters.")
    world = tell(SETTINGS[params.setting], CASES[params.case], TOOLS[params.tool],
                 params.detective_name, params.helper_name, params.parent_name)
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
    StoryParams(setting="square", case="box", tool="notebook", detective_name="Nia", helper_name="Jules", parent_name="Parent"),
    StoryParams(setting="library", case="toy", tool="lamp", detective_name="Milo", helper_name="Ada", parent_name="Parent"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
