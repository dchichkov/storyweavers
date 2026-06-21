#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/foreign_conflict_lesson_learned_rhyming_story.py
================================================================================

A small standalone storyworld for a child-facing rhyming tale about a *foreign*
visitor, a conflict, and a lesson learned.

The domain is simple:
- A child sees something foreign and feels unsure.
- A misunderstanding turns into a small conflict.
- A patient helper explains, the child learns, and the ending turns warm.

The prose is state-driven: the story is built from a simulated world with
meters for physical changes and memes for emotions.

Run it:
    python storyworlds/worlds/gpt-5.4-mini/foreign_conflict_lesson_learned_rhyming_story.py
    python storyworlds/worlds/gpt-5.4-mini/foreign_conflict_lesson_learned_rhyming_story.py --all
    python storyworlds/worlds/gpt-5.4-mini/foreign_conflict_lesson_learned_rhyming_story.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/foreign_conflict_lesson_learned_rhyming_story.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    foreign: bool = False
    fragile: bool = False

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"damage": 0.0}
        if not self.memes:
            self.memes = {"fear": 0.0, "kindness": 0.0, "lesson": 0.0, "joy": 0.0}

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
class Place:
    id: str
    label: str
    atmosphere: str
    sound: str
    can_host: set[str] = field(default_factory=set)
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


@dataclass
class ForeignThing:
    id: str
    label: str
    phrase: str
    origin: str
    use: str
    fragile: bool = False
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
class Tension:
    id: str
    trigger: str
    flare: str
    settle: str
    damage: int
    lesson: str
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
class StoryParams:
    place: str
    foreign_thing: str
    tension: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


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


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    item = world.entities.get("foreign")
    helper = world.entities.get("helper")
    if not child or not item or not helper:
        return out
    if child.memes["fear"] < THRESHOLD or item.meters["damage"] >= THRESHOLD:
        return out
    sig = ("conflict",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["fear"] += 1
    helper.memes["kindness"] += 1
    out.append("__conflict__")
    return out


def _r_lesson(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    helper = world.entities.get("helper")
    if not child or not helper:
        return out
    if child.memes["lesson"] >= THRESHOLD:
        return out
    if world.facts.get("resolved") is not True:
        return out
    sig = ("lesson",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["lesson"] += 1
    child.memes["fear"] = 0.0
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    out.append("__lesson__")
    return out


CAUSAL_RULES = [Rule("conflict", _r_conflict), Rule("lesson", _r_lesson)]


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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place_id, place in PLACES.items():
        for foreign_id, thing in FOREIGN_THINGS.items():
            for tension_id, tension in TENSIONS.items():
                if place_id in place.can_host and thing.fragile:
                    out.append((place_id, foreign_id, tension_id))
    return out


def story_rhyme(lines: list[str]) -> str:
    return "\n".join(lines)


def _article(noun: str) -> str:
    return "an" if noun[0].lower() in "aeiou" else "a"


def tell(place: Place, thing: ForeignThing, tension: Tension, child_name: str,
         child_gender: str, helper_name: str, helper_gender: str) -> World:
    world = World(place)
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name))
    helper = world.add(Entity(id="helper", kind="character", type=helper_gender, label=helper_name))
    foreign = world.add(Entity(id="foreign", kind="thing", type="thing", label=thing.label, foreign=True, fragile=thing.fragile))
    world.facts["child_name"] = child_name
    world.facts["helper_name"] = helper_name

    world.say(
        f"In {place.label}, where {place.atmosphere could be place.atmosphere}, "
        f"{child_name} saw {thing.phrase} and gave a little stare."
    )
    world.say(
        f'"What is that?" asked {child_name}. "It looks so foreign to me!"'
    )
    world.say(
        f"The breeze went hush with a soft little hum, and the room held its breath with a curious kind of drum."
    )

    world.para()
    child.memes["fear"] += 1
    world.say(
        f"But {child_name} poked at {thing.label} and gave it a shake, "
        f"just as {helper_name} cried, \"Please wait, for goodness' sake!\""
    )
    world.say(
        f"That matched {tension.flare}; the moment grew tense, "
        f"and the little misunderstanding felt rather immense."
    )

    # The accident / conflict.
    if thing.fragile:
        foreign.meters["damage"] += tension.damage
    propagate(world, narrate=False)

    world.para()
    if thing.fragile:
        world.say(
            f"{thing.label.capitalize()} got a tiny crack, not much but still sad, "
            f"and both children felt worried and a little bit bad."
        )
    else:
        world.say(
            f"{thing.label.capitalize()} wobbled but held, like a brave little shell, "
            f"and the children learned quickly that rough hands don't help well."
        )

    world.say(
        f"{helper_name} knelt down and spoke soft and slow: \"When something is foreign, we ask first and learn before we go.\""
    )
    world.say(
        f"{helper_name} showed what {thing.label} was for, and why it was there, "
        f"and {child_name}'s frown turned lighter in the air."
    )

    world.facts["resolved"] = True
    propagate(world, narrate=False)
    world.para()
    world.say(
        f"{child_name} said, \"I'm sorry.\" {helper_name} smiled with grace. "
        f"\"We all make mistakes; we can slow down our pace.\""
    )
    world.say(
        f"So they cleaned up the spot and handled it true, "
        f"and {child_name} learned a sweet lesson through and through."
    )
    world.say(
        f"Now {child_name} looks with respect, not fear, when something seems new, "
        f"for foreign things can be friendly when handled right, too."
    )

    world.facts.update(
        child=child,
        helper=helper,
        foreign=foreign,
        place=place,
        thing=thing,
        tension=tension,
    )
    return world


PLACES = {
    "market": Place(id="market", label="the market", atmosphere="bright and busy", sound="buzz and chatter", can_host={"sticker", "spice", "lantern"}),
    "yard": Place(id="yard", label="the yard", atmosphere="sunny and still", sound="birds and sway", can_host={"sticker", "spice"}),
    "kitchen": Place(id="kitchen", label="the kitchen", atmosphere="warm and neat", sound="clink and tap", can_host={"cup", "lantern", "spice"}),
}

FOREIGN_THINGS = {
    "sticker": ForeignThing(id="sticker", label="a foreign sticker", phrase="a foreign sticker with bright blue swirls", origin="a faraway town", use="to decorate a box", fragile=True, tags={"foreign", "fragile"}),
    "cup": ForeignThing(id="cup", label="a foreign cup", phrase="a foreign cup with a painted bird", origin="a distant island", use="to hold tea", fragile=True, tags={"foreign", "fragile"}),
    "spice": ForeignThing(id="spice", label="a foreign spice jar", phrase="a foreign spice jar with a golden lid", origin="a faraway market", use="to flavor soup", fragile=True, tags={"foreign", "fragile"}),
    "lantern": ForeignThing(id="lantern", label="a foreign lantern", phrase="a foreign lantern with silver glass", origin="a faraway port", use="to light the room", fragile=True, tags={"foreign", "fragile"}),
}

TENSIONS = {
    "poke": Tension(id="poke", trigger="poke", flare="a little poke went wrong", settle="a soft talk made the trouble small", damage=1, lesson="gentle hands and kind asks make new things feel nice", tags={"conflict", "lesson"}),
    "grab": Tension(id="grab", trigger="grab", flare="a grab upset the calm", settle="a calm apology settled the fuss", damage=2, lesson="ask before touch, and learn before you rush", tags={"conflict", "lesson"}),
    "tap": Tension(id="tap", trigger="tap", flare="a tap was too rough", settle="a careful touch made the meaning clear", damage=1, lesson="foreign things need careful care", tags={"conflict", "lesson"}),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Zoe", "Ella"]
BOY_NAMES = ["Noah", "Theo", "Ben", "Leo", "Max"]


def story_qa(world: World) -> list[QAItem]:
    c = world.facts["child_name"]
    h = world.facts["helper_name"]
    thing = world.facts["thing"]
    place = world.facts["place"]
    tension = world.facts["tension"]
    foreign = world.facts["foreign"]
    items = [
        QAItem(
            question="What did the child see?",
            answer=f"The child saw {thing.phrase} in {place.label}. It seemed foreign at first, so the child did not know what to do."
        ),
        QAItem(
            question="What caused the conflict?",
            answer=f"The conflict started when {c} touched {thing.label} too roughly. That made the moment tense before {h} could explain."
        ),
        QAItem(
            question="How was the problem solved?",
            answer=f"{h} explained what {thing.label} was for and asked for gentle hands. Then {c} apologized, and the problem turned small and calm."
        ),
        QAItem(
            question="What lesson was learned?",
            answer=f"{tension.lesson}. The child learned to ask before touching something foreign, so new things could feel safe and kind."
        ),
    ]
    if world.facts.get("resolved"):
        items.append(
            QAItem(
                question="What changed by the end?",
                answer=f"At the end, the child felt wiser and calmer, and the foreign thing was treated with care. The story moved from worry to understanding."
            )
        )
    return items


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does foreign mean?", answer="Foreign means it comes from another place, country, or home than the one you know. It can seem new or unfamiliar at first."),
        QAItem(question="Why should you ask before touching something new?", answer="Asking first helps keep people and things safe. It also shows respect for what belongs to someone else."),
        QAItem(question="What helps when there is conflict?", answer="Calm words, listening, and gentle hands help fix conflict. They turn a tense moment into a learning moment."),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"].label
    thing = f["thing"].label
    return [
        f"Write a rhyming story set in {place} about {thing} that includes the word foreign.",
        f"Tell a child-friendly rhyming tale where a foreign thing causes conflict and a lesson is learned.",
        "Write a gentle rhyme about someone new, a small conflict, and a better way to choose.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.foreign:
            bits.append("foreign=True")
        if e.fragile:
            bits.append("fragile=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


ASP_RULES = r"""
foreign_thing(F) :- foreign(F).
fragile(F) :- thing(F), fragile_thing(F).
valid(P, F, T) :- place(P), place_can_host(P, F), fragile_thing(F), tension(T).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for host in sorted(p.can_host):
            lines.append(asp.fact("place_can_host", pid, host))
    for fid, f in FOREIGN_THINGS.items():
        lines.append(asp.fact("thing", fid))
        lines.append(asp.fact("foreign", fid))
        if f.fragile:
            lines.append(asp.fact("fragile_thing", fid))
    for tid in TENSIONS:
        lines.append(asp.fact("tension", tid))
    return "\n".join(lines)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos.")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"MISMATCH: generate() smoke test failed: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Foreign conflict lesson-learned rhyming storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--foreign-thing", choices=FOREIGN_THINGS)
    ap.add_argument("--tension", choices=TENSIONS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
              and (args.foreign_thing is None or c[1] == args.foreign_thing)
              and (args.tension is None or c[2] == args.tension)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, foreign_thing, tension = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if child_gender == "girl" and rng.random() < 0.5 else "girl")
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(GIRL_NAMES if helper_gender == "girl" else BOY_NAMES)
    if helper == child:
        helper = (GIRL_NAMES[0] if child != GIRL_NAMES[0] else BOY_NAMES[0])
    return StoryParams(
        place=place,
        foreign_thing=foreign_thing,
        tension=tension,
        child=child,
        child_gender=child_gender,
        helper=helper,
        helper_gender=helper_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.foreign_thing not in FOREIGN_THINGS:
        raise StoryError(f"Unknown foreign thing: {params.foreign_thing}")
    if params.tension not in TENSIONS:
        raise StoryError(f"Unknown tension: {params.tension}")
    world = tell(
        PLACES[params.place],
        FOREIGN_THINGS[params.foreign_thing],
        TENSIONS[params.tension],
        params.child,
        params.child_gender,
        params.helper,
        params.helper_gender,
    )
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


CURATED = [
    StoryParams(place="market", foreign_thing="sticker", tension="poke", child="Mia", child_gender="girl", helper="Noah", helper_gender="boy"),
    StoryParams(place="kitchen", foreign_thing="cup", tension="grab", child="Leo", child_gender="boy", helper="Nora", helper_gender="girl"),
    StoryParams(place="market", foreign_thing="lantern", tension="tap", child="Ella", child_gender="girl", helper="Theo", helper_gender="boy"),
]


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
        for item in combos:
            print(item)
        return
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
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
