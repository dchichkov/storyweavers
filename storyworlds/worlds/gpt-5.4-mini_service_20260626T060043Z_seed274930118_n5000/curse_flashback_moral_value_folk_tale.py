#!/usr/bin/env python3
"""
storyworlds/worlds/curse_flashback_moral_value_folk_tale.py
============================================================

A small folk-tale story world about a curse, a remembered past, and a moral
choice that breaks the spell.

The premise is intentionally classical:
- a child or young villager finds a strange cursed thing,
- trouble grows until an elder remembers a flashback,
- a moral choice is made,
- the curse lifts and the ending proves the change.

The world is compact, but state-driven: the curse changes meters and memes,
and the flashback is not decorative—it explains why the chosen remedy works.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    placed_in: str = ""
    cursed: bool = False
    blessed: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "grandmother", "elder woman"}
        male = {"boy", "man", "father", "grandfather", "elder man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def init_meter(self, name: str) -> None:
        self.meters.setdefault(name, 0.0)

    def init_meme(self, name: str) -> None:
        self.memes.setdefault(name, 0.0)


@dataclass
class Setting:
    place: str
    kind: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    region: str
    cursed: bool = True


@dataclass
class MoralChoice:
    id: str
    label: str
    verb: str
    result: str
    lifts_curse: bool
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_notes: list[str] = []

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = copy.deepcopy(self.facts)
        w.paragraphs = [[]]
        return w


SETTINGS = {
    "village": Setting(place="the village green", kind="village", affords={"gather", "market"}),
    "forest": Setting(place="the forest edge", kind="forest", affords={"gather", "walk"}),
    "river": Setting(place="the riverbank", kind="river", affords={"walk", "wash"}),
}

RELICS = {
    "ring": Relic(id="ring", label="ring", phrase="a silver ring with a dull blue stone", region="hand"),
    "spindle": Relic(id="spindle", label="spindle", phrase="a carved spindle bound with red thread", region="hand"),
    "bell": Relic(id="bell", label="bell", phrase="a tiny brass bell on a frayed cord", region="neck"),
}

MORALS = {
    "return": MoralChoice(
        id="return",
        label="return what was taken",
        verb="give the relic back",
        result="the owner smiles and the curse loosens",
        lifts_curse=True,
        tags={"honesty", "return"},
    ),
    "apologize": MoralChoice(
        id="apologize",
        label="tell the truth and apologize",
        verb="speak the truth",
        result="the hurt is named and the curse softens",
        lifts_curse=True,
        tags={"honesty", "truth"},
    ),
    "share": MoralChoice(
        id="share",
        label="share the prize with the village",
        verb="share it fairly",
        result="kind hands join in and the curse lifts",
        lifts_curse=True,
        tags={"generosity", "share"},
    ),
    "keep": MoralChoice(
        id="keep",
        label="keep the relic hidden",
        verb="hide it away",
        result="the curse grows worse",
        lifts_curse=False,
        tags={"greed"},
    ),
}

HEROES = {
    "girl": ["Mara", "Suri", "Elin", "Nia", "Tess", "Lina"],
    "boy": ["Jory", "Pavel", "Ren", "Borin", "Kellan", "Milo"],
}

ELDERS = {
    "grandmother": "grandmother",
    "grandfather": "grandfather",
    "elder woman": "elder woman",
    "elder man": "elder man",
}

TRAITS = ["kind", "curious", "careful", "brave", "gentle", "stubborn"]


def _meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _meme(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def _say_flashback(world: World, elder: Entity, relic: Entity) -> None:
    world.say(
        f"{elder.pronoun().capitalize()} remembered an old winter, when the same {relic.label} "
        f"had once been carried away from its proper home."
    )
    world.say(
        f"In that flashback, a child had kept a secret instead of speaking plainly, and the house "
        f"had grown cold with worry until the truth came out."
    )


def _curse_spreads(world: World, hero: Entity, relic: Entity) -> None:
    sig = ("curse_spread", hero.id, relic.id)
    if sig in world.fired:
        return
    if not relic.cursed or _meter(hero, "curse") < THRESHOLD:
        return
    world.fired.add(sig)
    hero.meters["trouble"] = hero.meters.get("trouble", 0.0) + 1
    hero.meters["luck"] = hero.meters.get("luck", 0.0) - 1
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    world.say(
        f"At once, small troubles began to follow {hero.id}: a basket tipped, a loaf rolled, and "
        f"the morning felt strangely hard."
    )


def _moral_resolves(world: World, hero: Entity, elder: Entity, relic: Entity, choice: MoralChoice) -> None:
    sig = ("resolve", hero.id, choice.id)
    if sig in world.fired:
        return
    if _meme(hero, "guilt") < THRESHOLD:
        return
    if not choice.lifts_curse:
        return
    world.fired.add(sig)
    hero.meters["curse"] = 0.0
    hero.meters["luck"] = hero.meters.get("luck", 0.0) + 2
    hero.memes["peace"] = hero.memes.get("peace", 0.0) + 2
    relic.cursed = False
    world.say(
        f"{hero.id} did the hard, honest thing and {choice.verb}."
    )
    world.say(
        f"Then {relic.label} grew warm in {hero.pronoun('possessive')} hand, and the dark luck slipped away like fog in sunrise."
    )


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    while changed:
        changed = False
        before = len(world.paragraphs[-1])
        for e in list(world.entities.values()):
            if e.kind != "character":
                continue
            relic = world.facts.get("relic")
            elder = world.facts.get("elder")
            choice = world.facts.get("choice")
            if relic and e.id == world.facts.get("hero").id:
                _curse_spreads(world, e, relic)
                if choice:
                    _moral_resolves(world, e, elder, relic, choice)
        if len(world.paragraphs[-1]) != before:
            changed = True


def tell(setting: Setting, relic_cfg: Relic, choice: MoralChoice, hero_name: str, gender: str, trait: str, elder_kind: str) -> World:
    world = World(setting)

    hero = world.add(Entity(id=hero_name, kind="character", type=gender, label=hero_name))
    elder = world.add(Entity(id="Elder", kind="character", type=elder_kind, label=elder_kind))
    relic = world.add(Entity(
        id="Relic",
        kind="thing",
        type=relic_cfg.label,
        label=relic_cfg.label,
        phrase=relic_cfg.phrase,
        cursed=relic_cfg.cursed,
    ))
    relic.meters["curse"] = 1.0

    hero.memes["desire"] = 1.0
    hero.memes["curiosity"] = 1.0
    hero.memes["guilt"] = 0.0

    world.facts.update(hero=hero, elder=elder, relic=relic, choice=choice, setting=setting)

    world.say(
        f"Once, in {setting.place}, there lived a {trait} young {gender} named {hero.id} who noticed every shiny thing."
    )
    world.say(
        f"One day {hero.id} found {relic.phrase} near the path and thought it looked like a gift from the old stories."
    )
    world.say(
        f"{hero.id} took it home, and before sunset the {relic.label}'s curse had settled into {hero.pronoun('possessive')} day."
    )
    propagate(world)

    world.para()
    world.say(
        f"By evening, {hero.id} met {elder_kind} and admitted that the little treasure had brought trouble instead of joy."
    )
    _say_flashback(world, elder, relic)
    hero.memes["guilt"] = 1.0
    world.say(
        f"{elder.pronoun().capitalize()} said that a curse does not like greedy hands, but it can be shamed by a brave heart."
    )
    world.say(
        f"\"{choice.label.capitalize()} is the right road,\" {elder.pronoun('subject')} said. \"{choice.result.capitalize()}.\""
    )
    propagate(world)

    world.para()
    if choice.lifts_curse:
        world.say(
            f"{hero.id} listened, {choice.verb}, and placed the matter back where it belonged."
        )
        world.say(
            f"The next morning the village looked brighter, and {hero.id}'s bread stayed in the basket, the way bread should."
        )
    else:
        world.say(
            f"{hero.id} hid the {relic.label} away, and the house stayed uneasy with the curse still awake."
        )
        world.say(
            f"The ending was not kind, for a hidden wrong keeps making shadows larger."
        )

    world.facts["hero"] = hero
    world.facts["elder"] = elder
    world.facts["relic"] = relic
    world.facts["choice"] = choice
    return world


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for relic_id, relic in RELICS.items():
            for moral_id, moral in MORALS.items():
                if moral.lifts_curse and place in {"village", "forest", "river"}:
                    out.append((place, relic_id, moral_id, "girl"))
                    out.append((place, relic_id, moral_id, "boy"))
    return out


@dataclass
class StoryParams:
    place: str
    relic: str
    moral: str
    gender: str
    name: str
    trait: str
    elder: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short folk tale about a curse, a flashback, and a moral choice in {f["setting"].place}.',
        f"Tell a child-sized story where {f['hero'].id} finds {f['relic'].phrase} and learns to do the honest thing.",
        f'Write a gentle story that uses the word "curse" and ends with the wrong put right.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, elder, relic, choice = f["hero"], f["elder"], f["relic"], f["choice"]
    return [
        QAItem(
            question=f"What did {hero.id} find in {f['setting'].place}?",
            answer=f"{hero.id} found {relic.phrase}, and it turned out to carry a curse.",
        ),
        QAItem(
            question=f"Why did the elder remember the past?",
            answer="The elder remembered a flashback because an old wrong had happened before, and that memory showed the way to fix the new trouble.",
        ),
        QAItem(
            question=f"What moral choice helped at the end?",
            answer=f"{hero.id} chose to {choice.verb}, and that honest choice broke the curse.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The curse lifted, the village felt lighter, and {hero.id} ended with peace instead of worry.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a curse in a folktale?",
            answer="A curse is a bad magical trouble that keeps making life harder until someone puts the wrong right.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a memory of something that happened before the main part of the story.",
        ),
        QAItem(
            question="What does moral value mean in a story?",
            answer="Moral value means the story shows a good choice like honesty, kindness, or fairness.",
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
        if e.kind == "thing":
            bits.append(f"cursed={e.cursed}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A relic is cursed when it is marked cursed and the hero carries curse.
cursed(H, R) :- hero(H), relic(R), carries(H, R), relic_cursed(R).

% A moral choice lifts the curse only when it is an honest/repairing action.
lifts(H) :- choice(return).
lifts(H) :- choice(apologize).
lifts(H) :- choice(share).

valid_story(P, R, M, G) :- setting(P), relic(R), moral(M), gender(G),
                           place_ok(P), relic_cursed(R), choice_lifts(M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
        lines.append(asp.fact("place_ok", pid))
    for rid, relic in RELICS.items():
        lines.append(asp.fact("relic", rid))
        if relic.cursed:
            lines.append(asp.fact("relic_cursed", rid))
    for mid, moral in MORALS.items():
        lines.append(asp.fact("moral", mid))
        if moral.lifts_curse:
            lines.append(asp.fact("choice_lifts", mid))
    for g in ["girl", "boy"]:
        lines.append(asp.fact("gender", g))
    lines.append(asp.fact("hero", "h"))
    lines.append(asp.fact("carries", "h", "r"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    am = set(asp.atoms(asp.one_model(asp_program("#show valid_story/4.")), "valid_story"))
    if py == am:
        print(f"OK: ASP and Python agree on {len(py)} valid story patterns.")
        return 0
    print("MISMATCH between ASP and Python:")
    print(" python-only:", sorted(py - am))
    print(" asp-only:", sorted(am - py))
    return 1


def explain_rejection() -> str:
    return "(No story: this world only tells folk tales where an honest moral choice can break the curse.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny folk-tale world of curse, flashback, and moral value.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--moral", choices=MORALS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--elder", choices=list(ELDERS))
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
    place = args.place or rng.choice(list(SETTINGS))
    relic = args.relic or rng.choice(list(RELICS))
    moral = args.moral or rng.choice(["return", "apologize", "share"])
    if moral not in MORALS or not MORALS[moral].lifts_curse:
        raise StoryError(explain_rejection())
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HEROES[gender])
    trait = args.trait or rng.choice(TRAITS)
    elder = args.elder or rng.choice(list(ELDERS))
    return StoryParams(place=place, relic=relic, moral=moral, gender=gender, name=name, trait=trait, elder=elder)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        RELICS[params.relic],
        MORALS[params.moral],
        params.name,
        params.gender,
        params.trait,
        ELDERS[params.elder],
    )
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
    StoryParams(place="village", relic="ring", moral="return", gender="girl", name="Mara", trait="curious", elder="grandmother"),
    StoryParams(place="forest", relic="spindle", moral="apologize", gender="boy", name="Jory", trait="careful", elder="grandfather"),
    StoryParams(place="river", relic="bell", moral="share", gender="girl", name="Lina", trait="gentle", elder="elder woman"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible story patterns:")
        for t in stories:
            print(" ", t)
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
            header = f"### {p.name}: {p.relic} / {p.moral} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
