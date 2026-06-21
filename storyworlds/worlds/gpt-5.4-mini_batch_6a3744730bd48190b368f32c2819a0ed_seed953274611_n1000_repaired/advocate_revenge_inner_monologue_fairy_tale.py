#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/advocate_revenge_inner_monologue_fairy_tale.py
===============================================================================

A small fairy-tale storyworld about a hurt child or creature, a tempting idea of
revenge, an inner monologue of self-control, and a wiser advocate who guides the
ending toward repair instead of retaliation.

The story stays in a fairy-tale style: a castle, a bridge, a garden, a little
kingdom, and a magical helper or wise elder. The tension comes from a wrong that
invites revenge; the turn comes from an inner monologue that notices the danger,
then an advocate helps choose a kinder, braver path.

Run:
    python storyworlds/worlds/gpt-5.4-mini/advocate_revenge_inner_monologue_fairy_tale.py
    python storyworlds/worlds/gpt-5.4-mini/advocate_revenge_inner_monologue_fairy_tale.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/advocate_revenge_inner_monologue_fairy_tale.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
BRAVERY_INIT = 5.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {}
        if not self.memes:
            self.memes = {}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "princess", "queen", "woman", "mother"}
        male = {"boy", "prince", "king", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class StoryParams:
    setting: str
    wrong: str
    hurt: str
    advocate: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass(frozen=True)
class Setting:
    id: str
    opening: str
    place: str
    mood: str
    shelter: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass(frozen=True)
class Wrong:
    id: str
    verb: str
    noun: str
    effect: str
    tempting_revenge: str
    lesson: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass(frozen=True)
class HurtThing:
    id: str
    label: str
    kind: str
    value: str
    fragile: bool = True
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


SETTINGS = {
    "castle": Setting(
        id="castle",
        opening="Once upon a time in a small castle by a silver river",
        place="the castle garden",
        mood="bright with roses and soft bells",
        shelter="a stone archway",
    ),
    "village": Setting(
        id="village",
        opening="Long ago, in a village where chimneys breathed warm smoke",
        place="the market square",
        mood="busy with ribbons and bread",
        shelter="a lantern-lit porch",
    ),
    "forest": Setting(
        id="forest",
        opening="Once, under a forest where the leaves whispered like old songs",
        place="the mossy path",
        mood="green and secret",
        shelter="a hollow oak",
    ),
}

WRONGS = {
    "stolen_bread": Wrong(
        id="stolen_bread",
        verb="stole",
        noun="bread",
        effect="the table went hungry",
        tempting_revenge="take back the loaf and hide the thief's supper",
        lesson="hurt does not heal when another stomach is left empty",
    ),
    "broken_toy": Wrong(
        id="broken_toy",
        verb="broke",
        noun="a toy horse",
        effect="the toy pieces lay in the grass",
        tempting_revenge="break the other child's drum in return",
        lesson="revenge only makes two sad things instead of one",
    ),
    "ripped_banner": Wrong(
        id="ripped_banner",
        verb="tore",
        noun="a banner",
        effect="the fair banner fluttered in tatters",
        tempting_revenge="tear the rival banner from the gate",
        lesson="anger is loud, but wisdom can be quiet and strong",
    ),
}

HURTS = {
    "bread": HurtThing(id="bread", label="a loaf of bread", kind="food", value="warm bread"),
    "toy": HurtThing(id="toy", label="a toy horse", kind="toy", value="toy horse"),
    "banner": HurtThing(id="banner", label="a banner", kind="cloth", value="banner"),
}

ADVOCATES = {
    "owl": {"name": "the owl advocate", "type": "owl", "tone": "wise"},
    "grandmother": {"name": "Grandmother Rose", "type": "woman", "tone": "gentle"},
    "knight": {"name": "a small knight advocate", "type": "boy", "tone": "steady"},
}

HEROES = {
    "girl": ["Mira", "Lina", "Sera", "Nina"],
    "boy": ["Theo", "Bram", "Owen", "Alfie"],
}

HELPERS = {
    "mouse": ["Pip", "Tilly", "Moss"],
    "fox": ["Fenn", "Rook", "Wren"],
    "bird": ["Goldie", "Robin", "Pipit"],
}


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        other = World()
        other.entities = {k: Entity(**vars(v)) for k, v in self.entities.items()}
        other.facts = dict(self.facts)
        other.fired = set(self.fired)
        return other


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld about revenge and advocacy.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--wrong", choices=WRONGS)
    ap.add_argument("--hurt", choices=HURTS)
    ap.add_argument("--advocate", choices=ADVOCATES)
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for wid, w in WRONGS.items():
            for hid, h in HURTS.items():
                if wid == "stolen_bread" and hid == "bread":
                    combos.append((sid, wid, hid))
                if wid == "broken_toy" and hid == "toy":
                    combos.append((sid, wid, hid))
                if wid == "ripped_banner" and hid == "banner":
                    combos.append((sid, wid, hid))
    return combos


def explain_rejection() -> str:
    return "(No story: the chosen wrong and hurt do not form a clear fairy-tale grievance.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.wrong is None or c[1] == args.wrong)
              and (args.hurt is None or c[2] == args.hurt)]
    if not combos:
        raise StoryError(explain_rejection())
    setting, wrong, hurt = rng.choice(sorted(combos))
    advocate = args.advocate or rng.choice(sorted(ADVOCATES))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    hero = rng.choice(HEROES[hero_type])
    helper = args.helper or rng.choice(sorted(HELPERS))
    return StoryParams(setting=setting, wrong=wrong, hurt=hurt, advocate=advocate, hero=hero, hero_type=hero_type, helper=helper)


def _build_world(params: StoryParams) -> World:
    if params.setting not in SETTINGS or params.wrong not in WRONGS or params.hurt not in HURTS:
        raise StoryError("Invalid parameters for this storyworld.")
    world = World()
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type, role="hero"))
    helper_name = HELPERS[params.helper][0]
    helper = world.add(Entity(id=helper_name, kind="character", type="animal", role="helper"))
    advocate_info = ADVOCATES[params.advocate]
    advocate = world.add(Entity(id=advocate_info["name"], kind="character", type=advocate_info["type"], role="advocate"))
    hurt = world.add(Entity(id="hurt", kind="thing", type=HURTS[params.hurt].kind, label=HURTS[params.hurt].label))
    wrong = WRONGS[params.wrong]
    setting = SETTINGS[params.setting]

    hero.memes["hurt"] = 1.0
    hero.memes["revenge"] = 0.0
    hero.memes["resolve"] = 0.0
    advocate.memes["calm"] = 1.0
    helper.memes["concern"] = 1.0

    world.say(f"{setting.opening}, there lived {hero.id}, and {setting.mood}.")
    world.say(f"Near {setting.place}, {wrong.effect}.")
    world.say(f"{hero.id} folded {hero.pronoun('possessive')} hands and thought, \"{wrong.tempting_revenge}.\"")
    world.say(f"Inside {hero.pronoun('possessive')} heart, a small voice whispered: \"If I strike back, will I feel better?\"")

    world.para()
    hero.memes["revenge"] += 1.0
    world.say(f"But then {helper.id} hurried near, and {advocate_info['name']} stepped from {setting.shelter}.")
    world.say(f"\"Do not let revenge wear a golden crown,\" said {advocate_info['name']}. \"{wrong.lesson}.\"")
    world.say(f"{hero.id} listened, and the thought turned over like a stone in {hero.pronoun('possessive')} pocket.")

    world.para()
    hero.memes["resolve"] += 1.0
    if params.wrong == "stolen_bread":
        world.say(f"{hero.id} took a deep breath, found the missing loaf, and asked for the bread to be shared fairly.")
        world.say(f"Then {hero.id} offered a crust to the one who had been hungry, and the table grew kinder instead of colder.")
    elif params.wrong == "broken_toy":
        world.say(f"{hero.id} gathered the toy pieces, tied them with ribbon, and asked for help making the toy horse whole again.")
        world.say(f"The little horse returned to the play rug, stitched with care, and the children sat together in quiet peace.")
    else:
        world.say(f"{hero.id} smoothed the torn banner and asked the seamstress to mend it before sunset.")
        world.say(f"When the banner rose again, it fluttered like a bright promise over the gate.")

    world.say(f"{hero.id} thought, \"I can choose better than revenge,\" and the little kingdom felt lighter for it.")
    world.facts.update(params=params, hero=hero, helper=helper, advocate=advocate, hurt=hurt, wrong=wrong, setting=setting)
    return world


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]  # type: ignore[assignment]
    return [
        f'Write a fairy-tale story with the words "{p.advocate}" and "revenge" where an inner monologue helps a child choose wisely.',
        f"Tell a gentle castle-or-forest fairy tale where {p.hero} is tempted by revenge, but an advocate helps {p.hero} decide on repair instead.",
        f"Write a short story for a child that includes an inner thought like \"Should I seek revenge?\" and ends with a kind solution.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    p: StoryParams = world.facts["params"]  # type: ignore[assignment]
    wrong: Wrong = world.facts["wrong"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    advocate: Entity = world.facts["advocate"]  # type: ignore[assignment]
    setting: Setting = world.facts["setting"]  # type: ignore[assignment]
    return [
        ("Who is the story about?",
         f"It is about {hero.id}, who was hurt and had to decide what to do next. {advocate.id} helped {hero.id} think clearly."),
        ("What did {0} want at first?".format(hero.id),
         f"{hero.id} first wanted revenge, because the wrong felt sharp and unfair. The tempting idea was to {wrong.tempting_revenge}."),
        ("Who acted as the advocate?",
         f"{advocate.id} was the advocate. {advocate.id} spoke calmly and helped {hero.id} choose repair instead of revenge."),
        ("How did the story end?",
         f"It ended with {hero.id} making things better in {setting.place} rather than striking back. The ending is peaceful, and the little kingdom feels lighter."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is an advocate?",
         "An advocate is someone who speaks up for what is right and helps someone choose a good path."),
        ("What does revenge mean?",
         "Revenge means trying to hurt back after someone has hurt you. It often makes sadness grow instead of shrink."),
        ("Why is it wiser to repair than to seek revenge?",
         "Repair can fix the hurt and help people live together again. Revenge usually makes the wrong bigger and keeps the trouble going."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, q in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {q}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: kind={e.kind} type={e.type} role={e.role} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,W,H) :- setting(S), wrong(W), hurt(H), compatible(W,H).
compatible("stolen_bread","bread").
compatible("broken_toy","toy").
compatible("ripped_banner","banner").
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for wid in WRONGS:
        lines.append(asp.fact("wrong", wid))
    for hid in HURTS:
        lines.append(asp.fact("hurt", hid))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: story generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


CURATED = [
    StoryParams(setting="castle", wrong="stolen_bread", hurt="bread", advocate="owl", hero="Mira", hero_type="girl", helper="mouse"),
    StoryParams(setting="forest", wrong="broken_toy", hurt="toy", advocate="grandmother", hero="Theo", hero_type="boy", helper="fox"),
    StoryParams(setting="village", wrong="ripped_banner", hurt="banner", advocate="knight", hero="Sera", hero_type="girl", helper="bird"),
]


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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
            i += 1

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
