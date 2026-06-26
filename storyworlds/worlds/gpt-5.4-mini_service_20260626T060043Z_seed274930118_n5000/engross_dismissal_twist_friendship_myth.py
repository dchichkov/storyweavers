#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/engross_dismissal_twist_friendship_myth.py
===============================================================================================================

A small myth-style story world about a childlike seeker, a dismissal, a twist,
and a friendship that changes the ending.

Seed tale used to build the world:
---
A young listener named Nia loved old myths. One evening, she sat beside the fire
and listened so hard that even the crickets seemed to hush. She wanted to learn
why the moon rose and why ravens laughed at dawn.

Her elder, who guarded the village stories, dismissed her question. "Myths are
for waiting, not for chasing," the elder said. Nia felt small and left out.

Then a clever friend showed her that the old tale had a twist: the moon's silver
path only appeared when two children shared a lantern and walked together to the
hill. Nia and her friend climbed the hill, and the sky answered with a bright,
surprising glow.

Causal world model:
---
- engrossed attention -> curiosity rises, hunger for meaning rises
- dismissal -> shame rises, trust in elder falls, urge to prove oneself rises
- friendship -> courage rises, loneliness falls
- twist discovered together -> curiosity becomes understanding, shame softens
- shared climb and lantern -> the sky-image changes and the ending becomes proof
  that the friendship mattered
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
        female = {"girl", "woman", "mother", "elder"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    kind: str
    feature: str
    allows: set[str] = field(default_factory=set)


@dataclass
class Artifact:
    id: str
    label: str
    phrase: str
    effect: str
    needed_for_twist: bool = False


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.artifacts: dict[str, Artifact] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_artifact(self, art: Artifact) -> Artifact:
        self.artifacts[art.id] = art
        return art

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
    hero: str
    elder: str
    friend: str
    artifact: str
    seed: Optional[int] = None


PLACES = {
    "firecircle": Place(name="the fire circle", kind="circle", feature="a bright fire", allows={"listen", "walk", "share"}),
    "hill": Place(name="the hill", kind="hill", feature="a moon-bright path", allows={"climb", "share"}),
    "lakeshore": Place(name="the lakeshore", kind="shore", feature="silver water", allows={"listen", "walk", "share"}),
}

HEROES = [
    ("Nia", "girl"),
    ("Milo", "boy"),
    ("Sara", "girl"),
    ("Tavi", "boy"),
]

ELDERS = [
    ("the elder", "elder"),
    ("the storyteller", "elder"),
    ("the old keeper", "elder"),
]

FRIENDS = [
    ("Kito", "boy"),
    ("Lina", "girl"),
    ("Pek", "boy"),
    ("Rae", "girl"),
]

ARTIFACTS = {
    "lantern": Artifact("lantern", "lantern", "a little bronze lantern", "casts a shared path", needed_for_twist=True),
    "shell": Artifact("shell", "shell", "a bright shell", "holds a whisper of the sea"),
    "ribbon": Artifact("ribbon", "ribbon", "a red ribbon", "marks the safe road"),
}

TRAITS = ["curious", "gentle", "earnest", "bright", "bold"]


class Rule:
    def __init__(self, name, apply):
        self.name = name
        self.apply = apply


def _r_engross(world: World) -> list[str]:
    out = []
    for e in world.entities.values():
        if e.memes.get("engross", 0.0) < THRESHOLD:
            continue
        sig = ("engross", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["curiosity"] = e.memes.get("curiosity", 0.0) + 1.0
        e.memes["wonder"] = e.memes.get("wonder", 0.0) + 1.0
        out.append(f"{e.id} listened so hard that the whole night felt close.")
    return out


def _r_dismissal(world: World) -> list[str]:
    out = []
    for e in world.entities.values():
        if e.memes.get("dismissed", 0.0) < THRESHOLD:
            continue
        sig = ("dismissal", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["shame"] = e.memes.get("shame", 0.0) + 1.0
        e.memes["trust"] = max(0.0, e.memes.get("trust", 0.0) - 1.0)
        out.append(f"{e.id} felt small after the elder brushed the question away.")
    return out


def _r_friendship(world: World) -> list[str]:
    out = []
    for e in world.entities.values():
        if e.memes.get("friendship", 0.0) < THRESHOLD:
            continue
        sig = ("friendship", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["courage"] = e.memes.get("courage", 0.0) + 1.0
        e.memes["loneliness"] = max(0.0, e.memes.get("loneliness", 0.0) - 1.0)
        out.append(f"A friend stayed beside {e.id}, and that made the dark feel less sharp.")
    return out


def _r_twist(world: World) -> list[str]:
    out = []
    hero = world.entities.get("hero")
    friend = world.entities.get("friend")
    if not hero or not friend:
        return out
    if hero.memes.get("twist_seen", 0.0) < THRESHOLD:
        return out
    sig = ("twist", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["understanding"] = hero.memes.get("understanding", 0.0) + 1.0
    hero.memes["shame"] = max(0.0, hero.memes.get("shame", 0.0) - 1.0)
    friend.memes["joy"] = friend.memes.get("joy", 0.0) + 1.0
    out.append("Together they saw the hidden rule, and the old tale opened like a door.")
    return out


CAUSAL_RULES = [
    Rule("engross", _r_engross),
    Rule("dismissal", _r_dismissal),
    Rule("friendship", _r_friendship),
    Rule("twist", _r_twist),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_story(world: World, hero: Entity, elder: Entity, friend: Entity, artifact: Artifact) -> None:
    world.say(
        f"{hero.id} was a {world.facts['trait']} child who loved old myths and the fire's red hush."
    )
    world.say(
        f"{hero.id} sat at {world.place.name} and became so engrossed in the story that even the sparks seemed to listen."
    )
    hero.memes["engross"] = 1.0
    hero.memes["curiosity"] = 1.0
    propagate(world)

    world.para()
    world.say(
        f"{hero.id} asked why the moon climbed so slowly, but {elder.id} gave the question a dismissal and said myths were for waiting."
    )
    hero.memes["dismissed"] = 1.0
    hero.memes["loneliness"] = 1.0
    propagate(world)

    world.say(
        f"{hero.id} carried the question away with a heavy chest, and the night felt bigger than before."
    )

    world.para()
    world.say(
        f"Then {friend.id} came close, smiled, and shared {artifact.phrase}."
    )
    hero.memes["friendship"] = 1.0
    friend.memes["friendship"] = 1.0
    world.facts["artifact_label"] = artifact.label
    world.facts["artifact_phrase"] = artifact.phrase
    world.facts["artifact_effect"] = artifact.effect
    propagate(world)

    world.say(
        f"{friend.id} whispered that the old tale had a twist: the silver path would appear only when two friends went together."
    )
    hero.memes["twist_seen"] = 1.0
    propagate(world)

    world.say(
        f"So {hero.id} and {friend.id} climbed toward the hill and held the {artifact.label} high."
    )
    world.say(
        f"The sky answered at once, and a pale road opened above them like a secret finally told."
    )
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    friend.memes["joy"] = friend.memes.get("joy", 0.0) + 1.0
    world.facts["resolved"] = True


def choose_one(rng: random.Random, items):
    return items[rng.randrange(len(items))]


def resolve_place(place_id: str) -> Place:
    if place_id not in PLACES:
        raise StoryError(f"Unknown place: {place_id}")
    return PLACES[place_id]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    hero_name, _ = rng.choice(HEROES)
    elder_name, _ = rng.choice(ELDERS)
    friend_name, _ = rng.choice(FRIENDS)
    artifact = args.artifact or rng.choice(list(ARTIFACTS))
    return StoryParams(place=place, hero=hero_name, elder=elder_name, friend=friend_name, artifact=artifact)


def tell(params: StoryParams) -> World:
    place = resolve_place(params.place)
    world = World(place)
    world.facts["trait"] = random.choice(TRAITS) if params.seed is None else TRAITS[params.seed % len(TRAITS)]
    hero = world.add(Entity(id="hero", kind="character", type="girl", label=params.hero))
    elder = world.add(Entity(id="elder", kind="character", type="elder", label=params.elder))
    friend = world.add(Entity(id="friend", kind="character", type="girl", label=params.friend))
    art = world.add_artifact(ARTIFACTS[params.artifact])

    # fix types for pronouns from chosen names
    hero.type = dict(HEROES).get(params.hero, "girl")
    elder.type = "elder"
    friend.type = dict(FRIENDS).get(params.friend, "girl")

    build_story(world, hero, elder, friend, art)
    world.facts.update(hero=hero, elder=elder, friend=friend, artifact=art, place=place)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a small myth-like story about a child named {f["hero"].label} who becomes engrossed in an old tale at {f["place"].name}.',
        f"Tell a story where {f['elder'].label} gives a dismissal, but {f['friend'].label} helps reveal the twist.",
        f'Write a gentle myth for children where friendship leads to a surprising sky image and the word "{f["artifact_label"]}" appears.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    friend = f["friend"]
    place = f["place"]
    artifact = f["artifact"]
    return [
        QAItem(
            question=f"Why was {hero.label} sitting so quietly at {place.name}?",
            answer=f"{hero.label} was engrossed in the old myth, listening so hard that the night felt close.",
        ),
        QAItem(
            question=f"How did {elder.label} answer {hero.label}'s question at first?",
            answer=f"{elder.label} answered with a dismissal and said myths were for waiting, not for chasing.",
        ),
        QAItem(
            question=f"What did {friend.label} do to help {hero.label} after the dismissal?",
            answer=f"{friend.label} stayed near {hero.label}, shared {artifact.phrase}, and helped turn the story toward a better ending.",
        ),
        QAItem(
            question=f"What was the twist in the old tale?",
            answer=f"The twist was that the silver path appeared when two friends went together and held the {artifact.label} high.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"{hero.label} and {friend.label} climbed the hill together, and the sky answered with a pale road above them.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="What does it mean to be engrossed in something?",
            answer="Being engrossed means paying such close attention that other things fade away for a while.",
        ),
        QAItem(
            question="What is a dismissal?",
            answer="A dismissal is when someone brushes away a question or idea instead of taking it seriously.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other, stay near each other, and help each other feel braver.",
        ),
        QAItem(
            question=f"What is special about the {f['artifact_label']} in this world?",
            answer=f"The {f['artifact_label']} is special because it helps reveal the hidden path in the twist of the tale.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  place: {world.place.name}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


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
% A hero is engrossed if the story says so.
engrossed(H) :- hero(H), eager(H), not dismissed(H).

% A dismissal pushes shame up and trust down.
dismissal(H) :- hero(H), brushed_aside(H).

% Friendship softens the effects of dismissal.
friendship(H) :- hero(H), friend_of(H,F), helper(F).

% A twist is visible when the shared artifact is carried to the place that
% reveals the hidden path.
twist(H) :- hero(H), at_place(H,P), shared_artifact(A), twist_artifact(A), path_opens(P).

% A story is reasonable when it includes engrossment, dismissal, friendship,
% and a twist.
reasonable_story(H) :- engrossed(H), dismissal(H), friendship(H), twist(H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("hero", "hero"))
    lines.append(asp.fact("helper", "friend"))
    lines.append(asp.fact("eager", "hero"))
    lines.append(asp.fact("brushed_aside", "hero"))
    lines.append(asp.fact("dismissed", "hero"))
    lines.append(asp.fact("friend_of", "hero", "friend"))
    lines.append(asp.fact("at_place", "hero", "hill"))
    lines.append(asp.fact("shared_artifact", "lantern"))
    lines.append(asp.fact("twist_artifact", "lantern"))
    lines.append(asp.fact("path_opens", "hill"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable() -> bool:
    import asp
    model = asp.one_model(asp_program("#show reasonable_story/1."))
    return bool(asp.atoms(model, "reasonable_story"))


def asp_verify() -> int:
    ok = asp_reasonable()
    if not ok:
        print("MISMATCH: ASP reasonableness gate failed.")
        return 1
    print("OK: ASP reasonableness gate accepts the story shape.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Myth-style story world about engrossment, dismissal, friendship, and a twist.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--artifact", choices=sorted(ARTIFACTS))
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reasonable_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show reasonable_story/1."))
        print("reasonable_story:", bool(asp.atoms(model, "reasonable_story")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, (place, hero, elder, friend, artifact) in enumerate([
            ("firecircle", "Nia", "the elder", "Kito", "lantern"),
            ("hill", "Milo", "the storyteller", "Lina", "shell"),
            ("lakeshore", "Sara", "the old keeper", "Rae", "ribbon"),
        ]):
            params = StoryParams(place=place, hero=hero, elder=elder, friend=friend, artifact=artifact, seed=base_seed + i)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            params = resolve_params(args, rng)
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
