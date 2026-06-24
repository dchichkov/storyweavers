#!/usr/bin/env python3
"""
A mythic dialogue storyworld about a small hero, a sacred quest, a helpful voice,
and a triumphant return.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "queen", "goddess"}
        male = {"boy", "man", "father", "king", "god"}
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
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Trial:
    id: str
    verb: str
    gerund: str
    peril: str
    zone: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False


@dataclass
class Ally:
    id: str
    label: str
    offer: str
    boon: str
    guard: str
    guard_region: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
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


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in text.split("\n") if s.strip()]


def warrior_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


SETTINGS = {
    "mountain": Setting(place="the mountain path", mood="high", affords={"light", "river", "wind"}),
    "grove": Setting(place="the moonlit grove", mood="quiet", affords={"light", "wind"}),
    "riverbank": Setting(place="the riverbank", mood="silver", affords={"river", "wind"}),
    "temple": Setting(place="the old temple stairs", mood="hushed", affords={"light"}),
}

TRIALS = {
    "river": Trial(
        id="river",
        verb="cross the river",
        gerund="crossing the river",
        peril="the cold water would sweep the lantern away",
        zone="hands",
        keyword="river",
        tags={"water", "flow"},
    ),
    "wind": Trial(
        id="wind",
        verb="climb the windy ridge",
        gerund="climbing the windy ridge",
        peril="the fierce wind would blow the lantern from the hand",
        zone="hands",
        keyword="wind",
        tags={"wind", "sky"},
    ),
    "light": Trial(
        id="light",
        verb="carry the light to the altar",
        gerund="carrying the light",
        peril="the shadows would swallow the flame",
        zone="hands",
        keyword="light",
        tags={"light", "flame"},
    ),
}

PRIZES = {
    "lantern": Prize(id="lantern", label="lantern", phrase="a small bronze lantern", region="hands"),
    "crown": Prize(id="crown", label="crown", phrase="a star-crown of hammered gold", region="head"),
}

ALLY = Ally(
    id="guide",
    label="the old guide",
    offer="tie a silver cord around your wrist",
    boon="a silver cord",
    guard="hold fast even when the world trembles",
    guard_region="hands",
)

GIRL_NAMES = ["Iris", "Mira", "Nora", "Lina", "Sera", "Tala", "Zora", "Rhea"]
BOY_NAMES = ["Arin", "Tomas", "Eli", "Kian", "Niko", "Bren", "Orin", "Levi"]


@dataclass
class StoryParams:
    place: str
    trial: str
    prize: str
    name: str
    gender: str
    seed: Optional[int] = None


def reasonableness_gate(params: StoryParams) -> None:
    trial = TRIALS[params.trial]
    prize = PRIZES[params.prize]
    if trial.zone != prize.region:
        raise StoryError(
            f"(No story: {trial.gerund} does not threaten a {prize.label} in this myth.)"
        )


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for trial_id in setting.affords:
            for prize_id, prize in PRIZES.items():
                trial = TRIALS[trial_id]
                if trial.zone == prize.region:
                    combos.append((place, trial_id, prize_id))
    return combos


def _do_trial(world: World, hero: Entity, trial: Trial, narrate: bool = True) -> None:
    hero.meters[trial.id] = hero.meters.get(trial.id, 0.0) + 1
    if narrate:
        world.say(f"{hero.id} faced {trial.gerund}.")
    if trial.id == "river":
        hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1
    elif trial.id == "wind":
        hero.memes["doubt"] = hero.memes.get("doubt", 0.0) + 1
    else:
        hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1


def tell(setting: Setting, trial: Trial, prize_cfg: Prize, hero_name: str, hero_gender: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender))
    guide = world.add(Entity(id="Guide", kind="character", type="elder", label=ALLY.label))
    prize = world.add(Entity(id="Prize", type=prize_cfg.id, label=prize_cfg.label, phrase=prize_cfg.phrase))

    world.say(f"Long ago, {hero.id} walked under the sky at {setting.place}.")
    world.say(f"{hero.id} sought {prize.phrase}, because the old songs said it belonged to the dawn.")
    world.say(f'“Will the road let me pass?” {hero.pronoun()} asked.')
    world.say(f'“Only if you answer it with courage,” said {guide.label}.')

    world.para()
    world.say(f"At the gate of the trial, the air grew sharp and strange.")
    world.say(f'The path demanded this: “{trial.verb}.”')
    world.say(f"{hero.id} swallowed hard. {trial.peril.capitalize()}.")
    world.say(f'“I am afraid,” {hero.pronoun()} whispered.')
    world.say(f'“Fear can walk beside you,” said {guide.label}. “It need not lead.”')
    world.say(f'“Then lend me a sign,” said {hero.id}.')
    world.say(f'“Take this,” said {guide.label}, and the guide offered {ALLY.offer}.')

    world.para()
    hero.memes["resolve"] = hero.memes.get("resolve", 0.0) + 1
    if trial.id == "river":
        world.say(f"{hero.id} tied the cord tight and stepped into the cold water.")
        world.say(f'The current tugged, but {hero.id} answered, “Not today.”')
    elif trial.id == "wind":
        world.say(f"{hero.id} lifted the lantern low and climbed into the howling air.")
        world.say(f'The wind cried, “Turn back!” and {hero.id} replied, “I was sent forward.”')
    else:
        world.say(f"{hero.id} carried the light with both hands and climbed the temple stairs.")
        world.say(f'The shadows muttered, but {hero.id} said, “I bring what was promised.”')

    _do_trial(world, hero, trial, narrate=False)
    prize.meters["safe"] = prize.meters.get("safe", 0.0) + 1
    hero.memes["triumphant"] = hero.memes.get("triumphant", 0.0) + 1
    guide.memes["pride"] = guide.memes.get("pride", 0.0) + 1

    world.say(f"At last, the trial yielded.")
    world.say(f"{hero.id} reached the far side with {prize.label} unbroken.")
    world.say(f'“I did not run from the fear,” {hero.pronoun()} said. “I walked through it.”')
    world.say(f'“And that is how songs are born,” said {guide.label}.')
    world.say(f"So the child returned in triumph, and the sky seemed to bow a little lower.")

    world.facts.update(hero=hero, guide=guide, prize=prize, trial=trial, setting=setting)
    return world


KNOWLEDGE = {
    "river": [
        ("What is a river?", "A river is a long stream of moving water that flows across the land."),
        ("Why should a lantern stay dry near water?", "A flame or lantern can go out if it gets wet."),
    ],
    "wind": [
        ("What is wind?", "Wind is moving air. It can feel cool and can push light things around."),
        ("Why do people hold onto hats in strong wind?", "Strong wind can blow hats or paper away if they are not held down."),
    ],
    "light": [
        ("What is light?", "Light is what helps us see. Sunlight, candles, and lanterns all give light."),
        ("Why do people use lanterns at night?", "People use lanterns to make a path bright when it is dark."),
    ],
    "triumphant": [
        ("What does triumphant mean?", "Triumphant means full of victory and happy success after a hard task."),
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short myth for children with dialogue about {f["hero"].id} and a brave trial.',
        f'Tell a mythic story where a young hero says, “I am afraid,” but still completes {f["trial"].verb}.',
        f'Write a gentle legend in which a guide offers help and the hero returns triumphant with {f["prize"].label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, guide, prize, trial = f["hero"], f["guide"], f["prize"], f["trial"]
    return [
        QAItem(
            question=f"What did {hero.id} want to bring back from the road?",
            answer=f"{hero.id} wanted to bring back {prize.phrase}, the treasure the old songs had promised.",
        ),
        QAItem(
            question=f"Who told {hero.id}, “Fear can walk beside you,”?",
            answer=f"{guide.label} said that so {hero.id} would keep going even while afraid.",
        ),
        QAItem(
            question=f"What trial did {hero.id} have to face on the way?",
            answer=f"{hero.id} had to {trial.verb}, and the road threatened {trial.peril}.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id}?",
            answer=f"{hero.id} returned triumphant with {prize.label} unbroken, which proved the hard road had been crossed.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["trial"].tags)
    tags.add("triumphant")
    out: list[QAItem] = []
    for tag, pairs in KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in pairs)
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="mountain", trial="wind", prize="lantern", name="Iris", gender="girl"),
    StoryParams(place="riverbank", trial="river", prize="lantern", name="Arin", gender="boy"),
    StoryParams(place="temple", trial="light", prize="crown", name="Mira", gender="girl"),
]


ASP_RULES = r"""
% A trial threatens a prize when they share the same body zone.
threatens(T, P) :- trial(T), prize(P), zone(T, Z), region(P, Z).

% A valid mythic story is one where the setting allows the trial and the trial threatens the prize.
valid(Place, T, P) :- setting(Place), affords(Place, T), threatens(T, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for t in sorted(s.affords):
            lines.append(asp.fact("affords", sid, t))
    for tid, t in TRIALS.items():
        lines.append(asp.fact("trial", tid))
        lines.append(asp.fact("zone", tid, t.zone))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, p.region))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, s in SETTINGS.items():
        for t in s.affords:
            for p in PRIZES:
                if TRIALS[t].zone == PRIZES[p].region:
                    combos.append((place, t, p))
    return combos


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic dialogue storyworld with a triumphant ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--trial", choices=TRIALS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.trial is None or c[1] == args.trial)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, trial, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or warrior_name(rng, gender)
    return StoryParams(place=place, trial=trial, prize=prize, name=name, gender=gender)


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = tell(SETTINGS[params.place], TRIALS[params.trial], PRIZES[params.prize], params.name, params.gender)
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
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, trial, prize) combos:\n")
        for item in combos:
            print(" ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.name}: {p.trial} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
