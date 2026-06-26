#!/usr/bin/env python3
"""
A tiny bedtime-story world about a mammal, a barber, a mystery to solve,
and a kind, funny help that makes the ending feel warm and safe.
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


@dataclass
class Character:
    id: str
    kind: str = "character"
    species: str = "mammal"
    role: str = ""
    label: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: {"movement": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"curiosity": 0.0, "kindness": 0.0, "humor": 0.0})

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def title(self) -> str:
        return self.label or self.role or self.id


@dataclass
class Place:
    id: str
    label: str
    calm: bool = True
    has_chair: bool = True
    has_mirror: bool = True
    has_clippers: bool = True
    has_combing_cape: bool = True


@dataclass
class Mystery:
    id: str
    label: str
    clue: str
    reveal: str
    harmless: bool = True
    funny: bool = True


@dataclass
class KindnessTool:
    id: str
    label: str
    action: str
    result: str


@dataclass
class HumorBeat:
    id: str
    label: str
    line: str


@dataclass
class StoryParams:
    place: str
    mystery: str
    helper: str
    hero_name: str
    barber_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, object] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


PLACES = {
    "quiet_shop": Place(id="quiet_shop", label="the little barber shop", calm=True),
    "moonroom": Place(id="moonroom", label="the moonlit trimming room", calm=True),
    "window_shop": Place(id="window_shop", label="the shop by the soft window", calm=True),
}

MYSTERIES = {
    "lost_combs": Mystery(
        id="lost_combs",
        label="the mystery of the missing combs",
        clue="the combs kept vanishing from the counter",
        reveal="the combs had rolled into a basket under the chair",
    ),
    "snip_sound": Mystery(
        id="snip_sound",
        label="the mystery of the snipping sound",
        clue="a tiny snip-snip sound came from behind the curtain",
        reveal="a wind-up toy was tapping its tin scissors together",
    ),
    "curl_shadow": Mystery(
        id="curl_shadow",
        label="the mystery of the curly shadow",
        clue="a curly shadow kept dancing over the floor",
        reveal="the shadow came from a hanging ribbon spinning near the lamp",
    ),
}

HELPERS = {
    "gentle_rinse": KindnessTool(
        id="gentle_rinse",
        label="a warm, gentle rinse",
        action="used it to soften the tangles",
        result="the fur settled smooth and neat",
    ),
    "soft_brush": KindnessTool(
        id="soft_brush",
        label="a soft brush",
        action="brushed in little circles",
        result="the knots loosened without any pulling",
    ),
    "quiet_breath": KindnessTool(
        id="quiet_breath",
        label="a quiet breathing game",
        action="took slow breaths together",
        result="the whole room felt calmer",
    ),
}

HUMOR = {
    "moustache_tickles": HumorBeat(
        id="moustache_tickles",
        label="the tickly moustache",
        line="the barber's moustache bounced once and made the hero giggle",
    ),
    "chair_squeak": HumorBeat(
        id="chair_squeak",
        label="the squeaky chair",
        line="the chair gave a tiny squeak, as if it were clearing its own throat",
    ),
    "cap_bloop": HumorBeat(
        id="cap_bloop",
        label="the cap bloop",
        line="the cape swished with a soft bloop and looked like a cape in a fairy tale",
    ),
}

NAMES = ["Milo", "Nora", "Pip", "Luna", "Toby", "Cora", "Junie", "Benny", "Rae", "Otis"]
BARBER_NAMES = ["Mr. Finch", "Mrs. Wren", "Auntie Dot", "Mr. Bell"]
TRAITS = ["curious", "gentle", "brave", "sleepy", "kind", "playful"]


def is_reasonable(place: Place, mystery: Mystery, helper: KindnessTool, humor: HumorBeat) -> bool:
    return place.calm and mystery.harmless and mystery.funny and helper.action and humor.line


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pid, place in PLACES.items():
        for mid, mystery in MYSTERIES.items():
            for hid, helper in HELPERS.items():
                if is_reasonable(place, mystery, helper, HUMOR["chair_squeak"]):
                    out.append((pid, mid, hid))
    return out


def explain_rejection() -> str:
    return "(No story: this world only tells a calm mystery where the clue is harmless and the solution can be kind and funny.)"


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    mystery = MYSTERIES[params.mystery]
    helper = HELPERS[params.helper]
    world = World(place)
    hero = world.add(Character(id=params.hero_name, role="mammal", label="little mammal", traits=[random.choice(TRAITS)]))
    barber = world.add(Character(id=params.barber_name, role="barber", label="the barber", traits=["kind", "steady"]))
    world.facts.update(hero=hero, barber=barber, mystery=mystery, helper=helper, place=place)
    return world


def intro(world: World) -> None:
    hero: Character = world.facts["hero"]
    barber: Character = world.facts["barber"]
    world.say(
        f"{hero.id} was a little mammal who loved bedtime stories, warm lamps, and the quiet clink of scissors at {world.place.label}."
    )
    world.say(
        f"The barber, {barber.id}, smiled at {hero.id} with kind eyes and said the shop was ready for a gentle trim."
    )


def mystery_setup(world: World) -> None:
    mystery: Mystery = world.facts["mystery"]
    hero: Character = world.facts["hero"]
    barber: Character = world.facts["barber"]
    hero.memes["curiosity"] += 1
    world.para()
    world.say(f"Then a small mystery arrived: {mystery.clue}.")
    world.say(
        f"{hero.id} leaned closer, and {barber.id} said, 'Let's solve it slowly, like a tiny bedtime puzzle.'"
    )


def kindness_turn(world: World) -> None:
    helper: KindnessTool = world.facts["helper"]
    hero: Character = world.facts["hero"]
    barber: Character = world.facts["barber"]
    hero.memes["kindness"] += 1
    world.para()
    world.say(
        f"{barber.id} reached for {helper.label} and {helper.action}, because a kind mystery should never feel scary."
    )
    world.say(
        f"With that gentle help, {helper.result}, and {hero.id} felt safe enough to keep looking."
    )


def humor_turn(world: World) -> None:
    beat: HumorBeat = random.choice(list(HUMOR.values()))
    hero: Character = world.facts["hero"]
    barber: Character = world.facts["barber"]
    hero.memes["humor"] += 1
    world.say(f"To keep things light, {beat.line}.")
    world.say(
        f"{hero.id} laughed so softly that {barber.id} had to smile too, and the whole shop felt cozy as a blanket."
    )


def solve_mystery(world: World) -> None:
    mystery: Mystery = world.facts["mystery"]
    hero: Character = world.facts["hero"]
    barber: Character = world.facts["barber"]
    world.para()
    world.say(
        f"At last, they found the answer: {mystery.reveal}."
    )
    world.say(
        f"{hero.id} pointed it out, and {barber.id} nodded as if the little puzzle had been waiting all along for a patient pair of eyes."
    )


def ending(world: World) -> None:
    hero: Character = world.facts["hero"]
    barber: Character = world.facts["barber"]
    world.para()
    world.say(
        f"After the mystery was solved, {barber.id} gave {hero.id} a neat trim, and {hero.id}'s heart felt light and sleepy."
    )
    world.say(
        f"The shop was quiet again, the combs were safe, and {hero.id} left with a smile that looked ready for dreams."
    )


def tell_story(params: StoryParams) -> World:
    world = build_world(params)
    intro(world)
    mystery_setup(world)
    kindness_turn(world)
    humor_turn(world)
    solve_mystery(world)
    ending(world)
    return world


def generation_prompts(world: World) -> list[str]:
    hero: Character = world.facts["hero"]
    mystery: Mystery = world.facts["mystery"]
    helper: KindnessTool = world.facts["helper"]
    place: Place = world.facts["place"]
    return [
        f"Write a bedtime story about a little mammal in {place.label} who helps solve {mystery.label}.",
        f"Tell a gentle story with a barber, a mystery, kindness, and a small funny moment for {hero.id}.",
        f"Create a calm story where {hero.id} and the barber use {helper.label} to solve a harmless mystery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Character = world.facts["hero"]
    barber: Character = world.facts["barber"]
    mystery: Mystery = world.facts["mystery"]
    helper: KindnessTool = world.facts["helper"]
    place: Place = world.facts["place"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a little mammal, and {barber.id}, the barber, at {place.label}.",
        ),
        QAItem(
            question=f"What mystery did they try to solve?",
            answer=f"They tried to solve {mystery.label}, because something small and puzzling needed a calm answer.",
        ),
        QAItem(
            question=f"What kind thing helped the story feel safe?",
            answer=f"{helper.label} helped, because {helper.action} and made the search feel gentle.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the mystery solved, a neat haircut, and {hero.id} leaving sleepy and happy.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a barber?",
            answer="A barber is a person who cuts hair and helps keep people looking neat.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling that people try to understand or solve.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, helpful, and caring toward someone else.",
        ),
        QAItem(
            question="Why can humor help in a hard moment?",
            answer="Humor can make a hard moment feel lighter, because a small laugh can help people relax.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Story questions ==",]
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        if isinstance(ent, Character):
            lines.append(
                f"  {ent.id}: role={ent.role}, traits={ent.traits}, meters={ent.meters}, memes={ent.memes}"
            )
    return "\n".join(lines)


@dataclass
class ASPStub:
    pass


ASP_RULES = r"""
% Calm bedtime story rules.

mystery_exists(M) :- mystery(M).
kind_help(H) :- helper(H).
funny_beat(B) :- humor(B).

reasonable_story(P, M, H) :- place(P), mystery_exists(M), kind_help(H).
solves(P, M) :- reasonable_story(P, M, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    for bid in HUMOR:
        lines.append(asp.fact("humor", bid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonable_story/3."))
    return sorted(set(asp.atoms(model, "reasonable_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    lp = set(asp_reasonable())
    if py == lp:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - lp:
        print("  only in python:", sorted(py - lp))
    if lp - py:
        print("  only in ASP:", sorted(lp - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime-story world: a mammal, a barber, and a harmless mystery.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--hero-name", dest="hero_name")
    ap.add_argument("--barber-name", dest="barber_name")
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
    if args.place and args.mystery and args.helper:
        if not is_reasonable(PLACES[args.place], MYSTERIES[args.mystery], HELPERS[args.helper], list(HUMOR.values())[0]):
            raise StoryError(explain_rejection())
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.mystery is None or c[1] == args.mystery)
        and (args.helper is None or c[2] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid story matches those options.)")
    place, mystery, helper = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        mystery=mystery,
        helper=helper,
        hero_name=args.hero_name or rng.choice(NAMES),
        barber_name=args.barber_name or rng.choice(BARBER_NAMES),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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


CURATED = [
    StoryParams(place="quiet_shop", mystery="lost_combs", helper="soft_brush", hero_name="Milo", barber_name="Mr. Finch"),
    StoryParams(place="moonroom", mystery="snip_sound", helper="quiet_breath", hero_name="Luna", barber_name="Mrs. Wren"),
    StoryParams(place="window_shop", mystery="curl_shadow", helper="gentle_rinse", hero_name="Pip", barber_name="Auntie Dot"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reasonable_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_reasonable()
        print(f"{len(triples)} reasonable story combos:\n")
        for t in triples:
            print("  ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
