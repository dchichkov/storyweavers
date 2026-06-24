#!/usr/bin/env python3
"""
A small detective-style storyworld about a thaw that reveals clues, a team of
little infantry toys, and a lesson learned about teamwork.
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
class StoryParams:
    place: str
    mystery: str
    culprit: str
    hero_name: str
    partner_name: str
    seed: Optional[int] = None


@dataclass
class Entity:
    name: str
    role: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def add_meter(self, key: str, amount: float = 1.0) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def add_meme(self, key: str, amount: float = 1.0) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass
class SceneState:
    place: str
    thaw: float = 0.0
    clues_found: int = 0
    teamwork: float = 0.0
    lesson_learned: bool = False
    solved: bool = False
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


PLACES = {
    "snowyard": "the snowy yard",
    "shed": "the old shed",
    "playroom": "the playroom floor",
}

MYSTERIES = {
    "missing_flag": "the missing flag",
    "lost_boot": "the lost boot",
    "crumbled_map": "the crumbled map",
}

CULPRITS = {
    "wind": "the windy gust",
    "mischief": "the sneaky squirrel",
    "spill": "the tipped paint cup",
}

HERO_NAMES = ["Ada", "Milo", "Nina", "Eli", "Tess", "Theo", "Lena", "Owen"]
PARTNER_NAMES = ["Bea", "Ivo", "Rae", "Jules", "Mina", "Sam", "Pip", "Noah"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective storyworld about thaw, infantry, teamwork, and a lesson learned.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--name")
    ap.add_argument("--partner")
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for mystery in MYSTERIES:
            for culprit in CULPRITS:
                combos.append((place, mystery, culprit))
    return combos


def explain_invalid(args: argparse.Namespace) -> str:
    return "(No story: the requested detective setup does not make a clear little mystery.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.culprit is None or c[2] == args.culprit)]
    if not combos:
        raise StoryError(explain_invalid(args))
    place, mystery, culprit = rng.choice(sorted(combos))
    hero_name = args.name or rng.choice(HERO_NAMES)
    partner_name = args.partner or rng.choice(PARTNER_NAMES)
    if hero_name == partner_name:
        partner_name = next(n for n in PARTNER_NAMES if n != hero_name)
    return StoryParams(
        place=place,
        mystery=mystery,
        culprit=culprit,
        hero_name=hero_name,
        partner_name=partner_name,
    )


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    for c in CULPRITS:
        lines.append(asp.fact("culprit", c))
    return "\n".join(lines)


ASP_RULES = r"""
ready(P,M,C) :- place(P), mystery(M), culprit(C).
#show ready/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show ready/3."))
    return sorted(set(asp.atoms(model, "ready")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only in python:", sorted(py - cl))
    print(" only in clingo:", sorted(cl - py))
    return 1


def generate_story(state: SceneState, params: StoryParams) -> None:
    hero = state.entities["hero"]
    partner = state.entities["partner"]
    state.say(
        f"{hero.name} was a small detective who liked looking for clues in {state.place}."
    )
    state.say(
        f"{partner.name} was a brave infantry friend who marched beside {hero.name} and never missed a footprint."
    )
    state.say(
        f"One morning, a thaw began. The cold white crust softened, and tiny shiny tracks appeared where no tracks had been before."
    )
    state.say(
        f"{hero.name} and {partner.name} found {MYSTERIES[params.mystery]} was gone, so they had a mystery to solve."
    )
    state.para()
    state.thaw += 1.0
    hero.add_meter("curiosity", 1.0)
    partner.add_meter("searching", 1.0)
    state.say(
        f"{hero.name} looked at the wet ground and said the thaw was hiding clues and also revealing them."
    )
    state.say(
        f"At first, {hero.name} searched alone, but the muddy spots kept changing under each step, and the trail was hard to follow."
    )
    state.say(
        f"Then {partner.name} noticed a little mark near the fence. Together they bent low, checked the prints, and counted every clue."
    )
    state.clues_found += 1
    state.teamwork += 1.0
    hero.add_meme("hope", 1.0)
    partner.add_meme("helpfulness", 1.0)
    state.say(
        f"Their teamwork helped them spot that {CULPRITS[params.culprit]} had made the mess."
    )
    state.say(
        f"They followed the clue to the right place, and the missing thing was found tucked under a board."
    )
    state.para()
    state.solved = True
    state.lesson_learned = True
    hero.add_meme("pride", 1.0)
    state.say(
        f"{hero.name} smiled and learned a lesson: a hard mystery gets easier when friends search together."
    )
    state.say(
        f"{partner.name} marched home beside {hero.name}, and the little infantry pair felt stronger because they had solved it as a team."
    )

    state.facts.update(
        hero=hero,
        partner=partner,
        params=params,
        thaw=state.thaw,
        clues_found=state.clues_found,
        teamwork=state.teamwork,
        lesson_learned=state.lesson_learned,
        solved=state.solved,
    )


def generation_prompts(world: SceneState) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a short detective story for children about a thaw that reveals clues at {PLACES[p.place]}.",
        f"Tell a gentle mystery where {p.hero_name} and {p.partner_name} use teamwork to solve {MYSTERIES[p.mystery]}.",
        f"Write a tiny story with infantry, a thaw, and a lesson learned about working together.",
    ]


def story_qa(world: SceneState) -> list[QAItem]:
    p = world.facts["params"]
    hero: Entity = world.facts["hero"]
    partner: Entity = world.facts["partner"]
    return [
        QAItem(
            question=f"Who was the detective in the story?",
            answer=f"{hero.name} was the little detective who looked for clues in {PLACES[p.place]}.",
        ),
        QAItem(
            question=f"Who helped {hero.name} solve the mystery?",
            answer=f"{partner.name} helped by marching beside {hero.name} and searching for the clue together.",
        ),
        QAItem(
            question=f"What changed when the thaw came?",
            answer="The cold ground softened, and hidden tracks and marks showed up so the clue could be found.",
        ),
        QAItem(
            question=f"What lesson did {hero.name} learn?",
            answer="The lesson was that teamwork makes a hard mystery easier to solve.",
        ),
    ]


def world_knowledge_qa(world: SceneState) -> list[QAItem]:
    return [
        QAItem(
            question="What is a thaw?",
            answer="A thaw is when cold snow or ice starts to melt and turn soft or wet.",
        ),
        QAItem(
            question="What does infantry mean?",
            answer="Infantry means soldiers who move on foot. In a child story, they can be little marching helpers.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and do a task together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: SceneState) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"place={world.place}")
    lines.append(f"thaw={world.thaw}")
    lines.append(f"clues_found={world.clues_found}")
    lines.append(f"teamwork={world.teamwork}")
    lines.append(f"lesson_learned={world.lesson_learned}")
    lines.append(f"solved={world.solved}")
    for key, ent in world.entities.items():
        lines.append(f"{key}: meters={ent.meters} memes={ent.memes}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = SceneState(place=PLACES[params.place])
    world.entities["hero"] = Entity(name=params.hero_name, role="detective", kind="character")
    world.entities["partner"] = Entity(name=params.partner_name, role="infantry", kind="character")
    generate_story(world, params)
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
    StoryParams(place="snowyard", mystery="missing_flag", culprit="wind", hero_name="Ada", partner_name="Bea"),
    StoryParams(place="shed", mystery="lost_boot", culprit="mischief", hero_name="Milo", partner_name="Rae"),
    StoryParams(place="playroom", mystery="crumbled_map", culprit="spill", hero_name="Nina", partner_name="Jules"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show ready/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, mystery, culprit) combos:")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
