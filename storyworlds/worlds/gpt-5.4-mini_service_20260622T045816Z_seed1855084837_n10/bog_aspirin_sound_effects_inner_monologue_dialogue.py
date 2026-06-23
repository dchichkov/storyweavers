#!/usr/bin/env python3
"""
storyworlds/worlds/bog_aspirin_sound_effects_inner_monologue_dialogue.py
========================================================================

A small fairy-tale storyworld about a bog, a headache, and a tiny cure plan.
The world keeps typed entities with physical meters and emotional memes, uses
state-driven causal updates, and supports dialogue, inner monologue, and sound
effects in the rendered prose.

Seed tale:
---
A little miller named Wren crossed a misty bog and found an old willow whose
roots made her head throb. A kindly frog told her that a calm cup of tea was
best, but Wren found a tiny aspirin in her satchel. "Plink!" said the spoon,
and Wren thought, "I hope this will help." She asked the bog witch for water,
took the aspirin with a sip, and soon the ache faded. The willow whispered,
the frogs croaked, and Wren walked home smiling through the reeds.

This storyworld keeps that premise but varies the names, place details, and the
sequence of caution, choice, relief, and ending image.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

# Make results.py importable when run directly from arbitrary working dirs.
_HERE = os.path.abspath(__file__)
_CUR = os.path.dirname(_HERE)
while True:
    if os.path.exists(os.path.join(_CUR, "results.py")):
        if _CUR not in sys.path:
            sys.path.insert(0, _CUR)
        break
    parent = os.path.dirname(_CUR)
    if parent == _CUR:
        break
    _CUR = parent

from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
STYLES = ("fairy_tale",)
FEATURES = ("sound_effects", "inner_monologue", "dialogue")


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "witch"}
        male = {"boy", "man", "father", "frog", "miller"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    kind: str
    misty: bool = False
    has_water: bool = False
    has_witch: bool = False
    has_herbs: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Ailment:
    id: str
    label: str
    symptom: str
    remedy: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Caution:
    id: str
    label: str
    advice: str
    reply: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.history: list[str] = []
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.history.append(text)

    def render(self) -> str:
        return " ".join(self.history)

    def copy(self) -> "World":
        w = World(self.place)
        w.entities = {k: Entity(
            id=v.id, kind=v.kind, type=v.type, label=v.label, phrase=v.phrase,
            role=v.role, attrs=dict(v.attrs), owner=v.owner, plural=v.plural,
            meters=defaultdict(float, v.meters), memes=defaultdict(float, v.memes),
        ) for k, v in self.entities.items()}
        w.facts = dict(self.facts)
        w.history = list(self.history)
        w.fired = set(self.fired)
        return w


@dataclass
class StoryParams:
    place: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    ailment: str
    caution: str
    seed: Optional[int] = None


PLACES = {
    "bog": Place(id="bog", label="the bog", kind="bog", misty=True, has_water=True, has_witch=True, has_herbs=True, tags={"bog", "mist"}),
    "brook": Place(id="brook", label="the brook", kind="brook", misty=False, has_water=True, has_witch=False, has_herbs=True, tags={"water"}),
    "cottage_garden": Place(id="cottage_garden", label="the cottage garden", kind="garden", misty=False, has_water=True, has_witch=False, has_herbs=True, tags={"garden"}),
}

AILMENTS = {
    "headache": Ailment(id="headache", label="headache", symptom="her head throbbed", remedy="the ache faded", risk="taking the aspirin without water", tags={"ache", "aspirin"}),
}

CAUTIONS = {
    "frog": Caution(id="frog", label="frog", advice="a calm cup of tea was best", reply="Use a gentle drink and rest first", tags={"frog", "tea"}),
    "witch": Caution(id="witch", label="witch", advice="sip some water before you swallow anything", reply="Take it with water, dear child", tags={"witch", "water"}),
}

NAMES_GIRL = ["Wren", "Mira", "Anya", "Elsie", "Pippa"]
NAMES_BOY = ["Robin", "Toby", "Perrin", "Owen", "Milo"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in PLACES:
        for ail in AILMENTS:
            for caution in CAUTIONS:
                combos.append((place, ail, caution, "aspirin"))
    return combos


def explain_rejection(params: StoryParams) -> str:
    return "(No story: this little world needs a place, a headache, a warning, and aspirin.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld: bog, aspirin, sound effects, inner monologue, and dialogue.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=["girl", "boy", "frog", "witch"])
    ap.add_argument("--ailment", choices=AILMENTS)
    ap.add_argument("--caution", choices=CAUTIONS)
    ap.add_argument("-n", "--n", type=int, default=1)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.ailment is None or c[1] == args.ailment)
              and (args.caution is None or c[2] == args.caution)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, ailment, caution, _ = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(["frog", "witch"])
    hero = args.hero or rng.choice(NAMES_GIRL if hero_type == "girl" else NAMES_BOY)
    helper = args.helper or rng.choice(["Puddle", "Willow", "Moss", "Bran"])
    return StoryParams(place=place, hero=hero, hero_type=hero_type, helper=helper, helper_type=helper_type, ailment=ailment, caution=caution)


def _hero_noun(hero: Entity) -> str:
    return f"little {hero.type} {hero.id}"


def tell(place: Place, hero_name: str, hero_type: str, helper_name: str, helper_type: str, ailment: Ailment, caution: Caution) -> World:
    w = World(place)
    hero = w.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name, role="hero"))
    helper = w.add(Entity(id=helper_name, kind="character", type=helper_type, label=helper_name, role="helper"))
    bog = w.add(Entity(id="bog", kind="thing", type="bog", label="the bog"))
    aspirin = w.add(Entity(id="aspirin", kind="thing", type="aspirin", label="aspirin", phrase="a tiny aspirin", owner=hero.id))
    water = w.add(Entity(id="water", kind="thing", type="water", label="water"))
    bog.meters["mist"] += 1
    hero.memes["worry"] += 1
    w.facts.update(place=place, hero=hero, helper=helper, bog=bog, aspirin=aspirin, water=water, ailment=ailment, caution=caution, took=False, helped=False)

    w.say(f"Once upon a time, {hero.label} wandered into {place.label}.")
    w.say(f"The reeds whispered around the bog, and {hero.label} felt {ailment.symptom}.")
    w.say(f'"{caution.reply}," said {helper.label}.')
    w.say(f'{hero.label} looked down at the satchel. "I have aspirin," {hero.label} thought, "and I hope it will help."')
    w.say("Plink! went the spoon against the cup.")
    helper.memes["caution"] += 1
    hero.meters["ache"] += 1
    if place.has_water:
        w.say(f'"May I have water?" asked {hero.label}.')
        hero.meters["sip"] += 1
        aspirin.meters["taken"] += 1
        hero.memes["hope"] += 1
        w.say(f"With a small sip, {hero.label} took the aspirin.")
        hero.meters["ache"] = 0
        hero.memes["relief"] += 1
        w.say(f"Before long, {ailment.remedy}.")
        w.say(f"The frogs croaked, the willow swayed, and {hero.label} smiled through the reeds.")
        w.facts["took"] = True
        w.facts["helped"] = True
    else:
        w.say(f"{hero.label} could not take the aspirin safely there, so {helper.label} led the way home.")
        hero.memes["hope"] += 1
        w.say(f"At the cottage, water was found, and only then did {hero.label} swallow the little tablet.")
        hero.meters["ache"] = 0
        hero.memes["relief"] += 1
        w.say(f"By sunset, {ailment.remedy}, and the bog looked kind instead of grim.")
        w.facts["took"] = True
        w.facts["helped"] = True
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fairy-tale story that includes the words "bog" and "aspirin" and uses dialogue, sound effects, and inner monologue.',
        f"Tell a gentle story about {f['hero'].label} in {f['place'].label} who has an {f['ailment'].label} and wonders whether aspirin will help.",
        f'Write a child-friendly fairy tale where a helper in {f["place"].label} gives advice, the main character thinks aloud, and the ending turns from worry to relief.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    ailment: Ailment = f["ailment"]
    place: Place = f["place"]
    caution: Caution = f["caution"]
    qa = [
        QAItem(question=f"Where did {hero.id} walk in the story?", answer=f"{hero.id} walked into {place.label}, where the bog mist hung low and the reeds whispered. That was the place where the trouble and the cure both happened."),
        QAItem(question=f"What was wrong with {hero.id} before the aspirin helped?", answer=f"{hero.id} had a {ailment.label}, so {hero.pronoun('possessive')} head throbbed. The aspirin was meant to ease that ache."),
        QAItem(question=f"What did {helper.id} say before {hero.id} took the aspirin?", answer=f"{helper.id} gave a gentle warning: {caution.reply}. It mattered because the child needed to think carefully before swallowing anything."),
    ]
    if f.get("took"):
        qa.append(QAItem(question=f"How did {hero.id} finally take the aspirin?", answer=f"{hero.id} asked for water, then took the aspirin with a small sip. That safe choice let the medicine do its work and brought relief soon after."))
    if f.get("helped"):
        qa.append(QAItem(question=f"How did the ending prove that things changed for {hero.id}?", answer=f"At the end, the ache was gone and {hero.id} smiled through the reeds. The bog was still there, but it no longer felt frightening because the pain had faded."))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a bog?", answer="A bog is a wet, muddy place with soft ground, water, and plants like reeds or moss. It can feel misty and mysterious like a fairy-tale setting."),
        QAItem(question="What is aspirin?", answer="Aspirin is medicine that grown-ups use to help with pain or fever. It should be taken only the safe way, usually with guidance and water."),
        QAItem(question="What does a sound effect do in a story?", answer="A sound effect shows a noise in a lively way, like plink or croak. It helps the reader hear the moment in their mind."),
        QAItem(question="What is inner monologue?", answer="Inner monologue is the quiet thought a character has in their own head. It lets the reader know what the character is hoping or worrying about."),
        QAItem(question="What is dialogue?", answer="Dialogue is when characters speak to each other. It makes a story feel active and lets you hear the voices directly."),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
taken(aspirin) :- took_medicine.
relief :- taken(aspirin).
valid(place,bog,aspirin) :- place(bog), medicine(aspirin), has_water(bog).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("place", "bog"),
        asp.fact("place", "brook"),
        asp.fact("place", "cottage_garden"),
        asp.fact("medicine", "aspirin"),
        asp.fact("has_water", "bog"),
        asp.fact("has_water", "brook"),
        asp.fact("has_water", "cottage_garden"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    ok = py == asp_set
    if ok:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
    else:
        print("MISMATCH:")
        if py - asp_set:
            print("  only in python:", sorted(py - asp_set))
        if asp_set - py:
            print("  only in clingo:", sorted(asp_set - py))
        return 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        if not sample.story:
            raise RuntimeError("empty story")
        print("OK: generate smoke test produced a story.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return 0


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.ailment not in AILMENTS or params.caution not in CAUTIONS:
        raise StoryError(explain_rejection(params))
    place = PLACES[params.place]
    if params.helper_type not in {"frog", "witch", "girl", "boy"}:
        raise StoryError("(No story: unsupported helper type.)")
    world = tell(place, params.hero, params.hero_type, params.helper, params.helper_type, AILMENTS[params.ailment], CAUTIONS[params.caution])
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


CURATED = [
    StoryParams(place="bog", hero="Wren", hero_type="girl", helper="Fenn", helper_type="frog", ailment="headache", caution="frog"),
    StoryParams(place="brook", hero="Robin", hero_type="boy", helper="Moss", helper_type="witch", ailment="headache", caution="witch"),
    StoryParams(place="cottage_garden", hero="Mira", hero_type="girl", helper="Bran", helper_type="frog", ailment="headache", caution="frog"),
]


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
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
