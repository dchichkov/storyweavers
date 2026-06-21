#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/gloom_humor_flashback_kindness_slice_of_life.py
===============================================================================

A small slice-of-life storyworld about a gloomy afternoon, a tiny mishap,
a funny flashback, and a kind repair that makes the day feel warmer.

Seed prompt
-----------
Write a story that includes the following words and narrative instruments.
Words: gloom
Features: Humor, Flashback, Kindness
Style: Slice of Life
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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "grandma"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "grandmother": "grandma", "grandfather": "grandpa"}.get(self.type, self.type)
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
    mood: str
    affords: set[str] = field(default_factory=set)
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
class ObjectCfg:
    id: str
    label: str
    phrase: str
    problem: str
    fix: str
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
class HelperCfg:
    id: str
    label: str
    phrase: str
    kindness: int
    humor: int
    helps_with: set[str] = field(default_factory=set)
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


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


def _r_gloom(world: World) -> list[str]:
    out = []
    if world.place.mood != "gloomy":
        return out
    for e in list(world.entities.values()):
        if e.kind == "character" and e.memes["gloom"] >= THRESHOLD:
            sig = ("gloom", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.memes["cheer"] -= 0.5
            out.append("")
    return out


def _r_kindness(world: World) -> list[str]:
    out = []
    helper = world.entities.get("helper")
    child = world.entities.get("child")
    if not helper or not child:
        return out
    if helper.memes["kindness"] < THRESHOLD or child.meters["trouble"] < THRESHOLD:
        return out
    sig = ("kindness",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["trouble"] = 0.0
    child.memes["relief"] += 1
    helper.memes["warmth"] += 1
    out.append("")
    return out


CAUSAL_RULES = [Rule("gloom", _r_gloom), Rule("kindness", _r_kindness)]


def propagate(world: World) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            if rule.apply(world):
                changed = True


def tell(place: Place, item: ObjectCfg, helper: HelperCfg, child_name: str, child_type: str, helper_name: str, helper_type: str) -> World:
    world = World(place)
    child = world.add(Entity(id="child", kind="character", type=child_type, label=child_name, role="protagonist"))
    helper_ent = world.add(Entity(id="helper", kind="character", type=helper_type, label=helper_name, role="helper"))
    thing = world.add(Entity(id="thing", type="thing", label=item.label, attrs={"problem": item.problem, "fix": item.fix}))

    child.memes["gloom"] = 1.0 if place.mood == "gloomy" else 0.0
    helper_ent.memes["kindness"] = float(helper.kindness)
    helper_ent.memes["humor"] = float(helper.humor)

    world.say(
        f"It was a {place.mood} afternoon at {place.label}, the kind of day when even the windows seemed to sigh."
    )
    world.say(
        f"{child.label} frowned at {item.phrase}. {child.pronoun().capitalize()} had meant to keep it safe, but now {item.problem}."
    )

    world.para()
    child.meters["trouble"] += 1
    child.memes["worry"] += 1
    world.say(
        f"{child.label} gave a tiny groan and then laughed at {child.pronoun('object')}self, because the whole thing sounded a little ridiculous."
    )
    world.say(
        "That pulled up a memory: last week, when the same problem happened, the cat sat on the bag as if it were guarding treasure."
    )
    child.memes["flashback"] += 1

    world.para()
    world.say(
        f"{helper_name} noticed the face and came over with a soft smile. {helper_name} did not make a big speech; {helper_name} just sat down beside {child.label}."
    )
    if helper.humor:
        world.say(
            f'"Maybe the day is only trying to teach us a new trick," {helper_name} said, and {child.label} snorted because that sounded like something a blanket would say.'
        )
    world.say(
        f"Then {helper_name} helped with {item.fix}, and the little trouble was gone."
    )
    world.say(
        f"{child.label}'s shoulders loosened. Even the gloom felt thinner when two people were handling one small problem together."
    )

    child.memes["joy"] += 1
    helper_ent.memes["warmth"] += 1
    propagate(world)

    world.para()
    world.say(
        f"Before long, {child.label} was back to the day, smiling at the funny memory and carrying {item.phrase} as carefully as if it were a prize."
    )
    world.say(
        f"The {place.label} was still gray outside, but inside the moment had turned bright in its own quiet way."
    )

    world.facts.update(
        child=child,
        helper=helper_ent,
        thing=thing,
        place=place,
        item=item,
    )
    return world


PLACES = {
    "kitchen": Place(id="kitchen", label="the kitchen", mood="gloomy", affords={"fix"}),
    "porch": Place(id="porch", label="the porch", mood="gloomy", affords={"fix"}),
    "living_room": Place(id="living_room", label="the living room", mood="gloomy", affords={"fix"}),
    "sunroom": Place(id="sunroom", label="the sunroom", mood="soft", affords={"fix"}),
}

OBJECTS = {
    "spilled_tea": ObjectCfg(
        id="spilled_tea",
        label="tea",
        phrase="a warm mug of tea",
        problem="a little spill had dripped onto the table",
        fix="wiping it up with a towel and setting the mug on a coaster",
        tags={"tea", "spill"},
    ),
    "tangled_scarf": ObjectCfg(
        id="tangled_scarf",
        label="scarf",
        phrase="a blue scarf",
        problem="it had become tangled in a chair leg",
        fix="untying the knot and folding it neatly",
        tags={"scarf", "tangle"},
    ),
    "missing_cookie": ObjectCfg(
        id="missing_cookie",
        label="cookie",
        phrase="a plate with one missing cookie",
        problem="the last cookie had disappeared",
        fix="finding the crumbs and sharing the last two cookies anyway",
        tags={"cookie", "humor"},
    ),
}

HELPERS = {
    "neighbor": HelperCfg(
        id="neighbor",
        label="the neighbor",
        phrase="a friendly neighbor",
        kindness=2,
        humor=1,
        helps_with={"fix"},
        tags={"kindness", "neighbor"},
    ),
    "grandma": HelperCfg(
        id="grandma",
        label="grandma",
        phrase="grandma",
        kindness=3,
        humor=2,
        helps_with={"fix"},
        tags={"kindness", "flashback", "humor"},
    ),
    "older_sibling": HelperCfg(
        id="older_sibling",
        label="older sibling",
        phrase="an older sibling",
        kindness=2,
        humor=2,
        helps_with={"fix"},
        tags={"kindness", "humor"},
    ),
}

CHILDREN = {
    "Mina": "girl",
    "Eli": "boy",
    "Noa": "girl",
    "Theo": "boy",
}

@dataclass
class StoryParams:
    place: str
    object: str
    helper: str
    child_name: str
    child_gender: str
    helper_name: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for o in OBJECTS:
            for h in HELPERS:
                combos.append((p, o, h))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny gloomy slice-of-life storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--object", dest="object_", choices=OBJECTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.object_:
        combos = [c for c in combos if c[1] == args.object_]
    if args.helper:
        combos = [c for c in combos if c[2] == args.helper]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, obj, helper = rng.choice(sorted(combos))
    child_gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(["Mina", "Eli", "Noa", "Theo"])
    helper_name = args.helper_name or rng.choice(["Aunt June", "Mr. Pate", "Nana", "Rae"])
    return StoryParams(place=place, object=obj, helper=helper, child_name=child_name, child_gender=child_gender, helper_name=helper_name, helper_gender=helper_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a slice-of-life story about {f['child'].label} on a gloomy afternoon.",
        f"Tell a kind, funny story in which {f['helper'].label} helps with {f['item'].phrase}.",
        f"Write a story that includes a small flashback and the word gloom.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    item = f["item"]
    return [
        QAItem(
            question="What kind of afternoon was it?",
            answer=f"It was a gloomy afternoon, so the day felt gray and a little heavy at first. That mood made the small problem seem bigger until someone kind sat down to help.",
        ),
        QAItem(
            question="What funny memory did the child remember?",
            answer="The child remembered a time when the cat sat on the bag like it was guarding treasure. That silly picture helped turn worry into a laugh.",
        ),
        QAItem(
            question=f"How did {helper.label} help?",
            answer=f"{helper.label} stayed calm, sat beside {child.label}, and helped with {item.fix}. The kindness made the trouble disappear and left the day feeling warmer.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does gloomy mean?",
            answer="Gloomy means dark, gray, or heavy-feeling, like the sky is covered and the day has less sparkle. People can still be safe and cozy on a gloomy day.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when the story briefly remembers something that happened earlier. It helps explain why a character feels a certain way now.",
        ),
        QAItem(
            question="What does kindness look like?",
            answer="Kindness looks like listening, helping, and staying gentle when someone has a problem. Small kind actions can make a hard moment feel much easier.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
gloom(E) :- mood(gloomy), character(E).
kindness(E) :- character(E), kind(E).
helped :- kindness(helper), trouble(child).
flashback :- remembers(child).
ending_warm :- helped.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("mood", pid, p.mood))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    try:
        model = asp.one_model(asp_program("", "#show ending_warm/0."))
        _ = model
    except Exception as exc:
        print(f"ASP smoke test failed: {exc}")
        return 1
    print("OK: ASP smoke test ran.")
    return 0


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.object not in OBJECTS or params.helper not in HELPERS:
        raise StoryError("Invalid params.")
    world = tell(
        PLACES[params.place],
        OBJECTS[params.object],
        HELPERS[params.helper],
        params.child_name,
        params.child_gender,
        params.helper_name,
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
    StoryParams(place="kitchen", object="missing_cookie", helper="grandma", child_name="Mina", child_gender="girl", helper_name="Grandma Jo", helper_gender="girl"),
    StoryParams(place="living_room", object="spilled_tea", helper="neighbor", child_name="Eli", child_gender="boy", helper_name="Mr. Pate", helper_gender="boy"),
    StoryParams(place="porch", object="tangled_scarf", helper="older_sibling", child_name="Noa", child_gender="girl", helper_name="Rae", helper_gender="girl"),
]


def generate_story(params: StoryParams) -> StorySample:
    return generate(params)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show ending_warm/0."))
        return
    if args.verify:
        rc = asp_verify()
        try:
            sample = generate(CURATED[0])
            _ = sample.story
            print("OK: normal generate() smoke test passed.")
        except Exception as exc:
            print(f"Generate smoke test failed: {exc}")
            rc = 1
        sys.exit(rc)
    if args.asp:
        print("asp mode is available; this world is intentionally tiny.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
