#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
import textwrap
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample

THRESHOLD = 1.0
METER_KEYS = {"closeness", "noise_level"}
MEME_KEYS = {"love", "joy", "disappointment"}

@dataclass
class Entity:
    id: str
    kind: str = "character"
    type: str = ""
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    region: str = ""
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"mama", "mom", "auntie", "grandma"}
        male = {}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mama": "mama"}.get(self.type, self.type)

@dataclass
class Setting:
    place: str = "the cantina"
    indoor: bool = True
    feature: str = "warm lights and wooden tables"

@dataclass
class Activity:
    id: str = "tasting"
    verb: str = "taste the sweet things"
    gerund: str = "tasting sweet treats together"
    rush: str = "grab the nearest sweet thing"
    spoil: str = "spoiled and loud"
    tags: set[str] = field(default_factory=set)

@dataclass
class Prize:
    label: str = ""
    phrase: str = ""
    type: str = ""
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, line: str) -> None:
        if line:
            self.paragraphs[-1].append(line)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        lines = []
        for p in self.paragraphs:
            if p:
                wrapped = [textwrap.fill(sent, width=70, break_long_words=False, break_on_hyphens=False) for sent in p]
                lines.extend(line for para in wrapped for line in para.split("\n"))
        return "\n\n".join(lines)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

def _r_noise_impact(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if world.setting.place == "the cantina" and actor.meters["noise_level"] >= THRESHOLD:
            sig = ("noise", actor.id)
            if sig not in world.fired:
                world.fired.add(sig)
                if actor.memes["disappointment"] < THRESHOLD:
                    out.append(f'"This place feels too busy," {actor.pronoun()} sighed.')
        elif actor.memes["love"] >= THRESHOLD:
            sig = ("joy", actor.id)
            if sig not in world.fired:
                world.fired.add(sig)
                out.append(f'"Let\'s share this sweetness," {actor.pronoun("possessive")} voice rang clear.')
    return out

def _r_closeness_reward(world: World) -> list[str]:
    out: list[str] = []
    for a1 in world.characters():
        for a2 in world.characters():
            if a1.id == a2.id:
                continue
            closeness = min(a1.meters["closeness"], a2.meters["closeness"])
            if closeness >= THRESHOLD:
                sig = ("bond", a1.id, a2.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    out.append(f'Cuddled close by lantern glow, their hearts beat as one.')
    return out

CAUSAL_RULES: list[Rule] = [
    Rule(name="noise_impact", tag="social", apply=_r_noise_impact),
    Rule(name="closeness_reward", tag="social", apply=_r_closeness_reward),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced

def rhyming_wrap(text: str) -> str:
    lines = []
    words = text.split()
    for i in range(0, len(words), 5):
        chunk = " ".join(words[i:i+5])
        if i > 0:
            lines[-1] += " " + chunk
        else:
            lines.append(chunk)
    return "\n".join(lines)

def in_cantina_quarrel(world: World) -> bool:
    return world.setting.place == "the cantina" and world.entities["Sweetum"].memes["disappointment"] >= THRESHOLD

def share_sweetness(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] += 1.2
    hero.memes["joy"] += 1.0
    prize.worn_by = hero.id
    world.paragraphs[-1][-1] += " " + (
        f'"Sweet {prize.label}, oh so fine! '
        f'Just for you—now it\'s thine!"'
    )
    world.paragraphs[-1].append(
        f'They shared a bite, so small, so bright, '
        f'in warm glow of lantern light.'
    )

def arrive(world: World, hero: Entity, mama: Entity) -> None:
    who_takes = "her mama warm and true" if hero.type in {"girl", "sweetum"} else "his mama strong and true"
    world.say(
        f'One twilight hour, kind and bright, '
        f'{who_takes} led {hero.id} to the cantina\'s light.'
    )
    world.say(
        f'The {world.setting.feature} '
        f'shimmered gold through misty air—'
    )

def admire_treats(world: World, mama: Entity, treat: Entity) -> str:
    return (
        f'{mama.pronoun("subject").capitalize()} spied a stack so fine and neat: '
        f'{treat.phrase.lower()}! Sweet and small and oh so sweet.'
    )

def wanna_leave(world: World, sweetum: Entity) -> str:
    return (
        f'But Sweetum pouted, crossed each arm: '
        f'"This place is loud! Let\'s go—it means no harm!"'
    )

def persuade_stay(world: World, mama: Entity, treat: Entity) -> str:
    return (
        f"{mama.pronoun('subject').capitalize()} bent low with tender grace, "
        f'"Just one bite of this sweet taste."'
    )

def enjoy_silence(world: World) -> str:
    return (
        'Between the clinks and soft guitar, '
        'they found a hush, just them—so far.'
    )

def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         child_name: str = "Sweetum", child_type: str = "sweetum",
         child_traits: Optional[list[str]] = None) -> World:
    world = World(setting)

    mama = world.add(Entity(
        id="Mama", kind="character", type="mama",
        label="mama", traits=["loving", "patient"],
        phrase="a loving mama",
    ))
    sweetum = world.add(Entity(
        id=child_name, kind="character", type=child_type,
        label="Sweetum", traits=["sweet", "curious"] + (child_traits or []),
        phrase="her Sweetum",
    ))
    treat = world.add(Entity(
        id="sweet", type="treat", label=prize_cfg.label,
        phrase=prize_cfg.phrase, region="hands", plural=prize_cfg.plural,
    ))

    setting.indoor = True
    setting.feature = "soft lantern glow and wooden beams tall"

    world.say(f'{sweetum.pronoun("subject").capitalize()} was a {child_type} small,')
    world.say("soft of heart and sweetest of them all.")
    world.say(
        f'{sweetum.pronoun("subject").capitalize()} enjoyed the simple things, '
        'the hum of life that springtime brings.'
    )
    world.para()

    arrive(world, sweetum, mama)
    world.say(
        f'They picked a corner, small and sweet, '
        'where quiet friends could skip and meet.'
    )

    world.paragraphs[-1].append(admire_treats(world, mama, treat))
    share_sweetness(world, mama, treat)

    world.para()
    world.say(wanna_leave(world, sweetum))
    world.say(persuade_stay(world, mama, treat))
    world.say(enjoy_silence(world))

    mama.meters["closeness"] = 1.4
    sweetum.meters["closeness"] = 1.2
    mama.meters["noise_level"] = 0.3
    sweetum.meters["noise_level"] = 0.4 if in_cantina_quarrel(world) else 0.1

    propagate(world)

    world.facts.update(
        mama=mama, sweetum=sweetum, treat=treat,
        closeness=mama.meters["closeness"],
        noisy=(world.setting.place == "the cantina"),
        resolved=not in_cantina_quarrel(world),
    )
    return world

SETTINGS = {
    "cantina": Setting(place="the cantina", feature="golden lanterns on wooden beams"),
}

ACTIVITIES = {
    "tasting": Activity(
        id="tasting",
        verb="share sweet things",
        gerund="sharing sweet treats together",
        rush="grab the nearest sweet",
        spoil="bright laughter becomes the only sound",
        tags={"sweet", "tasting", "cantina", "maternal"},
    ),
}

PRIZES = {
    "candy": Prize(
        label="red candy",
        phrase="a shiny little red candy",
        type="candy",
        plural=False,
    ),
    "sweetdrink": Prize(
        label="honey sip",
        phrase="a small cup of golden honey sip",
        type="drink",
        plural=True,
    ),
}

NAMES = ["Luna", "Nova", "Bree", "Daisy"]

@dataclass
class StoryParams:
    place: str = "cantina"
    activity: str = "tasting"
    prize: str = "candy"
    name: str = "Sweetum"
    gender: str = "girl"
    seed: Optional[int] = None

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id, act in ACTIVITIES.items():
            if place != "cantina" and act_id != "tasting":
                continue
            for prize_id in PRIZES:
                if act_id == "tasting" and place == "cantina":
                    combos.append((place, act_id, prize_id))
    return combos

KNOWLEDGE = {
    "cantina": [("What is a cantina?",
                 "A cantina is a cozy tavern or gathering place where people share food and songs.")],
    "sweet": [("Why do we love sweet things?",
                "Sweet foods taste nice to our tongues and often make us feel happy and loving.")],
    "mama": [("What does a mama do?",
              "A mama loves, feeds, and cares for little ones like Sweetum.")],
    "sharing": [("Why do we share sweets?",
                  "Sharing makes the sweet taste even sweeter and brings hearts together.")],
}
KNOWLEDGE_ORDER = ["sweet", "mama", "sharing", "cantina"]

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a gentle rhyming bedtime poem for a small child about a mama taking their sweetie to a "cantina" to share one small sweet treat.',
        'Compose a few short stanzas in rhyming couplets that tell the tale of Mama and Sweetum discovering quiet joy in a bustling corner of the cantina.',
        'Create a tiny, rhyming story where a mama and her small sweet child find a calm sweet moment together despite visiting a busy place.',
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    sweetum, mama = f["sweetum"], f["mama"]
    sub = sweetum.pronoun("subject")
    obj = sweetum.pronoun("object")
    pos = sweetum.pronoun("possessive")
    return [
        QAItem(
            question="Who took Sweetum to the cantina to share something sweet?",
            answer=(
                "It was a loving mama who took Sweetum to the cantina. "
                "They went together to share a small sweet moment."
            ),
        ),
        QAItem(
            question="What did Sweetum and Mama share in the cantina?",
            answer=(
                f"{sub.capitalize()} shared a {world.get('sweet').label} "
                "from a quiet corner with the golden lantern glow."
            ),
        ),
        QAItem(
            question="How did Sweetum feel when they first arrived at the cantina?",
            answer=(
                f'{sub.capitalize()} thought the place was loud at first, '
                "but Mama found a sweet spot so they could sit together."
            ),
        ),
    ]

KNOWLEDGE_RULES = {
    "busy implies disappointment": lambda w: (
        w.entities["Sweetum"].memes["disappointment"] >= THRESHOLD
    ),
    "closeness implies love": lambda w: (
        w.get("Mama").meters["closeness"] >= 1.0 and
        w.get("Sweetum").meters["closeness"] >= 1.0
    ),
}

def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    tags = set()
    tags.add("cantina")
    tags.update(w.tags for w in ACTIVITIES.values())
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE.get(tag, []))
    if KNOWLEDGE_RULES["closeness implies love"](world):
        out.append(QAItem(
            question="What helped Sweetum feel safe despite the busy cantina?",
            answer=(
                "Being close to Mama with shared warmth and sweetness "
                "made Sweetum feel safe and loved."
            ),
        ))
    return out

ASP_RULES = r"""
% A story is valid when:
% - it happens in a cantina
% - involves a mama and a child named Sweetum
% - resolves the quiet-sharing of a sweet treat
valid_story :- setting(cantina).
valid_story :- character(mama).
valid_story :- character(sweetum), name(sweetum).
valid_story :- shared(sweet_treat).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = [asp.fact("setting", "cantina")]
    lines.append(asp.fact("character", "mama"))
    lines.append(asp.fact("character", "sweetum"))
    lines.append(asp.fact("name", "sweetum"))
    lines.append(asp.fact("shared", "sweet_treat"))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/0."))
    return [(1,)] if model else []

def asp_verify() -> int:
    clingo_set, python_set = set(asp_stories()), {(1,)}
    if clingo_set == python_set:
        print(f"OK: ASP gate grants exactly {len(clingo_set)} compatible story shape.")
        return 0
    print("MISMATCH between clingo and python guard:")
    sys.exit(1)

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Maternal Cantina Sweetum Dialogue: a tiny rhyming story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
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
    if args.all:
        base = StoryParams(
            place="cantina",
            activity="tasting",
            prize="candy",
            name="Luna",
            gender="girl",
        )
        base.seed = 0xBEEF
        return base

    if args.activity or args.prize or args.place:
        act_ok = (args.activity is None) or (args.activity == "tasting")
        place_ok = (args.place is None) or (args.place == "cantina")
        prize_ok = (args.prize in PRIZES)
        if not (act_ok and place_ok and prize_ok):
            raise StoryError(
                "Only cantina+tasting+prizes are valid. "
                "Run with --all to see the curated set."
            )

    params = StoryParams(
        place=args.place or "cantina",
        activity=args.activity or "tasting",
        prize=args.prize or rng.choice(list(PRIZES.keys())),
        name=args.name or rng.choice(NAMES),
        gender="girl",
        seed=args.seed,
    )
    return params

def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        params.name,
        child_type="sweetum", child_traits=["small", "quiet"],
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )

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
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, * in world.fired))}")
    return "\n".join(lines)

def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print("== Story Q&A ==")
        for qa in sample.story_qa:
            print(f"Q: {qa.question}")
            print(f"A: {qa.answer}")
        print("\n== World Q&A ==")
        for qa in sample.world_qa:
            print(f"Q: {qa.question}")
            print(f"A: {qa.answer}")

def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        ok = "valid" if asp_stories() else "invalid"
        print(f"Combinatorics gate: stories are {ok}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(place="cantina", activity="tasting", prize="candy", name="Luna", seed=0xBEEF))]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 10, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                if args.trace:
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
        if args.all or len(samples) > 1:
            header = f"### Rhyming Cantina Sweetum Story #{i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
