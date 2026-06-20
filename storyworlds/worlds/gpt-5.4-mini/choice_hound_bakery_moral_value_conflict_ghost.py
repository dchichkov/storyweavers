#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/choice_hound_bakery_moral_value_conflict_ghost.py
==================================================================================

A standalone storyworld for a tiny ghost-story bakery domain.

Premise:
- A child in a bakery faces a choice about a pastry.
- A pale hound-ghost appears and stirs up a conflict.
- The child must choose between selfishness and kindness.
- A small moral value is earned through a concrete action.
- The ending proves what changed in the bakery.

The world is built as a lightweight simulation with physical meters and emotional
memes. The story is driven by world state, not by swapping nouns in a frozen text.
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
    haunting: bool = False
    edible: bool = False
    bakery_item: bool = False
    can_share: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "mom"}
        male = {"boy", "father", "man", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Bakery:
    id: str
    place: str
    scent: str
    quiet_detail: str
    eerie_detail: str
    ending_image: str


@dataclass
class Choice:
    id: str
    label: str
    act: str
    consequence: str
    moral: int
    sense: int
    tags: set[str] = field(default_factory=set)


@dataclass
class ConflictBeat:
    id: str
    label: str
    pressure: str
    height: int
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    hound = world.entities.get("hound")
    if not child or not hound:
        return out
    if child.memes["conflict"] < THRESHOLD:
        return out
    sig = ("conflict", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["fear"] += 1
    hound.memes["restless"] += 1
    out.append("__conflict__")
    return out


def _r_moral(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    baker = world.entities.get("baker")
    if not child or not baker:
        return out
    if child.memes["kindness"] < THRESHOLD:
        return out
    sig = ("moral", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    baker.memes["warmth"] += 1
    out.append("__moral__")
    return out


CAUSAL_RULES = [Rule("conflict", "social", _r_conflict), Rule("moral", "social", _r_moral)]


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


def predict_choice(world: World, choice_id: str) -> dict:
    sim = world.copy()
    _make_choice(sim, sim.get("child"), CHOICES[choice_id], narrate=False)
    return {
        "conflict": sim.get("child").memes["conflict"],
        "moral": sim.get("child").memes["kindness"],
        "warmth": sim.get("baker").memes["warmth"],
    }


def _make_choice(world: World, child: Entity, choice: Choice, narrate: bool = True) -> None:
    child.meters["choice_made"] += 1
    child.memes["choice_pull"] += 1
    if choice.id == "share":
        child.memes["kindness"] += 1
    else:
        child.memes["greed"] += 1
        child.memes["conflict"] += 1
    propagate(world, narrate=narrate)


def opening(world: World, bak: Bakery, child: Entity, hound: Entity, baker: Entity) -> None:
    world.say(
        f"Late one evening, {child.id} stood in {bak.place}, where {bak.scent} "
        f"drifted through the air and {bak.quiet_detail}."
    )
    world.say(
        f"Near the glass case, {hound.id} waited like a ghost with bright eyes, "
        f"and {bak.eerie_detail}."
    )
    child.memes["wonder"] += 1
    hound.memes["haunt"] += 1


def temptation(world: World, child: Entity, bak: Bakery) -> None:
    world.say(
        f"{child.id} found a choice: one sweet bun could be kept for {child.pronoun('possessive')}self, "
        f"or it could be shared with someone lonely."
    )


def warning(world: World, hound: Entity, child: Entity, baker: Entity) -> None:
    child.memes["conflict"] += 1
    world.say(
        f"The hound drifted closer and whispered, 'Take it all.' But behind the counter, "
        f"{baker.id} watched quietly, as if waiting to see what {child.id} would become."
    )


def decide(world: World, child: Entity, baker: Entity, choice: Choice) -> None:
    pred = predict_choice(world, choice.id)
    world.facts["predicted"] = pred
    if choice.id == "share":
        world.say(
            f"{child.id} breathed in the warm smell of bread, then chose to share the bun instead."
        )
        child.memes["conflict"] = 0.0
        child.memes["kindness"] += 1
    else:
        world.say(
            f"{child.id} took the bun and hid it close, even though the choice made {child.pronoun('object')} feel uneasy."
        )
        child.memes["conflict"] += 1


def resolve_story(world: World, child: Entity, hound: Entity, baker: Entity, bak: Bakery, choice: Choice) -> None:
    if choice.id == "share":
        baker.meters["pastries_shared"] += 1
        hound.meters["vanish"] += 1
        world.say(
            f"The hound gave a soft, misty nod. Its shape thinned like steam, and the baker smiled."
        )
        world.say(
            f"{baker.id} slid a second bun onto a paper plate for the child to carry to the old gate outside."
        )
        world.say(
            f"There, {child.id} left the bun for a smaller, shivering stray, and the bakery felt warmer than before."
        )
        world.say(
            f"By the end, the ghostly hound was only a pale wag in the window, and {child.id} had learned that a kind choice can quiet a dark room."
        )
    else:
        hound.meters["haunt"] += 1
        world.say(
            f"The hound grinned through the dark glass, and the room felt colder."
        )
        world.say(
            f"{baker.id} came out with a lantern and a firm voice, asking {child.id} to make a better choice."
        )
        world.say(
            f"{child.id} finally placed the bun on the counter, and the hound faded as if it had been waiting for that one brave act."
        )
        world.say(
            f"The bakery went quiet again, but the cold on the windows stayed a little while longer."
        )


def tell(bak: Bakery, choice: Choice, conflict: ConflictBeat,
         child_name: str = "Mina", child_gender: str = "girl",
         baker_name: str = "Bela", baker_gender: str = "woman") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    hound = world.add(Entity(id="hound", kind="character", type="ghost-hound", role="ghost", haunting=True))
    baker = world.add(Entity(id=baker_name, kind="character", type=baker_gender, role="baker"))
    bun = world.add(Entity(id="bun", type="thing", label="a cinnamon bun", bakery_item=True, edible=True, can_share=True))
    world.facts.update(bakery=bak, choice=choice, conflict=conflict, child=child, hound=hound, baker=baker, bun=bun)

    opening(world, bak, child, hound, baker)
    world.para()
    temptation(world, child, bak)
    warning(world, hound, child, baker)
    decide(world, child, baker, choice)
    world.para()
    resolve_story(world, child, hound, baker, bak, choice)

    child.meters["moral_value"] += choice.moral
    world.facts.update(
        outcome="kind" if choice.id == "share" else "stubborn",
        moral_value=child.meters["moral_value"],
        conflict_level=child.memes["conflict"],
    )
    return world


THEMES = {
    "bakery_ghost": Bakery(
        id="bakery_ghost",
        place="the bakery",
        scent="fresh bread and sugar",
        quiet_detail="the trays were still warm from the oven",
        eerie_detail="a pale hound-shaped shadow floated over the flour dust",
        ending_image="the lantern glow sat golden on the counter",
    )
}

CHOICES = {
    "share": Choice("share", "share the bun", "shared the bun", "the room grew warmer", 1, 3, {"kindness", "moral"}),
    "keep": Choice("keep", "keep the bun", "kept the bun hidden", "the room stayed cold", 0, 2, {"selfishness", "conflict"}),
}

CONFLICTS = {
    "spooky_choice": ConflictBeat("spooky_choice", "a ghostly tug-of-war", "the hound pressed the child to be selfish", 1, {"ghost", "conflict"}),
}

GIRL_NAMES = ["Mina", "Lina", "Mila", "Nora", "Ivy", "Rose"]
BOY_NAMES = ["Owen", "Theo", "Eli", "Noah", "Leo", "Finn"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [("bakery_ghost", "spooky_choice", cid) for cid in CHOICES]


@dataclass
class StoryParams:
    theme: str
    conflict: str
    choice: str
    child_name: str
    child_gender: str
    baker_name: str
    baker_gender: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story bakery world about choice, hound, moral value, and conflict.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--conflict", choices=CONFLICTS)
    ap.add_argument("--choice", choices=CHOICES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--baker-name")
    ap.add_argument("--baker-gender", choices=["woman", "man"])
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
              if (args.theme is None or c[0] == args.theme)
              and (args.conflict is None or c[1] == args.conflict)
              and (args.choice is None or c[2] == args.choice)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, conflict, choice = rng.choice(combos)
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    baker_gender = args.baker_gender or rng.choice(["woman", "man"])
    baker_name = args.baker_name or rng.choice(["Bela", "Rowan", "Greta", "Marta", "Hugo", "Nell"])
    return StoryParams(theme, conflict, choice, child_name, child_gender, baker_name, baker_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a ghost-story set in {f["bakery"].place} that includes the words "choice" and "hound".',
        f"Tell a child-facing story about a bakery, a spooky hound, and a hard moral choice between keeping and sharing food.",
        f"Write a quiet ghost story where a child must make a kind choice in a bakery and the ending shows the room grow warmer.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, baker, choice, bak = f["child"], f["baker"], f["choice"], f["bakery"]
    ans1 = (
        f"{child.id} was in {bak.place}, where fresh bread and sugar drifted through the air. "
        f"A ghostly hound appeared and made the child face a choice."
    )
    ans2 = (
        f"The hound pushed {child.id} toward selfishness, but the baker stayed calm and watched. "
        f"That made the conflict feel serious, because the child had to decide what kind of person to be."
    )
    ans3 = (
        f"{child.id} chose to share the bun, and that kinder choice warmed the bakery. "
        f"The ghost hound faded, which showed the moral value of the choice."
    )
    return [
        QAItem("Where did the story happen?", ans1),
        QAItem("Why was there conflict in the bakery?", ans2),
        QAItem("What did the child choose in the end, and what changed?", ans3),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a bakery?", "A bakery is a place where bread, buns, and other baked treats are made and sold."),
        QAItem("What is a hound?", "A hound is a kind of dog. In ghost stories, a hound can seem spooky or mysterious."),
        QAItem("What does it mean to share?", "To share means to give part of something to someone else instead of keeping it all."),
        QAItem("Why is kindness a moral value?", "Kindness helps people and makes a group feel safer, warmer, and more trusted."),
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
    lines.append("== (3) World knowledge questions ==")
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.haunting:
            bits.append("haunting=True")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(theme, conflict, share) :- theme(theme), conflict(conflict), choice(share).
valid(theme, conflict, keep) :- theme(theme), conflict(conflict), choice(keep).
moral(share).
conflict(keep).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for cid in CONFLICTS:
        lines.append(asp.fact("conflict", cid))
    for cid in CHOICES:
        lines.append(asp.fact("choice", cid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: default generate smoke test succeeded.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(THEMES[params.theme], CHOICES[params.choice], CONFLICTS[params.conflict],
                 params.child_name, params.child_gender, params.baker_name, params.baker_gender)
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{t} {c} {ch}" for t, c, ch in asp_valid_combos()))
        return
    base = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams("bakery_ghost", "spooky_choice", cid, "Mina", "girl", "Bela", "woman")) for cid in CHOICES]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base + i))
            params.seed = base + i
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
