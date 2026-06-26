#!/usr/bin/env python3
"""
A small pirate-tale storyworld about a bronco, a shoe-dim harbor, bravery,
sharing, and the lesson learned when the right help is offered at the right
time.

The story premise:
- A child pirate and a captain spot a frightened bronco near the shoe-dim dock.
- The child is afraid at first, but the captain reminds them that bravery is
  taking a careful step.
- The child shares food and a rope, the bronco calms, and the child learns that
  sharing can be the kindest brave choice.

This file is standalone and follows the storyworld contract:
- StoryParams plus registries
- build_parser, resolve_params, generate, emit, main
- lazy ASP import in helper functions only
- QA, trace, JSON, ASP, verify, show-asp support
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    dim: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Encounter:
    id: str
    verb: str
    gerund: str
    risk: str
    calm: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Helper:
    id: str
    label: str
    fix: str
    share_item: str
    guards: set[str]
    covers: set[str]


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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_bravery(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts.get("hero")
    if not hero:
        return out
    e = world.get(hero.id)
    if e.memes.get("fear", 0.0) >= THRESHOLD and e.memes.get("resolve", 0.0) >= THRESHOLD:
        sig = ("bravery", e.id)
        if sig not in world.fired:
            world.fired.add(sig)
            e.memes["bravery"] = max(e.memes.get("bravery", 0.0), 1.0)
            out.append(f"{e.id} found a brave breath and took one careful step forward.")
    return out


def _r_sharing(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts.get("hero")
    bronco = world.facts.get("bronco")
    if not hero or not bronco:
        return out
    h = world.get(hero.id)
    b = world.get(bronco.id)
    if h.meters.get("shared_food", 0.0) >= THRESHOLD or h.meters.get("shared_rope", 0.0) >= THRESHOLD:
        sig = ("sharing", h.id, b.id)
        if sig not in world.fired:
            world.fired.add(sig)
            b.meters["calm"] = b.meters.get("calm", 0.0) + 1
            h.memes["kindness"] = h.memes.get("kindness", 0.0) + 1
            out.append("The bronco's eyes softened because the child shared kindly.")
    return out


def _r_lesson(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts.get("hero")
    if not hero:
        return out
    h = world.get(hero.id)
    bronco = world.facts.get("bronco")
    b = world.get(bronco.id)
    if h.memes.get("bravery", 0.0) >= THRESHOLD and h.memes.get("kindness", 0.0) >= THRESHOLD:
        sig = ("lesson", h.id)
        if sig not in world.fired:
            world.fired.add(sig)
            h.memes["lesson_learned"] = 1.0
            out.append("The child learned that brave sharing can be the safest kind of heroism.")
    return out


RULES = [_r_bravery, _r_sharing, _r_lesson]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)


SETTINGS = {
    "shoe_dim_dock": Setting(place="the shoe-dim dock", dim=True, affords={"meeting"}),
    "moon_wharf": Setting(place="the moon wharf", dim=True, affords={"meeting"}),
}

ENCOUNTERS = {
    "bronco": Encounter(
        id="bronco",
        verb="approach the bronco",
        gerund="approaching the bronco",
        risk="frightened",
        calm="less frightened",
        zone={"dock"},
        keyword="bronco",
        tags={"bronco"},
    )
}

PRIZES = {
    "rope": Prize(label="rope", phrase="a coiled harbor rope", type="rope", region="hands", plural=False),
    "apple": Prize(label="apple", phrase="a red apple bundle", type="apple", region="hands", plural=False),
}

HELPERS = {
    "lantern": Helper(
        id="lantern",
        label="a lantern",
        fix="held the lantern high so the child could see the bronco clearly",
        share_item="lantern light",
        guards={"dark"},
        covers={"eyes"},
    ),
    "rope_share": Helper(
        id="rope_share",
        label="the spare rope",
        fix="shared the spare rope so the bronco would feel less trapped",
        share_item="rope",
        guards={"tangled"},
        covers={"hooves"},
    ),
}

NAMES = ["Mara", "Nell", "Pip", "Rory", "Tessa", "Finn", "Wren", "Bea"]
TRAITS = ["brave", "curious", "gentle", "steady", "spry"]


@dataclass
class StoryParams:
    place: str
    encounter: str
    helper: str
    prize: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld: bronco, shoe-dim, bravery, sharing, lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--encounter", choices=ENCOUNTERS)
    ap.add_argument("--helper", choices=HELPERS)
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
    if args.gender and args.name is None:
        pass
    place = args.place or rng.choice(list(SETTINGS))
    encounter = args.encounter or "bronco"
    helper = args.helper or rng.choice(list(HELPERS))
    prize = args.prize or rng.choice(list(PRIZES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, encounter=encounter, helper=helper, prize=prize, name=name, gender=gender, trait=trait)


def _article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    captain = world.add(Entity(id="Captain", kind="character", type="captain", label="the captain"))
    bronco = world.add(Entity(id="Bronco", kind="character", type="bronco", label="the bronco"))
    prize = world.add(Entity(id="Prize", type=params.prize, label=PRIZES[params.prize].label, phrase=PRIZES[params.prize].phrase))
    helper = HELPERS[params.helper]

    hero.memes.update({"fear": 0.0, "resolve": 0.0, "bravery": 0.0, "kindness": 0.0})
    bronco.meters.update({"calm": 0.0, "tied": 0.0})

    world.say(f"{hero.id} was a {params.trait} little pirate who sailed past the {setting.place}.")
    world.say(f"One dim evening, {hero.id} spotted {world.facts.setdefault('bronco_word', 'the bronco')} near the shoe-dim dock.")
    world.say(f"The bronco was skittish, and the tide made everything look a little gray.")

    world.para()
    hero.memes["fear"] += 1
    world.say(f"{hero.id} wanted to {ENCOUNTERS['bronco'].verb}, but {hero.pronoun('possessive')} knees shook.")
    world.say(f'The captain said, "Bravery is not being unafraid. Bravery is taking the kind step anyway."')
    hero.memes["resolve"] += 1

    if params.helper == "lantern":
        world.say(f"Then {hero.id} carried {helper.label} and {helper.fix}.")
    else:
        world.say(f"Then {hero.id} offered {helper.label} and {helper.fix}.")
    world.say(f"{hero.id} also shared {PRIZES[params.prize].phrase} with the bronco.")
    hero.meters["shared_food" if params.prize == "apple" else "shared_rope"] = 1.0

    propagate(world, narrate=True)

    world.para()
    if bronco.meters.get("calm", 0.0) >= THRESHOLD:
        world.say(f"The bronco stopped trembling and leaned in with a soft, warm nicker.")
    world.say(f"{hero.id} smiled and learned that sharing could make a brave moment kinder.")
    world.say(f"By the end, the shoe-dim dock seemed brighter, and the bronco walked beside {hero.id} without fear.")

    world.facts.update(
        hero=hero,
        captain=captain,
        bronco=bronco,
        prize=prize,
        helper=helper,
        params=params,
        setting=setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f"Write a short pirate tale for a child named {hero.id} about a bronco on a shoe-dim dock.",
        f"Tell a gentle story where bravery and sharing help a little pirate and a bronco feel safe.",
        f"Write a child-facing pirate story that includes the words bronco and shoe-dim and ends with a lesson learned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    bronco = f["bronco"]
    return [
        QAItem(
            question=f"Who was the pirate child in the story?",
            answer=f"The pirate child was {hero.id}, a {world.facts['params'].trait} little {hero.type}.",
        ),
        QAItem(
            question="What did the child do when the bronco looked scared?",
            answer="The child took a brave step forward and shared what they had so the bronco would feel safer.",
        ),
        QAItem(
            question="What did the child learn by the end?",
            answer="The child learned that sharing can be part of bravery when someone needs comfort.",
        ),
        QAItem(
            question="How did the bronco change?",
            answer=f"The bronco became calmer and less frightened after {hero.id} shared kindly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bronco?",
            answer="A bronco is a horse that can feel wild, quick, and hard to control until it calms down.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing the right thing even when you feel a little scared.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use or enjoy something you have too.",
        ),
        QAItem(
            question="What is a lesson learned?",
            answer="A lesson learned is a useful thing you understand after something happens.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero_brave(H) :- fear(H), resolve(H).
bronco_calms(B) :- shared_food(H), bronco(B).
lesson_learned(H) :- hero_brave(H), shared_food(H).
valid_story(P, E, H) :- setting(P), encounter(E), helper(H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for eid in ENCOUNTERS:
        lines.append(asp.fact("encounter", eid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    got = sorted(set(asp.atoms(model, "valid_story")))
    want = sorted((p, e, h) for p in SETTINGS for e in ENCOUNTERS for h in HELPERS)
    if got == want:
        print(f"OK: ASP matches Python registry combos ({len(got)}).")
        return 0
    print("MISMATCH")
    print("ASP:", got)
    print("PY :", want)
    return 1


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


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
    StoryParams(place="shoe_dim_dock", encounter="bronco", helper="rope_share", prize="rope", name="Mara", gender="girl", trait="brave"),
    StoryParams(place="moon_wharf", encounter="bronco", helper="lantern", prize="apple", name="Pip", gender="boy", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for p, e, h in stories:
            print(f"  {p} {e} {h}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.place} / {p.encounter} / {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
