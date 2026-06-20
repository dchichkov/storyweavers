#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/wooden_youngest_living_room_suspense_repetition_fairy.py
=========================================================================================

A small fairy-tale storyworld about a youngest child in a living room, a
wooden object, a suspenseful repeated search, and a gentle ending.

The seed image:
- living room
- wooden
- youngest
- suspense
- repetition
- fairy tale style

This world builds a tiny simulation around a child hearing a mysterious tap in
the living room, searching under cushions and behind curtains, discovering a
wooden keepsake or toy, and sharing it with family or a helpful fairy-like
helper. The prose is driven by world state, not a frozen template swap.
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
SUSPENSE_STEP = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    wooden: bool = False
    hidden: bool = False
    found: bool = False
    keepsake: bool = False
    helper: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "fairy"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    hush: str
    nook: str
    props: str


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    wooden: bool = True
    secret: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    text: str
    repeat: str
    hiding: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes["curiosity"] < THRESHOLD:
        return out
    sig = ("suspense",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["unease"] += 1
    if "hall" in world.entities:
        world.get("hall").meters["quiet"] += 1
    out.append("__suspense__")
    return out


def _r_found(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    treasure = world.get("treasure")
    if child.meters["searching"] < THRESHOLD or treasure.found:
        return out
    if child.meters["clue"] < THRESHOLD:
        return out
    sig = ("found",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    treasure.found = True
    child.memes["relief"] += 1
    out.append("__found__")
    return out


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    if not world.get("treasure").found:
        return out
    sig = ("share",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("mother").memes["warmth"] += 1
    world.get("child").memes["joy"] += 1
    out.append("__share__")
    return out


CAUSAL_RULES = [Rule("suspense", "social", _r_suspense), Rule("found", "physical", _r_found), Rule("share", "social", _r_share)]


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


def reasonableness_gate(treasure: Treasure, clue: Clue) -> bool:
    return treasure.wooden and clue.hiding in {"under", "behind", "inside"}


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def predict(world: World, treasure: Treasure) -> dict:
    sim = world.copy()
    _search(sim, sim.get("child"), sim.get("clue"), treasure, narrate=False)
    return {
        "found": sim.get("treasure").found,
        "unease": sim.get("child").memes["unease"],
    }


def _search(world: World, child: Entity, clue: Entity, treasure: Treasure, narrate: bool = True) -> None:
    child.meters["searching"] += 1
    child.meters["clue"] += 1
    child.memes["curiosity"] += 1
    child.memes["brave"] += 0.5
    clue.meters["revealed"] += 1
    propagate(world, narrate=narrate)
    treasure_ent = world.get("treasure")
    treasure_ent.hidden = False


def introduce(world: World, child: Entity, mother: Entity, setting: Setting) -> None:
    world.say(
        f"In the {setting.place}, where the lamps made a soft gold glow, there lived a "
        f"{child.label_word} child named {child.id} and {mother.label_word} who kept the room kind and tidy."
    )
    world.say(
        f"The {setting.hush} of the room made every tiny sound easy to hear."
    )


def repeat_chase(world: World, child: Entity, clue: Entity, setting: Setting) -> None:
    world.say(
        f"Tap, tap, tap went something near {setting.nook}. {child.id} listened."
    )
    world.say(
        f"Tap, tap, tap went it again, and {child.id} looked once more."
    )
    world.say(
        f"Each time, the little noise seemed to hide and then return, as if it wanted to be found."
    )
    clue.meters["heard"] += 1


def warn(world: World, mother: Entity, child: Entity, treasure: Treasure) -> None:
    pred = predict(world, world.get("treasure_cfg"))
    mother.memes["care"] += 1
    world.facts["predicted_unease"] = pred["unease"]
    world.say(
        f'{mother.id} noticed {child.id} peeking toward the shadows. "A quiet room can feel larger at night," '
        f'{mother.pronoun()} said softly. "Let us look together, one step at a time."'
    )
    if pred["unease"] >= THRESHOLD:
        world.say(
            f"{mother.id} could already tell the suspense was growing, so {mother.pronoun()} kept {child.id} close."
        )


def search_beats(world: World, child: Entity, clue: Entity, treasure: Treasure, setting: Setting) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"{child.id} searched under the cushion, then behind the wooden chair, then under the cushion again."
    )
    world.say(
        f"At last, the clue led {child.id} to {setting.nook}, where the mystery waited."
    )
    _search(world, child, clue, treasure, narrate=False)
    world.say(
        f"There, nestled in a shadowy corner, {child.id} found {treasure.phrase}."
    )


def reveal(world: World, child: Entity, mother: Entity, treasure: Treasure) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"It was a small wooden treasure, worn smooth by many hands and shining like a secret moon."
    )
    world.say(
        f'{child.id} gasped. "{treasure.label.capitalize()}!"'
    )


def resolve(world: World, mother: Entity, child: Entity, treasure: Treasure, response: Response) -> None:
    if treasure.found:
        mother.memes["warmth"] += 1
        child.memes["joy"] += 1
    world.say(
        f"{mother.id} came over at once and {response.text.replace('{treasure}', treasure.label)}."
    )
    world.say(
        f"The room grew calm again, and the little wooden thing was safe in {mother.id}'s hands."
    )


def ending(world: World, mother: Entity, child: Entity, treasure: Treasure) -> None:
    world.say(
        f"Then {mother.id} placed it on the shelf by the window, where the moonlight could find it."
    )
    world.say(
        f"{child.id} gave one last look, then smiled, because the secret had turned into a story instead of a worry."
    )


def tell(setting: Setting, treasure: Treasure, clue: Clue, response: Response,
         child_name: str = "Mina", child_gender: str = "girl", mother_name: str = "Mother",
         mother_gender: str = "woman", youngest: bool = True) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child", age=4 if youngest else 6))
    mother = world.add(Entity(id=mother_name, kind="character", type=mother_gender, role="mother"))
    hall = world.add(Entity(id="hall", type="room", label="the living room"))
    tr = world.add(Entity(id="treasure", type="thing", label=treasure.label))
    clue_ent = world.add(Entity(id="clue", type="thing", label=clue.text))
    world.add(Entity(id="treasure_cfg", type="thing", label=treasure.label))
    child.memes["curiosity"] = 2.0
    child.memes["brave"] = 1.0
    world.facts["setting"] = setting
    world.facts["treasure"] = treasure
    world.facts["clue"] = clue
    world.facts["response"] = response
    world.facts["child"] = child
    world.facts["mother"] = mother

    introduce(world, child, mother, setting)
    world.para()
    repeat_chase(world, child, clue_ent, setting)
    warn(world, mother, child, treasure)
    world.para()
    search_beats(world, child, clue_ent, treasure, setting)
    reveal(world, child, mother, treasure)
    world.para()
    resolve(world, mother, child, treasure, response)
    ending(world, mother, child, treasure)

    world.facts.update(outcome="found" if tr.found else "missed")
    return world


SETTINGS = {
    "living_room": Setting("living_room", "living room", "hush", "sofa", "under the cushions"),
    "parlor": Setting("parlor", "parlor", "stillness", "fireplace", "behind the curtains"),
}

TREASURES = {
    "box": Treasure("box", "wooden box", "a wooden box", wooden=True, tags={"wooden", "box"}),
    "horse": Treasure("horse", "wooden horse", "a wooden horse", wooden=True, tags={"wooden", "toy"}),
}

CLUES = {
    "tap": Clue("tap", "tiny tap-tap", "tap, tap, tap", "under the sofa", tags={"tap", "suspense"}),
    "knock": Clue("knock", "gentle knock", "knock, knock, knock", "behind the chair", tags={"knock", "suspense"}),
}

SENSE_MIN = 2
RESPONSES = {
    "open": Response("open", 3, 3, "opened the little box and found a ribbon inside", "tried to open it, but the lid stuck fast"),
    "show": Response("show", 2, 2, "showed the wooden treasure to the family and smiled", "held it up, but the room stayed uneasy"),
    "listen": Response("listen", 3, 2, "sat quietly and listened until the tapping became a song", "listened, but the mystery stayed hidden"),
}

GIRL_NAMES = ["Mina", "Ella", "Luna", "Nina", "Tessa"]
BOY_NAMES = ["Owen", "Finn", "Theo", "Milo", "Eli"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for cid in CLUES:
            for tid, treasure in TREASURES.items():
                if reasonableness_gate(treasure, CLUES[cid]):
                    combos.append((sid, cid, tid))
    return combos


@dataclass
class StoryParams:
    setting: str
    clue: str
    treasure: str
    response: str
    child: str
    child_gender: str
    mother: str
    youngest: bool = True
    seed: Optional[int] = None


KNOWLEDGE = {
    "wooden": [("What is wooden?", "Wooden things are made from wood. Wood comes from trees, so wooden things feel sturdy and natural.")],
    "living_room": [("What is a living room?", "A living room is a room in a home where families sit, talk, and play together.")],
    "suspense": [("What is suspense in a story?", "Suspense is the feeling of wondering what will happen next. It makes a story exciting and a little mysterious.")],
    "repetition": [("Why do stories repeat things?", "Stories repeat words or actions to make them easier to remember and to build a steady rhythm.")],
    "fairy": [("What does a fairy often do in stories?", "A fairy is often a tiny magical helper who brings wonder, kindness, or a little bit of magic.")],
    "tap": [("What does a tap sound like?", "A tap is a small, quick knocking sound, like a finger on wood or a tiny pebble on a table.")],
}
KNOWLEDGE_ORDER = ["wooden", "living_room", "suspense", "repetition", "fairy", "tap"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy-tale story for a young child set in a living room, with the word "wooden" and a repeated tapping mystery.',
        f"Tell a suspenseful but gentle story about {f['child'].id}, the youngest child, who hears a tap-tap-tap in the living room and finds something wooden.",
        f'Write a story with repetition like "tap, tap, tap" and a happy ending where a hidden wooden thing is found in the living room.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    mother = f["mother"]
    treasure = f["treasure"]
    setting = f["setting"]
    qa = [
        ("Who is the story about?", f"It is about {child.id}, the youngest child, and {mother.id} in the {setting.place}."),
        ("What sound started the mystery?", f"The mystery started with a repeated tap, tap, tap sound that seemed to come from the {setting.nook}."),
        ("What did the child find?", f"{child.id} found {treasure.phrase}, a small wooden treasure hidden in the room."),
        ("How did the story end?", f"It ended calmly, with the wooden treasure safe and the child feeling glad instead of worried."),
    ]
    if f.get("outcome") == "found":
        qa.append(("Why was the story suspenseful?", f"It was suspenseful because the tapping kept repeating and the child did not know what was making it. The mystery slowly got closer until the hidden wooden thing was found."))
        qa.append(("What changed by the end?", f"At the end, the unknown tapping became a real treasure and the worry turned into wonder. The room felt calm again because the secret was no longer hidden."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["treasure"].tags) | set(world.facts["clue"].tags) | {"living_room", "repetition", "suspense", "fairy"}
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.wooden:
            bits.append("wooden=True")
        if e.hidden:
            bits.append("hidden=True")
        if e.found:
            bits.append("found=True")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("living_room", "tap", "box", "open", "Mina", "girl", "Mother", True),
    StoryParams("living_room", "knock", "horse", "show", "Owen", "boy", "Mother", True),
]


def explain_rejection(treasure: Treasure, clue: Clue) -> str:
    if not reasonableness_gate(treasure, clue):
        return "(No story: the clue does not fit the hidden wooden-treasure pattern for this fairy tale.)"
    return "(No story: this combination is not reasonable.)"


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        if t.wooden:
            lines.append(asp.fact("wooden", tid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("hiding", cid, c.hiding))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, C, T) :- setting(S), clue(C), treasure(T), wooden(T), hiding(C, H), H = "under"; H = "behind"; H = "inside".
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program(show="#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP gate matches valid_combos().")
    else:
        rc = 1
        print("MISMATCH: ASP gate does not match valid_combos().")
    if {r.id for r in sensible_responses()} == set(asp_sensible()):
        print("OK: ASP sensible responses match.")
    else:
        rc = 1
        print("MISMATCH: ASP sensible responses differ.")
    sample = generate(CURATED[0])
    if not sample.story.strip():
        rc = 1
        print("MISMATCH: smoke test story is empty.")
    else:
        print("OK: smoke test generation succeeded.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale story world for a youngest child and a wooden mystery in the living room.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--mother")
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
    if args.setting and args.clue and args.treasure:
        if not reasonableness_gate(TREASURES[args.treasure], CLUES[args.clue]):
            raise StoryError(explain_rejection(TREASURES[args.treasure], CLUES[args.clue]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.clue is None or c[1] == args.clue)
              and (args.treasure is None or c[2] == args.treasure)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, treasure = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    t = TREASURES[treasure]
    gender = args.gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    mother = args.mother or "Mother"
    return StoryParams(setting, clue, treasure, response, child, gender, mother, True)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], TREASURES[params.treasure], CLUES[params.clue], RESPONSES[params.response], params.child, params.child_gender, params.mother, "woman", params.youngest)
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
        print(asp_program(show="#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}")
        print(f"{len(asp_valid_combos())} compatible combos")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            try:
                p = resolve_params(args, random.Random(base_seed + i))
            except StoryError as e:
                print(e)
                return
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        hdr = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=hdr)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
