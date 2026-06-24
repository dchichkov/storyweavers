#!/usr/bin/env python3
"""
A small mythic storyworld about a relay, a conflict, kindness, and problem solving.

A seed tale for this world:
---
Long ago, in a valley of gold grass, the runners of Hearth Hill prepared for the
sunset relay. Each runner carried a wooden token of hope from one stone arch to
the next. But on the day of the race, two runners argued over who should begin.
Their quarrel slowed the line, and the wind tugged the token toward the river.

Then a kind child named Mira noticed the trouble. She did not shout. She listened,
asked each runner what they feared, and found a careful plan: one runner would
start, the other would anchor the token with a ribbon, and both would run together
for the last stretch. The relay finished, the token stayed safe, and the valley
cheered.
---

The simulated world below turns that premise into state: who is carrying the token,
where the conflict rises, how kindness reduces it, and how problem solving
restores the relay to motion.
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
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carrier: Optional[str] = None
    place: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        feminine = {"girl", "woman", "mother", "sister"}
        masculine = {"boy", "man", "father", "brother"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def reflexive(self) -> str:
        if self.type in {"girl", "woman", "mother", "sister"}:
            return "herself"
        if self.type in {"boy", "man", "father", "brother"}:
            return "himself"
        return "itself"

    def noun(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    detail: str
    wind: bool = False
    river: bool = False


@dataclass
class Relay:
    id: str
    name: str
    token_label: str
    token_phrase: str
    start_text: str
    finish_text: str
    problem: str
    solution: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    relay: str
    hero: str
    hero_type: str
    rival: str
    rival_type: str
    helper: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place, relay: Relay) -> None:
        self.place = place
        self.relay = relay
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "hearth_valley": Place(
        id="hearth_valley",
        label="Hearth Valley",
        detail="a wide valley where the grass shone like old gold",
        wind=True,
        river=True,
    ),
    "stone_bridge": Place(
        id="stone_bridge",
        label="Stone Bridge",
        detail="an ancient bridge that crossed a bright river",
        wind=True,
        river=True,
    ),
    "sun_gate": Place(
        id="sun_gate",
        label="the Sun Gate",
        detail="a shining arch where races began and ended",
        wind=False,
        river=False,
    ),
}

RELAYS = {
    "sun_token": Relay(
        id="sun_token",
        name="sunset relay",
        token_label="sun-token",
        token_phrase="a small wooden token carved with a spiral sun",
        start_text="the first runner lifted the token at the stone arch",
        finish_text="the last runner touched the token to the finish stone",
        problem="the runners argued and the token nearly slipped toward the river",
        solution="the helper tied a ribbon to the token so it could be shared safely",
        tags={"relay", "conflict", "kindness", "problem_solving", "myth"},
    ),
    "moon_streak": Relay(
        id="moon_streak",
        name="moon relay",
        token_label="moon-token",
        token_phrase="a smooth silver token that caught the moonlight",
        start_text="the first runner raised the token under the pale sky",
        finish_text="the final runner set the token into a moonstone bowl",
        problem="the runners could not agree on who should begin",
        solution="the helper suggested a rhythm: one step, one breath, one pass",
        tags={"relay", "conflict", "kindness", "problem_solving", "myth"},
    ),
    "river_run": Relay(
        id="river_run",
        name="river relay",
        token_label="river-token",
        token_phrase="a round token polished by many careful hands",
        start_text="the runners gathered where the river bent around the reeds",
        finish_text="the token crossed the water on a braid of reeds and silk",
        problem="a gust threatened to scatter the handoff",
        solution="the helper asked everyone to make a calm chain of hands",
        tags={"relay", "conflict", "kindness", "problem_solving", "myth"},
    ),
}

HERO_NAMES = ["Mira", "Anya", "Leto", "Nilo", "Iris", "Tavi", "Orin", "Suri"]
RIVAL_NAMES = ["Korin", "Dara", "Pax", "Rhea", "Bren", "Sel", "Juno", "Aris"]
HELPER_NAMES = ["Edda", "Pina", "Hale", "Mara", "Theo", "Sana", "Bela", "Neri"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combo(place: Place, relay: Relay) -> bool:
    return relay.id in RELAYS and place.id in PLACES and ("relay" in relay.tags)


def valid_combos() -> list[tuple[str, str]]:
    return [(p.id, r.id) for p in PLACES.values() for r in RELAYS.values() if valid_combo(p, r)]


def explain_rejection(place: Place, relay: Relay) -> str:
    return (
        f"(No story: {relay.name} belongs in a place like {place.label}, but the chosen "
        f"pair does not make a strong relay tale.)"
    )


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def begin_state(world: World, hero: Entity, rival: Entity, helper: Entity) -> None:
    world.say(
        f"Long ago, in {world.place.label}, there was a {world.place.detail}. "
        f"There the runners prepared for {world.relay.name}."
    )
    world.say(
        f"{hero.id} was quick-footed, {rival.id} was proud, and {helper.id} was the one who noticed the small worries others missed."
    )
    world.facts["hero"] = hero
    world.facts["rival"] = rival
    world.facts["helper"] = helper


def start_relay(world: World) -> None:
    world.say(
        f"{world.relay.start_text}. The token was meant to move from hand to hand until the whole path was finished."
    )
    world.facts["token_safe"] = True
    world.facts["relay_started"] = True


def conflict_beats(world: World, hero: Entity, rival: Entity) -> None:
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1
    rival.memes["pride"] = rival.memes.get("pride", 0.0) + 1
    hero.memes["conflict"] = hero.memes.get("conflict", 0.0) + 1
    rival.memes["conflict"] = rival.memes.get("conflict", 0.0) + 1
    world.facts["conflict"] = True
    world.say(
        f"But {hero.id} and {rival.id} both wanted the opening run. Their voices grew sharp, and the line of runners slowed."
    )
    if world.place.wind:
        world.say(
            f"The wind found the pause and tugged at the token as if it wanted to steal the race away."
        )
        world.facts["token_safe"] = False


def kindness_beats(world: World, helper: Entity, hero: Entity, rival: Entity) -> None:
    helper.memes["kindness"] = helper.memes.get("kindness", 0.0) + 1
    helper.memes["calm"] = helper.memes.get("calm", 0.0) + 1
    hero.memes["heard"] = hero.memes.get("heard", 0.0) + 1
    rival.memes["heard"] = rival.memes.get("heard", 0.0) + 1
    world.facts["kindness"] = True
    world.say(
        f"{helper.id} did not scold them. {helper.pronoun().capitalize()} sat between them and asked what each runner feared."
    )
    world.say(
        f"At last they listened. The sharpness in the air softened, because kindness made room for both voices."
    )


def problem_solving_beats(world: World, helper: Entity, hero: Entity, rival: Entity) -> None:
    world.facts["problem_solving"] = True
    hero.memes["calm"] = hero.memes.get("calm", 0.0) + 1
    rival.memes["calm"] = rival.memes.get("calm", 0.0) + 1
    hero.memes["conflict"] = 0.0
    rival.memes["conflict"] = 0.0
    world.say(
        f"{helper.id} then found a plan: {world.relay.solution}."
    )
    world.say(
        f"{hero.id} would begin, {rival.id} would guard the token on the middle stretch, and both would run together at the end."
    )
    world.facts["token_safe"] = True


def finish_relay(world: World, hero: Entity, rival: Entity, helper: Entity) -> None:
    world.para()
    world.say(
        f"The race moved again. One runner passed the token, then another, and the last runner carried it through the final turn."
    )
    world.say(
        f"{world.relay.finish_text}. {hero.id} and {rival.id} smiled at each other, because the quarrel had turned into a stronger way to run."
    )
    world.say(
        f"{helper.id} watched the finish and smiled too. In that old valley, the relay ended with safe hands, a steady heart, and everyone cheering together."
    )
    world.facts["finished"] = True


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def tell(place: Place, relay: Relay, hero_name: str, hero_type: str,
         rival_name: str, rival_type: str, helper_name: str, helper_type: str) -> World:
    world = World(place, relay)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    rival = world.add(Entity(id=rival_name, kind="character", type=rival_type))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type))

    token = world.add(Entity(
        id="token",
        kind="thing",
        type="token",
        label=relay.token_label,
        phrase=relay.token_phrase,
        carrier=hero.id,
    ))
    world.facts["token"] = token

    begin_state(world, hero, rival, helper)
    world.para()
    start_relay(world)
    conflict_beats(world, hero, rival)
    kindness_beats(world, helper, hero, rival)
    problem_solving_beats(world, helper, hero, rival)
    finish_relay(world, hero, rival, helper)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a short myth-like story about a {world.relay.name} where a conflict is solved with kindness.",
        f"Tell a child-friendly tale in which {world.facts['hero'].id}, {world.facts['rival'].id}, and {world.facts['helper'].id} learn to work together during a relay.",
        f"Write a simple story set in {world.place.label} that includes a relay, a quarrel, and a clever plan.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    rival = world.facts["rival"]
    helper = world.facts["helper"]
    qa = [
        QAItem(
            question=f"Who were the runners at the center of the relay story?",
            answer=f"The story focused on {hero.id}, {rival.id}, and {helper.id}. {hero.id} and {rival.id} had the conflict, and {helper.id} used kindness and problem solving to help.",
        ),
        QAItem(
            question=f"What problem made the relay stop for a moment?",
            answer=f"The relay paused because {hero.id} and {rival.id} both wanted the opening run, so they argued and the line slowed down.",
        ),
        QAItem(
            question=f"How did the helper fix the problem?",
            answer=f"{helper.id} listened to both runners, calmed them with kindness, and suggested a new plan so the relay could continue safely.",
        ),
    ]
    if world.facts.get("token_safe"):
        qa.append(
            QAItem(
                question="What happened to the token by the end?",
                answer="The token stayed safe, moved from hand to hand, and reached the finish without being lost.",
            )
        )
    if world.facts.get("finished"):
        qa.append(
            QAItem(
                question="How did the story end?",
                answer="The relay ended with the runners working together, the token crossing the finish, and everyone cheering in the valley.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a relay race?",
            answer="A relay race is a race where one runner passes a token or baton to another runner so the team can keep going together.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means treating other people gently and helping them feel safe, heard, and cared for.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means finding a careful plan that helps fix a hard situation.",
        ),
        QAItem(
            question="Why do teams pass a token in a relay?",
            answer="Teams pass a token so each runner takes a turn and the whole group can finish the race together.",
        ),
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A relay story is valid when the place and relay are both registered.
valid_story(Place, Relay) :- place(Place), relay(Relay).

% A strong story includes a conflict, a kindness beat, and a problem-solving beat.
has_beats(Relay) :- relay(Relay), conflict(Relay), kindness(Relay), problem_solving(Relay).

% The selected world is reasonable only if the relay supports all required beats.
reasonable(Place, Relay) :- valid_story(Place, Relay), has_beats(Relay).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for rid, relay in RELAYS.items():
        lines.append(asp.fact("relay", rid))
        if "conflict" in relay.tags:
            lines.append(asp.fact("conflict", rid))
        if "kindness" in relay.tags:
            lines.append(asp.fact("kindness", rid))
        if "problem_solving" in relay.tags:
            lines.append(asp.fact("problem_solving", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show reasonable/2."))
    clingo_set = set(asp.atoms(model, "reasonable"))
    python_set = set((p, r) for p, r in valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python reasonableness gate:")
    print("  clingo:", sorted(clingo_set))
    print("  python:", sorted(python_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        place="hearth_valley",
        relay="sun_token",
        hero="Mira",
        hero_type="girl",
        rival="Korin",
        rival_type="boy",
        helper="Edda",
        helper_type="girl",
    ),
    StoryParams(
        place="stone_bridge",
        relay="river_run",
        hero="Leto",
        hero_type="boy",
        rival="Dara",
        rival_type="girl",
        helper="Hale",
        helper_type="boy",
    ),
    StoryParams(
        place="sun_gate",
        relay="moon_streak",
        hero="Suri",
        hero_type="girl",
        rival="Pax",
        rival_type="boy",
        helper="Mara",
        helper_type="girl",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld: relay, conflict, kindness, problem solving.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--relay", choices=RELAYS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--rival")
    ap.add_argument("--rival-type", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=["girl", "boy"])
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
    if args.place and args.relay:
        if (args.place, args.relay) not in valid_combos():
            raise StoryError(explain_rejection(PLACES[args.place], RELAYS[args.relay]))
    place = args.place or rng.choice(list(PLACES))
    relay = args.relay or rng.choice(list(RELAYS))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    rival_type = args.rival_type or ("boy" if hero_type == "girl" else "girl")
    helper_type = args.helper_type or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(HERO_NAMES)
    rival = args.rival or rng.choice([n for n in RIVAL_NAMES if n != hero])
    helper = args.helper or rng.choice([n for n in HELPER_NAMES if n not in {hero, rival}])
    return StoryParams(place, relay, hero, hero_type, rival, rival_type, helper, helper_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        RELAYS[params.relay],
        params.hero,
        params.hero_type,
        params.rival,
        params.rival_type,
        params.helper,
        params.helper_type,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"place: {world.place.label}")
    lines.append(f"relay: {world.relay.name}")
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.kind == "thing":
            bits.append(f"carrier={e.carrier}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"facts: {world.facts}")
    return "\n".join(lines)


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
        print(asp_program("#show reasonable/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show reasonable/2."))
        vals = sorted(set(asp.atoms(model, "reasonable")))
        print(f"{len(vals)} reasonable combos:")
        for v in vals:
            print(" ", v)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.hero} / {p.rival} / {p.helper} in {p.place} ({p.relay})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
