#!/usr/bin/env python3
"""
A tiny ghost-story world about a curious child, a chilly aft deck, and a
temperature change that turns a spooky night into a brave discovery.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Place:
    name: str
    kind: str
    temperature: int
    aft: bool = False
    eerie: bool = False


@dataclass
class Item:
    name: str
    kind: str
    carried_by: Optional[str] = None
    warm: bool = False


@dataclass
class Character:
    name: str
    role: str
    curiosity: int = 0
    brave: int = 0
    chilly: int = 0
    comfort: int = 0
    meters: dict[str, int] = field(default_factory=dict)
    memes: dict[str, int] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    place: Place
    hero: Character
    ghost: Character
    lantern: Item
    blanket: Item
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    place: str
    temperature: int
    name: str
    seed: Optional[int] = None


PLACES = {
    "old_house": Place(name="the old house", kind="house", temperature=12, aft=False, eerie=True),
    "harbor": Place(name="the harbor dock", kind="dock", temperature=8, aft=True, eerie=True),
    "boat": Place(name="the little boat", kind="boat", temperature=6, aft=True, eerie=True),
    "attic": Place(name="the attic", kind="room", temperature=10, aft=False, eerie=True),
}

NAMES = ["Mina", "Ivy", "Noa", "Sage", "Lena", "Tess"]
GHOST_NAMES = ["Murmur", "Pale Finn", "Whisper", "Old Nettle"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small ghost-story world about curiosity and temperature.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--temperature", type=int)
    ap.add_argument("--name")
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
    place_key = args.place or rng.choice(list(PLACES))
    place = PLACES[place_key]
    temperature = args.temperature if args.temperature is not None else place.temperature + rng.choice([-2, -1, 0, 1, 2])
    name = args.name or rng.choice(NAMES)
    if not (0 <= temperature <= 30):
        raise StoryError("Temperature must stay in a child-friendly, believable range.")
    return StoryParams(place=place_key, temperature=temperature, name=name)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for k, p in PLACES.items():
        lines.append(asp.fact("place", k))
        if p.aft:
            lines.append(asp.fact("aft_place", k))
        if p.eerie:
            lines.append(asp.fact("eerie_place", k))
        lines.append(asp.fact("base_temp", k, p.temperature))
    return "\n".join(lines)


ASP_RULES = r"""
#show cold/1.
#show story_place/1.

cold(P) :- base_temp(P,T), T < 10.
story_place(P) :- place(P).
story_place(P) :- aft_place(P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show cold/1."))
    cold_places = {p[0] for p in asp.atoms(model, "cold")}
    py = {k for k, p in PLACES.items() if p.temperature < 10}
    if cold_places == py:
        print(f"OK: ASP matches Python cold-place gate ({len(py)} places).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("ASP:", sorted(cold_places))
    print("Python:", sorted(py))
    return 1


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    hero = Character(name=params.name, role="child")
    ghost = Character(name=GHOST_NAMES[hash((params.name, params.place, params.temperature)) % len(GHOST_NAMES)], role="ghost")
    lantern = Item(name="lantern", kind="lantern", warm=True)
    blanket = Item(name="blanket", kind="blanket", warm=True)
    world = World(place=place, hero=hero, ghost=ghost, lantern=lantern, blanket=blanket)
    world.facts["temperature"] = params.temperature
    world.facts["aft"] = place.aft
    world.facts["curiosity"] = 1

    hero.curiosity = 1
    hero.brave = 0
    hero.chilly = 1 if params.temperature < 12 else 0
    hero.comfort = 0

    world.say(f"{hero.name} loved stories about ghosts, and {hero.pronoun('possessive')} curiosity always led {hero.pronoun('object')} toward strange corners.")
    if place.aft:
        world.say(f"One evening, {hero.name} walked aft, where the wind felt sharper and the boards creaked like old whispers.")
    else:
        world.say(f"One evening, {hero.name} crept into {place.name}, where the air was still and a little spooky.")
    world.para()
    world.say(f"The temperature had dropped to {params.temperature} degrees, and {hero.name} hugged {hero.pronoun('possessive')} arms as a pale shape shimmered nearby.")
    world.say(f"It was only {ghost.name}, a shy ghost who liked to drift by the lantern glow and listen.")
    world.say(f"{ghost.name} asked, 'Why are you here?' and {hero.name} answered, 'I wanted to see what made the night feel so cold.'")
    hero.curiosity += 1
    hero.chilly += 1
    world.para()
    if params.temperature < 10:
        world.say(f"{ghost.name} nodded and pointed at the draft. 'The wind comes through the aft side,' the ghost said. 'That's what lowers the temperature.'")
    else:
        world.say(f"{ghost.name} smiled. 'This night isn't very cold,' the ghost said, 'but the shadows make it feel colder than it is.'")
    world.say(f"{hero.name} held up the lantern, and the little glow made the ghost look kinder than scary.")
    world.say(f"Then {hero.name} shared the blanket, and the cold feeling eased from {hero.pronoun('possessive')} shoulders.")
    hero.comfort += 1
    hero.brave += 1
    world.para()
    world.say(f"At the end, {hero.name} was no longer just curious; {hero.pronoun()} was brave enough to laugh with {ghost.name} in the softly lit dark.")
    world.say(f"The aft wind still blew, but now it sounded like a sleepy song instead of a warning.")
    world.facts.update(hero=hero, ghost=ghost, place=place, lantern=lantern, blanket=blanket)

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    p = world.facts["place"]
    return [
        f"Write a child-friendly ghost story set in {p.name} with a chilly temperature and a curious child.",
        f"Tell a short spooky-but-gentle story where curiosity leads a child aft and they learn why the temperature feels cold.",
        f"Write a story about a ghost, a lantern, and a blanket that turns fear into friendship.",
    ]


def story_qa(world: World) -> list[QAItem]:
    h = world.facts["hero"]
    g = world.facts["ghost"]
    p = world.facts["place"]
    t = world.facts["temperature"]
    qa = [
        QAItem(
            question=f"Where did {h.name} go to look for the ghost?",
            answer=f"{h.name} went to {p.name}. It was an eerie place, and if it was aft, the wind made it feel even stranger.",
        ),
        QAItem(
            question=f"Why did {h.name} feel chilly on the night with {g.name}?",
            answer=f"{h.name} felt chilly because the temperature had dropped to {t} degrees, and the wind and shadows made the night feel colder.",
        ),
        QAItem(
            question=f"What helped {h.name} feel braver near the ghost?",
            answer=f"A lantern and a warm blanket helped {h.name} feel safer. The light made {g.name} look gentle, and the blanket chased away the chill.",
        ),
    ]
    if p.aft:
        qa.append(QAItem(
            question=f"What did the word aft mean in this story?",
            answer=f"Aft meant the back part of the boat or dock area. That was where the wind could slip through and make the temperature feel lower.",
        ))
    return qa


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a lantern do?",
            answer="A lantern gives off light, so people can see in the dark and feel less afraid.",
        ),
        QAItem(
            question="Why can a blanket help when it is cold?",
            answer="A blanket helps keep warmth close to the body, so a person feels more comfortable when the temperature is low.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to know more about something. A curious child asks questions and looks closely at new things.",
        ),
        QAItem(
            question="What is a ghost in a story like this?",
            answer="In a gentle story, a ghost is a spooky-looking figure that can still be kind, shy, or lonely.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Story questions =="]
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
    for e in [world.hero, world.ghost]:
        lines.append(f"{e.role}: {e.name} curiosity={e.curiosity} brave={e.brave} chilly={e.chilly} comfort={e.comfort}")
    lines.append(f"place: {world.place.name} kind={world.place.kind} temperature={world.place.temperature} aft={world.place.aft}")
    lines.append(f"items: lantern={asdict(world.lantern)} blanket={asdict(world.blanket)}")
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


def resolve_all() -> list[StoryParams]:
    return [
        StoryParams(place="harbor", temperature=7, name="Mina"),
        StoryParams(place="boat", temperature=5, name="Ivy"),
        StoryParams(place="old_house", temperature=9, name="Noa"),
        StoryParams(place="attic", temperature=11, name="Sage"),
    ]


def build_story_samples(args: argparse.Namespace) -> list[StorySample]:
    if args.all:
        return [generate(p) for p in resolve_all()]
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    seen: set[str] = set()
    i = 0
    while len(samples) < args.n and i < max(50, args.n * 20):
        rng = random.Random(base_seed + i)
        i += 1
        try:
            params = resolve_params(args, rng)
        except StoryError as err:
            print(err)
            break
        params.seed = base_seed + i
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    return samples


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show story_place/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show story_place/1. #show cold/1."))
        places = sorted(set(asp.atoms(model, "story_place")))
        cold = sorted(set(asp.atoms(model, "cold")))
        print(f"{len(places)} places, {len(cold)} cold places")
        for p in places:
            tag = "cold" if (p[0],) in cold else "warm"
            print(f"  {p[0]}: {tag}")
        return

    samples = build_story_samples(args)
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
            header = f"### {p.name} at {p.place} (temperature={p.temperature})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
