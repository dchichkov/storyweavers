#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/yum_referee_gonk_surprise_conflict_bedtime_story.py
====================================================================================

A small standalone storyworld for a bedtime-style tale: a child, a tiny conflict,
a surprising helper, and a calm ending that feels safe and cozy.

The seed words for this world are:
- yum
- referee
- gonk

The world keeps two kinds of state:
- physical meters: sleepiness, mess, calm, glow
- emotional memes: worry, grumpiness, surprise, relief, kindness

The story premise is simple:
A child is trying to settle down for bed, but a silly "referee" rule in a bedtime
game turns into a conflict. A tiny gonk appears with a surprising solution, and
the bedtime ends with yum and calm instead of fuss.

This script follows the Storyweavers contract:
- typed entities with meters and memes
- state-driven narration
- a Python reasonableness gate
- an inline ASP twin
- QA generated from world state, not by parsing the rendered story
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
    cozy_detail: str
    dark_detail: str
    bed_detail: str
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
class RoleItem:
    id: str
    label: str
    phrase: str
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
class ConflictMove:
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
    tag: str
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


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if not child:
        return out
    if child.memes["grumpiness"] < THRESHOLD:
        return out
    sig = ("conflict", "child")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["worry"] += 1
    if "referee" in world.entities:
        world.get("referee").memes["sternness"] += 1
    out.append("__conflict__")
    return out


CAUSAL_RULES = [Rule("conflict", "social", _r_conflict)]


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


def sensible_moves() -> list[ConflictMove]:
    return [m for m in MOVES.values() if m.sense >= 2]


def valid_combo(setting: Setting, snack: RoleItem, move: ConflictMove) -> bool:
    return "bedtime" in setting.tags and "yum" in snack.tags and move.sense >= 2


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for mid, move in MOVES.items():
            for rid, snack in SNACKS.items():
                if valid_combo(setting, snack, move):
                    combos.append((sid, rid, mid))
    return combos


def is_resolved(move: ConflictMove, delay: int) -> bool:
    return move.power >= 1 + delay


def bedtime_setup(world: World, child: Entity, referee: Entity, setting: Setting) -> None:
    child.memes["sleepiness"] += 1
    child.memes["kindness"] += 1
    world.say(
        f"At {setting.place}, the night was soft and still. {setting.cozy_detail} "
        f"{setting.bed_detail}"
    )
    world.say(
        f"{child.id} was getting sleepy, but {referee.label_word} had one more game "
        f"to finish before bed."
    )


def snack_hint(world: World, snack: RoleItem) -> None:
    world.say(
        f"On the pillow there was a little surprise: {snack.phrase}. It looked "
        f"so small and bright that even the word yum seemed to bounce."
    )


def argue(world: World, child: Entity, referee: Entity, move: ConflictMove) -> None:
    child.memes["grumpiness"] += 1
    world.say(
        f'{child.id} frowned. "That is not fair," {child.id} said, and the '
        f"{referee.label_word} shook {referee.pronoun('possessive')} head."
    )
    world.say(
        f'"A bedtime rule is a bedtime rule," {referee.id} said, which made the '
        f"little room feel a bit tense."
    )


def surprise_gonk(world: World, gonk: Entity, snack: RoleItem, child: Entity) -> None:
    child.memes["surprise"] += 1
    child.memes["relief"] += 1
    gonk.memes["helpfulness"] += 1
    world.say(
        f"Then a tiny gonk peeked out from behind the blanket, wearing a shy grin. "
        f'It whispered, "No need for a fuss. Here is the {snack.label}, and it is '
        f"yum."'
    )


def soothe(world: World, child: Entity, referee: Entity, snack: RoleItem, move: ConflictMove) -> None:
    child.memes["calm"] += 1
    child.memes["kindness"] += 1
    referee.memes["softness"] += 1
    world.say(
        f"{referee.label_word} blinked, then laughed gently. "
        f'"Well," {referee.id} said, "that is a surprise worth sharing."'
    )
    world.say(
        f"{child.id} took the {snack.label}, and the room grew warm with quiet yum "
        f"instead of grumpy words."
    )


def end_sleep(world: World, child: Entity, gonk: Entity, setting: Setting) -> None:
    child.memes["sleepiness"] += 2
    child.meters["calm"] += 1
    gonk.memes["glad"] += 1
    world.say(
        f"After that, {child.id} tucked the blanket under the chin, and the tiny "
        f"gonk waved goodnight."
    )
    world.say(
        f"The moon watched over {setting.place}, and everything felt cozy, fair, "
        f"and ready for sleep."
    )


def tell(setting: Setting, snack: RoleItem, move: ConflictMove,
         child_name: str = "Mina", child_gender: str = "girl",
         referee_name: str = "Pip", referee_gender: str = "boy",
         gonk_name: str = "Nubble") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    referee = world.add(Entity(id=referee_name, kind="character", type=referee_gender, role="referee"))
    gonk = world.add(Entity(id=gonk_name, kind="character", type="thing", role="gonk"))
    world.facts["setting"] = setting
    world.facts["snack"] = snack
    world.facts["move"] = move
    world.facts["child"] = child
    world.facts["referee"] = referee
    world.facts["gonk"] = gonk

    bedtime_setup(world, child, referee, setting)
    world.para()
    snack_hint(world, snack)
    argue(world, child, referee, move)
    world.para()
    surprise_gonk(world, gonk, snack, child)
    if is_resolved(move, 0):
        soothe(world, child, referee, snack, move)
        world.para()
        end_sleep(world, child, gonk, setting)
    else:
        world.say("But the problem stayed prickly, and the bedtime felt too bumpy to soften.")
    world.facts["resolved"] = is_resolved(move, 0)
    return world


SETTINGS = {
    "bedtime": Setting(
        id="bedtime",
        place="the little bedroom",
        cozy_detail="A lamp glowed like a sleepy star, and the sheets were tucked in neat.",
        dark_detail="The corners were dark and hush-soft.",
        bed_detail="The bed waited with a round pillow and a folded blanket.",
        tags={"bedtime"},
    ),
    "campbed": Setting(
        id="campbed",
        place="the blanket fort",
        cozy_detail="A paper moon hung above the cushions, and everything smelled like soap.",
        dark_detail="The fort made a tiny cave of shadows.",
        bed_detail="The floor mattress was lined with one soft quilt.",
        tags={"bedtime"},
    ),
}

SNACKS = {
    "yum_cookie": RoleItem(
        id="yum_cookie",
        label="cookie",
        phrase="a crumbly little cookie",
        tags={"yum"},
    ),
    "yum_pear": RoleItem(
        id="yum_pear",
        label="pear slice",
        phrase="a sweet pear slice",
        tags={"yum"},
    ),
}

MOVES = {
    "gentle_rule": ConflictMove(
        id="gentle_rule",
        sense=3,
        power=2,
        text="kept the bedtime game fair without making anyone sad",
        fail="tried to keep the game fair, but the fuss only grew",
        qa_text="kept the bedtime game fair in a gentle way",
        tags={"conflict"},
    ),
    "countdown": ConflictMove(
        id="countdown",
        sense=3,
        power=2,
        text="counted softly to calm the room and help everyone agree",
        fail="counted too late to calm the room",
        qa_text="counted softly until the room felt calm again",
        tags={"conflict"},
    ),
    "quiet_swap": ConflictMove(
        id="quiet_swap",
        sense=2,
        power=1,
        text="swapped the rule for a quieter bedtime choice",
        fail="swapped the rule, but the grumble stayed",
        qa_text="swapped the rule for a quieter choice",
        tags={"conflict"},
    ),
    "splash_bucket": ConflictMove(
        id="splash_bucket",
        sense=1,
        power=1,
        text="dumped a bucket of splashy noise on the problem",
        fail="made the problem even louder",
        qa_text="made a loud mess of the problem",
        tags={"conflict"},
    ),
}

CURATED = [
    StoryParams := None
]


@dataclass
class StoryParams:
    setting: str
    snack: str
    move: str
    child_name: str = "Mina"
    child_gender: str = "girl"
    referee_name: str = "Pip"
    referee_gender: str = "boy"
    gonk_name: str = "Nubble"
    delay: int = 0
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
    StoryParams(setting="bedtime", snack="yum_cookie", move="gentle_rule", child_name="Mina", child_gender="girl", referee_name="Pip", referee_gender="boy", gonk_name="Nubble", delay=0),
    StoryParams(setting="campbed", snack="yum_pear", move="countdown", child_name="Owen", child_gender="boy", referee_name="Tess", referee_gender="girl", gonk_name="Glim", delay=0),
]


def explain_rejection(move: ConflictMove) -> str:
    return f"(No story: the move '{move.id}' is too shaky for a bedtime conflict.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.move and MOVES[args.move].sense < 2:
        raise StoryError(explain_rejection(MOVES[args.move]))
    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.snack is None or c[1] == args.snack)
        and (args.move is None or c[2] == args.move)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, snack, move = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting,
        snack=snack,
        move=move,
        child_name=args.child_name or rng.choice(["Mina", "Owen", "Lia", "Noah"]),
        child_gender=args.child_gender or rng.choice(["girl", "boy"]),
        referee_name=args.referee_name or rng.choice(["Pip", "Tess", "Bo", "June"]),
        referee_gender=args.referee_gender or rng.choice(["girl", "boy"]),
        gonk_name=args.gonk_name or rng.choice(["Nubble", "Glim", "Moss", "Wink"]),
        delay=args.delay,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story that includes the words "yum", "referee", and "gonk".',
        f"Tell a cozy conflict story where {f['child'].id} and the referee disagree at bedtime, then a gonk brings a surprising yum treat.",
        f"Write a gentle bedtime tale with a surprise helper and a small argument that turns soft by the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    referee = f["referee"]
    snack = f["snack"]
    move = f["move"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id}, {referee.id}, and a tiny gonk who appears at bedtime. The room starts quiet, then the little conflict changes the night."),
        ("Why were they in conflict?",
         f"{child.id} wanted the bedtime moment to feel different, but {referee.id} was trying to keep the bedtime rule fair. That made the room feel tense for a little while."),
        ("What surprise changed the mood?",
         f"A tiny gonk showed up with {snack.phrase}. The surprise turned the grumpy moment into something softer."),
    ]
    if f.get("resolved"):
        qa.append((
            "How did the conflict end?",
            f"{referee.id} laughed gently, and {child.id} accepted the calm choice. The bedtime problem settled because the surprise made everyone kinder."
        ))
    else:
        qa.append((
            "How did the conflict end?",
            f"It stayed bumpy, so the bedtime did not fully soften. The story ends by showing that not every fuss turns smooth right away."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does yum mean?",
         "Yum is a word people say when food looks or tastes especially good. It usually sounds happy and playful."),
        ("What is a referee?",
         "A referee is someone who helps keep rules fair in a game or contest. The referee watches closely and speaks up when there is a problem."),
        ("What is a gonk?",
         "A gonk is a silly little creature from make-believe stories. Gonks are often tiny, strange, and friendly."),
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
        lines.append(f"  {e.id:8} ({e.type:7}) meters={dict(meters)} memes={dict(memes)} role={e.role}")
    return "\n".join(lines)


ASP_RULES = r"""
resolved :- move(M), power(M, P), delay(D), P >= D + 1.
conflict :- child, referee, gonk.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sid in SNACKS:
        lines.append(asp.fact("snack", sid))
        lines.append(asp.fact("yum", sid))
    for mid, move in MOVES.items():
        lines.append(asp.fact("move", mid))
        lines.append(asp.fact("sense", mid, move.sense))
        lines.append(asp.fact("power", mid, move.power))
    lines.append(asp.fact("referee"))
    lines.append(asp.fact("gonk"))
    lines.append(asp.fact("child"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid_combos()")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    else:
        print("OK: story generation smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime storyworld: yum, referee, gonk.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--move", choices=MOVES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--referee-name")
    ap.add_argument("--referee-gender", choices=["girl", "boy"])
    ap.add_argument("--gonk-name")
    ap.add_argument("--delay", type=int, default=0)
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


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.snack not in SNACKS or params.move not in MOVES:
        raise StoryError("Invalid story parameters.")
    world = tell(
        SETTINGS[params.setting],
        SNACKS[params.snack],
        MOVES[params.move],
        child_name=params.child_name,
        child_gender=params.child_gender,
        referee_name=params.referee_name,
        referee_gender=params.referee_gender,
        gonk_name=params.gonk_name,
    )
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
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
