#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/tamper_fall_clamor_twist_misunderstanding_happy_ending.py
==========================================================================================

A standalone mystery-flavored TinyStories-style storyworld built from the seed
words: tamper, fall, clamor.

Premise
-------
A child notices something odd in a quiet museum or library-like place: a case
has been tampered with, something falls, and the resulting clamor causes a
misunderstanding. A careful check reveals the twist, and the ending is happy:
the true cause is simple, the confusion clears, and the missing item is safely
returned.

The world model is small and state-driven:
- typed entities
- physical meters and emotional memes
- forward rules for fall/clamor/tamper/twist/resolution
- a reasonableness gate and inline ASP twin
- grounded QA from simulated state, not rendered text

The style is mystery-like: quiet setup, a clue, a mistaken guess, a reveal, and a
warm ending image.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/tamper_fall_clamor_twist_misunderstanding_happy_ending.py
    python storyworlds/worlds/gpt-5.4-mini/tamper_fall_clamor_twist_misunderstanding_happy_ending.py --all
    python storyworlds/worlds/gpt-5.4-mini/tamper_fall_clamor_twist_misunderstanding_happy_ending.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/tamper_fall_clamor_twist_misunderstanding_happy_ending.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2

GIRL_NAMES = ["Mina", "Lila", "Nora", "Tess", "Zoe", "Ruby"]
BOY_NAMES = ["Pip", "Theo", "Owen", "Kai", "Eli", "Finn"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "librarian"}
        male = {"boy", "father", "dad", "man", "guard"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "librarian": "librarian"}.get(self.type, self.type)



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
    hush: str
    dark_spot: str

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
    phrase: str
    quiet_use: str
    noisy_use: str
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
class Object:
    id: str
    label: str
    phrase: str
    can_fall: bool = False
    can_bang: bool = False
    can_tamper: bool = False
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
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


SETTINGS = {
    "library": Setting("library", "the little library", "quiet as a whisper", "the back shelf"),
    "museum": Setting("museum", "the small museum", "still as a mouse", "the glass case"),
}

CLUES = {
    "map": Clue("map", "map", "a folded map", "read it by a lamp", "shake it loudly", {"map", "paper"}),
    "key": Clue("key", "key", "a brass key", "turn it gently", "drop it on the floor", {"key", "metal"}),
    "note": Clue("note", "note", "a tiny note", "peek at it quietly", "crumple it in a rush", {"note", "paper"}),
}

OBJECTS = {
    "shelf_sign": Object("shelf_sign", "sign", "a small sign on the shelf", can_fall=True, can_bang=True, tags={"sign", "fall"}),
    "glass_case": Object("glass_case", "case", "a glass case", can_fall=True, can_bang=True, tags={"case", "fall"}),
    "lantern": Object("lantern", "lantern", "a little lantern", can_fall=True, can_bang=True, can_tamper=True, tags={"lantern", "light"}),
    "box": Object("box", "box", "a clue box", can_tamper=True, tags={"box", "tamper"}),
}

RESPONSES = {
    "steady": Response("steady", 3, 4, "picked up the fallen clue box and set it back on the shelf", "tried to steady the mess, but the noise was already too big", "picked up the fallen clue box and set it back on the shelf", {"help", "quiet"}),
    "return": Response("return", 3, 3, "returned the lantern and closed the glass case door carefully", "tried to return everything, but the pieces were still too mixed up", "returned the lantern and closed the glass case door carefully", {"help", "quiet"}),
    "tap_off": Response("tap_off", 2, 2, "used a soft cloth to nudge the sign back into place", "nudged at it, but the clamor kept growing", "used a soft cloth to nudge the sign back into place", {"help", "quiet"}),
    "bucket": Response("bucket", 1, 1, "splashed water around the floor", "splashed water around the floor, which only made things worse", "splashed water around the floor", {"wrong"}),
}


@dataclass
@dataclass
class StoryParams:
    setting: str
    clue: str
    object: str
    response: str
    child: str
    child_gender: str
    helper: str
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


def hazard_at_risk(setting: Setting, clue: Clue, obj: Object) -> bool:
    return obj.can_tamper and obj.can_fall and ("fall" in obj.tags or "box" in obj.tags)


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, setting in SETTINGS.items():
        for cid, clue in CLUES.items():
            for oid, obj in OBJECTS.items():
                if hazard_at_risk(setting, clue, obj):
                    out.append((sid, cid, oid))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld about tamper, fall, and clamor.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child")
    ap.add_argument("--helper")
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


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.clue is None or c[1] == args.clue)
              and (args.object is None or c[2] == args.object)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, obj = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    child_gender = rng.choice(["girl", "boy"])
    helper_gender = "girl" if child_gender == "boy" else "boy"
    child = args.child or _pick_name(rng, child_gender)
    helper = args.helper or _pick_name(rng, helper_gender)
    return StoryParams(setting, clue, obj, response, child, child_gender, helper, helper_gender)


def _fall(world: World, obj: Entity) -> None:
    obj.meters["fallen"] += 1
    obj.meters["banged"] += 1
    world.get("room").meters["noise"] += 1
    for e in list(world.entities.values()):
        if e.kind == "character":
            e.memes["startle"] += 1


def _tamper(world: World, clue: Entity, obj: Entity) -> None:
    clue.meters["tampered"] += 1
    obj.meters["opened"] += 1


def tell(setting: Setting, clue: Clue, obj: Object, response: Response,
         child: str, child_gender: str, helper: str, helper_gender: str) -> World:
    w = World()
    c = w.add(Entity(child, "character", child_gender, role="child"))
    h = w.add(Entity(helper, "character", helper_gender, role="helper"))
    room = w.add(Entity("room", "room", "room"))
    clue_ent = w.add(Entity("clue", "thing", "thing", label=clue.label))
    obj_ent = w.add(Entity("object", "thing", "thing", label=obj.label))
    w.facts["setting"] = setting
    w.facts["clue_cfg"] = clue
    w.facts["obj_cfg"] = obj
    w.facts["response"] = response

    c.memes["curiosity"] = 2
    h.memes["care"] = 2

    w.say(f"At {setting.place}, {c.id} and {h.id} moved softly through {setting.hush}.")
    w.say(f"They noticed {clue.phrase} near {setting.dark_spot}, and the clue felt important.")
    w.para()
    w.say(f"{c.id} reached for the clue box, but someone had tried to tamper with the display.")
    _tamper(w, clue_ent, obj_ent)
    _fall(w, obj_ent)
    w.say(f"Then {obj.phrase} slipped and fell with a clamor that echoed through the room.")
    w.say(f"Both children froze, because the clamor sounded like trouble.")

    w.para()
    w.say(f"{h.id} thought the noise meant {c.id} had broken something on purpose.")
    w.say(f"But {c.id} pointed at the loose latch and the fallen box, and the mystery shifted.")
    if response.id in {"steady", "return", "tap_off"}:
        body = response.text
        w.say(f"{h.id} came closer and {body}.")
        w.say(f"The room went quiet again, and the true clue was left safe where it belonged.")
        w.say(f"In the end, the misunderstanding turned into a happy ending, with {c.id} smiling beside {h.id}.")
    else:
        body = response.fail
        w.say(f"{h.id} tried to help, but {body}.")
        w.say("A second clatter made the misunderstanding bigger, until another grown-up arrived.")
        w.say("Even so, the real problem was found and fixed, and everyone ended safe and calm.")

    w.facts.update(child=c, helper=h, room=room, clue=clue_ent, obj=obj_ent, outcome="happy")
    return w


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a mystery story for a young child that includes the words tamper, fall, and clamor.",
        f"Tell a gentle mystery where {f['child'].id} notices a tampered clue in {f['setting'].place} and a falling object causes a clamor.",
        f"Write a story with a misunderstanding and a happy ending set in a quiet {f['setting'].id}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    c, h, clue, obj = f["child"], f["helper"], f["clue_cfg"], f["obj_cfg"]
    return [
        ("Who is the story about?",
         f"It is about {c.id} and {h.id}, who were exploring a quiet place together. The mystery begins when they notice something had been tampered with."),
        ("What caused the clamor?",
         f"{obj.phrase} fell and made a loud clamor. That loud sound is what made everyone think trouble had started."),
        ("What was the misunderstanding?",
         f"{h.id} thought {c.id} had broken the display on purpose, but that was not true. The loose latch and the fallen object showed a different clue."),
        ("How did the story end?",
         f"It ended happily, with the true problem fixed and everyone calm again. The children understood each other better after the twist."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["clue_cfg"].tags) | set(world.facts["obj_cfg"].tags)
    out: list[tuple[str, str]] = []
    if "paper" in tags:
        out.append(("What is a note or map?", "A note or map is a piece of paper that can carry a message or a path. People read it carefully so they do not miss a clue."))
    if "metal" in tags:
        out.append(("What is a key?", "A key is a small metal tool that opens a lock. It should be handled gently so it does not slip away."))
    if "fall" in tags or "light" in tags:
        out.append(("Why can a falling object make a loud sound?", "When something falls, it hits the floor or shelf and makes a bang or clatter. That is why people look up when they hear it."))
    out.append(("What does tamper mean?", "To tamper with something is to touch or change it in a sneaky or improper way. It can make a clue look wrong even when the real story is different."))
    return out


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
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("library", "map", "box", "steady", "Mina", "girl", "Theo", "boy"),
    StoryParams("museum", "key", "lantern", "return", "Pip", "boy", "Nora", "girl"),
    StoryParams("museum", "note", "glass_case", "tap_off", "Zoe", "girl", "Eli", "boy"),
]


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    good = ", ".join(sorted(x.id for x in sensible_responses()))
    return f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}). Try: {good}.)"


def outcome_of(params: StoryParams) -> str:
    return "happy"


ASP_RULES = r"""
hazard(S, C, O) :- setting(S), clue(C), object(O), can_tamper(O), can_fall(O).
valid(S, C, O) :- hazard(S, C, O).
sensible(R) :- response(R), sense(R, N), sense_min(M), N >= M.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if o.can_fall:
            lines.append(asp.fact("can_fall", oid))
        if o.can_tamper:
            lines.append(asp.fact("can_tamper", oid))
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


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos()")
    if set(asp_sensible()) == {r.id for r in sensible_responses()}:
        print("OK: sensible responses match.")
    else:
        rc = 1
        print("MISMATCH in sensible responses.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        assert sample.story
        print("OK: smoke test generation succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], CLUES[params.clue], OBJECTS[params.object],
                 RESPONSES[params.response], params.child, params.child_gender,
                 params.helper, params.helper_gender)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}")
        print(f"{len(asp_valid_combos())} compatible combos.")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
