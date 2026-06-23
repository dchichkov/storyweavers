#!/usr/bin/env python3
"""
storyworlds/worlds/pedicure_ethic_attack_seaside_promenade_misunderstanding_animal.py
=====================================================================================

A tiny animal-story world at a seaside promenade.

Seed tale:
- A small animal wants a pedicure at the seaside promenade.
- Another animal mistakes the tools and the sea-scented fuss for an attack.
- A calm helper explains the ethic of gentle care.
- The misunderstanding clears, and the ending proves the change: clean paws, peaceful promenade, kinder play.

This world models:
- typed entities with physical meters and emotional memes,
- a forward story state that drives prose,
- a reasonableness gate,
- an inline ASP twin,
- three QA sets grounded in simulated world state.

Words required by the seed prompt are used in the world model and prose:
pedicure, ethic, attack, misunderstanding, seaside promenade
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, object] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "cat", "seagull"}
        male = {"boy", "father", "dad", "man", "dog", "otter"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.attrs.get("plural") else "it"


@dataclass
class Place:
    id: str
    label: str
    seaside: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    zone: set[str]
    mess: str
    soil: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class PrizedThing:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    prep: str
    tail: str
    protects: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str = "promenade"
    activity: str = "pedicure"
    prize: str = "paws"
    helper: str = "towel"
    animal: str = "dog"
    watcher: str = "seagull"
    name: str = "Milo"
    watcher_name: str = "Pip"
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def animals(self) -> list[Entity]:
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        return clone


def _rule_splatter(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.animals():
        if actor.meters.get("messy", 0.0) < THRESHOLD:
            continue
        sig = ("splatter", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        helper = world.get("helper")
        helper.meters["used"] = helper.meters.get("used", 0.0) + 1
        out.append(f"{actor.label}'s paws stayed in the careful little wash basin.")
    return out


def _rule_misunderstanding(world: World) -> list[str]:
    for actor in world.animals():
        if actor.memes.get("alarm", 0.0) < THRESHOLD:
            continue
        sig = ("misunderstanding", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] = actor.memes.get("conflict", 0.0) + 1
        return ["__misunderstanding__"]
    return []


CAUSAL_RULES = [_rule_splatter, _rule_misunderstanding]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule(world)
            if out:
                changed = True
                produced.extend(x for x in out if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for act_id in place.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize.region in act.zone:
                    combos.append((place_id, act_id, prize_id))
    return combos


def explain_rejection(activity: Activity, prize: PrizedThing) -> str:
    return (
        f"(No story: {activity.verb} never reaches {prize.label} in a way that can "
        f"cause a misunderstanding. Pick a prize in {sorted(activity.zone)}.)"
    )


def select_helper(activity: Activity, prize: PrizedThing) -> Optional[Helper]:
    for helper in HELPERS:
        if prize.region in helper.protects:
            return helper
    return None


def predict_conflict(world: World, actor: Entity, activity: Activity, prize_id: str) -> bool:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    return sim.get(actor.id).memes.get("alarm", 0.0) >= THRESHOLD


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.meters["messy"] = actor.meters.get("messy", 0.0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
    propagate(world, narrate=narrate)


def start(world: World, hero: Entity, watcher: Entity) -> None:
    world.say(
        f"On a bright morning at the seaside promenade, {hero.label} and "
        f"{watcher.label} wandered past the candy stall and the gulls."
    )
    world.say(
        f"{hero.label} was a little {hero.type} who loved quiet grooming days and "
        f"small splashes near the water."
    )


def want_pedicure(world: World, hero: Entity, activity: Activity, prize: Entity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    world.say(
        f"{hero.label} wanted a {activity.keyword} because {hero.pronoun()} liked "
        f"having {prize.label} neat and shiny."
    )


def mistake_for_attack(world: World, watcher: Entity, hero: Entity, activity: Activity) -> None:
    watcher.memes["alarm"] = watcher.memes.get("alarm", 0.0) + 1
    world.say(
        f"{watcher.label} saw the brush, the suds, and the busy paws and thought "
        f"it looked like an attack."
    )
    world.say(
        f'"Wait!" {watcher.label} cried. "That looks mean!"'
    )


def explain_ethic(world: World, helper: Entity, hero: Entity, watcher: Entity) -> None:
    helper.memes["calm"] = helper.memes.get("calm", 0.0) + 1
    world.say(
        f"{helper.label} spoke gently and explained the ethic of the moment: "
        f"care for animals softly, never with rough hands."
    )
    world.say(
        f"Then {helper.label} showed that the soap was for cleaning, not hurting."
    )


def clear_misunderstanding(world: World, hero: Entity, watcher: Entity, prize: Entity, helper: Entity) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["conflict"] = 0.0
    watcher.memes["alarm"] = 0.0
    watcher.memes["relief"] = watcher.memes.get("relief", 0.0) + 1
    world.say(
        f"{watcher.label} blinked, then laughed in relief. It was only a {helper.label}, "
        f"a friendly little pedicure, and a careful wash for {prize.label}."
    )
    world.say(
        f"By the end, {hero.label} had neat {prize.label}, {watcher.label} had a soft smile, "
        f"and the promenade felt peaceful again."
    )


PLACES = {
    "promenade": Place(id="promenade", label="the seaside promenade", affords={"pedicure"}),
    "dock": Place(id="dock", label="the wooden dock", affords={"pedicure"}),
}

ACTIVITIES = {
    "pedicure": Activity(
        id="pedicure",
        verb="give a pedicure",
        gerund="giving a pedicure",
        rush="dash at the paws with the brush",
        zone={"paws"},
        mess="splash",
        soil="wet and foamy",
        keyword="pedicure",
        tags={"pedicure", "care", "water"},
    ),
}

PRIZES = {
    "paws": PrizedThing(
        id="paws",
        label="paws",
        phrase="tiny paws",
        region="paws",
        plural=True,
        tags={"animal", "paws"},
    ),
}

HELPERS = [
    Helper(
        id="towel",
        label="a soft towel",
        prep="dry the paws gently with",
        tail="wrapped up the paws and dried them with the soft towel",
        protects={"paws"},
        tags={"towel", "care"},
    ),
    Helper(
        id="brush",
        label="a baby brush",
        prep="brush the fur with",
        tail="brushed the fur with a baby brush and let the soap rinse away",
        protects={"paws"},
        tags={"brush", "care"},
    ),
]

ANIMAL_NAMES = ["Milo", "Pip", "Ruby", "Otis", "Nina", "Bram"]
WATCHER_NAMES = ["Pip", "Sage", "Mina", "Wren", "Dot", "Jules"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: an animal misunderstanding at the seaside promenade.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--helper", choices=[h.id for h in HELPERS])
    ap.add_argument("--animal", choices=["dog", "cat", "otter", "seagull"])
    ap.add_argument("--name")
    ap.add_argument("--watcher-name")
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
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    helper = args.helper or rng.choice([h.id for h in HELPERS])
    animal = args.animal or rng.choice(["dog", "cat", "otter", "seagull"])
    name = args.name or rng.choice(ANIMAL_NAMES)
    watcher_name = args.watcher_name or rng.choice([n for n in WATCHER_NAMES if n != name])
    return StoryParams(place=place, activity=activity, prize=prize, helper=helper, animal=animal, watcher=animal, name=name, watcher_name=watcher_name)


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    act = ACTIVITIES[params.activity]
    prize_cfg = PRIZES[params.prize]
    helper_cfg = next(h for h in HELPERS if h.id == params.helper)
    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", type=params.animal, label=params.name))
    watcher = world.add(Entity(id="watcher", kind="character", type="seagull", label=params.watcher_name))
    helper = world.add(Entity(id="helper", kind="character", type="otter", label="the harbor helper"))

    hero.meters["messy"] = 0.0
    hero.memes["joy"] = 0.0
    hero.memes["desire"] = 0.0
    hero.memes["conflict"] = 0.0
    watcher.memes["alarm"] = 0.0
    watcher.memes["relief"] = 0.0
    helper.memes["calm"] = 0.0
    world.facts.update(params=params, place=place, activity=act, prize_cfg=prize_cfg, helper_cfg=helper_cfg,
                       hero=hero, watcher=watcher, helper=helper, resolved=False, misunderstanding=False)

    start(world, hero, watcher)
    world.para()
    want_pedicure(world, hero, act, hero)
    mistake_for_attack(world, watcher, hero, act)
    predicted = predict_conflict(world, hero, act, prize_cfg.id)
    world.facts["misunderstanding"] = predicted
    world.para()
    explain_ethic(world, helper, hero, watcher)
    clear_misunderstanding(world, hero, watcher, hero, helper)
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short animal story set at the seaside promenade that includes the words "pedicure", "attack", and "ethic".',
        f"Tell a gentle story where {f['hero'].label} wants a pedicure, {f['watcher'].label} misunderstands it as an attack, and a helper explains the ethic of kind care.",
        'Write a child-friendly story about a seaside promenade misunderstanding that ends with peaceful paws and a clear lesson.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    watcher: Entity = f["watcher"]
    helper: Entity = f["helper"]
    prize_cfg: PrizedThing = f["prize_cfg"]
    qa = [
        QAItem(
            question=f"Why did {hero.label} go to the seaside promenade?",
            answer=f"{hero.label} went there for a pedicure, because {hero.pronoun()} wanted {prize_cfg.label} to be clean and neat. The promenade was a calm place for gentle care."
        ),
        QAItem(
            question=f"Why did {watcher.label} think the scene was an attack?",
            answer=f"{watcher.label} saw the fast hands, the suds, and the busy paws and got worried. It looked rough from far away, even though it was really only careful grooming."
        ),
        QAItem(
            question=f"What did the helper explain about the ethic of the moment?",
            answer=f"{helper.label} explained that the ethic was to treat animals softly and kindly. That explanation turned the noisy misunderstanding into a peaceful little lesson."
        ),
        QAItem(
            question=f"How did the story end for {hero.label} and {watcher.label}?",
            answer=f"They ended with clean paws, a relieved smile, and no more misunderstanding. The seaside promenade felt friendly again because everyone understood the pedicure was gentle."
        ),
    ]
    if f.get("misunderstanding"):
        qa.append(QAItem(
            question="What first caused the misunderstanding?",
            answer="The grooming tools and splashing water looked scary from a distance. The watcher thought it might be an attack, but it was only a pedicure."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pedicure?",
            answer="A pedicure is a gentle care routine for feet or paws, where they are cleaned and made neat."
        ),
        QAItem(
            question="What is an ethic?",
            answer="An ethic is a rule about what is kind, fair, and right to do."
        ),
        QAItem(
            question="What does attack mean?",
            answer="An attack is a harmful action that tries to hurt or scare someone or something."
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks a situation means one thing, but it really means something else."
        ),
        QAItem(
            question="What is a seaside promenade?",
            answer="A seaside promenade is a walking path near the sea where people and animals can stroll and watch the water."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        out.append(f"  {e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    out.append(f"  zone={sorted(world.zone)}")
    return "\n".join(out)


ASP_RULES = r"""
misunderstanding(H) :- alarm(H), gentle_care(H).
resolved(H) :- misunderstanding(H), calm_explanation(H).
good_story(P,A,Pr) :- place(P), activity(A), prize(Pr), fits(A,Pr).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
        for z in sorted(ACTIVITIES[a].zone):
            lines.append(asp.fact("fits", a, z))
    for p in PRIZES:
        lines.append(asp.fact("prize", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good_story/3."))
    return sorted(set(asp.atoms(model, "good_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = True
    if py != cl:
        ok = False
        print("MISMATCH between Python and ASP gates")
        print("only python:", sorted(py - cl))
        print("only asp:", sorted(cl - py))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    if ok:
        print(f"OK: ASP parity and smoke test passed ({len(py)} combos).")
        return 0
    return 1


CURATED = [
    StoryParams(place="promenade", activity="pedicure", prize="paws", helper="towel", animal="dog", watcher="seagull", name="Milo", watcher_name="Pip"),
    StoryParams(place="promenade", activity="pedicure", prize="paws", helper="brush", animal="cat", watcher="seagull", name="Ruby", watcher_name="Sage"),
]


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.activity not in ACTIVITIES or params.prize not in PRIZES:
        raise StoryError("Invalid params for this story world.")
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show good_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show good_story/3."))
        print(asp.atoms(model, "good_story"))
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
