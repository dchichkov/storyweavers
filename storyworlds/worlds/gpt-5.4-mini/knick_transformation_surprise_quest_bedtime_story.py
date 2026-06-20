#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/knick_transformation_surprise_quest_bedtime_story.py
====================================================================================

A small bedtime story world about a child, a tiny quest, a surprise, and a gentle
transformation. The seed word "knick" is kept in the world as a little knick-knack
token, and the story grows from a child searching for a missing bedtime treasure
into a calm, magical ending image.

The world model uses typed entities with physical meters and emotional memes,
a compact causal engine, a reasonableness gate, and an inline ASP twin.
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
SENSE_MIN = 2


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

    tags: set[str] = field(default_factory=set)

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
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Place:
    id: str
    label: str
    dark: str
    calm: str
    keepsake_spot: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class QuestItem:
    id: str
    label: str
    phrase: str
    hidden_by: str
    surprise: str
    transform_into: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Tool:
    id: str
    label: str
    phrase: str
    can_transform: bool = False
    can_reveal: bool = False
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Surprise:
    id: str
    label: str
    reveal: str
    reward: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


def _r_tuck(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes["sleepy"] >= THRESHOLD and "blanket" in world.entities:
        blanket = world.get("blanket")
        if blanket.meters["glow"] >= THRESHOLD and ("tuck", blanket.id) not in world.fired:
            world.fired.add(("tuck", blanket.id))
            blanket.meters["warm"] += 1
            child.memes["calm"] += 1
            out.append("__tuck__")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    quest = world.get("quest")
    if quest.meters["found"] < THRESHOLD:
        return out
    if ("transform", quest.id) in world.fired:
        return out
    world.fired.add(("transform", quest.id))
    quest.meters["found"] += 1
    quest.meters["changed"] += 1
    world.get("child").memes["wonder"] += 1
    out.append("__transform__")
    return out


CAUSAL_RULES = [Rule("tuck", "comfort", _r_tuck), Rule("transform", "magic", _r_transform)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend([b for b in bits if not b.startswith("__")])
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def quest_can_happen(place: Place, quest: QuestItem) -> bool:
    return True


def sensible_tools() -> list[Tool]:
    return [t for t in TOOLS.values() if t.id != "moonbeam" or t.can_transform]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid in PLACES:
        for qid, q in QUESTS.items():
            for sid, s in SURPRISES.items():
                if quest_can_happen(PLACES[pid], q) and q.hidden_by == s.id:
                    combos.append((pid, qid, sid))
    return combos


def surprise_ok(surprise: Surprise) -> bool:
    return True


def reasonableness_gate(quest: QuestItem, surprise: Surprise) -> bool:
    return quest.hidden_by == surprise.id and surprise_ok(surprise)


def _do_search(world: World, child: Entity, quest: QuestItem, surprise: Surprise) -> None:
    child.memes["hope"] += 1
    quest_ent = world.get("quest")
    quest_ent.meters["found"] += 1
    quest_ent.meters["hidden"] += 1
    if "knick" in world.entities:
        world.get("knick").meters["shine"] += 1
    propagate(world, narrate=False)


def predict_story(world: World, quest: QuestItem, surprise: Surprise) -> dict:
    sim = world.copy()
    _do_search(sim, sim.get("child"), quest, surprise)
    return {"found": sim.get("quest").meters["found"] >= THRESHOLD,
            "wonder": sim.get("child").memes["wonder"]}


def start(world: World, child: Entity, bedtime: bool) -> None:
    world.say(
        f"It was bedtime in {world.place.label}, and {child.id} felt sleepy but not quite ready to drift off."
    )
    if bedtime:
        world.say(
            f"{child.id} looked at {world.place.calm} and hugged {child.pronoun('possessive')} blanket close."
        )


def quest_beat(world: World, child: Entity, quest: QuestItem) -> None:
    child.memes["curious"] += 1
    world.say(
        f"Then {child.id} noticed a tiny missing {quest.label}, the little {quest.phrase}, and started a quiet quest to find it."
    )
    world.say(
        f"It had been tucked near {world.place.keepsake_spot}, where the night shadows made everything feel a little mysterious."
    )


def surprise_beat(world: World, child: Entity, quest: QuestItem, surprise: Surprise) -> None:
    pred = predict_story(world, quest, surprise)
    world.facts["predicted"] = pred
    world.say(
        f"{child.id} searched under the pillow, beside the bed, and behind the curtain."
    )
    world.say(
        f"At last, {child.id} found it hidden where {quest.hidden_by.replace('_', ' ')}."
    )
    if pred["found"]:
        world.say(
            f"That was when the surprise began: {surprise.reveal}, and the little quest turned into {quest.transform_into}."
        )


def transform_beat(world: World, child: Entity, quest: QuestItem, tool: Tool, surprise: Surprise) -> None:
    child.memes["wonder"] += 1
    quest_ent = world.get("quest")
    quest_ent.meters["transformed"] += 1
    world.say(
        f"{tool.label_word if hasattr(tool, 'label_word') else tool.label} helped, and the {quest.label} shimmered softly."
    )
    world.say(
        f"It changed into {quest.transform_into}, {surprise.reward}, as if the bedtime room had breathed out a tiny moonlit spell."
    )


def ending(world: World, child: Entity, quest: QuestItem) -> None:
    child.memes["calm"] += 1
    child.memes["love"] += 1
    world.say(
        f"{child.id} tucked the new {quest.transform_into} close and smiled, ready to sleep."
    )
    world.say(
        f"In the hush of {world.place.label}, the ordinary little knick had become something marvelous, and the room felt gentle again."
    )


def tell(place: Place, quest: QuestItem, surprise: Surprise, tool: Tool) -> World:
    world = World(place)
    child = world.add(Entity(id="child", kind="character", type="girl", role="seeker", traits=["gentle"]))
    parent = world.add(Entity(id="parent", kind="character", type="mother", role="helper", label="the parent"))
    quest_ent = world.add(Entity(id="quest", type="thing", label=quest.label))
    knick = world.add(Entity(id="knick", type="thing", label="knick", role="keepsake"))
    blanket = world.add(Entity(id="blanket", type="thing", label="blanket"))
    blanket.meters["glow"] = 1.0
    child.memes["sleepy"] = 1.0
    start(world, child, True)
    world.para()
    quest_beat(world, child, quest)
    surprise_beat(world, child, quest, surprise)
    world.para()
    transform_beat(world, child, quest, tool, surprise)
    ending(world, child, quest)
    world.facts.update(child=child, parent=parent, quest=quest_ent, quest_cfg=quest,
                       surprise=surprise, tool=tool, place=place, knick=knick)
    return world


PLACES = {
    "nursery": Place("nursery", "the nursery", "the dark corner by the window", "soft lamplight", "the bedside drawer"),
    "attic": Place("attic", "the attic room", "the quiet trunk under the eaves", "warm quilt light", "the old music box"),
    "cabin": Place("cabin", "the little cabin", "the shelf above the bed", "firelight and hush", "the rocking chair"),
}

QUESTS = {
    "knick": QuestItem("knick", "knick", "little knick-knack", "surprise_box", "a soft surprise", "a moon charm", {"knick", "quest"}),
    "star": QuestItem("star", "star", "tiny star token", "pillow", "a sleep surprise", "a star pendant", {"quest"}),
    "shell": QuestItem("shell", "shell", "small seashell charm", "sock", "a hidden surprise", "a pearl charm", {"quest"}),
}

SURPRISES = {
    "surprise_box": Surprise("surprise_box", "surprise box", "the box opened with a whisper", "and there was a gentle glow inside", {"surprise"}),
    "pillow": Surprise("pillow", "pillow pocket", "the pillow gave a tiny bump", "and out came a sparkling ribbon", {"surprise"}),
    "sock": Surprise("sock", "bed sock", "the sock twitched", "and a silver button rolled out", {"surprise"}),
}

TOOLS = {
    "moonbeam": Tool("moonbeam", "moonbeam", "a moonbeam", can_transform=True, can_reveal=True, tags={"magic"}),
    "lamp": Tool("lamp", "lamp", "a small lamp", can_reveal=True, tags={"light"}),
}

GENTLE_NAMES = ["Mina", "Lina", "Tess", "Ivy", "Nora", "June", "Maya"]


@dataclass
@dataclass
class StoryParams:
    place: str
    quest: str
    surprise: str
    tool: str
    name: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


KNOWLEDGE = {
    "knick": [("What is a knick-knack?",
               "A knick-knack is a tiny object kept for fun, memory, or decoration. It is usually small enough to sit on a shelf or in a drawer.")],
    "quest": [("What is a quest?",
               "A quest is a search for something important. In stories, a quest often means going step by step until the missing thing is found.")],
    "surprise": [("What is a surprise?",
                  "A surprise is something you do not expect. It can make a moment feel exciting, happy, or magical.")],
    "transform": [("What is a transformation?",
                   "A transformation is a change from one thing into another. In stories, it can feel magical, like a toy becoming special.")],
    "bedtime": [("Why is bedtime calm?",
                 "Bedtime is calm because people slow down, get cozy, and rest so their bodies and minds can sleep.")],
}

KNOWLEDGE_ORDER = ["bedtime", "knick", "quest", "surprise", "transform"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    q = f["quest_cfg"]
    s = f["surprise"]
    return [
        f'Write a bedtime story for a 4-year-old that includes the word "knick", a quiet quest, a surprise, and a gentle transformation.',
        f"Tell a cozy story where {f['child'].id} looks for a missing {q.label} near bedtime and discovers a surprising magical change.",
        f'Write a child-friendly night story about a tiny quest that ends with a transformation and a soft surprise.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    q = f["quest_cfg"]
    s = f["surprise"]
    return [
        ("Who is the story about?",
         f"It is about {child.id}, a sleepy child who goes on a quiet bedtime quest. The story stays small and gentle so it feels cozy."),
        ("What was {child.id} looking for?".replace("{child.id}", child.id),
         f"{child.id} was looking for the little {q.phrase}. It had been hidden close to the bed, so the search could stay calm and close."),
        ("What surprise happened at the end?",
         f"{s.reveal}, and the small {q.label} changed into {q.transform_into}. The surprise made the ending feel magical instead of ordinary."),
        ("How did the story end?",
         f"It ended with {child.id} holding the new {q.transform_into} and feeling sleepy and happy. That ending shows the quest was finished and the room became peaceful again."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["quest_cfg"].tags) | set(world.facts["surprise"].tags) | {"bedtime"}
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags and key in KNOWLEDGE:
            out.extend(KNOWLEDGE[key])
    return out


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
    return "\n".join(lines)


CURATED = [
    StoryParams("nursery", "knick", "surprise_box", "moonbeam", "Mina"),
    StoryParams("attic", "star", "pillow", "moonbeam", "Nora"),
    StoryParams("cabin", "shell", "sock", "lamp", "Ivy"),
]


def explain_rejection(quest: QuestItem, surprise: Surprise) -> str:
    if quest.hidden_by != surprise.id:
        return "(No story: this quest and surprise do not belong together, so the tiny mystery would not fit.)"
    return "(No story: this combination is not reasonable.)"


def outcome_of(params: StoryParams) -> str:
    return "transformed"


ASP_RULES = r"""
quest_match(Q,S) :- hidden_by(Q,S), surprise(S).
valid(P,Q,S) :- place(P), quest(Q), surprise(S), quest_match(Q,S).
outcome(transformed) :- valid(_,_,_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("hidden_by", qid, q.hidden_by))
    for sid in SURPRISES:
        lines.append(asp.fact("surprise", sid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, quest=None, surprise=None, tool=None, name=None, seed=None), random.Random(1)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world: a tiny quest, a surprise, and a gentle transformation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
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
              and (args.quest is None or c[1] == args.quest)
              and (args.surprise is None or c[2] == args.surprise)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, quest, surprise = rng.choice(sorted(combos))
    tool = args.tool or rng.choice(sorted(TOOLS))
    name = args.name or rng.choice(GENTLE_NAMES)
    return StoryParams(place, quest, surprise, tool, name)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], QUESTS[params.quest], SURPRISES[params.surprise], TOOLS[params.tool])
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
        print(asp_program("", "#show valid/3."))
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
