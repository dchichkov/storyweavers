#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/benefit_vein_conflict_mystery_to_solve_moral.py
================================================================================

A small ghost-story world about a child, a whispering mystery, a vein of light
under the house, a conflict about whether to follow a scary clue, and a moral
ending that proves a better choice was made.

The seed words are "benefit" and "vein". The story world treats them as two
important ideas in the tale:
- a "benefit" is the good result of helping, sharing, or being brave
- a "vein" is a thin line of color or light, like a vein in marble or a vein of
  silver running through old stone

The model supports three story outcomes:
- a child solves a spooky mystery with help
- a conflict is resolved by telling the truth or sharing the clue
- a moral value is learned at the end
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
class Setting:
    id: str
    place: str
    mood: str
    shadow: str
    affords: set[str] = field(default_factory=set)

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
    hidden_thing: str
    reveal: str
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
class ConflictChoice:
    id: str
    temptation: str
    danger: str
    brave_act: str
    moral: str
    sense: int
    power: int
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

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


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


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["haunted"] < THRESHOLD:
            continue
        sig = ("fear", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["fear"] += 1
        out.append("__fear__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("solved") and ("relief", "house") not in world.fired:
        world.fired.add(("relief", "house"))
        for e in world.characters():
            e.memes["relief"] += 1
        out.append("The house felt lighter at once.")
    return out


CAUSAL_RULES = [Rule("fear", "social", _r_fear), Rule("relief", "social", _r_relief)]


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


def mystery_at_risk(mystery: Mystery, setting: Setting) -> bool:
    return mystery.id in setting.affords


def sensible_choices() -> list[ConflictChoice]:
    return [c for c in CHOICES.values() if c.sense >= 2]


def solveable(choice: ConflictChoice, mystery: Mystery) -> bool:
    return choice.power >= 1 and mystery.id in mystery.tags


def _do_haunt(world: World, child: Entity) -> None:
    child.meters["haunted"] += 1
    propagate(world, narrate=False)


def predict_world(world: World, child: Entity, mystery: Mystery, choice: ConflictChoice) -> dict:
    sim = world.copy()
    _do_haunt(sim, sim.get(child.id))
    sim.facts["solved"] = choice.power >= 1
    return {
        "fear": sim.get(child.id).memes["fear"],
        "relief": sim.get(child.id).memes["relief"],
    }


def opening(world: World, child: Entity, friend: Entity, setting: Setting) -> None:
    world.say(
        f"On a cold evening, {child.id} and {friend.id} stepped into {setting.place}, "
        f"where {setting.mood} air moved like a whisper and {setting.shadow} made the walls look watchful."
    )
    world.say(
        f"{child.id} held a candle and listened to the quiet. {friend.id} pointed at a thin vein of light in the old stone and said it looked like the house was keeping a secret."
    )


def conflict(world: World, child: Entity, friend: Entity, mystery: Mystery, choice: ConflictChoice) -> None:
    child.memes["curiosity"] += 1
    child.memes["defiance"] += 1
    world.say(
        f'"Do we follow the clue or run?" {friend.id} asked. {child.id} wanted to follow it right away, because the clue seemed to promise a benefit.'
    )
    world.say(
        f'But the hall felt spooky, and the whisper near the floor said there was something hidden behind the loose board: {mystery.hidden_thing}.'
    )
    world.say(
        f'{friend.id} frowned. "{choice.danger}"'
    )


def warn(world: World, friend: Entity, child: Entity, mystery: Mystery, choice: ConflictChoice) -> None:
    pred = predict_world(world, child, mystery, choice)
    world.facts["predicted_fear"] = pred["fear"]
    world.say(
        f'{friend.id} swallowed hard and said, "We should be careful. If we rush, we will only feel more scared, and nobody will learn the secret the right way."'
    )


def resolve(world: World, child: Entity, friend: Entity, mystery: Mystery, choice: ConflictChoice) -> None:
    child.memes["bravery"] += 1
    child.memes["kindness"] += 1
    world.say(
        f'{child.id} took a breath, nodded, and chose the kind thing. {choice.brave_act.capitalize()}, then they both looked together.'
    )
    world.say(
        f'Behind the board they found {mystery.reveal}, and the strange whisper was only the wind passing through a crack in the basement wall.'
    )
    world.say(
        f'{mystery.reveal.capitalize()} had been making the ghostly sound all along, and the mystery finally made sense.'
    )


def moral(world: World, child: Entity, friend: Entity, choice: ConflictChoice) -> None:
    child.memes["moral"] += 1
    friend.memes["moral"] += 1
    world.say(
        f'At the end, {child.id} learned the moral value of being honest and gentle: a real benefit is not just finding a hidden thing, but helping without fear.'
    )
    world.say(
        f'{friend.id} smiled, and the house was quiet in the best way.'
    )


def tell(setting: Setting, mystery: Mystery, choice: ConflictChoice,
         child_name: str = "Mina", child_gender: str = "girl",
         friend_name: str = "Noah", friend_gender: str = "boy",
         parent_type: str = "mother") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="hero", traits=["curious"]))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend", traits=["careful"]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))

    opening(world, child, friend, setting)
    world.para()
    conflict(world, child, friend, mystery, choice)
    warn(world, friend, child, mystery, choice)
    _do_haunt(world, child)
    world.para()
    resolve(world, child, friend, mystery, choice)
    moral(world, child, friend, choice)

    world.facts.update(
        child=child,
        friend=friend,
        parent=parent,
        setting=setting,
        mystery=mystery,
        choice=choice,
        solved=True,
    )
    return world


SETTINGS = {
    "old_house": Setting("old_house", "the old house", "dusty", "a long dark hallway", affords={"vein"}),
    "attic": Setting("attic", "the attic", "thin", "a line of moon-shadow", affords={"vein"}),
    "cellar": Setting("cellar", "the cellar", "cool", "a cracked beam of light", affords={"vein"}),
}

MYSTERIES = {
    "vein": Mystery("vein", "vein", "a hidden silver vein in the wall", "a silver vein running through the stone", tags={"vein"}),
    "benefit": Mystery("benefit", "benefit", "a helpful note tucked behind the board", "a note that explained the house map", tags={"benefit"}),
}

CHOICES = {
    "ask": ConflictChoice("ask", "follow the whisper alone", "the whisper might lead them into trouble", "asked the parent for a lantern first", "The brave choice is to ask for help before acting.", 3, 2, tags={"ask"}),
    "share": ConflictChoice("share", "keep the clue secret", "secrets make the fear grow", "told the friend the clue out loud", "The kinder choice is to share what you found.", 3, 2, tags={"share"}),
    "wait": ConflictChoice("wait", "rush down the stairs", "rushing makes mysteries worse", "waited until they could see clearly", "Sometimes patience is the safest way to solve a mystery.", 2, 1, tags={"wait"}),
}

GIRL_NAMES = ["Mina", "Ivy", "Luna", "Rose", "Nina", "Clara"]
BOY_NAMES = ["Noah", "Eli", "Theo", "Finn", "Owen", "Sam"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for mid, mystery in MYSTERIES.items():
            if not mystery_at_risk(mystery, setting):
                continue
            for cid, choice in CHOICES.items():
                if choice.sense >= 2 and solveable(choice, mystery):
                    combos.append((sid, mid, cid))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    mystery: str
    choice: str
    child_name: str
    child_gender: str
    friend_name: str
    friend_gender: str
    parent: str
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
    ap = argparse.ArgumentParser(description="A ghost-story world with a mystery, conflict, and moral value.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--choice", choices=CHOICES)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
    if args.mystery and args.setting and not mystery_at_risk(MYSTERIES[args.mystery], SETTINGS[args.setting]):
        raise StoryError("That mystery does not fit that setting.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.choice is None or c[2] == args.choice)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    sid, mid, cid = rng.choice(sorted(combos))
    child_gender = args.gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if child_gender == "girl" else "girl")
    child_name = args.name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    friend_name = args.friend or rng.choice([n for n in (BOY_NAMES if friend_gender == "boy" else GIRL_NAMES) if n != child_name])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(sid, mid, cid, child_name, child_gender, friend_name, friend_gender, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], MYSTERIES[params.mystery], CHOICES[params.choice],
                 params.child_name, params.child_gender, params.friend_name, params.friend_gender, params.parent)
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
        f'Write a ghost-story for a young child that uses the words "benefit" and "vein" and ends with a moral value.',
        f"Tell a spooky mystery story where {f['child'].id} and {f['friend'].id} explore {f['setting'].place} and find a vein in the wall.",
        f'Write a calm ghost story with conflict, a mystery to solve, and a kind moral about helping instead of rushing.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    c = f["child"]
    fr = f["friend"]
    mystery = f["mystery"]
    choice = f["choice"]
    return [
        ("Who is the story about?",
         f"It is about {c.id} and {fr.id}, who went into {f['setting'].place} to solve a spooky mystery. They were scared, but they stayed together."),
        ("What was the mystery?",
         f"They were trying to understand {mystery.reveal}. It only sounded ghostly because the wind was moving through the old house."),
        ("What conflict did they face?",
         f"{c.id} wanted to follow the clue at once, but {fr.id} warned that rushing could make things worse. That conflict pushed them to make a better choice."),
        ("What moral did they learn?",
         f"They learned that kindness, honesty, and patience have a real benefit. The story shows that helping carefully is braver than rushing into the dark."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["mystery"].tags) | set(f["choice"].tags)
    out = []
    if "vein" in tags:
        out.append(("What is a vein in stone?", "A vein is a thin line of a different color or material running through stone, like silver in rock."))
    if "benefit" in tags:
        out.append(("What does benefit mean?", "A benefit is a good result or helpful thing that comes from a choice."))
    out.append(("Why is it smart to ask for help in a spooky place?", "A grown-up can bring a light and help you stay calm, so the mystery can be solved safely."))
    out.append(("What should you do if a place feels too scary to explore alone?", "Stay with someone you trust and ask for help instead of rushing off by yourself."))
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("old_house", "vein", "ask", "Mina", "girl", "Noah", "boy", "mother"),
    StoryParams("attic", "benefit", "share", "Ivy", "girl", "Eli", "boy", "father"),
    StoryParams("cellar", "vein", "wait", "Theo", "boy", "Rose", "girl", "mother"),
]


def explain_rejection(setting: Setting, mystery: Mystery) -> str:
    return f"(No story: the mystery {mystery.id} does not fit the setting {setting.place}.)"


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        for t in sorted(m.tags):
            lines.append(asp.fact("tags", mid, t))
    for cid, c in CHOICES.items():
        lines.append(asp.fact("choice", cid))
        lines.append(asp.fact("sense", cid, c.sense))
        lines.append(asp.fact("power", cid, c.power))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, M, C) :- setting(S), mystery(M), choice(C), affords(S, M), sense(C, X), sense_min(Y), X >= Y.
solvable(M, C) :- mystery(M), choice(C), tags(M, vein), power(C, P), P >= 1.
valid_story(S, M, C) :- valid(S, M, C), solvable(M, C).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid_combos()")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(
            setting=None, mystery=None, choice=None, name=None, friend=None,
            gender=None, friend_gender=None, parent=None
        ), random.Random(777)))
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: verification passed.")
    return rc


def build_story(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


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
        print(asp_program(show="#show valid/3.\n#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a} {b} {c}" for a, b, c in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
                params = build_story(args, random.Random(seed))
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
