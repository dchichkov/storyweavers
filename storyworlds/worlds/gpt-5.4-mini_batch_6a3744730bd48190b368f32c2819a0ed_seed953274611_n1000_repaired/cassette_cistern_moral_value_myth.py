#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/cassette_cistern_moral_value_myth.py
=====================================================================

A tiny mythic storyworld about a child, a treasured cassette, a cistern,
and a moral choice: listen to a wise warning, or chase glory and risk loss.

The world is intentionally small and classical:
- a child seeks a song for a ritual
- a forbidden act could drop a cassette into a cistern
- a mentor warns them
- the child either chooses virtue early, or loses the cassette and learns a moral

The tone is meant to feel like a simple myth, with a clear rule, a test, and a
reward or lesson.
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
MORAL_MIN = 2.0


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
        female = {"girl", "mother", "woman", "priestess"}
        male = {"boy", "father", "man", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    label: str
    depth: str
    echo: str
    wet: bool = True
    dangerous: bool = True
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
class Precious:
    id: str
    label: str
    phrase: str
    sung: str
    carried: str
    belongs_to: str
    fragile: bool = True
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    use: str
    safe: bool = True
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Rule:
    name: str
    apply: Callable[["World"], list[str]]
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


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    if world.get("cassette").meters["in_hand"] >= THRESHOLD and world.get("cistern").meters["opened"] >= THRESHOLD:
        sig = ("spill",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("cassette").meters["at_risk"] += 1
            world.get("hero").memes["fear"] += 1
            out.append("__spill__")
    return out


def _r_loss(world: World) -> list[str]:
    out: list[str] = []
    cassette = world.get("cassette")
    cistern = world.get("cistern")
    if cassette.meters["fallen"] >= THRESHOLD and cistern.meters["opened"] >= THRESHOLD:
        sig = ("loss",)
        if sig not in world.fired:
            world.fired.add(sig)
            cassette.meters["lost"] += 1
            cistern.meters["claimed"] += 1
            out.append("__loss__")
    return out


CAUSAL_RULES = [Rule("spill", _r_spill), Rule("loss", _r_loss)]


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


def moral_value_ok(kind: str) -> bool:
    return kind in {"kindness", "humility", "honesty", "patience"}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for precious in PRECIOUS:
            for tool in TOOLS:
                if place.dangerous and precious.fragile and tool.safe:
                    combos.append((place.id, precious.id, tool.id))
    return combos


def danger_forbidden(place: Place, precious: Precious) -> bool:
    return place.dangerous and precious.fragile


def choose_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def predicted_loss(world: World, place_id: str) -> bool:
    sim = world.copy()
    sim.get("cistern").meters["opened"] += 1
    sim.get("cassette").meters["in_hand"] += 1
    propagate(sim, narrate=False)
    return sim.get("cassette").meters["lost"] >= THRESHOLD


def tell(place: Place, precious: Precious, tool: Tool, hero_name: str, hero_gender: str,
         mentor_name: str, mentor_gender: str, seed_word: str = "cassette") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    mentor = world.add(Entity(id=mentor_name, kind="character", type=mentor_gender, role="mentor"))
    cistern = world.add(Entity(id="cistern", type="thing", label="cistern"))
    cassette = world.add(Entity(id="cassette", type="thing", label="cassette"))
    shrine = world.add(Entity(id="shrine", type="place", label=place.label))

    cassette.meters["held"] += 1
    hero.memes["wonder"] += 1
    mentor.memes["calm"] += 1

    world.say(
        f"Long ago, when the shrine was quiet and {place.echo}, "
        f"{hero.id} found {precious.phrase} beside the stone path. "
        f"It was a {seed_word} of old songs, said to remember the names of the stars."
    )
    world.say(
        f"Below the shrine waited the {place.label}, a deep cistern that kept its water "
        f"like a secret. {hero.id} wanted to carry the {precious.label} there and let "
        f"the old song sound over the water."
    )

    world.para()
    hero.memes["desire"] += 1
    if predicted_loss(world, place.id):
        world.say(
            f"But {mentor.id} saw the danger first. "
            f'"If the {precious.label} slips into the cistern, the song will be gone," '
            f"{mentor.id} said. \"A gift is not made greater by risking it.\""
        )
    else:
        world.say(
            f"But {mentor.id} looked at the cistern and warned, "
            f'"Some doors should not be opened for play."'
        )

    if moral_value_ok("humility") and tool.safe:
        world.say(
            f"{hero.id} bowed {hero.pronoun('possessive')} head and listened. "
            f"Instead of boasting, {hero.pronoun()} set the {precious.label} on a dry stone "
            f"and asked how the song should be honored."
        )
        world.para()
        world.say(
            f"{mentor.id} smiled and showed {hero.pronoun('object')} a safer rite: "
            f"hold the {precious.label} high, sing once, and keep {tool.phrase} ready "
            f"to light the path."
        )
        world.say(
            f"So the {precious.label} stayed bright, the cistern stayed silent, "
            f"and the shrine kept its peace. That night the song was heard without loss, "
            f"and {hero.id} learned that wisdom can be a kind of strength."
        )
        outcome = "virtuous"
    else:
        world.say(
            f"{hero.id} did not listen. With proud hands {hero.pronoun()} reached too close, "
            f"and the {precious.label} slipped from {hero.pronoun('possessive')} grasp."
        )
        world.para()
        cistern.meters["opened"] += 1
        cassette.meters["in_hand"] += 1
        cassette.meters["fallen"] += 1
        propagate(world, narrate=False)
        world.say(
            f"The {precious.label} fell into the cistern with a small dark splash. "
            f"The song was not heard again, and {hero.id} stood in silence, ashamed."
        )
        world.say(
            f"Then {mentor.id} drew {hero.pronoun('object')} back and taught the old truth: "
            f"some treasures are kept by care, not by claiming."
        )
        outcome = "fall"
    world.facts.update(
        hero=hero,
        mentor=mentor,
        place=place,
        precious=precious,
        tool=tool,
        cistern=cistern,
        cassette=cassette,
        outcome=outcome,
    )
    return world


PLACES = [
    Place(id="sanctuary", label="cistern", depth="deep", echo="the air carried a holy echo"),
    Place(id="wellyard", label="cistern", depth="deep", echo="the stones answered in a whisper"),
    Place(id="courtyard", label="cistern", depth="deep", echo="the walls returned every sound"),
]

PRECIOUS = [
    Precious(id="silver_cassette", label="cassette", phrase="a silver cassette", sung="old songs", carried="its ribboned case", belongs_to="hero"),
    Precious(id="sun_cassette", label="cassette", phrase="a small cassette of dawn songs", sung="dawn songs", carried="its cracked shell", belongs_to="hero"),
]

TOOLS = [
    Tool(id="lamp", label="lamp", phrase="a little lamp", use="light"),
    Tool(id="rope", label="rope", phrase="a rope", use="steady hands"),
]

GIRL_NAMES = ["Alya", "Mira", "Nora", "Lina", "Sana"]
BOY_NAMES = ["Eran", "Tavi", "Oren", "Ilan", "Dorin"]
MENTOR_GIRLS = ["priestess", "guardian"]
MENTOR_BOYS = ["priest", "guardian"]

TRAITS = ["humble", "careful", "brave", "patient"]


@dataclass
class StoryParams:
    place: str
    precious: str
    tool: str
    hero_name: str
    hero_gender: str
    mentor_name: str
    mentor_gender: str
    trait: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short myth for a child that includes the words "{f["precious"].label}" and "cistern", and teaches a moral value.',
        f"Tell a mythic story where {f['hero'].id} nearly loses a {f['precious'].label} to a cistern, but learns humility from {f['mentor'].id}.",
        f'Write a gentle legend about a cassette, a cistern, and the lesson that care is stronger than pride.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    mentor = f["mentor"]
    precious = f["precious"]
    qa: list[QAItem] = [
        QAItem(
            question="Who was the story about?",
            answer=f"It was about {hero.id} and {mentor.id}, who stood near the cistern and faced a test of character."
        ),
        QAItem(
            question=f"Why did {mentor.id} warn {hero.id}?",
            answer=f"{mentor.id} warned {hero.id} because the cassette could fall into the cistern and be lost forever. The warning mattered because a fragile treasure should be kept with care."
        ),
    ]
    if f["outcome"] == "virtuous":
        qa.append(QAItem(
            question="How did the story end?",
            answer=f"{hero.id} listened, and the cassette stayed safe beside the cistern. The ending proves that humility and patience can guard what pride might lose."
        ))
    else:
        qa.append(QAItem(
            question="How did the story end?",
            answer=f"The cassette fell into the cistern, and {hero.id} had to learn from the loss. The ending turns the mistake into a moral lesson about care."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cistern?",
            answer="A cistern is a deep container or chamber that holds water. In old stories, it can be a dangerous place for a dropped treasure."
        ),
        QAItem(
            question="What is a cassette?",
            answer="A cassette is a small case that can hold recorded music or sound. If it falls somewhere wet or deep, it can be damaged or lost."
        ),
        QAItem(
            question="What moral value does this story teach?",
            answer="It teaches humility and carefulness. A wise person listens before acting, because care can protect what pride might destroy."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
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


CURATED = [
    StoryParams(
        place="sanctuary",
        precious="silver_cassette",
        tool="lamp",
        hero_name="Alya",
        hero_gender="girl",
        mentor_name="Sana",
        mentor_gender="girl",
        trait="humble",
    ),
    StoryParams(
        place="wellyard",
        precious="sun_cassette",
        tool="rope",
        hero_name="Eran",
        hero_gender="boy",
        mentor_name="Tavi",
        mentor_gender="boy",
        trait="careful",
    ),
]


def explain_rejection(place: Place, precious: Precious) -> str:
    if not danger_forbidden(place, precious):
        return "(No story: this choice does not create a real moral test around the cistern.)"
    return "(No story: this combination is not reasonable for the mythic loss test.)"


def outcome_of(params: StoryParams) -> str:
    if params.tool not in TOOLS_BY_ID:
        return "?"
    return "virtuous"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld about a cassette and a cistern.")
    ap.add_argument("--place", choices=PLACES_BY_ID)
    ap.add_argument("--precious", choices=PRECIOUS_BY_ID)
    ap.add_argument("--tool", choices=TOOLS_BY_ID)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--mentor-gender", choices=["girl", "boy"])
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
    if args.place and args.precious:
        if (args.place, args.precious, args.tool or "lamp") not in combos:
            raise StoryError(explain_rejection(PLACES_BY_ID[args.place], PRECIOUS_BY_ID[args.precious]))
    candidates = [c for c in combos if (args.place is None or c[0] == args.place)
                  and (args.precious is None or c[1] == args.precious)]
    if not candidates:
        raise StoryError("(No valid combination matches the given options.)")
    place, precious, tool = rng.choice(sorted(candidates))
    gender = args.gender or rng.choice(["girl", "boy"])
    mentor_gender = args.mentor_gender or rng.choice(["girl", "boy"])
    return StoryParams(
        place=place,
        precious=precious,
        tool=tool,
        hero_name=choose_name(rng, gender),
        hero_gender=gender,
        mentor_name=choose_name(rng, mentor_gender),
        mentor_gender=mentor_gender,
        trait=rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES_BY_ID or params.precious not in PRECIOUS_BY_ID or params.tool not in TOOLS_BY_ID:
        raise StoryError("Invalid StoryParams.")
    world = tell(
        PLACES_BY_ID[params.place],
        PRECIOUS_BY_ID[params.precious],
        TOOLS_BY_ID[params.tool],
        params.hero_name,
        params.hero_gender,
        params.mentor_name,
        params.mentor_gender,
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


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p.id))
        if p.dangerous:
            lines.append(asp.fact("dangerous", p.id))
    for pr in PRECIOUS:
        lines.append(asp.fact("precious", pr.id))
        if pr.fragile:
            lines.append(asp.fact("fragile", pr.id))
    for t in TOOLS:
        lines.append(asp.fact("tool", t.id))
        if t.safe:
            lines.append(asp.fact("safe", t.id))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, C, T) :- place(P), precious(C), tool(T), dangerous(P), fragile(C), safe(T).
moral_value(humility).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    a = set(asp_valid_combos())
    p = set(valid_combos())
    if a == p:
        print(f"OK: ASP matches Python ({len(a)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        print(" only in ASP:", sorted(a - p))
        print(" only in Python:", sorted(p - a))
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for c in PRECIOUS:
            for t in TOOLS:
                if danger_forbidden(p, c) and t.safe:
                    combos.append((p.id, c.id, t.id))
    return combos


PLACES_BY_ID = {p.id: p for p in PLACES}
PRECIOUS_BY_ID = {p.id: p for p in PRECIOUS}
TOOLS_BY_ID = {t.id: t for t in TOOLS}


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.precious} and the cistern"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
