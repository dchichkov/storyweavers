#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/circulate_neutral_friendship_moral_value_teamwork_whodunit.py
=============================================================================================

A small whodunit storyworld about a missing item, a calm clue trail, and
friends who work together to find the truth without jumping to blame.

Seed words: circulate, neutral
Features: Friendship, Moral Value, Teamwork
Style: Whodunit
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    has_clue_surface: bool = False
    calm: bool = True
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Suspect:
    id: str
    label: str
    good_reason: str
    clue: str
    could_be: bool = True
    honest: bool = True
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class StoryParams:
    place: str
    missing: str
    culprit: str
    helper1: str
    helper2: str
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
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.place: Optional[Place] = None
        self.suspects: dict[str, Suspect] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
        clone.place = copy.deepcopy(self.place)
        clone.suspects = copy.deepcopy(self.suspects)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
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


def _r_clue_heat(world: World) -> list[str]:
    out: list[str] = []
    for s in world.suspects.values():
        if s.meters["suspicion"] < THRESHOLD:
            continue
        sig = ("heat", s.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if world.place:
            world.place.memes["unease"] += 1
        out.append("")
    return out


CAUSAL_RULES = [Rule("clue_heat", _r_clue_heat)]


def propagate(world: World) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            if rule.apply(world):
                changed = True


def sense_reasonable(missing: str, culprit: str) -> bool:
    return missing != culprit


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for miss in MISSING_ITEMS:
            for cul in SUSPECTS:
                if sense_reasonable(miss, cul):
                    combos.append((place, miss, cul))
    return combos


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for mid in MISSING_ITEMS:
        lines.append(asp.fact("missing", mid))
    for sid in SUSPECTS:
        lines.append(asp.fact("suspect", sid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,M,S) :- place(P), missing(M), suspect(S), M != S.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def setup(world: World, params: StoryParams) -> None:
    world.place = Place(id=params.place, label=PLACES[params.place]["label"],
                        has_clue_surface=True, calm=True)
    world.say(
        f"At {world.place.label}, something small and important had gone missing."
    )
    world.say(
        f"The whole room stayed neutral and quiet, as if it knew the truth would have to circulate before it could be found."
    )


def introduce(world: World, params: StoryParams) -> None:
    h1 = world.add(Entity(id=params.helper1, kind="character", type="girl",
                          role="helper", traits=["kind", "careful"]))
    h2 = world.add(Entity(id=params.helper2, kind="character", type="boy",
                          role="helper", traits=["steady", "thoughtful"]))
    cul = world.add(Entity(id=params.culprit, kind="character", type="girl",
                           role="culprit", traits=["nervous"]))
    world.suspects = {
        h1.id: Suspect(h1.id, h1.id, "She helped by looking carefully", "She noticed a clue"),
        h2.id: Suspect(h2.id, h2.id, "He helped by checking the quiet corner", "He noticed a second clue"),
        cul.id: Suspect(cul.id, cul.id, "She had taken it by mistake", "She had hidden it nearby"),
    }
    world.say(
        f"{h1.id} and {h2.id} decided to solve the mystery together."
    )


def circulate_clue(world: World) -> None:
    world.say(
        "They did not accuse anyone right away. Instead, they let the clues circulate from table to shelf to pocket, one calm step at a time."
    )


def gather(world: World, params: StoryParams) -> None:
    world.para()
    world.say(
        f"{params.helper1} found a tiny mark by the window, and {params.helper2} found the same mark on a chair."
    )
    world.say(
        f"That made the case feel less spooky and more like a puzzle."
    )


def reveal(world: World, params: StoryParams) -> None:
    cul = params.culprit
    world.para()
    world.say(
        f"At last, {params.helper1} noticed {cul} hiding {MISSING_ITEMS[params.missing]['label']} behind a book."
    )
    world.say(
        f"{cul} looked down and admitted the mistake. {MISSING_ITEMS[params.missing]['why']}."
    )
    world.say(
        "The friends stayed kind, and the clue trail turned into an honest answer."
    )


def resolve(world: World, params: StoryParams) -> None:
    world.para()
    world.say(
        f"Together they put everything back where it belonged, and the room felt peaceful again."
    )
    world.say(
        f"{params.helper1} and {params.helper2} smiled, because teamwork had solved what blame would only have made worse."
    )


def tell(params: StoryParams) -> World:
    world = World()
    setup(world, params)
    introduce(world, params)
    circulate_clue(world)
    gather(world, params)
    reveal(world, params)
    resolve(world, params)
    world.facts.update(
        place=params.place,
        missing=params.missing,
        culprit=params.culprit,
        helper1=params.helper1,
        helper2=params.helper2,
        outcome="solved",
    )
    return world


PLACES = {
    "classroom": {"label": "the classroom"},
    "clubhouse": {"label": "the clubhouse"},
    "library": {"label": "the library nook"},
}

MISSING_ITEMS = {
    "glove": {"label": "the blue glove", "why": "It had slipped off during the game"},
    "bookmark": {"label": "the red bookmark", "why": "It had been tucked into the wrong book"},
    "badge": {"label": "the shiny badge", "why": "It had fallen off the bulletin board"},
}

SUSPECTS = {
    "Mira": {"label": "Mira"},
    "Noah": {"label": "Noah"},
    "Sana": {"label": "Sana"},
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly whodunit in which something goes missing at {PLACES[f["place"]]["label"]} and the word "neutral" appears.',
        f"Tell a mystery story where {f['helper1']} and {f['helper2']} work together to find {MISSING_ITEMS[f['missing']]['label']} without unfair blame.",
        f'Write a friendship-and-teamwork mystery that uses the word "circulate" and ends with an honest apology.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    missing = MISSING_ITEMS[f["missing"]]["label"]
    return [
        QAItem(question="What kind of story is this?", answer="It is a calm whodunit about a missing thing, friendly clues, and a truthful ending."),
        QAItem(question=f"What went missing?", answer=f"{missing} went missing, and that made everyone curious."),
        QAItem(question="How did the friends solve it?", answer=f"They worked together, let the clues circulate, and found the hidden item without blaming anyone too quickly."),
        QAItem(question="What lesson did the story teach?", answer="It taught that honesty and teamwork are better than gossip or blame."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does circulate mean?", answer="Circulate means to move around from person to person or place to place."),
        QAItem(question="What does neutral mean?", answer="Neutral means calm and not taking sides."),
        QAItem(question="Why is teamwork helpful?", answer="Teamwork is helpful because people can notice different clues and solve hard problems together."),
        QAItem(question="Why is friendship important in a mystery?", answer="Friendship helps people stay kind and trust each other while they look for the truth."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    if world.place:
        lines.append(f"place={world.place.label}")
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: memes={dict(e.memes)} meters={dict(e.meters)} role={e.role}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="classroom", missing="glove", culprit="Sana", helper1="Mira", helper2="Noah"),
    StoryParams(place="clubhouse", missing="bookmark", culprit="Mira", helper1="Noah", helper2="Sana"),
    StoryParams(place="library", missing="badge", culprit="Noah", helper1="Mira", helper2="Sana"),
]


def explain_rejection() -> str:
    return "(No story: this combination does not make a fair whodunit.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny whodunit storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--missing", choices=MISSING_ITEMS)
    ap.add_argument("--culprit", choices=SUSPECTS)
    ap.add_argument("--helper1", choices=SUSPECTS)
    ap.add_argument("--helper2", choices=SUSPECTS)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.missing is None or c[1] == args.missing)
              and (args.culprit is None or c[2] == args.culprit)]
    if not combos:
        raise StoryError(explain_rejection())
    place, missing, culprit = rng.choice(sorted(combos))
    helpers = [s for s in SUSPECTS if s != culprit]
    helper1 = args.helper1 or rng.choice(sorted(helpers))
    helper2_choices = [s for s in helpers if s != helper1]
    helper2 = args.helper2 or rng.choice(sorted(helper2_choices))
    return StoryParams(place=place, missing=missing, culprit=culprit, helper1=helper1, helper2=helper2)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.missing not in MISSING_ITEMS or params.culprit not in SUSPECTS:
        raise StoryError("Invalid params.")
    if params.helper1 == params.culprit or params.helper2 == params.culprit or params.helper1 == params.helper2:
        raise StoryError("Helpers must be distinct from the culprit and each other.")
    world = tell(params)
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


def asp_verify() -> int:
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP matches Python.")
        return 0
    print("MISMATCH: ASP and Python differ.")
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        rc = asp_verify()
        try:
            sample = generate(CURATED[0])
            _ = sample.story
            print("OK: generation smoke test passed.")
        except Exception as exc:
            print(f"SMOKE TEST FAILED: {exc}")
            rc = 1
        sys.exit(rc)
    if args.asp:
        print(asp_program("#show valid/3."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
            s = generate(params)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {idx+1}" if len(samples) > 1 else "")
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
