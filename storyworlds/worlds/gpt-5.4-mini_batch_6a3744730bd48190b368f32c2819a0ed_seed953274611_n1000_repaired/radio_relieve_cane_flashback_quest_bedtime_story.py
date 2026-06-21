#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/radio_relieve_cane_flashback_quest_bedtime_story.py
===================================================================================

A small bedtime-story world about a child, a crackly radio, a walking cane, a
flashback, and a quest to relieve a worried feeling.

Premise
-------
A child hears a radio message about a lost bedtime song. They take a tiny quest
through a quiet house to find what will help a tired grandparent feel better.
Along the way, a flashback reminds them why the cane matters, and the ending
proves what changed: the radio is found, the grandparent is relieved, and the
bedtime room grows calm.

Seed words: radio, relieve, cane
Features: Flashback, Quest
Style: Bedtime Story

This script follows the Storyweavers contract:
- stdlib-only script
- imports storyworlds/results eagerly
- imports storyworlds/asp lazily inside ASP helpers
- defines StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
QUIET_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: {"distance": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"worry": 0.0})

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother"}
        male = {"boy", "father", "dad", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
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
class Thing:
    id: str
    label: str
    phrase: str
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))


@dataclass
class Place:
    id: str
    label: str
    quiet: bool = True
    can_hold: set[str] = field(default_factory=set)
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
class QuestItem:
    id: str
    label: str
    phrase: str
    need: str
    reward: str
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
class Relief:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.memes.get("worry", 0.0) >= THRESHOLD and ("worry", e.id) not in world.fired:
            world.fired.add(("worry", e.id))
            out.append("__worry__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
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


CAUSAL_RULES = [Rule("worry", _r_worry)]


@dataclass
class StoryParams:
    place: str
    radio: str
    cane: str
    quest: str
    flashback: str
    child_name: str
    child_gender: str
    elder_name: str
    elder_gender: str
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
    "hall": Place(id="hall", label="the hallway", quiet=True, can_hold={"radio", "cane", "quest"}),
    "bedroom": Place(id="bedroom", label="the bedroom", quiet=True, can_hold={"radio", "cane", "quest"}),
    "porch": Place(id="porch", label="the porch", quiet=True, can_hold={"radio", "cane", "quest"}),
}

RADIOS = {
    "radio": Thing(id="radio", label="radio", phrase="a little radio with a round knob", tags={"radio"}),
    "toy_radio": Thing(id="toy_radio", label="toy radio", phrase="a toy radio with a silver antenna", tags={"radio"}),
}

CANES = {
    "cane": Thing(id="cane", label="cane", phrase="a smooth wooden cane", tags={"cane"}),
    "walking_cane": Thing(id="walking_cane", label="walking cane", phrase="a sturdy walking cane", tags={"cane"}),
}

QUESTS = {
    "find_song": QuestItem(id="find_song", label="bedtime song", phrase="a bedtime song hidden by the quiet house", need="song", reward="relief"),
    "find_music": QuestItem(id="find_music", label="missing tune", phrase="a missing tune for sleep", need="music", reward="relief"),
}

FLASHBACKS = {
    "remember_help": QuestItem(id="remember_help", label="helpful memory", phrase="a flashback about helping someone walk slowly and safely", need="memory", reward="care"),
    "remember_lullaby": QuestItem(id="remember_lullaby", label="lullaby memory", phrase="a flashback about a lullaby hummed beside a bed", need="memory", reward="calm"),
}

RELIEVES = {
    "turn_dial": Relief(id="turn_dial", sense=3, power=3, text="turned the radio dial until the music came back as a soft sleepy hum", fail="turned the radio dial, but only got a hiss of static", qa_text="turned the radio dial until the music came back", tags={"radio"}),
    "press_button": Relief(id="press_button", sense=2, power=2, text="pressed the little button and coaxed the radio into a warm whisper of sound", fail="pressed the little button, but the radio stayed quiet", qa_text="pressed the button and coaxed the radio into sound", tags={"radio"}),
}

CHILD_NAMES = ["Mia", "Lily", "Noah", "Ben", "Ava", "Finn"]
ELDER_NAMES = ["Grandma", "Grandpa", "Nana", "Papa"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for p in PLACES:
        for r in RADIOS:
            for c in CANES:
                for q in QUESTS:
                    out.append((p, r, c, q))
    return out


def reasonableness_ok(params: StoryParams) -> bool:
    return params.place in PLACES and params.radio in RADIOS and params.cane in CANES and params.quest in QUESTS and params.flashback in FLASHBACKS


def quiet_warning(place: Place, quest: QuestItem) -> bool:
    return place.quiet and quest.need in {"song", "music", "memory"}


def render_flashback(child: Entity, elder: Entity, cane: Thing, flashback: QuestItem) -> str:
    return (
        f"Then {child.id} remembered something from before: "
        f"{flashback.phrase}. The cane had tapped the floor in a gentle rhythm, "
        f"and {elder.id} had smiled because slow steps are still good steps."
    )


def do_relieve(world: World, radio: Entity, relief: Relief) -> None:
    radio.memes["hope"] = radio.memes.get("hope", 0.0) + 1
    world.say(
        f"{relief.text.capitalize()}."
    )


def complete_quest(world: World, child: Entity, elder: Entity, quest: QuestItem, place: Place, radio: Thing, cane: Thing) -> None:
    elder.memes["worry"] = 0.0
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1
    world.say(
        f"Together they found {radio.phrase} on a shelf near {place.label}, and the song filled the room like a blanket."
    )
    world.say(
        f"{elder.id} leaned on the {cane.label} and sighed with relief. "
        f"Their tired face looked softer right away."
    )
    world.say(
        f"The bedtime quest was done, and the house felt quiet in the best way."
    )


def tell(place: Place, radio: Thing, cane: Thing, quest: QuestItem, flashback: QuestItem,
         child_name: str = "Mia", child_gender: str = "girl",
         elder_name: str = "Grandma", elder_gender: str = "grandmother",
         relief: Relief = RELIEVES["turn_dial"]) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_gender, role="elder"))
    radio_ent = world.add(Entity(id="radio", kind="thing", type="thing", label=radio.label))
    cane_ent = world.add(Entity(id="cane", kind="thing", type="thing", label=cane.label))

    elder.memes["worry"] = 1.0
    world.say(
        f"At bedtime, {child.id} heard a crackly radio whisper from {place.label}. "
        f"{elder.id} sat nearby with {cane.label} resting beside {elder.pronoun('object')}."
    )
    world.say(
        f"\"We need the little song,\" {child.id} said softly, and began a tiny quest through the quiet room."
    )
    world.para()
    world.say(render_flashback(child, elder, cane, flashback))
    world.say(
        f"That memory made {child.id} brave and careful at the same time."
    )
    world.para()
    do_relieve(world, radio_ent, relief)
    complete_quest(world, child, elder, quest, place, radio, cane)
    world.facts.update(
        child=child, elder=elder, place=place, radio=radio, cane=cane, quest=quest,
        flashback=flashback, relief=relief, outcome="relieved"
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story that includes the words "{f["radio"].label}", "{f["cane"].label}", and a gentle quest.',
        f"Tell a calm story where {f['child'].id} searches for a radio song to help {f['elder'].id} feel better, and a flashback about the cane matters.",
        f'Write a bedtime story with a flashback and a quest, ending with relief and a quiet room.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and {elder.id}. The child takes a little bedtime quest to help the elder feel better."),
        ("Why did the child go on a quest?",
         f"{child.id} wanted to find the radio song so {elder.id} could relax. The quest was a gentle way to bring comfort back to the room."),
        ("What did the flashback show?",
         f"It showed a memory about the cane and slow, careful steps. That memory helped {child.id} remember how to move kindly and quietly."),
        ("How did the story end?",
         f"It ended with relief. The radio sang again, {elder.id} looked less worried, and the bedtime room became calm and cozy."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a radio?",
         "A radio is a little machine that can bring voices and music into a room. People turn a knob or press a button to hear it."),
        ("What is a cane for?",
         "A cane helps someone walk with steadier steps. It can give support and make moving around easier."),
        ("What is a flashback?",
         "A flashback is when a story briefly remembers something from before. It helps explain why a character feels or acts a certain way."),
        ("What is a quest?",
         "A quest is a small mission or search for something important. In a bedtime story, it can be gentle and cozy instead of scary."),
        ("What does relieve mean?",
         "To relieve someone is to make a worry, pain, or heavy feeling smaller. Relief feels like a deep breath after a hard moment."),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="hall", radio="radio", cane="cane", quest="find_song", flashback="remember_help", child_name="Mia", child_gender="girl", elder_name="Grandma", elder_gender="grandmother"),
    StoryParams(place="bedroom", radio="toy_radio", cane="walking_cane", quest="find_music", flashback="remember_lullaby", child_name="Noah", child_gender="boy", elder_name="Grandpa", elder_gender="grandfather"),
]


def explain_rejection() -> str:
    return "(No story: the chosen pieces do not make a gentle bedtime quest.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world: radio, relieve, cane, flashback, quest.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--radio", choices=RADIOS)
    ap.add_argument("--cane", choices=CANES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--flashback", choices=FLASHBACKS)
    ap.add_argument("--name", dest="child_name")
    ap.add_argument("--gender", dest="child_gender", choices=["girl", "boy"])
    ap.add_argument("--elder", dest="elder_name")
    ap.add_argument("--elder-gender", dest="elder_gender", choices=["grandmother", "grandfather"])
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
    if args.place and args.place not in PLACES:
        raise StoryError(explain_rejection())
    keys = [k for k in valid_combos()
            if (args.place is None or k[0] == args.place)
            and (args.radio is None or k[1] == args.radio)
            and (args.cane is None or k[2] == args.cane)
            and (args.quest is None or k[3] == args.quest)]
    if not keys:
        raise StoryError(explain_rejection())
    place, radio, cane, quest = rng.choice(keys)
    flashback = args.flashback or rng.choice(list(FLASHBACKS))
    return StoryParams(
        place=place, radio=radio, cane=cane, quest=quest, flashback=flashback,
        child_name=args.child_name or rng.choice(CHILD_NAMES),
        child_gender=args.child_gender or rng.choice(["girl", "boy"]),
        elder_name=args.elder_name or rng.choice(ELDER_NAMES),
        elder_gender=args.elder_gender or rng.choice(["grandmother", "grandfather"]),
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.radio not in RADIOS or params.cane not in CANES or params.quest not in QUESTS or params.flashback not in FLASHBACKS:
        raise StoryError("(Invalid params for this bedtime story world.)")
    world = tell(PLACES[params.place], RADIOS[params.radio], CANES[params.cane], QUESTS[params.quest], FLASHBACKS[params.flashback], params.child_name, params.child_gender, params.elder_name, params.elder_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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


ASP_RULES = r"""
chosen_place(P) :- place(P).
chosen_radio(R) :- radio(R).
chosen_cane(C) :- cane(C).
chosen_quest(Q) :- quest(Q).
bedtime_story :- chosen_place(_), chosen_radio(_), chosen_cane(_), chosen_quest(_).

need_relief(E) :- elder(E).
flashback_help(F) :- flashback(F).
questable(Q) :- quest(Q), need(song).
quiet_place(P) :- place(P), quiet(P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.quiet:
            lines.append(asp.fact("quiet", pid))
    for rid in RADIOS:
        lines.append(asp.fact("radio", rid))
    for cid in CANES:
        lines.append(asp.fact("cane", cid))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("need", qid, q.need))
    for fid in FLASHBACKS:
        lines.append(asp.fact("flashback", fid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show bedtime_story/0."))
    return ["ok"] if any(sym.name == "bedtime_story" for sym in model) else []


def asp_verify() -> int:
    rc = 0
    try:
        sample = generate(CURATED[0])
        if not sample.story:
            raise RuntimeError("empty story")
    except Exception as e:
        print(f"FAIL: generate smoke test crashed: {e}")
        return 1
    if not reasonableness_ok(CURATED[0]):
        print("FAIL: curated params invalid")
        rc = 1
    if asp_valid_combos() != ["ok"]:
        print("FAIL: ASP twin did not validate a simple bedtime story")
        rc = 1
    print("OK: generate smoke test passed.")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show bedtime_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ok" if asp_valid_combos() else "no story")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))
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
