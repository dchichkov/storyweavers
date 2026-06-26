#!/usr/bin/env python3
"""
storyworlds/worlds/hiccup_entitle_semi_twist_myth.py
=====================================================

A small mythic storyworld about a child, a sacred rite, a hiccup,
and a twist that turns embarrassment into a blessing.

Seed-tale sketch:
---
In a stone ring beside a quiet grove, a little child named Mira hoped to be
entitled to a star-name. The elder asked Mira to speak the naming vow before the
fire. But just as Mira began, a hiccup burst out and the vow stumbled. Mira
blushed and wanted to hide.

The elder listened, smiled, and changed the rite. Instead of a perfect speech,
Mira would say the vow again as a semi-song, with the drum beating softly in the
middle. Mira tried once more. This time the hiccup became part of the rhythm,
and the star-name sounded brighter than before. The grove answered with light,
and Mira went home laughing with the new name.

World model:
---
- A spoken rite can be interrupted by a hiccup.
- A patient elder can choose a semi-rite: a half-song, half-speech, which still
  counts as a true naming.
- The twist is that the hiccup is not a failure; it becomes the beat that helps
  the child accept the name.

The prose is designed to feel mythic, concrete, and child-facing.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

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
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "priestess"}
        male = {"boy", "father", "dad", "man", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    glow: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Rite:
    id: str
    verb: str
    gerund: str
    rush: str
    keyword: str
    twist: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    rite: str = ""
    weather: str = ""

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
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
        clone.rite = self.rite
        clone.weather = self.weather
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_hiccup(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["hiccup"] < THRESHOLD:
            continue
        if actor.memes["embarrassment"] < THRESHOLD:
            continue
        sig = ("hiccup_break", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["shaken"] += 1
        out.append(f"The vow wavered when {actor.id} hiccuped.")
    return out


def _r_semi(world: World) -> list[str]:
    out: list[str] = []
    elder = world.facts.get("elder")
    hero = world.facts.get("hero")
    if not elder or not hero:
        return out
    h = world.get(hero.id)
    e = world.get(elder.id)
    if h.memes["hiccup"] < THRESHOLD or e.memes["patience"] < THRESHOLD:
        return out
    sig = ("semi_rite", h.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    e.memes["mercy"] += 1
    h.memes["hope"] += 1
    out.append("__semi__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("hiccup", "social", _r_hiccup),
    Rule("semi", "mythic", _r_semi),
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
                produced.extend(s for s in sents if s != "__semi__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_outcome(world: World, hero: Entity, rite: Rite, prize_id: str) -> dict:
    sim = world.copy()
    perform_rite(sim, sim.get(hero.id), rite, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "entitled": bool(prize and prize.memes["named"] >= THRESHOLD),
        "twist": bool(sim.facts.get("twist_done")),
    }


def perform_rite(world: World, hero: Entity, rite: Rite, narrate: bool = True) -> None:
    if rite.id not in world.setting.affords:
        return
    hero.memes["hiccup"] += 1
    hero.memes["embarrassment"] += 1
    world.rite = rite.id
    propagate(world, narrate=narrate)


def introduction(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "quiet")
    world.say(
        f"In the stone ring, {hero.id} was a little {trait} {hero.type} who listened for old names."
    )


def desire(world: World, hero: Entity, rite: Rite) -> None:
    hero.memes["hope"] += 1
    world.say(
        f"{hero.id} wanted to {rite.verb}, because a star-name was waiting if the vow could be spoken."
    )


def bring_to_rite(world: World, hero: Entity, elder: Entity, setting: Setting) -> None:
    world.say(
        f"One dusk, {hero.id} and {hero.pronoun('possessive')} {elder.type} came to {setting.place}, where {setting.glow} pooled on the stones."
    )


def warn(world: World, elder: Entity, hero: Entity, rite: Rite, prize: Prize) -> bool:
    pred = predict_outcome(world, hero, rite, prize.type)
    if pred["entitled"]:
        return False
    world.facts["predicted_twist"] = rite.twist
    world.say(
        f'"If you try to {rite.verb} now," {elder.id} said, "the vow may stumble and the name may hide."'
    )
    return True


def stumble(world: World, hero: Entity, rite: Rite) -> None:
    hero.memes["shame"] += 1
    world.say(
        f"{hero.id} tried to {rite.rush}, but a hiccup hopped out and broke the middle of the sound."
    )


def semi_turn(world: World, elder: Entity, hero: Entity, rite: Rite) -> None:
    hero.memes["hiccup"] += 1
    elder.memes["patience"] += 1
    world.facts["twist_done"] = True
    world.say(
        f"Then the {elder.type} smiled and said the rite could be a semi-song: half speech, half drumbeat, with room for a little hiccup."
    )


def accept(world: World, elder: Entity, hero: Entity, rite: Rite, prize: Prize) -> None:
    hero.memes["joy"] += 1
    hero.memes["hope"] += 1
    hero.memes["embarrassment"] = 0.0
    world.say(
        f"{hero.id} tried again, and this time the hiccup fell neatly into the rhythm. {hero.id} was entitled to {prize.phrase}, and the grove answered with a soft bright wind."
    )
    world.say(
        f"At the end, {hero.id} walked home laughing, with {hero.pronoun('possessive')} new name shining like a small star over {hero.pronoun('possessive')} brow."
    )


def tell(setting: Setting, rite: Rite, prize_cfg: Prize, hero_name: str = "Mira",
         hero_type: str = "girl", hero_traits: Optional[list[str]] = None,
         elder_type: str = "elder") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type,
                            traits=["little"] + (hero_traits or ["brave", "curious"])))
    elder = world.add(Entity(id="Elder", kind="character", type=elder_type))
    prize = world.add(Entity(id="Prize", type=prize_cfg.type, label=prize_cfg.label,
                             phrase=prize_cfg.phrase, owner=hero.id))
    world.facts.update(hero=hero, elder=elder, prize=prize, rite=rite, setting=setting)

    introduction(world, hero)
    desire(world, hero, rite)
    world.para()
    bring_to_rite(world, hero, elder, setting)
    warn(world, elder, hero, rite, prize)
    stumble(world, hero, rite)
    world.para()
    semi_turn(world, elder, hero, rite)
    accept(world, elder, hero, rite, prize)
    world.facts.update(resolved=True, twist_done=True)
    return world


SETTINGS = {
    "stone_ring": Setting(place="the stone ring", glow="moonlight", affords={"naming"}),
    "grove": Setting(place="the grove", glow="green dusk", affords={"naming"}),
    "hill_temple": Setting(place="the hill temple", glow="sunset", affords={"naming"}),
}

RITES = {
    "naming": Rite(
        id="naming",
        verb="speak the naming vow",
        gerund="speaking the naming vow",
        rush="say the vow all at once",
        keyword="name",
        twist="semi-song",
        tags={"name", "voice", "hiccup", "semi"},
    ),
}

PRIZES = {
    "star_name": Prize(label="star-name", phrase="a star-name", type="star_name"),
}

GIRL_NAMES = ["Mira", "Sana", "Iris", "Luna", "Nia"]
BOY_NAMES = ["Ari", "Tavi", "Milo", "Kian", "Orin"]
TRAITS = ["gentle", "brave", "curious", "patient", "earnest"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for rite_id in setting.affords:
            for prize_id in PRIZES:
                out.append((place, rite_id, prize_id))
    return out


@dataclass
class StoryParams:
    place: str
    rite: str
    prize: str
    name: str
    gender: str
    elder: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    rite = f["rite"]
    return [
        f'Write a short myth for a child about a {rite.keyword} rite, a hiccup, and a semi-song twist.',
        f"Tell a gentle story where {hero.id} tries to {rite.verb}, but a hiccup interrupts the naming and an elder finds a kinder way.",
        f'Write a mythic little story that includes the words "hiccup", "entitle", and "semi", and ends with a blessing.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    prize = f["prize"]
    rite = f["rite"]
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do in the stone ring?",
            answer=f"{hero.id} wanted to {rite.verb} so {hero.pronoun('subject')} could be entitled to {prize.phrase}.",
        ),
        QAItem(
            question=f"Why did the rite wobble when {hero.id} began?",
            answer=f"The rite wobbled because {hero.id} hiccuped in the middle of saying the vow, and the sound broke apart.",
        ),
        QAItem(
            question=f"How did the elder help after the hiccup?",
            answer=f"{elder.id} turned the moment into a semi-song, so the naming could still happen even with a hiccup in it.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {hero.id} was entitled to {prize.phrase}, and the hiccup had become part of the blessing instead of a problem.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hiccup?",
            answer="A hiccup is a quick sudden sound from your body that can interrupt talking or singing for a moment.",
        ),
        QAItem(
            question="What does it mean to entitle someone to something?",
            answer="To entitle someone to something means to give them the right to have it or be called by it.",
        ),
        QAItem(
            question="What does semi- mean?",
            answer='Semi- means "half" or "partly," like a semi-song that is partly speech and partly music.',
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="stone_ring", rite="naming", prize="star_name", name="Mira", gender="girl", elder="elder", trait="brave"),
    StoryParams(place="grove", rite="naming", prize="star_name", name="Ari", gender="boy", elder="elder", trait="curious"),
]


def explain_rejection() -> str:
    return "(No story: this world only supports a naming rite that can be turned into a semi-song after a hiccup.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: {PRIZES[prize_id].label} is not a typical {gender}'s item here; try --gender {ok}.)"


ASP_RULES = r"""
prize_at_risk(R, P) :- rite(R), prize(P).
has_twist(R) :- rite(R), can_semi(R).
valid(Place, R, P) :- setting(Place), affords(Place, R), prize_at_risk(R, P), has_twist(R).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for r in sorted(s.affords):
            lines.append(asp.fact("affords", sid, r))
    for rid in RITES:
        lines.append(asp.fact("rite", rid))
        lines.append(asp.fact("can_semi", rid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, py_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - py_set:
        print("  only in clingo:", sorted(clingo_set - py_set))
    if py_set - clingo_set:
        print("  only in python:", sorted(py_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic story world of a hiccup, a semi-song, and a naming twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--rite", choices=RITES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["elder"])
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
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.rite is None or c[1] == args.rite)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError(explain_rejection())
    place, rite, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or "elder"
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, rite=rite, prize=prize, name=name, gender=gender, elder=elder, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], RITES[params.rite], PRIZES[params.prize], params.name, params.gender, [params.trait], params.elder)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for c in combos:
            print("  ", c)
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
            header = f"### {p.name}: {p.rite} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
