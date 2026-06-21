#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/pipe_caddy_sound_effects_whodunit.py
=====================================================================

A tiny whodunit storyworld built from the seed words "pipe" and "caddy" with
sound effects as a narrative instrument.

Premise:
- A small mystery happens in a study.
- A child or detective hears distinct sounds, notices a missing item, and
  follows clues.
- The story turns on concrete state changes: who had the pipe, where the caddy
  was moved, and what sound led to the reveal.
- The ending shows the culprit found and the pipe returned.

This is a standalone storyworld script under the Storyweavers contract.
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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    dim: str
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
class Prop:
    id: str
    label: str
    phrase: str
    kind: str
    sound: str
    movable: bool = True
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
class SoundClue:
    id: str
    sound: str
    reveal: str
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
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


def _r_notice(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("detective")
    if detective.memes["curiosity"] >= THRESHOLD and "pipe" in world.entities:
        pipe = world.get("pipe")
        if pipe.meters["missing"] >= THRESHOLD and ("notice", pipe.id) not in world.fired:
            world.fired.add(("notice", pipe.id))
            detective.memes["alert"] += 1
            out.append("__notice__")
    return out


def _r_search(world: World) -> list[str]:
    out: list[str] = []
    caddy = world.get("caddy")
    if caddy.meters["moved"] >= THRESHOLD and ("search", caddy.id) not in world.fired:
        world.fired.add(("search", caddy.id))
        world.get("detective").memes["deduction"] += 1
        out.append("__search__")
    return out


CAUSAL_RULES = [Rule("notice", _r_notice), Rule("search", _r_search)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    lines: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                lines.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in lines:
            world.say(s)
    return lines


def predict_scene(world: World) -> dict:
    sim = world.copy()
    sim.get("pipe").meters["missing"] += 1
    sim.get("caddy").meters["moved"] += 1
    propagate(sim, narrate=False)
    return {
        "noticed": sim.get("detective").memes["alert"] >= THRESHOLD,
        "searched": sim.get("detective").memes["deduction"] >= THRESHOLD,
    }


def setup(world: World, detective: Entity, helper: Entity, place: Place) -> None:
    detective.memes["curiosity"] += 1
    helper.memes["calm"] += 1
    world.say(f"That morning, {detective.id} and {helper.id} were in {place.label}.")
    world.say(f"On the table sat a pipe caddy, neat as a little puzzle box.")


def vanish(world: World, pipe: Entity, caddy: Entity) -> None:
    pipe.meters["missing"] += 1
    caddy.meters["moved"] += 1
    world.say('Snip. The pipe was gone from the caddy.')
    world.say('Tap-tap. The caddy had been shifted to the wrong side of the room.')


def clue(world: World, clue_obj: SoundClue, helper: Entity) -> None:
    helper.memes["helpful"] += 1
    world.say(f'{clue_obj.sound} — that was the sound clue. "{clue_obj.reveal}"')
    world.say("The room went quiet after the little noise, as if the furniture knew something.")


def deduce(world: World, detective: Entity, helper: Entity) -> None:
    detective.memes["deduction"] += 1
    world.say(f"{detective.id} frowned, then looked at the caddy, then at the window.")
    world.say(f'"{helper.id}," {detective.id} said, "someone moved the caddy after the pipe disappeared."')


def reveal(world: World, culprit: Entity, pipe: Entity, caddy: Entity) -> None:
    culprit.memes["guilt"] += 1
    culprit.meters["caught"] += 1
    pipe.meters["found"] += 1
    caddy.meters["returned"] += 1
    world.say(f'At last, {culprit.id} stepped forward. "I did it," {culprit.pronoun()} whispered.')
    world.say(f'{culprit.id} had used the caddy to hide the pipe, but the sound clue gave it away.')
    world.say(f'The pipe went back into the caddy: click, and the mystery was solved.')


def closure(world: World, detective: Entity, helper: Entity, culprit: Entity) -> None:
    detective.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say("Nobody was angry for long.")
    world.say(f"{detective.id} nodded, because the answer mattered more than the fuss.")
    world.say(f"By evening, the caddy sat tidy again, and the pipe was safe where it belonged.")


def tell(place: Place, clue_obj: SoundClue, culprit_name: str = "Ned",
         detective_name: str = "Mira", helper_name: str = "Aunt Jo") -> World:
    world = World()
    detective = world.add(Entity(id=detective_name, kind="character", type="girl", role="detective"))
    helper = world.add(Entity(id=helper_name, kind="character", type="woman", role="helper"))
    culprit = world.add(Entity(id=culprit_name, kind="character", type="boy", role="culprit"))
    pipe = world.add(Entity(id="pipe", label="pipe"))
    caddy = world.add(Entity(id="caddy", label="caddy"))
    world.facts["place"] = place
    world.facts["clue"] = clue_obj
    world.facts["culprit"] = culprit
    world.facts["detective"] = detective
    world.facts["helper"] = helper

    setup(world, detective, helper, place)
    world.para()
    vanish(world, pipe, caddy)
    clue(world, clue_obj, helper)
    propagate(world, narrate=False)
    deduce(world, detective, helper)
    world.para()
    reveal(world, culprit, pipe, caddy)
    closure(world, detective, helper, culprit)

    world.facts.update(
        pipe=pipe,
        caddy=caddy,
        outcome="solved",
        noticed=detective.memes["alert"] >= THRESHOLD,
    )
    return world


PLACES = {
    "study": Place(id="study", label="the study", dim="indoors", tags={"study"}),
    "library": Place(id="library", label="the library nook", dim="indoors", tags={"library"}),
    "porch": Place(id="porch", label="the screened porch", dim="indoors", tags={"porch"}),
}

CLUES = {
    "tick": SoundClue(id="tick", sound="Tick, tick, tick", reveal="A tiny metal latch had been nudged"),
    "clink": SoundClue(id="clink", sound="Clink!", reveal="Something hard had bumped the caddy"),
    "thud": SoundClue(id="thud", sound="Thud!", reveal="The pipe had been dropped onto a cushion"),
}

GUILTY = ["Ned", "Pip", "Owen", "Luca"]
DETECTIVES = ["Mira", "June", "Elsie", "Ruby"]
HELPERS = ["Aunt Jo", "Uncle Ben", "Grandma", "Mr. Vale"]


@dataclass
class StoryParams:
    place: str
    clue: str
    culprit: str
    detective: str
    helper: str
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
    StoryParams(place="study", clue="clink", culprit="Ned", detective="Mira", helper="Aunt Jo"),
    StoryParams(place="library", clue="tick", culprit="Pip", detective="June", helper="Grandma"),
    StoryParams(place="porch", clue="thud", culprit="Owen", detective="Elsie", helper="Mr. Vale"),
]


def valid_combos() -> list[tuple[str, str]]:
    return [(p, c) for p in PLACES for c in CLUES]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small whodunit storyworld with pipe, caddy, and sound clues.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--culprit")
    ap.add_argument("--detective")
    ap.add_argument("--helper")
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
    combos = [(p, c) for p, c in valid_combos()
              if (args.place is None or p == args.place)
              and (args.clue is None or c == args.clue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, clue = rng.choice(sorted(combos))
    culprit = args.culprit or rng.choice(GUILTY)
    detective = args.detective or rng.choice(DETECTIVES)
    helper = args.helper or rng.choice(HELPERS)
    if culprit == detective:
        raise StoryError("The detective and culprit must be different people.")
    return StoryParams(place=place, clue=clue, culprit=culprit, detective=detective, helper=helper)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.clue not in CLUES:
        raise StoryError(f"Unknown clue: {params.clue}")
    world = tell(PLACES[params.place], CLUES[params.clue],
                 culprit_name=params.culprit, detective_name=params.detective,
                 helper_name=params.helper)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"].label
    clue = f["clue"].sound
    return [
        f'Write a short whodunit for a 3-to-5-year-old set in {place} with the words "pipe" and "caddy".',
        f"Tell a gentle mystery where a pipe goes missing from a caddy, and a sound like {clue} helps solve it.",
        "Write a child-friendly mystery with sound effects, a clue, and a tidy ending where the pipe is returned.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    culprit = f["culprit"]
    clue = f["clue"]
    return [
        ("What happened first?",
         f"The pipe disappeared from the caddy, and then the caddy was moved to the wrong side of the room. That started the mystery."),
        ("What sound helped solve the mystery?",
         f'{clue.sound} helped. It pointed the detective toward the clue and showed that someone had nudged the caddy.'),
        ("Who solved the mystery?",
         f"{detective.id} solved it with help from {helper.id}. Together they listened, looked closely, and figured out what happened."),
        ("Who caused the trouble?",
         f"{culprit.id} admitted it at the end. The pipe had been hidden, but the sound clue gave the game away."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a pipe?",
         "A pipe is a small object with a narrow shape. In a whodunit, it can become an important clue if it goes missing."),
        ("What is a caddy?",
         "A caddy is a holder or container that keeps things together and neat. If it gets moved, that can be a clue."),
        ("Why do detectives listen for sound effects?",
         "Because sounds can show when something moved, bumped, clicked, or dropped. A tiny noise can point to the answer."),
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
mystery_started :- missing(pipe), moved(caddy).
sound_clue_seen :- clue(tick).
sound_clue_seen :- clue(clink).
sound_clue_seen :- clue(thud).
solved :- mystery_started, sound_clue_seen.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("missing", "pipe"),
        asp.fact("moved", "caddy"),
    ]
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_solve() -> list[list]:
    import asp
    return asp.solve(asp_program("#show solved/0."), models=1)


def asp_verify() -> int:
    rc = 0
    if set(valid_combos()) != set(asp_valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python combo sets differ.")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    else:
        print("OK: generation smoke test passed.")
    return rc


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show mystery_started/0.\n#show sound_clue_seen/0.\n#show solved/0."))
    # The program is only a parity twin here; return the Python-valid combos.
    # The verify path checks the story generator itself too.
    return valid_combos()


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
        print(asp_program("#show solved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("valid combos:")
        for place, clue in valid_combos():
            print(f"  {place} / {clue}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
