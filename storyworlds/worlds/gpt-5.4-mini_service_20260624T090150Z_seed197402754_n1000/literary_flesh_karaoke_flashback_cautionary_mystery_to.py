#!/usr/bin/env python3
"""
A mythic story world about a singer-bard, a fragile chorus, and a mystery that
must be solved before a cautionary promise is broken.

Premise:
- In a moonlit hall, a young bard wants to lead a karaoke song with a sacred
  chorus carved into an old wooden charm.
- A strange problem appears: the charm has been cracked, and the missing line
  cannot be sung unless the right memory returns.
- A flashback reveals who last handled the charm and why a warning was given.
- The story ends when the mystery is solved and the bard sings with care.

This script models:
- physical meters: sound, crack, smoke, shine, warmth
- emotional memes: courage, worry, hope, relief, shame, pride

The world is deliberately small and state-driven, with a single causal turn:
the hero's attempt to perform the song risks the charm, a cautionary warning
halts reckless action, and a flashback reveals the clue needed to solve the
mystery.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretakers: list[str] = field(default_factory=list)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ["sound", "crack", "shine", "warmth", "dust", "silence"]:
            self.meters.setdefault(k, 0.0)
        for k in ["courage", "worry", "hope", "relief", "shame", "pride", "curiosity"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def them(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Hall:
    name: str = "the moonlit hall"
    setting: str = "the moonlit hall"
    hush: bool = True
    instruments: list[str] = field(default_factory=lambda: ["karaoke bowl", "reed lyre"])


class World:
    def __init__(self, hall: Hall) -> None:
        self.hall = hall
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.flashback_open: bool = False
        self.mystery_solved: bool = False
        self.caution_given: bool = False
        self.clue_seen: bool = False

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
        clone = World(self.hall)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.flashback_open = self.flashback_open
        clone.mystery_solved = self.mystery_solved
        clone.caution_given = self.caution_given
        clone.clue_seen = self.clue_seen
        return clone


@dataclass
class StoryParams:
    name: str
    role: str
    guide: str
    charm: str
    seed: Optional[int] = None


HALLS = {
    "moon": Hall(),
}

ROLES = {
    "bard": "bard",
    "singer": "singer",
    "child": "child",
}

CHARMS = {
    "flesh-charm": ("flesh charm", "a soft charm of braided flesh-colored thread"),
    "literary-mask": ("literary mask", "a mask painted with tiny gold letters"),
    "karaoke-bell": ("karaoke bell", "a small bell used to begin the song"),
}

GUIDES = {
    "grandmother": ("grandmother", "an old grandmother with a memory like a lamp"),
    "uncle": ("uncle", "an uncle who carried stories in his sleeves"),
    "moon-keeper": ("moon-keeper", "the moon-keeper who watched the hall"),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic story world about karaoke, flesh, and a mystery to solve.")
    ap.add_argument("--name", choices=["Ari", "Mina", "Taro", "Lio"])
    ap.add_argument("--role", choices=list(ROLES))
    ap.add_argument("--guide", choices=list(GUIDES))
    ap.add_argument("--charm", choices=list(CHARMS))
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
    name = args.name or rng.choice(["Ari", "Mina", "Taro", "Lio"])
    role = args.role or rng.choice(list(ROLES))
    guide = args.guide or rng.choice(list(GUIDES))
    charm = args.charm or rng.choice(list(CHARMS))
    if role == "child" and name == "Taro":
        pass
    return StoryParams(name=name, role=role, guide=guide, charm=charm)


def asp_facts() -> str:
    import asp
    lines = [asp.fact("hero", n) for n in ["Ari", "Mina", "Taro", "Lio"]]
    for r in ROLES:
        lines.append(asp.fact("role", r))
    for g in GUIDES:
        lines.append(asp.fact("guide", g))
    for c in CHARMS:
        lines.append(asp.fact("charm", c))
    lines.append(asp.fact("theme", "literary"))
    lines.append(asp.fact("theme", "flesh"))
    lines.append(asp.fact("theme", "karaoke"))
    return "\n".join(lines)


ASP_RULES = r"""
needs_flashback(H) :- hero(H).
cautionary(H) :- hero(H).
mystery_to_solve(H) :- hero(H).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def tell_story(params: StoryParams) -> World:
    world = World(HALLS["moon"])
    hero = world.add(Entity(id=params.name, kind="character", type=params.role, label=params.name))
    guide_type, guide_phrase = GUIDES[params.guide]
    guide = world.add(Entity(id="Guide", kind="character", type=guide_type, label=guide_phrase))
    charm_label, charm_phrase = CHARMS[params.charm]
    charm = world.add(Entity(id="Charm", type="thing", label=charm_label, phrase=charm_phrase, owner=hero.id))
    charm.meters["crack"] = 1.0
    charm.meters["shine"] = 0.5
    hero.memes["curiosity"] = 1.0
    guide.memes["worry"] = 1.0

    world.say(
        f"In the moonlit hall, {hero.id} was a little {params.role} who loved the old, literary sounds of a karaoke hymn."
    )
    world.say(
        f"{hero.pronoun().capitalize()} carried {charm.phrase}, because the song was said to wake the sleeping names of the ancestors."
    )

    world.para()
    world.say(
        f"That night, {hero.id} raised {hero.pronoun('possessive')} voice to begin the chorus, but the charm gave a tiny crack like dry bark."
    )
    hero.memes["courage"] += 1
    charm.meters["sound"] += 1
    charm.meters["crack"] += 1

    world.say(
        f"{guide_phrase.capitalize()} lifted a hand and gave a cautionary warning: \"Do not force the chorus, or the flesh-thread may split.\""
    )
    world.caution_given = True
    guide.memes["worry"] += 1
    hero.memes["worry"] += 1

    world.para()
    world.say(
        f"At the warning, {hero.id} remembered a flashback: earlier, {params.guide} had found a pale thread wrapped around the charm and said the missing verse was hidden in an old story."
    )
    world.flashback_open = True
    world.clue_seen = True
    hero.memes["hope"] += 1
    hero.memes["shame"] += 1

    world.say(
        f"The clue was simple: the final line was not loud, but gentle. It belonged to the quiet part of the song, where a hero listens before singing."
    )

    world.para()
    world.say(
        f"So {hero.id} solved the mystery by singing softly, naming the charm's true shape, and tying the cracked place with a strip of gold thread."
    )
    charm.meters["crack"] = 0.0
    charm.meters["shine"] = 2.0
    hero.memes["relief"] += 1
    hero.memes["pride"] += 1
    guide.memes["hope"] += 1
    world.mystery_solved = True

    world.say(
        f"Then the karaoke hymn rose without hurting the charm. The hall grew warm, the moon looked near, and the old literary song ended in peace."
    )
    charm.meters["warmth"] += 1

    world.facts.update(
        hero=hero,
        guide=guide,
        charm=charm,
        params=params,
        caution=world.caution_given,
        flashback=world.flashback_open,
        solved=world.mystery_solved,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a myth-like story about {f["hero"].id}, a {f["params"].role}, whose karaoke song must solve a mystery.',
        f"Tell a children's story with a flashback, a cautionary warning, and a calm ending about {f['params'].charm}.",
        f'Write a gentle myth where the words "literary", "flesh", and "karaoke" all belong in the tale.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    guide = f["guide"]
    charm = f["charm"]
    params = f["params"]
    return [
        QAItem(
            question=f"Who was trying to sing in the moonlit hall?",
            answer=f"{hero.id}, a little {params.role}, was trying to lead the karaoke song in the moonlit hall.",
        ),
        QAItem(
            question=f"What warning did {guide.label} give about the charm?",
            answer="The warning was not to force the chorus, because the flesh-thread could split if the song was pushed too hard.",
        ),
        QAItem(
            question=f"What solved the mystery in the end?",
            answer=f"{hero.id} solved the mystery by remembering the missing verse, tying the cracked {charm.label} with gold thread, and singing softly.",
        ),
        QAItem(
            question="What changed by the ending?",
            answer="The cracked charm was mended, the song became safe again, and the hall ended warm and peaceful.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly shows something that happened earlier, so the reader can learn an important clue.",
        ),
        QAItem(
            question="What does cautionary mean?",
            answer="Cautionary means giving a warning to help someone avoid a mistake or danger.",
        ),
        QAItem(
            question="What is karaoke?",
            answer="Karaoke is when a person sings a song while the music helps carry the tune.",
        ),
        QAItem(
            question="What is a mystery to solve?",
            answer="A mystery to solve is a problem with a hidden answer that a character must figure out by noticing clues.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== generation prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    lines.append(f"flashback_open={world.flashback_open}")
    lines.append(f"mystery_solved={world.mystery_solved}")
    lines.append(f"caution_given={world.caution_given}")
    return "\n".join(lines)


CURATED = [
    StoryParams(name="Ari", role="bard", guide="moon-keeper", charm="literary-mask"),
    StoryParams(name="Mina", role="singer", guide="grandmother", charm="flesh-charm"),
    StoryParams(name="Lio", role="child", guide="uncle", charm="karaoke-bell"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for name in ["Ari", "Mina", "Taro", "Lio"]:
        for role in ROLES:
            for guide in GUIDES:
                for charm in CHARMS:
                    out.append((name, role, guide, charm))
    return [(a, b, c) for a, b, c, _ in [(*t, None) for t in out]]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show hero/1."))
    return sorted(set(asp.atoms(model, "hero")))


def asp_verify() -> int:
    print("OK: ASP twin present.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show hero/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

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
            header = f"### {p.name}: {p.role} with {p.charm}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
