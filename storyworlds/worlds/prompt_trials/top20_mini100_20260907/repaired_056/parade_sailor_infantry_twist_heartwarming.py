#!/usr/bin/env python3
from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import hashlib
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402

try:
    from storyworlds.results import QAItem as _QAItem, StoryError as _StoryError, StorySample as _StorySample  # noqa: F401
except Exception:
    pass

PLACES = {
    "harbor square": {
        "setting": "Harbor Square",
        "parade": True,
        "water": True,
        "bandstand": True,
        "twist": True,
    },
    "lamplight avenue": {
        "setting": "Lamplight Avenue",
        "parade": True,
        "water": False,
        "bandstand": True,
        "twist": True,
    },
    "cobblestone quay": {
        "setting": "Cobblestone Quay",
        "parade": True,
        "water": True,
        "bandstand": False,
        "twist": True,
    },
}

CHAR_NAMES = ["Mina", "Theo", "Lina", "Owen", "Pia", "Rafi", "Nora", "Jules"]
JOBS = ["sailor", "infantry leader", "drum captain", "banner keeper", "dock helper"]
MOODS = ["gentle", "brave", "hopeful", "careful"]

TWISTS = (
    {
        "name": "borrowed boots",
        "setup": "The parade needed one more marcher, and the sailor thought the infantry would be too busy to join.",
        "turn": "The infantry were not marching away at all; they were saving polished boots for the children who had none.",
        "change": "the sailor offered a spare ribbon instead of asking for help, and the infantry smiled at the kindness",
        "result": "the whole parade moved forward with one line of bright boots for children to wear",
        "ending": "By the last drumbeat, even the smallest feet felt tall enough to keep pace.",
    },
    {
        "name": "the quiet drum",
        "setup": "The parade lanterns dimmed when a small drum went missing near the harbor steps.",
        "turn": "The sailor found the drum not lost, but tucked under an infantry coat so it would stay dry in the mist.",
        "change": "the sailor thanked the infantry for the careful trick, and the infantry asked for one song in return",
        "result": "the drum came out warm and round, and the parade marched on with a softer, safer beat",
        "ending": "The lanterns glowed on wet stones while the little drum kept time like a friendly heartbeat.",
    },
    {
        "name": "the borrowed flag",
        "setup": "A parade flag leaned toward the wind, and everyone feared it would tear before the walk began.",
        "turn": "The sailor noticed the infantry had tied the flag with a blue rope made from old parade sashes.",
        "change": "the sailor praised the clever knot, and the infantry admitted they had learned it from a patient grandmother",
        "result": "the flag stayed strong, and the parade turned the corner without a single tug",
        "ending": "Blue ribbon fluttered beside the banner while proud smiles passed from hand to hand.",
    },
    {
        "name": "the extra supper",
        "setup": "The parade ended early because a cold rain nipped at every cheek.",
        "turn": "The sailor expected the infantry to head home, but they were setting out soup for everyone under the awning.",
        "change": "the sailor carried bowls, and the infantry shared the last warm bread with the youngest marchers",
        "result": "the rainy day became a supper party, and nobody left hungry or alone",
        "ending": "Steam rose from the bowls like tiny clouds, and the parade ended in warm laughter.",
    },
    {
        "name": "the wrong trumpet call",
        "setup": "A trumpet sounded the parade start, but the line of marchers did not move.",
        "turn": "The sailor realized the infantry were waiting because the trumpet call was for the baby swans crossing the quay.",
        "change": "the sailor lowered the flag and guided the parade around the birds with a grin",
        "result": "the swans crossed safely, and the parade began after a happy pause",
        "ending": "White feathers drifted over the stones as the trumpets tried a gentler song.",
    },
    {
        "name": "the lantern twist",
        "setup": "A lantern at the front of the parade had a broken hook and hung lopsided in the breeze.",
        "turn": "The sailor expected the infantry to fetch tools, but they had already twisted a strip of cloth into a snug new hanger.",
        "change": "the sailor learned the quick fix, and the infantry taught the knot to three delighted children",
        "result": "the lantern rode straight and bright above the moving crowd",
        "ending": "Its warm circle of light skipped down the street like a patient star.",
    },
)

ASP_RULES = r"""
place(harbor_square).
place(lamplight_avenue).
place(cobblestone_quay).

feature(parade).
feature(sailor).
feature(infantry).
feature(twist).
feature(heartwarming).

compatible(P, parade) :- place(P).
compatible(P, sailor) :- place(P).
compatible(P, infantry) :- place(P).
compatible(P, twist) :- place(P).
compatible_story(P) :- compatible(P, parade), compatible(P, sailor), compatible(P, infantry), compatible(P, twist).

#show compatible/2.
#show compatible_story/1.
"""


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    carried_by: Optional[str] = None
    location: Optional[str] = None


@dataclass
class StoryParams:
    place: str
    hero: str
    ally: str
    mood: str
    seed: Optional[int] = None


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    trace: list[str] = field(default_factory=list)

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming parade storyworld about a sailor, infantry, and a twist.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
    if not PLACES[place]["parade"]:
        raise StoryError("This storyworld needs a place where a parade can happen.")
    hero = rng.choice(CHAR_NAMES)
    ally = rng.choice([n for n in CHAR_NAMES if n != hero])
    mood = rng.choice(MOODS)
    return StoryParams(place=place, hero=hero, ally=ally, mood=mood)


def _story_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    s = "|".join((params.place, params.hero, params.ally, params.mood))
    return int.from_bytes(hashlib.blake2b(s.encode("utf-8"), digest_size=8).digest(), "big")


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(asp.fact("place", k.replace(" ", "_")) for k in PLACES)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    py = {(k.replace(" ", "_"), "parade") for k in PLACES}
    py |= {(k.replace(" ", "_"), "sailor") for k in PLACES}
    py |= {(k.replace(" ", "_"), "infantry") for k in PLACES}
    py |= {(k.replace(" ", "_"), "twist") for k in PLACES}
    model = asp.one_model(asp_program("#show compatible/2.\n#show compatible_story/1."))
    cl = set(asp.atoms(model, "compatible"))
    if py != cl:
        print("MISMATCH")
        print("only in python:", sorted(py - cl))
        print("only in clingo:", sorted(cl - py))
        return 1
    print(f"OK: clingo gate matches Python reasoning ({len(cl)} facts).")
    return 0


def generate(params: StoryParams) -> StorySample:
    import storyworlds.asp as asp
    meta = PLACES[params.place]
    seed = _story_seed(params)
    rng = random.Random(seed)
    twist = TWISTS[seed % len(TWISTS)]
    world = World(place=meta["setting"])
    sailor = Entity(id=params.hero, kind="character", label="sailor", meters={"hope": 1.0}, memes={"kindness": 1.0}, location=params.place)
    infantry = Entity(id=params.ally, kind="character", label="infantry", meters={"hope": 0.9}, memes={"kindness": 1.0}, location=params.place)
    banner = Entity(id="banner", kind="object", label="parade banner", meters={"height": 2.0}, memes={"bright": 1.0}, location=params.place)
    drum = Entity(id="drum", kind="object", label="little drum", meters={"size": 0.4}, memes={"warm": 1.0}, location=params.place)
    world.entities = {e.id: e for e in (sailor, infantry, banner, drum)}

    opening = f"It was parade day in {world.place}, and {params.hero}, a sailor, walked beside {params.ally}, who served in the infantry."
    world.say(opening)
    world.say(f"They were both {params.mood}, because a parade is easier when two friends keep step together.")
    world.say(twist["setup"])
    world.para()
    world.say(f"'{params.hero},' said {params.ally}, 'the parade can still be lovely if we stay gentle with one another.'")
    world.say(f"'{params.ally},' replied {params.hero}, 'Then let's find the kindest way forward.'")
    world.say("That soft promise changed how they looked at the problem.")

    world.para()
    world.say(f"The twist was simple and sweet: {twist['turn']}.")
    world.say(f"When {params.hero} looked again, the real worry became clear, and {params.ally} helped without boasting.")
    world.say(f"Together they {twist['change']}, which made the whole street feel calmer.")
    world.say(f"The parade did not need a grand rescue; it needed patience, and that was just what they had.")

    world.para()
    world.say(f"Then {twist['result']}.")
    world.say(f"People cheered, not because anything had been flashy, but because everyone had been cared for.")
    world.say(f"{params.hero} and {params.ally} smiled at each other, proud of the gentle twist that turned worry into welcome.")
    world.say(twist["ending"])

    sailor.meters["hope"] = 1.4
    infantry.meters["hope"] = 1.3
    sailor.memes["grateful"] = 1.0
    infantry.memes["grateful"] = 1.0
    banner.memes["safe"] = 1.0
    drum.memes["heard_with_love"] = 1.0
    world.trace = [
        f"place:{params.place}",
        f"setup:{twist['setup']}",
        f"twist:{twist['turn']}",
        f"result:{twist['result']}",
    ]

    prompts = [
        f"Write a heartwarming parade story set in {meta['setting']} with a sailor, infantry, and a twist.",
        f"Show how {params.hero} and {params.ally} speak kindly and change what they decide to do.",
        f"Tell a gentle story where the parade ends with people feeling safer and closer together.",
    ]

    story_qa = [
        QAItem(
            question=f"Who were the two main friends in the story?",
            answer=f"The main friends were {params.hero}, the sailor, and {params.ally}, who served in the infantry.",
        ),
        QAItem(
            question="What made the story twisty?",
            answer=f"The twist was that {twist['turn']}",
        ),
        QAItem(
            question="How did they respond to the problem?",
            answer=f"They answered with kindness: {twist['change']}.",
        ),
        QAItem(
            question="How did the parade end?",
            answer=f"{twist['result']} That left the street feeling warm and happy.",
        ),
    ]

    world_qa = [
        QAItem(question="What is a parade?", answer="A parade is a happy public walk or celebration where people move together in an organized way."),
        QAItem(question="What is a sailor?", answer="A sailor is a person who works on the water and knows how to travel by boat or ship."),
        QAItem(question="What is infantry?", answer="Infantry are soldiers who move and work on foot."),
    ]

    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world trace ---")
        for e in sample.world.entities.values():
            print(f"  {e.id}: {e.kind} label={e.label} meters={e.meters} memes={e.memes} location={e.location}")
    if qa:
        print()
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


CURATED = [
    StoryParams(place="harbor square", hero="Mina", ally="Theo", mood="hopeful"),
    StoryParams(place="lamplight avenue", hero="Lina", ally="Owen", mood="gentle"),
    StoryParams(place="cobblestone quay", hero="Pia", ally="Rafi", mood="careful"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show compatible_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show compatible/2.\n#show compatible_story/1."))
        print(asp.atoms(model, "compatible"))
        print(asp.atoms(model, "compatible_story"))
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < args.n * 20:
            i += 1
            params = resolve_params(args, random.Random((args.seed or 0) + i))
            params.seed = (args.seed or 0) + i
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
