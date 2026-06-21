#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/protective_least_carpenter_conflict_mystery_to_solve.py
======================================================================================

A small standalone storyworld for a folk-tale style mystery:
a carpenter makes something protective, the least trusted helper causes a conflict,
and the village must solve a mystery before the ending can turn warm and safe.

The world model is intentionally tiny:
- typed entities have physical meters and emotional memes
- state drives prose
- the conflict is whether the carpenter's protective work is sabotaged or simply
  delayed by a puzzling missing part
- the mystery is solved by discovering what was hidden, broken, or borrowed

This script follows the Storyweavers storyworld contract:
- stdlib only
- imports shared result containers eagerly
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
- includes a Python reasonableness gate and an inline ASP twin
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen"}
        male = {"boy", "father", "dad", "man", "carpenter"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father"}.get(self.type, self.label or self.type)



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
    mood: str
    opening: str
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
class ObjectThing:
    id: str
    label: str
    phrase: str
    kind: str
    protective: bool = False
    hidden: bool = False
    broken: bool = False
    borrowed: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

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
class Mystery:
    id: str
    clue: str
    missing: str
    culprit: str
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


@dataclass
class ConflictMove:
    id: str
    text: str
    sense: int
    power: int
    resolution: str
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
        self.objects: dict[str, ObjectThing] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add_entity(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def add_object(self, o: ObjectThing) -> ObjectThing:
        self.objects[o.id] = o
        return o

    def get_entity(self, eid: str) -> Entity:
        return self.entities[eid]

    def get_object(self, oid: str) -> ObjectThing:
        return self.objects[oid]

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
        clone.objects = copy.deepcopy(self.objects)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
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


def _r_missing(world: World) -> list[str]:
    out: list[str] = []
    for obj in world.objects.values():
        if not obj.hidden or obj.meters["noticed"] >= THRESHOLD:
            continue
        sig = ("noticed", obj.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        obj.meters["noticed"] += 1
        out.append(f"A small clue pointed toward the missing {obj.label}.")
    return out


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.memes["doubt"] < THRESHOLD or e.memes["stubborn"] < THRESHOLD:
            continue
        sig = ("conflict", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["worry"] += 1
        out.append("__conflict__")
    return out


CAUSAL_RULES = [Rule("missing", "mystery", _r_missing), Rule("conflict", "social", _r_conflict)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_ok(mystery: Mystery, move: ConflictMove) -> bool:
    return move.sense >= 2 and mystery.missing in {"roof_tile", "door_latch", "lantern_hook", "painted_sign"}


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid in SETTINGS:
        for mid, m in MYSTERIES.items():
            if any(reasonableness_ok(m, mv) for mv in MOVES.values()):
                combos.append((sid, mid))
    return combos


def best_move() -> ConflictMove:
    return max(MOVES.values(), key=lambda m: m.sense)


def choose_move(mystery: Mystery) -> ConflictMove:
    sensible = [m for m in MOVES.values() if m.sense >= 2]
    for m in sensible:
        if mystery.missing == m.resolution:
            return m
    return best_move()


def predict(world: World, mystery_id: str) -> dict:
    sim = world.copy()
    m = sim.facts["mystery"]
    _do_mystery(sim, sim.facts["mystery_obj"], narrate=False)
    return {
        "noticed": sim.get_object(missing_by_id[m.id]).meters["noticed"] >= THRESHOLD,
        "conflict": any(e.memes["worry"] > 0 for e in sim.entities.values()),
    }


def _do_mystery(world: World, obj: ObjectThing, narrate: bool = True) -> None:
    obj.hidden = True
    obj.meters["noticed"] += 1
    propagate(world, narrate=narrate)


def tell(setting: Setting, mystery: Mystery, move: ConflictMove,
         hero_name: str = "Mara", hero_type: str = "girl",
         carpenter_name: str = "Joren", carpenter_type: str = "carpenter",
         helper_name: str = "Nell", helper_type: str = "girl",
         seed: Optional[int] = None) -> World:
    world = World()
    hero = world.add_entity(Entity(id=hero_name, kind="character", type=hero_type, role="villager"))
    carpenter = world.add_entity(Entity(id=carpenter_name, kind="character", type=carpenter_type, role="carpenter"))
    helper = world.add_entity(Entity(id=helper_name, kind="character", type=helper_type, role="least", traits=["least", "restless"]))
    hero.memes["hope"] = 1
    carpenter.memes["care"] = 1
    helper.memes["stubborn"] = 1
    helper.memes["doubt"] = 1

    obj = world.add_object(ObjectThing(id=mystery.missing, label=mystery.missing.replace("_", " "), phrase=mystery.missing.replace("_", " "), kind="object", protective=True))
    spare = world.add_object(ObjectThing(id="spare", label="spare peg", phrase="a spare peg", kind="object", borrowed=True))
    world.facts.update(mystery=mystery, move=move, setting=setting, mystery_obj=obj, carpenter=carpenter, helper=helper, hero=hero)

    world.say(setting.opening.format(hero=hero.id, carpenter=carpenter.id, helper=helper.id))
    world.say(f"{carpenter.id} was the carpenter in the little village, and {helper.id} was the least trusted helper.")
    world.say(f"They were building something protective: a new cover for the {mystery.clue}.")
    world.say(f"But one cold morning, the protective piece was gone, and no one knew where it had gone.")

    world.para()
    helper.memes["doubt"] += 1
    world.say(f'"We should fix it at once," said {hero.id}, "but first we must solve the mystery."')
    world.say(f'{helper.id} frowned and made a small conflict of words, because {helper.id} had been near the workbench last.')
    world.say(f'{carpenter.id} stayed calm and said, "The least help can still be true help if it tells the truth."')

    world.para()
    clue = mystery.clue
    world.say(f"They searched by the lantern light and found the {clue}.")
    if mystery.culprit == "wind":
        world.say("A strong wind had blown the piece into the herb bed and hidden it under leaves.")
    elif mystery.culprit == "cat":
        world.say("The cat had dragged it behind a rain barrel, where it waited in the shadows.")
    else:
        world.say("A jealous sparrow had carried it to the fence, where moss and twine hid it well.")
    world.say(f"{mystery.reveal}")

    obj.hidden = False
    world.para()
    world.say(f"{carpenter.id} fixed the protective work with steady hands.")
    world.say(f"{move.text.capitalize()}.")
    world.say(f"{mystery.fix}")
    world.say(f"In the end, the village had its protective shelter again, and even the least helper learned to help by telling the truth.")

    world.facts["outcome"] = "solved"
    return world


SETTINGS = {
    "village": Setting(
        "village",
        "a small village by the woods",
        "folk",
        "The village was quiet except for the tapping of tools and the whisper of pine trees.",
        "At dusk, the repaired shelter stood firm, and the windows glowed like tiny moons.",
    ),
    "mill": Setting(
        "mill",
        "a mill beside the river",
        "folk",
        "The mill sang softly with the river, and every board smelled of sap and rain.",
        "By evening, the protective frame leaned strong against the wind, shining with fresh wax.",
    ),
    "market": Setting(
        "market",
        "a market square with a stone well",
        "folk",
        "The market woke with baskets, bread, and hammer taps from the carpenter's stall.",
        "When the sun went down, the finished protection stood near the well, plain and sturdy.",
    ),
}

MYSTERIES = {
    "roof_tile": Mystery("roof_tile", "roof", "roof_tile", "wind",
                         "The missing tile had landed in the herb bed, hidden under mint leaves.",
                         "The roof would stay dry now that the tile was back in place.",
                         tags={"protective", "mystery"}),
    "door_latch": Mystery("door_latch", "door", "door_latch", "cat",
                          "The latch had been tucked behind the rain barrel by the cat.",
                          "The door would shut safe and snug again.",
                          tags={"protective", "mystery"}),
    "lantern_hook": Mystery("lantern_hook", "lantern", "lantern_hook", "sparrow",
                            "The hook had been carried to the fence and tangled in twine.",
                            "The lantern would hang safely beside the path once more.",
                            tags={"protective", "mystery"}),
}

MOVES = {
    "brace": ConflictMove("brace", "the carpenter added a brace of oak and tied the board tight", 3, 3, "roof_tile", {"protective"}),
    "latch": ConflictMove("latch", "the carpenter set a new latch with a bright iron pin", 3, 3, "door_latch", {"protective"}),
    "hook": ConflictMove("hook", "the carpenter hung the lantern on a stronger hook", 2, 2, "lantern_hook", {"protective"}),
}

missing_by_id = {m.id: m.id for m in MYSTERIES.values()}


@dataclass
@dataclass
class StoryParams:
    setting: str
    mystery: str
    move: str
    hero: str
    carpenter: str
    helper: str
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
    ap = argparse.ArgumentParser(description="Folk-tale storyworld: a protective craft, a conflict, and a mystery to solve.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--move", choices=MOVES)
    ap.add_argument("--name")
    ap.add_argument("--carpenter-name")
    ap.add_argument("--helper-name")
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
    if args.move and args.mystery:
        if not reasonableness_ok(MYSTERIES[args.mystery], MOVES[args.move]):
            raise StoryError("That move does not fit this mystery.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery = rng.choice(sorted(combos))
    move = args.move or rng.choice(sorted(MOVES))
    hero = args.name or rng.choice(["Mara", "Elsa", "Rin", "Tilda"])
    carpenter = args.carpenter_name or rng.choice(["Joren", "Bram", "Pavel", "Ivo"])
    helper = args.helper_name or rng.choice(["Nell", "Mina", "Pip", "Sera"])
    return StoryParams(setting, mystery, move, hero, carpenter, helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], MYSTERIES[params.mystery], MOVES[params.move],
                 hero_name=params.hero, carpenter_name=params.carpenter, helper_name=params.helper)
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk-tale story that includes the words "protective", "least", and "carpenter".',
        f"Tell a small village mystery where {f['carpenter'].id} makes something protective, but the least trusted helper causes a conflict before the mystery is solved.",
        f"Write a child-facing tale with a puzzle, a calm carpenter, and a protective fix that ends well.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, carpenter, helper, mystery, move = f["hero"], f["carpenter"], f["helper"], f["mystery"], f["move"]
    return [
        ("Who are the main characters?",
         f"The story is about {hero.id}, {carpenter.id}, and {helper.id}. {carpenter.id} is the carpenter, and {helper.id} is the least trusted helper."),
        ("What was the conflict?",
         f"The conflict was that something important went missing while the protective work was being built, and {helper.id} had been the last one near the workbench. Everyone had to stay calm and solve the mystery before they could finish the repair."),
        ("How was the mystery solved?",
         f"They followed the clue, found the missing {mystery.missing.replace('_', ' ')}, and fixed it with steady hands. Then {move.text} so the protective work was strong again."),
        ("How did the story end?",
         f"It ended safely, with the protective shelter repaired and the village feeling calm again. Even the least helper learned that telling the truth can help solve a mystery."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does a carpenter do?",
         "A carpenter builds and repairs things made of wood, like roofs, doors, and sturdy frames."),
        ("What does protective mean?",
         "Protective means made to keep something safe from harm, like rain, wind, or a bump."),
        ("What is a mystery?",
         "A mystery is a puzzle where something is missing, hidden, or hard to explain until you look closely."),
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
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    for o in world.objects.values():
        bits = []
        if o.protective:
            bits.append("protective")
        if o.hidden:
            bits.append("hidden")
        if o.borrowed:
            bits.append("borrowed")
        if o.broken:
            bits.append("broken")
        lines.append(f"  {o.id:10} (object    ) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
protective(X) :- item(X), protective_item(X).
conflict(helper) :- least(helper), doubt(helper), stubborn(helper).
mystery_solved(M) :- mystery(M), clue_found(M), fixed(M).
valid_setting(S) :- setting(S).
valid_story(S, M) :- valid_setting(S), mystery(M), protective_item(M).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    for oid, o in MYSTERIES.items():
        lines.append(asp.fact("protective_item", oid))
    for mid in MYSTERIES:
        lines.append(asp.fact("clue_found", mid))
        lines.append(asp.fact("fixed", mid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import sys as _sys
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH between ASP and Python valid_combos().")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, mystery=None, move=None, name=None, carpenter_name=None, helper_name=None), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP parity and story generation smoke test passed.")
    return rc


CURATED = [
    StoryParams("village", "roof_tile", "brace", "Mara", "Joren", "Nell"),
    StoryParams("mill", "door_latch", "latch", "Elsa", "Bram", "Pip"),
    StoryParams("market", "lantern_hook", "hook", "Rin", "Pavel", "Sera"),
]


def _explain_rejection(mystery: Mystery, move: ConflictMove) -> str:
    return f"(No story: the move '{move.id}' does not fit the mystery of the {mystery.missing.replace('_', ' ')}.)"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible story combinations:\n")
        for setting, mystery in asp_valid_combos():
            print(f"  {setting:10} {mystery}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid in SETTINGS:
        for mid in MYSTERIES:
            if any(reasonableness_ok(MYSTERIES[mid], mv) for mv in MOVES.values()):
                combos.append((sid, mid))
    return combos


def world_knowledge_qa(_: World) -> list[tuple[str, str]]:
    return [
        ("What does protective mean?",
         "Protective means made to keep something safe from harm."),
        ("What does a carpenter do?",
         "A carpenter builds and repairs things from wood."),
        ("What is a mystery?",
         "A mystery is something hidden or missing that you can solve by looking carefully."),
    ]


if __name__ == "__main__":
    main()
