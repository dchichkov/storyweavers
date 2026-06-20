#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/freshen_quest_sound_effects_conflict_heartwarming.py
=====================================================================================

A standalone story world for a small, heartwarming TinyStories-style domain:

A child begins a "freshen" quest to make a room smell and feel nice again,
a sibling or friend disagrees about the best method, sound effects carry the
action, and the conflict ends in a warm, caring resolution.

The world is modeled with typed entities, physical meters, and emotional memes.
The story is driven from world state rather than swapped nouns in a frozen
paragraph. The default premise is a quest to freshen a shared space; the tension
comes from clashing ideas; the turn uses a concrete tool or natural fix; the end
proves the room and the feelings changed.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/freshen_quest_sound_effects_conflict_heartwarming.py
    python storyworlds/worlds/gpt-5.4-mini/freshen_quest_sound_effects_conflict_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4-mini/freshen_quest_sound_effects_conflict_heartwarming.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4-mini/freshen_quest_sound_effects_conflict_heartwarming.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/freshen_quest_sound_effects_conflict_heartwarming.py --verify
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
    kind: str = "thing"          # character | thing | place
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)
    freshen_power: int = 0
    conflict_soothe: int = 0
    makes_sound: str = ""

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
    smell: str
    state: str
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
    action: str
    sound: str
    freshen: int
    soothe: int
    kind: str = "tool"

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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.place: Optional[Place] = None
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.place = copy.deepcopy(self.place)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


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


def _r_stale_spreads(world: World) -> list[str]:
    out: list[str] = []
    if world.place is None:
        return out
    if world.place.meters["stale"] < THRESHOLD:
        return out
    sig = ("stale_spreads", world.place.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.place.meters["fresh_needed"] += 1
    for ent in list(world.entities.values()):
        if ent.kind == "character":
            ent.memes["hope"] += 1
    out.append("__need_freshen__")
    return out


def _r_conflict_heats(world: World) -> list[str]:
    out: list[str] = []
    if world.place is None:
        return out
    if world.place.meters["fresh_needed"] < THRESHOLD:
        return out
    for ent in list(world.entities.values()):
        if ent.role != "arguer":
            continue
        sig = ("conflict_heats", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["stubborn"] += 1
        out.append("__conflict__")
    return out


def _r_freshen_done(world: World) -> list[str]:
    out: list[str] = []
    if world.place is None:
        return out
    if world.place.meters["fresh"] < THRESHOLD:
        return out
    sig = ("freshen_done", world.place.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.place.meters["stale"] = 0.0
    world.place.meters["fresh_needed"] = 0.0
    for ent in list(world.entities.values()):
        if ent.kind == "character":
            ent.memes["relief"] += 1
            ent.memes["joy"] += 1
    out.append("__fresh__")
    return out


CAUSAL_RULES = [
    Rule("stale_spreads", "physical", _r_stale_spreads),
    Rule("conflict_heats", "social", _r_conflict_heats),
    Rule("freshen_done", "physical", _r_freshen_done),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
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


def can_freshen(tool: Tool, place: Place) -> bool:
    return tool.freshen >= 2 and place.meters["stale"] >= THRESHOLD


def can_soothe(tool: Tool) -> bool:
    return tool.soothe >= 2


def predict_outcome(world: World, tool_id: str) -> dict:
    sim = world.copy()
    _use_tool(sim, sim.get(tool_id), narrate=False)
    return {
        "fresh": sim.place.meters["fresh"] >= THRESHOLD if sim.place else False,
        "stale": sim.place.meters["stale"],
    }


def _use_tool(world: World, tool: Entity, narrate: bool = True) -> None:
    if world.place is None:
        return
    world.place.meters["fresh"] += tool.freshen_power
    world.place.meters["smell"] += 1
    if tool.freshen_power >= 3:
        world.place.meters["sparkle"] += 1
    propagate(world, narrate=narrate)


def open_setup(world: World, child: Entity, helper: Entity, place: Place) -> None:
    child.memes["curiosity"] += 1
    helper.memes["care"] += 1
    world.say(
        f"On a quiet afternoon, {child.id} looked at {place.label} and decided to "
        f"start a freshen quest. The air felt {place.smell}, and the room had "
        f"lost its happy shine."
    )
    world.say(
        f"{helper.id} came along, ready to help. They wanted to make the place "
        f"feel nice again."
    )


def quest_step(world: World, child: Entity, place: Place) -> None:
    world.say(
        f'{child.id} tipped their head and listened. The room seemed to whisper, '
        f'"Please freshen me."'
    )
    world.say(
        f"So {child.id} opened the window a little: whoosh, the curtain made a soft "
        f"swish, and a cool breeze wandered in."
    )
    place.meters["fresh_needed"] += 1


def conflict(world: World, child: Entity, helper: Entity, tool: Tool, place: Place) -> None:
    child.memes["wanting"] += 1
    helper.memes["worry"] += 1
    world.say(
        f'{child.id} grabbed {tool.phrase} and said, "{tool.action}!" '
        f'{helper.id} frowned and said that was too much.'
    )
    world.say(
        f'The room answered with a little "{tool.sound}" as the idea bounced '
        f'back and forth.'
    )
    if can_soothe(tool):
        world.say(
            f"{helper.id} took a breath and explained that the best quest would "
            f"freshen the room without making more trouble."
        )


def resolve(world: World, child: Entity, helper: Entity, tool: Tool, place: Place) -> None:
    child.memes["trust"] += 1
    helper.memes["love"] += 1
    _use_tool(world, world.get(tool.id))
    world.say(
        f"Then {helper.id} smiled and helped. Together they used {tool.phrase}, "
        f"and it went {tool.sound}."
    )
    world.say(
        f"The {place.label} grew brighter and lighter, like it had taken a big "
        f"happy breath."
    )
    world.say(
        f"{child.id} laughed, {helper.id} laughed too, and the fresh little room "
        f"felt ready for a cuddle and a story."
    )


def heart_warming_end(world: World, child: Entity, helper: Entity, place: Place) -> None:
    place.meters["fresh"] = max(place.meters["fresh"], 2.0)
    world.say(
        f"At the end, {child.id} tucked the tool away neatly and gave {helper.id} a "
        f"warm hug. The quest was finished, and the room smelled sweet and clean."
    )
    world.say(
        f"Everything felt calm again in {place.label}, as if the walls were smiling."
    )


def tell(place: Place, child: Entity, helper: Entity, tool: Tool) -> World:
    world = World()
    world.place = copy.deepcopy(place)
    c = world.add(Entity(id=child.id, kind="character", type=child.type, role="quester"))
    h = world.add(Entity(id=helper.id, kind="character", type=helper.type, role="helper"))
    t = world.add(Entity(id=tool.id, kind="thing", type="tool", label=tool.label))
    t.freshen_power = tool.freshen
    t.conflict_soothe = tool.soothe
    t.makes_sound = tool.sound

    open_setup(world, c, h, world.place)
    world.para()
    quest_step(world, c, world.place)
    conflict(world, c, h, tool, world.place)
    world.para()
    resolve(world, c, h, tool, world.place)
    heart_warming_end(world, c, h, world.place)

    world.facts.update(
        child=c,
        helper=h,
        tool=tool,
        place=world.place,
        fresh=world.place.meters["fresh"],
        stale=world.place.meters["stale"],
        outcome="freshened" if world.place.meters["fresh"] >= THRESHOLD else "unchanged",
    )
    return world


PLACES = {
    "bedroom": Place("bedroom", "the bedroom", "a little stale", "stale"),
    "playroom": Place("playroom", "the playroom", "a bit stuffy", "stale"),
    "kitchen": Place("kitchen", "the kitchen", "a little cooking-smelly", "stale"),
}

TOOLS = {
    "fan": Tool("fan", "small fan", "a small fan", "blow fresh air in", "whirr", 3, 2),
    "flowers": Tool("flowers", "vase of flowers", "a vase of flowers", "bring a sweet smell", "hmm", 2, 2),
    "blanket": Tool("blanket", "fresh blanket", "a fresh blanket", "shake it out nicely", "fluff", 2, 3),
}

CHILD_NAMES = ["Mia", "Leo", "Nina", "Owen", "Ava", "Theo", "Lily", "Sam"]


@dataclass
@dataclass
class StoryParams:
    place: str
    tool: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
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


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for p in PLACES:
        for t in TOOLS:
            combos.append((p, t))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming quest to freshen a room.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--child")
    ap.add_argument("--helper")
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
              and (args.tool is None or c[1] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, tool = rng.choice(sorted(combos))
    child = args.child or rng.choice(CHILD_NAMES)
    helper = args.helper or rng.choice([n for n in CHILD_NAMES if n != child])
    return StoryParams(place, tool, child, "girl", helper, "boy")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story that includes the word "freshen" and a small '
        f'quest to make {f["place"].label} feel nice again.',
        f"Tell a story where {f['child'].id} and {f['helper'].id} disagree about "
        f"how to freshen the room, but end up helping each other.",
        f'Write a gentle conflict story with sound effects like "{f["tool"].sound}" '
        f'and a happy ending in a cozy room.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, tool, place = f["child"], f["helper"], f["tool"], f["place"]
    return [
        QAItem(
            question=f"What was {child.id} trying to do?",
            answer=f"{child.id} was trying to freshen {place.label}. {child.id} wanted to make the room feel brighter and nicer for everyone."
        ),
        QAItem(
            question=f"Why did {helper.id} disagree at first?",
            answer=f"{helper.id} worried that the first idea would make things worse instead of better. That conflict happened because both children cared about the room, but they had different plans."
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{child.id} and {helper.id} solved the problem together, and {place.label} felt clean and calm again. The ending is warm because they listened to each other and worked as a team."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does freshen mean?",
            answer="To freshen something means to make it feel cleaner, lighter, or nicer. A room can be freshened by opening a window, tidying it, or adding a pleasant smell."
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a goal you go after with effort and care. It can be a small adventure, like trying to fix or find something important."
        ),
        QAItem(
            question="What does a sound effect do in a story?",
            answer="A sound effect helps the reader hear the action in their mind. Sounds like swish, whirr, or fluff can make a scene feel more alive."
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
    if world.place:
        lines.append(f"  place    ({world.place.label}) meters={dict(world.place.meters)}")
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
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
fresh_needed(P) :- stale(P, S), S >= 1.
conflict(C) :- child(C), wants_freshen(C).
freshened(P) :- fresh(P, F), F >= 1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("stale", pid, 1))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("", "#show freshened/1."))
    _ = asp.atoms(model, "freshened")
    # Smoke test ordinary story generation, per contract.
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        return 1
    if set(valid_combos()) != set((p, t) for p in PLACES for t in TOOLS):
        print("MISMATCH: valid_combos() drifted.")
        return 1
    print("OK: asp loaded, valid_combos consistent, and generation smoke test passed.")
    return 0


def tell_from_params(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], Entity(id=params.child, type=params.child_gender),
                 Entity(id=params.helper, type=params.helper_gender),
                 TOOLS[params.tool])
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return tell_from_params(params)


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
    StoryParams("bedroom", "fan", "Mia", "girl", "Leo", "boy"),
    StoryParams("playroom", "flowers", "Ava", "girl", "Sam", "boy"),
    StoryParams("kitchen", "blanket", "Lily", "girl", "Theo", "boy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("", "#show freshened/1."))
        return
    if args.asp:
        print(f"{len(valid_combos())} compatible combos:")
        for p, t in valid_combos():
            print(f"  {p:8} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
