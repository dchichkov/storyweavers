#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/oval_botanic_permissive_friendship_sound_effects_mystery.py
==========================================================================================

A small TinyStories-style storyworld about two friends solving a gentle mystery
in a botanic place. The world uses physical meters and emotional memes, a
forward rule engine, a Python reasonableness gate, and an inline ASP twin.

Premise:
- Two friends hear odd sound effects in an oval botanic space.
- A permissive grown-up lets them investigate.
- The clues lead to a harmless mystery and a warm friendship ending.

The seed words are woven into the world model:
- oval
- botanic
- permissive

The style aims for mystery without darkness: curiosity, clues, a reveal, and a
soft ending image that shows what changed.
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
SOUND_THRESHOLD = 1.0
CURIOUS_MIN = 4.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: str = ""
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
class Location:
    id: str
    label: str
    oval: bool = False
    botanic: bool = False
    permissive: bool = False
    quiet: bool = True
    sound_echo: str = ""
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
class Clue:
    id: str
    label: str
    sound: str
    source: str
    visible: str
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
class Action:
    id: str
    sound: str
    method: str
    clue: str
    safe: bool = True
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
        self.location: Optional[Location] = None

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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        c.location = copy.deepcopy(self.location)
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


def _r_echo(world: World) -> list[str]:
    out: list[str] = []
    if not world.location or not world.location.oval:
        return out
    for e in world.characters():
        if e.meters["listening"] < THRESHOLD:
            continue
        sig = ("echo", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["curious"] += 1
        out.append("__echo__")
    return out


def _r_clue(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["listening"] < THRESHOLD:
            continue
        if e.meters["found_clue"] >= THRESHOLD:
            continue
        if world.facts.get("heard_sound", ""):
            sig = ("clue", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.meters["found_clue"] += 1
            out.append("__clue__")
    return out


def _r_friendship(world: World) -> list[str]:
    out: list[str] = []
    a = world.entities.get("friend_a")
    b = world.entities.get("friend_b")
    if not a or not b:
        return out
    if a.meters["shared_clue"] >= THRESHOLD and b.meters["shared_clue"] >= THRESHOLD:
        sig = ("bond",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        a.memes["trust"] += 1
        b.memes["trust"] += 1
        out.append("__bond__")
    return out


CAUSAL_RULES = [
    Rule("echo", "sound", _r_echo),
    Rule("clue", "mystery", _r_clue),
    Rule("friendship", "social", _r_friendship),
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


def reasonableness_gate(location: Location, clue: Clue, action: Action) -> bool:
    return location.permissive and location.botanic and location.oval and action.safe


def predict_clue(world: World, action: Action) -> dict:
    sim = world.copy()
    sim.facts["heard_sound"] = action.sound
    for e in sim.characters():
        e.meters["listening"] += 1
    propagate(sim, narrate=False)
    return {
        "clue_found": any(e.meters["found_clue"] >= THRESHOLD for e in sim.characters()),
        "bond": sim.get("friend_a").memes["trust"] + sim.get("friend_b").memes["trust"],
    }


def setup(world: World, a: Entity, b: Entity, location: Location) -> None:
    world.location = location
    a.memes["curious"] += 1
    b.memes["curious"] += 1
    world.say(
        f"On a quiet afternoon, {a.id} and {b.id} wandered into {location.label}, "
        f"a {('oval ' if location.oval else '')}{'botanic ' if location.botanic else ''}place full of leaves and paths."
    )
    world.say(
        f"They liked exploring together, because their friendship made even a small walk feel like a secret mission."
    )


def hear_sound(world: World, a: Entity, b: Entity, clue: Clue) -> None:
    for e in (a, b):
        e.meters["listening"] += 1
    world.facts["heard_sound"] = clue.sound
    world.say(
        f"Then they heard it again -- {clue.sound} -- coming from somewhere near the {clue.source}."
    )
    world.say(
        f'{b.id} tilted {b.pronoun("possessive")} head. "{clue.label}?" {b.pronoun()} whispered. '
        f'It sounded funny, but not scary.'
    )


def ask_permission(world: World, parent: Entity, a: Entity, b: Entity) -> None:
    parent.memes["permissive"] += 1
    world.say(
        f"When they asked {parent.label_word}, {parent.pronoun()} smiled and said they could look, "
        f"as long as they stayed together and touched nothing sharp."
    )


def search(world: World, a: Entity, b: Entity, clue: Clue, action: Action) -> None:
    pred = predict_clue(world, action)
    world.facts["predicted_clue_found"] = pred["clue_found"]
    world.facts["predicted_bond"] = pred["bond"]
    a.meters["listening"] += 1
    b.meters["listening"] += 1
    world.say(
        f"They tiptoed past the ferns and peered behind a big pot. The sound kept coming, soft and steady."
    )
    world.say(
        f'{a.id} pointed. "{clue.visible}!" {a.pronoun()} said, because the clue was hiding in plain sight.'
    )


def discover(world: World, a: Entity, b: Entity, clue: Clue, action: Action) -> None:
    a.meters["found_clue"] += 1
    b.meters["found_clue"] += 1
    a.meters["shared_clue"] += 1
    b.meters["shared_clue"] += 1
    propagate(world, narrate=False)
    world.say(
        f"It was only {clue.visible}, making the sound with {clue.source}. "
        f"{action.method} had made the mystery easy to solve."
    )


def friendship_end(world: World, a: Entity, b: Entity, parent: Entity, clue: Clue, location: Location) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    a.memes["trust"] += 1
    b.memes["trust"] += 1
    world.say(
        f"They laughed, and {b.id} said that the oval path had sounded mysterious only because the wind was playful."
    )
    world.say(
        f"{parent.label_word.capitalize()} handed them each a little leaf-shaped sticker and thanked them for solving the tiny mystery kindly."
    )
    world.say(
        f"By the end, the botanic path seemed friendly instead of strange, and the two friends walked home side by side."
    )


def tell(location: Location, clue: Clue, action: Action,
         friend_a: str = "Mina", friend_b: str = "Jasper",
         parent_type: str = "mother") -> World:
    world = World()
    a = world.add(Entity(id="friend_a", kind="character", type="girl", label=friend_a, role="friend"))
    b = world.add(Entity(id="friend_b", kind="character", type="boy", label=friend_b, role="friend"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the grown-up", role="parent"))
    world.add(Entity(id="clue", type="thing", label=clue.label))
    world.facts["location"] = location
    world.facts["clue"] = clue
    world.facts["action"] = action

    setup(world, a, b, location)
    world.para()
    hear_sound(world, a, b, clue)
    ask_permission(world, parent, a, b)
    world.para()
    search(world, a, b, clue, action)
    discover(world, a, b, clue, action)
    world.para()
    friendship_end(world, a, b, parent, clue, location)

    world.facts.update(
        friend_a=a,
        friend_b=b,
        parent=parent,
        outcome="solved",
        shared=True,
    )
    return world


LOCATIONS = {
    "oval_garden": Location(
        "oval_garden", "the oval botanic garden", oval=True, botanic=True, permissive=True,
        quiet=True, sound_echo="soft whoosh", tags={"oval", "botanic", "permissive"},
    ),
    "oval_greenhouse": Location(
        "oval_greenhouse", "the oval greenhouse", oval=True, botanic=True, permissive=True,
        quiet=True, sound_echo="tap tap", tags={"oval", "botanic", "permissive"},
    ),
    "botanic_loop": Location(
        "botanic_loop", "the botanic oval path", oval=True, botanic=True, permissive=True,
        quiet=True, sound_echo="shhh", tags={"oval", "botanic", "permissive"},
    ),
}

CLUES = {
    "watering_can": Clue(
        "watering_can", "watering can", "clink-clink", "a metal hook", "shiny and round",
        tags={"sound", "botanic"},
    ),
    "wind_chimes": Clue(
        "wind_chimes", "wind chimes", "tinkling", "the porch beam", "hanging in the leaves",
        tags={"sound", "mystery"},
    ),
    "sprinkler": Clue(
        "sprinkler", "sprinkler", "psst-psst", "a tiny nozzle", "spinning in the grass",
        tags={"sound", "water"},
    ),
}

ACTIONS = {
    "peek": Action(
        "peek", "a soft rustle", "peek behind the fern", "the shiny loop", safe=True, tags={"mystery"},
    ),
    "listen": Action(
        "listen", "tinkling", "listen carefully", "the hanging chimes", safe=True, tags={"sound"},
    ),
    "follow": Action(
        "follow", "psst-psst", "follow the trail of sound", "the watering path", safe=True, tags={"sound"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Tess", "Ivy", "Rosa"]
BOY_NAMES = ["Jasper", "Owen", "Theo", "Noah", "Milo", "Ezra"]
TRAITS = ["curious", "careful", "bright", "gentle"]


@dataclass
@dataclass
class StoryParams:
    location: str
    clue: str
    action: str
    friend_a: str
    friend_b: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for loc_id, loc in LOCATIONS.items():
        for clue_id in CLUES:
            for action_id in ACTIONS:
                if reasonableness_gate(loc, CLUES[clue_id], ACTIONS[action_id]):
                    combos.append((loc_id, clue_id, action_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a gentle botanic mystery with friends and sound effects.")
    ap.add_argument("--location", choices=LOCATIONS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
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
              if (args.location is None or c[0] == args.location)
              and (args.clue is None or c[1] == args.clue)
              and (args.action is None or c[2] == args.action)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    loc_id, clue_id, action_id = rng.choice(sorted(combos))
    return StoryParams(
        location=loc_id,
        clue=clue_id,
        action=action_id,
        friend_a=args.name_a or rng.choice(GIRL_NAMES),
        friend_b=args.name_b or rng.choice(BOY_NAMES),
        parent=args.parent or rng.choice(["mother", "father"]),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    loc, clue, action = f["location"], f["clue"], f["action"]
    return [
        f'Write a gentle mystery story for a 3-to-5-year-old that includes the words "oval", "botanic", and "permissive".',
        f"Tell a friendship mystery where two friends hear {clue.sound} in {loc.label} and solve it by {action.method}.",
        f"Write a child-friendly story about a botanic place, a strange sound, and a grown-up who is permissive enough to let the friends investigate.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a = f["friend_a"]
    b = f["friend_b"]
    parent = f["parent"]
    loc = f["location"]
    clue = f["clue"]
    action = f["action"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {a.id if isinstance(a, Entity) else a} and {b.id if isinstance(b, Entity) else b}, two friends who solved a small mystery together. Their friendship is what made the clue feel exciting instead of scary.",
        ),
        QAItem(
            question="What sound did they hear?",
            answer=f"They heard {clue.sound}, which came from {clue.source}. That sound led them to the clue and gave the story its mystery.",
        ),
        QAItem(
            question="How did the grown-up help?",
            answer=f"{parent.label_word.capitalize()} was permissive and let them look, as long as they stayed careful. That freedom helped the friends solve the mystery without making trouble.",
        ),
        QAItem(
            question="What was the clue really?",
            answer=f"It was only {clue.visible}. The sound came from something ordinary, so the mystery turned out to be harmless.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"They solved the clue, laughed together, and walked home feeling brave. The ending shows that the oval botanic place became friendly once they understood the sound.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does botanic mean?",
            answer="Botanic means related to plants and gardens. A botanic place has leaves, flowers, and things that grow.",
        ),
        QAItem(
            question="What is an oval?",
            answer="An oval is a round shape that is stretched a little. It is smooth and looping, not pointy.",
        ),
        QAItem(
            question="What does permissive mean?",
            answer="Permissive means a grown-up allows something gentle or safe. A permissive person gives permission instead of saying no right away.",
        ),
        QAItem(
            question="What are sound effects in a story?",
            answer="Sound effects are words that help you hear the story in your head, like clink-clink or tinkling. They make the scene feel alive.",
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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(LOCATIONS[params.location], CLUES[params.clue], ACTIONS[params.action],
                 params.friend_a, params.friend_b, params.parent)
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


ASP_RULES = r"""
valid(L,C,A) :- location(L), clue(C), action(A), permissive(L), botanic(L), oval(L), safe(A).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for lid, loc in LOCATIONS.items():
        lines.append(asp.fact("location", lid))
        if loc.oval:
            lines.append(asp.fact("oval", lid))
        if loc.botanic:
            lines.append(asp.fact("botanic", lid))
        if loc.permissive:
            lines.append(asp.fact("permissive", lid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for aid, act in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        if act.safe:
            lines.append(asp.fact("safe", aid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP gate.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


CURATED = [
    StoryParams("oval_garden", "watering_can", "peek", "Mina", "Jasper", "mother"),
    StoryParams("oval_greenhouse", "wind_chimes", "listen", "Lila", "Owen", "father"),
    StoryParams("botanic_loop", "sprinkler", "follow", "Nora", "Theo", "mother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for item in asp_valid_combos():
            print(item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
