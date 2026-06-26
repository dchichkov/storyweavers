#!/usr/bin/env python3
"""
A small superhero storyworld with a synagogue setting, a noisy sock mishap,
sound effects, and a lesson learned.

Seed tale:
- A young superhero arrives at a synagogue with a squeaky sock.
- The noisy "squeee!" sound distracts everyone during the quiet moment.
- A grown-up suggests a simple fix: swap to a quieter sock and step softly.
- The hero learns that being strong also means being considerate.

The world model tracks:
- physical meters: noise, comfort, stillness
- emotional memes: pride, worry, kindness, embarrassment, relief

The story stays child-facing and gentle, and the ending makes the lesson clear.
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

LESSON_LEARNED = "Even heroes should move quietly in a synagogue."


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: {"noise": 0.0, "comfort": 0.0, "stillness": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"pride": 0.0, "worry": 0.0, "kindness": 0.0, "embarrassment": 0.0, "relief": 0.0})

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the synagogue"
    quiet: bool = True
    affords: set[str] = field(default_factory=lambda: {"visit", "listen", "speak_softly"})


@dataclass
class Sock:
    label: str
    phrase: str
    squeakiness: float
    softness: float
    quiet_fix: str


@dataclass
class StoryParams:
    place: str = "synagogue"
    sock: str = "striped"
    hero_name: str = "Milo"
    sidekick_name: str = "Ari"
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


SOCKS = {
    "striped": Sock("striped sock", "a striped sock with a tiny springy seam", squeakiness=1.0, softness=0.4, quiet_fix="changed into a softer sock"),
    "wool": Sock("wool sock", "a thick wool sock", squeakiness=0.2, softness=0.9, quiet_fix="pulled the sock smooth and tucked it in"),
    "polka": Sock("polka-dot sock", "a bright polka-dot sock", squeakiness=0.7, softness=0.5, quiet_fix="slid the sock off and replaced it with a quiet one"),
}

HERO_NAMES = ["Milo", "Nina", "Ezra", "Talia", "Rafi", "Leah"]
SIDEKICK_NAMES = ["Ari", "Sima", "Noam", "Rina", "Dovi", "Mara"]


ASP_RULES = r"""
hero(H).
place(synagogue).
sock(S) :- sock_kind(S).
noisy(S) :- squeakiness(S, N), N > 0.
quiet_fix(S) :- quiet_fix(S, _).

problem(H,S) :- hero(H), wears(H,S), noisy(S).
lesson(H) :- problem(H,S), quiet_place(synagogue).
safe(H) :- lesson(H), quiet_fix(S).
#show problem/2.
#show lesson/1.
#show safe/1.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("place", "synagogue")]
    for name in HERO_NAMES:
        lines.append(asp.fact("hero", name))
    for key, sock in SOCKS.items():
        lines.append(asp.fact("sock_kind", key))
        lines.append(asp.fact("squeakiness", key, int(sock.squeakiness * 10)))
        if sock.softness >= 0.5:
            lines.append(asp.fact("quiet_fix", key, sock.quiet_fix))
    lines.append(asp.fact("quiet_place", "synagogue"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_sock(sock: Sock) -> bool:
    return sock.squeakiness >= 0.5


def build_world(params: StoryParams) -> World:
    setting = Setting()
    world = World(setting)
    hero = world.add(Entity(id=params.hero_name, kind="character", type="superhero", label=params.hero_name))
    sidekick = world.add(Entity(id=params.sidekick_name, kind="character", type="helper", label=params.sidekick_name))
    sock = SOCKS[params.sock]
    sock_ent = world.add(Entity(id="sock", type="sock", label=sock.label, phrase=sock.phrase, owner=hero.id, worn_by=hero.id))
    world.facts = {
        "hero": hero,
        "sidekick": sidekick,
        "sock": sock_ent,
        "sock_cfg": sock,
    }
    return world


def tell(world: World) -> None:
    hero = world.facts["hero"]
    sidekick = world.facts["sidekick"]
    sock = world.facts["sock"]
    cfg = world.facts["sock_cfg"]

    world.say(f"{hero.id} was a small superhero with a big cape and a careful heart.")
    world.say(f"{hero.id} wore {sock.phrase}, and {cfg.label} felt comfy at first.")

    world.para()
    world.say(f"One evening, {hero.id} and {sidekick.id} went to the synagogue.")
    world.say(f"It was a quiet place, so even tiny noises seemed extra loud.")

    world.para()
    world.say(f"Then came a sharp sound: \"Squeee!\"")
    world.say(f"{hero.id}'s {cfg.label} made the floor whisper and the cape swish too loudly.")
    hero.memes["embarrassment"] += 1
    hero.meters["noise"] += cfg.squeakiness
    sidekick.memes["worry"] += 1
    sidekick.meters["stillness"] += 0.2

    world.say(f"{sidekick.id} leaned close and said, \"Let’s be heroes with soft steps.\"")
    world.say(f"{hero.id} blinked, listened, and heard the room go extra still.")

    world.para()
    world.say(f"{hero.id} took a breath, changed into a softer sock, and walked carefully.")
    hero.memes["kindness"] += 1
    hero.memes["relief"] += 1
    hero.meters["noise"] = 0.0
    hero.meters["comfort"] += 1.0
    world.say(f"This time there was only a little swish, not a squeee.")
    world.say(f"Everyone smiled because the quiet was safe again.")

    world.para()
    world.say(f"{hero.id} learned {LESSON_LEARNED}")
    world.say(f"From then on, {hero.id} kept a quiet pair of socks ready for calm places.")


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    sidekick = world.facts["sidekick"]
    sock = world.facts["sock"]
    cfg = world.facts["sock_cfg"]
    return [
        QAItem(
            question=f"Who went to the synagogue with {hero.id}?",
            answer=f"{sidekick.id} went with {hero.id} to the synagogue.",
        ),
        QAItem(
            question=f"What made the noisy squeee sound in the story?",
            answer=f"{hero.id}'s {cfg.label} made the noisy squeee sound.",
        ),
        QAItem(
            question="What lesson did the hero learn?",
            answer=LESSON_LEARNED,
        ),
        QAItem(
            question=f"What did {hero.id} do to fix the problem?",
            answer=f"{hero.id} changed into a softer sock and walked carefully.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a synagogue?",
            answer="A synagogue is a Jewish place for prayer, learning, and gathering together.",
        ),
        QAItem(
            question="What do sound effects like squeee show in a story?",
            answer="Sound effects help readers hear what a character hears, like a squeak, bang, or swish.",
        ),
        QAItem(
            question="Why can soft socks be better in a quiet place?",
            answer="Soft socks make less noise, so they are better when a place needs calm and careful steps.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    sock = world.facts["sock_cfg"]
    return [
        f"Write a short superhero story about {hero.id}, a noisy {sock.label}, and a synagogue.",
        f"Tell a child-friendly story with a sound effect like \"squeee\" and a lesson learned.",
        f"Write a gentle superhero story where a hero learns to move quietly in a synagogue.",
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story Q&A ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 3) for k, v in e.meters.items() if abs(v) > 1e-9}
        memes = {k: round(v, 3) for k, v in e.memes.items() if abs(v) > 1e-9}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.place != "synagogue":
        raise StoryError("This tiny world only supports the synagogue setting.")
    if params.sock not in SOCKS:
        raise StoryError("Unknown sock choice.")
    if not valid_sock(SOCKS[params.sock]):
        raise StoryError("The chosen sock is not noisy enough to drive the story.")

    world = build_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld with a synagogue, a noisy sock, sound effects, and a lesson learned.")
    ap.add_argument("--place", choices=["synagogue"], default="synagogue")
    ap.add_argument("--sock", choices=sorted(SOCKS), default=None)
    ap.add_argument("--hero-name", choices=HERO_NAMES, default=None)
    ap.add_argument("--sidekick-name", choices=SIDEKICK_NAMES, default=None)
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
    sock = args.sock or rng.choice(list(SOCKS))
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    sidekick = args.sidekick_name or rng.choice([n for n in SIDEKICK_NAMES if n != hero_name])
    return StoryParams(place="synagogue", sock=sock, hero_name=hero_name, sidekick_name=sidekick)


def asp_verify() -> int:
    import asp
    _ = asp.one_model(asp_program("#show problem/2. #show lesson/1. #show safe/1."))
    print("OK: ASP twin loads and solves.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show problem/2. #show lesson/1. #show safe/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for sock in sorted(SOCKS):
            params = StoryParams(place="synagogue", sock=sock, hero_name=HERO_NAMES[0], sidekick_name=SIDEKICK_NAMES[0])
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
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
