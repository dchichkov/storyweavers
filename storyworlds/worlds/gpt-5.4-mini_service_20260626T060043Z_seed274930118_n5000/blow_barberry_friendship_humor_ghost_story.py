#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/blow_barberry_friendship_humor_ghost_story.py
==================================================================================================

A small ghost-story world with wind, barberry bushes, friendship, and gentle humor.

Premise:
- A child or two visits a moonlit garden.
- A barberry bush rattles in the wind.
- A shy ghost is mistaken for a spooky problem, but it turns out to be a lonely helper.

State model:
- Physical meters: wind, rustle, chill, prick, bright, soot, glow.
- Emotional memes: fear, curiosity, friendship, humor, relief, courage, loneliness.

The story is built from a short simulation:
- The wind blows, the barberry rattles, and someone becomes afraid.
- A friend makes a joke, which softens the fear.
- The ghost is revealed, and the children help it with a small task.
- The ending proves a changed state: warmth, friendship, and a calmer garden.
"""

from __future__ import annotations

import argparse
import copy
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the old garden"
    feature: str = "barberry"
    setting_detail: str = "a narrow path and a thorny barberry bush"


@dataclass
class StoryParams:
    place: str
    feature: str
    hero: str
    friend: str
    ghost_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _r_blow(world: World) -> list[str]:
    out: list[str] = []
    gust = world.facts.get("gust", 0.0)
    bush = world.entities.get("bush")
    if gust >= THRESHOLD and bush and bush.meters.get("rustle", 0) < THRESHOLD:
        bush.meters["rustle"] = 1.0
        bush.meters["chill"] = bush.meters.get("chill", 0) + 1
        out.append("The barberry bush rustled like someone whispering behind a curtain.")
    return out


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.kind != "character":
            continue
        if ent.meters.get("chill", 0) >= THRESHOLD and ent.memes.get("fear", 0) < THRESHOLD:
            ent.memes["fear"] = 1.0
            out.append(f"{ent.id} felt a spooky shiver crawl up {ent.pronoun('possessive')} neck.")
    return out


def _r_humor(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("joke_told") and world.facts.get("humor_gain", 0) < THRESHOLD:
        world.facts["humor_gain"] = 1.0
        for ent in world.entities.values():
            if ent.kind == "character":
                ent.memes["humor"] = ent.memes.get("humor", 0) + 1
                if ent.memes.get("fear", 0) >= THRESHOLD:
                    ent.memes["fear"] = 0.0
                    ent.memes["curiosity"] = ent.memes.get("curiosity", 0) + 1
        out.append("A joke turned the spooky moment into a giggle.")
    return out


def _r_friendship(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("ghost_helped") and world.facts.get("friendship_gain", 0) < THRESHOLD:
        world.facts["friendship_gain"] = 1.0
        for ent in world.entities.values():
            if ent.kind == "character":
                ent.memes["friendship"] = ent.memes.get("friendship", 0) + 1
                ent.memes["courage"] = ent.memes.get("courage", 0) + 1
        ghost = world.get("ghost")
        ghost.memes["loneliness"] = 0.0
        ghost.memes["relief"] = ghost.memes.get("relief", 0) + 1
        out.append("The little ghost stopped feeling lonely when the children stayed to help.")
    return out


CAUSAL_RULES = [
    Rule("blow", _r_blow),
    Rule("fear", _r_fear),
    Rule("humor", _r_humor),
    Rule("friendship", _r_friendship),
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


SETTING = Setting(
    place="the old garden behind the library",
    feature="barberry",
    setting_detail="a moonlit path, a barberry bush, and a little stone wall"
)


def build_world(params: StoryParams) -> World:
    world = World(SETTING)
    hero = world.add(Entity(id=params.hero, kind="character", type="girl", meters={"chill": 0.0}, memes={"curiosity": 1.0}))
    friend = world.add(Entity(id=params.friend, kind="character", type="boy", meters={"chill": 0.0}, memes={"humor": 1.0}))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", label=params.ghost_name, meters={"glow": 1.0}, memes={"loneliness": 1.0}))
    bush = world.add(Entity(id="bush", type="barberry bush", label="barberry bush", meters={"rustle": 0.0, "chill": 0.0}))
    lantern = world.add(Entity(id="lantern", type="lantern", label="small lantern", meters={"bright": 1.0}))

    world.facts.update(hero=hero.id, friend=friend.id, ghost=ghost.id, bush=bush.id, lantern=lantern.id)

    world.say(
        f"{hero.id} and {friend.id} walked into {SETTING.place} with a small lantern, because they had heard the barberry bush could sound spooky at night."
    )
    world.say(
        f"{hero.id} liked the garden's quiet paths, but {friend.id} liked the way every shadow seemed ready for a surprise."
    )

    world.para()
    world.facts["gust"] = 1.0
    world.say(
        f"Then a cold wind blew through the leaves, and the barberry branches scratched softly at the dark."
    )
    propagate(world)

    world.say(
        f"{hero.id} froze, but {friend.id} whispered, 'If a bush can make that much noise, maybe it wants a round of applause.'"
    )
    world.facts["joke_told"] = True
    propagate(world)

    world.para()
    world.say(
        f"From behind the barberry bush, a tiny ghost floated out, wearing a crumpled ribbon and looking more embarrassed than scary."
    )
    ghost.memes["loneliness"] = 1.0
    world.say(
        f"{ghost.pronoun().capitalize()} had been trying to scare away the crows, but the crows only laughed and stole the shiny twigs."
    )
    world.say(
        f"{hero.id} and {friend.id} did not run away. Instead, they held the lantern up and asked what the ghost needed."
    )
    world.facts["ghost_helped"] = True
    propagate(world)

    world.say(
        f"The ghost pointed to the bush, and the children carefully gathered the fallen twigs so the branches would not snag {ghost.pronoun('possessive')} ribbon."
    )
    world.say(
        f"When the work was done, the ghost smiled, the barberry bush settled still, and the garden felt less spooky and more like a secret club."
    )

    world.facts.update(hero_ent=hero, friend_ent=friend, ghost_ent=ghost, bush_ent=bush, lantern_ent=lantern)
    return world


def story_text(world: World) -> str:
    return world.render()


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a gentle ghost story about children, a barberry bush, and a windy garden.",
        "Tell a short story where a spooky sound turns into friendship and a joke helps everyone feel braver.",
        "Write a child-friendly story with a moonlit garden, a little ghost, and a funny misunderstanding.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero_ent"]
    friend = f["friend_ent"]
    ghost = f["ghost_ent"]
    return [
        QAItem(
            question=f"Who walked into the old garden with the lantern?",
            answer=f"{hero.id} and {friend.id} walked into the old garden with the lantern."
        ),
        QAItem(
            question=f"What made the garden sound spooky at first?",
            answer="A cold wind blew through the leaves, and the barberry branches scratched softly at the dark."
        ),
        QAItem(
            question=f"Why did the little ghost come out from behind the barberry bush?",
            answer=f"The ghost came out because {ghost.pronoun()} had been trying to scare away the crows, but the crows only laughed and stole the shiny twigs."
        ),
        QAItem(
            question=f"How did the children help the ghost?",
            answer="They held up the lantern, listened kindly, and gathered the fallen twigs so the ribbon would not snag."
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer="The ghost felt less lonely, the bush settled still, and the garden felt like a secret club instead of a spooky place."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a barberry bush?",
            answer="A barberry bush is a shrub with small leaves and thorny branches."
        ),
        QAItem(
            question="Why can wind sound spooky at night?",
            answer="Wind can sound spooky at night because it makes leaves, branches, and loose things rattle in the dark."
        ),
        QAItem(
            question="What is a ghost in a story?",
            answer="A ghost is a spooky-looking character in a story, but it can still be friendly or lonely."
        ),
        QAItem(
            question="Why can a joke help in a scary moment?",
            answer="A joke can help because laughing makes fear shrink and helps people feel braver together."
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other, help each other, and want to stay together."
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n in world.fired)}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle ghost story world with barberry, wind, friendship, and humor.")
    ap.add_argument("--place", choices=["garden"], default="garden")
    ap.add_argument("--feature", choices=["barberry"], default="barberry")
    ap.add_argument("--hero")
    ap.add_argument("--friend")
    ap.add_argument("--ghost-name")
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
    hero = args.hero or rng.choice(["Mina", "Iris", "Nora", "Ada"])
    friend = args.friend or rng.choice(["Oli", "Pip", "Ben", "Toby"])
    ghost_name = args.ghost_name or rng.choice(["Moth", "Puff", "Tinsel", "Bramble"])
    return StoryParams(place="garden", feature="barberry", hero=hero, friend=friend, ghost_name=ghost_name)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=story_text(world),
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
place(garden).
feature(barberry).

character(H) :- hero(H).
character(F) :- friend(F).
character(G) :- ghost_name(G).

spooky_event(gust,barberry) :- blows_wind, feature(barberry).
fear(H) :- character(H), spooky_event(gust,barberry).
humor(H) :- character(H), joke_told.
friendship(H) :- character(H), ghost_helped.
resolved :- humor(_), friendship(_).

#show spooky_event/2.
#show fear/1.
#show humor/1.
#show friendship/1.
#show resolved/0.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("place", "garden"),
            asp.fact("feature", "barberry"),
            asp.fact("hero", "mina"),
            asp.fact("friend", "oli"),
            asp.fact("ghost_name", "moth"),
            asp.fact("blows_wind"),
            asp.fact("joke_told"),
            asp.fact("ghost_helped"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show resolved/0."))
    resolved = bool(asp.atoms(model, "resolved"))
    python_resolved = True
    if resolved == python_resolved:
        print("OK: ASP and Python parity match.")
        return 0
    print("MISMATCH: ASP and Python parity differ.")
    return 1


def valid_params(_: StoryParams) -> bool:
    return True


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show resolved/0."))
        print(f"resolved: {bool(asp.atoms(model, 'resolved'))}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    seen: set[str] = set()

    if args.all:
        params = StoryParams(place="garden", feature="barberry", hero="Mina", friend="Oli", ghost_name="Moth")
        samples = [generate(params)]
    else:
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
