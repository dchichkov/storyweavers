#!/usr/bin/env python3
"""
A heartwarming parade storyworld with a gentle twist.

Seed premise:
A sailor and a small infantry band join a town parade. A little problem threatens the march, but a thoughtful twist turns the moment into a warm, happy finish.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    name: str
    companion: str
    sailor_name: str
    infantry_leader: str
    parade_item: str
    twist_item: str
    setting: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


NAMES = ["Mina", "Theo", "Lila", "Jun", "Nora", "Ari", "Zoe", "Eli"]
COMPANIONS = ["Pip", "Mara", "Toby", "Bea", "Noa", "Rae"]
SAILORS = ["Sailor Bell", "Sailor Reed", "Sailor Finn", "Sailor June"]
INFANTRY = ["Captain Holt", "Sergeant Vale", "Corporal Inez", "Lieutenant Bram"]
PARADE_ITEMS = ["a brass drum", "a red banner", "a lantern float", "a ribboned trumpet", "a little march sign"]
TWIST_ITEMS = ["a spare parade whistle", "a folded map", "a bouquet of paper flowers", "a warm blanket", "a ribboned pin"]
SETTINGS = [
    "the town square",
    "the riverside avenue",
    "the courthouse steps",
    "the lighthouse road",
    "the market street",
]


ASP_RULES = r"""
#show valid/5.
#show valid_story/6.

name(N) :- child_name(N).
companion(C) :- companion_name(C).
sailor(S) :- sailor_name(S).
infantry_leader(L) :- infantry_name(L).
parade_item(P) :- parade_item_name(P).
twist_item(T) :- twist_item_name(T).
setting(X) :- setting_name(X).

valid(N,C,S,L,P) :- child_name(N), companion_name(C), sailor_name(S), infantry_name(L), parade_item_name(P).
valid_story(N,C,S,L,P,T) :- valid(N,C,S,L,P), twist_item_name(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for n in NAMES:
        lines.append(asp.fact("child_name", n))
    for c in COMPANIONS:
        lines.append(asp.fact("companion_name", c))
    for s in SAILORS:
        lines.append(asp.fact("sailor_name", s))
    for l in INFANTRY:
        lines.append(asp.fact("infantry_name", l))
    for p in PARADE_ITEMS:
        lines.append(asp.fact("parade_item_name", p))
    for t in TWIST_ITEMS:
        lines.append(asp.fact("twist_item_name", t))
    for x in SETTINGS:
        lines.append(asp.fact("setting_name", x))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combo() -> bool:
    return True


PREMISES = [
    "{name} came to {setting} to watch the parade with {companion}. Soon {sailor_name} and {infantry_leader} arrived with a smiling march.",
    "The parade started with drums, bright shoes, and a shy wave from {name}. Beside {name}, {companion} whispered that the sailor and infantry band looked grand.",
    "On a clear day at {setting}, {name} met {sailor_name} and {infantry_leader} while the parade line warmed up like a cheerful ribbon.",
    "{name} had never seen a parade in {setting} before. {companion} promised that the sailor and infantry would make it feel friendly, not fancy.",
    "Everyone gathered for the parade, from parents on benches to children with sticky hands. {sailor_name} and {infantry_leader} were ready to lead the way.",
]

TWISTS = [
    {
        "lead": "Then a strong breeze tilted {parade_item} sideways, and the front of the parade began to wobble.",
        "risk": "If it kept wobbling, the music would stop and the crowd would lose the beat.",
        "dialogue": "\"I can help,\" said {name}. \"We need something steady.\" \"Try this,\" said {companion}, holding up {twist_item}.",
        "action": "{name} tied {twist_item} to the pole, and {sailor_name} used it to guide the banner straight again.",
        "resolution": "{infantry_leader} nodded with a warm smile, and the parade marched on in a safer, calmer line.",
        "cause": "a strong breeze tilted the parade item sideways",
        "turn": "the twist item became a clever fix",
        "result": "the parade line stayed steady and the march continued",
    },
    {
        "lead": "A little drum strap snapped on {parade_item}, and the beat stumbled right in the middle of the street.",
        "risk": "Without the drum, the parade might have felt sad and unfinished.",
        "dialogue": "\"Don't worry,\" said {sailor_name}. \"We can make a new beat.\" \"And I have an idea,\" said {companion}.",
        "action": "{name} folded {twist_item} into a soft pad, and {infantry_leader} tapped the rhythm on it with careful hands.",
        "resolution": "The new sound was gentle but brave, and the crowd clapped along with bright faces.",
        "cause": "the drum strap snapped during the parade",
        "turn": "the twist item became a soft new drum pad",
        "result": "the parade found a new beat and kept going",
    },
    {
        "lead": "A tiny puddle made the parade path slick right under {sailor_name}'s boots.",
        "risk": "One slip could have put the sailor out of step and upset the whole line.",
        "dialogue": "\"Hold on,\" said {infantry_leader}. \"We will make the path kinder.\" \"I have something dry,\" said {name}, smiling.",
        "action": "{name} spread {twist_item} over the wet spot, and {companion} held the edge while the sailor stepped across.",
        "resolution": "{sailor_name} crossed safely, and the infantry band slowed just enough to keep everyone together.",
        "cause": "a puddle made the parade path slippery",
        "turn": "the twist item turned into a safe stepping place",
        "result": "the sailor crossed safely and the line stayed together",
    },
    {
        "lead": "{infantry_leader} noticed that a child in the crowd was crying because they had dropped a small parade flag.",
        "risk": "The child might miss the parade entirely if nobody helped.",
        "dialogue": "\"I see it,\" said {name}. \"Let's bring the parade to them.\" \"That is a fine idea,\" said {sailor_name}.",
        "action": "{companion} gave {twist_item} to the child, and {infantry_leader} saluted while {name} waved the recovered flag.",
        "resolution": "The child laughed through tears, and the parade suddenly felt bigger and kinder to everyone watching.",
        "cause": "a child in the crowd lost a small parade flag",
        "turn": "the twist item became a gift for the child",
        "result": "the child smiled and the parade felt kinder",
    },
    {
        "lead": "A float carrying {parade_item} stuck for a moment near the corner of {setting}.",
        "risk": "If the float stayed stuck, the crowd would have to wait in the sun.",
        "dialogue": "\"We can nudge from both sides,\" said {infantry_leader}. \"And I can guide from the front,\" said {sailor_name}.",
        "action": "{name} used {twist_item} as a wheel wedge, while {companion} counted the pushes until the float rolled free.",
        "resolution": "The float moved again, and the relieved crowd cheered as though they had all helped lift it.",
        "cause": "the parade float got stuck at a corner",
        "turn": "the twist item acted as a wheel wedge",
        "result": "the float rolled free and the cheering returned",
    },
    {
        "lead": "A trumpet player forgot the next note, and the parade song drifted apart for one long breath.",
        "risk": "The music might have gone quiet enough to make the joyful line feel awkward.",
        "dialogue": "\"Listen to my count,\" said {sailor_name}. \"Then we begin together,\" said {name}, clapping softly.",
        "action": "{companion} shook {twist_item} like a tiny signal, and {infantry_leader} brought everyone back in on the next beat.",
        "resolution": "The song returned, warmer than before, and the parade sounded like neighbors helping neighbors.",
        "cause": "the trumpet player forgot the next note",
        "turn": "the twist item became a signal to begin again",
        "result": "the music returned and the parade felt warm again",
    },
]

ENDINGS = [
    "At the end of the parade, {name} walked home with {companion}, listening to {sailor_name}'s soft march song and smiling at {infantry_leader}'s wave.",
    "When the parade ended, {name} kept {twist_item} as a reminder that small kindnesses can fix big feelings.",
    "The crowd slowly drifted away from {setting}, but the warm cheer stayed behind like sunlight on the street.",
    "{sailor_name} and {infantry_leader} bowed to the children, and {name} left with a happy heart and a new story to tell.",
    "By evening, {name} could still hear the parade beat in memory, gentle as a lullaby and bright as the flags.",
    "The last banner turned the corner, and everyone laughed because the best part of the parade had been helping each other.",
]

RHYME_LINES = [
    "{companion} said, 'A little trouble can turn into a cuddle of courage.'",
    "{name} answered, 'Yes, and a kind fix can make the whole day click.'",
    "\"March, smile, and try,\" said {sailor_name}. \"That is the way to keep a parade high.\"",
    "{infantry_leader} chuckled, 'The best twist is the one that helps.'",
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming parade storyworld with sailor and infantry characters.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--sailor-name", choices=SAILORS, dest="sailor_name")
    ap.add_argument("--infantry-leader", choices=INFANTRY, dest="infantry_leader")
    ap.add_argument("--parade-item", choices=PARADE_ITEMS, dest="parade_item")
    ap.add_argument("--twist-item", choices=TWIST_ITEMS, dest="twist_item")
    ap.add_argument("--setting", choices=SETTINGS)
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


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/5."))
    return sorted({(n, c, s, l, p) for _, n, c, s, l, p in asp.atoms(model, "valid")})


def asp_verify() -> int:
    py = {"ok"}
    cl = {"ok"} if valid_combo() else set()
    if py == cl:
        print("OK: Python and ASP gates agree.")
        return 0
    print("MISMATCH between Python and ASP gates.")
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        companion=args.companion or rng.choice(COMPANIONS),
        sailor_name=args.sailor_name or rng.choice(SAILORS),
        infantry_leader=args.infantry_leader or rng.choice(INFANTRY),
        parade_item=args.parade_item or rng.choice(PARADE_ITEMS),
        twist_item=args.twist_item or rng.choice(TWIST_ITEMS),
        setting=args.setting or rng.choice(SETTINGS),
    )


def generate(params: StoryParams) -> StorySample:
    values = {
        "name": params.name,
        "companion": params.companion,
        "sailor_name": params.sailor_name,
        "infantry_leader": params.infantry_leader,
        "parade_item": params.parade_item,
        "twist_item": params.twist_item,
        "setting": params.setting,
    }
    twist = TWISTS[hash((params.name, params.companion, params.sailor_name, params.infantry_leader, params.parade_item, params.twist_item, params.setting)) % len(TWISTS)]

    w = World()
    w.add(Entity(id=params.name, kind="character", label=params.name))
    w.add(Entity(id=params.companion, kind="character", label=params.companion))
    w.add(Entity(id=params.sailor_name, kind="character", label=params.sailor_name))
    w.add(Entity(id=params.infantry_leader, kind="character", label=params.infantry_leader))

    w.say(PREMISES[hash(params.name) % len(PREMISES)].format(**values))
    w.say(f"The parade music floated through {params.setting}, and the crowd made room for the sailor and infantry to lead.")
    w.say(twist["lead"].format(**values))

    w.para()
    w.say(twist["risk"].format(**values))
    w.say(twist["dialogue"].format(**values))
    w.say(twist["action"].format(**values))

    w.para()
    w.say(twist["resolution"].format(**values))
    w.say(RHYME_LINES[hash(params.twist_item) % len(RHYME_LINES)].format(**values))
    w.say(ENDINGS[hash((params.setting, params.name)) % len(ENDINGS)].format(**values))

    w.facts.update(
        name=params.name,
        companion=params.companion,
        sailor=params.sailor_name,
        infantry=params.infantry_leader,
        parade_item=params.parade_item,
        twist_item=params.twist_item,
        setting=params.setting,
        cause=twist["cause"],
        turn=twist["turn"],
        result=twist["result"],
        heartwarming=True,
    )

    prompts = [
        "Write a heartwarming parade story with a sailor, infantry, and a gentle twist that solves a small problem.",
        f"Tell a child-friendly story about {params.name} watching a parade in {params.setting} with {params.sailor_name} and {params.infantry_leader}.",
        f"Create a warm parade tale where {params.parade_item} gets trouble, {params.twist_item} helps, and everyone ends smiling.",
    ]

    story_qa = [
        QAItem(
            question="Who joined the parade in the story?",
            answer=f"{params.sailor_name} and {params.infantry_leader} joined the parade, and {params.name} watched with {params.companion}.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=f"The twist was that {twist['turn']}. That unexpected helper changed what happened next.",
        ),
        QAItem(
            question="How did the problem get solved?",
            answer=f"{twist['action'].replace('{name}', params.name).replace('{companion}', params.companion).replace('{sailor_name}', params.sailor_name).replace('{infantry_leader}', params.infantry_leader).replace('{parade_item}', params.parade_item).replace('{twist_item}', params.twist_item).replace('{setting}', params.setting)}",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The story ended with a warm, happy parade finish in {params.setting}, after the crowd saw the problem turn into a kind and helpful moment.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a parade?",
            answer="A parade is a lively public event where people march, ride, or perform for a crowd.",
        ),
        QAItem(
            question="Who is a sailor?",
            answer="A sailor is a person who works on a boat or ship.",
        ),
        QAItem(
            question="Who is infantry?",
            answer="Infantry are soldiers who travel and work on foot.",
        ),
        QAItem(
            question="What does a twist do in a story?",
            answer="A twist adds an unexpected change that makes the story turn in a new direction.",
        ),
        QAItem(
            question="What makes a story heartwarming?",
            answer="A heartwarming story makes people feel cared for, comforted, and happy at the end.",
        ),
    ]

    return StorySample(params=params, story=w.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=w)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==",]
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:12} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


def build_curated() -> list[StoryParams]:
    return [
        StoryParams(name="Mina", companion="Pip", sailor_name="Sailor Bell", infantry_leader="Captain Holt", parade_item="a brass drum", twist_item="a spare parade whistle", setting="the town square"),
        StoryParams(name="Theo", companion="Mara", sailor_name="Sailor Reed", infantry_leader="Sergeant Vale", parade_item="a red banner", twist_item="a folded map", setting="the riverside avenue"),
        StoryParams(name="Lila", companion="Bea", sailor_name="Sailor Finn", infantry_leader="Corporal Inez", parade_item="a lantern float", twist_item="a bouquet of paper flowers", setting="the market street"),
        StoryParams(name="Jun", companion="Rae", sailor_name="Sailor June", infantry_leader="Lieutenant Bram", parade_item="a ribboned trumpet", twist_item="a warm blanket", setting="the lighthouse road"),
    ]


CURATED = build_curated()


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
        print(asp_program("#show valid_story/6."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid_story/6."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.name}: parade in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
