#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/permit_dominant_suspense_folk_tale.py
=====================================================================

A small folk-tale storyworld with suspense around a much-wanted permit.

Premise:
A child and a helper want to cross a guarded bridge to bring medicine to a
grandparent. The bridge keeper is dominant and will only permit passage if the
travellers bring the right token and show patience. Suspense comes from the
tight clock, the keeper's stern manner, and the risk that the path will close
before the medicine arrives.

The world stays compact:
- typed entities with physical meters and emotional memes
- a causal turn driven by state, not frozen prose
- a calm resolution that proves what changed
- three Q&A sets grounded in world state

The story uses the seed words "permit" and "dominant" directly, while keeping a
folk-tale style with a bridgekeeper, a village path, and a simple moral tone.
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
TOKEN_NEED = 1.0
CLOCK_LIMIT = 2.0


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
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother"}
        male = {"boy", "father", "dad", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father",
                "grandmother": "grandmother", "grandfather": "grandfather"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    kind: str
    guarded: bool = False
    requires_token: bool = False
    narrow: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Token:
    id: str
    label: str
    phrase: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Keeper:
    id: str
    label: str
    demeanor: str
    dominant: bool = True
    permit_word: str = "permit"
    tags: set[str] = field(default_factory=set)


@dataclass
class Goal:
    id: str
    label: str
    phrase: str
    needy: bool = True
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
        c.facts = copy.deepcopy(self.facts)
        return c


def _r_clock(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("clock") and world.facts["clock"] >= CLOCK_LIMIT:
        if "gate" in world.entities:
            gate = world.get("gate")
            if gate.meters["closed"] < THRESHOLD:
                gate.meters["closed"] += 1
                out.append("The gate would not stay open forever.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if child and child.memes["fear"] >= THRESHOLD and "grandmother" in world.entities:
        world.get("grandmother").memes["worry"] += 1
        out.append("Far away, the grandmother waited and listened for the road.")
    return out


CAUSAL_RULES = [_r_clock, _r_worry]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)


def _do_wait(world: World, child: Entity) -> None:
    child.memes["patience"] += 1
    world.facts["clock"] += 1
    propagate(world, narrate=False)


def _ask_permit(world: World, child: Entity, keeper: Entity, place: Place) -> None:
    child.memes["hope"] += 1
    world.say(
        f"{child.id} came to the {place.label} and bowed politely. "
        f'"Good keeper," {child.id} said, "will you {keeper.attrs["permit_word"]} us across?"'
    )


def _refuse_then_test(world: World, keeper: Entity, child: Entity, place: Place, token: Token) -> None:
    keeper.memes["stern"] += 1
    world.say(
        f'The {keeper.label} stood {keeper.attrs["demeanor"]} and dominant as an old oak. '
        f'"Not yet," {keeper.id} said. "A traveler must bring the {token.label} and keep a steady heart."'
    )
    child.memes["fear"] += 1
    if place.requires_token:
        world.say(f"The bridge was narrow, and the wind teased the boards beneath their feet.")


def _show_token(world: World, child: Entity, keeper: Entity, token: Token) -> bool:
    child.meters["token"] += 1
    child.memes["courage"] += 1
    keeper.memes["respect"] += 1
    enough = child.meters["token"] >= TOKEN_NEED
    if enough:
        world.say(
            f"{child.id} held up {token.phrase}. The keeper's stern look softened a little."
        )
    else:
        world.say(
            f"{child.id} searched the pocket and found nothing but lint and hope."
        )
    return enough


def _permit_crossing(world: World, child: Entity, keeper: Entity, place: Place, goal: Goal) -> None:
    keeper.meters["permit"] += 1
    world.say(
        f"At last the {keeper.label} gave the word to {keeper.attrs['permit_word']} them through."
    )
    world.say(
        f"{child.id} crossed the bridge at once, and the road to {goal.label} opened like a ribbon."
    )


def _miss_the_chance(world: World, child: Entity, keeper: Entity, place: Place, goal: Goal) -> None:
    child.memes["fear"] += 1
    world.say(
        f"But the clouds grew darker, and the keeper said the gate must close now."
    )
    world.say(
        f"{child.id} turned back with the medicine held tight, promising to return at dawn by the long way."
    )
    world.say(
        f"Even so, the village remembered the lesson: a calm heart and the right token can open a stubborn road."
    )


def tell(place: Place, keeper: Keeper, token: Token, goal: Goal,
         child_name: str = "Mara", child_gender: str = "girl",
         companion_name: str = "Niko", companion_gender: str = "boy",
         grandmother_name: str = "Grandmother", clock: int = 0) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    companion = world.add(Entity(id=companion_name, kind="character", type=companion_gender, role="companion"))
    guard = world.add(Entity(id="keeper", kind="character", type="man", role="keeper", label=keeper.label))
    grandmother = world.add(Entity(id=grandmother_name, kind="character", type="grandmother", role="elder", label="the grandmother"))
    gate = world.add(Entity(id="gate", type="place", label=place.label))
    goal_ent = world.add(Entity(id="goal", type="goal", label=goal.label))

    guard.attrs["demeanor"] = keeper.demeanor
    guard.attrs["permit_word"] = keeper.permit_word
    world.facts["clock"] = float(clock)

    child.memes["hope"] = 1.0
    companion.memes["loyal"] = 1.0
    grandmother.memes["worry"] = 0.0

    world.say(
        f"Long ago, in a small village, {child.id} and {companion.id} carried a basket to {goal.label}."
    )
    world.say(
        f"The path ended at a guarded bridge, and the {keeper.label} watched the boards with a dominant eye."
    )
    world.say(
        f"Inside the basket lay medicine for {grandmother_name.lower()}, and the hour was growing late."
    )

    world.para()
    _ask_permit(world, child, guard, place)
    _refuse_then_test(world, guard, child, place, token)

    world.para()
    if _show_token(world, child, guard, token):
        if world.facts["clock"] < CLOCK_LIMIT:
            _permit_crossing(world, child, guard, place, goal)
            world.say(
                f"{companion.id} hurried beside {child.id}, and together they reached the cottage before night fell."
            )
            outcome = "permitted"
        else:
            _miss_the_chance(world, child, guard, place, goal)
            outcome = "late"
    else:
        _miss_the_chance(world, child, guard, place, goal)
        outcome = "late"

    child.memes["lesson"] += 1
    world.facts.update(
        child=child,
        companion=companion,
        keeper=guard,
        grandmother=grandmother,
        place=place,
        token=token,
        goal=goal_ent,
        outcome=outcome,
    )
    return world


PLACES = {
    "bridge": Place("bridge", "bridge", "crossing", guarded=True, requires_token=True, narrow=True,
                    tags={"bridge", "guarded"}),
    "gate": Place("gate", "stone gate", "gateway", guarded=True, requires_token=True, narrow=True,
                  tags={"gate", "guarded"}),
    "ford": Place("ford", "river ford", "crossing", guarded=False, requires_token=False, narrow=True,
                  tags={"ford"}),
}

TOKENS = {
    "seal": Token("seal", "wax seal", "a wax seal", tags={"seal", "permit"}),
    "leaf": Token("leaf", "green leaf badge", "a green leaf badge", tags={"leaf", "permit"}),
    "ribbon": Token("ribbon", "blue ribbon", "a blue ribbon from the miller", tags={"ribbon"}),
}

KEEPERS = {
    "bridgekeeper": Keeper("bridgekeeper", "bridgekeeper", "by the gate", True, "permit", tags={"keeper", "dominant"}),
    "watcher": Keeper("watcher", "watcher", "on the steps", True, "permit", tags={"keeper", "dominant"}),
}

GOALS = {
    "cottage": Goal("cottage", "the cottage", "the grandmother's cottage", True, tags={"cottage", "elder"}),
    "mill": Goal("mill", "the mill", "the mill by the stream", True, tags={"mill"}),
}

GIRL_NAMES = ["Mara", "Elsa", "Ines", "Lina", "Sera"]
BOY_NAMES = ["Niko", "Oren", "Tavi", "Bram", "Jory"]


@dataclass
class StoryParams:
    place: str
    keeper: str
    token: str
    goal: str
    child: str
    child_gender: str
    companion: str
    companion_gender: str
    clock: int = 0
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES.values():
        for t in TOKENS.values():
            for g in GOALS.values():
                if p.requires_token and "permit" in t.tags:
                    combos.append((p.id, t.id, g.id))
                elif not p.requires_token:
                    combos.append((p.id, t.id, g.id))
    return combos


KNOWLEDGE = {
    "permit": [("What is a permit?", "A permit is permission that lets someone do a thing or go somewhere. It is a word for being allowed.")],
    "bridge": [("What is a bridge?", "A bridge is a path built over water or a gap so people can cross safely.")],
    "gate": [("What is a gate?", "A gate is a doorway in a fence or wall that can open and close.")],
    "dominant": [("What does dominant mean?", "Dominant means strong, bossy, or in charge in a way that others can feel right away.")],
    "token": [("What is a token?", "A token is a small sign or object that shows you belong or have permission.")],
    "medicine": [("Why is medicine important?", "Medicine can help someone feel better when they are sick.")],
    "night": [("Why is it scary when night is coming?", "Night can feel scary because the light fades and it is harder to see the road.")],
}
KNOWLEDGE_ORDER = ["permit", "bridge", "gate", "dominant", "token", "medicine", "night"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a suspenseful folk tale that includes the words "permit" and "dominant".',
        f"Tell a small village story where {f['child'].id} asks a dominant keeper for a permit to cross the {f['place'].label}.",
        f"Write a calm-but-tense story about a child who needs permission to cross a guarded bridge before dark.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    companion = f["companion"]
    keeper = f["keeper"]
    place = f["place"]
    token = f["token"]
    goal = f["goal"]
    out = f["outcome"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and {companion.id}, who wanted to cross {place.label} before night came."),
        ("Why did they need a permit?",
         f"They needed a permit because the bridge was guarded and the keeper would not let anyone pass without permission. The permit showed they were allowed to cross."),
        ("What made the keeper seem dominant?",
         f"The keeper spoke in a stern voice and stood like the one in charge at the bridge. That dominant manner made the crossing feel tense until the right token appeared."),
    ]
    if out == "permitted":
        qa.append((
            "How did the children get across?",
            f"{child.id} showed {token.phrase}, and the keeper gave them permission to cross. After that, they hurried over the bridge and reached {goal.label} in time."
        ))
        qa.append((
            "How did the story end?",
            f"It ended well: the permit was granted, the road opened, and the medicine reached the grandmother before night closed in. The ending proves the waiting was worth it."
        ))
    else:
        qa.append((
            "What happened when time ran out?",
            f"The keeper closed the gate before they could safely cross, so {child.id} had to turn back. The medicine stayed with them, but the story kept its suspense because the road would not open in time."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with a careful retreat and a lesson about patience and the right token. The children were safe, even though the bridge stayed closed."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["place"].tags) | set(world.facts["token"].tags) | set(world.facts["goal"].tags) | {"permit", "dominant", "night"}
    out = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(KNOWLEDGE[key])
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("bridge", "bridgekeeper", "seal", "cottage", "Mara", "girl", "Niko", "boy", 0),
    StoryParams("gate", "watcher", "leaf", "mill", "Elsa", "girl", "Bram", "boy", 1),
    StoryParams("ford", "watcher", "ribbon", "cottage", "Tavi", "boy", "Lina", "girl", 2),
]


def explain_rejection() -> str:
    return "(No story: this tale needs a guarded crossing and a real permit, so the suspense has a reason to matter.)"


ASP_RULES = r"""
valid(P, T, G) :- place(P), token(T), goal(G), guarded(P).
permit_needed(P) :- guarded(P).
dominant_keeper(K) :- keeper(K), dominant(K).
suspense(P, T, G) :- valid(P, T, G), permit_needed(P), token(T).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.guarded:
            lines.append(asp.fact("guarded", pid))
    for tid in TOKENS:
        lines.append(asp.fact("token", tid))
    for gid in GOALS:
        lines.append(asp.fact("goal", gid))
    for kid, k in KEEPERS.items():
        lines.append(asp.fact("keeper", kid))
        if k.dominant:
            lines.append(asp.fact("dominant", kid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos().")
    try:
        sample = generate(CURATED[0])
        assert sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale suspense world about a permit and a dominant keeper.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--keeper", choices=KEEPERS)
    ap.add_argument("--token", choices=TOKENS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--companion")
    ap.add_argument("--companion-gender", choices=["girl", "boy"])
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.token:
        combos = [c for c in combos if c[1] == args.token]
    if args.goal:
        combos = [c for c in combos if c[2] == args.goal]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, token, goal = rng.choice(combos)
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    companion_gender = args.companion_gender or ("boy" if child_gender == "girl" else "girl")
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    companion = args.companion or rng.choice([n for n in (BOY_NAMES if companion_gender == "boy" else GIRL_NAMES) if n != child])
    keeper = args.keeper or rng.choice(list(KEEPERS))
    return StoryParams(place, keeper, token, goal, child, child_gender, companion, companion_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], KEEPERS[params.keeper], TOKENS[params.token], GOALS[params.goal],
                 params.child, params.child_gender, params.companion, params.companion_gender, clock=params.clock)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for p, t, g in asp_valid_combos():
            print(p, t, g)
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
