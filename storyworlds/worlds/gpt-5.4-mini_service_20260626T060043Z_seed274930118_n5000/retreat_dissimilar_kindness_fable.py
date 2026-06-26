#!/usr/bin/env python3
"""
storyworlds/worlds/retreat_dissimilar_kindness_fable.py
=======================================================

A small fable-style storyworld about dissimilar woodland neighbors learning that
kindness can turn retreat into friendship.

Seed tale sketch:
---
A proud sparrow and a quiet mole lived in the same lane but loved different
things. The sparrow sang loudly from the fence; the mole preferred the cool dark
under the roots. One windy afternoon, the sparrow mocked the mole for being so
slow and strange. The mole retreated underground, hurt and lonely.

Then a sudden shower soaked the lane. The sparrow slipped and lost a feather,
and the mole, despite being hurt by the teasing, came back with a leaf to shield
the sparrow. The sparrow felt ashamed, thanked the mole, and learned that
kindness made dissimilar neighbors into friends.

Causal state updates:
---
    mockery              -> target.memes["hurt"] += 1, target.memes["distance"] += 1
    retreat              -> actor.meters["retreat"] += 1, actor.memes["fear"] += 1
    offered kindness     -> receiver.memes["trust"] += 1, actor.memes["kindness"] += 1
    received kindness    -> receiver.memes["warmth"] += 1, receiver.memes["distance"] -= 1
    shared shelter       -> both actors.memes["peace"] += 1
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
    traits: list[str] = field(default_factory=list)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = "lane"

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"sparrow", "bird", "fox", "wolf", "crow", "hare"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"mole", "mouse", "badger", "stoat", "deer"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    shelter: str
    weather: str
    afford_retreat: bool = True


@dataclass
class CharacterSpec:
    type: str
    label: str
    traits: list[str]


@dataclass
class StoryParams:
    setting: str
    boastful: str
    quiet: str
    helper: str
    weather_turn: str
    seed: Optional[int] = None


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
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


def _r_mock(world: World) -> list[str]:
    out = []
    for a in world.entities.values():
        if a.memes.get("mocking", 0.0) < THRESHOLD:
            continue
        target_id = world.facts.get("mock_target")
        if not target_id:
            continue
        target = world.get(target_id)
        sig = ("mock", a.id, target.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        target.memes["hurt"] = target.memes.get("hurt", 0.0) + 1
        target.memes["distance"] = target.memes.get("distance", 0.0) + 1
        out.append(f"{target.label or target.id} felt hurt and pulled away.")
    return out


def _r_retreat(world: World) -> list[str]:
    out = []
    for a in world.entities.values():
        if a.memes.get("hurt", 0.0) < THRESHOLD and a.memes.get("fear", 0.0) < THRESHOLD:
            continue
        sig = ("retreat", a.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        a.meters["retreat"] = a.meters.get("retreat", 0.0) + 1
        a.location = "burrow" if a.type == "mole" else "branch"
        out.append(f"{a.label or a.id} retreated to a quieter place.")
    return out


def _r_kindness(world: World) -> list[str]:
    out = []
    giver_id = world.facts.get("giver")
    receiver_id = world.facts.get("receiver")
    if not giver_id or not receiver_id:
        return out
    giver = world.get(giver_id)
    receiver = world.get(receiver_id)
    if giver.memes.get("kindness", 0.0) < THRESHOLD:
        return out
    sig = ("kindness", giver.id, receiver.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    receiver.memes["trust"] = receiver.memes.get("trust", 0.0) + 1
    receiver.memes["warmth"] = receiver.memes.get("warmth", 0.0) + 1
    receiver.memes["distance"] = max(0.0, receiver.memes.get("distance", 0.0) - 1)
    out.append(f"{receiver.label or receiver.id} felt warmed by the kind act.")
    return out


def _r_peace(world: World) -> list[str]:
    out = []
    if world.facts.get("peace_done"):
        return out
    if world.facts.get("shared_shelter"):
        world.facts["peace_done"] = True
        for eid in (world.facts["boastful"], world.facts["quiet"]):
            world.get(eid).memes["peace"] = world.get(eid).memes.get("peace", 0.0) + 1
        out.append("The lane grew peaceful again.")
    return out


RULES = [_r_mock, _r_retreat, _r_kindness, _r_peace]


def propagate(world: World, narrate: bool = True) -> list[str]:
    all_out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            out = rule(world)
            if out:
                changed = True
                all_out.extend(out)
    if narrate:
        for s in all_out:
            world.say(s)
    return all_out


SETTING_REGISTRY = {
    "lane": Setting(place="the hedgerow lane", shelter="the root bank", weather="windy"),
    "orchard": Setting(place="the orchard edge", shelter="the old shed", weather="breezy"),
    "pond": Setting(place="the reed pond", shelter="the willow reeds", weather="cloudy"),
}

CHARACTERS = {
    "sparrow": CharacterSpec(type="sparrow", label="sparrow", traits=["brave", "proud", "loud"]),
    "mole": CharacterSpec(type="mole", label="mole", traits=["quiet", "careful", "small"]),
    "crow": CharacterSpec(type="crow", label="crow", traits=["wise", "patient", "kind"]),
    "hare": CharacterSpec(type="hare", label="hare", traits=["swift", "restless", "bright"]),
    "badger": CharacterSpec(type="badger", label="badger", traits=["steady", "strong", "plain-spoken"]),
}

CURATED = [
    StoryParams(setting="lane", boastful="sparrow", quiet="mole", helper="crow", weather_turn="shower"),
    StoryParams(setting="orchard", boastful="hare", quiet="badger", helper="crow", weather_turn="rain"),
    StoryParams(setting="pond", boastful="crow", quiet="mole", helper="sparrow", weather_turn="shower"),
]

GAMES = {
    "shower": "a sudden shower",
    "rain": "a cold rain",
    "wind": "a hard wind",
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable-style storyworld about dissimilar neighbors and kindness.")
    ap.add_argument("--setting", choices=SETTING_REGISTRY)
    ap.add_argument("--boastful", choices=CHARACTERS)
    ap.add_argument("--quiet", choices=CHARACTERS)
    ap.add_argument("--helper", choices=CHARACTERS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def valid_combo(setting: str, boastful: str, quiet: str, helper: str) -> bool:
    return len({boastful, quiet, helper}) == 3 and setting in SETTING_REGISTRY


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTING_REGISTRY))
    names = list(CHARACTERS)
    boastful = args.boastful or rng.choice(names)
    quiet = args.quiet or rng.choice([n for n in names if n != boastful])
    helper = args.helper or rng.choice([n for n in names if n not in {boastful, quiet}])
    if not valid_combo(setting, boastful, quiet, helper):
        raise StoryError("The chosen characters must be three different neighbors.")
    if CHARACTERS[boastful].type == CHARACTERS[quiet].type:
        raise StoryError("This fable needs dissimilar neighbors, not a mirrored pair.")
    return StoryParams(setting=setting, boastful=boastful, quiet=quiet, helper=helper, weather_turn=rng.choice(list(GAMES)))


def predict_retreat(world: World, quiet_id: str) -> bool:
    sim = world.copy()
    sim.get(quiet_id).memes["hurt"] = 1
    propagate(sim, narrate=False)
    return sim.get(quiet_id).meters.get("retreat", 0.0) >= THRESHOLD


def tell(setting: Setting, boastful: CharacterSpec, quiet: CharacterSpec, helper: CharacterSpec, weather_turn: str) -> World:
    world = World(setting)
    b = world.add(Entity(id=boastful.type, kind="character", type=boastful.type, label=f"the {boastful.label}", traits=boastful.traits))
    q = world.add(Entity(id=quiet.type, kind="character", type=quiet.type, label=f"the {quiet.label}", traits=quiet.traits))
    h = world.add(Entity(id=helper.type, kind="character", type=helper.type, label=f"the {helper.label}", traits=helper.traits))

    world.facts.update(boastful=b.id, quiet=q.id, giver=h.id, receiver=b.id, mock_target=q.id)

    world.say(
        f"Once, beside {setting.place}, there lived {b.label} and {q.label}. "
        f"They were dissimilar in every way: {b.label} sang high in the open air, "
        f"while {q.label} liked the cool hush beneath the roots."
    )
    world.say(
        f"{b.label.capitalize()} felt proud of {b.pronoun('possessive')} bright song, "
        f"and {q.label} felt content with {q.label} own small burrow."
    )

    world.para()
    world.say(
        f"One windy day, {b.label} laughed at how quiet {q.label} was and how slowly {q.label} moved."
    )
    b.memes["mocking"] = 1
    propagate(world)
    world.say(
        f"{q.label.capitalize()} did not answer. {q.label.capitalize()} simply retreated toward {setting.shelter}, "
        f"hurt by the unkind words."
    )

    world.para()
    world.say(
        f"Then {GAMES[weather_turn]} came across {setting.place}, and the path grew slick and cold."
    )
    b.memes["fear"] = 1
    propagate(world)
    world.say(
        f"{b.label.capitalize()} slipped, and {b.pronoun('possessive')} feathers shivered in the wet."
    )

    world.para()
    h.memes["kindness"] = 1
    world.say(
        f"Yet {h.label}, who had heard the teasing, returned with a broad leaf and held it above {b.label}."
    )
    propagate(world)
    world.say(
        f"{b.label.capitalize()} felt ashamed, then grateful. {b.label.capitalize()} said, "
        f"\"A kind heart is worth more than a loud voice.\""
    )

    world.para()
    world.facts["shared_shelter"] = True
    propagate(world)
    world.say(
        f"So {b.label} and {q.label} walked together to {setting.shelter}, and even "
        f"{h.label} joined them. In the little shelter, the dissimilar neighbors grew gentle, "
        f"and kindness made the lane feel wide enough for all three."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable for a child about dissimilar neighbors who learn kindness beside {world.setting.place}.',
        f"Tell a gentle story where {f['boastful']} and {f['quiet']} are unlike each other, but {f['giver']} helps them with kindness.",
        f'Write a tiny woodland fable that uses the word "retreat" and ends with neighbors sharing {world.setting.shelter}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    b = world.get(f["boastful"])
    q = world.get(f["quiet"])
    h = world.get(f["giver"])
    return [
        QAItem(
            question=f"Who were the dissimilar neighbors in this fable?",
            answer=f"The dissimilar neighbors were {b.label} and {q.label}. They liked different places and different ways of living.",
        ),
        QAItem(
            question=f"Why did {q.label} retreat during the story?",
            answer=f"{q.label} retreated because {b.label} mocked {q.label}, and the hurt words made {q.label} pull away to {world.setting.shelter}.",
        ),
        QAItem(
            question=f"How did {h.label} show kindness?",
            answer=f"{h.label} showed kindness by coming back with a leaf shelter and helping when the lane turned wet and slippery.",
        ),
        QAItem(
            question=f"What changed at the end?",
            answer=f"At the end, the neighbors shared {world.setting.shelter} instead of staying apart, and the lane became peaceful again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does retreat mean?",
            answer="To retreat means to move back or away to a safer or quieter place.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness is when someone chooses to help, comfort, or treat another creature gently.",
        ),
        QAItem(
            question="Why can dissimilar neighbors still be friends?",
            answer="Dissimilar neighbors can still be friends because friendship does not depend on being the same; it depends on care, respect, and kindness.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: loc={e.location} meters={{{', '.join(f'{k}:{v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}:{v}' for k, v in e.memes.items() if v)}}}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
dissimilar(X,Y) :- character(X), character(Y), X != Y, kind(X,KX), kind(Y,KY), KX != KY.
retreats(X) :- hurt(X), quiet_place(X).
kindness_help(G,R) :- kind_act(G), receiver(R).
peace :- kindness_help(_, _), dissimilar(_, _).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTING_REGISTRY.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("place_name", sid, s.place))
    for cid, c in CHARACTERS.items():
        lines.append(asp.fact("character", cid))
        lines.append(asp.fact("kind", cid, c.type))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show dissimilar/2.\n#show peace/0."))
    # sanity only: if there are at least 5 chars, there must be some dissimilar pairs
    dis = asp.atoms(model, "dissimilar")
    if dis:
        print(f"OK: ASP produced {len(dis)} dissimilar pairs.")
        return 0
    print("MISMATCH: ASP produced no dissimilar pairs.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTING_REGISTRY[params.setting],
        CHARACTERS[params.boastful],
        CHARACTERS[params.quiet],
        CHARACTERS[params.helper],
        params.weather_turn,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show dissimilar/2.\n#show peace/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            seed = base_seed + i
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.setting}: {p.boastful} / {p.quiet} / {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTING_REGISTRY))
    names = list(CHARACTERS)
    boastful = args.boastful or rng.choice(names)
    quiet_choices = [n for n in names if n != boastful]
    quiet = args.quiet or rng.choice(quiet_choices)
    helper_choices = [n for n in names if n not in {boastful, quiet}]
    helper = args.helper or rng.choice(helper_choices)
    if len({boastful, quiet, helper}) != 3:
        raise StoryError("The fable needs three different characters.")
    if CHARACTERS[boastful].type == CHARACTERS[quiet].type:
        raise StoryError("The story needs dissimilar neighbors, not two of the same kind.")
    return StoryParams(
        setting=setting,
        boastful=boastful,
        quiet=quiet,
        helper=helper,
        weather_turn=rng.choice(list(GAMES)),
    )


if __name__ == "__main__":
    main()
