#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/soul_dynamite_try_cautionary_ghost_story.py
===========================================================================

A small cautionary ghost-story world about a child, a rumor of a haunted mine,
and the dangerous idea of using dynamite to "try" to prove the ghost is fake.

The story engine models a few typed entities with physical meters and emotional
memes. The world supports a single careful outcome: a child is tempted to use
dynamite in a spooky place, a wiser helper warns them, and the story resolves
by choosing a safer way to listen, look, and leave the ghost alone.

The seed words are intentionally present in the domain:
- soul
- dynamite
- try

This is a cautionary ghost story: the lesson is not "be brave with explosives";
it is "don't test a scary place with something that can hurt people." The best
ending proves a change in state: the dangerous tool stays put, the haunted room
gets treated with respect, and the child leaves with a lantern instead.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
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
    dark: str
    mood: str
    haunted: bool = True
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
class Hazard:
    id: str
    label: str
    phrase: str
    where: str
    danger: int
    makes_boom: bool = True
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
class LightTool:
    id: str
    label: str
    phrase: str
    glow: str
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
class SaferChoice:
    id: str
    label: str
    text: str
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


def propagate(world: World) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    for s in out:
        world.say(s)
    return out


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["fear"] < THRESHOLD:
            continue
        sig = ("fear", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["shake"] += 1
        out.append("The dark felt even colder.")
    return out


CAUSAL_RULES = [Rule("fear", _r_fear)]


def haunted_risk(place: Place, hazard: Hazard) -> bool:
    return place.haunted and hazard.makes_boom and hazard.danger >= 2


def sensible_choices() -> list[SaferChoice]:
    return [c for c in SAFE_CHOICES.values()]


def outcome_of(params: "StoryParams") -> str:
    return "safe"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for hid, hazard in HAZARDS.items():
            for sid in SAFE_CHOICES:
                if haunted_risk(place, hazard):
                    combos.append((pid, hid, sid))
    return combos


def _choose_name(rng: random.Random) -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return name, gender


def preview_danger(world: World, place_id: str, hazard_id: str) -> dict:
    sim = world.copy()
    sim.get(place_id).meters["unease"] += 1
    sim.get("child").meters["fear"] += 1
    propagate(sim)
    return {
        "fear": sim.get("child").meters["fear"],
        "unease": sim.get(place_id).meters["unease"],
    }


def setup(world: World, child: Entity, helper: Entity, place: Place) -> None:
    child.memes["curiosity"] += 1
    helper.memes["care"] += 1
    world.say(
        f"One foggy evening, {child.id} and {helper.id} came to {place.label}, "
        f"where the windows looked like sleepy eyes."
    )
    world.say(
        f"{place.dark} made every hallway whisper, and the air had a cold, old smell."
    )


def rumor(world: World, child: Entity, place: Place) -> None:
    child.memes["bravado"] += 1
    world.say(
        f'"Maybe there is a soul trapped in here," {child.id} whispered. '
        f'"I want to try to prove it."'
    )
    world.say(
        f"{child.id} thought the darkness might hide a secret, but it also hid danger."
    )


def warn(world: World, helper: Entity, child: Entity, hazard: Hazard, place: Place) -> None:
    pred = preview_danger(world, place.id, hazard.id)
    helper.memes["warning"] += 1
    world.facts["preview"] = pred
    world.say(
        f'{helper.id} shook {helper.pronoun("possessive")} head. '
        f'"Do not use {hazard.label} here," {helper.id} said. '
        f'"This place is not for a test, and one boom can wake the whole mine."'
    )


def refuse(world: World, child: Entity, hazard: Hazard) -> None:
    child.memes["defiance"] += 1
    world.say(
        f"{child.id} opened {child.pronoun('possessive')} mouth to argue, then saw "
        f"how still the shadows were."
    )
    world.say(
        f'At last {child.id} said, "All right. I will not touch the {hazard.label}."'
    )


def safer_plan(world: World, helper: Entity, child: Entity, choice: SaferChoice) -> None:
    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"{helper.id} nodded and showed {child.id} {choice.text} instead."
    )
    world.say(
        f"The child held the light carefully, and the dark corners stayed quiet."
    )


def ending(world: World, child: Entity, place: Place, choice: SaferChoice) -> None:
    child.memes["peace"] += 1
    place.meters["calm"] += 1
    world.say(
        f"At the end, {child.id} walked away with {choice.label}, and the haunted "
        f"place kept its secret soul to itself."
    )
    world.say(
        f"The night remained spooky, but nobody was hurt, and the dynamite stayed where it belonged."
    )


def tell(place: Place, hazard: Hazard, choice: SaferChoice,
         child_name: str = "Mara", child_gender: str = "girl",
         helper_name: str = "Uncle Reed", helper_gender: str = "man") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    hall = world.add(Entity(id="hall", kind="place", type="place", label=place.label))
    tool = world.add(Entity(id="dynamite", kind="thing", type="tool", label=hazard.label))
    world.facts.update(place=place, hazard=hazard, choice=choice, child=child, helper=helper, tool=tool, hall=hall)

    setup(world, child, helper, place)
    world.para()
    rumor(world, child, place)
    warn(world, helper, child, hazard, place)
    refuse(world, child, hazard)
    world.para()
    safer_plan(world, helper, child, choice)
    ending(world, child, place, choice)
    world.get("hall").meters["calm"] += 1
    return world


@dataclass
class StoryParams:
    place: str
    hazard: str
    choice: str
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


PLACES = {
    "old_mine": Place(id="old_mine", label="the old mine", dark="The tunnel mouth was black as soot", mood="echoing"),
    "attic": Place(id="attic", label="the attic", dark="The rafters made long, nervous lines", mood="dusty"),
}

HAZARDS = {
    "dynamite": Hazard(id="dynamite", label="dynamite", phrase="a stick of dynamite", where="in a rusty box", danger=3, tags={"dynamite", "boom"}),
}

SAFE_CHOICES = {
    "lantern": SaferChoice(id="lantern", label="lantern", text="a small lantern that glowed warm and steady", tags={"light"}),
    "listen": SaferChoice(id="listen", label="listen", text="a quiet moment to listen for the wind and the echoes", tags={"listen"}),
}

GIRL_NAMES = ["Mara", "Ivy", "Lena", "Nell", "June"]
BOY_NAMES = ["Owen", "Finn", "Theo", "Rowan", "Eli"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a cautionary ghost story for a young child that includes the words "soul", "dynamite", and "try".',
        f"Tell a spooky story where {f['child'].id} wants to try dynamite in {f['place'].label}, but a wiser helper stops {f['child'].pronoun('object')}.",
        f"Write a ghost story with a safe ending: the scary place keeps its soul, the child backs away from dynamite, and the night feels calmer.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, place, hazard, choice = f["child"], f["helper"], f["place"], f["hazard"], f["choice"]
    preview = f.get("preview", {})
    return [
        QAItem(
            question="Why did the helper warn the child?",
            answer=(
                f"{helper.id} warned {child.id} because dynamite can make a violent boom, and that is dangerous in {place.label}. "
                f"The warning mattered because the dark place was already spooky and a blast could hurt people or wake something worse."
            ),
        ),
        QAItem(
            question="What did the child decide to do instead?",
            answer=(
                f"{child.id} decided not to touch the dynamite and chose {choice.text} instead. "
                f"That change turned the moment from a risky test into a careful retreat."
            ),
        ),
        QAItem(
            question="How did the story end?",
            answer=(
                f"It ended safely, with {child.id} leaving the haunted place and the dynamite staying put. "
                f"The night was still ghostly, but the danger was smaller because nobody tried to force a secret out of the dark."
            ),
        ),
        QAItem(
            question="What made the place feel scary?",
            answer=(
                f"The place felt scary because {place.dark.lower()}, and the echoes made every step sound lonely. "
                f"That kind of silence is exactly why dynamite would have been the wrong thing to try."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is dynamite?",
            answer="Dynamite is a powerful explosive. It can break rock, but it is very dangerous and only grown-ups with special training should handle it.",
        ),
        QAItem(
            question="Why is a ghost story scary?",
            answer="A ghost story is scary because it often has dark places, strange sounds, and the feeling that something unseen is nearby.",
        ),
        QAItem(
            question="What should you do if a place seems dangerous?",
            answer="Back away and get a grown-up right away. It is much safer to leave a dangerous place alone than to try something risky.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
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
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="old_mine", hazard="dynamite", choice="lantern", child_name="Mara", child_gender="girl", helper_name="Uncle Reed", helper_gender="man"),
    StoryParams(place="attic", hazard="dynamite", choice="listen", child_name="Owen", child_gender="boy", helper_name="Aunt June", helper_gender="woman"),
]


def explain_rejection() -> str:
    return "(No story: this world only allows a haunted place with a dangerous explosive and a safer choice.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cautionary ghost story world about soul, dynamite, and try.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--choice", choices=SAFE_CHOICES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["woman", "man"])
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
    if not combos:
        raise StoryError(explain_rejection())
    filtered = [c for c in combos if (args.place is None or c[0] == args.place)
                and (args.hazard is None or c[1] == args.hazard)
                and (args.choice is None or c[2] == args.choice)]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    place, hazard, choice = rng.choice(filtered)
    gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_gender = args.helper_gender or rng.choice(["woman", "man"])
    helper_name = args.helper_name or ("Aunt June" if helper_gender == "woman" else "Uncle Reed")
    return StoryParams(place=place, hazard=hazard, choice=choice, child_name=child_name, child_gender=gender, helper_name=helper_name, helper_gender=helper_gender)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.hazard not in HAZARDS or params.choice not in SAFE_CHOICES:
        raise StoryError("(Invalid params.)")
    world = tell(PLACES[params.place], HAZARDS[params.hazard], SAFE_CHOICES[params.choice],
                 child_name=params.child_name, child_gender=params.child_gender,
                 helper_name=params.helper_name, helper_gender=params.helper_gender)
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


ASP_RULES = r"""
place(old_mine). place(attic).
hazard(dynamite). makes_boom(dynamite). danger(dynamite,3).
choice(lantern). choice(listen).
valid(P,H,C) :- place(P), hazard(H), choice(C), makes_boom(H), danger(H,D), D >= 2.
#show valid/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for h in HAZARDS:
        lines.append(asp.fact("hazard", h))
        lines.append(asp.fact("makes_boom", h))
        lines.append(asp.fact("danger", h, HAZARDS[h].danger))
    for c in SAFE_CHOICES:
        lines.append(asp.fact("choice", c))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP matches Python valid_combos().")
    else:
        rc = 1
        print("MISMATCH: ASP/Python parity failed.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"MISMATCH: generate() failed: {exc}")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(" ".join(map(str, row)))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
