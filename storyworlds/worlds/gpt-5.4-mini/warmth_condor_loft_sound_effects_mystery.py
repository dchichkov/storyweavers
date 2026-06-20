#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/warmth_condor_loft_sound_effects_mystery.py
============================================================================

A standalone storyworld for a small mystery set in a cozy loft.

Premise:
- A child hears strange sound effects in the loft.
- A condor-themed object is involved.
- The child feels warmth from a hidden source.
- A careful search reveals the cause and ends in a gentle, clear resolution.

This world keeps the prose child-facing, concrete, and state-driven.
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
MIN_SOUND_CLUES = 2


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
class Place:
    id: str
    label: str
    cozy: bool = False
    loft: bool = False
    hidden_places: list[str] = field(default_factory=list)

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
    sound: str
    where: str
    effect: str
    score: int
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
class Cause:
    id: str
    label: str
    warmth_source: bool = False
    harmless: bool = True
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
        self.world = self  # for trace/debug convenience

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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        if ("warmth_notice",) not in world.fired and world.facts.get("warmth_hint"):
            world.fired.add(("warmth_notice",))
            world.get("room").memes["curiosity"] += 1
            out.append("A small warm draft seemed to be hiding a secret.")
            changed = True
        if ("clue_chain",) not in world.fired and world.facts.get("sound_clues", 0) >= MIN_SOUND_CLUES:
            world.fired.add(("clue_chain",))
            world.get("child").memes["confidence"] += 1
            out.append("__clue_chain__")
            changed = True
    if narrate:
        for line in out:
            if line != "__clue_chain__":
                world.say(line)
    return out


def predict_hidden_source(world: World, source_id: str) -> dict:
    sim = world.copy()
    _inspect_source(sim, sim.get(source_id), narrate=False)
    return {
        "warmth": sim.facts.get("warmth_hint", False),
        "clues": sim.facts.get("sound_clues", 0),
    }


def _inspect_source(world: World, source: Entity, narrate: bool = True) -> None:
    source.memes["noticed"] += 1
    world.facts["warmth_hint"] = True
    world.facts["sound_clues"] = world.facts.get("sound_clues", 0) + 1
    propagate(world, narrate=narrate)


def setup(world: World, child: Entity, helper: Entity, place: Place) -> None:
    world.say(
        f"On a quiet evening, {child.id} and {helper.id} climbed up to the {place.label}."
    )
    world.say(
        f"The {place.label} was {('cozy' if place.cozy else 'dim')}, and the air had a faint warmth to it."
    )


def first_sound(world: World, child: Entity, clue: Clue) -> None:
    child.memes["unease"] += 1
    world.say(f"Then came a sound: {clue.sound}.")
    world.say(f"It seemed to come from {clue.where}, and it felt like {clue.effect}.")


def second_sound(world: World, helper: Entity, clue: Clue) -> None:
    helper.memes["focus"] += 1
    world.facts["sound_clues"] = world.facts.get("sound_clues", 0) + 1
    world.say(f"{helper.id} pointed. Another sound answered: {clue.sound}.")
    world.say(f"This time it seemed closer to {clue.where}.")


def notice_condor(world: World, child: Entity, helper: Entity, cause: Cause) -> None:
    child.memes["curiosity"] += 1
    helper.memes["curiosity"] += 1
    world.say(
        f"Behind a folded blanket, they found {cause.label}, all tangled in dust and feathers."
    )
    world.say(
        f"It was a condor-shaped toy, and the warmth came from a tiny lamp tucked beside it."
    )


def explain(world: World, helper: Entity, cause: Cause) -> None:
    world.say(
        f"{helper.label_word.capitalize()} smiled and turned the lamp off. "
        f'"The sound effects were only the toy moving in the draft," {helper.pronoun()} said softly.'
    )
    world.say(
        f'"The warmth was just the lamp. Nothing scary was hiding here."'
    )


def ending(world: World, child: Entity, helper: Entity, place: Place) -> None:
    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"{child.id} tucked the condor toy onto a shelf in the {place.label}, and the loft felt peaceful again."
    )
    world.say(
        f"In the quiet, the little room was warm in the safe way, with no more mystery left to chase."
    )


def tell(place: Place, clue1: Clue, clue2: Clue, cause: Cause,
         child_name: str = "Mina", child_gender: str = "girl",
         helper_name: str = "Mom", helper_gender: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    room = world.add(Entity(id="room", type="room", label=place.label))
    source = world.add(Entity(id="source", type="thing", label=cause.label))
    world.facts.update(place=place, clue1=clue1, clue2=clue2, cause=cause,
                       child=child, helper=helper, room=room, source=source)

    setup(world, child, helper, place)
    world.para()
    first_sound(world, child, clue1)
    second_sound(world, helper, clue2)
    world.para()
    if predict_hidden_source(world, "source")["clues"] >= MIN_SOUND_CLUES:
        notice_condor(world, child, helper, cause)
        explain(world, helper, cause)
    else:
        world.say("They listened, but the loft stayed silent and gave no answer.")
    world.para()
    ending(world, child, helper, place)

    world.facts["resolved"] = True
    return world


PLACES = {
    "loft": Place("loft", "loft", cozy=True, loft=True,
                  hidden_places=["behind the trunk", "under the eaves", "near the rafters"]),
    "attic": Place("attic", "attic", cozy=False, loft=True,
                   hidden_places=["behind the boxes", "under the slanted roof"]),
    "studio": Place("studio", "studio loft", cozy=True, loft=True,
                    hidden_places=["behind the curtain", "near the skylight"]),
}

CLUES = {
    "tap": Clue("tap", "tap-tap-tap", "the window frame", "a careful little message", 1, {"sound"}),
    "creak": Clue("creak", "creeeak", "the ladder", "an old sleepy whisper", 1, {"sound"}),
    "flutter": Clue("flutter", "flap-flap", "the rafters", "soft wings or cloth", 1, {"sound"}),
    "whir": Clue("whir", "whirr-whirr", "a small fan", "a tiny rushing secret", 1, {"sound"}),
}

CAUSES = {
    "condor_toy": Cause("condor_toy", "a condor-shaped toy", harmless=True, tags={"condor"}),
    "paper_condor": Cause("paper_condor", "a paper condor hanging by a string", harmless=True, tags={"condor"}),
    "kite": Cause("kite", "a condor kite from the last windy day", harmless=True, tags={"condor"}),
}

SAFE_LIGHTS = ["lamp", "night-light", "small lantern"]

GIRL_NAMES = ["Mina", "Lena", "Iris", "Nora", "Ava"]
BOY_NAMES = ["Theo", "Owen", "Eli", "Finn", "Leo"]
HELPERS = [("Mom", "mother"), ("Dad", "father")]


@dataclass
@dataclass
class StoryParams:
    place: str
    clue1: str
    clue2: str
    cause: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
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
    for p in PLACES:
        for c1 in CLUES:
            for c2 in CLUES:
                if c1 != c2:
                    for cause in CAUSES:
                        combos.append((p, c1, cause))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny mystery storyworld with warmth, a condor, and loft sound effects.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue1", choices=CLUES)
    ap.add_argument("--clue2", choices=CLUES)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["mother", "father"])
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
    if args.clue1 and args.clue2 and args.clue1 == args.clue2:
        raise StoryError("Choose two different sound clues.")
    place = args.place or rng.choice(list(PLACES))
    clue1 = args.clue1 or rng.choice(list(CLUES))
    clue2 = args.clue2 or rng.choice([k for k in CLUES if k != clue1])
    cause = args.cause or rng.choice(list(CAUSES))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper_gender = args.helper_gender or rng.choice(["mother", "father"])
    helper_name = args.helper_name or ( "Mom" if helper_gender == "mother" else "Dad")
    return StoryParams(place, clue1, clue2, cause, child_name, child_gender, helper_name, helper_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly mystery story set in a {f["place"].label} that includes the words "warmth", "condor", and "loft".',
        f"Tell a gentle mystery where {f['child'].id} hears sound effects in the loft and discovers what is making the warmth.",
        f"Write a short story with tap-tap sounds, a condor clue, and a cozy ending in the loft.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    place = f["place"]
    cause = f["cause"]
    return [
        QAItem(
            question="What kind of place was the story set in?",
            answer=f"It was set in a {place.label}. That made the mystery feel close and cozy."
        ),
        QAItem(
            question="What did the child hear?",
            answer=f"{child.id} heard sound effects like {f['clue1'].sound} and {f['clue2'].sound}. Those sounds led them to search the loft more carefully."
        ),
        QAItem(
            question="What caused the warmth?",
            answer=f"The warmth came from {cause.label}. It was harmless, and the little lamp or toy made the room feel warmer than expected."
        ),
        QAItem(
            question="What did the grown-up do at the end?",
            answer=f"{helper.id} explained the clues and turned off the lamp. That solved the mystery and left the loft calm again."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a loft?", "A loft is a room up high under the roof. It can feel quiet, hidden, and a little mysterious."),
        QAItem("What are sound effects in a story?", "Sound effects are words that imitate a noise, like tap-tap or creak. They help the reader hear the scene."),
        QAItem("What is warmth?", "Warmth is the feeling of being gently warm, like from sunlight, a lamp, or a cozy blanket."),
        QAItem("What is a condor?", "A condor is a very large bird with broad wings. In stories, a condor can also show up as a toy, picture, or kite."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,C1,C2,O) :- place(P), clue(C1), clue(C2), C1 != C2, cause(O).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    for o in CAUSES:
        lines.append(asp.fact("cause", o))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp  # noqa: F401
    py = set(valid_combos())
    cl = set((p, c1, c2, o) for (p, c1, c2, o) in asp_valid_combos())
    rc = 0
    if py != cl:
        rc = 1
        print("MISMATCH between ASP and Python combos.")
    else:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    sample = generate(resolve_params(argparse.Namespace(place=None, clue1=None, clue2=None, cause=None,
                                                        child_name=None, child_gender=None, helper_name=None,
                                                        helper_gender=None), random.Random(7)))
    if not sample.story.strip():
        rc = 1
        print("MISMATCH: story generation returned empty text.")
    else:
        print("OK: generate() smoke test produced story text.")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], CLUES[params.clue1], CLUES[params.clue2], CAUSES[params.cause],
                 params.child_name, params.child_gender, params.helper_name, params.helper_gender)
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
    StoryParams("loft", "tap", "creak", "condor_toy", "Mina", "girl", "Mom", "mother"),
    StoryParams("studio", "flutter", "whir", "paper_condor", "Theo", "boy", "Dad", "father"),
    StoryParams("attic", "tap", "flutter", "kite", "Nora", "girl", "Mom", "mother"),
]


def explain_rejection(params: StoryParams) -> str:
    return "Choose two different sound clues."


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
