#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/clear_suspense_fable.py
=======================================================

A tiny fable-like storyworld about a clear spring, a worried little animal,
and a suspenseful choice that ends in a calm, earned resolution.

The world is built to satisfy the Storyweavers contract:
- typed entities with meters and memes
- a state-driven story engine
- a Python reasonableness gate plus an inline ASP twin
- prompts, story Q&A, and world-knowledge Q&A generated from world state
- CLI support for --trace, --qa, --json, --asp, --verify, and --show-asp

Seed premise:
- include the word "clear"
- keep the style close to fable
- include suspense

This world tells small stories about a fox, a rabbit, a crow, a hedgehog, and a
clear spring in the lantern-wood. Someone hears a sound, suspects danger, and
must decide whether to wait, warn, or act. The suspense turns on what is really
making the sound: a trapped creature, a falling branch, or a hidden leak. A
helpful act clears the way and leaves a moral-like ending image.
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "fox", "rabbit", "crow", "hedgehog"}
        male = {"boy", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
class Place:
    id: str
    label: str
    detail: str
    tags: set[str] = field(default_factory=set)
    clear: bool = True
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class SoundSource:
    id: str
    label: str
    kind: str
    danger: int
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Helper:
    id: str
    label: str
    tool: str
    power: int
    method: str
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def animals(self) -> list[Entity]:
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


def _r_alarm(world: World) -> list[str]:
    out: list[str] = []
    spring = world.get("spring")
    if spring.meters["troubled"] < THRESHOLD:
        return out
    sig = ("alarm",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for a in world.animals():
        a.memes["worry"] += 1
    out.append("__alarm__")
    return out


def _r_clear(world: World) -> list[str]:
    out: list[str] = []
    spring = world.get("spring")
    if spring.meters["blocked"] < THRESHOLD:
        return out
    sig = ("clear",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    spring.meters["blocked"] = 0.0
    spring.meters["clear"] = 1.0
    out.append("__clear__")
    return out


CAUSAL_RULES = [Rule("alarm", _r_alarm), Rule("clear", _r_clear)]


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


def hazard_at_risk(clue: SoundSource, place: Place) -> bool:
    return clue.danger >= 1 and place.clear


def best_helpers() -> list[Helper]:
    return [h for h in HELPERS.values() if h.power >= 2]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    if not best_helpers():
        return combos
    for pid, place in PLACES.items():
        for cid, clue in CLUES.items():
            for hid, helper in HELPERS.items():
                if hazard_at_risk(clue, place) and helper.power >= clue.danger:
                    combos.append((pid, cid, hid))
    return combos


def explain_rejection(clue: SoundSource, place: Place, helper: Optional[Helper] = None) -> str:
    if not hazard_at_risk(clue, place):
        return f"(No story: {clue.label} does not create a real suspenseful danger at {place.label}.)"
    if helper is not None and helper.power < clue.danger:
        return f"(No story: {helper.label} is too weak for {clue.label}; the choice would not solve the problem.)"
    return "(No story: this combination does not produce a clear suspenseful fable.)"


def predict(world: World, clue_id: str) -> dict:
    sim = world.copy()
    _trigger_clue(sim, sim.get("clue"), narrate=False)
    return {"alarm": sim.get("spring").meters["troubled"] >= THRESHOLD,
            "worry": sum(a.memes["worry"] for a in sim.animals())}


def _trigger_clue(world: World, clue: SoundSource, narrate: bool = True) -> None:
    spring = world.get("spring")
    spring.meters["troubled"] += 1
    spring.meters["blocked"] += 1
    propagate(world, narrate=narrate)


def _setup(world: World, hero: Entity, friend: Entity, place: Place) -> None:
    hero.memes["curiosity"] += 1
    friend.memes["care"] += 1
    world.say(f"In {place.label}, where the water stayed {place.detail}, {hero.id} and {friend.id} walked softly by the spring.")
    world.say(f"Their noses lifted, because the place was so {place.detail} that every small sound seemed worth hearing.")


def suspense(world: World, hero: Entity, friend: Entity, clue: SoundSource, place: Place) -> None:
    pred = predict(world, clue.id)
    world.facts["predicted_worry"] = pred["worry"]
    world.say(f"Then a thin sound came from the reeds. It was not clear what made it.")
    world.say(f"{hero.id} froze. {friend.id} listened too, and both of them stared at the water.")
    world.say(f'"Something is wrong," {hero.id} whispered, though the water still looked clear.')


def choose(world: World, hero: Entity, friend: Entity, clue: SoundSource, helper: Helper) -> None:
    hero.memes["bravery"] += 1
    friend.memes["hope"] += 1
    world.say(f"{friend.id} said, 'Let us not leap first and think later.'")
    world.say(f'{hero.id} nodded. "Then let us watch one breath longer," {hero.id} said.')
    world.say(f"They waited just long enough to learn what was really there.")


def reveal(world: World, clue: SoundSource, helper: Helper, place: Place) -> None:
    _trigger_clue(world, clue)
    world.say(f"It was only a little fox cub caught by a bramble, and the sound had made the spring seem frightened.")
    world.say(f"{helper.label.capitalize()} came at once and used {helper.method} to free the cub.")
    world.say(f"The bramble came loose, the cub sprang away, and the spring began to shine {place.label} and clear again.")


def lesson(world: World, hero: Entity, friend: Entity, place: Place, helper: Helper) -> None:
    hero.memes["relief"] += 1
    friend.memes["relief"] += 1
    world.say("For a moment, the woods were very still.")
    world.say(f"Then {hero.id} and {friend.id} smiled, because careful ears had saved a frightened life.")
    world.say(f"The spring was clear, the path was calm, and the little animals went home wiser than before.")


def tell(place: Place, clue: SoundSource, helper: Helper, hero_name: str = "Mina",
         friend_name: str = "Pip", hero_type: str = "fox", friend_type: str = "rabbit") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="seer"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, role="listener"))
    spring = world.add(Entity(id="spring", type="place", label="the spring"))
    world.add(Entity(id="clue", type="thing", label=clue.label))
    world.facts["place"] = place
    world.facts["clue"] = clue
    world.facts["helper"] = helper
    world.facts["hero"] = hero
    world.facts["friend"] = friend

    _setup(world, hero, friend, place)
    world.para()
    suspense(world, hero, friend, clue, place)
    choose(world, hero, friend, clue, helper)
    world.para()
    reveal(world, clue, helper, place)
    lesson(world, hero, friend, place, helper)

    world.facts["outcome"] = "clear"
    world.facts["spring"] = spring
    return world


PLACES = {
    "lantern_wood": Place(id="lantern_wood", label="Lantern Wood", detail="clear as glass", tags={"clear", "wood"}),
    "green_bank": Place(id="green_bank", label="the green bank", detail="bright and still", tags={"clear", "bank"}),
    "quiet_hollow": Place(id="quiet_hollow", label="the quiet hollow", detail="so still you could hear leaves", tags={"clear", "hollow"}),
}

CLUES = {
    "bramble": SoundSource(id="bramble", label="a rustling bramble", kind="hidden_snare", danger=1, tags={"suspense", "fox"}),
    "branch": SoundSource(id="branch", label="a creaking branch", kind="falling_branch", danger=2, tags={"suspense", "branch"}),
    "net": SoundSource(id="net", label="a tangled net", kind="trap", danger=2, tags={"suspense", "trap"}),
}

HELPERS = {
    "hoof": Helper(id="hoof", label="deer-hoof helper", tool="steady hooves", power=2, method="careful hooves", tags={"help"}),
    "twig": Helper(id="twig", label="a long twig", tool="long twig", power=1, method="a long twig", tags={"weak"}),
    "rope": Helper(id="rope", label="a thin rope", tool="thin rope", power=3, method="a loop of rope", tags={"help"}),
}


@dataclass
class StoryParams:
    place: str
    clue: str
    helper: str
    hero_name: str
    friend_name: str
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
    StoryParams(place="lantern_wood", clue="bramble", helper="hoof", hero_name="Mina", friend_name="Pip"),
    StoryParams(place="green_bank", clue="branch", helper="rope", hero_name="Lio", friend_name="Nell"),
    StoryParams(place="quiet_hollow", clue="net", helper="hoof", hero_name="Faye", friend_name="Tov"),
]


KNOWLEDGE = {
    "clear": [("What does it mean when water is clear?", "Clear water lets you see through it. It looks clean and bright, so you can notice what is beneath the surface.")],
    "fox": [("What is a fox?", "A fox is a small wild animal with a bushy tail and a clever nose. It watches and learns quickly.")],
    "rabbit": [("What is a rabbit?", "A rabbit is a small animal with long ears and quick feet. Rabbits listen carefully because they stay alert for trouble.")],
    "spring": [("What is a spring?", "A spring is water that comes up from the ground. It can be clean and cool and may feed a stream.")],
    "suspense": [("What is suspense in a story?", "Suspense is the feeling of not knowing what will happen next. It makes you wait and listen carefully.")],
    "bramble": [("What is a bramble?", "A bramble is a prickly plant with branches and thorns. It can catch on fur or clothes.")],
    "branch": [("Why can a branch be dangerous?", "A branch can snap or fall if it cracks. That can scare animals or block a path.")],
    "net": [("Why can a net trap an animal?", "A net has holes and loops that can tangle around legs or wings. A frightened animal may get stuck in it.")],
    "rope": [("What can a rope do?", "A rope can help pull, lift, or free something when it is used carefully.")],
    "hoof": [("Why are steady hooves helpful?", "Steady hooves help an animal stand firm and move carefully. They are good for reaching a place without making a mess.")],
}
KNOWLEDGE_ORDER = ["clear", "suspense", "fox", "rabbit", "spring", "bramble", "branch", "net", "rope", "hoof"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fable-like suspense story that uses the word "clear" and takes place near {f["place"].label}.',
        f"Tell a small animal story where {f['hero'].id} hears a worrying sound, waits, and learns what is really there.",
        f"Write a gentle suspense tale about {f['hero'].type} and {f['friend'].type} by a spring, ending with a wise choice and a clear lesson.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    place = f["place"]
    helper = f["helper"]
    qa = [
        ("Who is the story about?",
         f"It is about {hero.id} and {friend.id}, two small animals who walked by {place.label}."),
        ("What made the story suspenseful?",
         f"A thin sound came from the reeds, and nobody knew at first what made it. That uncertainty made the animals pause and listen."),
        ("What did they do instead of rushing in?",
         f"They waited one breath longer and chose to watch carefully. That gave them enough time to understand the danger before acting."),
        ("How did the helper solve the problem?",
         f"{helper.label.capitalize()} used {helper.method} to free the trapped little fox cub. The careful help cleared the way without hurting anyone."),
        ("How did the story end?",
         f"It ended with the spring clear again and the little animals wiser and calmer. The woods felt safe after the rescue."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["place"].tags) | set(world.facts["clue"].tags) | set(world.facts["helper"].tags) | {"clear", "suspense"}
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(r for r, in [(x[0],) for x in world.fired])}")
    return "\n".join(lines)


ASP_RULES = r"""
place(p1) :- p1 = lantern_wood.
place(p2) :- p2 = green_bank.
place(p3) :- p3 = quiet_hollow.

clue(c1) :- c1 = bramble.
clue(c2) :- c2 = branch.
clue(c3) :- c3 = net.

helper(h1) :- h1 = hoof.
helper(h2) :- h2 = twig.
helper(h3) :- h3 = rope.

clear_place(P) :- place(P).
hazard(C) :- clue(C), danger(C, D), D >= 1.
strong_helper(H) :- helper(H), power(H, P), P >= 2.
valid(P, C, H) :- clear_place(P), hazard(C), strong_helper(H), danger(C, D), power(H, P2), P2 >= D.
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("danger", cid, c.danger))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("power", hid, h.power))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    p = set(valid_combos())
    a = set(asp_valid_combos())
    rc = 0
    if p == a:
        print(f"OK: clingo gate matches valid_combos() ({len(p)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and python valid combos.")
        print("python only:", sorted(p - a))
        print("clingo only:", sorted(a - p))
    try:
        sample = generate(CURATED[0])
        assert sample.story
        assert sample.prompts and sample.story_qa and sample.world_qa
        print("OK: generate() smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small clear-suspense fable storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
              and (args.clue is None or c[1] == args.clue)
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, clue, helper = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        clue=clue,
        helper=helper,
        hero_name=args.name or rng.choice(["Mina", "Lio", "Faye", "Nia", "Pip"]),
        friend_name=args.friend or rng.choice(["Pip", "Nell", "Tov", "Sera", "Bram"]),
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    for key, table in (("place", PLACES), ("clue", CLUES), ("helper", HELPERS)):
        if getattr(params, key) not in table:
            raise StoryError(f"Unknown {key}: {getattr(params, key)}")
    world = tell(PLACES[params.place], CLUES[params.clue], HELPERS[params.helper],
                 hero_name=params.hero_name, friend_name=params.friend_name)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for p, c, h in combos:
            print(f"  {p:14} {c:8} {h}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} and {p.friend_name}: {p.place}, {p.clue}, {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
