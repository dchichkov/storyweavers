#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from results import QAItem, StoryError, StorySample

@dataclass
class Entity:
    id: str
    kind: str
    label: str
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    held: Optional[str] = None

@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero: str = "Luna"
    rival: str = "Pip"
    place: str = "the moonlit nursery"
    object_name: str = "certificate"
    scenario: int = 0
    telling: int = 0

class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.parts: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, entity: Entity) -> None:
        self.entities[entity.id] = entity

    def say(self, text: str) -> None:
        self.parts[-1].append(text)

    def para(self) -> None:
        if self.parts[-1]:
            self.parts.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.parts if p)

SCENES = [
    {
        "title": "the crooked golden seal",
        "opening": "Luna polished a golden certificate beneath the nursery moon",
        "conflict": "Pip snatched it and cried, “It is mine, because my sneeze was grand!”",
        "flashback": "Luna remembered yesterday, when Pip had sneezed into a basket and launched three socks like birds",
        "clue": "a blue ribbon tied to the certificate matched Luna's careful practice chart",
        "fix": "Luna and Pip read the certificate aloud and found that it honored patient helping, not the loudest sneeze",
        "lesson": "the ribbon belongs to the helper who can share the honor",
        "ending": "the certificate hung between their beds, while Pip's socks rested safely in a drawer",
    },
    {
        "title": "the upside-down stamp",
        "opening": "Luna found a certificate with a purple stamp dancing upside down",
        "conflict": "Pip puffed his cheeks and said, “I stamped it first, so I am the winner!”",
        "flashback": "Luna remembered the morning Pip had stamped a pancake, mistaking breakfast for paperwork",
        "clue": "the tiny moon mark pointed toward the line about taking turns",
        "fix": "Luna turned the paper around, and Pip added his mark beside hers instead of over it",
        "lesson": "a prize grows brighter when every careful helper gets a turn",
        "ending": "the certificate twinkled above the toy chest, right-side up at last",
    },
    {
        "title": "the giggling inkpot",
        "opening": "Luna carried a certificate past an inkpot that giggled whenever anyone bragged",
        "conflict": "Pip bowed to the pot and declared, “It laughed for me, therefore I must be best!”",
        "flashback": "Luna remembered Pip's earlier boast, when he claimed he could teach a spoon to sing",
        "clue": "the inkpot giggled at every proud voice, but grew quiet when someone thanked a friend",
        "fix": "Luna thanked Pip for finding the missing crayon, and Pip thanked Luna for writing his name neatly",
        "lesson": "kind thanks speak more truly than a noisy boast",
        "ending": "the certificate rested beside the quiet inkpot, and both friends bowed without bragging",
    },
]

WORLD_KNOWLEDGE = [
    QAItem("What is a certificate?", "A certificate is a paper or record that recognizes an accomplishment, skill, or special act."),
    QAItem("Why can a conflict help a story?", "A conflict gives characters a problem to solve and lets their choices change what happens."),
    QAItem("What is a flashback?", "A flashback is a brief return to an earlier event that helps explain the present."),
    QAItem("What makes a nursery rhyme style?", "Nursery rhyme style often uses rhythm, repetition, playful sounds, and simple memorable lines."),
]

ASP_RULES = r"""
certificate(certificate).
quality(helping).
quality(turn_taking).
valid_choice(shared_honor) :- certificate(certificate), quality(helping), quality(turn_taking).
resolved(shared_honor) :- valid_choice(shared_honor).
"""

def build_world(params: StoryParams) -> World:
    rng = random.Random(params.seed if params.seed is not None else 17)
    scene = SCENES[params.scenario % len(SCENES)]
    world = World()
    hero = Entity("hero", "character", params.hero, ["patient", "bright"], {"calm": 1.0, "confidence": 0.5}, {"kindness": 1.0})
    rival = Entity("rival", "character", params.rival, ["silly", "proud"], {"boast": 1.0, "worry": 0.2}, {"humor": 1.0, "lesson": 0.0})
    paper = Entity("certificate", "object", "certificate", ["golden", "precious"], {"clarity": 0.5}, {"fairness": 1.0})
    world.add(hero)
    world.add(rival)
    world.add(paper)

    openings = [
        f"In {params.place}, where moonbeams hummed a silver tune, {scene['opening']}.",
        f"By the cradle and the bright balloon, {scene['opening']} in the glow of the moon.",
        f"At bedtime, beneath a sleepy star, {scene['opening']} near a toy red car.",
    ]
    world.say(openings[params.telling % len(openings)])
    world.say("It was a certificate of careful hearts, with a ribbon, a seal, and a promise to share.")
    world.para()
    world.say(f"{scene['conflict']} The claim made the stuffed rabbit fall over with a comic flop.")
    world.say(f"Then Luna recalled: {scene['flashback']}.")
    world.say(f"“Let us look before we tug,” said {params.hero}. “A paper can tell the truth.”")
    world.say(f"“Can it tell a joke?” asked {params.rival}. “I hope it knows one about a dancing sock.”")
    world.say(f"“Perhaps,” said Luna, “but first it tells us this: {scene['clue']}.”")
    hero.meters["calm"] += 1.0
    rival.meters["boast"] -= 0.5
    world.para()
    world.say(f"{scene['fix']}.")
    world.say(f"{params.rival} blinked. “Then my grand sneeze may have been only a supporting sneeze.”")
    world.say(f"“A very important supporting sneeze,” said {params.hero}, and both children laughed.")
    rival.memes["lesson"] += 1.0
    hero.memes["kindness"] += 1.0
    world.say(f"They agreed that {scene['lesson']}.")
    world.say(f"At last, {scene['ending']}.")
    world.facts.update(scene=scene, hero=hero, rival=rival, paper=paper, resolved=True)
    return world

def generation_prompts(world: World) -> list[str]:
    scene = world.facts["scene"]
    return [
        "Write a playful nursery-rhyme story about a certificate and two children who disagree about who earned it.",
        f"Include a funny conflict, a flashback, and a kind resolution connected to {scene['title']}.",
        "Use rhythmic, child-friendly language and let dialogue change the characters' decisions.",
    ]

def story_qa(world: World) -> list[QAItem]:
    scene = world.facts["scene"]
    hero = world.facts["hero"]
    rival = world.facts["rival"]
    return [
        QAItem(f"Why did {hero.label} and {rival.label} disagree?", f"They disagreed because {rival.label} claimed the certificate belonged to them, while {hero.label} wanted to check what the certificate actually recognized."),
        QAItem("What did the flashback reveal?", f"The flashback recalled that {scene['flashback'].split(', when ')[-1].capitalize()}, which helped explain {rival.label}'s funny boast."),
        QAItem("How was the conflict resolved?", f"They read the certificate carefully, noticed that {scene['clue']}, and agreed to share the honor."),
        QAItem("What lesson did the children learn?", f"They learned that {scene['lesson']}."),
        QAItem("What proved the story ended happily?", f"At the end, {scene['ending']}."),
    ]

def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)

def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("\n== (2) Story questions ==")
    for q in sample.story_qa:
        lines.extend([f"Q: {q.question}", f"A: {q.answer}"])
    lines.append("\n== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.extend([f"Q: {q.question}", f"A: {q.answer}"])
    return "\n".join(lines)

def asp_facts() -> str:
    import asp
    return "\n".join([asp.fact("certificate", "certificate"), asp.fact("quality", "helping"), asp.fact("quality", "turn_taking")])

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def python_reasonable(params: StoryParams) -> None:
    if not params.hero.strip() or not params.rival.strip():
        raise StoryError("Both characters need names.")
    if params.hero == params.rival:
        raise StoryError("The two characters must have different names.")
    if params.object_name != "certificate":
        raise StoryError("This story requires a certificate.")

def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolved/1."))
    found = set(asp.atoms(model, "resolved"))
    expected = {("shared_honor",)}
    if found == expected:
        print("OK: ASP gate matches Python reasonableness gate.")
        for seed in (3, 11, 29):
            generate(StoryParams(seed=seed))
        return 0
    print("MISMATCH between ASP and Python gates.")
    return 1

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme storyworld about a certificate, conflict, humor, and a flashback.")
    ap.add_argument("--hero", choices=["Luna", "Mina", "Nell", "Rose"])
    ap.add_argument("--rival", choices=["Pip", "Bobo", "Toby", "Moth"])
    ap.add_argument("--place", default="the moonlit nursery")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(["Luna", "Mina", "Nell", "Rose"])
    rival = args.rival or rng.choice(["Pip", "Bobo", "Toby", "Moth"])
    params = StoryParams(
        seed=None,
        hero=hero,
        rival=rival,
        place=args.place,
        scenario=rng.randrange(len(SCENES)),
        telling=rng.randrange(3),
    )
    python_reasonable(params)
    return params

def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
    for e in world.entities.values():
        lines.append(f"  {e.id}: {e.label}; meters={e.meters}; memes={e.memes}; traits={e.traits}")
    lines.append(f"  resolved={world.facts.get('resolved')}")
    return "\n".join(lines)

def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print("\n" + format_qa(sample))

CURATED = [
    StoryParams(hero="Luna", rival="Pip", scenario=0, telling=0),
    StoryParams(hero="Mina", rival="Bobo", scenario=1, telling=1),
    StoryParams(hero="Nell", rival="Toby", scenario=2, telling=2),
]

def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show resolved/1."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show resolved/1."))
        print("Resolved ASP atoms:", asp.atoms(model, "resolved"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for i in range(max(1, args.n)):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
