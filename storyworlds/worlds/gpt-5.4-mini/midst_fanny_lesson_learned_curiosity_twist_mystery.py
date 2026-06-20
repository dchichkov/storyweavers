#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/midst_fanny_lesson_learned_curiosity_twist_mystery.py
=====================================================================================

A small standalone storyworld in a mystery style.

Premise
-------
A curious child, Fanny, follows a tiny mystery in a quiet place at the very
midst of an ordinary day. The clue trail begins with a missing object, grows into
a twist, and ends with a lesson learned: look carefully, ask kindly, and check
the simplest place first.

This world keeps the domain small and classical:
- typed entities with physical meters and emotional memes
- state-driven narration
- a reasonableness gate
- inline ASP twin for parity checks
- three QA sets grounded in world state
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
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Setting:
    id: str
    place: str
    mood: str
    hiding_places: list[str]
    note: str

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
class Clue:
    id: str
    label: str
    where_seen: str
    curiosity: int
    mystery: int
    story_hint: str
    qa_hint: str
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
class Twist:
    id: str
    label: str
    reveal: str
    lesson: str
    ending_image: str
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


def _r_attention(world: World) -> list[str]:
    out: list[str] = []
    fanny = world.get("Fanny")
    if fanny.meters["noticed"] >= THRESHOLD and ("attention", "fanny") not in world.fired:
        world.fired.add(("attention", "fanny"))
        fanny.memes["curiosity"] += 1
        out.append("__attention__")
    return out


def _r_search(world: World) -> list[str]:
    out: list[str] = []
    fanny = world.get("Fanny")
    clue = world.get("clue")
    if fanny.memes["curiosity"] < THRESHOLD:
        return out
    if fanny.meters["searched"] < THRESHOLD:
        return out
    if clue.meters["found"] >= THRESHOLD:
        return out
    sig = ("find", clue.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    clue.meters["found"] += 1
    out.append("__find__")
    return out


def _r_twist(world: World) -> list[str]:
    out: list[str] = []
    clue = world.get("clue")
    twist = world.get("twist")
    if clue.meters["found"] < THRESHOLD:
        return out
    if twist.meters["revealed"] >= THRESHOLD:
        return out
    sig = ("twist", twist.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    twist.meters["revealed"] += 1
    out.append("__twist__")
    return out


CAUSAL_RULES = [
    Rule("attention", "mind", _r_attention),
    Rule("search", "mind", _r_search),
    Rule("twist", "plot", _r_twist),
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


def predict_find(world: World) -> bool:
    sim = world.copy()
    sim.get("Fanny").meters["searched"] += 1
    propagate(sim, narrate=False)
    return sim.get("clue").meters["found"] >= THRESHOLD


def reasonableness_ok(setting: Setting, clue: Clue, twist: Twist) -> bool:
    return clue.id in setting.hiding_places and clue.mystery >= 1 and twist.id != clue.id


def introduce(world: World, kid: Entity, setting: Setting) -> None:
    kid.memes["joy"] += 1
    world.say(
        f"At the midst of a quiet afternoon, {kid.id} wandered through "
        f"{setting.place}. {setting.note}"
    )


def curiosity(world: World, kid: Entity, clue: Clue) -> None:
    kid.memes["curiosity"] += 1
    kid.meters["noticed"] += 1
    world.say(
        f"{kid.id} noticed something odd {clue.where_seen}. "
        f"{kid.pronoun().capitalize()} could not stop wondering about it."
    )
    world.say(
        f'"What is that?" {kid.id} whispered. The question tickled '
        f"{kid.pronoun('possessive')} curiosity."
    )


def search(world: World, kid: Entity, clue: Clue) -> None:
    kid.meters["searched"] += 1
    world.say(
        f"{kid.id} looked under cushions, behind a chair, and in the quiet corners "
        f"where little secrets like to hide."
    )
    if predict_find(world):
        world.say(
            f"{kid.id} thought the answer had to be near. "
            f"{kid.pronoun().capitalize()} was right to keep looking."
        )


def find_clue(world: World, clue: Clue, kid: Entity) -> None:
    world.say(
        f"At last, {kid.id} found {clue.label}. "
        f"It had been tucked away {clue.where_seen} all along."
    )


def reveal_twist(world: World, twist: Twist, clue: Clue, kid: Entity) -> None:
    kid.memes["surprise"] += 1
    world.say(
        f"Then came the twist: {twist.reveal} "
        f"{twist.ending_image}"
    )
    world.say(
        f"{kid.id} blinked, then smiled. The mystery was not scary after all; "
        f"it was just a little mix-up."
    )


def lesson(world: World, twist: Twist, kid: Entity) -> None:
    kid.memes["lesson"] += 1
    kid.memes["calm"] += 1
    world.say(
        f"{twist.lesson} {kid.id} learned to check the simplest place first and "
        f"to ask kindly when something seemed strange."
    )


def tell(setting: Setting, clue: Clue, twist: Twist, name: str = "Fanny") -> World:
    world = World()
    fanny = world.add(Entity(id=name, kind="character", type="girl", role="curious"))
    friend = world.add(Entity(id="Milo", kind="character", type="boy", role="helper"))
    room = world.add(Entity(id="room", type="room", label=setting.place))
    clue_ent = world.add(Entity(id="clue", type="thing", label=clue.label))
    twist_ent = world.add(Entity(id="twist", type="thing", label=twist.label))
    world.facts.update(setting=setting, clue=clue, twist=twist, kid=fanny, friend=friend, room=room,
                       clue_ent=clue_ent, twist_ent=twist_ent)

    introduce(world, fanny, setting)
    world.para()
    curiosity(world, fanny, clue)
    search(world, fanny, clue)
    propagate(world, narrate=True)
    world.para()
    find_clue(world, clue, fanny)
    reveal_twist(world, twist, clue, fanny)
    lesson(world, twist, fanny)
    return world


SETTINGS = {
    "garden": Setting(
        id="garden",
        place="the garden path",
        mood="quiet",
        hiding_places=["bench", "garden path", "flower pot"],
        note="The leaves were still, and a single fanny pack lay near a bench."
    ),
    "library": Setting(
        id="library",
        place="the little library",
        mood="hushed",
        hiding_places=["book cart", "reading nook", "lamp table"],
        note="The room was hushed, and a round lamp made a bright pool on the floor."
    ),
    "kitchen": Setting(
        id="kitchen",
        place="the kitchen",
        mood="warm",
        hiding_places=["bread box", "chair", "counter corner"],
        note="The kettle had gone quiet, and a fanny apron hung on a hook."
    ),
}

CLUES = {
    "fanny_pack": Clue(
        id="fanny_pack",
        label="a small fanny pack",
        where_seen="near a bench",
        curiosity=2,
        mystery=2,
        story_hint="The fanny pack looked out of place in the stillness.",
        qa_hint="It was a little bag that someone had set down and forgotten.",
        tags={"fanny", "bag", "mystery"},
    ),
    "note": Clue(
        id="note",
        label="a folded note",
        where_seen="under a lamp",
        curiosity=2,
        mystery=2,
        story_hint="The folded note looked like it wanted to be read.",
        qa_hint="A folded note is a message written on paper.",
        tags={"note", "mystery"},
    ),
    "key": Clue(
        id="key",
        label="a tiny brass key",
        where_seen="behind a flower pot",
        curiosity=2,
        mystery=3,
        story_hint="The tiny brass key flashed once in the middle of the calm day.",
        qa_hint="A brass key can open a lock if it fits.",
        tags={"key", "mystery"},
    ),
}

TWISTS = {
    "mixup": Twist(
        id="mixup",
        label="a simple mix-up",
        reveal="the missing thing was never lost at all; it had been put away by mistake.",
        lesson="The lesson learned was gentle:",
        ending_image="The little clue felt ordinary now, sitting safely in plain sight.",
        tags={"twist", "lesson"},
    ),
    "borrowed": Twist(
        id="borrowed",
        label="a borrowed item",
        reveal="the clue belonged to Milo, who had lent it and then forgotten to say so.",
        lesson="The lesson learned was clear:",
        ending_image="Milo waved and showed that nothing had been stolen, only borrowed.",
        tags={"twist", "lesson"},
    ),
    "hide_and_seek": Twist(
        id="hide_and_seek",
        label="a game of hide and seek",
        reveal="the clue was part of a game, and the hiding place was meant to be found.",
        lesson="The lesson learned was bright:",
        ending_image="The hiding place made sense at once, like a puzzle piece clicking home.",
        tags={"twist", "lesson"},
    ),
}

GIRL_NAMES = ["Fanny", "Mina", "Lila", "Nora", "Ivy"]
BOY_NAMES = ["Milo", "Theo", "Ben", "Owen", "Leo"]
TRAITS = ["curious", "careful", "bright", "gentle"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    clue: str
    twist: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, s in SETTINGS.items():
        for cid, c in CLUES.items():
            for tid, t in TWISTS.items():
                if reasonableness_ok(s, c, t):
                    out.append((sid, cid, tid))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting, clue, twist = f["setting"], f["clue"], f["twist"]
    return [
        f'Write a mystery story for a young child that includes the words "midst" and "fanny".',
        f"Tell a gentle mystery set in {setting.place} where {f['kid'].id} follows a clue and discovers a twist.",
        f"Write a short curious story about {clue.label} and end with a clear lesson learned.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    kid, setting, clue, twist = f["kid"], f["setting"], f["clue"], f["twist"]
    return [
        ("Who is the story about?",
         f"It is about {kid.id}, who is a curious child solving a small mystery."),
        ("What did {kid} notice?".replace("{kid}", kid.id),
         f"{kid.id} noticed {clue.label} {clue.where_seen}, and that odd sight made {kid.pronoun('possessive')} curiosity wake up."),
        ("What was the twist?",
         f"{twist.reveal} That changed the story from puzzling to simple."),
        ("What lesson did {kid} learn?".replace("{kid}", kid.id),
         f"{twist.lesson} {kid.id} learned to check the simplest place first and to ask kindly before worrying."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    clue = f["clue"]
    if clue.id == "fanny_pack":
        return [("What is a fanny pack?",
                 "A fanny pack is a small bag that people wear around the waist to carry little things.")]
    if clue.id == "key":
        return [("What does a key do?",
                 "A key can open a lock when it fits the lock correctly.")]
    return [("What is a clue?",
             "A clue is a little bit of information that helps solve a mystery.")]


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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
noticed(fanny) :- curiosity(fanny), seen(clue).
find(clue) :- noticed(fanny), searched(fanny), clue_ok(clue).
twist(twist) :- find(clue), twist_ok(twist).
outcome(lesson_learned) :- twist(twist).
"""

def asp_facts() -> str:
    import asp
    lines = [asp.fact("character", "fanny")]
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("curiosity", "fanny", c.curiosity))
        lines.append(asp.fact("mystery", cid, c.mystery))
        lines.append(asp.fact("seen", cid))
        lines.append(asp.fact("clue_ok", cid))
    for tid in TWISTS:
        lines.append(asp.fact("twist_ok", tid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    # smoke test
    sample = generate(resolve_params(argparse.Namespace(setting=None, clue=None, twist=None, name=None, seed=None), random.Random(3)))
    if not sample.story.strip():
        print("MISMATCH: empty story from smoke test")
        return 1
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        rc = 1
        print("MISMATCH in valid_combos:")
        print(" python-only:", sorted(py - cl))
        print(" clingo-only:", sorted(cl - py))
    else:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld with curiosity and a lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--twist", choices=TWISTS)
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
              if (args.setting is None or c[0] == args.setting)
              and (args.clue is None or c[1] == args.clue)
              and (args.twist is None or c[2] == args.twist)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, twist = rng.choice(sorted(combos))
    name = args.name or "Fanny"
    return StoryParams(setting, clue, twist, name)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], CLUES[params.clue], TWISTS[params.twist], params.name)
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
    StoryParams("garden", "fanny_pack", "mixup", "Fanny"),
    StoryParams("library", "note", "borrowed", "Fanny"),
    StoryParams("kitchen", "key", "hide_and_seek", "Fanny"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
