#!/usr/bin/env python3
"""
storyworlds/worlds/pit_incinerator_analyze_petting_zoo_rhyme_tall.py
=====================================================================

A tiny standalone story world for a tall-tale, rhyming petting-zoo story
about a child who has to analyze a pit and choose a safe way to use an
incinerator without frightening the animals.

Seed tale sketch:
---
At a petting zoo, a tall, merry kid named June found a strange pit behind the
feed shed. The goats kept peeking at it, the donkey kept braying at it, and
the whole place felt uneasy. June wanted to analyze the pit, but the keeper
warned that no one should lean in too far or toss the wrong things into the
incinerator. After June and the keeper rhymed their way through a careful
look, they found the pit was only full of old soggy straw, and the incinerator
could safely handle the spoiled scraps that needed burning. The animals settled,
the rhyme grew bright, and the zoo became calm again.

This file models that premise with physical meters and emotional memes:
- a pit can be deep and risky
- an incinerator can safely destroy only the right kind of trash
- analyzing the pit raises understanding but can also raise fear if done
  carelessly
- a careful helper can turn worry into relief with a safe rhyme-led plan
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    in_pit: bool = False
    near_incinerator: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the petting zoo"
    has_pit: bool = True
    has_incinerator: bool = True
    has_choir: bool = True


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    animal: str
    rhyme_style: str = "tall"
    seed: Optional[int] = None


ANIMALS = {
    "goat": {"type": "goat", "label": "goat", "sound": "baa"},
    "donkey": {"type": "donkey", "label": "donkey", "sound": "hee-haw"},
    "pony": {"type": "pony", "label": "pony", "sound": "neigh"},
    "lamb": {"type": "lamb", "label": "lamb", "sound": "baa"},
}

HEROES = [
    ("June", "girl"),
    ("Milo", "boy"),
    ("Ada", "girl"),
    ("Beck", "boy"),
    ("Nell", "girl"),
]

HELPERS = [
    ("Nora", "woman"),
    ("Otto", "man"),
    ("Mara", "woman"),
    ("Bram", "man"),
]

RHYMES = [
    ("high", "sky"),
    ("bright", "night"),
    ("wide", "side"),
    ("neat", "feet"),
    ("low", "glow"),
]


def rhyme_line(a: str, b: str) -> str:
    return f"{a} and {b}, a tall-tale pair."


def reasonableness_gate(params: StoryParams) -> None:
    if params.animal not in ANIMALS:
        raise StoryError("Unknown animal.")
    if params.rhyme_style != "tall":
        raise StoryError("This world is tuned for a tall-tale rhyme style.")
    if not params.hero_name or not params.helper_name:
        raise StoryError("Hero and helper names are required.")


def predict(world: World, hero: Entity, helper: Entity, animal: Entity) -> dict:
    sim = world.copy()
    h = sim.get(hero.id)
    a = sim.get(animal.id)
    h.memes["curiosity"] = h.memes.get("curiosity", 0) + 1
    h.memes["analysis"] = h.memes.get("analysis", 0) + 1
    a.memes["unease"] = a.memes.get("unease", 0) + 0.5
    pit = sim.get("pit")
    if h.meters.get("careless", 0) >= THRESHOLD:
        pit.meters["risk"] = pit.meters.get("risk", 0) + 1
        a.memes["fear"] = a.memes.get("fear", 0) + 1
    return {
        "pit_risky": pit.meters.get("risk", 0) >= THRESHOLD,
        "animal_frightened": a.memes.get("fear", 0) >= THRESHOLD,
    }


def setup_world(params: StoryParams) -> World:
    world = World(Setting())
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper_name))
    animal = world.add(Entity(id="animal", kind="character", type=ANIMALS[params.animal]["type"], label=params.animal))
    pit = world.add(Entity(id="pit", type="pit", label="pit"))
    inc = world.add(Entity(id="incinerator", type="incinerator", label="incinerator"))
    scraps = world.add(Entity(id="scraps", type="scraps", label="old soggy straw", plural=True, caretaker="helper"))
    world.facts.update(hero=hero, helper=helper, animal=animal, pit=pit, inc=inc, scraps=scraps, params=params)
    return world


def tell(params: StoryParams) -> World:
    reasonableness_gate(params)
    world = setup_world(params)
    hero = world.get("hero")
    helper = world.get("helper")
    animal = world.get("animal")
    pit = world.get("pit")
    inc = world.get("incinerator")
    scraps = world.get("scraps")

    world.say(
        f"At the petting zoo, {hero.label} was a {hero.type} with a tall-tale grin "
        f"and a voice that could rhyme with the wind."
    )
    world.say(
        f" {hero.label} loved to look, to learn, and to analyze every curious corner, "
        f"especially when the animals gathered round."
    )
    world.say(
        f"The {animal.label} kept peeking, and the keeper said, "
        f"\"Mind the pit, little one, and keep your feet from the ditch.\""
    )
    world.para()
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    world.say(
        f"{hero.label} leaned near the edge to analyze the pit, and the zoo went hush-hush "
        f"as a drumbeat in a thundercloud."
    )
    hero.meters["careless"] = 1
    pred = predict(world, hero, helper, animal)
    if pred["pit_risky"]:
        pit.meters["risk"] = pit.meters.get("risk", 0) + 1
        animal.memes["fear"] = animal.memes.get("fear", 0) + 1
        world.say(
            f"The pit looked deeper than a horse could hop, and the {animal.label} "
            f"made a nervous little sound: \"{ANIMALS[params.animal]['sound']}!\""
        )
        world.say(
            f"{helper.label} said, \"First we look with care, then we tell what we know; "
            f"a clever rhyme is safer than a careless show.\""
        )
    world.para()

    helper.memes["calm"] = helper.memes.get("calm", 0) + 1
    world.say(
        f"So {hero.label} and {helper.label} walked side by side, slow as snails and proud as kings, "
        f"and they rhymed their way around the place."
    )
    world.say(
        rhyme_line("high", "sky") + " "
        f"They kept to the side, peered in with a stick, and saw the pit was only full of old straw and scraps."
    )

    if scraps.label:
        scraps.in_pit = False
    hero.memes["understanding"] = hero.memes.get("understanding", 0) + 1
    world.say(
        f"That was the trick of it: the pit was not a monster at all, just a muddy pocket for broken bits, "
        f"and the trouble was nothing but worry wearing big boots."
    )

    world.para()
    world.say(
        f"{helper.label} pointed to the incinerator and said, \"Only the spoiled scraps may go there, "
        f"and only with a safe hand.\""
    )
    if world.setting.has_incinerator:
        scraps.near_incinerator = True
        scraps.meters["burn"] = 1
        world.say(
            f"So they carried the old soggy straw to the incinerator, and it vanished in a puff "
            f"that smelled like a finished storm."
        )
        world.say(
            f"The animals blinked, the keeper nodded, and the pit stayed a pit while the scrap was gone."
        )

    animal.memes["fear"] = max(0.0, animal.memes.get("fear", 0) - 1)
    animal.memes["relief"] = animal.memes.get("relief", 0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    helper.memes["joy"] = helper.memes.get("joy", 0) + 1

    world.para()
    world.say(
        f"In the end, {hero.label} stood by the quiet pit, the {animal.label} munched hay, "
        f"and {helper.label} laughed a low, warm laugh."
    )
    world.say(
        f"The zoo felt brave and bright, and the rhyme of the day was simple and true: "
        f"analyze with care, and the whole wide world can settle."
    )

    world.facts.update(pred=pred)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    animal = world.facts["animal"].label
    return [
        f"Write a tall-tale rhyme set at a petting zoo where {p.hero_name} must analyze a pit.",
        f"Tell a child-friendly story about {p.hero_name}, a {animal}, and a safe incinerator.",
        f"Write a rhyming petting-zoo tale in which a curious hero studies a pit without causing trouble.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    animal = f["animal"]
    pred = f["pred"]
    return [
        QAItem(
            question=f"Where did {hero.label} have to analyze the strange pit?",
            answer=f"{hero.label} had to analyze it at the petting zoo, where the animals were already peeking and worrying.",
        ),
        QAItem(
            question=f"Who helped {hero.label} stay careful near the pit?",
            answer=f"{helper.label} helped {hero.label} stay careful and said to look with care before making any big move.",
        ),
        QAItem(
            question=f"Why did the {animal.label} act nervous at first?",
            answer=f"The {animal.label} acted nervous because the pit looked deep and strange, so the animal thought something risky might happen.",
        ),
    ] + [
        QAItem(
            question="What did they learn after looking more carefully?",
            answer="They learned the pit was only full of old straw and scraps, not a monster or a mystery that could hurt anyone.",
        ),
        QAItem(
            question="What happened to the spoiled scraps?",
            answer="The spoiled scraps went to the incinerator, where they could be destroyed safely instead of left to rot.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pit?",
            answer="A pit is a hole or hollow place in the ground. People need to be careful around a pit because it can be deep.",
        ),
        QAItem(
            question="What is an incinerator for?",
            answer="An incinerator is a machine or furnace that burns trash or scraps at very high heat so they are destroyed safely.",
        ),
        QAItem(
            question="What does analyze mean?",
            answer="To analyze something means to study it carefully and think about what it is and what it means.",
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.in_pit:
            bits.append("in_pit=True")
        if e.near_incinerator:
            bits.append("near_incinerator=True")
        lines.append(f"  {e.id:11} ({e.type:12}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(hero_name="June", hero_type="girl", helper_name="Nora", helper_type="woman", animal="goat", rhyme_style="tall"),
    StoryParams(hero_name="Milo", hero_type="boy", helper_name="Otto", helper_type="man", animal="donkey", rhyme_style="tall"),
    StoryParams(hero_name="Ada", hero_type="girl", helper_name="Mara", helper_type="woman", animal="pony", rhyme_style="tall"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale rhyme story world: petting zoo, pit, incinerator, analyze.")
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["woman", "man"])
    ap.add_argument("--animal", choices=sorted(ANIMALS))
    ap.add_argument("--rhyme-style", choices=["tall"], default="tall")
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
    hero_name, hero_type = (args.hero_name, args.hero_type) if args.hero_name and args.hero_type else rng.choice(HEROES)
    helper_name, helper_type = (args.helper_name, args.helper_type) if args.helper_name and args.helper_type else rng.choice(HELPERS)
    animal = args.animal or rng.choice(list(ANIMALS))
    return StoryParams(
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
        animal=animal,
        rhyme_style=args.rhyme_style,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


ASP_RULES = r"""
has_pit.
has_incinerator.
can_analyze(hero).
risky_when_near_pit(hero) :- analyze(hero), has_pit.
safe_burn(scraps) :- has_incinerator, scraps_spoiled(scraps).
resolved :- risky_when_near_pit(hero), safe_burn(scraps).
#show resolved/0.
#show risky_when_near_pit/1.
#show safe_burn/1.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("has_pit"),
        asp.fact("has_incinerator"),
        asp.fact("can_analyze", "hero"),
        asp.fact("analyze", "hero"),
        asp.fact("scraps_spoiled", "scraps"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolved/0."))
    atoms = {sym.name for sym in model}
    if "resolved" in atoms:
        print("OK: ASP model confirms the safe resolution.")
        return 0
    print("MISMATCH: ASP model did not resolve.")
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show resolved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

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
            header = f"### {p.hero_name} and the {p.animal} at the petting zoo"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
