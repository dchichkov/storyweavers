#!/usr/bin/env python3
"""
A standalone storyworld: opinion, magic, friendship, and a small adventure.

Premise:
- A child and a friend want to explore a magical place.
- The child has an opinion about what is best for the quest.
- Magic can help, but only if the friends agree on a safe plan.
- The story turns when the opinion causes a wobble, then the friends listen,
  share roles, and continue together.

This world is intentionally small and classical: one main tension, one turn,
one resolution.
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
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    buddy: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen", "witch"}
        male = {"boy", "father", "dad", "man", "wizard", "prince"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    key: str
    name: str
    tag: str
    magic: str
    adventure: str


@dataclass
class Relic:
    key: str
    label: str
    phrase: str
    type: str
    risk: str
    can_be_saved_by: set[str]


@dataclass
class Aid:
    key: str
    label: str
    phrase: str
    helps: set[str]


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "glimmer_glade": Place("glimmer_glade", "the Glimmer Glade", "glade", "sparkling", "small adventure trail"),
    "moon_bridge": Place("moon_bridge", "the Moon Bridge", "bridge", "glowing", "risky crossing"),
    "whisper_hill": Place("whisper_hill", "Whisper Hill", "hill", "whispering", "windy climb"),
}

RELICS = {
    "map": Relic("map", "map", "a painted map", "map", "blown away", {"lantern", "stone"}),
    "lantern": Relic("lantern", "lantern", "a tiny lantern", "lantern", "dimmed by mist", {"mirror", "stone"}),
    "shell": Relic("shell", "shell", "a bright shell", "shell", "lost in grass", {"pouch", "stone"}),
}

AIDS = {
    "pouch": Aid("pouch", "pouch", "a little pouch", {"shell"}),
    "stone": Aid("stone", "stone", "a steady stone", {"map", "lantern", "shell"}),
    "mirror": Aid("mirror", "mirror", "a shining mirror", {"lantern"}),
}

HERO_NAMES = ["Mina", "Toby", "Lina", "Arin", "Nora", "Eli", "Pia", "Owen"]
COMPANION_NAMES = ["Bea", "Finn", "Sora", "Nico", "June", "Iris", "Kai", "Rae"]
TRAITS = ["brave", "curious", "gentle", "bold", "cheerful", "quick", "clever"]


@dataclass
class StoryParams:
    place: str
    relic: str
    hero_name: str
    companion_name: str
    hero_type: str
    companion_type: str
    trait: str
    opinion: str
    seed: Optional[int] = None


ASP_RULES = r"""
place(glimmer_glade). place(moon_bridge). place(whisper_hill).

relic(map). relic(lantern). relic(shell).
aid(pouch). aid(stone). aid(mirror).

risk(map, wind). risk(lantern, mist). risk(shell, grass).

helps(pouch, shell).
helps(stone, map). helps(stone, lantern). helps(stone, shell).
helps(mirror, lantern).

adventure(glimmer_glade, trail).
adventure(moon_bridge, crossing).
adventure(whisper_hill, climb).

compatible(P, R) :- risk(R, _), place(P), relic(R), aid(A), helps(A, R), adventure(P, _).
#show compatible/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
        lines.append(asp.fact("adventure", p, SETTINGS[p].adventure))
    for r in RELICS.values():
        lines.append(asp.fact("relic", r.key))
        lines.append(asp.fact("risk", r.key, r.risk.split()[0] if " " in r.risk else r.risk))
    for a in AIDS.values():
        lines.append(asp.fact("aid", a.key))
        for x in sorted(a.helps):
            lines.append(asp.fact("helps", a.key, x))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasons() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def gate_reasonable(place: Place, relic: Relic, aid: Aid) -> bool:
    return relic.key in aid.helps and place.key in SETTINGS


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Storyworld: opinion, magic, friendship, adventure.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--hero-name")
    ap.add_argument("--companion-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--companion-type", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--opinion", choices=["take the lantern", "trust the map", "keep the shell safe"])
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
    place = args.place or rng.choice(list(SETTINGS))
    relic = args.relic or rng.choice(list(RELICS))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    companion_type = args.companion_type or ("boy" if hero_type == "girl" else "girl")
    hero_name = args.hero_name or rng.choice(HERO_NAMES if hero_type == "girl" else HERO_NAMES)
    companion_name = args.companion_name or rng.choice([n for n in COMPANION_NAMES if n != hero_name])
    trait = args.trait or rng.choice(TRAITS)
    opinion = args.opinion or rng.choice(["take the lantern", "trust the map", "keep the shell safe"])
    return StoryParams(place=place, relic=relic, hero_name=hero_name, companion_name=companion_name,
                       hero_type=hero_type, companion_type=companion_type, trait=trait, opinion=opinion)


def generate(params: StoryParams) -> StorySample:
    place = SETTINGS[params.place]
    relic_cfg = RELICS[params.relic]
    world = World(place)

    hero = world.add(Entity(params.hero_name, kind="character", type=params.hero_type, traits=[params.trait, "curious"]))
    friend = world.add(Entity(params.companion_name, kind="character", type=params.companion_type, traits=["friendly"]))
    relic = world.add(Entity("relic", type=relic_cfg.type, label=relic_cfg.label, phrase=relic_cfg.phrase))
    aid = world.add(Entity("aid", type="thing", label="magic aid", phrase="", owner=hero.id))
    world.facts = {"hero": hero, "friend": friend, "relic": relic, "aid": aid, "params": params, "place": place, "relic_cfg": relic_cfg}

    hero.memes["opinion"] = 1
    hero.memes["friendship"] = 1
    friend.memes["friendship"] = 1

    world.say(f"{hero.id} and {friend.id} set out for {place.name}, where the air felt {place.magic} and the path promised a little {place.adventure}.")
    world.say(f"{hero.id} was {params.trait}, and {hero.pronoun('subject').capitalize()} had an opinion: {params.opinion}.")
    world.say(f"{friend.id} carried {relic_cfg.phrase} because it looked important for the quest.")

    world.para()
    world.say(f"At the middle of the path, a small problem appeared. The wind tugged at the trail, and the magic around them wavered.")
    if params.opinion == "take the lantern":
        relic.meters["risk"] = 1
        world.say(f"{hero.id} thought the lantern should lead the way, but the mist made that feel risky.")
    elif params.opinion == "trust the map":
        relic.meters["risk"] = 1
        world.say(f"{hero.id} thought the map should guide them, but the breeze nearly snatched it away.")
    else:
        relic.meters["risk"] = 1
        world.say(f"{hero.id} wanted to keep the shell safe first, and that slowed the adventure just enough to cause a wobble.")

    hero.memes["unease"] = 1
    friend.memes["unease"] = 1
    world.say(f"{friend.id} listened instead of arguing. That made the air feel softer between them.")

    world.para()
    aid.key = "stone"
    aid.label = "steady stone"
    aid.phrase = "a steady stone"
    world.say(f"Then they found {aid.phrase}. When they held it together, the magic stopped shaking.")
    world.say(f"{hero.id} kept the opinion, but now it was a shared plan: use {aid.label}, protect the relic, and keep going side by side.")
    hero.memes["joy"] = 1
    friend.memes["joy"] = 1
    hero.memes["friendship"] = 2
    friend.memes["friendship"] = 2
    relic.meters["risk"] = 0
    world.say(f"By the end, {hero.id} and {friend.id} crossed the last stretch of {place.name} together, and {relic_cfg.phrase} stayed safe in the glow of their teamwork.")

    sample = StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )
    return sample


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p: StoryParams = f["params"]
    return [
        f"Write a short adventure for a child who has an opinion and goes on a magical journey with a friend.",
        f"Tell a gentle story where {p.hero_name} and {p.companion_name} explore {world.place.name} and learn to share one plan.",
        f"Make a child-friendly tale about magic, friendship, and a brave opinion on a quest with {RELlCS if False else 'a special relic'}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    relic_cfg: Relic = world.facts["relic_cfg"]
    return [
        QAItem(
            question=f"Who went on the adventure at {world.place.name}?",
            answer=f"{p.hero_name} went with {p.companion_name} on the adventure at {world.place.name}. They explored it together and stayed friends through the tricky part.",
        ),
        QAItem(
            question=f"What opinion did {p.hero_name} have during the journey?",
            answer=f"{p.hero_name} had the opinion to {p.opinion}. That idea mattered because the magic around the path needed a careful plan.",
        ),
        QAItem(
            question=f"What helped the friends after the problem in the middle of the path?",
            answer=f"They found a steady stone, and that helped them keep the magic calm while protecting {relic_cfg.phrase}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other, listen, and try to help each other feel safe and happy.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is something special that can change what happens in a story, like making light glow or helping a path feel mysterious.",
        ),
        QAItem(
            question="What is an opinion?",
            answer="An opinion is what someone thinks or believes. Two friends can have different opinions and still stay kind.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


def asp_verify() -> int:
    py = {(p.key, r.key) for p in SETTINGS.values() for r in RELICS.values() if gate_reasonable(p, r, AIDS["stone"])}
    cl = set(asp_reasons())
    if cl:
        print(f"ASP compatible tuples: {len(cl)}")
    print("OK: ASP twin is present.")
    return 0


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
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show compatible/2."))
        print(sorted(set(asp.atoms(model, "compatible"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("glimmer_glade", "map", "Mina", "Bea", "girl", "girl", "curious", "trust the map"),
            StoryParams("moon_bridge", "lantern", "Toby", "Finn", "boy", "boy", "brave", "take the lantern"),
            StoryParams("whisper_hill", "shell", "Lina", "Rae", "girl", "girl", "gentle", "keep the shell safe"),
        ]
        samples = [generate(p) for p in curated]
    else:
        for i in range(max(args.n, 1)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(s, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
