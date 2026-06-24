#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/issue_escalator_campground_misunderstanding_mystery.py
================================================================================================

A small standalone story world for a campground mystery with a misunderstanding
about an escalator and an issue.
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

    def __post_init__(self) -> None:
        for key in ["dusty", "lost", "blocked", "found", "moved"]:
            self.meters.setdefault(key, 0.0)
        for key in ["curiosity", "worry", "relief", "confusion", "pride"]:
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "ranger"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the campground"
    detail: str = "a pine-shaded path"
    affords: set[str] = field(default_factory=lambda: {"look", "search", "listen"})


@dataclass
class StoryParams:
    place: str = "campground"
    name: str = "Mina"
    gender: str = "girl"
    parent: str = "mother"
    trait: str = "curious"
    seed: Optional[int] = None


SETTINGS = {
    "campground": Setting(
        place="the campground",
        detail="a pine-shaded path that led from the office to the steep hill",
        affords={"look", "search", "listen"},
    )
}

GIRL_NAMES = ["Mina", "Lia", "Nora", "June", "Ivy", "Pia"]
BOY_NAMES = ["Evan", "Noah", "Theo", "Owen", "Leo", "Finn"]
TRAITS = ["curious", "careful", "brave", "quiet", "sharp-eyed"]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        clone = World(self.setting)
        clone.entities = {k: Entity(**vars(v)) for k, v in self.entities.items()}
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _misunderstanding_score(world: World, hero: Entity) -> float:
    return hero.memes["confusion"] + hero.memes["worry"]


def _render_issue_word() -> str:
    return "issue"


def _setup(world: World, hero: Entity, parent: Entity, ranger: Entity, clue: Entity) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} was a {hero.type} with a curious nose for clues, and {hero.pronoun('possessive')} "
        f"{parent.pronoun('possessive')} had brought {hero.pronoun('object')} to {world.setting.place}."
    )
    world.say(
        f"Near the office, {hero.pronoun('possessive')} {ranger.label} pointed down the path and said, "
        f"\"We have an {_render_issue_word()} with the escalator.\""
    )
    hero.memes["confusion"] += 1
    world.say(
        f"{hero.id} blinked. {hero.pronoun('subject').capitalize()} thought {_render_issue_word()} must be a little paper thing, "
        f"not a problem."
    )
    clue.owner = ranger.id
    world.say(
        f"{ranger.pronoun('subject').capitalize()} handed over {clue.phrase}, because the camp needed one for the cabins."
    )


def _search(world: World, hero: Entity, clue: Entity) -> None:
    hero.memes["worry"] += 1
    world.say(
        f"{hero.id} searched the path beside the escalator, peering under fern leaves and wooden steps."
    )
    world.say(
        f"{hero.pronoun('subject').capitalize()} looked for the missing {_render_issue_word()}, but the only thing that moved was a dry pine needle."
    )


def _listen(world: World, hero: Entity, escalator: Entity) -> None:
    hero.meters["found"] += 1
    world.say(
        f"Then {hero.id} heard a soft clink under the escalator. It sounded like something small bumping metal."
    )
    world.say(
        f"{hero.pronoun('subject').capitalize()} crouched and saw that the escalator's bottom comb was stuck on a pinecone."
    )
    escalator.meters["blocked"] += 1
    world.facts["blockage"] = "a pinecone"
    world.facts["mystery_clue"] = "the pinecone was blocking the steps"
    hero.memes["curiosity"] += 1


def _reveal(world: World, hero: Entity, parent: Entity, ranger: Entity, clue: Entity, escalator: Entity) -> None:
    if escalator.meters["blocked"] >= THRESHOLD and "fixed" not in world.fired:
        world.fired.add("fixed")
        world.say(
            f"{hero.id} pointed at the pinecone and told the adults. {ranger.pronoun('subject').capitalize()} pulled it free, "
            f"and the escalator started to hum again."
        )
        escalator.meters["blocked"] = 0.0
        escalator.meters["moved"] += 1
        hero.memes["pride"] += 1
        hero.memes["worry"] = 0.0
        hero.memes["relief"] += 1
        world.say(
            f"That was the real {_render_issue_word()}: not a paper slip at all, but a blocked escalator."
        )
        world.say(
            f"{parent.id} smiled at {hero.id}, and the camp ranger thanked {hero.pronoun('object')} for noticing the clue."
        )
        world.say(
            f"In the end, {hero.id} held the cabin {_render_issue_word()} card, the escalator glided smoothly, and the pine scent drifted through the quiet campground."
        )


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label="parent"))
    ranger = world.add(Entity(id="Ranger", kind="character", type="ranger", label="ranger"))
    escalator = world.add(Entity(id="Escalator", type="escalator", label="escalator"))
    clue = world.add(Entity(
        id="issue_card",
        type="card",
        label="issue card",
        phrase="a little paper issue card for the cabins",
        owner=ranger.id,
    ))

    world.say(
        f"At {world.setting.place}, a shiny escalator climbed the hill beside {world.setting.detail}."
    )
    world.say(
        f"{params.name}'s {parent.label} said the walk should be easy, but the ranger had noticed an {_render_issue_word()}."
    )
    world.para()

    _setup(world, hero, parent, ranger, clue)
    world.para()
    _search(world, hero, clue)
    _listen(world, hero, escalator)
    world.para()
    _reveal(world, hero, parent, ranger, clue, escalator)

    world.facts.update(
        hero=hero,
        parent=parent,
        ranger=ranger,
        escalator=escalator,
        clue=clue,
        setting=world.setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f'Write a short mystery for a child at a campground that uses the word "{_render_issue_word()}".',
        f"Tell a gentle story where {hero.id} misunderstands what an {_render_issue_word()} is when the ranger mentions the escalator.",
        "Write a small campground mystery that ends with a clue under the escalator being explained.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    ranger = f["ranger"]
    clue = f["clue"]
    escalator = f["escalator"]
    return [
        QAItem(
            question=f"Why did {hero.id} get confused when the ranger mentioned the escalator?",
            answer=(
                f"{hero.id} thought an {_render_issue_word()} was a little paper thing, so "
                f"{hero.pronoun('subject')} misunderstood the ranger and looked for a thing instead of a problem."
            ),
        ),
        QAItem(
            question=f"What was the real {_render_issue_word()} at the campground?",
            answer=(
                f"The real {_render_issue_word()} was that the escalator was blocked by a pinecone. "
                f"Once that was removed, the escalator could move again."
            ),
        ),
        QAItem(
            question=f"What did {hero.id} help the adults notice?",
            answer=(
                f"{hero.id} noticed the pinecone under the escalator and pointed it out, which helped the ranger fix the problem."
            ),
        ),
        QAItem(
            question=f"Who thanked {hero.id} for solving the mystery?",
            answer=(
                f"The ranger and {parent.id} both thanked {hero.id} for paying close attention and finding the clue."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a campground?",
            answer="A campground is a place where people stay in tents, cabins, or campers and spend time outdoors.",
        ),
        QAItem(
            question="What does an escalator do?",
            answer="An escalator is a moving set of steps that carries people up or down without them climbing every step.",
        ),
        QAItem(
            question="What does it mean when someone has an issue?",
            answer="When someone has an issue, it means there is a problem that needs attention.",
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(X) :- hero_name(X).
issue_word(issue).
blocked(E) :- escalator(E), pinecone_block(E).
mystery_resolved :- blocked(E), removed(E).
misunderstanding(H) :- hero(H), hears_issue(H), thinks_issue_is_object(H).
happy_ending :- mystery_resolved, misunderstanding(_).
#show mystery_resolved/0.
#show misunderstanding/1.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("hero_name", "hero"),
        asp.fact("escalator", "escalator"),
        asp.fact("hears_issue", "hero"),
        asp.fact("thinks_issue_is_object", "hero"),
        asp.fact("pinecone_block", "escalator"),
        asp.fact("removed", "escalator"),
    ]
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    atoms = {sym.name for sym in model}
    if "mystery_resolved" in atoms and "misunderstanding" in atoms:
        print("OK: ASP rules produce the expected mystery state.")
        return 0
    print("MISMATCH: ASP rules did not produce the expected state.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Campground mystery with a misunderstanding about an issue and an escalator.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        place=args.place or "campground",
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
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


CURATED = [
    StoryParams(place="campground", name="Mina", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="campground", name="Owen", gender="boy", parent="father", trait="sharp-eyed"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program())
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
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
