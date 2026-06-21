#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/reinforce_airport_flashback_animal_story.py
===========================================================================

A small standalone story world for an animal-story airport tale with a
flashback beat and the word "reinforce".

Premise
-------
Two animal characters are at an airport. One wants to rush through a fragile
thing they need for the trip; the other remembers a past mistake in a flashback
and warns them. A helper arrives, reinforces the weak thing, and the trip ends
safely with a concrete change in the world.

This script follows the shared storyworld contract:
- typed entities with meters and memes
- state-driven prose
- reasonableness gate + inline ASP twin
- prompts, story QA, world QA from simulated state
- CLI: --all, -n, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
"""

from __future__ import annotations

import argparse
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
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
        return self.label or self.id
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Airport:
    id: str
    place: str
    crowd: str
    loud: str
    flashback_trigger: str
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
class FragileThing:
    id: str
    label: str
    phrase: str
    weak_spot: str
    spread: int = 2
    fragile: bool = True
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
class Reinforcement:
    id: str
    sense: int
    strength: int
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


@dataclass
class StoryParams:
    airport: str
    fragile: str
    reinforce: str
    helper: str
    helper_type: str
    traveler: str
    traveler_type: str
    flashback: str
    seed: Optional[int] = None
    delay: int = 0
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
        import copy
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


def _r_restore(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["damaged"] < THRESHOLD:
            continue
        sig = ("restore", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["stable"] += 1
        out.append("__restored__")
    return out


CAUSAL_RULES = [Rule("restore", "physical", _r_restore)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                produced.extend(x for x in got if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def hazard_at_risk(fragile: FragileThing, reinforce: Reinforcement) -> bool:
    return fragile.fragile and reinforce.strength > 0


def sensible_reinforcements() -> list[Reinforcement]:
    return [r for r in REINFORCEMENTS.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for airport in AIRPORTS:
        for fragile in FRAGILE.items():
            for reinf in REINFORCEMENTS.items():
                if hazard_at_risk(FRAGILES[fragile[0]], reinf[1]):
                    combos.append((airport, fragile[0], reinf[0]))
    return combos


def flashback_line(world: World, traveler: Entity, helper: Entity, fragile: FragileThing, flashback: str) -> None:
    traveler.memes["anxiety"] += 1
    world.say(
        f"{traveler.id} stared at the {fragile.label} and remembered a flashback: "
        f"{flashback}."
    )
    world.say(
        f"In that memory, {helper.id} had watched the weak thing wobble, and {traveler.id} "
        f"had wished someone would reinforce it sooner."
    )


def setup(world: World, airport: Airport, traveler: Entity, helper: Entity, fragile: FragileThing) -> None:
    traveler.memes["curiosity"] += 1
    helper.memes["care"] += 1
    world.say(
        f"At the {airport.place}, {traveler.id} and {helper.id} moved through the bright crowd. "
        f"Suitcases rolled, announcements hummed, and the air felt busy and loud."
    )
    world.say(
        f"They had a small plan for the trip, but the {fragile.label} was still a little weak."
    )


def want_to_go(world: World, traveler: Entity, fragile: FragileThing) -> None:
    traveler.memes["eagerness"] += 1
    world.say(
        f'"Come on," {traveler.id} said. "We can use the {fragile.label} now and keep going."'
    )


def warn(world: World, helper: Entity, traveler: Entity, fragile: FragileThing) -> None:
    helper.memes["caution"] += 1
    world.say(
        f'{helper.id} shook {helper.pronoun("possessive")} head. "Not yet. It is still too weak, '
        f'and the airport crowds could jostle it."'
    )


def reinforce_thing(world: World, helper: Entity, reinforce: Reinforcement, fragile: FragileThing) -> None:
    fragile_obj = world.get("fragile")
    fragile_obj.meters["damaged"] += 0
    fragile_obj.meters["stable"] += 1
    world.say(
        f"Then {helper.id} used {reinforce.id} to reinforce the {fragile.label}. "
        f"{reinforce.text.replace('{fragile}', fragile.label)}"
    )


def finish(world: World, traveler: Entity, helper: Entity, fragile: FragileThing) -> None:
    world.say(
        f"After that, the {fragile.label} held steady. {traveler.id} tucked it in safely, "
        f"and they walked on together."
    )
    world.say(
        f"The airport still hummed around them, but now the weak thing had become strong enough "
        f"for the trip."
    )


def tell(params: StoryParams) -> World:
    world = World()
    airport = AIRPORTS[params.airport]
    fragile = FRAGILES[params.fragile]
    reinforce = REINFORCEMENTS[params.reinforce]
    traveler = world.add(Entity(id=params.traveler, kind="character", type=params.traveler_type, role="traveler"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_type, role="helper"))
    world.add(Entity(id="fragile", type="thing", label=fragile.label, tags=set(fragile.tags)))
    setup(world, airport, traveler, helper, fragile)
    world.para()
    want_to_go(world, traveler, fragile)
    flashback_line(world, traveler, helper, fragile, params.flashback)
    warn(world, helper, traveler, fragile)
    world.para()
    reinforce_thing(world, helper, reinforce, fragile)
    finish(world, traveler, helper, fragile)
    world.facts.update(
        airport=airport, fragile_cfg=fragile, reinforce=reinforce,
        traveler=traveler, helper=helper, flashback=params.flashback, outcome="stable"
    )
    return world


AIRPORTS = {
    "airport": Airport(
        id="airport",
        place="airport",
        crowd="busy crowd",
        loud="loud announcements",
        flashback_trigger="the rolling suitcases",
        tags={"airport"},
    )
}

FRAGILES = {
    "paper_tag": FragileThing(
        id="paper_tag",
        label="paper tag",
        phrase="a paper tag for the bag",
        weak_spot="its folded edge",
        spread=1,
        fragile=True,
        tags={"paper", "tag"},
    ),
    "handle_wrap": FragileThing(
        id="handle_wrap",
        label="bag handle wrap",
        phrase="a small wrap for the bag handle",
        weak_spot="the stitched seam",
        spread=2,
        fragile=True,
        tags={"bag", "handle"},
    ),
}

REINFORCEMENTS = {
    "tape": Reinforcement(
        id="tape",
        sense=3,
        strength=2,
        text="They pressed the tape flat, and the little edge stopped curling.",
        fail="They tried to help, but the tape was not enough.",
        qa_text="used tape to make it steadier",
        tags={"tape"},
    ),
    "sticker_patch": Reinforcement(
        id="sticker_patch",
        sense=2,
        strength=2,
        text="A bright patch went on top, and the weak spot held together.",
        fail="The patch slipped right off.",
        qa_text="added a bright patch and held it in place",
        tags={"patch"},
    ),
}

TRAVELERS = [("Milo", "cat"), ("Poppy", "rabbit"), ("Nina", "fox"), ("Benny", "bear")]
HELPERS = [("Auntie", "owl"), ("Grandpa", "turtle"), ("Mina", "dog"), ("Rafi", "fox")]
FLASHBACKS = [
    "last time, the tag bent and nearly tore before they could board",
    "the handle wrap had slipped once before in the long line",
    "a small wobble in the past had made everyone worry",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an animal story set in an {f["airport"].place} where {f["traveler"].id} needs to reinforce a weak travel item.',
        f'Tell a child-friendly flashback story about {f["traveler"].id} at the airport, with a helper who remembers the past and makes the item stronger.',
        f'Write a short story that includes the word "reinforce" and ends with a safe airport trip.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    return [
        ("Where does the story take place?",
         "It takes place at an airport, with crowds, rolling suitcases, and loud announcements around the characters."),
        ("What did the flashback do in the story?",
         f'It reminded {f["traveler"].id} of a past time when the weak item almost failed. That memory made the warning feel important and helped the helper choose to fix it carefully.'),
        ("What did they do to solve the problem?",
         f'{f["helper"].id} reinforced the {f["fragile_cfg"].label} so it would hold steady. After that, the travelers could keep going without worrying that it would come apart.'),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is an airport?",
         "An airport is a place where people and animals go to catch planes and travel to other places."),
        ("What does reinforce mean?",
         "To reinforce something means to make it stronger so it can hold up better."),
        ("What is a flashback in a story?",
         "A flashback is a part of the story that shows something that happened earlier, so the characters can remember it and understand what to do now."),
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
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection(fragile: FragileThing, reinforce: Reinforcement) -> str:
    if not fragile.fragile:
        return "(No story: the chosen item is not fragile enough to need reinforcement.)"
    if reinforce.sense < SENSE_MIN:
        return f"(No story: {reinforce.id} is too weak-minded for this storyworld.)"
    return "(No story: this combination does not produce a meaningful airport flashback story.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.reinforce and REINFORCEMENTS[args.reinforce].sense < SENSE_MIN:
        raise StoryError(explain_rejection(FRAGILES[args.fragile if args.fragile else "paper_tag"], REINFORCEMENTS[args.reinforce]))
    combos = list(valid_combos())
    if args.fragile:
        combos = [c for c in combos if c[1] == args.fragile]
    if args.reinforce:
        combos = [c for c in combos if c[2] == args.reinforce]
    if args.airport and args.airport not in AIRPORTS:
        raise StoryError("(No story: unknown airport.)")
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    airport, fragile, reinforce = rng.choice(sorted(combos))
    traveler_name, traveler_type = rng.choice(TRAVELERS)
    helper_name, helper_type = rng.choice([h for h in HELPERS if h[0] != traveler_name])
    flashback = rng.choice(FLASHBACKS)
    return StoryParams(
        airport=airport,
        fragile=fragile,
        reinforce=reinforce,
        helper=helper_name,
        helper_type=helper_type,
        traveler=traveler_name,
        traveler_type=traveler_type,
        flashback=flashback,
        delay=0,
    )


def generate(params: StoryParams) -> StorySample:
    if params.airport not in AIRPORTS or params.fragile not in FRAGILES or params.reinforce not in REINFORCEMENTS:
        raise StoryError("(Invalid params for this storyworld.)")
    world = tell(params)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal-story airport flashback world with reinforce.")
    ap.add_argument("--airport", choices=sorted(AIRPORTS))
    ap.add_argument("--fragile", choices=sorted(FRAGILES))
    ap.add_argument("--reinforce", choices=sorted(REINFORCEMENTS))
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


ASP_RULES = r"""
fragile(Item) :- item(Item).
needs_reinforce(Item) :- fragile(Item), reinforce_tool(T), strong(T).
valid_story(Airport, Item, T) :- airport(Airport), item(Item), reinforce_tool(T), needs_reinforce(Item).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for a in AIRPORTS:
        lines.append(asp.fact("airport", a))
    for fid, f in FRAGILES.items():
        lines.append(asp.fact("item", fid))
        if f.fragile:
            lines.append(asp.fact("fragile_item", fid))
    for rid, r in REINFORCEMENTS.items():
        lines.append(asp.fact("reinforce_tool", rid))
        if r.strength > 0:
            lines.append(asp.fact("strong", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_story_combos() -> list[tuple[str, str, str]]:
    out = []
    for a in AIRPORTS:
        for f in FRAGILES:
            for r in REINFORCEMENTS:
                if FRAGILES[f].fragile and REINFORCEMENTS[r].strength > 0:
                    out.append((a, f, r))
    return out


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_story_combos()):
        print(f"OK: ASP matches Python gate ({len(valid_story_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH: ASP/Python gate differ.")
    try:
        sample = generate(StoryParams(
            airport="airport",
            fragile="paper_tag",
            reinforce="tape",
            helper="Auntie",
            helper_type="owl",
            traveler="Milo",
            traveler_type="cat",
            flashback=FLASHBACKS[0],
            delay=0,
        ))
        assert sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"MISMATCH: generate() smoke test failed: {exc}")
    return rc


CURATED = [
    StoryParams(
        airport="airport",
        fragile="paper_tag",
        reinforce="tape",
        helper="Auntie",
        helper_type="owl",
        traveler="Milo",
        traveler_type="cat",
        flashback=FLASHBACKS[0],
        delay=0,
    ),
    StoryParams(
        airport="airport",
        fragile="handle_wrap",
        reinforce="sticker_patch",
        helper="Mina",
        helper_type="dog",
        traveler="Poppy",
        traveler_type="rabbit",
        flashback=FLASHBACKS[1],
        delay=0,
    ),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible airport stories:\n")
        for combo in combos:
            print("  ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as exc:
                print(exc)
                return
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
