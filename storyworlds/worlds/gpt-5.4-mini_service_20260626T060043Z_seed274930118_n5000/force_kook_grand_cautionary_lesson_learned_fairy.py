#!/usr/bin/env python3
"""
A small fairy-tale storyworld about force, a kooky mistake, and a grand lesson.

The seed tale imagined here:
---
In a grand forest, little Pippa found a locked silver gate. A kooky raven told
her to force it open, but the gate was enchanted. Pippa pushed hard, the gate
shook, and a thistle crown fell into the mud. Then a wise old lantern sprite
said the kind way was to ask the gatekeeper stone for help. Pippa apologized,
used a soft knock, and the gate opened with a chime. She learned that force can
hurt what magic is trying to keep safe.
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

# ---------------------------------------------------------------------------
# Shared world model
# ---------------------------------------------------------------------------


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" or "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "queen", "mother", "fairy"}
        male = {"boy", "man", "king", "father", "raven", "sprite"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    grand: bool = False
    openable: set[str] = field(default_factory=set)


@dataclass
class Challenge:
    id: str
    verb: str
    gerund: str
    rush: str
    force: str
    consequence: str
    target: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    fragile: bool = True


@dataclass
class Remedy:
    id: str
    label: str
    method: str
    ending: str
    suitable_for: set[str] = field(default_factory=set)
    calm: bool = True


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.trace: list[str] = []

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
        import copy

        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.facts = copy.deepcopy(self.facts)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "grand_forest": Place("the grand forest", grand=True, openable={"gate", "door"}),
    "moon_glen": Place("Moon Glen", grand=True, openable={"gate"}),
    "mossy_keep": Place("the mossy keep", grand=True, openable={"door", "gate"}),
}

CHALLENGES = {
    "gate": Challenge(
        id="gate",
        verb="open the gate",
        gerund="opening the gate",
        rush="push the gate wide",
        force="force it open",
        consequence="the hinges creaked and the lock jammed tighter",
        target="gate",
        tags={"force", "cautionary"},
    ),
    "door": Challenge(
        id="door",
        verb="open the door",
        gerund="opening the door",
        rush="shove the door",
        force="force the door open",
        consequence="the door groaned and the latch slipped crooked",
        target="door",
        tags={"force", "lesson"},
    ),
}

PRIZES = {
    "thistle_crown": Prize(
        id="thistle_crown",
        label="thistle crown",
        phrase="a bright thistle crown",
        region="head",
    ),
    "silver_key": Prize(
        id="silver_key",
        label="silver key",
        phrase="a tiny silver key",
        region="hand",
    ),
    "star_cloak": Prize(
        id="star_cloak",
        label="star cloak",
        phrase="a grand starry cloak",
        region="shoulders",
    ),
}

REMEDIES = {
    "soft_knock": Remedy(
        id="soft_knock",
        label="soft knock",
        method="tap three times and speak politely",
        ending="the gate answered with a sweet chime",
        suitable_for={"gate", "door"},
    ),
    "ask_stone": Remedy(
        id="ask_stone",
        label="gatekeeper stone",
        method="ask the gatekeeper stone for help",
        ending="the stone woke, bowed, and unlatched the way",
        suitable_for={"gate"},
    ),
    "key_turn": Remedy(
        id="key_turn",
        label="silver key",
        method="use the silver key with patience",
        ending="the key turned like a little song",
        suitable_for={"door"},
    ),
}

NAMES = ["Pippa", "Milo", "Tessa", "Nell", "Bram", "Eloise"]
TITLES = ["little", "brave", "curious", "bright", "gentle", "kooky"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------


@dataclass
class StoryParams:
    place: str
    challenge: str
    prize: str
    name: str
    title: str
    companion: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A challenge is cautionary when force would damage the prize or spoil the opening.
risk(C,P) :- challenge(C), prize(P), target(C,R), prize_region(P,R).

% A remedy is suitable if it matches the target and is gentle.
suitable(R,C) :- remedy(R), challenge(C), allows(R, T), target(C, T).

% A story is valid if the challenge is risky and a suitable remedy exists.
valid_story(Place, C, P, R) :- place(Place), challenge(C), prize(P), remedy(R),
                               risk(C,P), suitable(R,C).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for cid, c in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        lines.append(asp.fact("target", cid, c.target))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_region", pid, p.region))
    for rid, r in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        for t in sorted(r.suitable_for):
            lines.append(asp.fact("allows", rid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------


def challenge_is_risky(challenge: Challenge, prize: Prize) -> bool:
    return (challenge.id == "gate" and prize.region in {"head", "hand", "shoulders"}) or (
        challenge.id == "door" and prize.region in {"hand", "shoulders"}
    )


def choose_remedy(challenge: Challenge) -> Optional[Remedy]:
    for remedy in REMEDIES.values():
        if challenge.id in remedy.suitable_for:
            return remedy
    return None


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in PLACES:
        for challenge in CHALLENGES:
            for prize in PRIZES:
                for remedy in REMEDIES:
                    c = CHALLENGES[challenge]
                    p = PRIZES[prize]
                    r = REMEDIES[remedy]
                    if challenge_is_risky(c, p) and challenge in r.suitable_for:
                        combos.append((place, challenge, prize, remedy))
    return combos


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------


def _predict(world: World, hero: Entity, challenge: Challenge, prize: Prize) -> dict:
    sim = world.copy()
    _attempt_force(sim, hero, challenge, prize, narrate=False)
    return {
        "ruined": bool(sim.facts.get("ruined")),
        "tension": sim.facts.get("tension", 0),
    }


def _attempt_force(world: World, hero: Entity, challenge: Challenge, prize: Prize, narrate: bool = True) -> None:
    hero.memes["impulse"] = hero.memes.get("impulse", 0) + 1
    world.facts["used_force"] = True
    world.facts["tension"] = world.facts.get("tension", 0) + 1
    if challenge_is_risky(challenge, prize):
        world.facts["ruined"] = True
    if narrate:
        world.say(
            f"{hero.id} tried to {challenge.force}, and {challenge.consequence}."
        )


def tell(place: Place, challenge: Challenge, prize: Prize, name: str, title: str, companion: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=name, kind="character", type="girl", label=name))
    other = world.add(Entity(id="companion", kind="character", type=companion, label=f"the {companion}"))
    prize_ent = world.add(Entity(id="prize", type=prize.id, label=prize.label, phrase=prize.phrase, owner=hero.id))
    remedy = choose_remedy(challenge)

    world.say(
        f"Once in {place.name}, there was a {title} girl named {hero.id}, and everyone called {hero.id} a little {title} soul."
    )
    world.say(
        f"She loved the {place.name} because it felt grand, and she also had a kooky little friend who liked to tell bold tales."
    )
    world.say(
        f"One morning, {hero.id} found {prize.phrase} near a {challenge.target}."
    )

    world.para()
    world.say(
        f"{hero.id} wanted to {challenge.verb}, but the {challenge.target} was enchanted and would not budge for force."
    )
    pred = _predict(world, hero, challenge, prize)
    if pred["ruined"]:
        world.say(
            f"A cautious hush came over the stones, for everyone could see that force would only make trouble."
        )
    _attempt_force(world, hero, challenge, prize, narrate=True)

    world.para()
    if remedy:
        world.say(
            f"Then the kooky friend grew serious and said, 'Lesson learned: try the {remedy.label}, not rough hands.'"
        )
        world.say(
            f"{hero.id} listened, apologized to the {challenge.target}, and chose to {remedy.method}."
        )
        world.say(
            f"At once, {remedy.ending}, and {hero.id} took back {prize_ent.pronoun('possessive')} {prize.label} without another push."
        )
        world.say(
            f"By the end, the grand place was peaceful again, and {hero.id} had learned that careful kindness works better than force."
        )

    world.facts.update(
        hero=hero,
        other=other,
        prize=prize_ent,
        challenge=challenge,
        remedy=remedy,
        place=place,
        title=title,
        companion=companion,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy-tale story about a {f["title"]} girl named {f["hero"].id} in {f["place"].name} who faces a {f["challenge"].target} and learns a cautionary lesson.',
        f"Tell a grand, child-friendly tale where {f['hero'].id} wants to {f['challenge'].verb} but a kooky friend helps her choose a gentler way.",
        f'Write a story that includes the words "force", "kooky", and "grand", and ends with lesson learned.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    prize: Entity = f["prize"]
    challenge: Challenge = f["challenge"]
    remedy: Optional[Remedy] = f["remedy"]

    items = [
        QAItem(
            question=f"What did {hero.id} want to do with the {challenge.target}?",
            answer=f"{hero.id} wanted to {challenge.verb}, but that was a risky choice.",
        ),
        QAItem(
            question=f"Why was the story cautionary?",
            answer=(
                f"It was cautionary because force made the {challenge.target} act badly, "
                f"and the story showed that rough pushing can cause harm."
            ),
        ),
        QAItem(
            question=f"What happened to {prize.label} when {hero.id} used force?",
            answer=f"The story says {prize.label} was in danger while the forceful attempt made the problem worse.",
        ),
    ]
    if remedy:
        items.append(
            QAItem(
                question=f"How did {hero.id} fix the problem?",
                answer=(
                    f"She used the {remedy.label}, listened carefully, and chose the gentle method instead of force."
                ),
            )
        )
        items.append(
            QAItem(
                question="What lesson did she learn?",
                answer="She learned that kindness, patience, and asking for help work better than forcing things open.",
            )
        )
    return items


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does cautionary mean?",
            answer="Cautionary means a story warns you about a bad choice so you can be careful.",
        ),
        QAItem(
            question="What does it mean to learn a lesson?",
            answer="To learn a lesson means to understand something important from what happened.",
        ),
        QAItem(
            question="What is a fairy tale?",
            answer="A fairy tale is a magical story with unusual people, talking creatures, and an important lesson.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld about force, a kooky warning, and a grand lesson.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--title", choices=TITLES)
    ap.add_argument("--companion", choices=["raven", "sprite", "fox"])
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
    combos = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.challenge is None or c[1] == args.challenge)
        and (args.prize is None or c[2] == args.prize)
    ]
    if not combos:
        raise StoryError("No valid fairy-tale combination matches those options.")

    place, challenge, prize, _remedy = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    title = args.title or rng.choice(TITLES)
    companion = args.companion or rng.choice(["raven", "sprite", "fox"])
    return StoryParams(place=place, challenge=challenge, prize=prize, name=name, title=title, companion=companion)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], CHALLENGES[params.challenge], PRIZES[params.prize], params.name, params.title, params.companion)
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP verification
# ---------------------------------------------------------------------------


def asp_verify() -> int:
    import asp

    def py():
        return set(valid_combos())

    def asp_set():
        model = asp.one_model(asp_program("#show valid_story/4."))
        return set(asp.atoms(model, "valid_story"))

    if py() == asp_set():
        print(f"OK: ASP matches Python ({len(py())} combos).")
        return 0
    print("Mismatch between ASP and Python.")
    print("Python-only:", sorted(py() - asp_set()))
    print("ASP-only:", sorted(asp_set() - py()))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="grand_forest", challenge="gate", prize="thistle_crown", name="Pippa", title="brave", companion="raven"),
    StoryParams(place="moon_glen", challenge="gate", prize="silver_key", name="Tessa", title="curious", companion="sprite"),
    StoryParams(place="mossy_keep", challenge="door", prize="star_cloak", name="Eloise", title="gentle", companion="fox"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_stories()
        for t in triples:
            print(t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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
            header = f"### {p.name}: {p.challenge} at {p.place} ({p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
