#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/even_cup_ful_contemplate_lesson_learned_myth.py
================================================================================

A small myth-flavored storyworld about a child, a sacred cup-ful, and a lesson
learned.  The domain is intentionally tiny: a young helper brings water to a dry
field, pauses to contemplate the old warning, makes the wrong choice, and then a
wise elder shows a better way.  The story must use the seed words even,
cup-ful, and contemplate, and it should feel like a compact myth with a clear
lesson learned.

The world model tracks:
- physical meters: thirst, dryness, spill, bloom, and loss
- emotional memes: wonder, worry, pride, shame, and wisdom

The mythic shape:
1. A child is sent to bring a cup-ful of sacred water.
2. They contemplate a promise but choose the boastful shortcut.
3. The spill brings trouble to a dry place.
4. An elder responds with calm practical wisdom.
5. The ending proves the lesson learned by showing a new, safer ritual.

The generated stories are not event logs; they are state-driven, child-facing
myths with a concrete beginning, middle turn, and ending image.
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
WISE_TRAITS = {"wise", "patient", "gentle", "careful"}
BRASH_TRAITS = {"proud", "impatient", "reckless", "bold"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "father", "man", "king"}
        female = {"girl", "mother", "woman", "queen"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"father": "father", "mother": "mother", "elder": "elder"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Myth:
    id: str
    place: str
    dry_phrase: str
    promise: str
    ritual: str
    ending_image: str

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
class Vessel:
    id: str
    label: str
    phrase: str
    fulness: str
    spill_word: str
    is_sacred: bool = True

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

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

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


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    vessel = world.get("vessel")
    if vessel.meters["spill"] >= THRESHOLD and ("spill",) not in world.fired:
        world.fired.add(("spill",))
        world.get("field").meters["dryness"] += 1
        world.get("field").memes["worry"] += 1
        world.get("child").memes["shame"] += 1
        out.append("__spill__")
    return out


def _r_bloom(world: World) -> list[str]:
    out: list[str] = []
    field = world.get("field")
    if field.meters["bloom"] >= THRESHOLD and ("bloom",) not in world.fired:
        world.fired.add(("bloom",))
        world.get("child").memes["wonder"] += 1
        out.append("__bloom__")
    return out


CAUSAL_RULES = [Rule("spill", "physical", _r_spill), Rule("bloom", "physical", _r_bloom)]


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


def contemplate_truth(world: World, child: Entity, elder: Entity, myth: Myth) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"{child.id} stood by the old well and did what the elders taught: "
        f"{child.pronoun()} would contemplate before taking even a single step."
    )
    world.say(
        f"The wind brushed the stones, and the dry {myth.place} waited under a pale sky."
    )


def tempt(world: World, child: Entity, vessel: Vessel, myth: Myth) -> None:
    child.memes["pride"] += 1
    world.say(
        f'"I can carry the {vessel.fulness} {vessel.label} all by myself," {child.id} said, '
        f"though {child.pronoun()} remembered the old warning."
    )
    world.say(
        f"{child.id} did contemplate the promise for a heartbeat, but pride was louder "
        f"than patience."
    )


def take_shortcut(world: World, child: Entity, vessel: Vessel) -> None:
    child.memes["defiance"] += 1
    vessel.meters["spill"] += 1
    world.say(
        f"{child.id} hurried faster than was wise, and the {vessel.spill_word} splashed "
        f"over the rim of the cup-ful."
    )
    propagate(world, narrate=False)


def warn_and_guide(world: World, elder: Entity, child: Entity, vessel: Vessel, myth: Myth) -> None:
    elder.memes["wisdom"] += 1
    world.say(
        f'{elder.id} lifted a calm hand. "A true keeper does not waste sacred water," '
        f'{elder.pronoun()} said. "Carry it slowly, or fill the basin again."'
    )
    world.say(
        f"Then {elder.id} pointed to the thirsty roots waiting beside {myth.place}."
    )


def repair(world: World, elder: Entity, child: Entity, myth: Myth, response: Response) -> None:
    field = world.get("field")
    field.meters["dryness"] = max(0.0, field.meters["dryness"] - 1)
    field.meters["bloom"] += 1
    child.memes["shame"] = max(0.0, child.memes["shame"] - 1)
    child.memes["wisdom"] += 1
    body = response.text
    world.say(
        f"Together they {body}, and the little stream found the roots at last."
    )
    world.say(
        f"The field answered at once: a green shoot rose where there had been only dust."
    )


def lesson(world: World, elder: Entity, child: Entity, myth: Myth) -> None:
    child.memes["lesson"] += 1
    world.say(
        f"{elder.id} smiled, and {child.id} bowed {child.pronoun('possessive')} head. "
        f'"The lesson is plain," {elder.pronoun()} said. "Even a cup-ful matters, '
        f"and the hands that carry it must move with care."
    )
    world.say(
        f"{child.id} remembered that saying as if it had always lived inside the stones."
    )
    world.say(
        f"From then on, {child.id} would pause to contemplate before touching the water."
    )


def ending(world: World, child: Entity, elder: Entity, myth: Myth) -> None:
    world.say(
        f"By sunset, the {myth.place} was not dry anymore. "
        f"{myth.ending_image.capitalize()}"
    )


MYTHS = {
    "spring": Myth("spring", "valley spring", "the valley spring was nearly dry", "carry water without waste", "walk slowly and pour at the roots", "new leaves trembled in the gold light"),
    "orchard": Myth("orchard", "orchard", "the orchard had thirsty trees", "carry water without waste", "walk slowly and pour at the roots", "the first blossoms opened like small stars"),
    "garden": Myth("garden", "stone garden", "the stone garden was cracked with heat", "carry water without waste", "walk slowly and pour at the roots", "green shoots curled up between the stones"),
}

VESSELS = {
    "cup": Vessel("cup", "cup", "a cup", "cup-ful", "water"),
    "bowl": Vessel("bowl", "bowl", "a bowl", "bowl-ful", "water"),
    "goblet": Vessel("goblet", "goblet", "a goblet", "goblet-ful", "water"),
}

RESPONSES = {
    "pour_slowly": Response("pour_slowly", 3, 3, "poured the water slowly and let every drop find the roots", "poured too fast and lost the water in the dust", "poured the water slowly"),
    "carry_again": Response("carry_again", 3, 2, "returned to the well and carried a second load with steady steps", "returned too late and the roots stayed dry", "carried a second load with steady steps"),
    "shared_hands": Response("shared_hands", 3, 4, "joined both hands around the vessel and brought it safely to the roots", "held it alone and let it slip", "joined both hands around the vessel"),
}

GIRL_NAMES = ["Ari", "Mina", "Lila", "Nia", "Sera", "Tala"]
BOY_NAMES = ["Ivo", "Niko", "Rian", "Kian", "Aren", "Milo"]


@dataclass
@dataclass
class StoryParams:
    myth: str
    vessel: str
    response: str
    child: str
    gender: str
    elder: str
    elder_gender: str
    trait: str
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
    return [(m, v, r) for m in MYTHS for v in VESSELS for r in RESPONSES]


def reasonableness_ok(params: StoryParams) -> bool:
    return params.vessel in VESSELS and params.response in RESPONSES and params.myth in MYTHS


def explain_rejection() -> str:
    return "(No story: the myth needs a vessel, a response, and a dry place that can learn the lesson.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic lesson-learned storyworld with even, cup-ful, and contemplate.")
    ap.add_argument("--myth", choices=MYTHS)
    ap.add_argument("--vessel", choices=VESSELS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-gender", choices=["woman", "man"])
    ap.add_argument("--trait", choices=sorted(WISE_TRAITS | BRASH_TRAITS))
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
    if args.response and args.response not in RESPONSES:
        raise StoryError(explain_rejection())
    myth = args.myth or rng.choice(list(MYTHS))
    vessel = args.vessel or rng.choice(list(VESSELS))
    response = args.response or rng.choice(list(RESPONSES))
    gender = args.gender or rng.choice(["girl", "boy"])
    child = args.name or _pick_name(rng, gender)
    elder_gender = args.elder_gender or rng.choice(["woman", "man"])
    elder = args.elder or ("Mara" if elder_gender == "woman" else "Orin")
    trait = args.trait or rng.choice(sorted(WISE_TRAITS | BRASH_TRAITS))
    return StoryParams(myth, vessel, response, child, gender, elder, elder_gender, trait)


def tell(params: StoryParams) -> World:
    world = World()
    myth = MYTHS[params.myth]
    vessel = VESSELS[params.vessel]
    response = RESPONSES[params.response]
    child = world.add(Entity(id=params.child, kind="character", type=params.gender, role="child", traits=[params.trait]))
    elder_type = "mother" if params.elder_gender == "woman" else "father"
    elder = world.add(Entity(id=params.elder, kind="character", type=elder_type, role="elder", traits=["wise"]))
    field = world.add(Entity(id="field", kind="thing", type="field", label=myth.place))
    vessel_ent = world.add(Entity(id="vessel", kind="thing", type="vessel", label=vessel.label))
    child.memes["wonder"] = 1
    field.meters["dryness"] = 2
    world.say(
        f"Long ago, when the {myth.place} still waited for rain, {child.id} went to the well with a {vessel.fulness} {vessel.label}."
    )
    contemplate_truth(world, child, elder, myth)
    world.para()
    tempt(world, child, vessel, myth)
    take_shortcut(world, child, vessel)
    world.para()
    warn_and_guide(world, elder, child, vessel, myth)
    repair(world, elder, child, myth, response)
    lesson(world, elder, child, myth)
    world.para()
    ending(world, child, elder, myth)
    world.facts.update(child=child, elder=elder, myth=myth, vessel=vessel, response=response)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    myth: Myth = f["myth"]
    vessel: Vessel = f["vessel"]
    return [
        f'Write a myth-like story that includes the words "even", "{vessel.fulness}", and "contemplate".',
        f"Tell a small lesson-learned myth about a child carrying {vessel.phrase} to {myth.place}.",
        f"Write a gentle myth where someone must contemplate before using a {vessel.label}, and the ending teaches a clear lesson.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    elder: Entity = f["elder"]
    myth: Myth = f["myth"]
    vessel: Vessel = f["vessel"]
    response: Response = f["response"]
    return [
        QAItem(
            question="What was the child carrying?",
            answer=f"{child.id} was carrying {vessel.phrase}, which is a small sacred amount of water. The story says even a cup-ful mattered because the dry place needed every drop."
        ),
        QAItem(
            question="Why did the child need to contemplate?",
            answer=f"{child.id} needed to contemplate because the water was precious and the dry {myth.place} depended on it. The pause mattered, because rushing would spill what the field needed most."
        ),
        QAItem(
            question="How did the elder fix the problem?",
            answer=f"{elder.id} asked them to use {response.qa_text} and then pour the water again with care. That kept the lesson gentle and helped the thirsty place recover."
        ),
        QAItem(
            question="What lesson did the child learn?",
            answer=f"{child.id} learned that even a cup-ful should be treated with care, and that thinking first helps keep promises. By the end, the child remembered to contemplate before acting."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does cup-ful mean?",
            answer="Cup-ful means the amount that fits in one cup. It is a small measure, which is why the story treats it as precious."
        ),
        QAItem(
            question="Why do people contemplate before acting?",
            answer="People contemplate to think carefully before they choose. That can stop a mistake and help them do the right thing."
        ),
        QAItem(
            question="What is a lesson learned?",
            answer="A lesson learned is something a character understands after a mistake or a wise warning. It changes how they act next time."
        ),
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
    lines = ["--- world trace ---"]
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
        lines.append(f"  {e.id}: {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("spring", "cup", "pour_slowly", "Ari", "girl", "Mara", "woman", "wise"),
    StoryParams("orchard", "bowl", "carry_again", "Ivo", "boy", "Orin", "man", "bold"),
    StoryParams("garden", "goblet", "shared_hands", "Nia", "girl", "Mara", "woman", "patient"),
]


ASP_RULES = r"""
valid(M,V,R) :- myth(M), vessel(V), response(R).
lesson_learned(C) :- child(C), contemplation(C), wisdom(C).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for m in MYTHS:
        lines.append(asp.fact("myth", m))
    for v in VESSELS:
        lines.append(asp.fact("vessel", v))
    for r in RESPONSES:
        lines.append(asp.fact("response", r))
    lines.append(asp.fact("child", "child"))
    lines.append(asp.fact("contemplation", "child"))
    lines.append(asp.fact("wisdom", "child"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as exc:
        print(f"MISMATCH: smoke test failed: {exc}")
        rc = 1
    else:
        print("OK: smoke test passed.")
    return rc


def generate(params: StoryParams) -> StorySample:
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for t in asp_valid_combos():
            print(t)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
