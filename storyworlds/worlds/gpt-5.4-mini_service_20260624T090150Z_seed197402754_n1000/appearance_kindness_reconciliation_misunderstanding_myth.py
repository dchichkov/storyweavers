#!/usr/bin/env python3
"""
A small mythic storyworld: a traveler, a strange appearance, a misunderstanding,
and a reconciliation made through kindness.

The seed tale behind this world:
---
A young shepherd saw a hooded stranger at the well and thought the stranger was
a hungry beggar. The shepherd offered bread and water. When the stranger lifted
the hood, he was a silver-haired god in plain clothes testing the shepherd's
heart. The god blessed the shepherd's village, and the shepherd understood that
kindness could see past appearance.
---
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


# ---------------------------------------------------------------------------
# Core world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "goddess", "maiden"}
        male = {"boy", "man", "father", "god", "shepherd"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the well"
    kind: str = "sacred"
    detail: str = "a stone well under an old fig tree"


@dataclass
class Glamour:
    id: str
    appearance: str
    cause: str
    truth: str
    reveal: str


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    blessing: str
    outcome: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "well": Setting(place="the well", kind="sacred", detail="a stone well under an old fig tree"),
    "gate": Setting(place="the city gate", kind="public", detail="a bronze gate where dust and sun met"),
    "shore": Setting(place="the shore", kind="wild", detail="a bright shore where gulls cried over the water"),
}

GLAMOURS = {
    "hood": Glamour(
        id="hood",
        appearance="a hooded stranger",
        cause="a shadowed cloak and dust from the road",
        truth="a divine visitor in plain clothes",
        reveal="When the hood fell back, silver hair shone like moonlight.",
    ),
    "ash": Glamour(
        id="ash",
        appearance="a tired old woman",
        cause="gray ash from the hearth and a bent walking stick",
        truth="a river goddess in disguise",
        reveal="When she smiled, the ash on her hands turned to sparks.",
    ),
    "mist": Glamour(
        id="mist",
        appearance="a pale child",
        cause="sea mist and a shell-white veil",
        truth="a sea spirit looking for kindness",
        reveal="When the veil lifted, salt-water light flashed in her eyes.",
    ),
}

GIFTS = {
    "bread": Gift(
        id="bread",
        label="bread",
        phrase="warm bread and a cup of water",
        blessing="the village wells would stay full",
        outcome="the fields grew green even in a dry season",
    ),
    "cloak": Gift(
        id="cloak",
        label="cloak",
        phrase="a wool cloak and a quiet seat by the fire",
        blessing="the hearth would never go cold",
        outcome="every doorway felt safer after that night",
    ),
    "shell": Gift(
        id="shell",
        label="shell",
        phrase="a clean shell bowl and a smile",
        blessing="the tide would bring fish in abundance",
        outcome="the shore shimmered with silver nets at dawn",
    ),
}

HEROES = [
    ("shepherd", "boy", ["brave", "thoughtful"]),
    ("miller", "girl", ["gentle", "curious"]),
    ("fisher", "girl", ["kind", "patient"]),
]

NAMES = {
    "boy": ["Eli", "Theon", "Arin", "Levi", "Maro"],
    "girl": ["Nia", "Lina", "Sera", "Mira", "Tala"],
}


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    glamour: str
    gift: str
    hero_name: str
    hero_type: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World actions and narration
# ---------------------------------------------------------------------------
class StoryWorld:
    def __init__(self, setting: Setting, glamour: Glamour, gift: Gift, hero_name: str, hero_type: str) -> None:
        self.world = World(setting)
        self.setting = setting
        self.glamour = glamour
        self.gift = gift

        self.hero = self.world.add(
            Entity(
                id=hero_name,
                kind="character",
                type=hero_type,
                traits=["young"],
                meters={"courage": 0.0},
                memes={"kindness": 0.0, "worry": 0.0, "understanding": 0.0, "reconciliation": 0.0},
            )
        )
        self.stranger = self.world.add(
            Entity(
                id="stranger",
                kind="character",
                type="god" if "god" in glamour.truth else "woman",
                label=glamour.appearance,
                phrase=glamour.appearance,
                traits=["mysterious"],
                meters={"mystery": 1.0},
                memes={"hidden_truth": 1.0},
            )
        )
        self.village = self.world.add(
            Entity(
                id="village",
                kind="thing",
                type="place",
                label="the village",
                phrase="the village",
                meters={"peace": 0.0, "need": 1.0},
            )
        )

    def tell(self) -> World:
        self._opening()
        self.world.para()
        self._misunderstanding()
        self.world.para()
        self._kindness_reveal_reconcile()
        return self.world

    def _opening(self) -> None:
        self.world.say(
            f"Long ago, near {self.setting.place}, there lived {self.hero.id}, "
            f"a young {self.hero.type} with a heart that noticed small things."
        )
        self.world.say(
            f"One morning, {self.hero.id} saw {self.stranger.phrase} beside the water."
        )
        self.world.say(
            f"{self.stranger.phrase.capitalize()} looked like {self.glamour.appearance} because of {self.glamour.cause}."
        )
        self.hero.memes["curiosity"] = 1.0

    def _misunderstanding(self) -> None:
        self.hero.memes["worry"] += 1.0
        self.hero.memes["misunderstanding"] = 1.0
        self.world.say(
            f"{self.hero.id} thought the stranger was only a weary traveler and not a being of power."
        )
        self.world.say(
            f"So {self.hero.id} brought {self.gift.phrase}, because kindness felt wiser than fear."
        )
        self.hero.memes["kindness"] += 1.0
        self.hero.meters["courage"] += 1.0

    def _kindness_reveal_reconcile(self) -> None:
        self.stranger.memes["moved"] = 1.0
        self.hero.memes["understanding"] += 1.0
        self.hero.memes["reconciliation"] += 1.0
        self.village.meters["peace"] += 1.0
        self.village.meters["need"] = 0.0
        self.world.say(
            f"The stranger took the gift and smiled."
        )
        self.world.say(
            f'"{self.gift.blessing}," said the stranger, and then the truth came clear.'
        )
        self.world.say(
            f"{self.glamour.reveal} {self.hero.id} bowed, ashamed of the mistake, but the stranger only laughed softly."
        )
        self.world.say(
            f"{self.hero.id} and the stranger forgave the misunderstanding, and {self.gift.outcome}."
        )
        self.world.say(
            f"From then on, people said that kindness could see past appearance and make peace where doubt had stood."
        )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A stranger's appearance can mislead when the outer sign hides the true form.
misunderstanding(H, S) :- sees(H, S), masked(S), thinks_plain(H, S).

% Kindness answers misunderstanding when the hero offers food, shelter, or care.
kindness(H) :- offers(H, _).
reconciliation(H, S) :- misunderstanding(H, S), kindness(H), revealed(S).

% A blessing follows reconciliation in the mythic pattern.
blessed(V) :- reconciliation(_, _), village(V).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("place_name", sid, s.place))
    for gid, g in GLAMOURS.items():
        lines.append(asp.fact("glamour", gid))
        lines.append(asp.fact("appearance", gid, g.appearance))
        lines.append(asp.fact("masked", gid))
        lines.append(asp.fact("truth", gid, g.truth))
    for gift_id, gift in GIFTS.items():
        lines.append(asp.fact("gift", gift_id))
        lines.append(asp.fact("offers", "hero", gift_id))
    lines.append(asp.fact("sees", "hero", "stranger"))
    lines.append(asp.fact("thinks_plain", "hero", "stranger"))
    lines.append(asp.fact("revealed", "stranger"))
    lines.append(asp.fact("village", "village"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show reconciliation/2. #show blessed/1."))
    rec = set(asp.atoms(model, "reconciliation"))
    bless = set(asp.atoms(model, "blessed"))
    py = {("hero", "stranger")}
    if rec == py and bless == {("village",)}:
        print("OK: ASP parity holds.")
        return 0
    print("MISMATCH between ASP and Python reasoning.")
    print("  reconciliation:", sorted(rec))
    print("  blessed:", sorted(bless))
    return 1


# ---------------------------------------------------------------------------
# Q&A and prose
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short myth about {f["hero"].id}, {f["glamour"].appearance}, and the power of kindness.',
        f"Tell a gentle legend in which {f['hero'].id} misunderstands a stranger but later reconciles after giving {f['gift'].label}.",
        f'Write a child-friendly myth that includes the word "appearance" and ends with peace in the village.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    glamour = f["glamour"]
    gift = f["gift"]
    return [
        QAItem(
            question=f"What did {hero.id} first think the stranger was?",
            answer=f"{hero.id} first thought the stranger was just {glamour.appearance}, a tired-looking traveler, because of {glamour.cause}.",
        ),
        QAItem(
            question=f"What did {hero.id} do to show kindness?",
            answer=f"{hero.id} offered {gift.phrase} instead of turning away.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer=f"The misunderstanding ended, the truth was revealed, and {hero.id} reconciled with the stranger. The village was left in peace.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is appearance?",
            answer="Appearance is the way something or someone looks on the outside.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means choosing to help, share, or care about someone in a gentle way.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop being upset and make peace after a disagreement or mistake.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks something is true, but later learns they were wrong.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Validation and generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic storyworld about appearance, kindness, misunderstanding, and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--glamour", choices=GLAMOURS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=["boy", "girl"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    glamour = args.glamour or rng.choice(list(GLAMOURS))
    gift = args.gift or rng.choice(list(GIFTS))
    hero_type = args.hero_type or rng.choice(["boy", "girl"])
    hero_name = args.name or rng.choice(NAMES[hero_type])
    return StoryParams(setting=setting, glamour=glamour, gift=gift, hero_name=hero_name, hero_type=hero_type)


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    glamour = GLAMOURS[params.glamour]
    gift = GIFTS[params.gift]
    sw = StoryWorld(setting, glamour, gift, params.hero_name, params.hero_type)
    world = sw.tell()
    world.facts = {"hero": sw.hero, "glamour": glamour, "gift": gift, "setting": setting}
    return world


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
        print(asp_program("#show reconciliation/2. #show blessed/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show reconciliation/2. #show blessed/1."))
        print(f"reconciliation: {sorted(set(asp.atoms(model, 'reconciliation')))}")
        print(f"blessed: {sorted(set(asp.atoms(model, 'blessed')))}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        combos = [(s, g, gift) for s in SETTINGS for g in GLAMOURS for gift in GIFTS]
        for i, (s, g, gift) in enumerate(combos[: max(args.n, len(combos))]):
            params = StoryParams(setting=s, glamour=g, gift=gift, hero_name="Ari", hero_type="boy", seed=base_seed + i)
            samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
