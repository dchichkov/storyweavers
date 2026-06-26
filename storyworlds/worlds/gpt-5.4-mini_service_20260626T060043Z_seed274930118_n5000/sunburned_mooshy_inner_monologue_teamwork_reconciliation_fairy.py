#!/usr/bin/env python3
"""
A tiny fairy-tale storyworld about a sunburned helper, a mooshy path, teamwork,
and reconciliation.

This world is designed as a classical simulation rather than a frozen template:
characters have physical meters and emotional memes, the plot advances by world
state, and the ending proves what changed.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    place: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        feminine = {"girl", "princess", "queen", "fairy", "mother", "woman"}
        masculine = {"boy", "prince", "king", "knight", "father", "man"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Trial:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)


@dataclass
class Rule:
    name: str
    apply: callable


def _r_soak(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.meters.get("wet", 0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.place and item.place != world.setting.place:
                continue
            sig = ("soak", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["wet"] = item.meters.get("wet", 0) + 1
            item.meters["mooshy"] = item.meters.get("mooshy", 0) + 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} turned mooshy.")
    return out


def _r_work(world: World) -> list[str]:
    out = []
    for item in world.entities.values():
        if item.meters.get("mooshy", 0) < THRESHOLD or not item.caretaker:
            continue
        sig = ("work", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        caretaker = world.get(item.caretaker)
        caretaker.meters["busy"] = caretaker.meters.get("busy", 0) + 1
        out.append(f"That meant more work for {caretaker.label}.")
    return out


def _r_reconcile(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.memes.get("hurt", 0) < THRESHOLD:
            continue
        if actor.memes.get("helped", 0) < THRESHOLD:
            continue
        sig = ("reconcile", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["hurt"] = 0
        actor.memes["peace"] = actor.memes.get("peace", 0) + 1
        out.append("__reconcile__")
    return out


CAUSAL_RULES = [
    Rule("soak", _r_soak),
    Rule("work", _r_work),
    Rule("reconcile", _r_reconcile),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(x for x in lines if x != "__reconcile__")
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def predict_mooshy(world: World, actor: Entity, trial: Trial, target_id: str) -> dict:
    sim = World(world.setting)
    sim.entities = {
        k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label,
            "phrase": v.phrase, "owner": v.owner, "caretaker": v.caretaker,
            "worn_by": v.worn_by, "place": v.place, "plural": v.plural,
            "meters": dict(v.meters), "memes": dict(v.memes),
        }) for k, v in world.entities.items()
    }
    hero = sim.get(actor.id)
    hero.meters["wet"] = hero.meters.get("wet", 0) + 1
    item = sim.get(target_id)
    if trial.zone & {"feet", "legs", "torso"}:
        item.meters["mooshy"] = item.meters.get("mooshy", 0) + 1
    return {"mooshy": item.meters.get("mooshy", 0) >= THRESHOLD}


def tell(world: World, hero: Entity, friend: Entity, item: Entity, trial: Trial, aid: Optional[Aid]) -> World:
    world.say(
        f"Once upon a time, {hero.id} was a little {hero.type} who could hear every rustle "
        f"of the willow leaves and every whisper of the wind."
    )
    world.say(
        f"{hero.pronoun().capitalize()} loved {trial.gerund}, because it made the whole meadow feel like a song."
    )
    world.say(
        f"One bright morning, {friend.id} brought {hero.id} a {item.phrase} for the path."
    )
    item.worn_by = hero.id
    world.say(
        f"{hero.id} treasured {hero.pronoun('possessive')} {item.label}, and {friend.id} promised to keep it safe."
    )

    world.para()
    world.say(
        f"But when they came to {world.setting.place}, the ground was { 'soft and mooshy' }."
    )
    hero.meters["wet"] = hero.meters.get("wet", 0) + 1
    pred = predict_mooshy(world, hero, trial, item.id)
    if pred["mooshy"]:
        world.say(
            f"{hero.id} wanted to {trial.verb}, yet {hero.pronoun('possessive')} heart gave a small worried flutter."
        )
        world.say(
            f'"If I step there, my {item.label} will get {trial.soil}," {hero.pronoun("subject")} thought.'
        )
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    friend.memes["worry"] = friend.memes.get("worry", 0) + 1

    world.say(
        f'"We should be careful," {friend.id} said, though {friend.pronoun("subject")} felt unsure too.'
    )
    world.say(
        f"{hero.id} took a slow breath and listened to the little voice inside."
    )
    world.say(
        f'"Maybe the meadow needs help first," {hero.pronoun("subject")} thought.'
    )

    world.para()
    if aid is None:
        raise StoryError("No suitable aid exists for this fairy-tale trial.")
    world.say(
        f"{hero.id} pointed to the bent reeds and the soggy stepping stones. "
        f'"What if we {aid.prep}?" {hero.pronoun("subject")} asked.'
    )
    world.say(
        f"{friend.id}'s eyes shone. "{aid.prep.capitalize()} would take teamwork," {friend.pronoun("subject")} said, "but we can do it.""
    )
    helper = world.add(Entity(id="Helper", kind="character", type="fairy", label="the little fairy"))
    helper.memes["kindness"] = 1

    world.say(
        f"So the three of them worked together: {friend.id} lifted the fallen branch, "
        f"{helper.id} sprinkled a dry trail of dust, and {hero.id} steadied the stones."
    )
    hero.memes["helped"] = hero.memes.get("helped", 0) + 1
    friend.memes["helped"] = friend.memes.get("helped", 0) + 1
    helper.memes["helped"] = 1
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"When the path was ready, {hero.id} smiled at {friend.id}. "
        f'"I was afraid," {hero.pronoun("subject")} admitted, "but I knew we could fix it together."'
    )
    world.say(
        f'{friend.id} bowed her head. "I was afraid too," she said, "and I am sorry I doubted your idea."'
    )
    friend.memes["apology"] = 1
    hero.memes["forgive"] = 1
    hero.memes["peace"] = hero.memes.get("peace", 0) + 1
    world.say(
        f"{hero.id} took {friend.id}'s hand, and the two of them crossed the meadow by the new dry way."
    )
    world.say(
        f"At the end of the day, {item.label} stayed dry, the mooshy ground had a safe trail, and the friends walked home laughing like bells."
    )
    world.facts.update(hero=hero, friend=friend, item=item, trial=trial, aid=aid)
    return world


SETTINGS = {
    "meadow": Setting(place="the moonlit meadow", affords={"cross"}),
    "brook": Setting(place="the brookside path", affords={"cross"}),
    "garden": Setting(place="the herb garden", affords={"cross"}),
}

TRIALS = {
    "crossing": Trial(
        id="crossing",
        verb="cross the mooshy path",
        gerund="dancing lightly over wet stones",
        rush="hurry over the soft ground",
        mess="mooshy",
        soil="mooshy and muddy",
        zone={"feet"},
        keyword="mooshy",
        tags={"mooshy", "path"},
    )
}

AIDS = {
    "planks": Aid(
        id="planks",
        label="little wooden planks",
        phrase="a bundle of little wooden planks",
        covers={"feet"},
        guards={"mooshy"},
        prep="lay down the little wooden planks first",
        tail="laid down the little wooden planks",
    ),
    "stones": Aid(
        id="stones",
        label="flat stepping stones",
        phrase="a line of flat stepping stones",
        covers={"feet"},
        guards={"mooshy"},
        prep="place the flat stepping stones in a line",
        tail="placed the flat stepping stones",
    ),
}

HERO_NAMES = ["Elara", "Nia", "Mina", "Iris", "Faye"]
FRIEND_NAMES = ["Rowan", "Poppy", "Linden", "Bram", "Mira"]
TRAITS = ["brave", "gentle", "curious", "kind", "thoughtful"]


@dataclass
class StoryParams:
    place: str
    trial: str
    aid: str
    hero_name: str
    friend_name: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy-tale story for a small child about "{f["trial"].keyword}" and a gentle repair.',
        f"Tell a story where {f['hero'].id} and {f['friend'].id} feel worried, work together, and make peace.",
        f"Write a short story with an inner monologue, teamwork, and reconciliation around a {f['trial'].keyword} path.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, item, trial = f["hero"], f["friend"], f["item"], f["trial"]
    aid = f["aid"]
    return [
        QAItem(
            question=f"Why did {hero.id} hesitate at {world.setting.place}?",
            answer=(
                f"{hero.id} hesitated because {hero.pronoun('possessive')} {item.label} could get {trial.soil} "
                f"if {hero.pronoun('subject')} stepped onto the mooshy ground."
            ),
        ),
        QAItem(
            question=f"How did {hero.id} and {friend.id} fix the problem?",
            answer=(
                f"They worked together with {aid.label}. {friend.id} helped clear the way, "
                f"and {hero.id} helped make the path safe."
            ),
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=(
                f"The path had a safe dry crossing, the {item.label} stayed clean, and the friends "
                f"felt close again after they apologized and forgave one another."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does mooshy mean?",
            answer="Mooshy means soft, wet, and squishy under your feet.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other to do something together.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when friends make up after a disagreement and feel peaceful again.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the little voice in a character's head that says what they are thinking.",
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
        if e.place:
            bits.append(f"place={e.place}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
at_risk(T, I) :- trial(T), item(I), zone(T, R), worn_on(I, R).
fix(T, A) :- aid(A), trial(T), guard(A, M), mess(T, M).
compatible(T, A) :- trial(T), aid(A), fix(T, A).
valid_story(P, T, A) :- setting(P), trial(T), aid(A), compatible(T, A).
"""

SETTINGS_REGISTRY = SETTINGS
TRIALS_REGISTRY = TRIALS
AIDS_REGISTRY = AIDS


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
    for tid, t in TRIALS.items():
        lines.append(asp.fact("trial", tid))
        lines.append(asp.fact("mess", tid, t.mess))
        for z in sorted(t.zone):
            lines.append(asp.fact("zone", tid, z))
    for aid, a in AIDS.items():
        lines.append(asp.fact("aid", aid))
        for g in sorted(a.guards):
            lines.append(asp.fact("guard", aid, g))
        for c in sorted(a.covers):
            lines.append(asp.fact("covers", aid, c))
    for item_id, item in [("portrait", Entity(id="portrait", type="thing"))]:
        pass
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, s in SETTINGS.items():
        for trial_id in s.affords:
            trial = TRIALS[trial_id]
            for aid_id, aid in AIDS.items():
                if trial.mess in aid.guards and trial.zone & aid.covers:
                    out.append((place, trial_id, aid_id))
    return sorted(set(out))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale story world with sunburned and mooshy motifs.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--trial", choices=TRIALS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--trait", choices=TRAITS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.trial:
        combos = [c for c in combos if c[1] == args.trial]
    if args.aid:
        combos = [c for c in combos if c[2] == args.aid]
    if not combos:
        raise StoryError("No valid story matches the given options.")
    place, trial, aid = rng.choice(combos)
    return StoryParams(
        place=place,
        trial=trial,
        aid=aid,
        hero_name=args.name or rng.choice(HERO_NAMES),
        friend_name=args.friend or rng.choice(FRIEND_NAMES),
        trait=args.trait or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.hero_name, kind="character", type="girl", label=params.hero_name))
    friend = world.add(Entity(id=params.friend_name, kind="character", type="girl", label=params.friend_name))
    item = world.add(Entity(
        id="cloak",
        kind="thing",
        type="cloak",
        label="cloak",
        phrase="a bright traveling cloak",
        caretaker=friend.id,
        worn_by=hero.id,
        place=params.place,
    ))
    hero.meters["sunburned"] = 1
    hero.memes["worry"] = 1
    friend.memes["worry"] = 1

    trial = TRIALS[params.trial]
    aid = AIDS[params.aid]

    world.say(f"{hero.id} was a little fairy-tale traveler, and one sunny afternoon {hero.pronoun('subject')} came home sunburned.")
    world.say(f"{friend.id} saw the red cheeks and fetched a cool cup of mint tea.")
    world.para()
    world.say(f"They walked together to {world.setting.place}, where the ground looked especially mooshy after the rain.")
    world.say(f"{hero.id} looked at the path and listened to the quiet inner monologue in {hero.pronoun('possessive')} head.")
    world.say(f'"I want to {trial.verb}," {hero.pronoun("subject")} thought, "but I do not want my cloak to get {trial.soil}."')
    world.say(f"{friend.id} nodded, because {friend.pronoun('subject')} had been thinking the same thing.")
    world.para()
    world.say(f'Then {hero.id} had an idea: "{aid.prep}."')
    world.say(f"{friend.id} smiled at once. " + f'"That is teamwork," {friend.pronoun("subject")} said, "and I can help."')
    world.say(f"So they {aid.tail}, and the little fairy helper sprinkled silver dust over the edges.")
    hero.memes["helped"] = 1
    friend.memes["helped"] = 1
    world.para()
    world.say(f"When the safe crossing was ready, {friend.id} said sorry for worrying too loudly.")
    world.say(f"{hero.id} forgave {friend.id}, and {friend.id} forgave {hero.id} for worrying in silence.")
    hero.memes["forgive"] = 1
    friend.memes["apology"] = 1
    hero.memes["peace"] = 1
    friend.memes["peace"] = 1
    world.say(f"In the end, the cloak stayed clean, the path was fair, and the two friends went home reconciled.")
    world.facts.update(hero=hero, friend=friend, item=item, trial=trial, aid=aid)
    return world


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
    StoryParams(place="meadow", trial="crossing", aid="planks", hero_name="Elara", friend_name="Poppy", trait="gentle"),
    StoryParams(place="brook", trial="crossing", aid="stones", hero_name="Nia", friend_name="Bram", trait="brave"),
]


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = python_set
    if clingo_set == python_set:
        print(f"OK: ASP and Python gates match ({len(python_set)} combos).")
        return 0
    print("Mismatch between ASP and Python gates.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for combo in valid_combos():
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
