#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/disturb_hope_confidence_inner_monologue_rhyming_story.py
=======================================================================================

A small storyworld about a child trying to keep a calm, hopeful rhythm while
a tiny disturbance threatens their confidence. The world is built around a
rhyming bedtime-style scene with inner monologue as a narrative instrument.

Premise
-------
A child is practicing a little rhyme for tomorrow. A small disturbance breaks
their focus, their hope dips, and their confidence wobbles. The child thinks
quietly to themself, makes a sensible fix, and finishes with a brighter image
than they started with.

This world keeps the scope small:
- one child
- one little task
- one disturbance
- one helpful response
- a complete ending that shows what changed

It supports the standard storyworld CLI:
- default run
- -n
- --all
- --seed
- --trace
- --qa
- --json
- --asp
- --verify
- --show-asp
"""

from __future__ import annotations

import argparse
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
HOPE_MIN = 1.0
CONFIDENCE_MIN = 1.0


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
class Setting:
    id: str
    place: str
    quiet: str
    rhyme_texture: str
    weather: str
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
class Task:
    id: str
    verb: str
    thing: str
    inner_voice: str
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
class Disturbance:
    id: str
    label: str
    source: str
    effect: str
    small: str
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
class Comfort:
    id: str
    label: str
    action: str
    result: str
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
        import copy

        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone
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
    "windowseat": Setting(
        id="windowseat",
        place="the window seat",
        quiet="the room was soft and still",
        rhyme_texture="moonlight made a silver seam on the floor",
        weather="night",
    ),
    "kitchen_table": Setting(
        id="kitchen_table",
        place="the kitchen table",
        quiet="the house was warm and humming low",
        rhyme_texture="a lamp laid a cozy glow on the wood",
        weather="evening",
    ),
    "porch": Setting(
        id="porch",
        place="the porch",
        quiet="the air was cool and thin",
        rhyme_texture="the dark held a sleepy hush beyond the rail",
        weather="night",
    ),
}

TASKS = {
    "recite": Task(
        id="recite",
        verb="recite",
        thing="a tiny rhyme",
        inner_voice="I can do this, line by line",
        ending_image="the rhyme landed like a soft small bell",
        tags={"rhyme", "voice"},
    ),
    "draw": Task(
        id="draw",
        verb="draw",
        thing="a starry picture",
        inner_voice="I can make the stars stay bright",
        ending_image="the paper shone with a brave little sky",
        tags={"drawing", "paper"},
    ),
    "sing": Task(
        id="sing",
        verb="sing",
        thing="a gentle tune",
        inner_voice="I can keep my tune clear and true",
        ending_image="the song floated out, warm and round",
        tags={"song", "voice"},
    ),
}

DISTURBANCES = {
    "noise": Disturbance(
        id="noise",
        label="a clatter from the hall",
        source="the hall",
        effect="broke the child's focus",
        small="just a brief clatter",
        tags={"noise", "focus"},
    ),
    "wind": Disturbance(
        id="wind",
        label="a cool gust at the window",
        source="the window",
        effect="stirred the page and the child's nerves",
        small="only a little rush of air",
        tags={"wind", "paper"},
    ),
    "shadow": Disturbance(
        id="shadow",
        label="a wobbling shadow on the wall",
        source="the wall",
        effect="made the room look strange for a moment",
        small="a harmless moving shape",
        tags={"shadow", "fear"},
    ),
}

COMFORTS = {
    "lamp": Comfort(
        id="lamp",
        label="the little lamp",
        action="turned it on",
        result="its warm light calmed the room",
        tags={"light", "calm"},
    ),
    "breath": Comfort(
        id="breath",
        label="a slow breath",
        action="took one slow breath",
        result="the child's thoughts settled into a steadier tune",
        tags={"calm", "breath"},
    ),
    "blanket": Comfort(
        id="blanket",
        label="the quilt",
        action="wrapped up in the quilt for a moment",
        result="the soft weight helped the child feel safe again",
        tags={"calm", "warmth"},
    ),
}


@dataclass
class StoryParams:
    setting: str
    task: str
    disturbance: str
    comfort: str
    child_name: str
    child_type: str
    parent_name: str
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


GIRL_NAMES = ["Mia", "Luna", "Nora", "Zoe", "Ivy", "Ruby", "Ella", "Maya"]
BOY_NAMES = ["Noah", "Theo", "Finn", "Leo", "Eli", "Max", "Owen", "Ben"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for tid, task in TASKS.items():
            for did, disturb in DISTURBANCES.items():
                for cid, comfort in COMFORTS.items():
                    if "paper" in task.tags and "wind" in disturb.tags and cid == "breath":
                        continue
                    combos.append((sid, tid, did, cid))
    return combos


def explain_rejection() -> str:
    return "(No story: this combination leaves no believable path from disturbance to recovery.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny rhyming storyworld with inner monologue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--disturbance", choices=DISTURBANCES)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.task is None or c[1] == args.task)
              and (args.disturbance is None or c[2] == args.disturbance)
              and (args.comfort is None or c[3] == args.comfort)]
    if not combos:
        raise StoryError(explain_rejection())
    setting, task, disturbance, comfort = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        setting=setting,
        task=task,
        disturbance=disturbance,
        comfort=comfort,
        child_name=name,
        child_type=gender,
        parent_name=parent,
    )


def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_type, role="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent_name, label="the parent"))
    setting = SETTINGS[params.setting]
    task = TASKS[params.task]
    disturbance = DISTURBANCES[params.disturbance]
    comfort = COMFORTS[params.comfort]

    child.memes["hope"] = 2.0
    child.memes["confidence"] = 2.0
    child.memes["focus"] = 2.0

    world.say(
        f"{child.id} sat at {setting.place}, and {setting.quiet}. "
        f"{setting.rhyme_texture}. {child.id} wanted to {task.verb} {task.thing}."
    )
    world.say(
        f'Inside {child.id}\'s head, a small thought softly grew: "{task.inner_voice}."'
    )
    world.para()
    child.memes["hope"] -= 1.0
    child.memes["confidence"] -= 1.0
    child.meters["disturbed"] += 1.0
    world.say(
        f"Then {disturbance.label} came drifting through, and {disturbance.effect}. "
        f"{child.id} frowned and thought, 'Oh no, I may lose my glow.'"
    )
    world.say(
        f"Another thought came next: 'But I am still here, and I still know how to go.'"
    )
    child.memes["hope"] += 1.0
    child.memes["confidence"] += 1.0

    world.para()
    if params.comfort == "lamp":
        child.meters["light"] += 1.0
    if params.comfort == "blanket":
        child.meters["warm"] += 1.0
    if params.comfort == "breath":
        child.memes["calm"] += 1.0
    world.say(
        f"{child.id} {comfort.action}, and {comfort.result}. "
        f"{child.id} thought, 'I can be brave. I can stay wise.'"
    )
    child.meters["settled"] += 1.0
    child.memes["hope"] += 1.0
    child.memes["confidence"] += 1.0
    world.say(
        f"So {child.id} kept going and did not hide. {task.ending_image}, "
        f"and {parent.label_word} smiled with pride."
    )
    world.say(
        f"In the end, {child.id} stood a little taller, with more hope in the heart "
        f"and more confidence in the song."
    )

    world.facts.update(
        child=child,
        parent=parent,
        setting=setting,
        task=task,
        disturbance=disturbance,
        comfort=comfort,
        outcome="steady",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a rhyming story for a child named {f['child'].id} who stays calm after {f['disturbance'].label}.",
        f"Tell a gentle inner-monologue story where {f['child'].id} thinks, 'I can be brave,' and keeps going with {f['task'].thing}.",
        f"Write a short rhyming story that includes the words disturb, hope, and confidence, and ends with a brighter feeling.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    task = f["task"]
    disturb = f["disturbance"]
    comfort = f["comfort"]
    return [
        QAItem(
            question=f"What happened that disturbed {child.id}?",
            answer=(
                f"{disturb.label} disturbed {child.id} and broke the little rhythm for a moment. "
                f"That is why {child.id} had to steady the mind before finishing."
            ),
        ),
        QAItem(
            question=f"What did {child.id} tell themself to keep going?",
            answer=(
                f"{child.id} thought, '{task.inner_voice}.' "
                f"That inner voice gave {child.id} hope first, then confidence to continue."
            ),
        ),
        QAItem(
            question="How did the comfort help?",
            answer=(
                f"{comfort.result}. "
                f"Because of that, the child could return to the task with a calmer heart and a steadier step."
            ),
        ),
        QAItem(
            question="How did the story end?",
            answer=(
                f"It ended with {child.id} finishing the task and standing a little taller. "
                f"The last image shows more hope and more confidence than at the start."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is hope?",
            answer="Hope is the feeling that something good can still happen, even after a hard moment.",
        ),
        QAItem(
            question="What is confidence?",
            answer="Confidence is the feeling that you can try, keep going, and do your best.",
        ),
        QAItem(
            question="What does it mean to disturb something?",
            answer="To disturb something means to break its calm or its smooth flow for a moment.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
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
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="windowseat", task="recite", disturbance="noise", comfort="lamp", child_name="Mia", child_type="girl", parent_name="mother"),
    StoryParams(setting="kitchen_table", task="draw", disturbance="shadow", comfort="breath", child_name="Theo", child_type="boy", parent_name="father"),
    StoryParams(setting="porch", task="sing", disturbance="wind", comfort="blanket", child_name="Luna", child_type="girl", parent_name="mother"),
]


ASP_RULES = r"""
setting(S) :- setting_fact(S).
task(T) :- task_fact(T).
disturbance(D) :- disturbance_fact(D).
comfort(C) :- comfort_fact(C).

valid(S,T,D,C) :- setting(S), task(T), disturbance(D), comfort(C), not blocked(S,T,D,C).
blocked(S,T,D,C) :- task_fact(T), disturbance_fact(D), comfort_fact(C), paper_task(T), wind_disturbance(D), comfort_fact(C), C = breath.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting_fact", sid))
    for tid in TASKS:
        lines.append(asp.fact("task_fact", tid))
    for did in DISTURBANCES:
        lines.append(asp.fact("disturbance_fact", did))
    for cid in COMFORTS:
        lines.append(asp.fact("comfort_fact", cid))
    lines.append(asp.fact("paper_task", "draw"))
    lines.append(asp.fact("wind_disturbance", "wind"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid-combos differ.")
        rc = 1
    else:
        print(f"OK: ASP and Python valid_combos() match ({len(valid_combos())} combos).")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(1)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        print(f"FAIL: generation smoke test crashed: {e}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.task not in TASKS or params.disturbance not in DISTURBANCES or params.comfort not in COMFORTS:
        raise StoryError("invalid params")
    world = tell(params)
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
