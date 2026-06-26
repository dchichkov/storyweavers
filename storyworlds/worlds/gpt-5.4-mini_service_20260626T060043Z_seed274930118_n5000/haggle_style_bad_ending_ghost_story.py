#!/usr/bin/env python3
"""
storyworlds/worlds/haggle_style_bad_ending_ghost_story.py
=========================================================

A small ghost-story world about a child haggling for a spooky bargain.
The domain is intentionally tight: one setting, one style, one tension,
and one bad ending.

Seed idea:
- A child meets a ghostly seller at dusk.
- They haggle over a lantern, charm, or keepsake.
- The child pushes too hard.
- The bargain goes wrong, and the story ends with a cold, eerie loss.

The world model tracks physical meters and emotional memes so the prose
is driven by state rather than by a frozen template.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "ghostgirl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "ghostboy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    style: str = "ghost story"
    spooky: bool = True
    afford: set[str] = field(default_factory=set)


@dataclass
class Want:
    id: str
    verb: str
    noun: str
    bargain_topic: str
    risk: str
    tension: str
    outcome: str


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    spooky: bool = True


@dataclass
class StoryParams:
    setting: str
    want: str
    prize: str
    name: str
    gender: str
    seed: Optional[int] = None


SETTINGS = {
    "lantern_shop": Setting(
        place="the lantern shop at the edge of town",
        style="ghost story",
        spooky=True,
        afford={"haggle"},
    ),
    "graveyard_stall": Setting(
        place="a little stall by the graveyard gate",
        style="ghost story",
        spooky=True,
        afford={"haggle"},
    ),
    "fog_road": Setting(
        place="a cart on the fog road",
        style="ghost story",
        spooky=True,
        afford={"haggle"},
    ),
}

WANTS = {
    "lantern": Want(
        id="lantern",
        verb="haggle for a lantern",
        noun="lantern",
        bargain_topic="price",
        risk="the flame might go out in the dark",
        tension="the ghost would not lower the price",
        outcome="the lantern went cold in her hands",
    ),
    "style": Want(
        id="style",
        verb="haggle for a strange style of cloak",
        noun="cloak",
        bargain_topic="style",
        risk="the cloak might cling like a shadow",
        tension="the ghost kept calling it a better style",
        outcome="the cloak fit like a midnight shiver",
    ),
    "charm": Want(
        id="charm",
        verb="haggle for a silver charm",
        noun="charm",
        bargain_topic="price",
        risk="the charm might bring bad luck",
        tension="the ghost wanted one more coin",
        outcome="the charm rang once and turned black",
    ),
}

PRIZES = {
    "coin_pouch": Prize(id="coin_pouch", label="coin pouch", phrase="a small coin pouch"),
    "red_scarf": Prize(id="red_scarf", label="red scarf", phrase="a bright red scarf"),
    "brass_key": Prize(id="brass_key", label="brass key", phrase="an old brass key"),
}

GIRL_NAMES = ["Mina", "Eve", "Lia", "Nora", "Ivy", "June"]
BOY_NAMES = ["Theo", "Finn", "Leo", "Miles", "Noah", "Jude"]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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

        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def _ghost_bargain(world: World, child: Entity, ghost: Entity, want: Want, prize: Prize) -> None:
    child.memes["want"] = child.memes.get("want", 0.0) + 1
    ghost.memes["cold"] = ghost.memes.get("cold", 0.0) + 1
    world.say(
        f"At {world.setting.place}, {child.id} found {ghost.pronoun('object')} waiting beside a table of dim things."
    )
    world.say(
        f'The ghost said, "{want.noun}s are rare tonight. You may have one if you can pay the right price."'
    )
    world.say(
        f"{child.id} wanted to {want.verb}, because {want.risk}."
    )


def _haggle(world: World, child: Entity, ghost: Entity, want: Want, prize: Prize) -> None:
    child.memes["greed"] = child.memes.get("greed", 0.0) + 1
    ghost.memes["patience"] = ghost.memes.get("patience", 0.0) - 1
    world.say(
        f"{child.id} haggled hard about the {want.bargain_topic}, but {want.tension}."
    )
    world.say(
        f"{ghost.id} tapped {ghost.pronoun('possessive')} fingers on the table and the fog seemed to listen."
    )


def _bad_turn(world: World, child: Entity, ghost: Entity, want: Want, prize: Prize) -> None:
    child.memes["fear"] = child.memes.get("fear", 0.0) + 1
    child.meters["chill"] = child.meters.get("chill", 0.0) + 1
    ghost.meters["cold"] = ghost.meters.get("cold", 0.0) + 1
    world.say(
        f"Then the ghost smiled with no warmth at all and agreed."
    )
    world.say(
        f"{child.id} reached for the {prize.label}, but {want.outcome}."
    )


def _ending(world: World, child: Entity, ghost: Entity, want: Want, prize: Prize) -> None:
    child.meters["loss"] = child.meters.get("loss", 0.0) + 1
    child.memes["regret"] = child.memes.get("regret", 0.0) + 1
    world.say(
        f"By the time {child.id} looked up, the stall was smaller, the fog was thicker, and the {prize.label} was gone."
    )
    world.say(
        f"{child.id} walked home with empty hands, while a thin voice drifted from the dark: 'Next time, pay before you bargain.'"
    )


def tell(setting: Setting, want: Want, prize: Prize, hero_name: str, gender: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=gender, label=hero_name))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", label="the ghost"))
    trinket = world.add(Entity(id=prize.id, type="thing", label=prize.label, phrase=prize.phrase, owner=ghost.id))

    world.say(
        f"At dusk, {hero.id} went to {setting.place}, where the air already felt old."
    )
    world.say(
        f"On a crooked table sat {trinket.phrase}, and behind it hovered {ghost.label}."
    )
    _ghost_bargain(world, hero, ghost, want, trinket)
    world.para()
    _haggle(world, hero, ghost, want, trinket)
    _bad_turn(world, hero, ghost, want, trinket)
    world.para()
    _ending(world, hero, ghost, want, trinket)

    world.facts.update(hero=hero, ghost=ghost, prize=trinket, want=want, setting=setting)
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting_id, setting in SETTINGS.items():
        if "haggle" not in setting.afford:
            continue
        for want_id in WANTS:
            for prize_id in PRIZES:
                combos.append((setting_id, want_id, prize_id))
    return combos


def explain_rejection(setting_id: str, want_id: str, prize_id: str) -> str:
    return f"(No story: {setting_id}, {want_id}, and {prize_id} do not form a ghostly haggling scene.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small ghost-story world about haggling and a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--want", choices=WANTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.want is None or c[1] == args.want)
        and (args.prize is None or c[2] == args.prize)
    ]
    if not combos:
        raise StoryError("(No valid ghost-haggle combination matches the given options.)")
    setting, want, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(setting=setting, want=want, prize=prize, name=name, gender=gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short ghost story for a child about a {f["want"].noun} and a bargain gone wrong.',
        f"Tell a spooky tale where {f['hero'].id} tries to haggle at {f['setting'].place}.",
        f'Write a ghost story with the word "{f["want"].id}" and a bad ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    want = f["want"]
    prize = f["prize"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Where did {hero.id} meet the ghost?",
            answer=f"{hero.id} met the ghost at {setting.place}, where everything felt quiet and strange.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do?",
            answer=f"{hero.id} wanted to {want.verb}, but the ghost kept asking for a higher price.",
        ),
        QAItem(
            question=f"What happened at the end?",
            answer=f"The bargain went badly, and {hero.id} lost the {prize.label} and walked home with empty hands.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ghost story?",
            answer="A ghost story is a spooky tale about a ghost, a strange place, and something eerie that happens.",
        ),
        QAItem(
            question="What does it mean to haggle?",
            answer="To haggle means to argue about a price and try to make it lower or better.",
        ),
        QAItem(
            question="Why can a bad ending feel scary?",
            answer="A bad ending can feel scary because the danger is not fixed and the character goes away unhappy or unsafe.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], WANTS[params.want], PRIZES[params.prize], params.name, params.gender)
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
setting(S) :- setting_id(S).
want(W) :- want_id(W).
prize(P) :- prize_id(P).

valid(S,W,P) :- setting(S), want(W), prize(P), afford_haggle(S).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting_id", sid))
        if "haggle" in s.afford:
            lines.append(asp.fact("afford_haggle", sid))
    for wid in WANTS:
        lines.append(asp.fact("want_id", wid))
    for pid in PRIZES:
        lines.append(asp.fact("prize_id", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print(" only in python:", sorted(py - cl))
    print(" only in clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for s in sorted(SETTINGS):
            for w in sorted(WANTS):
                for p in sorted(PRIZES):
                    params = StoryParams(setting=s, want=w, prize=p, name="Mina", gender="girl")
                    samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
