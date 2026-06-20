#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/bite_non_transformation_inner_monologue_suspense_folk.py
======================================================================================

A standalone story world in a folk-tale style about a child, a strange bite,
and a transformation that must be stopped before nightfall.

Seed words: bite, non
Features: Transformation, Inner Monologue, Suspense
Style: Folk Tale

The tiny domain:
- A traveler finds a strange loaf, berry, or charm in a forest cottage.
- One bite can start a transformation.
- A careful companion notices the danger and helps choose the non-biting path.
- The ending proves what changed in the world: either a curse was avoided,
  or the bite caused a partial change that a wise helper reversed.

This file follows the Storyweavers storyworld contract:
- stdlib only
- imports results eagerly
- defines StoryParams, registries, build_parser, resolve_params, generate,
  emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, --show-asp
- includes Python reasonableness gates and inline ASP twin
- generates story-grounded and world-knowledge QA from world state
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SUSPENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    darkness: str
    trail: str
    shelter: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    where: str
    bite: bool
    transform: str
    forbidden: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Companion:
    id: str
    label: str
    trait: str
    warns: str
    helps: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
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

    def copy(self) -> "World":
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("danger_seen") and not world.facts.get("safe_chosen"):
        for eid in ("hero", "companion"):
            world.get(eid).memes["fear"] += 1
        out.append("__suspense__")
    return out


def _r_transformation(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    if not hero:
        return out
    if hero.meters["changed"] >= THRESHOLD and not world.fired.__contains__(("transformed", hero.id)):
        world.fired.add(("transformed", hero.id))
        hero.memes["wonder"] += 1
        out.append("__change__")
    return out


CAUSAL_RULES = [Rule("suspense", "social", _r_suspense), Rule("transformation", "physical", _r_transformation)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def danger_from(charm: Charm) -> bool:
    return charm.bite


def prudent_choice(companion: Companion, charm: Charm) -> bool:
    return companion.trait in {"wise", "careful", "cautious"} and charm.forbidden == "non-biting"


def inner_thought(hero: Entity, text: str) -> str:
    return f"{hero.id} thought, “{text}”"


def choose_story_outcome(charm: Charm, delay: int, companion: Companion) -> str:
    if not danger_from(charm):
        return "averted"
    if companion.trait in {"wise", "careful", "cautious"} and delay == 0:
        return "contained"
    return "transformed"


def _bite(world: World, hero: Entity, charm: Charm) -> None:
    hero.meters["changed"] += 1
    hero.memes["curiosity"] += 1
    world.facts["danger_seen"] = True
    propagate(world, narrate=False)


def warn(world: World, companion: Entity, hero: Entity, charm: Charm, setting: Setting) -> None:
    world.say(
        f"In the old wood by {setting.place}, {hero.id} found {charm.phrase} near {charm.where}. "
        f'"{hero.id}," {companion.id} said softly, "that looks like a {charm.forbidden}."'
    )
    world.say(inner_thought(hero, "It smells sweet, but I do not trust the stillness of it."))
    world.say(
        f"{hero.id} looked at the path, then at the berry, and listened to the hush of the trees."
    )


def suspense_beat(world: World, hero: Entity, companion: Entity, setting: Setting) -> None:
    world.say(
        f"The wind stopped at once. Even the crows were quiet, and the trail into the dark "
        f"seemed to wait for a single foolish choice."
    )
    world.say(
        f"{companion.id} held up {companion.pronoun('possessive')} lantern. "
        f'"We can take the {setting.shelter} road instead," {companion.id} whispered.'
    )


def averted_story(world: World, hero: Entity, companion: Entity, charm: Charm, setting: Setting) -> None:
    world.say(
        f"{hero.id} shut {hero.pronoun('possessive')} mouth and stepped back. "
        f'"No bite," {hero.id} said. "The safe road is enough for me."'
    )
    world.say(
        f"Together they followed the {setting.trail}, leaving {charm.phrase} on the moss where the moon could keep it."
    )
    world.say(
        f"By the time they reached the cottage, {hero.id} still had {hero.pronoun('possessive')} own face, "
        f"and {companion.id} smiled at the clever non-biting choice."
    )


def transformed_story(world: World, hero: Entity, companion: Entity, charm: Charm, setting: Setting) -> None:
    hero.meters["changed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} took one bite. The sweet crust cracked, the hush broke, and a silver line of light "
        f"ran across {hero.pronoun('possessive')} skin."
    )
    world.say(
        f"At once {hero.id} felt {hero.pronoun('possessive')} hands grow light and strange, as if the forest itself "
        f"had reached in and begun to rewrite {hero.pronoun('object')}."
    )
    world.say(
        f"{companion.id} gasped, then steadied {hero.id} under the lantern, whispering, "
        f'"Hold still. We must see what the magic has done."'
    )
    world.say(
        f"At last the change settled: {hero.id} was no longer hungry for the charm, and the old road showed "
        f"its way home at last."
    )


def contained_story(world: World, hero: Entity, companion: Entity, charm: Charm, setting: Setting) -> None:
    hero.meters["changed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} lifted the charm, then paused with it at {hero.pronoun('possessive')} lips."
    )
    world.say(
        f'"Wait," {companion.id} said. "If you bite that, the old tale says you will change."'
    )
    world.say(
        f"{hero.id} swallowed hard. The lantern shook once in {hero.pronoun('possessive')} hand."
    )
    world.say(
        f"Then {hero.id} put the charm down, and the feared change never came; only the night changed, growing kinder."
    )


SETTINGS = {
    "wood": Setting("wood", "the old wood", "quiet", "deepening dusk", "mossy path", "cottage door",
                    tags={"wood", "folk", "suspense"}),
    "orchard": Setting("orchard", "the elder orchard", "golden", "falling shade", "apple lane", "warm kitchen",
                       tags={"orchard", "folk", "suspense"}),
    "river": Setting("river", "the river bend", "silver", "misty dusk", "reed path", "stone bridge",
                     tags={"river", "folk", "suspense"}),
}

CHARMS = {
    "berry": Charm("berry", "berry", "a bowl of red berries", "a root-twined stump", True, "red-mouthed",
                   "a non-biting charm", tags={"berry", "bite"}),
    "cake": Charm("cake", "cake", "a little honey cake", "the doorstep of a hollow tree", True, "sweet-faced",
                  "a non-biting charm", tags={"cake", "bite"}),
    "bread": Charm("bread", "bread", "a round loaf of barley bread", "the window ledge of the cottage", True, "golden-faced",
                   "a non-biting charm", tags={"bread", "bite"}),
    "stone": Charm("stone", "stone", "a smooth gray river-stone", "the bank by the reeds", False, "still-faced",
                   "a non-biting charm", tags={"stone", "non"}),
}

COMPANIONS = {
    "grandmother": Companion("grandmother", "grandmother", "wise", "knows old warnings", "knows the safe road", tags={"wise", "folk"}),
    "miller": Companion("miller", "miller", "careful", "listens for trouble", "brings a lantern", tags={"careful", "folk"}),
    "sister": Companion("sister", "sister", "cautious", "speaks in a low voice", "walks beside the hero", tags={"cautious", "folk"}),
}

GIRL_NAMES = ["Anya", "Mara", "Tilda", "Elin", "Brida"]
BOY_NAMES = ["Robin", "Perrin", "Jonas", "Alden", "Finn"]
TRAITS = ["curious", "brave", "dreamy", "gentle"]


@dataclass
class StoryParams:
    setting: str
    charm: str
    companion: str
    hero_name: str
    hero_gender: str
    hero_trait: str
    delay: int = 0
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for c in CHARMS:
            for p in COMPANIONS:
                charm = CHARMS[c]
                if danger_from(charm) or prudent_choice(COMPANIONS[p], charm):
                    combos.append((s, c, p))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale story world of bites, non-bites, and transformations.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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
    if args.charm and not CHARMS[args.charm].bite and args.delay is None:
        pass
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.charm is None or c[1] == args.charm)
              and (args.companion is None or c[2] == args.companion)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, charm, companion = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(setting, charm, companion, name, gender, trait, delay=delay)


def tell(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity("hero", kind="character", type=params.hero_gender, role="hero", traits=[params.hero_trait]))
    companion = world.add(Entity("companion", kind="character", type="woman", role="companion"))
    hero.id = params.hero_name
    companion.id = COMPANIONS[params.companion].label
    setting = SETTINGS[params.setting]
    charm = CHARMS[params.charm]
    world.facts.update(hero=hero, companion=companion, setting=setting, charm=charm, delay=params.delay)

    world.say(f"Once, in {setting.place}, there lived {hero.id}, a {params.hero_trait} child who loved the old folk roads.")
    world.say(f"{hero.id} and {companion.id} came upon {charm.phrase} by {charm.where}.")
    world.para()
    warn(world, companion, hero, charm, setting)
    world.facts["danger_seen"] = charm.bite
    outcome = choose_story_outcome(charm, params.delay, COMPANIONS[params.companion])
    if outcome == "averted":
        world.facts["safe_chosen"] = True
        suspense_beat(world, hero, companion, setting)
        world.para()
        averted_story(world, hero, companion, charm, setting)
    elif outcome == "contained":
        world.facts["safe_chosen"] = False
        suspense_beat(world, hero, companion, setting)
        world.para()
        contained_story(world, hero, companion, charm, setting)
    else:
        world.facts["safe_chosen"] = False
        suspense_beat(world, hero, companion, setting)
        world.para()
        transformed_story(world, hero, companion, charm, setting)
    world.facts["outcome"] = outcome
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk-tale story that includes the words "bite" and "non" and features an inner monologue and suspense.',
        f"Tell a short tale where {f['hero'].id} almost takes a bite of {f['charm'].label}, but {f['companion'].id} helps with a wiser non-biting choice.",
        f"Write a suspenseful folk story about {f['setting'].place} where one bite might cause a transformation, and the ending proves what changed.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, companion, charm, setting = f["hero"], f["companion"], f["charm"], f["setting"]
    qas = [
        QAItem(
            question=f"What was the danger in the story?",
            answer=f"The danger was that one bite of {charm.phrase} could cause a transformation. The old tale made the choice feel risky because the change might begin at once."
        ),
        QAItem(
            question=f"What did {hero.id} think to themself?",
            answer=f"{hero.id} thought that the charm smelled sweet, but the stillness around it felt wrong. That inner thought helped {hero.id} pause before doing anything foolish."
        ),
        QAItem(
            question=f"How did {companion.id} help?",
            answer=f"{companion.id} warned {hero.id} and pointed to the safer road, choosing the non-biting way. That kept the suspense from becoming a full curse."
        ),
    ]
    if f["outcome"] == "averted":
        qas.append(QAItem(
            question="How did the story end?",
            answer=f"It ended safely, with {hero.id} leaving the charm behind and taking the road home. The night changed, but {hero.id} did not."
        ))
    elif f["outcome"] == "contained":
        qas.append(QAItem(
            question="Did the transformation happen?",
            answer=f"A small change started, but it was stopped before it became a true curse. The wise companion kept the trouble from growing."
        ))
    else:
        qas.append(QAItem(
            question="What changed by the end?",
            answer=f"{hero.id} changed after the bite, and the forest felt different too. The ending image shows the magic settling into a real transformation."
        ))
    return qas


WORLD_KNOWLEDGE = {
    "bite": [("Why can a bite matter in old tales?",
              "In old tales, a bite can carry magic or a curse, so one small bite can change a person or start a big problem.")],
    "non": [("What does non- mean?",
             "Non- means not or without. A non-biting choice is a choice without biting.")],
    "transformation": [("What is a transformation?",
                        "A transformation is a big change, when something becomes different from what it was before.")],
    "suspense": [("What is suspense in a story?",
                  "Suspense is the feeling of waiting and wondering what will happen next.")],
    "folk": [("What is a folk tale?",
             "A folk tale is an old story that is told again and again, often with magic, warnings, and a lesson.")],
}
WORLD_ORDER = ["folk", "suspense", "bite", "non", "transformation"]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["setting"].tags) | set(world.facts["charm"].tags) | {"folk", "suspense"}
    out: list[QAItem] = []
    for tag in WORLD_ORDER:
        if tag in tags and tag in WORLD_KNOWLEDGE:
            q, a = WORLD_KNOWLEDGE[tag][0]
            out.append(QAItem(q, a))
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
    lines.append("== (3) World knowledge questions ==")
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, C, P) :- setting(S), charm(C), companion(P).
danger(C) :- charm(C), bite(C).
safe(C) :- charm(C), not bite(C).
outcome(averted) :- safe(C), chosen(C).
outcome(contained) :- danger(C), wise(P), delay(0).
outcome(transformed) :- danger(C), not wise(P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, c in CHARMS.items():
        lines.append(asp.fact("charm", cid))
        lines.append(asp.fact("bite", cid, int(c.bite)))
    for pid, p in COMPANIONS.items():
        lines.append(asp.fact("companion", pid))
        if p.trait == "wise":
            lines.append(asp.fact("wise", pid))
    lines.append(asp.fact("delay", 0))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    return choose_story_outcome(CHARMS[params.charm], params.delay, COMPANIONS[params.companion])


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP matches Python valid_combos().")
    else:
        print("MISMATCH in valid_combos().")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, charm=None, companion=None, gender=None, name=None, delay=None), random.Random(1)))
        assert sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def explain_rejection(charm: Charm) -> str:
    if not charm.bite:
        return "(No story: this charm cannot start the bite-and-transformation tale.)"
    return "(No story: invalid combination.)"


def explain_response() -> str:
    return "(No story: no suitable suspenseful branch exists.)"


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
    StoryParams("wood", "berry", "grandmother", "Anya", "girl", "curious", delay=0),
    StoryParams("orchard", "cake", "miller", "Robin", "boy", "brave", delay=1),
    StoryParams("river", "stone", "sister", "Tilda", "girl", "gentle", delay=0),
]


def resolve_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.charm is None or c[1] == args.charm)
              and (args.companion is None or c[2] == args.companion)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, charm, companion = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(setting, charm, companion, name, gender, trait, delay=delay)


def build_parser_wrapper() -> argparse.ArgumentParser:
    return build_parser()


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_story_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
