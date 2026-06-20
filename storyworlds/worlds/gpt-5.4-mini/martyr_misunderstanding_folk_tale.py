#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/martyr_misunderstanding_folk_tale.py
====================================================================

A standalone story world for a small folk-tale domain about a village child,
a misunderstood old word, and a gentle correction that turns fear into a wiser
kind of help.

Seed premise
------------
A child hears the word "martyr" in an old story and misunderstands it. The child
starts acting as if a martyr must keep suffering quietly and never ask for help.
A village elder corrects the misunderstanding, and the child learns that true
kindness does not mean hiding pain; it means sharing burdens so the whole village
can help.

This world keeps the tone close to a folk tale: a small village, a village elder,
a family task, an omen-like problem, a mistaken belief, and a warm lesson at the
end.
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
SENSE_MIN = 2


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
        female = {"girl", "mother", "mom", "woman", "grandmother", "elder"}
        male = {"boy", "father", "dad", "man", "grandfather", "village elder"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    name: str
    mood: str
    has_well: bool = False
    has_bridge: bool = False


@dataclass
class ObjectThing:
    id: str
    label: str
    phrase: str
    weight: int
    precious: bool = False
    fragile: bool = False
    carries_water: bool = False
    warms: bool = False
    sounds_like: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Misunderstanding:
    id: str
    label: str
    wrong_idea: str
    right_idea: str
    clue: str
    fear: str
    turn: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_sad(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.memes["burden"] >= THRESHOLD and ("sad", e.id) not in world.fired:
            world.fired.add(("sad", e.id))
            e.memes["worry"] += 1
            out.append("")
    return out


CAUSAL_RULES = [Rule("sad", "social", _r_sad)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if s)
    if narrate:
        for s in out:
            world.say(s)
    return out


def is_reasonable(mis: Misunderstanding, obj: ObjectThing) -> bool:
    return True


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def family_task(place: Place, obj: ObjectThing) -> bool:
    return place.has_well or obj.carries_water


def tell(place: Place, obj: ObjectThing, mis: Misunderstanding, resp: Response,
         child_name: str = "Toma", child_gender: str = "boy",
         elder_name: str = "Aunt Mara", elder_gender: str = "woman",
         helper_name: str = "Jori", helper_gender: str = "girl") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender,
                             role="child", traits=["curious"]))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_gender,
                             role="elder", label="the elder"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender,
                              role="helper"))
    well = world.add(Entity(id="well", type="place", label="the well"))
    bucket = world.add(Entity(id="bucket", type="thing", label=obj.label))
    child.memes["burden"] = 0.0

    world.say(
        f"In a small village between the river and the pine trees, {child.id} "
        f"listened to old tales by the hearth. One night {elder.id} said the word "
        f'"{mis.label}," and {child.id} took it the wrong way.'
    )
    world.say(
        f"{child.id} thought {mis.wrong_idea}. So {child.pronoun()} grew quiet and "
        f"tried to prove it by carrying {obj.phrase} alone."
    )

    world.para()
    child.memes["burden"] += 1
    world.say(
        f"At dawn, the village task began. The bucket was heavy, the path was long, "
        f"and {child.id}'s shoulders soon ached."
    )
    world.say(
        f"{child.id} would not ask for help, because {child.pronoun()} believed "
        f"{mis.fear}."
    )

    world.para()
    world.say(
        f"But {helper.id} saw {child.id} stumbling and called out, "
        f'"That is not what {mis.label} means!"'
    )
    world.say(
        f"{elder.id} came at once and explained that {mis.right_idea}. "
        f"{mis.clue}."
    )
    world.say(
        f"Then {elder.id} showed {mis.turn}, and the village learned a kinder way."
    )
    child.memes["burden"] = 0.0
    helper.memes["joy"] += 1
    child.memes["relief"] += 1

    world.para()
    world.say(
        f"{child.id} finally set the bucket down by the well and let {helper.id} "
        f"take one handle while {elder.id} took the other."
    )
    world.say(
        f"Together they carried {obj.phrase} home, and by sunset the work was done "
        f"with singing instead of silence."
    )
    world.say(
        f"{child.id} learned that a true martyr is not a child who suffers alone; "
        f"it is a brave soul who loves something enough to face hardship, and wise "
        f"people still share the load."
    )

    world.facts.update(
        child=child, elder=elder, helper=helper, place=place, object=obj,
        misunderstanding=mis, response=resp, burden=child.memes["burden"],
        learned=True, shared=True
    )
    return world


PLACES = {
    "village": Place("village", "the village green", "quiet", has_well=True),
    "mill": Place("mill", "the old mill lane", "busy", has_well=False),
    "river": Place("river", "the river bank", "windy", has_well=True, has_bridge=True),
}

OBJECTS = {
    "water": ObjectThing("water", "water bucket", "a pail of water", 6, carries_water=True, sounds_like="slosh"),
    "bread": ObjectThing("bread", "bread basket", "a basket of bread", 4, precious=True, sounds_like="soft rustle"),
    "wood": ObjectThing("wood", "firewood bundle", "a bundle of firewood", 7, warms=True, sounds_like="thump"),
}

MISUNDERSTANDINGS = {
    "martyr": Misunderstanding(
        "martyr",
        "martyr",
        "a martyr was someone who must never ask for help",
        "a martyr is someone who endures hardship for a cause or a good promise",
        "The elder had meant that old tales honor brave people, not lonely children",
        "sharing a burden felt like failing the tale",
        "the good part of the story was the helping, not the suffering",
        tags={"martyr", "misunderstanding", "folk_tale"},
    ),
}

RESPONSES = {
    "explain": Response(
        "explain", 3, 4,
        "explained the old word kindly and helped carry the bucket with the others",
        "explained too late, after the child had already collapsed under the load",
        "explained the word and shared the work",
        tags={"martyr", "help"},
    ),
    "sing": Response(
        "sing", 2, 3,
        "began a work-song and matched the pace so the bucket felt lighter",
        "tried to sing, but the child still felt alone under the weight",
        "broke the silence with a song and shared the work",
        tags={"song", "help"},
    ),
    "cart": Response(
        "cart", 3, 5,
        "rolled out a small handcart and set the bucket on its wooden bed",
        "rolled out the cart, but the lane was too rough and the load spilled",
        "used a handcart to carry the load safely",
        tags={"cart", "help"},
    ),
    "ignore": Response(
        "ignore", 1, 1,
        "watched quietly and did nothing at all",
        "watched quietly while the child grew more tired and lonely",
        "did nothing",
        tags={"ignore"},
    ),
}

GIRL_NAMES = ["Mara", "Tavi", "Nia", "Lina", "Sela", "Iria", "Asha"]
BOY_NAMES = ["Toma", "Bren", "Niko", "Soren", "Pavel", "Jori"]
TRAITS = ["curious", "gentle", "thoughtful", "patient", "brave"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for m in MISUNDERSTANDINGS:
            for o in OBJECTS:
                if family_task(PLACES[p], OBJECTS[o]):
                    combos.append((p, m, o))
    return combos


@dataclass
class StoryParams:
    place: str
    misunderstanding: str
    object: str
    child: str
    child_gender: str
    elder: str
    elder_gender: str
    helper: str
    helper_gender: str
    trait: str
    response: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale story world about a misunderstood old word.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
              and (args.misunderstanding is None or c[1] == args.misunderstanding)
              and (args.object is None or c[2] == args.object)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mis, obj = rng.choice(sorted(combos))
    child_gender = rng.choice(["boy", "girl"])
    elder_gender = rng.choice(["woman", "man"])
    child = args.child if hasattr(args, "child") and getattr(args, "child", None) else rng.choice(BOY_NAMES if child_gender == "boy" else GIRL_NAMES)
    elder = args.elder if hasattr(args, "elder") and getattr(args, "elder", None) else ("Aunt Mara" if elder_gender == "woman" else "Uncle Rook")
    helper = args.helper if hasattr(args, "helper") and getattr(args, "helper", None) else rng.choice(GIRL_NAMES + BOY_NAMES)
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    return StoryParams(place, mis, obj, child, child_gender, elder, elder_gender, helper, "girl" if helper in GIRL_NAMES else "boy", rng.choice(TRAITS), response)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk-tale style story for a young child that includes the word "{f["misunderstanding"].label}" and a misunderstanding about what it means.',
        f"Tell a small village story where {f['child'].id} takes the word {f['misunderstanding'].label} the wrong way, then learns a kinder truth from {f['elder'].id}.",
        f"Write a gentle tale about heavy work, an old word, and a village helper who sets the misunderstanding right.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    helper = f["helper"]
    mis = f["misunderstanding"]
    obj = f["object"]
    return [
        QAItem(
            question="What did the child misunderstand?",
            answer=f"{child.id} misunderstood the word {mis.label}. {child.pronoun('subject').capitalize()} thought {mis.wrong_idea}.",
        ),
        QAItem(
            question="How did the elder fix the misunderstanding?",
            answer=f"{elder.id} explained that {mis.right_idea}. {mis.clue}. That helped {child.id} see the old word more clearly.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer=f"The work was shared instead of carried alone. {child.id}, {helper.id}, and {elder.id} carried {obj.phrase} together, and {child.id} ended with relief instead of worry.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a martyr?",
            answer="A martyr is a person who suffers or gives up comfort for a cause or belief. In old stories, the word often carries courage and sacrifice.",
        ),
        QAItem(
            question="Why is it better to share a heavy task?",
            answer="Sharing a heavy task keeps one person from getting worn out or hurt. When people help each other, the load feels lighter and the work gets done safely.",
        ),
        QAItem(
            question="What is a folk tale?",
            answer="A folk tale is an old kind of story passed from mouth to mouth. It often has simple villagers, a lesson, and a little bit of magic or wonder in the feeling of it.",
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
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
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("village", "martyr", "water", "Toma", "boy", "Aunt Mara", "woman", "Jori", "boy", "curious", "explain"),
    StoryParams("river", "martyr", "bread", "Mara", "girl", "Uncle Rook", "man", "Nia", "girl", "gentle", "cart"),
]


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}). Try: {better}.)"


ASP_RULES = r"""
valid(P, M, O) :- place(P), misunderstanding(M), object(O), family_task(P, O).
good_response(R) :- response(R), sense(R, S), sense_min(M), S >= M.
outcome(shared) :- good_response(R), response(R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for mid in MISUNDERSTANDINGS:
        lines.append(asp.fact("misunderstanding", mid))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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
        print("MISMATCH in valid combos.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        return 1 if not print(exc) else 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        OBJECTS[params.object],
        MISUNDERSTANDINGS[params.misunderstanding],
        RESPONSES[params.response],
        params.child,
        params.child_gender,
        params.elder,
        params.elder_gender,
        params.helper,
        params.helper_gender,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q.question, q.answer) for q in story_qa(world)],
        world_qa=[QAItem(q.question, q.answer) for q in world_knowledge_qa(world)],
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
    samples = [generate(resolve_params(args, random.Random(base_seed + i))) for i in range(args.n)]
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))


if __name__ == "__main__":
    main()
