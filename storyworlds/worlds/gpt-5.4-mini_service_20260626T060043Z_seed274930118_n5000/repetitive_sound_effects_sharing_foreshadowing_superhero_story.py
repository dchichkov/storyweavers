#!/usr/bin/env python3
"""
storyworlds/worlds/repetitive_sound_effects_sharing_foreshadowing_superhero_story.py
====================================================================================

A small superhero-style story world with:
- repetitive sound effects
- sharing a tool or power
- foreshadowing that pays off in the ending

The simulated premise is simple: a young hero wants to help on a city day,
but the first plan is a little too hard to do alone. A helper, a shared item,
and a hinted detail from earlier make the ending work.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    shared_with: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"strength": 0.0, "sound": 0.0, "danger": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "brave": 0.0, "care": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "heroine"}
        male = {"boy", "man", "father", "hero"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the city"
    afforded: set[str] = field(default_factory=set)


@dataclass
class Challenge:
    id: str
    scene: str
    danger: str
    sound: str
    repeated_sound: str
    foreshadow: str
    payoff: str
    requires: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class ShareItem:
    id: str
    label: str
    phrase: str
    helps: set[str]
    shared_type: str = "thing"


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def heroes(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    setting: str
    challenge: str
    share_item: str
    hero: str
    sidekick: str
    seed: Optional[int] = None


SETTINGS = {
    "city": Setting(place="the city", afforded={"stomp", "storm", "glow"}),
    "bridge": Setting(place="the bridge", afforded={"stomp", "storm"}),
    "tower": Setting(place="the tower roof", afforded={"glow", "storm"}),
    "park": Setting(place="the park", afforded={"stomp", "glow"}),
}

CHALLENGES = {
    "stomp": Challenge(
        id="stomp",
        scene="a giant robot stomping by",
        danger="the ground shook every time it took a step",
        sound="BOOM",
        repeated_sound="boom-boom, boom-boom",
        foreshadow="A loose bolt on the robot's knee kept flashing in the sun.",
        payoff="That same bolt was easy to reach with a careful magnet tap.",
        requires={"tool"},
        tags={"robot", "metal", "sound"},
    ),
    "storm": Challenge(
        id="storm",
        scene="a windy storm spinning trash and rain",
        danger="the wind kept snatching things away",
        sound="WHOOOSH",
        repeated_sound="whoosh-whoosh, whoosh-whoosh",
        foreshadow="A bright kite string had wrapped around a pole earlier.",
        payoff="That string later became the safest line to guide the rescue.",
        requires={"line"},
        tags={"storm", "wind", "sound"},
    ),
    "glow": Challenge(
        id="glow",
        scene="a dark tunnel with a blinking light",
        danger="the shadows made every step feel tricky",
        sound="click",
        repeated_sound="click-click, click-click",
        foreshadow="A sign on the wall said the old lamp still worked if someone pressed it twice.",
        payoff="Two quick presses woke the lamp and lit the whole tunnel.",
        requires={"signal"},
        tags={"dark", "light", "sound"},
    ),
}

SHARE_ITEMS = {
    "magnet": ShareItem(
        id="magnet",
        label="a bright magnet",
        phrase="a bright magnet with a blue string",
        helps={"tool"},
    ),
    "kite_line": ShareItem(
        id="kite_line",
        label="a long kite line",
        phrase="a long kite line",
        helps={"line"},
    ),
    "flash_button": ShareItem(
        id="flash_button",
        label="a flash button",
        phrase="a little flash button",
        helps={"signal"},
    ),
}

HERO_NAMES = ["Nova", "Milo", "Ruby", "Zane", "Luna", "Iris", "Kai", "Aria"]
SIDEKICK_NAMES = ["Pip", "Bea", "Tess", "Nico", "Wren", "Jo", "Otis", "Zuri"]
TRAITS = ["brave", "kind", "quick", "tiny", "lively"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for setting_id, setting in SETTINGS.items():
        for challenge_id, challenge in CHALLENGES.items():
            if challenge_id not in setting.afforded:
                continue
            for item_id, item in SHARE_ITEMS.items():
                if challenge.requires & item.helps:
                    out.append((setting_id, challenge_id, item_id))
    return out


def explain_rejection(challenge: Challenge, item: ShareItem) -> str:
    return (
        f"(No story: {item.label} does not help with {challenge.scene}. "
        f"Pick a shared item that can actually solve the challenge.)"
    )


def explain_setting(setting_id: str, challenge_id: str) -> str:
    return (
        f"(No story: {SETTINGS[setting_id].place} does not fit the challenge "
        f"{challenge_id}.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Superhero story world with repetitive sound effects, sharing, and foreshadowing."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--share-item", choices=SHARE_ITEMS)
    ap.add_argument("--hero")
    ap.add_argument("--sidekick")
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
    if args.setting and args.challenge:
        if args.challenge not in SETTINGS[args.setting].afforded:
            raise StoryError(explain_setting(args.setting, args.challenge))
    if args.challenge and args.share_item:
        ch = CHALLENGES[args.challenge]
        item = SHARE_ITEMS[args.share_item]
        if not (ch.requires & item.helps):
            raise StoryError(explain_rejection(ch, item))

    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.challenge is None or c[1] == args.challenge)
              and (args.share_item is None or c[2] == args.share_item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, challenge, share_item = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(HERO_NAMES)
    sidekick = args.sidekick or rng.choice(SIDEKICK_NAMES)
    if sidekick == hero:
        sidekick = rng.choice([n for n in SIDEKICK_NAMES if n != hero])
    return StoryParams(setting=setting, challenge=challenge, share_item=share_item, hero=hero, sidekick=sidekick)


def _can_use(world: World, hero: Entity, item: Entity, challenge: Challenge) -> bool:
    return item.owner == hero.id and bool(challenge.requires & world.facts.get("share_item_helps", set()))


def tell(setting: Setting, challenge: Challenge, item_cfg: ShareItem, hero_name: str, sidekick_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="hero", traits=["little", "brave"]))
    sidekick = world.add(Entity(id=sidekick_name, kind="character", type="hero", traits=["helpful"]))
    item = world.add(Entity(id=item_cfg.id, label=item_cfg.label, phrase=item_cfg.phrase, owner=hero.id))
    item.shared_with.add(sidekick.id)

    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        item=item,
        item_cfg=item_cfg,
        challenge=challenge,
        setting=setting,
        share_item_helps=set(item_cfg.helps),
    )

    hero.memes["joy"] += 1
    world.say(f"{hero.id} was a little superhero who loved helping people.")
    world.say(f"{hero.id} carried {item_cfg.phrase}, and {sidekick.id} stayed close by.")

    world.para()
    world.say(f"One day at {setting.place}, there was {challenge.scene}.")
    world.say(f"It felt serious because {challenge.danger}.")
    world.say(f'It went "{challenge.sound}!" then "{challenge.repeated_sound}!" again and again.')
    world.say(challenge.foreshadow)

    world.para()
    hero.memes["worry"] += 1
    hero.meters["danger"] += 1
    world.say(f"{hero.id} wanted to help right away, but one hero alone could not do it safely.")
    world.say(f"{sidekick.id} looked at {hero.id} and said, 'We can share.'")
    world.say(f"{hero.id} held out {item_cfg.label}, and {sidekick.id} took one end or one turn with care.")
    item.shared_with.add(sidekick.id)
    hero.memes["care"] += 1
    sidekick.memes["care"] += 1

    world.para()
    if "tool" in item_cfg.helps:
        world.say(f"{hero.id} and {sidekick.id} used the magnet together: tap, tap, tap.")
    elif "line" in item_cfg.helps:
        world.say(f"{hero.id} and {sidekick.id} guided the rescue with the line: pull, pull, pull.")
    elif "signal" in item_cfg.helps:
        world.say(f"{hero.id} and {sidekick.id} pressed the button together: click-click, click-click.")
    world.say(challenge.payoff)
    hero.memes["joy"] += 2
    sidekick.memes["joy"] += 2
    hero.meters["strength"] += 1
    sidekick.meters["strength"] += 1
    world.say(f"At the end, {hero.id} and {sidekick.id} smiled, because sharing had made the job easier.")
    world.say(f'The city sounded safe again, with a last soft "tap-tap" / "whoosh-whoosh" / "click-click" fading away.')

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    ch = f["challenge"]
    item = f["item_cfg"]
    return [
        f'Write a short superhero story for a young child that includes the sound "{ch.sound}" and repeats it.',
        f"Tell a story where {f['hero'].id} and {f['sidekick'].id} share {item.label} to solve {ch.scene}.",
        f"Write a gentle superhero tale with foreshadowing, sharing, and a happy ending at {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    item = f["item_cfg"]
    ch = f["challenge"]
    place = f["setting"].place
    return [
        QAItem(
            question=f"Who was the story about at {place}?",
            answer=f"It was about {hero.id}, with help from {sidekick.id}.",
        ),
        QAItem(
            question=f"What did {hero.id} and {sidekick.id} share?",
            answer=f"They shared {item.label} so they could solve the problem together.",
        ),
        QAItem(
            question=f"What sound was repeated during the challenge?",
            answer=f'The story repeated "{ch.sound}" and also used "{ch.repeated_sound}".',
        ),
        QAItem(
            question="What hinted that the ending would work?",
            answer=f"{ch.foreshadow}",
        ),
        QAItem(
            question=f"How did the problem get fixed in the end?",
            answer=f"{ch.payoff} Then {hero.id} and {sidekick.id} finished the job together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    item = f["item_cfg"]
    ch = f["challenge"]
    out = [
        QAItem(
            question="What does it mean to share something?",
            answer="To share means to let another person use it too, or to take turns with it.",
        ),
        QAItem(
            question="What is a superhero?",
            answer="A superhero is a pretend hero with special courage who helps people and solves big problems.",
        ),
    ]
    if "tool" in item.helps:
        out.append(QAItem(
            question="What can a magnet do?",
            answer="A magnet can pull some metal things toward it.",
        ))
    if "line" in item.helps:
        out.append(QAItem(
            question="What is a line for?",
            answer="A line can help guide, hold, or pull something safely.",
        ))
    if "signal" in item.helps:
        out.append(QAItem(
            question="What is a signal?",
            answer="A signal is a small sign, light, or sound that tells people what to do.",
        ))
    if "sound" in ch.tags:
        out.append(QAItem(
            question="Why do sound effects matter in a story?",
            answer="Sound effects can make a story feel lively and help readers imagine what is happening.",
        ))
    return out


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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.shared_with:
            bits.append(f"shared_with={sorted(e.shared_with)}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="city", challenge="stomp", share_item="magnet", hero="Nova", sidekick="Pip"),
    StoryParams(setting="bridge", challenge="storm", share_item="kite_line", hero="Milo", sidekick="Bea"),
    StoryParams(setting="tower", challenge="glow", share_item="flash_button", hero="Ruby", sidekick="Nico"),
]


ASP_RULES = r"""
valid_combo(S,C,I) :- setting(S), challenge(C), item(I), affords(S,C), helps(I,H), needs(C,H).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for ch in sorted(s.afforded):
            lines.append(asp.fact("affords", sid, ch))
    for cid, c in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        for req in sorted(c.requires):
            lines.append(asp.fact("needs", cid, req))
    for iid, it in SHARE_ITEMS.items():
        lines.append(asp.fact("item", iid))
        for h in sorted(it.helps):
            lines.append(asp.fact("helps", iid, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], CHALLENGES[params.challenge], SHARE_ITEMS[params.share_item], params.hero, params.sidekick)
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
        print(asp_program("#show valid_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero}: {p.challenge} at {p.setting} using {p.share_item}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
