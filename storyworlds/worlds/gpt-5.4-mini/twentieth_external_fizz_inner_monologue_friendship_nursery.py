#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/twentieth_external_fizz_inner_monologue_friendship_nursery.py
============================================================================================

A small standalone storyworld for a nursery-rhyme-like friendship tale.
It uses typed entities with physical meters and emotional memes, a tiny causal
simulation, grounded QA generation, and an inline ASP twin.

Core premise
------------
Two friends prepare a tiny rhyme-time treat. One child wants to make a big
external fizz by shaking a bottle, while the other has an inner monologue that
warns about the spill and the noise. They choose a gentler way, count to the
twentieth beat, and finish with a bright, friendly ending.
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
COUNT_TARGET = 20


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    age: int = 0
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
        return self.label or self.id



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
    scene: str

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
class FriendAction:
    id: str
    verb: str
    inner_thought: str
    danger: str
    gentle_way: str
    ending_image: str
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
class ObjectCfg:
    id: str
    label: str
    kind: str
    fizzy: bool = False
    spillable: bool = False
    noisy: bool = False
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


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


def _r_fizz(world: World) -> list[str]:
    out: list[str] = []
    bottle = world.entities.get("bottle")
    if bottle and bottle.meters["shaken"] >= THRESHOLD and "fizz" not in world.fired:
        world.fired.add(("fizz",))
        bottle.meters["fizzing"] += 1
        world.get("room").meters["mess"] += 1
        for e in world.characters():
            e.memes["surprise"] += 1
        out.append("__fizz__")
    return out


CAUSAL_RULES = [Rule("fizz", "physical", _r_fizz)]


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


def predict_fizz(world: World) -> dict:
    sim = world.copy()
    sim.get("bottle").meters["shaken"] += 1
    propagate(sim, narrate=False)
    return {
        "fizzing": sim.get("bottle").meters["fizzing"] >= THRESHOLD,
        "mess": sim.get("room").meters["mess"],
    }


def tell(setting: Setting, action: FriendAction, child_a: str = "Mina", child_b: str = "Rory",
         a_gender: str = "girl", b_gender: str = "boy", parent: str = "mother") -> World:
    world = World(setting)
    a = world.add(Entity(id=child_a, kind="character", type=a_gender, role="instigator"))
    b = world.add(Entity(id=child_b, kind="character", type=b_gender, role="cautioner"))
    mom = world.add(Entity(id="Parent", kind="character", type=parent, role="parent", label="the parent"))
    room = world.add(Entity(id="room", type="room", label="the little room"))
    bottle = world.add(Entity(id="bottle", type="object", label="the bottle", fizzy=True, spillable=True, noisy=True))
    cup = world.add(Entity(id="cup", type="object", label="the cup"))

    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"In a small bright room, {a.id} and {b.id} sat side by side. {setting.scene}"
    )
    world.say(
        f"{a.id} counted taps on the table, and {b.id} counted along in a soft little song."
    )
    world.say(
        f'"One, two, three," they sang, "and on to the twentieth!"'
    )

    world.para()
    world.say(
        f"{a.id} looked at {action.label} and smiled. {a.id} wanted to {action.verb}, and {action.inner_thought}."
    )
    world.say(
        f"But {b.id} listened to a quiet inner monologue: {action.danger}."
    )

    pred = predict_fizz(world)
    world.facts["predicted"] = pred

    if pred["fizzing"]:
        world.say(
            f"{b.id} pointed to the bottle and whispered, \"Let's not make the fizz spill all over the floor.\""
        )
        world.say(
            f"{a.id} nodded, because friendship felt warmer than the big splash idea."
        )
        a.memes["trust"] += 1
        b.memes["trust"] += 1
        world.para()
        world.say(
            f"So they chose the gentle way instead. They poured a little into the cup, one careful stream at a time."
        )
        world.say(
            f"The bottle gave a tiny external fizz, like a mouse tapping a drum, and the room stayed neat and sweet."
        )
        world.say(
            f"At the twentieth count, the cup stood full, the song stayed soft, and {action.ending_image}."
        )
        outcome = "gentle"
    else:
        world.say(
            f"{b.id} smiled and said the bottle could wait. They did not need the fizz after all."
        )
        world.para()
        world.say(
            f"Together they used the cup in a careful way, and {action.ending_image}."
        )
        outcome = "calm"

    world.facts.update(
        instigator=a, cautioner=b, parent=mom, room=room, bottle=bottle, cup=cup,
        action=action, setting=setting, outcome=outcome, counted=COUNT_TARGET,
    )
    return world


SETTINGS = {
    "nursery": Setting(
        "nursery",
        "the nursery",
        "The nursery smelled of crayons and warm milk, and the little rug made a square for sitting."
    ),
    "playroom": Setting(
        "playroom",
        "the playroom",
        "The playroom was bright with blocks and ribbons, and a tiny table waited for tea-time play."
    ),
    "sunroom": Setting(
        "sunroom",
        "the sunroom",
        "The sunroom shone through the glass, and the windows made little gold patches on the floor."
    ),
}

ACTIONS = {
    "shake": FriendAction(
        "shake",
        "shake the bottle for a bigger fizz",
        "I can hear a brave little bounce in my heart",
        "If I shake it too hard, the fizz may leap out and make a sticky mess",
        "pour it slowly and listen to the bubbles sing",
        "the bubbles hummed softly and the little room stayed tidy",
        tags={"fizz", "friendship", "inner_monologue"},
    ),
    "tip": FriendAction(
        "tip",
        "tip the bottle too fast",
        "I wonder if the bottle will dance if I tilt it",
        "If I tip it too fast, the external fizz could splatter onto the rug",
        "hold it steady and pour in a thin stream",
        "the bubbles stayed small as pearl beads and nobody slipped",
        tags={"fizz", "friendship", "inner_monologue"},
    ),
}

OBJECTS = {
    "bottle": ObjectCfg("bottle", "the bottle", "object", fizzy=True, spillable=True, noisy=True, tags={"fizz"}),
    "cup": ObjectCfg("cup", "the cup", "object", spillable=True, tags={"cup"}),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "June", "Rita"]
BOY_NAMES = ["Rory", "Theo", "Benn", "Owen", "Finn"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    action: str
    name_a: str
    gender_a: str
    name_b: str
    gender_b: str
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


def valid_combos() -> list[tuple[str, str]]:
    return [(s, a) for s in SETTINGS for a in ACTIONS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme friendship storyworld with inner monologue and fizz.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
    ap.add_argument("--gender-a", choices=["girl", "boy"])
    ap.add_argument("--gender-b", choices=["girl", "boy"])
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
    if args.setting and args.action:
        if (args.setting, args.action) not in valid_combos():
            raise StoryError("(No valid combination matches the given options.)")
    setting = args.setting or rng.choice(list(SETTINGS))
    action = args.action or rng.choice(list(ACTIONS))
    ga = args.gender_a or rng.choice(["girl", "boy"])
    gb = args.gender_b or ("boy" if ga == "girl" else "girl")
    na = args.name_a or rng.choice(GIRL_NAMES if ga == "girl" else BOY_NAMES)
    nb = args.name_b or rng.choice([n for n in (GIRL_NAMES if gb == "girl" else BOY_NAMES) if n != na])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, action, na, ga, nb, gb, parent)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    act = f["action"]
    return [
        f'Write a nursery-rhyme-like story about friendship that includes the words "twentieth" and "external fizz".',
        f"Tell a gentle story where {a.id} wants to {act.verb}, but {b.id}'s inner monologue warns about the fizz, and they choose the safer way.",
        f"Write a short child-friendly story with a careful bubble moment, a friendship choice, and a happy ending at the twentieth count.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    act = f["action"]
    setting = f["setting"]
    return [
        ("Who are the story friends?", f"The story is about {a.id} and {b.id}. They sit together in {setting.place} and make a gentle little game out of counting."),
        ("What did {0} want to do with the bottle?".format(a.id), f"{a.id} wanted to {act.verb}. The idea seemed exciting, but it could make the fizz jump out too fast."),
        ("What did {0} think in the inner monologue?".format(b.id), f"{b.id} thought that {act.danger}. That quiet thought helped {b.id} speak up kindly before the bottle got shaken."),
        ("How did the friends solve the problem?", f"They chose the gentle way and poured slowly into the cup. That kept the external fizz small and let them finish at the twentieth count without a mess."),
        ("How did the story end?", f"It ended with a tidy room, a full cup, and two friends feeling close and proud. The last image proves they kept playing together without making a sticky spill."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is fizz?", "Fizz is the bubbly sound and feeling made by gas in a drink. It can rise fast if a bottle is shaken too hard."),
        ("What is an inner monologue?", "An inner monologue is the quiet voice inside your head. It helps a person think before they speak or act."),
        ("What does friendship mean?", "Friendship means being kind, listening, and helping each other. Friends can stop each other from doing something unkind or unsafe."),
        ("What does twentieth mean?", "Twentieth means number twenty. If you count to the twentieth, you have counted twenty things or twenty beats."),
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


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ACTIONS[params.action], params.name_a, params.name_b, params.gender_a, params.gender_b, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


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
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
shaken_fizz :- shaken(B), fizzy(B).
mess(Room) :- shaken(B), fizzy(B), room(Room).
outcome(gentle) :- friend_choice.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid in ACTIONS:
        lines.append(asp.fact("action", aid))
    lines.append(asp.fact("count_target", COUNT_TARGET))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show setting/1. #show action/1."))
    return sorted(set(asp.atoms(model, "setting")))


def asp_verify() -> int:
    import asp
    # simple parity: all combos are valid in both models
    py = set(valid_combos())
    cl = {(s, a) for (s,) in asp.atoms(asp.one_model(asp_program("", "#show setting/1. #show action/1.")), "setting") for a in ACTIONS}
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python.")
    return 1


def build_story_params_from_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
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


CURATED = [
    StoryParams("nursery", "shake", "Mina", "girl", "Rory", "boy", "mother"),
    StoryParams("playroom", "tip", "Lila", "girl", "Theo", "boy", "father"),
    StoryParams("sunroom", "shake", "Nora", "girl", "Finn", "boy", "mother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show setting/1. #show action/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} compatible combos:")
        for s, a in valid_combos():
            print(f"  {s:10} {a}")
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
