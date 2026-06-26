#!/usr/bin/env python3
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
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "sister", "priestess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "brother", "priest"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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


@dataclass
class StoryParams:
    setting: str = "shore"
    seed: Optional[int] = None


SETTINGS = {
    "shore": "the silver shore",
    "cliffs": "the black cliffs above the sea",
    "harbor": "the old harbor",
}

TRAITS = ["curious", "brave", "patient", "earnest", "humble"]


@dataclass
class Domain:
    title: str
    setting: str
    hero_name: str
    hero_type: str
    elder_name: str
    problem: str
    remedy: str
    sea_sign: str
    clue_item: str


DOMAINS = [
    Domain(
        title="The Salt Cloud",
        setting="shore",
        hero_name="Mira",
        hero_type="girl",
        elder_name="Grandmother Nera",
        problem="a salt cloud had crept over the fishing nets",
        remedy="fresh river reeds, rinsed in a silver bowl",
        sea_sign="the sea had gone dull and low",
        clue_item="a shell marked with a blue spiral",
    ),
    Domain(
        title="The Sleeping Tide",
        setting="harbor",
        hero_name="Ari",
        hero_type="boy",
        elder_name="Old Tidekeeper Soren",
        problem="the tide-gate would not open",
        remedy="a bronze key cooled in seawater",
        sea_sign="the waves kept bowing against the stones",
        clue_item="a gull feather tucked under the gate",
    ),
    Domain(
        title="The Lantern Reef",
        setting="cliffs",
        hero_name="Lena",
        hero_type="girl",
        elder_name="Aunt Thale",
        problem="a reef lamp had gone dark",
        remedy="a wick soaked in oil from sea beans",
        sea_sign="the water below flashed like watching eyes",
        clue_item="a polished pebble warm as a hand",
    ),
]


class StoryWorld:
    def __init__(self, domain: Domain, setting_name: str) -> None:
        self.domain = domain
        self.place = SETTINGS[setting_name]
        self.world = World(self.place)
        self.world.facts["setting_name"] = setting_name

    def build(self) -> World:
        d = self.domain
        w = self.world
        hero = w.add(Entity(id=d.hero_name, kind="character", type=d.hero_type, traits=["little"] + [t for t in TRAITS]))
        elder = w.add(Entity(id=d.elder_name, kind="character", type="woman" if "Grandmother" in d.elder_name or "Aunt" in d.elder_name else "man"))
        sea = w.add(Entity(id="Sea", kind="thing", type="sea", label="the sea"))
        clue = w.add(Entity(id="Clue", kind="thing", type="thing", label=d.clue_item))
        remedy = w.add(Entity(id="Remedy", kind="thing", type="thing", label=d.remedy, owner=hero.id))
        w.facts.update(hero=hero, elder=elder, sea=sea, clue=clue, remedy=remedy, domain=d)
        return w

    def tell(self) -> World:
        d = self.domain
        w = self.build()
        hero = w.get(d.hero_name)
        elder = w.get(d.elder_name)

        w.say(f"Long ago, at {w.place}, there lived {hero.id}, a little {hero.type} with a curious heart.")
        w.say(f"{hero.pronoun().capitalize()} loved to watch the sea, and {hero.pronoun()} listened when {elder.id} spoke in a low, old voice about the old ways.")
        w.para()
        w.say(f"One morning, {w.place} grew quiet, and {d.sea_sign}.")
        w.say(f"Then {d.problem}.")
        w.say(f"{hero.id} bowed {hero.pronoun('possessive')} head in submission and said, \"Tell me what the sea asks of us.\"")

        hero.memes["curiosity"] = 1
        hero.memes["submission"] = 1
        hero.memes["concern"] = 1

        w.para()
        w.say(f"{elder.id} laid out {d.clue_item}, and {hero.id} noticed a tiny mark no one else had seen.")
        w.say(f"\"That mark is a sign,\" {hero.id} said. \"We should follow it.\"")
        w.say(f"So {hero.id}, though small, walked bravely to the water's edge and listened for the right answer.")
        hero.memes["bravery"] = 1

        w.para()
        w.say(f"The clue led to {d.remedy}.")
        w.say(f"{hero.id} carried it back, hands steady as a prayer, and {elder.id} made the remedy ready.")
        hero.meters["helpfulness"] = 1
        w.facts["solved"] = True

        w.para()
        w.say(f"They used the remedy at once, and the trouble loosened like a knot in wet rope.")
        w.say(f"The nets shone clean again, the gate moved, or the lamp burned bright, and the sea answered with a soft, shining hush.")
        w.say(f"By sunset, {hero.id} stood beside {elder.id} and watched the water glow gold, glad that submission had become wisdom, curiosity had become a path, and bravery had become action.")
        return w


def validate_domain(domain: Domain) -> None:
    if "sea" not in domain.problem and "tide" not in domain.problem and "reef" not in domain.problem and "nets" not in domain.problem and "lamp" not in domain.problem:
        raise StoryError("domain problem must be sea-related")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic story world: submission, remedy, and the sea.")
    ap.add_argument("--setting", choices=sorted(SETTINGS), default=None)
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
    setting = args.setting or rng.choice(sorted(SETTINGS))
    return StoryParams(setting=setting)


def choose_domain(rng: random.Random) -> Domain:
    return rng.choice(DOMAINS)


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed)
    domain = choose_domain(rng)
    validate_domain(domain)
    if params.setting not in SETTINGS:
        raise StoryError("invalid setting")
    sw = StoryWorld(domain, params.setting)
    world = sw.tell()
    story = world.render()
    prompts = [
        "Write a mythic story for young children about a small hero, a sea trouble, and a wise remedy.",
        f"Tell a gentle legend set at {world.place} where {domain.hero_name} solves a problem by listening first.",
        "Make the story begin with submission, turn to brave action, and end with the sea made right again.",
    ]
    story_qa = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {domain.hero_name}, a curious little {domain.hero_type} who learned to listen to the sea and the elder."
        ),
        QAItem(
            question=f"What was the trouble by the sea?",
            answer=f"The trouble was that {domain.problem}."
        ),
        QAItem(
            question=f"What did {domain.hero_name} do before acting?",
            answer=f"{domain.hero_name} showed submission by bowing {domain.pronoun('possessive')} head and asking what the sea needed."
        ),
        QAItem(
            question=f"How was the problem solved?",
            answer=f"{domain.hero_name} followed the clue to {domain.remedy} and brought it back so the elder could use it as the remedy."
        ),
        QAItem(
            question=f"Why did the end feel triumphant?",
            answer=f"It felt triumphant because curiosity found the clue, bravery carried the remedy, and the sea grew calm and bright again."
        ),
    ]
    world_qa = [
        QAItem(question="What is a remedy?", answer="A remedy is something that helps fix a problem or make a bad thing better."),
        QAItem(question="What does bravery mean?", answer="Bravery means doing what is right or needed even when you feel small or afraid."),
        QAItem(question="What does curiosity mean?", answer="Curiosity means wanting to know more and looking closely for clues and answers."),
        QAItem(question="What is the sea?", answer="The sea is a huge body of salt water that moves in waves and touches the shore."),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world trace ---")
        for e in sample.world.entities.values():
            bits = []
            if e.meters:
                bits.append(f"meters={e.meters}")
            if e.memes:
                bits.append(f"memes={e.memes}")
            print(f"{e.id}: {e.type} {' '.join(bits)}")
    if qa:
        print()
        for i, p in enumerate(sample.prompts, 1):
            print(f"PROMPT {i}: {p}")
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


ASP_RULES = r"""
setting(shore).
setting(cliffs).
setting(harbor).

hero(mira). hero(ari). hero(lena).
virtue(curiosity). virtue(bravery). virtue(submission).

problem(sea_problem).
remedy(sea_remedy).

good_story(S) :- setting(S), hero(_), virtue(curiosity), virtue(bravery), virtue(submission), problem(sea_problem), remedy(sea_remedy).
#show good_story/1.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "shore"), asp.fact("setting", "cliffs"), asp.fact("setting", "harbor")]
    for name in ["Mira", "Ari", "Lena"]:
        lines.append(asp.fact("hero", name.lower()))
    for v in ["curiosity", "bravery", "submission"]:
        lines.append(asp.fact("virtue", v))
    lines.append(asp.fact("problem", "sea_problem"))
    lines.append(asp.fact("remedy", "sea_remedy"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show good_story/1."))
    got = set(asp.atoms(model, "good_story"))
    want = {(s,) for s in sorted(SETTINGS)}
    if got == want:
        print(f"OK: ASP gate matches Python ({len(got)} settings).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("ASP:", sorted(got))
    print("PY :", sorted(want))
    return 1


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good_story/1."))
    return sorted(set(asp.atoms(model, "good_story")))


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show good_story/1."))
        return
    if args.asp:
        print(asp_valid_stories())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for i, setting in enumerate(sorted(SETTINGS)):
            p = StoryParams(setting=setting, seed=base_seed + i)
            samples.append(generate(p))
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))

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
