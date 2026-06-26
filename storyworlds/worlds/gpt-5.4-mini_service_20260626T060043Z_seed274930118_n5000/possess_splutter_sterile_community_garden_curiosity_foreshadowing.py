#!/usr/bin/env python3
"""
A standalone storyworld for a tiny space-adventure tale in a community garden.

Premise:
- A curious child explorer visits a community garden with a tiny rover and a
  cherished seed pod.
- The garden's sterilizer makes one bed too clean for planting, which risks
  disappointing the child.
- A whispered warning foreshadows a splutter from the garden pump.
- Brave problem-solving restores the bed and ends with a hopeful planting image.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    name: str
    gender: str
    companion: str
    prize: str
    seed: Optional[int] = None


NAMES = {
    "girl": ["Ava", "Mina", "Luna", "Zoe", "Iris"],
    "boy": ["Nova", "Theo", "Milo", "Finn", "Leo"],
}
COMPANIONS = ["robot", "sparrow drone", "tool bot", "tiny rover"]
PRIZES = {
    "seed pod": {"label": "seed pod", "phrase": "a little seed pod", "topic": "seed"},
    "star jar": {"label": "star jar", "phrase": "a shiny star jar", "topic": "jar"},
    "moon gloves": {"label": "moon gloves", "phrase": "soft moon gloves", "topic": "gloves"},
}


def build_world(params: StoryParams) -> World:
    world = World(place="the community garden")
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    friend = world.add(Entity(id="friend", kind="character", type="robot", label=params.companion))
    prize_def = PRIZES[params.prize]
    prize = world.add(Entity(
        id="prize",
        type=params.prize,
        label=prize_def["label"],
        phrase=prize_def["phrase"],
        owner=hero.id,
        caretaker=hero.id,
    ))
    bed = world.add(Entity(id="bed", type="garden-bed", label="the garden bed"))

    # Act 1: setup.
    world.say(f"{hero.id} was a curious little space explorer who loved the community garden.")
    world.say(f"{hero.id} carried {hero.pronoun('possessive')} {prize.label} as if it were a treasure from a moon base.")
    world.say(f"Beside {hero.id} rolled {friend.label}, and together they watched every leaf and pebble.")

    # Act 2: foreshadowing and tension.
    world.para()
    world.say(f"Near the center plot, a silver sign warned that the newest bed was sterile and freshly cleaned.")
    world.say(f"{hero.id} wanted to plant there right away, but the sterile soil looked too plain for sprouts.")
    world.say(f"{friend.label} gave a small beep of foreshadowing, as if it knew the pump was about to splutter.")

    # Simulated state
    bed.meters["sterile"] = 1.0
    bed.memes["warning"] = 1.0
    hero.memes["curiosity"] = 1.0
    hero.memes["worry"] = 0.5
    world.facts["sterile_bed"] = True
    world.facts["foreshadowed"] = True

    world.say(f"Then the watering pipe did splutter, and one dusty spray pattered across the path.")
    world.say(f"{hero.id} took a careful step back. {hero.pronoun().capitalize()} did not want the whole bed to stay too sterile to grow anything.")

    # Act 3: bravery and resolution.
    world.para()
    hero.memes["bravery"] = 1.0
    world.say(f"With a brave grin, {hero.id} asked {friend.label} for help and used a tiny spade to loosen the soil.")
    world.say(f"They mixed in dark compost from the garden cart, and the bed slowly stopped feeling sterile.")
    bed.meters["sterile"] = 0.0
    bed.meters["ready"] = 1.0
    hero.meters["helped"] = 1.0

    world.say(f"At last, {hero.id} planted {hero.pronoun('possessive')} {prize.label} in the soft earth.")
    world.say(f"The community garden looked bright and safe again, and the little explorer smiled at the first hopeful row.")

    world.facts.update(hero=hero, friend=friend, prize=prize, bed=bed)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    prize = f["prize"]
    return [
        'Write a short space-adventure story for a young child in a community garden.',
        f"Tell a story where {hero.id} shows curiosity, notices a sterile garden bed, and solves the problem bravely.",
        f"Write a gentle story that includes a splutter from a garden pipe and ends with {hero.id} planting {prize.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    prize = f["prize"]
    return [
        QAItem(
            question=f"Who was the story about in the community garden?",
            answer=f"The story was about {hero.id}, a curious little space explorer, and {friend.label}, the robot friend who stayed nearby.",
        ),
        QAItem(
            question=f"What problem did {hero.id} notice in the garden bed?",
            answer="The garden bed was sterile and too freshly cleaned, so it needed soil and compost before anything could grow there.",
        ),
        QAItem(
            question=f"What sound foreshadowed trouble before the planting?",
            answer="The watering pipe gave a splutter, which warned that the garden would need a careful fix.",
        ),
        QAItem(
            question=f"How did {hero.id} solve the problem?",
            answer=f"{hero.id} showed bravery, asked for help, loosened the soil, and mixed in compost so the bed was ready for planting.",
        ),
        QAItem(
            question=f"What did {hero.id} do at the end?",
            answer=f"{hero.id} planted {hero.pronoun('possessive')} {prize.label} in the soft earth, and the garden felt safe and bright again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity is the wish to look, ask, and learn more about something new.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a small hint that tells you something important may happen soon.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing the right thing even when something feels a little scary.",
        ),
        QAItem(
            question="What does sterile mean?",
            answer="Sterile means very clean or free from tiny living things, like a bed that has been scrubbed too much for planting.",
        ),
        QAItem(
            question="What is a splutter?",
            answer="A splutter is a rough, choppy sound, like a pipe or engine making short bursts of noise.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
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
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


def tell(params: StoryParams) -> World:
    return build_world(params)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("place", "community_garden"),
        asp.fact("feature", "curiosity"),
        asp.fact("feature", "foreshadowing"),
        asp.fact("feature", "bravery"),
        asp.fact("word", "possess"),
        asp.fact("word", "splutter"),
        asp.fact("word", "sterile"),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
% A tiny declarative twin for the narrative gate.
feature(curiosity) :- word(sterile), place(community_garden).
feature(foreshadowing) :- word(splutter).
feature(bravery) :- feature(curiosity), feature(foreshadowing).

compatible_story(community_garden, curiosity, foreshadowing, bravery) :-
    place(community_garden),
    feature(curiosity),
    feature(foreshadowing),
    feature(bravery),
    word(possess),
    word(splutter),
    word(sterile).
#show compatible_story/4.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show compatible_story/4."))
    ok = bool(asp.atoms(model, "compatible_story"))
    if not ok:
        print("MISMATCH: ASP did not find the required compatible story.")
        return 1
    print("OK: ASP gate is satisfied.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure community garden storyworld.")
    ap.add_argument("--name", choices=sum([NAMES["girl"], NAMES["boy"]], []))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--prize", choices=list(PRIZES))
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    companion = args.companion or rng.choice(COMPANIONS)
    prize = args.prize or rng.choice(list(PRIZES))
    if gender == "boy" and name in NAMES["girl"]:
        raise StoryError("Requested name does not match the chosen gender.")
    return StoryParams(name=name, gender=gender, companion=companion, prize=prize)


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


CURATED = [
    StoryParams(name="Ava", gender="girl", companion="robot", prize="seed pod"),
    StoryParams(name="Theo", gender="boy", companion="tiny rover", prize="star jar"),
    StoryParams(name="Luna", gender="girl", companion="tool bot", prize="moon gloves"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show compatible_story/4."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
