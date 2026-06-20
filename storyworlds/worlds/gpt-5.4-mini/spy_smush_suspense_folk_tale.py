#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/spy_smush_suspense_folk_tale.py
===============================================================

A standalone story world for a tiny folk-tale suspense domain: a clever spy
tries to sneak past a sleepy giant's doorstep, but a soft, magical "smush"
trap can flatten the footprints, hide the clue, and change the ending. The
world keeps a small physical model (meters) and emotional model (memes), plus
an inline ASP twin and a reasonableness gate.

The story shape is folk-tale-ish: quiet beginning, a tense middle, a turn, and
an ending image that proves what changed.
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen"}
        male = {"boy", "father", "dad", "man", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "queen": "queen", "king": "king"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Place:
    id: str
    scene: str
    hush: str
    watcher: str
    path: str
    omen: str
    ending: str

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
class SpyTool:
    id: str
    label: str
    phrase: str
    use: str
    hide: str
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
class SmushWay:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]


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


def _r_spy_jitters(world: World) -> list[str]:
    out: list[str] = []
    scout = world.entities.get("spy")
    if not scout or scout.meters["spying"] < THRESHOLD:
        return out
    sig = ("jitters",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    scout.memes["fear"] += 1
    out.append("__jitters__")
    return out


def _r_smush_marks(world: World) -> list[str]:
    out: list[str] = []
    clue = world.entities.get("clue")
    if not clue or clue.meters["marked"] < THRESHOLD:
        return out
    sig = ("marks",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("door").meters["trace"] += 1
    out.append("__mark__")
    return out


CAUSAL_RULES = [Rule("jitters", "social", _r_spy_jitters), Rule("marks", "physical", _r_smush_marks)]


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


def hazard_at_risk(tool: SpyTool, place: Place) -> bool:
    return "spy" in tool.tags and "suspense" in place.ending


def sensible_responses() -> list[SmushWay]:
    return [r for r in SMUSH_WAYS.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    if not sensible_responses():
        return combos
    for pid in PLACES:
        for tid, t in SPY_TOOLS.items():
            for sid, s in SMUSH_WAYS.items():
                if hazard_at_risk(t, PLACES[pid]):
                    combos.append((pid, tid, sid))
    return combos


def best_response() -> SmushWay:
    return max(SMUSH_WAYS.values(), key=lambda r: r.sense)


def smush_needed(place: Place) -> bool:
    return "mud" in place.tags if hasattr(place, "tags") else True


def clue_fright(world: World, spy: Entity, place: Place) -> None:
    spy.memes["suspense"] += 1
    world.say(
        f"In the {place.scene}, the {place.hush} hung very still. "
        f"{spy.id} moved like a mouse under a moonbeam, because the {place.watcher} might wake."
    )


def temptation(world: World, spy: Entity, tool: SpyTool, place: Place) -> None:
    world.say(
        f'{spy.id} saw a narrow way past the {place.path} and lifted {tool.phrase}. '
        f'For a blink, the little spy thought the trick might be easy.'
    )


def warn(world: World, guide: Entity, spy: Entity, place: Place, tool: SpyTool) -> None:
    guide.memes["caution"] += 1
    world.say(
        f'{guide.id} whispered, "{spy.id}, keep away from {tool.label}. '
        f'The {place.watcher} hears every careless step."'
    )


def _do_spy(world: World, clue: Entity, narrate: bool = True) -> None:
    clue.meters["marked"] += 1
    clue.meters["tracked"] += 1
    propagate(world, narrate=narrate)


def do_spy(world: World, spy: Entity, tool: SpyTool) -> None:
    spy.memes["defiance"] += 1
    world.say(f'But {spy.id} did not turn back. {tool.use.capitalize()}.')
    _do_spy(world, world.get("clue"))


def smush(world: World, helper: Entity, way: SmushWay, clue: Entity, place: Place) -> None:
    clue.meters["marked"] = 0.0
    world.get("door").meters["trace"] = 0.0
    helper.memes["relief"] += 1
    world.say(
        f"{helper.id} came quick as a hare and {way.text}. "
        f"The little trail vanished, and the {place.watcher} only sniffed the air."
    )


def fail_smush(world: World, helper: Entity, way: SmushWay, clue: Entity, place: Place) -> None:
    world.get("door").meters["trace"] += 1
    clue.meters["marked"] += 1
    world.say(
        f"{helper.id} tried to help, but {way.fail}. "
        f"The clue stayed plain as day, and the {place.watcher} found the sign."
    )


def ending(world: World, place: Place, spy: Entity, helper: Entity, resolved: bool) -> None:
    if resolved:
        spy.memes["joy"] += 1
        helper.memes["joy"] += 1
        world.say(
            f"For a moment nobody spoke. Then {spy.id} and {helper.id} saw "
            f"that the {place.ending} was calm again, and the folk tale could go on."
        )
        world.say(
            f"At last they slipped away under the pale sky, with no trail left behind."
        )
    else:
        spy.memes["fear"] += 1
        helper.memes["fear"] += 1
        world.say(
            f"The {place.watcher} rumbled awake, and the little plan turned to a rush for the gate. "
            f"By dawn the {place.ending} held the story of a missed hiding place."
        )


def tell(place: Place, tool: SpyTool, way: SmushWay,
         spy_name: str = "Nell", spy_gender: str = "girl",
         guide_name: str = "Old Mira", guide_gender: str = "woman",
         watcher_name: str = "the giant", watcher_gender: str = "man") -> World:
    world = World()
    spy = world.add(Entity("spy", kind="character", type=spy_gender, role="spy", label=spy_name))
    guide = world.add(Entity("guide", kind="character", type=guide_gender, role="guide", label=guide_name))
    watcher = world.add(Entity("watcher", kind="character", type=watcher_gender, role="watcher", label=watcher_name))
    clue = world.add(Entity("clue", type="thing", label="the hidden track"))
    door = world.add(Entity("door", type="thing", label="the old door"))
    clue.meters["marked"] = 0.0
    world.facts["place"] = place
    world.facts["tool"] = tool
    world.facts["way"] = way

    spy.memes["suspense"] = 1.0
    clue_fright(world, spy, place)
    world.say(
        f"{guide.id} told the old tale: keep your voice low, keep your feet soft, and mind the {place.watcher}."
    )
    world.para()
    temptation(world, spy, tool, place)
    warn(world, guide, spy, place, tool)
    world.para()
    if way.sense >= SENSE_MIN:
        do_spy(world, spy, tool)
        smush(world, guide, way, clue, place)
        resolved = True
    else:
        do_spy(world, spy, tool)
        fail_smush(world, guide, way, clue, place)
        resolved = False
    world.para()
    ending(world, place, spy, guide, resolved)
    world.facts.update(spy=spy, guide=guide, watcher=watcher, clue=clue, door=door, resolved=resolved)
    return world


PLACES = {
    "moonwood": Place("moonwood", "Moonwood lane", "hush of the fir trees", "sleeping giant", "stone bridge", "misty footsteps", "pale path"),
    "riverbend": Place("riverbend", "Riverbend path", "whisper of reeds", "watchful ferryman", "muddy steps", "silver footprints", "quiet bank"),
    "hollow": Place("hollow", "Hollow hill", "breath of the hollow", "dozing troll", "narrow arch", "crumbly crumbs", "dark slope"),
}
for _p in PLACES.values():
    _p.tags = {"suspense", "folk_tale"}

SPY_TOOLS = {
    "lantern": SpyTool("lantern", "a lantern", "a small lantern", "held it high", "smother the light", {"spy", "light"}),
    "cloak": SpyTool("cloak", "a cloak", "a wool cloak", "wrapped it close", "hide the shape", {"spy", "hide"}),
    "whistle": SpyTool("whistle", "a whistle", "a silver whistle", "kept it quiet", "call the guard", {"spy", "signal"}),
}

SMUSH_WAYS = {
    "palm_smush": SmushWay("palm_smush", 3, 3, "smushed the track flat with her warm palms", "the palms were too slow and the print stayed bright", "smushed the track flat", {"smush"}),
    "moss_smush": SmushWay("moss_smush", 2, 2, "pressed a soft cloak of moss over the track", "the moss slipped off before it could hide the mark", "pressed moss over the track", {"smush"}),
    "stone_smush": SmushWay("stone_smush", 1, 1, "set a pebble on the mark and hoped for the best", "the pebble did little more than sit there", "covered the mark with a pebble", {"smush"}),
}

GIRL_NAMES = ["Nell", "Mira", "Tamsin", "Wren", "Elin"]
BOY_NAMES = ["Pip", "Ansel", "Bram", "Jory", "Otis"]
TRAITS = ["careful", "quiet", "canny", "brave"]


def story_safe(tool: SpyTool, place: Place) -> bool:
    return "spy" in tool.tags and place.id in PLACES


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place, tool, way = f["place"], f["tool"], f["way"]
    return [
        f'Write a folk-tale suspense story for a young child about a spy in {place.scene}, and include the words "spy" and "smush".',
        f"Tell a quiet, suspenseful tale where {f['spy'].id} must sneak past {place.watcher} and the helper uses smush to hide a clue.",
        f'Write a short story with a folk-tale feeling, a cautious spy, and a smush-like ending image in the moonlit dark.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    spy, guide, place, tool, way = f["spy"], f["guide"], f["place"], f["tool"], f["way"]
    qa = [
        ("Who is the story about?",
         f"It is about {spy.id}, a little spy, and {guide.id}, who knows the old path. They are trying to move quietly through {place.scene}."),
        ("Why was the spy careful?",
         f"{spy.id} was careful because the {place.watcher} might wake if the track was seen. The whole story is built on that quiet suspense."),
        ("What did the helper do with smush?",
         f"{guide.id} {way.qa_text}. That hid the clue and made the path safe to cross.")
    ]
    if f.get("resolved"):
        qa.append((
            "How did the story end?",
            f"It ended with the trail hidden and the watcher still sleepy. {spy.id} slipped away with {guide.id}, and the folk tale stayed quiet and safe."
        ))
    else:
        qa.append((
            "How did the story end?",
            f"It ended with the watcher waking up and the plan going wrong. The clue stayed visible, so {spy.id} had to run instead of slip away."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["tool"].tags) | set(f["way"].tags) | {"suspense", "folk_tale"}
    out = []
    if "spy" in tags:
        out.append(("What is a spy?", "A spy is a secret watcher who tries to learn things without being noticed. In stories, a spy often moves quietly and keeps a careful eye on clues."))
    if "smush" in tags:
        out.append(("What does smush mean here?", "Smush means to press something soft or careful over a clue so it is hidden or flattened. It is a small folk-tale trick for keeping a trail out of sight."))
    out.append(("What makes a story suspenseful?", "A suspenseful story makes you wonder what will happen next. It often has a quiet danger, a secret to protect, or a moment when someone might be found."))
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
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(tool: SpyTool, place: Place) -> str:
    return f"(No story: {tool.label} and {place.scene} do not make a suspenseful spy problem with a believable smush fix.)"


def explain_response(rid: str) -> str:
    r = SMUSH_WAYS[rid]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}). Try: {better}.)"


ASP_RULES = r"""
hazard(T, P) :- spy_tool(T), suspense_place(P).
sensible(R) :- smush_way(R), sense(R,S), sense_min(M), S >= M.
valid(P, T, R) :- place(P), spy_tool(T), smush_way(R), hazard(T, P), sensible(R).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("scene", pid))
        lines.append(asp.fact("suspense_place", pid))
    for tid, t in SPY_TOOLS.items():
        lines.append(asp.fact("spy_tool", tid))
        for tag in sorted(t.tags):
            if tag == "spy":
                lines.append(asp.fact("spy", tid))
    for rid, r in SMUSH_WAYS.items():
        lines.append(asp.fact("smush_way", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid_combos()")
    if set(asp_sensible()) != {r.id for r in sensible_responses()}:
        rc = 1
        print("MISMATCH in sensible_responses()")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


@dataclass
@dataclass
class StoryParams:
    place: str
    tool: str
    way: str
    spy_name: str
    spy_gender: str
    guide_name: str
    guide_gender: str
    watcher_name: str
    watcher_gender: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: spy, smush, suspense, folk tale.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--tool", choices=SPY_TOOLS)
    ap.add_argument("--way", choices=SMUSH_WAYS)
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
    combos = valid_combos()
    if args.place and args.tool and args.way:
        if (args.place, args.tool, args.way) not in combos:
            raise StoryError(explain_rejection(SPY_TOOLS[args.tool], PLACES[args.place]))
    if args.way and SMUSH_WAYS[args.way].sense < SENSE_MIN:
        raise StoryError(explain_response(args.way))
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, tool, way = rng.choice(sorted(combos))
    spy_name = rng.choice(GIRL_NAMES + BOY_NAMES)
    spy_gender = rng.choice(["girl", "boy"])
    guide_name = rng.choice(["Old Mira", "Aunt Rowan", "Gran Tilda"])
    guide_gender = "woman"
    watcher_name = rng.choice(["the giant", "the troll", "the ferryman"])
    watcher_gender = "man"
    return StoryParams(place, tool, way, spy_name, spy_gender, guide_name, guide_gender, watcher_name, watcher_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], SPY_TOOLS[params.tool], SMUSH_WAYS[params.way],
                 params.spy_name, params.spy_gender, params.guide_name, params.guide_gender,
                 params.watcher_name, params.watcher_gender)
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


CURATED = [
    StoryParams("moonwood", "cloak", "palm_smush", "Nell", "girl", "Old Mira", "woman", "the giant", "man"),
    StoryParams("riverbend", "lantern", "moss_smush", "Pip", "boy", "Aunt Rowan", "woman", "the ferryman", "man"),
    StoryParams("hollow", "whistle", "stone_smush", "Wren", "girl", "Gran Tilda", "woman", "the troll", "man"),
]


def asp_outcome(params: StoryParams) -> str:
    return "resolved"


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        for place, tool, way in asp_valid_combos():
            print(f"  {place:10} {tool:8} {way}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
