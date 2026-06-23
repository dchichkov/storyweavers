#!/usr/bin/env python3
"""
storyworlds/worlds/bronze_twist_curiosity_flashback_comedy.py
==============================================================

A small comedy storyworld about a curious child, a bronze object, a twisty
mistake, and a flashback that helps fix it.

Premise:
- A child sees a bronze jar, lock, or music-box-like object in a cozy place.
- Curiosity makes them twist the wrong part.
- The twist causes a silly spill or clatter.
- A flashback reminds them of the proper way to use it.
- The ending proves the change: the bronze thing is put right, and the room is calm.

This file follows the Storyweavers contract:
- self-contained stdlib script
- imports storyworlds/results eagerly
- imports storyworlds/asp lazily inside ASP helpers
- defines StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports --verify, --asp, --show-asp, --json, --qa, --trace, --all, -n, --seed
- includes a Python reasonableness gate plus an inline ASP twin
- uses typed entities with meters and memes
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
    phrase: str = ""
    role: str = ""
    owner: str = ""
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.attrs.get("plural") == "yes" else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.label or self.type)


@dataclass
class Place:
    id: str
    label: str
    cozy_detail: str
    afford: set[str] = field(default_factory=set)


@dataclass
class BronzeThing:
    id: str
    label: str
    phrase: str
    use: str
    twist_part: str
    spill: str
    fix: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    thing: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    parent_gender: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.history: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.history.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [list(p) for p in self.paragraphs]
        clone.facts = copy.deepcopy(self.facts)
        clone.history = list(self.history)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    thing = world.entities.get("thing")
    if child is None or thing is None:
        return out
    if child.memes["curiosity"] < THRESHOLD or child.meters["twisted"] < THRESHOLD:
        return out
    sig = ("spill",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    thing.meters["scattered"] += 1
    child.meters["mess"] += 1
    out.append(f"The {thing.label} burst open, and tiny bits bounced everywhere.")
    return out


CAUSAL_RULES = [Rule("spill", "physical", _r_spill)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def setup_valid(place: Place, thing: BronzeThing) -> bool:
    return thing.id in place.afford


def select_fix(place: Place, thing: BronzeThing) -> bool:
    return thing.id in place.afford


PLACES = {
    "kitchen": Place(id="kitchen", label="the kitchen", cozy_detail="the table was warm from a loaf of bread", afford={"jar", "box"}),
    "attic": Place(id="attic", label="the attic", cozy_detail="the rafters were dusty and the old trunk sat like a sleepy giant", afford={"box", "lantern"}),
    "study": Place(id="study", label="the study", cozy_detail="the lamp made the desk glow like honey", afford={"musicbox", "jar"}),
}

THINGS = {
    "jar": BronzeThing(
        id="jar",
        label="bronze jar",
        phrase="a little bronze jar with a twist lid",
        use="hold buttons and beads",
        twist_part="lid",
        spill="buttons and beads scattered on the floor",
        fix="twist the lid back on until it clicked",
        tags={"bronze", "twist", "curiosity"},
    ),
    "box": BronzeThing(
        id="box",
        label="bronze box",
        phrase="a bronze box with a twist latch",
        use="keep crayons and stickers",
        twist_part="latch",
        spill="crayons rolled under the chair",
        fix="line up the latch and give it one careful twist",
        tags={"bronze", "twist", "curiosity", "flashback"},
    ),
    "musicbox": BronzeThing(
        id="musicbox",
        label="bronze music box",
        phrase="a small bronze music box with a twist key",
        use="play a tune",
        twist_part="key",
        spill="a tiny tune started up all by itself",
        fix="twist the key only a little, then stop",
        tags={"bronze", "twist", "curiosity", "flashback"},
    ),
}

CHILD_NAMES = ["Mia", "Noah", "Lily", "Finn", "Ava", "Theo"]
HELPER_NAMES = ["Pip", "June", "Kai", "Zoe", "Ben", "Mila"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for tid, thing in THINGS.items():
            if setup_valid(place, thing):
                combos.append((pid, tid))
    return combos


def explain_rejection(place: Place, thing: BronzeThing) -> str:
    return (
        f"(No story: {thing.label} doesn't fit the cozy setup in {place.label}. "
        f"Pick one that belongs there, so the curious twist can matter.)"
    )


def initial_flashback_text(thing: BronzeThing) -> str:
    if thing.id == "musicbox":
        return "A flashback flashed through the child's head: Grandma had once said, 'Only a tiny twist, then stop.'"
    if thing.id == "box":
        return "A flashback popped up: the helper had seen a grown-up line up the latch before turning it."
    return "A flashback nudged them: the lid should turn snugly, not wildly."


def predict_spill(world: World, child: Entity, thing: Entity) -> bool:
    sim = world.copy()
    sim.get("child").meters["twisted"] += 1
    sim.get("child").memes["curiosity"] += 1
    propagate(sim, narrate=False)
    return sim.get("thing").meters["scattered"] >= THRESHOLD


def tell(place: Place, thing_def: BronzeThing, child_name: str, child_gender: str,
         helper_name: str, helper_gender: str, parent_gender: str) -> World:
    world = World(place)
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name))
    helper = world.add(Entity(id="helper", kind="character", type=helper_gender, label=helper_name))
    parent = world.add(Entity(id="parent", kind="character", type=parent_gender, label="the parent"))
    thing = world.add(Entity(id="thing", type="thing", label=thing_def.label, phrase=thing_def.phrase, tags=set(thing_def.tags)))
    child.memes["curiosity"] = 0.0
    child.meters["twisted"] = 0.0
    child.meters["mess"] = 0.0
    thing.meters["scattered"] = 0.0
    world.facts.update(place=place, thing_def=thing_def, child=child, helper=helper, parent=parent, thing=thing)

    world.say(f"{child_name} and {helper_name} were in {place.label}. {place.cozy_detail}.")
    world.say(f"On the table sat {thing_def.phrase}. It looked serious, like it knew a secret and was trying not to grin.")
    world.para()
    child.memes["curiosity"] += 1
    world.say(f"{child_name} leaned closer. Curiosity made {child.pronoun('possessive')} nose wiggle. \"I just want to see what it does,\" {child.pronoun()} said.")
    world.say(f"{child_name} gave the {thing_def.twist_part} one twist.")
    if predict_spill(world, child, thing):
        world.say(initial_flashback_text(thing_def))
        helper.memes["memory"] += 1
        world.say(f"{helper_name} remembered the trick from before and said, \"No big spin! Just a careful turn.\"")
    propagate(world)
    world.para()
    if thing.meters["scattered"] >= THRESHOLD:
        thing.meters["fixed"] += 1
        world.say(f"So they laughed, picked up every last piece, and put {thing_def.label} back together.")
        world.say(f"This time {child_name} turned {thing_def.twist_part} just right. Click. The {thing_def.label} stayed neat, and nobody had to chase crumbs, beads, or trouble.")
    else:
        world.say(f"The careful twist worked at once, and {thing_def.label} stayed tidy. The room felt pleased with itself, as if it had won a tiny argument against chaos.")

    world.facts.update(resolved=thing.meters["fixed"] >= THRESHOLD or thing.meters["scattered"] < THRESHOLD)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place: Place = f["place"]  # type: ignore[assignment]
    thing: BronzeThing = f["thing_def"]  # type: ignore[assignment]
    return [
        f'Write a short comedy story for a 3-to-5-year-old about a curious child in {place.label} and a {thing.label}. Include the word "bronze".',
        f"Tell a gentle funny story where a child's curiosity leads them to twist a {thing.label}, and a flashback helps them do it the right way.",
        f'Write a story with a twist, a flashback, and a happy ending where "{thing.label}" stays safe and shiny.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    place: Place = f["place"]  # type: ignore[assignment]
    thing: BronzeThing = f["thing_def"]  # type: ignore[assignment]
    child: Entity = f["child"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    qa = [
        QAItem(
            question=f"Where was {child.label} when the bronze thing became interesting?",
            answer=f"{child.label} was in {place.label}, where the room felt cozy and ready for a silly little mistake. That is where the bronze {thing.label.split()[-1]} sat waiting on the table.",
        ),
        QAItem(
            question=f"Why did {child.label} want to touch the {thing.label}?",
            answer=f"{child.label} was curious and wanted to see what the {thing.label} would do. Curiosity made the child reach first and think second, which is exactly how small comedy trouble begins.",
        ),
        QAItem(
            question=f"What did the flashback help {helper.label} remember?",
            answer=f"It helped {helper.label} remember the careful way to use the {thing.label}: a small twist, not a wild one. That memory kept the story funny instead of messy.",
        ),
    ]
    if f.get("resolved"):
        qa.append(
            QAItem(
                question=f"How did the story end after the twist with the bronze {thing.label.split()[-1]}?",
                answer=f"The child fixed the mistake, and the {thing.label} stayed neat and usable. The ending image proves the change: everyone is smiling, and the bronze thing is back where it belongs.",
            )
        )
    if world.get("thing").meters["scattered"] >= THRESHOLD:
        qa.append(
            QAItem(
                question=f"What happened when the {thing.label} was twisted too far?",
                answer=f"It burst open and its little bits scattered across the floor. The spill was silly rather than scary, but it still needed cleaning up.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    thing: BronzeThing = f["thing_def"]  # type: ignore[assignment]
    tags = set(thing.tags)
    out: list[QAItem] = []
    if "bronze" in tags:
        out.append(QAItem("What is bronze?", "Bronze is a metal. It is often brownish-gold and can be made into shiny objects like jars, bells, and boxes."))
    if "twist" in tags:
        out.append(QAItem("What does it mean to twist something?", "To twist something is to turn it around a little with your hand. A careful twist can open a lid or move a latch."))
    if "flashback" in tags:
        out.append(QAItem("What is a flashback in a story?", "A flashback is a quick memory of something that happened before. It helps explain why a character knows what to do now."))
    if "curiosity" in tags:
        out.append(QAItem("What is curiosity?", "Curiosity is the feeling that makes you want to look, ask, and learn more. It can lead to discoveries, and sometimes to funny trouble."))
    return out


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
    lines.append("== (3) World knowledge ==")
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
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  history items: {len(world.history)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, T) :- place(P), thing(T), affords(P, T).
spill :- curiosity, twisted.
resolved :- not spill.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for tid in sorted(place.afford):
            lines.append(asp.fact("affords", pid, tid))
    for tid, thing in THINGS.items():
        lines.append(asp.fact("thing", tid))
        if "bronze" in thing.tags:
            lines.append(asp.fact("bronze", tid))
        if "twist" in thing.tags:
            lines.append(asp.fact("twist", tid))
        if "curiosity" in thing.tags:
            lines.append(asp.fact("curiosity", tid))
        if "flashback" in thing.tags:
            lines.append(asp.fact("flashback", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("MISMATCH between Python and ASP valid-combo gates.")
        if cl - py:
            print(" only in clingo:", sorted(cl - py))
        if py - cl:
            print(" only in python:", sorted(py - cl))
        return 1
    print(f"OK: ASP matches valid_combos() for {len(py)} combos.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: bronze curiosity, a twist, a flashback, and a comic fix.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--thing", choices=THINGS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--parent-gender", choices=["mother", "father"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.thing is None or c[1] == args.thing)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place_id, thing_id = rng.choice(sorted(combos))
    place = PLACES[place_id]
    thing = THINGS[thing_id]
    child_gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    parent_gender = args.parent_gender or rng.choice(["mother", "father"])
    child_name = args.name or rng.choice(CHILD_NAMES)
    helper_name = args.helper or rng.choice(HELPER_NAMES)
    if helper_name == child_name:
        helper_name = rng.choice([n for n in HELPER_NAMES if n != child_name])
    return StoryParams(
        place=place_id,
        thing=thing_id,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        parent_gender=parent_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.thing not in THINGS:
        raise StoryError(f"Unknown thing: {params.thing}")
    place = PLACES[params.place]
    thing = THINGS[params.thing]
    if not setup_valid(place, thing):
        raise StoryError(explain_rejection(place, thing))
    world = tell(place, thing, params.child_name, params.child_gender, params.helper_name, params.helper_gender, params.parent_gender)
    story = world.render()
    if not story.strip():
        raise StoryError("Generated an empty story.")
    return StorySample(
        params=params,
        story=story,
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


def _smoke_test(sample: StorySample) -> None:
    if not sample.story.strip():
        raise StoryError("Smoke test failed: empty story.")
    if not sample.prompts or not sample.story_qa or not sample.world_qa:
        raise StoryError("Smoke test failed: missing QA/prompts.")


def asp_all_combos_small() -> bool:
    return len(valid_combos()) <= 12


def asp_show_program() -> str:
    return asp_program("#show valid/2.")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_show_program())
        return
    if args.verify:
        rc = asp_verify()
        if rc != 0:
            sys.exit(rc)
        # real smoke tests
        default_args = build_parser().parse_args([])
        for seed in (3, 7, 11):
            params = resolve_params(default_args, random.Random(seed))
            sample = generate(params)
            _smoke_test(sample)
        sample = generate(resolve_params(build_parser().parse_args(["--seed", "777"]), random.Random(777)))
        _smoke_test(sample)
        if len(generate(resolve_params(build_parser().parse_args(["--seed", "777"]), random.Random(777))).story) == 0:
            sys.exit(1)
        # n=3 qa smoke
        samples = []
        for i in range(3):
            p = resolve_params(build_parser().parse_args(["--seed", "777"]), random.Random(777 + i))
            samples.append(generate(p))
        if len({s.story for s in samples}) != len(samples):
            # not fatal, but our verify wants diversity when it can get it
            pass
        qa_sample = generate(resolve_params(build_parser().parse_args(["-n", "3", "--seed", "777", "--qa"]), random.Random(777)))
        _smoke_test(qa_sample)
        if args.json or True:
            json.loads(generate(resolve_params(build_parser().parse_args(["--seed", "777"]), random.Random(777))).to_json())
        if asp_all_combos_small():
            _ = asp_valid_combos()
        print("OK: verify smoke tests passed.")
        return

    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, thing) combos:\n")
        for place, thing in combos:
            print(f"  {place:10} {thing}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(place=p, thing=t, child_name="Mia", child_gender="girl", helper_name="Pip", helper_gender="boy", parent_gender="mother")) for p, t in valid_combos()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.place} / {p.thing}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
