#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/tromp_assistance_suspense_dialogue_animal_story.py
==================================================================================

A small animal storyworld about a lost little animal, a tense search, spoken
reassurance, and timely assistance. The key words are "tromp" and "assistance";
the story shape leans into suspense and dialogue while staying child-facing.

The domain is deliberately tiny:
- a young animal gets separated from a parent or friend,
- sounds in the dark raise the suspense,
- a helper arrives and offers assistance,
- the group reunites and ends in a calm, concrete image.

The simulation tracks physical meters and emotional memes so prose is driven by
state rather than by a frozen paragraph with swapped nouns.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "fox": {"subject": "he", "object": "him", "possessive": "his"},
            "rabbit": {"subject": "she", "object": "her", "possessive": "her"},
            "hedgehog": {"subject": "they", "object": "them", "possessive": "their"},
            "owl": {"subject": "they", "object": "them", "possessive": "their"},
            "bear": {"subject": "he", "object": "him", "possessive": "his"},
            "parent": {"subject": "they", "object": "them", "possessive": "their"},
            "helper": {"subject": "they", "object": "them", "possessive": "their"},
        }
        return mapping.get(self.type, mapping["parent"])[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    dark: bool = False
    echoes: bool = False
    shelter: bool = False
    dust: str = "dust"
    path_name: str = "path"


@dataclass
class LostThing:
    id: str
    label: str
    kind_word: str
    where: str
    hidden_in: str
    can_hear: bool = True


@dataclass
class HelperPlan:
    id: str
    assistance: str
    action: str
    calm_text: str
    success_text: str
    fail_text: str
    power: int


@dataclass
class StoryParams:
    place: str
    lost_thing: str
    helper: str
    seeker: str
    seeker_type: str
    helper_type: str
    parent: str
    seed: Optional[int] = None


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
        clone.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label,
            "role": v.role, "attrs": dict(v.attrs), "meters": dict(v.meters),
            "memes": dict(v.memes)
        }) for k, v in self.entities.items()}
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_echo(world: World) -> list[str]:
    out = []
    for e in world.entities.values():
        if e.meters.get("tromp", 0.0) < THRESHOLD:
            continue
        sig = ("echo", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["worry"] = e.memes.get("worry", 0.0) + 1
        out.append("__echo__")
    return out


CAUSAL_RULES = [_r_echo]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)


def build_story(world: World, place: Place, lost: LostThing, helper: HelperPlan) -> None:
    seeker = world.get("seeker")
    parent = world.get("parent")
    helper_ent = world.get("helper")

    seeker.memes["love"] = seeker.memes.get("love", 0.0) + 1
    parent.memes["care"] = parent.memes.get("care", 0.0) + 1
    world.say(
        f"On a quiet afternoon, {seeker.id} and {parent.id} wandered into {place.label}. "
        f"The little path there was soft, and the trees made the sky look green."
    )
    world.say(
        f"{seeker.id} was looking for {lost.label}, but then the sound of a long "
        f"tromp came from behind the brush."
    )

    world.para()
    seeker.meters["tromp"] = 1.0
    propagate(world, narrate=False)
    seeker.memes["fear"] = seeker.memes.get("fear", 0.0) + 1
    world.say(f'"Did you hear that?" {seeker.id} whispered. "{parent.id}, are you there?"')
    world.say(f'"I am here," said {parent.id}, "but stay close. We do not want to be alone in the dark path."')

    world.para()
    helper_ent.memes["calm"] = helper_ent.memes.get("calm", 0.0) + 1
    world.say(
        f"Then {helper_ent.id} stepped out from the shelter with a small lantern. "
        f'"I heard the tromp too," {helper_ent.id} said. "I can help."'
    )
    world.say(f'"We need assistance," said {parent.id}. "{helper_ent.id}, please, can you look by {lost.where}?"')
    world.say(f'"Yes," said {helper_ent.id}, and {helper_ent.pronoun()} moved slowly so nobody would startle.')

    world.para()
    if helper.power >= 1:
        lost_spot = lost.hidden_in
        world.say(
            f"{helper_ent.id} peered near {lost_spot}, then lifted a leafy branch. "
            f"There was {lost.label}, tucked safely where the wind could not move it."
        )
        world.say(f'"Oh!" cried {seeker.id}. "{lost.label_word if False else lost.label}!"')
        world.say(f'"I found it," said {helper_ent.id}, "and now I will walk with you back."')
        seeker.memes["relief"] = seeker.memes.get("relief", 0.0) + 1
        parent.memes["relief"] = parent.memes.get("relief", 0.0) + 1
        world.say(
            f"The three of them tromped home together, but now the sound felt friendly. "
            f"{seeker.id} held {lost.label} close, and {parent.id} kept the lantern near."
        )
    else:
        seeker.memes["worry"] = seeker.memes.get("worry", 0.0) + 1
        world.say(
            f"{helper_ent.id} looked and looked, but the little thing stayed hidden. "
            f"The dark path felt bigger, and everyone had to wait for more help."
        )
        world.say(
            f'"{helper.assistance} would be better with a brighter lantern," said {parent.id}. '
            f'"Let us call again."'
        )

    world.facts.update(
        seeker=seeker,
        helper=helper_ent,
        parent=parent,
        place=place,
        lost=lost,
        plan=helper,
        found=helper.power >= 1,
    )


PLACES = {
    "woods": Place("woods", "the woods", dark=True, echoes=True, shelter=True, dust="leaf dust", path_name="path"),
    "garden": Place("garden", "the garden", dark=True, echoes=False, shelter=False, dust="soil", path_name="trail"),
    "barn": Place("barn", "the barn", dark=True, echoes=True, shelter=True, dust="hay dust", path_name="lane"),
}

LOST_THINGS = {
    "bluebell": LostThing("bluebell", "a bluebell ribbon", "ribbon", "the willow tree", "a thorny bush"),
    "shell": LostThing("shell", "a shiny shell", "shell", "the fence post", "a pile of leaves"),
    "acorn": LostThing("acorn", "a tiny acorn toy", "toy", "the old stump", "a mossy log"),
}

HELPERS = {
    "mole": HelperPlan("mole", "assistance", "tromp", "softly", "found the lost thing quickly", "could not find it", 1),
    "otter": HelperPlan("otter", "assistance", "tromp", "kindly", "found the lost thing quickly", "could not find it", 1),
    "badger": HelperPlan("badger", "assistance", "tromp", "carefully", "found the lost thing quickly", "could not find it", 1),
}


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, l, h) for p in PLACES for l in LOST_THINGS for h in HELPERS]


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
        if PLACES[p].dark:
            lines.append(asp.fact("dark", p))
    for l in LOST_THINGS:
        lines.append(asp.fact("lost", l))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
        lines.append(asp.fact("assists", h, "assistance"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,L,H) :- place(P), lost(L), helper(H).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = set(asp_valid_combos()) == set(valid_combos())
    if ok:
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH: ASP and Python differ.")
        return 1
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, lost_thing=None, helper=None, seeker=None, seeker_type=None, helper_type=None, parent=None), random.Random(1)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal suspense storyworld with tromp and assistance.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--lost-thing", choices=LOST_THINGS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--seeker")
    ap.add_argument("--seeker-type", choices=["fox", "rabbit", "hedgehog", "owl", "bear"])
    ap.add_argument("--helper-type", choices=["fox", "rabbit", "hedgehog", "owl", "bear"])
    ap.add_argument("--parent")
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
    place = args.place or rng.choice(list(PLACES))
    lost = args.lost_thing or rng.choice(list(LOST_THINGS))
    helper = args.helper or rng.choice(list(HELPERS))
    seeker = args.seeker or rng.choice(["Pip", "Milo", "Mina", "Toby", "Luna"])
    seeker_type = args.seeker_type or rng.choice(["fox", "rabbit", "hedgehog", "owl", "bear"])
    helper_type = args.helper_type or rng.choice(["mole", "otter", "badger", "owl"])
    parent = args.parent or rng.choice(["Mama", "Papa", "Auntie", "Uncle"])
    if place not in PLACES or lost not in LOST_THINGS or helper not in HELPERS:
        raise StoryError("Invalid choices for this storyworld.")
    return StoryParams(place=place, lost_thing=lost, helper=helper, seeker=seeker,
                       seeker_type=seeker_type, helper_type=helper_type, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = World()
    seeker = world.add(Entity(id=params.seeker, kind="character", type=params.seeker_type, role="seeker"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_type, role="helper"))
    parent = world.add(Entity(id=params.parent, kind="character", type="parent", role="parent"))
    build_story(world, PLACES[params.place], LOST_THINGS[params.lost_thing], HELPERS[params.helper])
    story = world.render()
    prompts = [
        f'Write a suspenseful animal story including the words "tromp" and "assistance".',
        f"Tell a child-friendly animal story where {params.seeker} gets nervous in {PLACES[params.place].label} and a helper offers assistance.",
        f"Write a dialogue-heavy animal story that ends with a safe reunion and the word tromp."
    ]
    story_qa = [
        QAItem(
            question=f"What made {params.seeker} feel nervous?",
            answer=f"{params.seeker} heard a tromp in the dark place and worried someone or something was nearby. The sound made the path feel bigger until {params.helper} arrived with assistance."
        ),
        QAItem(
            question=f"How did the helper help?",
            answer=f"{params.helper} looked near the hiding spot, found the lost item, and walked back with the others. That assistance turned the scary search into a safe trip home."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with everyone together and calm. {params.seeker} carried the lost thing home while the lantern glowed and the tromp became a friendly walking sound."
        ),
    ]
    world_qa = [
        QAItem(question="What is assistance?", answer="Assistance means helping someone with a task or a problem. In this story it is the careful help that makes the search safe."),
        QAItem(question="What does a tromp sound like?", answer="A tromp is a heavy, thumping step. It can sound scary in the dark, which is why the animals listened closely."),
        QAItem(question="Why is a lantern useful at night?", answer="A lantern gives a steady light without making the dark feel so big. It helps friends see where they are going.")
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        out.append(f"  {e.id}: type={e.type} role={e.role} meters={e.meters} memes={e.memes}")
    out.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(out)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for section, items in (("prompts", sample.prompts),):
            pass
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


CURATED = [
    StoryParams(place="woods", lost_thing="bluebell", helper="mole", seeker="Pip", seeker_type="rabbit", helper_type="mole", parent="Mama"),
    StoryParams(place="barn", lost_thing="shell", helper="badger", seeker="Milo", seeker_type="fox", helper_type="badger", parent="Papa"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = [generate(p) for p in CURATED] if args.all else []
    if not samples:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
