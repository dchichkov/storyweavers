#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/slick_pole_rural_repetition_conflict_detective_story.py
======================================================================================

A tiny detective-style storyworld built from the seed words:
slick, pole, rural.

Premise:
- A careful detective investigates a repeated disturbance in a rural place.
- A slick pole creates a conflict: it causes slips, blocks a sign, or hides a clue.
- Repetition matters: the same problem keeps happening until the detective
  notices the pattern and solves it.

The world is small, classical, and state-driven: entities carry physical meters
and emotional memes, and the story is rendered from a simulated sequence of
events rather than by swapping nouns into a frozen paragraph.

Run:
    python storyworlds/worlds/gpt-5.4-mini/slick_pole_rural_repetition_conflict_detective_story.py
    python storyworlds/worlds/gpt-5.4-mini/slick_pole_rural_repetition_conflict_detective_story.py --verify
    python storyworlds/worlds/gpt-5.4-mini/slick_pole_rural_repetition_conflict_detective_story.py --qa --json
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
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
class Setting:
    id: str
    place: str
    detail: str
    repetition_spot: str
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
class Clue:
    id: str
    label: str
    sign: str
    tells: str
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
class SlickThing:
    id: str
    label: str
    phrase: str
    danger: str
    fix: str
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Response:
    id: str
    sense: int
    text: str
    fail: str
    qa_text: str
    power: int
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
        clone.facts = copy.deepcopy(self.facts)
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


def _r_repeat(world: World) -> list[str]:
    out: list[str] = []
    for clue in list(world.entities.values()):
        if clue.role != "clue" or clue.meters["noticed"] < THRESHOLD:
            continue
        sig = ("repeat", clue.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("detective").memes["focus"] += 1
        out.append("__repeat__")
    return out


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    pole = world.entities.get("pole")
    if not pole or pole.meters["slick"] < THRESHOLD:
        return out
    if world.get("detective").memes["frustration"] < THRESHOLD:
        return out
    sig = ("conflict", "pole")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("detective").memes["frustration"] += 1
    world.get("helper").memes["worry"] += 1
    out.append("__conflict__")
    return out


CAUSAL_RULES = [Rule("repeat", _r_repeat), Rule("conflict", _r_conflict)]


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


def reasonable_combo(setting: Setting, slick: SlickThing, clue: Clue, response: Response) -> bool:
    return setting.id == "rural" and slick.id in {"slick_pole", "slick_pole_sign"} and clue.id in {"road_sign", "barn_note"} and response.sense >= 2


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for tid, thing in SLICK_THINGS.items():
            for cid, clue in CLUES.items():
                for rid, resp in RESPONSES.items():
                    if setting.id == "rural" and thing.id.startswith("slick_pole") and resp.sense >= 2:
                        combos.append((sid, tid, cid, rid))
    return combos


def predict_solved(world: World, response: Response) -> bool:
    sim = world.copy()
    sim.get("clue").meters["noticed"] += 1
    sim.get("detective").memes["frustration"] += 1
    return response.power >= 2


def scene_open(world: World, detective: Entity, helper: Entity, setting: Setting) -> None:
    detective.memes["curiosity"] += 1
    helper.memes["trust"] += 1
    world.say(
        f"In the rural place, {detective.id} and {helper.id} walked past quiet fields and a narrow lane. "
        f"{setting.detail}"
    )


def repeat_beats(world: World, clue: Entity, setting: Setting) -> None:
    world.say(
        f"Again and again, the same thing kept happening near the old pole by {setting.repetition_spot}. "
        f"Each time, the clue seemed a little more important."
    )
    clue.meters["noticed"] += 1
    clue.memes["mystery"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{clue.label_word.capitalize()} was there before, and then there again, as if the place wanted to be seen twice."
    )


def conflict_scene(world: World, detective: Entity, pole: Entity, clue: Entity) -> None:
    detective.memes["frustration"] += 1
    pole.meters["slick"] += 1
    world.say(
        f"The pole was slick with rain, so slick that even a careful step slipped a little. "
        f"{detective.id} frowned, because the slick pole blocked the clue and made the case harder."
    )
    world.say(
        f'"This is the same trouble," {detective.id} said. "Same pole. Same slick shine. Same hidden clue."'
    )


def investigate(world: World, detective: Entity, clue: Entity) -> None:
    detective.meters["search"] += 1
    world.say(
        f"{detective.id} bent down, looked again, and checked the ground twice. "
        f"The repeated marks finally pointed to {clue.label_word}."
    )


def solve(world: World, helper: Entity, response: Response, pole: Entity, clue: Entity) -> None:
    pole.meters["slick"] = 0
    pole.meters["fixed"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"{helper.id} brought a dry cloth and a bit of grit. In a little while, the {response.id} was done, and the pole was no longer slick."
    )
    world.say(
        f"{response.text}. The clue could be read at last, and the mystery stopped repeating."
    )


def ending(world: World, detective: Entity, helper: Entity, clue: Entity) -> None:
    detective.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"At the end, {detective.id} pinned the note in the file and smiled. "
        f"The rural lane was calm again, the pole was dry, and the clue made sense."
    )


def tell(setting: Setting, slick: SlickThing, clue: Clue, response: Response) -> World:
    world = World()
    detective = world.add(Entity(id="Detective June", kind="character", type="woman", role="detective"))
    helper = world.add(Entity(id="Milo", kind="character", type="boy", role="helper"))
    place = world.add(Entity(id=setting.id, type="place", label=setting.place))
    pole = world.add(Entity(id="pole", type="thing", label="pole"))
    clue_ent = world.add(Entity(id="clue", type="thing", label=clue.label, role="clue"))
    slick_ent = world.add(Entity(id=slick.id, type="thing", label=slick.label))
    detective.memes["focus"] = 1
    helper.memes["trust"] = 1
    slick_ent.meters["slick"] = 1

    scene_open(world, detective, helper, setting)
    world.para()
    repeat_beats(world, clue_ent, setting)
    conflict_scene(world, detective, pole, clue_ent)
    world.para()
    investigate(world, detective, clue_ent)
    if predict_solved(world, response):
        solve(world, helper, response, pole, clue_ent)
        ending(world, detective, helper, clue_ent)
        outcome = "solved"
    else:
        world.say(f"{response.fail}. The pole stayed slick, and the clue stayed hidden.")
        outcome = "stalled"

    world.facts.update(
        detective=detective, helper=helper, setting=setting, slick=slick, clue=clue,
        response=response, pole=pole, outcome=outcome
    )
    return world


SETTINGS = {
    "rural": Setting(id="rural", place="a rural lane", detail="A small shed leaned by the road, and a fence split the fields.", repetition_spot="the mailbox"),
}

SLICK_THINGS = {
    "slick_pole": SlickThing(id="slick_pole", label="slick pole", phrase="a slick pole", danger="slips", fix="dry it"),
    "slick_pole_sign": SlickThing(id="slick_pole_sign", label="slick pole", phrase="a slick pole by the sign", danger="slips", fix="dry it"),
}

CLUES = {
    "road_sign": Clue(id="road_sign", label="road sign", sign="sign", tells="which way to go"),
    "barn_note": Clue(id="barn_note", label="barn note", sign="note", tells="who left the message"),
}

RESPONSES = {
    "dry_cloth": Response(id="dry cloth", sense=3, text="They dried the pole and wiped off the slippery shine", fail="The cloth was too small to help", qa_text="dried the pole and wiped off the slippery shine", power=3),
    "grit": Response(id="grit", sense=2, text="They sprinkled grit on the pole and made it safe to touch", fail="The grit slipped away before it could help", qa_text="sprinkled grit on the pole and made it safe to touch", power=2),
    "shout": Response(id="shout", sense=1, text="They shouted at the pole, but that did not change anything", fail="Shouting did nothing at all", qa_text="shouted at the pole", power=1),
}

CURATED = [
    StoryParams = None
]

@dataclass
class StoryParams:
    setting: str
    slick: str
    clue: str
    response: str
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
        'Write a detective story for a young child that includes the words "slick", "pole", and "rural".',
        f"Tell a small mystery where {f['detective'].id} keeps seeing the same clue near a slick pole in a rural place, until the pattern is solved.",
        f"Write a repetition-and-conflict story where a slick pole causes the same trouble twice before the detective fixes it.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    clue = f["clue"]
    response = f["response"]
    items = [
        QAItem(
            question="Who solved the mystery?",
            answer=f"{detective.id} solved it by noticing the repeated pattern and checking the clue again."
        ),
        QAItem(
            question="Why was there conflict in the story?",
            answer=f"The pole was slick, so it kept causing trouble and hiding the clue. That made the case harder until someone dried it off."
        ),
        QAItem(
            question="What did the helper do?",
            answer=f"{helper.id} helped by bringing a dry cloth and getting the pole safe again. That let the clue be read at last."
        ),
        QAItem(
            question="What changed at the end?",
            answer="The pole was no longer slick, the clue was no longer hidden, and the repeated trouble stopped."
        ),
    ]
    if f["outcome"] == "solved":
        items.append(QAItem(
            question="How did the detective know what to do?",
            answer=f"{detective.id} noticed the same sign of trouble twice, then matched it to the slick pole and used {response.id} to fix it."
        ))
    return items


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does slick mean?", answer="Slick means smooth and slippery, so it is easy to slide on."),
        QAItem(question="What is a pole?", answer="A pole is a long upright stick or post."),
        QAItem(question="What is a rural place?", answer="A rural place is out in the countryside, with fields, lanes, and fewer houses."),
        QAItem(question="What is repetition?", answer="Repetition means something happens again and again."),
        QAItem(question="What is conflict in a story?", answer="Conflict is the trouble or problem that the characters have to deal with."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
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
        out.append(f"  {e.id}: {' '.join(bits)}")
    return "\n".join(out)


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "rural")]
    lines.append(asp.fact("repeatable", "clue"))
    lines.append(asp.fact("slick", "pole"))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, X, C, R) :- setting(S), slick(X), repeatable(C), response(R), sense(R, N), N >= 2.
solve(R) :- response(R), power(R, P), P >= 2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = True
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP and Python combo gates match.")
    else:
        ok = False
        print("MISMATCH: combo gate differs.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, slick=None, clue=None, response=None, seed=None), random.Random(0)))
        _ = sample.story
        print("OK: generate smoke test succeeded.")
    except Exception as ex:
        ok = False
        print(f"SMOKE TEST FAILED: {ex}")
    return 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective storyworld with slick poles and repetition.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--slick", choices=SLICK_THINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--response", choices=RESPONSES)
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


@dataclass
class StoryParams:
    setting: str
    slick: str
    clue: str
    response: str
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or "rural"
    slick = args.slick or rng.choice(list(SLICK_THINGS))
    clue = args.clue or rng.choice(list(CLUES))
    response = args.response or rng.choice([k for k, v in RESPONSES.items() if v.sense >= 2])
    if setting != "rural":
        raise StoryError("This tiny world only tells rural detective stories.")
    if response not in RESPONSES or RESPONSES[response].sense < 2:
        raise StoryError("That response is too weak for a detective solution.")
    return StoryParams(setting=setting, slick=slick, clue=clue, response=response)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.slick not in SLICK_THINGS or params.clue not in CLUES or params.response not in RESPONSES:
        raise StoryError("Invalid story parameters.")
    world = tell(SETTINGS[params.setting], SLICK_THINGS[params.slick], CLUES[params.clue], RESPONSES[params.response])
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        params_list = [
            StoryParams(setting="rural", slick="slick_pole", clue="road_sign", response="dry_cloth"),
            StoryParams(setting="rural", slick="slick_pole_sign", clue="barn_note", response="grit"),
        ]
        samples = [generate(p) for p in params_list]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
    for idx, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {idx+1}" if len(samples) > 1 else ""))
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
